-- Retour arrière de patch_ged_m9a_pieces_personnes_2026-11-13.sql : retire le registre des pièces d'identité, ses deux
-- portes et l'interrupteur ged_lecture_personnes. ⚠ Le registre part avec le schéma : s'il n'est pas vide, en faire
-- d'abord une copie datée HORS de l'API, par exemple dans un schéma non exposé.
-- Les lectures (app_ged_lecture, app_ged_valeur) restent : elles ne portent aucune valeur privée.
begin;
delete from public.app_setting where key = 'ged_lecture_personnes';
drop function if exists public.app_ged_piece_privee_lire(uuid);
drop function if exists public.app_ged_piece_privee_ecrire(uuid, jsonb);
drop schema if exists ged_prive cascade;
do $controle$
begin
  if exists (select 1 from pg_namespace where nspname = 'ged_prive') then raise exception 'contrôle : le schéma est resté'; end if;
  if exists (select 1 from pg_proc where proname in ('app_ged_piece_privee_ecrire', 'app_ged_piece_privee_lire')) then raise exception 'contrôle : une fonction est restée'; end if;
  if exists (select 1 from public.app_setting where key = 'ged_lecture_personnes') then raise exception 'contrôle : l''interrupteur est resté'; end if;
  if to_regclass('public.app_ged_lecture') is null or to_regclass('public.app_ged_valeur') is null then raise exception 'contrôle : une table des lectures a disparu !'; end if;
end
$controle$;
commit;
