-- ═══════════════════════════════════════════════════════════════════════════
-- C2 -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- ═══════════════════════════════════════════════════════════════════════════

select 'commissions posees par C2' as controle, count(*)::text as mesure,
       '62' as attendu
  from public.app_affaire_ledger
 where app_affaire_id in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817) and honoraires_entree_app is not null
union all
select 'les 4 saisies de l app, INTACTES', count(*)::text, '4'
  from public.app_affaire_ledger
 where honoraires_entree_app is not null and app_affaire_id not in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817)
union all
select 'aucun montant zero, negatif ou illisible', count(*)::text, '0'
  from public.app_affaire_ledger
 where honoraires_entree_app is not null
   and (honoraires_entree_app !~ '^[0-9]+(\.[0-9]+)?$'
        or honoraires_entree_app::numeric <= 0)
union all
select 'la somme posee', to_char(sum(honoraires_entree_app::numeric), 'FM999G999G999'),
       '158 537 + 283 480 EUR'
  from public.app_affaire_ledger
 where app_affaire_id in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817) and honoraires_entree_app is not null
union all
-- ⭐⭐ LE CONTROLE QUI COMPTE VRAIMENT : les 270 cibles des affaires ANNULEES
--   doivent rester VIDES. C'est la decision de Frederic du 17/11, et c'est la seule
--   chose que ce patch pourrait abimer sans qu'on le voie.
-- ⛔ Ma premiere version de ce controle portait « and false » : il rendait 0 PAR
--   CONSTRUCTION et ne verifiait RIEN. Un controle vide est pire qu'aucun controle.
select 'les 270 annulees sont restees VIDES', count(*)::text,
       '0 -- decision du 17/11'
  from public.app_affaire_ledger
 where honoraires_entree_app is not null
   and app_affaire_id in (30648, 28908, 20, 17243, 4623, 11365, 16249, 8926, 1000126, 27243, 9362, 4130, 28857, 23888, 28787, 25742, 28839, 25753, 1103, 4134, 28733, 28633, 15032, 11963, 4722, 19750, 28974, 4544, 28555, 6203, 27372, 24337, 28687, 23037, 28762, 3697, 14962, 4421, 4578, 9898, 20405, 15925, 16223, 28631, 15051, 27247, 7185, 14143, 4587, 19466, 24453, 2451, 14824, 28584, 28728, 23500, 24573, 28956, 4923, 29000, 17429, 19102, 11560, 4668, 28725, 14819, 28736, 2499, 4272, 27560, 24381, 27461, 3631, 4484, 15072, 11524, 14961, 24542, 7731, 4255, 1203, 23417, 6450, 4192, 26102, 24168, 19142, 26043, 6204, 26, 19512, 25752, 21963, 16861, 7452, 27526, 8917, 27687, 16393, 27427, 17215, 20267, 8911, 6208, 25867, 8868, 17642, 7180, 4372, 11885, 9300, 6445, 28148, 24335, 4719, 14964, 4653, 8918, 15020, 24165, 11523, 26026, 14968, 4358, 27404, 7943, 11596, 7273, 20296, 24166, 17026, 6215, 7250, 4633, 27448, 1105, 25880, 1089, 15915, 24311, 10018, 23025, 14114, 22024, 23983, 27185, 4290, 10027, 16858, 19830, 11193, 4293, 20513, 11188, 19746, 11767, 1589, 8910, 24333, 4655, 4271, 24094, 15002, 24478, 27610, 14810, 24121, 17205, 19693, 26831, 17521, 16051, 7598, 4790, 22210, 11972, 4389, 7761, 14941, 11447, 4472, 21884, 6557, 15042, 23447, 4463, 16382, 16018, 19818, 7606, 17377, 17390, 7907, 24589, 17401, 19472, 14817, 8925, 4321, 20075, 11411, 9359, 19112, 27196, 23426, 16185, 4388, 16134, 7904, 23335, 24336, 24652, 11581, 14922, 11561, 17410, 19009, 17411, 4353, 23053, 16017, 6379, 6603, 27052, 14085, 26070, 10730, 16169, 9905, 25735, 4498, 4799, 19473, 27556, 6138, 27470, 161, 24610, 15103, 14812, 19277, 7667, 15073, 27533, 27280, 19463, 9447, 26852, 22216, 22209, 26106, 17291, 16344, 24401, 17136, 28996, 20227, 28975, 28905, 989, 28731, 25710, 28907, 29025, 30645, 1000316, 19049, 14823, 28931, 28340)
union all
select 'la sauvegarde est FERMEE', count(*)::text, '0'
  from information_schema.role_table_grants
 where table_schema='public' and table_name='app_affaire_avant_c2_20261117'
   and grantee in ('authenticated','anon')
union all
select 'VOISINES -- les 450 dates de C3', count(*)::text, '450'
  from public.app_affaire_ledger where date_annulation_app is not null
union all
select 'VOISINES -- vente_reglee_app', count(*)::text, '3729'
  from public.app_affaire_ledger where vente_reglee_app is not null
order by 1;
