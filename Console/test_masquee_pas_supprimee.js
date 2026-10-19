// UNE PHOTO MASQUEE N'EST PAS UNE PHOTO SUPPRIMEE                     18/10/2026
//
// ⚠⚠ POURQUOI CE FICHIER EXISTE. Le 15/10 a 23:23, la ligne 4/4 de « GTI Entretien
// Documents » a declare « disparues de Hektor » 440 photos. 337 l'etaient vraiment
// (reportages remplaces -- verifie en direct le 18/10 : 13/13, 25/25, 25/25).
// ⛔ MAIS 103 NE L'ETAIENT PAS : elles sont MASQUEES chez Hektor, et toujours la
//    (verifie en direct sur 6 annonces, 75 photos : 19/19, 14/14, 14/14, 12/12,
//     10/10, 6/6).
//
// LA CAUSE, en une phrase : `accorder_photos_miroir.js` compare notre registre au
// MIROIR, et le miroir vient de l'API detail de Hektor, QUI NE LISTE QUE LES
// VISIBLES. Une masquee n'y figure donc pas -- elle ressemble trait pour trait a
// une supprimee, et les trois verrous existants ne la protegent pas (elle a un
// hektor_photo_id, elle est plus ancienne que la lecture du miroir, et ce n'est pas
// un envoi `app` en cours).
//
// ⚠ ET CE N'EST PAS UN DETAIL D'ARCHIVES : c'est le PREALABLE au bouton
//   « masquer » (chantier (7)-8). Sans ce verrou, masquer une photo la ferait
//   declarer disparue la nuit suivante -> elle sortirait du panneau de l'app
//   (loadConsolePhotos filtre present_in_hektor) -> ON NE POURRAIT PLUS LA
//   DEMASQUER. Le geste serait A SENS UNIQUE.
//
// CE FICHIER FAIT TOURNER LA VRAIE FONCTION extraite du script. Il n'appelle NI
// Hektor, NI le CDN, NI Supabase, et n'ecrit RIEN.
//
//   node Console/test_masquee_pas_supprimee.js
//
// ⚠ IL EST ROUGE TANT QUE LE VERROU N'EST PAS POSE -- c'est voulu : il est ecrit
//   AVANT le correctif, pour prouver que le correctif change quelque chose.

const fs = require("fs");
const path = require("path");

