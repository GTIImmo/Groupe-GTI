-- ═══════════════════════════════════════════════════════════════════════════════
-- RETIRER LES 5 OFFRES DU CLASSEUR POSEES EN DOUBLON                   18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- POURQUOI, ET C'EST UNE CAUSE EN CHAINE :
--   11/11 19:01  `rattrapage_cascade_annulation` refuse 661 offres chez Hektor.
--   12/11 15:26  reparation apres l'alerte de Frederic (dossier 3676) : 19 offres
--                sont reacceptees -- dont celles-ci.
--   ⚠ LA CICATRICE : chez Hektor, `date` d'une offre porte son DERNIER mouvement.
--     Ces 5 offres portent donc 2026-11-12 au lieu de leur vraie proposition.
--   16/11 13:44  le lot « C5 lot B -- offres vente reglee » ne retrouve plus
--                l'offre a sa date, croit qu'elle manque, et en pose UNE SECONDE.
--
--   ⭐ LA PREUVE QUE C'EST BIEN CA : sur les 64 offres du lot, 6 tombent sur une
--     chaine qui en portait deja une, et 5 des 6 sont EXACTEMENT les 5 cicatrices
--     du 11-12/11. La 6e (annonce 47557) a une autre cause -- ELLE N'EST PAS ICI.
--
-- ⛔ CE QUE CE PATCH NE FAIT PAS : il ne touche NI la colonne `date` (le run la
--   relit chez Hektor chaque nuit, R2_CHAMP_VERS_COLONNE, et la protection lui est
--   nommement refusee, R2_JUGES_SUR_LE_REGISTRE), NI les 59 autres lignes du lot,
--   NI quoi que ce soit chez Hektor.
--
-- RETOUR ARRIERE : patch_retirer_doublons_offres_classeur_2026-11-18_INVERSE.sql
-- CONTROLE       : ..._REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

-- ── ① LA GARDE : exactement 5 lignes, toutes marquees « classeur » ─────────────
--   ⛔ Si quelqu'un est passe avant, le patch S'ARRETE au lieu d'ecrire a cote.
do $$
declare n int;
begin
  select count(*) into n from app_affaire_ledger
   where app_affaire_id in (1001575,1001576,1001577,1001604,1001619)
     and transaction_origine = 'classeur'
     and kind = 'offre'
     and payload_json->>'classeur_lot' = 'C5 lot B -- offres vente reglee';
  if n <> 5 then
    raise exception '⛔ garde : % ligne(s) au lieu de 5 -- rien n''est ecrit', n;
  end if;
end $$;

-- ── ② LA SAUVEGARDE DATEE, AVANT TOUT GESTE DESTRUCTIF ────────────────────────
--   ⭐ Elle garde AUSSI la date du classeur (06/02/2026 pour 43091), que Hektor
--     n'a pas : si on la veut un jour, elle est ici, pas perdue.
create table if not exists app_affaire_ledger_avant_doublons_classeur_20261118
  as select * from app_affaire_ledger where false;
insert into app_affaire_ledger_avant_doublons_classeur_20261118
  select * from app_affaire_ledger
   where app_affaire_id in (1001575,1001576,1001577,1001604,1001619);

create table if not exists app_affaire_note_avant_doublons_classeur_20261118
  as select * from app_affaire_note where false;
insert into app_affaire_note_avant_doublons_classeur_20261118
  select * from app_affaire_note
   where app_affaire_id in (1001575,1001576,1001577,1001604,1001619);

create table if not exists app_classeur_lien_avant_doublons_classeur_20261118
  as select * from app_classeur_lien where false;
insert into app_classeur_lien_avant_doublons_classeur_20261118
  select * from app_classeur_lien
   where app_affaire_id in (1001575,1001576,1001577,1001604,1001619);

-- ── ③ LE RETRAIT, DU PLUS ACCROCHE AU PORTEUR ─────────────────────────────────
--   ⚠ Le lien d'abord : laisse en place, il pointerait dans le vide.
delete from app_classeur_lien
 where app_affaire_id in (1001575,1001576,1001577,1001604,1001619);
delete from app_affaire_note
 where app_affaire_id in (1001575,1001576,1001577,1001604,1001619);
delete from app_affaire_ledger
 where app_affaire_id in (1001575,1001576,1001577,1001604,1001619)
   and transaction_origine = 'classeur';

-- ── ④ LE CONTROLE, DANS LA MEME TRANSACTION ───────────────────────────────────
do $$
declare reste int; garde int; lot int;
begin
  select count(*) into reste from app_affaire_ledger
   where app_affaire_id in (1001575,1001576,1001577,1001604,1001619);
  if reste <> 0 then raise exception '⛔ % ligne(s) restante(s)', reste; end if;

  select count(*) into garde from app_affaire_ledger_avant_doublons_classeur_20261118;
  if garde <> 5 then raise exception '⛔ sauvegarde : % lignes au lieu de 5', garde; end if;

  -- ⭐ TEMOIN INVERSE : les 59 autres lignes du lot n'ont PAS bouge.
  select count(*) into lot from app_affaire_ledger
   where transaction_origine='classeur'
     and payload_json->>'classeur_lot' = 'C5 lot B -- offres vente reglee';
  if lot <> 59 then raise exception '⛔ temoin inverse : % lignes du lot au lieu de 59', lot; end if;

  raise notice '✅ 5 doublons retires, sauvegardes, et les 59 autres intactes';
end $$;

commit;
