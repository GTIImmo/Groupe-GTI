-- Espace client : index de recherche stable sur l'envoi (la contact_search_key change à l'édition).
-- Additif, réversible (alter table ... drop column search_index).
alter table public.app_email_envoi add column if not exists search_index integer;
comment on column public.app_email_envoi.search_index
is 'Index de la recherche du contact (stable), pour retrouver la recherche meme si contact_search_key change apres edition.';
