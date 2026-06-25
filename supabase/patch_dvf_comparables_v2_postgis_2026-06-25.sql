-- =====================================================================
-- DVF v2 — RPC comparables : PostGIS, rayon progressif, médiane + fourchette
-- 2026-06-25 (Lot 2).
--
-- Remplace le commune-first/haversine par un filtre GPS réel (ST_DWithin) avec
-- RAYON PROGRESSIF : on part de 2 km, on élargit à 5 puis 10 km tant qu'on n'a
-- pas au moins `p_min_local` (=5) comparables. On plafonne le calcul aux
-- `p_max_comps` (=30) biens les plus proches. Nettoyage final : rognage 5/95 %
-- (si échantillon >= 20). Statistique = MÉDIANE. Estimation = médiane €/m² ×
-- surface ; fourchette = quartiles p25–p75 × surface. `fiable` = (count >= min).
--
-- Compat : signature conservée (mêmes params + p_max_comps en queue, défaut) et
-- réponse en SURENSEMBLE (anciens champs avg/median/count/comparables/evolution/
-- scope conservés) -> le front déjà déployé continue de fonctionner.
--   p_radius_km  -> réinterprété en rayon MAX (cap des anneaux)
--   p_tol        -> surface ±25 % (défaut 0.25)
--   p_min_local  -> min comparables (fiabilité + expansion) (défaut 5)
-- =====================================================================

drop function if exists public.app_dvf_comparables(
  double precision, double precision, text, numeric, numeric, integer, numeric, integer, text, text, integer);

create or replace function public.app_dvf_comparables(
  p_lat         double precision,
  p_lon         double precision,
  p_type        text    default 'Maison',
  p_surface     numeric default null,
  p_radius_km   numeric default 12,     -- rayon MAX (cap des anneaux)
  p_months      integer default 24,
  p_tol         numeric default 0.25,   -- surface ±25 %
  p_limit       integer default 6,      -- nb comparables affichés
  p_code_postal text    default null,   -- (libellé commune)
  p_commune     text    default null,
  p_min_local   integer default 5,      -- min comparables (fiabilité + expansion)
  p_max_comps   integer default 30)     -- plafond comparables pour le calcul
 returns jsonb
 language plpgsql
 security definer
 set search_path to public, extensions
as $function$
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
begin
  if p_lat is null or p_lon is null or p_lat = 0 or p_lon = 0 then
    return jsonb_build_object('ok', false, 'reason', 'missing_geo', 'count', 0, 'fiable', false, 'comparables', '[]'::jsonb);
  end if;

  -- rayon progressif : plus petit anneau (<= cap) atteignant p_min_local comparables
  foreach v_ring in array v_rings loop
    if v_ring > v_cap then continue; end if;
    select count(*) into v_n from app_dvf_vente v
    where v.type_local = p_type and v.date_mutation >= v_cutoff
      and (v_smin is null or v.surface between v_smin and v_smax)
      and st_dwithin(v.geom, v_ref, v_ring);
    if v_n >= p_min_local then v_radius := v_ring; exit; end if;
  end loop;
  if v_radius is null then v_radius := least(10000, v_cap); end if;  -- rien d'assez fourni -> plus grand anneau autorisé

  with base as (   -- comparables dans le rayon retenu (type, période, surface ±tol)
    select v.*, st_distance(v.geom, v_ref) as dist
    from app_dvf_vente v
    where v.type_local = p_type and v.date_mutation >= v_cutoff
      and (v_smin is null or v.surface between v_smin and v_smax)
      and st_dwithin(v.geom, v_ref, v_radius)
  ),
  bnd as (
    select count(*) n,
           percentile_cont(0.05) within group (order by prix_m2) p05,
           percentile_cont(0.95) within group (order by prix_m2) p95
    from base where prix_m2 is not null
  ),
  trimmed as (   -- rognage 5/95 % seulement si échantillon suffisant (>=20)
    select b.* from base b, bnd
    where b.prix_m2 is not null
      and (bnd.n < 20 or b.prix_m2 between bnd.p05 and bnd.p95)
  ),
  sel as (       -- plafond : les p_max_comps plus proches servent au calcul
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
  evo_base as (  -- évolution : type + rayon retenu, sans filtre surface/période
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
    'radius_used_m', v_radius,
    'radius_km', round(v_radius / 1000.0, 1),
    'count', s.n,                       -- = nb comparables utilisés (compat)
    'count_clean', s.n,
    'fiable', (s.n >= p_min_local),
    'median_prix_m2', round(s.med),
    'avg_prix_m2', s.avg,               -- compat
    'p25_prix_m2', round(s.p25),
    'p75_prix_m2', round(s.p75),
    'prix_estime',      case when p_surface is not null and s.med is not null then round(s.med * p_surface) end,
    'fourchette_basse', case when p_surface is not null and s.p25 is not null then round(s.p25 * p_surface) end,
    'fourchette_haute', case when p_surface is not null and s.p75 is not null then round(s.p75 * p_surface) end,
    'commune', coalesce(nullif(trim(coalesce(p_commune, '')), ''), (select mode() within group (order by commune) from sel)),
    'scope', case when v_radius <= 2000 then 'commune' else 'secteur' end,  -- compat
    'n_local', s.n,                     -- compat
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

grant execute on function public.app_dvf_comparables(
  double precision, double precision, text, numeric, numeric, integer, numeric, integer, text, text, integer, integer
) to authenticated, service_role;
