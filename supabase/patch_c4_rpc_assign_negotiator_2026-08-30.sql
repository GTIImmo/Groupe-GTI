-- =====================================================================
-- C.4 — AFFECTER LE NÉGOCIATEUR ÉCRIT CHEZ NOUS D'ABORD
-- Date : 2026-08-30   (3ᵉ des onze workers à convertir)
--
-- Même patron que l'archivage : le carnet et le travail sont écrits dans la
-- MÊME transaction. Si Hektor refuse ou tombe, l'intention reste chez nous.
--
-- CE QU'ON INSCRIT AU CARNET : `negociateur_email`, la valeur que l'app AFFIRME
-- — celle que le négociateur a choisie à l'écran. Le worker, lui, travaille avec
-- l'idUser Hektor ; les deux voyagent ensemble dans la charge du travail.
--
-- Pourquoi l'email et pas l'identifiant : c'est la colonne que la vue serveur
-- porte déjà (`app_view_generale.negociateur_email`), donc la seule qui se
-- compare à ce que le miroir sait. Un carnet dont la valeur ne se compare à rien
-- ne sert qu'à moitié.
--
-- ET S'IL N'Y A PAS D'EMAIL, ON N'ÉCRIT RIEN. Le travail part quand même, le
-- carnet reste muet. C'est la règle du projet, arbitrée le 28/08 :
-- **« l'app gagne seulement quand elle a quelque chose à dire »**. Inventer une
-- valeur pour remplir une ligne serait pire que de laisser vide.
--
-- ÉPROUVÉ LE 30/08 : appelée sans session, la RPC REFUSE et le carnet reste
-- intact — ce qui vérifie du même coup le correctif de
-- `patch_c4_droits_jamais_null_2026-08-30.sql`. La validation de bout en bout
-- se fera depuis l'app, avec une session admin : c'est le seul chemin qui porte
-- un rôle, et c'est voulu.
--
-- Appliqué en production via la migration `c4_rpc_assign_negotiator_optimistic`.
-- =====================================================================

create or replace function public.app_assign_negotiator_optimistic(
  target_dossier_id bigint,
  target_user_id    text,
  job_payload       jsonb   default '{}'::jsonb,
  job_priority      integer default 9
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
  v_email  text;
begin
  if coalesce(trim(target_user_id), '') !~ '^\d+$' then
    raise exception 'target_hektor_user_id numerique requis' using errcode = '22023';
  end if;

  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;

  if not public.app_console_can_request_job('assign_hektor_annonce_negotiator',
                                            target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_assign_negotiator' using errcode = '42501';
  end if;

  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier',        d.numero_dossier,
    'titre_bien',            d.titre_bien,
    'target_hektor_user_id', trim(target_user_id));

  v_email := nullif(trim(coalesce(v_charge->>'target_hektor_user_email', '')), '');

  -- 1. CHEZ NOUS D'ABORD -- mais seulement si on a quelque chose a dire.
  if v_email is not null then
    insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_par)
    values (target_dossier_id, 'negociateur_email', v_email, 'geste_affecter_negociateur', auth.uid()::text)
    on conflict (app_dossier_id, champ) do update
       set valeur_app = excluded.valeur_app,
           origine    = excluded.origine,
           ecrit_le   = now(),
           ecrit_par  = excluded.ecrit_par;
  end if;

  -- 2. PUIS le travail, meme transaction
  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  values
    ('assign_hektor_annonce_negotiator', target_dossier_id, d.hektor_annonce_id::text,
     v_charge, coalesce(job_priority, 9), auth.uid())
  returning id into v_job_id;

  return jsonb_build_object('job_id', v_job_id,
                            'app_dossier_id', target_dossier_id,
                            'champ', 'negociateur_email',
                            'valeur_app', v_email);
end
$function$;

revoke execute on function public.app_assign_negotiator_optimistic(bigint, text, jsonb, integer) from public;
revoke execute on function public.app_assign_negotiator_optimistic(bigint, text, jsonb, integer) from anon;
grant  execute on function public.app_assign_negotiator_optimistic(bigint, text, jsonb, integer) to authenticated, service_role;
