-- Répétition de patch_assistant_parcours_memoire_2026-11-19.sql SANS RIEN GARDER : pose, contrôle, rejoue l'INVERSE,
-- et ANNULE (rollback). À coller tel quel ; chaque contrôle lève une exception s'il est ROUGE, et le dernier lève
-- « TOUT EST VERT » EXPRÈS pour que rien ne reste, même par un outil qui commite.
-- ⚠ Aucune personne réelle n'est touchée : l'auteur et « l'autre » sont des numéros tirés au hasard ; le négociateur et
--   l'admin sont des profils réels, mais seule leur LECTURE est jouée, et rien n'est gardé.
begin;
set local lock_timeout = '3s';

-- ═══════════════ (le corps du patch, recopié sans son begin/commit)
do $garde$
begin
  if to_regclass('public.app_assistant_conversation') is null then raise exception 'ARRET : app_assistant_conversation absente'; end if;
  if to_regclass('public.app_assistant_parcours') is not null then raise exception 'ARRET : app_assistant_parcours existe deja -- patch deja applique ?'; end if;
  if exists (select 1 from pg_namespace where nspname = 'assistant_prive') then raise exception 'ARRET : assistant_prive existe deja'; end if;
  if exists (select 1 from pg_proc where pronamespace = 'public'::regnamespace and proname in
             ('app_assistant_parcours_du_negociateur', 'app_assistant_mandant_deposer', 'app_assistant_mandant_prendre',
              'app_assistant_parcours_purger', 'app_assistant_parcours_maj_le')) then
    raise exception 'ARRET : une des fonctions existe deja';
  end if;
  if exists (select 1 from cron.job where jobname = 'assistant-parcours-purge') then raise exception 'ARRET : la tache de purge existe deja'; end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LA MÉMOIRE DU PARCOURS
create table public.app_assistant_parcours (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null,
  conversation_id  uuid references public.app_assistant_conversation (id) on delete set null,
  genre            text not null,
  app_dossier_id   bigint,
  reponses         jsonb not null default '{}'::jsonb,
  etape            text,
  etat             text not null default 'en_cours',
  cree_le          timestamptz not null default now(),
  maj_le           timestamptz not null default now(),
  termine_le       timestamptz,
  constraint app_assistant_parcours_genre check (genre in ('creation_estimation', 'creation_annonce', 'avis')),
  constraint app_assistant_parcours_etat check (etat in ('en_cours', 'termine', 'abandonne')),
  constraint app_assistant_parcours_reponses_objet check (jsonb_typeof(reponses) = 'object'),
  -- ⛔ règle du 18/11 : les coordonnées d'un nouveau mandant n'entrent JAMAIS ici (elles vivent dans assistant_prive)
  constraint app_assistant_parcours_sans_coordonnees check (not (reponses ?| array['email', 'telephone', 'mandant_email', 'mandant_telephone']))
);
create index app_assistant_parcours_user_idx on public.app_assistant_parcours (user_id, maj_le desc);
create index app_assistant_parcours_dossier_idx on public.app_assistant_parcours (app_dossier_id) where app_dossier_id is not null;
create index app_assistant_parcours_conversation_idx on public.app_assistant_parcours (conversation_id);
create index app_assistant_parcours_maj_idx on public.app_assistant_parcours (maj_le);

comment on table public.app_assistant_parcours is
  'Assistant IA (étape 4 chap. 6, P3, 19/11/2026) : un parcours guidé et ses réponses, aux noms des cases de la '
  'fenêtre. Écrite par le serveur seul. Lue par l''auteur, le négociateur de l''annonce et l''admin. Effacée 30 jours '
  'après son dernier mouvement. Ne porte JAMAIS de coordonnées (voir assistant_prive.mandant_coordonnees).';

create function public.app_assistant_parcours_maj_le() returns trigger
language plpgsql
set search_path to 'public'
as $function$
begin
  new.maj_le := now();
  return new;
end
$function$;
revoke all on function public.app_assistant_parcours_maj_le() from public, anon, authenticated, service_role;
create trigger app_assistant_parcours_maj_le before update on public.app_assistant_parcours
  for each row execute function public.app_assistant_parcours_maj_le();

