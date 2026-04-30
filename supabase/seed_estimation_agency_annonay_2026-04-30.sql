insert into public.app_estimation_agency_route (
  route_key,
  agency_id,
  agency_label,
  is_active
) values (
  'annonay',
  '10',
  'Groupe GTI ANNONAY',
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
  ('annonay', '54', 'Hugo LABBE', 'labbe@gti-immobilier.fr', '0760683854', true, 10),
  ('annonay', '56', 'Pierrick MARTINEZ', 'martinez@gti-immobilier.fr', '0678250925', true, 20),
  ('annonay', '55', 'Stéphanie MARTINEZ', 'stephanie.martinez@gti-immobilier.fr', '0632930450', true, 30),
  ('annonay', '115', 'Corinne REYNAUD', 'corinne.reynaud@gti-immobilier.fr', '06 81 61 69 43', true, 40)
on conflict (route_key, user_id) do update
set
  negotiator_label = excluded.negotiator_label,
  negotiator_email = excluded.negotiator_email,
  negotiator_phone = excluded.negotiator_phone,
  is_active = excluded.is_active,
  sort_order = excluded.sort_order,
  updated_at = now();
