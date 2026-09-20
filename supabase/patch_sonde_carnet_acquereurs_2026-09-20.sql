-- ═══════════════════════════════════════════════════════════════════════════
-- LA SONDE DU CARNET DES ACQUEREURS                              20/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Frederic, 20/09 : « vu qu'il n'y a pas de test il faut au moins une sonde ».
--
-- CE QU'ELLE SURVEILLE. L'etape « phase2 contacts devenus acquereurs », posee
-- le meme jour en fin de run quotidien (d7a3586) : elle relit les fiches dont
-- la typologie vient de gagner « acquereur », et c'est le SEUL chemin par
-- lequel une recherche creee dans Hektor entre dans l'app.
--
-- POURQUOI UNE LIGNE EN BASE, ET PAS DU CODE. heartbeat.py fait un PATCH sur
-- app_worker_registry : sans ligne, il ne remonte RIEN, et sans erreur. C'est
-- le defaut C.17-ter -- 13 cles du run sont dans ce cas. L'etape etant NON
-- BLOQUANTE dans le run, son echec serait donc doublement invisible.
--
-- ⚠ status = 'active' ET PAS 'active_optional', et c'est le point de tout ce
--   patch : check_worker_heartbeat SAUTE les lignes dont le status n'est pas
--   'active' (monitoring/check_gti_health.py). Une etape optionnelle declaree
--   'active_optional' n'est jamais surveillee -- c'est le cas aujourd'hui de
--   supabase.push_contacts. Ici on veut l'inverse : l'etape peut echouer sans
--   arreter la nuit, mais on veut le SAVOIR.
--
-- LE SEUIL vient de la frequence : 'optional_pipeline_step' -> 50 h sans succes
-- avant alerte (WORKER_STALE_POLICY). L'etape tourne chaque nuit : deux nuits
-- muettes declenchent donc un avertissement, une seule ne reveille personne.
--
-- RETOUR ARRIERE :
--   DELETE FROM public.app_worker_registry WHERE worker_key = 'hektor.carnet_acquereurs';
-- ═══════════════════════════════════════════════════════════════════════════

INSERT INTO public.app_worker_registry (
    worker_key, worker_name, worker_role, worker_type, criticality, frequency,
    dependencies_json, status, owner, monitoring_domain, source_kind, source_notes,
    script_path, command_hint, expected_max_runtime_minutes
) VALUES (
    'hektor.carnet_acquereurs',
    'Contacts devenus acquereurs',
    'Relit les fiches dont la typologie a gagne « acquereur » : Hektor la pose lui-meme quand une recherche est enregistree, c''est ainsi qu''une recherche creee dans Hektor entre dans l''app.',
    'python_worker',
    'medium',
    'optional_pipeline_step',
    '["phase1.sync_raw", "supabase.push_contacts"]'::jsonb,
    'active',
    'frederic',
    'business',
    'static_analysis',
    'Pose le 20/09/2026 avec l''etape du meme nom (d7a3586). Le carnet est rempli par normalize_source, consomme par phase2/sync/sync_active_searches.py --carnet-seul en fin de run quotidien, et repris par le run de 03:00 en filet.',
    'phase2/sync/sync_active_searches.py',
    '.venv\Scripts\python.exe phase2\sync\sync_active_searches.py --carnet-seul',
    15
)
ON CONFLICT (worker_key) DO UPDATE SET
    worker_name = EXCLUDED.worker_name,
    worker_role = EXCLUDED.worker_role,
    criticality = EXCLUDED.criticality,
    frequency = EXCLUDED.frequency,
    status = EXCLUDED.status,
    monitoring_domain = EXCLUDED.monitoring_domain,
    source_notes = EXCLUDED.source_notes,
    script_path = EXCLUDED.script_path,
    command_hint = EXCLUDED.command_hint,
    expected_max_runtime_minutes = EXCLUDED.expected_max_runtime_minutes,
    updated_at = now();
