-- ═══════════════════════════════════════════════════════════════════════════
-- REPETITION DE patch_mise_de_cote_cicatrices_famille1_2026-11-22.sql -- LECTURE SEULE, APRES LE PATCH
-- Chaque ligne doit dire OUI.
-- ═══════════════════════════════════════════════════════════════════════════
select 'les 3 cicatrices ne sont plus au registre' as controle,
       case when count(*) = 0 then 'OUI' else 'NON' end as verdict, count(*)::text as detail
  from public.app_affaire_ledger where app_affaire_id in (1001482, 1001563, 1001580)
union all
select 'leur garde les porte ENTIERES (3 lignes)',
       case when count(*) = 3 then 'OUI' else 'NON' end, count(*)::text
  from public.app_affaire_ledger_mise_de_cote_cicatrices_20261122
union all
select 'le registre des cicatrices garde leur ANCIEN numero (D2019-0649, D2024-0505, D2020-0607)',
       case when count(*) = 3 then 'OUI' else 'NON' end, string_agg(ancien_dossier_numero, ', ' order by app_affaire_id)
  from public.app_classeur_cicatrice_mise_de_cote
 where (app_affaire_id, ancien_dossier_numero) in ((1001482, 'D2019-0649'), (1001563, 'D2024-0505'), (1001580, 'D2020-0607'))
union all
select 'leurs notes sont gardees, aucune ne reste',
       case when (select count(*) from public.app_affaire_note where app_affaire_id in (1001482, 1001563, 1001580)) = 0
             and count(*) >= 1 then 'OUI' else 'NON' end, count(*)::text || ' gardee(s)'
  from public.app_affaire_note_mise_de_cote_cicatrices_20261122
union all
select 'les 3 jumelles sont intactes (5055, 1876, 11958)',
       case when count(*) = 3 then 'OUI' else 'NON' end, count(*)::text
  from public.app_affaire_ledger where app_affaire_id in (5055, 1876, 11958) and coalesce(transaction_origine, '') <> 'classeur'
union all
select 'les 187 autres copies sont la (dont la famille 2 : 1001561, 1001593)',
       case when count(*) = 187 and count(*) filter (where app_affaire_id in (1001561, 1001593)) = 2 then 'OUI' else 'NON' end,
       count(*)::text
  from public.app_affaire_ledger where transaction_origine = 'classeur'
union all
select 'aucune piece ne porte plus leurs anciennes etiquettes',
       case when count(*) = 0 then 'OUI' else 'NON' end, count(*)::text
  from public.app_affaire_ledger l
 where l.app_dossier_uuid in (select ancien_dossier_uuid from public.app_classeur_cicatrice_mise_de_cote
                               where app_affaire_id in (1001482, 1001563, 1001580));
