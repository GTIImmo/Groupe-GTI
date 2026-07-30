-- Lot A (principe de clôture de mandat) — remonter la date de clôture du mandat
-- au niveau racine de la ligne du registre, pour dériver le "Statut du Mandat"
-- (Actif / Clos / Échu) côté front et permettre tri/filtre serveur.

alter table public.app_mandat_register_current
add column if not exists mandat_date_cloture text;

-- Recrée la vue en select * pour qu'elle expose la nouvelle colonne
-- (Postgres fige la liste des colonnes à la création de la vue).
drop view if exists public.app_registre_mandats_current;

create view public.app_registre_mandats_current
with (security_invoker=on) as
select *
from public.app_mandat_register_current;

notify pgrst, 'reload schema';
