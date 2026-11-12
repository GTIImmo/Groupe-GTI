-- RETOUR ARRIÈRE — patch_ged_m6_lecture_2026-11-12.sql (CHANTIER GED, morceau 6, lot 1).
-- Retire app_ged_valeur et app_ged_lecture. ⛔ Refuse s'il existe déjà une lecture (elle a coûté un appel et peut
-- servir) : la retirer d'abord, en le décidant. Ne touche à RIEN d'autre (classements, documents, interrupteurs).
begin;
set local lock_timeout = '3s';
do $garde$
begin
  if to_regclass('public.app_ged_lecture') is null then raise exception 'ARRET : rien a retirer'; end if;
  if exists (select 1 from public.app_ged_lecture) then
    raise exception 'ARRET : % lecture(s) deja ecrite(s) -- les retirer d''abord, en le decidant', (select count(*) from public.app_ged_lecture);
  end if;
end
$garde$;
drop table public.app_ged_valeur;
drop table public.app_ged_lecture;
do $verif$
begin
  if to_regclass('public.app_ged_lecture') is not null or to_regclass('public.app_ged_valeur') is not null then
    raise exception 'ARRET : une table reste';
  end if;
  if exists (select 1 from pg_policies where tablename in ('app_ged_lecture', 'app_ged_valeur')) then
    raise exception 'ARRET : une regle de lecture reste';
  end if;
  if to_regclass('public.app_ged_classement') is null then raise exception 'ARRET : le classement a disparu'; end if;
end
$verif$;
commit;