-- le négociateur de l'annonce : son e-mail de profil ACTIF est celui de la fiche (même règle que les droits du chantier ②)
create function public.app_assistant_parcours_du_negociateur(p_app_dossier_id bigint) returns boolean
language sql
stable
security definer
set search_path to 'public'
as $function$
  select p_app_dossier_id is not null and exists (
    select 1
      from public.app_dossier_current d
      join public.app_user_profile p on p.id = auth.uid() and p.is_active
     where d.app_dossier_id = p_app_dossier_id
       and nullif(btrim(p.email), '') is not null
       and lower(btrim(d.negociateur_email)) = lower(btrim(p.email))
  );
$function$;
comment on function public.app_assistant_parcours_du_negociateur(bigint) is
  'P3 (19/11/2026) : vrai si la personne connectée (profil actif) est le négociateur de cette annonce.';
revoke all on function public.app_assistant_parcours_du_negociateur(bigint) from public, anon, service_role;
grant execute on function public.app_assistant_parcours_du_negociateur(bigint) to authenticated;

alter table public.app_assistant_parcours enable row level security;
revoke all on table public.app_assistant_parcours from public, anon, authenticated;
grant select on table public.app_assistant_parcours to authenticated;
create policy app_assistant_parcours_select on public.app_assistant_parcours
  for select to authenticated
  using (user_id = (select auth.uid())
         or (select public.is_app_admin())
         or public.app_assistant_parcours_du_negociateur(app_dossier_id));

-- ─────────────────────────────────────────────────────── ② LES COORDONNÉES D'UN NOUVEAU MANDANT (À PART)
create schema assistant_prive;
revoke all on schema assistant_prive from public, anon, authenticated, service_role;
comment on schema assistant_prive is
  'Assistant IA (P3, 19/11/2026) : coordonnées d''un nouveau mandant saisies dans la conversation. NON exposé par '
  'l''API, non recopié par la descente. Accès par public.app_assistant_mandant_deposer / _prendre seulement.';

create table assistant_prive.mandant_coordonnees (
  parcours_id  uuid primary key references public.app_assistant_parcours (id) on delete cascade,
  user_id      uuid not null,
  coordonnees  jsonb not null,
  depose_le    timestamptz not null default now(),
  constraint mandant_coordonnees_objet check (jsonb_typeof(coordonnees) = 'object'),
  constraint mandant_coordonnees_cles check (
    (coordonnees - array['civilite', 'nom', 'prenom', 'email', 'telephone', 'adresse', 'cp', 'ville']) = '{}'::jsonb)
);
create index mandant_coordonnees_depose_idx on assistant_prive.mandant_coordonnees (depose_le);
alter table assistant_prive.mandant_coordonnees enable row level security;
revoke all on table assistant_prive.mandant_coordonnees from public, anon, authenticated, service_role;
comment on table assistant_prive.mandant_coordonnees is
  'P3 (19/11/2026) : coordonnées d''un nouveau mandant, une ligne par parcours. Déposées par l''écran de l''auteur, '
  'PRISES (rendues puis effacées) par l''écran qui ouvre la fenêtre. Jamais lues par le serveur de l''assistant.';

create function public.app_assistant_mandant_deposer(p_parcours_id uuid, p_coordonnees jsonb) returns integer
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_user    uuid := auth.uid();
  v_inconnu text;
  v_propre  jsonb;
begin
  -- P3 (19/11/2026). L'écran de l'AUTEUR seul, sur SON parcours de création en cours. Rend le nombre de cases gardées.
  if v_user is null then raise exception '%', 'Connexion requise.'; end if;
  if not exists (select 1 from public.app_assistant_parcours t
                  where t.id = p_parcours_id and t.user_id = v_user and t.etat = 'en_cours' and t.genre like 'creation%') then
    raise exception '%', 'Parcours introuvable.';
  end if;
  if p_coordonnees is null or jsonb_typeof(p_coordonnees) <> 'object' then raise exception '%', 'Coordonnées attendues en objet.'; end if;
  select k into v_inconnu from jsonb_object_keys(p_coordonnees) k
   where k <> all (array['civilite', 'nom', 'prenom', 'email', 'telephone', 'adresse', 'cp', 'ville']) limit 1;
  if v_inconnu is not null then raise exception 'Case inconnue : %', v_inconnu; end if;
  -- une case vide n'est pas gardée
  select coalesce(jsonb_object_agg(e.key, btrim(e.value)), '{}'::jsonb) into v_propre
    from jsonb_each_text(p_coordonnees) e where nullif(btrim(e.value), '') is not null;
  if v_propre = '{}'::jsonb then
    delete from assistant_prive.mandant_coordonnees where parcours_id = p_parcours_id;
    return 0;
  end if;
  insert into assistant_prive.mandant_coordonnees (parcours_id, user_id, coordonnees, depose_le)
  values (p_parcours_id, v_user, v_propre, now())
  on conflict (parcours_id) do update set coordonnees = excluded.coordonnees, depose_le = excluded.depose_le;
  return (select count(*) from jsonb_object_keys(v_propre));
