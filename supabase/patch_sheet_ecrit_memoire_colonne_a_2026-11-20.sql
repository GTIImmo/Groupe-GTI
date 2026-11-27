-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER CLASSEUR, ⑬ -- LA MEMOIRE DE CE QUE NOUS ECRIVONS DANS LE SHEET    20/11/2026
--   (le prealable V2 du § 8.2 : « sans elle, on ne distingue pas "la case porte encore
--    NOTRE valeur" de "un humain l'a corrigee" »)
-- ═══════════════════════════════════════════════════════════════════════════════
-- A COLLER PAR FREDERIC dans l'editeur SQL Supabase. Aucun redemarrage, aucun
-- deploiement. Idempotent : le recoller ne change rien.
--
-- ⚠ ELLE REMPLACE LE PATCH DU 16/10 (patch_sheet_memoire_ecriture_2026-10-16.sql), QUI
--   N'A JAMAIS ETE COLLE (la table n'existe pas chez Supabase, verifie le 19/11 et le
--   20/11). Sa clef etait app_chaine_id -- le NUMERO DE CHAINE, qui BOUGE a chaque
--   recalcul des dossiers. Une memoire tenue par une clef qui bouge perd ses lignes en
--   silence. ⛔ NE PAS COLLER L'ANCIEN. S'il etait colle APRES celui-ci, il tomberait en
--   erreur sur son index (pas de colonne app_chaine_id) et la transaction de l'editeur
--   serait annulee ; s'il etait colle AVANT, celui-ci refuse (garde d'entree ci-dessous).
--
-- ─── A QUOI ELLE SERT, EN UNE PHRASE ──────────────────────────────────────────
-- Pour chaque case du Sheet que NOUS avons ecrite : la valeur posee, et ce qu'il y
-- avait avant. Le retour arriere ne vide une case QUE si elle porte encore notre
-- valeur (lecon 31 : il ne juge que SA part) ; toute autre valeur est nommee et laissee.
--
-- ─── LA CLEF : (id_unique, colonne) ───────────────────────────────────────────
--   id_unique  la colonne AL « ID Unique » du Sheet : 4 797 lignes, 4 797 valeurs
--              distinctes, 0 vide (mesure du 19/11). C'est LEUR clef, elle ne bouge
--              pas quand un humain trie ou insere une ligne -- le NUMERO de ligne, lui,
--              bouge (4 794 lignes le 18/11, 4 797 le 19/11). ⛔ Jamais le numero.
--   colonne    le LIBELLE de la colonne en ligne 1 (« affair_uuid »), pas sa lettre :
--              une colonne inseree decalerait les lettres en silence.
--
-- ─── LE CYCLE D'UNE CASE (colonne etat) ───────────────────────────────────────
--   prevu   ecrit AVANT d'envoyer le paquet au Sheet : si l'envoi tombe en panne au
--           milieu, la memoire sait deja ou chercher (le retour arriere lit prevu ET ecrit)
--   ecrit   la case a ete RELUE apres l'envoi et porte notre valeur, sur la bonne ligne
--   defait  le retour arriere l'a videe (defait_le dit quand)
--
-- ─── QUI ECRIT, QUI LIT ───────────────────────────────────────────────────────
--   ECRIT : le seul outil phase2/checks/ecrire_colonne_a_du_sheet_2026-11-20.py, avec la
--           cle de service (qui passe outre la securite par ligne), et SEULEMENT quand
--           ses trois verrous sont ouverts (interrupteur, fichier de vague, empreinte).
--           Tant qu'il dort, la table reste VIDE.
--   LIT   : les managers et admins (un ecran pourra dire un jour « cette case, c'est
--           nous, ecrite tel jour, vague tant »).
--
-- ─── RETOUR ARRIERE ────────────────────────────────────────────────────────────
--   patch_sheet_ecrit_memoire_colonne_a_2026-11-20_INVERSE.sql -- il REFUSE de retirer
--   la table si elle porte une seule ligne (ce serait perdre le moyen de reconnaitre
--   nos cases dans le Sheet).
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU D'ENTREE
-- ---------------------------------------------------------------------
do $garde$
declare n integer;
begin
  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'app_sheet_ecrit' and column_name = 'app_chaine_id';
  if n > 0 then
    raise exception 'ARRET : app_sheet_ecrit existe DEJA avec la forme du 16/10 (clef app_chaine_id). '
                    'Ce n''est pas la meme table : ne rien empiler, me prevenir.';
  end if;

  select count(*) into n from information_schema.tables
   where table_schema = 'public' and table_name = 'app_sheet_ecrit';
  if n = 1 then
    select count(*) into n from information_schema.columns
     where table_schema = 'public' and table_name = 'app_sheet_ecrit' and column_name = 'id_unique';
    if n <> 1 then
      raise exception 'ARRET : app_sheet_ecrit existe avec une forme inconnue (ni id_unique, ni app_chaine_id)';
    end if;
    raise notice 'app_sheet_ecrit existe deja sous cette forme : le patch ne fait que reverifier.';
  end if;

  select count(*) into n from pg_proc p join pg_namespace s on s.oid = p.pronamespace
   where s.nspname = 'public' and p.proname = 'is_app_manager_or_admin';
  if n < 1 then
    raise exception 'ARRET : public.is_app_manager_or_admin() est introuvable (la politique de lecture en a besoin)';
  end if;
