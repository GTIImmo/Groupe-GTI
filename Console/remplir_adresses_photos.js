#!/usr/bin/env node
/**
 * G.15 -- REMPLIR LES ADRESSES DE PHOTOS « CHEZ NOUS »                27/09/2026
 *
 *   node Console/remplir_adresses_photos.js
 *
 * Il appelle deux fonctions Supabase et rend compte. Il ne contient AUCUNE logique :
 * la regle vit en base, la ou les donnees sont.
 *
 *   app_photos_remplir_adresses_app()       les adresses de nos derives, sur les 4 index
 *   app_photos_remplir_adresses_registre()  le registre RECOPIE ce que les index savent
 *   app_photos_placeholder_sans_photo()     notre image « pas de photo » pour celles qui
 *                                           n'en ont AUCUNE
 *
 * ⚠⚠ LE REGISTRE EST UNE FONCTION A PART, ET IL SE JOINT PAR hektor_annonce_id.
 *   Deux mesures du 27/09, payees dans cet ordre :
 *   1. en faire une cible de la 1re fonction faisait recalculer la photo principale de
 *      23 800 annonces chaque nuit -> PostgREST expirait a 8 s ;
 *   2. son app_dossier_id descend a -281 472 776 635 305 : c'est un hache synthetique.
 *      Seules 746 lignes sur 23 840 portent un vrai numero d'app. Joindre par lui ne
 *      couvrait que 3 % du registre -- sans erreur visible, juste 97 % de vide.
 *
 * ⚠ POURQUOI DANS LE PIPELINE ET PAS EN pg_cron : le push de nuit reecrit les lignes
 *   d'index vers 06 h 58. Les colonnes soeurs, elles, SURVIVENT (verifie le 27/09 :
 *   PostgREST en « merge-duplicates » ne touche que les colonnes du payload). Mais une
 *   annonce NEUVE arrive sans adresse. La remplir ici, juste apres la fabrication des
 *   derives, evite qu'elle reste une journee entiere sur Hektor -- inoffensif tant que
 *   Hektor vit, INACCEPTABLE apres la coupure.
 *
 * ⚠ IL NE PARLE NI A HEKTOR NI AU CDN. Deux appels Supabase, rien d'autre.
 *
 * ⚠ LE GARDE-FOU EST EN BASE, pas ici : les deux fonctions REFUSENT d'agir si
 *   app_dossier_current est sous son plancher (5 000). Sans lui, un push de nuit casse
 *   VIDERAIT les adresses de tout le parc, et l'app retomberait entierement sur Hektor.
 */

const path = require("path");
for (const f of ["Console/.env", ".env", "matterport/.env", "apps/hektor-v1/.env"]) {
  require("dotenv").config({ path: path.join(__dirname, "..", f.replace("Console/", "")) });
}

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

// ⚠ CHAQUE APPEL A SON PROPRE BUDGET DE 8 s (le statement_timeout de PostgREST), pas
//   la somme des trois. Le chrono est la pour le voir : le 27/09 l'ensemble tenait en
//   7,1 s et j'ai cru toucher le plafond, alors qu'aucun appel n'en depassait le tiers.
async function rpc(nom) {
  const t0 = Date.now();
  const r = await fetch(`${SUPABASE_URL}/rest/v1/rpc/${nom}`, {
    method: "POST",
    headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}`,
               "Content-Type": "application/json" },
    body: "{}",
  });
  if (!r.ok) throw new Error(`${nom} : ${r.status} ${(await r.text()).slice(0, 200)}`);
  const sortie = await r.json();
  console.log(`  (${nom} : ${((Date.now() - t0) / 1000).toFixed(1)} s)`);
  return sortie;
}

(async () => {
  if (!SUPABASE_URL || !SERVICE_KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");

  const adresses = await rpc("app_photos_remplir_adresses_app");
  console.log(`adresses    : ${JSON.stringify(adresses)}`);
  // ⚠ UN REFUS N'EST PAS UNE PANNE : c'est le garde-fou qui protege le parc. Mais il
  //   doit SE VOIR -- on sort en 1 pour que le heartbeat passe en erreur et que le
  //   moniteur le dise, au lieu de le laisser passer pour un succes.
  if (adresses && adresses.statut === "refus") {
    console.error(`REFUS : ${adresses.raison || "garde-fou"}`);
    process.exitCode = 1;
    return;
  }

  const registre = await rpc("app_photos_remplir_adresses_registre");
  console.log(`registre    : ${JSON.stringify(registre)}`);
  if (registre && registre.statut === "refus") {
    console.error(`REFUS registre : ${registre.raison || "garde-fou"}`);
    process.exitCode = 1;
    return;
  }

  const placeholder = await rpc("app_photos_placeholder_sans_photo");
  console.log(`sans photo  : ${JSON.stringify(placeholder)}`);
  if (placeholder && placeholder.statut === "refus") {
    console.error("REFUS sur le placeholder");
    process.exitCode = 1;
  }
  // ⚠ ON NE FAIT PAS process.exit() ICI. Mesure du 27/09 : appeler process.exit() juste
  // apres un fetch coupe une poignee reseau encore en fermeture, et node leve
  // « Assertion failed: !(handle->flags & UV_HANDLE_CLOSING) » -> code de sortie 127.
  // Le travail avait REUSSI, mais le pipeline l'aurait compte pour un echec, chaque
  // nuit. On pose exitCode et on laisse le processus finir seul.
})().catch((e) => { console.error("ERREUR :", e.message); process.exitCode = 1; });