const SCRIPT = path.join(__dirname, "accorder_photos_miroir.js");
const src = fs.readFileSync(SCRIPT, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

// ── on extrait LA VRAIE fonction, on ne l'imite pas ──────────────────────────
function tranche(marque) {
  const d = src.indexOf(marque);
  if (d < 0) return null;
  const f = src.indexOf("\n}", d);
  return f < 0 ? null : src.slice(d, f + 2);
}

const bloc = tranche("function drapeauVisible(");
if (!bloc) {
  console.log("");
  console.log("  KO  drapeauVisible() est introuvable dans accorder_photos_miroir.js");
  console.log("");
  console.log("  ⚠ C'EST LE TEMOIN INVERSE, ET IL EST NORMAL AUJOURD'HUI : cette epreuve");
  console.log("    a ete ecrite AVANT le correctif. Elle passera au vert quand le verrou");
  console.log("    sera pose. Si elle etait verte maintenant, elle ne prouverait rien.");
  console.log("");
  process.exit(1);
}

// eslint-disable-next-line no-eval
const drapeauVisible = eval(`(${bloc})`);

console.log("=== LA REGLE DU DRAPEAU : trois etats, pas deux ===");

// ① Les formes que Hektor et nos deux chemins d'ecriture produisent reellement.
//    `true` vient de rattrapage_photos.js (booleen), "1" du miroir, "true" d'un
//    aller-retour par JSON. Les trois doivent dire la meme chose.
controle("booleen true           -> visible", drapeauVisible({ visible: true }) === "visible", drapeauVisible({ visible: true }));
controle("chaine \"1\"             -> visible", drapeauVisible({ visible: "1" }) === "visible", drapeauVisible({ visible: "1" }));
controle("chaine \"true\"          -> visible", drapeauVisible({ visible: "true" }) === "visible", drapeauVisible({ visible: "true" }));
controle("chaine \"TRUE\"          -> visible", drapeauVisible({ visible: "TRUE" }) === "visible", drapeauVisible({ visible: "TRUE" }));

// ② Ce que le verrou doit reconnaitre. Les 103 portent le booleen `false`.
controle("booleen false          -> masquee", drapeauVisible({ visible: false }) === "masquee", drapeauVisible({ visible: false }));
controle("chaine \"0\"             -> masquee", drapeauVisible({ visible: "0" }) === "masquee", drapeauVisible({ visible: "0" }));
controle("chaine \"false\"         -> masquee", drapeauVisible({ visible: "false" }) === "masquee", drapeauVisible({ visible: "false" }));

// ③ ⚠ L'INCONNU N'EST PAS UNE MASQUEE. Un drapeau absent ou vide ne doit PAS
//    proteger la ligne : une photo dont on ignore l'etat et que Hektor ne liste
//    plus est, selon toute vraisemblance, vraiment supprimee. Le verrou ne doit
//    couvrir QUE ce qu'on sait masque -- sinon il cesserait de marquer des
//    photos legitimement retirees, et le registre divergerait en silence.
controle("null                   -> inconnu", drapeauVisible({ visible: null }) === "inconnu", drapeauVisible({ visible: null }));
controle("undefined              -> inconnu", drapeauVisible({}) === "inconnu", drapeauVisible({}));
controle("chaine vide            -> inconnu", drapeauVisible({ visible: "" }) === "inconnu", drapeauVisible({ visible: "" }));

console.log("");
console.log("=== LE VERROU EST-IL BRANCHE SUR LA BRANCHE DE MARQUAGE ? ===");

// ⚠ Le verrou doit etre DANS `if (!chezEux)`, avant le push, sinon il ne sert a
//   rien. On verifie l'ORDRE dans le texte, pas sa seule presence.
const iBranche = src.indexOf("if (!chezEux)");
const iVerrou = src.indexOf('drapeauVisible(r) === "masquee"');
const iPush = src.indexOf("aMarquer.get(aid).push(r.id)");
controle("la branche de marquage existe", iBranche > 0, "if (!chezEux) introuvable");
controle("le verrou est APRES l'entree de la branche", iVerrou > iBranche, `verrou=${iVerrou} branche=${iBranche}`);
controle("le verrou est AVANT le marquage", iVerrou > 0 && iVerrou < iPush, `verrou=${iVerrou} push=${iPush}`);

console.log("");
console.log("=== LA REGLE N'EST ECRITE QU'UNE FOIS ===");
// Le fichier calculait deja la verite du drapeau en ligne (l. 247). Deux copies
// divergeraient au premier ajustement : la statistique `visible_divergent` et le
// verrou doivent lire LA MEME fonction.
// ⚠ ON COMPTE HORS DE LA DEFINITION. La regle DOIT exister une fois -- dans
//   drapeauVisible() -- et nulle part ailleurs. Une premiere version de cette
//   epreuve exigeait ZERO occurrence et accusait donc la definition elle-meme :
//   elle etait rouge sur un code juste (18/10). On retire le corps de la
//   fonction avant de compter.
const horsDefinition = src.replace(bloc, "");
const copiesEnLigne = (horsDefinition.match(/String\(r\.visible\)\s*===\s*"1"/g) || []).length;
controle("la regle n'existe QUE dans drapeauVisible()", copiesEnLigne === 0,
  `${copiesEnLigne} copie(s) hors de la definition -- la statistique doit l'appeler`);
controle("et elle existe BIEN dans drapeauVisible()",
  /String\(r\.visible\)\s*===\s*"1"/.test(bloc),
  "la definition ne porte pas la regle : le temoin serait vide");
controle("la statistique visible_divergent appelle la fonction",
  /visible_divergent/.test(src) && /drapeauVisible\(r\)/.test(src),
  "visible_divergent ne passe pas par drapeauVisible()");

console.log("");
console.log("=== LE COMPTEUR EXISTE : un verrou muet ne se verifie pas ===");
controle("le compte rendu porte `sautees_masquee`", /sautees_masquee/.test(src),
  "sans compteur, on ne saurait jamais combien de masquees ont ete protegees");

console.log("");
if (echecs === 0) {
  console.log(`✅ ${10 + 3 + 3 + 1} controles, 0 echec -- une masquee ne sera plus prise pour une supprimee.`);
} else {
  console.log(`⛔ ${echecs} echec(s).`);
}
process.exit(echecs === 0 ? 0 : 1);
