#!/usr/bin/env node
"use strict";
/**
 * ⑧ NOTAIRE, ÉTAPE 3 — L'ÉCRAN DES NOTAIRES.   28/10/2026
 *
 *   La catégorie « Notaire » EN PREMIER (décision 1 de Frédéric, 27/10), le bleu encre et la balance de la maquette
 *   fiche-notaire-v2, le filtre « Notaire » de l'annuaire (les deux côtés), la recherche globale, et les lignes de biens
 *   de la fiche contact (« Notaire — côté vendeur / acquéreur », avec l'étape du dossier).
 *
 * On EXÉCUTE le code réel : les fonctions sont découpées dans App.tsx, lib/api.ts et RechercheGlobale.tsx, puis jouées
 * par esbuild + vm. TÉMOIN INVERSE : un contact SANS rôle notaire donne exactement le même écran, interrupteur allumé
 * ou éteint. MUTANT : sans la ligne « notaire en premier », le contrôle du rang doit tomber.
 * Données SYNTHÉTIQUES (aucune donnée personnelle).
 *
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_notaire_ecran.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const SRC = path.resolve(__dirname, "src");
const lire = (f) => fs.readFileSync(path.join(SRC, f), "utf8").replace(/\r\n/g, "\n");

function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const finLigne = src.indexOf("\n", i);
  const ligne = src.slice(i, finLigne < 0 ? undefined : finLigne);
  if (/^const \w+ = [^{(]*$/.test(ligne)) return ligne;           // constante sur une ligne
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

const MORCEAUX_APP = ["const TYPE_CONTACT_UNIQUE = ", "const TYPE_NOTAIRE_ECRAN = ", "const FICHE_UN_BIEN_TOUS_ROLES = ",
  "function isBuyerRole(", "function estRoleNotaire(", "const contactDirectoryTypeLabel:", "function contactDirectoryCategories(",
  "function contactToneFromRoles(", "function contactDirectoryRoleLabel(", "function dateDuRole(", "function couleurDuRoleDuBien(",
  "function familleDuRole(", "function etapeAcheteurRetenue(", "function detailEtapeAcheteur(", "function roleNotaireDuBien(",
  "function regrouperRelationsParBien(", "const NOTAIRE_BIENS_MAX = ", "function indicesBiensAffiches("];

function monter(app, api, rg) {
  const code = [];
  for (const m of MORCEAUX_APP) {
    const t = tranche(app, m);
    if (!t) return { erreur: `absent de App.tsx : ${m}` };
    code.push(t);
  }
  const filtre = tranche(api, "function contactRoleFilterValues(");
  if (!filtre) return { erreur: "absent de lib/api.ts : contactRoleFilterValues" };
  code.push(filtre);
  const roles = tranche(rg, "function rolesContact(");
  if (!roles) return { erreur: "absent de RechercheGlobale.tsx : rolesContact" };
  code.push(roles.replace("function rolesContact(", "function rolesContactRG("));
  const js = esbuild.transformSync(code.join("\n\n") + "\nthis.api = { contactDirectoryCategories, contactToneFromRoles, "
    + "contactDirectoryTypeLabel, contactDirectoryRoleLabel, regrouperRelationsParBien, couleurDuRoleDuBien, contactRoleFilterValues, rolesContactRG, indicesBiensAffiches };",
  { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return { api: ctx.api };
}

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log((ok ? "OK    " : "ECHEC ") + nom + (ok ? "" : "  -> " + (detail || "")));
  if (!ok) echecs += 1;
}

// une ligne de la vue des liens (synthétique)
const ligne = (o) => ({ relation_key: o.k, hektor_contact_id: "20000001", hektor_annonce_id: o.a, app_dossier_id: o.d ?? null,
  role_contact: o.r, transaction_type: o.t ?? null, transaction_id: o.id ?? null, transaction_state: o.s ?? null,
  transaction_date: o.date ?? null, transaction_amount: o.m ?? null, origine: null, proprietaire_depuis: null });

const BIEN_VENTE = [
  ligne({ k: "aff_1_9", a: "61001", d: 501, r: "notaire_vendeur", t: "compromis", id: "C1", s: "active", date: "2025-03-02" }),
  ligne({ k: "aff_2_9", a: "61001", d: 501, r: "notaire_vendeur", t: "vente", id: "V1", s: "vente", date: "2025-06-20" }),
];
const BIEN_DEUX_COTES = [
  ligne({ k: "aff_3_9", a: "61002", d: 502, r: "notaire_vendeur", t: "compromis", id: "C2", s: "active", date: "2026-09-01" }),
  ligne({ k: "aff_4_9", a: "61002", d: 502, r: "notaire_acquereur", t: "compromis", id: "C2", s: "active", date: "2026-09-01" }),
];
const BIEN_ANNULE = [
  ligne({ k: "aff_5_9", a: "61003", d: 503, r: "notaire_acquereur", t: "compromis", id: "C3", s: "cancelled", date: "2024-11-15" }),
];
const BIEN_MANDANT_ET_NOTAIRE = [
  ligne({ k: "rel_61004_9", a: "61004", d: 504, r: "mandant" }),
  ligne({ k: "aff_6_9", a: "61004", d: 504, r: "notaire_vendeur", t: "compromis", id: "C4", s: "active", date: "2026-10-01" }),
];
const SANS_NOTAIRE = [
  ligne({ k: "rel_62001_9", a: "62001", d: 601, r: "mandant" }),
  ligne({ k: "aff_7_9", a: "62002", d: 602, r: "acquereur_compromis", t: "compromis", id: "C7", s: "active", date: "2026-02-01", m: "180000" }),
  ligne({ k: "aff_8_9", a: "62002", d: 602, r: "acquereur_vente", t: "vente", id: "V7", s: "vente", date: "2026-05-01", m: "182000" }),
];

const app = lire("App.tsx"), api = lire(path.join("lib", "api.ts")), rg = lire("RechercheGlobale.tsx");
const m = monter(app, api, rg);
if (m.erreur) { console.log("⛔ " + m.erreur); process.exit(2); }
const A = m.api;
const jsonEgal = (x, y) => JSON.stringify(x) === JSON.stringify(y);

// 1. le rang (décision 1)
verifier("un notaire seul est « Notaire »", jsonEgal(A.contactDirectoryCategories(["notaire_vendeur"], 0), ["notaire"]));
verifier("décision 1 : notaire ET mandant -> « Notaire » d'abord, « Mandant » ensuite",
  jsonEgal(A.contactDirectoryCategories(["mandant", "notaire_acquereur"], 0), ["notaire", "mandant"]),
  JSON.stringify(A.contactDirectoryCategories(["mandant", "notaire_acquereur"], 0)));
verifier("témoin : mandant + acheteur + recherche active -> inchangé",
  jsonEgal(A.contactDirectoryCategories(["mandant", "acquereur_vente"], 2), ["mandant", "acheteur", "acquereur"]));
verifier("les anciens rôles « notaire_entree / sortie » ne font pas un notaire (aucun contact ne les porte)",
  jsonEgal(A.contactDirectoryCategories(["notaire_entree"], 0), []));
// 2. le ton du téléphone et de la pastille, le mot
verifier("le téléphone et la pastille : ton « notary » pour un notaire, « mandate » pour un mandant",
  A.contactToneFromRoles(["notaire_vendeur", "mandant"], null) === "notary" && A.contactToneFromRoles(["mandant"], null) === "mandate");
verifier("le mot de la catégorie est « Notaire »", A.contactDirectoryTypeLabel.notaire === "Notaire");
verifier("les rôles en clair : « Notaire — côté vendeur / acquéreur »",
  A.contactDirectoryRoleLabel("notaire_vendeur") === "Notaire — côté vendeur"
  && A.contactDirectoryRoleLabel("notaire_acquereur") === "Notaire — côté acquéreur");

// 3. la fiche contact : une ligne par bien
const biens = A.regrouperRelationsParBien([...BIEN_VENTE, ...BIEN_DEUX_COTES, ...BIEN_ANNULE, ...BIEN_MANDANT_ET_NOTAIRE]);
const r0 = biens[0] && biens[0].roles[0];
verifier("un bien = une ligne (4 biens, 6 lignes de la vue)", biens.length === 4, String(biens.length));
verifier("bien vendu : « Notaire — côté vendeur », la VENTE retenue, en bleu encre",
  r0 && r0.famille === "notaire" && r0.libelle === "Notaire — côté vendeur" && r0.detail === "Vente signée le 20/06/2025"
  && !r0.gris && A.couleurDuRoleDuBien(r0) === "#3b4a8c", JSON.stringify(r0));
verifier("les deux côtés du même dossier : « côtés vendeur et acquéreur », une seule pastille",
  biens[1].roles.length === 1 && biens[1].roles[0].libelle === "Notaire — côtés vendeur et acquéreur", JSON.stringify(biens[1].roles));
verifier("compromis annulé : montré, en gris", biens[2].roles[0].gris === true
  && biens[2].roles[0].detail === "Compromis annulé (du 15/11/2024)", JSON.stringify(biens[2].roles[0]));
verifier("décision 1 sur la ligne : la pastille notaire AVANT la pastille mandant",
  jsonEgal(biens[3].roles.map((r) => r.famille), ["notaire", "mandant"]), JSON.stringify(biens[3].roles.map((r) => r.famille)));
const melange = A.regrouperRelationsParBien([...BIEN_VENTE].reverse());
verifier("le résultat ne dépend pas de l'ordre reçu", jsonEgal(melange[0].roles, biens[0].roles));

// 4. TÉMOIN INVERSE : sans notaire, l'écran est le même, interrupteur allumé ou éteint
const eteint = monter(app.replace("const TYPE_NOTAIRE_ECRAN = true", "const TYPE_NOTAIRE_ECRAN = false"), api, rg).api;
verifier("TÉMOIN INVERSE : un contact sans notaire -> mêmes lignes et même catégorie, allumé comme éteint",
  jsonEgal(A.regrouperRelationsParBien(SANS_NOTAIRE), eteint.regrouperRelationsParBien(SANS_NOTAIRE))
  && jsonEgal(A.contactDirectoryCategories(["mandant", "acquereur_vente"], 1), eteint.contactDirectoryCategories(["mandant", "acquereur_vente"], 1)));
verifier("éteint : un notaire n'a plus de catégorie (l'écran d'avant)", jsonEgal(eteint.contactDirectoryCategories(["notaire_vendeur"], 0), []));

// 5. le filtre et la recherche globale
verifier("le filtre « Notaire » vise les deux côtés", jsonEgal(A.contactRoleFilterValues("notaire"), ["notaire_vendeur", "notaire_acquereur"]));
verifier("témoin : le filtre « Acheteur » est inchangé",
  jsonEgal(A.contactRoleFilterValues("acquereur"), ["acquereur", "acquereur_offre", "acquereur_compromis", "acquereur_vente"]));
verifier("la recherche globale dit « Notaire · Mandant »",
  A.rolesContactRG({ relation_roles_json: ["mandant", "notaire_vendeur"], active_search_count: 0 }) === "Notaire · Mandant",
  A.rolesContactRG({ relation_roles_json: ["mandant", "notaire_vendeur"], active_search_count: 0 }));

// 6. les deux menus, la balance, les styles
const menus = (app.match(/\[\{ value: 'notaire', label: 'Notaire' \}\]/g) || []).length;
verifier("les DEUX menus du filtre proposent « Notaire »", menus === 2, String(menus));
// 28/10 : l'annuaire affiché n'utilise pas ces menus mais une rangée de pastilles (vu à l'écran après la pose)
verifier("la rangée de pastilles de l'annuaire a « Notaires », qui choisit le même filtre",
  /selectRole\('notaire'\) \}\}><span className="dot" style=\{\{ background: '#3b4a8c' \}\} \/><span>Notaires<\/span>/.test(app));
verifier("la balance est dans l'avatar de la fiche (fa-cx-ty-notaire) et dans l'annuaire", /fa-cx-ty-ic fa-cx-ty-notaire/.test(app)
  && /cat === 'notaire'\) \{\n\s*\/\/ la balance/.test(app));
const cssAnn = lire("annuaire-contacts-v2.css"), cssFiche = lire("contact-detail-v2.css");
verifier("les styles : avatar, mot et statut de l'annuaire ; couleur, balance et lignes de la fiche",
  /\.ci-av\.notaire\{/.test(cssAnn) && /\.ci-role\.notaire\{/.test(cssAnn) && /\.st-pill\.notaire\{/.test(cssAnn)
  && /\.ty-notaire \{ --ty: #3b4a8c/.test(cssFiche) && /\.ty-notaire \.fa-cx-av \.fa-cx-ty-notaire/.test(cssFiche)
  && /\.fa-cx-lk\.r-notaire \{ --rc: #3b4a8c; \}/.test(cssFiche));

// 7. DÉCISION 2 (28/10, « A ») : au-delà de 10 biens, les 10 plus récents et « Tout afficher »
// 15 biens : le k-ième a sa transaction le 2026-01-(k+1) ; deux lignes par bien (compromis + vente), mélangées ; un bien sans date
const QUINZE = [];
for (let k = 0; k < 15; k++) {
  const jour = String(k + 1).padStart(2, "0");
  QUINZE.push(ligne({ k: `c${k}`, a: String(63000 + k), d: 700 + k, r: "notaire_vendeur", t: "compromis", id: `C${k}`, s: "active", date: `2025-12-${jour}` }));
  if (k !== 3) QUINZE.push(ligne({ k: `v${k}`, a: String(63000 + k), d: 700 + k, r: "notaire_vendeur", t: "vente", id: `V${k}`, s: "vente", date: `2026-01-${jour}` }));
}
const QUINZE_MELE = [...QUINZE.filter((_, i) => i % 2), ...QUINZE.filter((_, i) => !(i % 2))];
const nb = A.regrouperRelationsParBien(QUINZE_MELE).length;
const dix = A.indicesBiensAffiches(QUINZE_MELE, nb, true, false);
const regroupes = A.regrouperRelationsParBien(QUINZE_MELE);
const annoncesMontrees = dix.map((i) => regroupes[i].relation.hektor_annonce_id);
const attendues = [14, 13, 12, 11, 10, 9, 8, 7, 6, 5].map((k) => String(63000 + k));
verifier("un notaire à 15 biens : les 10 plus récents, du plus récent au plus ancien, sur LE BON bien (numéros alignés)",
  dix.length === 10 && jsonEgal(annoncesMontrees, attendues), JSON.stringify(annoncesMontrees));
verifier("« Tout afficher » : les 15, toujours du plus récent au plus ancien",
  A.indicesBiensAffiches(QUINZE_MELE, nb, true, true).length === 15
  && regroupes[A.indicesBiensAffiches(QUINZE_MELE, nb, true, true)[0]].relation.hektor_annonce_id === "63014");
verifier("témoin : un contact qui n'est pas notaire, 15 biens -> tous, dans l'ordre d'avant",
  jsonEgal(A.indicesBiensAffiches(QUINZE_MELE, nb, false, false), [...Array(15).keys()]));
verifier("témoin : un notaire à 10 biens et moins -> tous, dans l'ordre d'avant",
  jsonEgal(A.indicesBiensAffiches(QUINZE_MELE.slice(0, 4), 2, true, false), [0, 1]));
const boucles = (app.match(/indicesBiens\.map\(\(indexBien\) => \{\n\s*const ligneVue = linkedRelations\[indexBien\]/g) || []).length;
const boutons = (app.match(/onClick=\{\(\) => setTousLesBiens\(true\)\}>Tout afficher/g) || []).length;
verifier("les DEUX fiches (V1 et V2) parcourent les biens choisis et ont le bouton « Tout afficher »",
  boucles === 2 && boutons === 2 && /\.fa-cx-lk-more \{/.test(cssFiche), `boucles ${boucles}, boutons ${boutons}`);
const mutantDix = monter(app.replace("return toutAfficher ? tries : tries.slice(0, NOTAIRE_BIENS_MAX)", "return tries"), api, rg);
verifier("MUTANT (sans la limite de 10) : attrapé",
  !mutantDix.erreur && mutantDix.api.indicesBiensAffiches(QUINZE_MELE, nb, true, false).length !== 10);

// 8. MUTANT : sans « notaire en premier »
const mutant = monter(app.replace(/\n  if \(TYPE_NOTAIRE_ECRAN && roles\.some\(estRoleNotaire\)\) out\.push\('notaire'\)[^\n]*/, ""), api, rg);
verifier("MUTANT (sans la ligne « Notaire en premier ») : le rang tombe -> attrapé",
  !mutant.erreur && !jsonEgal(mutant.api.contactDirectoryCategories(["mandant", "notaire_acquereur"], 0), ["notaire", "mandant"]));

console.log(echecs ? `\n${echecs} contrôle(s) en échec` : "\ntout vert");
process.exit(echecs ? 1 : 0);
