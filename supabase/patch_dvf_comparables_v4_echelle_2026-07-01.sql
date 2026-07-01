-- =====================================================================
-- app_dvf_comparables v4 — 2026-07-01 (déjà appliqué en prod).
--
-- Règle d'élargissement « temps avant distance » demandée :
--   - rayons fins 1 / 2 / 4 / 8 km (plafond p_radius_km, défaut 12) ;
--   - min p_min_local = 10 comparables pour valider (sinon on élargit),
--     et on prend TOUS les comparables similaires du périmètre retenu (plafond p_max_comps = 30) ;
--   - surface ±20 % (p_tol) ; fenêtre 24 -> 48 mois (p_months -> p_months_max) ;
--   - MAISONS : terrain de taille comparable (bande p_terrain / p_terrain_tol .. * p_terrain_tol,
--     défaut facteur 2 => 0,5×–2×) MAIS uniquement en LOCAL (<= 2 km), abandonné avant de s'éloigner
--     (évite la dérive vers le rural bon marché : cf. échec de la v3 qui filtrait le terrain à 10 km).
--
-- Échelle (maison + terrain), on s'arrête au 1er palier atteignant p_min_local :
--   1) 1km/24m/+terrain  2) 1km/48m/+terrain  3) 2km/24m/+terrain  4) 2km/48m/+terrain
--   5) 2km/48m/-terrain  6) 4km/48m           7) 8km/48m           8) cap/48m
-- Appartement (ou maison sans terrain) : terrain jamais appliqué => paliers équivalents.
--
-- IMPORTANT : signature à 15 args. Supprimer toute ancienne surcharge (12 args) après application
-- (drop function ... 12 args) pour éviter l'ambiguïté PostgREST.
-- =====================================================================

CREATE OR REPLACE FUNCTION public.app_dvf_comparables(
  p_lat double precision, p_lon double precision,
  p_type text DEFAULT 'Maison'::text, p_surface numeric DEFAULT NULL::numeric,
  p_radius_km numeric DEFAULT 12, p_months integer DEFAULT 24,
  p_tol numeric DEFAULT 0.20, p_limit integer DEFAULT 6,
  p_code_postal text DEFAULT NULL::text, p_commune text DEFAULT NULL::text,
  p_min_local integer DEFAULT 10, p_max_comps integer DEFAULT 30,
  p_terrain numeric DEFAULT NULL::numeric, p_terrain_tol numeric DEFAULT 2.0,
  p_months_max integer DEFAULT 48)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'extensions'
AS $function$
declare
  v_ref    geography := st_setsrid(st_makepoint(p_lon, p_lat), 4326)::geography;
  v_smin   numeric := case when p_surface is not null then p_surface * (1 - p_tol) end;
  v_smax   numeric := case when p_surface is not null then p_surface * (1 + p_tol) end;
  v_cap    integer := greatest(1000, round(p_radius_km * 1000)::int);
  v_use_terrain boolean := (lower(p_type) = 'maison' and p_terrain is not null and p_terrain > 0 and coalesce(p_terrain_tol,0) > 1);
  v_tmin   numeric := case when v_use_terrain then p_terrain / p_terrain_tol end;
  v_tmax   numeric := case when v_use_terrain then p_terrain * p_terrain_tol end;
  v_radius integer;
  v_months integer;
  v_terr   boolean;
  v_result jsonb;
begin
  if p_lat is null or p_lon is null or p_lat = 0 or p_lon = 0 then
    return jsonb_build_object('ok', false, 'reason', 'missing_geo', 'count', 0, 'fiable', false, 'comparables', '[]'::jsonb);
  end if;

  with ladder(ord, radius, months, terr) as (
    values
      (1, 1000, p_months,     v_use_terrain),
      (2, 1000, p_months_max, v_use_terrain),
      (3, 2000, p_months,     v_use_terrain),
      (4, 2000, p_months_max, v_use_terrain),
      (5, 2000, p_months_max, false),
      (6, 4000, p_months_max, false),
      (7, 8000, p_months_max, false),
      (8, greatest(v_cap, 8000), p_months_max, false)
  ),
  counts as (
    select l.ord, least(l.radius, v_cap) as radius, l.months, l.terr,
      (select count(*) from app_dvf_vente v
        where v.type_local = p_type
          and v.date_mutation >= (current_date - make_interval(months => l.months))::date
          and (v_smin is null or v.surface between v_smin and v_smax)
          and (not l.terr or (v.terrain is not null and v.terrain between v_tmin and v_tmax))
          and st_dwithin(v.geom, v_ref, least(l.radius, v_cap))) as n
    from ladder l
  )
  select radius, months, terr into v_radius, v_months, v_terr
  from counts where n >= p_min_local order by ord limit 1;

  if v_radius is null then
    v_radius := v_cap; v_months := p_months_max; v_terr := false;
  end if;

  with base as (
    select v.*, st_distance(v.geom, v_ref) as dist
    from app_dvf_vente v
    where v.type_local = p_type
      and v.date_mutation >= (current_date - make_interval(months => v_months))::date
      and (v_smin is null or v.surface between v_smin and v_smax)
      and (not v_terr or (v.terrain is not null and v.terrain between v_tmin and v_tmax))
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
    'ok', true, 'type', p_type, 'months', v_months, 'surface', p_surface,
    'terrain_applied', v_terr, 'radius_used_m', v_radius, 'radius_km', round(v_radius / 1000.0, 1),
    'count', s.n, 'count_clean', s.n, 'fiable', (s.n >= p_min_local),
    'median_prix_m2', round(s.med), 'avg_prix_m2', s.avg, 'p25_prix_m2', round(s.p25), 'p75_prix_m2', round(s.p75),
    'prix_estime',      case when p_surface is not null and s.med is not null then round(s.med * p_surface) end,
    'fourchette_basse', case when p_surface is not null and s.p25 is not null then round(s.p25 * p_surface) end,
    'fourchette_haute', case when p_surface is not null and s.p75 is not null then round(s.p75 * p_surface) end,
    'commune', coalesce(nullif(trim(coalesce(p_commune, '')), ''), (select mode() within group (order by commune) from sel)),
    'scope', case when v_radius <= 2000 then 'commune' else 'secteur' end,
    'n_local', s.n, 'data_through', (select max(date_mutation) from sel),
    'evolution', coalesce((select jsonb_agg(jsonb_build_object('annee', annee::text, 'prix_m2', prix_m2, 'n', n) order by annee) from evo), '[]'::jsonb),
    'comparables', coalesce((
      select jsonb_agg(jsonb_build_object(
        'commune', commune, 'type', type_local, 'surface', round(surface)::int, 'pieces', pieces::text,
        'terrain', case when terrain is not null then round(terrain)::int end,
        'valeur', round(valeur)::int, 'prix_m2', prix_m2, 'date', date_mutation::text,
        'distance_km', round((dist / 1000.0)::numeric, 1)) order by dist)
      from (select * from sel order by dist limit greatest(p_limit, 1)) c
    ), '[]'::jsonb)
  ) into v_result from stats s;

  return v_result;
end
$function$;

-- Nettoyage de l'ancienne surcharge 12 args (évite l'ambiguïté PostgREST) :
DROP FUNCTION IF EXISTS public.app_dvf_comparables(
  double precision, double precision, text, numeric, numeric, integer, numeric, integer, text, text, integer, integer);
