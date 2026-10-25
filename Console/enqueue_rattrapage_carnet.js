// LE RATTRAPAGE DU CARNET (R3), SANS RELECTURE DE L'ANNONCE          25/10/2026
// ═══════════════════════════════════════════════════════════════════════════════
// POURQUOI. R3 (le controle du carnet des transactions) juge a deux moments : juste
// apres la creation, et a chaque relecture de l'annonce. Or les lignes que SEULE LA
// NUIT peut prouver -- le numero de mandat, le notaire d'une vente -- partent
// toujours « en attente » au clic, et attendent une relecture APRES la nuit. Une
// relecture d'ouverture n'est accordee qu'a un bien du parc vivant
// (app_console_request_annonce_refresh -> annonce_not_found), et SAISIR UNE VENTE
// FAIT SORTIR LE BIEN DU PARC le jour meme. Ces lignes restaient donc « en attente »
// pour toujours. Mesure du 25/10 : toutes les lignes en attente du carnet sont sur
// des biens sortis du parc -- 0 sur un bien vivant.
//   Etude : notice/ETUDE_NUMEROS_PERSONNES_REGISTRE_TRANSACTIONS_2026-10-24.md §17-19.
//
// CE QUE FAIT CE SCRIPT. Il cherche les annonces dont le carnet a au moins une ligne
// « en attente » ou « inconnu » constatee il y a plus de 6 h, et pose pour chacune
// UN travail `refresh_console_data` en mode « carnet seul » : le worker ne relit pas
// l'annonce, il lance seulement R3 (console_job_worker.js, handleRefreshConsoleData).
//
// ⚠⚠ CE SCRIPT NE PARLE JAMAIS A HEKTOR. Il POSE des travaux ; c'est le worker
//    « sync_light » qui les prend, avec SES freins. Et R3 ne lit Hektor que si une
//    ligne en a besoin (R3_HEKTOR_SI_BESOIN) : le mandat et le notaire se lisent dans
//    notre base, relue la nuit.
//
// ⭐ POURQUOI CE TYPE DE TRAVAIL, ET PAS UN NOUVEAU : `refresh_console_data` est deja
//    accepte par la contrainte, deja distribue (app_console_claim_next_job, service
//    sync_light), deja hors des notifications et hors du suivi de l'ecran. Un type neuf
//    demandait trois verrous en base (memoire « nouveau type de travail : trois verrous »).
//
// QUAND. 4e etape de la descente (scheduled/run_descente.ps1) : la nuit vient de relire
// le registre chez Hektor. L'heure n'est pas critique : R3 est idempotent, et avant la
// nuit il repond « en attente » sans se tromper.
//
// L'INTERRUPTEUR. `APP_AFFAIRE_R3_RATTRAPAGE=1` dans le .env du projet, lu APRES le
// chargement (piege du 20/10). Absent : `--pousser` ne pose RIEN et le dit. L'essai en
// blanc (par defaut) marche toujours -- il ne fait que LIRE.
//
// ⛔ L'ORDRE DE L'ALLUMAGE : pousser -> redemarrer les 4 services, file vide -> SEULEMENT
//    ENSUITE poser la ligne du .env. Un service sur l'ancien code ignorerait « carnet
//    seul » et ferait une relecture complete d'un bien vendu -- chemin jamais eprouve.
//
// LIMITE DECLAREE. Une ligne JAMAIS jugee (etat vide) n'est pas visee : ce sont les
// lignes EXCLUES EXPRES a l'offre (R3_NON_CONTROLES du worker) et celles d'avant la
// naissance de R3 (essai 24933 du 04/09). Les viser obligerait a RECOPIER la liste des
// exclusions du worker -- « deux copies d'une regle divergent ». Une ligne reecrite
// apres son verdict n'est pas visee non plus : apres une vente, plus rien ne se modifie.
//
//     node Console/enqueue_rattrapage_carnet.js                essai en blanc (defaut)
//     node Console/enqueue_rattrapage_carnet.js --pousser      pose (interrupteur requis)
//     options : --limit 50 · --priority 200
//     sortie 0 = fait (ou rien a faire, ou eteint) · 2 = n'a pas pu mesurer
const path = require("path");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const JOB_TYPE = "refresh_console_data";
const INTERRUPTEUR = "APP_AFFAIRE_R3_RATTRAPAGE";
// ⚠ DEUX COPIES D'UNE CONSTANTE : R3_REVOIR_APRES_MS vit dans le worker (6 h). Si elles
//   divergent, la panne est BENIGNE : un travail pose trop tot ne juge rien (R3 respecte
//   SA regle), un travail pose trop tard attend un matin de plus.
const REVOIR_APRES_MS = 6 * 3600 * 1000;
const ORIGINES_JUGEES = ["creation_app", "modification_app"];   // R3_ORIGINES_JUGEES du worker
const ETATS_A_REJUGER = ["en_attente", "inconnu"];

