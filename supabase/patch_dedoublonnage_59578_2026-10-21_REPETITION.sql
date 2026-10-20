-- ════════════════════════════════════════════════════════════════════════════
-- REPETITION du dedoublonnage de 59578 -- 9 controles              21/10/2026
-- ════════════════════════════════════════════════════════════════════════════
-- A COLLER APRES le patch. Il NE FAIT QUE LIRE.
-- Chaque ligne porte son verdict : ✅ ou ⛔. Une seule ⛔ = on appelle l'inverse.
-- ⚠ « Un controle qui AGREGE perd ce qui sert a agir » : chaque controle dit sa
--   valeur ET sa reference, jamais un « N sur M » seul.
-- ⚠⚠ Le controle (9) est le TEMOIN INVERSE, et c'est le plus important :
--    un geste qui enleve TOUT serait un desastre silencieux.
-- ════════════════════════════════════════════════════════════════════════════

WITH f AS (
  SELECT id, document_name, hektor_document_id, sha256, created_at, source, storage_path,
         regexp_replace(metadata_json->>'console_url', '^https?://[^/]+', '') AS chemin,
         (metadata_json->>'console_url' LIKE '%la-boite-immo.com%') AS ancien
    FROM app_console_document
   WHERE hektor_annonce_id = '59578'
     AND source LIKE 'hektor_console%'
     AND metadata_json->>'console_url' IS NOT NULL
),
doublons AS (
  SELECT chemin, source, count(*) AS n
    FROM f GROUP BY chemin, source HAVING count(*) > 1
)
SELECT * FROM (

  -- (1) LA PREUVE D'ABORD : il ne reste AUCUN chemin en double
  SELECT 1 AS n, 'plus aucun document en double' AS controle,
         (SELECT count(*) FROM doublons)::text AS mesure, '0 attendu' AS reference,
         CASE WHEN (SELECT count(*) FROM doublons) = 0 THEN '✅' ELSE '⛔' END AS verdict

  -- (2) le compte des fiches : 35 - 17 = 18
  UNION ALL SELECT 2, 'fiches sur 59578',
         (SELECT count(*) FROM app_console_document WHERE hektor_annonce_id = '59578')::text,
         '18 attendues (35 - 17)',
         CASE WHEN (SELECT count(*) FROM app_console_document WHERE hektor_annonce_id = '59578') = 18
              THEN '✅' ELSE '⛔' END

  -- (3) ⭐ LES ANCIENNES SONT TOUTES LA -- c'est elles qu'on garde
  UNION ALL SELECT 3, 'fiches a l''ANCIENNE adresse conservees',
         (SELECT count(*) FROM f WHERE ancien)::text, '17 attendues',
         CASE WHEN (SELECT count(*) FROM f WHERE ancien) = 17 THEN '✅' ELSE '⛔' END

  -- (4) ⭐⭐ ET ELLES ONT GARDE LEUR DATE DE NAISSANCE DU 17 AOUT
  UNION ALL SELECT 4, 'conservees nees le 2026-08-17 (leur numero d''origine)',
         (SELECT count(*) FROM f WHERE ancien AND created_at::date = '2026-08-17')::text,
         '17 attendues',
         CASE WHEN (SELECT count(*) FROM f WHERE ancien AND created_at::date = '2026-08-17') = 17
              THEN '✅' ELSE '⛔' END

  -- (5) les neuves du 20/10 12:22 sont parties
  UNION ALL SELECT 5, 'fiches neuves du 20/10 restantes',
         (SELECT count(*) FROM f WHERE NOT ancien AND created_at::date = '2026-10-20')::text,
         '0 attendue',
         CASE WHEN (SELECT count(*) FROM f WHERE NOT ancien AND created_at::date = '2026-10-20') = 0
              THEN '✅' ELSE '⛔' END

  -- (6) ⭐ AUCUN FICHIER PERDU : chaque fiche restante ouvre encore
  UNION ALL SELECT 6, 'fiches restantes SANS fichier au coffre',
         (SELECT count(*) FROM f WHERE storage_path IS NULL)::text, '0 attendue',
         CASE WHEN (SELECT count(*) FROM f WHERE storage_path IS NULL) = 0 THEN '✅' ELSE '⛔' END

  -- (7) la sauvegarde datee existe et porte les 17
  UNION ALL SELECT 7, 'lignes dans la sauvegarde datee',
         coalesce((SELECT count(*)::text FROM app_console_document_avant_dedoublonnage_59578_20261021), 'TABLE ABSENTE'),
         '17 attendues',
         CASE WHEN coalesce((SELECT count(*) FROM app_console_document_avant_dedoublonnage_59578_20261021), 0) = 17
              THEN '✅' ELSE '⛔' END

  -- (8) ⛔ AUCUNE SIGNATURE N'A ETE TOUCHEE sur cette annonce
  UNION ALL SELECT 8, 'documents signes sur 59578 (il n''y en avait aucun)',
         (SELECT count(*) FROM app_console_document
           WHERE hektor_annonce_id = '59578'
             AND (metadata_json->'signature'->>'status' IS NOT NULL
                  OR metadata_json ? 'signed_document'))::text,
         '0 avant, 0 apres',
         CASE WHEN (SELECT count(*) FROM app_console_document
                     WHERE hektor_annonce_id = '59578'
                       AND (metadata_json->'signature'->>'status' IS NOT NULL
                            OR metadata_json ? 'signed_document')) = 0 THEN '✅' ELSE '⛔' END

  -- (9) ⚠⚠ TEMOIN INVERSE : le geste n'a PAS vide l'annonce, et il n'a touche
  --     QUE 59578. Un dedoublonnage qui enleve tout « reussit » sans rien dire.
  UNION ALL SELECT 9, '⚠ TEMOIN INVERSE : documents du parc (hors 59578) intacts',
         (SELECT count(*) FROM app_console_document WHERE hektor_annonce_id <> '59578')::text,
         '192 591 attendus (192 626 - 35)',
         CASE WHEN (SELECT count(*) FROM app_console_document WHERE hektor_annonce_id <> '59578')
                   BETWEEN 192500 AND 193200 THEN '✅' ELSE '⛔ REMESURER' END

) x ORDER BY n;

-- ════════════════════════════════════════════════════════════════════════════
-- ⏰ ET APRES, AU PROCHAIN BALAYAGE : le correctif doit RE-CLER les 17 anciennes
--    par leur chemin. Pour le voir :
--      python phase2/checks/controle_domaine_documents.py
--    Son temoin (« fiches nees AVANT la bascule au nouveau domaine ») doit monter
--    de 17, et le journal doit porter « reconnus par leur CHEMIN » pour 59578.
-- ⚠ LE CONTROLE (9) A UNE FOURCHETTE EXPRES : le parc bouge toutes les nuits.
--    S'il sort ⛔, ce n'est pas forcement un degat -- c'est « remesurer ».
-- ════════════════════════════════════════════════════════════════════════════
