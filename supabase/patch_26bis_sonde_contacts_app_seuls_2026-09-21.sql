-- ═══════════════════════════════════════════════════════════════════════════
-- 26bis-CONTACTS / 26bis-RELATIONS — LA SONDE DE L'ETAPE          21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Lecon de C.17-ter, apprise hier : une cle de battement de coeur absente du
-- registre n'ecrit RIEN, et sans erreur. L'etape « phase2 contacts connus de
-- l app seule » est posee AUJOURD'HUI avec sa ligne -- on ne repete pas le trou
-- des 13 cles muettes.
--
-- L'ETAPE EST FACULTATIVE dans le run (Invoke-OptionalStepWithRetry) : elle
-- OBSERVE, elle ne repare rien, et son echec ne doit pas priver l'agence de sa
-- nuit. Mais status = 'active' quand meme, sinon check_worker_heartbeat la
-- saute -- le piege de supabase.push_contacts.
--
-- RETOUR ARRIERE :
--   DELETE FROM public.app_worker_registry WHERE worker_key = 'phase2.contacts_app_seuls';
-- ═══════════════════════════════════════════════════════════════════════════

insert into public.app_worker_registry (
    worker_key, worker_name, worker_role, worker_type, criticality, frequency,
    dependencies_json, status, owner, monitoring_domain, source_kind, source_notes,
    script_path, expected_max_runtime_minutes
) values (
    'phase2.contacts_app_seuls',
    'Contacts et relations connus de l''app seule',
    'Recense ce que l''app detient et que le miroir Hektor ignore : un contact ou une relation nes dans l''app. Sans ce releve, la reconstruction nocturne les ferait disparaitre.',
    'python_worker', 'medium', 'optional_pipeline_step',
    '["phase2.contacts_layer"]'::jsonb,
    'active', 'frederic', 'business', 'static_analysis',
    '26bis 21/09/2026. Jumeau de phase2.annonces_app_seule. INERTE tant que rien ne nait dans l''app (mesure du 21/09 : 0 contact, 0 relation) -- la creation sans Hektor est le lot L4.',
    'phase2/identite/contacts_app_seuls.py', 15
)
on conflict (worker_key) do update set
    worker_name = excluded.worker_name,
    worker_role = excluded.worker_role,
    criticality = excluded.criticality,
    frequency = excluded.frequency,
    status = excluded.status,
    source_notes = excluded.source_notes,
    script_path = excluded.script_path,
    updated_at = now();
