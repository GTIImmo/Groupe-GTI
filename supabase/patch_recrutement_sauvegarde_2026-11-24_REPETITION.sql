-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — RECRUTEMENT R6.8 (la sauvegarde quotidienne)                                 24/11/2026
-- Rejoue le patch dans une transaction, vérifie, puis LÈVE VOLONTAIREMENT UNE EXCEPTION à la fin : tout est
-- annulé, quoi qu'il arrive (même si l'outil qui colle valide seul). Le message attendu commence par
-- « RÉPÉTITION VERTE ». Tout autre message = un contrôle rouge, et rien n'a été écrit non plus.
-- ⛔ Ce fichier ne contient AUCUN commit.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- l'état d'avant, pour le témoin
CREATE TEMP TABLE rep_avant ON COMMIT DROP AS
SELECT (SELECT count(*) FROM public.app_worker_registry) AS lignes_registre,
       (SELECT count(*) FROM pg_policies WHERE schemaname = 'recrutement') AS regles,
       has_table_privilege('recrutement_robot', 'recrutement.suivi', 'SELECT') AS robot_lisait_suivi;

grant select on recrutement.suivi, recrutement.evenement, recrutement.retrait to recrutement_robot;
create policy robot_suivi_lecture     on recrutement.suivi     for select to recrutement_robot using (true);
create policy robot_evenement_lecture on recrutement.evenement for select to recrutement_robot using (true);
create policy robot_retrait_lecture   on recrutement.retrait   for select to recrutement_robot using (true);
insert into public.app_worker_registry
    (worker_key, worker_name, worker_role, worker_type, criticality, frequency, status,
     script_path, expected_max_runtime_minutes, monitoring_domain, source_notes)
values
    ('recrutement.sauvegarde_quotidienne', 'Recrutement : la sauvegarde quotidienne de l''app', 'répétition',
     'python_worker', 'medium', 'scheduled_or_manual', 'active', 'recrutement\sauvegarder_app.py', 5, 'business', 'répétition');

DO $$
DECLARE
  t text;
  n integer := 0;
  a record;
BEGIN
  SELECT * INTO a FROM rep_avant;
  -- 1. le témoin d'avant : le robot NE lisait PAS le suivi
  IF a.robot_lisait_suivi THEN RAISE EXCEPTION 'ROUGE 1 : le robot lisait déjà le suivi avant le patch'; END IF;
  n := n + 1;
  FOREACH t IN ARRAY array['recrutement.suivi', 'recrutement.evenement', 'recrutement.retrait'] LOOP
    -- 2. il lit
    IF NOT has_table_privilege('recrutement_robot', t, 'SELECT') THEN RAISE EXCEPTION 'ROUGE 2 : le robot ne lit pas %', t; END IF;
    -- 3. il n'écrit pas
    IF has_table_privilege('recrutement_robot', t, 'INSERT') OR has_table_privilege('recrutement_robot', t, 'UPDATE')
       OR has_table_privilege('recrutement_robot', t, 'DELETE') THEN RAISE EXCEPTION 'ROUGE 3 : le robot pourrait écrire dans %', t; END IF;
    -- 4. l'API ne lit toujours pas
    IF has_table_privilege('authenticated', t, 'SELECT') OR has_table_privilege('anon', t, 'SELECT') THEN
      RAISE EXCEPTION 'ROUGE 4 : % lisible par l''API', t; END IF;
  END LOOP;
  n := n + 3;
  -- 5. trois règles de plus, toutes en lecture, toutes pour le robot seul
  IF (SELECT count(*) FROM pg_policies WHERE schemaname = 'recrutement') <> a.regles + 3 THEN RAISE EXCEPTION 'ROUGE 5 : pas exactement 3 règles neuves'; END IF;
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'recrutement' AND policyname LIKE 'robot\_%\_lecture'
               AND (cmd <> 'SELECT' OR roles <> '{recrutement_robot}')) THEN RAISE EXCEPTION 'ROUGE 5 : une règle neuve n''est pas « lecture, robot seul »'; END IF;
  n := n + 1;
  -- 6. une seule ligne de registre de plus
  IF (SELECT count(*) FROM public.app_worker_registry) <> a.lignes_registre + 1 THEN RAISE EXCEPTION 'ROUGE 6 : le registre n''a pas pris exactement une ligne'; END IF;
  n := n + 1;
  -- 7. la fréquence est connue de la surveillance (28 h) : pas une fréquence neuve qui crierait au retard
  IF (SELECT frequency FROM public.app_worker_registry WHERE worker_key = 'recrutement.sauvegarde_quotidienne') <> 'scheduled_or_manual' THEN
    RAISE EXCEPTION 'ROUGE 7 : fréquence inattendue'; END IF;
  n := n + 1;
  -- 8. les droits de R3 du robot sont intacts
  IF NOT has_table_privilege('recrutement_robot', 'recrutement.fiche', 'INSERT')
     OR NOT has_table_privilege('recrutement_robot', 'recrutement.liste_noire', 'SELECT')
     OR has_table_privilege('recrutement_robot', 'recrutement.liste_noire', 'INSERT') THEN RAISE EXCEPTION 'ROUGE 8 : les droits de R3 ont bougé'; END IF;
  n := n + 1;
  RAISE EXCEPTION 'RÉPÉTITION VERTE : % contrôles sur 8 (tout est annulé, rien n''a été écrit)', n;
END $$;

ROLLBACK;
