-- ═══════════════════════════════════════════════════════════════════════════
-- INVERSE — RECRUTEMENT R6.8 (la sauvegarde quotidienne)                                    24/11/2026
-- Retire ce que patch_recrutement_sauvegarde_2026-11-24.sql a posé : la lecture du suivi, du fil et des retraits
-- par le robot, et la ligne de battement « recrutement.sauvegarde_quotidienne ». Ne touche à rien d'autre.
-- ⚠ Arrêter d'abord la tâche « GTI Recrutement Sauvegarde » : sans ce droit, elle tombera chaque jour.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

drop policy if exists robot_suivi_lecture     on recrutement.suivi;
drop policy if exists robot_evenement_lecture on recrutement.evenement;
drop policy if exists robot_retrait_lecture   on recrutement.retrait;
revoke select on recrutement.suivi, recrutement.evenement, recrutement.retrait from recrutement_robot;
delete from public.app_worker_registry where worker_key = 'recrutement.sauvegarde_quotidienne';

-- Le retour arrière ne juge que SA part : plus de lecture par le robot, et ses autres droits intacts.
DO $$
BEGIN
  IF has_table_privilege('recrutement_robot', 'recrutement.suivi', 'SELECT')
     OR has_table_privilege('recrutement_robot', 'recrutement.evenement', 'SELECT')
     OR has_table_privilege('recrutement_robot', 'recrutement.retrait', 'SELECT') THEN
    RAISE EXCEPTION 'le robot lit encore le suivi, le fil ou les retraits';
  END IF;
  IF NOT has_table_privilege('recrutement_robot', 'recrutement.liste_noire', 'SELECT')
     OR NOT has_table_privilege('recrutement_robot', 'recrutement.fiche', 'INSERT') THEN
    RAISE EXCEPTION 'les droits de R3 du robot ont été touchés : ils ne devaient pas l''être';
  END IF;
  IF EXISTS (SELECT 1 FROM public.app_worker_registry WHERE worker_key = 'recrutement.sauvegarde_quotidienne') THEN
    RAISE EXCEPTION 'la ligne de battement est toujours là';
  END IF;
END $$;

COMMIT;
