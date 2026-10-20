-- ═══════════════════════════════════════════════════════════════════════════════
-- TEMOIN DE LA PIECE ② -- a coller APRES le patch.           20/10/2026
--
-- ⚠⚠ REECRIT LE 20/10 APRES UN PREMIER ESSAI RATE. La version precedente
--   annoncait « 5 controle(s) en ECHEC » SANS DIRE LESQUELS, et ecrivait son detail
--   en RAISE NOTICE -- or L'EDITEUR SUPABASE N'AFFICHE PAS LES NOTICE. Resultat :
--   Frederic voyait un nombre, et rien d'autre. Deux fautes contre les regles du
--   projet : « un controle qui AGREGE perd ce qui sert a agir -- jamais N sur M,
--   une ligne par objet, nommee », et « mesurer LE GESTE DE L'ECRAN ».
--   ➡ Il RE N D   M A I N T E N A N T   U N   T A B L E A U. Une ligne par objet.
--
-- ⛔ IL N'ECRIT RIEN. Tout est en lecture. La transaction finit par ROLLBACK, parce
--   qu'on EMPRUNTE une identite (set_config) pour eprouver les droits comme les
--   vivrait un negociateur.
--
-- COMMENT LE LIRE : la colonne `verdict` doit etre « OK » partout. Chaque ligne
-- « ECHEC » dit, dans `detail`, ce qui manque et quoi faire.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── On emprunte l'identite d'un negociateur ACTIF qui possede un brouillon ────
-- (s'il n'y en a aucun, les deux derniers controles se declarent « NON MESURE »)
SELECT set_config(
    'request.jwt.claims',
    json_build_object(
        'sub', coalesce((
            SELECT p.id::text
              FROM public.app_brouillon_annonce_index_current b
              JOIN public.app_user_profile p ON lower(p.email) = lower(b.negociateur_email)
             WHERE p.is_active = true AND p.role::text = 'commercial'
               AND nullif(trim(b.negociateur_email), '') IS NOT NULL
             LIMIT 1), '00000000-0000-0000-0000-000000000000'),
        'role', 'authenticated')::text,
    true) AS identite_empruntee;

