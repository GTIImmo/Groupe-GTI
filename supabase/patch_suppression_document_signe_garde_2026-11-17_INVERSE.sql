-- RETOUR ARRIÈRE de patch_suppression_document_signe_garde_2026-11-17.sql
-- Retire le garde et ses deux fonctions, puis vérifie qu'il ne reste RIEN (un retour arrière ne juge que SA part).
-- Après lui, la base se comporte comme avant le 17/11 : un travail de suppression n'est plus contrôlé sur la signature
-- (l'écran et le worker gardent leurs propres verrous, à défaire par git si besoin).

drop trigger if exists app_console_job_refus_suppression_signe_trg on public.app_console_job;
drop function if exists public.app_console_job_refus_suppression_signe();
drop function if exists public.app_document_signature_engagee(jsonb);

do $$
begin
  if exists (select 1 from pg_trigger where tgrelid = 'public.app_console_job'::regclass
               and tgname = 'app_console_job_refus_suppression_signe_trg') then
    raise exception 'INVERSE INCOMPLET : le garde est encore la';
  end if;
  if to_regprocedure('public.app_console_job_refus_suppression_signe()') is not null
     or to_regprocedure('public.app_document_signature_engagee(jsonb)') is not null then
    raise exception 'INVERSE INCOMPLET : une fonction est encore la';
  end if;
  -- Les autres gardes de la table sont intacts (on ne juge que notre part, mais on vérifie de ne pas avoir débordé).
  if (select count(*) from pg_trigger where tgrelid = 'public.app_console_job'::regclass and not tgisinternal) < 3 then
    raise exception 'INVERSE A DEBORDE : un autre garde de app_console_job a disparu';
  end if;
  raise notice 'INVERSE OK : le garde et ses fonctions sont retires, les 3 autres gardes de la table sont la.';
end $$;
