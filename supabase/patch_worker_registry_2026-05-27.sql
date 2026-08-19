begin;

create table if not exists public.app_worker_registry (
    worker_key text primary key,
    worker_name text not null,
    worker_role text not null,
    worker_type text not null,
    criticality text not null
        check (criticality in ('critical', 'high', 'medium', 'low')),
    frequency text not null default 'manual',
    dependencies_json jsonb not null default '[]'::jsonb
        constraint app_worker_registry_dependencies_json_is_array
        check (jsonb_typeof(dependencies_json) = 'array'),
    status text not null default 'active'
        check (status in ('active', 'active_optional', 'legacy', 'disabled')),
    owner text not null default 'gti_ops',
    worker_version text not null default '2026.05.27-static',
    last_update date not null default date '2026-05-27',
    compatible_schema text not null default 'unknown',
    script_path text not null,
    command_hint text,
    expected_max_runtime_minutes integer
        constraint app_worker_registry_expected_max_runtime_positive
        check (expected_max_runtime_minutes is null or expected_max_runtime_minutes > 0),
    monitoring_domain text not null default 'system'
        check (monitoring_domain in ('system', 'business', 'mixed')),
    source_kind text not null default 'static_analysis',
    source_notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'app_worker_registry_dependencies_json_is_array'
          and conrelid = 'public.app_worker_registry'::regclass
    ) then
        alter table public.app_worker_registry
            add constraint app_worker_registry_dependencies_json_is_array
            check (jsonb_typeof(dependencies_json) = 'array');
    end if;

    if not exists (
        select 1
        from pg_constraint
        where conname = 'app_worker_registry_expected_max_runtime_positive'
          and conrelid = 'public.app_worker_registry'::regclass
    ) then
        alter table public.app_worker_registry
            add constraint app_worker_registry_expected_max_runtime_positive
            check (expected_max_runtime_minutes is null or expected_max_runtime_minutes > 0);
    end if;
end $$;

create index if not exists idx_app_worker_registry_type
on public.app_worker_registry (worker_type, status, criticality);

create index if not exists idx_app_worker_registry_criticality
on public.app_worker_registry (criticality, status);

create index if not exists idx_app_worker_registry_domain
on public.app_worker_registry (monitoring_domain, status);

create or replace view public.app_workers_current
with (security_invoker = true)
as
select *
from public.app_worker_registry
where status <> 'disabled'
order by
    case criticality
        when 'critical' then 1
        when 'high' then 2
        when 'medium' then 3
        else 4
    end,
    worker_key;

alter table public.app_worker_registry enable row level security;

drop policy if exists app_worker_registry_select_ops on public.app_worker_registry;
create policy app_worker_registry_select_ops
on public.app_worker_registry
for select
to authenticated
using (public.is_app_manager_or_admin());

revoke all on public.app_worker_registry from anon;
revoke all on public.app_worker_registry from public;
revoke all on public.app_workers_current from anon;
revoke all on public.app_workers_current from public;

grant select on public.app_worker_registry to authenticated;
grant select on public.app_workers_current to authenticated;
grant all on public.app_worker_registry to service_role;