-- ── LE TABLEAU DES CONTROLES ──────────────────────────────────────────────────
WITH nego AS (
    SELECT p.id AS nego_id, lower(p.email) AS nego_email,
           b.hektor_annonce_id::text AS mon_brouillon, b.app_brouillon_id AS mon_app_id
      FROM public.app_brouillon_annonce_index_current b
      JOIN public.app_user_profile p ON lower(p.email) = lower(b.negociateur_email)
     WHERE p.is_active = true AND p.role::text = 'commercial'
       AND nullif(trim(b.negociateur_email), '') IS NOT NULL
     LIMIT 1
), autre AS (
    SELECT b.hektor_annonce_id::text AS son_brouillon
      FROM public.app_brouillon_annonce_index_current b
     WHERE lower(coalesce(b.negociateur_email, '')) <> coalesce((SELECT nego_email FROM nego), '~')
     LIMIT 1
), c AS (
    -- 1 a 4 : les 3 verrous et les droits
    SELECT 1 AS n, 'verrou 1 -- la contrainte job_type accepte le type' AS controle,
           (SELECT position('prepare_brouillon_annonce_detail' in pg_get_constraintdef(oid)) > 0
              FROM pg_constraint WHERE conname = 'app_console_job_job_type_check') AS vrai,
           'sans lui, l''INSERT du front est refuse net -- COLLER LE PATCH' AS quoi_faire
    UNION ALL SELECT 2, 'verrou 2 -- can_request_job connait le type',
           (SELECT position('prepare_brouillon_annonce_detail' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_can_request_job'),
           'sans lui, la politique RLS refuse la demande d''un negociateur'
    UNION ALL SELECT 3, 'verrou 3 -- claim_next_job le reclamera (worker DOCUMENTS)',
           (SELECT position('prepare_brouillon_annonce_detail' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_claim_next_job'),
           'sans lui, le travail resterait « pending » A VIE, sans erreur'
    UNION ALL SELECT 4, 'droits -- can_access_dossier connait le 4e index',
           (SELECT position('app_brouillon_annonce_index_current' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_can_access_dossier'),
           'sans lui, un negociateur lit 0 ligne SANS ERREUR : defaut muet'
    -- 5 et 6 : LE TEMOIN INVERSE -- les deux familles soeurs sont intactes
    UNION ALL SELECT 5, 'TEMOIN INVERSE -- Archive et Historique toujours reclamees',
           (SELECT position('prepare_archived_annonce_detail' in prosrc) > 0
               AND position('prepare_historical_annonce_detail' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_claim_next_job'),
           'si ECHEC : le patch a casse une famille QUI MARCHAIT -> coller l''INVERSE'
    UNION ALL SELECT 6, 'TEMOIN INVERSE -- les 2 index soeurs sont encore lus',
           (SELECT position('app_archive_annonce_index_current' in prosrc) > 0
               AND position('app_historical_annonce_index_current' in prosrc) > 0
              FROM pg_proc WHERE proname = 'app_console_can_access_dossier'),
           'si ECHEC : coller l''INVERSE immediatement'
    -- 7 : la table du cache et ses droits (elle EXISTAIT avant le patch)
    UNION ALL SELECT 7, 'le cache brouillon a bien ses 2 politiques',
           (SELECT count(*) = 2 FROM pg_policy p JOIN pg_class k ON k.oid = p.polrelid
             WHERE k.relname = 'app_brouillon_annonce_detail_cache'),
           'elle existait AVANT le patch : si ECHEC, ce n''est pas le patch'
    -- 8 et 9 : ⭐⭐ LE VRAI TEST, celui du defaut muet
    UNION ALL SELECT 8, 'un negociateur PEUT lire le cache de SON brouillon',
           CASE WHEN (SELECT nego_id FROM nego) IS NULL THEN NULL
                ELSE public.app_console_can_access_dossier(
                        (SELECT mon_app_id FROM nego), (SELECT mon_brouillon FROM nego)) END,
           'c''est LE test : avant le patch, c''etait faux pour TOUT brouillon'
    UNION ALL SELECT 9, 'et il ne peut PAS lire celui de quelqu''un d''autre',
           CASE WHEN (SELECT son_brouillon FROM autre) IS NULL THEN NULL
                ELSE NOT public.app_console_can_access_dossier(
                        NULL, (SELECT son_brouillon FROM autre)) END,
           'si ECHEC : on a ouvert le perimetre de TOUT LE MONDE -- bien pire'
)
SELECT c.n AS "#",
       CASE WHEN c.vrai IS NULL THEN '⚠ NON MESURE'
            WHEN c.vrai THEN 'OK'
            ELSE '⛔ ECHEC' END AS verdict,
       c.controle,
       CASE WHEN c.vrai IS NULL THEN 'aucun negociateur commercial actif ne possede de brouillon'
            WHEN c.vrai THEN ''
            ELSE c.quoi_faire END AS detail,
       CASE WHEN c.n IN (8, 9) THEN coalesce((SELECT nego_email FROM nego), '(aucun)') ELSE '' END AS identite_eprouvee
  FROM c
 ORDER BY c.n;

ROLLBACK;

-- ═══════════════════════════════════════════════════════════════════════════════
-- ⭐ TOUT « OK » (ou « NON MESURE » sur 8 et 9) -> la piece ② est posee en base.
--   Il reste alors : POUSSER, puis REDEMARRER HektorConsoleWorkerDocuments
--   (et SEULEMENT file vide : 0 pending ET 0 running).
-- ⛔ UN « ECHEC » sur 5 ou 6 -> coller l'INVERSE TOUT DE SUITE : le patch aurait
--   emporte une famille qui marchait.
-- ═══════════════════════════════════════════════════════════════════════════════
