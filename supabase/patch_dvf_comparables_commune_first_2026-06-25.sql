-- =====================================================================
-- DVF — comparables « commune d'abord, secteur en repli » (2026-06-25)
--
-- Avant : tout dans le rayon (12 km) sans distinction -> un bien d'une petite
-- commune était noyé sous les ventes de la grande ville voisine.
-- Maintenant : on privilégie la COMMUNE du bien (code postal + nom unaccenté) ;
-- on n'élargit au secteur (rayon, communes limitrophes incluses) QUE si l'échantillon
-- communal est trop maigre (< p_min_local, défaut 10). La RPC renvoie `scope`
-- ('commune' | 'secteur') + `n_local` pour transparence (éditeur + PDF).
--
-- NB : 100 % CTE (pas de table temporaire) -> robuste si la fonction est appelée
-- plusieurs fois dans la même transaction. search_path = public, extensions
-- (extensions = schéma où vit unaccent sur Supabase ; SANS guillemets, sinon
-- Postgres cherche un schéma unique nommé "public, extensions").
-- =====================================================================

create extension if not exists unaccent with schema extensions;

-- signature élargie -> on supprime l'ancienne (8 args) pour éviter toute ambiguïté
drop function if exists public.app_dvf_comparables(
  double precision, double precision, text, numeric, numeric, integer, numeric, integer);

create or replace function public.app_dvf_comparables(
  p_lat         double precision,
  p_lon         double precision,
  p_type        text    default 'Maison',
  p_surface     numeric default null,
  p_radius_km   numeric default 12,
  p_months      integer default 24,
  p_tol         numeric default 0.30,
  p_limit       integer default 5,
  p_code_postal text    default null,
  p_commune     text    default null,
  p_min_local   integer default 10)
 returns jsonb
 language plpgsql
 security definer
 set search_path to public, extensions
as $function$
declare
  v_dlat   double precision := p_radius_km / 111.0;
  v_dlon   double precision := p_radius_km / (111.0 * greatest(cos(radians(p_lat)), 0.01));
  v_cutoff date := (current_date - make_interval(months => p_months))::date;
  v_smin   numeric := case when p_surface is not null then p_surface * (1 - p_tol) end;
  v_smax   numeric := case when p_surface is not null then p_surface * (1 + p_tol) end;
  v_ncp    text := nullif(trim(coalesce(p_code_postal, '')), '');
  v_ncom   text := nullif(trim(coalesce(p_commune, '')), '');
  v_n_local integer;
  v_scope  text;
  v_result jsonb;
begin
  if p_lat is null or p_lon is null or p_lat = 0 or p_lon = 0 then
    return jsonb_build_object('ok', false, 'reason', 'missing_geo', 'count', 0, 'comparables', '[]'::jsonb);
  end if;

  -- 1) échantillon communal disponible (24 mois, surface ±tol) -> décide le scope
  select count(*) filter (where v.prix_m2 is not null) into v_n_local
  from app_dvf_vente v
  where v.type_local = p_type
    and v.lat between p_lat - v_dlat and p_lat + v_dlat
    and v.lon between p_lon - v_dlon and p_lon + v_dlon
    and ( (v_ncp is not null and v.code_postal = v_ncp)
          or (v_ncom is not null and extensions.unaccent(lower(v.commune)) = extensions.unaccent(lower(v_ncom))) )
    and v.date_mutation >= v_cutoff
    and (v_smin is null or v.surface between v_smin and v_smax)
    and 6371.0 * 2 * asin(sqrt(
          power(sin(radians((v.lat - p_lat) / 2)), 2)
          + cos(radians(p_lat)) * cos(radians(v.lat)) * power(sin(radians((v.lon - p_lon) / 2)), 2))) <= p_radius_km;

  v_scope := case when (v_ncp is not null or v_ncom is not null) and coalesce(v_n_local, 0) >= p_min_local
                  then 'commune' else 'secteur' end;

  -- 2) candidats (type + boîte englobante) + distance + flag commune, sélection selon le scope
  with cand as (
    select v.id, v.date_mutation, v.type_local, v.valeur, v.surface, v.pieces, v.terrain,
           v.commune, v.code_postal, v.prix_m2,
           6371.0 * 2 * asin(sqrt(
             power(sin(radians((v.lat - p_lat) / 2)), 2)
             + cos(radians(p_lat)) * cos(radians(v.lat)) * power(sin(radians((v.lon - p_lon) / 2)), 2))) as dist,
           ( (v_ncp is not null and v.code_postal = v_ncp)
             or (v_ncom is not null and extensions.unaccent(lower(v.commune)) = extensions.unaccent(lower(v_ncom))) ) as is_local
    from app_dvf_vente v
    where v.type_local = p_type
      and v.lat between p_lat - v_dlat and p_lat + v_dlat
      and v.lon between p_lon - v_dlon and p_lon + v_dlon
  ),
  sel as (
    select * from cand
    where dist <= p_radius_km and date_mutation >= v_cutoff
      and (v_smin is null or surface between v_smin and v_smax)
      and (v_scope = 'secteur' or is_local)
  ),
  evo_base as (
    select * from cand
    where dist <= p_radius_km and prix_m2 is not null
      and (v_scope = 'secteur' or is_local)
  ),
  agg as (
    select count(*) filter (where prix_m2 is not null)::int as n,
           round(avg(prix_m2)) as avg_pm,
           percentile_cont(0.5) within group (order by prix_m2) as med_pm
    from sel
  ),
  evo as (
    select extract(year from date_mutation)::int as annee,
           round(avg(prix_m2)) as prix_m2, count(*)::int as n
    from evo_base group by 1 order by 1
  ),
  comps as (
    select * from sel
    order by case when p_surface is not null then abs(surface - p_surface) else 0 end,
             date_mutation desc
    limit greatest(p_limit, 1)
  )
  select jsonb_build_object(
    'ok', true,
    'scope', v_scope,
    'n_local', v_n_local,
    'commune', coalesce(v_ncom, (select mode() within group (order by commune) from sel)),
    'count', coalesce((select n from agg), 0),
    'avg_prix_m2', (select avg_pm from agg),
    'median_prix_m2', (select round(med_pm) from agg),
    'radius_km', p_radius_km,
    'months', p_months,
    'type', p_type,
    'data_through', (select max(date_mutation) from sel),
    'evolution', coalesce((
      select jsonb_agg(jsonb_build_object('annee', annee::text, 'prix_m2', prix_m2, 'n', n) order by annee)
      from evo), '[]'::jsonb),
    'comparables', coalesce((
      select jsonb_agg(jsonb_build_object(
        'commune', commune, 'type', type_local, 'surface', round(surface)::int,
        'pieces', pieces::text,
        'terrain', case when terrain is not null then round(terrain)::int end,
        'valeur', round(valeur)::int, 'prix_m2', prix_m2,
        'date', date_mutation::text, 'distance_km', round(dist::numeric, 1)))
      from comps), '[]'::jsonb)
  ) into v_result;

  return v_result;
end
$function$;

grant execute on function public.app_dvf_comparables(
  double precision, double precision, text, numeric, numeric, integer, numeric, integer, text, text, integer
) to authenticated, service_role;
