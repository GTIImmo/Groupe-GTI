-- GED morceau 6, lot 2 (12/11/2026) -- la taxe foncière devient un type LU (décision de Frédéric du 12/11 soir, §12.14).
-- Le catalogue l'avait rangée « classer » (lue plus tard) ; la colonne n'est qu'une étiquette (seul « jamais_envoye »
-- change un comportement, DepotDocuments.tsx) : on l'aligne pour que la base dise la vérité.
-- Retour arrière : patch_ged_m6_lot2_taxe_lue_2026-11-12_INVERSE.sql
begin;

do $$
begin
  if (select lecture from public.app_ged_type where code = 'justif.taxe') is distinct from 'classer' then
    raise exception 'justif.taxe n''est pas « classer » : quelqu''un est passé avant, on s''arrête';
  end if;
end $$;

update public.app_ged_type set lecture = 'lue' where code = 'justif.taxe' and lecture = 'classer';

do $$
begin
  if (select lecture from public.app_ged_type where code = 'justif.taxe') <> 'lue' then
    raise exception 'contrôle : justif.taxe n''est pas « lue »';
  end if;
end $$;

commit;
