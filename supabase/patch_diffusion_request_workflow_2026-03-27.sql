alter table public.app_diffusion_request
add column if not exists request_type text not null default 'demande_diffusion',
add column if not exists request_reason text,
add column if not exists admin_response text,
add column if not exists refusal_reason text,
add column if not exists follow_up_needed boolean not null default false,
add column if not exists follow_up_at timestamptz,
add column if not exists relaunch_count integer not null default 0;

update public.app_diffusion_request
set request_type = coalesce(nullif(request_type, ''), 'demande_diffusion'),
    request_reason = coalesce(request_reason, request_comment),
    admin_response = coalesce(admin_response, processing_comment)
where true;

create index if not exists idx_app_diffusion_request_followup
on public.app_diffusion_request (follow_up_needed, follow_up_at);
