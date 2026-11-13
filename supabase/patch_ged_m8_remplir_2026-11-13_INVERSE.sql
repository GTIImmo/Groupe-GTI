-- Retour arrière de patch_ged_m8_remplir_2026-11-13.sql : retire la table des décisions, sa porte d'écriture et
-- l'interrupteur ged_remplir. ⚠ Les décisions gardées partent avec la table : en faire une copie datée d'abord
-- s'il y en a (create table app_ged_decision_avant_inverse_AAAAMMJJ as select * from public.app_ged_decision;).
-- Les valeurs DÉJÀ remplies sur les fiches restent (elles ont été écrites par les gestes existants).
begin;
drop function if exists public.app_ged_decider(text, uuid, text, text, text, text, jsonb);
drop table if exists public.app_ged_decision;
delete from public.app_setting where key = 'ged_remplir';
do $controle$
begin
  if to_regclass('public.app_ged_decision') is not null then raise exception 'contrôle : la table est restée'; end if;
  if exists (select 1 from pg_proc where proname = 'app_ged_decider') then raise exception 'contrôle : la fonction est restée'; end if;
  if exists (select 1 from public.app_setting where key = 'ged_remplir') then raise exception 'contrôle : l''interrupteur est resté'; end if;
  if to_regclass('public.app_ged_lecture') is null then raise exception 'contrôle : app_ged_lecture a disparu !'; end if;
end
$controle$;
commit;
