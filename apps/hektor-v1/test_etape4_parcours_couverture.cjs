#!/usr/bin/env node
"use strict";
/**
 * ÉTAPE 4, CHAPITRE 6 — P1 : LA COUVERTURE DU PARCOURS GUIDÉ (note ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT, §88 et §93).  19/11/2026
 *
 * Le §88 a prouvé, avec un programme de travail, que les 19 questions nomment TOUTES les cases que la fenêtre
 * « Nouvelle annonce » montre, pour chaque type de bien. Cet essai VERSE cette preuve au dépôt et la REJOUE sur les
 * données du moteur du serveur (backend/app/services/parcours_creation.json), contre le CODE RÉEL d'App.tsx
 * (esbuild + vm) : les groupes de la fenêtre, leurs cases par profil, les cases du haut de l'étape 3, et le profil de
 * chaque type de bien. Rien n'est recopié à la main : si la fenêtre gagne une case, cet essai la voit.
 *
 * Il exige :
 *   ① pour chaque profil (maison, appartement, terrain, garage, immeuble, autre) : 0 case montrée oubliée ;
 *   ② chaque case nommée par une question existe dans la fenêtre (ou est une case déclarée hors des groupes) ;
 *   ③ chaque question posée pour un profil y montre au moins une case (pas de question vide) ;
 *   ④ le profil de chaque type de bien, dans les données du serveur, est celui que calcule la fenêtre ;
 *   ⑤ la condition « piscine » du serveur est celle de la fenêtre (showIf PISCINE- = OUI) ;
 *   ⑥ les clés hors des groupes : chaque case de la liste déclarée a sa question ; aucune coordonnée de mandant
 *      (e-mail, téléphone…) n'est une case de réponse (elles vivent à part, règle du 18/11) ;
 *   ⑦ TÉMOIN INVERSE : retirer une case d'une question fait apparaître un oubli (l'essai sait voir rouge).
 *
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_etape4_parcours_couverture.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");
const DONNEES = path.resolve(__dirname, "..", "..", "backend", "app", "services", "parcours_creation.json");
const PROFILS = ["house", "apartment", "land", "garage", "building", "other"];

// Les cases de la fenêtre qui vivent HORS des groupes (états à part dans App.tsx), dans la langue du parcours.
// La liste vient du §88 (29 cases hors des groupes) ; chacune doit avoir sa question.
const HORS_GROUPES = {
  agence: "agence", negociateur: "négociateur", type: "famille et type de bien", offre_famille: "vente ordinaire / immo pro",
  sous_type: "sous-type (immobilier professionnel)", adresse_haut: "adresse", cp: "code postal", ville: "ville",
  mandant_choix: "choix du mandant", mandant: "mandant existant", note: "note interne", composition: "composition (7 cases par pièce)",
  photos: "photos (fichiers, visible / masquée)",
};
// Les coordonnées d'un NOUVEAU mandant ne sont JAMAIS des cases de réponse (schéma assistant_prive, P3).
const COORDONNEES = ["civilite", "nom", "prenom", "email", "telephone", "mandant_email", "mandant_telephone"];

function ligneDe(s, debut) {
  const i = s.indexOf(debut);
  return i < 0 ? null : i;
}
function tranche(s, debut, fin) {
  const i = ligneDe(s, debut);
  if (i === null) return null;
  const f = s.indexOf(fin, i);
  return f < 0 ? null : s.slice(i, f + fin.length);
}

// de `debut` jusqu'à la première `fin` qui suit `repere` (pour couper un tableau après ceux qui le précèdent)
function jusquApres(s, debut, repere, fin) {
  const i = ligneDe(s, debut);
  const r = s.indexOf(repere, i === null ? 0 : i);
  if (i === null || r < 0) return null;
  const f = s.indexOf(fin, r);
  return f < 0 ? null : s.slice(i, f + fin.length);
}

function monter(src) {
  const s = src.replace(/\r\n/g, "\n");
  const morceaux = [
    "type HektorPropertyProfileKind = 'apartment' | 'house' | 'land' | 'garage' | 'building' | 'other'",
    tranche(s, "type HektorSelectOption =", "}\n"),
    tranche(s, "function normalizeDraftAnnonceScanText(", "\n}\n"),
    // les familles et types de bien, et le profil de chaque type
    tranche(s, "type DraftAnnoncePropertyGroupId =", "\nfunction draftAnnonceTypeProfile(id: string): DraftAnnonceTypeProfile {"),
    "  return draftAnnonceTypeProfileFromKind(draftAnnoncePropertyProfileKindForTypeId(id))\n}",
    // les cases de la fenêtre (types, options, wf, puis les groupes jusqu'à leur « ] » de fin)
    jusquApres(s, "type DraftAnnonceWizardField = {", "const draftAnnonceWizardGroups: DraftAnnonceWizardGroup[] = [", "\n]\n"),
    tranche(s, "const draftAnnonceWizardCommonFieldsByStep:", "\n}\n"),
    tranche(s, "const draftAnnonceWizardFieldsByProfile:", "\n}\n"),
    tranche(s, "function isDraftAnnonceWizardFieldVisibleForProfile(", "\n}\n"),
  ];
  const haut = tranche(s, "const draftAnnonceNomsAuHaut = new Set<string>([", "\n  ])");
  if (morceaux.some((m) => !m) || !haut) return { erreur: "un morceau est absent d'App.tsx" };
  const code = morceaux.join("\n\n") + `
function nomsAuHaut(draftAnnonceTypeRules) {
  ${haut.trim()}
  return draftAnnonceNomsAuHaut
}
this.api = { draftAnnonceWizardGroups, draftAnnoncePropertyTypes, draftAnnoncePropertyProfileKindForTypeId,
  draftAnnonceTypeProfileFromKind, isDraftAnnonceWizardFieldVisibleForProfile, nomsAuHaut };`;
  // Les groupes citent des listes d'options définies AILLEURS dans App.tsx : chaque nom manquant est cherché dans le
  // vrai fichier (sa déclaration au premier niveau) et ajouté en tête, jusqu'à ce que le code s'exécute.
  const ajoutees = [];
  for (let tour = 0; tour < 40; tour++) {
    const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp, Math, Date };
    vm.createContext(ctx);
    try {
      vm.runInContext(esbuild.transformSync(ajoutees.join("\n\n") + "\n\n" + code, { loader: "ts" }).code, ctx);
      return { api: ctx.api, dependances: ajoutees.length };
    } catch (e) {
      const m = /^(\w+) is not defined/.exec(e.message);
      const decl = m && declarationDe(s, m[1]);
      if (!decl) return { erreur: "le code découpé ne s'exécute pas : " + e.message };
      ajoutees.unshift(decl);
    }
  }
  return { erreur: "trop de dépendances" };
}

// La déclaration de premier niveau de `nom` : de sa ligne jusqu'avant la déclaration suivante (ligne en colonne 0).
function declarationDe(s, nom) {
  const re = new RegExp(`^(?:export )?(?:const|let|function|type) ${nom}\\b`, "m");
  const m = re.exec(s);
  if (!m) return null;
  const lignes = s.slice(m.index).split("\n");
  const garde = [lignes[0]];
  for (const l of lignes.slice(1)) {
    if (/^[A-Za-z/]/.test(l)) break;
    garde.push(l);
  }
  return garde.join("\n").trimEnd();
}

// Les cases que la fenêtre MONTRE pour un profil (même calcul que la modale : visibles pour le profil, plus le haut).
function montrees(api, profil) {
  const regles = api.draftAnnonceTypeProfileFromKind(profil);
  const haut = api.nomsAuHaut(regles);
  const noms = new Set(haut);
  for (const groupe of api.draftAnnonceWizardGroups) {
    for (const champ of groupe.fields) {
      if (!api.isDraftAnnonceWizardFieldVisibleForProfile(profil, groupe.step, champ.name)) continue;
      // même règle que la modale : à l'étape 7, le prix net vendeur est retiré (il vit en « Mandat / Prix »)
      if (groupe.step === 7 && champ.name === "PRIXNETVENDEUR") continue;
      noms.add(champ.name);
    }
  }
  return noms;
}

function questionsPour(donnees, profil) {
  return donnees.questions.filter((q) => !q.profils || q.profils.includes(profil));
}

function oublis(api, donnees, profil) {
  const couvert = new Set(questionsPour(donnees, profil).flatMap((q) => q.champs));
  for (const c of donnees.auto) couvert.add(c);
  for (const c of Object.keys(donnees.a_la_main)) couvert.add(c);
  return [...montrees(api, profil)].filter((c) => !couvert.has(c)).sort();
}

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log(`${ok ? "OK   " : "ECHEC"} ${nom}${ok ? "" : "  -> " + detail}`);
  if (!ok) echecs++;
}

let src, donnees;
try {
  src = fs.readFileSync(APP, "utf8");
  donnees = JSON.parse(fs.readFileSync(DONNEES, "utf8"));
} catch (e) {
  console.log("IMPOSSIBLE de lire App.tsx ou les données du parcours : " + e.message);
  process.exit(2);
}
const monte = monter(src);
if (monte.erreur) { console.log("IMPOSSIBLE de monter le code : " + monte.erreur); process.exit(2); }
const api = monte.api;
const toutesLesCases = new Set(api.draftAnnonceWizardGroups.flatMap((g) => g.fields.map((f) => f.name)));
if (toutesLesCases.size < 150) { console.log(`IMPOSSIBLE : seulement ${toutesLesCases.size} cases lues dans la fenêtre`); process.exit(2); }

// ① 0 oubli par profil (avec le compte montré, témoin que la lecture a porté)
for (const profil of PROFILS) {
  const o = oublis(api, donnees, profil);
  verifier(`① ${profil} : ${montrees(api, profil).size} cases montrées, 0 oubliée`, o.length === 0, o.join(", "));
}

// ② chaque case nommée existe
const connues = new Set([...toutesLesCases, ...Object.keys(HORS_GROUPES)]);
const inconnues = donnees.questions.flatMap((q) => q.champs.filter((c) => !connues.has(c)).map((c) => `${q.id}.${c}`));
verifier("② chaque case nommée par une question existe dans la fenêtre", inconnues.length === 0, inconnues.join(", "));
const declarees = [...donnees.auto, ...Object.keys(donnees.a_la_main)].filter((c) => !toutesLesCases.has(c));
verifier("② les cases automatiques et laissées à la main existent", declarees.length === 0, declarees.join(", "));

// ③ aucune question vide pour un profil où elle est posée
const vides = [];
for (const profil of PROFILS) {
  const vues = montrees(api, profil);
  for (const q of questionsPour(donnees, profil)) {
    if (!q.champs.some((c) => vues.has(c) || c in HORS_GROUPES)) vides.push(`${q.id}/${profil}`);
  }
}
verifier("③ aucune question posée sans une case montrée", vides.length === 0, vides.join(", "));

// ④ le profil de chaque type
const types = api.draftAnnoncePropertyTypes.map((t) => t.id);
const faux = types.filter((id) => donnees.profil_par_type[id] !== api.draftAnnoncePropertyProfileKindForTypeId(id));
const enTrop = Object.keys(donnees.profil_par_type).filter((id) => !types.includes(id));
verifier(`④ le profil des ${types.length} types de bien est celui de la fenêtre`, faux.length === 0 && enTrop.length === 0,
  `faux : ${faux.map((id) => `${id}=${donnees.profil_par_type[id]} au lieu de ${api.draftAnnoncePropertyProfileKindForTypeId(id)}`).join(", ")} ; en trop : ${enTrop.join(", ")}`);

// ⑤ la condition piscine
const piscine = donnees.questions.find((q) => q.id === "piscine");
const showIfPiscine = new Set(api.draftAnnonceWizardGroups.flatMap((g) => g.fields)
  .filter((f) => f.showIf).map((f) => `${f.showIf.field}=${f.showIf.value}`));
verifier("⑤ la question « piscine » suit la condition de la fenêtre (PISCINE- = OUI)",
  piscine && piscine.si && `${piscine.si.champ}=${piscine.si.vaut}` === "PISCINE-=OUI" && showIfPiscine.has("PISCINE-=OUI")
  && showIfPiscine.size === 1, JSON.stringify(piscine && piscine.si) + " / fenêtre : " + [...showIfPiscine].join(", "));

// ⑥ les cases hors des groupes, et aucune coordonnée
const nommees = new Set(donnees.questions.flatMap((q) => q.champs));
const horsSansQuestion = Object.keys(HORS_GROUPES).filter((c) => !nommees.has(c));
verifier(`⑥ les ${Object.keys(HORS_GROUPES).length} cases hors des groupes ont leur question`, horsSansQuestion.length === 0, horsSansQuestion.join(", "));
const coord = [...nommees].filter((c) => COORDONNEES.includes(c));
verifier("⑥ aucune coordonnée de mandant n'est une case de réponse", coord.length === 0, coord.join(", "));
const doublons = [...nommees].filter((c) => donnees.questions.filter((q) => q.champs.includes(c)).length > 1);
verifier("⑥ aucune case n'est posée par deux questions", doublons.length === 0, doublons.join(", "));

// ⑧ le type par défaut (avant que le type soit dit, la fenêtre part sur lui) et les clés d'une pièce de composition
const defaut = /const \[draftAnnonceTypeId, setDraftAnnonceTypeId\] = useState\('(\w+)'\)/.exec(src);
verifier(`⑧ le type par défaut du serveur (${donnees.type_par_defaut}) est celui de la fenêtre`,
  defaut && defaut[1] === donnees.type_par_defaut, defaut ? defaut[1] : "introuvable");
const typePiece = tranche(src.replace(/\r\n/g, "\n"), "type HektorCompositionPieceDraft = {", "\n}\n") || "";
const clesFenetre = new Set([...typePiece.matchAll(/^\s+(\w+)\??:/gm)].map((m) => m[1]));
const clesEnTrop = donnees.cles_piece.filter((c) => !clesFenetre.has(c));
verifier(`⑧ les ${donnees.cles_piece.length} clés d'une pièce existent dans la fenêtre (${clesFenetre.size} lues)`,
  clesFenetre.size >= 10 && clesEnTrop.length === 0, clesEnTrop.join(", "));

// ⑦ témoin inverse : on retire une case de la question « intérieur » -> la maison doit avoir un oubli
const ampute = JSON.parse(JSON.stringify(donnees));
const interieur = ampute.questions.find((q) => q.id === "interieur");
interieur.champs = interieur.champs.filter((c) => c !== "CUISINE_EQUIPEMENT");
const vu = oublis(api, ampute, "house");
verifier("⑦ témoin inverse : sans « CUISINE_EQUIPEMENT », la maison a 1 oubli", vu.length === 1 && vu[0] === "CUISINE_EQUIPEMENT", vu.join(", "));

console.log(echecs ? `\n${echecs} contrôle(s) en ÉCHEC` : "\nTOUT EST VERT");
process.exit(echecs ? 1 : 0);
