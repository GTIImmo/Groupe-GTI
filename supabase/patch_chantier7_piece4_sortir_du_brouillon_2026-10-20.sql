-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER 7, PIECE ④ -- SORTIR UNE ANNONCE DU BROUILLON
-- Les 3 verrous du nouveau type de travail                           20/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- LE TYPE : exit_hektor_draft_annonce
--
-- CE QU'IL EST, ET CE QU'IL N'EST PAS. Il NE CHANGE PAS le statut de l'annonce :
-- il retire le drapeau « brouillon », et l'annonce part dans le catalogue que son
-- statut designe DEJA. Mesure du 20/10 sur les 529 brouillons :
--     241 portent deja « Actif »        277 portent deja « Estimation »
--      11 ne portent rien -- et ce sont des COQUILLES VIDES (ni titre, ni ville,
--         0 EUR, 0 m2, 9 jamais touchees, 2 sans negociateur). Elles sont REFUSEES,
--         a l'ecran ET dans le worker : il n'y a rien a mettre en ligne.
-- ⭐ C'est pour ca qu'il n'y a PAS de 6e statut a ajouter : 518 fiches sur 529
--   savent deja ou elles vont, et les 11 autres ne vont nulle part.
--
-- UN SEUL APPEL A HEKTOR : mode=upval & champ=etatAnnonce & val=1 -- le meme
-- mecanisme que le changement de statut (champ=status). Et c'est REVERSIBLE :
-- etatAnnonce = 2 refait un brouillon.
-- ⚠ Le worker EXIGE LE BASCULEMENT : il relit isDraft par GraphQL avant et apres.
--   Un 200 sans basculement est un refus silencieux, jamais un succes.
--
-- LES TROIS VERROUS (regle du projet, memoire « nouveau-type-de-travail-trois-verrous ») :
--     1. app_console_job_job_type_check   sinon l'INSERT est refuse
--     2. app_console_can_request_job      sinon la politique RLS refuse
--     3. app_console_claim_next_job       sinon PERSONNE ne le reclame -> pending A VIE
--
-- ⭐ LE GESTE EST RESERVE ADMIN / MANAGER, comme l'archivage et le changement de
--   statut : c'est un deplacement STRUCTUREL du bien. Pour l'ouvrir un jour aux
--   negociateurs, il suffira de deplacer le type dans la deuxieme liste de
--   can_request_job (celle qui appelle app_console_can_access_dossier).
--
-- ⚠ METHODE : aucune fonction n'est retapee. On lit la definition vivante, on
--   verifie son empreinte, on verifie que l'ancre y est UNE SEULE FOIS, on
--   remplace. Ancres SUR UNE SEULE LIGNE (lecon 30), et tout litteral multi-ligne
--   insere est normalise chr(13). Si une empreinte a change, LE PATCH S'ARRETE.
--
-- ⛔ Ensuite : pousser, puis REDEMARRER HektorConsoleWorkerAdmin (c'est lui qui
--   porte ce type), ET SEULEMENT FILE VIDE : 0 pending ET 0 running.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── VERROU 1 : la contrainte ──────────────────────────────────────────────────
DO $garde$
DECLARE
    src     text;
    ancre   text := $a$'prepare_brouillon_annonce_detail'::text$a$;
    nouveau text;
    combien int;
