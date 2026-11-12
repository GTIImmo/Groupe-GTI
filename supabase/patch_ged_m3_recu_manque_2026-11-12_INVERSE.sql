-- RETOUR ARRIÈRE — patch_ged_m3_recu_manque_2026-11-12.sql (CHANTIER GED, morceau 3).
-- Retire la règle de lecture du classement, le droit SELECT d'authenticated, et l'interrupteur ged_recu_manque.
-- Aucune donnée n'est touchée : les classements restent (écrits par app_ged_classer), simplement plus lisibles par l'écran.
-- ⛔ Il refuse si l'interrupteur n'est pas éteint : l'éteindre d'abord.
begin;
set local lock_timeout = '3s';

do $garde$
begin
  if exists (select 1 from public.app_setting where key = 'ged_recu_manque' and coalesce(value, '') <> 'off') then
    raise exception 'ARRET : ged_recu_manque n''est pas eteint -- l''eteindre d''abord.';
  end if;
end
$garde$;

drop policy if exists app_ged_classement_select_scope on public.app_ged_classement;
revoke select on table public.app_ged_classement from authenticated;
delete from public.app_setting where key = 'ged_recu_manque';

do $verif$
begin
  if exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'app_ged_classement')
     or exists (select 1 from information_schema.role_table_grants where table_schema = 'public'
                 and table_name = 'app_ged_classement' and grantee = 'authenticated')
     or exists (select 1 from public.app_setting where key = 'ged_recu_manque') then
    raise exception 'ARRET : il reste une trace du morceau 3. Annule.';
  end if;
end
$verif$;

commit;
