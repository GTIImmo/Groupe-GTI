alter table public.app_mandat_register_current
add column if not exists price_change_event_count integer not null default 0;

alter table public.app_mandat_register_current
add column if not exists price_change_last_source_kind text;

alter table public.app_mandat_register_current
add column if not exists price_change_last_old_value numeric;

alter table public.app_mandat_register_current
add column if not exists price_change_last_new_value numeric;

alter table public.app_mandat_register_current
add column if not exists price_change_last_detected_at text;

alter table public.app_mandat_register_current
add column if not exists price_change_last_source_updated_at text;

drop view if exists public.app_registre_mandats_current;

create view public.app_registre_mandats_current
with (security_invoker=on) as
select *
from public.app_mandat_register_current;

notify pgrst, 'reload schema';
