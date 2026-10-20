-- ═══════════════════════════════════════════════════════════════════════════════
-- TEMOIN DE LA PIECE ④ -- a coller APRES le patch.            20/10/2026
--
-- ⛔ IL N'ECRIT RIEN. Tout est en lecture ; la transaction finit par ROLLBACK parce
--   qu'on EMPRUNTE deux identites (set_config) pour eprouver les droits en vrai.
-- ⭐ IL REND UN TABLEAU, pas des NOTICE : l'editeur Supabase n'affiche pas les
--   NOTICE (lecon apprise le 20/10, a la piece ②).
--
-- La colonne `verdict` doit etre « OK » partout.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- on emprunte l'identite d'un ADMIN actif
SELECT set_config('request.jwt.claims',
    json_build_object('sub', coalesce((SELECT id::text FROM public.app_user_profile
                                        WHERE is_active = true AND role::text = 'admin' LIMIT 1),
                                      '00000000-0000-0000-0000-000000000000'),
                      'role', 'authenticated')::text, true) AS identite_admin;

WITH c AS (
    SELECT 1 AS n, 'verrou 1 -- la contrainte accepte le type' AS controle,
           (SELECT position('exit_hektor_draft_annonce' in pg_get_constraintdef(oid)) > 0
              FROM pg_constraint WHERE conname = 'app_console_job_job_type_check') AS vrai,
           'sans lui, l''INSERT est refuse net -- COLLER LE PATCH' AS quoi_faire
    UNION ALL SELECT 2, 'verrou 2 -- can_request_job connait le type',
           (SELECT position('exit_hektor_draft_annonce' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_can_request_job'),
           'sans lui, la politique RLS refuse la demande'
    UNION ALL SELECT 3, 'verrou 3 -- le worker ADMIN le reclamera',
           (SELECT position('exit_hektor_draft_annonce' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_claim_next_job'),
           'sans lui, le travail reste « pending » A VIE, sans erreur'
    UNION ALL SELECT 4, '⭐ UN ADMIN PEUT demander le geste',
           public.app_console_can_request_job('exit_hektor_draft_annonce', NULL, NULL),
           'c''est LE test : le geste doit etre demandable par un admin'
    UNION ALL SELECT 5, 'TEMOIN INVERSE -- la piece ② (detail brouillon) est intacte',
           (SELECT position('prepare_brouillon_annonce_detail' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_claim_next_job'),
           'si ECHEC : le patch a casse la piece 2 -> coller l''INVERSE'
    UNION ALL SELECT 6, 'TEMOIN INVERSE -- archivage et statut toujours reserves',
           (SELECT position('archive_hektor_annonce' in prosrc) > 0
               AND position('change_hektor_annonce_status' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_can_request_job'),
           'si ECHEC : coller l''INVERSE immediatement'
)
SELECT c.n AS "#",
       CASE WHEN c.vrai IS NULL THEN '⚠ NON MESURE' WHEN c.vrai THEN 'OK' ELSE '⛔ ECHEC' END AS verdict,
       c.controle,
       CASE WHEN coalesce(c.vrai, false) THEN '' ELSE c.quoi_faire END AS detail
  FROM c ORDER BY c.n;

ROLLBACK;

-- ═══════════════════════════════════════════════════════════════════════════════
-- ⚠ LE TEST DU REFUS, A COLLER SEPAREMENT (il emprunte une AUTRE identite) :
--
-- BEGIN;
-- SELECT set_config('request.jwt.claims',
--     json_build_object('sub', (SELECT id::text FROM public.app_user_profile
--                                WHERE is_active = true AND role::text = 'commercial' LIMIT 1),
--                       'role', 'authenticated')::text, true);
-- SELECT CASE WHEN public.app_console_can_request_job('exit_hektor_draft_annonce', NULL, NULL)
--             THEN '⛔ ECHEC : un negociateur PEUT sortir du brouillon -- ce n''etait pas voulu'
--             ELSE 'OK : un negociateur ne peut PAS, le geste reste admin/manager' END AS verdict;
-- ROLLBACK;
-- ═══════════════════════════════════════════════════════════════════════════════
