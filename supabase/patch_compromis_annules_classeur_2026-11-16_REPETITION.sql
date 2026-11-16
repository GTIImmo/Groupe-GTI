-- ════════════════════════════════════════════════════════════════════════════
-- CONTROLES DES 35 OFFRES « ANNULEE » -- 16/11/2026 . A REJOUER QUAND ON VEUT
-- ⛔ AUCUNE ECRITURE. Tout est en select.
-- ════════════════════════════════════════════════════════════════════════════

-- ① le compte, la forme, et la plage
select 'posees' as controle, count(*) as valeur, '35 attendues' as attendu
  from app_affaire_ledger where transaction_origine = 'classeur'
union all
select 'toutes en compromis/cancelled', count(*), '35'
  from app_affaire_ledger
 where transaction_origine = 'classeur' and kind = 'compromis' and state = 'cancelled'
union all
select 'toutes sans numero Hektor', count(*), '35'
  from app_affaire_ledger
 where transaction_origine = 'classeur' and hektor_affaire_id is null
   and present_in_hektor = false
union all
select 'toutes dans la plage app', count(*), '35'
  from app_affaire_ledger
 where transaction_origine = 'classeur' and app_affaire_id >= 1000000
union all
select 'toutes rattachees a une chaine', count(*), '35'
  from app_affaire_ledger
 where transaction_origine = 'classeur' and app_chaine_id is not null
union all
select 'leurs notes', count(*), 'au moins 35'
  from app_affaire_note where origine = 'classeur'
union all
-- ② ⭐ LE TEMOIN DE L'ACQUEREUR : aucune partie ne doit avoir ete creee
select 'parties creees (doit etre 0)', count(*), '0'
  from app_affaire_partie p
  join app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id
 where l.transaction_origine = 'classeur'
union all
-- ③ ⭐ LE TEMOIN INVERSE : les voisines n'ont pas bouge
select 'plage app AVEC numero (voisines)', count(*), '340'
  from app_affaire_ledger
 where app_affaire_id >= 1000000 and hektor_affaire_id is not null
   and btrim(hektor_affaire_id) <> ''
union all
select 'hors plage (voisines)', count(*), '30817'
  from app_affaire_ledger where app_affaire_id < 1000000
union all
-- ④ ⛔ ET LA SENTINELLE NE DOIT PAS CRIER : la garde de l'origine joue
select 'ce que voit data.transaction_disparue', count(*), '0'
  from app_affaire_ledger
 where present_in_hektor = false
   and last_seen_at >= now() - interval '48 hours'
   and transaction_origine is null
union all
select 'ce que voit data.affaire_sans_numero_hektor', count(*), '0'
  from app_affaires_sans_numero_hektor
order by 1;
