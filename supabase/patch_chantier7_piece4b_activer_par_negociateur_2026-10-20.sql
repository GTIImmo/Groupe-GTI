-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER 7, PIECE ④b -- UN NEGOCIATEUR PEUT ACTIVER SES PROPRES BROUILLONS
--                                                                    20/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- CE QUE CE PATCH FAIT. Il deplace `exit_hektor_draft_annonce` de la liste
-- ADMIN/MANAGER vers la liste des gestes qu'un NEGOCIATEUR peut demander.
--
-- ⭐⭐ ET LE PERIMETRE SE FAIT TOUT SEUL, SANS UNE LIGNE DE PLUS. La deuxieme
--   liste de can_request_job ne rend pas `true` : elle appelle
--       app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id)
--   et CETTE fonction connait l'index brouillon depuis la piece ② (20/10). Donc un
--   negociateur ne peut activer que les brouillons dont il est le negociateur --
--   c'est la fonction des droits qui le garantit, PAS l'ecran.
--
-- CE QUE CA DONNE, mesure du 20/10 sur les 529 brouillons :
--     509 ont un negociateur   -> leur negociateur pourra les activer
--      20 n'en ont aucun       -> hors de portee d'un negociateur (ils n'appartiennent
--                                 a personne) : admin/manager seulement
--      11 sont des coquilles vides -> REFUSEES pour tout le monde, a l'ecran ET
--                                 dans le worker
--
-- ⚠ ET CA N'OUVRE RIEN D'AUTRE. « Changer le statut » et « archiver » restent
--   reserves admin/manager : ils sont dans la PREMIERE liste, qu'on ne touche pas.
--   C'est precisement pour ca que « activer » est un geste A PART et non une
--   variante du changement de statut -- demande de Frederic, 20/10.
--
-- ⭐ ACTIVER NE DIFFUSE RIEN : `diffusable = 0` pour les 529 (mesure du 20/10), et
--   le geste n'y touche pas. Le bien entre au catalogue, il n'est publie nulle part.
--
-- RETOUR ARRIERE : ..._INVERSE.sql (il remet le geste en admin/manager).
-- ⛔ Ensuite : pousser le front (le bouton suit la meme regle). Le worker, lui, n'a
--   PAS besoin d'etre redemarre : rien ne change de son cote.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
DECLARE
    src      text;
    retrait  text := $a$, 'exit_hektor_draft_annonce') then$a$;
    ajout    text := $b$            'create_hektor_mandat_auto_number','restore_hektor_annonce'$b$;
    nouveau  text;
    combien  int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_request_job';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_can_request_job est introuvable.';
    END IF;
    IF md5(src) <> '3121945c4b5a1e5ec01a3994c01fe273' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_console_can_request_job a change depuis la mesure du 20/10. '
            'Attendue 3121945c4b5a1e5ec01a3994c01fe273, trouvee %s.', md5(src));
    END IF;

    -- 1) on RETIRE le type de la liste admin/manager
    combien := (length(src) - length(replace(src, retrait, ''))) / length(retrait);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre de retrait apparait %s fois.', combien);
    END IF;
    nouveau := replace(src, retrait, ') then');

    -- 2) on l'AJOUTE a la liste des negociateurs -- celle qui passe par
    --    app_console_can_access_dossier, donc « ses biens seulement ».
    combien := (length(nouveau) - length(replace(nouveau, ajout, ''))) / length(ajout);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre d''ajout apparait %s fois.', combien);
    END IF;
    -- ⚠ lecon 30 : le texte insere est MULTI-LIGNE -> on le normalise aussi.
    nouveau := replace(nouveau, ajout, replace($c$            'create_hektor_mandat_auto_number','restore_hektor_annonce',
            -- ⑦ piece ④b (20/10/2026) : ACTIVER SES PROPRES BROUILLONS.
            --   Ici et pas dans la liste admin : le perimetre vient de
            --   app_console_can_access_dossier, qui connait l'index brouillon depuis
            --   la piece ② -- donc « ses biens », garanti par la base, pas par l'ecran.
            --   ⚠ « changer le statut » et « archiver » restent admin/manager : ils
            --     sont dans la PREMIERE liste, qu'on ne touche pas.
            'exit_hektor_draft_annonce'$c$, chr(13), ''));

    EXECUTE nouveau;
END
$garde$;

-- ── LE TABLEAU DE FIN ────────────────────────────────────────────────────────
SELECT 1 AS "#", 'le geste N''EST PLUS dans la liste admin/manager' AS controle,
       CASE WHEN (SELECT position($a$'change_hektor_annonce_status', 'exit_hektor_draft_annonce'$a$ in prosrc) = 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'il EST dans la liste des negociateurs',
       CASE WHEN (SELECT position($a$'exit_hektor_draft_annonce'$a$ in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, '⚠ TEMOIN INVERSE -- archiver et changer le statut restent admin',
       CASE WHEN (SELECT position($a$'archive_hektor_annonce', 'change_hektor_annonce_status') then$a$ in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ J''AI OUVERT AUTRE CHOSE -- COLLER L''INVERSE' END
UNION ALL SELECT 4, '⚠ TEMOIN INVERSE -- le detail brouillon (piece ②) est intact',
       CASE WHEN (SELECT position($a$'prepare_brouillon_annonce_detail'$a$ in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
