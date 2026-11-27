-- ═══════════════════════════════════════════════════════════════════════════
-- RECRUTEMENT R6.8 (R5 bis) — LA SAUVEGARDE QUOTIDIENNE DE CE QUE L'APP ÉCRIT              24/11/2026
-- Chantier à part : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md, §13 (R5 bis) et §14 (R6.8).
-- Suppose R3 et R6 posés. Répétition : _REPETITION.sql ; retour : _INVERSE.sql.
--
-- POURQUOI : depuis l'écran (R6), l'app écrit chaque jour dans le schéma « recrutement » (suivi, fil,
--   retraits, corrections, liste « ne plus contacter », fiches ajoutées à la main). La sauvegarde de nuit
--   (« GTI Sauvegarde ») ne copie que le schéma public, et la sauvegarde du recrutement ne passe que tous les
--   deux mois. La tâche « GTI Recrutement Sauvegarde » (recrutement/sauvegarder_app.py) en fait une copie
--   datée chaque jour, par le ROBOT.
--
-- CE QUE POSE CE PATCH (et rien d'autre) :
--   1. le robot peut LIRE le suivi, le fil et les retraits (il ne peut toujours RIEN y écrire) ;
--   2. la ligne de battement « recrutement.sauvegarde_quotidienne » (fréquence scheduled_or_manual = 28 h).
-- ⛔ RIEN N'EST ÉCRIT CHEZ HEKTOR. authenticated et anon n'ont toujours AUCUN accès direct à ces tables.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $$
BEGIN
  IF to_regclass('recrutement.suivi') IS NULL THEN
    RAISE EXCEPTION 'le patch de l''écran (R6) n''est pas posé : rien n''a été fait';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'recrutement' AND policyname = 'robot_suivi_lecture')
     OR EXISTS (SELECT 1 FROM public.app_worker_registry WHERE worker_key = 'recrutement.sauvegarde_quotidienne') THEN
    RAISE EXCEPTION 'patch déjà posé ? (rien n''a été fait)';
  END IF;
END $$;

-- 1. LIRE, ET SEULEMENT LIRE
grant select on recrutement.suivi, recrutement.evenement, recrutement.retrait to recrutement_robot;
create policy robot_suivi_lecture     on recrutement.suivi     for select to recrutement_robot using (true);
create policy robot_evenement_lecture on recrutement.evenement for select to recrutement_robot using (true);
create policy robot_retrait_lecture   on recrutement.retrait   for select to recrutement_robot using (true);

-- 2. LE BATTEMENT DE LA TÂCHE QUOTIDIENNE
insert into public.app_worker_registry
    (worker_key, worker_name, worker_role, worker_type, criticality, frequency, status,
     script_path, expected_max_runtime_minutes, monitoring_domain, source_notes)
values
    ('recrutement.sauvegarde_quotidienne', 'Recrutement : la sauvegarde quotidienne de l''app',
     'Chaque jour : ramène la liste « ne plus contacter » et les corrections en local (un effacement demandé dans l''app est appliqué le jour même), puis copie datée et relue de ce que l''app écrit (suivi, fil, retraits, corrections, liste, fiches ajoutées à la main, agences). 90 copies gardées.',
     'python_worker', 'medium', 'scheduled_or_manual', 'active', 'recrutement\sauvegarder_app.py', 5, 'business',
     'Ajoutée le 24/11/2026 (chantier recrutement, R6.8 = R5 bis). Aucune requête chez Hektor.');

-- LE CONTRÔLE, AVANT DE VALIDER (une exception annule tout)
DO $$
DECLARE
  t text;
BEGIN
  FOREACH t IN ARRAY array['recrutement.suivi', 'recrutement.evenement', 'recrutement.retrait'] LOOP
    IF NOT has_table_privilege('recrutement_robot', t, 'SELECT') THEN
      RAISE EXCEPTION 'le robot ne peut pas lire % : rien n''a été fait', t;
    END IF;
    IF has_table_privilege('recrutement_robot', t, 'INSERT') OR has_table_privilege('recrutement_robot', t, 'UPDATE')
       OR has_table_privilege('recrutement_robot', t, 'DELETE') THEN
      RAISE EXCEPTION 'le robot pourrait ÉCRIRE dans % : rien n''a été fait', t;
    END IF;
    IF has_table_privilege('authenticated', t, 'SELECT') OR has_table_privilege('anon', t, 'SELECT') THEN
      RAISE EXCEPTION '% serait lisible par l''API : rien n''a été fait', t;
    END IF;
  END LOOP;
  IF (SELECT count(*) FROM pg_policies WHERE schemaname = 'recrutement' AND policyname LIKE 'robot\_%\_lecture') <> 3 THEN
    RAISE EXCEPTION 'il manque une règle de lecture du robot : rien n''a été fait';
  END IF;
END $$;

COMMIT;
