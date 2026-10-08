-- =====================================================================
-- CHANTIER ⑤ · POINT 5a -- DESARCHIVER REDEVIENT POSSIBLE
-- Date : 2026-10-08 · Detail : notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md
--
-- LE PROBLEME. Depuis le commit e7b9df7 du 30/08/2026 09:43, le bouton
-- « Desarchiver » passe par app_restore_annonce_optimistic, dont la premiere ligne
-- cherche le bien dans app_dossier_current. Un bien ARCHIVE n'y est jamais :
-- 35 317 archives, 0 presente (mesure du 08/10). Tout desarchivage leve donc
-- `dossier_not_found`, affiche tel quel a l'ecran (App.tsx:13869). Dernier
-- desarchivage reussi : 30/08 a 07:42:21 UTC, UNE MINUTE avant ce commit.
--
-- LE CORRECTIF, ADDITIF. On garde le chemin du bien vivant mot pour mot et on ajoute
-- un SECOND chemin : si le numero n'est pas un dossier, on le cherche dans
-- app_archive_annonce_index_current par `app_archive_id` -- exactement le numero que
-- l'ecran envoie pour une archive (api.ts:2618). Le travail est alors cree avec le bon
-- `hektor_annonce_id` et `app_dossier_id` a NULL (colonne nullable, sans cle etrangere).
-- Un numero qui n'est ni un dossier ni une archive leve toujours `dossier_not_found`.
--
-- CE QUI NE CHANGE PAS (verifie, voir la note) :
--   · le chemin du bien vivant : meme code, meme carnet, meme travail ;
--   · le front : AUCUNE ligne modifiee, AUCUN deploiement ;
--   · le worker (4 services) : il n'utilise que hektor_annonce_id et tolere
--     app_dossier_id nul (console_job_worker.js:18406-18453) -- aucun redemarrage ;
--   · les droits : admin ou manager, controle par app_console_can_request_job,
--     qui ne se sert pas du numero de dossier ;
--   · le chantier ① : `create or replace` CONSERVE l'ACL de la fonction
--     (authenticated + service_role, PAS anon). Ce patch ne fait JAMAIS `drop function`,
--     qui rouvrirait la fonction a tout le monde ;
--   · le run de nuit, les crons, phase2, les pages publiques : aucun ne l'appelle.
--
-- RETOUR ARRIERE : supabase/patch_5a_desarchiver_archive_2026-10-08_INVERSE.sql
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

-- ---------------------------------------------------------------------
-- 0. GARDE-FOU D'ENTREE : la base est bien celle qu'on a mesuree.
-- ---------------------------------------------------------------------
DO $$
DECLARE n int; m int;
BEGIN
  IF to_regclass('public.app_archive_annonce_index_current') IS NULL THEN
    RAISE EXCEPTION 'STOP : app_archive_annonce_index_current est introuvable';
  END IF;
  SELECT count(*) INTO n FROM pg_attribute
   WHERE attrelid='public.app_archive_annonce_index_current'::regclass
     AND attname IN ('app_archive_id','hektor_annonce_id','numero_dossier','titre_bien')
     AND NOT attisdropped;
  IF n <> 4 THEN RAISE EXCEPTION 'STOP : l''index des archives n''a pas les 4 colonnes attendues (%)', n; END IF;
  SELECT count(*) INTO m FROM pg_attribute
   WHERE attrelid='public.app_console_job'::regclass AND attname='app_dossier_id' AND attnotnull;
  IF m <> 0 THEN RAISE EXCEPTION 'STOP : app_console_job.app_dossier_id est devenu NOT NULL'; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE oid='public.app_restore_annonce_optimistic(bigint,jsonb,integer)'::regprocedure) THEN
    RAISE EXCEPTION 'STOP : la fonction a desarchiver n''existe pas sous cette signature';
  END IF;
END $$;

-- ---------------------------------------------------------------------
-- 1. LA FONCTION
-- ---------------------------------------------------------------------
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
  d         app_dossier_current%rowtype;
  v_job_id  uuid;
  v_charge  jsonb;
  v_dossier bigint;
  v_hektor  text;
  v_numero  text;
  v_titre   text;
  v_source  text;
