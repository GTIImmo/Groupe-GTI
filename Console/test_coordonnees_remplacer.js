// D-5 (05/11/2026) -- une coordonnée MODIFIÉE remplace sa ligne chez Hektor au lieu d'en ajouter une
// (chantier partenaires §21). Le défaut : le worker envoyait le téléphone / l'e-mail avec un numéro interne VIDE,
// Hektor créait une ligne et gardait l'ancienne (604020 : 5 téléphones). Cet essai extrait les VRAIES fonctions du
// worker (sans le lancer) et les éprouve sur la forme relevée en GET le 05/11 sur 604020 (labels en <select>
// portable|fixe|bureau|fax, e-mails en <input> « email »).
//     node Console/test_coordonnees_remplacer.js
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

const morceaux = {
  decode: tranche("function decodeHtmlEntities("),
  attr: tranche("function attrValue("),
  extract: tranche("function extractHektorFormValues("),
  replace: tranche("function replaceParam("),
  tel: tranche("function replaceContactTelephoneParams("),
  lignes: tranche("function lignesCoordonnees("),
  poser: tranche("function poserCoordonnee("),
  ecrire: tranche("function ecrireLignesCoordonnees("),
  remplacer: tranche("function remplacerCoordonnee("),
  appliquer: tranche("function applyHektorContactIdentityValues("),
  maj: tranche("async function updateHektorContactIdentity("),
  interrupteur: tranche("async function interrupteurCoordonneesRemplacer("),
  creation: tranche("async function createHektorContact("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
if (manquants.length) {
  console.log(`⛔ Pièces introuvables dans le worker : ${manquants.join(", ")} -- rien ne serait prouvé.`);
  process.exit(2);
}

const ctx = { URLSearchParams };
vm.createContext(ctx);
vm.runInContext([morceaux.decode, morceaux.attr, morceaux.extract, morceaux.replace, morceaux.tel, morceaux.lignes,
  morceaux.poser, morceaux.ecrire, morceaux.remplacer, morceaux.appliquer,
  "this.api = { extractHektorFormValues, applyHektorContactIdentityValues, lignesCoordonnees };"].join("\n"), ctx);
const api = ctx.api;

const G = 'group="mefContacts/contacts_full_accueil"';
const sel = (v) => `<select name="label_telephone[]" ${G}>${["portable", "fixe", "bureau", "fax"].map((o) => `<option value="${o}"${o === v ? " selected" : ""}>${o}</option>`).join("")}</select>`;
const ligneTel = (label, id, valeur) => `${sel(label)}<input type="hidden" name="id_telephone[]" value="${id}" ${G}><input type="text" name="telephone[]" value="${valeur}" ${G}>`;
const ligneMail = (id, valeur) => `<input type="hidden" name="label_email[]" value="email" ${G}><input type="hidden" name="id_email[]" value="${id}" ${G}><input type="text" name="email[]" value="${valeur}" ${G}>`;
// La forme de 604020 relue le 05/11 (valeurs fictives) : portable, fixe, puis 3 portables ajoutés par le défaut.
const FORM_604020 = `<input type="text" name="nom" value="TEST" ${G}>`
  + ligneTel("portable", "446123", "0600000001") + ligneTel("fixe", "446124", "0400000001")
  + ligneTel("portable", "446198", "0600000002") + ligneTel("portable", "446199", "0600000003")
  + ligneTel("portable", "446282", "0600000004")
  + ligneMail("445815", "a@example.invalid") + ligneMail("446125", "b@example.invalid");
const FORM_SIMPLE = `<input type="text" name="nom" value="TEST" ${G}>` + ligneTel("portable", "11", "0600000001") + ligneMail("21", "a@example.invalid");
const FORM_VIDE = `<input type="text" name="nom" value="TEST" ${G}>`;

const envoi = (extra) => ({ contactStatus: "1", civility: null, lastName: "TEST", firstName: null, email: null,
  phone: null, phoneSecondary: null, address: null, city: null, postalCode: null, birthDate: null, birthPlace: null,
  maritalStatus: null, sourceId: null, categoryId: null, comments: null, sendRgpdEmail: false, ...extra });
const lire = (form, extra, options) => {
  const v = api.extractHektorFormValues(form, "mefContacts/contacts_full_accueil");
  api.applyHektorContactIdentityValues(v, envoi(extra), options);
  return v;
};
const triplets = (v, s) => api.lignesCoordonnees(v, s).map((l) => `${l.label}|${l.id}|${l.valeur}`);

// 1. ÉTEINT : le chemin d'avant, à l'identique
const e = lire(FORM_SIMPLE, { phone: "0611111111", email: "n@example.invalid" });
controle("(1) TÉMOIN éteint : le téléphone part avec un numéro interne VIDE (le défaut d'avant)",
  JSON.stringify(triplets(e, "telephone")) === JSON.stringify(["portable||0611111111"]), JSON.stringify(triplets(e, "telephone")));
controle("(2) TÉMOIN éteint : l'e-mail aussi", JSON.stringify(triplets(e, "email")) === JSON.stringify(["email||n@example.invalid"]));

// 2. ALLUMÉ, une ligne relue
const on = { remplacer: true };
const s = lire(FORM_SIMPLE, { phone: "0611111111", email: "n@example.invalid" }, on);
controle("(3) le portable REMPLACE sa ligne : même numéro interne, nouvelle valeur, une seule ligne",
  JSON.stringify(triplets(s, "telephone")) === JSON.stringify(["portable|11|0611111111"]), JSON.stringify(triplets(s, "telephone")));
controle("(4) l'e-mail remplace sa ligne", JSON.stringify(triplets(s, "email")) === JSON.stringify(["email|21|n@example.invalid"]));

// 3. ALLUMÉ, la forme de 604020 : on remplace la DERNIÈRE ligne de la sorte (celle que l'API rend)
const t = lire(FORM_604020, { phone: "0699999999" }, on);
const tt = triplets(t, "telephone");
controle("(5) 604020 : 5 lignes avant, 5 lignes après (rien n'est ajouté)", tt.length === 5, JSON.stringify(tt));
controle("(6) 604020 : c'est le DERNIER portable (446282) qui reçoit le numéro", tt[4] === "portable|446282|0699999999", tt[4]);
controle("(7) 604020 : les 4 autres lignes repartent telles quelles, dans l'ordre",
  JSON.stringify(tt.slice(0, 4)) === JSON.stringify(["portable|446123|0600000001", "fixe|446124|0400000001", "portable|446198|0600000002", "portable|446199|0600000003"]));
controle("(8) un téléphone non envoyé ne touche pas aux e-mails",
  JSON.stringify(triplets(t, "email")) === JSON.stringify(["email|445815|a@example.invalid", "email|446125|b@example.invalid"]));
const f = lire(FORM_604020, { phoneSecondary: "0477777777" }, on);
controle("(9) le fixe remplace la ligne « fixe » (446124) et seulement elle",
  triplets(f, "telephone")[1] === "fixe|446124|0477777777" && triplets(f, "telephone").length === 5
  && triplets(f, "telephone")[4] === "portable|446282|0600000004");
const m = lire(FORM_604020, { email: "z@example.invalid" }, on);
controle("(10) l'e-mail remplace la DERNIÈRE ligne e-mail (446125)",
  JSON.stringify(triplets(m, "email")) === JSON.stringify(["email|445815|a@example.invalid", "email|446125|z@example.invalid"]));

// 4. ALLUMÉ, rien de relu : une ligne neuve, comme avant
const n = lire(FORM_VIDE, { phone: "0611111111", phoneSecondary: "0411111111", email: "n@example.invalid" }, on);
controle("(11) aucune ligne relue : portable et fixe naissent (numéro interne vide)",
  JSON.stringify(triplets(n, "telephone")) === JSON.stringify(["portable||0611111111", "fixe||0411111111"]), JSON.stringify(triplets(n, "telephone")));
controle("(12) aucune ligne relue : l'e-mail naît", JSON.stringify(triplets(n, "email")) === JSON.stringify(["email||n@example.invalid"]));

// 5. une valeur vide n'efface rien
const vide = lire(FORM_SIMPLE, { phone: "", email: "" }, on);
controle("(13) un téléphone et un e-mail VIDES laissent les lignes de Hektor intactes",
  JSON.stringify(triplets(vide, "telephone")) === JSON.stringify(["portable|11|0600000001"])
  && JSON.stringify(triplets(vide, "email")) === JSON.stringify(["email|21|a@example.invalid"]));

// 6. le conjoint (couple, bloc _m2)
const C = 'group="mefContacts/contactCoupleAll"';
const FORM_COUPLE = `<input type="text" name="nom" value="TEST" ${C}><input type="text" name="nom_m2" value="TEST" ${C}>`
  + `<select name="label_telephone_m2[]" ${C}><option value="portable" selected>portable</option></select><input type="hidden" name="id_telephone_m2[]" value="31" ${C}><input type="text" name="telephone_m2[]" value="0600000009" ${C}>`
  + `<input type="hidden" name="label_email_m2[]" value="email" ${C}><input type="hidden" name="id_email_m2[]" value="41" ${C}><input type="text" name="email_m2[]" value="c@example.invalid" ${C}>`;
const vc = api.extractHektorFormValues(FORM_COUPLE, "mefContacts/contactCoupleAll");
api.applyHektorContactIdentityValues(vc, envoi({ contactStatus: "2", spousePhone: "0688888888", spouseEmail: "d@example.invalid" }), on);
controle("(14) conjoint : téléphone et e-mail remplacent leur ligne _m2",
  JSON.stringify(triplets(vc, "telephone_m2")) === JSON.stringify(["portable|31|0688888888"])
  && JSON.stringify(triplets(vc, "email_m2")) === JSON.stringify(["email|41|d@example.invalid"]));

// 7. le branchement
controle("(15) la MODIFICATION lit l'interrupteur et passe { remplacer }",
  /const remplacer = await interrupteurCoordonneesRemplacer\(\);/.test(morceaux.maj)
  && /applyHektorContactIdentityValues\(values, contact, \{ remplacer \}\)/.test(morceaux.maj));
controle("(16) la CRÉATION n'est pas touchée (aucune option)", /applyHektorContactIdentityValues\(values, contact\);/.test(morceaux.creation)
  && !/remplacer/.test(morceaux.creation));
controle("(17) l'interrupteur : une lecture ratée vaut éteint", /catch \(_\) \{\s*return false;/.test(morceaux.interrupteur)
  && /key=eq\.contact_coordonnees_remplacer/.test(morceaux.interrupteur));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTout est vert.");
process.exit(echecs.length ? 1 : 0);
