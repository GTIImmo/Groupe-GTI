-- Vignette des annonces des index légers (archivées + vendues/closes)
-- -----------------------------------------------------------------------------
-- Problème : app_archive_annonce_index_current et app_historical_annonce_index_current
-- (index "légers") ne portaient pas de photo. La photo existe pourtant dans la source
-- locale app_view_generale.photo_url_listing (déjà lue par l'index actif et le registre).
-- On matérialise donc la colonne dans les deux index pour qu'ils soient autosuffisants
-- (listing + détail annonce + vignette du bien lié dans la fiche contact), sans dépendre
-- du registre des mandats (pas de mélange de sources).
--
-- 1) Colonne. 2) Backfill immédiat depuis dossiers (actifs) + registre (vendus/archivés),
--    en ne gardant qu'une vraie photo (on ignore les placeholders no_pic).
--    Le sync Python (export_app_payload.py + push_upgrade_to_supabase.py) prend ensuite
--    le relais comme source canonique (app_view_generale.photo_url_listing).

ALTER TABLE public.app_archive_annonce_index_current
  ADD COLUMN IF NOT EXISTS photo_url_listing text;

ALTER TABLE public.app_historical_annonce_index_current
  ADD COLUMN IF NOT EXISTS photo_url_listing text;

WITH photos AS (
  SELECT aid, max(photo) AS photo
  FROM (
    SELECT hektor_annonce_id::text AS aid, photo_url_listing AS photo
    FROM public.app_dossiers_current
    WHERE photo_url_listing IS NOT NULL AND photo_url_listing NOT ILIKE '%no_pic%'
    UNION ALL
    SELECT hektor_annonce_id::text, photo_url_listing
    FROM public.app_registre_mandats_current
    WHERE photo_url_listing IS NOT NULL AND photo_url_listing NOT ILIKE '%no_pic%'
  ) s
  GROUP BY aid
)
UPDATE public.app_archive_annonce_index_current i
SET photo_url_listing = p.photo
FROM photos p
WHERE p.aid = i.hektor_annonce_id::text
  AND i.photo_url_listing IS DISTINCT FROM p.photo;

WITH photos AS (
  SELECT aid, max(photo) AS photo
  FROM (
    SELECT hektor_annonce_id::text AS aid, photo_url_listing AS photo
    FROM public.app_dossiers_current
    WHERE photo_url_listing IS NOT NULL AND photo_url_listing NOT ILIKE '%no_pic%'
    UNION ALL
    SELECT hektor_annonce_id::text, photo_url_listing
    FROM public.app_registre_mandats_current
    WHERE photo_url_listing IS NOT NULL AND photo_url_listing NOT ILIKE '%no_pic%'
  ) s
  GROUP BY aid
)
UPDATE public.app_historical_annonce_index_current i
SET photo_url_listing = p.photo
FROM photos p
WHERE p.aid = i.hektor_annonce_id::text
  AND i.photo_url_listing IS DISTINCT FROM p.photo;
