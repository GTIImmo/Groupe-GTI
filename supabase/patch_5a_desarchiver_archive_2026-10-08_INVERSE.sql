-- =====================================================================
-- RETOUR ARRIERE du POINT 5a -- repose la fonction d'AVANT, mot pour mot
-- Date : 2026-10-08 · A coller seulement si on veut annuler le patch
--        supabase/patch_5a_desarchiver_archive_2026-10-08.sql
--
-- CE QUE C'EST. Le corps ci-dessous est la definition exacte en production avant le
-- patch du 08/10 (relevee par pg_get_functiondef le 08/10 vers 09:20, empreinte md5
-- d4f311d782c7525494107cc0596fdedc), identique a celle posee le 30/08 par
-- supabase/patch_c4_rpc_archive_restore_2026-08-30.sql.
--
-- ATTENTION : `create or replace`, JAMAIS `drop function` -- un drop ferait renaitre la
-- fonction ouverte a tout le monde et defferait le chantier ① (securite).
--
-- EFFET : desarchiver redevient impossible pour les 35 317 archives (`dossier_not_found`).
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

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

DO $$
DECLARE e text;
BEGIN
  -- ⚠ 08/10 : on compare SANS les retours a la ligne Windows. Un copier-coller depuis
  -- Windows transforme les fins de ligne du corps (\n -> \r\n), ce qui change l'empreinte
  -- sans changer une seule lettre du code. Mesure du 08/10 : la meme definition donne
  -- d4f311d782c7525494107cc0596fdedc en LF et d0b925a2ceb970acf69efe3140d31581 en CRLF.
  e := md5(replace(pg_get_functiondef('public.app_restore_annonce_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), ''));
  RAISE NOTICE 'empreinte de la fonction reposee : % (attendu d4f311d782c7525494107cc0596fdedc)', e;
  IF e <> 'd4f311d782c7525494107cc0596fdedc' THEN
    RAISE EXCEPTION 'CONTROLE : la fonction reposee n''est pas celle d''avant (empreinte %)', e;
  END IF;
  IF has_function_privilege('anon', 'public.app_restore_annonce_optimistic(bigint,jsonb,integer)', 'EXECUTE') THEN
    RAISE EXCEPTION 'CONTROLE : anon peut executer la fonction -- chantier ① casse';
  END IF;
END $$;

COMMIT;
