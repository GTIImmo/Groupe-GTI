/*
 * Étape 4 chap. 6, P4-a (19/11/2026) — LA TABLE DE TRADUCTION « cases du scan » -> « cases de la fenêtre », PRODUITE
 * PAR LE VRAI CODE DE LA FENÊTRE.
 *
 * Le parcours guidé démarre rempli de ce que la personne a dit (lu par l'IA dans les clés du SCAN). Le serveur traduit
 * ces clés dans la langue de la FENÊTRE (décision « A » du 19/11 : la traduction vit côté serveur). Pour ne RIEN
 * recopier à la main, ce script exécute App.tsx (esbuild + vm, comme test_etape4_parcours_couverture.cjs) et écrit
 * backend/app/services/parcours_traduction.json :
 *   - les tables du remplisseur du scan (SCAN_MIROIR, SCAN_CASES_DIRECTES, scanWizardFieldMap avec leurs listes) ;
 *   - les listes que le remplisseur résout (exposition, cuisine, états, types de bien, types de pièce) et les synonymes
 *     du type de bien ;
 *   - un JEU D'EXEMPLES : ce que rendent les fonctions de la fenêtre (oui / non, liste, type de bien, type de pièce)
 *     sur des centaines d'entrées. Le serveur doit rendre EXACTEMENT la même chose (backend/tests/test_parcours_traduction.py).
 *
 * Usage : node parcours_traduction.cjs          -> réécrit le fichier
 *         node parcours_traduction.cjs --verifier -> 0 si le fichier est à jour, 1 sinon (App.tsx a changé), 2 si impossible
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const APP = path.join(__dirname, "src", "App.tsx");
const SORTIE = path.join(__dirname, "..", "..", "backend", "app", "services", "parcours_traduction.json");

function tranche(s, debut, fin) {
  const i = s.indexOf(debut);
  if (i < 0) return null;
  const f = s.indexOf(fin, i);
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

function monter(s) {
  const morceaux = {
    miroir: tranche(s, "const SCAN_MIROIR: Record<string, DraftAnnonceSheetScanFieldKey> = {", "\n}\n"),
    directes: tranche(s, "const SCAN_CASES_DIRECTES: Partial<Record<DraftAnnonceSheetScanFieldKey, string>> = {", "\n}\n"),
    carte: tranche(s, "const scanWizardFieldMap: ScanWizardMapEntry[] = [", "\n]\n"),
    resoudre: tranche(s, "function resolveWizardOptionValue(", "\n}\n"),
    typeBien: tranche(s, "function draftAnnoncePropertyTypeIdFromLabel(", "\n}\n"),
    piece: tranche(s, "function compositionPieceTypeIdFromLabel(", "\n}\n"),
    // dans le remplisseur (applyDraftAnnonceScan, un composant) : recopiés tels quels, lus dans le texte
    ouiNon: tranche(s, "const toOuiNon = (raw: string): string => {", "\n    }\n"),
    expo: tranche(s, "const expoMap: Record<string, string> = {", "}\n"),
  };
  const absents = Object.entries(morceaux).filter(([, v]) => !v).map(([k]) => k);
  if (absents.length) return { erreur: "morceaux absents d'App.tsx : " + absents.join(", ") };
  const code = [
    "type HektorPropertyProfileKind = 'apartment' | 'house' | 'land' | 'garage' | 'building' | 'other'",
    "type DraftAnnonceSheetScanFieldKey = string",
    "type ScanWizardMapEntry = { ocr: string; name: string; kind: string; options?: HektorSelectOption[] }",
    morceaux.miroir, morceaux.directes, morceaux.carte, morceaux.resoudre, morceaux.typeBien, morceaux.piece,
    morceaux.ouiNon, morceaux.expo,
    // le texte des synonymes, pour les donner au serveur (les fonctions les gardent en local)
    `this.api = { SCAN_MIROIR, SCAN_CASES_DIRECTES, scanWizardFieldMap, resolveWizardOptionValue,
      draftAnnoncePropertyTypeIdFromLabel, compositionPieceTypeIdFromLabel, toOuiNon, expoMap,
      normalizeDraftAnnonceScanText, draftAnnoncePropertyTypes, hektorCompositionPieceTypeOptions, hektorExposureOptions,
      hektorKitchenOptions, hektorInteriorStateOptions, hektorExteriorStateOptions };`,
  ].join("\n\n");
  const ajoutees = [];
  for (let tour = 0; tour < 60; tour++) {
    const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp, Math, Date };
    vm.createContext(ctx);
    try {
      vm.runInContext(esbuild.transformSync(ajoutees.join("\n\n") + "\n\n" + code, { loader: "ts" }).code, ctx);
      return { api: ctx.api, typeBienTexte: morceaux.typeBien };
    } catch (e) {
      const m = /^(\w+) is not defined/.exec(e.message);
      const decl = m && declarationDe(s, m[1]);
      if (!decl) return { erreur: "le code découpé ne s'exécute pas : " + e.message };
      ajoutees.unshift(decl);
    }
  }
  return { erreur: "trop de dépendances" };
}

// un tableau littéral déclaré DANS une fonction (les synonymes du type de bien), évalué tel quel
function tableauDans(texte, debut) {
  const bloc = tranche(texte, debut, "\n  ]\n");
  if (!bloc) return null;
  const litteral = bloc.slice(bloc.indexOf("= [") + 2).replace(/\/\/[^\n]*/g, "");
  return vm.runInNewContext("(" + litteral.trim() + ")");
}

