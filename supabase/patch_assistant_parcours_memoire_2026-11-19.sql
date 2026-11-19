-- ═══════════════════════════════════════════════════════════════════════════════
-- ASSISTANT IA — ÉTAPE 4, CHAPITRE 6, P3 : LA MÉMOIRE DU PARCOURS GUIDÉ          19/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §85 (qui lit), §89.2 (P3), §91 (ce patch).
-- Ses mots : « La mémoire accessible par le négociateur de l'annonce ou admin » (18/11) ; « je valide ta reco de
-- règle » (19/11) = les coordonnées d'un nouveau mandant s'effacent DÈS QUE LA FENÊTRE LES A REÇUES.
--
-- ─── CE QUE CE PATCH POSE ───
--   ① app_assistant_parcours : un parcours guidé (création d'une estimation ou d'une annonce, avis de valeur) et ses
--      réponses, dans la LANGUE DE LA FENÊTRE (les noms de ses cases). Écrite par le serveur seul (clé de service).
--      Lue par : son AUTEUR ; le NÉGOCIATEUR DE L'ANNONCE dès qu'elle existe ; l'ADMIN. ⚠ Le manager n'est pas nommé.
--   ② le schéma assistant_prive et sa table mandant_coordonnees : civilité, nom, prénom, e-mail, téléphone, adresse,
--      CP, ville d'un NOUVEAU mandant saisis dans la conversation. Deux portes seulement :
--        · app_assistant_mandant_deposer()  l'ÉCRAN de l'auteur, droit dans la base ;
--        · app_assistant_mandant_prendre()  l'ÉCRAN qui ouvre la fenêtre : rend les coordonnées ET LES EFFACE
--          (une seule lecture possible ; c'est la règle du 19/11).
--      ⛔ LA CLÉ DE SERVICE N'A AUCUNE DES DEUX PORTES : le serveur de l'assistant (celui qui parle au modèle) ne peut
--        ni les écrire ni les lire, même par erreur. Elles ne vont donc jamais au modèle, ni dans
--        app_assistant_message, ni dans le résumé d'une carte (règle du 18/11).
--   ③ app_assistant_parcours_purger() et la tâche pg_cron « assistant-parcours-purge » (04:15 heure de Paris) :
--      un parcours sans mouvement depuis 30 jours s'efface, et ses coordonnées avec lui (proposition du §80.8) ;
--      des coordonnées jamais prises s'effacent aussi à 30 jours.
--
-- ─── POURQUOI UN SCHÉMA À PART (patron de ged_prive, GED morceau 9) ───
--   · l'API n'expose que public : aucune table de assistant_prive n'est lisible directement par un rôle de l'app ;
--   · la descente de 07:45 (phase2/sync/pull_from_supabase.py) découvre les tables par la spec de l'API : elle ne
--     voit pas assistant_prive, donc ne recopie PAS ces coordonnées sur le serveur local (ni dans la sauvegarde).
--   · app_assistant_parcours, elle, SERA recopiée par la descente : elle ne porte aucune coordonnée (une contrainte
--     refuse les clés email / telephone dans les réponses).
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Il ne touche ni les conversations, ni les messages, ni les cartes, ni app_agent_run, ni aucune table métier.
-- ⛔ Personne ne l'appelle encore : le moteur de questions (P1) et l'écran (P2, D7) viendront à part. Table vide.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · la descente recopiera app_assistant_parcours (vide au départ) ; rien d'autre ne la lit ;
--   · une tâche pg_cron de plus (14 aujourd'hui) : un DELETE sur une petite table, une fois par jour.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_assistant_parcours_memoire_2026-11-19_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_assistant_parcours_memoire_2026-11-19_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

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

commit;
