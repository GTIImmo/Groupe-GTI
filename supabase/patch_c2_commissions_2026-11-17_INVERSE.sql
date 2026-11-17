-- ═══════════════════════════════════════════════════════════════════════════
-- C2 -- RETOUR ARRIERE
-- ⭐ Il ne vide que les 62 cibles de ce lot, et REFUSE de se jouer si une
--   valeur a change depuis la pose.
-- ⚠ Il NE TOUCHE PAS aux 4 saisies de l'app qui existaient avant le 17/11.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare changees integer;
begin
  with attendu(app_affaire_id, montant) as (values
      (27346, '6000'),
    (28668, '8000'),
    (8884, '9000'),
    (28948, '7500'),
    (30761, '8000'),
    (29028, '10000'),
    (27011, '12000'),
    (28878, '15000'),
    (30778, '7000'),
    (30716, '15200'),
    (30743, '2900'),
    (14137, '2337'),
    (998, '1000'),
    (28665, '13000'),
    (28962, '10000'),
    (29032, '7000'),
    (7113, '6400'),
    (25846, '5700'),
    (28952, '5000'),
    (28656, '7500'),
    (29015, '7000'),
    (30688, '6000'),
    (30784, '4000'),
    (30706, '2500'),
    (30729, '5000'),
    (30692, '11000'),
    (30742, '11000'),
    (30744, '10000'),
    (30759, '9500'),
    (28995, '4000'),
    (29020, '500'),
    (28985, '1700'),
    (30763, '9000'),
    (30768, '4000'),
    (30786, '9000'),
    (30815, '9000'),
    (30735, '10000'),
    (30804, '10000'),
    (30796, '12400'),
    (28568, '4000'),
    (30713, '6580'),
    (30707, '8000'),
    (30792, '4000'),
    (30764, '5000'),
    (30658, '3500'),
    (30808, '10500'),
    (30816, '3500'),
    (30785, '8000'),
    (1000320, '4600'),
    (30775, '2000'),
    (30758, '4000'),
    (30741, '5000'),
    (30806, '3900'),
    (30803, '9000'),
    (30802, '14000'),
    (1000318, '1800'),
    (30756, '10000'),
    (30705, '10000'),
    (30797, '7000'),
    (30747, '8000'),
    (30702, '5500'),
    (30817, '10000')
  )
  select count(*) into changees
    from attendu a join public.app_affaire_ledger l using (app_affaire_id)
   where coalesce(l.honoraires_entree_app, '') <> a.montant;
  if changees <> 0 then
    raise exception '⛔ ARRET : % ligne(s) ne portent plus la valeur de C2.', changees;
  end if;
  raise notice '✅ les 62 cibles portent bien les valeurs de C2.';
end $$;

update public.app_affaire_ledger
   set honoraires_entree_app = null
 where app_affaire_id in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817);

do $$
declare reste integer; autres integer;
begin
  select count(*) into reste from public.app_affaire_ledger
   where app_affaire_id in (27346, 28668, 8884, 28948, 30761, 29028, 27011, 28878, 30778, 30716, 30743, 14137, 998, 28665, 28962, 29032, 7113, 25846, 28952, 28656, 29015, 30688, 30784, 30706, 30729, 30692, 30742, 30744, 30759, 28995, 29020, 28985, 30763, 30768, 30786, 30815, 30735, 30804, 30796, 28568, 30713, 30707, 30792, 30764, 30658, 30808, 30816, 30785, 1000320, 30775, 30758, 30741, 30806, 30803, 30802, 1000318, 30756, 30705, 30797, 30747, 30702, 30817) and honoraires_entree_app is not null;
  if reste <> 0 then
    raise exception '⛔ il reste % ligne(s) du lot.', reste;
  end if;
  select count(*) into autres from public.app_affaire_ledger
   where honoraires_entree_app is not null;
  if autres <> 4 then
    raise exception '⛔⛔ % saisies de l''app au lieu de 4 : le retour arriere a '
      'deborde sur des saisies humaines. GRAVE.', autres;
  end if;
  raise notice '✅ 62 retirees . LES 4 SAISIES DE L''APP SONT INTACTES.';
end $$;

commit;
