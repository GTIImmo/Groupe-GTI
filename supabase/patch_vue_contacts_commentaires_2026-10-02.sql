-- ═══════════════════════════════════════════════════════════════════════════════
-- LA VUE app_contacts_current EXPOSE LE COMMENTAIRE            02/10/2026 · ③a
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Ne touche AUCUNE donnee. Ne change AUCUNE colonne existante.
--
-- ─── POURQUOI ───────────────────────────────────────────────────────────────────
-- Suite du patch du meme jour qui a ajoute `commentaires` a la TABLE
-- app_contact_current. Le front lit les deux : la table (lib/api.ts:5731) ET cette
-- vue (lib/api.ts:169, `contactsCurrentView`). Or une vue Postgres fige la liste de
-- ses colonnes a sa creation : elle ignore la nouvelle tant qu'on ne la refait pas.
--
-- C'est le chemin qui compte : `contactsListingSelect` -- la liste de champs que le
-- front demande pour une fiche contact -- interroge CETTE VUE. L'audit du 02/10 a
-- montre qu'elle porte deja 14 des 15 champs dont la rubrique « Contact » d'une
-- annonce a besoin pour lire NOTRE registre au lieu de proprietaires_json :
--     civilite · nom · prenom · adresse · code_postal · ville · archive
--     date_enregistrement · date_maj · phone_primary · email · typologies_json
--     hektor_couple_contact_id + couple_role  -> LA FUSION DES MENAGES SURVIT
--     hektor_target_id                        -> le numero HEKTOR pour le worker
-- Le quinzieme est le commentaire, et c'est ce patch.
--
-- ─── CE QU'IL FAIT, ET CE QU'IL NE FAIT PAS ─────────────────────────────────────
--   · les 42 colonnes actuelles, RECOPIEES A L'IDENTIQUE depuis pg_get_viewdef,
--     dans le MEME ORDRE, + `commentaires` EN DERNIER
--     ⚠ CREATE OR REPLACE VIEW n'autorise QUE l'ajout en fin : changer l'ordre ou
--       le type d'une colonne existante serait refuse. C'est une garantie, pas une
--       contrainte -- elle interdit de casser un lecteur par megarde.
--   · ⛔ AUCUNE OPTION. La vue n'est PAS en `security_invoker` (reloptions = NULL,
--     verifie le 02/10) : elle s'execute avec les droits de son proprietaire
--     (postgres), donc la RLS de la table ne s'y applique pas. En ajouter une
--     changerait QUI VOIT QUOI. Reproduire a l'identique, c'est aussi ne pas lui
--     en donner.
--   · les droits (authenticated, postgres, service_role) sont conserves par
--     CREATE OR REPLACE -- verifie dans l'epreuve.
--   · ⛔ IL NE REMPLIT RIEN : la colonne vaut NULL partout tant que le run n'a pas
--     tourne avec l'extraction (posee le meme jour dans build_contacts_layer.py).
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
--   Rejouer ce meme CREATE OR REPLACE VIEW sans la derniere ligne (`commentaires`).
--   ⚠ Postgres REFUSE de retirer une colonne par CREATE OR REPLACE : il faudrait
--     DROP VIEW puis CREATE -- ce qui perdrait les droits. Donc en pratique : on ne
--     revient pas en arriere sur ce patch, on cesse simplement de lire la colonne.
--     C'est sans danger : une colonne exposee que personne ne demande ne coute rien.
--
-- ─── EPROUVE AVANT ENVOI, le 02/10 ──────────────────────────────────────────────
--   En BEGIN/ROLLBACK sur la base reelle :
--      colonnes de la vue .......  43   (42 + commentaires)
--      lignes ...................  62 103  (inchangees)
--      commentaires expose ......  1
--      beneficiaires des droits .  3   (authenticated, postgres, service_role)
--      sans option comme avant ..  true
--   Puis ROLLBACK verifie : 42 colonnes, 0 commentaires.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ⛔ GARDE-FOU 1 : la colonne doit exister dans la TABLE avant d'etre exposee.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name='app_contact_current'
                    AND column_name='commentaires') THEN
    RAISE EXCEPTION 'ARRET : app_contact_current.commentaires n''existe pas. '
                    'Appliquer d''abord patch_contact_commentaires_2026-10-02.sql.';
  END IF;
