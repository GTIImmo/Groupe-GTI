// ════════════════════════════════════════════════════════════════════════════
// LA GARDE DE L'ORIGINE SUR LE LOT DE REFUS D'OFFRES.            16/11/2026
//
//     node Console/test_garde_origine_refus_offres.js
//
// CE QU'ON EPROUVE. `enqueue_refus_offres_mortes_lot.js` REFUSE DES OFFRES CHEZ
// HEKTOR. Sa source « cascade » retient un dossier des qu'il porte un compromis
// annule et une offre encore acceptee. Les transactions reprises du classeur
// n'ont JAMAIS existe chez Hektor : elles ne doivent ni declencher un refus, ni
// en etre la cible.
//
// ⛔ LE DANGER, MESURE LE 16/11 AVANT D'ECRIRE LA GARDE :
//   . poser les 38 compromis « Annulee » du classeur suffisait a faire refuser,
//     a la prochaine relance du lot, les offres acceptees de leurs dossiers ;
//   . et poser plus tard les 69 offres « Vente reglee » (state 'accepted') les
//     rendait elles-memes CIBLES d'un refus chez Hektor, ou elles n'existent pas.
//   . 348 dossiers portent deja « compromis annule + offre acceptee ».
//
// ⚠ ET `vivante()` NE PROTEGEAIT PAS : elle ecarte « porte un numero Hektor ET
//   absente de Hektor ». Nos lignes n'ont PAS de numero, donc la condition est
//   fausse et elles passent pour VIVANTES. C'est le controle 2 qui le prouve.
//
// ⛔ AUCUN RESEAU, AUCUNE ECRITURE : on rejoue la logique de tri sur des lignes
//   fabriquees, et on lit le fichier source pour verifier que la garde y est.
// ════════════════════════════════════════════════════════════════════════════
"use strict";
const fs = require("node:fs");
const path = require("node:path");

const SOURCE = path.join(__dirname, "enqueue_refus_offres_mortes_lot.js");
const src = fs.readFileSync(SOURCE, "utf8");

let verts = 0;
const rouges = [];
function juger(nom, attendu, obtenu) {
  const a = JSON.stringify(attendu), o = JSON.stringify(obtenu);
  if (a === o) { verts += 1; console.log("  OK    " + nom); }
  else { rouges.push(nom); console.log("  ROUGE " + nom + "\n        attendu " + a + "\n        obtenu " + o); }
}

// ── la logique du script, rejouee a l'identique ─────────────────────────────
const ETATS_COMPROMIS_MORTS = new Set(["cancelled", "annule"]);
function vivante(t) {
  return !(String(t.hektor_affaire_id || "").trim() !== "" && t.present_in_hektor === false);
}
// `avecGarde` = le script tel qu'il est maintenant ; `false` = le temoin d'avant.
function dossiersRetenus(lignes, avecGarde) {
  const parChaine = new Map();
  for (const t of lignes) {
    if (!vivante(t)) continue;
    if (avecGarde && String(t.transaction_origine || "").trim() !== "") continue;
    if (!parChaine.has(t.app_chaine_id)) parChaine.set(t.app_chaine_id, []);
    parChaine.get(t.app_chaine_id).push(t);
  }
  const out = [];
  for (const [chaine, membres] of parChaine) {
    const cpAnnule = membres.some((t) => t.kind === "compromis"
      && ETATS_COMPROMIS_MORTS.has(String(t.state || "").toLowerCase()));
    const cpVivant = membres.some((t) => t.kind === "compromis"
      && !ETATS_COMPROMIS_MORTS.has(String(t.state || "").toLowerCase()));
    const vente = membres.some((t) => t.kind === "vente");
    const offreAcceptee = membres.some((t) => t.kind === "offre"
      && ["accepted", "acceptee"].includes(String(t.state || "").toLowerCase()));
    if (cpAnnule && !cpVivant && !vente && offreAcceptee) out.push(chaine);
  }
  return out.sort((a, b) => a - b);
}

// ── les lignes d'essai ──────────────────────────────────────────────────────
const HEKTOR = (ch, kind, state) => ({
  app_chaine_id: ch, kind, state, hektor_affaire_id: "9" + ch,
  present_in_hektor: true, transaction_origine: null, hektor_annonce_id: 1000 + ch });
