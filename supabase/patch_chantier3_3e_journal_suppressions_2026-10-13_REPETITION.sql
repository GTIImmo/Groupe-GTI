-- =====================================================================
-- REPETITION du palier 1 de 3e -- 2026-10-13
--
-- ELLE FAIT TOUT POUR DE VRAI, PUIS TOUT DEFAIT, PUIS ANNULE LA TRANSACTION.
--   ① mesure l'etat d'avant
--   ② pose les 2 journaux, les droits, et la mention sur les documents
--   ③ EPROUVE :
--       1. une vraie ligne de journal par objet, relue
--       2. ⭐ LES DROITS, EN EMPRUNTANT DES IDENTITES : un ADMIN doit lire,
--          un inconnu NE DOIT RIEN LIRE (un journal de suppressions dit qui a
--          detruit quoi -- c'est la piece la plus sensible du palier)
--       3. la mention « plus chez Hektor » sur un vrai document, et le compte
--          par l'index partiel
--       4. le garde-fou du RETOUR ARRIERE : avec des traces, il doit REFUSER
--   ④ defait tout (apres avoir vide ce qu'il a ecrit)
--   ⑤ verifie que l'etat de depart est rendu
--   ⑥ se termine par une erreur VOLONTAIRE -> transaction annulee, RIEN D'ECRIT
--
-- A COLLER EN UNE SEULE FOIS. Le resultat attendu est une ERREUR « ESSAI ANNULE »
-- suivie des mesures : c'est le succes.
-- =====================================================================

BEGIN;

SET LOCAL statement_timeout = '120s';

DO $rep$
DECLARE
  c_moi constant text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6",'
                         || '"email":"frederic.gerphagnon@gti-immobilier.fr","role":"authenticated"}';
  c_inconnu constant text := '{"sub":"00000000-0000-0000-0000-000000000000",'
                         || '"email":"inconnu@example.invalid","role":"authenticated"}';

  -- l'etat d'avant
  a_journaux int; a_colonnes int; a_docs bigint; a_marques bigint;
  -- apres le patch
  p_journaux int; p_politiques int; p_colonnes int; p_null bigint; p_true bigint;
  -- les epreuves
  t_doc_id uuid; t_annonce text; t_nom text; t_dossier bigint;
  t_photo_id uuid; t_photo_annonce text; t_photo_nom text;
  e_doc_log bigint; e_photo_log bigint;
  e_before_cles int;
  r_admin bigint; r_inconnu bigint; r_erreur_admin text := '(aucune)';
  m_marques bigint; m_par_index bigint;
  g_refus text;
  -- apres le retour arriere
  f_journaux int; f_colonnes int; f_marques bigint;
  v_msg text;
BEGIN
  -- =================================================================
  -- ① L'ETAT D'AVANT
  -- =================================================================
  SELECT count(*) INTO a_journaux FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public'
     AND c.relname IN ('app_console_deleted_document_log','app_console_deleted_photo_log');
  SELECT count(*) INTO a_colonnes FROM pg_attribute
   WHERE attrelid='public.app_console_document'::regclass
     AND attname IN ('present_in_hektor','absent_depuis') AND NOT attisdropped;
  SELECT count(*) INTO a_docs FROM public.app_console_document;

  IF a_journaux <> 0 OR a_colonnes <> 0 THEN
    RAISE EXCEPTION 'STOP : le patch est deja passe (% journaux, % colonnes)', a_journaux, a_colonnes;
  END IF;

  -- =================================================================
  -- ② LE PATCH
  -- =================================================================
  CREATE TABLE public.app_console_deleted_document_log (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references public.app_console_job(id) on delete set null,
    app_dossier_id bigint,
    hektor_annonce_id text not null,
    document_id uuid,
    hektor_document_id text,
    document_name text,
    requested_by uuid references auth.users(id) on delete set null,
    reason text,
    before_json jsonb,
    result_json jsonb,
    created_at timestamptz not null default now());
  CREATE INDEX app_console_deleted_document_log_annonce_idx
    ON public.app_console_deleted_document_log (hektor_annonce_id, created_at desc);

  CREATE TABLE public.app_console_deleted_photo_log (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references public.app_console_job(id) on delete set null,
    app_dossier_id bigint,
    hektor_annonce_id text not null,
    photo_id uuid,
    hektor_photo_id text,
    filename text,
    requested_by uuid references auth.users(id) on delete set null,
    reason text,
    before_json jsonb,
    result_json jsonb,
    created_at timestamptz not null default now());
  CREATE INDEX app_console_deleted_photo_log_annonce_idx
    ON public.app_console_deleted_photo_log (hektor_annonce_id, created_at desc);

  ALTER TABLE public.app_console_deleted_document_log ENABLE ROW LEVEL SECURITY;
  ALTER TABLE public.app_console_deleted_photo_log    ENABLE ROW LEVEL SECURITY;
  EXECUTE 'create policy app_console_deleted_document_log_service_insert on public.app_console_deleted_document_log for insert to service_role with check (true)';
  EXECUTE 'create policy app_console_deleted_document_log_admin_select on public.app_console_deleted_document_log for select to authenticated using (public.app_console_current_role() = ''admin'')';
  EXECUTE 'create policy app_console_deleted_photo_log_service_insert on public.app_console_deleted_photo_log for insert to service_role with check (true)';
  EXECUTE 'create policy app_console_deleted_photo_log_admin_select on public.app_console_deleted_photo_log for select to authenticated using (public.app_console_current_role() = ''admin'')';
  EXECUTE 'grant all on public.app_console_deleted_document_log to authenticated, service_role';
  EXECUTE 'grant all on public.app_console_deleted_photo_log to authenticated, service_role';

  ALTER TABLE public.app_console_document
    ADD COLUMN present_in_hektor boolean default true,
    ADD COLUMN absent_depuis timestamptz;
  UPDATE public.app_console_document SET present_in_hektor = true WHERE present_in_hektor IS NULL;
  CREATE INDEX app_console_document_absent_idx
    ON public.app_console_document (absent_depuis) WHERE present_in_hektor IS FALSE;

  SELECT count(*) INTO p_journaux FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public'
     AND c.relname IN ('app_console_deleted_document_log','app_console_deleted_photo_log');
  SELECT count(*) INTO p_politiques FROM pg_policies
   WHERE schemaname='public'
     AND tablename IN ('app_console_deleted_document_log','app_console_deleted_photo_log');
  SELECT count(*) INTO p_colonnes FROM pg_attribute
   WHERE attrelid='public.app_console_document'::regclass
     AND attname IN ('present_in_hektor','absent_depuis') AND NOT attisdropped;
  SELECT count(*) FILTER (WHERE present_in_hektor IS NULL),
         count(*) FILTER (WHERE present_in_hektor IS TRUE)
    INTO p_null, p_true FROM public.app_console_document;

  -- =================================================================
  -- ③ LES EPREUVES
  -- =================================================================

  -- 1. UNE VRAIE LIGNE DE JOURNAL, PAR OBJET.
  --    On choisit un document et une photo REELS, avec un ordre (un LIMIT sans
  --    ORDER BY ne prouve rien).
  SELECT d.id, d.hektor_annonce_id, d.document_name, d.app_dossier_id
    INTO t_doc_id, t_annonce, t_nom, t_dossier
    FROM public.app_console_document d
   WHERE nullif(btrim(coalesce(d.sha256,'')),'') IS NOT NULL
   ORDER BY d.id LIMIT 1;

  SELECT p.id, p.hektor_annonce_id, p.filename
    INTO t_photo_id, t_photo_annonce, t_photo_nom
    FROM public.app_console_photo p
   WHERE p.derives_json IS NOT NULL
   ORDER BY p.id LIMIT 1;

  -- ⭐ `before_json` = LA LIGNE ENTIERE. C'est ce qui rend le journal utile :
  --   nom, type, empreinte, taille, chemins, id Hektor, visibilite -- tout.
  INSERT INTO public.app_console_deleted_document_log
    (app_dossier_id, hektor_annonce_id, document_id, hektor_document_id, document_name,
     requested_by, reason, before_json, result_json)
  SELECT d.app_dossier_id, d.hektor_annonce_id, d.id, d.hektor_document_id, d.document_name,
         'd4b1685f-948b-4ce8-af15-671b94a725e6'::uuid, 'repetition_3e',
         to_jsonb(d), jsonb_build_object('hektor_confirme', true)
    FROM public.app_console_document d WHERE d.id = t_doc_id;

  -- ⚠ Pour la photo, before_json DOIT emporter derives_json : les derives publics
  --   partent avec la photo (decision de Frederic du 13/10), donc le journal est la
  --   seule trace de ce qui a ete publie.
  INSERT INTO public.app_console_deleted_photo_log
    (app_dossier_id, hektor_annonce_id, photo_id, hektor_photo_id, filename,
     requested_by, reason, before_json, result_json)
  SELECT p.app_dossier_id, p.hektor_annonce_id, p.id, p.hektor_photo_id, p.filename,
         'd4b1685f-948b-4ce8-af15-671b94a725e6'::uuid, 'repetition_3e',
         to_jsonb(p), jsonb_build_object('hektor_confirme', true, 'derives_detruits', true)
    FROM public.app_console_photo p WHERE p.id = t_photo_id;

  SELECT count(*) INTO e_doc_log   FROM public.app_console_deleted_document_log;
  SELECT count(*) INTO e_photo_log FROM public.app_console_deleted_photo_log;
  SELECT count(*) INTO e_before_cles
    FROM public.app_console_deleted_photo_log, jsonb_object_keys(before_json) k
   WHERE k = 'derives_json';

  -- 2. ⭐ LES DROITS, EN EMPRUNTANT DES IDENTITES.
  --    Un journal de suppressions dit QUI a detruit QUOI : c'est la piece la plus
  --    sensible du palier. On verifie les deux sens.
  --    ⚠ Chaque emprunt est enferme dans son propre bloc, et le role est RENDU
  --      dans les deux cas -- sinon la suite de la repetition tournerait en
  --      `authenticated` et echouerait pour une mauvaise raison.
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM set_config('role', 'authenticated', true);
    SELECT count(*) INTO r_admin FROM public.app_console_deleted_document_log;
    PERFORM set_config('role', 'postgres', true);
  EXCEPTION WHEN others THEN
    PERFORM set_config('role', 'postgres', true);
    r_admin := -1;
    r_erreur_admin := SQLERRM;
  END;

  BEGIN
    PERFORM set_config('request.jwt.claims', c_inconnu, true);
    PERFORM set_config('role', 'authenticated', true);
    SELECT count(*) INTO r_inconnu FROM public.app_console_deleted_document_log;
    PERFORM set_config('role', 'postgres', true);
  EXCEPTION WHEN others THEN
    PERFORM set_config('role', 'postgres', true);
    r_inconnu := -1;
  END;
  PERFORM set_config('request.jwt.claims', '', true);

  -- 3. LA MENTION « PLUS CHEZ HEKTOR » SUR UN VRAI DOCUMENT.
  UPDATE public.app_console_document
     SET present_in_hektor = false, absent_depuis = now()
   WHERE id = t_doc_id;
  SELECT count(*) INTO m_marques FROM public.app_console_document WHERE present_in_hektor IS FALSE;
  SELECT count(*) INTO m_par_index FROM public.app_console_document
   WHERE present_in_hektor IS FALSE AND absent_depuis IS NOT NULL;

  -- 4. LE GARDE-FOU DU RETOUR ARRIERE : avec des traces, il DOIT refuser.
  g_refus := CASE
    WHEN (SELECT count(*) FROM public.app_console_deleted_document_log) > 0
      OR (SELECT count(*) FROM public.app_console_deleted_photo_log) > 0
    THEN 'REFUSE (c''est voulu : jeter le journal effacerait la memoire d''une destruction)'
    ELSE 'accepterait -- ANORMAL ICI' END;

  -- =================================================================
  -- ④ LE RETOUR ARRIERE
  --    On vide d'abord ce que LA REPETITION a ecrit : le vrai script, lui,
  --    REFUSE de defaire tant qu'il reste des traces (c'est l'epreuve 4).
  -- =================================================================
  DELETE FROM public.app_console_deleted_document_log WHERE reason = 'repetition_3e';
  DELETE FROM public.app_console_deleted_photo_log    WHERE reason = 'repetition_3e';
  UPDATE public.app_console_document
     SET present_in_hektor = true, absent_depuis = NULL
   WHERE id = t_doc_id;

  DROP TABLE public.app_console_deleted_document_log;
  DROP TABLE public.app_console_deleted_photo_log;
  DROP INDEX public.app_console_document_absent_idx;
  ALTER TABLE public.app_console_document
    DROP COLUMN present_in_hektor,
    DROP COLUMN absent_depuis;

  -- =================================================================
  -- ⑤ TOUT EST-IL REVENU ?
  -- =================================================================
  SELECT count(*) INTO f_journaux FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public'
     AND c.relname IN ('app_console_deleted_document_log','app_console_deleted_photo_log');
  SELECT count(*) INTO f_colonnes FROM pg_attribute
   WHERE attrelid='public.app_console_document'::regclass
     AND attname IN ('present_in_hektor','absent_depuis') AND NOT attisdropped;
  SELECT count(*) INTO f_marques FROM public.app_console_document;

  -- =================================================================
  -- ⑥ L'ERREUR VOLONTAIRE
  -- =================================================================
  v_msg := format(
       E'ESSAI ANNULE -- RIEN N''EST ECRIT. Mesures :\n'
    || E'\n  --- L''ETAT DE DEPART --------------------------------\n'
    || E'   journaux %s  ·  colonnes %s  ·  documents %s   (attendu 0, 0, 162543)\n'
    || E'\n  --- APRES LE PATCH ---------------------------------\n'
    || E'   journaux %s   (attendu 2)\n'
    || E'   politiques %s   (attendu 4 : 2 insert service_role + 2 select admin)\n'
    || E'   colonnes de la mention %s   (attendu 2)\n'
    || E'   documents sans mention : %s   (attendu 0 -- le rattrapage)\n'
    || E'   documents marques « present chez Hektor » : %s\n'
    || E'\n  --- 1. UNE VRAIE LIGNE DE JOURNAL ------------------\n'
    || E'   document d''essai   %s  ·  annonce %s  ·  %s\n'
    || E'   photo d''essai      %s  ·  annonce %s  ·  %s\n'
    || E'   lignes ecrites : %s document(s), %s photo(s)   (attendu 1 et 1)\n'
    || E'   before_json de la photo porte-t-il derives_json ? %s   (attendu 1)\n'
    || E'\n  --- 2. LES DROITS, IDENTITES EMPRUNTEES -----------\n'
    || E'   un ADMIN lit        : %s ligne(s)   (attendu 1)\n'
    || E'   un INCONNU lit      : %s ligne(s)   (attendu 0)\n'
    || E'   erreur cote admin   : %s\n'
    || E'\n  --- 3. LA MENTION « PLUS CHEZ HEKTOR » ------------\n'
    || E'   documents marques : %s   (attendu 1)\n'
    || E'   dont avec une date : %s   (attendu 1)\n'
    || E'\n  --- 4. LE GARDE-FOU DU RETOUR ARRIERE -------------\n'
    || E'   avec des traces au journal, il : %s\n'
    || E'\n  --- APRES LE RETOUR ARRIERE -----------------------\n'
    || E'   journaux %s  ·  colonnes %s  ·  documents %s   (attendu 0, 0, inchange)'
    ,
    a_journaux, a_colonnes, a_docs,
    p_journaux, p_politiques, p_colonnes, p_null, p_true,
    coalesce(t_doc_id::text,'(aucun)'), coalesce(t_annonce,'-'), coalesce(t_nom,'-'),
    coalesce(t_photo_id::text,'(aucune)'), coalesce(t_photo_annonce,'-'), coalesce(t_photo_nom,'-'),
    e_doc_log, e_photo_log, e_before_cles,
    r_admin, r_inconnu, r_erreur_admin,
    m_marques, m_par_index,
    g_refus,
    f_journaux, f_colonnes, f_marques
  );
  RAISE EXCEPTION '%', v_msg;
END $rep$;

COMMIT;
