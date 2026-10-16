-- ═══════════════════════════════════════════════════════════════════════════════
-- LOT 2 — LA MEMOIRE DE CE QUE NOUS ECRIVONS DANS LE CLASSEUR    16/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage, aucun deploiement. Idempotent.
--
-- ⚠ CETTE TABLE RESTE VIDE ET INERTE jusqu'au lot 5. Rien ne l'ecrit, rien ne la
--   lit avant. Elle est posee maintenant parce qu'elle DEBLOQUE les lots 4, 5
--   et 6, et qu'un patch colle aujourd'hui est un patch qui ne manquera pas.
--
-- ─── A QUOI ELLE SERT, EN UNE PHRASE ──────────────────────────────────────────
-- Pouvoir REMPLACER une valeur dans le classeur sans jamais ecraser une
-- correction humaine.
--     la case porte ENCORE notre valeur  -> personne n'y a touche -> on remplace
--     la case porte AUTRE CHOSE          -> un humain a corrige   -> ON S'ABSTIENT
--                                                                   et on le dit
-- Sans cette memoire, « remplacer » et « ecraser le travail de Delphine » sont
-- le meme geste. Mesure du 13/10 : 34 abstentions sur 44 en octobre, parce
-- qu'elle saisit AVANT notre descente.
--
-- ─── LA CLE, ET POURQUOI CELLE-LA -- mesure du 16/10 sur les 4 771 lignes ─────
-- Le classeur n'a AUCUNE clef exploitable aujourd'hui :
--     colonne  0  affair_uuid     remplie     1 fois   -- et la valeur est « E »
--     colonne  1  product_ref     remplie   694 fois   -- partielle
--     colonne  2  Mandat          remplie 4 766 fois, 4 047 distinctes
--                                 -> 719 DOUBLONS. Un numero de mandat n'est pas
--                                    une clef : Hektor les recycle (8 116 numeros
--                                    portes par plusieurs mandats, mesure du projet).
--     colonne 37  ID Unique       remplie 4 766 fois, 4 766 DISTINCTES  <- unique,
--                                 mais genere de LEUR cote (AppSheet ou un Apps
--                                 Script) : nous ne le connaissons pas au moment
--                                 d'ecrire une ligne neuve.
--
-- ⭐ D'OU LE CHOIX : `affair_uuid`, la colonne A -- vide, et nommee pour ca.
--   C'est NOUS qui la remplirons, avec notre `app_chaine_id`, sur les lignes que
--   nous creons. Elle devient la clef que nous maitrisons ; `ID Unique` reste la
--   leur. ⚠ La seule valeur deja presente (« E », ligne 77) n'est pas touchee :
--   c'est une saisie humaine, et on ne corrige pas ce qu'on n'a pas ecrit.
--
-- ─── POURQUOI UNE LIGNE PAR (CHAINE, COLONNE) ET PAS PAR LIGNE ────────────────
-- Parce que l'abstention se decide CASE PAR CASE. Delphine peut corriger la
-- commission et laisser la date : on doit alors remplacer la date et se tenir a
-- l'ecart de la commission. Une memoire par ligne ne saurait pas le dire.
--
-- ─── CE QU'ELLE N'EST PAS ─────────────────────────────────────────────────────
-- ⛔ PAS un journal d'audit : elle ne garde que la DERNIERE valeur que nous avons
--    posee, celle qui sert a reconnaitre notre propre ecriture. L'historique,
--    s'il est voulu un jour, est un autre sujet.
-- ⛔ PAS une copie du classeur. On n'y range que ce que NOUS avons ecrit.
--
-- ─── RETOUR ARRIERE ────────────────────────────────────────────────────────────
--   DROP TABLE IF EXISTS public.app_sheet_ecrit;
--   Rien n'en depend avant le lot 5.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU D'ENTREE
-- ---------------------------------------------------------------------
do $garde$
declare n integer;
begin
  select count(*) into n from information_schema.tables
   where table_schema = 'public' and table_name = 'app_affaire_ledger';
  if n <> 1 then
    raise exception 'ARRET : app_affaire_ledger est introuvable -- la clef de '
                    'cette table est son app_chaine_id';
  end if;

  select count(*) into n from information_schema.columns
   where table_schema = 'public' and table_name = 'app_affaire_ledger'
     and column_name = 'app_chaine_id';
  if n <> 1 then
    raise exception 'ARRET : app_affaire_ledger.app_chaine_id est introuvable';
  end if;
end $garde$;