BEGIN
    SELECT replace(pg_get_constraintdef(oid), chr(13), '')
      INTO src FROM pg_constraint WHERE conname = 'app_console_job_job_type_check';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : la contrainte app_console_job_job_type_check est introuvable.';
    END IF;
    IF md5(src) <> '306de2345a04fdd21babba7f0064c226' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : la contrainte a change depuis la mesure du 20/10. Attendue '
            '306de2345a04fdd21babba7f0064c226, trouvee %s.', md5(src));
    END IF;
    IF position($c$'exit_hektor_draft_annonce'$c$ in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : le type est DEJA dans la contrainte -- patch deja applique.';
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois (il en faut 1).', combien);
    END IF;
    nouveau := replace(src, ancre, ancre || $b$, 'exit_hektor_draft_annonce'::text$b$);
    EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check ' || nouveau;
END
$garde$;

-- ── VERROU 2 : can_request_job -- RESERVE ADMIN / MANAGER ────────────────────
DO $garde$
DECLARE
    src      text;
    ancre    text := $a$    if target_job_type in ('archive_hektor_annonce', 'change_hektor_annonce_status') then$a$;
    remplace text;
    combien  int;
BEGIN
    -- ⚠ lecon 30 : le texte insere est MULTI-LIGNE -> on le normalise aussi.
    remplace := replace($b$    -- ⑦ piece ④ (20/10/2026) : sortir du brouillon est un deplacement STRUCTUREL
    --   du bien, comme l'archivage et le changement de statut. Meme reserve.
    if target_job_type in ('archive_hektor_annonce', 'change_hektor_annonce_status', 'exit_hektor_draft_annonce') then$b$,
                        chr(13), '');

    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_request_job';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_can_request_job est introuvable.';
    END IF;
    IF md5(src) <> '1edc09ca234a555886cf9d65ae379698' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_console_can_request_job a change. Attendue '
            '1edc09ca234a555886cf9d65ae379698, trouvee %s.', md5(src));
    END IF;
    IF position($c$'exit_hektor_draft_annonce'$c$ in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : le type est DEJA dans can_request_job.';
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans can_request_job.', combien);
    END IF;
    EXECUTE replace(src, ancre, remplace);
END
$garde$;

-- ── VERROU 3 : claim_next_job, liste « admin » ───────────────────────────────
DO $garde$
DECLARE
    src     text;
    ancre   text := $a$'change_hektor_annonce_status','assign_hektor_annonce_negotiator',$a$;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_claim_next_job';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_claim_next_job est introuvable.';
    END IF;
    IF md5(src) <> '1c845e9f0b2334c33e5510c98e8308d7' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_console_claim_next_job a change. Attendue '
            '1c845e9f0b2334c33e5510c98e8308d7, trouvee %s.', md5(src));
    END IF;
    IF position($c$'exit_hektor_draft_annonce'$c$ in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : le type est DEJA dans claim_next_job.';
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans claim_next_job.', combien);
    END IF;
    EXECUTE replace(src, ancre,
        $b$'change_hektor_annonce_status','assign_hektor_annonce_negotiator','exit_hektor_draft_annonce',$b$);
END
$garde$;

-- ── LE TABLEAU DE FIN : un silence ne dit pas si c'est pose ──────────────────
SELECT 1 AS "#", 'verrou 1 -- contrainte job_type' AS objet,
       CASE WHEN (SELECT position('exit_hektor_draft_annonce' in pg_get_constraintdef(oid)) > 0
                    FROM pg_constraint WHERE conname = 'app_console_job_job_type_check')
            THEN 'POSE' ELSE '⛔ PAS POSE' END AS etat
UNION ALL SELECT 2, 'verrou 2 -- can_request_job (admin/manager)',
       CASE WHEN (SELECT position('exit_hektor_draft_annonce' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'POSE' ELSE '⛔ PAS POSE' END
UNION ALL SELECT 3, 'verrou 3 -- claim_next_job (worker ADMIN)',
       CASE WHEN (SELECT position('exit_hektor_draft_annonce' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_claim_next_job')
            THEN 'POSE' ELSE '⛔ PAS POSE' END
UNION ALL SELECT 4, 'TEMOIN INVERSE -- la famille du detail brouillon est intacte',
       CASE WHEN (SELECT position('prepare_brouillon_annonce_detail' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_claim_next_job')
            THEN 'INTACTE' ELSE '⛔ CASSEE -- COLLER L''INVERSE' END
UNION ALL SELECT 5, 'TEMOIN INVERSE -- les gestes admin existants sont intacts',
       CASE WHEN (SELECT position('archive_hektor_annonce' in prosrc) > 0
                     AND position('assign_hektor_annonce_negotiator' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_claim_next_job')
            THEN 'INTACTS' ELSE '⛔ CASSES -- COLLER L''INVERSE' END
ORDER BY 1;

COMMIT;