function variantes(t) {
  const sans = t.normalize("NFD").replace(/[̀-ͯ]/g, "");
  return [t, t.toUpperCase(), t.toLowerCase(), sans, `  ${t}  `, `grand ${t.toLowerCase()}`, t.slice(0, Math.max(3, Math.floor(t.length / 2)))];
}

function produire(src) {
  const s = src.replace(/\r\n/g, "\n");
  const monte = monter(s);
  if (monte.erreur) return { erreur: monte.erreur };
  const a = monte.api;
  const anciens = tableauDans(monte.typeBienTexte, "const legacyMatches");
  const synonymes = tableauDans(monte.typeBienTexte, "const familySynonyms");
  if (!anciens || !synonymes) return { erreur: "synonymes du type de bien illisibles" };
  const listes = {
    exposition: a.hektorExposureOptions, cuisine: a.hektorKitchenOptions, etat_interieur: a.hektorInteriorStateOptions,
    etat_exterieur: a.hektorExteriorStateOptions,
  };
  const carte = a.scanWizardFieldMap.map((e) => ({ scan: e.ocr, fenetre: e.name, sorte: e.kind, ...(e.options ? { options: e.options } : {}) }));
  // LE JEU D'EXEMPLES : la réponse de la fenêtre sur des entrées réelles et des variantes
  const libres = ["", "zzz", "oui", "non", "avec", "sans", "1", "0", "o", "n", "peut-être", "Oui, refait", "NON", "  ",
    "grande maison", "villa contemporaine", "Appartement T3", "corps de ferme", "beau terrain", "maison de ville",
    "Studio meublé", "box fermé", "Immeuble de rapport", "pavillon des années 70", "Local commercial", "T2 lumineux",
    "maison meublée", "parking garage", "rez de chaussée", "place de parking", "un mas provençal", "longère", "F4",
    "séjour", "Salle d'eau", "cuisine équipée", "chambre parentale", "sud ouest", "S", "NO", "américaine", "neuf",
    "bon état", "à rafraîchir", "Est", "Nord-Est", "équipée", "Mitoyenne 1 côté", "fioul", "gaz de ville", "collectif"];
  const exemplesType = [...new Set([
    ...a.draftAnnoncePropertyTypes.flatMap((t) => variantes(t.label)),
    ...anciens.flatMap((x) => x.labels), ...synonymes.flatMap((x) => x.keys), ...libres,
  ])].map((e) => [e, a.draftAnnoncePropertyTypeIdFromLabel(e)]);
  const exemplesPiece = [...new Set([...a.hektorCompositionPieceTypeOptions.flatMap((o) => variantes(o.label)), ...libres])]
    .map((e) => [e, a.compositionPieceTypeIdFromLabel(e)]);
  const exemplesOuiNon = libres.map((e) => [e, a.toOuiNon(e)]);
  const exemplesListes = {};
  const toutesListes = { ...listes };
  for (const e of a.scanWizardFieldMap) if (e.options) toutesListes[e.name] = e.options;
  for (const [nom, options] of Object.entries(toutesListes)) {
    const entrees = [...new Set([...options.filter((o) => o.label).flatMap((o) => variantes(o.label)), ...libres])];
    exemplesListes[nom] = entrees.map((e) => [e, a.resolveWizardOptionValue(e, options)]);
  }
  const exemplesNormaliser = [...new Set([...libres, "  Éléphant  Rose ", "MAISON\tde  Ville", "Ça va"])]
    .map((e) => [e, a.normalizeDraftAnnonceScanText(e)]);
  return {
    donnees: {
      note: "PRODUIT par apps/hektor-v1/parcours_traduction.cjs à partir d'App.tsx : ne pas modifier à la main.",
      miroir: a.SCAN_MIROIR,
      directes: a.SCAN_CASES_DIRECTES,
      carte,
      listes,
      expo_lettres: a.expoMap,
      types_bien: a.draftAnnoncePropertyTypes.map((t) => ({ id: t.id, label: t.label })),
      types_bien_anciens: anciens,
      types_bien_synonymes: synonymes,
      types_piece: a.hektorCompositionPieceTypeOptions,
      exemples: { normaliser: exemplesNormaliser, type_bien: exemplesType, piece: exemplesPiece, oui_non: exemplesOuiNon, listes: exemplesListes },
    },
  };
}

if (require.main === module) {
  let src;
  try { src = fs.readFileSync(APP, "utf8"); } catch (e) { console.log("IMPOSSIBLE de lire App.tsx : " + e.message); process.exit(2); }
  const r = produire(src);
  if (r.erreur) { console.log("IMPOSSIBLE : " + r.erreur); process.exit(2); }
  const texte = JSON.stringify(r.donnees, null, 1) + "\n";
  if (process.argv.includes("--verifier")) {
    let actuel = "";
    try { actuel = fs.readFileSync(SORTIE, "utf8").replace(/\r\n/g, "\n"); } catch { /* absent */ }
    const ok = actuel === texte;
    console.log(ok ? "OK    la table de traduction du serveur est à jour avec App.tsx"
      : "ECHEC la table de traduction n'est plus à jour : App.tsx a changé -> node parcours_traduction.cjs");
    process.exit(ok ? 0 : 1);
  }
  fs.writeFileSync(SORTIE, texte, "utf8");
  const d = r.donnees;
  console.log(`écrit ${path.relative(process.cwd(), SORTIE)} : ${Object.keys(d.miroir).length} miroirs, ${Object.keys(d.directes).length} directes, `
    + `${d.carte.length} cases du scan, ${d.types_bien.length} types de bien, ${d.exemples.type_bien.length} exemples de type, `
    + `${Object.values(d.exemples.listes).reduce((n, l) => n + l.length, 0)} exemples de listes`);
}

module.exports = { produire, SORTIE };
