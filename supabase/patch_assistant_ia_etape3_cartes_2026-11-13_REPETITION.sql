-- RÉPÉTITION — patch_assistant_ia_etape3_cartes_2026-11-13.sql (ASSISTANT IA, étape 3, lot 1 : les cartes).
-- Pose la table DANS une transaction, range une carte factice d'un négociateur, la lit à sa place, à la place d'un
-- AUTRE négociateur, puis d'un admin, tente une écriture par l'écran, rejoue le clic deux fois (une seule passe),
-- puis lève une erreur VOLONTAIRE qui porte les verdicts : RIEN n'est gardé. Attendu : « 8 OK, 0 KO ».
-- ⚠ Pas de « commit » dans ce fichier : il se joue à blanc (leçon du 13/11).
begin;
set local lock_timeout = '3s';
do $garde$
begin
  if to_regclass('public.app_assistant_action') is not null then raise exception 'ARRET : deja pose'; end if;
  if to_regclass('public.app_assistant_conversation') is null then raise exception 'ARRET : etape 1 absente'; end if;
  if (select count(*) from public.app_user_profile where is_active and role = 'commercial') < 2 then
    raise exception 'ARRET : il faut deux negociateurs actifs pour l''essai';
  end if;
end
$garde$;

create table public.app_assistant_action (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references public.app_assistant_conversation (id) on delete set null,
  user_id uuid not null, user_email text, geste text not null,
  parametres jsonb not null default '{}'::jsonb, resume text not null,
  etat text not null default 'proposee', resultat jsonb,
  cree_le timestamptz not null default now(),
  expire_le timestamptz not null default now() + interval '30 minutes',
  decide_le timestamptz, execute_le timestamptz,
  constraint app_assistant_action_etat check (etat in ('proposee', 'en_cours', 'executee', 'echec', 'refusee', 'expiree')),
  constraint app_assistant_action_geste_non_vide check (btrim(geste) <> ''),
  constraint app_assistant_action_resume_non_vide check (btrim(resume) <> ''));
alter table public.app_assistant_action enable row level security;
revoke all on table public.app_assistant_action from public, anon, authenticated;
grant select on table public.app_assistant_action to authenticated;
create policy app_assistant_action_select on public.app_assistant_action for select to authenticated
  using (user_id = (select auth.uid()) or (select public.is_app_admin()));

do $essai$
declare v_carte uuid; v_nego uuid; v_autre uuid; v_admin uuid;
        n_nego int; n_autre int; n_admin int; n_clic1 int; n_clic2 int;
        ok int := 0; ko int := 0; j text := ''; v_refus text := 'non refuse'; v_etat text := 'non refuse'; v_vide text := 'non refuse';
begin
  select id into v_nego  from public.app_user_profile where is_active and role = 'commercial' order by id limit 1;
  select id into v_autre from public.app_user_profile where is_active and role = 'commercial' and id <> v_nego order by id limit 1;
  select id into v_admin from public.app_user_profile where is_active and role = 'admin' order by id limit 1;

  insert into public.app_assistant_action (user_id, geste, parametres, resume)
    values (v_nego, 'creer_relance', '{"label": "essai"}'::jsonb, 'Créer une relance (essai)') returning id into v_carte;

  perform set_config('request.jwt.claims', json_build_object('sub', v_nego, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_nego from public.app_assistant_action where id = v_carte;
  begin update public.app_assistant_action set etat = 'en_cours' where id = v_carte;
  exception when insufficient_privilege then v_refus := 'refuse'; end;
  reset role;

  perform set_config('request.jwt.claims', json_build_object('sub', v_autre, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_autre from public.app_assistant_action where id = v_carte;
  reset role;

  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_admin from public.app_assistant_action where id = v_carte;
  reset role;

  -- le clic du serveur : une mise à jour CONDITIONNELLE, rejouée deux fois -> une seule passe
  update public.app_assistant_action set etat = 'en_cours', decide_le = now()
   where id = v_carte and etat = 'proposee' and expire_le > now();
  get diagnostics n_clic1 = row_count;
  update public.app_assistant_action set etat = 'en_cours', decide_le = now()
   where id = v_carte and etat = 'proposee' and expire_le > now();
  get diagnostics n_clic2 = row_count;

  begin insert into public.app_assistant_action (user_id, geste, resume, etat) values (v_nego, 'x', 'x', 'faite');
  exception when check_violation then v_etat := 'refuse'; end;
  begin insert into public.app_assistant_action (user_id, geste, resume) values (v_nego, 'x', '  ');
  exception when check_violation then v_vide := 'refuse'; end;

  if n_nego = 1 then ok := ok + 1; j := j || E'\nOK  ① le négociateur lit SA carte'; else ko := ko + 1; j := j || E'\nKO  ① ' || n_nego; end if;
  if n_autre = 0 then ok := ok + 1; j := j || E'\nOK  ② un AUTRE négociateur ne la voit pas'; else ko := ko + 1; j := j || E'\nKO  ② ' || n_autre; end if;
  if n_admin = 1 then ok := ok + 1; j := j || E'\nOK  ③ l''admin la lit (même règle que les conversations)'; else ko := ko + 1; j := j || E'\nKO  ③'; end if;
  if v_refus = 'refuse' then ok := ok + 1; j := j || E'\nOK  ④ l''écran ne peut pas valider une carte lui-même'; else ko := ko + 1; j := j || E'\nKO  ④'; end if;
  if n_clic1 = 1 and n_clic2 = 0 then ok := ok + 1; j := j || E'\nOK  ⑤ deux clics : une seule exécution'; else ko := ko + 1; j := j || E'\nKO  ⑤ ' || n_clic1 || '/' || n_clic2; end if;
  if v_etat = 'refuse' then ok := ok + 1; j := j || E'\nOK  ⑥ un état inconnu est refusé'; else ko := ko + 1; j := j || E'\nKO  ⑥'; end if;
  if v_vide = 'refuse' then ok := ok + 1; j := j || E'\nOK  ⑦ une carte sans résumé est refusée'; else ko := ko + 1; j := j || E'\nKO  ⑦'; end if;
  if not has_table_privilege('anon', 'public.app_assistant_action', 'select')
     and not has_table_privilege('authenticated', 'public.app_assistant_action', 'insert') then
    ok := ok + 1; j := j || E'\nOK  ⑧ la clé publique ne lit rien, l''écran n''écrit rien';
  else ko := ko + 1; j := j || E'\nKO  ⑧'; end if;
  raise exception 'RÉPÉTITION ASSISTANT IA étape 3 cartes (rien n''est gardé) : % OK, % KO%', ok, ko, j;
end
$essai$;

rollback;
