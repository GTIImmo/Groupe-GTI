-- =====================================================================
-- REPETITION du POINT 5b -- NE CHANGE RIEN A LA BASE  (version 2)
-- Date : 2026-10-08 · Detail : notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md
--
-- ⚠ VERSION 2. La v1 a echoue sur `missing_contact_email` : ma charge d'essai n'avait
--   pas d'e-mail, et le garde-fou d'origine (app_console_create_update_mandant_contact_job)
--   l'exige, comme il exige un nom. Il a donc fait son travail. La charge est desormais
--   construite DEPUIS LA BASE -- aucun e-mail de client n'est ecrit dans ce fichier.
--
-- Elle joue LE VRAI patch (patch_5b_mandant_identite_2026-10-08.sql, recopie sans son
-- BEGIN/COMMIT ni son garde-fou), essaie le geste AVANT et APRES, PUIS joue le vrai
-- script inverse, PUIS leve volontairement une erreur : Postgres ANNULE TOUT.
-- Chaque essai qui ECRIT est en plus annule immediatement (savepoint) : aucun travail
-- pour Hektor, aucune modification de contact n'existe une seconde de trop.
--
-- LE CAS D'ESSAI, pris dans la vraie base : annonce 63244 (V430063244),
-- mandant « MARTINS FERNANDES » -- identite 10025872, cible Hektor 48422,
-- ville actuelle « Saint-André-le-Puy ». On lui envoie la ville « ESSAI 5B ».
--
-- RESULTAT ATTENDU : une erreur rouge « ESSAI ANNULE » qui dit, dans cet ordre :
--   role_vu_par_la_base=admin
--   avant_empreinte=b8a89ff72095acb00dccbf3c857e90ab
--   avant_travaux_mandant=9
--   avant_lignes_attente=0
--   avant_ville=Saint-André-le-Puy
--   AVANT_PATCH=travail cree=oui | ville apres=Saint-André-le-Puy | attente=0
--        <- LE BUG : le travail part, mais RIEN n'est ecrit chez nous
--   APRES_PATCH=travail cree=oui | ville apres=ESSAI 5B | attente=1 | travail designe=oui
--        <- repare : la valeur est chez nous ET le double envoi est verrouille
--   APRES_PATCH_identite_directe=ville apres=ESSAI 5B BIS   <- le repli marche aussi
--   apres_travaux_mandant=9   apres_lignes_attente=0   apres_ville=Saint-André-le-Puy
--        <- rien n'a ete laisse derriere
--   apres_droits=anon=non authenticated=oui service_role=oui
--   apres_inverse_empreinte=b8a89ff72095acb00dccbf3c857e90ab   <- identique a l'avant
--
-- Toute AUTRE erreur (« STOP », « CONTROLE ») = un garde-fou a parle : me la recopier,
-- ne pas appliquer le patch.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='120s';

CREATE TEMP TABLE _e5b(ord int, cle text, val text);

-- ---------------------------------------------------------------------
-- 0. On se met dans la peau d'un administrateur actif, le temps de l'essai.
-- ---------------------------------------------------------------------
DO $$
DECLARE u uuid;
BEGIN
  SELECT id INTO u FROM public.app_user_profile WHERE role='admin' AND is_active ORDER BY id LIMIT 1;
  IF u IS NULL THEN RAISE EXCEPTION 'STOP : aucun administrateur actif dans app_user_profile'; END IF;
  PERFORM set_config('request.jwt.claims', json_build_object('sub', u)::text, true);
  INSERT INTO pg_temp._e5b VALUES (0,'role_vu_par_la_base', coalesce(public.app_console_current_role(),'(null)'));
END $$;

-- ---------------------------------------------------------------------
-- 1. L'ETAT DE DEPART
-- ---------------------------------------------------------------------
INSERT INTO pg_temp._e5b SELECT 1,'avant_empreinte',
  md5(replace(pg_get_functiondef('public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)'::regprocedure), chr(13), ''));
INSERT INTO pg_temp._e5b SELECT 2,'avant_travaux_mandant', count(*)::text
  FROM public.app_console_job WHERE job_type='update_hektor_mandant_contact';
INSERT INTO pg_temp._e5b SELECT 3,'avant_lignes_attente', count(*)::text
  FROM public.app_contact_pending WHERE hektor_contact_id='10025872';
INSERT INTO pg_temp._e5b SELECT 4,'avant_ville', coalesce(ville,'(vide)')
  FROM public.app_contact_current WHERE hektor_contact_id='10025872';

