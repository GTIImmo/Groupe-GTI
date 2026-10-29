// ⑧ 8f -- UN DOCUMENT RETIRE CHEZ HEKTOR EST GARDE (MARQUE), PLUS EFFACE : essai hors ligne.   29/10/2026
//
// CE QU'ON EPROUVE, sur LE CODE REEL (pruneDeletedDocuments + signatureProtegee + cheminDocument decoupes dans le
// worker, montes dans un bac a sable avec un FAUX Hektor et une FAUSSE base qui notent les appels) :
//   (1) un document depose disparait : il est MARQUE (PATCH present_in_hektor=false), JAMAIS efface, et le journal
//       porte son NOM et son NUMERO
//   (2) deja marque par l'upsert du meme passage : rien de plus en base, mais le journal le nomme
//   (3) marque depuis deux jours : ni ecriture ni journal (on ne re-date pas, on ne repete pas)
//   (4) un document signe n'est jamais touche
//   (5) trois sur quatre d'un coup : MARQUES (marquer se defait), pas de refus « en bloc »
//   (6) interrupteur CONSOLE_DOCUMENTS_RETIRES_EFFACES=1 : l'effacement d'avant (DELETE), et le refus « en bloc » tient
//   (7) l'upsert ecrit present_in_hektor: true (un document qui revient redevient present) -- lu dans le code
//   (8) TEMOIN INVERSE sur 329b9d9 (FIXE) : l'ancienne purge EFFACAIT le cas (1)
//   (9) MUTANT : sans la branche « on garde », le cas (1) est efface -> l'essai le voit
//
//     node Console/test_document_retire_garde.js      sortie 0 = vert · 1 = un echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");

const TEMOIN = "329b9d9";
const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8").replace(/\r\n/g, "\n");
const echecs = [];
function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}
function tranche(texte, debut) {
  const i = texte.indexOf(debut);
  if (i < 0) return null;
  const f = texte.indexOf("\n}", i);
  return f < 0 ? null : texte.slice(i, f + 2);
}
function ligne(texte, debut) {
  const i = texte.indexOf(debut);
  return i < 0 ? "" : texte.slice(i, texte.indexOf("\n", i));
}

const URL_BASE = "https://www.gti-immobilier.fr/admin/documents/biens/1/";
const doc = (id, nom, extra = {}) => ({ id, hektor_document_id: "h" + id, document_name: nom, source: "hektor_console_uploaded_private",
  present_in_hektor: true, absent_depuis: null, metadata_json: { console_url: URL_BASE + nom + "?flag=x" }, ...extra });
const entree = (id, nom) => ({ hektor_document_id: "h" + id, source: "hektor_console_uploaded_private", console_url: URL_BASE + nom + "?flag=x" });

function monter(texte, existants, env) {
  const morceaux = ["async function pruneDeletedDocuments(", "function signatureProtegee(", "function cheminDocument("].map((n) => tranche(texte, n));
  if (morceaux.some((m) => !m)) return null;
  const ctx = { console, JSON, String, Array, Set, Map, Number, Boolean, Date, URL, encodeURIComponent,
    process: { env: env || {} }, existants, appels: [], journal: [] };
  vm.createContext(ctx);
  vm.runInContext(`
    const XMLRPC_URL = "x";
    ${ligne(texte, "const DOCUMENTS_RETIRES_EFFACES =")}
    async function hektorFetch() { return { text: "<html></html>" }; }
    function buildSignatureMapFromHtml() { return new Map(); }
    async function loadExistingDocuments() { return { rows: existants }; }
    async function logJob(id, etape, statut, message, details) { journal.push({ statut, message, details }); }
    async function supabaseRequest(chemin, options) { appels.push({ chemin, methode: options && options.method, corps: options && options.body }); return null; }
    ${morceaux.join("\n\n")}
    this.prune = pruneDeletedDocuments;`, ctx);
  return ctx;
}
const job = { id: "essai" };
const dossier = { hektor_annonce_id: "1" };
const methodes = (c) => c.appels.map((a) => a.methode).join(",");

