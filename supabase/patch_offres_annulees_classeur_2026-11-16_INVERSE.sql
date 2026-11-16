-- ════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DES 96 OFFRES « ANNULEE » DU CLASSEUR -- 16/11/2026
-- ════════════════════════════════════════════════════════════════════════════
--
-- ⛔ IL NE JUGE QUE SA PART (regle n0 31) : il retire les lignes marquees
--   `transaction_origine = 'classeur'` ET nees de CE lot (payload_json le dit),
--   puis il VERIFIE qu'il ne reste aucune trace et que les voisines sont intactes.
--
-- ⚠ ON NE VISE PAS « la plage app » : ce serait emporter les 340 lignes legitimes.
--   On vise LE MARQUEUR DU LOT, comme l'inverse de l'essai A2 visait le sien.
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- ── a lire AVANT
select count(*) as a_retirer
  from app_affaire_ledger
 where transaction_origine = 'classeur'
   and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres annulees';

-- ── les notes d'abord (elles pointent les lignes)
delete from app_affaire_note
 where origine = 'classeur'
   and app_affaire_id in (select app_affaire_id from app_affaire_ledger
                           where transaction_origine = 'classeur'
                             and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres annulees');

delete from app_affaire_ledger
 where transaction_origine = 'classeur'
   and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres annulees';

-- ── LES CONTROLES DU RETOUR ARRIERE
do $$
declare
  reste integer;
  plage_avec_numero integer;
  hors_plage integer;
begin
  select count(*) into reste from app_affaire_ledger
   where (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres annulees';
  if reste <> 0 then
    raise exception 'ARRET : il reste %s ligne(s) du lot -- le retour est INCOMPLET', reste;
  end if;

  select count(*) into plage_avec_numero from app_affaire_ledger
   where app_affaire_id >= 1000000
     and hektor_affaire_id is not null and btrim(hektor_affaire_id) <> '';
  if plage_avec_numero <> 340 then
    raise exception 'ARRET : la plage app AVEC numero vaut %s au lieu de 340 -- NE PAS VALIDER', plage_avec_numero;
  end if;

  select count(*) into hors_plage from app_affaire_ledger where app_affaire_id < 1000000;
  if hors_plage <> 30817 then
    raise exception 'ARRET : le hors-plage vaut %s au lieu de 30 817 -- NE PAS VALIDER', hors_plage;
  end if;

  raise notice 'retour arriere OK : 0 trace du lot, voisines intactes (340 + 30 817)';
end $$;

commit;
