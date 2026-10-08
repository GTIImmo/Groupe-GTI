-- =====================================================================
-- REPETITION du POINT 5a -- NE CHANGE RIEN A LA BASE
-- Date : 2026-10-08 · Detail : notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md
--
-- Ce fichier joue LE VRAI patch (patch_5a_desarchiver_archive_2026-10-08.sql, recopie tel
-- quel sans son BEGIN/COMMIT), essaie le geste dans les quatre cas, PUIS joue le vrai
-- script inverse, PUIS leve volontairement une erreur : Postgres ANNULE TOUT.
-- En plus, chaque essai qui REUSSIT est annule tout de suite (savepoint) : meme au milieu
-- de la repetition, aucun travail de desarchivage n'existe une seconde de trop.
--
-- RESULTAT ATTENDU : une erreur rouge qui commence par « ESSAI ANNULE » et qui dit,
-- dans cet ordre :
--   role_vu_par_la_base=admin
--   avant_empreinte_fonction=d4f311d782c7525494107cc0596fdedc
--   avant_travaux_restore=15
--   avant_lignes_carnet=3
--   avant_patch_archive_15633=22023/dossier_not_found        <- le bug, reproduit
--   apres_archive_15633=job=restore_hektor_annonce dossier=NULL hektor=49544
--       statut=pending priorite=8 numero=VM69168 source=index_archives demandeur=pose
--   apres_dossier_vivant_3828957=dossier=3828957 hektor=62774 source=dossier_vivant
--       carnet=0/geste_desarchiver
--   apres_inconnu_999999999=22023/dossier_not_found
--   sans_session_archive_15633=42501/forbidden_restore
--   apres_travaux_restore=15                                 <- rien n'a ete laisse
--   apres_lignes_carnet=3
--   apres_droits=anon=non authenticated=oui service_role=oui
--   apres_inverse_empreinte=d4f311d782c7525494107cc0596fdedc <- identique a l'avant
--
-- Toute AUTRE erreur (« STOP », « CONTROLE », « aucun administrateur ») = un garde-fou a
-- parle : me la recopier, ne pas appliquer le patch.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='120s';

CREATE TEMP TABLE _e5a(ord int, cle text, val text);

