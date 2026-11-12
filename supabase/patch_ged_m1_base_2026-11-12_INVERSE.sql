-- RETOUR ARRIÈRE — patch_ged_m1_base_2026-11-12.sql (CHANTIER GED, morceau 1).
-- Retire les 4 tables app_ged_* et les 3 interrupteurs ged_*.
-- ⛔ Il REFUSE si un classement, un rattachement ou une ligne de journal existe : ce serait une vraie saisie
--   (« une saisie ne se perd jamais »). Dans ce cas, sauvegarder d'abord, puis décider.
-- ⛔ Il refuse aussi si un interrupteur n'est plus éteint : éteindre d'abord, c'est le premier geste du retour.
-- Il ne juge que SA part (leçon 31) : il vérifie à la fin qu'il ne reste aucune trace de ce patch, et que
-- app_console_document n'a pas été touchée.
begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_ged_classement') is not null
     and exists (select 1 from public.app_ged_classement) then
    raise exception 'ARRET : app_ged_classement porte des saisies -- sauvegarder avant tout retour arriere.';
  end if;
  if to_regclass('public.app_ged_rattachement') is not null
     and exists (select 1 from public.app_ged_rattachement) then
    raise exception 'ARRET : app_ged_rattachement porte des saisies -- sauvegarder avant tout retour arriere.';
  end if;
  if to_regclass('public.app_ged_journal') is not null
     and exists (select 1 from public.app_ged_journal) then
    raise exception 'ARRET : app_ged_journal porte des lignes -- sauvegarder avant tout retour arriere.';
  end if;
  if exists (select 1 from public.app_setting
              where key in ('ged_depot_multiple', 'ged_lecture_ia', 'ged_propositions')
                and coalesce(value, '') <> 'off') then
    raise exception 'ARRET : un interrupteur ged_* n''est pas eteint -- l''eteindre d''abord.';
  end if;
end
$garde$;

drop table if exists public.app_ged_journal;
drop table if exists public.app_ged_rattachement;
drop table if exists public.app_ged_classement;
drop table if exists public.app_ged_type;
delete from public.app_setting where key in ('ged_depot_multiple', 'ged_lecture_ia', 'ged_propositions');

do $verif$
begin
  if exists (select 1 from information_schema.tables
              where table_schema = 'public' and table_name like 'app\_ged\_%') then
    raise exception 'ARRET : il reste une table app_ged_*. Annule.';
  end if;
  if exists (select 1 from public.app_setting
              where key in ('ged_depot_multiple', 'ged_lecture_ia', 'ged_propositions')) then
    raise exception 'ARRET : il reste un interrupteur ged_*. Annule.';
  end if;
  if (select count(*) from pg_constraint where confrelid = 'public.app_console_document'::regclass) <> 1 then
    raise exception 'ARRET : les cles etrangeres vers app_console_document ont change (attendu : 1, la signature). Annule.';
  end if;
end
$verif$;

commit;
