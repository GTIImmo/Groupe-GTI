-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE de patch_vente_prix_de_vente_dabord_2026-11-02.sql (4C-prix, 02/11/2026)
-- Remet `montant = coalesce(amount, sale_price)` dans les deux fonctions. Rien d'autre n'est touché.
-- GARDE : empreintes du patch 11616ec6 / a52966fa avant ; preuve : 446df246 / 176ee0df retrouvées après.
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

DO $inverse$
DECLARE
    f1 text;
    f2 text;
    a1 text := $a$coalesce(v_payload->>'amount', v_payload->>'sale_price','')$a$;
    n1 text := $a$coalesce(/* 4C-prix 02/11 : vente -> prix de vente d'abord */ case when v_kind = 'vente' then nullif(btrim(v_payload->>'sale_price'), '') end, v_payload->>'amount', v_payload->>'sale_price','')$a$;
    a2 text := $a$('montant',            coalesce(v_payload->>'amount', v_payload->>'sale_price')),$a$;
    n2 text := $a$('montant',            coalesce(/* 4C-prix 02/11 */ case when v_kind = 'vente' then nullif(btrim(v_payload->>'sale_price'), '') end, v_payload->>'amount', v_payload->>'sale_price')),$a$;
    a3 text := $a$coalesce(nullif(btrim(coalesce(v_maj->>'amount',$a$;
    n3 text := $a$coalesce(nullif(btrim(coalesce(/* 4C-prix 02/11 : vente -> prix de vente d'abord */ case when a.kind = 'vente' then nullif(btrim(v_maj->>'sale_price'), '') end, v_maj->>'amount',$a$;
    a4 text := $a$('montant',            coalesce(v_payload->>'amount', v_payload->>'sale_price'), a.montant::text),$a$;
    n4 text := $a$('montant',            coalesce(/* 4C-prix 02/11 */ case when a.kind = 'vente' then nullif(btrim(v_payload->>'sale_price'), '') end, v_payload->>'amount', v_payload->>'sale_price'), a.montant::text),$a$;
BEGIN
    f1 := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    f2 := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    IF md5(f1) <> '11616ec6891c5c1caa5f647fafecdfdd' OR md5(f2) <> 'a52966fa2e92b2e37f39efbcc222f5b0' THEN
        RAISE EXCEPTION '%', 'ARRET : les fonctions en ligne ne sont pas celles du patch 4C-prix (empreintes 11616ec6 / a52966fa attendues). Rien n''est change.';
    END IF;
    EXECUTE replace(replace(f1, n1, a1), n2, a2);
    EXECUTE replace(replace(f2, n3, a3), n4, a4);
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> '446df24693d75c0bf1917d0b94847c9a'
       OR md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '176ee0df2aa45021777390b08d5763e7' THEN
        RAISE EXCEPTION '%', 'ARRET : les empreintes d''origine 446df246 / 176ee0df ne sont pas retrouvees. Rien n''est garde.';
    END IF;
END
$inverse$;

COMMIT;
