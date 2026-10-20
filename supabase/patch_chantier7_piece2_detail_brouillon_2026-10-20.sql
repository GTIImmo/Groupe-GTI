-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER 7, PIECE ② -- LE DETAIL D'UN BROUILLON POUR 24 H
-- Les 3 verrous du nouveau type de travail + les droits de lecture du cache
--                                                                    20/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- CE QUE CE PATCH AJOUTE. Un seul nouveau type de travail :
--     prepare_brouillon_annonce_detail
-- la troisieme soeur de `prepare_archived_annonce_detail` et
-- `prepare_historical_annonce_detail`, qui tournent depuis le 08/10 (49 travaux,
-- 49 reussis). Elle reconstruit la fiche complete d'un BROUILLON depuis notre
-- miroir local, la depose dans `app_brouillon_annonce_detail_cache`, et le front
-- la lit -- tout ce chemin de lecture EXISTE DEJA et n'est pas touche ici.
--
-- ⭐ LA TABLE ET SES DROITS EXISTENT DEJA : `app_brouillon_annonce_detail_cache`
--   porte les 8 memes colonnes que sa soeur Archive, et ses 2 politiques sont
--   clonees du meme patron. Rien a creer.
--
-- POURQUOI QUATRE OBJETS ET PAS UN. La regle du projet
-- (memoire « nouveau-type-de-travail-trois-verrous ») : un type de travail neuf
-- doit passer TROIS verrous, sinon il reste « pending » a vie, sans erreur :
--     1. la contrainte  app_console_job_job_type_check   sinon l'INSERT est refuse
--     2. app_console_can_request_job                     sinon la politique RLS refuse
--     3. app_console_claim_next_job                      sinon PERSONNE ne le reclame
-- Le quatrieme objet, `app_console_can_access_dossier`, est le DEFAUT MUET trouve
-- a l'audit : il connait 3 index sur 4 (parc vivant, archive, historique) et PAS
-- le panier brouillon. Sans lui, un NEGOCIATEUR lirait 0 ligne du cache, sans
-- erreur, et la fiche ne s'ouvrirait jamais.
-- ⭐ Un admin ou un manager, lui, passe deja (`return true` inconditionnel) --
--   donc ce quatrieme objet ne change RIEN pour Frederic, et tout pour les negos.
--
-- ⚠ METHODE : AUCUNE FONCTION N'EST RETAPEE. On lit la definition vivante, on
--   verifie son empreinte, on verifie que l'ancre y est UNE SEULE FOIS, et on
--   remplace. Les ancres sont SUR UNE SEULE LIGNE (lecon 30 du projet), donc
--   immunisees aux retours chariot. Si une empreinte a change -- parce qu'un autre
--   developpeur est passe -- LE PATCH S'ARRETE ET NE FAIT RIEN.
--
-- ⛔ RIEN N'EST DEPLOYE PAR CE PATCH. Le worker doit etre REDEMARRE ensuite
--   (HektorConsoleWorkerDocuments), et seulement file vide : 0 pending ET 0 running.
--
-- RETOUR ARRIERE : supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20_INVERSE.sql
-- TEMOIN        : supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- VERROU 1 -- LA CONTRAINTE. Sans elle, l'INSERT du front est refuse net.
-- Elle est NOT VALID aujourd'hui : on la repose NOT VALID a l'identique.
-- ─────────────────────────────────────────────────────────────────────────────
DO $garde$
DECLARE
    src        text;
    nouveau    text;
    ancre      text := $a$'prepare_historical_annonce_detail'::text$a$;
    remplace   text := $b$'prepare_historical_annonce_detail'::text, 'prepare_brouillon_annonce_detail'::text$b$;
    combien    int;
