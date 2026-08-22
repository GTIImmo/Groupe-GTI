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

function parseArgs(argv) {
  const args = { scope: "archive", limit: 3000, priority: 200, dryRun: false };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    const next = argv[i + 1];
    if (a === "--scope" && next) { args.scope = next; i += 1; }
    else if (a === "--limit" && next) { args.limit = Number(next); i += 1; }
    else if (a === "--priority" && next) { args.priority = Number(next); i += 1; }
    else if (a === "--dry-run") { args.dryRun = true; }
    else throw new Error("Argument inconnu: " + a);
  }
  if (!SOURCES[args.scope]) throw new Error("--scope doit valoir : " + Object.keys(SOURCES).join(", "));
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

async function main() {
  const args = parseArgs(process.argv);
  const source = SOURCES[args.scope];

  const empreintes = await loadSet("app_console_document_fingerprint?select=hektor_annonce_id", "hektor_annonce_id");
  const erreurs = await loadSet("app_console_job?select=hektor_annonce_id&job_type=eq." + JOB_TYPE + "&status=eq.error", "hektor_annonce_id");
  const enFile = await loadSet("app_console_job?select=hektor_annonce_id&job_type=eq." + JOB_TYPE + "&status=in.(pending,running)", "hektor_annonce_id");

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