end
$function$;
comment on function public.app_assistant_mandant_deposer(uuid, jsonb) is
  'P3 (19/11/2026) : l''écran de l''auteur dépose les coordonnées d''un nouveau mandant. Clé de service EXCLUE.';
revoke all on function public.app_assistant_mandant_deposer(uuid, jsonb) from public, anon, service_role;
grant execute on function public.app_assistant_mandant_deposer(uuid, jsonb) to authenticated;

create function public.app_assistant_mandant_prendre(p_parcours_id uuid) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_user  uuid := auth.uid();
  v_coord jsonb;
begin
  -- P3 (19/11/2026). Rend les coordonnées ET LES EFFACE : la fenêtre les a reçues (règle du 19/11). Auteur ou admin.
  -- Un second appel rend null. Un parcours d'un autre : refus sans rien dire de plus.
  if v_user is null then raise exception '%', 'Connexion requise.'; end if;
  if not exists (select 1 from public.app_assistant_parcours t
                  where t.id = p_parcours_id and (t.user_id = v_user or public.is_app_admin())) then
    raise exception '%', 'Parcours introuvable.';
  end if;
  delete from assistant_prive.mandant_coordonnees where parcours_id = p_parcours_id returning coordonnees into v_coord;
  return v_coord;
end
$function$;
comment on function public.app_assistant_mandant_prendre(uuid) is
  'P3 (19/11/2026) : rend les coordonnées d''un nouveau mandant à l''écran qui ouvre la fenêtre, et les efface. '
  'Auteur ou admin. Clé de service EXCLUE.';
revoke all on function public.app_assistant_mandant_prendre(uuid) from public, anon, service_role;
grant execute on function public.app_assistant_mandant_prendre(uuid) to authenticated;

-- ─────────────────────────────────────────────────────── ③ L'EFFACEMENT À 30 JOURS
create function public.app_assistant_parcours_purger() returns integer
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_n integer;
begin
  -- P3 (19/11/2026). Appelée par pg_cron chaque nuit. Les coordonnées partent avec leur parcours (cascade).
  delete from assistant_prive.mandant_coordonnees where depose_le < now() - interval '30 days';
  delete from public.app_assistant_parcours where maj_le < now() - interval '30 days';
  get diagnostics v_n = row_count;
  return v_n;
end
$function$;
comment on function public.app_assistant_parcours_purger() is
  'P3 (19/11/2026) : efface les parcours sans mouvement depuis 30 jours (et leurs coordonnées). pg_cron seul.';
revoke all on function public.app_assistant_parcours_purger() from public, anon, authenticated, service_role;

select cron.schedule('assistant-parcours-purge', '15 3 * * *', 'select public.app_assistant_parcours_purger()');

-- ─────────────────────────────────────────────────────── LES VÉRIFICATIONS AVANT DE VALIDER
do $verif$
begin
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'app_assistant_parcours') <> 1 then
    raise exception 'ARRET : il faut exactement 1 regle de lecture';
  end if;
  if has_table_privilege('authenticated', 'public.app_assistant_parcours', 'insert')
     or has_table_privilege('authenticated', 'public.app_assistant_parcours', 'update')
     or has_table_privilege('authenticated', 'public.app_assistant_parcours', 'delete')
     or has_table_privilege('anon', 'public.app_assistant_parcours', 'select') then
    raise exception 'ARRET : un droit d''ecriture ou anonyme reste ouvert sur le parcours';
  end if;
  if not has_table_privilege('service_role', 'public.app_assistant_parcours', 'insert') then
    raise exception 'ARRET : le serveur (service_role) ne peut pas ecrire le parcours';
  end if;
  if has_schema_privilege('authenticated', 'assistant_prive', 'usage') or has_schema_privilege('anon', 'assistant_prive', 'usage')
     or has_schema_privilege('service_role', 'assistant_prive', 'usage') then
    raise exception 'ARRET : le schema prive est ouvert';
  end if;
  if has_function_privilege('service_role', 'public.app_assistant_mandant_prendre(uuid)', 'execute')
     or has_function_privilege('service_role', 'public.app_assistant_mandant_deposer(uuid, jsonb)', 'execute')
     or has_function_privilege('anon', 'public.app_assistant_mandant_prendre(uuid)', 'execute') then
    raise exception 'ARRET : la cle de service ou anon atteint les coordonnees';
  end if;
  if not exists (select 1 from cron.job where jobname = 'assistant-parcours-purge' and schedule = '15 3 * * *') then
    raise exception 'ARRET : la tache de purge n''est pas posee';
  end if;
