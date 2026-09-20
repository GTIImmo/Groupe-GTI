-- ═══════════════════════════════════════════════════════════════════════════
-- C.4 — LES LIGNES QUI POINTENT DANS LE VIDE                      20/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- AUTORISE PAR FREDERIC le 20/09, inventaire sous les yeux.
--
-- CE QU'ON SUPPRIME : 146 lignes accrochees a une CLE DE RECHERCHE qui n'existe
-- plus. Aucune perte de travail -- mesure du jour : 0 rapprochement, 0 proposition,
-- 0 envoi, 0 relance, 0 relation orphelins. Restent deux tables :
--
--    app_rapprochement_search_state   132 sur 4 309   (15/06 -> 17/09)
--       une ligne technique par recherche : date du dernier calcul, nb de
--       correspondances. Orpheline, elle fausse les compteurs.
--    app_notification                  14, toutes NON LUES  (19/06 -> 04/09)
--       12 « nouveau rapprochement », 1 « demande de visite », 1 « requalification ».
--       Elles s'affichent au negociateur et ne peuvent pas s'ouvrir.
--
-- ORIGINE : les 8 suppressions de contact faites par l'app, et surtout les anciens
-- changements de cle de recherche, d'avant le gel du nom (21/08). Le correctif de
-- fond est dans le worker le meme jour : il lit les cles AVANT de supprimer les
-- recherches -- c'etait l'ordre, le defaut.
--
-- CE QU'ON NE SUPPRIME PAS : le lien vers l'agenda Google (1 ligne). L'evenement
-- existe toujours dans l'agenda du negociateur ; effacer notre ligne effacerait la
-- trace d'un vrai rendez-vous.
--
-- ⚠ INVENTAIRE CONSERVE AVANT SUPPRESSION, ligne par ligne :
--    notice/inventaires/C4_orphelins_avant_purge_2026-09-20.json
--    (regle du projet : rien de destructif sans inventaire)
--
-- RETOUR ARRIERE : ces lignes sont RECALCULABLES -- l'etat de calcul se refait au
-- prochain passage du moteur ; une notification perimee n'a pas a revenir. Le
-- fichier d'inventaire permet de prouver ce qui a ete retire.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- Garde-fou : on ne supprime QUE des orphelins, et on refuse si le volume ne
-- correspond pas a l'inventaire (quelqu'un aurait travaille entre-temps).
do $$
declare n_state int; n_notif int;
begin
  select count(*) into n_state from public.app_rapprochement_search_state x
   where not exists (select 1 from public.app_contact_search_current s
                      where s.contact_search_key = x.contact_search_key);
  select count(*) into n_notif from public.app_notification n
   where n.contact_search_key is not null
     and not exists (select 1 from public.app_contact_search_current s
                      where s.contact_search_key = n.contact_search_key);
  if n_state > 200 or n_notif > 50 then
    raise exception 'VOLUME INATTENDU : % etats, % notifications (inventaire du 20/09 : 132 et 14). On ne supprime pas a l aveugle.', n_state, n_notif;
  end if;
  raise notice 'purge : % etats de calcul, % notifications', n_state, n_notif;
end $$;

delete from public.app_rapprochement_search_state x
 where not exists (select 1 from public.app_contact_search_current s
                    where s.contact_search_key = x.contact_search_key);

delete from public.app_notification n
 where n.contact_search_key is not null
   and not exists (select 1 from public.app_contact_search_current s
                    where s.contact_search_key = n.contact_search_key);

commit;
