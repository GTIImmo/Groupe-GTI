-- =====================================================================
-- REPETITION du patch « ARCHIVER + NEGOCIATEUR sur un vendu / clos » -- 12/10/2026
--
-- A COLLER DANS : https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- ⚠ ELLE N'ECRIT RIEN : une seule transaction, qui finit par une erreur volontaire.
--   Recopie-moi le message.
--
-- LES HUIT ESSAIS, sur les VRAIES fonctions, sous l'identite de Frederic (admin) :
--   A1  ARCHIVER un VENDU (bien 284 / annonce 107)   -> doit MARCHER, vrai numero, carnet ecrit
--   A2  ARCHIVER une ARCHIVE (49544)                 -> refus `annonce_deja_archivee`
--   A3  ARCHIVER un bien VIVANT (62774)              -> INCHANGE
--   B1  NEGOCIATEUR sur le VENDU                     -> doit MARCHER, vrai numero
--   B2  NEGOCIATEUR sur l'ARCHIVE                    -> refus `annonce_archivee_lecture_seule`
--   B3  NEGOCIATEUR sur le bien VIVANT               -> INCHANGE
--   C1  ARCHIVER un numero inventé                   -> `dossier_not_found`
--   C2  NEGOCIATEUR un numero inventé                -> `dossier_not_found`
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '180s';

DO $rep$
DECLARE
  sigs  constant text[] := ARRAY[
    'public.app_archive_annonce_optimistic(bigint,jsonb,integer)',
    'public.app_assign_negotiator_optimistic(bigint,text,jsonb,integer)'];
  emps  constant text[] := ARRAY[
    'b9bf9d40d32be0a16959ee4a35548ac9',
    '275f8d9d1000fb4100889c10314c8cf5'];
  refus constant text[] := ARRAY['annonce_deja_archivee', 'annonce_archivee_lecture_seule'];

  c_moi  constant text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6"}';
  c_hist constant bigint := 284;        -- index HISTORIQUE, annonce Hektor 107 (Vendu)
  c_vif  constant bigint := 3828957;    -- parc VIVANT, annonce Hektor 62774
  c_arch constant bigint := 15633;      -- index des ARCHIVES, annonce Hektor 49544
  c_faux constant bigint := 999999999;

  c_ancre text; v_bloc text; v_def text; v_apres text; v_retour text;
  i int; n int;

  m_av text := ''; m_anc text := ''; m_nue text := ''; m_fin text := ''; m_marq text := '';
  blocs text[] := ARRAY[''::text, ''::text];

  a1 jsonb; a1_dossier text; a1_hektor text; a1_carnet text;
  a2 text;
  a3 jsonb; a3_dossier text;
  b1 jsonb; b1_dossier text; b1_hektor text; b1_carnet text;
  b2 text;
  b3 jsonb; b3_dossier text;
  c1 text; c2 text;

  rapport text;
