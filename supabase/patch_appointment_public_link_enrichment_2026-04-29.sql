alter table public.app_appointment_public_link
    add column if not exists ville text,
    add column if not exists type_bien text,
    add column if not exists prix numeric,
    add column if not exists photo_url text,
    add column if not exists negociateur_phone text,
    add column if not exists negociateur_mobile text,
    add column if not exists agence_phone text,
    add column if not exists agence_email text;

comment on column public.app_appointment_public_link.ville is 'Ville publique affichee sur la page RDV.';
comment on column public.app_appointment_public_link.type_bien is 'Nature du bien affichee sur la page RDV.';
comment on column public.app_appointment_public_link.prix is 'Prix affiche sur la page RDV.';
comment on column public.app_appointment_public_link.photo_url is 'Photo principale du bien pour la page RDV.';
comment on column public.app_appointment_public_link.negociateur_phone is 'Telephone fixe du negociateur enrichi hors parcours public.';
comment on column public.app_appointment_public_link.negociateur_mobile is 'Telephone mobile du negociateur enrichi hors parcours public.';
comment on column public.app_appointment_public_link.agence_phone is 'Telephone agence enrichi hors parcours public.';
comment on column public.app_appointment_public_link.agence_email is 'Email agence enrichi hors parcours public.';
