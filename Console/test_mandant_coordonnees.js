// A.2 LOT 6b P3 -- la porte « modifier un mandant » suit la regle D-5 : un telephone ou un e-mail remplace
// la ligne de MEME etiquette (portable / fixe / email), avec son numero interne, au lieu de vider la liste.
// Sur LE CODE REEL du worker (updateHektorMandantContact entier, decoupe, doublures) : n'appelle rien.  05/11/2026
//     node Console/test_mandant_coordonnees.js   (0 = vert · 1 = un echec · 2 = pas pu mesurer)
// ⭐ TEMOIN INVERSE : le worker d'avant P3 perd le fixe d'un mandant (portable + fixe) ; interrupteur ETEINT,
//   le code du travail envoie A L'OCTET la meme requete que celui d'avant.
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
const controle = (nom, ok, detail) => { console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`); if (!ok) echecs.push(nom); };
const racine = path.join(__dirname, "..");
const git = (args) => execFileSync("git", args, { cwd: racine, encoding: "utf8", maxBuffer: 128 * 1024 * 1024 });
const srcNeuf = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
let srcAvant;
try {
  const introduit = git(["log", "--format=%H", "-S", "LA REGLE D-5 DANS LA PORTE DU MANDANT", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
  srcAvant = git(["show", `${introduit ? `${introduit}~1` : "HEAD"}:Console/console_job_worker.js`]);
} catch (e) { console.log("ECHEC  version d'avant illisible -- " + e.message); process.exit(2); }

const tranche = (src, d) => { const i = src.indexOf(d); return i < 0 ? null : src.slice(i, src.indexOf("\n}", i) + 2); };
const ligne = (src, d) => { const i = src.indexOf(d); return i < 0 ? null : src.slice(i, src.indexOf("\n", i) + 1); };

function monter(src, interrupteur, form) {
  const lignes = ["const HEKTOR_GROUPE_CONTACT_SEUL = ", "const HEKTOR_GROUPE_CONTACT_COUPLE = ", "const HEKTOR_GROUPE_PARTENAIRE_PERSONNE = ",
    "const HEKTOR_GROUPE_PARTENAIRE_SOCIETE = "].map((d) => ligne(src, d)).filter(Boolean);
  const blocs = ["function cleanString(", "function decodeHtmlEntities(", "function attrValue(", "function extractHektorFormValues(",
    "function hektorContactFormGroup(", "function replaceFirstArrayParam(", "function lignesCoordonnees(", "function poserCoordonnee(",
    "function ecrireLignesCoordonnees(", "function remplacerCoordonnee(", "async function interrupteurCoordonneesRemplacer(",
    "async function updateHektorMandantContact("].map((d) => tranche(src, d)).filter(Boolean);
  const trace = { corps: null, journal: [] };
  const D = {
    URLSearchParams,
    XMLRPC_URL: "https://hektor.invalid/admin/xmlrpc.php",
    ADMIN_URL: "https://hektor.invalid/admin/",
    supabaseRequest: async (chemin) => {
      if (chemin.includes("key=eq.contact_coordonnees_remplacer")) return [{ value: interrupteur }];
      throw new Error(`appel non prevu : ${chemin}`);
    },
    fetchHektorContactEditForm: async () => form,
    applyContactLocalityIds: async () => null,
    logJob: async (_id, _e, _s, _m, details) => { trace.journal.push(details || {}); },
    hektorFetch: async (_url, options) => { trace.corps = options.body; return { text: '{"content_mefContacts":"ok"}' }; },
  };
  // eslint-disable-next-line no-new-func
  const f = new Function(...Object.keys(D), `${lignes.join("")}\n${blocs.join("\n")}\nreturn updateHektorMandantContact;`)(...Object.values(D));
  return { f, trace };
}

const G = 'group="mefContacts/contacts_full_accueil"';
const sel = (v) => `<select name="label_telephone[]" ${G}>${["portable", "fixe", "bureau", "fax"].map((o) => `<option value="${o}"${o === v ? " selected" : ""}>${o}</option>`).join("")}</select>`;
const ligneTel = (label, id, valeur) => `${sel(label)}<input type="hidden" name="id_telephone[]" value="${id}" ${G}><input type="text" name="telephone[]" value="${valeur}" ${G}>`;
const ligneMail = (id, valeur) => `<input type="hidden" name="label_email[]" value="email" ${G}><input type="hidden" name="id_email[]" value="${id}" ${G}><input type="text" name="email[]" value="${valeur}" ${G}>`;
const tete = `<input type="text" name="nom" value="ESSAI" ${G}><input type="text" name="prenom" value="Jean" ${G}>`;
// Valeurs fictives, forme relevee par le chantier partenaires sur 604020 (labels en <select>).
const FORM_PORTABLE_FIXE = tete + ligneTel("portable", "11", "0600000001") + ligneTel("fixe", "12", "0400000001") + ligneMail("21", "ancien@example.invalid");
const FORM_FIXE_D_ABORD = tete + ligneTel("fixe", "12", "0400000001") + ligneTel("portable", "11", "0600000001") + ligneMail("21", "ancien@example.invalid");
const FORM_SANS_TEL = tete + ligneMail("21", "ancien@example.invalid");

const payload = (extra) => ({ last_name: "ESSAI", first_name: "Jean", email: "neuf@example.invalid", ...extra });
const triplets = (corps, s) => {
  const p = new URLSearchParams(String(corps));
  const l = p.getAll(`label_${s}[]`), i = p.getAll(`id_${s}[]`), v = p.getAll(`${s}[]`);
  return Array.from({ length: Math.max(l.length, i.length, v.length) }, (_, k) => `${l[k] ?? "∅"}|${i[k] ?? "∅"}|${v[k] ?? "∅"}`);
};
const job = { id: "job-p3" };

(async () => {
  try {
    controle("(0) LA PREUVE D'ABORD : la regle D-5 est dans la porte du mandant du travail", srcNeuf.includes("LA REGLE D-5 DANS LA PORTE DU MANDANT"));
    controle("(0) …et PAS dans la version d'avant (sinon le temoin ne temoigne de rien)", !srcAvant.includes("LA REGLE D-5 DANS LA PORTE DU MANDANT"));

    // 1. LE DEFAUT D'AVANT : un mandant a portable + fixe, on modifie son portable.
    const a = monter(srcAvant, "on", FORM_PORTABLE_FIXE);
    await a.f(job, "70001", "603953", payload({ phone: "0611111111" }));
    const ta = triplets(a.trace.corps, "telephone");
    controle("1. TEMOIN INVERSE : le worker d'avant perd la valeur du fixe (2 etiquettes, 1 seul numero)",
      ta.length === 2 && ta[0] === "portable|11|0611111111" && ta[1] === "fixe|12|∅", JSON.stringify(ta));

    // 2. APRES, interrupteur ALLUME
    const n = monter(srcNeuf, "on", FORM_PORTABLE_FIXE);
    await n.f(job, "70001", "603953", payload({ phone: "0611111111" }));
    controle("2. le portable remplace SA ligne (meme numero interne), le fixe reste intact",
      JSON.stringify(triplets(n.trace.corps, "telephone")) === JSON.stringify(["portable|11|0611111111", "fixe|12|0400000001"]), JSON.stringify(triplets(n.trace.corps, "telephone")));
    controle("2. l'e-mail remplace sa ligne (meme numero interne)",
      JSON.stringify(triplets(n.trace.corps, "email")) === JSON.stringify(["email|21|neuf@example.invalid"]), JSON.stringify(triplets(n.trace.corps, "email")));
    controle("2. le journal du travail dit « remplacees_par_etiquette »", n.trace.journal.some((d) => d.coordonnees === "remplacees_par_etiquette"));
    const fd = monter(srcNeuf, "on", FORM_FIXE_D_ABORD);
    await fd.f(job, "70001", "603953", payload({ phone: "0611111111" }));
    controle("2. le fixe en PREMIERE ligne n'est pas pris pour le portable",
      JSON.stringify(triplets(fd.trace.corps, "telephone")) === JSON.stringify(["fixe|12|0400000001", "portable|11|0611111111"]), JSON.stringify(triplets(fd.trace.corps, "telephone")));
    const st = monter(srcNeuf, "on", FORM_SANS_TEL);
    await st.f(job, "70001", "603953", payload({ phone: "0611111111" }));
    controle("2. aucun telephone chez Hektor : le portable nait (numero interne vide)",
      JSON.stringify(triplets(st.trace.corps, "telephone")) === JSON.stringify(["portable||0611111111"]), JSON.stringify(triplets(st.trace.corps, "telephone")));
    const vide = monter(srcNeuf, "on", FORM_PORTABLE_FIXE);
    await vide.f(job, "70001", "603953", payload({ phone: "" }));
    controle("2. un telephone VIDE n'efface rien : portable et fixe repartent tels quels",
      JSON.stringify(triplets(vide.trace.corps, "telephone")) === JSON.stringify(["portable|11|0600000001", "fixe|12|0400000001"]), JSON.stringify(triplets(vide.trace.corps, "telephone")));
    const sans = monter(srcNeuf, "on", FORM_PORTABLE_FIXE);
    await sans.f(job, "70001", "603953", payload({}));
    controle("2. sans telephone dans l'envoi : les lignes de Hektor repartent telles quelles",
      JSON.stringify(triplets(sans.trace.corps, "telephone")) === JSON.stringify(["portable|11|0600000001", "fixe|12|0400000001"]));

    // 3. ETEINT : a l'octet le chemin d'avant (4 envois differents)
    for (const [nom, form, extra] of [["portable + fixe", FORM_PORTABLE_FIXE, { phone: "0611111111" }], ["fixe d'abord", FORM_FIXE_D_ABORD, { phone: "0611111111" }],
      ["sans telephone", FORM_SANS_TEL, { phone: "0611111111" }], ["telephone vide", FORM_PORTABLE_FIXE, { phone: "" }]]) {
      const av = monter(srcAvant, "off", form); await av.f(job, "70001", "603953", payload(extra));
      const ne = monter(srcNeuf, "off", form); await ne.f(job, "70001", "603953", payload(extra));
      controle(`3. ETEINT (${nom}) : la requete envoyee est IDENTIQUE au worker d'avant, a l'octet`, String(av.trace.corps) === String(ne.trace.corps));
    }
    const lr = monter(srcNeuf, "illisible", FORM_PORTABLE_FIXE);
    await lr.f(job, "70001", "603953", payload({ phone: "0611111111" }));
    controle("3. un interrupteur illisible vaut ETEINT (journal « premiere_ligne »)", lr.trace.journal.some((d) => d.coordonnees === "premiere_ligne"));
  } catch (e) {
    console.log("ECHEC  le montage n'a pas pu tourner -- " + (e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e));
    process.exit(2);
  }
  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})();
