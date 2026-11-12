-- RETOUR ARRIÈRE — patch_assistant_ia_etape1_2026-11-12.sql (ASSISTANT IA, étape 1).
-- Retire app_assistant_message, app_assistant_conversation, l'interrupteur assistant_ia et la fiche « assistant ».
-- ⛔ Refuse s'il existe déjà une conversation (elle a coûté des appels et peut servir) : la retirer d'abord, en le
-- décidant. Les lignes « assistant » de app_agent_run RESTENT (le journal des coûts ne s'efface pas).
-- Ne touche à RIEN d'autre (autres interrupteurs, autres fiches, journal des agents).
begin;
set local lock_timeout = '3s';
do $garde$
begin
  if to_regclass('public.app_assistant_conversation') is null then raise exception 'ARRET : rien a retirer'; end if;
  if exists (select 1 from public.app_assistant_conversation) then
    raise exception 'ARRET : % conversation(s) deja ecrite(s) -- les retirer d''abord, en le decidant',
      (select count(*) from public.app_assistant_conversation);
  end if;
end
$garde$;
drop table public.app_assistant_message;
drop table public.app_assistant_conversation;
delete from public.app_setting where key = 'assistant_ia';
delete from public.app_agent_prompt where agent_key = 'assistant';
do $verif$
begin
  if to_regclass('public.app_assistant_conversation') is not null or to_regclass('public.app_assistant_message') is not null then
    raise exception 'ARRET : une table reste';
  end if;
  if exists (select 1 from pg_policies where tablename in ('app_assistant_conversation', 'app_assistant_message')) then
    raise exception 'ARRET : une regle de lecture reste';
  end if;
  if exists (select 1 from public.app_setting where key = 'assistant_ia')
     or exists (select 1 from public.app_agent_prompt where agent_key = 'assistant') then
    raise exception 'ARRET : l''interrupteur ou la fiche reste';
  end if;
  if (select count(*) from public.app_agent_prompt where agent_key in ('redacteur', 'avis_valeur', 'scan_fiche')) <> 3 then
    raise exception 'ARRET : une fiche d''un autre agent a disparu';
  end if;
  if to_regclass('public.app_agent_run') is null then raise exception 'ARRET : le journal des agents a disparu'; end if;
end
$verif$;
commit;
