-- ============================================================================
-- patch_console_job_approval_gate_2026-07-05.sql
--
-- Socle du "bac a sable" pour agents IA (Phase 1) : porte de VALIDATION HUMAINE
-- sur la file de jobs, SANS toucher le claim RPC prod-critique.
--
-- Principe : un job cree en status 'pending_approval' n'est PAS pris par
-- app_console_claim_next_job (qui ne claim que 'pending') -> il reste en attente
-- tant qu'un humain ne l'approuve pas. L'approbation le passe a 'pending' -> il
-- entre alors dans le flux normal.
--
-- ADDITIF & DORMANT : par defaut aucun job n'utilise 'pending_approval' -> le
-- comportement actuel est strictement inchange. Reversible.
-- ============================================================================

-- 1) Autoriser le nouveau statut (drop + re-add atomique dans la migration).
alter table public.app_console_job drop constraint if exists app_console_job_status_check;
alter table public.app_console_job add constraint app_console_job_status_check
  check (status = any (array['pending','running','done','error','pending_approval']));

-- 2) Colonnes d'audit de l'approbation.
alter table public.app_console_job
  add column if not exists approved_at timestamptz,
  add column if not exists approved_by uuid;

comment on column public.app_console_job.approved_at is
  'Bac a sable : horodatage de la validation humaine (pending_approval -> pending).';
comment on column public.app_console_job.approved_by is
  'Bac a sable : utilisateur (auth uid) ayant valide le job.';

-- 3) RPC d'approbation : passe un job de pending_approval a pending.
--    Renvoie la ligne (null si le job n'existe pas / n'est pas en attente).
create or replace function public.app_console_approve_job(p_job_id uuid, p_approved_by uuid default null)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $function$
declare v_row public.app_console_job;
begin
  update public.app_console_job
     set status = 'pending',
         approved_at = now(),
         approved_by = coalesce(p_approved_by, approved_by),
         updated_at = now()
   where id = p_job_id
     and status = 'pending_approval'
  returning * into v_row;
  return v_row;
end
$function$;

-- Appelable par le front (authenticated) ; l'UI reserve le bouton aux admin/manager.
revoke all on function public.app_console_approve_job(uuid, uuid) from public, anon;
grant execute on function public.app_console_approve_job(uuid, uuid) to authenticated, service_role;
