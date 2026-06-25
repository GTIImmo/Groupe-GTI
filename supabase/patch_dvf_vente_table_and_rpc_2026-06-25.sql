-- =====================================================================
-- DVF pré-chargé — table + RPC comparables (Supabase-first)
-- 2026-06-25.
--
-- Contexte : la DVF (DGFiP/geo-dvf) n'est publiée que ~2×/an (avril + octobre).
-- Inutile de re-télécharger à chaque requête depuis data.gouv. On pré-charge les
-- ventes des 4 départements GTI (42/43/63/07) dans `app_dvf_vente`, rafraîchies
-- 2×/an (fin avril / fin octobre) par un script d'ingestion planifié. Le front
-- (et le worker via payload.marche) lisent la RPC `app_dvf_comparables` —
-- haversine côté SQL, plus aucune dépendance data.gouv/Render au moment de la requête.
--
-- Périmètre : 42/43/63/07 (mutuellement limitrophes : un bien près d'une frontière
-- interne récupère les comparables du dépt voisin parmi les 4 via le rayon).
-- =====================================================================

-- 1) Table des ventes pré-chargées --------------------------------------------
create table if not exists public.app_dvf_vente (
  id          bigserial primary key,
  date_mutation date     not null,
  type_local  text       not null,                 -- 'Maison' | 'Appartement'
  valeur      numeric    not null,                 -- valeur_fonciere
  surface     numeric    not null,                 -- surface_reelle_bati
  pieces      integer,                             -- nombre_pieces_principales
  terrain     numeric,                             -- surface_terrain
  commune     text,
  code_postal text,
  dept        text       not null,                 -- '42' | '43' | '63' | '07'
  lat         double precision not null,
  lon         double precision not null,
  prix_m2     numeric                              -- valeur / surface (arrondi)
);

create index if not exists idx_dvf_type_dept on public.app_dvf_vente(type_local, dept);
create index if not exists idx_dvf_latlon     on public.app_dvf_vente(lat, lon);
create index if not exists idx_dvf_date       on public.app_dvf_vente(date_mutation);

-- Table verrouillée : accès uniquement via la RPC (security definer). Pas de
-- policy => aucun rôle anon/authenticated ne lit la table en direct.
alter table public.app_dvf_vente enable row level security;

-- Le service_role (script d'ingestion) écrit en bypassant la RLS. On lui accorde
-- explicitement les droits table (au cas où la clé ne serait pas BYPASSRLS).
grant select, insert, delete on public.app_dvf_vente to service_role;
grant usage, select on sequence public.app_dvf_vente_id_seq to service_role;

-- 2) RPC comparables ----------------------------------------------------------
-- Pré-filtre par boîte englobante (index lat/lon) puis haversine exact. Renvoie
-- le même JSON que l'ancien service Python (ok/count/avg/median/evolution/
-- comparables) + data_through (date de la vente la plus récente du secteur).
create or replace function public.app_dvf_comparables(
  p_lat       double precision,
  p_lon       double precision,
  p_type      text    default 'Maison',
  p_surface   numeric default null,
  p_radius_km numeric default 12,
  p_months    integer default 24,
  p_tol       numeric default 0.30,
  p_limit     integer default 5)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  v_dlat   double precision := p_radius_km / 111.0;
  v_dlon   double precision := p_radius_km / (111.0 * greatest(cos(radians(p_lat)), 0.01));
  v_cutoff date := (current_date - make_interval(months => p_months))::date;
  v_smin   numeric := case when p_surface is not null then p_surface * (1 - p_tol) end;
  v_smax   numeric := case when p_surface is not null then p_surface * (1 + p_tol) end;
  v_result jsonb;
begin
  if p_lat is null or p_lon is null or p_lat = 0 or p_lon = 0 then
    return jsonb_build_object('ok', false, 'reason', 'missing_geo', 'count', 0, 'comparables', '[]'::jsonb);
  end if;

  with cand as (
    -- boîte englobante (rapide via index) + distance haversine
    select v.*,
      6371.0 * 2 * asin(sqrt(
        power(sin(radians((v.lat - p_lat) / 2)), 2)
        + cos(radians(p_lat)) * cos(radians(v.lat)) * power(sin(radians((v.lon - p_lon) / 2)), 2)
      )) as dist
    from app_dvf_vente v
    where v.type_local = p_type
      and v.lat between p_lat - v_dlat and p_lat + v_dlat
      and v.lon between p_lon - v_dlon and p_lon + v_dlon
  ),
  inrad as (
    select * from cand where dist <= p_radius_km
  ),
  matched as (
    -- comparables retenus : rayon + période + surface ±tol
    select * from inrad
    where date_mutation >= v_cutoff
      and (v_smin is null or surface between v_smin and v_smax)
  ),
  agg as (
    select count(*) filter (where prix_m2 is not null)::int as n,
           round(avg(prix_m2))                              as avg_pm,
           percentile_cont(0.5) within group (order by prix_m2) as med_pm
    from matched
  ),
  evo as (
    -- évolution du prix/m² par année : tout le secteur (rayon, sans filtre surface/période)
    select extract(year from date_mutation)::int as annee,
           round(avg(prix_m2)) as prix_m2, count(*)::int as n
    from inrad where prix_m2 is not null
    group by 1 order by 1
  ),
  comps as (
    select * from matched
    order by case when p_surface is not null then abs(surface - p_surface) else 0 end,
             date_mutation desc
    limit greatest(p_limit, 1)
  )
  select jsonb_build_object(
    'ok', true,
    'count', coalesce((select n from agg), 0),
    'avg_prix_m2', (select avg_pm from agg),
    'median_prix_m2', (select round(med_pm) from agg),
    'radius_km', p_radius_km,
    'months', p_months,
    'type', p_type,
    'data_through', (select max(date_mutation) from inrad),
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
  double precision, double precision, text, numeric, numeric, integer, numeric, integer
) to authenticated, service_role;
