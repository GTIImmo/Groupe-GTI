-- RETOUR ARRIÈRE — patch_ged_m2_classer_2026-11-12.sql (CHANTIER GED, morceau 2).
-- Retire la fonction app_ged_classer et la colonne app_ged_classement.app_console_job_id.
-- ⛔ Il REFUSE si un classement porte déjà un travail (une vraie saisie) : sauvegarder d'abord.
-- Il ne juge que SA part : les tables du morceau 1 restent.
begin;
set local lock_timeout = '3s';

do $garde$
begin
  if exists (select 1 from information_schema.columns where table_schema = 'public'
              and table_name = 'app_ged_classement' and column_name = 'app_console_job_id')
     and exists (select 1 from public.app_ged_classement where app_console_job_id is not null) then
    raise exception 'ARRET : des classements portent un travail -- sauvegarder avant tout retour arriere.';
  end if;
end
$garde$;

drop function if exists public.app_ged_classer(uuid, text, text, text, text, text);
drop index if exists public.app_ged_classement_un_par_travail_uidx;
alter table public.app_ged_classement drop column if exists app_console_job_id;

do $verif$
begin
  if to_regprocedure('public.app_ged_classer(uuid,text,text,text,text,text)') is not null
     or exists (select 1 from information_schema.columns where table_schema = 'public'
                 and table_name = 'app_ged_classement' and column_name = 'app_console_job_id') then
    raise exception 'ARRET : il reste une trace du morceau 2. Annule.';
  end if;
  if to_regclass('public.app_ged_classement') is null then
    raise exception 'ARRET : la table du morceau 1 a disparu. Annule.';
  end if;
end
$verif$;

commit;
