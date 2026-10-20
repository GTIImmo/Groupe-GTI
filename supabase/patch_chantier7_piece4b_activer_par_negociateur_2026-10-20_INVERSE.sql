-- ═══════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DE LA PIECE ④b -- « activer » redevient admin/manager
--                                                                    20/10/2026
-- ⚠ Il ne juge que SA part : il remet le geste dans la liste admin/manager et le
--   retire de celle des negociateurs. Il ne defait PAS la piece ④ elle-meme (le
--   geste continue d'exister), ni les activations deja faites.
-- ⛔ Penser au front : le bouton suivra la regle de la base pour les negociateurs
--   (ils recevront un refus), mais il vaut mieux repousser le front aussi.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
DECLARE
    src     text;
    bloc    text;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_request_job';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_can_request_job est introuvable.';
    END IF;

    -- ⚠ lecon 30 : ancre MULTI-LIGNE -> on la normalise, sinon le retrait echouerait
    --   EN SILENCE sur un fichier passe en CRLF.
    bloc := replace($a$,
            -- ⑦ piece ④b (20/10/2026) : ACTIVER SES PROPRES BROUILLONS.
            --   Ici et pas dans la liste admin : le perimetre vient de
            --   app_console_can_access_dossier, qui connait l'index brouillon depuis
            --   la piece ② -- donc « ses biens », garanti par la base, pas par l'ecran.
            --   ⚠ « changer le statut » et « archiver » restent admin/manager : ils
            --     sont dans la PREMIERE liste, qu'on ne touche pas.
            'exit_hektor_draft_annonce'$a$, chr(13), '');

    combien := (length(src) - length(replace(src, bloc, ''))) / length(bloc);
    IF combien = 0 THEN
        RAISE NOTICE 'Rien a retirer de la liste negociateur.';
    ELSIF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : le bloc negociateur apparait %s fois.', combien);
    ELSE
        src := replace(src, bloc, '');
    END IF;

    -- et on le remet dans la liste admin/manager
    IF position($b$, 'exit_hektor_draft_annonce') then$b$ in src) = 0 THEN
        combien := (length(src) - length(replace(src, $c$'change_hektor_annonce_status') then$c$, '')))
                   / length($c$'change_hektor_annonce_status') then$c$);
        IF combien <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre admin apparait %s fois.', combien);
        END IF;
        src := replace(src, $c$'change_hektor_annonce_status') then$c$,
                            $d$'change_hektor_annonce_status', 'exit_hektor_draft_annonce') then$d$);
    END IF;

    EXECUTE src;
END
$garde$;

SELECT 1 AS "#", 'le geste est REVENU en admin/manager' AS controle,
       CASE WHEN (SELECT position($a$, 'exit_hektor_draft_annonce') then$a$ in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'et il n''est plus dans la liste negociateur',
       CASE WHEN (SELECT (length(prosrc) - length(replace(prosrc, 'exit_hektor_draft_annonce', '')))
                         / length('exit_hektor_draft_annonce') = 1
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ il y est encore (ou deux fois)' END
UNION ALL SELECT 3, '⚠ TEMOIN INVERSE -- les gestes du negociateur sont intacts',
       CASE WHEN (SELECT position('update_hektor_annonce_fields' in prosrc) > 0
                     AND position('prepare_brouillon_annonce_detail' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ J''AI CASSE AUTRE CHOSE' END
ORDER BY 1;

COMMIT;
