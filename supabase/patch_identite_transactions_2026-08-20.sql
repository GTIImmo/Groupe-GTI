-- =====================================================================
-- Identite des transactions -- l'affaire porte d'abord le numero de l'app
-- Date : 2026-08-20
-- Applique en prod via les migrations Supabase :
--   `affaire_ledger_cases_app`      (etape 1 : les deux colonnes, vides)
--   `affaire_ledger_identite_app`   (etape 2 : la cle bascule)
--
-- POURQUOI. La cle du registre d'affaires etait
--   (hektor_annonce_id, kind, hektor_affaire_id)
-- soit DEUX numeros appartenant a Hektor, tous deux obligatoires. Consequence :
-- une offre, un compromis ou une vente ne pouvait pas exister dans les livres de
-- l'app avant que Hektor ne l'ait numerotee. C'est pour cela qu'aujourd'hui, quand
-- un negociateur enregistre une offre, l'app n'ecrit rien : elle poste une tache au
-- worker et attend le run de nuit.
--
-- CE QUI A ETE MESURE LE 20/08, avant d'ecrire une ligne :
--   * L'app n'envoie JAMAIS un numero de transaction a Hektor. Le worker pose
--     litteralement idOffre="" / idCompromis="" / idVente="" : il ne sait que creer,
--     jamais modifier. Zero point d'appel a repointer.
--   * Cote ecran, les trois numeros ne servent qu'a un voyant ("y a-t-il une offre ?")
--     et a une ligne d'affichage. Aucune recherche par identifiant.
--   * Le registre n'est touche que par 3 fichiers.
--   * hektor_affaire_id n'est PAS unique : 7 541 numeros sont portes par deux types
--     differents -- sur des annonces et des acquereurs differents (0 sur 7 541
--     partagent l'annonce). Hektor tient trois compteurs separes qui se telescopent.
--     D'ou : le numero de l'app est UNE SEULE serie pour les trois types, et la cle
--     de reconciliation reste le TRIPLET, jamais l'identifiant seul.
--   * Les 10 477 annonces citees par le registre sont toutes retrouvees dans
--     app_dossier local : la recopie du numero d'annonce est integrale, 0 orpheline.
--     (Elle n'etait pas possible avant l'alignement du 19/08.)
--
-- VERIFIE APRES APPLICATION :
--   28 980 lignes, numeros 1..28 980, 0 doublon, 0 ligne perdue, 0 ligne apparue,
--   0 numero d'annonce faux, et empreinte IDENTIQUE entre le serveur local et
--   Supabase : 7784b25532b4b6f88e42691a74197f40 -- inchangee apres deux cycles
--   complets refresh+push, donc le run de nuit ne renumerote rien.
-- =====================================================================

-- --- Etape 1 : les deux cases -----------------------------------------
alter table public.app_affaire_ledger add column if not exists app_affaire_id bigint;
alter table public.app_affaire_ledger add column if not exists app_dossier_id  bigint;

comment on column public.app_affaire_ledger.app_affaire_id is
  'Numero d''affaire distribue par le serveur local. Serie unique pour les trois types.';
comment on column public.app_affaire_ledger.app_dossier_id is
  'Numero d''annonce de l''app (serie locale), a cote de hektor_annonce_id.';

-- --- Entre les deux : le serveur local remplit et pousse ---------------
--   python phase2/sync/affaire_ledger.py --refresh --push

-- --- Etape 2 : la cle bascule -----------------------------------------
alter table public.app_affaire_ledger alter column app_affaire_id set not null;
alter table public.app_affaire_ledger drop constraint app_affaire_ledger_pkey;
alter table public.app_affaire_ledger add primary key (app_affaire_id);

-- Cle de RECONCILIATION : par quoi on reconnait une affaire au retour de Hektor.
-- Partielle, parce qu'une affaire nee dans l'app n'a pas encore de numero Hektor
-- -- et n'en aura peut-etre jamais.
create unique index if not exists idx_app_affaire_ledger_hektor
  on public.app_affaire_ledger (hektor_annonce_id, kind, hektor_affaire_id)
  where hektor_affaire_id is not null;

alter table public.app_affaire_ledger alter column hektor_annonce_id drop not null;
alter table public.app_affaire_ledger alter column hektor_affaire_id drop not null;

create index if not exists idx_app_affaire_ledger_dossier
  on public.app_affaire_ledger (app_dossier_id);

-- Sentinelle : rien ne doit produire d'affaire sans numero Hektor avant la tache 13
-- (saisie directe dans l'app). Une seule ligne ici aujourd'hui = un bug qui ecrit
-- en silence. Branchee dans monitoring/check_gti_health.py, seuil 0.
create or replace view public.app_affaires_sans_numero_hektor as
  select app_affaire_id, app_dossier_id, kind, state, montant, date, first_seen_at
    from public.app_affaire_ledger
   where hektor_affaire_id is null;

-- --- Retour arriere ----------------------------------------------------
-- Cote local : la table d'avant est conservee telle quelle sous
--   app_affaire_ledger_avant_identite_20260820  (28 980 lignes, forme d'origine).
-- Cote Supabase : reposer la cle sur le triplet et rendre les colonnes Hektor
-- obligatoires suffit -- aucune donnee n'a ete supprimee ni modifiee, seules deux
-- colonnes ont ete ajoutees.