end
$verif$;

-- ─────────────────────────────────────────────────────── LES CONTRÔLES (chaque rouge lève une exception)
-- Mise en scène en propriétaire ; seul l'APPEL testé passe dans le rôle de la personne (leçon du 06/11).
create function pg_temp.comme(p_uid uuid, p_role text, p_sql text) returns text
language plpgsql as $f$
declare
  r text;
begin
  perform set_config('request.jwt.claims', json_build_object('sub', p_uid, 'role', p_role)::text, true);
  begin
    execute format('set local role %I', p_role);
    execute p_sql into r;
    execute 'reset role';
  exception when others then
    execute 'reset role';
    r := 'ERREUR: ' || sqlerrm;
  end;
  return r;
end
$f$;

do $controle$
declare
  v_admin   uuid;
  v_nego    uuid;
  v_dossier bigint;
  v_auteur  uuid := gen_random_uuid();   -- un auteur sans profil : la règle « l'auteur lit » ne dépend que de user_id
  v_autre   uuid := gen_random_uuid();   -- quelqu'un d'autre, ni auteur, ni négociateur, ni admin
  v_p       uuid;
  v_vieux   uuid;
  v_touche  uuid;
  n         integer;
  r         text;
  j         jsonb;
  lire      text;
  ok        integer := 0;
