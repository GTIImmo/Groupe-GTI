-- =====================================================================
-- RETOUR ARRIERE du POINT 5b -- repose la fonction d'AVANT, mot pour mot
-- Date : 2026-10-08 · A coller seulement si on veut annuler le patch
--        supabase/patch_5b_mandant_identite_2026-10-08.sql
--
-- CE QUE C'EST. Le corps ci-dessous est la definition exacte en production avant le
-- patch du 08/10 : empreinte du corps 0d6d48371f09ca3626c2fad404a27d5b, verifiee
-- hors ligne contre pg_proc.prosrc AVANT d'ecrire ce fichier.
--
-- ATTENTION : `create or replace`, JAMAIS `drop function` -- un drop ferait renaitre
-- la fonction ouverte a tout le monde et deferait le chantier ① (securite).
--
-- EFFET : modifier un mandant depuis sa carte n'ecrit plus rien chez nous (le geste
-- part toujours chez Hektor), et la protection contre le double envoi redevient morte.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

create or replace function public.app_update_mandant_contact_optimistic(
  target_app_dossier_id   bigint,
  target_hektor_annonce_id text,
  target_contact_id       text,
  contact_payload         jsonb,
  job_priority            integer default 16
)
returns app_console_job
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  created_job public.app_console_job;
  champs      jsonb := '{}'::jsonb;
  cle         text;
  -- Seules ces cles sont des CHAMPS du contact. Le reste du payload
  -- (identifiants, contexte negociateur) n'a rien a faire dans une edition :
  -- il partirait dans push_fields et polluerait l'envoi.
  connues     text[] := array['civilite','last_name','first_name','email',
                              'phone','address','postal_code','city'];
begin
  -- ── 1. LE TRAVAIL, avec ses garde-fous d'origine (par recouvrement) ──
  created_job := public.app_console_create_update_mandant_contact_job(
      target_app_dossier_id, target_hektor_annonce_id,
      target_contact_id, contact_payload, job_priority);

  -- ── 2. PUIS l'ecriture chez nous, best effort ──
  begin
    foreach cle in array connues loop
      if nullif(trim(coalesce(contact_payload->>cle, '')), '') is not null then
        champs := champs || jsonb_build_object(cle, contact_payload->>cle);
      end if;
    end loop;

    if champs <> '{}'::jsonb then
      perform public.app_edit_contact_optimistic(target_contact_id, champs);

      -- ── 3. UN SEUL ENVOI : on designe NOTRE travail au balayage ──
      update public.app_contact_pending
         set push_job_id = created_job.id, updated_at = now()
       where hektor_contact_id = target_contact_id;
    end if;
  exception when others then
    -- Le geste part quand meme chez Hektor. L'app n'aura simplement pas la
    -- valeur d'avance -- c'est le comportement d'avant, pas une regression.
    null;
  end;

  return created_job;
end;
$function$;

DO $$
DECLARE e text;
BEGIN
  -- Comparaison SANS les retours a la ligne Windows : un copier-coller depuis Windows
  -- transforme \n en \r\n dans le corps, ce qui change l'empreinte sans changer une
  -- seule lettre du code (mesure du 08/10, point 5a).
  e := md5(replace(pg_get_functiondef('public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)'::regprocedure), chr(13), ''));
  RAISE NOTICE 'empreinte de la fonction reposee : % (attendu b8a89ff72095acb00dccbf3c857e90ab)', e;
  IF e <> 'b8a89ff72095acb00dccbf3c857e90ab' THEN
    RAISE EXCEPTION 'CONTROLE : la fonction reposee n''est pas celle d''avant (empreinte %)', e;
  END IF;
  IF has_function_privilege('anon', 'public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)', 'EXECUTE') THEN
    RAISE EXCEPTION 'CONTROLE : anon peut executer la fonction -- chantier ① casse';
  END IF;
END $$;

COMMIT;