-- ---------------------------------------------------------------------
-- 0. On se met dans la peau d'un administrateur actif, le temps de l'essai.
--    (sans cette identite, la fonction refuse : c'est le garde-fou des droits)
-- ---------------------------------------------------------------------
DO $$
DECLARE u uuid;
BEGIN
  SELECT id INTO u FROM public.app_user_profile WHERE role='admin' AND is_active ORDER BY id LIMIT 1;
  IF u IS NULL THEN RAISE EXCEPTION 'STOP : aucun administrateur actif dans app_user_profile'; END IF;
  PERFORM set_config('request.jwt.claims', json_build_object('sub', u)::text, true);
  INSERT INTO pg_temp._e5a VALUES (0,'role_vu_par_la_base', coalesce(public.app_console_current_role(),'(null)'));
END $$;

-- ---------------------------------------------------------------------
-- 1. L'ETAT DE DEPART
-- ---------------------------------------------------------------------
INSERT INTO pg_temp._e5a SELECT 1,'avant_empreinte_fonction',
  md5(pg_get_functiondef('public.app_restore_annonce_optimistic(bigint,jsonb,integer)'::regprocedure));
INSERT INTO pg_temp._e5a SELECT 2,'avant_travaux_restore', count(*)::text
  FROM public.app_console_job WHERE job_type='restore_hektor_annonce';
INSERT INTO pg_temp._e5a SELECT 3,'avant_lignes_carnet', count(*)::text FROM public.app_annonce_champ_app;

-- ---------------------------------------------------------------------
-- 2. LE BUG, REPRODUIT : l'archive 15633 (bien Hektor 49544, dossier VM69168)
-- ---------------------------------------------------------------------
DO $$
DECLARE s text;
BEGIN
  BEGIN
    PERFORM public.app_restore_annonce_optimistic(15633::bigint);
    s := 'AUCUNE_ERREUR(anormal)';
  EXCEPTION WHEN OTHERS THEN s := SQLSTATE||'/'||SQLERRM;
  END;
  INSERT INTO pg_temp._e5a VALUES (4,'avant_patch_archive_15633', s);
END $$;

-- ---------------------------------------------------------------------
-- 3. LE VRAI PATCH (corps recopie tel quel)
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
-- 4. LES QUATRE ESSAIS, SOUS IDENTITE D'ADMINISTRATEUR
--    Chaque essai qui reussit est ANNULE tout de suite : ce qu'on garde, c'est la
--    constatation (une variable PL/pgSQL ne s'annule pas), pas la ligne ecrite.
-- ---------------------------------------------------------------------
DO $$
DECLARE r jsonb; j record; info text;
BEGIN
  BEGIN
    r := public.app_restore_annonce_optimistic(15633::bigint);
    SELECT * INTO j FROM public.app_console_job WHERE id = (r->>'job_id')::uuid;
    info := 'job='||coalesce(j.job_type,'?')
         ||' dossier='||coalesce(j.app_dossier_id::text,'NULL')
         ||' hektor='||coalesce(j.hektor_annonce_id,'?')
         ||' statut='||coalesce(j.status,'?')
         ||' priorite='||coalesce(j.priority::text,'?')
         ||' numero='||coalesce(j.payload_json->>'numero_dossier','?')
         ||' source='||coalesce(j.payload_json->>'cible_source','?')
         ||' demandeur='||CASE WHEN j.requested_by IS NULL THEN 'NULL' ELSE 'pose' END;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN info := 'ERREUR '||SQLSTATE||'/'||SQLERRM; END IF;
  END;
  INSERT INTO pg_temp._e5a VALUES (5,'apres_archive_15633', coalesce(info,'(rien)'));
END $$;

DO $$
DECLARE r jsonb; j record; k record; info text;
BEGIN
  BEGIN
    r := public.app_restore_annonce_optimistic(3828957::bigint);
    SELECT * INTO j FROM public.app_console_job WHERE id = (r->>'job_id')::uuid;
    SELECT * INTO k FROM public.app_annonce_champ_app WHERE app_dossier_id=3828957 AND champ='archive';
    info := 'dossier='||coalesce(j.app_dossier_id::text,'NULL')
         ||' hektor='||coalesce(j.hektor_annonce_id,'?')
         ||' source='||coalesce(j.payload_json->>'cible_source','?')
         ||' carnet='||coalesce(k.valeur_app,'?')||'/'||coalesce(k.origine,'?');
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN info := 'ERREUR '||SQLSTATE||'/'||SQLERRM; END IF;
  END;
  INSERT INTO pg_temp._e5a VALUES (6,'apres_dossier_vivant_3828957', coalesce(info,'(rien)'));
END $$;

DO $$
DECLARE s text;
BEGIN
  BEGIN
    PERFORM public.app_restore_annonce_optimistic(999999999::bigint);
    s := 'AUCUNE_ERREUR(anormal)';
  EXCEPTION WHEN OTHERS THEN s := SQLSTATE||'/'||SQLERRM;
  END;
  INSERT INTO pg_temp._e5a VALUES (7,'apres_inconnu_999999999', s);
END $$;

DO $$
DECLARE s text;
BEGIN
  PERFORM set_config('request.jwt.claims', '', true);
  BEGIN
    PERFORM public.app_restore_annonce_optimistic(15633::bigint);
    s := 'AUCUNE_ERREUR(anormal)';
  EXCEPTION WHEN OTHERS THEN s := SQLSTATE||'/'||SQLERRM;
  END;
  INSERT INTO pg_temp._e5a VALUES (8,'sans_session_archive_15633', s);
END $$;

INSERT INTO pg_temp._e5a SELECT 9,'apres_travaux_restore', count(*)::text
  FROM public.app_console_job WHERE job_type='restore_hektor_annonce';
INSERT INTO pg_temp._e5a SELECT 10,'apres_lignes_carnet', count(*)::text FROM public.app_annonce_champ_app;
INSERT INTO pg_temp._e5a SELECT 11,'apres_droits',
  'anon='||CASE WHEN has_function_privilege('anon','public.app_restore_annonce_optimistic(bigint,jsonb,integer)','EXECUTE') THEN 'oui' ELSE 'non' END
  ||' authenticated='||CASE WHEN has_function_privilege('authenticated','public.app_restore_annonce_optimistic(bigint,jsonb,integer)','EXECUTE') THEN 'oui' ELSE 'non' END
  ||' service_role='||CASE WHEN has_function_privilege('service_role','public.app_restore_annonce_optimistic(bigint,jsonb,integer)','EXECUTE') THEN 'oui' ELSE 'non' END;

-- ---------------------------------------------------------------------
-- 5. LE VRAI SCRIPT INVERSE (corps recopie tel quel)
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

INSERT INTO pg_temp._e5a SELECT 12,'apres_inverse_empreinte',
  md5(pg_get_functiondef('public.app_restore_annonce_optimistic(bigint,jsonb,integer)'::regprocedure));

-- ---------------------------------------------------------------------
-- 6. L'ERREUR VOLONTAIRE : elle annule la repetition en entier.
-- ---------------------------------------------------------------------
DO $$
DECLARE msg text;
BEGIN
  SELECT string_agg(cle||'='||val, ' || ' ORDER BY ord) INTO msg FROM pg_temp._e5a;
  RAISE EXCEPTION 'ESSAI ANNULE -- %', msg;
END $$;
