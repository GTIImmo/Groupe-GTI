-- Retour arrière de patch_ged_m6_lot3_pv_lu_2026-11-12.sql : le PV d'AG redevient « classer ».
begin;
update public.app_ged_type set lecture = 'classer' where code = 'copro.pv_ag' and lecture = 'lue';
do $$
begin
  if (select lecture from public.app_ged_type where code = 'copro.pv_ag') <> 'classer' then
    raise exception 'contrôle : copro.pv_ag n''est pas revenue à « classer »';
  end if;
end $$;
commit;
