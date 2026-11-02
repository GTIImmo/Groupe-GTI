-- ═══════════════════════════════════════════════════════════════════════════
-- 4C (registre des transactions) : MODIFIER UNE TRANSACTION D'UN BIEN VENDU        02/11/2026
-- Audit : notice/AUDIT_GESTES_REGISTRE_TRANSACTIONS_2026-10-30.md § 11, défaut (a) ;
--         notice/AUDIT_MODALE_STATUT_REGLES_2026-10-30.md § 3.6 et § 4. « Go » de Frédéric du 02/11.
--
-- LE DÉFAUT. app_modifier_affaire_optimistic relit le bien dans app_dossier_current et ÉCRASE dans la
-- charge numero_dossier, titre_bien et negociateur_email. Un bien vendu n'y est plus (0 vente 2026 sur
-- 287) : les trois partent à NULL, même si l'écran les avait envoyés. Le worker perd alors le repère de
-- ses messages et l'e-mail du négociateur, son repli pour le contexte (console_job_worker.js ~2550).
--
-- LE REMÈDE : app_dossier_current d'abord (rien ne change pour un bien en annonce), sinon l'index
-- historique (app_historical_id = app_dossier_id, 257/257 mesuré le 30/10), sinon ce que l'écran a envoyé.
-- Seules ces trois lignes changent. Pas d'interrupteur : pour un bien en annonce la valeur est la même
-- qu'avant dès que la fiche du bien porte la valeur ; une valeur vide n'écrase plus celle de l'écran.
--
-- GARDE : s'arrête si la fonction en ligne n'est pas celle mesurée le 02/11 (empreinte 97b1b9d2, retours
--         chariot retirés) ou si une ancre n'est pas trouvée UNE fois exactement.
-- Retour arrière : patch_modifier_vente_bien_vendu_2026-11-02_INVERSE.sql
-- Contrôle       : patch_modifier_vente_bien_vendu_2026-11-02_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

DO $pose$
DECLARE
    d      text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    a1     text := '      ''numero_dossier'',        d.numero_dossier,';
    a2     text := '      ''titre_bien'',            d.titre_bien,';
    a3     text := '      ''negociateur_email'',     d.negociateur_email);';
    n1     text := replace($n1$      -- 4C (02/11/2026) : un bien VENDU n'est plus dans app_dossier_current -> l'index historique,
      -- puis ce que l'ecran a envoye. Voir supabase/patch_modifier_vente_bien_vendu_2026-11-02.sql.
      'numero_dossier',        coalesce(d.numero_dossier,
                                 (select h.numero_dossier from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'numero_dossier', '')), '')),$n1$, chr(13), '');
    n2     text := replace($n2$      'titre_bien',            coalesce(d.titre_bien,
                                 (select h.titre_bien from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'titre_bien', '')), '')),$n2$, chr(13), '');
    n3     text := replace($n3$      'negociateur_email',     coalesce(d.negociateur_email,
                                 (select h.negociateur_email from public.app_historical_annonce_index_current h
                                   where h.app_historical_id = a.app_dossier_id limit 1),
                                 nullif(btrim(coalesce(v_payload->>'negociateur_email', '')), '')));$n3$, chr(13), '');
    n      integer;
BEGIN
    IF md5(d) <> '97b1b9d28bffb7a9b5d2e6e92eea9bd4' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic a change depuis l''audit du 02/11 (empreinte 97b1b9d2 attendue). Rien n''est change.';
    END IF;
    n := (length(d) - length(replace(d, a1, ''))) / length(a1);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre numero_dossier trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;
    n := (length(d) - length(replace(d, a2, ''))) / length(a2);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre titre_bien trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;
    n := (length(d) - length(replace(d, a3, ''))) / length(a3);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre negociateur_email trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;

    EXECUTE replace(replace(replace(d, a1, n1), a2, n2), a3, n3);
END
$pose$;

-- LA PREUVE, DANS LA MÊME TRANSACTION : sinon rien n'est gardé.
DO $preuve$
DECLARE d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
BEGIN
    IF position('4C (02/11/2026)' in d) = 0 THEN
        RAISE EXCEPTION 'ARRET : le correctif 4C n''est pas dans la fonction. Rien n''est garde.';
    END IF;
    IF (length(d) - length(replace(d, 'app_historical_annonce_index_current', ''))) / length('app_historical_annonce_index_current') <> 3 THEN
        RAISE EXCEPTION 'ARRET : l''index historique devrait etre lu 3 fois. Rien n''est garde.';
    END IF;
    IF position('''numero_dossier'',        d.numero_dossier,' in d) > 0 THEN
        RAISE EXCEPTION 'ARRET : l''ancienne ligne numero_dossier est encore la. Rien n''est garde.';
    END IF;
    RAISE NOTICE 'empreinte apres pose : %', md5(d);
END
$preuve$;

COMMIT;
