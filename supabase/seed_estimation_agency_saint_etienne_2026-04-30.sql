insert into public.app_estimation_agency_route (
  route_key,
  agency_id,
  agency_label,
  is_active
) values (
  'saint-etienne',
  '18',
  'Groupe GTI Saint-Etienne',
  true
)
on conflict (route_key) do update
set
  agency_id = excluded.agency_id,
  agency_label = excluded.agency_label,
  is_active = excluded.is_active,
  updated_at = now();

insert into public.app_estimation_agency_negotiator (
  route_key,
  user_id,
  negotiator_label,
  negotiator_email,
  negotiator_phone,
  is_active,
  sort_order
) values
  ('saint-etienne', '29', 'Lucille FORLICO', 'forlico@gti-immobilier.fr', '0640193927', true, 10),
  ('saint-etienne', '30', 'Melanie LEGRAND', 'legrand@gti-immobilier.fr', '0668413858', true, 20)
on conflict (route_key, user_id) do update
set
  negotiator_label = excluded.negotiator_label,
  negotiator_email = excluded.negotiator_email,
  negotiator_phone = excluded.negotiator_phone,
  is_active = excluded.is_active,
  sort_order = excluded.sort_order,
  updated_at = now();
