create table if not exists public.app_setting (
    key text primary key,
    value text,
    description text,
    updated_at timestamptz not null default now()
);

alter table public.app_setting enable row level security;

drop policy if exists app_setting_select_active_user on public.app_setting;
create policy app_setting_select_active_user
on public.app_setting
for select
using (public.is_app_user_active());

insert into public.app_setting (key, value, description)
values (
    'appointment_email_logo_url',
    'https://gtiimmo.github.io/vitrine/rdv/gti-logo.png',
    'URL publique du logo utilise dans les emails HTML de demande de rendez-vous.'
)
on conflict (key) do update
set
    value = excluded.value,
    description = excluded.description,
    updated_at = now();

comment on table public.app_setting is 'Parametres applicatifs simples lus par le backend via Supabase.';
