-- =====================================================================
-- RETOUR ARRIERE du patch 4j (les battements que personne ne lit)
-- Date : 2026-10-13
--
-- CE QU'IL FAIT : il retire les 23 lignes de configuration posees par le patch,
-- NOMMEES UNE PAR UNE. Rien d'autre.
--
-- ⚠ IL NE TOUCHE PAS a `phase2.repose_cloture_mandat` : cette cle appartient au
--   chantier ③, qui l'a posee le 13/10 a 14:08. Elle n'est pas dans la liste.
--
-- CE QU'ON PERD EN REVENANT EN ARRIERE : seulement l'etat de surveillance de ces
-- etapes (leur dernier succes, leur dernier statut). Aucune donnee metier -- cette
-- table ne porte que de la configuration de surveillance.
--
-- ⚠ ET LE RUN. Si le changement de run a ete fait (les 14 `-WorkerKey` ajoutes), les
--   retirer aussi -- sinon leurs battements repartiront dans le vide, exactement
--   comme avant. L'ordre n'importe pas : un battement sans ligne est silencieux,
--   une ligne sans battement est « jamais vue » et ne declenche rien.
-- =====================================================================

BEGIN;

delete from public.app_worker_registry
where worker_key in (
  -- les 9 dont le run envoyait deja le nom
  'phase2.adresses_photos',
  'phase2.correspondance_identite',
  'phase2.doublure_relation',
  'phase2.doublure_mandat',
  'phase2.correspondance_annonces',
  'phase2.rattrapage_photos',
  'phase2.derives_photos',
  'phase2.sonde_photos',
  'phase1.archived_details',
  -- les 14 qui n'envoyaient aucune cle
  'hektor.drafts_sweep',
  'hektor.immo_pro',
  'hektor.immo_pro_archivees',
  'hektor.chauffage_delta',
  'contacts.champs_manquants',
  'phase2.magasin_mandat',
  'phase2.contrat_mandat',
  'phase2.contacts_layer_passe2',
  'phase2.doublure_affaire_ledger',
  'phase2.registre_relations',
  'phase2.registre_mandats',
  'phase2.magasin_affaire',
  'phase2.contrat_affaire',
  'phase2.carnet_annonce'
);

notify pgrst, 'reload schema';

COMMIT;
