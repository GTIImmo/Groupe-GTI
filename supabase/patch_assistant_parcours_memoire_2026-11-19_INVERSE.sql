-- Retour arrière de patch_assistant_parcours_memoire_2026-11-19.sql : retire la mémoire du parcours, le schéma
-- assistant_prive (coordonnées des nouveaux mandants), leurs portes et la tâche de purge.
-- ⚠ Les parcours et les coordonnées partent avec : s'il en reste, ils sont perdus (c'est voulu pour les coordonnées ;
--   pour les parcours, en faire d'abord une copie datée si un parcours en cours doit survivre).
-- Les conversations, les messages et les cartes de l'assistant restent : ce patch ne les touchait pas.
begin;
set local lock_timeout = '3s';
select cron.unschedule(jobid) from cron.job where jobname = 'assistant-parcours-purge';
drop function if exists public.app_assistant_parcours_purger();
drop function if exists public.app_assistant_mandant_prendre(uuid);
drop function if exists public.app_assistant_mandant_deposer(uuid, jsonb);
drop schema if exists assistant_prive cascade;
drop table if exists public.app_assistant_parcours;
drop function if exists public.app_assistant_parcours_du_negociateur(bigint);
drop function if exists public.app_assistant_parcours_maj_le();
do $controle$
begin
  if exists (select 1 from pg_namespace where nspname = 'assistant_prive') then raise exception 'contrôle : le schéma est resté'; end if;
  if to_regclass('public.app_assistant_parcours') is not null then raise exception 'contrôle : la table est restée'; end if;
  if exists (select 1 from pg_proc where pronamespace = 'public'::regnamespace and proname in
             ('app_assistant_parcours_du_negociateur', 'app_assistant_mandant_deposer', 'app_assistant_mandant_prendre',
              'app_assistant_parcours_purger', 'app_assistant_parcours_maj_le')) then
    raise exception 'contrôle : une fonction est restée';
  end if;
  if exists (select 1 from cron.job where jobname = 'assistant-parcours-purge') then raise exception 'contrôle : la tâche est restée'; end if;
  -- sa part seulement : les sœurs de l'assistant sont intactes
  if to_regclass('public.app_assistant_conversation') is null or to_regclass('public.app_assistant_message') is null
     or to_regclass('public.app_assistant_action') is null then
    raise exception 'contrôle : une table de l''assistant a disparu !';
  end if;
end
$controle$;
commit;
