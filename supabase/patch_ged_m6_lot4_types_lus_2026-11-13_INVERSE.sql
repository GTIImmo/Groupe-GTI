-- Retour arrière de patch_ged_m6_lot4_types_lus_2026-11-13.sql : l'amiante, le plomb, les termites et le règlement
-- redeviennent « classer ». Les 10 autres types du lot 4 étaient déjà « lue » avant le patch : on n'y touche pas.
begin;
update public.app_ged_type set lecture = 'classer'
 where code in ('diag.amiante', 'diag.plomb', 'diag.termites', 'copro.reglement') and lecture = 'lue';
do $$
begin
  if (select count(*) from public.app_ged_type
      where code in ('diag.amiante', 'diag.plomb', 'diag.termites', 'copro.reglement') and lecture = 'classer') <> 4 then
    raise exception 'contrôle : les 4 types ne sont pas revenus à « classer »';
  end if;
end $$;
commit;
