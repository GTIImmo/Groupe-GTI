-- ═══════════════════════════════════════════════════════════════════════════════
-- LE REGISTRE AFFICHE DOIT POUVOIR PORTER UN MANDAT SANS BIEN    15/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage, aucun deploiement. Idempotent.
--
-- ─── POURQUOI ───────────────────────────────────────────────────────────────────
-- 38 mandats de RECHERCHE sont entres au registre legal le 15/10. Ils n'ont pas
-- de bien : ils sont portes par un CONTACT. Ils sont en base, mais l'ecran ne
-- peut pas les montrer, et le dernier mur est ici :
--
--     app_mandat_register_current.hektor_annonce_id   bigint NOT NULL   ⛔
--
-- ─── CE QUI A ETE ECARTE, ET POURQUOI ──────────────────────────────────────────
-- ⛔ PAS `app_mandat` : sa cle (annonce, numero) et son NOT NULL restent INTACTS.
--    Un mandat de recherche y vit avec hektor_annonce_id = '' (la chaine vide,
--    jamais NULL) -- c'est ce qui laisse l'index unique proteger (eprouve le 15/10).
-- ⛔ PAS la lecture directe de `app_mandat` par le front : sa regle RLS est
--      using (app_console_can_access_dossier(app_dossier_id, hektor_annonce_id::text))
--    Avec app_dossier_id NULL et une annonce vide, elle rend FAUX : personne ne
--    verrait les 38. Et l'elargir ouvrirait 12 fonctions dont 10 d'ECRITURE
--    (mesure du 14/10, chantier 6a-bis). Chemin ferme.
-- ✅ ICI, en revanche, la regle est `using (is_app_manager_or_admin())` : aucune
--    garde de dossier. L'ecran registre est deja reserve aux admins et managers
--    (decision du 12/10), donc les 38 seront vus par exactement les bonnes personnes.
--
-- ─── POURQUOI C'EST PEU RISQUE ICI ─────────────────────────────────────────────
-- `app_mandat_register_current` N'EST PAS UN REGISTRE, c'est une VUE DE TRAVAIL
-- (decision du 29/09, ecrite dans patch_app_mandat_2026-09-29.sql) : elle est
-- VIDEE ET REFAITE a chaque push. Rendre une colonne facultative n'y met aucune
-- donnee en peril -- contrairement a `app_mandat`, qui garde tout pour toujours.
--
-- ⚠ CE QUE CA NE FAIT PAS : AUCUNE ligne n'apparait apres ce patch. Le fabricant
--   ne produit encore rien pour ces mandats (il part des annonces). Ce patch
--   OUVRE LA PORTE, il ne fait entrer personne. C'est voulu : on mesure le
--   fabricant separement.
--
-- ⚠ CE QUI DEVRA SUIVRE, ET QUI N'EST PAS ICI :
--   · le tri du registre fait `-int(hektor_annonce_id or 0)` : un NULL vaut 0,
--     donc ces lignes se grouperaient en bout de liste. A regler dans le fabricant.
--   · le front lit `hektor_annonce_id` pour le bouton « Hektor »
--     (App.tsx:24329) : un NULL donnerait un lien mort. A masquer.
--
-- ─── RETOUR ARRIERE ────────────────────────────────────────────────────────────
-- ⚠ Il n'est sur QUE si aucune ligne a NULL n'existe (sinon Postgres refuse) :
--     DELETE FROM public.app_mandat_register_current WHERE hektor_annonce_id IS NULL;
--     ALTER TABLE public.app_mandat_register_current
--       ALTER COLUMN hektor_annonce_id SET NOT NULL;
--   Le prochain push reconstruit la table de toute facon.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU : la table doit etre celle qu'on croit.
-- ---------------------------------------------------------------------
DO $garde$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n
    FROM information_schema.columns
   WHERE table_schema = 'public'
     AND table_name   = 'app_mandat_register_current'
     AND column_name  = 'hektor_annonce_id';
  IF n <> 1 THEN
    RAISE EXCEPTION 'ARRET : app_mandat_register_current.hektor_annonce_id est introuvable';
  END IF;

  SELECT count(*) INTO n
    FROM information_schema.columns
   WHERE table_schema = 'public'
     AND table_name   = 'app_mandat_register_current'
     AND column_name  = 'register_row_id'
     AND is_nullable  = 'NO';
  IF n <> 1 THEN
    RAISE EXCEPTION 'ARRET : register_row_id n''est plus la cle obligatoire -- '
                    'la table n''est pas celle mesuree le 15/10';
  END IF;
END $garde$;

-- ---------------------------------------------------------------------
-- LE GESTE
-- ---------------------------------------------------------------------
ALTER TABLE public.app_mandat_register_current
    ALTER COLUMN hektor_annonce_id DROP NOT NULL;

COMMENT ON COLUMN public.app_mandat_register_current.hektor_annonce_id IS
    'Le bien que le mandat couvre. NULL pour un MANDAT DE RECHERCHE, qui est '
    'porte par un CONTACT et non par un bien (app_mandat.app_contact_id). '
    'Rendu facultatif le 15/10/2026 ; app_mandat, lui, garde son NOT NULL.';

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU DE SORTIE
-- ---------------------------------------------------------------------
DO $garde$
DECLARE souple text; lignes bigint;
BEGIN
  SELECT is_nullable INTO souple
    FROM information_schema.columns
   WHERE table_schema = 'public'
     AND table_name   = 'app_mandat_register_current'
     AND column_name  = 'hektor_annonce_id';
  IF souple <> 'YES' THEN
    RAISE EXCEPTION 'La colonne est restee obligatoire (%)', souple;
  END IF;
  SELECT count(*) INTO lignes FROM public.app_mandat_register_current;
  RAISE NOTICE 'OK : hektor_annonce_id est facultative. % ligne(s) au registre '
               'affiche, AUCUNE a NULL pour l''instant (le fabricant n''en produit '
               'pas encore).', lignes;
END $garde$;

-- ─── CONTROLE APRES APPLICATION ────────────────────────────────────────────────
--   SELECT count(*) AS total,
--          count(*) FILTER (WHERE hektor_annonce_id IS NULL) AS sans_bien
--     FROM public.app_mandat_register_current;
--   ATTENDU : total ~24 520, sans_bien = 0 (le fabricant ne les produit pas encore).
