-- Retour arrière de patch_ged_garder_lecture_2026-11-18.sql : retire la porte « garder la lecture » et rend au journal
-- de la GED son CHECK d'avant (classement, rattachement).
-- ⚠ S'il existe des lignes « lecture » au journal, des lectures ont DÉJÀ été gardées : le retour arrière S'ARRÊTE
--   (le CHECK d'avant les refuserait, et elles sont l'historique d'une décision humaine). Les lectures gardées restent
--   « lu » : ce retour arrière ne juge que SA part (la porte), pas les décisions prises avec elle.
begin;
set local lock_timeout = '3s';
do $garde$
declare n int;
begin
  select count(*) into n from public.app_ged_journal where objet = 'lecture';
  if n > 0 then
    raise exception 'ARRET : % lecture(s) deja gardee(s) au journal -- a trancher par Frederic avant tout retour arriere', n;
  end if;
end
$garde$;
drop function if exists public.app_ged_lecture_garder(uuid);
alter table public.app_ged_journal drop constraint app_ged_journal_objet;
alter table public.app_ged_journal add constraint app_ged_journal_objet
  check (objet = any (array['classement'::text, 'rattachement'::text]));
do $controle$
begin
  if exists (select 1 from pg_proc where proname = 'app_ged_lecture_garder') then raise exception 'contrôle : la fonction est restée'; end if;
  if (select pg_get_constraintdef(oid) from pg_constraint where conrelid = 'public.app_ged_journal'::regclass and conname = 'app_ged_journal_objet')
     like '%lecture%' then raise exception 'contrôle : le CHECK accepte encore « lecture »'; end if;
  if not exists (select 1 from public.app_setting where key = 'ged_lecture_ia') then raise exception 'contrôle : ged_lecture_ia a disparu !'; end if;
end
$controle$;
commit;
