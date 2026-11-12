-- 12/11/2026 -- Lot A « diffusion des vendus » : la diffusion d'un vendu arrive dans l'app.
--
-- Hektor diffusait encore 60 biens vendus (Etreproprio 60, Paper 60, Superimmo 9 ; 56 de
-- Firminy) et l'app n'en savait rien : l'index des vendus n'avait aucune colonne de portails
-- et l'ecran posait « aucun portail » en dur.
-- Remplies chaque nuit par push_upgrade_to_supabase.py (meme calcul que les actives).
--
-- ORDRE : CE PATCH D'ABORD, l'ecran ensuite (sa lecture demande ces colonnes ; sans elles la
-- liste des vendus tomberait). Le run, lui, a un filet (adapter_index_vendus_au_schema).
-- Retour arriere : patch_index_vendus_portails_2026-11-12_INVERSE.sql.

alter table public.app_historical_annonce_index_current
  add column if not exists nb_portails_actifs integer not null default 0,
  add column if not exists portails_resume text;

comment on column public.app_historical_annonce_index_current.portails_resume is
  'Portails ou Hektor diffuse encore ce vendu (cles de passerelle, separees par des virgules). 12/11/2026.';
