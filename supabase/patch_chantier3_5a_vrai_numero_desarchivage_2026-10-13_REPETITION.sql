-- =====================================================================
-- REPETITION de la correction du defaut 5a -- 13/10/2026
--
-- A COLLER DANS : https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- ⚠ ELLE N'ECRIT RIEN : une seule transaction, qui finit par une erreur volontaire.
--
-- LES ESSAIS, dans l'ordre -- et le premier est le TEMOIN D'AVANT :
--   A0  AVANT le patch : desarchiver l'archive 49544 -> le travail doit porter NULL
--   A   APRES le patch : le meme geste -> le travail doit porter 15633, et le CARNET
--       doit recevoir `archive=0` (aujourd'hui cette ligne est purement sautee)
--   B   un bien VIVANT (62774) -> INCHANGE
--   C   un numero inventé -> `dossier_not_found`, comme avant
--   D   apres l'inverse : l'empreinte doit REVENIR a l'identique
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '180s';

DO $rep$
DECLARE
  c_sig  constant text := 'public.app_restore_annonce_optimistic(bigint,jsonb,integer)';
  c_emp  constant text := '709571469083a76b1be384e879ca523b';
  c_moi  constant text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6"}';
  c_arch constant bigint := 15633;      -- index des ARCHIVES, annonce Hektor 49544
  c_vif  constant bigint := 3828957;    -- parc VIVANT, annonce Hektor 62774
  c_faux constant bigint := 999999999;

  a text[]; b text[];
  v_def text; v_apres text; v_retour text;
  i int; n int;

  m_emp_avant text; m_taille_avant int; m_ancres text := '';
  m_taille_apres int; m_emp_retour text; m_emp_final text;

  z0 jsonb; z0_dossier text;
  za jsonb; za_dossier text; za_hektor text; za_carnet text;
  zb jsonb; zb_dossier text;
  zc text;

  rapport text;
BEGIN
  v_def          := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_emp_avant    := md5(v_def);
  m_taille_avant := length(v_def);

  IF m_emp_avant <> c_emp THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- empreinte % au lieu de %', m_emp_avant, c_emp;
  END IF;
  IF position('@5a-vrai-numero' in v_def) > 0 THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- le patch est deja passe';
  END IF;

  -- ═══ A0 -- LE TEMOIN D'AVANT : la fonction d'aujourd'hui pose NULL ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    z0 := public.app_restore_annonce_optimistic(c_arch, '{}'::jsonb, 8);
    SELECT coalesce(app_dossier_id::text,'NULL') INTO z0_dossier
      FROM public.app_console_job WHERE id = (z0->>'job_id')::uuid;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN z0_dossier := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ LE VRAI PATCH ═══
  a := ARRAY[
    $a1$    v_dossier := null;   -- nous n'avons AUCUN numero de dossier pour une archive$a1$,
    $a2$    --    (mesure du 08/10). L'index des archives n'a pas de numero de dossier ; l'ecran
    --    envoie donc son `app_archive_id` a cette place (api.ts:2618). C'est par la qu'on$a2$,
    $a3$  --    numero de dossier ; pour une archive il n'y en a pas, et y ecrire le numero
  --    d'archive serait poser un FAUX identifiant (la faute meme de 5d et 5g). Ce carnet$a3$
  ];
  b := ARRAY[
    $b1$    -- @5a-vrai-numero (13/10/2026) : LE NUMERO RECU EST LE NOTRE, ON LE GARDE.
    --   `app_archive_id` n'est pas une serie a part : c'est NOTRE `app_dossier_id`, renomme
    --   (export_app_payload.py:316). Recoupe le 13/10 par un chemin independant -- le numero
    --   que portent les ANCIENS travaux de chaque bien : 35 312 identiques sur 35 318, et les
    --   6 ecarts sont des fantomes deja reconcilies dont le numero RECENT est bien celui-ci.
    --   Le mettre a NULL privait le bandeau « geste abandonne » (App.tsx:32925, il cherche par
    --   numero de dossier) et empechait le filet de rejeu de voir un geste DEPASSE
    --   (`NULL = NULL` n'est jamais vrai).
    v_dossier := target_dossier_id;$b1$,
    $b2$    --    (mesure du 08/10). L'index des archives range NOTRE numero de dossier sous le
    --    nom `app_archive_id` ; l'ecran l'envoie a cette place (api.ts:2618). C'est par la qu'on$b2$,
    $b3$  --    numero de dossier -- et une archive EN A UN : `app_archive_id` est notre
  --    `app_dossier_id` renomme (verifie le 13/10). Ce carnet$b3$
  ];

  FOR i IN 1 .. array_length(a, 1) LOOP
    a[i] := replace(a[i], chr(13), '');
    b[i] := replace(b[i], chr(13), '');
  END LOOP;

  FOR i IN 1 .. array_length(a, 1) LOOP
    n := (length(v_def) - length(replace(v_def, a[i], ''))) / length(a[i]);
    m_ancres := m_ancres || 'R' || i || '=' || n || ' ';
    IF n <> 1 THEN RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- ancre R% trouvee % fois', i, n; END IF;
    v_def := replace(v_def, a[i], b[i]);
  END LOOP;

  EXECUTE v_def;
  v_apres        := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_taille_apres := length(v_apres);
  v_retour := v_apres;
  FOR i IN REVERSE array_length(a, 1) .. 1 LOOP
    v_retour := replace(v_retour, b[i], a[i]);
  END LOOP;
  m_emp_retour := md5(v_retour);

  -- ═══ A -- APRES le patch : le vrai numero, et le carnet ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    za := public.app_restore_annonce_optimistic(c_arch, '{}'::jsonb, 8);
    SELECT coalesce(app_dossier_id::text,'NULL'), coalesce(hektor_annonce_id,'(vide)')
      INTO za_dossier, za_hektor
      FROM public.app_console_job WHERE id = (za->>'job_id')::uuid;
    SELECT string_agg(champ||'='||valeur_app||' ('||origine||')', ' | ' ORDER BY champ) INTO za_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_arch;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN
      za_dossier := 'ERREUR: ' || SQLERRM; za_hektor := '-'; za_carnet := '-';
    END IF;
  END;

  -- ═══ B -- un bien VIVANT : INCHANGE ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    zb := public.app_restore_annonce_optimistic(c_vif, '{}'::jsonb, 8);
    SELECT coalesce(app_dossier_id::text,'NULL') INTO zb_dossier
      FROM public.app_console_job WHERE id = (zb->>'job_id')::uuid;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN zb_dossier := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ C -- numero inventé ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_restore_annonce_optimistic(c_faux, '{}'::jsonb, 8);
    zc := '(AUCUNE ERREUR -- ANORMAL)';
  EXCEPTION WHEN others THEN zc := SQLERRM;
  END;

  -- ═══ L'INVERSE ═══
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  FOR i IN REVERSE array_length(b, 1) .. 1 LOOP
    v_def := replace(v_def, b[i], a[i]);
  END LOOP;
  IF md5(v_def) <> c_emp THEN
    RAISE EXCEPTION 'INVERSE IMPOSSIBLE -- on obtient % au lieu de %', md5(v_def), c_emp;
  END IF;
  EXECUTE v_def;
  m_emp_final := md5(replace(pg_get_functiondef(c_sig::regprocedure), chr(13), ''));

  rapport :=
    'ESSAI ANNULE -- rien n''a ete ecrit. Mesures :'
    || chr(10) || '--- 1. AVANT -----------------------------------------------------'
    || chr(10) || 'empreinte_avant = ' || m_emp_avant    || '  (attendu 709571469083a76b1be384e879ca523b)'
    || chr(10) || 'taille_avant    = ' || m_taille_avant || '  (attendu 3557)'
    || chr(10) || 'ancres          = ' || m_ancres       || ' (attendu R1=1 R2=1 R3=1)'
    || chr(10) || '--- A0. LE TEMOIN D''AVANT : desarchiver l''archive 49544 ---------'
    || chr(10) || 'travail.app_dossier_id = ' || coalesce(z0_dossier,'?') || '   (attendu NULL -- c''est LE DEFAUT)'
    || chr(10) || '--- 2. APRES LE PATCH -------------------------------------------'
    || chr(10) || 'taille_apres     = ' || m_taille_apres
    || chr(10) || 'empreinte_RETOUR = ' || m_emp_retour  || '  (attendu = empreinte_avant : RIEN D''AUTRE N''A CHANGE)'
    || chr(10) || '--- A. LE MEME GESTE, APRES ------------------------------------'
    || chr(10) || 'travail.app_dossier_id = ' || coalesce(za_dossier,'?') || '   (attendu 15633 -- NOTRE vrai numero)'
    || chr(10) || 'travail.hektor_id      = ' || coalesce(za_hektor,'?')  || '   (attendu 49544)'
    || chr(10) || 'carnet                 = ' || coalesce(za_carnet,'?')  || '   (attendu archive=0 (geste_desarchiver) -- ligne AUJOURD''HUI SAUTEE)'
    || chr(10) || '--- B. un bien VIVANT (62774) : INCHANGE ------------------------'
    || chr(10) || 'travail.app_dossier_id = ' || coalesce(zb_dossier,'?') || '   (attendu 3828957)'
    || chr(10) || '--- C. numero inventé ------------------------------------------'
    || chr(10) || 'message = ' || coalesce(zc,'?') || '   (attendu dossier_not_found)'
    || chr(10) || '--- D. APRES L''INVERSE ----------------------------------------'
    || chr(10) || 'empreinte_finale = ' || m_emp_final || '  (attendu = empreinte_avant)'
    || chr(10) || '----------------------------------------------------------------';

  RAISE EXCEPTION '%', rapport;
END $rep$;

ROLLBACK;
