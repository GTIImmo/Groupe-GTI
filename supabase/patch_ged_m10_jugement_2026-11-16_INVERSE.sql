-- Retour arrière de patch_ged_m10_jugement_2026-11-16.sql : retire la table des jugements et sa porte d'écriture.
-- ⚠ Les jugements gardés partent avec la table : en faire une copie datée d'abord s'il y en a
-- (create table app_ged_jugement_avant_inverse_AAAAMMJJ as select * from public.app_ged_jugement;).
-- ged_propositions N'EST PAS touché (il existait avant ce patch, et il ouvre les lignes « À regarder »).
begin;
drop function if exists public.app_ged_juger(text, text, text, text, text, text, text);
drop table if exists public.app_ged_jugement;
do $controle$
begin
  if to_regclass('public.app_ged_jugement') is not null then raise exception 'contrôle : la table est restée'; end if;
  if exists (select 1 from pg_proc where proname = 'app_ged_juger') then raise exception 'contrôle : la fonction est restée'; end if;
  if not exists (select 1 from public.app_setting where key = 'ged_propositions') then raise exception 'contrôle : ged_propositions a disparu !'; end if;
  if to_regclass('public.app_ged_decision') is null then raise exception 'contrôle : app_ged_decision a disparu !'; end if;
end
$controle$;
commit;
