-- ═══════════════════════════════════════════════════════════════════════════════
-- ASSISTANT IA — ÉTAPE 3, LOT 1 : LES CARTES DE VALIDATION                  13/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Notes : notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md (le mécanisme) et
--         notice/ETAPE3_CATALOGUE_COMPLET_DES_ACTIONS_2026-11-13.md §5 (lot 1, « Oui enchaîne » du 13/11).
--
-- ─── CE QUE CE PATCH POSE ───
--   app_assistant_action : une action PROPOSÉE par l'assistant, en attente du clic de la personne.
--   Le modèle ne fait JAMAIS un geste : il propose ; le serveur range la proposition ici ; la personne
--   valide ou refuse ; AU CLIC SEULEMENT le serveur exécute la même fonction que l'écran, avec le jeton
--   de la personne. Une ligne = une carte : qui, quel geste, quels paramètres, le résumé affiché, l'état,
--   le résultat. C'est aussi le JOURNAL des actions (qui, quoi, quand) demandé par le plan.
--   ⚠ Les paramètres et le résumé contiennent du texte (commentaire d'une demande, libellé d'une relance) :
--     c'est pourquoi ils vivent ICI et pas dans app_agent_run, qui ne garde jamais de texte (règle de l'étape 1).
--
-- ─── LE CYCLE ───
--   proposee → en_cours (le clic, posé UNE fois par une mise à jour conditionnelle) → executee | echec
--   proposee → refusee (la personne refuse) | expiree (30 min sans réponse : le serveur refuse le clic)
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Il ne touche aucune table métier, ni app_agent_run, ni les conversations.
-- ⛔ AUCUNE ÉCRITURE PAR L'ÉCRAN : seul le serveur (clé de service) écrit dans cette table.
--
-- ─── LES DROITS (patron de l'étape 1) ───
-- Lecture : la personne lit SES cartes, l'admin lit aussi celles des autres (décision du 12/11 :
-- « NON ADMIN AUSSI », pour les conversations ; même règle ici). ⚠ Le manager n'est PAS nommé.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · La descente de 07:45 recopiera cette table (vide au départ). Rien d'autre ne la lit.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_assistant_ia_etape3_cartes_2026-11-13_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_assistant_ia_etape3_cartes_2026-11-13_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_assistant_conversation') is null then
    raise exception 'ARRET : app_assistant_conversation absente (etape 1 non posee ?)';
  end if;
  if to_regclass('public.app_assistant_action') is not null then
    raise exception 'ARRET : app_assistant_action existe deja -- patch deja applique ?';
  end if;
end
$garde$;

create table public.app_assistant_action (
  id               uuid primary key default gen_random_uuid(),
  conversation_id  uuid references public.app_assistant_conversation (id) on delete set null,
  user_id          uuid not null,
  user_email       text,
  geste            text not null,
  parametres       jsonb not null default '{}'::jsonb,
  resume           text not null,
  etat             text not null default 'proposee',
  resultat         jsonb,
  cree_le          timestamptz not null default now(),
  expire_le        timestamptz not null default now() + interval '30 minutes',
  decide_le        timestamptz,
  execute_le       timestamptz,
  constraint app_assistant_action_etat check (etat in ('proposee', 'en_cours', 'executee', 'echec', 'refusee', 'expiree')),
  constraint app_assistant_action_geste_non_vide check (btrim(geste) <> ''),
  constraint app_assistant_action_resume_non_vide check (btrim(resume) <> '')
);
create index app_assistant_action_user_idx on public.app_assistant_action (user_id, cree_le desc);
create index app_assistant_action_conversation_idx on public.app_assistant_action (conversation_id, cree_le);

comment on table public.app_assistant_action is
  'Assistant IA (étape 3, 13/11/2026) : une action proposée par l''assistant, exécutée par le serveur '
  'SEULEMENT au clic de la personne. Écrite par le serveur seul. Lue par la personne, et par l''admin.';

alter table public.app_assistant_action enable row level security;
revoke all on table public.app_assistant_action from public, anon, authenticated;
grant select on table public.app_assistant_action to authenticated;
create policy app_assistant_action_select on public.app_assistant_action
  for select to authenticated
  using (user_id = (select auth.uid()) or (select public.is_app_admin()));

do $verif$
begin
  if (select count(*) from pg_policies where tablename = 'app_assistant_action') <> 1 then
    raise exception 'ARRET : il faut exactement 1 regle de lecture';
  end if;
  if has_table_privilege('authenticated', 'public.app_assistant_action', 'insert')
     or has_table_privilege('authenticated', 'public.app_assistant_action', 'update')
     or has_table_privilege('authenticated', 'public.app_assistant_action', 'delete')
     or has_table_privilege('anon', 'public.app_assistant_action', 'select') then
    raise exception 'ARRET : un droit d''ecriture ou anonyme reste ouvert';
  end if;
  if not has_table_privilege('service_role', 'public.app_assistant_action', 'insert') then
    raise exception 'ARRET : le serveur (service_role) ne peut pas ecrire';
  end if;
end
$verif$;

commit;