with seed (
    worker_key,
    worker_name,
    worker_role,
    worker_type,
    criticality,
    frequency,
    dependencies_json,
    status,
    owner,
    worker_version,
    last_update,
    compatible_schema,
    script_path,
    command_hint,
    expected_max_runtime_minutes,
    monitoring_domain,
    source_notes
) as (
    values
    (
        'pipeline.full',
        'Full pipeline PowerShell',
        'Orchestre le flux Hektor API -> SQLite -> Normalize -> Phase2 -> Supabase.',
        'powershell_orchestrator',
        'critical',
        'scheduled_or_manual',
        '["python_venv", "hektor_api_oauth", "data.hektor.sqlite", "phase2.phase2.sqlite", "supabase", "matterport_api", "backend.appointments", "optional.github_vitrine"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'pipeline_local_sqlite_phase2_supabase',
        'run_full_pipeline.ps1',
        '.\\run_full_pipeline.ps1',
        180,
        'mixed',
        'Seed statique genere par analyse du projet. Aucun worker modifie.'
    ),
    (
        'phase1.sync_raw',
        'Hektor raw sync',
        'Extrait les ressources Hektor via API OAuth vers SQLite local.',
        'python_worker',
        'critical',
        'pipeline_step',
        '["hektor_api_oauth", "data.hektor.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'hektor_sqlite_v1',
        'sync_raw.py',
        '.\\.venv\\Scripts\\python.exe sync_raw.py --mode update',
        90,
        'system',
        'Phase 1 extraction. Source directe Hektor.'
    ),
    (
        'phase1.normalize_source',
        'Normalize source',
        'Normalise les payloads Hektor bruts en tables locales exploitables.',
        'python_worker',
        'critical',
        'pipeline_step',
        '["phase1.sync_raw", "data.hektor.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'hektor_sqlite_v1',
        'normalize_source.py',
        '.\\.venv\\Scripts\\python.exe normalize_source.py',
        60,
        'business',
        'Logique metier de normalisation locale.'
    ),
    (
        'phase1.build_case_index',
        'Build case index',
        'Construit l index local des dossiers et annonces.',
        'python_worker',
        'critical',
        'pipeline_step',
        '["phase1.normalize_source", "data.hektor.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'hektor_sqlite_v1',
        'build_case_index.py',
        '.\\.venv\\Scripts\\python.exe build_case_index.py',
        30,
        'business',
        'Alimente les etapes Phase2.'
    ),
    (
        'contacts.detail_backfill.wrapper',
        'Contact details backfill wrapper',
        'Wrapper PowerShell de reprise du backfill ContactById.',
        'powershell_wrapper',
        'high',
        'manual_or_scheduled',
        '["contacts.sync_detail", "hektor_api_oauth", "data.hektor.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'contacts_local_first_2026_05_25',
        'run_contact_details_backfill.ps1',
        '.\\run_contact_details_backfill.ps1',
        240,
        'mixed',
        'Contacts et relations encore en cours d integration.'
    ),
    (
        'contacts.sync_detail',
        'Contact details sync',
        'Recupere les details ContactById dans SQLite local.',
        'python_worker',
        'high',
        'pipeline_step',
        '["hektor_api_oauth", "data.hektor.sqlite", "sync_contact_state"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'contacts_local_first_2026_05_25',
        'phase2/sync/sync_contact_details.py',
        '.\\.venv\\Scripts\\python.exe phase2\\sync\\sync_contact_details.py',
        120,
        'business',
        'Backfill delta des fiches contacts detaillees.'
    ),
    (
        'phase2.bootstrap',
        'Phase2 bootstrap',
        'Construit la base metier Phase2 depuis les donnees locales.',
        'python_worker',
        'critical',
        'pipeline_step',
        '["phase1.build_case_index", "data.hektor.sqlite", "phase2.phase2.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'phase2_sqlite_v1',
        'phase2/bootstrap_phase2.py',
        '.\\.venv\\Scripts\\python.exe phase2\\bootstrap_phase2.py',
        60,
        'business',
        'Etape centrale du modele applicatif local.'
    ),
    (
        'phase2.refresh_views',
        'Phase2 refresh views',
        'Rafraichit les vues et agregats Phase2.',
        'python_worker',
        'critical',
        'pipeline_step',
        '["phase2.bootstrap", "phase2.phase2.sqlite", "data.hektor.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'phase2_sqlite_v1',
        'phase2/refresh_views.py',
        '.\\.venv\\Scripts\\python.exe phase2\\refresh_views.py',
        45,
        'business',
        'Produit les vues utilisees par les pushs et controles.'
    ),
    (
        'phase2.contacts_layer',
        'Phase2 contacts layer',
        'Construit la couche contacts locale, relations et doublons.',
        'python_worker',
        'high',
        'pipeline_step',
        '["contacts.sync_detail", "phase2.phase2.sqlite", "data.hektor.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'contacts_local_first_2026_05_25',
        'phase2/contacts/build_contacts_layer.py',
        '.\\.venv\\Scripts\\python.exe phase2\\contacts\\build_contacts_layer.py --no-reports',
        60,
        'business',
        'Module contacts non considere comme complet fonctionnellement.'
    ),
    (
        'phase2.quality_checks',
        'Phase2 quality checks',
        'Execute les controles de coherence locaux.',
        'python_worker',
        'high',
        'pipeline_step',
        '["phase2.refresh_views", "phase2.phase2.sqlite", "data.hektor.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'phase2_sqlite_v1',
        'phase2/checks/run_quality_checks.py',
        '.\\.venv\\Scripts\\python.exe phase2\\checks\\run_quality_checks.py',
        30,
        'business',
        'Doit distinguer alertes metier et erreurs systeme.'
    ),
    (
        'supabase.push_upgrade',
        'Push upgrade to Supabase',
        'Publie les donnees applicatives courantes vers Supabase.',
        'python_worker',
        'critical',
        'pipeline_step',
        '["phase2.refresh_views", "phase2.phase2.sqlite", "data.hektor.sqlite", "supabase_service_role", "app_delta_run"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'supabase_app_schema_v1_plus_patches',
        'phase2/sync/push_upgrade_to_supabase.py',
        '.\\.venv\\Scripts\\python.exe phase2\\sync\\push_upgrade_to_supabase.py',
        90,
        'system',
        'Supabase reste une cible applicative, pas la source primaire.'
    ),
    (
        'supabase.push_hektor_directory',
        'Push Hektor directory to Supabase',
        'Publie agences, utilisateurs et negociateurs Hektor vers Supabase.',
        'python_worker',
        'high',
        'pipeline_step',
        '["hektor_api_oauth", "data.hektor.sqlite", "supabase_service_role"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'hektor_directory_2026_05_22',
        'phase2/sync/push_hektor_directory_to_supabase.py',
        '.\\.venv\\Scripts\\python.exe phase2\\sync\\push_hektor_directory_to_supabase.py',
        30,
        'system',
        'Annuaire necessaire aux scopes et vues applicatives.'
    ),
    (
        'supabase.push_contacts',
        'Push contacts to Supabase',
        'Push optionnel de la couche contacts vers Supabase.',
        'python_worker',
        'medium',
        'optional_pipeline_step',
        '["phase2.contacts_layer", "supabase_service_role", "app_contact_current"]'::jsonb,
        'active_optional',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'contacts_module_2026_05_25',
        'phase2/sync/push_contacts_to_supabase.py',
        '.\\.venv\\Scripts\\python.exe phase2\\sync\\push_contacts_to_supabase.py --push-mode update',
        90,
        'business',
        'Optionnel dans run_full_pipeline.ps1 via PushContactsToSupabase.'
    ),
    (
        'supabase.push_single_annonce',
        'Push single annonce to Supabase',
        'Publie une annonce ciblee apres refresh local.',
        'python_worker',
        'high',
        'console_follow_up',
        '["phase2.refresh_single_annonce", "phase2.phase2.sqlite", "data.hektor.sqlite", "supabase_service_role"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'supabase_app_schema_v1_plus_patches',
        'phase2/sync/push_single_annonce_to_supabase.py',
        '.\\.venv\\Scripts\\python.exe phase2\\sync\\push_single_annonce_to_supabase.py',
        15,
        'system',
        'Utilise apres actions Console ciblees.'
    ),
    (
        'phase2.refresh_single_annonce',
        'Refresh single annonce',
        'Rafraichit localement une annonce Hektor ciblee.',
        'python_worker',
        'high',
        'console_follow_up',
        '["hektor_api_oauth", "data.hektor.sqlite", "phase2.phase2.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'phase2_sqlite_v1',
        'phase2/sync/refresh_single_annonce.py',
        '.\\.venv\\Scripts\\python.exe phase2\\sync\\refresh_single_annonce.py',
        15,
        'system',
        'Refresh cible apres action Hektor.'
    ),
    (
        'hektor.diffusion_writeback',
        'Hektor diffusion writeback',
        'Applique les changements de diffusion vers Hektor.',
        'python_worker',
        'high',
        'backend_or_manual',
        '["hektor_api_oauth", "data.hektor.sqlite", "supabase_service_role", "app_diffusion_target"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'diffusion_targets_console_2026_04_07',
        'phase2/sync/hektor_diffusion_writeback.py',
        '.\\.venv\\Scripts\\python.exe phase2\\sync\\hektor_diffusion_writeback.py',
        30,
        'business',
        'Ecriture Hektor sensible.'
    ),
    (
        'matterport.sync_models',
        'Matterport models sync',
        'Synchronise les modeles Matterport et associations annonces vers Supabase.',
        'python_worker',
        'medium',
        'pipeline_step',
        '["matterport_api", "matterport/.env", "data.hektor.sqlite", "supabase_service_role"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'matterport_groups_2026_05_05',
        'phase2/sync/sync_matterport_models.py',
        '.\\.venv\\Scripts\\python.exe phase2\\sync\\sync_matterport_models.py --max-models 0 --supabase-upsert',
        60,
        'business',
        'Sync liens/modeles Matterport, distinct des actions Playwright Matterport.'
    ),
    (
        'appointments.backfill_public_links',
        'Appointment public link backfill',
        'Complete les liens publics de rendez-vous annonce/estimation.',
        'python_worker',
        'medium',
        'pipeline_step',
        '["backend.settings", "supabase_service_role", "app_appointment_public_link"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'appointment_qr_annonce_2026_04_29',
        'backend/scripts/backfill_appointment_public_links.py',
        '.\\.venv\\Scripts\\python.exe backend\\scripts\\backfill_appointment_public_links.py --quiet',
        30,
        'business',
        'Alimente le module RDV public.'
    ),
    (
        'console.enqueue_sync_jobs',
        'Console enqueue sync jobs',
        'Cree des jobs Console de synchronisation documents selon scope.',
        'node_script',
        'medium',
        'optional_pipeline_step',
        '["supabase_service_role", "app_console_job"]'::jsonb,
        'active_optional',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'console_job_schema_v9',
        'Console/enqueue_console_sync_jobs.js',
        'node Console\\enqueue_console_sync_jobs.js',
        30,
        'system',
        'Optionnel dans run_full_pipeline.ps1 via EnqueueConsoleDocuments.'
    ),
    (
        'console.worker.actions',
        'Console worker actions',
        'Execute les actions Hektor metier depuis app_console_job.',
        'node_playwright_worker',
        'critical',
        'daemon_or_scheduled',
        '["supabase_service_role", "app_console_job", "app_console_job_log", "hektor_admin_session", "playwright"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'console_job_schema_v9',
        'Console/console_job_worker.js',
        '.\\Console\\run_console_worker.ps1 -WorkerKind actions',
        null,
        'mixed',
        'Worker Playwright critique. Ne pas remplacer.'
    ),
    (
        'console.worker.documents',
        'Console worker documents',
        'Execute les jobs documents/photos Hektor.',
        'node_playwright_worker',
        'high',
        'daemon_or_scheduled',
        '["supabase_service_role", "app_console_job", "app_console_document", "app_console_photo", "hektor_admin_session", "playwright", "C:\\\\Hektor\\\\HektorConsoleDocuments"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'console_job_schema_v9',
        'Console/console_job_worker.js',
        '.\\Console\\run_console_worker.ps1 -WorkerKind documents',
        null,
        'mixed',
        'Gere documents, photos, storage local et Supabase.'
    ),
    (
        'console.worker.admin',
        'Console worker admin',
        'Execute les actions admin Hektor : suppression, archive, restauration, statut, affectation.',
        'node_playwright_worker',
        'critical',
        'daemon_or_scheduled',
        '["supabase_service_role", "app_console_job", "hektor_admin_session", "playwright"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'console_job_schema_v9',
        'Console/console_job_worker.js',
        '.\\Console\\run_console_worker.ps1 -WorkerKind admin',
        null,
        'mixed',
        'Actions Hektor destructives ou sensibles.'
    ),
    (
        'console.worker.matterport',
        'Console worker Matterport',
        'Execute les actions Matterport via Playwright.',
        'node_playwright_worker',
        'medium',
        'daemon_or_scheduled',
        '["supabase_service_role", "app_console_job", "matterport_storage_state", "playwright"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'console_job_schema_v9',
        'Console/console_job_worker.js',
        '.\\Console\\run_console_worker.ps1 -WorkerKind matterport',
        null,
        'business',
        'Actions Matterport distinctes du sync read-only des modeles.'
    ),
    (
        'console.worker.sync_light',
        'Console worker sync light',
        'Execute les refreshs cibles apres actions Console.',
        'node_worker',
        'high',
        'daemon_or_scheduled',
        '["supabase_service_role", "app_console_job", "phase2.refresh_single_annonce", "supabase.push_single_annonce"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'console_job_schema_v9',
        'Console/console_job_worker.js',
        '.\\Console\\run_console_worker.ps1 -WorkerKind sync_light',
        null,
        'system',
        'Maintient la coherence local/Supabase apres action Console.'
    ),
    (
        'console.worker.sync_full',
        'Console worker sync full',
        'Execute les synchronisations Console plus larges.',
        'node_worker',
        'high',
        'daemon_or_scheduled',
        '["supabase_service_role", "app_console_job", "Console/enqueue_console_sync_jobs.js"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'console_job_schema_v9',
        'Console/console_job_worker.js',
        '.\\Console\\run_console_worker.ps1 -WorkerKind sync_full',
        null,
        'system',
        'Le job archive_cloud_documents est reference mais non implemente.'
    ),
    (
        'backend.fastapi',
        'GTI FastAPI backend',
        'Expose health, admin users, diffusion, notifications et rendez-vous.',
        'python_service',
        'high',
        'service',
        '["supabase", "supabase_service_role", "smtp_or_gmail", "optional_hektor_api"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'backend_api_0_1_0',
        'backend/app/main.py',
        'uvicorn backend.app.main:app',
        null,
        'mixed',
        'Service surveille via GET /health.'
    ),
    (
        'archive.annonce_details.wrapper',
        'Archived annonce details wrapper',
        'Wrapper PowerShell pour details annonces archivees.',
        'powershell_wrapper',
        'medium',
        'manual',
        '["archive.annonce_details.sync", "data.hektor.sqlite"]'::jsonb,
        'active_optional',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'archive_detail_cache_2026_05_20',
        'run_archived_annonce_details.ps1',
        '.\\run_archived_annonce_details.ps1',
        120,
        'business',
        'Workflow de details archives/historiques.'
    ),
    (
        'archive.annonce_details.sync',
        'Archived annonce details sync',
        'Synchronise les details locaux des annonces archivees.',
        'python_worker',
        'medium',
        'manual',
        '["hektor_api_oauth", "data.hektor.sqlite"]'::jsonb,
        'active_optional',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'archive_detail_cache_2026_05_20',
        'sync_archived_annonce_details.py',
        '.\\.venv\\Scripts\\python.exe sync_archived_annonce_details.py',
        120,
        'business',
        'Workflow separe du pipeline full.'
    ),
    (
        'actif.sync',
        'ACTIF sync',
        'Synchronise les donnees ACTIF.',
        'python_worker',
        'medium',
        'manual_or_watch',
        '["hektor_api_oauth", "ACTIF/actif.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'actif_sqlite_v1',
        'ACTIF/actif_sync.py',
        '.\\.venv\\Scripts\\python.exe ACTIF\\actif_sync.py',
        90,
        'business',
        'Pipeline ACTIF separe du flux principal.'
    ),
    (
        'actif.normalize',
        'ACTIF normalize',
        'Normalise les donnees ACTIF.',
        'python_worker',
        'medium',
        'manual_or_watch',
        '["actif.sync", "ACTIF/actif.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'actif_sqlite_v1',
        'ACTIF/actif_normalize.py',
        '.\\.venv\\Scripts\\python.exe ACTIF\\actif_normalize.py',
        60,
        'business',
        'Pipeline ACTIF autonome.'
    ),
    (
        'actif.build',
        'ACTIF build',
        'Construit les sorties exploitables ACTIF.',
        'python_worker',
        'medium',
        'manual_or_watch',
        '["actif.normalize", "ACTIF/actif.sqlite"]'::jsonb,
        'active',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'actif_sqlite_v1',
        'ACTIF/actif_build.py',
        '.\\.venv\\Scripts\\python.exe ACTIF\\actif_build.py',
        60,
        'business',
        'Pipeline ACTIF autonome.'
    ),
    (
        'actif.report',
        'ACTIF report',
        'Produit les rapports ACTIF.',
        'python_worker',
        'low',
        'manual',
        '["actif.build", "ACTIF/actif.sqlite"]'::jsonb,
        'active_optional',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'actif_sqlite_v1',
        'ACTIF/actif_report.py',
        '.\\.venv\\Scripts\\python.exe ACTIF\\actif_report.py',
        30,
        'business',
        'Reporting ACTIF.'
    ),
    (
        'actif.watch',
        'ACTIF watch',
        'Surveille le pipeline ACTIF local.',
        'python_worker',
        'low',
        'watcher',
        '["ACTIF/actif.sqlite"]'::jsonb,
        'active_optional',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'actif_sqlite_v1',
        'ACTIF/actif_watch.py',
        '.\\.venv\\Scripts\\python.exe ACTIF\\actif_watch.py',
        null,
        'system',
        'Watcher ACTIF separe.'
    ),
    (
        'phase1.safe_runner',
        'Phase1 safe runner',
        'Wrapper historique de lancement Phase1 securise.',
        'powershell_wrapper',
        'medium',
        'manual',
        '["phase1.sync_raw", "phase1.normalize_source"]'::jsonb,
        'legacy',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'hektor_sqlite_v1',
        'run_phase1_safe.ps1',
        '.\\run_phase1_safe.ps1',
        120,
        'system',
        'Present dans le code mais le flux principal utilise run_full_pipeline.ps1.'
    ),
    (
        'phase1.safe_worker',
        'Phase1 safe worker',
        'Wrapper historique worker Phase1.',
        'powershell_wrapper',
        'medium',
        'manual',
        '["phase1.sync_raw", "phase1.normalize_source"]'::jsonb,
        'legacy',
        'gti_ops',
        '2026.05.27-static',
        date '2026-05-27',
        'hektor_sqlite_v1',
        'run_phase1_safe_worker.ps1',
        '.\\run_phase1_safe_worker.ps1',
        120,
        'system',
        'Present dans le code mais non central dans le pipeline actuel.'
    )
)
insert into public.app_worker_registry (
    worker_key,
    worker_name,
    worker_role,
    worker_type,
    criticality,
    frequency,
    dependencies_json,
    status,
    owner,
    worker_version,
    last_update,
    compatible_schema,
    script_path,
    command_hint,
    expected_max_runtime_minutes,
    monitoring_domain,
    source_notes
)
select
    worker_key,
    worker_name,
    worker_role,
    worker_type,
    criticality,
    frequency,
    dependencies_json,
    status,
    owner,
    worker_version,
    last_update,
    compatible_schema,
    script_path,
    command_hint,
    expected_max_runtime_minutes,
    monitoring_domain,
    source_notes
from seed
on conflict (worker_key) do update
set
    worker_name = excluded.worker_name,
    worker_role = excluded.worker_role,
    worker_type = excluded.worker_type,
    dependencies_json = excluded.dependencies_json,
    worker_version = excluded.worker_version,
    last_update = excluded.last_update,
    compatible_schema = excluded.compatible_schema,
    script_path = excluded.script_path,
    command_hint = excluded.command_hint,
    monitoring_domain = excluded.monitoring_domain,
    source_kind = 'static_analysis',
    source_notes = excluded.source_notes,
    updated_at = now();

comment on table public.app_worker_registry is
'Registre statique des workers GTI. Source de verite monitoring initiale, generee par analyse du projet sans modifier les workers existants.';

comment on column public.app_worker_registry.worker_version is
'Version statique declaree dans le registre. Les workers ne sont pas encore auto-declaratifs.';

comment on column public.app_worker_registry.compatible_schema is
'Contrat/schema attendu par le worker selon analyse statique.';

comment on column public.app_worker_registry.dependencies_json is
'Dependances logiques utilisees pour supervision et suppression des alertes en cascade.';

commit;
