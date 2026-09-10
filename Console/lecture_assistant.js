/**
 * LE LECTEUR DE L'ASSISTANT, PARTAGÉ                            10/09/2026
 * ═══════════════════════════════════════════════════════════════════════
 *
 * CE QU'IL FAIT. Il rend les fonctions de lecture du worker — celles qui
 * tirent du formulaire de Hektor ce que l'API ne rend jamais — sans
 * charger le worker lui-même, qui ouvre une session et boucle sur les
 * travaux dès qu'on le require.
 *
 * ⚠ POURQUOI IL LES EXTRAIT AU LIEU DE LES RECOPIER. Une copie diverge
 *   sans prévenir : le jour où le lecteur du worker est corrigé, le
 *   rattrapage continuerait de lire l'ancienne forme et personne ne le
 *   verrait. C'est arrivé aujourd'hui même — les conditions suspensives
 *   ont changé de lecteur deux fois en trois heures. Ici il n'existe
 *   qu'UNE définition, dans console_job_worker.js, et tout le monde la lit.
 *
 * C'est déjà la méthode de Console/test_lecture_console.js, éprouvée.
 *
 *     const { chargerLecteur } = require("./lecture_assistant");
 *     const lire = chargerLecteur();
 *     lire([htmlEtape0, htmlEtape2, ...])  ->  { acquereurs, notaires… }
 */
const fs = require("fs");
const path = require("path");

const SOURCE = path.join(__dirname, "console_job_worker.js");

/** Découpe une fonction ou une constante du source, par équilibre d'accolades. */
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

/** Les morceaux à emporter, dans l'ordre où ils se dépendent. */
const MORCEAUX = [
  ["decodeHtml", "function"],
  ["stripHtml", "function"],
  ["htmlAttrValue", "function"],
  ["htmlInputValue", "function"],
  ["RE_INFOS_USER", "const"],
  ["identiteAvantLInput", "function"],
  ["lirePartiesTableauCache", "function"],
  ["lireIdentifiantsTableauCache", "function"],
  ["RE_ACQUEREURS", "const"],
  ["RE_MANDANTS", "const"],
  ["RE_NOTAIRE_ACQUEREUR", "const"],
  ["RE_NOTAIRE_MANDANT", "const"],
  ["RE_INTERVENANT", "const"],
  ["RE_SIGNATAIRE", "const"],
  ["lireIntervenants", "function"],
  ["RE_ITEM_CONDITION", "const"],
  ["lireConditionsSuspensives", "function"],
  ["lireChampsConsoleAssistant", "function"],
];

function chargerLecteur(cheminSource) {
  const src = fs.readFileSync(cheminSource || SOURCE, "utf8");
  const code = MORCEAUX.map(([nom, type]) => extraire(src, nom, type)).join("\n");
  return new Function(`${code}\nreturn lireChampsConsoleAssistant;`)();
}

module.exports = { chargerLecteur, extraire, SOURCE };
