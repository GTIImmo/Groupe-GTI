insert into public.app_worker_registry (
    worker_key, worker_name, worker_role, worker_type, criticality, frequency,
    dependencies_json, status, owner, monitoring_domain, source_kind, source_notes,
    script_path, expected_max_runtime_minutes
) values (
    'phase2.reappliquer_saisies',
    'Reappliquer les saisies de l''app',
    'Repose, apres le push, les champs saisis dans l''app que Hektor n''a pas encore confirmes. La protection passe du BIEN au CHAMP.',
    'python_worker', 'medium', 'optional_pipeline_step', '["supabase.push_upgrade"]'::jsonb,
    'active', 'frederic', 'business', 'static_analysis',
    'L3 21/09/2026. Inerte tant qu''aucun envoi n''echoue (0 ligne en attente aujourd''hui).',
    'phase2/identite/reappliquer_saisies_app.py', 10
)
on conflict (worker_key) do update set worker_name = excluded.worker_name, source_notes = excluded.source_notes, updated_at = now();
