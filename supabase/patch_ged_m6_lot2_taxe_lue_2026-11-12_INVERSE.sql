-- Retour arrière de patch_ged_m6_lot2_taxe_lue_2026-11-12.sql : la taxe foncière redevient « classer ».
begin;
update public.app_ged_type set lecture = 'classer' where code = 'justif.taxe' and lecture = 'lue';
do $$
begin
  if (select lecture from public.app_ged_type where code = 'justif.taxe') <> 'classer' then
    raise exception 'contrôle : justif.taxe n''est pas revenue à « classer »';
  end if;
end $$;
commit;
