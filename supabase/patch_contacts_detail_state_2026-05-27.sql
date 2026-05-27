begin;

alter table public.app_contact_current
    add column if not exists has_contact_detail boolean not null default false,
    add column if not exists contact_detail_synced_at text;

create index if not exists idx_app_contact_current_detail_state
    on public.app_contact_current (has_contact_detail, contact_detail_synced_at desc);

comment on column public.app_contact_current.has_contact_detail is
    'Indique si la fiche ContactById du contact est deja presente dans le miroir local Hektor.';

comment on column public.app_contact_current.contact_detail_synced_at is
    'Date locale du dernier chargement ContactById connu. Le payload brut reste local.';

create or replace view public.app_contacts_current
with (security_invoker = true)
as
select *
from public.app_contact_current;

grant select on public.app_contacts_current to authenticated;

commit;
