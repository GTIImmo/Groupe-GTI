-- =============================================================================
--  ENREGISTRER LA CLE DE SURVEILLANCE DU MENAGE DES ORPHELINS   14/10/2026
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
--  LE PATRON EST RECOPIE de `phase2.repose_cloture_mandat`, posee le 13/10 pour
--  exactement le meme usage : une etape OPTIONNELLE et NON BLOQUANTE du run.
--
--  A COLLER UNE SEULE FOIS. Si l'empreinte est refusee, c'est qu'il est deja
--  passe -- l'editeur Supabase n'affiche pas les NOTICE, il ecrit seulement
--  « Success. No rows returned ».
-- =============================================================================

DO $$
DECLARE
  v_existe boolean;
BEGIN
  SELECT EXISTS (SELECT 1 FROM public.app_worker_registry
                  WHERE worker_key = 'phase2.menage_orphelins_recherche')
    INTO v_existe;

  IF v_existe THEN
    RAISE NOTICE 'DEJA POSE : la cle phase2.menage_orphelins_recherche existe. Rien a faire.';
    RETURN;
  END IF;

  -- Garde-fou : on refuse de poser la ligne si le patron dont on s'inspire a
  -- disparu -- cela voudrait dire que la table a change de forme sous nos pieds.
  IF NOT EXISTS (SELECT 1 FROM public.app_worker_registry
                  WHERE worker_key = 'phase2.repose_cloture_mandat') THEN
    RAISE EXCEPTION 'STOP : le patron phase2.repose_cloture_mandat est introuvable';
  END IF;

  INSERT INTO public.app_worker_registry (
    worker_key, worker_name, worker_type, criticality, frequency,
    status, monitoring_domain, source_kind, source_notes, script_path, command_hint
  ) VALUES (
    'phase2.menage_orphelins_recherche',
    'Menage des orphelins de recherche',
    'python_worker',
    'medium',
    'optional_pipeline_step',
    'active_optional',
    'business',
    'static_analysis',
    'Pose le 14/10/2026. Appelle app_sweep_search_orphans() JUSTE APRES le push '
    || 'des contacts, pour supprimer la course avec le cron Supabase « 0 5 * * * » '
    || '(07:00 locale) qui passait 48 secondes AVANT le push (07:00:48). '
    || 'Le cron reste en place : filet de securite si le run echoue avant.',
    'phase2/sync/menage_orphelins_recherche.py',
    'python phase2/sync/menage_orphelins_recherche.py'
  );

  RAISE NOTICE 'POSE : phase2.menage_orphelins_recherche est enregistree.';
END $$;

-- Controle : la ligne doit exister, et une seule.
SELECT worker_key, worker_name, status, monitoring_domain, script_path
  FROM public.app_worker_registry
 WHERE worker_key = 'phase2.menage_orphelins_recherche';
