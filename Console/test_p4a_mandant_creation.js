// ⑧ TYPES §53 P4-a -- LE MANDANT EXISTANT CHOISI A LA CREATION : la part du worker, essai hors ligne.   28/10/2026
//
// CE QU'ON EPROUVE, sur LE CODE REEL (fonctions decoupees dans le worker, montees dans un bac a sable avec une
// FAUSSE BASE qui note les appels -- meme technique que test_type_apres_ecriture_worker.js) :
//   (1) le numero Hektor est pose sur les liens nes au clic : PAR NOTRE DOSSIER, numero vide, source app
//   (2) Hektor confirme -> le lien est ETABLI (present_in_hektor a vrai), par (annonce, contact Hektor)
//   (3) la creation echoue -> les liens nes au clic quittent l'ecran (absent_depuis), la trace reste
//   (4) la base refuse -> JAMAIS d'exception, et c'est ECRIT au journal
//   (5) les appels sont branches au bon endroit de la creation (lu dans le code)
//   (6) TEMOIN INVERSE : sur la version d'avant P4-a (le parent du commit 412a0bf, FIXE : un temoin qui lit HEAD
//       casse des que la correction est committee, lecon du 27/10), les trois fonctions n'existent pas
//
//     node Console/test_p4a_mandant_creation.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");

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
const NOMS = ["async function poserNumeroSurLiensDeLaCreation(", "async function marquerLienDeLaCreationEtabli(",
  "async function retirerLiensDeLaCreationEchouee(",
  // ⑧ types §53.5 P4-b
  "async function poserCaseCibleDuMandantNeuf(", "async function suivreLienDuMandantNeuf("];

function monter(texte, base) {
  const morceaux = NOMS.map((n) => tranche(texte, n));
  if (morceaux.some((m) => !m)) return null;
  const ctx = { console, JSON, String, Array, Date, encodeURIComponent, journal: [], appels: [], base };
  vm.createContext(ctx);
  vm.runInContext(`
    async function supabaseRequest(chemin, options) { appels.push({ chemin, options }); return base(chemin, options); }
    async function logJob(id, etape, statut, message, details) { journal.push({ etape, statut, message, details }); }
    async function recalculerTypeDesContacts(job, contacts, contexte) { appels.push({ chemin: 'type', contacts, contexte }); return { recalcule: true }; }
    ${morceaux.join("\n\n")}
    function cleanString(v) { return String(v == null ? "" : v).trim(); }
    this.api = { poserNumeroSurLiensDeLaCreation, marquerLienDeLaCreationEtabli, retirerLiensDeLaCreationEchouee,
      poserCaseCibleDuMandantNeuf, suivreLienDuMandantNeuf };`, ctx);
  return ctx;
}

