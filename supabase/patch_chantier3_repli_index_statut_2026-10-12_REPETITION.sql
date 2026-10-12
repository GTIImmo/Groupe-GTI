-- =====================================================================
-- REPETITION du patch « VENDU / CLOS MANIPULABLE » (statut) -- 12/10/2026
--
-- A COLLER DANS : https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- ⚠ ELLE N'ECRIT RIEN : tout se passe dans UNE transaction qui finit par une erreur volontaire,
--   donc PostgreSQL annule l'integralite. Le message porte les mesures -- recopie-le-moi.
--
-- LES SEPT ESSAIS, joues sur la VRAIE fonction, sous l'identite de Frederic (admin) :
--   A  VENDU/CLOS (62963) -> « Actif »     : doit MARCHER, avec le VRAI numero de dossier
--   B  bien VIVANT (62774) -> « Actif »    : le comportement d'aujourd'hui, INCHANGE
--   C  ARCHIVE (49544) -> « Mandat clos »  : doit etre REFUSE, et le DIRE (lecture seule)
--   D  VENDU/CLOS -> « Compromis »         : doit etre REFUSE (une affaire tient au parc vivant)
--   E  numero inventé                      : doit rendre « dossier_not_found », comme avant
--   F  bien VIVANT -> « Clos »             : le carnet doit porter « Clos », plus « Mandat clos »
--   G  DESARCHIVER l'archive 49544         : doit TOUJOURS marcher (on n'a pas ferme sa sortie)
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '180s';

DO $rep$
DECLARE
  c_sig  constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp  constant text := '1f9e987f3a2a9fc977ae4efd6db5b000';
  c_moi  constant text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6"}';
  c_hist constant bigint := 5880239;    -- index HISTORIQUE, annonce Hektor 62963 (Clos)
  c_vif  constant bigint := 3828957;    -- parc VIVANT, annonce Hektor 62774
  c_arch constant bigint := 15633;      -- index des ARCHIVES, annonce Hektor 49544
  c_faux constant bigint := 999999999;

  a text[]; b text[];
  v_def text; v_apres text; v_retour text;
  i int; n int;

  m_emp_avant text; m_taille_avant int; m_ancres text := '';
  m_taille_apres int; m_emp_retour text; m_emp_final text; m_marqueurs int;

  ra jsonb; ra_dossier text; ra_hektor text; ra_fiche int; ra_carnet text; ra_charge jsonb;
  rb jsonb; rb_dossier text; rb_fiche text; rb_carnet int;
  rc text; rd text; re text; rf text;
  rg jsonb; rg_dossier text; rg_hektor text; rg_msg text;

  rapport text;
