-- GED morceau 6, lot 3 (12/11/2026) -- le PV d'assemblée générale devient un type LU (« vas-y, lot 3 », 12/11 soir, §12.15).
-- Le catalogue l'avait rangé « classer » (lu plus tard) ; la colonne n'est qu'une étiquette (seul « jamais_envoye »
-- change un comportement, DepotDocuments.tsx) : on l'aligne pour que la base dise la vérité.
-- Retour arrière : patch_ged_m6_lot3_pv_lu_2026-11-12_INVERSE.sql
begin;

do $$
begin
  if (select lecture from public.app_ged_type where code = 'copro.pv_ag') is distinct from 'classer' then
    raise exception 'copro.pv_ag n''est pas « classer » : quelqu''un est passé avant, on s''arrête';
  end if;
end $$;

update public.app_ged_type set lecture = 'lue' where code = 'copro.pv_ag' and lecture = 'classer';

do $$
begin
  if (select lecture from public.app_ged_type where code = 'copro.pv_ag') <> 'lue' then
    raise exception 'contrôle : copro.pv_ag n''est pas « lue »';
  end if;
end $$;

commit;
