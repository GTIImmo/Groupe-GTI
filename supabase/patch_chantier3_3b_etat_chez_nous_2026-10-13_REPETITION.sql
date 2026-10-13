-- =====================================================================
-- REPETITION du patch 3b (archiver + negociateur) -- 13/10/2026
--
-- A COLLER DANS : https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
-- ⚠ ELLE N'ECRIT RIEN : une transaction qui finit par une erreur volontaire.
--
-- LES ESSAIS :
--   A  ARCHIVER un bien VIVANT (62965) avec un motif -> fiche `archive=1`, carnet
--      `archive` + `archive_motif`, et `archive_avant` dans la charge
--   B  ARCHIVER un bien VENDU (284) -> le carnet est ecrit, la fiche touche 0 ligne
--   C  NEGOCIATEUR sur un bien vivant, AVEC email -> la fiche change, l'ancien part
--      dans la charge
--   D  NEGOCIATEUR SANS email -> la fiche NE DOIT PAS BOUGER (la regle « on n'invente
--      pas » est conservee) -- c'est le TEMOIN
--   E  apres l'inverse : les deux empreintes reviennent
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '180s';

DO $rep$
DECLARE
  c_arch constant text := 'public.app_archive_annonce_optimistic(bigint,jsonb,integer)';
  c_nego constant text := 'public.app_assign_negotiator_optimistic(bigint,text,jsonb,integer)';
  e_arch constant text := '04dfcb30fa1a6010ce3714d4c85dfddd';
  e_nego constant text := '85bde9eb83c794ddfcd08445316e4064';
  c_moi  constant text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6"}';
  c_vif  constant bigint := 5941336;   -- parc VIVANT, annonce Hektor 62965
  c_hist constant bigint := 284;       -- index HISTORIQUE, annonce Hektor 107 (Vendu)

  a text[]; b text[];
  v_def text; v_apres text; v_retour text;
  i int; n int;

  m_av text := ''; m_anc text := ''; m_nue text := ''; m_fin text := '';

  ra jsonb; ra_fiche text; ra_carnet text; ra_charge jsonb;
  rb jsonb; rb_fiche int; rb_carnet text;
  rc jsonb; rc_fiche text; rc_charge jsonb;
  rd_avant text; rd_apres text; rd_carnet text;

  rapport text;
