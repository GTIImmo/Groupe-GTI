-- ═══════════════════════════════════════════════════════════════════════════
-- PILOTAGE (écran admin), ONGLET STOCK : LE C.A POTENTIEL DES BIENS EN VENTE                02/11/2026
-- Décisions de Frédéric (02/11) : écran « Pilotage » dédié, ADMINS SEULS, honoraires HT par défaut ;
--   « il faut surtout mettre en avant le montant de C.A potentiel, donc les honoraires et non le prix ».
-- Audit : notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md § 11.
--
-- POURQUOI UNE FONCTION : les honoraires d'un bien en vente n'ont pas de colonne. Ils sont dans
--   app_dossier_detail_current.detail_payload_json (TEXTE, ~20 ko par bien), clé `honoraires_json`,
--   elle-même un texte JSON : [{"id": "85989", "taux": "6500", "charge": "vendeur"}].
--   `taux` est un MONTANT en euros (919 entrées mesurées, toutes entre 500 et 125 000 €).
--   Lire ces 700 textes depuis l'écran ferait descendre ~31 Mo : on extrait en base.
-- ⚠ Hektor y garde des COPIES identiques (2, 3, 5 ou 6 entrées) : par bien ET par charge, on prend
--   l'entrée au plus grand `id`, puis on additionne les charges (vendeur + acheteur).
-- ⚠ Pas de jsonb sur tout le texte (5,7 s) ni d'expression régulière (5 s) : on découpe le morceau
--   par sa position (2,8 s mesurées pour les 699 biens).
--
-- CE QUE FAIT CE PATCH (additif, LECTURE SEULE, rien n'est modifié ni retiré) :
--   app_pilotage_stock() : une ligne par bien « Actif », « Sous offre » ou « Sous compromis » de
--   app_dossier_current, avec ses honoraires. ADMINS SEULS : pour tout autre compte (et sans compte),
--   la fonction rend ZÉRO ligne.
-- RETOUR ARRIÈRE : patch_pilotage_stock_2026-11-02_INVERSE.sql (l'onglet Stock affiche alors « non lu »).
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

DO $garde$
BEGIN
    IF to_regprocedure('public.app_pilotage_stock()') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : app_pilotage_stock() existe deja -- quelqu''un est passe avant. Rien n''est fait.';
    END IF;
    IF to_regprocedure('public.is_app_admin()') IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : is_app_admin() est introuvable. Rien n''est fait.';
    END IF;
END
$garde$;

CREATE FUNCTION public.app_pilotage_stock()
RETURNS TABLE (
    app_dossier_id                bigint,
    hektor_annonce_id             bigint,
    statut_annonce                text,
    agence_nom                    text,
    commercial_nom                text,
    negociateur_email             text,
    prix                          numeric,
    mandat_type                   text,
    mandat_date_debut             text,
    mandat_date_fin               text,
    diffusable                    text,
    nb_portails_actifs            integer,
    price_change_last_old_value   numeric,
    price_change_last_new_value   numeric,
    honoraires                    numeric,
    honoraires_charge_acquereur   boolean
)
LANGUAGE sql
STABLE SECURITY DEFINER
SET search_path TO 'public'
AS $fn$
    -- Pilotage, onglet Stock, 02/11/2026. Voir supabase/patch_pilotage_stock_2026-11-02.sql
    with adm as (
        select public.is_app_admin() as ok
    ), b as (
        select d.*,
               substr(dt.detail_payload_json, nullif(strpos(dt.detail_payload_json, '"honoraires_json":"['), 0) + 18, 1500) as p
          from public.app_dossier_current d
          join adm on adm.ok
          left join public.app_dossier_detail_current dt on dt.app_dossier_id = d.app_dossier_id
         where d.statut_annonce in ('Actif', 'Sous offre', 'Sous compromis')
    ), j as (
        select b.app_dossier_id, (substr(b.p, 1, strpos(b.p, ']"') + 1)::jsonb #>> '{}')::jsonb as hj
          from b
         where b.p is not null and strpos(b.p, ']"') > 0
    ), e as (
        select j.app_dossier_id, lower(x->>'charge') as charge,
               case when x->>'id' ~ '^\d+$' then (x->>'id')::bigint end as id,
               nullif(regexp_replace(coalesce(x->>'taux', ''), '[^0-9.]', '', 'g'), '')::numeric as t
          from j, jsonb_array_elements(case when jsonb_typeof(j.hj) = 'array' then j.hj else '[]'::jsonb end) x
    ), der as (
        select distinct on (e.app_dossier_id, e.charge) e.app_dossier_id, e.charge, e.t
          from e
         where e.t > 0
         order by e.app_dossier_id, e.charge, e.id desc nulls last
    ), h as (
        select der.app_dossier_id, sum(der.t) as honoraires, bool_or(der.charge = 'acheteur') as acq
          from der
         group by der.app_dossier_id
    )
    select b.app_dossier_id, b.hektor_annonce_id, b.statut_annonce, b.agence_nom, b.commercial_nom,
           b.negociateur_email, b.prix, b.mandat_type, b.mandat_date_debut, b.mandat_date_fin, b.diffusable,
           b.nb_portails_actifs, b.price_change_last_old_value, b.price_change_last_new_value,
           h.honoraires, coalesce(h.acq, false)
      from b
      left join h on h.app_dossier_id = b.app_dossier_id;
$fn$;

REVOKE ALL ON FUNCTION public.app_pilotage_stock() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_pilotage_stock() TO authenticated, service_role;

-- LA PREUVE, DANS LA MÊME TRANSACTION : sinon rien n'est gardé.
DO $preuve$
BEGIN
    -- sans utilisateur (postgres), la fonction rend 0 ligne : la règle « admins seuls » tient
    IF (SELECT count(*) FROM public.app_pilotage_stock()) <> 0 THEN
        RAISE EXCEPTION '%', 'ARRET : sans utilisateur, app_pilotage_stock() rend des lignes. Rien n''est garde.';
    END IF;
    IF has_function_privilege('anon', 'public.app_pilotage_stock()', 'EXECUTE') THEN
        RAISE EXCEPTION '%', 'ARRET : la cle publique peut appeler app_pilotage_stock(). Rien n''est garde.';
    END IF;
END
$preuve$;

COMMIT;
