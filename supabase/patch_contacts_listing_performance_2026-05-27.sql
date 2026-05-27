-- Optimisation lecture Contacts.
-- Objectif: rendre le listing Contacts comparable aux index legers Annonces sans changer le perimetre RLS.

create index if not exists idx_app_contact_current_search_text_trgm
on public.app_contact_current
using gin (search_text gin_trgm_ops);

create index if not exists idx_app_contact_current_listing_order
on public.app_contact_current (
  archive,
  duplicate_group_count desc nulls last,
  date_maj desc nulls last,
  display_name asc,
  hektor_contact_id asc
);

drop policy if exists "app_contact_current_select_scoped" on public.app_contact_current;
create policy "app_contact_current_select_scoped"
on public.app_contact_current
for select
using (
  (select public.is_app_global_reader())
  or public.can_access_negotiator_email(negociateur_email)
  or exists (
    select 1
    from public.app_contact_relation_current r
    where r.hektor_contact_id = app_contact_current.hektor_contact_id
      and r.app_dossier_id is not null
      and public.can_access_current_dossier(r.app_dossier_id)
  )
);

drop policy if exists "app_contact_relation_current_select_scoped" on public.app_contact_relation_current;
create policy "app_contact_relation_current_select_scoped"
on public.app_contact_relation_current
for select
using (
  (select public.is_app_global_reader())
  or (
    app_dossier_id is not null
    and public.can_access_current_dossier(app_dossier_id)
  )
);

drop policy if exists "app_contact_search_current_select_scoped" on public.app_contact_search_current;
create policy "app_contact_search_current_select_scoped"
on public.app_contact_search_current
for select
using (
  exists (
    select 1
    from public.app_contact_current c
    where c.hektor_contact_id = app_contact_search_current.hektor_contact_id
      and (
        (select public.is_app_global_reader())
        or public.can_access_negotiator_email(c.negociateur_email)
      )
  )
);
