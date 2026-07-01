-- =====================================================================
-- app_dvf_comparables v3 — affinage MAISONS par terrain similaire — 2026-07-01.
--
-- Ajoute un critère « surface de terrain comparable » pour les MAISONS, en 2 niveaux
-- (dégradation douce) pour ne pas vider l'échantillon en secteur peu dense :
--   - p_terrain fourni + type=Maison -> on tente de filtrer les ventes dont le terrain
--     est dans la bande [p_terrain / p_terrain_tol ; p_terrain * p_terrain_tol]
--     (défaut tol=2.0 => 0,5× à 2×) ;
--   - si cette bande donne < p_min_local ventes dans le rayon max -> on l'IGNORE
--     (comportement historique : type + surface + secteur uniquement).
-- Le résultat expose `terrain_applied` (true/false) pour l'affichage.
-- Appartements : p_terrain ignoré (terrain non pertinent). Rétro-compatible
-- (p_terrain a une valeur par défaut => l'ancien front continue de fonctionner).
-- =====================================================================

CREATE OR REPLACE FUNCTION public.app_dvf_comparables(
  p_lat double precision, p_lon double precision,
  p_type text DEFAULT 'Maison'::text, p_surface numeric DEFAULT NULL::numeric,
  p_radius_km numeric DEFAULT 12, p_months integer DEFAULT 24,
  p_tol numeric DEFAULT 0.25, p_limit integer DEFAULT 6,
  p_code_postal text DEFAULT NULL::text, p_commune text DEFAULT NULL::text,
  p_min_local integer DEFAULT 5, p_max_comps integer DEFAULT 30,
  p_terrain numeric DEFAULT NULL::numeric, p_terrain_tol numeric DEFAULT 2.0)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'extensions'
AS $function$
declare
  v_ref    geography := st_setsrid(st_makepoint(p_lon, p_lat), 4326)::geography;
  v_cutoff date := (current_date - make_interval(months => p_months))::date;
  v_smin   numeric := case when p_surface is not null then p_surface * (1 - p_tol) end;
  v_smax   numeric := case when p_surface is not null then p_surface * (1 + p_tol) end;
  v_cap    integer := greatest(2000, round(p_radius_km * 1000)::int);
  v_rings  integer[] := array[2000, 5000, 10000];
  v_ring   integer;
  v_radius integer := null;
  v_n      integer;
  v_result jsonb;
  -- Affinage terrain (maisons) : bande + drapeau d'application.
  v_use_terrain boolean := (lower(p_type) = 'maison' and p_terrain is not null and p_terrain > 0 and coalesce(p_terrain_tol,0) > 1);
  v_tmin   numeric := case when v_use_terrain then p_terrain / p_terrain_tol end;
  v_tmax   numeric := case when v_use_terrain then p_terrain * p_terrain_tol end;
  v_terrain_on boolean := false;
begin
  if p_lat is null or p_lon is null or p_lat = 0 or p_lon = 0 then
    return jsonb_build_object('ok', false, 'reason', 'missing_geo', 'count', 0, 'fiable', false, 'comparables', '[]'::jsonb);
  end if;

  -- Niveau 1 : le filtre terrain donne-t-il assez de ventes dans le rayon max ? Sinon on l'ignore.
  if v_use_terrain then
    select count(*) into v_n from app_dvf_vente v
    where v.type_local = p_type and v.date_mutation >= v_cutoff
      and (v_smin is null or v.surface between v_smin and v_smax)
      and v.terrain between v_tmin and v_tmax
      and st_dwithin(v.geom, v_ref, v_cap);
    if v_n >= p_min_local then v_terrain_on := true; end if;
  end if;

  foreach v_ring in array v_rings loop
    if v_ring > v_cap then continue; end if;
    select count(*) into v_n from app_dvf_vente v
    where v.type_local = p_type and v.date_mutation >= v_cutoff
      and (v_smin is null or v.surface between v_smin and v_smax)
      and (not v_terrain_on or v.terrain between v_tmin and v_tmax)
      and st_dwithin(v.geom, v_ref, v_ring);
    if v_n >= p_min_local then v_radius := v_ring; exit; end if;
  end loop;
  if v_radius is null then v_radius := least(10000, v_cap); end if;

  with base as (
    select v.*, st_distance(v.geom, v_ref) as dist
    from app_dvf_vente v
    where v.type_local = p_type and v.date_mutation >= v_cutoff
      and (v_smin is null or v.surface between v_smin and v_smax)
      and (not v_terrain_on or v.terrain between v_tmin and v_tmax)
      and st_dwithin(v.geom, v_ref, v_radius)
  ),
  bnd as (
    select count(*) n,
           percentile_cont(0.05) within group (order by prix_m2) p05,
           percentile_cont(0.95) within group (order by prix_m2) p95
    from base where prix_m2 is not null
  ),
  trimmed as (
    select b.* from base b, bnd
    where b.prix_m2 is not null
      and (bnd.n < 20 or b.prix_m2 between bnd.p05 and bnd.p95)
  ),
  sel as (
    select * from trimmed order by dist limit greatest(p_max_comps, 1)
  ),
  stats as (
    select count(*)::int n,
           percentile_cont(0.50) within group (order by prix_m2) med,
           percentile_cont(0.25) within group (order by prix_m2) p25,
           percentile_cont(0.75) within group (order by prix_m2) p75,
           round(avg(prix_m2)) avg
    from sel
  ),
  evo_base as (
    select v.date_mutation, v.prix_m2
    from app_dvf_vente v
    where v.type_local = p_type and st_dwithin(v.geom, v_ref, v_radius) and v.prix_m2 is not null
  ),
  evo as (
    select extract(year from date_mutation)::int annee, round(avg(prix_m2)) prix_m2, count(*)::int n
    from evo_base group by 1 order by 1
  )
  select jsonb_build_object(
    'ok', true,
    'type', p_type,
    'months', p_months,
    'surface', p_surface,
    'terrain_applied', v_terrain_on,
    'radius_used_m', v_radius,
    'radius_km', round(v_radius / 1000.0, 1),
    'count', s.n,
    'count_clean', s.n,
    'fiable', (s.n >= p_min_local),
    'median_prix_m2', round(s.med),
    'avg_prix_m2', s.avg,
    'p25_prix_m2', round(s.p25),
    'p75_prix_m2', round(s.p75),
    'prix_estime',      case when p_surface is not null and s.med is not null then round(s.med * p_surface) end,
    'fourchette_basse', case when p_surface is not null and s.p25 is not null then round(s.p25 * p_surface) end,
    'fourchette_haute', case when p_surface is not null and s.p75 is not null then round(s.p75 * p_surface) end,
    'commune', coalesce(nullif(trim(coalesce(p_commune, '')), ''), (select mode() within group (order by commune) from sel)),
    'scope', case when v_radius <= 2000 then 'commune' else 'secteur' end,
    'n_local', s.n,
    'data_through', (select max(date_mutation) from sel),
    'evolution', coalesce((
      select jsonb_agg(jsonb_build_object('annee', annee::text, 'prix_m2', prix_m2, 'n', n) order by annee) from evo
    ), '[]'::jsonb),
    'comparables', coalesce((
      select jsonb_agg(jsonb_build_object(
        'commune', commune, 'type', type_local, 'surface', round(surface)::int,
        'pieces', pieces::text,
        'terrain', case when terrain is not null then round(terrain)::int end,
        'valeur', round(valeur)::int, 'prix_m2', prix_m2,
        'date', date_mutation::text, 'distance_km', round((dist / 1000.0)::numeric, 1))
        order by dist)
      from (select * from sel order by dist limit greatest(p_limit, 1)) c
    ), '[]'::jsonb)
  ) into v_result
  from stats s;

  return v_result;
end
$function$;