end $garde$;

-- ---------------------------------------------------------------------
-- LA TABLE
-- ---------------------------------------------------------------------
create table if not exists public.app_sheet_ecrit (
    id_unique   text        not null,
    colonne     text        not null,
    valeur      text        not null,
    avant       text        not null default '',
    etat        text        not null,
    vague       text        not null,
    ligne_vue   integer,
    ecrit_le    timestamptz not null default now(),
    defait_le   timestamptz,
    origine     text        not null,
    constraint app_sheet_ecrit_pk primary key (id_unique, colonne),
    constraint app_sheet_ecrit_etat_ck check (etat in ('prevu', 'ecrit', 'defait')),
    constraint app_sheet_ecrit_defait_ck check ((etat = 'defait') = (defait_le is not null)),
    constraint app_sheet_ecrit_id_unique_ck check (btrim(id_unique) <> '' and id_unique = btrim(id_unique)),
    constraint app_sheet_ecrit_valeur_ck check (btrim(valeur) <> '')
);

create index if not exists idx_app_sheet_ecrit_vague on public.app_sheet_ecrit (vague, etat);

comment on table public.app_sheet_ecrit is
    'Chantier classeur (20/11/2026) : chaque case du Sheet de suivi que NOUS avons ecrite -- la valeur '
    'posee et ce qu''il y avait avant. Le retour arriere ne vide une case que si elle porte ENCORE notre '
    'valeur ; toute autre valeur est nommee et laissee. Clef = l''ID Unique du Sheet (colonne AL), JAMAIS '
    'le numero de ligne (il bouge). Ecrite par le seul outil ecrire_colonne_a_du_sheet_2026-11-20.py. '
    'Remplace le patch du 16/10 (clef app_chaine_id, qui bouge), jamais colle.';
comment on column public.app_sheet_ecrit.id_unique is
    'La colonne AL « ID Unique » du Sheet : leur clef, stable quand une ligne est triee ou inseree.';
comment on column public.app_sheet_ecrit.colonne is
    'Le LIBELLE de la colonne en ligne 1 (« affair_uuid »), pas sa lettre.';
comment on column public.app_sheet_ecrit.valeur is
    'Ce que NOUS avons ecrit (pour affair_uuid : l''etiquette de dossier app_dossier_uuid).';
comment on column public.app_sheet_ecrit.avant is
    'Ce que la case portait juste avant notre ecriture (pour la colonne A : vide, exige par l''outil).';
