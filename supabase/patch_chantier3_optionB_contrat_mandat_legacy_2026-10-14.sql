-- =====================================================================
-- CHANTIER ③ -- OPTION B : LES DEUX ETAPES DU CONTRAT DE MANDAT PASSENT EN « legacy »
-- Date : 2026-10-14 · Decision de Frederic : « fais le Bloc 1 B »
-- Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md, « AUDIT DU 14/10 »
--
-- POURQUOI. Les deux etapes « phase2 magasin des champs de mandat » et « phase2 appliquer
-- le contrat de mandat » sont RETIREES DU RUN le meme jour (run_full_pipeline.ps1, laissees
-- en commentaire).
-- ⚠ CORRIGE LE 14/10 (question de Frederic : « ca va pas casser quelque chose ? »).
--   ▸ Elles n'atteignaient plus le REGISTRE depuis le 30/09 : sa date de cloture se lit dans
--     le mandat de la FICHE DETAIL, jamais dans la colonne qu'elles posaient.
--   ▸ Mais leur colonne alimente bien la FICHE DETAIL du dossier (detail_payload_json, une
--     colonne TEXTE -- d'abord manquee, la recherche ne regardait que les colonnes jsonb).
--     Mesure : AUCUNE de leurs 8 valeurs n'y arrivait -- 7 biens sans fiche detail, et le 8e
--     (62774) voit sa ligne refaite depuis Hektor a chaque geste. Les 4 fiches qui portent
--     une vraie date l'ont recue de Hektor.
--   ▸ Un seul ecran lit cette fiche : « Mandat source », qui doit montrer Hektor (decision
--     du 13/10). Tous les autres lisent le registre.
--   ➡ Ce que le patch FAIT est inchange ; seul ce qu'il DIT a ete corrige.
--
-- ⚠ CE PATCH EST LA MOITIE OBLIGATOIRE DU GESTE. Les deux etapes portaient un -WorkerKey,
--   inscrit au registre de surveillance le 13/10 (chantier ④, 4j). Retirees du run SANS ce
--   patch, leurs battements vieilliraient, et check_worker_heartbeat (qui ne regarde que les
--   lignes `active`) alerterait CHAQUE JOUR.
--   ➡ A COLLER AUJOURD'HUI -- avant le run de demain 05:00 de preference, et en tout cas
--     avant le moniteur de demain matin.
--
-- POURQUOI `legacy` ET PAS `disabled`. C'est l'usage deja en place dans ce registre :
--   `legacy` = « present dans le code mais le flux principal ne l'utilise plus »
--   (phase1.safe_runner, phase1.safe_worker). C'est exactement le cas : les deux scripts sont
--   GARDES dans phase2/identite/, seules leurs etapes quittent le run.
--   ⚠ Mesure du 14/10 : les DEUX sondes du moniteur qui lisent ce registre restent muettes
--     sur une ligne `legacy` -- la sonde des battements ecarte tout ce qui n'est pas
--     `active` (check_gti_health.py l. 1381), la sonde de comptage ne fait que compter et
--     repond toujours « ok » (l. 1313-1343).
--
-- CE QUI NE CHANGE PAS : aucune autre ligne du registre · aucune table · aucune fonction ·
-- les colonnes du registre des mandats · le carnet · la re-pose (phase2.repose_cloture_mandat,
-- qui reste `active`).
--
-- RETOUR ARRIERE : supabase/patch_chantier3_optionB_contrat_mandat_legacy_2026-10-14_INVERSE.sql
--   (et decommenter les six lignes dans run_full_pipeline.ps1)
-- REPETITION     : supabase/patch_chantier3_optionB_contrat_mandat_legacy_2026-10-14_REPETITION.sql
-- ⚠ NE LE COLLER QU'UNE SEULE FOIS (le succes est un NOTICE, invisible dans l'editeur).
-- =====================================================================

BEGIN;

-- ① La garde : on ne touche que si les deux lignes sont EXACTEMENT dans l'etat mesure.
DO $garde$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.app_worker_registry
   WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
     AND status = 'active'
     AND position('[[RETIREE DU RUN 14/10/2026]]' in coalesce(source_notes, '')) = 0;
  IF n <> 2 THEN
    RAISE EXCEPTION 'STOP : % inscription(s) dans l''etat attendu au lieu de 2 -- deja applique, ou le registre a change', n;
  END IF;
END $garde$;

-- ② Le geste. La note est AJOUTEE derriere un marqueur fixe : l'inverse la retire au
--    caractere pres, sans avoir a recopier l'ancienne.
UPDATE public.app_worker_registry
   SET status       = 'legacy',
       source_notes = coalesce(source_notes, '')
                      || ' [[RETIREE DU RUN 14/10/2026]] Decision de Frederic (chantier 3, option B) : '
                      || 'l''etape ne servait plus : le registre lit la fiche detail depuis le 30/09, et aucune de ses '
                      || 'valeurs n''arrivait a l''ecran (mesure du 14/10). '
                      || 'Le script est garde ; la date de l''app vit dans le carnet et mandat_date_cloture_app, '
                      || 'reposee par phase2.repose_cloture_mandat.',
       updated_at   = now()
 WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
   AND status = 'active';

-- ③ Le controle de sortie.
DO $ctrl$
DECLARE n_legacy int; n_vues int; n_autres_actives int;
BEGIN
  SELECT count(*) INTO n_legacy FROM public.app_worker_registry
   WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat') AND status = 'legacy';
  IF n_legacy <> 2 THEN RAISE EXCEPTION 'STOP : % ligne(s) en legacy au lieu de 2', n_legacy; END IF;

  -- Ce que la sonde des battements regardera desormais : (status or 'active') = 'active'.
  SELECT count(*) INTO n_vues FROM public.app_worker_registry
   WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
     AND coalesce(status, 'active') = 'active';
  IF n_vues <> 0 THEN RAISE EXCEPTION 'STOP : la sonde des battements verrait encore % ligne(s)', n_vues; END IF;

  -- La re-pose, elle, doit rester surveillee.
  SELECT count(*) INTO n_autres_actives FROM public.app_worker_registry
   WHERE worker_key = 'phase2.repose_cloture_mandat' AND status = 'active';
  IF n_autres_actives <> 1 THEN RAISE EXCEPTION 'STOP : la re-pose n''est plus active'; END IF;

  RAISE NOTICE 'OK : 2 inscriptions en legacy, la sonde des battements ne les voit plus, la re-pose reste active.';
END $ctrl$;

COMMIT;
