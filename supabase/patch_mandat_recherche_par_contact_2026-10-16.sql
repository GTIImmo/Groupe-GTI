-- ═══════════════════════════════════════════════════════════════════════════════
-- A.3 PIECE 5 -- LE MANDAT DE RECHERCHE DANS LA CARTE DU CONTACT   16/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage, aucun deploiement. Idempotent (re-collable sans risque).
--
-- ─── CE QUE CA FAIT ─────────────────────────────────────────────────────────────
-- Cree `app_contact_mandat_recherche_current` : 32 lignes, une par mandat de
-- recherche de NOTRE registre porte par un contact identifie. Elle dit, quand on
-- peut le dire sans deviner, QUELLE recherche ce mandat couvre.
--
-- ─── POURQUOI UNE TABLE, ET PAS UNE COLONNE SUR LES RECHERCHES ─────────────────
-- Une colonne sur `app_contact_search_current` aurait ete plus courte cote front
-- (il la lit en `select('*')`). DEUX MESURES L'ONT ECARTEE :
--
--   (1) CETTE TABLE EST REMPLACEE EN ENTIER CHAQUE NUIT. `build_contacts_layer.py`
--       fait `replace_table_rows(..., search_rows, ...)` : notre colonne serait
--       vide chaque matin. C'est le principe meme de A.3 -- notre donnee ne vit
--       pas dans une table que la descente de Hektor reecrit.
--   (2) `stable_payload_hash` hache TOUTES les colonnes sauf `refreshed_at` :
--       ajouter une colonne, meme NULL partout, change l'empreinte des 77 195
--       recherches et les fait TOUTES repartir. Ici on pousse 32 lignes.
--
-- PRECEDENT SUIVI : `app_contact_stats_current`, satellite poussee a part.
--
-- ─── LA VISIBILITE, ET POURQUOI CELLE-LA ───────────────────────────────────────
-- La politique est COPIEE sur celle de `app_contact_search_current`
-- (patch_contacts_listing_performance_2026-05-27.sql) : le negociateur voit le
-- mandat de SES contacts, un lecteur global voit tout.
-- ⭐ Ce n'est PAS la regle de l'ecran registre (`is_app_manager_or_admin()`), et
--   c'est exactement la precision de Frederic du 12/10 : « je voulais que la vue
--   registre des mandats soit limitee aux admin et manager, MAIS PAS LE BLOC
--   mandat dans l'annonce ou le contact ».
--
-- ─── RETOUR ARRIERE ────────────────────────────────────────────────────────────
--   DROP TABLE IF EXISTS public.app_contact_mandat_recherche_current;
--   Rien d'autre n'en depend : le front ne fait que l'afficher s'il la trouve.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU D'ENTREE : les deux tables dont on copie la regle doivent etre la.
-- ---------------------------------------------------------------------
do $garde$
declare n integer;
begin
  select count(*) into n from information_schema.tables
   where table_schema = 'public' and table_name = 'app_contact_current';
  if n <> 1 then
    raise exception 'ARRET : app_contact_current est introuvable';
  end if;

  select count(*) into n from pg_proc p
    join pg_namespace s on s.oid = p.pronamespace
   where s.nspname = 'public' and p.proname = 'can_access_negotiator_email';
  if n < 1 then
    raise exception 'ARRET : can_access_negotiator_email() est introuvable -- '
                    'la regle de visibilite des recherches n''existe pas ici';
  end if;
end $garde$;

-- ---------------------------------------------------------------------
-- LA TABLE
-- ---------------------------------------------------------------------
create table if not exists public.app_contact_mandat_recherche_current (
    hektor_contact_id   text    not null,
    numero_mandat       text    not null,
    -- La recherche que ce mandat couvre. NULL quand on ne peut pas la designer
    -- sans deviner : la carte le dira, elle ne mentira pas.
    contact_search_key  text,
    search_index        integer,
    type                text,
    date_debut          text,
    date_fin            text,
    date_cloture        text,
    famille             text,
    source_app          text,
    designation         text,
    refreshed_at        timestamptz not null default now(),
    primary key (hektor_contact_id, numero_mandat)
);

create index if not exists idx_app_contact_mandat_recherche_contact
    on public.app_contact_mandat_recherche_current (hektor_contact_id);
create index if not exists idx_app_contact_mandat_recherche_search
    on public.app_contact_mandat_recherche_current (contact_search_key);

comment on table public.app_contact_mandat_recherche_current is
    'A.3 piece 5 (16/10/2026) : le lien entre un MANDAT DE RECHERCHE de notre '
    'registre (app_mandat, hektor_annonce_id = '''') et LA recherche du contact '
    'qu''il couvre. CALCUL, pas registre : refaite en entier a chaque pose. Le '
    'registre, c''est app_mandat -- lui ne perd jamais rien.';

comment on column public.app_contact_mandat_recherche_current.contact_search_key is
    'NULL = aucune recherche ne peut etre designee sans deviner (plusieurs '
    'possibles et aucune commune ne tranche, ou aucune recherche saisie). '
    'On ne rattache jamais au hasard.';

-- ---------------------------------------------------------------------
-- LA VISIBILITE -- copiee sur celle des recherches
-- ---------------------------------------------------------------------
alter table public.app_contact_mandat_recherche_current enable row level security;

drop policy if exists app_contact_mandat_recherche_select_scoped
    on public.app_contact_mandat_recherche_current;
create policy app_contact_mandat_recherche_select_scoped
on public.app_contact_mandat_recherche_current
for select
using (
  exists (
    select 1
    from public.app_contact_current c
    where c.hektor_contact_id = app_contact_mandat_recherche_current.hektor_contact_id
      and (
        (select public.is_app_global_reader())
        or public.can_access_negotiator_email(c.negociateur_email)
      )
  )
);

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU DE SORTIE
-- ---------------------------------------------------------------------
do $garde$
declare rls boolean; pol integer; cols integer;
begin
  select relrowsecurity into rls from pg_class
   where oid = 'public.app_contact_mandat_recherche_current'::regclass;
  if not coalesce(rls, false) then
    raise exception 'La securite par ligne n''est pas active';
  end if;

  select count(*) into pol from pg_policies
   where schemaname = 'public'
     and tablename = 'app_contact_mandat_recherche_current';
  if pol < 1 then
    raise exception 'Aucune politique de lecture : personne ne verrait la table';
  end if;

  select count(*) into cols from information_schema.columns
   where table_schema = 'public'
     and table_name = 'app_contact_mandat_recherche_current';
  raise notice 'OK : table creee, % colonne(s), % politique(s), RLS active. '
               'ATTENDU ENSUITE : 32 lignes apres la poussee depuis le serveur.',
               cols, pol;
end $garde$;

-- ─── CONTROLE APRES LA POUSSEE ─────────────────────────────────────────────────
--   select count(*) as total,
--          count(contact_search_key) as rattaches,
--          count(*) - count(contact_search_key) as sans_recherche
--     from public.app_contact_mandat_recherche_current;
--   ATTENDU : total 32, rattaches 20, sans_recherche 12.