begin
  -- 1. LE BIEN VIVANT -- le chemin d'origine (C.4, 30/08), mot pour mot.
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if found then
    v_dossier := target_dossier_id;
    v_hektor  := d.hektor_annonce_id::text;
    v_numero  := d.numero_dossier;
    v_titre   := d.titre_bien;
    v_source  := 'dossier_vivant';
  else
    -- 2. LE BIEN ARCHIVE -- 5a, ajoute le 08/10/2026.
    --    Une archive n'est JAMAIS dans app_dossier_current : 35 317 archives, 0 presente
    --    (mesure du 08/10). L'index des archives n'a pas de numero de dossier ; l'ecran
    --    envoie donc son `app_archive_id` a cette place (api.ts:2618). C'est par la qu'on
    --    la retrouve. Sans ce chemin, le geste levait `dossier_not_found` pour TOUTES les
    --    archives depuis le 30/08 (dernier desarchivage reussi : 30/08 a 07:42 UTC).
    select a.hektor_annonce_id::text, a.numero_dossier, a.titre_bien
      into v_hektor, v_numero, v_titre
      from public.app_archive_annonce_index_current a
     where a.app_archive_id = target_dossier_id;
    if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;
    v_dossier := null;   -- nous n'avons AUCUN numero de dossier pour une archive
    v_source  := 'index_archives';
  end if;

  if not public.app_console_can_request_job('restore_hektor_annonce',
                                            v_dossier, v_hektor) then
    raise exception 'forbidden_restore' using errcode = '42501';
  end if;

  -- 3. CHEZ NOUS D'ABORD -- quand il y a un « chez nous ». Le carnet est range par
  --    numero de dossier ; pour une archive il n'y en a pas, et y ecrire le numero
  --    d'archive serait poser un FAUX identifiant (la faute meme de 5d et 5g). Ce carnet
  --    n'applique rien pour l'annonce (phase2/identite/magasin_annonce_app.py) :
  --    l'intention est portee par le travail, cree dans la MEME transaction juste apres.
  if v_dossier is not null then
    insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_par)
    values (v_dossier, 'archive', '0', 'geste_desarchiver', auth.uid()::text)
    on conflict (app_dossier_id, champ) do update
       set valeur_app = excluded.valeur_app,
           origine    = excluded.origine,
           ecrit_le   = now(),
           ecrit_par  = excluded.ecrit_par;
  end if;

  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier', v_numero,
    'titre_bien',     v_titre,
    'target_archive', '0',
    'cible_source',   v_source);

  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  values
    ('restore_hektor_annonce', v_dossier, v_hektor,
     v_charge, coalesce(job_priority, 8), auth.uid())
  returning id into v_job_id;

  return jsonb_build_object('job_id', v_job_id,
                            'app_dossier_id', v_dossier,
                            'hektor_annonce_id', v_hektor,
                            'champ', 'archive',
                            'valeur_app', '0');
end
$function$;

-- ---------------------------------------------------------------------
-- 9. CONTROLE DE SORTIE : un seul point faux -> exception -> rien n'est applique.
-- ---------------------------------------------------------------------
DO $$
DECLARE anon_peut boolean; auth_peut boolean; svc_peut boolean;
BEGIN
  anon_peut := has_function_privilege('anon',          'public.app_restore_annonce_optimistic(bigint,jsonb,integer)', 'EXECUTE');
  auth_peut := has_function_privilege('authenticated', 'public.app_restore_annonce_optimistic(bigint,jsonb,integer)', 'EXECUTE');
  svc_peut  := has_function_privilege('service_role',  'public.app_restore_annonce_optimistic(bigint,jsonb,integer)', 'EXECUTE');
  IF anon_peut THEN RAISE EXCEPTION 'CONTROLE : anon peut executer la fonction -- chantier ① casse'; END IF;
  IF NOT auth_peut THEN RAISE EXCEPTION 'CONTROLE : authenticated a PERDU le droit d''executer la fonction'; END IF;
  IF NOT svc_peut THEN RAISE EXCEPTION 'CONTROLE : service_role a PERDU le droit d''executer la fonction'; END IF;
  RAISE NOTICE 'droits apres patch : anon=non authenticated=oui service_role=oui';
  -- Empreinte, retours a la ligne Windows retires (un copier-coller depuis Windows pose
  -- des \r\n dans le corps : cela change l'empreinte sans changer une lettre du code).
  RAISE NOTICE 'empreinte de la fonction posee : % (attendu 709571469083a76b1be384e879ca523b)',
    md5(replace(pg_get_functiondef('public.app_restore_annonce_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), ''));
END $$;

COMMIT;
