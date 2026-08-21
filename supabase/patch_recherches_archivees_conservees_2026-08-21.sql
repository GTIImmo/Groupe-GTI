-- =====================================================================
-- Les recherches archivees ne sont plus supprimees de Supabase
-- Date : 2026-08-21
-- Applique en prod via la migration `rapprochement_ignore_recherches_archivees`
--
-- LE PROBLEME. Supabase ne detenait que les recherches ACTIVES. Quand Hektor
-- archivait une recherche, sa ligne disparaissait -- et tout ce qui pointait sur
-- sa cle devenait orphelin : propositions, relances, retours acquereur, envois,
-- rapprochements. C'est la principale source des orphelins reparees le 20/08.
--
-- Et Hektor n'efface JAMAIS une recherche : meme le bouton "Supprimer" de l'app
-- appelle archiveHektorContactSearch -> modifDateArchiveCritere, qui pose une
-- date d'archivage (console_job_worker.js:11878-11890, :11918). L'archivage est
-- donc le cas NORMAL, pas l'exception.
--
-- LA REGLE RETENUE : delete-never, la meme que pour le registre d'affaires
-- (20/08). La ligne reste, marquee inactive. Sa cle reste vivante. Rien ne se
-- detache plus.
--
-- LE VERROU, indispensable et pose AVANT les donnees. Le moteur de rapprochement
-- ne filtrait pas les archivees : il aurait calcule des rapprochements -- donc des
-- alertes, donc des propositions -- pour 6 777 clients qui ne cherchent plus.
-- Probleme de JUSTESSE, pas de charge : mesure du 21/08, 42 ms par recherche
-- contre les 340 biens reellement evalues (statut Actif ET diffusable), soit
-- ~90 secondes etalees sur 85 minutes pour tout le rattrapage.
--
-- DEUX GESTES :
--   1. app_bulk_recompute_chunk ne score que les actives ;
--   2. app_trg_search_dirty n'enfile pas une ligne DEJA archivee (insertion de
--      rattrapage), mais laisse passer le PASSAGE actif -> archive, qui doit
--      nettoyer les rapprochements devenus sans objet.
--
-- EFFET SECONDAIRE VOULU : une recherche qui passe en archive est recalculee, ne
-- produit rien, et ses rapprochements sont supprimes proprement par le DELETE deja
-- present -- tandis que sa ligne, sa cle, ses propositions et ses relances RESTENT.
--
-- COTE PIPELINE, trois portes a ouvrir et non une (sinon le run de 03:00 et le
-- read-through resupprimaient chaque nuit ce que le run de 05:30 venait d'ecrire) :
--   scheduled/run_quotidien.ps1        -> -IncludeArchivedContactSearches
--   phase2/sync/sync_active_searches.py     -> --include-archived-searches
--   phase2/sync/refresh_contact_inproc.py   -> --include-archived-searches
--
-- ET UN PIEGE RENCONTRE EN DIRECT : --include-archived-searches ne portait pas le
-- perimetre des CONTACTS. Le premier rattrapage a pousse 72 869 recherches au lieu
-- des 6 777 voulues, dont 66 095 portees par des contacts absents de Supabase.
-- Le verrou a tenu (0 rapprochement, file vide), les 66 095 ont ete retirees, et
-- push_contacts_to_supabase.py fait desormais suivre aux recherches le perimetre
-- des contacts.
--
-- RESULTAT VERIFIE le 21/08 : 10 744 recherches (3 967 actives + 6 777 archivees),
-- 0 recherche sans contact, 0 rapprochement sur archivee, file d'attente vide.
-- Sentinelle `data.rapprochement_sur_archivee`, seuil 0.
-- =====================================================================

-- Corps complet des deux fonctions : voir la migration
-- `rapprochement_ignore_recherches_archivees`. Les deux differences avec l'etat
-- anterieur sont ci-dessous.

-- 1) Le declencheur ignore une ligne inseree deja archivee.
--    (Le cas UPDATE actif -> archive continue de passer : c'est lui qui nettoie.)
--
--    IF TG_OP='INSERT' AND NEW.is_active IS DISTINCT FROM true THEN RETURN NEW; END IF;

-- 2) Le moteur ne score que les actives.
--    /!\ p_limit garde son DEFAULT 250 : Postgres refuse de retirer un defaut
--        existant (« cannot remove parameter defaults from existing function »).
--
--    CREATE TEMP TABLE _sch ON COMMIT DROP AS
--    SELECT s.* FROM app_contact_search_current s
--    JOIN _chunk c ON c.search_key = s.contact_search_key
--    WHERE s.is_active IS NOT DISTINCT FROM true;      <-- LE VERROU

-- 3) La sentinelle.
create or replace view public.app_rapprochements_sur_recherche_archivee as
  select r.contact_search_key, r.hektor_contact_id, r.app_dossier_id, r.score, r.computed_at
    from public.app_rapprochement r
    join public.app_contact_search_current s on s.contact_search_key = r.contact_search_key
   where s.is_active is distinct from true;

-- --- Retour arriere ----------------------------------------------------
-- Retirer le verrou (revenir au JOIN sans WHERE), retirer les trois options du
-- pipeline, puis supprimer les archivees de Supabase :
--   delete from app_contact_search_current where not is_active;
-- Rien n'est perdu : le serveur local detient les 76 839 recherches, archivees
-- comprises, et les reecrit a chaque passage.