(async () => {
  const job = { id: "essai" };
  // (1)
  let c = monter(src, () => [{ app_relation_id: 1, app_contact_id: 20000013 }]);
  if (!c) { console.log("⛔ fonctions introuvables dans le worker"); process.exit(2); }
  let r = await c.api.poserNumeroSurLiensDeLaCreation(job, 10000031, 63400);
  const a1 = c.appels[0];
  controle("(1) numero pose PAR NOTRE DOSSIER, sur les seuls liens nes au clic encore sans numero",
    a1 && a1.chemin === "app_relation?app_dossier_id=eq.10000031&hektor_annonce_id=is.null&source=eq.app"
      && a1.options.method === "PATCH" && JSON.parse(a1.options.body).hektor_annonce_id === "63400" && r.lignes === 1,
    JSON.stringify(a1));
  controle("(1) c'est dit au journal", c.journal.some((j) => j.etape === "liens_creation_numero" && j.statut === "done"));
  c = monter(src, () => []);
  await c.api.poserNumeroSurLiensDeLaCreation(job, 10000031, 63400);
  controle("(1) TEMOIN : aucun lien ne au clic -> rien d'ecrit au journal", c.journal.length === 0);
  // (2)
  c = monter(src, () => [{ app_relation_id: 1 }]);
  r = await c.api.marquerLienDeLaCreationEtabli(job, "63400", "605973");
  const a2 = c.appels[0];
  controle("(2) Hektor confirme -> le lien est ETABLI, seulement s'il ne l'etait pas et n'est pas retire",
    a2 && a2.chemin === "app_relation?hektor_annonce_id=eq.63400&hektor_contact_id=eq.605973&present_in_hektor=is.false&retire_le=is.null"
      && JSON.parse(a2.options.body).present_in_hektor === true && r.lignes === 1, JSON.stringify(a2));
  // (3)
  c = monter(src, () => [{ app_relation_id: 1, app_contact_id: 20000013 }]);
  r = await c.api.retirerLiensDeLaCreationEchouee(job, 10000031, "Hektor injoignable");
  const a3 = c.appels[0];
  controle("(3) creation echouee -> les liens nes au clic quittent l'ecran (absent_depuis), RIEN n'est efface",
    a3 && a3.chemin === "app_relation?app_dossier_id=eq.10000031&hektor_annonce_id=is.null&source=eq.app&absent_depuis=is.null"
      && a3.options.method === "PATCH" && typeof JSON.parse(a3.options.body).absent_depuis === "string" && r.lignes === 1,
    JSON.stringify(a3));
  controle("(3) le type du mandant qui perd ce lien est recalcule (audit du 28/10)",
    c.appels.some((a) => a.chemin === "type" && Array.isArray(a.contacts) && a.contacts[0] === 20000013 && a.contexte === "creation_echouee"),
    JSON.stringify(c.appels.map((a) => a.chemin)));
  controle("(3) aucun appel DELETE dans les trois fonctions", c.appels.every((a) => (a.options || {}).method !== "DELETE")
    && !NOMS.map((n) => tranche(src, n)).join("").includes('"DELETE"'));
  // (4)
  c = monter(src, () => { throw new Error("la base refuse"); });
  let jete = false;
  try {
    await c.api.poserNumeroSurLiensDeLaCreation(job, 1, 2);
    await c.api.marquerLienDeLaCreationEtabli(job, "2", "3");
    await c.api.retirerLiensDeLaCreationEchouee(job, 1, "x");
  } catch (_) { jete = true; }
  controle("(4) la base refuse -> jamais d'exception, et les trois echecs sont ECRITS",
    !jete && c.journal.filter((j) => j.statut === "error").length === 3, JSON.stringify(c.journal.map((j) => j.etape + ":" + j.statut)));
  c = monter(src, () => []);
  r = await c.api.poserNumeroSurLiensDeLaCreation(job, null, 2);
  controle("(4) sans dossier -> rien demande a la base", r.status === "skipped" && c.appels.length === 0);
  // (5) les branchements, lus dans le code
  const creation = src.slice(src.indexOf("async function handleCreateHektorDraftAnnonce("), src.indexOf("async function handleCreateHektorDraftAnnonceWithProvisional("));
  const enveloppe = tranche(src, "async function handleCreateHektorDraftAnnonceWithProvisional(") || "";
  controle("(5) le numero est pose sur les liens JUSTE apres l'avoir pose sur la fiche du bien",
    /Numero Hektor pose sur la ligne de l'app, AVANT le rafraichissement", numeroApp\);\n\s+\/\/[^\n]*\n\s+await poserNumeroSurLiensDeLaCreation\(job, payload\.app_dossier_id, created\.id\);/.test(creation));
  controle("(5) apres la confirmation de Hektor : etabli, puis le type", /await marquerLienDeLaCreationEtabli\(job, String\(created\.id\), cibleMandant\);\n\s+await recalculerTypeDuBien\(job, String\(created\.id\), "mandant_creation_etabli"\);/.test(creation));
  controle("(5) Hektor refuse : le meme retour arriere que « lier un mandant »", /if \(cibleMandant\) await annulerRattachementOptimiste\(job, String\(created\.id\), cibleMandant, message\);/.test(creation));
  controle("(5) la creation echoue : les liens sont retires, APRES la marque d'erreur de la fiche",
    /await markProvisionalCreationError\([^\n]*\n\s+\/\/[^\n]*\n\s+await retirerLiensDeLaCreationEchouee\(job, payload && payload\.app_dossier_id/.test(enveloppe));
  // (7) P4-b, le mandant neuf
  c = monter(src, () => []);
  await c.api.poserCaseCibleDuMandantNeuf(job, "20000017", 606001, 63400);
  const a7 = c.appels[0];
  controle("(7) P4-b : la case cible de NOTRE fiche recoit le numero Hektor, et RIEN d'autre (piege du 21/09)",
    a7 && a7.chemin === "app_contact_current?hektor_contact_id=eq.20000017" && a7.options.method === "PATCH"
      && JSON.stringify(JSON.parse(a7.options.body)) === JSON.stringify({ hektor_target_id: "606001" }), JSON.stringify(a7));
  c = monter(src, () => [{ app_relation_id: 9, app_contact_id: 20000017 }]);
  r = await c.api.suivreLienDuMandantNeuf(job, "20000017", 10000200,
    { hektor_contact_id: "606001", present_in_hektor: true, absent_depuis: null }, "relation_etablie", "etabli");
  const a8 = c.appels[0];
  controle("(7) P4-b : Hektor confirme -> le lien (par NOTRE numero et notre dossier) est etabli sous son numero Hektor",
    a8 && a8.chemin === "app_relation?app_contact_id=eq.20000017&app_dossier_id=eq.10000200&source=eq.app&retire_le=is.null"
      && JSON.parse(a8.options.body).present_in_hektor === true && JSON.parse(a8.options.body).hektor_contact_id === "606001" && r.lignes === 1,
    JSON.stringify(a8));
  controle("(7) P4-b : ... et son type est recalcule", c.appels.some((x) => x.chemin === "type" && x.contacts[0] === "20000017"));
  c = monter(src, () => []);
  r = await c.api.suivreLienDuMandantNeuf(job, "", 10000200, {}, "x", "x");
  controle("(7) P4-b : sans notre numero (charge d'avant P4-b) -> rien demande a la base", r.status === "skipped" && c.appels.length === 0);
  c = monter(src, () => { throw new Error("la base refuse"); });
  jete = false;
  try {
    await c.api.poserCaseCibleDuMandantNeuf(job, "20000017", 606001, 63400);
    await c.api.suivreLienDuMandantNeuf(job, "20000017", 1, {}, "rattachement_annule", "x");
  } catch (_) { jete = true; }
  controle("(7) P4-b : la base refuse -> jamais d'exception, et c'est ECRIT", !jete && c.journal.filter((j) => j.statut === "error").length === 2);
  controle("(7) P4-b : la case cible est posee JUSTE apres la creation chez Hektor, avant meme la preuve du rattachement",
    /const createdContact = await createHektorMandantContact\(job, created\.id, \{[\s\S]{0,140}\}\);\n(\s+\/\/[^\n]*\n){2}\s+await poserCaseCibleDuMandantNeuf\(job, initialMandantPayload\.app_identite, createdContact\.contactId, created\.id\);\n\s+await sleep\(1800\);/.test(creation));
  controle("(7) P4-b : rattachement confirme -> etabli + relecture du contact (comme le geste voisin)",
    /Mandant initial cree et associe a l annonce[\s\S]{0,260}await suivreLienDuMandantNeuf\(job, initialMandantPayload\.app_identite, payload\.app_dossier_id,\n\s+\{ hektor_contact_id: String\(createdContact\.contactId\), present_in_hektor: true, absent_depuis: null \}[\s\S]{0,260}enqueueRefreshConsoleContactDataJobBestEffort\(job, createdContact\.contactId/.test(creation));
  controle("(7) P4-b : echec -> le lien quitte l'ecran (absent_depuis), la fiche reste",
    /mandant initial non associe[\s\S]{0,260}await suivreLienDuMandantNeuf\(job, initialMandantPayload\.app_identite, payload\.app_dossier_id,\n\s+\{ absent_depuis: new Date\(\)\.toISOString\(\) \}/.test(creation));
  // (6) temoin inverse
  try {
    const avant = execFileSync("git", ["show", "412a0bf^:Console/console_job_worker.js"], { cwd: path.join(__dirname, ".."), encoding: "utf8", maxBuffer: 1 << 27 });
    controle("(6) TEMOIN INVERSE : la version d'avant n'a pas ces fonctions", monter(avant.replace(/\r\n/g, "\n"), () => []) === null);
  } catch (e) { console.log("⚠ temoin inverse non fait : " + e.message); }
  console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log("ERREUR", e.message); process.exit(2); });
