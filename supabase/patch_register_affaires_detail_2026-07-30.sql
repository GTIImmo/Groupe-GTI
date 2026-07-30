-- Lot B / C1 (vision par cycle) : détail COMPLET de l'affaire par cycle
-- (financiers + parties acquéreur/mandant/notaire avec leur id contact et
-- coordonnées, déjà embarqués dans les tables locales hektor_offre/compromis/
-- vente), sérialisé en JSON par ligne de registre pour re-scoper les rubriques
-- Affaires et Contacts du cockpit sur le cycle sélectionné.

alter table public.app_mandat_register_current
add column if not exists affaires_detail_json text;

drop view if exists public.app_registre_mandats_current;

create view public.app_registre_mandats_current
with (security_invoker=on) as
select *
from public.app_mandat_register_current;

notify pgrst, 'reload schema';
