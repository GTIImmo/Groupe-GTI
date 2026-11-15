-- ════════════════════════════════════════════════════════════════════════════
-- ESSAI A2 -- UNE TRANSACTION DE LA PLAGE APP SURVIT-ELLE A UNE NUIT ?
-- 15/11/2026 . chantier classeur, tache 3.3zero
-- ════════════════════════════════════════════════════════════════════════════
--
-- CE QU'ON MESURE, ET POURQUOI C'EST OBLIGATOIRE.
--   L'audit du 15/11 (plan, section 3.3quater) a lu les protections du code :
--   le run de nuit ne peut PAS effacer une ligne dont app_affaire_id >= 1 000 000
--   (sa premiere garde est litteralement « app_affaire_id < PLAGE_RESERVEE_APP »),
--   et sa seule suppression EXIGE un numero Hektor.
--   ⛔ MAIS AUCUN TEMOIN POSITIF N'EXISTE : les 340 lignes de la plage app portent
--      TOUTES un hektor_affaire_id, et 3 lignes de cette plage (1001388, 1001391,
--      1001394) ONT DISPARU des deux bases sans sauvegarde, sans journal, sans
--      trace de qui. « Un zero ne se croit pas sans temoin positif. »
--   ➡ Cette ligne est ce temoin. Si elle est intacte demain matin, les 241
--     transactions manquantes du classeur peuvent etre creees chez nous.
--
-- LA CIBLE, CHOISIE PAR LA MESURE (et non au hasard) :
--   annonce 28351 . chaine 14001 . dossier D2006-0007
--     . VENDUE EN 2006 (compromis 16/05, vente 24/07) -> hors du parc vivant,
--       0 ligne dans app_dossier_current ;
--     . ELLE N'A AUCUNE OFFRE -> l'essai reproduit EXACTEMENT le cas des
--       144 offres manquantes du classeur ;
--     . ⭐ ELLE EST ABSENTE DU CLASSEUR (0 lien dans app_classeur_lien) -> l'essai
--       ne faussera AUCUNE mesure du chantier.
--
-- CE QUE LA LIGNE PORTE, ET POURQUOI :
--   hektor_affaire_id = NULL  et  present_in_hektor = false   <- LE SUJET DE L'ESSAI
--   state = 'refused'   une offre REFUSEE ne declenche aucune des 4 regles de
--                       chainage (une offre ACCEPTEE orpheline, elle, en declenche)
--   date  = 2006-04-01  avant le compromis, coherent avec l'histoire du dossier
--   payload_json        porte le marqueur de l'essai et « a_supprimer_apres_mesure »
--
-- ⚠ EFFET DE BORD CONNU : la table porte 3 declencheurs, dont un AFTER INSERT qui
--   appelle app_affaire_partie_suivre(). Comme la ligne n'a ni acquereurs_json ni
--   mandants_json, il ne devrait rien creer -- la REPETITION le verifie.
--
-- RETOUR ARRIERE : patch_essai_a2_plage_app_2026-11-15_INVERSE.sql
-- CONTROLES      : patch_essai_a2_plage_app_2026-11-15_REPETITION.sql
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- ── LES TROIS GARDES : le patch S'ARRETE si la cible n'est pas celle attendue
do $$
begin
  if not exists (
    select 1 from app_affaire_ledger
     where hektor_annonce_id = 28351 and app_chaine_id = 14001
       and kind = 'compromis' and hektor_affaire_id = '20217') then
    raise exception 'ARRET : la cible 28351 / chaine 14001 n est pas celle mesuree le 15/11';
  end if;

  if exists (
    select 1 from app_affaire_ledger
     where hektor_annonce_id = 28351 and kind = 'offre') then
    raise exception 'ARRET : une offre existe deja sur 28351 -- cet essai ne doit RIEN ecraser';
  end if;

  if exists (
    select 1 from app_classeur_lien cl
      join app_affaire_ledger l on l.app_affaire_id = cl.app_affaire_id
     where l.hektor_annonce_id = 28351) then
    raise exception 'ARRET : 28351 est reliee au classeur -- il faut un bien NEUTRE';
  end if;
end $$;

-- ── LA LIGNE D'ESSAI
insert into app_affaire_ledger (
  app_affaire_id, app_chaine_id, app_dossier_id,
  kind, state, date,
  hektor_annonce_id, hektor_affaire_id, present_in_hektor,
  app_dossier_uuid, app_dossier_numero,
  payload_json, first_seen_at, last_seen_at)
values (
  nextval('app_affaire_id_app_seq'), 14001, 1355930,
  'offre', 'refused', '2006-04-01',
  28351, null, false,
  'c3c940db-edac-42aa-8644-99801cec858b', 'D2006-0007',
  jsonb_build_object(
    'essai_a2_2026_11_15', true,
    'but', 'mesurer la survie d une ligne de la plage app SANS numero Hektor',
    'a_supprimer_apres_mesure', true,
    'plan', 'tache 3.3zero du chantier classeur'),
  now(), now());

-- ── CE QUI VIENT D'ETRE POSE, a lire dans la sortie
select app_affaire_id, app_chaine_id, kind, state, date,
       hektor_annonce_id, hektor_affaire_id, present_in_hektor
  from app_affaire_ledger
 where hektor_annonce_id = 28351 and kind = 'offre';

commit;
