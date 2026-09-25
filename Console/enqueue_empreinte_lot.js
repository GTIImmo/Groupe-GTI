// Composeur de lot pour le rattrapage d'empreintes documentaires (2026-08-21).
//
// enqueue_console_sync_jobs.js empile TOUT un perimetre : il ne sait pas sauter les annonces
// deja marquees. Rejouer une annonce deja traitee coute des requetes Hektor pour rien, et le
// quota de la console web est la contrainte qui a fait bannir notre IP le 20/08.
// Ce script ne retient donc que les annonces reellement a faire.
//
// Trois exclusions, dans cet ordre :
//   1. empreinte deja posee            -> deja rattrapee
//   2. job en erreur sur cette annonce -> NE JAMAIS REJOUER (les 403 repetes ont fait bannir l'IP)
//   3. job pending/running             -> deja dans la file
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const JOB_TYPE = "sync_console_documents";

const SOURCES = {
  archive: { table: "app_archive_annonce_index_current", idColumn: "app_archive_id" },
  historical: { table: "app_historical_annonce_index_current", idColumn: "app_historical_id" },
  brouillon: { table: "app_brouillon_annonce_index_current", idColumn: "app_brouillon_id" },
};

// AJOUTS DU 25/09 pour la tache planifiee de 23:00 -- tous ADDITIFS : sans eux, le
// comportement manuel d'origine est inchange.
//   --scope auto              enchaine archive -> historical -> brouillon tout seul
//   --exiger-file-vide        REFUSE de poser un lot si le precedent n'est pas digere
//   --max-erreurs-recentes N  REFUSE si N erreurs ou plus en 24 h (signature d'un rejet Hektor)
// Codes de sortie : 0 pose ou rien a faire · 3 file occupee · 4 trop d'erreurs · 1 panne
function parseArgs(argv) {
  const args = { scope: "archive", limit: 3000, priority: 200, dryRun: false,
                 exigerFileVide: false, maxErreursRecentes: 0 };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = argv[i + 1];
    if (a === "--scope" && next) { args.scope = next; i += 1; }
    else if (a === "--limit" && next) { args.limit = Number(next); i += 1; }
    else if (a === "--priority" && next) { args.priority = Number(next); i += 1; }
    else if (a === "--dry-run") { args.dryRun = true; }
    else if (a === "--exiger-file-vide") { args.exigerFileVide = true; }
    else if (a === "--max-erreurs-recentes" && next) { args.maxErreursRecentes = Number(next); i += 1; }
    else throw new Error("Argument inconnu: " + a);
  }
  if (args.scope !== "auto" && !SOURCES[args.scope]) {
    throw new Error("--scope doit valoir : auto, " + Object.keys(SOURCES).join(", "));
  }
  return args;
}

async function rest(pathname, options = {}) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const response = await fetch(SUPABASE_URL + "/rest/v1/" + pathname.replace(/^\/+/, ""), {
    ...options,
    headers: { apikey: KEY, Authorization: "Bearer " + KEY, "Content-Type": "application/json", ...(options.prefer ? { Prefer: options.prefer } : {}) },
  });
  if (!response.ok) throw new Error("Supabase " + response.status + " " + (await response.text()).slice(0, 300));
  return options.prefer === "return=minimal" ? null : response.json();
}

// Pagination systematique : sans elle PostgREST plafonne a 1000 lignes et on croirait a tort
// que les annonces non retournees sont "a faire" -> on les rejouerait indefiniment.
async function loadSet(pathname, column) {
  const set = new Set();
  const page = 1000;
  for (let offset = 0; ; offset += page) {
    const rows = await rest(pathname + "&limit=" + page + "&offset=" + offset);
    if (!Array.isArray(rows) || !rows.length) break;
    for (const row of rows) set.add(String(row[column]));
    if (rows.length < page) break;
  }
  return set;
}

// REFUS 1 : la file n'est pas vide. Poser un lot par-dessus un lot non digere ferait
// grossir le retard nuit apres nuit sans que personne ne le voie -- et un jour le
// rattrapage deborderait sur le run de 05:00, qui a lui aussi besoin de Hektor.
// REFUS 2 : des erreurs recentes en nombre = Hektor nous rejette. La regle du projet est
// « un 403 arrete tout, on ne rejoue jamais » : on s'arrete et on laisse regarder.
async function refusEventuel(args, enFile) {
  if (args.exigerFileVide && enFile.size > 0) {
    console.log(JSON.stringify({ refus: "file_occupee", en_file: enFile.size,
      message: "le lot precedent n'est pas digere -- rien n'est pose" }, null, 2));
    return 3;
  }
  if (args.maxErreursRecentes > 0) {
    const depuis = new Date(Date.now() - 24 * 3600 * 1000).toISOString();
    const recentes = await rest("app_console_job?select=hektor_annonce_id&job_type=eq." + JOB_TYPE
      + "&status=eq.error&finished_at=gte." + encodeURIComponent(depuis) + "&limit=1000");
    const n = Array.isArray(recentes) ? recentes.length : 0;
    if (n >= args.maxErreursRecentes) {
      console.log(JSON.stringify({ refus: "trop_d_erreurs_recentes", erreurs_24h: n,
        seuil: args.maxErreursRecentes,
        message: "Hektor nous rejette peut-etre -- on arrete, on ne rejoue jamais" }, null, 2));
      return 4;
    }
  }
  return 0;
}

