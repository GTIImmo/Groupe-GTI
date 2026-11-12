-- RÉPÉTITION — patch_assistant_ia_etape1_2026-11-12.sql (ASSISTANT IA, étape 1).
-- Pose les deux tables, l'interrupteur et la fiche DANS une transaction, écrit une conversation factice d'un
-- négociateur, la lit à sa place, à la place d'un AUTRE négociateur, puis d'un admin, tente une écriture par l'écran,
-- puis lève une erreur VOLONTAIRE qui porte les verdicts : RIEN n'est gardé. Attendu : « 9 OK, 0 KO ».
begin;
set local lock_timeout = '3s';
do $garde$
begin
  if to_regclass('public.app_assistant_conversation') is not null then raise exception 'ARRET : deja pose'; end if;
  if (select count(*) from public.app_user_profile where is_active and role = 'commercial') < 2 then
    raise exception 'ARRET : il faut deux negociateurs actifs pour l''essai';
  end if;
end
$garde$;

create table public.app_assistant_conversation (
  id uuid primary key default gen_random_uuid(), user_id uuid not null, user_email text,
  agent_key text not null default 'assistant', titre text, archivee boolean not null default false,
  cree_le timestamptz not null default now(), maj_le timestamptz not null default now(),
  constraint app_assistant_conversation_agent_non_vide check (btrim(agent_key) <> ''));
create table public.app_assistant_message (
  id bigint generated always as identity primary key,
  conversation_id uuid not null references public.app_assistant_conversation (id) on delete cascade,
  role text not null, contenu text not null default '', outils jsonb,
  agent_run_id bigint references public.app_agent_run (id) on delete set null,
  cree_le timestamptz not null default now(),
  constraint app_assistant_message_role check (role in ('user', 'assistant')));
alter table public.app_assistant_conversation enable row level security;
alter table public.app_assistant_message      enable row level security;
revoke all on table public.app_assistant_conversation from public, anon, authenticated;
revoke all on table public.app_assistant_message      from public, anon, authenticated;
revoke all on sequence public.app_assistant_message_id_seq from public, anon, authenticated;
grant select on table public.app_assistant_conversation to authenticated;
grant select on table public.app_assistant_message      to authenticated;
create policy app_assistant_conversation_select on public.app_assistant_conversation for select to authenticated
  using (user_id = (select auth.uid()) or (select public.is_app_admin()));
create policy app_assistant_message_select on public.app_assistant_message for select to authenticated
  using (exists (select 1 from public.app_assistant_conversation c where c.id = conversation_id));
insert into public.app_setting (key, value, description, updated_at) values ('assistant_ia', 'off', 'essai', now());
insert into public.app_agent_prompt (agent_key, label, instructions, model, max_output_tokens, is_active, version, updated_by)
select 'assistant', 'Assistant IA (accueil)', '', 'gpt-4.1-mini', 1500, true, 1, 'repetition';

do $essai$
declare v_conv uuid; v_nego uuid; v_autre uuid; v_admin uuid;
        n_nego int; n_msg_nego int; n_autre int; n_msg_autre int; n_admin int;
        ok int := 0; ko int := 0; j text := ''; v_refus text := 'non refuse'; v_role text := 'non refuse'; v_cascade int;
