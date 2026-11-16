-- ═══════════════════════════════════════════════════════════════════════════
-- C9 (1re moitie) -- RETOUR ARRIERE
-- ⭐ « Un retour arriere ne juge que SA part » : il ne retire QUE les lignes
--   marquees `classeur:C9:2026-11-16`, et il verifie ensuite qu'il n'en reste aucune.
-- ⛔ IL NE SUPPRIME PAS LA TABLE : elle vient de B1, pas de ce patch.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare mienne integer; total integer;
begin
  select count(*) into mienne from public.app_classeur_avis
   where ecrit_par = 'classeur:C9:2026-11-16';
  select count(*) into total from public.app_classeur_avis;
  if mienne <> 2588 then
    raise exception '⛔ ARRET : % ligne(s) de ce lot au lieu de 2588. Quelqu''un est '
      'passe apres nous -- ne RIEN retirer sans relire.', mienne;
  end if;
  raise notice '✅ 2588 lignes du lot retrouvees (la table en porte % en tout).', total;
end $$;

delete from public.app_classeur_avis where ecrit_par = 'classeur:C9:2026-11-16';

do $$
declare reste integer; autres integer;
begin
  select count(*) into reste from public.app_classeur_avis
   where ecrit_par = 'classeur:C9:2026-11-16';
  if reste <> 0 then
    raise exception '⛔ il reste % ligne(s) du lot.', reste;
  end if;
  select count(*) into autres from public.app_classeur_avis;
  raise notice '✅ 2588 lignes retirees . la table porte encore % ligne(s), posee(s) '
    'par autre chose que C9 (0 attendu au 16/11).', autres;
end $$;

commit;