BEGIN
  a := ARRAY[
    $a1$  -- 1. CHEZ NOUS D'ABORD
  insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_par)
  values (target_dossier_id, 'archive', '1', 'geste_archiver', auth.uid()::text)
  on conflict (app_dossier_id, champ) do update
     set valeur_app = excluded.valeur_app,
         origine    = excluded.origine,
         ecrit_le   = now(),
         ecrit_par  = excluded.ecrit_par;$a1$,
    $a2$  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier', d.numero_dossier,
    'titre_bien',     d.titre_bien,
    'target_archive', '1');$a2$,
    $a3$  -- 1. CHEZ NOUS D'ABORD -- mais seulement si on a quelque chose a dire.
  -- Sans email, on n'invente pas une valeur : le travail part quand meme, et le
  -- carnet reste muet. « L'app gagne seulement quand elle a quelque chose a dire. »
  if v_email is not null then$a3$
  ];

  b := ARRAY[
    $b1$  -- @3b-debut   CHANTIER 3, POINT 3b (13/10/2026) : LA FICHE AUSSI, ET LE MOTIF
  --
  -- Avant, ce geste n'ecrivait QUE le carnet -- que personne ne relit aujourd'hui. La
  -- fiche du bien n'etait pas touchee : notre base disait « actif » tant que Hektor
  -- n'avait pas repondu (2 a 3 minutes, mesure du 12/10 sur le bien 62965).
  --
  -- ⚠ ET LE MOTIF SE PERDAIT. La modale en demande un (2 motifs principaux, 9 causes,
  --   prix, confrere) et le worker l'envoie bien a Hektor (`validerArchivage`), mais
  --   AUCUNE colonne de notre base ne le portait -- 0 sur tout le schema. Il ne vivait
  --   que dans la charge du travail. A la coupure on aurait garde la date et le geste,
  --   et perdu LA RAISON. On le range donc au carnet, avec le reste.
  --
  -- ⚠ Si le bien est VENDU/CLOS il n'a plus de ligne ici : l'update touche 0 ligne, sans
  --   erreur, et le carnet recoit quand meme la valeur. C'est voulu.
  update public.app_dossier_current
     set archive = '1'
   where app_dossier_id = target_dossier_id;

  insert into public.app_annonce_champ_app (app_dossier_id, champ, valeur_app, origine, ecrit_le, ecrit_par)
  select target_dossier_id, x.champ, x.valeur, 'geste_archiver', now(), auth.uid()::text
    from (values
      ('archive'::text,       '1'::text),
      ('archive_motif'::text, nullif(concat_ws(' · ',
          nullif(trim(coalesce(job_payload->>'archive_main_choice', '')), ''),
          nullif(trim(coalesce(job_payload->>'archive_sub_choice',  '')), ''),
          nullif(trim(coalesce(job_payload->>'archive_other_text',  '')), '')), ''))
    ) as x(champ, valeur)
   where x.valeur is not null
  on conflict (app_dossier_id, champ) do update
     set valeur_app = excluded.valeur_app,
         origine    = excluded.origine,
         ecrit_le   = excluded.ecrit_le,
         ecrit_par  = excluded.ecrit_par;
  -- @3b-fin$b1$,
    $b2$  -- @3b-charge : l'etat d'avant voyage avec le travail, pour pouvoir revenir.
  v_charge := coalesce(job_payload, '{}'::jsonb) || jsonb_build_object(
    'numero_dossier', d.numero_dossier,
    'titre_bien',     d.titre_bien,
    'archive_avant',  d.archive,
    'target_archive', '1');$b2$,
    $b3$  -- @3b-debut   CHANTIER 3, POINT 3b (13/10/2026) : LA FICHE AUSSI
  --
  -- Avant, ce geste n'ecrivait QUE le carnet. La colonne `negociateur_email` de la fiche
  -- n'etait jamais juste avant la reponse de Hektor (4 gestes depuis juillet, mesure du
  -- 13/10). Or c'est ELLE que lit tout le reste de l'app.
  --
  -- ⚠ C'est aussi LE champ du perimetre du negociateur (chantier ②) : l'ecrire change
  --   immediatement qui voit le bien. C'est le geste voulu -- et cela arrivait de toute
  --   facon 2 a 3 minutes plus tard, par la relecture.
  --
  -- La regle d'avant est conservee mot pour mot : sans email, on n'invente rien, le
  -- travail part quand meme et le carnet reste muet.
  if v_email is not null then
    v_charge := v_charge || jsonb_build_object('negociateur_avant', d.negociateur_email);
    update public.app_dossier_current
       set negociateur_email = v_email
     where app_dossier_id = target_dossier_id;
  -- @3b-fin$b3$
  ];

  FOR i IN 1 .. array_length(a, 1) LOOP
    a[i] := replace(a[i], chr(13), '');
    b[i] := replace(b[i], chr(13), '');
  END LOOP;

  -- ═══ AVANT + PATCH ═══
  v_def := replace(pg_get_functiondef(c_arch::regprocedure), chr(13), '');
  m_av  := m_av || 'archive=' || md5(v_def) || '  ';
  IF md5(v_def) <> e_arch THEN RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- archive porte %', md5(v_def); END IF;
  FOR i IN 1 .. 2 LOOP
    n := (length(v_def) - length(replace(v_def, a[i], ''))) / length(a[i]);
    m_anc := m_anc || 'R' || i || '=' || n || ' ';
    IF n <> 1 THEN RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- ancre R% trouvee % fois', i, n; END IF;
    v_def := replace(v_def, a[i], b[i]);
  END LOOP;
  EXECUTE v_def;
  v_retour := replace(pg_get_functiondef(c_arch::regprocedure), chr(13), '');
  FOR i IN REVERSE 2 .. 1 LOOP v_retour := replace(v_retour, b[i], a[i]); END LOOP;
  m_nue := m_nue || 'archive=' || md5(v_retour) || '  ';

  v_def := replace(pg_get_functiondef(c_nego::regprocedure), chr(13), '');
  m_av  := m_av || 'nego=' || md5(v_def);
  IF md5(v_def) <> e_nego THEN RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- nego porte %', md5(v_def); END IF;
  n := (length(v_def) - length(replace(v_def, a[3], ''))) / length(a[3]);
  m_anc := m_anc || 'R3=' || n;
  IF n <> 1 THEN RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- ancre R3 trouvee % fois', n; END IF;
  v_def := replace(v_def, a[3], b[3]);
  EXECUTE v_def;
  v_retour := replace(replace(pg_get_functiondef(c_nego::regprocedure), chr(13), ''), b[3], a[3]);
  m_nue := m_nue || 'nego=' || md5(v_retour);

  -- ═══ A -- ARCHIVER un bien VIVANT, avec un motif ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    ra := public.app_archive_annonce_optimistic(c_vif,
            '{"archive_main_choice":"choiceVendu","archive_sub_choice":"agence"}'::jsonb, 8);
    SELECT 'archive='||coalesce(archive,'?') INTO ra_fiche
      FROM public.app_dossier_current WHERE app_dossier_id = c_vif;
    SELECT string_agg(champ||'='||valeur_app, ' | ' ORDER BY champ) INTO ra_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_vif;
    SELECT payload_json INTO ra_charge
      FROM public.app_console_job WHERE id = (ra->>'job_id')::uuid;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN
      ra_fiche := 'ERREUR: ' || SQLERRM; ra_carnet := '-';
    END IF;
  END;

  -- ═══ B -- ARCHIVER un bien VENDU (hors parc vivant) ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    rb := public.app_archive_annonce_optimistic(c_hist,
            '{"archive_main_choice":"choiceAutre","archive_sub_choice":"autre","archive_other_text":"essai repetition"}'::jsonb, 8);
    SELECT count(*) INTO rb_fiche FROM public.app_dossier_current WHERE app_dossier_id = c_hist;
    SELECT string_agg(champ||'='||valeur_app, ' | ' ORDER BY champ) INTO rb_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_hist;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN rb_fiche := -1; rb_carnet := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ C -- NEGOCIATEUR avec email ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    rc := public.app_assign_negotiator_optimistic(c_vif, '12345',
            '{"target_hektor_user_email":"essai.3b@gti-immobilier.fr"}'::jsonb, 9);
    SELECT coalesce(negociateur_email,'(vide)') INTO rc_fiche
      FROM public.app_dossier_current WHERE app_dossier_id = c_vif;
    SELECT payload_json INTO rc_charge
      FROM public.app_console_job WHERE id = (rc->>'job_id')::uuid;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN rc_fiche := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ D -- LE TEMOIN : NEGOCIATEUR SANS email -> la fiche ne doit PAS bouger ═══
  SELECT coalesce(negociateur_email,'(vide)') INTO rd_avant
    FROM public.app_dossier_current WHERE app_dossier_id = c_vif;
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_assign_negotiator_optimistic(c_vif, '12345', '{}'::jsonb, 9);
    SELECT coalesce(negociateur_email,'(vide)') INTO rd_apres
      FROM public.app_dossier_current WHERE app_dossier_id = c_vif;
    SELECT coalesce(string_agg(champ, ','), '(aucune)') INTO rd_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_vif;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN rd_apres := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ L'INVERSE ═══
  v_def := replace(pg_get_functiondef(c_arch::regprocedure), chr(13), '');
  FOR i IN REVERSE 2 .. 1 LOOP v_def := replace(v_def, b[i], a[i]); END LOOP;
  IF md5(v_def) <> e_arch THEN RAISE EXCEPTION 'INVERSE IMPOSSIBLE -- archive rend %', md5(v_def); END IF;
  EXECUTE v_def;
  m_fin := m_fin || 'archive=' || md5(replace(pg_get_functiondef(c_arch::regprocedure), chr(13), '')) || '  ';

  v_def := replace(replace(pg_get_functiondef(c_nego::regprocedure), chr(13), ''), b[3], a[3]);
  IF md5(v_def) <> e_nego THEN RAISE EXCEPTION 'INVERSE IMPOSSIBLE -- nego rend %', md5(v_def); END IF;
  EXECUTE v_def;
  m_fin := m_fin || 'nego=' || md5(replace(pg_get_functiondef(c_nego::regprocedure), chr(13), ''));

  rapport :=
    'ESSAI ANNULE -- rien n''a ete ecrit. Mesures :'
    || chr(10) || '--- 1. AVANT ----------------------------------------------------'
    || chr(10) || 'empreintes : ' || m_av
    || chr(10) || '  (attendu archive=04dfcb30fa1a6010ce3714d4c85dfddd  nego=85bde9eb83c794ddfcd08445316e4064)'
    || chr(10) || 'ancres     : ' || m_anc || '   (attendu R1=1 R2=1 R3=1)'
    || chr(10) || '--- 2. APRES LE PATCH -------------------------------------------'
    || chr(10) || 'empreintes NUES : ' || m_nue
    || chr(10) || '  (attendu = celles d''AVANT : RIEN D''AUTRE N''A CHANGE)'
    || chr(10) || '--- A. ARCHIVER un bien VIVANT (62965), motif « Vendu/agence » ---'
    || chr(10) || 'fiche        = ' || coalesce(ra_fiche,'?')  || '   (attendu archive=1)'
    || chr(10) || 'carnet       = ' || coalesce(ra_carnet,'?') || '   (attendu archive=1 | archive_motif=choiceVendu · agence)'
    || chr(10) || 'charge.archive_avant = ' || coalesce(ra_charge->>'archive_avant','(absent)') || '   (attendu 0)'
    || chr(10) || '--- B. ARCHIVER un bien VENDU (284, hors parc vivant) ------------'
    || chr(10) || 'lignes de fiche = ' || coalesce(rb_fiche::text,'?') || '   (attendu 0 : il n''y est pas, et c''est normal)'
    || chr(10) || 'carnet          = ' || coalesce(rb_carnet,'?') || '   (attendu archive=1 | archive_motif=choiceAutre · autre · essai repetition)'
    || chr(10) || '--- C. NEGOCIATEUR avec email -----------------------------------'
    || chr(10) || 'fiche = ' || coalesce(rc_fiche,'?') || '   (attendu essai.3b@gti-immobilier.fr)'
    || chr(10) || 'charge.negociateur_avant = ' || coalesce(rc_charge->>'negociateur_avant','(absent)') || '   (attendu gonzalez@gti-immobilier.fr)'
    || chr(10) || '--- D. LE TEMOIN : NEGOCIATEUR SANS email -----------------------'
    || chr(10) || 'fiche avant = ' || coalesce(rd_avant,'?')
    || chr(10) || 'fiche apres = ' || coalesce(rd_apres,'?') || '   (attendu IDENTIQUE : on n''invente rien)'
    || chr(10) || 'carnet      = ' || coalesce(rd_carnet,'?') || '   (attendu : aucune ligne negociateur_email ajoutee)'
    || chr(10) || '--- E. APRES L''INVERSE -----------------------------------------'
    || chr(10) || 'empreintes finales : ' || m_fin || '   (attendu = celles d''AVANT)'
    || chr(10) || '----------------------------------------------------------------';

  RAISE EXCEPTION '%', rapport;
END $rep$;

ROLLBACK;
