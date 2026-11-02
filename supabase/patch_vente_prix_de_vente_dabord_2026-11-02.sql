-- ═══════════════════════════════════════════════════════════════════════════
-- 4C-prix : POUR UNE VENTE, LE MONTANT DU REGISTRE EST LE PRIX DE VENTE             02/11/2026
-- Audit : notice/AUDIT_GESTES_REGISTRE_TRANSACTIONS_2026-10-30.md § 11 ter et 11 quater. « Go, ligne + base »
-- de Frédéric du 02/11.
--
-- LE DÉFAUT. Pour une vente, la fenêtre de statut cache la case « Montant / prix public » (14/09) mais la
-- charge emporte quand même `amount` = le prix de l'ANNONCE ; le prix tapé est `sale_price`. Les deux
-- fonctions rangeaient `montant = coalesce(amount, sale_price)` : c'est le prix de l'annonce qui entrait au
-- registre et au carnet. Essai réel du 02/11, vente 23358 : Hektor 115 001 (juste), registre 128 787 (faux).
--
-- LE REMÈDE : pour une VENTE seulement, `sale_price` d'abord, `amount` en repli. Offre et compromis :
-- l'expression rend exactement la même chose qu'avant (le `case` vaut NULL hors vente). C'est aussi ce que
-- fait le worker en envoyant à Hektor (prixDeVente = sale_price, sinon amount).
-- Le front envoie désormais amount = prix de vente pour une vente ; ce patch protège en plus un écran resté
-- en cache.
--
-- GARDES : chaque fonction doit avoir l'empreinte mesurée le 02/11 (retours chariot retirés) :
--   app_change_annonce_status_optimistic  446df246   app_modifier_affaire_optimistic  176ee0df
-- et chaque ancre doit être trouvée UNE fois exactement. Sinon rien n'est changé.
-- Retour arrière : patch_vente_prix_de_vente_dabord_2026-11-02_INVERSE.sql
-- Contrôle       : patch_vente_prix_de_vente_dabord_2026-11-02_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

DO $pose$
DECLARE
    f1 text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    f2 text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    a1 text := $a$coalesce(v_payload->>'amount', v_payload->>'sale_price','')$a$;
    n1 text := $a$coalesce(/* 4C-prix 02/11 : vente -> prix de vente d'abord */ case when v_kind = 'vente' then nullif(btrim(v_payload->>'sale_price'), '') end, v_payload->>'amount', v_payload->>'sale_price','')$a$;
    a2 text := $a$('montant',            coalesce(v_payload->>'amount', v_payload->>'sale_price')),$a$;
    n2 text := $a$('montant',            coalesce(/* 4C-prix 02/11 */ case when v_kind = 'vente' then nullif(btrim(v_payload->>'sale_price'), '') end, v_payload->>'amount', v_payload->>'sale_price')),$a$;
    a3 text := $a$coalesce(nullif(btrim(coalesce(v_maj->>'amount',$a$;
    n3 text := $a$coalesce(nullif(btrim(coalesce(/* 4C-prix 02/11 : vente -> prix de vente d'abord */ case when a.kind = 'vente' then nullif(btrim(v_maj->>'sale_price'), '') end, v_maj->>'amount',$a$;
    a4 text := $a$('montant',            coalesce(v_payload->>'amount', v_payload->>'sale_price'), a.montant::text),$a$;
    n4 text := $a$('montant',            coalesce(/* 4C-prix 02/11 */ case when a.kind = 'vente' then nullif(btrim(v_payload->>'sale_price'), '') end, v_payload->>'amount', v_payload->>'sale_price'), a.montant::text),$a$;
    n  integer;
BEGIN
    IF md5(f1) <> '446df24693d75c0bf1917d0b94847c9a' THEN
        RAISE EXCEPTION '%', 'ARRET : app_change_annonce_status_optimistic a change (empreinte 446df246 attendue). Rien n''est change.';
    END IF;
    IF md5(f2) <> '176ee0df2aa45021777390b08d5763e7' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic a change (empreinte 176ee0df attendue). Rien n''est change.';
    END IF;
    n := (length(f1) - length(replace(f1, a1, ''))) / length(a1);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre 1 trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;
    n := (length(f1) - length(replace(f1, a2, ''))) / length(a2);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre 2 trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;
    n := (length(f2) - length(replace(f2, a3, ''))) / length(a3);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre 3 trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;
    n := (length(f2) - length(replace(f2, a4, ''))) / length(a4);
    IF n <> 1 THEN RAISE EXCEPTION 'ARRET : ancre 4 trouvee % fois au lieu de 1. Rien n''est change.', n; END IF;

    EXECUTE replace(replace(f1, a1, n1), a2, n2);
    EXECUTE replace(replace(f2, a3, n3), a4, n4);
END
$pose$;

-- LA PREUVE, DANS LA MÊME TRANSACTION : sinon rien n'est gardé.
DO $preuve$
DECLARE
    f1 text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    f2 text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
BEGIN
    IF (length(f1) - length(replace(f1, '4C-prix 02/11', ''))) / length('4C-prix 02/11') <> 2
       OR (length(f2) - length(replace(f2, '4C-prix 02/11', ''))) / length('4C-prix 02/11') <> 2 THEN
        RAISE EXCEPTION 'ARRET : les deux reperes 4C-prix ne sont pas dans chaque fonction. Rien n''est garde.';
    END IF;
    RAISE NOTICE 'empreintes apres pose : % / %', md5(f1), md5(f2);
END
$preuve$;

COMMIT;