function parseArgs(argv) {
  const args = { pousser: false, limit: 50, priority: 200 };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const next = argv[i + 1];
    if (a === "--pousser") args.pousser = true;
    else if (a === "--dry-run") args.pousser = false;
    else if (a === "--limit" && next) { args.limit = Number(next); i += 1; }
    else if (a === "--priority" && next) { args.priority = Number(next); i += 1; }
    else throw new Error("Argument inconnu: " + a);
  }
  if (!Number.isFinite(args.limit) || args.limit <= 0) throw new Error("--limit doit etre un nombre > 0");
  if (!Number.isFinite(args.priority)) throw new Error("--priority doit etre un nombre");
  return args;
}

async function rest(pathname, options = {}) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const response = await fetch(SUPABASE_URL + "/rest/v1/" + pathname.replace(/^\/+/, ""), {
    ...options,
    headers: {
      apikey: KEY, Authorization: "Bearer " + KEY, "Content-Type": "application/json",
      ...(options.prefer ? { Prefer: options.prefer } : {}),
    },
  });
  if (!response.ok) throw new Error("Supabase " + response.status + " " + (await response.text()).slice(0, 300));
  return options.prefer === "return=minimal" ? null : response.json();
}

// Le lot, annonce par annonce. Lecture seule. `maintenant` se passe pour l'essai.
async function choisirLeLot(args, maintenant = Date.now()) {
  const PLAFOND = 5000;
  const lignes = await rest("app_affaire_champ_app?select=app_affaire_id,champ,etat,constate_le"
    + "&origine=in.(" + ORIGINES_JUGEES.join(",") + ")&etat=in.(" + ETATS_A_REJUGER.join(",") + ")"
    + "&order=app_affaire_id.asc&limit=" + PLAFOND);
  if (!Array.isArray(lignes)) throw new Error("lecture du carnet illisible");
  // ⚠ Un plafond atteint se DIT : on ne pretend pas avoir tout vu.
  const tronque = lignes.length >= PLAFOND;
  const mures = lignes.filter((l) => {
    const vu = Date.parse(l.constate_le || "");
    return !Number.isFinite(vu) || maintenant - vu > REVOIR_APRES_MS;
  });
  const affaires = Array.from(new Set(mures.map((l) => String(l.app_affaire_id))));
  const registre = new Map();
  for (let i = 0; i < affaires.length; i += 200) {
    const tranche = affaires.slice(i, i + 200);
    const rows = await rest("app_affaire_ledger?select=app_affaire_id,kind,hektor_annonce_id,app_dossier_id,hektor_affaire_id"
      + "&app_affaire_id=in.(" + tranche.join(",") + ")");
    for (const r of (Array.isArray(rows) ? rows : [])) registre.set(String(r.app_affaire_id), r);
  }
  const parAnnonce = new Map();
  const sansRegistre = [];
  for (const l of mures) {
    const r = registre.get(String(l.app_affaire_id));
    // R3 ne juge que les lignes d'une transaction NUMEROTEE chez Hektor (hektor_affaire_id not null).
    if (!r || r.hektor_affaire_id == null || !/^\d+$/.test(String(r.hektor_annonce_id || ""))) {
      sansRegistre.push(Number(l.app_affaire_id));
      continue;
    }
    const annonce = String(r.hektor_annonce_id);
    if (!parAnnonce.has(annonce)) parAnnonce.set(annonce, { annonce, dossier: null, lignes: [] });
    const a = parAnnonce.get(annonce);
    const d = Number(r.app_dossier_id);
    if (a.dossier == null && Number.isFinite(d) && d > 0) a.dossier = d;
    a.lignes.push(`${r.kind}:${l.app_affaire_id}:${l.champ}:${l.etat}`);
  }
  // Une annonce qui a deja une relecture en file : elle jugera le carnet elle-meme.
  const enFile = new Set();
  const file = await rest("app_console_job?select=hektor_annonce_id&job_type=eq." + JOB_TYPE
    + "&status=in.(pending,running)&limit=1000");
  for (const j of (Array.isArray(file) ? file : [])) enFile.add(String(j.hektor_annonce_id || ""));
  const candidates = Array.from(parAnnonce.values()).sort((x, y) => Number(x.annonce) - Number(y.annonce));
  const dejaEnFile = candidates.filter((a) => enFile.has(a.annonce)).map((a) => a.annonce);
  const libres = candidates.filter((a) => !enFile.has(a.annonce));
  return {
    lignes_lues: lignes.length, lignes_mures: mures.length, tronque,
    sans_registre: Array.from(new Set(sansRegistre)),
    deja_en_file: dejaEnFile,
    lot: libres.slice(0, args.limit),
    reportees: libres.slice(args.limit).map((a) => a.annonce),
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const allume = String(process.env[INTERRUPTEUR] || "").trim() === "1";
  const choix = await choisirLeLot(args);
  const bilan = {
    script: "enqueue_rattrapage_carnet", le: new Date().toISOString(),
    mode: args.pousser ? "pousser" : "en blanc", interrupteur: allume ? "ALLUME" : "ETEINT",
    lignes_lues: choix.lignes_lues, lignes_mures: choix.lignes_mures,
    ...(choix.tronque ? { alerte: "plafond de lecture atteint : toutes les lignes n'ont pas ete vues" } : {}),
    annonces: choix.lot.map((a) => ({ annonce: a.annonce, dossier: a.dossier, lignes: a.lignes })),
    deja_en_file: choix.deja_en_file, reportees_au_lendemain: choix.reportees, sans_registre: choix.sans_registre,
  };
  if (!choix.lot.length) {
    bilan.statut = "rien a poser";
    console.log(JSON.stringify(bilan, null, 2));
    return 0;
  }
  if (!args.pousser) {
    bilan.statut = "en blanc -- RIEN n'a ete pose";
    console.log(JSON.stringify(bilan, null, 2));
    return 0;
  }
  if (!allume) {
    bilan.statut = `ETEINT (${INTERRUPTEUR} absent du .env) -- RIEN n'a ete pose`;
    console.log(JSON.stringify(bilan, null, 2));
    return 0;
  }
  const pose = new Date().toISOString();
  const travaux = choix.lot.map((a) => ({
    job_type: JOB_TYPE,
    hektor_annonce_id: a.annonce,
    ...(a.dossier != null ? { app_dossier_id: a.dossier } : {}),
    payload_json: { hektor_annonce_id: a.annonce, reason: "rattrapage_carnet", carnet_seul: true, light: true, pose_le: pose },
    priority: args.priority,
  }));
  await rest("app_console_job", { method: "POST", prefer: "return=minimal", body: JSON.stringify(travaux) });
  bilan.statut = `pose : ${travaux.length} travail(aux)`;
  console.log(JSON.stringify(bilan, null, 2));
  return 0;
}

if (require.main === module) {
  main().then((code) => process.exit(code)).catch((e) => {
    console.log(JSON.stringify({ script: "enqueue_rattrapage_carnet", statut: "n'a pas pu mesurer",
      erreur: String(e && e.message ? e.message : e).slice(0, 300) }, null, 2));
    process.exit(2);
  });
}

module.exports = { parseArgs, choisirLeLot };
