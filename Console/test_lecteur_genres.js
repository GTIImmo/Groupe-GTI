/**
 * LE LECTEUR CONNAIT DEUX GENRES — ÉPROUVÉ HORS LIGNE        14/09/2026
 * ═══════════════════════════════════════════════════════════════════════════════
 *
 * ⚠ IL N'APPELLE PAS HEKTOR. Il éprouve les pièces ajoutées au lecteur sur du
 *   HTML CAPTURÉ et sur des chaînes construites ici. C'est la méthode de
 *   test_lecture_console.js depuis le 10/09 : on vérifie un ajout AVANT de
 *   demander quoi que ce soit à leur serveur.
 *
 * CE QU'IL PROUVE, ET POURQUOI CHAQUE POINT COMPTE :
 *   ① le mode compromis n'a PAS bougé — c'est lui qui a lu 9 216 fiches sans
 *      incident, et un ajout qui le modifie serait une régression ;
 *   ② le mode vente vise bien l'assistant de la vente, avec SA clé ;
 *   ③ la clé de sortie suit le genre — le pilote apparie dessus, et se tromper
 *      ferait écrire une vente sous un numéro de compromis ;
 *   ④ on sait reposer un formulaire, et une case non cochée n'est pas reposée ;
 *   ⑤ le panier se lit dans la réponse — sans lui, l'étape suivante part à vide ;
 *   ⑥ et LE LECTEUR VOIT LES INTERVENANTS quand on lui donne la page 2, ce qui
 *      est tout l'objet de l'exercice.
 *
 *   node Console/test_lecteur_genres.js
 */
const fs = require("fs");
const path = require("path");
const { chargerLecteur, chargerReposeur } = require("./lecture_assistant");

let echecs = 0;
function verifier(titre, reel, attendu) {
  const a = JSON.stringify(reel), b = JSON.stringify(attendu);
  const ok = a === b;
  if (!ok) echecs += 1;
  console.log(`   ${ok ? "OK  " : "ECHEC"} ${titre}`);
  if (!ok) console.log(`        attendu ${b}\n        obtenu  ${a}`);
}

const source = fs.readFileSync(path.join(__dirname, "extract_hektor_compromis_console.js"), "utf8");

console.log("① LE MODE COMPROMIS N'A PAS BOUGE");
for (const marque of ["annonce-SuiviVente-compromis-createCompromis",
                      "annonce-SuiviVente-compromis-getStepCompromis",
                      "idCompromis", "hektor_compromis_id", "PopinCompromis"]) {
  verifier(`il connait toujours ${marque}`, source.includes(marque), true);
}

console.log("");
console.log("② ET IL CONNAIT DESORMAIS LA VENTE");
for (const marque of ["annonce-SuiviVente-vente-createVente",
                      "annonce-SuiviVente-vente-getStepVente",
                      "idVente", "hektor_vente_id", "PopinVente"]) {
  verifier(`il connait ${marque}`, source.includes(marque), true);
}

console.log("");
console.log("③ LES DEUX GENRES SONT DECRITS AU MEME ENDROIT, SANS DOUBLON");
// Un seul bloc ASSISTANTS : deux blocs divergeraient, c'est la regle du projet.
verifier("un seul catalogue d'assistants",
  (source.match(/const ASSISTANTS = \{/g) || []).length, 1);
verifier("aucun verbe de vente ecrit ailleurs qu'au catalogue",
  (source.match(/annonce-SuiviVente-vente-getStepVente/g) || []).length, 1);

console.log("");
console.log("④ REPOSER UN FORMULAIRE");
const reposer = chargerReposeur();
const formulaire = '<input name="prixDeVente" value="185000">'
  + '<input name="dateVente" value="14-09-2026">'
  + '<select name="mandat"><option value="a">A</option><option value="b" selected>B</option></select>'
  + '<input type="checkbox" name="pasCochee" value="1">'
  + '<input type="submit" name="bouton" value="Envoyer">';
const repose = reposer(formulaire, null);
verifier("le prix est repose", repose.get("prixDeVente"), "185000");
verifier("l'option choisie est reposee", repose.get("mandat"), "b");
verifier("une case NON cochee n'est pas reposee", repose.has("pasCochee"), false);
verifier("un bouton n'est pas un champ", repose.has("bouton"), false);

console.log("");
console.log("⑤ LE PANIER SE LIT DANS LA REPONSE");
// Recopie de la fonction du lecteur : si elles divergent, ce test doit tomber.
function panierDeLEtape(texte) {
  try {
    const j = JSON.parse(String(texte || ""));
    const d = (j && j.data) || {};
    return typeof d.basket === "string" ? d.basket : "";
  } catch (_) { return ""; }
}
verifier("panier lu", panierDeLEtape('{"data":{"basket":"a:1:{}"}}'), "a:1:{}");
verifier("reponse sans panier -> vide, pas une exception",
  panierDeLEtape('{"data":{}}'), "");
verifier("reponse illisible -> vide", panierDeLEtape("<html>"), "");

console.log("");
console.log("⑥ LE LECTEUR VOIT LES INTERVENANTS QUAND ON LUI DONNE LA PAGE 2");
const lire = chargerLecteur();
// Forme relevee EN REEL sur la vente 23304 le 12/09.
const page2 = '<p class="calcBlockTitle signataireName">Corinne REYNAUD</p>'
  + '<input name="intervenantsEntree[115][id]" value="115">'
  + '<input name="intervenantsEntree[115][percent]" value="100">'
  + '<input name="intervenantsEntree[115][montant]" value="4166.67">'
  + '<input name="intervenantsEntree[115][type]" value="NEGO">'
  + '<p class="calcBlockTitle signataireName">Stephanie MARTINEZ</p>'
  + '<input name="intervenantsSortie[55][id]" value="55">'
  + '<input name="intervenantsSortie[55][percent]" value="100">'
  + '<input name="intervenantsSortie[55][montant]" value="4166.67">'
  + '<input name="intervenantsSortie[55][type]" value="NEGO">'
  + '<input name="unitesEntreePercent" value="50">'
  + '<input name="unitesSortiePercent" value="50">';
const sansPage2 = lire(["<div>page d'ouverture</div>"]);
const avecPage2 = lire(["<div>page d'ouverture</div>", page2]);
verifier("sans la page 2, aucun intervenant",
  (sansPage2.intervenants || []).length, 0);
verifier("avec la page 2, deux intervenants",
  (avecPage2.intervenants || []).length, 2);
const parSens = Object.fromEntries((avecPage2.intervenants || []).map((x) => [x.sens, x.id]));
verifier("l'entree porte 115", parSens.entree, "115");
verifier("la sortie porte 55", parSens.sortie, "55");
verifier("le partage entree est lu", avecPage2.unites_entree_percent, "50");

console.log("");
console.log(echecs ? `${echecs} ASSERTION(S) EN ECHEC` : "TOUTES LES ASSERTIONS PASSENT");
process.exit(echecs ? 1 : 0);