BEGIN
  c_ancre := replace($anc$  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;$anc$, chr(13), '');

  -- ═══ 1. AVANT + LE VRAI PATCH, fonction par fonction ═══
  FOR i IN 1 .. 2 LOOP
    v_def := replace(pg_get_functiondef(sigs[i]::regprocedure), chr(13), '');
    m_av  := m_av || split_part(sigs[i], '.', 2) || '=' || md5(v_def) || '  ';
    IF md5(v_def) <> emps[i] THEN
      RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- % porte % au lieu de %', sigs[i], md5(v_def), emps[i];
    END IF;
    IF position('@repli-debut' in v_def) > 0 THEN
      RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- % porte deja le repli', sigs[i];
    END IF;

    n := (length(v_def) - length(replace(v_def, c_ancre, ''))) / length(c_ancre);
    m_anc := m_anc || split_part(sigs[i], '.', 2) || '=' || n || '  ';
    IF n <> 1 THEN RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- ancre trouvee % fois dans %', n, sigs[i]; END IF;

    v_bloc := replace(replace($bloc$  -- @repli-debut   CHANTIER 3 (12/10/2026) : LE BIEN PEUT ETRE VENDU OU CLOS
  --
  -- LA REGLE DE LA MAISON, telle que l'ECRAN la porte depuis le 21/05/2026
  -- (`isReadOnlyLightweightDetail`, App.tsx:406-411), confirmee par Frederic le 12/10 :
  --     · VENDU / CLOS  -> les gestes marchent (l'ecran les ouvre des que le detail est la)
  --     · ARCHIVE       -> LECTURE SEULE, sa seule sortie est « Desarchiver »
  --
  -- Depuis le 20/05, les Vendu/Clos ne sont plus dans app_dossier_current : ils vivent dans
  -- `app_historical_annonce_index_current`. Les RPC « optimistes », ecrites les 25 et 30/08,
  -- l'ignoraient et refusaient 8 941 biens sur un « dossier_not_found » brut -- alors que
  -- l'ecran, lui, affichait le bouton. L'ecran a trois etats, la base n'en avait qu'un.
  --
  -- ⭐ LE NUMERO RECU EST LE BON : `app_historical_id` EST notre `app_dossier_id`, renomme
  --   (export_app_payload.py:363), verifie par les anciens travaux des memes biens. On le
  --   garde donc TEL QUEL pour les droits, le carnet et le travail.
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then
    select h.app_historical_id, h.hektor_annonce_id, h.numero_dossier, h.titre_bien,
           h.statut_annonce, h.diffusable, h.archive, h.negociateur_email
      into d.app_dossier_id, d.hektor_annonce_id, d.numero_dossier, d.titre_bien,
           d.statut_annonce, d.diffusable, d.archive, d.negociateur_email
      from public.app_historical_annonce_index_current h
     where h.app_historical_id = target_dossier_id;

    if not found then
      -- UNE ARCHIVE RESTE EN LECTURE SEULE -- c'est voulu, pas un oubli. On le DIT, au lieu
      -- de rendre « dossier_not_found », qui ne veut rien dire pour celui qui lit.
      if exists (select 1 from public.app_archive_annonce_index_current x
                  where x.app_archive_id = target_dossier_id) then
        raise exception '__REFUS__' using errcode = '22023';
      end if;
      raise exception 'dossier_not_found' using errcode = '22023';
    end if;
  end if;
  -- @repli-fin$bloc$, chr(13), ''), '__REFUS__', refus[i]);

    blocs[i] := v_bloc;
    EXECUTE replace(v_def, c_ancre, v_bloc);

    v_retour := replace(replace(pg_get_functiondef(sigs[i]::regprocedure), chr(13), ''), v_bloc, c_ancre);
    m_nue := m_nue || split_part(sigs[i], '.', 2) || '=' || md5(v_retour) || '  ';
  END LOOP;

  -- ═══ A1 -- ARCHIVER un VENDU : doit MARCHER ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    a1 := public.app_archive_annonce_optimistic(c_hist, '{}'::jsonb, 8);
    SELECT coalesce(app_dossier_id::text,'NULL'), coalesce(hektor_annonce_id,'(vide)')
      INTO a1_dossier, a1_hektor
      FROM public.app_console_job WHERE id = (a1->>'job_id')::uuid;
    SELECT string_agg(champ||'='||valeur_app, ' | ' ORDER BY champ) INTO a1_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_hist;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN
      a1_dossier := 'ERREUR: ' || SQLERRM; a1_hektor := '-'; a1_carnet := '-';
    END IF;
  END;

  -- ═══ A2 -- ARCHIVER une ARCHIVE : doit etre REFUSE ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_archive_annonce_optimistic(c_arch, '{}'::jsonb, 8);
    a2 := '(AUCUNE ERREUR -- ANORMAL)';
  EXCEPTION WHEN others THEN a2 := SQLERRM;
  END;

  -- ═══ A3 -- ARCHIVER un bien VIVANT : INCHANGE ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    a3 := public.app_archive_annonce_optimistic(c_vif, '{}'::jsonb, 8);
    SELECT coalesce(app_dossier_id::text,'NULL') INTO a3_dossier
      FROM public.app_console_job WHERE id = (a3->>'job_id')::uuid;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN a3_dossier := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ B1 -- NEGOCIATEUR sur le VENDU : doit MARCHER ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    b1 := public.app_assign_negotiator_optimistic(
            c_hist, '12345',
            '{"target_hektor_user_email":"essai.repetition@gti-immobilier.fr"}'::jsonb, 9);
    SELECT coalesce(app_dossier_id::text,'NULL'), coalesce(hektor_annonce_id,'(vide)')
      INTO b1_dossier, b1_hektor
      FROM public.app_console_job WHERE id = (b1->>'job_id')::uuid;
    SELECT string_agg(champ||'='||valeur_app, ' | ' ORDER BY champ) INTO b1_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_hist;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN
      b1_dossier := 'ERREUR: ' || SQLERRM; b1_hektor := '-'; b1_carnet := '-';
    END IF;
  END;

  -- ═══ B2 -- NEGOCIATEUR sur une ARCHIVE : doit etre REFUSE ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_assign_negotiator_optimistic(c_arch, '12345', '{}'::jsonb, 9);
    b2 := '(AUCUNE ERREUR -- ANORMAL)';
  EXCEPTION WHEN others THEN b2 := SQLERRM;
  END;

  -- ═══ B3 -- NEGOCIATEUR sur un bien VIVANT : INCHANGE ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    b3 := public.app_assign_negotiator_optimistic(
            c_vif, '12345',
            '{"target_hektor_user_email":"essai.repetition@gti-immobilier.fr"}'::jsonb, 9);
    SELECT coalesce(app_dossier_id::text,'NULL') INTO b3_dossier
      FROM public.app_console_job WHERE id = (b3->>'job_id')::uuid;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN b3_dossier := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ C1 / C2 -- numero inventé : « dossier_not_found » conserve ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_archive_annonce_optimistic(c_faux, '{}'::jsonb, 8);
    c1 := '(AUCUNE ERREUR -- ANORMAL)';
  EXCEPTION WHEN others THEN c1 := SQLERRM;
  END;
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_assign_negotiator_optimistic(c_faux, '12345', '{}'::jsonb, 9);
    c2 := '(AUCUNE ERREUR -- ANORMAL)';
  EXCEPTION WHEN others THEN c2 := SQLERRM;
  END;

  -- ═══ LE VRAI INVERSE ═══
  FOR i IN 1 .. 2 LOOP
    v_def := replace(replace(pg_get_functiondef(sigs[i]::regprocedure), chr(13), ''), blocs[i], c_ancre);
    IF md5(v_def) <> emps[i] THEN
      RAISE EXCEPTION 'INVERSE IMPOSSIBLE -- % rend % au lieu de %', sigs[i], md5(v_def), emps[i];
    END IF;
    EXECUTE v_def;
    v_apres := replace(pg_get_functiondef(sigs[i]::regprocedure), chr(13), '');
    m_fin  := m_fin  || split_part(sigs[i], '.', 2) || '=' || md5(v_apres) || '  ';
    m_marq := m_marq || split_part(sigs[i], '.', 2) || '='
              || ((length(v_apres) - length(replace(v_apres, '@repli', ''))) / 6) || '  ';
  END LOOP;

  rapport :=
    'ESSAI ANNULE -- rien n''a ete ecrit. Mesures :'
    || chr(10) || '--- 1. AVANT ------------------------------------------------------'
    || chr(10) || 'empreintes : ' || m_av
    || chr(10) || '  (attendu archive=b9bf9d40d32be0a16959ee4a35548ac9  assign=275f8d9d1000fb4100889c10314c8cf5)'
    || chr(10) || 'ancres     : ' || m_anc || ' (attendu 1 et 1)'
    || chr(10) || '--- 2. APRES LE PATCH ---------------------------------------------'
    || chr(10) || 'empreintes NUES (bloc retire) : ' || m_nue
    || chr(10) || '  (attendu = les empreintes d''AVANT : RIEN D''AUTRE N''A CHANGE)'
    || chr(10) || '--- A1. ARCHIVER un VENDU (bien 284 / annonce 107) ----------------'
    || chr(10) || 'travail.app_dossier_id = ' || coalesce(a1_dossier,'?') || '   (attendu 284 -- NOTRE vrai numero)'
    || chr(10) || 'travail.hektor_id      = ' || coalesce(a1_hektor,'?')  || '   (attendu 107)'
    || chr(10) || 'carnet                 = ' || coalesce(a1_carnet,'?')  || '   (attendu archive=1)'
    || chr(10) || '--- A2. ARCHIVER une ARCHIVE (doit etre REFUSE) -------------------'
    || chr(10) || 'message = ' || coalesce(a2,'?') || '   (attendu annonce_deja_archivee)'
    || chr(10) || '--- A3. ARCHIVER un bien VIVANT (INCHANGE) ------------------------'
    || chr(10) || 'travail.app_dossier_id = ' || coalesce(a3_dossier,'?') || '   (attendu 3828957)'
    || chr(10) || '--- B1. NEGOCIATEUR sur le VENDU ----------------------------------'
    || chr(10) || 'travail.app_dossier_id = ' || coalesce(b1_dossier,'?') || '   (attendu 284)'
    || chr(10) || 'travail.hektor_id      = ' || coalesce(b1_hektor,'?')  || '   (attendu 107)'
    || chr(10) || 'carnet                 = ' || coalesce(b1_carnet,'?')  || '   (attendu negociateur_email=essai.repetition@…)'
    || chr(10) || '--- B2. NEGOCIATEUR sur une ARCHIVE (doit etre REFUSE) ------------'
    || chr(10) || 'message = ' || coalesce(b2,'?') || '   (attendu annonce_archivee_lecture_seule)'
    || chr(10) || '--- B3. NEGOCIATEUR sur un bien VIVANT (INCHANGE) -----------------'
    || chr(10) || 'travail.app_dossier_id = ' || coalesce(b3_dossier,'?') || '   (attendu 3828957)'
    || chr(10) || '--- C. numeros inventés (doivent rester REFUSES) ------------------'
    || chr(10) || 'archiver    = ' || coalesce(c1,'?') || '   (attendu dossier_not_found)'
    || chr(10) || 'negociateur = ' || coalesce(c2,'?') || '   (attendu dossier_not_found)'
    || chr(10) || '--- 3. APRES L''INVERSE -------------------------------------------'
    || chr(10) || 'empreintes finales : ' || m_fin || '  (attendu = celles d''AVANT)'
    || chr(10) || 'marqueurs restants : ' || m_marq || '  (attendu 0 et 0)'
    || chr(10) || '------------------------------------------------------------------';

  RAISE EXCEPTION '%', rapport;
END $rep$;

ROLLBACK;
