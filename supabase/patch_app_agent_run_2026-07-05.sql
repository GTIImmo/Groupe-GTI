-- ============================================================================
-- patch_app_agent_run_2026-07-05.sql
--
-- Phase 3 - Agent "Redacteur d'annonce" (premier agent IA, propose-only / N0).
-- Table de suivi des executions d'agent : 1 ligne par proposition generee, avec
-- le cout (tokens), la proposition, et la decision humaine (accepte/modifie/rejete).
--
-- ADDITIF : nouvelle table isolee, ne touche a aucune table existante.
-- Sert (a) au suivi/analytics des agents, (b) plus tard de source pour la couche
-- app_alert (branche 'agent' = trivial a brancher, cf. [[app-alert-et-bac-a-sable]]).
--
-- Aucune ecriture autonome : l'agent PROPOSE, l'humain valide dans l'UI. La
-- decision est enregistree ici a titre de trace, elle ne declenche rien.
-- ============================================================================

create table if not exists public.app_agent_run (
  id                bigint generated always as identity primary key,
  agent_key         text not null,                       -- 'redacteur'
  app_dossier_id    bigint,
  hektor_annonce_id bigint,
  negociateur_email text,
  status            text not null default 'proposed',    -- proposed | accepted | rejected | error
  model             text,
  input_tokens      integer,
  output_tokens     integer,
  total_tokens      integer,
  cost_usd          numeric(10,5),
  proposal_json     jsonb,                                -- {title, description, highlights}
  outcome_json      jsonb,                                -- texte finalement retenu par l'humain
  error_text        text,
  created_at        timestamptz not null default now(),
  decided_at        timestamptz,
  constraint app_agent_run_status_check
    check (status = any (array['proposed','accepted','rejected','error']))
);

create index if not exists app_agent_run_dossier_idx  on public.app_agent_run (app_dossier_id, created_at desc);
create index if not exists app_agent_run_nego_idx      on public.app_agent_run (negociateur_email, created_at desc);
create index if not exists app_agent_run_agent_idx     on public.app_agent_run (agent_key, created_at desc);

alter table public.app_agent_run enable row level security;

-- Lecture : le negociateur voit ses propres runs ; admin/manager voient tout.
drop policy if exists app_agent_run_select on public.app_agent_run;
create policy app_agent_run_select on public.app_agent_run
  for select to authenticated
  using (
    lower(coalesce(negociateur_email,'')) = lower(coalesce((auth.jwt() ->> 'email'),''))
    or exists (
      select 1 from public.app_user_profile p
      where p.id = auth.uid() and p.role in ('admin','manager') and p.is_active is true
    )
  );

-- Ecriture : reservee au service_role (le backend). Aucune policy insert/update
-- pour authenticated => les clients ne peuvent pas falsifier tokens/cout.
