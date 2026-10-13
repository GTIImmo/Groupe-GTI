#!/usr/bin/env node
/**
 * 3c PIECE 4 -- REPOSER LA CLOTURE DE MANDAT « CHEZ NOUS »           13/10/2026
 *
 *   node Console/reposer_cloture_mandat.js
 *
 * Il appelle UNE fonction Supabase et rend compte. Il ne contient AUCUNE logique :
 * la regle vit en base, la ou les donnees sont.
 *
 *   app_reposer_cloture_mandat_app()   le registre REFLETE le carnet
 *
 * POURQUOI IL EXISTE. La ligne de registre qui AFFICHE notre date de cloture est
 * DETRUITE PUIS REFAITE a chaque push :
 *   le run     push_upgrade_to_supabase.py l. 1726-1737 -> delete + insert
 *   le worker  push_single_annonce_to_supabase.py l. 358-360 puis 630 -> delete + upsert
 * Notre colonne `mandat_date_cloture_app` repart donc a NULL les deux fois. Le carnet
 * `app_mandat_champ_app`, lui, n'est jamais touche : c'est lui qui fait foi, et c'est
 * de lui qu'on repose.
 *
 * ⭐ C'EST LE PATRON DES PHOTOS, RECOPIE. Voir remplir_adresses_photos.js et son
 *   commentaire : « les colonnes soeurs SURVIVENT (merge-duplicates ne touche que les
 *   colonnes du payload) » -- VRAI pour la fiche et les index, FAUX pour le registre,
 *   qui est detruit et reinsere. D'ou `app_photos_remplir_adresses_registre`, et d'ou
 *   cette fonction-ci.
 *
 * ⚠ SA PLACE DANS LE RUN : APRES LE PUSH. Avant, elle reposerait sur des lignes que le
 *   push va effacer -- un travail pour rien, et un faux sentiment de securite.
 *
 * ⚠ IL NE PARLE NI A HEKTOR NI AU CDN. Un appel Supabase, rien d'autre.
 *
 * ⚠ LE GARDE-FOU EST EN BASE, pas ici : la fonction REFUSE d'agir si le registre est
 *   sous son plancher (10 000 lignes ; il en porte 24 505). Sans lui, un push casse
 *   VIDERAIT nos clotures en silence. Un refus n'est pas une panne -- mais il doit SE
 *   VOIR : on sort en 1 pour que le heartbeat passe en erreur et que le moniteur le dise.
 */

const path = require("path");
for (const f of ["Console/.env", ".env", "matterport/.env", "apps/hektor-v1/.env"]) {
  require("dotenv").config({ path: path.join(__dirname, "..", f.replace("Console/", "")) });
}

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

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

  const repose = await rpc("app_reposer_cloture_mandat_app");
  console.log(`cloture mandat : ${JSON.stringify(repose)}`);

  if (repose && repose.statut === "refus") {
    console.error(`REFUS : ${repose.raison || "garde-fou"}`);
    process.exitCode = 1;
    return;
  }

  // ⚠ UNE NUIT ORDINAIRE POSE PEU DE CHOSES, ET C'EST NORMAL : la fonction ne reecrit
  //   que ce qui differe. « posees: 0, effacees: 0 » veut dire « le registre dit deja
  //   la verite », pas « rien n'a marche ».
  // ⚠ ON NE FAIT PAS process.exit() ICI (mesure du 27/09 sur son jumeau : couper une
  //   poignee reseau en fermeture fait sortir node en 127, et le pipeline compte un
  //   echec alors que le travail a reussi). On pose exitCode et on laisse finir.
})().catch((e) => { console.error("ERREUR :", e.message); process.exitCode = 1; });