-- ---------------------------------------------------------------------
-- 2. LE BUG, REPRODUIT : on joue le geste tel que l'ecran l'envoie (cible 48422)
-- ---------------------------------------------------------------------
DO $$
DECLARE j public.app_console_job; info text; v_ville text; v_attente int; v_charge jsonb;
BEGIN
  -- La charge est construite DEPUIS LA BASE : nom et e-mail reels (le garde-fou les
  -- exige), sans qu'aucune donnee de client ne figure dans ce fichier.
  SELECT jsonb_build_object(
           'hektor_contact_id','48422', 'contact_id','48422',
           'last_name', coalesce(nullif(trim(c.nom),''),  'MANDANT ESSAI'),
           'email',     coalesce(nullif(trim(c.email),''),'essai-5b@gti-immobilier.fr'),
           'city',      'ESSAI 5B')
    INTO v_charge
    FROM public.app_contact_current c WHERE c.hektor_contact_id='10025872';

  BEGIN
    j := public.app_update_mandant_contact_optimistic(7589229::bigint, '63244', '48422', v_charge, 16);
    SELECT coalesce(ville,'(vide)') INTO v_ville FROM public.app_contact_current WHERE hektor_contact_id='10025872';
    SELECT count(*) INTO v_attente FROM public.app_contact_pending WHERE hektor_contact_id='10025872';
    info := 'travail cree=' || CASE WHEN j.id IS NULL THEN 'non' ELSE 'oui' END
         || ' | ville apres=' || v_ville || ' | attente=' || v_attente::text;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN info := 'ERREUR ' || SQLSTATE || '/' || SQLERRM; END IF;
  END;
  INSERT INTO pg_temp._e5b VALUES (5,'AVANT_PATCH', coalesce(info,'(rien)'));
END $$;

-- ---------------------------------------------------------------------
-- 3. LE VRAI PATCH (corps recopie tel quel)
-- ---------------------------------------------------------------------
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
  v_identite  text;
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
      -- ── 2bis. TRADUIRE LA CIBLE EN IDENTITE ── 5b, 08/10/2026 ───────────────
      --   L'ecran envoie `hektor_target_id`, LE NUMERO DE HEKTOR (App.tsx:7272,
      --   et c'est lui qu'il faut pour detacher un mandant). Or
      --   app_edit_contact_optimistic cherche par `hektor_contact_id`, qui porte
      --   NOTRE numero depuis la bascule du 23/09. Mesure du 08/10 : sur 62 162
      --   contacts, les deux numeros different pour 62 162 d'entre eux -- l'appel
      --   levait donc `contact_not_found` A TOUS LES COUPS, et le `exception when
      --   others` ci-dessous l'effacait. Ni valeur chez nous, ni ligne d'attente,
      --   ni nouvel essai. On traduit ici, une fois, au seul endroit qui en a besoin.
      select c.hektor_contact_id into v_identite
        from public.app_contact_current c
       where c.hektor_target_id = target_contact_id
       limit 1;

      if v_identite is null then
        -- Repli : l'appelant a peut-etre deja envoye l'identite.
        select c.hektor_contact_id into v_identite
          from public.app_contact_current c
         where c.hektor_contact_id = target_contact_id
         limit 1;
      end if;

      if v_identite is null then
        raise exception 'contact_not_found' using errcode = '22023';
      end if;

      perform public.app_edit_contact_optimistic(v_identite, champs);

      -- ── 3. UN SEUL ENVOI : on designe NOTRE travail au balayage ──
      update public.app_contact_pending
         set push_job_id = created_job.id, updated_at = now()
       where hektor_contact_id = v_identite;
    end if;
  exception when others then
    -- Le geste part quand meme chez Hektor. L'app n'aura simplement pas la
    -- valeur d'avance -- c'est le comportement d'avant, pas une regression.
    null;
  end;

  return created_job;
end;
$function$;

