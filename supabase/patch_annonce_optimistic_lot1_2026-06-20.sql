-- =====================================================================
-- TIER 2 — Lot 1 : socle édition optimiste des annonces (prix d'abord)
-- 2026-06-20. Clone de la machinerie recherches (app_search_pending + RPC).
-- Cible : ANNONCES actives (statut 'Actif'). Estimations = lot ultérieur
-- (valeur ESTIMATION_MONTANT dans un blob JSON, pas de rapprochement).
-- =====================================================================

-- 1) Table "en attente" (drapeau dirty + débounce + retry) — clone app_search_pending,
--    clé = app_dossier_id (1 bien = 1 brouillon, pas d'index multiple).
create table if not exists public.app_annonce_pending (
  app_dossier_id     bigint primary key,
  hektor_annonce_id  text,
  base_snapshot      jsonb not null default '{}'::jsonb,  -- valeurs pré-édition (anti-écrasement)
  push_fields        jsonb,                               -- champs à pousser vers Hektor
  dirty_at           timestamptz not null default now(),
  push_after         timestamptz not null default now(),
  source             text,                                -- nego_app | espace_client
  dirty_by           text,
  push_job_id        uuid,
  conflict           boolean not null default false,
  push_attempts      integer not null default 0,
  updated_at         timestamptz not null default now()
);
alter table public.app_annonce_pending enable row level security;
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='app_annonce_pending' and policyname='app_annonce_pending_read') then
    create policy app_annonce_pending_read on public.app_annonce_pending for select to authenticated using (true);
  end if;
end $$;

-- 2) Recompute des rapprochements POUR UN BIEN (inverse de app_refresh_rapprochements_for_search).
--    Score le bien contre toutes les recherches actives. Si le bien n'est plus Actif/diffusable,
--    on purge ses rapprochements.
create or replace function public.app_refresh_rapprochements_for_dossier(p_app_dossier_id bigint)
 returns integer language plpgsql security definer set search_path to 'public'
as $function$
declare d app_dossier_current%rowtype; pd jsonb;
begin
  select * into d from app_dossier_current where app_dossier_id = p_app_dossier_id;
  if not found then return 0; end if;

  if d.statut_annonce <> 'Actif' or d.diffusable <> '1' then
    delete from app_rapprochement where app_dossier_id = p_app_dossier_id;
    return 0;
  end if;

  pd := app_dossier_match_payload(p_app_dossier_id);

  drop table if exists _new_rappro_d;
  create temp table _new_rappro_d on commit drop as
  select s.contact_search_key, s.hektor_contact_id,
         (x.res->>'score')::int as score, x.res->'components' as components
  from app_contact_search_current s
  cross join lateral (select app_match_score_v2(to_jsonb(s), pd) as res) x
  where coalesce(s.is_active, true) = true
    and coalesce(s.archive, false) = false
    and (x.res->>'eligible')::bool = true
    and (x.res->>'score')::int >= 60;

  insert into app_rapprochement_score_history(contact_search_key, app_dossier_id, score, reason)
  select nw.contact_search_key, p_app_dossier_id, nw.score,
         case when old.app_dossier_id is null then 'init' else 'change' end
  from _new_rappro_d nw
  left join app_rapprochement old
    on old.contact_search_key = nw.contact_search_key and old.app_dossier_id = p_app_dossier_id
  where old.app_dossier_id is null or old.score <> nw.score;

  insert into app_rapprochement(contact_search_key, hektor_contact_id, app_dossier_id, score, score_components, eligible)
  select nw.contact_search_key, nw.hektor_contact_id, p_app_dossier_id, nw.score, nw.components, true
  from _new_rappro_d nw
  on conflict (contact_search_key, app_dossier_id)
  do update set score = excluded.score, score_components = excluded.score_components,
                eligible = true, computed_at = now();

  delete from app_rapprochement r
  where r.app_dossier_id = p_app_dossier_id
    and not exists (select 1 from _new_rappro_d nw where nw.contact_search_key = r.contact_search_key);

  return (select count(*) from _new_rappro_d);
end $function$;

-- 3) RPC édition optimiste du PRIX d'une annonce (négo dans l'app).
--    Écrit la colonne prix + recompute synchrone + arme le push débouncé.
create or replace function public.app_edit_annonce_optimistic(
  target_dossier_id bigint, edit_fields jsonb, debounce_seconds integer default 600)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $function$
declare d app_dossier_current%rowtype; v_price text; v_base jsonb;
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_job('update_hektor_annonce_fields', target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_update_annonce' using errcode='42501'; end if;

  v_price := nullif(trim(coalesce(edit_fields->>'price', edit_fields->>'prix', '')), '');
  if v_price is null or v_price !~ '^[0-9]+([.,][0-9]+)?$' then
    raise exception 'invalid_price' using errcode='22023'; end if;

  -- photo anti-écrasement : valeur Hektor AU CHARGEMENT (figée si déjà un pending)
  if exists (select 1 from app_annonce_pending p where p.app_dossier_id = target_dossier_id)
    then select base_snapshot into v_base from app_annonce_pending where app_dossier_id = target_dossier_id;
    else v_base := jsonb_build_object('prix', d.prix);
  end if;

  update app_dossier_current set prix = v_price where app_dossier_id = target_dossier_id;
  perform public.app_refresh_rapprochements_for_dossier(target_dossier_id);

  insert into public.app_annonce_pending(app_dossier_id, hektor_annonce_id, base_snapshot, push_fields, push_after, source, dirty_by)
  values (target_dossier_id, d.hektor_annonce_id::text, v_base,
          jsonb_build_object('price', v_price),
          now() + make_interval(secs => greatest(debounce_seconds, 30)), 'nego_app', auth.uid()::text)
  on conflict (app_dossier_id) do update set
    push_fields = excluded.push_fields,
    push_after = now() + make_interval(secs => greatest(debounce_seconds, 30)),
    push_job_id = null, conflict = false, push_attempts = 0, updated_at = now();

  return jsonb_build_object('ok', true, 'app_dossier_id', target_dossier_id, 'prix', v_price);
end $function$;