BEGIN
    SELECT replace(pg_get_constraintdef(oid), chr(13), '')
      INTO src
      FROM pg_constraint
     WHERE conname = 'app_console_job_job_type_check';

    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : la contrainte app_console_job_job_type_check est introuvable.';
    END IF;
    IF md5(src) <> '5075b433a31d2dddb52c707a7cd48d9d' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : la contrainte a change depuis l''audit du 20/10. Empreinte attendue '
            '5075b433a31d2dddb52c707a7cd48d9d, trouvee %s. Quelqu''un est passe : relire avant de coller.',
            md5(src));
    END IF;
    IF position($c$'prepare_brouillon_annonce_detail'$c$ in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : le type prepare_brouillon_annonce_detail est DEJA dans la contrainte -- patch deja applique.';
    END IF;

    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans la contrainte (il en faut 1).', combien);
    END IF;

    nouveau := replace(src, ancre, remplace);

    EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check ' || nouveau;
    RAISE NOTICE 'VERROU 1 pose : la contrainte accepte maintenant prepare_brouillon_annonce_detail.';
END
$garde$;

-- ─────────────────────────────────────────────────────────────────────────────
-- VERROU 2 -- app_console_can_request_job. Sans lui, la politique RLS d'INSERT
-- (app_console_job_insert_scope) refuse la demande d'un NEGOCIATEUR.
-- ⭐ Un admin/manager passait deja : ce verrou est pour les negos.
-- ─────────────────────────────────────────────────────────────────────────────
DO $garde$
DECLARE
    src      text;
    ancre    text := $a$'prepare_document_cloud','upload_document_to_hektor','prepare_archived_annonce_detail','prepare_historical_annonce_detail',$a$;
    remplace text := $b$'prepare_document_cloud','upload_document_to_hektor','prepare_archived_annonce_detail','prepare_historical_annonce_detail',
            -- ⑦ piece ② (20/10/2026) : la troisieme soeur. C'est une LECTURE -- elle
            -- reconstruit la fiche depuis NOTRE miroir, sans un seul appel a Hektor.
            'prepare_brouillon_annonce_detail',$b$;
    combien  int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_request_job';

    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_can_request_job est introuvable.';
    END IF;
    IF md5(src) <> '68d6883063e31518a9ea46b5ad590b79' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_console_can_request_job a change depuis l''audit. Attendue '
            '68d6883063e31518a9ea46b5ad590b79, trouvee %s.', md5(src));
    END IF;
    IF position($c$'prepare_brouillon_annonce_detail'$c$ in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : le type est DEJA dans can_request_job -- patch deja applique.';
    END IF;

    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans can_request_job (il en faut 1).', combien);
    END IF;

    EXECUTE replace(src, ancre, remplace);
    RAISE NOTICE 'VERROU 2 pose : un negociateur peut demander le detail d''un brouillon de son perimetre.';
END
$garde$;

-- ─────────────────────────────────────────────────────────────────────────────
-- VERROU 3 -- app_console_claim_next_job, liste « documents ». Sans lui, le
-- travail serait cree puis resterait « pending » A VIE, sans aucune erreur :
-- c'est exactement le defaut muet du 03/10 (unlink_hektor_mandant).
-- ⚠ Le worker DOCUMENTS est celui qui porte deja les deux soeurs.
-- ─────────────────────────────────────────────────────────────────────────────
DO $garde$
DECLARE
    src      text;
    ancre    text := $a$'prepare_archived_annonce_detail','prepare_historical_annonce_detail'))$a$;
    remplace text := $b$'prepare_archived_annonce_detail','prepare_historical_annonce_detail','prepare_brouillon_annonce_detail'))$b$;
    combien  int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_claim_next_job';

    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_claim_next_job est introuvable.';
    END IF;
    IF md5(src) <> 'bb456c57fdf566899d5824cf2e0ad3ef' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_console_claim_next_job a change depuis l''audit. Attendue '
            'bb456c57fdf566899d5824cf2e0ad3ef, trouvee %s.', md5(src));
    END IF;
    IF position($c$'prepare_brouillon_annonce_detail'$c$ in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : le type est DEJA dans claim_next_job -- patch deja applique.';
    END IF;

    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans claim_next_job (il en faut 1).', combien);
    END IF;

    EXECUTE replace(src, ancre, remplace);
    RAISE NOTICE 'VERROU 3 pose : le worker DOCUMENTS reclamera ce travail.';
END
$garde$;

-- ─────────────────────────────────────────────────────────────────────────────
-- LES DROITS -- app_console_can_access_dossier : LE 4e INDEX OUBLIE.
--
-- Elle garde la lecture des 3 caches de detail. Elle connait le parc vivant,
-- l'archive et l'historique -- PAS le panier brouillon. Pour un NEGOCIATEUR, la
-- politique rendrait donc 0 ligne, SANS ERREUR : `has_detail_cache` resterait
-- faux et la fiche ne s'ouvrirait jamais. Defaut muet, exactement la forme que
-- le projet traque.
-- ⭐ On ajoute la 4e branche, sur le patron EXACT des trois autres : meme forme,
--   meme filtre `negociateur_email`, meme double cle (numero d'app OU numero
--   Hektor). L'index brouillon porte bien ces deux colonnes (mesure du 20/10).
-- ─────────────────────────────────────────────────────────────────────────────
DO $garde$
DECLARE
    src      text;
    -- L'ancre est la FIN du 3e bloc : son point-virgule. MESUREE le 20/10 : elle
    -- apparait UNE SEULE FOIS et tient SUR UNE SEULE LIGNE (les deux premiers blocs
    -- finissent par une parenthese SANS point-virgule). Lecon 30 du projet.
    ancre    text := '        );';
    bloc     text;
    combien  int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_access_dossier';

    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_can_access_dossier est introuvable.';
    END IF;
    IF md5(src) <> '7267f75aa71993e77d6750f0b031c63b' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_console_can_access_dossier a change depuis l''audit. Attendue '
            '7267f75aa71993e77d6750f0b031c63b, trouvee %s.', md5(src));
    END IF;
    IF position('app_brouillon_annonce_index_current' in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : le panier brouillon est DEJA connu -- patch deja applique.';
    END IF;

    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format(
            'ARRET : l''ancre de fin apparait %s fois dans can_access_dossier (il en faut 1).', combien);
    END IF;

    bloc := $d$        )
        -- ⑦ piece ② (20/10/2026) : LE 4e INDEX. Un brouillon n'est dans aucun des
        -- trois ci-dessus, donc un negociateur se voyait refuser la lecture de son
        -- propre brouillon -- en silence, 0 ligne et aucune erreur.
        or exists (
            select 1
            from public.app_brouillon_annonce_index_current target
            where (
                    (target_app_dossier_id is not null and target.app_brouillon_id = target_app_dossier_id)
                 or (nullif(target_hektor_annonce_id, '') is not null and target.hektor_annonce_id::text = target_hektor_annonce_id)
                )
              and lower(coalesce(target.negociateur_email, '')) = lower(coalesce(current_email, ''))
        );$d$;

    EXECUTE replace(src, ancre, bloc);
    RAISE NOTICE 'DROITS poses : un negociateur voit le cache de SES brouillons.';