const CLASSEUR = (ch, kind, state) => ({
  app_chaine_id: ch, kind, state, hektor_affaire_id: null,
  present_in_hektor: false, transaction_origine: "classeur", hektor_annonce_id: 1000 + ch });

console.log("=== 1. LE DANGER : un compromis annule DU CLASSEUR sur un dossier sain ===");
// la chaine 1 : une offre acceptee CHEZ HEKTOR, et on y pose un compromis annule du classeur
const cas1 = [HEKTOR(1, "offre", "accepted"), CLASSEUR(1, "compromis", "cancelled")];
juger("1  SANS la garde, le dossier est RETENU -> l offre serait refusee chez Hektor",
      [1], dossiersRetenus(cas1, false));
juger("1b AVEC la garde, il n est PLUS retenu", [], dossiersRetenus(cas1, true));

console.log("");
console.log("=== 2. ⚠ `vivante()` NE PROTEGEAIT PAS -- c est la mesure du 16/11 ===");
juger("2  une ligne du classeur passe pour VIVANTE (pas de numero Hektor)",
      true, vivante(CLASSEUR(1, "compromis", "cancelled")));
juger("2b alors qu une ligne AVEC numero et absente de Hektor est bien ecartee",
      false, vivante({ hektor_affaire_id: "4320", present_in_hektor: false }));

console.log("");
console.log("=== 3. ⭐ LE TEMOIN INVERSE : la cascade LEGITIME marche toujours ===");
// chaine 2 : tout vient de Hektor -> le dossier DOIT etre retenu, garde ou pas
const cas3 = [HEKTOR(2, "offre", "accepted"), HEKTOR(2, "compromis", "cancelled")];
juger("3  un vrai dossier Hektor est retenu AVEC la garde", [2], dossiersRetenus(cas3, true));
juger("3b et il l etait deja sans elle (la garde ne change RIEN pour lui)",
      dossiersRetenus(cas3, false), dossiersRetenus(cas3, true));

console.log("");
console.log("=== 4. LE SECOND DANGER : une offre « Vente reglee » du classeur, CIBLE d un refus ===");
// chaine 3 : compromis annule chez Hektor, et on pose une offre ACCEPTEE du classeur
const cas4 = [HEKTOR(3, "compromis", "cancelled"), CLASSEUR(3, "offre", "accepted")];
juger("4  SANS la garde, le dossier est retenu a cause de NOTRE offre",
      [3], dossiersRetenus(cas4, false));
juger("4b AVEC la garde, il ne l est plus", [], dossiersRetenus(cas4, true));

console.log("");
console.log("=== 5. ON NE CASSE RIEN : les cas que le script ecartait deja ===");
juger("5  un compromis VIVANT bloque toujours le dossier", [],
      dossiersRetenus([HEKTOR(4, "offre", "accepted"), HEKTOR(4, "compromis", "cancelled"),
                       HEKTOR(4, "compromis", "active")], true));
juger("5b une VENTE bloque toujours le dossier", [],
      dossiersRetenus([HEKTOR(5, "offre", "accepted"), HEKTOR(5, "compromis", "cancelled"),
                       HEKTOR(5, "vente", null)], true));
juger("5c sans offre acceptee, rien n est retenu", [],
      dossiersRetenus([HEKTOR(6, "compromis", "cancelled"),
                       HEKTOR(6, "offre", "refused")], true));

console.log("");
console.log("=== 6. LA GARDE EST BIEN DANS LE FICHIER, ET AU BON ENDROIT ===");
const iVivante = src.indexOf("if (!vivante(t)) continue;");
const iGarde = src.indexOf('if (String(t.transaction_origine || "").trim() !== "") continue;');
const iParChaine = src.indexOf("if (!parChaine.has(t.app_chaine_id))");
juger("6  la colonne est DEMANDEE a PostgREST", true,
      src.includes("present_in_hektor,transaction_origine"));
juger("6b la garde existe", true, iGarde > 0);
juger("6c ⛔ et elle est APRES vivante() et AVANT le regroupement par chaine", true,
      iVivante > 0 && iGarde > iVivante && iParChaine > iGarde);
juger("6d le pourquoi est ECRIT (une exclusion se DECLARE)", true,
      src.includes("CE SCRIPT ECRIT CHEZ HEKTOR"));

console.log("");
console.log(verts + "/" + (verts + rouges.length) + " verts");
if (rouges.length) { console.log("ROUGES : " + rouges.join(" . ")); process.exit(1); }
