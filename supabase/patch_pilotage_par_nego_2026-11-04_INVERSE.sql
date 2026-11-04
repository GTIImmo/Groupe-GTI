-- Retour arrière de patch_pilotage_par_nego_2026-11-04.sql (04/11/2026). Lecture seule, rien d'autre n'avait été touché.
-- 1. retire les nouvelles versions ; 2. remet app_pilotage_stock() du 02/11 ; 3. puis COLLER
--    patch_pilotage_limites_2026-11-03.sql : il recrée app_pilotage_acquereurs(integer, text) et remet affaires_plus du 03/11.
drop function if exists public.app_pilotage_acquereurs(integer, text, text[], text[]);
drop function if exists public.app_pilotage_stock();

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

revoke all on function public.app_pilotage_stock() from public, anon;
grant execute on function public.app_pilotage_stock() to authenticated, service_role;
select count(*) as nouvelles_restantes from pg_proc where proname = 'app_pilotage_acquereurs' and pronargs = 4;