-- ---------------------------------------------------------------------
-- 4. LE MEME GESTE, APRES LE PATCH -- puis annule tout de suite.
-- ---------------------------------------------------------------------
DO $$
DECLARE j public.app_console_job; info text; v_ville text; v_attente int; v_designe int; v_charge jsonb;
BEGIN
  SELECT jsonb_build_object(
           'hektor_contact_id','48422', 'contact_id','48422',
           'last_name', coalesce(nullif(trim(c.nom),''),  'MANDANT ESSAI'),
           'email',     coalesce(nullif(trim(c.email),''),'essai-5b@gti-immobilier.fr'),
           'city',      'ESSAI 5B')
    INTO v_charge
    FROM public.app_contact_current c WHERE c.hektor_contact_id='10025872';

  BEGIN
    j := public.app_update_mandant_contact_optimistic(7589229::bigint, '63244', '48422', v_charge, 16);
    SELECT coalesce(ville,'(vide)') INTO v_ville FROM public.app_contact_current WHERE hektor_contact_id='10025872';
    SELECT count(*) INTO v_attente FROM public.app_contact_pending WHERE hektor_contact_id='10025872';
    SELECT count(*) INTO v_designe FROM public.app_contact_pending
     WHERE hektor_contact_id='10025872' AND push_job_id = j.id;
    info := 'travail cree=' || CASE WHEN j.id IS NULL THEN 'non' ELSE 'oui' END
         || ' | ville apres=' || v_ville || ' | attente=' || v_attente::text
         || ' | travail designe=' || CASE WHEN v_designe > 0 THEN 'oui' ELSE 'non' END;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN info := 'ERREUR ' || SQLSTATE || '/' || SQLERRM; END IF;
  END;
  INSERT INTO pg_temp._e5b VALUES (6,'APRES_PATCH', coalesce(info,'(rien)'));
END $$;

-- Le repli : si l'appelant envoie deja NOTRE numero, ca doit marcher aussi.
DO $$
DECLARE j public.app_console_job; info text; v_ville text; v_charge jsonb;
BEGIN
  SELECT jsonb_build_object(
           'hektor_contact_id','10025872', 'contact_id','10025872',
           'last_name', coalesce(nullif(trim(c.nom),''),  'MANDANT ESSAI'),
           'email',     coalesce(nullif(trim(c.email),''),'essai-5b@gti-immobilier.fr'),
           'city',      'ESSAI 5B BIS')
    INTO v_charge
    FROM public.app_contact_current c WHERE c.hektor_contact_id='10025872';

  BEGIN
    j := public.app_update_mandant_contact_optimistic(7589229::bigint, '63244', '10025872', v_charge, 16);
    SELECT coalesce(ville,'(vide)') INTO v_ville FROM public.app_contact_current WHERE hektor_contact_id='10025872';
    info := 'ville apres=' || v_ville;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN info := 'ERREUR ' || SQLSTATE || '/' || SQLERRM; END IF;
  END;
  INSERT INTO pg_temp._e5b VALUES (7,'APRES_PATCH_identite_directe', coalesce(info,'(rien)'));
END $$;

-- ---------------------------------------------------------------------
-- 5. RIEN N'A ETE LAISSE DERRIERE
-- ---------------------------------------------------------------------
INSERT INTO pg_temp._e5b SELECT 8,'apres_travaux_mandant', count(*)::text
  FROM public.app_console_job WHERE job_type='update_hektor_mandant_contact';
INSERT INTO pg_temp._e5b SELECT 9,'apres_lignes_attente', count(*)::text
  FROM public.app_contact_pending WHERE hektor_contact_id='10025872';
INSERT INTO pg_temp._e5b SELECT 10,'apres_ville', coalesce(ville,'(vide)')
  FROM public.app_contact_current WHERE hektor_contact_id='10025872';
INSERT INTO pg_temp._e5b SELECT 11,'apres_droits',
  'anon='||CASE WHEN has_function_privilege('anon','public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)','EXECUTE') THEN 'oui' ELSE 'non' END
  ||' authenticated='||CASE WHEN has_function_privilege('authenticated','public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)','EXECUTE') THEN 'oui' ELSE 'non' END
  ||' service_role='||CASE WHEN has_function_privilege('service_role','public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)','EXECUTE') THEN 'oui' ELSE 'non' END;

-- ---------------------------------------------------------------------
-- 6. LE VRAI SCRIPT INVERSE (corps recopie tel quel)
-- ---------------------------------------------------------------------
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

INSERT INTO pg_temp._e5b SELECT 12,'apres_inverse_empreinte',
  md5(replace(pg_get_functiondef('public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)'::regprocedure), chr(13), ''));

-- ---------------------------------------------------------------------
-- 7. L'ERREUR VOLONTAIRE : elle annule la repetition en entier.
-- ---------------------------------------------------------------------
DO $$
DECLARE msg text;
BEGIN
  SELECT string_agg(cle||'='||val, ' || ' ORDER BY ord) INTO msg FROM pg_temp._e5b;
  RAISE EXCEPTION 'ESSAI ANNULE -- %', msg;
END $$;
