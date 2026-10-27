// L'ALERTE PART A L'ABANDON DU GESTE -- essai hors ligne.             27/10/2026
//
// LA DECISION (D1 de Frederic, notice/AUDIT_NAVIGATION_APRES_ACTION_2026-10-23.md §23.1) :
// l'e-mail a l'admin ne part plus a CHAQUE echec, seulement quand le travail ne repartira pas.
//
// CE QU'ON EPROUVE, sur LE CODE REEL (fonction decoupee dans le worker, montee dans un bac
// a sable -- meme technique que test_garde_copropriete.js) :
//   (1) un type que la base ne rejoue pas (modifier une annonce) : alerte au 1er echec
//   (2) un type rejoue, 1er essai : alerte RETENUE
//   (3) un type rejoue, 4e essai : retenue ; 5e essai : alerte
//   (4) un refus d'etat, meme rejouable et au 1er essai : alerte
//   (5) une demande de plus de 23 h : alerte (la base ne la rejouera plus)
//   (6) la liste des types rejoues est EXACTEMENT celle lue en base le 27/10
//   (7) les 4 gestes de transaction previennent, avec un libelle
//   (8) processOnce passe bien par la regle, et garde l'interrupteur de repli
//
//     node Console/test_alerte_a_l_abandon.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8").replace(/\r/g, "");
const echecs = [];

function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}

function tranche(debut, fin = "\n}") {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf(fin, i);
  return f < 0 ? null : src.slice(i, f + fin.length);
}

const morceaux = [
  "const REJEU_MAX_TENTATIVES = 5;",
  tranche("const TYPES_REJOUES_PAR_LA_BASE = new Set([", "]);"),
  tranche("const REJEU_DEMANDE_TROP_VIEILLE_MS", ";"),
  tranche("function travailAbandonne("),
  tranche("const JOB_TYPES_A_NOTIFIER = new Set([", "]);"),
  tranche("const JOB_LIBELLES = {", "\n};"),
];
if (morceaux.some((m) => !m)) {
  console.log("N'A PAS PU MESURER : un morceau du worker est introuvable");
  process.exit(2);
}
const bac = {};
vm.createContext(bac);
vm.runInContext(`${morceaux.join("\n")}\nthis.r = { TYPES_REJOUES_PAR_LA_BASE, travailAbandonne, JOB_TYPES_A_NOTIFIER, JOB_LIBELLES };`, bac);
const { TYPES_REJOUES_PAR_LA_BASE, travailAbandonne, JOB_TYPES_A_NOTIFIER, JOB_LIBELLES } = bac.r;

const maintenant = Date.parse("2026-10-27T12:00:00Z");
const travail = (job_type, attempt_count, ilYA_h = 0) => ({
  job_type, attempt_count, requested_at: new Date(maintenant - ilYA_h * 3600 * 1000).toISOString(),
});

controle("(1) type non rejoue, 1er echec -> alerte", travailAbandonne(travail("update_hektor_annonce_fields", 1), false, maintenant) === true);
controle("(2) type rejoue, 1er essai -> retenue", travailAbandonne(travail("change_hektor_annonce_status", 1), false, maintenant) === false);
controle("(3a) type rejoue, 4e essai -> retenue", travailAbandonne(travail("delete_hektor_contact", 4), false, maintenant) === false);
controle("(3b) type rejoue, 5e essai -> alerte", travailAbandonne(travail("delete_hektor_contact", 5), false, maintenant) === true);
controle("(4) refus d'etat au 1er essai -> alerte", travailAbandonne(travail("change_hektor_offre_status", 1), true, maintenant) === true);
controle("(5a) demande de 22 h -> retenue", travailAbandonne(travail("archive_hektor_annonce", 2, 22), false, maintenant) === false);
controle("(5b) demande de 23 h 30 -> alerte", travailAbandonne(travail("archive_hektor_annonce", 2, 23.5), false, maintenant) === true);
controle("(5c) date illisible -> retenue (le 5e essai previendra)", travailAbandonne({ job_type: "archive_hektor_annonce", attempt_count: 1, requested_at: null }, false, maintenant) === false);

// Liste lue en base le 27/10/2026 (pg_get_functiondef de app_console_action_enqueue_due_retries).
const LUE_EN_BASE = [
  "archive_hektor_annonce", "restore_hektor_annonce", "delete_hektor_annonce", "delete_hektor_contact",
  "change_hektor_annonce_status", "assign_hektor_annonce_negotiator", "change_hektor_offre_status",
  "cancel_hektor_compromis", "delete_hektor_vente", "delete_hektor_compromis",
];
const copie = [...TYPES_REJOUES_PAR_LA_BASE].sort();
controle("(6) la copie = la liste de la base (10 types)", JSON.stringify(copie) === JSON.stringify([...LUE_EN_BASE].sort()), copie.join(","));

const transactions = ["change_hektor_offre_status", "cancel_hektor_compromis", "delete_hektor_compromis", "delete_hektor_vente"];
controle("(7a) les 4 gestes de transaction previennent", transactions.every((t) => JOB_TYPES_A_NOTIFIER.has(t)));
controle("(7b) et ont un libelle", transactions.every((t) => typeof JOB_LIBELLES[t] === "string" && JOB_LIBELLES[t].length > 5));

const processOnce = tranche("async function processOnce() {") || "";
const iRegle = processOnce.indexOf("travailAbandonne(job, refusDEtat)");
const iAlerte = processOnce.indexOf("notifyJobFailureBestEffort(job, message)");
controle("(8a) processOnce passe par la regle avant d'alerter", iRegle > 0 && iAlerte > iRegle);
controle("(8b) l'interrupteur de repli est dans la condition", processOnce.includes("!ALERTE_A_L_ABANDON || travailAbandonne"));
controle("(8c) une alerte retenue est ecrite au journal", processOnce.includes('logJob(job.id, "alerte"'));

console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT VERT");
process.exit(echecs.length ? 1 : 0);