comment on column public.app_sheet_ecrit.etat is
    'prevu (ecrit avant l''envoi) -> ecrit (relu apres l''envoi, sur la bonne ligne) -> defait (vide par le retour arriere).';
comment on column public.app_sheet_ecrit.ligne_vue is
    'Le numero de ligne VU au moment d''ecrire. Indicatif SEULEMENT : on ne s''en sert jamais pour adresser.';

-- ---------------------------------------------------------------------
-- LA VISIBILITE -- lecture : managers et admins ; ecriture : la cle de service seule
-- ---------------------------------------------------------------------
alter table public.app_sheet_ecrit enable row level security;

drop policy if exists app_sheet_ecrit_select_manager on public.app_sheet_ecrit;
create policy app_sheet_ecrit_select_manager
on public.app_sheet_ecrit
for select
to authenticated
using ((select public.is_app_manager_or_admin()));

-- ⛔ « revoke from public » ne ferme PAS anon ni authenticated chez Supabase (memoire du
--   projet) : on les nomme. Sans politique d'ecriture, la securite par ligne refuserait
--   deja ; on retire aussi le droit, pour qu'un oubli de RLS un jour ne suffise pas.
revoke insert, update, delete, truncate on public.app_sheet_ecrit from anon, authenticated;
revoke all on public.app_sheet_ecrit from anon;

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU DE SORTIE
-- ---------------------------------------------------------------------
do $garde$
declare rls boolean; pol integer; lignes bigint; cols text; ecrire_anon boolean; ecrire_auth boolean; lire_anon boolean;
begin
  select string_agg(column_name, ',' order by ordinal_position) into cols
    from information_schema.columns where table_schema = 'public' and table_name = 'app_sheet_ecrit';
  if cols is distinct from 'id_unique,colonne,valeur,avant,etat,vague,ligne_vue,ecrit_le,defait_le,origine' then
    raise exception 'Colonnes inattendues : %', cols;
  end if;

  select relrowsecurity into rls from pg_class where oid = 'public.app_sheet_ecrit'::regclass;
  if not coalesce(rls, false) then
    raise exception 'La securite par ligne n''est pas active';
  end if;

  select count(*) into pol from pg_policies where schemaname = 'public' and tablename = 'app_sheet_ecrit';
  if pol <> 1 then
    raise exception 'Politiques : % (attendu 1, la lecture des managers)', pol;
  end if;

  ecrire_anon := has_table_privilege('anon', 'public.app_sheet_ecrit', 'INSERT')
              or has_table_privilege('anon', 'public.app_sheet_ecrit', 'UPDATE')
              or has_table_privilege('anon', 'public.app_sheet_ecrit', 'DELETE');
  ecrire_auth := has_table_privilege('authenticated', 'public.app_sheet_ecrit', 'INSERT')
              or has_table_privilege('authenticated', 'public.app_sheet_ecrit', 'UPDATE')
              or has_table_privilege('authenticated', 'public.app_sheet_ecrit', 'DELETE');
  lire_anon := has_table_privilege('anon', 'public.app_sheet_ecrit', 'SELECT');
  if ecrire_anon or ecrire_auth or lire_anon then
    raise exception 'Droits trop ouverts : ecriture anon %, ecriture authenticated %, lecture anon %',
                    ecrire_anon, ecrire_auth, lire_anon;
  end if;

  select count(*) into lignes from public.app_sheet_ecrit;
  raise notice 'OK : app_sheet_ecrit en place -- 10 colonnes, RLS active, 1 politique de lecture, '
               'ecriture fermee a anon et authenticated. % ligne(s) -- ATTENDU 0 tant que l''outil dort.',
               lignes;
end $garde$;

-- ─── CONTROLE APRES APPLICATION : patch_sheet_ecrit_memoire_colonne_a_2026-11-20_REPETITION.sql
