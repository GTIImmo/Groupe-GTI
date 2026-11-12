-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — MORCEAU 6, LOT 1 : GARDER CE QUE L'IA A LU                 12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.11.
--
-- ─── CE QUE CE PATCH POSE ───
--   ① app_ged_lecture  UNE lecture d'un document déposé avec l'outil : son classement, la
--                      fiche de lecture et sa version, le modèle, le coût, l'état. Une relecture
--                      AJOUTE une ligne (la plus récente fait foi) : rien ne s'efface.
--   ② app_ged_valeur   les valeurs lues : une clé de la fiche, la valeur (texte, nombre ou date),
--                      la page, l'état (lu / incertain / non_vu). Une liste (les diagnostics d'un
--                      dossier) porte un rang.
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───
-- ⛔ Il ne touche ni app_console_document, ni le coffre, ni app_ged_classement (une clé
--   étrangère VERS le classement seulement, en cascade : un classement retiré emporte ses
--   lectures).
-- ⛔ AUCUNE ÉCRITURE PAR L'ÉCRAN : seul le serveur (backend Render, clé de service) écrit,
--   après avoir vérifié que le classement est celui de l'utilisateur. L'écran LIT.
-- ⛔ Aucune donnée de naissance, aucun numéro de pièce, aucun IBAN : les fiches de lecture
--   (schéma strict du serveur) ne les demandent pas et ne peuvent pas les rendre.
--
-- ─── LES DROITS ───
-- ⛔ Une table neuve donne PAR DÉFAUT tous les droits à `authenticated` (pg_default_acl) : chaque
--   rôle est nommé. RLS partout. Lecture au MÊME périmètre que les classements (morceau 3) :
--   lecteur global, ou bien du portefeuille. Les valeurs suivent leur lecture.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · La descente de 07:45 recopiera ces deux tables (vides au départ). Rien d'autre ne les lit.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_ged_m6_lecture_2026-11-12_INVERSE.sql. Répétition sans rien garder :
-- supabase/patch_ged_m6_lecture_2026-11-12_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if to_regclass('public.app_ged_classement') is null then raise exception 'ARRET : morceau 1 absent'; end if;
  if to_regclass('public.app_ged_lecture') is not null or to_regclass('public.app_ged_valeur') is not null then
    raise exception 'ARRET : app_ged_lecture ou app_ged_valeur existe deja -- patch deja applique ?';
  end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LES LECTURES
create table public.app_ged_lecture (
  id                 uuid primary key default gen_random_uuid(),
  classement_id      uuid not null references public.app_ged_classement (id) on delete cascade,
  hektor_annonce_id  text not null,
  type_code          text not null references public.app_ged_type (code),
  fiche              text not null,
  modele             text,
  etat               text not null,
  pages_lues         integer[],
  par_texte          boolean not null default false,
  input_tokens       integer,
  output_tokens      integer,
  cout_usd           numeric,
  lu_par             uuid,
  lu_le              timestamptz not null default now(),
  constraint app_ged_lecture_etat check (etat in ('lu', 'incomplet', 'pas_ce_type')),
  constraint app_ged_lecture_annonce_non_vide check (btrim(hektor_annonce_id) <> ''),
  constraint app_ged_lecture_fiche_non_vide check (btrim(fiche) <> '')
);
create index app_ged_lecture_classement_idx on public.app_ged_lecture (classement_id, lu_le desc);
create index app_ged_lecture_annonce_idx on public.app_ged_lecture (hektor_annonce_id);

comment on table public.app_ged_lecture is
  'GED : une lecture par l''IA d''un document déposé avec l''outil (morceau 6, 12/11/2026). Écrite par '
  'le serveur seul. Une relecture ajoute une ligne ; la plus récente fait foi.';

-- ─────────────────────────────────────────────────────── ② LES VALEURS
create table public.app_ged_valeur (
  id           bigint generated always as identity primary key,
  lecture_id   uuid not null references public.app_ged_lecture (id) on delete cascade,
  cle          text not null,
  rang         integer not null default 0,
  valeur       text,
  valeur_num   numeric,
  valeur_date  date,
  page         integer,
  etat         text not null,
  constraint app_ged_valeur_etat check (etat in ('lu', 'incertain', 'non_vu')),
  constraint app_ged_valeur_cle_non_vide check (btrim(cle) <> ''),
  constraint app_ged_valeur_unique unique (lecture_id, cle, rang)
);

comment on table public.app_ged_valeur is
  'GED : une valeur lue (clé de la fiche, valeur, page, état). « non_vu » = pas dans les pages lues, '
  'JAMAIS « absent du document ».';

-- ─────────────────────────────────────────────────────── ③ LES DROITS
alter table public.app_ged_lecture enable row level security;
alter table public.app_ged_valeur  enable row level security;
revoke all on table public.app_ged_lecture from public, anon, authenticated;
revoke all on table public.app_ged_valeur  from public, anon, authenticated;
revoke all on sequence public.app_ged_valeur_id_seq from public, anon, authenticated;

grant select on table public.app_ged_lecture to authenticated;
grant select on table public.app_ged_valeur  to authenticated;
create policy app_ged_lecture_select_scope on public.app_ged_lecture
  for select to authenticated
  using (
    (select public.is_app_global_reader())
    or hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))
  );
-- les valeurs suivent leur lecture : la sous-requête passe elle-même par la règle ci-dessus
create policy app_ged_valeur_select_scope on public.app_ged_valeur
  for select to authenticated
  using (exists (select 1 from public.app_ged_lecture l where l.id = lecture_id));

commit;
