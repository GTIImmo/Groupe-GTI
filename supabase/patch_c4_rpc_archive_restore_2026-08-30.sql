-- =====================================================================
-- C.4 — ARCHIVER ET DÉSARCHIVER PASSENT PAR L'APP D'ABORD
-- Date : 2026-08-30
--
-- Les deux premiers des onze workers à convertir. Le patron est celui des cinq
-- déjà faits, et on ne le réinvente pas :
--
--     1. charger l'objet et vérifier les droits
--     2. ÉCRIRE CHEZ NOUS
--     3. créer le travail DANS LA MÊME TRANSACTION
--     4. rendre le numéro du travail
--
-- Avant, le front faisait seulement l'étape 3 : il insérait le travail et
-- attendait. Si Hektor refusait ou tombait, **l'intention n'existait nulle part
-- chez nous** — c'est tout le sujet de C.4.
--
-- TOUT OU RIEN. Le carnet et le travail sont écrits dans la même transaction. Un
-- index unique interdit deux actions admin simultanées sur la même annonce
-- (`app_console_job_active_admin_annonce_idx`) : s'il se déclenche, la
-- transaction entière est annulée — carnet compris. On ne laisse jamais une
-- trace d'intention sans le travail qui va avec.
--
-- DORMANT. Le carnet se remplit, mais `CHAMPS_APP_ANNONCE` est vide dans
-- `contrat_autorite.py` : le run de nuit continue de laisser Hektor gagner.
-- Rien ne change en production tant que l'interrupteur n'est pas allumé.
--
-- ÉPROUVÉ LE 30/08 sur le bac à sable 62774 :
--     la RPC a écrit le carnet ET le travail à la même seconde (07:38:48)
--     le worker a pris le travail, `done` en 35 s
--     l'API a confirmé archive="1", puis "0" après le désarchivage
--
-- ET C'EST CET ESSAI qui a révélé le défaut du contrôle de droits corrigé dans
-- `patch_c4_droits_jamais_null_2026-08-30.sql` : l'archivage passait sans aucun
-- contrôle, parce que `not NULL` ne déclenche pas un `if`.
--
-- Appliqué en production via la migration `c4_rpc_archive_restore_optimistic`.
-- =====================================================================

create or replace function public.app_archive_annonce_optimistic(
  target_dossier_id bigint,
  job_payload       jsonb   default '{}'::jsonb,
  job_priority      integer default 8
)
returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  d        app_dossier_current%rowtype;
  v_job_id uuid;
  v_charge jsonb;
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;

  if not public.app_console_can_request_job('archive_hektor_annonce',
                                            target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_archive' using errcode = '42501';
  end if;

  -- 1. CHEZ NOUS D'ABORD
  insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_par)
  values (target_dossier_id, 'archive', '1', 'geste_archiver', auth.uid()::text)
  on conflict (app_dossier_id, champ) do update
     set valeur_app = excluded.valeur_app,
         origine    = excluded.origine,
         ecrit_le   = now(),
         ecrit_par  = excluded.ecrit_par;

  -- 2. PUIS le travail, meme transaction
  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier', d.numero_dossier,
    'titre_bien',     d.titre_bien,
    'target_archive', '1');

  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  values
    ('archive_hektor_annonce', target_dossier_id, d.hektor_annonce_id::text,
     v_charge, coalesce(job_priority, 8), auth.uid())
  returning id into v_job_id;

  return jsonb_build_object('job_id', v_job_id,
                            'app_dossier_id', target_dossier_id,
                            'champ', 'archive',
                            'valeur_app', '1');
end
$function$;

create or replace function public.app_restore_annonce_optimistic(
  target_dossier_id bigint,
  job_payload       jsonb   default '{}'::jsonb,
  job_priority      integer default 8
)
returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  d        app_dossier_current%rowtype;
  v_job_id uuid;
  v_charge jsonb;
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;

  if not public.app_console_can_request_job('restore_hektor_annonce',
                                            target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_restore' using errcode = '42501';
  end if;

  insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_par)
  values (target_dossier_id, 'archive', '0', 'geste_desarchiver', auth.uid()::text)
  on conflict (app_dossier_id, champ) do update
     set valeur_app = excluded.valeur_app,
         origine    = excluded.origine,
         ecrit_le   = now(),
         ecrit_par  = excluded.ecrit_par;

  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier', d.numero_dossier,
    'titre_bien',     d.titre_bien,
    'target_archive', '0');

  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  values
    ('restore_hektor_annonce', target_dossier_id, d.hektor_annonce_id::text,
     v_charge, coalesce(job_priority, 8), auth.uid())
  returning id into v_job_id;

  return jsonb_build_object('job_id', v_job_id,
                            'app_dossier_id', target_dossier_id,
                            'champ', 'archive',
                            'valeur_app', '0');
end
$function$;

-- Le piege du 29/08 : REVOKE FROM PUBLIC ne retire PAS `anon`, que Supabase
-- accorde par privilege par defaut sur toute fonction neuve du schema public.
-- Verifie apres application : les deux rendent « authenticated, postgres, service_role ».
revoke execute on function public.app_archive_annonce_optimistic(bigint, jsonb, integer) from public;
revoke execute on function public.app_archive_annonce_optimistic(bigint, jsonb, integer) from anon;
grant  execute on function public.app_archive_annonce_optimistic(bigint, jsonb, integer) to authenticated, service_role;

revoke execute on function public.app_restore_annonce_optimistic(bigint, jsonb, integer) from public;
revoke execute on function public.app_restore_annonce_optimistic(bigint, jsonb, integer) from anon;
grant  execute on function public.app_restore_annonce_optimistic(bigint, jsonb, integer) to authenticated, service_role;
