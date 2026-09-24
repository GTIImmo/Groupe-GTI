"use strict";
// ═══════════════════════════════════════════════════════════════════════════
// C.9-e (e2) — LE NUMERO HEKTOR SE POSE SUR LA LIGNE DE L'APP        24/09/2026
// ═══════════════════════════════════════════════════════════════════════════
// Audit : notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md, defaut D8.
//
// Une annonce NEE DANS L'APP a deja sa ligne dans app_dossier_current, sous son
// numero a nous (>= 10 000 000), la case hektor_annonce_id vide. Quand Hektor
// vient de la creer, le worker doit remplir cette case AVANT de lancer le
// rafraichissement : c'est par ce numero que le rafraichissement (e1) la
// retrouve. Dans l'autre ordre, il ne la voit pas, fabrique un numero serveur,
// et l'annonce se retrouve en double.
//
// ⚠ ON NE REMPLIT QU'UNE CASE VIDE (filtre `is.null`). Une case qui porte deja
//   une AUTRE valeur n'est jamais ecrasee : c'est une anomalie, on s'arrete.
// ⚠ POURQUOI UN MODULE A PART : le worker lance ses travaux des qu'on le charge,
//   donc aucun test ne peut l'importer. Ici, la regle se teste avec un faux
//   Supabase (Console/test_numero_annonce_app.js).
//
// POUR UNE ANNONCE NEE CHEZ HEKTOR (tout le parc au 24/09) : rien, pas meme une
// requete -- le travail ne porte pas de numero d'app.

const PLAGE_ANNONCE_APP = 10000000;

class ArretVolontaire extends Error {}

async function poserNumeroHektorSurLigneApp({
  appDossierId,
  hektorAnnonceId,
  requete,
  attendre = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  delais = [2000, 8000],
}) {
  const appId = Number(appDossierId);
  if (!Number.isInteger(appId) || appId < PLAGE_ANNONCE_APP) {
    return { status: "skipped", reason: "pas_nee_dans_l_app" };
  }
  const hektorId = String(hektorAnnonceId === undefined || hektorAnnonceId === null ? "" : hektorAnnonceId).trim();
  if (!/^\d+$/.test(hektorId) || Number(hektorId) >= PLAGE_ANNONCE_APP) {
    throw new ArretVolontaire(`C.9-e2 : numero Hektor invalide « ${hektorId} » pour la ligne ${appId}`);
  }

  let derniere = null;
  for (let tentative = 0; tentative <= delais.length; tentative += 1) {
    try {
      const majes = await requete(
        `app_dossier_current?app_dossier_id=eq.${appId}&hektor_annonce_id=is.null`,
        { method: "PATCH", prefer: "return=representation",
          body: JSON.stringify({ hektor_annonce_id: Number(hektorId) }) });
      if (Array.isArray(majes) && majes.length) {
        return { status: "pose", app_dossier_id: appId, hektor_annonce_id: hektorId, tentatives: tentative + 1 };
      }
      // Aucune ligne modifiee : deja posee (rejeu), autre valeur, ou ligne absente.
      const lignes = await requete(
        `app_dossier_current?select=app_dossier_id,hektor_annonce_id&app_dossier_id=eq.${appId}`,
        { method: "GET" });
      if (!Array.isArray(lignes) || !lignes.length) {
        throw new ArretVolontaire(`C.9-e2 : la ligne ${appId} n'existe pas dans app_dossier_current`);
      }
      const actuel = String(lignes[0].hektor_annonce_id === null || lignes[0].hektor_annonce_id === undefined
        ? "" : lignes[0].hektor_annonce_id).trim();
      if (actuel === hektorId) {
        return { status: "deja_pose", app_dossier_id: appId, hektor_annonce_id: hektorId, tentatives: tentative + 1 };
      }
      throw new ArretVolontaire(
        `C.9-e2 : la ligne ${appId} porte deja le numero Hektor ${actuel || "(vide ?)"}, ` +
        `pas ${hektorId} -- on n'ecrase pas`);
    } catch (erreur) {
      if (erreur instanceof ArretVolontaire) throw erreur;
      derniere = erreur;
      if (tentative < delais.length) await attendre(delais[tentative]);
    }
  }
  const message = derniere && derniere.message ? derniere.message : String(derniere);
  throw new Error(
    `C.9-e2 : numero Hektor ${hektorId} NON pose sur la ligne ${appId} apres ` +
    `${delais.length + 1} tentatives (${message}). A reparer a la main : ` +
    `app_dossier_current.hektor_annonce_id = ${hektorId} pour app_dossier_id = ${appId}.`);
}

module.exports = { poserNumeroHektorSurLigneApp, ArretVolontaire, PLAGE_ANNONCE_APP };