begin
  select id into v_admin from public.app_user_profile where is_active and role::text = 'admin' limit 1;
  select p.id, d.app_dossier_id into v_nego, v_dossier
    from public.app_user_profile p
    join public.app_dossier_current d on lower(btrim(d.negociateur_email)) = lower(btrim(p.email))
   where p.is_active and p.role::text <> 'admin' and nullif(btrim(p.email), '') is not null
   order by d.app_dossier_id limit 1;
  if v_admin is null or v_nego is null then raise exception 'PAS PU MESURER : il faut un admin actif et un négociateur actif non admin'; end if;

  -- ① la table refuse des coordonnées dans les réponses, et un genre inconnu
  begin
    insert into public.app_assistant_parcours (user_id, genre, reponses) values (v_auteur, 'creation_estimation', '{"email":"x@exemple.invalid"}');
    raise exception 'ROUGE ① : un e-mail est entré dans les réponses';
  exception when check_violation then ok := ok + 1;
  end;
  begin
    insert into public.app_assistant_parcours (user_id, genre) values (v_auteur, 'vente');
    raise exception 'ROUGE ① : un genre inconnu est passé';
  exception when check_violation then ok := ok + 1;
  end;

  -- ② le parcours, posé comme le posera le serveur, encore SANS annonce
  insert into public.app_assistant_parcours (user_id, genre, reponses, etape)
  values (v_auteur, 'creation_estimation', '{"surface":"85","cp":"42700"}', 'q4') returning id into v_p;
  lire := format('select count(*)::text from public.app_assistant_parcours where id = %L', v_p);

  -- ③ avant l'annonce : l'auteur et l'admin lisent ; le négociateur et un autre, non
  if pg_temp.comme(v_auteur, 'authenticated', lire) <> '1' then raise exception 'ROUGE ③ : l''auteur ne lit pas son parcours'; end if;
  if pg_temp.comme(v_admin, 'authenticated', lire) <> '1' then raise exception 'ROUGE ③ : l''admin ne lit pas'; end if;
  if pg_temp.comme(v_nego, 'authenticated', lire) <> '0' then raise exception 'ROUGE ③ : le négociateur lit avant que l''annonce existe'; end if;
  if pg_temp.comme(v_autre, 'authenticated', lire) <> '0' then raise exception 'ROUGE ③ : un autre lit le parcours'; end if;
  if pg_temp.comme(null, 'anon', lire) not like 'ERREUR:%' then raise exception 'ROUGE ③ : anon atteint la table'; end if;
  ok := ok + 5;

  -- ④ l'annonce existe : SON négociateur lit (témoin positif), l'autre toujours pas
  update public.app_assistant_parcours set app_dossier_id = v_dossier where id = v_p;
  if pg_temp.comme(v_nego, 'authenticated', lire) <> '1' then raise exception 'ROUGE ④ : le négociateur de l''annonce ne lit pas'; end if;
  if pg_temp.comme(v_autre, 'authenticated', lire) <> '0' then raise exception 'ROUGE ④ : un autre lit après l''annonce'; end if;
  if pg_temp.comme(v_auteur, 'authenticated', lire) <> '1' then raise exception 'ROUGE ④ : l''auteur a perdu son parcours'; end if;
  ok := ok + 3;

  -- ⑤ personne n'écrit le parcours depuis l'écran
  r := pg_temp.comme(v_auteur, 'authenticated',
         format('insert into public.app_assistant_parcours (user_id, genre) values (%L, %L) returning id::text', v_auteur, 'avis'));
  if r not like 'ERREUR:%' then raise exception 'ROUGE ⑤ : l''écran a écrit un parcours (%)', r; end if;
  r := pg_temp.comme(v_auteur, 'authenticated', format('update public.app_assistant_parcours set etape = %L where id = %L returning id::text', 'x', v_p));
  if r is not null and r not like 'ERREUR:%' then raise exception 'ROUGE ⑤ : l''écran a modifié un parcours'; end if;
  ok := ok + 2;

  -- ⑥ l'auteur dépose : 3 cases gardées (la ville vide ne l'est pas), le nom nettoyé
  r := pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p,
         '{"nom":"  Essai ","email":"essai@exemple.invalid","telephone":"0600000000","ville":""}'));
  if r <> '3' then raise exception 'ROUGE ⑥ : dépôt = %', r; end if;
  select coordonnees into j from assistant_prive.mandant_coordonnees where parcours_id = v_p;
  if j is null or j ->> 'nom' <> 'Essai' or j ? 'ville' or j ->> 'email' <> 'essai@exemple.invalid' then raise exception 'ROUGE ⑥ : gardé = %', j; end if;
  ok := ok + 1;

  -- ⑦ dépôts refusés : un autre ; une case inconnue
  r := pg_temp.comme(v_autre, 'authenticated', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p, '{"nom":"Intrus"}'));
  if r not like 'ERREUR: Parcours introuvable%' then raise exception 'ROUGE ⑦ : un autre a déposé (%)', r; end if;
  r := pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p, '{"iban":"FR76"}'));
  if r not like 'ERREUR: Case inconnue : iban%' then raise exception 'ROUGE ⑦ : une case inconnue est passée (%)', r; end if;
  ok := ok + 2;

  -- ⑧ personne ne lit la table privée directement, ni l'écran ni la clé de service
  if pg_temp.comme(v_auteur, 'authenticated', 'select count(*)::text from assistant_prive.mandant_coordonnees') not like 'ERREUR:%' then
    raise exception 'ROUGE ⑧ : l''écran lit la table privée';
  end if;
  if pg_temp.comme(null, 'service_role', 'select count(*)::text from assistant_prive.mandant_coordonnees') not like 'ERREUR:%' then
    raise exception 'ROUGE ⑧ : la clé de service lit la table privée';
  end if;
  ok := ok + 2;

  -- ⑨ la clé de service (le serveur de l'assistant) n'a PAS la porte de lecture
  r := pg_temp.comme(null, 'service_role', format('select public.app_assistant_mandant_prendre(%L)::text', v_p));
  if r not like 'ERREUR:%' then raise exception 'ROUGE ⑨ : la clé de service a pris les coordonnées (%)', r; end if;
  r := pg_temp.comme(null, 'service_role', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p, '{"nom":"X"}'));
  if r not like 'ERREUR:%' then raise exception 'ROUGE ⑨ : la clé de service a déposé'; end if;
  ok := ok + 2;

  -- ⑩ un autre ne prend rien, et les coordonnées restent en place
  r := pg_temp.comme(v_autre, 'authenticated', format('select public.app_assistant_mandant_prendre(%L)::text', v_p));
  if r not like 'ERREUR: Parcours introuvable%' then raise exception 'ROUGE ⑩ : un autre a pris (%)', r; end if;
  if (select count(*) from assistant_prive.mandant_coordonnees where parcours_id = v_p) <> 1 then raise exception 'ROUGE ⑩ : la tentative a effacé'; end if;
  ok := ok + 1;

  -- ⑪ LA RÈGLE DU 19/11 : la fenêtre prend, et c'est effacé ; une seconde prise ne rend rien
  r := pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_prendre(%L)::text', v_p));
  if r is null or (r::jsonb) ->> 'email' <> 'essai@exemple.invalid' then raise exception 'ROUGE ⑪ : prise = %', r; end if;
  if (select count(*) from assistant_prive.mandant_coordonnees where parcours_id = v_p) <> 0 then raise exception 'ROUGE ⑪ : PAS EFFACÉ après la prise'; end if;
  r := pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_prendre(%L)::text', v_p));
  if r is not null then raise exception 'ROUGE ⑪ : une seconde prise rend %', r; end if;
  ok := ok + 3;

  -- ⑫ l'admin peut prendre (reprise d'un parcours bloqué) ; un dépôt vide efface
  perform pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p, '{"nom":"Essai"}'));
  r := pg_temp.comme(v_admin, 'authenticated', format('select public.app_assistant_mandant_prendre(%L)::text', v_p));
  if r is null or (r::jsonb) ->> 'nom' <> 'Essai' then raise exception 'ROUGE ⑫ : l''admin ne prend pas (%)', r; end if;
  perform pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p, '{"nom":"Essai"}'));
  r := pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p, '{"nom":" ","email":""}'));
  if r <> '0' or exists (select 1 from assistant_prive.mandant_coordonnees where parcours_id = v_p) then raise exception 'ROUGE ⑫ : le dépôt vide n''a pas effacé'; end if;
  ok := ok + 2;

  -- ⑬ un parcours fini, ou un avis, ne reçoit pas de coordonnées
  update public.app_assistant_parcours set etat = 'termine', termine_le = now() where id = v_p;
  r := pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p, '{"nom":"Tard"}'));
  if r not like 'ERREUR: Parcours introuvable%' then raise exception 'ROUGE ⑬ : un parcours fini a reçu des coordonnées'; end if;
  ok := ok + 1;

  -- ⑭ l'effacement à 30 jours : le vieux part AVEC ses coordonnées ; celui qui vient de bouger reste
  insert into public.app_assistant_parcours (user_id, genre, maj_le) values (v_auteur, 'creation_annonce', now() - interval '40 days') returning id into v_vieux;
  insert into assistant_prive.mandant_coordonnees (parcours_id, user_id, coordonnees) values (v_vieux, v_auteur, '{"nom":"Vieux"}');
  insert into public.app_assistant_parcours (user_id, genre, maj_le) values (v_auteur, 'avis', now() - interval '40 days') returning id into v_touche;
  update public.app_assistant_parcours set etape = 'q2' where id = v_touche;   -- le déclencheur doit remettre maj_le à maintenant
  if (select maj_le from public.app_assistant_parcours where id = v_touche) < now() - interval '1 minute' then raise exception 'ROUGE ⑭ : maj_le n''a pas bougé'; end if;
  n := public.app_assistant_parcours_purger();
  if n <> 1 then raise exception 'ROUGE ⑭ : % parcours effacés au lieu de 1', n; end if;
  if exists (select 1 from public.app_assistant_parcours where id = v_vieux) then raise exception 'ROUGE ⑭ : le vieux parcours est resté'; end if;
  if exists (select 1 from assistant_prive.mandant_coordonnees where parcours_id = v_vieux) then raise exception 'ROUGE ⑭ : ses coordonnées sont restées'; end if;
  if not exists (select 1 from public.app_assistant_parcours where id = v_touche) or not exists (select 1 from public.app_assistant_parcours where id = v_p) then
    raise exception 'ROUGE ⑭ : un parcours récent a été effacé';
  end if;
  if pg_temp.comme(v_auteur, 'authenticated', 'select public.app_assistant_parcours_purger()::text') not like 'ERREUR:%' then
    raise exception 'ROUGE ⑭ : l''écran peut lancer la purge';
  end if;
  ok := ok + 4;

  -- ⑮ la tâche de nuit est posée
  if not exists (select 1 from cron.job where jobname = 'assistant-parcours-purge' and schedule = '15 3 * * *' and active) then
    raise exception 'ROUGE ⑮ : la tâche de purge';
  end if;
  ok := ok + 1;

  perform set_config('repetition.ok', ok::text, true);
end
$controle$;

-- ═══════════════ (le corps de l'INVERSE, recopié sans son begin/commit) : il doit tout retirer, et rien d'autre
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

do $fin$
begin
  raise exception 'TOUT EST VERT (% contrôles, patch puis inverse) -- rien ne reste : annulé', current_setting('repetition.ok');
end
$fin$;
rollback;