// Y a-t-il encore au moins UNE annonce a faire dans ce perimetre ? On s'arrete des la
// premiere trouvee : inutile de balayer 35 000 lignes pour repondre oui.
async function premierReste(source, empreintes, erreurs, enFile) {
  const page = 1000;
  for (let offset = 0; ; offset += page) {
    const rows = await rest(source.table + "?select=" + source.idColumn + ",hektor_annonce_id&order="
      + source.idColumn + ".asc&limit=" + page + "&offset=" + offset);
    if (!Array.isArray(rows) || !rows.length) return false;
    for (const row of rows) {
      const id = String(row.hektor_annonce_id);
      if (!row.hektor_annonce_id || row[source.idColumn] == null) continue;
      if (empreintes.has(id) || erreurs.has(id) || enFile.has(id)) continue;
      return true;
    }
    if (rows.length < page) return false;
  }
}

async function main() {
  const args = parseArgs(process.argv);

  const empreintes = await loadSet("app_console_document_fingerprint?select=hektor_annonce_id", "hektor_annonce_id");
  const erreurs = await loadSet("app_console_job?select=hektor_annonce_id&job_type=eq." + JOB_TYPE + "&status=eq.error", "hektor_annonce_id");
  const enFile = await loadSet("app_console_job?select=hektor_annonce_id&job_type=eq." + JOB_TYPE + "&status=in.(pending,running)", "hektor_annonce_id");

  const code = await refusEventuel(args, enFile);
  if (code) { process.exitCode = code; return; }

  // --scope auto : on prend le PREMIER perimetre qui a encore du travail. L'ordre est
  // celui du volume decroissant, et il se vide tout seul -- quand les trois sont finis,
  // le script le dit et ne pose rien (code 0 : ce n'est pas une panne).
  const scopes = args.scope === "auto" ? ["archive", "historical", "brouillon"] : [args.scope];
  let source = null;
  for (const s of scopes) {
    const reste = await premierReste(SOURCES[s], empreintes, erreurs, enFile);
    if (reste) { args.scope = s; source = SOURCES[s]; break; }
  }
  if (!source) {
    console.log(JSON.stringify({ scope: args.scope, rien_a_faire: true,
      message: "tous les perimetres sont rattrapes" }, null, 2));
    return;
  }

  const retenus = [];
  const stats = { balayees: 0, deja_marquees: 0, exclues_erreur: 0, deja_en_file: 0 };
  const page = 1000;
  for (let offset = 0; retenus.length < args.limit; offset += page) {
    const rows = await rest(source.table + "?select=" + source.idColumn + ",hektor_annonce_id&order=" + source.idColumn + ".asc&limit=" + page + "&offset=" + offset);
    if (!Array.isArray(rows) || !rows.length) break;
    for (const row of rows) {
      if (retenus.length >= args.limit) break;
      stats.balayees += 1;
      const id = String(row.hektor_annonce_id);
      if (!row.hektor_annonce_id || row[source.idColumn] == null) continue;
      if (empreintes.has(id)) { stats.deja_marquees += 1; continue; }
      if (erreurs.has(id)) { stats.exclues_erreur += 1; continue; }
      if (enFile.has(id)) { stats.deja_en_file += 1; continue; }
      retenus.push(row);
    }
    if (rows.length < page) break;
  }

  let empiles = 0;
  if (!args.dryRun) {
    for (let i = 0; i < retenus.length; i += 100) {
      const jobs = retenus.slice(i, i + 100).map((row) => ({
        job_type: JOB_TYPE,
        app_dossier_id: Number(row[source.idColumn]),
        hektor_annonce_id: String(row.hektor_annonce_id),
        payload_json: { scope: args.scope, lot: "empreinte" },
        status: "pending",
        priority: args.priority,
      }));
      await rest("app_console_job", { method: "POST", prefer: "return=minimal", body: JSON.stringify(jobs) });
      empiles += jobs.length;
    }
  }

  console.log(JSON.stringify({ scope: args.scope, ...stats, retenus: retenus.length, jobs_empiles: args.dryRun ? 0 : empiles, dry_run: args.dryRun }, null, 2));
}

main().catch((error) => { console.error(error.message); process.exit(1); });
