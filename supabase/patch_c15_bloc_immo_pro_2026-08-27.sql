-- =====================================================================
-- C.15 -- LE BLOC IMMOBILIER PROFESSIONNEL ARRIVE JUSQU'A L'ECRAN
-- Applique le 2026-08-27. Rejouable sans effet de bord.
-- =====================================================================
--
-- LE PROBLEME. L'API REST de Hektor renvoie le meme code de type (idtype 23,
-- "Commerce") pour les HUIT sous-types d'immobilier professionnel : elle disait
-- la meme chose d'un entrepot, d'un fonds de commerce et d'une pizzeria. Le vrai
-- sous-type -- et tout le bloc professionnel (loyer, bail, CA, vitrine, quai) --
-- n'existe que dans la console Hektor, interrogeable en GraphQL.
--
-- L'extracteur (phase2/sync/sync_hektor_immo_pro.py) le rapatrie dans le miroir,
-- la vue serveur le recompose. Ce patch ouvre les trois portes qui restaient
-- fermees cote Supabase.
--
-- LE PIEGE QUI A FAILLI PASSER. L'application ne lit PAS la table
-- app_dossier_current : elle lit la vue app_dossiers_current (au pluriel), qui
-- n'en projetait que 54 colonnes. Les colonnes commerce ajoutees a la table y
-- restaient invisibles -- et l'ecran n'aurait rien affiche, sans la moindre
-- erreur pour le signaler.
--
-- Toutes les colonnes de vue sont ajoutees EN FIN de projection : CREATE OR
-- REPLACE VIEW l'accepte et conserve les GRANT, contrairement a un DROP+CREATE.

-- ---------------------------------------------------------------------
-- 1. Le registre des mandats : sous-type et famille d'offre
-- ---------------------------------------------------------------------
ALTER TABLE public.app_mandat_register_current
    ADD COLUMN IF NOT EXISTS commerce_sous_type text;
ALTER TABLE public.app_mandat_register_current
    ADD COLUMN IF NOT EXISTS offre_type text;

DO $$
DECLARE existantes text; manquantes text;
BEGIN
  SELECT string_agg(quote_ident(column_name), ', ' ORDER BY ordinal_position)
    INTO existantes
    FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'app_registre_mandats_current';

  IF existantes IS NULL THEN
    RAISE EXCEPTION 'app_registre_mandats_current introuvable';
  END IF;

  -- N'ajouter QUE ce qui manque : un etat partiel (une colonne posee, pas l'autre)
  -- ferait sinon echouer la vue sur un doublon de colonne.
  SELECT string_agg(quote_ident(nom), ', ')
    INTO manquantes
    FROM unnest(ARRAY['commerce_sous_type', 'offre_type']) AS nom
   WHERE NOT EXISTS (
     SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'app_registre_mandats_current' AND column_name = nom);

  IF manquantes IS NULL THEN
    RAISE NOTICE 'app_registre_mandats_current : colonnes deja exposees';
    RETURN;
  END IF;

  EXECUTE format('CREATE OR REPLACE VIEW public.app_registre_mandats_current AS SELECT %s, %s FROM public.app_mandat_register_current',
                 existantes, manquantes);
END $$;

-- ---------------------------------------------------------------------
-- 2. Les annonces : le bloc complet, la ou l'app le lit vraiment
-- ---------------------------------------------------------------------
DO $$
DECLARE existantes text; manquantes text;
BEGIN
  SELECT string_agg(quote_ident(column_name), ', ' ORDER BY ordinal_position)
    INTO existantes
    FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'app_dossiers_current';

  IF existantes IS NULL THEN
    RAISE EXCEPTION 'app_dossiers_current introuvable';
  END IF;

  -- N'ajouter QUE ce qui manque : un etat partiel (une colonne posee, pas l'autre)
  -- ferait sinon echouer la vue sur un doublon de colonne.
  SELECT string_agg(quote_ident(nom), ', ')
    INTO manquantes
    FROM unnest(ARRAY['offre_type', 'commerce_sous_type', 'commerce_famille', 'commerce_activite', 'commerce_loyer', 'commerce_charges', 'commerce_taxe_fonciere', 'commerce_bail_duree', 'commerce_bail_echeance', 'commerce_etat', 'commerce_zone', 'commerce_json']) AS nom
   WHERE NOT EXISTS (
     SELECT 1 FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'app_dossiers_current' AND column_name = nom);

  IF manquantes IS NULL THEN
    RAISE NOTICE 'app_dossiers_current : colonnes deja exposees';
    RETURN;
  END IF;

  EXECUTE format('CREATE OR REPLACE VIEW public.app_dossiers_current AS SELECT %s, %s FROM public.app_dossier_current d',
                 existantes, manquantes);
END $$;

-- ---------------------------------------------------------------------
-- 3. Remplir la famille d'offre du registre
-- ---------------------------------------------------------------------
-- Les annonces que l'app detient font autorite.
UPDATE public.app_mandat_register_current AS r
   SET offre_type = d.offre_type
  FROM public.app_dossier_current AS d
 WHERE d.hektor_annonce_id = r.hektor_annonce_id
   AND r.offre_type IS DISTINCT FROM d.offre_type;

-- Une ligne dont on connait le sous-type est immo pro, meme archivee.
-- (Cet ordre DOIT passer apres le precedent : il le corrige.)
UPDATE public.app_mandat_register_current
   SET offre_type = '10'
 WHERE COALESCE(commerce_sous_type, '') <> '' AND offre_type IS DISTINCT FROM '10';

-- Le reste du registre est de la vente ordinaire.
UPDATE public.app_mandat_register_current
   SET offre_type = '0'
 WHERE offre_type IS NULL;

-- ---------------------------------------------------------------------
-- Le remplissage du bloc commerce sur les annonces ACTIVES ne se fait pas ici :
-- il passe par phase2/sync/backfill_commerce_actives.py, qui lit le serveur.
-- Raison : le paquet nocturne compare un source_hash calcule sur le contenu
-- HEKTOR ; ajouter une colonne ne le fait pas bouger, donc ces lignes ne
-- repartiraient jamais d'elles-memes.
-- ---------------------------------------------------------------------
