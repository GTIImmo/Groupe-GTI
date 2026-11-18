-- ═══════════════════════════════════════════════════════════════════════════════
-- DIRE A UN LOT DE LAISSER UNE LIGNE DU CLASSEUR TRANQUILLE          18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- POURQUOI. Le 18/11, Frederic a tranche « A » sur 43091 : l'offre et le compromis
-- repartent sur la ligne CHAPUIS, et la ligne GIBERT (53ZS73KW) reste SANS affaire.
-- ⛔ Mais les lots du classeur ecartent une ligne « quand un role est DEJA relie ».
--   Sans role, GIBERT redevient CANDIDATE, et son etat « Annulée » la ferait entrer
--   dans « offres annulees » ET « compromis annules » : un lot rejoue CREERAIT
--   l'affaire que Frederic a refuse de creer.
--
-- ⭐ LE PROJET N'AVAIT AUCUN MECANISME POUR CA (cherche le 18/11 dans phase2/ et
--   supabase/ : rien). Une exclusion se DECLARE, elle ne se retient pas de tete.
--
-- ⛔⛔ ET CETTE TABLE NE SERT A RIEN SEULE. Elle est branchee DANS LA MEME SEANCE
--   sur la seule porte qui cree des transactions depuis le classeur,
--   phase2/checks/poser_offres_annulees_classeur_2026-11-16.py. Une table posee
--   sans lecteur est un mecanisme installe a moitie -- le projet en a deja paye un.
--
-- RETOUR ARRIERE : ..._INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

create table if not exists public.app_classeur_ligne_exclue (
  id_unique       text primary key,
  ligne_classeur  integer,
  pourquoi        text not null,
  decide_le       timestamptz not null default now(),
  decide_par      text not null
);

comment on table public.app_classeur_ligne_exclue is
  'Les lignes du classeur qu''AUCUN lot ne doit transformer en transaction. '
  'Lue par poser_offres_annulees_classeur_2026-11-16.py, qui NOMME ce qu''il ecarte.';

-- ⛔ Personne ne lit cette table par l'API : RLS sans policy = service_role seul.
--   `revoke ... from public` NE FERME PAS `authenticated` -- c'est RLS qui ferme.
alter table public.app_classeur_ligne_exclue enable row level security;

insert into public.app_classeur_ligne_exclue
  (id_unique, ligne_classeur, pourquoi, decide_par)
values
  ('53ZS73KW', 227,
   'Dossier GIBERT 2024 du mandat 16992, annule au Sheet le 16/07/2025. Il n''existe '
   'plus chez Hektor, et le 18/11 Frederic a choisi « A » : ses deux liens repartent '
   'sur la ligne CHAPUIS (bdb548a3), et on NE CREE PAS l''affaire GIBERT.',
   'decision du 18/11/2026')
on conflict (id_unique) do nothing;

do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_ligne_exclue where id_unique='53ZS73KW';
  if n <> 1 then raise exception '⛔ l''exclusion n''est pas posee (% ligne)', n; end if;
  raise notice '✅ table posee, 53ZS73KW declaree exclue -- reste a la BRANCHER';
end $$;

commit;