END $$;

-- ⛔ GARDE-FOU 2 : on ne doit pas etre en train d'ajouter une option de securite
--   sans le vouloir. Si la vue en portait une AUJOURD'HUI, ce patch la perdrait.
DO $$
DECLARE opts text[];
BEGIN
  SELECT c.reloptions INTO opts FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname='app_contacts_current';
  IF opts IS NOT NULL THEN
    RAISE EXCEPTION 'ARRET : la vue porte des options (%) que ce patch ne reproduit '
                    'pas -- a relire avant.', array_to_string(opts, ', ');
  END IF;
END $$;

-- LA VUE : 42 colonnes recopiees de pg_get_viewdef, + commentaires EN DERNIER.
CREATE OR REPLACE VIEW public.app_contacts_current AS
 SELECT hektor_contact_id,
    hektor_agence_id,
    hektor_negociateur_id,
    negociateur_email,
    commercial_nom,
    agence_nom,
    civilite,
    nom,
    prenom,
    display_name,
    archive,
    date_enregistrement,
    date_maj,
    email,
    phone_primary,
    phone_secondary,
    ville,
    code_postal,
    typologies_json,
    relation_roles_json,
    linked_annonce_count,
    active_search_count,
    total_search_count,
    supabase_sync_eligible,
    eligibility_reasons_json,
    duplicate_group_count,
    duplicate_max_severity,
    duplicate_primary_candidate_id,
    completeness_score,
    search_text,
    source_hash,
    refreshed_at,
    has_contact_detail,
    contact_detail_synced_at,
    adresse,
    birth_date,
    birth_place,
    marital_status,
    hektor_couple_contact_id,
    couple_role,
    hektor_target_id,
    app_contact_id,
    -- ③a 02/10/2026 : le 15e champ de la rubrique « Contact » d'une annonce.
    commentaires
   FROM app_contact_current;

-- ⛔ GARDE-FOU 3 : elle expose la colonne, elle rend le meme nombre de lignes,
--   et elle n'a pas perdu ses droits. Une migration de vue qui ne verifie que sa
--   propre colonne ne prouve pas qu'elle n'a rien casse par ailleurs.
DO $$
DECLARE n_col int; n_vue bigint; n_tab bigint; n_grants int;
BEGIN
  SELECT count(*) INTO n_col FROM information_schema.columns
   WHERE table_schema='public' AND table_name='app_contacts_current';
  SELECT count(*) INTO n_vue FROM public.app_contacts_current;
  SELECT count(*) INTO n_tab FROM public.app_contact_current;
  SELECT count(DISTINCT grantee) INTO n_grants FROM information_schema.role_table_grants
   WHERE table_schema='public' AND table_name='app_contacts_current';

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name='app_contacts_current'
                    AND column_name='commentaires') THEN
    RAISE EXCEPTION 'La colonne n''est pas exposee par la vue.';
  END IF;
  IF n_col <> 43 THEN
    RAISE EXCEPTION 'ARRET : la vue a % colonnes, 43 attendues -- une a ete perdue '
                    'ou ajoutee.', n_col;
  END IF;
  IF n_vue <> n_tab THEN
    RAISE EXCEPTION 'ARRET : la vue rend % lignes et la table % -- incoherent.',
                    n_vue, n_tab;
  END IF;
  IF n_grants < 3 THEN
    RAISE EXCEPTION 'ARRET : % beneficiaire(s) seulement, 3 attendus -- des droits '
                    'ont ete perdus.', n_grants;
  END IF;
  RAISE NOTICE 'OK : 43 colonnes, % lignes, % beneficiaires.', n_vue, n_grants;
END $$;

COMMIT;

-- ─── A LIRE APRES LE COMMIT ─────────────────────────────────────────────────────
-- SELECT count(*) FROM information_schema.columns
--  WHERE table_schema='public' AND table_name='app_contacts_current';
--   -> 43
--
-- ℹ LA COLONNE SERA VIDE jusqu'au premier run qui passe avec l'extraction.
--   Attendu a ce moment-la : ~57 % des contacts porteront un commentaire
--   (34 180 sur 60 000 mesures sur le miroir le 02/10).
