-- ═══════════════════════════════════════════════════════════════════════════════
-- ASSISTANT IA — ÉTAPE 1 : LE SOCLE DORMANT                                  12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note de l'étape : notice/ETAPE1_SOCLE_ASSISTANT_IA_2026-11-12.md §3 pièce 2.
-- Plan : notice/PLAN_DEV_ACCUEIL_ASSISTANT_IA_2026-10-29.md.
--
-- ─── CE QUE CE PATCH POSE ───
--   ① app_assistant_conversation  une conversation : à qui, quel agent, un titre, les dates, archivée ou non.
--   ② app_assistant_message       le fil : la question, la réponse, les fonctions appelées et leurs
--                                 paramètres, relié à la ligne de app_agent_run du tour.
--   ③ l'interrupteur assistant_ia = 'off' dans app_setting (patron à trois crans off / admin / on).
--   ④ la fiche « assistant » dans app_agent_prompt (gpt-4.1-mini, décision du 29/10).
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Il ne touche ni app_agent_run (le tour y écrit une ligne SANS texte, colonnes existantes),
--   ni les fiches des autres agents, ni aucun objet métier.
-- ⛔ AUCUNE ÉCRITURE PAR L'ÉCRAN : seul le serveur (backend Render, clé de service) écrit.
--
-- ─── LES DROITS ───
-- ⛔ Une table neuve donne PAR DÉFAUT tous les droits à `authenticated` (pg_default_acl) : chaque
--   rôle est nommé. RLS partout.
-- Lecture : chacun lit SES conversations, et l'admin lit aussi celles des autres
--   (décision de Frédéric du 12/11 : « NON ADMIN AUSSI »). ⚠ Le manager n'est PAS nommé :
--   ne pas l'ajouter sans lui demander. Les messages suivent leur conversation.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · La descente de 07:45 recopiera ces deux tables (vides au départ). Rien d'autre ne les lit.
--   · app_setting et app_agent_prompt reçoivent une ligne chacune : aucun autre code ne lit ces clés.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_assistant_ia_etape1_2026-11-12_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_assistant_ia_etape1_2026-11-12_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_agent_run') is null then raise exception 'ARRET : app_agent_run absente'; end if;
  if to_regclass('public.app_assistant_conversation') is not null or to_regclass('public.app_assistant_message') is not null then
    raise exception 'ARRET : app_assistant_conversation ou app_assistant_message existe deja -- patch deja applique ?';
  end if;
  if exists (select 1 from public.app_setting where key = 'assistant_ia') then
    raise exception 'ARRET : l''interrupteur assistant_ia existe deja';
  end if;
  if exists (select 1 from public.app_agent_prompt where agent_key = 'assistant') then
    raise exception 'ARRET : la fiche assistant existe deja dans app_agent_prompt';
  end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LES CONVERSATIONS
create table public.app_assistant_conversation (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null,
  user_email  text,
  agent_key   text not null default 'assistant',
  titre       text,
  archivee    boolean not null default false,
  cree_le     timestamptz not null default now(),
  maj_le      timestamptz not null default now(),
  constraint app_assistant_conversation_agent_non_vide check (btrim(agent_key) <> '')
);
create index app_assistant_conversation_user_idx on public.app_assistant_conversation (user_id, maj_le desc);

comment on table public.app_assistant_conversation is
  'Assistant IA : une conversation (étape 1, 12/11/2026). Écrite par le serveur seul. Lue par la personne, '
  'et par l''admin (décision du 12/11).';

-- ─────────────────────────────────────────────────────── ② LES MESSAGES
create table public.app_assistant_message (
  id               bigint generated always as identity primary key,
  conversation_id  uuid not null references public.app_assistant_conversation (id) on delete cascade,
  role             text not null,
  contenu          text not null default '',
  outils           jsonb,
  agent_run_id     bigint references public.app_agent_run (id) on delete set null,
  cree_le          timestamptz not null default now(),
  constraint app_assistant_message_role check (role in ('user', 'assistant'))
);
create index app_assistant_message_conversation_idx on public.app_assistant_message (conversation_id, id);

comment on table public.app_assistant_message is
  'Assistant IA : un message du fil. « outils » = les fonctions appelées par l''agent pendant le tour '
  '(nom et paramètres). Le journal app_agent_run, lui, ne garde jamais le texte.';

-- ─────────────────────────────────────────────────────── LES DROITS
alter table public.app_assistant_conversation enable row level security;
alter table public.app_assistant_message      enable row level security;
revoke all on table public.app_assistant_conversation from public, anon, authenticated;
revoke all on table public.app_assistant_message      from public, anon, authenticated;
revoke all on sequence public.app_assistant_message_id_seq from public, anon, authenticated;

grant select on table public.app_assistant_conversation to authenticated;
grant select on table public.app_assistant_message      to authenticated;
create policy app_assistant_conversation_select on public.app_assistant_conversation
  for select to authenticated
  using (user_id = (select auth.uid()) or (select public.is_app_admin()));
-- les messages suivent leur conversation : la sous-requête passe elle-même par la règle ci-dessus
create policy app_assistant_message_select on public.app_assistant_message
  for select to authenticated
  using (exists (select 1 from public.app_assistant_conversation c where c.id = conversation_id));

-- ─────────────────────────────────────────────────────── ③ L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at) values
  ('assistant_ia', 'off',
   'Assistant IA (étape 1, 12/11/2026) : off = personne, admin = les admins seuls, on = tout compte actif. '
   'Relu à chaque question par le serveur.', now());
-- ALLUMER pour les admins : update public.app_setting set value = 'admin', updated_at = now() where key = 'assistant_ia';
-- ÉTEINDRE                : update public.app_setting set value = 'off',   updated_at = now() where key = 'assistant_ia';

-- ─────────────────────────────────────────────────────── ④ LA FICHE DE L'AGENT
-- Les consignes vides ici = le serveur garde son défaut EN CODE (agent_registry) ; la ligne porte le
-- modèle et le plafond de sortie, modifiables sans redéployer.
insert into public.app_agent_prompt (agent_key, label, instructions, model, max_output_tokens, is_active, version, updated_by)
select 'assistant', 'Assistant IA (accueil)', '', 'gpt-4.1-mini', 1500, true, 1, 'patch_assistant_ia_etape1_2026-11-12';

do $verif$
begin
  if (select count(*) from pg_policies where tablename in ('app_assistant_conversation', 'app_assistant_message')) <> 2 then
    raise exception 'ARRET : il faut exactement 2 regles de lecture';
  end if;
  if has_table_privilege('authenticated', 'public.app_assistant_message', 'insert')
     or has_table_privilege('authenticated', 'public.app_assistant_conversation', 'insert')
     or has_table_privilege('anon', 'public.app_assistant_conversation', 'select') then
    raise exception 'ARRET : un droit d''ecriture ou anonyme reste ouvert';
  end if;
  if (select value from public.app_setting where key = 'assistant_ia') <> 'off' then
    raise exception 'ARRET : l''interrupteur n''est pas eteint';
  end if;
end
$verif$;

commit;
