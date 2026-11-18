-- ═══════════════════════════════════════════════════════════════════════════════
-- REPETITION -- LE CONTROLE, SANS REPRENDRE LA LISTE DU PATCH          18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⭐ Il ne cite PAS les 5 identifiants : il REFAIT la mesure qui les avait
--   trouves (« une offre du lot sur une chaine qui en porte deja une »). Un
--   controle qui reprend la liste du patch ne repete que ce que le patch croit.
-- ═══════════════════════════════════════════════════════════════════════════════
with pose as (
  select app_affaire_id, app_chaine_id, hektor_annonce_id
  from app_affaire_ledger
  where transaction_origine='classeur'
    and payload_json->>'classeur_lot'='C5 lot B -- offres vente reglee'
), doublons as (
  select p.hektor_annonce_id, l.state
  from pose p join app_affaire_ledger l
    on l.app_chaine_id=p.app_chaine_id and l.kind='offre'
   and l.app_affaire_id<>p.app_affaire_id
   and l.transaction_origine is distinct from 'classeur'
)
select
  (select count(*) from pose) as lignes_du_lot_doit_valoir_59,
  (select count(*) from doublons) as doublons_restants_doit_valoir_1,
  (select count(*) from doublons where coalesce(state,'') not in ('refused','cancelled'))
    as doublons_sur_offre_vivante_doit_valoir_0,
  (select string_agg(hektor_annonce_id::text, ', ') from doublons)
    as le_seul_restant_doit_etre_47557,
  (select count(*) from app_affaire_ledger_avant_doublons_classeur_20261118)
    as sauvegarde_doit_valoir_5,
  (select count(*) from app_affaire_ledger where transaction_origine='classeur')
    as toutes_origines_classeur_doit_valoir_190,
  (select count(*) from app_affaire_ledger where hektor_annonce_id=43091)
    as transactions_de_43091_doit_valoir_3;