END
$garde$;

-- ─────────────────────────────────────────────────────────────────────────────
-- LE CONTROLE, DANS LA MEME TRANSACTION. S'il ne passe pas, tout est annule.
-- ⚠ On exige la PREUVE de chaque pose, jamais l'absence d'erreur.
-- ─────────────────────────────────────────────────────────────────────────────
DO $garde$
DECLARE
    v1 boolean; v2 boolean; v3 boolean; v4 boolean;
    manques text := '';
BEGIN
    SELECT position($a$'prepare_brouillon_annonce_detail'$a$ in replace(pg_get_constraintdef(oid), chr(13), '')) > 0
      INTO v1 FROM pg_constraint WHERE conname = 'app_console_job_job_type_check';
    SELECT position($a$'prepare_brouillon_annonce_detail'$a$ in prosrc) > 0
      INTO v2 FROM pg_proc WHERE proname = 'app_console_can_request_job';
    SELECT position($a$'prepare_brouillon_annonce_detail'$a$ in prosrc) > 0
      INTO v3 FROM pg_proc WHERE proname = 'app_console_claim_next_job';
    SELECT position('app_brouillon_annonce_index_current' in prosrc) > 0
      INTO v4 FROM pg_proc WHERE proname = 'app_console_can_access_dossier';

    IF NOT coalesce(v1, false) THEN manques := manques || ' verrou1(contrainte)'; END IF;
    IF NOT coalesce(v2, false) THEN manques := manques || ' verrou2(can_request)'; END IF;
    IF NOT coalesce(v3, false) THEN manques := manques || ' verrou3(claim_next)'; END IF;
    IF NOT coalesce(v4, false) THEN manques := manques || ' droits(can_access)'; END IF;

    IF manques <> '' THEN
        RAISE EXCEPTION '%', format('ARRET : pose incomplete, il manque :%s -- tout est annule.', manques);
    END IF;
    RAISE NOTICE 'CONTROLE VERT : les 3 verrous ET les droits portent la famille brouillon.';
END
$garde$;

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- APRES AVOIR COLLE CECI :
--   1. pousser le code (worker + front)
--   2. ⏰ redemarrer HektorConsoleWorkerDocuments -- ET SEULEMENT FILE VIDE :
--        0 pending ET 0 running (le 19/10 a 17:10 un redemarrage a tue 14 photos)
--        powershell -Command "Restart-Service HektorConsoleWorkerDocuments; Get-Service HektorConsoleWorker*"
--   3. lancer le temoin : ..._REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════════
