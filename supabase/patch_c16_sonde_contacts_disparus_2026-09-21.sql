insert into public.app_worker_registry (
    worker_key, worker_name, worker_role, worker_type, criticality, frequency,
    dependencies_json, status, owner, monitoring_domain, source_kind, source_notes,
    script_path, expected_max_runtime_minutes
) values (
    'phase2.contacts_disparus', 'Marquer les contacts disparus de Hektor',
    'Pose absent_depuis sur les fiches dont Hektor repond 404. On ne supprime jamais : effacer orphelinerait les 18 tables qui pointent le contact.',
    'python_worker', 'medium', 'optional_pipeline_step', '["phase2.registre_contacts"]'::jsonb,
    'active', 'frederic', 'business', 'static_analysis',
    'C.16 21/09/2026. Mesure du jour : 7 659 fiches inconnues de Hektor, 2 205 actives cote serveur, mais UNE SEULE encore active dans l''app -- le « 825 » du plan a vieilli.',
    'phase2/identite/marquer_contacts_disparus.py', 10
) on conflict (worker_key) do update set source_notes = excluded.source_notes, updated_at = now();
