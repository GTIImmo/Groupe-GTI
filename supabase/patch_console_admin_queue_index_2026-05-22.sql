drop index if exists public.app_console_job_active_admin_annonce_idx;

create index if not exists app_console_job_admin_annonce_queue_idx
on public.app_console_job (hektor_annonce_id, status, priority, requested_at)
where hektor_annonce_id is not null
  and job_type in (
    'delete_hektor_annonce',
    'archive_hektor_annonce',
    'restore_hektor_annonce',
    'change_hektor_annonce_status',
    'assign_hektor_annonce_negotiator'
  )
  and status in ('pending', 'running');
