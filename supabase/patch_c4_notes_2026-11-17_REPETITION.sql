-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (2e patch) -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- ═══════════════════════════════════════════════════════════════════════════

select 'notes de F' as controle, count(*)::text as mesure, '256' as attendu
  from public.app_affaire_note where origine = 'classeur:F'
union all
select 'notes de G', count(*)::text, '3484'
  from public.app_affaire_note where origine = 'classeur:G'
union all
select 'notes de F+G (une ligne qui porte les deux)', count(*)::text, '585'
  from public.app_affaire_note where origine = 'classeur:F+G'
union all
select '⭐ LES 195 NOTES DE C5, INTACTES ET DISCERNABLES', count(*)::text, '195'
  from public.app_affaire_note where origine = 'classeur'
union all
select 'aucune note vide', count(*)::text, '0'
  from public.app_affaire_note
 where origine in ('classeur:F','classeur:G','classeur:F+G') and btrim(coalesce(texte,'')) = ''
union all
select 'toutes portent la marque du lot', count(*)::text, '0'
  from public.app_affaire_note
 where origine in ('classeur:F','classeur:G','classeur:F+G')
   and ecrit_par is distinct from 'classeur:C4:2026-11-17'
union all
select 'toutes rattachees a une CHAINE', count(*)::text, '0'
  from public.app_affaire_note
 where origine in ('classeur:F','classeur:G','classeur:F+G') and app_chaine_id is null
union all
select 'textes DISTINCTS (le vocabulaire est varie)',
       count(distinct texte)::text, 'proche du total'
  from public.app_affaire_note where origine in ('classeur:F','classeur:G','classeur:F+G')
union all
select 'VOISINES -- les 169 motifs de C4', count(*)::text, '169'
  from public.app_affaire_ledger where motif_annulation_app is not null
union all
select 'VOISINES -- les 450 dates de C3', count(*)::text, '450'
  from public.app_affaire_ledger where date_annulation_app is not null
order by 1;
