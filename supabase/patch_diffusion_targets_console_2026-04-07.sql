create table if not exists public.app_diffusion_target (
    app_dossier_id bigint not null,
    hektor_annonce_id bigint not null,
    hektor_broadcast_id text not null,
    portal_key text,
    target_state text not null default 'enabled'
        check (target_state in ('enabled', 'disabled')),
    source_ref text,
    note text,
    requested_by_role text,
    requested_by_name text,
    requested_at timestamptz not null default now(),
    last_applied_at timestamptz,
    last_apply_status text,
    last_apply_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (app_dossier_id, hektor_broadcast_id)
);

create table if not exists public.app_diffusion_agency_target (
    agence_nom text not null,
    portal_key text not null,
    hektor_broadcast_id text not null,
    is_active integer not null default 1,
    note text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (agence_nom, portal_key)
);

create index if not exists idx_app_diffusion_target_annonce
on public.app_diffusion_target(hektor_annonce_id, target_state);

create index if not exists idx_app_diffusion_target_portal
on public.app_diffusion_target(hektor_broadcast_id, target_state);

create index if not exists idx_app_diffusion_agency_target_portal
on public.app_diffusion_agency_target(portal_key, hektor_broadcast_id, is_active);

insert into public.app_diffusion_agency_target (agence_nom, portal_key, hektor_broadcast_id, is_active, note)
values
('Groupe GTI Ambert', 'bienicidirect', '2', 1, 'Flux par agence'),
('Groupe GTI Ambert', 'leboncoinDirect', '35', 1, 'Flux par agence'),
('Groupe GTI ANNONAY', 'bienicidirect', '3', 1, 'Flux par agence'),
('Groupe GTI ANNONAY', 'leboncoinDirect', '36', 1, 'Flux par agence'),
('Groupe GTI BRIOUDE', 'bienicidirect', '4', 1, 'Flux par agence'),
('Groupe GTI BRIOUDE', 'leboncoinDirect', '41', 1, 'Flux par agence'),
('Groupe GTI Craponne-sur-Arzon', 'bienicidirect', '5', 1, 'Flux par agence'),
('Groupe GTI Craponne-sur-Arzon', 'leboncoinDirect', '42', 1, 'Flux par agence'),
('Groupe GTI Yssingeaux', 'bienicidirect', '6', 1, 'Flux par agence'),
('Groupe GTI Yssingeaux', 'leboncoinDirect', '38', 1, 'Flux par agence'),
('Groupe GTI Montbrison', 'bienicidirect', '7', 1, 'Flux par agence'),
('Groupe GTI Montbrison', 'leboncoinDirect', '37', 1, 'Flux par agence'),
('Groupe GTI Saint-Just-Saint-Rambert', 'bienicidirect', '8', 1, 'Flux par agence'),
('Groupe GTI Saint-Just-Saint-Rambert', 'leboncoinDirect', '37', 1, 'Flux par agence'),
('Groupe GTI Issoire', 'bienicidirect', '9', 1, 'Flux par agence'),
('Groupe GTI Issoire', 'leboncoinDirect', '41', 1, 'Flux par agence'),
('Groupe GTI Saint-Bonnet-le-Château', 'bienicidirect', '10', 1, 'Flux par agence'),
('Groupe GTI Saint-Bonnet-le-Château', 'leboncoinDirect', '42', 1, 'Flux par agence'),
('Groupe GTI COURPIERE', 'bienicidirect', '11', 1, 'Flux par agence'),
('Groupe GTI COURPIERE', 'leboncoinDirect', '35', 1, 'Flux par agence'),
('Groupe GTI Monistrol sur Loire', 'bienicidirect', '13', 1, 'Flux par agence'),
('Groupe GTI Monistrol sur Loire', 'leboncoinDirect', '40', 1, 'Flux par agence'),
('Groupe GTI Saint-Didier-en-Velay', 'bienicidirect', '14', 1, 'Flux par agence'),
('Groupe GTI Saint-Didier-en-Velay', 'leboncoinDirect', '40', 1, 'Flux par agence'),
('Groupe GTI Firminy', 'bienicidirect', '15', 1, 'Flux par agence'),
('Groupe GTI Firminy', 'leboncoinDirect', '39', 1, 'Flux par agence'),
('Groupe GTI Saint-Etienne', 'bienicidirect', '16', 1, 'Flux par agence'),
('Groupe GTI Saint-Etienne', 'leboncoinDirect', '39', 1, 'Flux par agence'),
('Groupe GTI Dunières', 'bienicidirect', '17', 1, 'Flux par agence'),
('Groupe GTI Dunières', 'leboncoinDirect', '43', 1, 'Flux par agence'),
('Groupe GTI Tence', 'bienicidirect', '22', 1, 'Flux par agence'),
('Groupe GTI Tence', 'leboncoinDirect', '43', 1, 'Flux par agence'),
('Groupe Gti Le Puy en Velay', 'bienicidirect', '23', 1, 'Flux par agence'),
('Groupe Gti Le Puy en Velay', 'leboncoinDirect', '38', 1, 'Flux par agence')
on conflict (agence_nom, portal_key) do update
set
    hektor_broadcast_id = excluded.hektor_broadcast_id,
    is_active = excluded.is_active,
    note = excluded.note,
    updated_at = now();

alter table public.app_diffusion_target enable row level security;
alter table public.app_diffusion_agency_target enable row level security;

drop policy if exists "app_diffusion_target_select_active_users" on public.app_diffusion_target;
create policy "app_diffusion_target_select_active_users"
on public.app_diffusion_target
for select
using (public.is_app_user_active());

drop policy if exists "app_diffusion_target_insert_active_users" on public.app_diffusion_target;
create policy "app_diffusion_target_insert_active_users"
on public.app_diffusion_target
for insert
with check (public.is_app_user_active());

drop policy if exists "app_diffusion_target_update_active_users" on public.app_diffusion_target;
create policy "app_diffusion_target_update_active_users"
on public.app_diffusion_target
for update
using (public.is_app_user_active())
with check (public.is_app_user_active());

drop policy if exists "app_diffusion_target_delete_active_users" on public.app_diffusion_target;
create policy "app_diffusion_target_delete_active_users"
on public.app_diffusion_target
for delete
using (public.is_app_user_active());

drop policy if exists "app_diffusion_agency_target_select_active_users" on public.app_diffusion_agency_target;
create policy "app_diffusion_agency_target_select_active_users"
on public.app_diffusion_agency_target
for select
using (public.is_app_user_active());