(async () => {
  // (1)
  let c = monter(src, [doc("a", "bail.pdf"), doc("b", "dpe.pdf")], {});
  if (!c) { console.log("⛔ fonctions introuvables"); process.exit(2); }
  let r = await c.prune(job, dossier, [entree("b", "dpe.pdf")]);
  controle("(1) le document disparu est MARQUE, jamais efface", methodes(c) === "PATCH" && /present_in_hektor":false/.test(c.appels[0].corps)
    && c.appels[0].chemin.includes("in.(a)"), JSON.stringify(c.appels));
  const j1 = c.journal.find((l) => /GARDES chez nous/.test(l.message));
  controle("(1) le journal nomme le document (nom et numero)", j1 && j1.details.documents[0].document_name === "bail.pdf"
    && j1.details.documents[0].hektor_document_id === "ha", JSON.stringify(c.journal));
  controle("(1) la fonction rend le nombre garde", r === 1, String(r));

  // (2) deja marque il y a une seconde par l'upsert
  c = monter(src, [doc("a", "bail.pdf", { present_in_hektor: false, absent_depuis: new Date().toISOString() }), doc("b", "dpe.pdf")], {});
  r = await c.prune(job, dossier, [entree("b", "dpe.pdf")]);
  controle("(2) marque par l'upsert du meme passage : aucune ecriture de plus", c.appels.length === 0, methodes(c));
  controle("(2) ... mais le journal le nomme", c.journal.some((l) => /GARDES/.test(l.message) && l.details.documents[0].document_name === "bail.pdf"));

  // (3) marque depuis deux jours
  c = monter(src, [doc("a", "bail.pdf", { present_in_hektor: false, absent_depuis: new Date(Date.now() - 2 * 86400000).toISOString() }), doc("b", "dpe.pdf")], {});
  r = await c.prune(job, dossier, [entree("b", "dpe.pdf")]);
  controle("(3) deja marque depuis 2 jours : ni ecriture, ni journal", c.appels.length === 0 && c.journal.length === 0 && r === 0,
    methodes(c) + " / " + c.journal.length);

  // (4) signe
  c = monter(src, [doc("a", "mandat.pdf", { source: "hektor_immosign_signed" }), doc("b", "dpe.pdf")], {});
  await c.prune(job, dossier, [entree("b", "dpe.pdf")]);
  controle("(4) un document signe n'est jamais touche", c.appels.length === 0, methodes(c));

  // (5) trois sur quatre
  const quatre = [doc("a", "1.pdf"), doc("b", "2.pdf"), doc("c", "3.pdf"), doc("d", "4.pdf")];
  c = monter(src, quatre, {});
  await c.prune(job, dossier, [entree("d", "4.pdf")]);
  controle("(5) trois d'un coup : MARQUES, pas de refus « en bloc »", methodes(c) === "PATCH" && !c.journal.some((l) => /EN BLOC/.test(l.message)),
    methodes(c));

  // (6) interrupteur
  c = monter(src, [doc("a", "bail.pdf"), doc("b", "dpe.pdf"), doc("e", "x.pdf")], { CONSOLE_DOCUMENTS_RETIRES_EFFACES: "1" });
  await c.prune(job, dossier, [entree("b", "dpe.pdf"), entree("e", "x.pdf")]);
  controle("(6) interrupteur a 1 : l'effacement d'avant", methodes(c) === "DELETE", methodes(c));
  c = monter(src, quatre.map((d) => ({ ...d })), { CONSOLE_DOCUMENTS_RETIRES_EFFACES: "1" });
  await c.prune(job, dossier, [entree("d", "4.pdf")]);
  controle("(6) interrupteur a 1 : le refus « en bloc » tient", c.appels.length === 0 && c.journal.some((l) => /EN BLOC/.test(l.message)), methodes(c));

  // (7) l'upsert remet present
  const up = tranche(src, "async function upsertConsoleDocuments(") || "";
  controle("(7) l'upsert ecrit present_in_hektor: true et absent_depuis: null", /present_in_hektor: true,\n\s*absent_depuis: null,/.test(up));

  // (8) TEMOIN
  let ancien;
  try { ancien = execFileSync("git", ["show", `${TEMOIN}:Console/console_job_worker.js`], { cwd: path.join(__dirname, ".."), maxBuffer: 64 * 1024 * 1024 }).toString("utf8").replace(/\r\n/g, "\n"); }
  catch (e) { console.log("⛔ temoin illisible : " + e.message); process.exit(2); }
  c = monter(ancien, [doc("a", "bail.pdf"), doc("b", "dpe.pdf"), doc("e", "x.pdf")], {});
  if (!c) { console.log("⛔ temoin : fonctions introuvables"); process.exit(2); }
  await c.prune(job, dossier, [entree("b", "dpe.pdf"), entree("e", "x.pdf")]);
  controle("(8) TEMOIN : l'ancienne purge EFFACAIT le document", methodes(c) === "DELETE", methodes(c));
  controle("(8) TEMOIN : l'ancien upsert n'ecrivait pas present_in_hektor", !/present_in_hektor: true,\n\s*absent_depuis: null,/.test(tranche(ancien, "async function upsertConsoleDocuments(") || ""));

  // (9) MUTANT
  const mutant = src.replace("if (!DOCUMENTS_RETIRES_EFFACES) {\n    const maintenant", "if (false) {\n    const maintenant");
  controle("(9) le mutant est fabrique", mutant !== src);
  c = monter(mutant, [doc("a", "bail.pdf"), doc("b", "dpe.pdf"), doc("e", "x.pdf")], {});
  await c.prune(job, dossier, [entree("b", "dpe.pdf"), entree("e", "x.pdf")]);
  controle("(9) MUTANT ATTRAPE : sans la branche « on garde », le document est efface", methodes(c) === "DELETE", methodes(c));

  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\ntout est vert");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log("⛔ " + (e && e.stack || e)); process.exit(2); });
