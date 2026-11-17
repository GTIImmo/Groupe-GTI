-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (1er patch) -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- ═══════════════════════════════════════════════════════════════════════════

select 'motifs poses' as controle, count(*)::text as mesure, '169' as attendu
  from public.app_affaire_ledger where motif_annulation_app is not null
union all
select 'aucun motif hors du lot', count(*)::text, '0'
  from public.app_affaire_ledger
 where motif_annulation_app is not null and app_affaire_id not in (6157, 23983, 25965, 16096, 7176, 11110, 26603, 8840, 8845, 20296, 6343, 7422, 27178, 7067, 28155, 22, 27143, 101, 8839, 958, 7177, 11111, 7232, 11501, 4198, 4179, 12952, 8856, 16170, 17433, 17209, 17203, 24008, 14083, 26605, 15914, 20, 4203, 8864, 20077, 6138, 28263, 28258, 8917, 24188, 27145, 16169, 1874, 160, 1019, 9359, 19102, 8925, 4272, 7646, 6431, 8321, 7251, 7645, 74, 17226, 25867, 26013, 9362, 19086, 19561, 7560, 117, 14935, 19619, 25735, 17011, 4277, 25877, 4321, 4508, 1000142, 6499, 4372, 27338, 16251, 16046, 7580, 19113, 7606, 10015, 4300, 4329, 17291, 16833, 16298, 9896, 26072, 19512, 24165, 2533, 24168, 19456, 27243, 22008, 19095, 17301, 15042, 15073, 200, 7438, 7667, 4327, 23447, 11596, 15915, 16327, 3719, 4484, 4111, 26076, 24297, 16305, 11524, 21598, 19657, 15032, 7724, 4480, 25742, 14086, 1089, 7699, 25897, 15059, 269, 7725, 259, 16846, 16841, 19665, 25911, 14141, 20408, 27372, 16382, 28289, 17525, 15096, 4799, 24499, 11472, 26028, 24443, 16378, 26155, 20613, 4706, 26152, 11791, 27661, 1229, 22256, 23809, 16388, 24564, 4771, 11885, 11963, 11972, 15901, 28839, 28881, 30648)
union all
select 'le catalogue', count(*)::text, '4 = 2 d origine + 2 de C4'
  from public.app_condition_catalogue
union all
select 'les 2 clauses d origine INTACTES', count(*)::text, '2'
  from public.app_condition_catalogue
 where lower(libelle) in ('preemption mairie', 'préemption mairie', 'obtention crédit', 'obtention credit')
union all
select 'motifs distincts', count(distinct motif_annulation_app)::text,
       '23 environ'
  from public.app_affaire_ledger where motif_annulation_app is not null
union all
-- ⭐⭐ LE CONTROLE QUI DONNE SON SENS AU LOT : le « quand » et le « pourquoi »
--   sur la MEME ligne. C'est ce que C3 + C4 devaient produire.
select 'lignes qui portent LA DATE ET LE MOTIFS', count(*)::text,
       '> 0 -- le quand ET le pourquoi reunis'
  from public.app_affaire_ledger
 where motif_annulation_app is not null and date_annulation_app is not null
union all
select 'motifs SANS date (perimetre different)', count(*)::text, 'compte, pas interdit'
  from public.app_affaire_ledger
 where motif_annulation_app is not null and date_annulation_app is null
union all
select 'la sauvegarde est FERMEE', count(*)::text, '0'
  from information_schema.role_table_grants
 where table_schema='public' and table_name='app_affaire_avant_c4_20261117'
   and grantee in ('authenticated','anon')
union all
select 'VOISINES -- les 450 dates de C3', count(*)::text, '450'
  from public.app_affaire_ledger where date_annulation_app is not null
union all
select 'VOISINES -- les 195 notes de C5', count(*)::text, '195'
  from public.app_affaire_note where origine = 'classeur'
order by 1;
