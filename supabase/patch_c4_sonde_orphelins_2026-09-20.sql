-- ═══════════════════════════════════════════════════════════════════════════
-- C.4 — LA SONDE DES LIGNES QUI POINTENT DANS LE VIDE             20/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Regle du projet, apprise le 21/08 : « une reparation qui ne dit pas ce qu'elle
-- repare ne se surveille pas ». On vient de purger 146 orphelins et de corriger
-- leur cause dans le worker -- sans sonde, on ne saurait pas si ca se reconstitue.
--
-- CE QU'ELLE COMPTE : toute ligne accrochee a une CLE DE RECHERCHE qui n'existe
-- plus dans app_contact_search_current. Une vue, parce que le moniteur interroge
-- par l'API REST et ne sait pas faire de jointure.
--
-- ⚠ ELLE NE COMPTE PAS le lien agenda Google : son evenement existe toujours
--   dans l'agenda du negociateur, sa ligne est gardee DELIBEREMENT.
--
-- SEUIL : 0. Toute remontee est anormale, et nommera la table fautive.
--
-- RETOUR ARRIERE : drop view public.app_v_orphelins_recherche;
-- ═══════════════════════════════════════════════════════════════════════════

create or replace view public.app_v_orphelins_recherche as
  select 'app_rapprochement'               as table_orpheline, x.contact_search_key
    from public.app_rapprochement x
   where not exists (select 1 from public.app_contact_search_current s
                      where s.contact_search_key = x.contact_search_key)
  union all
  select 'app_rapprochement_score_history', x.contact_search_key
    from public.app_rapprochement_score_history x
   where not exists (select 1 from public.app_contact_search_current s
                      where s.contact_search_key = x.contact_search_key)
  union all
  select 'app_rapprochement_search_state', x.contact_search_key
    from public.app_rapprochement_search_state x
   where not exists (select 1 from public.app_contact_search_current s
                      where s.contact_search_key = x.contact_search_key)
  union all
  select 'app_relance_rapprochement', x.contact_search_key
    from public.app_relance_rapprochement x
   where not exists (select 1 from public.app_contact_search_current s
                      where s.contact_search_key = x.contact_search_key)
  union all
  select 'app_notification', n.contact_search_key
    from public.app_notification n
   where n.contact_search_key is not null
     and not exists (select 1 from public.app_contact_search_current s
                      where s.contact_search_key = n.contact_search_key);

comment on view public.app_v_orphelins_recherche is
  'C.4 20/09/2026 : lignes accrochees a une cle de recherche disparue. Seuil de la sonde data.orphelins_recherche : 0.';

grant select on public.app_v_orphelins_recherche to service_role, authenticated;
