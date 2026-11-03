// COUPLES · PIÈCE G (03/11/2026) -- « Ajouter un conjoint » : le geste du worker, HORS LIGNE.
//
// Extrait les VRAIES fonctions du worker (sans le lancer) et les joue contre un faux Hektor, une fausse
// base et un faux Python. Rien ne part chez Hektor ni chez Supabase. Synthèse couples §52-53.
//     node Console/test_ajouter_conjoint.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const echecs = [];

function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}
function tranche(debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}
function ligne(debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  return src.slice(i, src.indexOf("\n", i) + 1);
}

const morceaux = {
  seul: ligne("const HEKTOR_GROUPE_CONTACT_SEUL = "),
  couple: ligne("const HEKTOR_GROUPE_CONTACT_COUPLE = "),
  attente: ligne("const CONJOINT_ATTENTE_CREATION_MS = "),
  groupe: tranche("function hektorContactFormGroup("),
  decode: tranche("function decodeHtmlEntities("),
  attr: tranche("function attrValue("),
  extract: tranche("function extractHektorFormValues("),
  json: tranche("function safeJsonParse("),
  libre: tranche("function caseDeMenageLibre("),
  cases: tranche("async function lireCasesDeMenage("),
  cible: tranche("async function cibleHektorDuConjoint("),
  geste: tranche("async function handleLinkHektorConjoint("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
if (manquants.length) {
  console.log(`⛔ Pièces introuvables dans le worker : ${manquants.join(", ")} -- rien ne serait prouvé.`);
  process.exit(2);
}
// Les déclarations au worker (les 4 endroits) : une absence = un travail jamais pris ou jamais dit.
controle("(0a) le type est dans la liste du service actions", /"archive_hektor_contact",[\s\S]{0,400}"link_hektor_conjoint",\n  "add_hektor_contact_search"/.test(src));
controle("(0b) le type est dans JOB_TYPES_A_NOTIFIER", /JOB_TYPES_A_NOTIFIER = new Set\(\[[\s\S]*?"link_hektor_conjoint"[\s\S]*?\]\);/.test(src));
controle("(0c) le type a son libellé", /link_hektor_conjoint: "L'ajout du conjoint"/.test(src));
controle("(0d) l'aiguillage mène au geste", /case "link_hektor_conjoint":\n\s+return handleLinkHektorConjoint\(job\);/.test(src));

// ── le décor ──
const G_SEUL = 'group="mefContacts/contacts_full_accueil"';
const G_COUPLE = 'group="mefContacts/contactCoupleAll"';
const FORM_SEUL = `<input type="text" name="nom" value="ESSAI" ${G_SEUL}><input type="text" name="prenom" value="Un" ${G_SEUL}>`;
const FORM_COUPLE = `<input type="text" name="nom" value="ESSAI" ${G_COUPLE}><input type="text" name="nom_m2" value="" ${G_COUPLE}>`;

function monde(options = {}) {
  const o = {
    principal: "29999991", conjoint: "29999992", cibleP: "700001", cibleC: "700002",
    avant: { "700001": { trouve: true, refCouple: "" }, "700002": { trouve: true, refCouple: "" } },
    apres: { "700001": { trouve: true, refCouple: "700001" }, "700002": { trouve: true, refCouple: "700001" } },
    forms: { "700001": FORM_SEUL, "700002": FORM_SEUL },
    reponse: "",
    cibleCManquanteFois: 0, creationEnFile: true, relectureEchoue: false,
    ...options,
  };
  const journal = { gets: [], rpc: [], python: [], logs: [], sommeils: 0, lecturesCible: 0 };
  const ctx = {
    URLSearchParams, JSON, Number, String, Array, Object, Math, Date, Promise, Error, RegExp,
    PLAGE_NUMEROS_APP: 10000000,
    XMLRPC_URL: "https://hektor.test/admin/xmlrpc.php",
    ADMIN_URL: "https://hektor.test/admin/",
    console,
    sleep: async () => { journal.sommeils += 1; },
    logJob: async (_id, step, status, message, payload) => { journal.logs.push({ step, status, message, payload }); },
    cibleHektorContact: async (identite) => (identite === o.principal ? o.cibleP : identite),
    loadContactExecutionContext: async () => ({ contact: { negociateur_email: "n@example.com" }, dossier: null }),
    resolveContactAgencyExecutionPayload: async (p) => p,
    contactAgencyExecutionPayload: (p) => p,
    ensureHektorExecutionContext: async () => true,
    fetchHektorContactEditForm: async (id) => o.forms[String(id)] || "",
    hektorFetch: async (url) => { journal.gets.push(url); return { text: o.reponse }; },
    supabaseRequest: async (chemin, opts) => {
      if (chemin.startsWith("rpc/")) {
        journal.rpc.push({ fonction: chemin.slice(4), corps: opts && opts.body });
        if (chemin === "rpc/app_conjoint_relier_biens") return { ok: true, poses: 1, deja: 0 };
        if (chemin === "rpc/app_conjoint_annuler_optimiste") return { ok: true, principal_remis: 1, conjoint_remis: 1 };
        return null;
      }
      if (chemin.startsWith("app_contact_current?")) {
        journal.lecturesCible += 1;
        if (journal.lecturesCible <= o.cibleCManquanteFois) return [{ hektor_target_id: null }];
        return [{ hektor_target_id: o.cibleC }];
      }
      if (chemin.startsWith("app_console_job?")) return o.creationEnFile ? [{ id: "c1", status: "running" }] : [];
      throw new Error(`appel inattendu : ${chemin}`);
    },
    runProjectPythonScript: async (args) => {
      journal.python.push(args.join(" "));
      if (args[0] === "phase2/sync/contact_refcouple_from_api.py") {
        const transformee = journal.gets.some((u) => u.includes("transformeContactToConjunct"));
        return { stdout: JSON.stringify({ lus: transformee ? o.apres : o.avant }) + "\n", stderr: "" };
      }
      if (args[0] === "phase2/contacts/relire_couple_rattache.py") {
        if (o.relectureEchoue) throw new Error("Python relire_couple_rattache.py failed with code 1");
        return { stdout: JSON.stringify({ ok: true, etapes: [] }) + "\n", stderr: "" };
      }
      throw new Error(`script inattendu : ${args[0]}`);
    },
  };
  vm.createContext(ctx);
  vm.runInContext([morceaux.seul, morceaux.couple, morceaux.attente, morceaux.decode, morceaux.attr, morceaux.extract,
    morceaux.groupe, morceaux.json, morceaux.libre, morceaux.cases, morceaux.cible, morceaux.geste,
    "this.geste = handleLinkHektorConjoint;"].join("\n"), ctx);
  const job = { id: "job-g", payload_json: { hektor_contact_id: o.principal, conjoint_id: o.conjoint } };
  return { lancer: () => ctx.geste(job), journal };
}
const transformations = (j) => j.gets.filter((u) => u.includes("transformeContactToConjunct"));
const appele = (j, f) => j.rpc.some((r) => r.fonction === f);

(async () => {
  // 1. le chemin heureux
  {
    const { lancer, journal } = monde();
    const r = await lancer();
    const t = transformations(journal);
    controle("(1a) le geste aboutit : status linked, preuve au 1er essai", r.status === "linked" && r.preuve && r.preuve.essai === 1, JSON.stringify(r));
    controle("(1b) UNE seule requête de transformation", t.length === 1, String(t.length));
    controle("(1c) la requête porte conjoint = la seconde, refCouple = la porteuse (pas l'inverse)",
      t[0] && /[?&]conjoint=700002(&|$)/.test(t[0]) && /[?&]refCouple=700001(&|$)/.test(t[0]) && t[0].includes("mode=contacts-create-transformeContactToConjunct"), t[0]);
    controle("(1d) les biens sont demandés APRÈS la preuve", appele(journal, "app_conjoint_relier_biens"));
    controle("(1e) la relecture des deux fiches est lancée, la personne et le conjoint nommés",
      journal.python.some((p) => p === "phase2/contacts/relire_couple_rattache.py --principal 29999991 --conjoint 29999992"), journal.python.join(" | "));
    controle("(1f) aucun retour arrière sur un succès", !appele(journal, "app_conjoint_annuler_optimiste"));
  }
  // 2. Hektor ne confirme pas : pas de renvoi, retour arrière, ni biens ni relecture
  {
    const { lancer, journal } = monde({ apres: { "700001": { trouve: true, refCouple: "" }, "700002": { trouve: true, refCouple: "" } } });
    let erreur = null;
    try { await lancer(); } catch (e) { erreur = e; }
    controle("(2a) sans preuve, le travail échoue en le disant", erreur && /n'a pas confirme le menage/.test(erreur.message), erreur && erreur.message);
    controle("(2b) la requête n'est PAS renvoyée (une seule écriture)", transformations(journal).length === 1, String(transformations(journal).length));
    controle("(2c) la preuve a été cherchée trois fois", journal.python.filter((p) => p.startsWith("phase2/sync/contact_refcouple_from_api.py")).length === 4);
    controle("(2d) nos fiches sont remises comme avant", appele(journal, "app_conjoint_annuler_optimiste"));
    controle("(2e) ni biens ni relecture", !appele(journal, "app_conjoint_relier_biens") && !journal.python.some((p) => p.startsWith("phase2/contacts/")));
  }
  // 3. la personne est déjà dans un ménage chez Hektor
  {
    const { lancer, journal } = monde({ avant: { "700001": { trouve: true, refCouple: "555" }, "700002": { trouve: true, refCouple: "" } } });
    let erreur = null;
    try { await lancer(); } catch (e) { erreur = e; }
    controle("(3a) refusé AVANT toute écriture", erreur && /deja dans un menage/.test(erreur.message) && transformations(journal).length === 0, erreur && erreur.message);
    controle("(3b) nos fiches sont remises", appele(journal, "app_conjoint_annuler_optimiste"));
  }
  // 4. refCouple = elle-même mais formulaire de COUPLE (une porteuse) : le formulaire tranche
  {
    const { lancer, journal } = monde({
      avant: { "700001": { trouve: true, refCouple: "" }, "700002": { trouve: true, refCouple: "700002" } },
      forms: { "700001": FORM_SEUL, "700002": FORM_COUPLE } });
    let erreur = null;
    try { await lancer(); } catch (e) { erreur = e; }
    controle("(4) une porteuse de couple est refusée par son formulaire, sans écriture",
      erreur && /deja une fiche de couple/.test(erreur.message) && transformations(journal).length === 0, erreur && erreur.message);
  }
  // 5. une lecture ratée n'est jamais un vert
  {
    const { lancer, journal } = monde({ avant: { "700001": { trouve: false, erreur: "x" }, "700002": { trouve: true, refCouple: "" } } });
    let erreur = null;
    try { await lancer(); } catch (e) { erreur = e; }
    controle("(5a) lecture API ratée : refus sans écriture", erreur && /n'a pas pu etre relu/.test(erreur.message) && transformations(journal).length === 0, erreur && erreur.message);
    const m = monde({ forms: { "700001": FORM_SEUL, "700002": "" } });
    let e2 = null;
    try { await m.lancer(); } catch (e) { e2 = e; }
    controle("(5b) formulaire illisible : refus sans écriture", e2 && /illisible/.test(e2.message) && transformations(m.journal).length === 0, e2 && e2.message);
  }
  // 6. le conjoint NOUVEAU : on attend sa création, mais pas une création qui n'existe pas
  {
    const { lancer, journal } = monde({ conjoint: "20000099", cibleCManquanteFois: 2, creationEnFile: true });
    const r = await lancer();
    controle("(6a) création en cours : on attend son numéro, puis on rattache", r.status === "linked" && journal.sommeils >= 2 && transformations(journal).length === 1, JSON.stringify(r));
    const m = monde({ conjoint: "20000099", cibleCManquanteFois: 99, creationEnFile: false });
    let e2 = null;
    try { await m.lancer(); } catch (e) { e2 = e; }
    controle("(6b) sans numéro ET sans création en cours : refus immédiat, sans écriture",
      e2 && /sa creation n'est pas en cours/.test(e2.message) && transformations(m.journal).length === 0, e2 && e2.message);
  }
  // 7. après la preuve, une relecture ratée ne défait pas le couple
  {
    const { lancer, journal } = monde({ relectureEchoue: true });
    const r = await lancer();
    controle("(7) relecture ratée : le couple reste posé, l'échec est dit", r.status === "linked" && r.relecture && r.relecture.ok === false
      && !appele(journal, "app_conjoint_annuler_optimiste") && journal.logs.some((l) => l.step === "conjoint_relecture" && l.status === "error"));
  }
  // 8. MUTANT : la même preuve avec le lien à l'envers doit être refusée
  {
    const { lancer, journal } = monde({ apres: { "700001": { trouve: true, refCouple: "700002" }, "700002": { trouve: true, refCouple: "700002" } } });
    let erreur = null;
    try { await lancer(); } catch (e) { erreur = e; }
    controle("(8) MUTANT : un ménage dans l'autre sens n'est pas une preuve", erreur && appele(journal, "app_conjoint_annuler_optimiste"), erreur && erreur.message);
  }

  console.log(echecs.length ? `\n${echecs.length} ECHEC(S)` : "\nTOUT VERT");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log("⛔ essai interrompu :", e && e.stack); process.exit(2); });
