drop index if exists public.idx_app_agence_directory_user;
create index if not exists idx_app_agence_directory_user on public.app_agence_directory (id_user);
