-- Fix : la recherche du Registre des mandats filtre sur `search_text`
-- (listingSearchColumns → app_registre_mandats_current.search_text), mais la
-- table registre n'avait jamais cette colonne → erreur SQL au moment de la
-- recherche. On l'ajoute (peuplée par build_search_text côté push) et on
-- recrée la vue pour l'exposer.

alter table public.app_mandat_register_current
add column if not exists search_text text;

drop view if exists public.app_registre_mandats_current;

create view public.app_registre_mandats_current
with (security_invoker=on) as
select *
from public.app_mandat_register_current;

notify pgrst, 'reload schema';
