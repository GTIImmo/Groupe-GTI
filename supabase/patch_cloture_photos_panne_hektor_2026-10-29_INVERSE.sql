-- =============================================================================
--  INVERSE -- retire les 277 clotures de la panne du 28-29/10        29/10/2026
-- =============================================================================
--  Ne touche QUE les lignes posees par patch_cloture_photos_panne_hektor_2026-10-29.sql
--  (double marque : resolved_by ET payload_json.lot). Les autres resolutions, et
--  les travaux eux-memes, ne sont pas touches. Apres lui, les 277 travaux
--  reapparaissent dans l'ecran et dans les alertes, comme avant le patch.
-- =============================================================================
begin;

do $$
declare
  v_lignes int;
  v_retire int;
begin
  select count(*) into v_lignes
    from public.app_pending_resolution
   where objet = 'geste'
     and resolved_by = 'cloture_panne_hektor_2026-10-29'
     and payload_json->>'lot' = 'cloture_panne_hektor_2026-10-29';

  if v_lignes not in (0, 277) then
    raise exception 'ARRET : % lignes marquees au lieu de 277 -- rien n''est retire', v_lignes;
  end if;

  delete from public.app_pending_resolution
   where objet = 'geste'
     and resolved_by = 'cloture_panne_hektor_2026-10-29'
     and payload_json->>'lot' = 'cloture_panne_hektor_2026-10-29';
  get diagnostics v_retire = row_count;

  -- Un retour arriere ne juge que SA part : il ne doit rester aucune trace du lot.
  if exists (select 1 from public.app_pending_resolution
              where payload_json->>'lot' = 'cloture_panne_hektor_2026-10-29') then
    raise exception 'ARRET : il reste des lignes du lot -- tout est annule';
  end if;
  raise notice 'OK : % cloture(s) retiree(s)', v_retire;
end
$$;

commit;