begin
  select id into v_nego  from public.app_user_profile where is_active and role = 'commercial' order by id limit 1;
  select id into v_autre from public.app_user_profile where is_active and role = 'commercial' and id <> v_nego order by id limit 1;
  select id into v_admin from public.app_user_profile where is_active and role = 'admin' order by id limit 1;

  insert into public.app_assistant_conversation (user_id, titre) values (v_nego, 'essai') returning id into v_conv;
  insert into public.app_assistant_message (conversation_id, role, contenu) values (v_conv, 'user', 'qui suis-je ?');
  insert into public.app_assistant_message (conversation_id, role, contenu, outils)
    values (v_conv, 'assistant', 'Tu es ...', '[{"nom": "qui_suis_je", "parametres": {}}]'::jsonb);

  perform set_config('request.jwt.claims', json_build_object('sub', v_nego, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_nego from public.app_assistant_conversation where id = v_conv;
  select count(*) into n_msg_nego from public.app_assistant_message where conversation_id = v_conv;
  begin insert into public.app_assistant_message (conversation_id, role, contenu) values (v_conv, 'user', 'x');
  exception when insufficient_privilege then v_refus := 'refuse'; end;
  reset role;

  perform set_config('request.jwt.claims', json_build_object('sub', v_autre, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_autre from public.app_assistant_conversation where id = v_conv;
  select count(*) into n_msg_autre from public.app_assistant_message where conversation_id = v_conv;
  reset role;

  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_admin from public.app_assistant_conversation where id = v_conv;
  reset role;

  begin insert into public.app_assistant_message (conversation_id, role, contenu) values (v_conv, 'system', 'x');
  exception when check_violation then v_role := 'refuse'; end;
  delete from public.app_assistant_conversation where id = v_conv;
  select count(*) into v_cascade from public.app_assistant_message where conversation_id = v_conv;

  if n_nego = 1 and n_msg_nego = 2 then ok := ok + 1; j := j || E'\nOK  ① le négociateur lit SA conversation et ses 2 messages'; else ko := ko + 1; j := j || E'\nKO  ① ' || n_nego || '/' || n_msg_nego; end if;
  if n_autre = 0 and n_msg_autre = 0 then ok := ok + 1; j := j || E'\nOK  ② un AUTRE négociateur ne la voit pas, ni ses messages'; else ko := ko + 1; j := j || E'\nKO  ② ' || n_autre || '/' || n_msg_autre; end if;
  if n_admin = 1 then ok := ok + 1; j := j || E'\nOK  ③ l''admin la lit (décision du 12/11)'; else ko := ko + 1; j := j || E'\nKO  ③'; end if;
  if v_refus = 'refuse' then ok := ok + 1; j := j || E'\nOK  ④ l''écran ne peut pas écrire un message'; else ko := ko + 1; j := j || E'\nKO  ④'; end if;
  if v_role = 'refuse' then ok := ok + 1; j := j || E'\nOK  ⑤ un rôle de message inconnu est refusé'; else ko := ko + 1; j := j || E'\nKO  ⑤'; end if;
  if v_cascade = 0 then ok := ok + 1; j := j || E'\nOK  ⑥ retirer une conversation emporte ses messages'; else ko := ko + 1; j := j || E'\nKO  ⑥'; end if;
  if not has_table_privilege('anon', 'public.app_assistant_conversation', 'select')
     and not has_table_privilege('anon', 'public.app_assistant_message', 'select') then ok := ok + 1; j := j || E'\nOK  ⑦ la clé publique ne lit rien'; else ko := ko + 1; j := j || E'\nKO  ⑦'; end if;
  if (select value from public.app_setting where key = 'assistant_ia') = 'off' then ok := ok + 1; j := j || E'\nOK  ⑧ l''interrupteur est éteint'; else ko := ko + 1; j := j || E'\nKO  ⑧'; end if;
  if (select count(*) from public.app_agent_prompt where agent_key in ('redacteur', 'avis_valeur', 'scan_fiche', 'assistant')) = 4
     and (select model from public.app_agent_prompt where agent_key = 'assistant') = 'gpt-4.1-mini' then ok := ok + 1; j := j || E'\nOK  ⑨ la fiche assistant (gpt-4.1-mini) s''ajoute aux 3 autres'; else ko := ko + 1; j := j || E'\nKO  ⑨'; end if;
  raise exception 'RÉPÉTITION ASSISTANT IA étape 1 (rien n''est gardé) : % OK, % KO%', ok, ko, j;
end
$essai$;
rollback;