BEGIN
  -- ═══ 1. AVANT ═══
  v_def          := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_emp_avant    := md5(v_def);
  m_taille_avant := length(v_def);

  IF m_emp_avant <> c_emp THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- empreinte % au lieu de %', m_emp_avant, c_emp;
  END IF;
  IF position('@repli-debut' in v_def) > 0 THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- le patch est deja passe';
  END IF;

  a := ARRAY[
    $a1$  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;$a1$,
    $a2$                          when 'closed'     then 'Mandat clos'$a2$
  ];

  b := ARRAY[
    $b1$  -- @repli-debut   CHANTIER 3 (12/10/2026) : LE BIEN PEUT ETRE VENDU OU CLOS
  --
  -- LA REGLE DE LA MAISON, telle que l'ECRAN la porte depuis le 21/05/2026
  -- (`isReadOnlyLightweightDetail`, App.tsx:406-411), et telle que Frederic l'a confirmee
  -- le 12/10 :
  --     · VENDU / CLOS  -> les gestes marchent (l'ecran les ouvre des que le detail est la)
  --     · ARCHIVE       -> LECTURE SEULE, sa seule sortie est « Desarchiver »
  --     · BROUILLON     -> lecture seule
  --
  -- Depuis le 20/05, les Vendu/Clos ne sont plus dans app_dossier_current : ils vivent dans
  -- `app_historical_annonce_index_current`. Cette fonction, ecrite le 25/08, l'ignorait et
  -- refusait 8 941 biens sur un « dossier_not_found » brut, alors que l'ecran affichait le
  -- bouton. L'ecran a trois etats, la base n'en avait qu'un.
  --
  -- ⭐ LE NUMERO RECU EST LE BON. `app_historical_id` n'est pas une serie a part : c'est
  --   NOTRE `app_dossier_id`, renomme (export_app_payload.py:363), verifie par les anciens
  --   travaux des memes biens. On le garde donc TEL QUEL pour les droits, le carnet et le
  --   travail -- aucun faux identifiant n'est pose nulle part.
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then
    select h.app_historical_id, h.hektor_annonce_id, h.numero_dossier, h.titre_bien,
           h.statut_annonce, h.diffusable, h.archive
      into d.app_dossier_id, d.hektor_annonce_id, d.numero_dossier, d.titre_bien,
           d.statut_annonce, d.diffusable, d.archive
      from public.app_historical_annonce_index_current h
     where h.app_historical_id = target_dossier_id;

    if not found then
      -- UNE ARCHIVE RESTE EN LECTURE SEULE -- c'est voulu, pas un oubli. On le DIT, au lieu
      -- de rendre « dossier_not_found », qui ne veut rien dire pour celui qui lit.
      if exists (select 1 from public.app_archive_annonce_index_current x
                  where x.app_archive_id = target_dossier_id) then
        raise exception 'annonce_archivee_lecture_seule' using errcode = '22023';
      end if;
      raise exception 'dossier_not_found' using errcode = '22023';
    end if;

    -- ⚠ UNE OFFRE, UN COMPROMIS OU UNE VENTE restent reserves au parc vivant : ils creent une
    --   ligne dans le registre des affaires, et une affaire se tient sur un bien en vie.
    if target_status not in ('active', 'closed') then
      raise exception 'transaction_hors_parc_vivant' using errcode = '22023';
    end if;
  end if;
  -- @repli-fin$b1$,
    $b2$                          when 'closed'     then 'Clos'$b2$
  ];

  -- ⚠ LES FINS DE LIGNE WINDOWS -- piege deja paye, et retrouve ce soir.
  --   `v_def` est lu SANS retour chariot. Ce script, colle depuis Windows, en porte : l'ancre
  --   R1 fait DEUX lignes, elle portait donc un chr(13) absent du corps -> « trouvee 0 fois ».
  --   On normalise les deux tableaux comme le corps.
  FOR i IN 1 .. array_length(a, 1) LOOP
    a[i] := replace(a[i], chr(13), '');
    b[i] := replace(b[i], chr(13), '');
  END LOOP;

  -- ═══ 2. LE VRAI PATCH ═══
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

  -- ═══ ESSAI A -- VENDU/CLOS -> « Actif » : doit MARCHER ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    ra := public.app_change_annonce_status_optimistic(c_hist, 'active', '{}'::jsonb, 7);
    SELECT coalesce(app_dossier_id::text,'NULL'), coalesce(hektor_annonce_id,'(vide)'), payload_json
      INTO ra_dossier, ra_hektor, ra_charge
      FROM public.app_console_job WHERE id = (ra->>'job_id')::uuid;
    SELECT count(*) INTO ra_fiche FROM public.app_dossier_current WHERE app_dossier_id = c_hist;
    SELECT string_agg(champ || '=' || valeur_app, ' | ' ORDER BY champ) INTO ra_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_hist;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN
      ra_dossier := 'ERREUR: ' || SQLERRM; ra_hektor := '-'; ra_fiche := -1; ra_carnet := '-';
    END IF;
  END;

  -- ═══ ESSAI B -- BIEN VIVANT -> « Actif » : rien ne doit changer pour lui ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    rb := public.app_change_annonce_status_optimistic(c_vif, 'active', '{}'::jsonb, 7);
    SELECT coalesce(app_dossier_id::text,'NULL') INTO rb_dossier
      FROM public.app_console_job WHERE id = (rb->>'job_id')::uuid;
    SELECT statut_annonce || ' / diffusable=' || coalesce(diffusable,'(null)') INTO rb_fiche
      FROM public.app_dossier_current WHERE app_dossier_id = c_vif;
    SELECT count(*) INTO rb_carnet FROM public.app_annonce_champ_app WHERE app_dossier_id = c_vif;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN
      rb_dossier := 'ERREUR: ' || SQLERRM; rb_fiche := '-'; rb_carnet := -1;
    END IF;
  END;

  -- ═══ ESSAI C -- ARCHIVE -> « Mandat clos » : doit etre REFUSE ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_change_annonce_status_optimistic(c_arch, 'closed', '{}'::jsonb, 7);
    rc := '(AUCUNE ERREUR -- ANORMAL)';
  EXCEPTION WHEN others THEN rc := SQLERRM;
  END;

  -- ═══ ESSAI D -- VENDU/CLOS -> « Compromis » : doit etre REFUSE ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_change_annonce_status_optimistic(c_hist, 'compromise', '{}'::jsonb, 7);
    rd := '(AUCUNE ERREUR -- ANORMAL)';
  EXCEPTION WHEN others THEN rd := SQLERRM;
  END;

  -- ═══ ESSAI E -- numero inventé : « dossier_not_found » conserve ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_change_annonce_status_optimistic(c_faux, 'active', '{}'::jsonb, 7);
    re := '(AUCUNE ERREUR -- ANORMAL)';
  EXCEPTION WHEN others THEN re := SQLERRM;
  END;

  -- ═══ ESSAI F -- l'ETIQUETTE : « Clos », plus « Mandat clos » ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    PERFORM public.app_change_annonce_status_optimistic(c_vif, 'closed', '{}'::jsonb, 7);
    SELECT coalesce(valeur_app,'(absent)') INTO rf
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_vif AND champ = 'statut';
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN rf := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ ESSAI G -- LE DESARCHIVAGE D'UNE ARCHIVE MARCHE TOUJOURS (5a intact) ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    rg := public.app_restore_annonce_optimistic(c_arch, '{}'::jsonb, 8);
    SELECT coalesce(app_dossier_id::text,'NULL'), coalesce(hektor_annonce_id,'(vide)')
      INTO rg_dossier, rg_hektor
      FROM public.app_console_job WHERE id = (rg->>'job_id')::uuid;
    rg_msg := 'travail cree';
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN
      rg_msg := 'ERREUR: ' || SQLERRM; rg_dossier := '-'; rg_hektor := '-';
    END IF;
  END;

  -- ═══ LE VRAI INVERSE ═══
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  FOR i IN REVERSE array_length(b, 1) .. 1 LOOP
    v_def := replace(v_def, b[i], a[i]);
  END LOOP;
  IF md5(v_def) <> c_emp THEN
    RAISE EXCEPTION 'INVERSE IMPOSSIBLE -- on obtient % au lieu de %', md5(v_def), c_emp;
  END IF;
  EXECUTE v_def;

  v_apres     := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_emp_final := md5(v_apres);
  m_marqueurs := (length(v_apres) - length(replace(v_apres, '@repli', ''))) / 6;

  -- ═══ LE RAPPORT, PUIS L'ANNULATION TOTALE ═══
  rapport :=
    'ESSAI ANNULE -- rien n''a ete ecrit. Mesures :'
    || chr(10) || '--- 1. AVANT -----------------------------------------------------'
    || chr(10) || 'empreinte_avant  = ' || m_emp_avant    || '  (attendu 1f9e987f3a2a9fc977ae4efd6db5b000)'
    || chr(10) || 'taille_avant     = ' || m_taille_avant || '  (attendu 12342)'
    || chr(10) || 'ancres           = ' || m_ancres       || ' (attendu R1=1 R2=1)'
    || chr(10) || '--- 2. APRES LE PATCH -------------------------------------------'
    || chr(10) || 'taille_apres     = ' || m_taille_apres
    || chr(10) || 'empreinte_RETOUR = ' || m_emp_retour   || '  (attendu = empreinte_avant : RIEN D''AUTRE N''A CHANGE)'
    || chr(10) || '--- A. VENDU/CLOS 62963 -> Actif (doit MARCHER) ------------------'
    || chr(10) || 'travail.app_dossier_id  = ' || coalesce(ra_dossier,'?') || '   (attendu 5880239 -- NOTRE vrai numero)'
    || chr(10) || 'travail.hektor_id       = ' || coalesce(ra_hektor,'?')  || '   (attendu 62963)'
    || chr(10) || 'charge.statut_avant     = ' || coalesce(ra_charge->>'statut_avant','(absent)')     || '   (attendu Clos)'
    || chr(10) || 'charge.diffusable_avant = ' || coalesce(ra_charge->>'diffusable_avant','(absent)') || '   (attendu 0)'
    || chr(10) || 'carnet                  = ' || coalesce(ra_carnet,'?')  || '   (attendu diffusable=1 | statut=Actif)'
    || chr(10) || 'lignes de fiche         = ' || coalesce(ra_fiche::text,'?') || '   (attendu 0 : il n''est plus au parc vivant, c''est normal)'
    || chr(10) || '--- B. BIEN VIVANT 62774 -> Actif (INCHANGE) ---------------------'
    || chr(10) || 'travail.app_dossier_id  = ' || coalesce(rb_dossier,'?') || '   (attendu 3828957)'
    || chr(10) || 'fiche apres             = ' || coalesce(rb_fiche,'?')   || '   (attendu Actif / diffusable=1)'
    || chr(10) || 'carnet                  = ' || coalesce(rb_carnet::text,'?') || ' lignes   (attendu 3)'
    || chr(10) || '--- C. ARCHIVE 49544 -> Mandat clos (doit etre REFUSE) -----------'
    || chr(10) || 'message = ' || coalesce(rc,'?') || '   (attendu annonce_archivee_lecture_seule)'
    || chr(10) || '--- D. VENDU/CLOS -> Compromis (doit etre REFUSE) ----------------'
    || chr(10) || 'message = ' || coalesce(rd,'?') || '   (attendu transaction_hors_parc_vivant)'
    || chr(10) || '--- E. numero inventé (doit rester REFUSE) ----------------------'
    || chr(10) || 'message = ' || coalesce(re,'?') || '   (attendu dossier_not_found)'
    || chr(10) || '--- F. l''ETIQUETTE du statut clos -------------------------------'
    || chr(10) || 'carnet.statut = ' || coalesce(rf,'?') || '   (attendu Clos -- et PLUS « Mandat clos »)'
    || chr(10) || '--- G. DESARCHIVER l''archive 49544 (doit TOUJOURS marcher) ------'
    || chr(10) || 'resultat = ' || coalesce(rg_msg,'?') || '   (attendu : travail cree)'
    || chr(10) || 'travail.app_dossier_id = ' || coalesce(rg_dossier,'?') || '   (⚠ NULL aujourd''hui : c''est le defaut 5a, NON corrige ici)'
    || chr(10) || 'travail.hektor_id      = ' || coalesce(rg_hektor,'?')  || '   (attendu 49544)'
    || chr(10) || '--- 3. APRES L''INVERSE -----------------------------------------'
    || chr(10) || 'empreinte_finale = ' || m_emp_final || '  (attendu = empreinte_avant)'
    || chr(10) || 'marqueurs restants = ' || m_marqueurs || '  (attendu 0 : LE REPLI A DISPARU)'
    || chr(10) || '-----------------------------------------------------------------';

  RAISE EXCEPTION '%', rapport;
END $rep$;

ROLLBACK;
