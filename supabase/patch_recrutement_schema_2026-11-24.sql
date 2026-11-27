-- ═══════════════════════════════════════════════════════════════════════════
-- RECRUTEMENT — R3 : LA BASE, DANS UN SCHÉMA À PART                                          24/11/2026
-- Chantier à part (sans lien avec Hektor) : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md
-- §13 (R3), §14 (liste), §15 (délégation). À coller par Frédéric dans l'éditeur SQL (l'outil refuse
-- d'écrire en production) ; puis _REPETITION.sql ; en cas de problème, _INVERSE.sql.
--
-- POURQUOI UN SCHÉMA « recrutement » ET PAS DES TABLES public.* (mesuré le 20/11) : la descente du matin
--   (phase2/sync/pull_from_supabase.py) DÉCOUVRE SEULE toutes les tables exposées de « public ». Une table
--   publique de recrutement serait recopiée chaque matin dans phase2.sqlite et ses sauvegardes de 90 jours
--   — et un effacement RGPD n'y arriverait jamais. Le schéma « recrutement » n'est PAS exposé à l'API :
--   invisible pour la descente, le run de nuit, les sentinelles et l'assistant.
--   Mesuré le 24/11 : Supabase ne pose AUCUN droit par défaut sur un schéma neuf (les droits automatiques
--   ne visent que public, storage, graphql) — on ferme quand même tout, par écrit.
--
-- CE QUE POSE CE PATCH (et rien d'autre) :
--   1. le schéma et 6 tables : fiche, entreprise, collecte, source_etat (ce que le serveur MONTE),
--      correction, liste_noire (ce que l'app écrit et que le serveur DESCEND) ;
--      ⚠ le suivi (parcours, fil d'échanges) viendra AVEC l'écran (R6), dans son propre patch ;
--   2. le ROBOT « recrutement_robot » : un rôle de base qui n'a de droits QUE sur ce schéma. La montée et
--      la descente passeront par lui (R4) : un défaut du pousseur ne pourra toucher aucune autre table.
--      Il naît SANS connexion possible (NOLOGIN) : Frédéric lui donnera un mot de passe à R4 ;
--   3. une seule fonction pour l'app, public.rec_etat_collecte() (le bandeau « dernière collecte »),
--      réservée aux administrateurs ; les autres viendront avec l'écran ;
--   4. les 7 lignes de battement de app_worker_registry (recrutement.*), fréquence « bimonthly » (64 j,
--      déclarée dans monitoring/check_gti_health.py) — pour qu'aucun battement ne parte dans le vide.
-- ⛔ RIEN N'EST ÉCRIT CHEZ HEKTOR. AUCUNE table existante n'est modifiée ; app_worker_registry reçoit
--   7 lignes neuves et rien d'autre.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 0. GARDE : on ne pose pas deux fois ──────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'recrutement') THEN
    RAISE EXCEPTION 'le schéma recrutement existe déjà : patch déjà posé ? (rien n''a été fait)';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'recrutement_robot') THEN
    RAISE EXCEPTION 'le rôle recrutement_robot existe déjà : patch déjà posé ? (rien n''a été fait)';
  END IF;
  IF EXISTS (SELECT 1 FROM public.app_worker_registry WHERE worker_key LIKE 'recrutement.%') THEN
    RAISE EXCEPTION 'des lignes recrutement.* existent déjà dans app_worker_registry (rien n''a été fait)';
  END IF;
END $$;

-- ── 1. LE SCHÉMA ET SES TABLES ───────────────────────────────────────────────────────────────────────
create schema recrutement;
comment on schema recrutement is
  '24/11/2026 : le chantier RECRUTEMENT (annuaire des mandataires de la région, sans lien avec Hektor). NON exposé à l''API : l''app y accède par les fonctions public.rec_*, le serveur par le rôle recrutement_robot. Note : CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md.';
revoke all on schema recrutement from public, anon, authenticated;

-- 1a. Les fiches : une par réseau (la même personne peut en avoir plusieurs, le SIREN les relie).
create table recrutement.fiche (
    reseau            text        not null,
    identifiant       text        not null,
    origine           text        not null default 'collecte' check (origine in ('collecte', 'saisie')),
    url               text,
    prenom            text,
    nom               text,
    fonction          text,
    agence            text,
    commune           text,
    code_postal       text,
    -- ⛔ MINIMISATION, tenue par la base aussi : une fiche COLLECTÉE est dans nos 4 départements
    departement       text,
    lat               double precision,
    lon               double precision,
    agence_gti_proche text,
    distance_km       numeric(6, 1),
    telephone         text,
    email             text,
    source_contact    text,
    siren             text        check (siren is null or siren ~ '^[0-9]{9}$'),
    rsac_ville        text,
    nb_annonces       integer,
    nb_avis           integer,
    note_avis         numeric(3, 2),
    distinction       text,
    desactive         boolean     not null default false,
    etat_suivi        text        check (etat_suivi is null or etat_suivi in ('nouveau', 'present', 'absent', 'parti', 'revenu')),
    etat_depuis       date,
    motif_depart      text,
    premiere_vue      date,
    derniere_vue      date,
    monte_le          timestamptz not null default now(),
    primary key (reseau, identifiant),
    -- ⚠ coalesce : un CHECK laisse passer un NULL ; sans lui, une fiche collectée SANS département passerait
    constraint fiche_collectee_dans_la_region
        check (origine = 'saisie' or coalesce(departement, '') in ('07', '42', '43', '63')),
    -- une coordonnée porte TOUJOURS sa source (règle du 20/11, note §9)
    constraint fiche_coordonnee_avec_sa_source
        check ((telephone is null and email is null) or source_contact is not null)
);
create index fiche_siren on recrutement.fiche (siren) where siren is not null;
create index fiche_departement on recrutement.fiche (departement);
comment on table recrutement.fiche is
  '24/11/2026 : une fiche par réseau (ou saisie dans l''app). Écrite par la MONTÉE (recrutement_robot) ; une valeur corrigée dans l''app vit dans recrutement.correction et n''est jamais écrasée.';

-- 1b. Ce que dit le registre public de l'entreprise (SIREN). Personne en opposition : seulement le fait.
create table recrutement.entreprise (
    siren          text        primary key check (siren ~ '^[0-9]{9}$'),
    trouve         boolean,
    date_creation  date,
    etat           text        check (etat is null or etat in ('A', 'C')),
    naf            text,
    siege_cp       text,
    siege_commune  text,
    opposition     boolean     not null default false,
    lu_le          timestamptz,
    monte_le       timestamptz not null default now(),
    -- ⛔ OPPOSITION À LA PROSPECTION : aucune donnée du registre n'est gardée, seulement le fait
    constraint entreprise_opposition_sans_donnee
        check (not opposition or (date_creation is null and etat is null and naf is null
                                  and siege_cp is null and siege_commune is null))
);

-- 1c. Les collectes (tous les deux mois) et la santé de chaque source.
create table recrutement.collecte (
    numero    integer     primary key check (numero > 0),
    debut     timestamptz not null,
    fin       timestamptz,
    etat      text        not null check (etat in ('en_cours', 'finie')),
    note      text,
    monte_le  timestamptz not null default now()
);
create table recrutement.source_etat (
    collecte   integer not null references recrutement.collecte (numero) on delete cascade,
    reseau     text    not null,
    vus        integer,
    precedent  integer,
    sante      text    not null check (sante in ('premiere', 'saine', 'malade')),
    raison     text,
    primary key (collecte, reseau)
);

-- 1d. Le carnet des corrections (écrit par l'app, lu par la descente et par l'écran).
create table recrutement.correction (
    reseau       text        not null,
    identifiant  text        not null,
    champ        text        not null check (champ in ('prenom', 'nom', 'telephone', 'email', 'commune',
                                                        'code_postal', 'fonction', 'agence')),
    valeur       text,
    par          uuid,
    le           timestamptz not null default now(),
    primary key (reseau, identifiant, champ),
    foreign key (reseau, identifiant) references recrutement.fiche (reseau, identifiant) on delete cascade
);

-- 1e. « Ne plus contacter » et « effacer » : des EMPREINTES seulement (sha256), lues avant toute collecte.
create table recrutement.liste_noire (
    empreinte   text        primary key check (empreinte ~ '^[0-9a-f]{64}$'),
    nature      text        not null check (nature in ('siren', 'telephone', 'email', 'nom')),
    niveau      text        not null check (niveau in ('ne_plus_contacter', 'effacer')),
    demande_le  date        not null,
    pose_le     timestamptz not null default now(),
    pose_par    uuid
);

-- 1f. TOUT EST FERMÉ par défaut : RLS partout, aucun droit pour public / anon / authenticated.
alter table recrutement.fiche        enable row level security;
alter table recrutement.entreprise   enable row level security;
alter table recrutement.collecte     enable row level security;
alter table recrutement.source_etat  enable row level security;
alter table recrutement.correction   enable row level security;
alter table recrutement.liste_noire  enable row level security;
revoke all on all tables in schema recrutement from public, anon, authenticated;

-- ── 2. LE ROBOT : des droits sur CE schéma, et sur rien d'autre ──────────────────────────────────────
-- NOLOGIN : il ne peut pas se connecter tant que Frédéric ne lui a pas donné de mot de passe (R4).
create role recrutement_robot nologin noinherit nocreatedb nocreaterole nobypassrls;
comment on role recrutement_robot is
  '24/11/2026 : la montée et la descente du recrutement (serveur). Droits sur le schéma recrutement SEULEMENT. Né NOLOGIN.';
grant usage on schema recrutement to recrutement_robot;
-- ce que le serveur MONTE : lire, ajouter, mettre à jour — jamais supprimer
grant select, insert, update on recrutement.fiche, recrutement.entreprise,
                                recrutement.collecte, recrutement.source_etat to recrutement_robot;
-- ce que le serveur DESCEND : lire seulement
grant select on recrutement.correction, recrutement.liste_noire to recrutement_robot;
create policy robot_fiche       on recrutement.fiche       for all    to recrutement_robot using (true) with check (true);
create policy robot_entreprise  on recrutement.entreprise  for all    to recrutement_robot using (true) with check (true);
create policy robot_collecte    on recrutement.collecte    for all    to recrutement_robot using (true) with check (true);
create policy robot_source_etat on recrutement.source_etat for all    to recrutement_robot using (true) with check (true);
create policy robot_correction  on recrutement.correction  for select to recrutement_robot using (true);
create policy robot_liste_noire on recrutement.liste_noire for select to recrutement_robot using (true);
alter role recrutement_robot set search_path = recrutement;
alter role recrutement_robot set statement_timeout = '120s';

-- ── 3. LA FONCTION DU BANDEAU (administrateurs seulement) ────────────────────────────────────────────
create or replace function public.rec_etat_collecte()
returns jsonb
language plpgsql
stable
security definer
set search_path to 'public'
as $$
declare
    n integer;
    r jsonb;
begin
    if not public.is_app_admin() then
        raise exception 'Réservé aux administrateurs' using errcode = '42501';
    end if;
    select max(numero) into n from recrutement.collecte where etat = 'finie';
    select jsonb_build_object(
        'collecte', (select to_jsonb(c) from recrutement.collecte c where c.numero = n),
        'sources',  coalesce((select jsonb_agg(to_jsonb(s) order by s.sante desc, s.reseau)
                                from recrutement.source_etat s where s.collecte = n), '[]'::jsonb),
        'fiches',   (select count(*) from recrutement.fiche),
        'par_etat', coalesce((select jsonb_object_agg(coalesce(etat_suivi, 'inconnu'), k)
                                from (select etat_suivi, count(*) k from recrutement.fiche group by 1) x), '{}'::jsonb)
    ) into r;
    return r;
end
$$;
comment on function public.rec_etat_collecte() is
  '24/11/2026 : le bandeau de l''écran Recrutement (dernière collecte finie, santé des sources, fiches par état). Administrateurs seulement (is_app_admin), sinon 42501.';
-- ⛔ `revoke ... from public` NE FERME PAS authenticated : on nomme les rôles. authenticated GARDE le droit
--   d'appeler (un administrateur est authenticated) ; c'est la fonction qui refuse les autres.
revoke all on function public.rec_etat_collecte() from public, anon;
grant execute on function public.rec_etat_collecte() to authenticated, service_role;

-- ── 4. LES 7 BATTEMENTS DU RUN (scheduled/run_recrutement.ps1, interrupteur RECRUTEMENT_BATTEMENTS) ──
-- « bimonthly » = 64 jours (monitoring/check_gti_health.py, WORKER_STALE_POLICY). Une clé jamais vue ne
-- déclenche rien : elles se taisent jusqu'au premier succès.
insert into public.app_worker_registry
    (worker_key, worker_name, worker_role, worker_type, criticality, frequency, status,
     script_path, expected_max_runtime_minutes, monitoring_domain, source_notes)
values
    ('recrutement.descente',     'Recrutement : la descente',
     'Rapporte de la base la liste « ne plus contacter », les effacements et les corrections de l''app, AVANT toute collecte. En échec, le run s''arrête. Interrupteur RECRUTEMENT_DESCENTE.',
     'python_worker', 'medium', 'bimonthly', 'active', 'recrutement\descendre.py', 10, 'business',
     'Ajoutée le 24/11/2026 (chantier recrutement, R3). Aucune requête chez Hektor.'),
    ('recrutement.collecte',     'Recrutement : la collecte des annuaires',
     'Lit les annuaires publics des réseaux de mandataires et le registre public (une source à la fois, robots.txt respecté). Une source en échec n''arrête pas les autres.',
     'python_worker', 'medium', 'bimonthly', 'active', 'recrutement\collecte_annuaires.py', 480, 'business',
     'Ajoutée le 24/11/2026 (chantier recrutement, R3). Aucune requête chez Hektor.'),
    ('recrutement.mise_a_jour',  'Recrutement : la mise à jour',
     'Compare la collecte à la précédente : nouveaux, absents, partis, revenus, changés de réseau. Une source MALADE ne fait partir personne.',
     'python_worker', 'medium', 'bimonthly', 'active', 'recrutement\collecte_annuaires.py', 15, 'business',
     'Ajoutée le 24/11/2026 (chantier recrutement, R3).'),
    ('recrutement.controle',     'Recrutement : le contrôle',
     'Règle des coordonnées, opposition au registre, témoins positifs. ROUGE = rien ne monte.',
     'python_worker', 'medium', 'bimonthly', 'active', 'recrutement\collecte_annuaires.py', 5, 'business',
     'Ajoutée le 24/11/2026 (chantier recrutement, R3).'),
    ('recrutement.montee',       'Recrutement : la montée',
     'Envoie la collecte dans le schéma recrutement, par le rôle recrutement_robot (aucun droit ailleurs). Interrupteur RECRUTEMENT_MONTEE.',
     'python_worker', 'medium', 'bimonthly', 'active', 'recrutement\pousser.py', 15, 'business',
     'Ajoutée le 24/11/2026 (chantier recrutement, R3).'),
    ('recrutement.sauvegarde',   'Recrutement : la sauvegarde',
     'Copie datée et relue de la base locale dans C:\Hektor\Backups\recrutement (6 gardées = un an).',
     'python_worker', 'medium', 'bimonthly', 'active', 'recrutement\sauvegarder.py', 5, 'business',
     'Ajoutée le 24/11/2026 (chantier recrutement, R3).'),
    ('recrutement.compte_rendu', 'Recrutement : le compte rendu',
     'L''état de chaque source de la collecte, en comptes (jamais un nom).',
     'python_worker', 'low', 'bimonthly', 'active', 'scheduled\run_recrutement.ps1', 2, 'business',
     'Ajoutée le 24/11/2026 (chantier recrutement, R3).');

COMMIT;
