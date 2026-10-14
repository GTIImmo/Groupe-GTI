-- =============================================================================
--  ENREGISTRER LA CLE DE SURVEILLANCE DU MENAGE DES ORPHELINS   14/10/2026
--  (version 2 -- la premiere a echoue, voir « MA PREMIERE VERSION » plus bas)
-- =============================================================================
--  POURQUOI CE PATCH EXISTE.
--  Le run appelle desormais `phase2/sync/menage_orphelins_recherche.py` avec
--  -WorkerKey "phase2.menage_orphelins_recherche". Sans ligne de registre, ce
--  battement PARTIRAIT DANS LE VIDE *ET COMPTERAIT POUR UN SUCCES* :
--  monitoring/heartbeat.py ecrit en PATCH FILTRE, une cle sans ligne touche
--  0 ligne, recoit 204, et `200 <= status < 300` compte un succes. C'est le
--  defaut 4j, trouve et repare le 13/10 pour 23 autres etapes -- on ne va pas
--  le refabriquer le lendemain.
--
--  ⚠ MA PREMIERE VERSION A ECHOUE, ET LA LECON VAUT D'ETRE ECRITE.
--    Elle enumerait 11 colonnes, recopiees d'un SELECT qui n'en montrait que 8.
--    Resultat : « null value in column "worker_role" violates not-null
--    constraint ». La table a SIX colonnes obligatoires sans valeur par defaut
--    (worker_key, worker_name, worker_role, worker_type, criticality,
--    script_path) et j'en avais vu cinq.
--    ➡ ON NE RECOPIE PLUS UNE LISTE DE COLONNES : on PART D'UNE LIGNE QUI
--      EXISTE DEJA et on ne remplace que ce qui doit changer. Ainsi aucune
--      colonne obligatoire ne peut manquer -- aujourd'hui ni le jour ou la
--      table en gagnera une nouvelle.
--    (Meme patron `to_jsonb` que le chantier ② : on manipule la ligne comme un
--     objet, sans jamais la retranscrire.)
--
--  LE PATRON COPIE est `phase2.repose_cloture_mandat`, posee le 13/10 pour
--  exactement le meme usage : une etape OPTIONNELLE et NON BLOQUANTE du run.
--
--  A COLLER UNE SEULE FOIS. L'editeur Supabase n'affiche pas les NOTICE : il
--  ecrit seulement « Success. No rows returned ». Si la cle existe deja, le
--  patch ne fait rien.
-- =============================================================================

DO $$
DECLARE
  v_patron CONSTANT text := 'phase2.repose_cloture_mandat';
  v_cle    CONSTANT text := 'phase2.menage_orphelins_recherche';
BEGIN
  IF EXISTS (SELECT 1 FROM public.app_worker_registry WHERE worker_key = v_cle) THEN
    RAISE NOTICE 'DEJA POSE : % existe. Rien a faire.', v_cle;
    RETURN;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM public.app_worker_registry WHERE worker_key = v_patron) THEN
    RAISE EXCEPTION 'STOP : le patron % est introuvable', v_patron;
  END IF;

  -- On part de la ligne du patron, on remplace les champs qui nous sont
  -- propres, et on remet le tout en ligne. Les colonnes qu'on ne nomme pas
  -- gardent la valeur du patron : rien ne peut etre oublie.
  INSERT INTO public.app_worker_registry
  SELECT (jsonb_populate_record(
            NULL::public.app_worker_registry,
            to_jsonb(r) || jsonb_build_object(
              'worker_key',   v_cle,
              'worker_name',  'Menage des orphelins de recherche',
              'worker_role',  'Appelle app_sweep_search_orphans() JUSTE APRES le push des '
                              || 'contacts, pour rattacher les rapprochements, scores, '
                              || 'notifications et relances dont la recherche a disparu. '
                              || 'Supprime la course avec le cron Supabase « 0 5 * * * » '
                              || '(07:00 locale), qui passait 48 secondes AVANT le push '
                              || '(07:00:48). Le cron reste en place : filet si le run '
                              || 'echoue avant cette etape.',
              'worker_type',  'python_worker',
              'script_path',  'phase2/sync/menage_orphelins_recherche.py',
              'command_hint', 'python phase2/sync/menage_orphelins_recherche.py',
              'source_notes', 'Pose le 14/10/2026, chantier des recherches orphelines.',
              'expected_max_runtime_minutes', 5,
              -- une ligne neuve ne doit pas heriter de l'historique du patron
              'last_run_at',    NULL,
              'last_success_at', NULL,
              'last_status',     NULL,
              'last_duration_ms', NULL,
              'last_error',       NULL,
              'last_run_host',    NULL
            )
          )).*
    FROM public.app_worker_registry r
   WHERE r.worker_key = v_patron;

  RAISE NOTICE 'POSE : % est enregistree.', v_cle;
END $$;

-- Controle : la ligne doit exister, avec worker_role rempli.
SELECT worker_key, worker_name, worker_type, criticality, frequency, status,
       monitoring_domain, script_path,
       left(worker_role, 60) || '…' AS worker_role_debut,
       last_success_at
  FROM public.app_worker_registry
 WHERE worker_key = 'phase2.menage_orphelins_recherche';
