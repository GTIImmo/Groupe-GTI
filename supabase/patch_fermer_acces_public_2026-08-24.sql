-- =====================================================================
-- Fermer l'acces public -- taches 0.4, 0.5 et 0.6 du plan
-- Date : 2026-08-24
-- Appliquee en prod via la migration `fermer_acces_public_vues_et_tables_surveillance`
--
-- CE QUI A ETE CONSTATE, en vrai et non deduit d'un avertissement de linter.
-- La cle ANONYME du front -- celle qui est compilee dans /assets/index-*.js, donc lisible
-- par n'importe quel visiteur avec F12 -- pouvait lire app_dossiers_current :
--
--    13 210 annonces, 54 colonnes
--       10 510  adresses privees
--       12 488  noms de mandants        (les vendeurs, nommement)
--       13 098  villes privees
--        9 025  e-mails de negociateurs
--
-- La lecture a ete FAITE avec cette cle, et elle a repondu. A l'inverse
-- app_contact_current refusait correctement (HTTP 401) : c'est bien CETTE vue qui etait
-- ouverte, pas toute la base. Et la cle a ete retrouvee dans le bundle public deploye,
-- a la position 567 301 de /assets/index-CAw2IrlX.js.
--
-- ⚠ LA CLE PUBLIQUE N'EST PAS LE PROBLEME. Elle est FAITE pour etre publique : c'est le
-- principe de Supabase, toutes les applications de ce type en embarquent une. Le probleme
-- est ce qu'on l'autorise a lire.
--
-- ET CE N'ETAIT PAS QUE LA LECTURE -- decouvert en relevant les droits avant correction :
--    anon -> SELECT, INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES
-- Sur app_search_count_high_water, qui est une vraie TABLE sans RLS, cela signifie que
-- n'importe qui pouvait l'EFFACER. D'ou `revoke all` et non `revoke select`.
--
-- LE DETAIL DES TROIS GESTES
--   0.4  app_dossiers_current : tout retire a `anon`, `authenticated` conserve -- le front
--        lit apres connexion. SEUL geste portant un risque de casse, a verifier sur l'app.
--   0.5  les 5 vues de surveillance + app_search_count_high_water : posees les 20 et 21/08
--        SANS politique d'acces -- le trou est de moi. Verifie qu'AUCUNE n'est utilisee par
--        l'app : aucun fichier du front, du backend ou du worker ne les nomme. Seul le
--        moniteur les interroge, avec la cle de service. On retire donc les deux roles.
--   0.6  tmp_etape12_avant : table temporaire d'une migration, vide, ouverte a tous.
--
-- VERIFIE APRES APPLICATION :
--   les 8 objets repondent HTTP 401 a la cle publique (404 pour la table supprimee) ;
--   les 21 sondes du moniteur lisent toujours -- 0 critique, et
--   « Monitor results written to Supabase ». Aucune regression.
--
-- RETOUR ARRIERE, si le front perdait quelque chose :
--   grant select on public.app_dossiers_current to anon;
-- Les autres objets n'etant lus par personne, il n'y a rien a leur rendre.
--
-- RESTE OUVERT (tache 0.7, non mesuree) : 164 fonctions SECURITY DEFINER appelables par
-- `anon` et `authenticated`. Beaucoup sont sans doute legitimes -- ce sont les RPC que le
-- front appelle -- mais aucune n'a jamais ete revue. A auditer, pas a corriger en bloc.
-- =====================================================================

-- 0.4 ------------------------------------------------------------------
revoke all on public.app_dossiers_current from anon;

-- 0.5 ------------------------------------------------------------------
revoke all on public.app_recherches_disparues                  from anon, authenticated;
revoke all on public.app_recherches_sans_numero                from anon, authenticated;
revoke all on public.app_recherches_numero_en_double           from anon, authenticated;
revoke all on public.app_search_orphans_non_rattachables       from anon, authenticated;
revoke all on public.app_rapprochements_sur_recherche_archivee from anon, authenticated;
revoke all on public.app_search_count_high_water               from anon, authenticated;

-- Ceinture et bretelles sur la seule vraie TABLE du lot : RLS active sans politique, donc
-- plus personne n'y accede sauf `service_role`, qui la contourne par nature.
alter table public.app_search_count_high_water enable row level security;

-- 0.6 ------------------------------------------------------------------
drop table if exists public.tmp_etape12_avant;