-- ---------------------------------------------------------------------
-- LA TABLE
-- ---------------------------------------------------------------------
create table if not exists public.app_sheet_ecrit (
    -- La ligne du classeur, par la clef QUE NOUS ECRIVONS en colonne A.
    -- ⚠ Pas de cle etrangere vers app_affaire_ledger : une chaine peut etre
    --   supprimee cote Hektor, et la memoire de ce qu'on a ecrit doit SURVIVRE
    --   a sa disparition -- sinon on perdrait justement le moyen de savoir si la
    --   case du classeur porte encore notre valeur.
    app_chaine_id   text        not null,
    -- Le nom de la colonne du classeur, tel qu'il est en ligne 1 (« Commission
    -- TTC », « Etat Actuel »...). On garde le LIBELLE, pas l'indice : une colonne
    -- inseree decalerait tous les indices et notre memoire deviendrait fausse en
    -- silence.
    colonne         text        not null,
    -- La derniere valeur QUE NOUS AVONS POSEE, telle qu'ecrite. C'est elle qu'on
    -- compare a la case avant de remplacer.
    valeur          text,
    ecrit_le        timestamptz not null default now(),
    -- Qui a declenche l'ecriture (un geste de l'app, ou l'expediteur de nuit).
    origine         text,
    primary key (app_chaine_id, colonne)
);

create index if not exists idx_app_sheet_ecrit_chaine
    on public.app_sheet_ecrit (app_chaine_id);

comment on table public.app_sheet_ecrit is
    'Lot 2 (16/10/2026) : la DERNIERE valeur que nous avons ecrite dans chaque '
    'case du classeur de suivi. Sert a une seule chose : avant de remplacer une '
    'case, savoir si elle porte ENCORE notre valeur (on remplace) ou AUTRE CHOSE '
    '(un humain a corrige -> on s''abstient et on le dit). Mesure du 13/10 : '
    '34 abstentions sur 44 en octobre, Delphine saisissant avant notre descente. '
    'VIDE ET INERTE jusqu''au lot 5.';

comment on column public.app_sheet_ecrit.app_chaine_id is
    'La clef de la ligne, telle que NOUS l''ecrivons en colonne A (affair_uuid). '
    '⚠ Le classeur n''avait AUCUNE clef exploitable au 16/10 : affair_uuid vide '
    '(1 valeur sur 4 771), Mandat avec 719 doublons, et ID Unique genere de leur '
    'cote donc inconnu de nous au moment d''ecrire.';

comment on column public.app_sheet_ecrit.colonne is
    'Le LIBELLE de la colonne, pas son indice : une colonne inseree decalerait '
    'les indices et rendrait cette memoire fausse en silence.';

-- ---------------------------------------------------------------------
-- LA VISIBILITE
-- L'expediteur ecrit avec la cle de service (qui passe outre RLS). La lecture
-- est ouverte aux managers et admins, pour qu'un ecran puisse un jour dire
-- « nous nous sommes abstenus sur cette case, et voici pourquoi ».
-- ---------------------------------------------------------------------
alter table public.app_sheet_ecrit enable row level security;

drop policy if exists app_sheet_ecrit_select_manager on public.app_sheet_ecrit;
create policy app_sheet_ecrit_select_manager
on public.app_sheet_ecrit
for select
using ((select public.is_app_manager_or_admin()));

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU DE SORTIE
-- ---------------------------------------------------------------------
do $garde$
declare rls boolean; pol integer; lignes bigint;
begin
  select relrowsecurity into rls from pg_class
   where oid = 'public.app_sheet_ecrit'::regclass;
  if not coalesce(rls, false) then
    raise exception 'La securite par ligne n''est pas active';
  end if;

  select count(*) into pol from pg_policies
   where schemaname = 'public' and tablename = 'app_sheet_ecrit';
  if pol < 1 then
    raise exception 'Aucune politique de lecture';
  end if;

  select count(*) into lignes from public.app_sheet_ecrit;
  raise notice 'OK : app_sheet_ecrit creee, RLS active, % politique(s). '
               '% ligne(s) -- ATTENDU 0 : elle reste inerte jusqu''au lot 5.',
               pol, lignes;
end $garde$;

-- ─── CONTROLE APRES APPLICATION ────────────────────────────────────────────────
--   select count(*) from public.app_sheet_ecrit;          -- attendu 0
--   select column_name, data_type, is_nullable
--     from information_schema.columns
--    where table_schema='public' and table_name='app_sheet_ecrit'
--    order by ordinal_position;
