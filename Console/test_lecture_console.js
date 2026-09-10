/**
 * ESSAI DES LECTEURS DE L'ASSISTANT — sur du HTML RÉEL       10/09/2026
 * ═══════════════════════════════════════════════════════════════════════
 *
 * ⚠ NE TOUCHE PAS À HEKTOR. Aucune requête, aucune session. Il rejoue la
 *   capture du 03/09 (compromis 24933) déjà au dépôt, et fait tourner
 *   dessus LES FONCTIONS DU WORKER ELLES-MÊMES — extraites du fichier, pas
 *   recopiées : une copie divergerait sans prévenir.
 *
 * CE QU'IL PROUVE, et pourquoi ça valait un essai :
 *   · le notaire acquéreur (49708) se lit dans `notairesAcquereur[]`
 *   · les honoraires du VENDEUR (10 000,00) et son taux (5,650) se lisent —
 *     ce sont eux le manque n°1 de la tâche 0.1, « invisibles ET non
 *     modifiables depuis l'app »
 *   · les unités de commission et les conditions suspensives ne s'y trouvent
 *     PAS, et c'est ATTENDU : elles vivent aux étapes 2 et 3, dont le HTML
 *     n'a jamais été capturé. C'est exactement pourquoi le worker conserve
 *     le brut de ces étapes-là au lieu de deviner des sélecteurs.
 *
 *   node Console/test_lecture_console.js
 */
const fs = require("fs");
const path = require("path");

const RACINE = path.resolve(__dirname, "..");
// ── 1. LE HTML RÉEL DE L'ÉTAPE 0, tiré de la capture du 03/09 (compromis 24933).
//
// ⚠ IL EST AU DÉPÔT, ET PAS LU DEPUIS Console/exports/. Ce dossier est dans le
//   .gitignore : le test aurait marché ici et échoué partout ailleurs. La capture
//   d'origine reste dans exports/ comme pièce ; la fixture en est la partie utile,
//   déjà déséchappée (`corps_apercu` y était tronqué, donc JSON.parse échouait).
const FIXTURE_ETAPE0 = path.join(
  RACINE, "Console", "fixtures", "etape0_compromis_24933_2026-09-03.html");

function htmlDeLaCapture() {
  return fs.readFileSync(FIXTURE_ETAPE0, "utf8");
}

// ── 2. LES FONCTIONS DU WORKER, prises dans le worker.
function extraire(src, nom, type) {
  const marqueur = type === "const" ? `const ${nom} = ` : `function ${nom}(`;
  const debut = src.indexOf(marqueur);
  if (debut < 0) throw new Error(`introuvable dans le worker : ${nom}`);
  if (type === "const") return src.slice(debut, src.indexOf("\n", debut));
  let n = 0;
  for (let j = src.indexOf("{", debut); j < src.length; j += 1) {
    if (src[j] === "{") n += 1;
    else if (src[j] === "}") { n -= 1; if (n === 0) return src.slice(debut, j + 1); }
  }
  throw new Error(`fin introuvable : ${nom}`);
}

function lecteurDuWorker() {
  const src = fs.readFileSync(path.join(RACINE, "Console", "console_job_worker.js"), "utf8");
  const morceaux = [
    extraire(src, "decodeHtml", "function"),
    extraire(src, "htmlAttrValue", "function"),
    extraire(src, "htmlInputValue", "function"),
    extraire(src, "lireIdentifiantsTableauCache", "function"),
    extraire(src, "RE_ACQUEREURS", "const"),
    extraire(src, "RE_MANDANTS", "const"),
    extraire(src, "RE_NOTAIRE_ACQUEREUR", "const"),
    extraire(src, "RE_NOTAIRE_MANDANT", "const"),
    extraire(src, "RE_ITEM_CONDITION", "const"),
    extraire(src, "lireConditionsSuspensives", "function"),
    extraire(src, "lireChampsConsoleAssistant", "function"),
  ];
  return new Function(`${morceaux.join("\n")}\nreturn lireChampsConsoleAssistant;`)();
}

// ── 3. LES CONDITIONS SUSPENSIVES, sur la fenêtre gardée par le worker
//       lui-même le 10/09 à 10:18 (compromis 50078, étape 3).
//
// ⚠ CE CAS EXISTE PARCE QUE MA PREMIÈRE VERSION A MENTI. Elle comptait tout
//   champ nommé `conditionsSuspensivesSelected[...]` et en annonçait NEUF, là
//   où il n'y en a AUCUNE : les neuf appartenaient à la ligne vide du conteneur
//   et aux deux <template> que le JavaScript clone à l'exécution.
const FIXTURE_CONDITIONS = path.join(
  // ⚠ PAS DANS Console/exports/ : ce dossier est dans le .gitignore, la fixture
  //   n'aurait pas suivi et le test aurait echoue sur toute autre machine.
  RACINE, "Console", "fixtures",
  "conditions_suspensives_50078_2026-09-10.html");

function main() {
  const html = htmlDeLaCapture();
  const r = lecteurDuWorker()([html]);
  console.log(`HTML réel de l'étape 0 : ${html.length} caractères\n`);
  console.log(JSON.stringify(r, null, 2), "\n");

  const attendus = [
    ["les TROIS acquéreurs du formulaire sont lus (49234, 86793, 605030)",
      r.acquereurs.length === 3 && r.acquereurs.includes("86793")],
    ["les TROIS mandants aussi (141053, 485955, 605030)", r.mandants.length === 3],
    ["le notaire acquéreur 49708 est lu", r.notaires_acquereur.includes("49708")],
    ["les honoraires du VENDEUR valent 10000.00", r.montant_honoraire_entree === "10000.00"],
    ["le taux VENDEUR vaut 5.650", r.taux_honoraire_entree === "5.650"],
    ["aucun faux positif sur les unités (étape 2 absente)", r.unites_entree_percent === null],
    // null, et non [] : à l'étape 0 le conteneur des conditions n'existe pas.
    // « Absent » et « aucune » ne sont pas la même chose, et la colonne le dit.
    ["conteneur des conditions absent de l'étape 0", r.conditions_suspensives === null],
  ];
  const c = lecteurDuWorker()([fs.readFileSync(FIXTURE_CONDITIONS, "utf8")]);
  console.log(`\nÉtape 3 réelle : ${c.conditions_suspensives === null ? "conteneur introuvable"
    : c.conditions_suspensives.length + " retenue(s)"} sur `
    + `${(c.conditions_catalogue || []).length} au catalogue\n`);
  attendus.push(
    ["le conteneur des conditions est trouvé", c.conditions_suspensives !== null],
    ["ZÉRO condition retenue — et non neuf", c.conditions_suspensives.length === 0],
    ["le catalogue de l'agence en porte deux", (c.conditions_catalogue || []).length === 2],
    ["chaque entrée du catalogue a son identifiant",
      (c.conditions_catalogue || []).every((x) => x.id && x.libelle)],
  );

  let ok = true;
  for (const [libelle, verdict] of attendus) {
    if (!verdict) ok = false;
    console.log(`   ${verdict ? "OK    " : "ÉCHEC "} ${libelle}`);
  }
  console.log(`\n   >>> ${ok ? "TOUT PASSE" : "IL Y A UN ÉCHEC"}`);
  process.exitCode = ok ? 0 : 1;
}

main();
