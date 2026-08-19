begin;

revoke all on public.app_worker_registry from anon;
revoke all on public.app_worker_registry from public;
revoke all on public.app_worker_registry from authenticated;

revoke all on public.app_workers_current from anon;
revoke all on public.app_workers_current from public;
revoke all on public.app_workers_current from authenticated;

grant select on public.app_worker_registry to authenticated;
grant select on public.app_workers_current to authenticated;
grant all on public.app_worker_registry to service_role;

commit;
