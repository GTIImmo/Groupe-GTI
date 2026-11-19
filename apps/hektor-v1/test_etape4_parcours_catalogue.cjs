/*
 * Étape 4 chap. 6, P2 (19/11/2026) — LE CATALOGUE DU PARCOURS GUIDÉ PARLE COMME LA FENÊTRE.
 *
 * Les boutons de l'assistant (ParcoursGuide.tsx) montrent les cases et les listes que leur donne
 * `catalogueParcoursFenetre` (App.tsx). Cette fonction RECOPIE la règle des cases du haut de la fenêtre
 * (`draftAnnonceNomsAuHaut`, dans le composant). Cet essai exécute le VRAI code d'App.tsx (esbuild + vm, comme
 * test_etape4_parcours_couverture.cjs) et exige :
 *   ① profil par profil, le catalogue montre EXACTEMENT les cases que la fenêtre montre (ni une de plus, ni une de moins) ;
 *   ② chaque case des 19 questions (backend/app/services/parcours_creation.json), montrée pour ce profil, a son libellé,
 *      et une liste a au moins un choix ;
 *   ③ une liste du catalogue EST celle de la fenêtre (même objet : une seule source) ;
 *   ④ les cases hors des groupes : les 29 types, le sous-type seulement pour l'immobilier professionnel, pas de
 *      négociateur à choisir pour un commercial ;
 *   ⑤ l'ouverture de la fenêtre (assistantOuvrirParcours) range chaque case hors des groupes ;
 *   ⑥ les coordonnées d'un nouveau mandant ne rejoignent JAMAIS la réponse envoyée au serveur de l'assistant ;
 *   ⑦ témoin inverse : un catalogue qui oublie « CUISINE_EQUIPEMENT » est attrapé.
 * Sorties : 0 vert · 1 un rouge · 2 pas pu mesurer.
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const APP = path.join(__dirname, "src", "App.tsx");
const GUIDE = path.join(__dirname, "src", "ParcoursGuide.tsx");
const DONNEES = path.join(__dirname, "..", "..", "backend", "app", "services", "parcours_creation.json");
const PROFILS = ["house", "apartment", "land", "garage", "building", "other"];
const HORS = ["type", "offre_famille", "sous_type", "agence", "negociateur", "adresse_haut", "cp", "ville", "note"];

function tranche(s, debut, fin) {
  const i = s.indexOf(debut);
  if (i < 0) return null;
  const f = s.indexOf(fin, i);
  return f < 0 ? null : s.slice(i, f + fin.length);
}
function jusquApres(s, debut, repere, fin) {
  const i = s.indexOf(debut);
  const r = s.indexOf(repere, i < 0 ? 0 : i);
  if (i < 0 || r < 0) return null;
  const f = s.indexOf(fin, r);
  return f < 0 ? null : s.slice(i, f + fin.length);
}
function declarationDe(s, nom) {
  const m = new RegExp(`^(?:export )?(?:const|let|function|type) ${nom}\\b`, "m").exec(s);
  if (!m) return null;
  const lignes = s.slice(m.index).split("\n");
  const garde = [lignes[0]];
  for (const l of lignes.slice(1)) {
    if (/^[A-Za-z/]/.test(l)) break;
    garde.push(l);
  }
  return garde.join("\n").trimEnd();
}

function monter(s, retouche) {
  const morceaux = [
    "type HektorPropertyProfileKind = 'apartment' | 'house' | 'land' | 'garage' | 'building' | 'other'",
    tranche(s, "type HektorSelectOption =", "}\n"),
    tranche(s, "function normalizeDraftAnnonceScanText(", "\n}\n"),
    tranche(s, "type DraftAnnoncePropertyGroupId =", "\nfunction draftAnnonceTypeProfile(id: string): DraftAnnonceTypeProfile {"),
    "  return draftAnnonceTypeProfileFromKind(draftAnnoncePropertyProfileKindForTypeId(id))\n}",
    jusquApres(s, "type DraftAnnonceWizardField = {", "const draftAnnonceWizardGroups: DraftAnnonceWizardGroup[] = [", "\n]\n"),
    tranche(s, "const draftAnnonceWizardCommonFieldsByStep:", "\n}\n"),
    tranche(s, "const draftAnnonceWizardFieldsByProfile:", "\n}\n"),
    tranche(s, "function isDraftAnnonceWizardFieldVisibleForProfile(", "\n}\n"),
    retouche(tranche(s, "function catalogueParcoursFenetre(", "\n}\n")),
  ];
  const haut = tranche(s, "const draftAnnonceNomsAuHaut = new Set<string>([", "\n  ])");
  if (morceaux.some((m) => !m) || !haut) return { erreur: "un morceau est absent d'App.tsx" };
  const code = morceaux.join("\n\n") + `
function nomsAuHaut(draftAnnonceTypeRules) {
  ${haut.trim()}
  return draftAnnonceNomsAuHaut
}
// un appel au chargement : les noms qu'elle lit à l'appel sont trouvés par le résolveur ci-dessous
catalogueParcoursFenetre('house', { agences: [], negociateurs: [], commercial: false, syndicCran: false });
this.api = { draftAnnonceWizardGroups, draftAnnonceTypeProfileFromKind, isDraftAnnonceWizardFieldVisibleForProfile, nomsAuHaut,
  catalogueParcoursFenetre };`;
  const ajoutees = [];
  for (let tour = 0; tour < 40; tour++) {
    const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp, Math, Date };
    vm.createContext(ctx);
    try {
      vm.runInContext(esbuild.transformSync(ajoutees.join("\n\n") + "\n\n" + code, { loader: "ts" }).code, ctx);
      return { api: ctx.api };
    } catch (e) {
      const m = /^(\w+) is not defined/.exec(e.message);
      const decl = m && declarationDe(s, m[1]);
      if (!decl) return { erreur: "le code découpé ne s'exécute pas : " + e.message };
      ajoutees.unshift(decl);
    }
  }
  return { erreur: "trop de dépendances" };
}

// les cases que la FENÊTRE montre pour un profil (le calcul de la modale : le haut, puis les groupes visibles)
function montrees(api, profil) {
  const haut = api.nomsAuHaut(api.draftAnnonceTypeProfileFromKind(profil));
  const noms = new Set(haut);
  for (const g of api.draftAnnonceWizardGroups) {
    for (const f of g.fields) {
      if (haut.has(f.name)) continue;
      if (!api.isDraftAnnonceWizardFieldVisibleForProfile(profil, g.step, f.name)) continue;
      if (g.step === 7 && f.name === "PRIXNETVENDEUR") continue;
      noms.add(f.name);
    }
  }
  return noms;
}

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log(`${ok ? "OK   " : "ECHEC"} ${nom}${ok ? "" : "  -> " + detail}`);
  if (!ok) echecs++;
}

let src, guide, donnees;
try {
  src = fs.readFileSync(APP, "utf8").replace(/\r\n/g, "\n");
  guide = fs.readFileSync(GUIDE, "utf8").replace(/\r\n/g, "\n");
  donnees = JSON.parse(fs.readFileSync(DONNEES, "utf8"));
} catch (e) {
  console.log("IMPOSSIBLE de lire les fichiers : " + e.message);
  process.exit(2);
}
const monte = monter(src, (m) => m);
if (monte.erreur) { console.log("IMPOSSIBLE de monter le code : " + monte.erreur); process.exit(2); }
const api = monte.api;
const autour = { agences: ["GTI Firminy"], negociateurs: [{ idUser: "7", label: "Paul", agenceNom: "GTI Firminy" }], commercial: false, syndicCran: false };

function ecarts(apiX, profil) {
  const cat = apiX.catalogueParcoursFenetre(profil, autour);
  const dansCat = new Set(Object.keys(cat.cases).filter((c) => !HORS.includes(c)));
  const fen = montrees(apiX, profil);
  return { manque: [...fen].filter((c) => !dansCat.has(c)), deTrop: [...dansCat].filter((c) => !fen.has(c)), taille: fen.size };
}

// ① exactement les cases de la fenêtre
for (const profil of PROFILS) {
  const e = ecarts(api, profil);
  verifier(`① ${profil} : le catalogue montre les ${e.taille} cases de la fenêtre, ni plus ni moins`, !e.manque.length && !e.deTrop.length,
    `manquent ${e.manque.join(", ") || "-"} ; de trop ${e.deTrop.join(", ") || "-"}`);
}

// ② chaque case montrée des 19 questions a son libellé (et une liste, un choix)
for (const profil of PROFILS) {
  const cat = api.catalogueParcoursFenetre(profil, autour);
  const fen = montrees(api, profil);
  const sans = [];
  for (const q of donnees.questions) {
    if (q.profils && !q.profils.includes(profil)) continue;
    for (const c of q.champs) {
      if (!fen.has(c) && !HORS.includes(c)) continue;
      const d = cat.cases[c];
      if (!d || !String(d.libelle || "").trim()) sans.push(`${q.id}/${c}`);
      else if (d.genre === "liste" && !(d.options || []).some((o) => o.value !== "")) sans.push(`${q.id}/${c} (liste vide)`);
    }
  }
  verifier(`② ${profil} : chaque case montrée des 19 questions a son libellé et sa liste`, !sans.length, sans.join(", "));
}

// ③ une seule source : la liste du catalogue EST celle de la fenêtre
const expo = api.draftAnnonceWizardGroups.flatMap((g) => g.fields).find((f) => f.name === "EXPOSITION");
verifier("③ la liste « Exposition » du catalogue est l'objet même de la fenêtre",
  !!expo && api.catalogueParcoursFenetre("house", autour).cases.EXPOSITION.options === expo.options, "copie ou absente");

// ④ les cases hors des groupes
const maison = api.catalogueParcoursFenetre("house", autour);
verifier("④ le type de bien propose au moins 29 types", (maison.cases.type.options || []).length >= 29, String((maison.cases.type.options || []).length));
verifier("④ le sous-type n'apparaît que pour l'immobilier professionnel", maison.cases.sous_type.si && maison.cases.sous_type.si.nom === "offre_famille", JSON.stringify(maison.cases.sous_type.si));
verifier("④ un commercial n'a pas de négociateur à choisir (c'est lui)",
  !api.catalogueParcoursFenetre("house", { ...autour, commercial: true }).cases.negociateur && !!maison.cases.negociateur, "négociateur présent pour un commercial");
verifier("④ les 32 types de pièce de la fenêtre", maison.typesPiece.length >= 30, String(maison.typesPiece.length));

// ⑤ l'ouverture de la fenêtre range chaque case hors des groupes
const ouvrir = (() => {
  const i = src.indexOf("async function assistantOuvrirParcours(");
  const f = src.indexOf("\n  }\n", i);
  return i < 0 || f < 0 ? "" : src.slice(i, f);
})();
const absentes = [...HORS, "composition", "mandant_choix", "mandant"].filter((c) => !ouvrir.includes(`'${c}'`) && !ouvrir.includes(`r.${c}`));
verifier("⑤ assistantOuvrirParcours range chaque case hors des groupes (et pose les autres par leur nom)",
  !!ouvrir && !absentes.length && ouvrir.includes("nomsFenetre.has(cle)"), absentes.join(", ") || "fonction introuvable");
verifier("⑤ les coordonnées sont PRISES au coffre (prendre = effacer), jamais lues ailleurs", ouvrir.includes("prendreCoordonneesMandant(vue.id)"), "absent");

// ⑥ les coordonnées ne partent jamais au serveur de l'assistant
const envoi = (() => {
  const i = guide.indexOf("const envoyer = async");
  const f = guide.indexOf("repondreParcours(vue.id", i);
  return i < 0 || f < 0 ? "" : guide.slice(i, f + 60);
})();
// corps = …, corps.email = …, corps['email'] = … : aucune affectation de la réponse ne lit les coordonnées
// (éprouvé le 19/11 sur un écran volontairement faux : `corps.email = coordonnees.email` est attrapé)
const fuite = /corps(\.\w+|\[[^\]]*\])?\s*=\s*[^;\n]*coordonnees|repondreParcours\([^)]*coordonnees/.test(envoi);
verifier("⑥ la réponse envoyée au serveur ne prend jamais les coordonnées (elles vont au coffre seul)",
  !!envoi && !fuite && envoi.includes("deposerCoordonneesMandant(vue.id, coordonnees)"), envoi ? "une coordonnée rejoint la réponse" : "envoi introuvable");
verifier("⑥ les coordonnées vivent dans un état À PART de `valeurs`", /useState<CoordonneesMandant>\(\{\}\)/.test(guide) && !/setValeur\('(email|telephone|nom|prenom)'/.test(guide), "mélangées aux valeurs");

// ⑦ témoin inverse : un catalogue qui oublie une case des groupes est attrapé (« nbpieces » ne servirait pas de témoin :
//   la fenêtre le montre AUSSI par ses groupes, le retirer du haut ne change rien -- vérifié le 19/11)
const temoin = monter(src, (m) => m.replace("if (!montre) continue", "if (!montre || f.name === 'CUISINE_EQUIPEMENT') continue"));
if (temoin.erreur) { console.log("IMPOSSIBLE de monter le témoin : " + temoin.erreur); process.exit(2); }
const et = ecarts(temoin.api, "house");
verifier("⑦ témoin inverse : sans « CUISINE_EQUIPEMENT », la maison a 1 case manquante", et.manque.length === 1 && et.manque[0] === "CUISINE_EQUIPEMENT", JSON.stringify(et));

console.log(echecs ? `\n${echecs} ROUGE(S)` : "\nTOUT EST VERT");
process.exit(echecs ? 1 : 0);
