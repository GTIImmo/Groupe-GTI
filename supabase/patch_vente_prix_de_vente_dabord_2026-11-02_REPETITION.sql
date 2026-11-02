-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION de patch_vente_prix_de_vente_dabord_2026-11-02.sql (4C-prix, 02/11/2026)
-- Joue le patch PUIS son retour arrière dans UNE transaction ANNULÉE : rien n'est gardé.
-- Droits de Frédéric. Chaque appel est isolé dans une sous-transaction qui s'annule aussitôt (ANNULE_ESSAI) :
-- une création de vente du premier passage ne doit pas verrouiller le compromis témoin du second.
-- ⚠ Jamais une fonction qui écrit dans un WHERE (02/11 : rejouée pour chaque ligne).
-- Attendu (jouée le 02/11 avant pose) :
--   creation vente (bien 1346424, amount 128000, prix de vente 101000) : 1 avant 128000 -> 2 apres 101000 -> 3 retour 128000
--   modif 1001395 (vente, amount 128787, prix de vente 115000)      : 128787 -> 115000 -> 128787
--   modif 30666 (compromis, témoin)                                  : 104000 -> 104000 -> 104000
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;
set local statement_timeout = '60s';
select set_config('request.jwt.claims', json_build_object('sub',(select id from auth.users where email='frederic.gerphagnon@gti-immobilier.fr'),'role','authenticated')::text, true);
create temp table t_res(moment text, cas text, montant text, carnet text, info text) on commit drop;
create or replace function pg_temp.modif(m text, aff bigint, charge jsonb) returns void language plpgsql as $f$
declare r jsonb; v1 text; v2 text;
begin
  begin
    r := public.app_modifier_affaire_optimistic(aff, charge);
    v1 := (select montant::text from app_affaire_ledger where app_affaire_id=aff);
    v2 := (select valeur_app from app_affaire_champ_app where app_affaire_id=aff and champ='montant');
    raise exception 'ANNULE_ESSAI';
  exception when others then
    insert into t_res values (m, 'modif '||aff, v1, v2, case when sqlerrm='ANNULE_ESSAI' then 'ok' else 'REFUS: '||left(sqlerrm,100) end);
  end;
end $f$;
create or replace function pg_temp.creer(m text, charge jsonb) returns void language plpgsql as $f$
declare r jsonb; id bigint; v1 text; v2 text;
begin
  begin
    r := public.app_change_annonce_status_optimistic(1346424, 'sold', charge);
    id := nullif(r->>'app_affaire_id','')::bigint;
    v1 := (select montant::text from app_affaire_ledger where app_affaire_id=id);
    v2 := (select valeur_app from app_affaire_champ_app where app_affaire_id=id and champ='montant');
    raise exception 'ANNULE_ESSAI';
  exception when others then
    insert into t_res values (m, 'creation vente', v1, v2, case when sqlerrm='ANNULE_ESSAI' then 'ok' else 'REFUS: '||left(sqlerrm,100) end);
  end;
end $f$;
create or replace function pg_temp.tour(m text) returns void language plpgsql as $f$
begin
  perform pg_temp.modif(m, 1001395, '{"amount":"128787","sale_price":"115000","champs_touches":["sale_price"]}'::jsonb);
  perform pg_temp.modif(m, 30666, '{"amount":"104000","sale_price":"99999","champs_touches":["amount","sale_price"]}'::jsonb);
  perform pg_temp.creer(m, '{"amount":"128000","sale_price":"101000","transaction_date":"2026-11-02","buyer_contact_id":"12725"}'::jsonb);
end $f$;

select pg_temp.tour('1 avant');

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

select pg_temp.tour('2 apres');

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

select pg_temp.tour('3 retour');

select * from t_res order by cas, moment;
ROLLBACK;
