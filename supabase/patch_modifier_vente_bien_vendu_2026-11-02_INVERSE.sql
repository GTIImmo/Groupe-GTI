-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE de patch_modifier_vente_bien_vendu_2026-11-02.sql (4C, 02/11/2026)
-- Remet les trois lignes d'origine (numero_dossier, titre_bien, negociateur_email lus dans
-- app_dossier_current seulement). Rien d'autre n'est touché.
-- GARDE : s'arrête si la fonction en ligne n'est pas celle posée par le patch (empreinte 176ee0df) ;
--         preuve : l'empreinte d'origine 97b1b9d2 est retrouvée, sinon rien n'est gardé.
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

DO $inverse$
DECLARE
    d      text;
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
BEGIN
    d := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    IF md5(d) <> '176ee0df2aa45021777390b08d5763e7' THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction en ligne n''est pas celle du patch 4C (empreinte 176ee0df attendue). Rien n''est change.';
    END IF;
    EXECUTE replace(replace(replace(d, n1, a1), n2, a2), n3, a3);
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), ''))
       <> '97b1b9d28bffb7a9b5d2e6e92eea9bd4' THEN
        RAISE EXCEPTION '%', 'ARRET : l''empreinte d''origine 97b1b9d2 n''est pas retrouvee. Rien n''est garde.';
    END IF;
END
$inverse$;

COMMIT;
