// PARTENAIRES (05/11/2026) -- la modification d'une fiche PARTENAIRE (chantier partenaires §18 et §20, défaut D-2).
//
// Le défaut : un partenaire PERSONNE porte group="mefContacts/contacts_full_accueil_partenaire", un partenaire
// SOCIÉTÉ group="mefContacts/partenaireMoraleInfo" (sans « nom ») ; le worker ne lisait que la personne seule et le
// couple → « Formulaire edition contact Hektor introuvable ». Cet essai extrait les VRAIES fonctions du worker (sans
// le lancer) et les éprouve sur des formulaires réduits, à la forme relevée en GET le 05/11 (414566, 423684).
//     node Console/test_partenaire_modification.js
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
  pPersonne: ligne("const HEKTOR_GROUPE_PARTENAIRE_PERSONNE = "),
  pSociete: ligne("const HEKTOR_GROUPE_PARTENAIRE_SOCIETE = "),
  champsPersonne: ligne("const HEKTOR_CHAMPS_PERSONNE_SEULEMENT = "),
  groupe: tranche("function hektorContactFormGroup("),
  decode: tranche("function decodeHtmlEntities("),
  attr: tranche("function attrValue("),
  extract: tranche("function extractHektorFormValues("),
  appliquer: tranche("function applyHektorContactIdentityValues("),
  replace: tranche("function replaceParam("),
  tel: tranche("function replaceContactTelephoneParams("),
  maj: tranche("async function updateHektorContactIdentity("),
  mandant: tranche("async function updateHektorMandantContact("),
  interrupteur: tranche("async function interrupteurModifPartenaire("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
if (manquants.length) {
  console.log(`⛔ Pièces introuvables dans le worker : ${manquants.join(", ")} -- rien ne serait prouvé.`);
  process.exit(2);
}

const ctx = { URLSearchParams };
vm.createContext(ctx);
vm.runInContext([morceaux.seul, morceaux.couple, morceaux.pPersonne, morceaux.pSociete, morceaux.champsPersonne,
  morceaux.decode, morceaux.attr, morceaux.extract, morceaux.groupe, morceaux.replace, morceaux.tel, morceaux.appliquer,
  "this.api = { hektorContactFormGroup, extractHektorFormValues, applyHektorContactIdentityValues, HEKTOR_CHAMPS_PERSONNE_SEULEMENT };"].join("\n"), ctx);
const api = ctx.api;

// Formes réduites relevées le 05/11.
const P = 'group="mefContacts/contacts_full_accueil_partenaire"';
const FORM_PARTENAIRE_PERSONNE = `<select name="civilite" ${P}><option value="" selected>Non défini</option></select>
<input type="text" name="nom" value="" ${P}><input type="text" name="prenom" value="" ${P}>
<select name="metier" ${P}><option value="5" selected>Syndic</option></select>
<input type="hidden" name="label_telephone[]" value="fixe" ${P}><input type="hidden" name="id_telephone[]" value="11" ${P}>
<input type="text" name="telephone[]" value="0477000000" ${P}><input type="text" name="email[]" value="" ${P}>
<input type="text" name="dateNaissance" value="" ${P}><textarea name="commentaires" ${P}>note</textarea>`;
const M = 'group="mefContacts/partenaireMoraleInfo"';
const FORM_PARTENAIRE_SOCIETE = `<input type="hidden" name="logo" value="" ${M}>
<select name="metier" ${M}><option value="">-</option><option value="5" selected>Syndic</option></select>
<select name="juridique" ${M}><option value="" selected>Non défini</option><option value="SARL">SARL</option></select>
<input type="text" name="sociale" value="FONCIA LOIRE AUVERGNE " ${M}><input type="text" name="siret" value="40688003900176" ${M}>
<input type="hidden" name="label_telephone[]" value="fixe" ${M}><input type="hidden" name="id_telephone[]" value="12" ${M}>
<input type="text" name="telephone[]" value="0477111111" ${M}><input type="text" name="url" value="https://example.com" ${M}>
<textarea name="commentaires" ${M}>gestion</textarea><input type="file" name="files[]">`;
const S = 'group="mefContacts/contacts_full_accueil"';
const FORM_SEUL = `<input type="text" name="nom" value="DUPONT" ${S}><input type="text" name="prenom" value="Paul" ${S}>
<input type="text" name="email[]" value="p@example.com" ${S}>`;
const C = 'group="mefContacts/contactCoupleAll"';
const FORM_COUPLE = `<input type="text" name="nom" value="ESSAI" ${C}><input type="text" name="nom_m2" value="ESSAI" ${C}>`;

// Ce que la fenêtre « Modifier le contact » envoie, une fois normalisé (cases vides = null).
const envoi = (extra) => ({ contactStatus: "1", civility: null, lastName: "FONCIA LOIRE AUVERGNE", firstName: null,
  companyName: null, legalForm: null, siret: null, partnerJobId: null, website: null, email: null,
  phone: "0477999999", phoneSecondary: null, address: null, city: null, postalCode: null, birthDate: null,
  birthPlace: null, maritalStatus: null, sourceId: null, categoryId: null, comments: null, sendRgpdEmail: false, ...extra });

// 1. le groupe, interrupteur ÉTEINT : exactement le chemin d'avant
controle("(1) TÉMOIN éteint : un partenaire société retombe sur le groupe d'avant (l'échec d'avant)",
  api.hektorContactFormGroup(FORM_PARTENAIRE_SOCIETE).group === "mefContacts/contacts_full_accueil");
controle("(2) TÉMOIN éteint : la personne seule et le couple ne bougent pas",
  api.hektorContactFormGroup(FORM_SEUL).group === "mefContacts/contacts_full_accueil"
  && api.hektorContactFormGroup(FORM_COUPLE).couple === true);

// 2. le groupe, interrupteur ALLUMÉ
const on = { partenaires: true };
const gS = api.hektorContactFormGroup(FORM_PARTENAIRE_SOCIETE, on);
const gP = api.hektorContactFormGroup(FORM_PARTENAIRE_PERSONNE, on);
controle("(3) un partenaire SOCIÉTÉ est reconnu", gS.group === "mefContacts/partenaireMoraleInfo" && gS.societe === true, JSON.stringify(gS));
controle("(4) un partenaire PERSONNE est reconnu", gP.group === "mefContacts/contacts_full_accueil_partenaire" && gP.societe === false && gP.partenaire === true, JSON.stringify(gP));
controle("(5) allumé : la personne seule garde son groupe, à l'identique",
  JSON.stringify(api.hektorContactFormGroup(FORM_SEUL, on)) === JSON.stringify({ group: "mefContacts/contacts_full_accueil", couple: false }));
controle("(6) allumé : le couple garde son groupe, à l'identique",
  JSON.stringify(api.hektorContactFormGroup(FORM_COUPLE, on)) === JSON.stringify({ group: "mefContacts/contactCoupleAll", couple: true }));
controle("(7) « contacts_full_accueil » ne se confond pas avec « contacts_full_accueil_partenaire »",
  api.hektorContactFormGroup(FORM_PARTENAIRE_PERSONNE).group === "mefContacts/contacts_full_accueil"
  && !api.extractHektorFormValues(FORM_PARTENAIRE_PERSONNE, "mefContacts/contacts_full_accueil").has("nom"));

// 3. la société : le nom part dans « sociale », le reste relu ne bouge pas
const vS = api.extractHektorFormValues(FORM_PARTENAIRE_SOCIETE, gS.group);
controle("(8) PREUVE : la société n'a pas de « nom » mais a « sociale »", !vS.has("nom") && vS.get("sociale") === "FONCIA LOIRE AUVERGNE ");
const relusS = new Set(vS.keys());
api.applyHektorContactIdentityValues(vS, envoi({ contactStatus: "3" }));
for (const champ of api.HEKTOR_CHAMPS_PERSONNE_SEULEMENT) if (!relusS.has(champ)) vS.delete(champ);
controle("(9) la raison sociale reçoit le nom saisi", vS.get("sociale") === "FONCIA LOIRE AUVERGNE", vS.get("sociale"));
controle("(10) métier, forme juridique, SIRET et site restent comme Hektor les a rendus",
  vS.get("metier") === "5" && vS.get("juridique") === "" && vS.get("siret") === "40688003900176" && vS.get("url") === "https://example.com",
  JSON.stringify([vS.get("metier"), vS.get("juridique"), vS.get("siret"), vS.get("url")]));
controle("(11) le téléphone saisi remplace l'ancien", vS.getAll("telephone[]").join(",") === "0477999999", vS.getAll("telephone[]").join(","));
controle("(12) aucun champ de PERSONNE n'est ajouté à l'envoi d'une société",
  ["civilite", "nom", "prenom", "dateNaissance", "lieuNaissance", "marital_status"].every((c) => !vS.has(c)));
controle("(13) le commentaire non saisi reste celui de Hektor", vS.get("commentaires") === "gestion");

// 4. le partenaire personne : chemin d'une personne
const vP = api.extractHektorFormValues(FORM_PARTENAIRE_PERSONNE, gP.group);
api.applyHektorContactIdentityValues(vP, envoi({ lastName: "GIBERT IMMOBILIER" }));
controle("(14) partenaire personne : le nom saisi part dans « nom », le métier reste",
  vP.get("nom") === "GIBERT IMMOBILIER" && vP.get("metier") === "5" && !vP.has("sociale"));

// 5. le branchement
controle("(15) updateHektorContactIdentity demande l'interrupteur et exige « sociale » pour une société",
  /hektorContactFormGroup\(formHtml, \{ partenaires: await interrupteurModifPartenaire\(\) \}\)/.test(morceaux.maj)
  && /values\.has\(formulaire\.societe \? "sociale" : "nom"\)/.test(morceaux.maj)
  && /if \(formulaire\.societe\) contact\.contactStatus = "3"/.test(morceaux.maj)
  && /body\.set\("group", formulaire\.group\)/.test(morceaux.maj));
controle("(16) la modification d'un MANDANT n'est pas touchée (pas d'option partenaires)",
  /hektorContactFormGroup\(formHtml\)/.test(morceaux.mandant));
controle("(17) l'interrupteur : une lecture ratée vaut éteint", /catch \(_\) \{\s*return false;/.test(morceaux.interrupteur)
  && /key=eq\.contact_partenaire_modif/.test(morceaux.interrupteur));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTout est vert.");
process.exit(echecs.length ? 1 : 0);
