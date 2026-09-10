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
const CAPTURE = path.join(
  RACINE, "Console", "exports",
  "capture_compromis_acquereur_24933_2026-09-03T17-55-04-374Z", "network_events.json");

// ── 1. LE HTML RÉEL. `corps_apercu` est TRONQUÉ à 40 000 caractères, donc
//       JSON.parse échoue : on déséchappe à la main.
function htmlDeLaCapture() {
  const ev = JSON.parse(fs.readFileSync(CAPTURE, "utf8"));
  let best = "";
  for (const e of ev) {
    const c = e && typeof e.corps_apercu === "string" ? e.corps_apercu : "";
    if (c.includes("notairesAcquereur") && c.length > best.length) best = c;
  }
  const marqueur = '"stepContent":"';
  const i = best.indexOf(marqueur);
  const brut = i >= 0 ? best.slice(i + marqueur.length) : best;
  return brut
    .replace(/\\r/g, "")
    .replace(/\\n/g, "\n")
    .replace(/\\\//g, "/")
    .replace(/\\"/g, '"')
    .replace(/\\\\/g, "\\");
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
    extraire(src, "RE_NOTAIRE_ACQUEREUR", "const"),
    extraire(src, "RE_NOTAIRE_MANDANT", "const"),
    extraire(src, "RE_CONDITION_SUSPENSIVE", "const"),
    extraire(src, "lireChampsConsoleAssistant", "function"),
  ];
  return new Function(`${morceaux.join("\n")}\nreturn lireChampsConsoleAssistant;`)();
}

function main() {
  const html = htmlDeLaCapture();
  const r = lecteurDuWorker()([html]);
  console.log(`HTML réel de l'étape 0 : ${html.length} caractères\n`);
  console.log(JSON.stringify(r, null, 2), "\n");

  const attendus = [
    ["le notaire acquéreur 49708 est lu", r.notaires_acquereur.includes("49708")],
    ["les honoraires du VENDEUR valent 10000.00", r.montant_honoraire_entree === "10000.00"],
    ["le taux VENDEUR vaut 5.650", r.taux_honoraire_entree === "5.650"],
    ["aucun faux positif sur les unités (étape 2 absente)", r.unites_entree_percent === null],
    ["aucun faux positif sur les conditions (étape 3 absente)", r.conditions_suspensives.length === 0],
  ];
  let ok = true;
  for (const [libelle, verdict] of attendus) {
    if (!verdict) ok = false;
    console.log(`   ${verdict ? "OK    " : "ÉCHEC "} ${libelle}`);
  }
  console.log(`\n   >>> ${ok ? "TOUT PASSE" : "IL Y A UN ÉCHEC"}`);
  process.exitCode = ok ? 0 : 1;
}

main();
