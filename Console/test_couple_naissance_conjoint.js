// GED lot G (18/11/2026) -- la naissance du CONJOINT d'un couple part chez Hektor (bloc _m2 du formulaire de couple).
//
// Cet essai extrait les VRAIES fonctions du worker (sans le lancer, sans réseau, comme test_couple_modification.js) et
// les éprouve sur deux formulaires réduits : celui d'un couple (forme relevée sur 606104 le 02/11, avec dateNaissance_m2
// et lieuNaissance_m2) et celui d'une personne seule.
//     node Console/test_couple_naissance_conjoint.js
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
  groupe: tranche("function hektorContactFormGroup("),
  decode: tranche("function decodeHtmlEntities("),
  attr: tranche("function attrValue("),
  extract: tranche("function extractHektorFormValues("),
  appliquer: tranche("function applyHektorContactIdentityValues("),
  replace: tranche("function replaceParam("),
  tel: tranche("function replaceContactTelephoneParams("),
  normaliser: tranche("function normalizeHektorContactPayload("),
  clean: tranche("function cleanString("),
  first: tranche("function firstDefined("),
  dateFr: tranche("function normalizeOptionalFrenchDate("),
  booleen: tranche("function normalizeOptionalBoolean("),
  qualif: tranche("function normalizeHektorContactQualification("),
  statut: tranche("function normalizeHektorContactStatus("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
if (manquants.length) {
  console.log(`⛔ Pièces introuvables dans le worker : ${manquants.join(", ")} -- rien ne serait prouvé.`);
  process.exit(2);
}

const ctx = { URLSearchParams };
vm.createContext(ctx);
try {
  vm.runInContext([morceaux.seul, morceaux.couple, morceaux.decode, morceaux.attr, morceaux.extract, morceaux.groupe,
    morceaux.replace, morceaux.tel, morceaux.appliquer, morceaux.clean, morceaux.first, morceaux.dateFr, morceaux.booleen,
    morceaux.qualif, morceaux.statut, morceaux.normaliser,
    "this.api = { hektorContactFormGroup, extractHektorFormValues, applyHektorContactIdentityValues, normalizeHektorContactPayload };"].join("\n"), ctx);
} catch (e) {
  console.log(`⛔ Les pièces du worker ne se chargent pas (${e.message}) -- rien ne serait prouvé.`);
  process.exit(2);
}
const api = ctx.api;

const G = 'group="mefContacts/contactCoupleAll"';
const FORM_COUPLE = `<div id="nom"><input type="text" name="nom" value="ESSAI MODIF" ${G}></div>
<input type="text" name="prenom" value="Un" ${G}><select name="civilite" ${G}><option value="">-</option></select>
<input type="text" name="dateNaissance" value="00-00-0000" ${G}><input type="text" name="lieuNaissance" value="" ${G}>
<input type="text" name="nom_m2" value="ESSAI MODIF" ${G}><input type="text" name="prenom_m2" value="Deux" ${G}>
<input type="text" name="email_m2[]" value="deux@example.com" ${G}>
<input type="text" name="dateNaissance_m2" value="00-00-0000" ${G}><input type="text" name="lieuNaissance_m2" value="" ${G}>
<span>idContact</span>`;
const S = 'group="mefContacts/contacts_full_accueil"';
const FORM_SEUL = `<input type="text" name="nom" value="DUPONT" ${S}><input type="text" name="prenom" value="Paul" ${S}>
<input type="text" name="dateNaissance" value="00-00-0000" ${S}><span>idContact</span>`;

function modifier(form, payload) {
  const formulaire = api.hektorContactFormGroup(form, {});
  const values = api.extractHektorFormValues(form, formulaire.group);
  const contact = api.normalizeHektorContactPayload({ ...payload, hektor_contact_id: "606104" }, { requireContactId: true, requireName: true });
  if (formulaire.couple) contact.contactStatus = "2";
  api.applyHektorContactIdentityValues(values, contact, { remplacer: true });
  return { values, contact, formulaire };
}

console.log("① la naissance du conjoint part dans le bloc _m2 d'un formulaire de couple");
const a = modifier(FORM_COUPLE, { last_name: "ESSAI MODIF", person_type: "personne_seule", spouse_birth_date: "1982-07-14", spouse_birth_place: "Saint-Étienne" });
controle("le formulaire relu est celui d'un couple", a.formulaire.couple === true);
controle("dateNaissance_m2 = 14-07-1982 (le format de Hektor, jj-mm-aaaa)", a.values.get("dateNaissance_m2") === "14-07-1982", a.values.get("dateNaissance_m2"));
controle("lieuNaissance_m2 = Saint-Étienne", a.values.get("lieuNaissance_m2") === "Saint-Étienne", a.values.get("lieuNaissance_m2"));
controle("⛔ la première personne n'est PAS touchée (dateNaissance reste 00-00-0000, lieu vide)", a.values.get("dateNaissance") === "00-00-0000" && a.values.get("lieuNaissance") === "", `${a.values.get("dateNaissance")} / ${a.values.get("lieuNaissance")}`);
controle("⛔ le reste du conjoint est INTACT (prénom Deux, e-mail)", a.values.get("prenom_m2") === "Deux" && a.values.getAll("email_m2[]").join() === "deux@example.com");

console.log("② les témoins");
const b = modifier(FORM_COUPLE, { last_name: "ESSAI MODIF", birth_date: "1980-02-02" });
controle("TÉMOIN : sans naissance du conjoint envoyée, le bloc _m2 ne bouge pas", b.values.get("dateNaissance_m2") === "00-00-0000" && b.values.get("lieuNaissance_m2") === "");
controle("TÉMOIN : la naissance de la première part toujours dans dateNaissance", b.values.get("dateNaissance") === "02-02-1980");
const c = modifier(FORM_COUPLE, { last_name: "ESSAI MODIF", spouse_birth_date: "", spouse_birth_place: "  " });
controle("⛔ une valeur VIDE ne part pas : elle n'efface rien chez Hektor", c.values.get("dateNaissance_m2") === "00-00-0000" && c.values.get("lieuNaissance_m2") === "");
const d = modifier(FORM_SEUL, { last_name: "DUPONT", spouse_birth_date: "1982-07-14", spouse_birth_place: "Lyon" });
controle("⛔ une personne SEULE : aucune case _m2 n'est fabriquée", !d.values.has("dateNaissance_m2") && !d.values.has("lieuNaissance_m2"));
const FORM_COUPLE_SANS = FORM_COUPLE.replace(/<input type="text" name="dateNaissance_m2"[^>]*><input type="text" name="lieuNaissance_m2"[^>]*>/, "");
const e = modifier(FORM_COUPLE_SANS, { last_name: "ESSAI MODIF", spouse_birth_date: "1982-07-14", spouse_birth_place: "Lyon" });
controle("⛔ un formulaire de couple SANS la case relue : rien n'est fabriqué (on n'écrit que les cases que Hektor a rendues)",
  e.formulaire.couple === true && !e.values.has("dateNaissance_m2") && !e.values.has("lieuNaissance_m2"));
let erreur = null;
try { modifier(FORM_COUPLE, { last_name: "ESSAI MODIF", spouse_birth_date: "14 juillet" }); } catch (e) { erreur = e.message; }
controle("une date illisible LÈVE (le travail échoue, rien n'est envoyé)", /date_naissance contact invalide/.test(erreur || ""), erreur);

console.log(echecs.length ? `\n${echecs.length} ECHEC(S)` : "\nTOUT EST VERT");
process.exit(echecs.length ? 1 : 0);
