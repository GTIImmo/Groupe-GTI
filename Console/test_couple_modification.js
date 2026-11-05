// COUPLES (02/11/2026) -- la modification d'une fiche de COUPLE (synthèse couples §26-28).
//
// Le défaut : pour un couple, le formulaire d'édition de Hektor porte group="mefContacts/contactCoupleAll" ;
// le worker ne lisait que « contacts_full_accueil » → « Formulaire edition contact Hektor introuvable ».
// Cet essai extrait les VRAIES fonctions du worker (sans le lancer) et les éprouve sur deux formulaires
// réduits, dont la forme est celle relevée sur 606104 le 02/11.
//     node Console/test_couple_modification.js
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
  maj: tranche("async function updateHektorContactIdentity("),
  mandant: tranche("async function updateHektorMandantContact("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
if (manquants.length) {
  console.log(`⛔ Pièces introuvables dans le worker : ${manquants.join(", ")} -- rien ne serait prouvé.`);
  process.exit(2);
}

const ctx = { URLSearchParams };
vm.createContext(ctx);
vm.runInContext([morceaux.seul, morceaux.couple, morceaux.decode, morceaux.attr, morceaux.extract, morceaux.groupe,
  morceaux.replace, morceaux.tel, morceaux.appliquer,
  "this.api = { hektorContactFormGroup, extractHektorFormValues, applyHektorContactIdentityValues, HEKTOR_GROUPE_CONTACT_SEUL, HEKTOR_GROUPE_CONTACT_COUPLE };"].join("\n"), ctx);
const api = ctx.api;

// La forme relevée sur 606104 (réduite) : tous les champs dans le groupe du couple.
const G = 'group="mefContacts/contactCoupleAll"';
const FORM_COUPLE = `<div id="nom"><input type="text" name="nom" value="ESSAI MODIF" ${G}></div>
<input type="text" name="prenom" value="Un" ${G}><select name="civilite" ${G}><option value="">-</option></select>
<input type="text" name="email[]" value="un@example.com" ${G}><input type="hidden" name="label_email[]" value="email" ${G}>
<input type="text" name="nom_m2" value="ESSAI MODIF" ${G}><input type="text" name="prenom_m2" value="Deux" ${G}>
<input type="text" name="email_m2[]" value="deux@example.com" ${G}><input type="text" name="telephone_m2[]" value="" ${G}>
<span>idContact</span>`;
const S = 'group="mefContacts/contacts_full_accueil"';
const FORM_SEUL = `<input type="text" name="nom" value="DUPONT" ${S}><input type="text" name="prenom" value="Paul" ${S}>
<input type="text" name="email[]" value="p@example.com" ${S}>`;

// 1. le groupe
const gc = api.hektorContactFormGroup(FORM_COUPLE);
const gs = api.hektorContactFormGroup(FORM_SEUL);
controle("(1) un couple est reconnu par son groupe", gc.couple === true && gc.group === "mefContacts/contactCoupleAll", JSON.stringify(gc));
controle("(2) TÉMOIN : une personne seule garde le groupe d'avant, à l'identique", gs.couple === false && gs.group === "mefContacts/contacts_full_accueil", JSON.stringify(gs));
controle("(3) un formulaire vide ou illisible = personne seule (le chemin d'avant)", api.hektorContactFormGroup("").couple === false);

// 2. l'extraction
const vAncien = api.extractHektorFormValues(FORM_COUPLE, "mefContacts/contacts_full_accueil");
controle("(4) PREUVE DU DÉFAUT : avec l'ancien groupe, le couple n'a pas de « nom »", !vAncien.has("nom"));
const vc = api.extractHektorFormValues(FORM_COUPLE, gc.group);
controle("(5) avec son groupe, le couple a nom, prenom, nom_m2, prenom_m2", vc.get("nom") === "ESSAI MODIF" && vc.get("prenom") === "Un" && vc.get("nom_m2") === "ESSAI MODIF" && vc.get("prenom_m2") === "Deux");

// 3. l'écriture du conjoint (statut 2)
const v2 = api.extractHektorFormValues(FORM_COUPLE, gc.group);
api.applyHektorContactIdentityValues(v2, { contactStatus: "2", civility: null, lastName: "ESSAI MODIF", firstName: "Un", spouseLastName: null, spouseFirstName: "DeuxModifie", spouseEmail: null, spousePhone: null, email: null, phone: null, phoneSecondary: null });
controle("(6) le prénom du conjoint est écrit dans le bloc _m2", v2.get("prenom_m2") === "DeuxModifie", v2.get("prenom_m2"));
controle("(7) ce qui n'est pas saisi reste comme Hektor l'a rendu (nom_m2, email_m2, e-mail)", v2.get("nom_m2") === "ESSAI MODIF" && v2.get("email_m2[]") === "deux@example.com" && v2.get("email[]") === "un@example.com");
const v1 = api.extractHektorFormValues(FORM_COUPLE, gc.group);
api.applyHektorContactIdentityValues(v1, { contactStatus: "1", civility: null, lastName: "ESSAI MODIF", firstName: "Un", spouseFirstName: "Ignore", email: null, phone: null, phoneSecondary: null });
controle("(8) TÉMOIN INVERSE : sans le statut 2, le bloc _m2 n'est pas touché (d'où le statut tiré du formulaire relu)", v1.get("prenom_m2") === "Deux");

// 4. le branchement dans les deux portes
controle("(9) updateHektorContactIdentity lit ET renvoie le groupe du formulaire relu",
  /hektorContactFormGroup\(formHtml[,)]/.test(morceaux.maj) && /extractHektorFormValues\(formHtml, formulaire\.group\)/.test(morceaux.maj) && /body\.set\("group", formulaire\.group\)/.test(morceaux.maj));
controle("(10) un couple relu est édité comme un couple (statut 2)", /if \(formulaire\.couple\) contact\.contactStatus = "2"/.test(morceaux.maj));
controle("(11) la modification d'un MANDANT lit et renvoie aussi le groupe relu",
  /extractHektorFormValues\(formHtml, formulaire\.group\)/.test(morceaux.mandant) && /body\.set\("group", formulaire\.group\)/.test(morceaux.mandant));
controle("(12) plus AUCUNE porte n'écrit le groupe « contacts_full_accueil » en dur dans un envoi",
  !/body\.set\("group", "mefContacts\/contacts_full_accueil"\)/.test(src));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTout est vert.");
process.exit(echecs.length ? 1 : 0);
