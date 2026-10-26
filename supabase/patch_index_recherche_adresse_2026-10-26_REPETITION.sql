-- ============================================================================
-- CONTROLE de patch_index_recherche_adresse_2026-10-26.sql -- lecture seule.
-- Se colle EN ENTIER (pas de CONCURRENTLY ici). Une ligne par controle, verdict OK / KO.
--   1-4  chaque index existe ET est valide (un CONCURRENTLY interrompu laisse un index
--        « invalide » : il existe mais ne sert a rien -- le relancer apres l'avoir retire) ;
--   5-8  la recherche passe PAR l'index, et son temps (pire cas : un mot absent) ;
--   9    TEMOIN : la recherche des mandants, deja indexee, n'a pas bouge.
-- ============================================================================

CREATE OR REPLACE FUNCTION pg_temp.plan(q text) RETURNS json LANGUAGE plpgsql AS $$
DECLARE p json;
BEGIN
  EXECUTE 'EXPLAIN (ANALYZE, FORMAT JSON) ' || q INTO p;
  RETURN p;
END $$;

WITH idx(n, controle, nom) AS (VALUES
  (1, 'index adresse des annonces en cours',  'idx_app_dossier_current_search_adresse_trgm'),
  (2, 'index adresse du registre',            'idx_app_mandat_register_search_adresse_trgm'),
  (3, 'index texte du registre',              'idx_app_mandat_register_search_text_trgm'),
  (4, 'index adresse des contacts',           'idx_app_contact_current_search_adresse_trgm')
),
etat AS (
  SELECT i.n, i.controle, i.nom,
         c.oid IS NOT NULL AS existe,
         coalesce(x.indisvalid, false) AS valide,
         CASE WHEN c.oid IS NOT NULL THEN pg_size_pretty(pg_relation_size(c.oid)) END AS taille
  FROM idx i
  LEFT JOIN pg_class c ON c.relname = i.nom AND c.relnamespace = 'public'::regnamespace
  LEFT JOIN pg_index x ON x.indexrelid = c.oid
),
req(n, controle, nom, q) AS (VALUES
  (5, 'adresse des annonces en cours passe par l''index', 'idx_app_dossier_current_search_adresse_trgm',
      'select app_dossier_id from public.app_dossier_current where adresse_detail ilike ''%zzqqxx%'' limit 6'),
  (6, 'adresse du registre passe par l''index', 'idx_app_mandat_register_search_adresse_trgm',
      'select register_row_id from public.app_mandat_register_current where search_text ilike ''%zzqqxx%'' or adresse_detail ilike ''%zzqqxx%'' limit 6'),
  (7, 'texte du registre passe par l''index', 'idx_app_mandat_register_search_text_trgm',
      'select register_row_id from public.app_mandat_register_current where search_text ilike ''%zzqqxx%'' or adresse_detail ilike ''%zzqqxx%'' limit 6'),
  (8, 'adresse des contacts passe par l''index', 'idx_app_contact_current_search_adresse_trgm',
      'select hektor_contact_id from public.app_contact_current where search_text ilike ''%zzqqxx%'' or adresse ilike ''%zzqqxx%'' limit 6'),
  (9, 'TEMOIN : mandants des annonces, inchange', 'idx_app_dossier_current_search_mandants_trgm',
      'select app_dossier_id from public.app_dossier_current where mandants_texte ilike ''%zzqqxx%'' limit 6')
),
mesures AS (
  SELECT r.n, r.controle, r.nom, pg_temp.plan(r.q) AS p FROM req r
)
SELECT n, controle,
       CASE WHEN existe AND valide THEN 'OK' ELSE 'KO' END AS verdict,
       concat('existe=', existe, ' valide=', valide, coalesce(' taille=' || taille, '')) AS detail
FROM etat
UNION ALL
SELECT n, controle,
       CASE WHEN p::text LIKE '%' || nom || '%' AND (p -> 0 ->> 'Execution Time')::numeric < 300 THEN 'OK' ELSE 'KO' END,
       concat(CASE WHEN p::text LIKE '%' || nom || '%' THEN 'index utilise' ELSE 'INDEX NON UTILISE' END,
              ', ', round((p -> 0 ->> 'Execution Time')::numeric, 1), ' ms')
FROM mesures
ORDER BY n;
