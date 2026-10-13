-- =====================================================================
-- REPETITION du patch 3c (pieces 1 et 2) -- 2026-10-13
--
-- ELLE FAIT TOUT POUR DE VRAI, PUIS TOUT DEFAIT, PUIS ANNULE LA TRANSACTION.
--   ① mesure l'etat d'avant
--   ② applique le patch entier (colonne, vue, alerte, re-pose, RPC, droits)
--   ③ EPROUVE LE RPC SUR DE VRAIES LIGNES : une saisie, un effacement, et
--      quatre refus (anonyme, mandat inconnu, date mal formee, date inexistante)
--   ④ applique le VRAI retour arriere
--   ⑤ verifie que tout est revenu a l'identique
--   ⑥ se termine par une erreur VOLONTAIRE qui porte toutes les mesures
--      -> la transaction entiere est annulee. RIEN N'EST ECRIT.
--
-- ⚠ Le test ③ efface puis repose de vraies lignes du carnet (24933). C'est
--   deliberé : c'est le seul moyen de prouver que l'effacement fait bien
--   reapparaitre la date de Hektor. Tout est annule a la fin.
--
-- A COLLER EN UNE SEULE FOIS dans l'editeur SQL. Le resultat attendu est une
-- ERREUR nommee « ESSAI ANNULE » suivie des mesures : c'est le succes.
-- =====================================================================

BEGIN;

SET LOCAL statement_timeout = '120s';

DO $rep$
DECLARE
  c_emp_vue    constant text := '5c64469d579405d028554350d3d44883';
  c_emp_alerte constant text := 'd45b9290d12bfca81f37713c4d361150';
  c_sig_alerte constant text := 'public.app_generate_mandat_echu_alerts()';
  c_moi        constant text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6",'
                                || '"email":"frederic.gerphagnon@gti-immobilier.fr"}';

  a text; b text; n int;
  v_def text; v_new text; v_ancien text;

  -- MESURES
  m_vue_avant      text;  m_vue_apres      text;  m_vue_rendue     text;
  m_alerte_avant   text;  m_alerte_apres   text;  m_alerte_rendue  text;
  m_col_avant      int;   m_col_apres      int;   m_col_rendue     int;
  m_noms_avant     text[]; m_noms_apres    text[];
  m_prefixe_ok     boolean;
  m_autres_avant   int;   m_autres_apres   int;   m_autres_rendu   int;
  m_nos_avant      int;   m_nos_apres      int;
  m_reposees       int;
  m_divergence     int;
  m_rpc_apres      int;   m_rpc_rendu      int;

  -- LES TROIS CLOTURES DE L'APP, AVANT / APRES
  m_detail         text := '';

  -- LE TEST DE SAISIE
  v_t_annonce text; v_t_numero text;
  r_saisie jsonb; r_relu text; r_carnet text; r_origine text; r_auteur text;
  r_efface jsonb; r_apres_efface text;
  r_anon jsonb; r_inconnu jsonb; r_forme jsonb; r_inexistante jsonb;
  v_msg text;
BEGIN
  -- =================================================================
  -- ① L'ETAT D'AVANT
  -- =================================================================
  m_vue_avant    := md5(replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true), chr(13), ''));
  m_alerte_avant := md5(replace(pg_get_functiondef(c_sig_alerte::regprocedure), chr(13), ''));

  IF m_vue_avant <> c_emp_vue THEN
    RAISE EXCEPTION 'STOP : la vue porte % au lieu de %', m_vue_avant, c_emp_vue;
  END IF;
  IF m_alerte_avant <> c_emp_alerte THEN
    RAISE EXCEPTION 'STOP : l''alerte porte % au lieu de %', m_alerte_avant, c_emp_alerte;
  END IF;

  SELECT count(*), array_agg(attname ORDER BY attnum)
    INTO m_col_avant, m_noms_avant
    FROM pg_attribute
   WHERE attrelid = 'public.app_registre_mandats_current'::regclass
     AND attnum > 0 AND NOT attisdropped;

  -- LE TEMOIN INVERSE : les lignes A DATE DE CLOTURE QUI NE SONT PAS LES NOTRES.
  -- Elles ne doivent PAS bouger -- ni en nombre, ni en valeur.
  SELECT count(*) INTO m_autres_avant
    FROM public.app_registre_mandats_current v
   WHERE nullif(btrim(coalesce(v.mandat_date_cloture, '')), '') IS NOT NULL
     AND NOT EXISTS (
       SELECT 1 FROM public.app_mandat_champ_app k
        WHERE k.champ = 'mandat_date_cloture' AND k.origine = 'cloture_app'
          AND k.hektor_annonce_id = v.hektor_annonce_id::text
          AND k.numero_mandat     = v.numero_mandat::text);

  SELECT count(*) INTO m_nos_avant
    FROM public.app_mandat_champ_app
   WHERE champ = 'mandat_date_cloture' AND origine = 'cloture_app'
     AND nullif(btrim(coalesce(valeur_app, '')), '') IS NOT NULL;

  -- le detail des notres, AVANT
  SELECT string_agg(format('%s/%s : notre=%s · hektor=%s · ecran=%s',
                           k.hektor_annonce_id, k.numero_mandat, k.valeur_app,
                           coalesce(v.mandat_date_cloture, '(vide)'),
                           coalesce(v.mandat_date_cloture, '(vide)')),
                    E'\n      ' ORDER BY k.valeur_app)
    INTO m_detail
    FROM public.app_mandat_champ_app k
    LEFT JOIN public.app_mandat_register_current v
      ON v.hektor_annonce_id::text = k.hektor_annonce_id
     AND v.numero_mandat::text     = k.numero_mandat
   WHERE k.champ = 'mandat_date_cloture' AND k.origine = 'cloture_app';

  -- =================================================================
  -- ② LE PATCH, EN ENTIER
  -- =================================================================
  ALTER TABLE public.app_mandat_register_current
    ADD COLUMN IF NOT EXISTS mandat_date_cloture_app text;

  -- --- la vue, refaite depuis elle-meme ---
  v_def := replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true), chr(13), '');

  a := chr(10) || '    mandat_date_cloture,' || chr(10);
  b := chr(10) || '    COALESCE(NULLIF(btrim(mandat_date_cloture_app), ''''::text), mandat_date_cloture) AS mandat_date_cloture,' || chr(10);
  n := (length(v_def) - length(replace(v_def, a, ''))) / length(a);
  IF n <> 1 THEN RAISE EXCEPTION 'ESSAI ANNULE : ancre R1 trouvee % fois, il en faut 1', n; END IF;
  v_new := replace(v_def, a, b);

  a := '    mandants_json' || chr(10) || '   FROM app_mandat_register_current r;';
  b := '    mandants_json,' || chr(10)
       || '    mandat_date_cloture_app,' || chr(10)
       || '    mandat_date_cloture AS mandat_date_cloture_hektor' || chr(10)
       || '   FROM app_mandat_register_current r;';
  n := (length(v_new) - length(replace(v_new, a, ''))) / length(a);
  IF n <> 1 THEN RAISE EXCEPTION 'ESSAI ANNULE : ancre R2 trouvee % fois, il en faut 1', n; END IF;
  v_new := replace(v_new, a, b);

  EXECUTE 'create or replace view public.app_registre_mandats_current '
          || 'with (security_invoker=on) as ' || v_new;

  -- --- l'alerte ---
  v_def := replace(pg_get_functiondef(c_sig_alerte::regprocedure), chr(13), '');
  a := replace($a1$          and nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null$a1$, chr(13), '');
  b := replace($b1$          and (nullif(btrim(coalesce(r.mandat_date_cloture_app, '')), '') is not null
               or nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null)$b1$, chr(13), '');
  n := (length(v_def) - length(replace(v_def, a, ''))) / length(a);
  IF n <> 2 THEN RAISE EXCEPTION 'ESSAI ANNULE : ancre alerte trouvee % fois, il en faut 2', n; END IF;
  EXECUTE replace(v_def, a, b);

  -- --- la re-pose des clotures de l'app ---
  UPDATE public.app_mandat_register_current r
     SET mandat_date_cloture_app = nullif(btrim(k.valeur_app), '')
    FROM public.app_mandat_champ_app k
   WHERE k.champ = 'mandat_date_cloture' AND k.origine = 'cloture_app'
     AND nullif(btrim(coalesce(k.valeur_app, '')), '') IS NOT NULL
     AND r.hektor_annonce_id::text = k.hektor_annonce_id
     AND r.numero_mandat::text     = k.numero_mandat;
  GET DIAGNOSTICS m_reposees = ROW_COUNT;

  -- --- le RPC ---
  EXECUTE $ddl$
  create or replace function public.app_set_mandat_cloture_optimistic(
    target_annonce text, target_numero_mandat text, cloture_date text default null
  ) returns jsonb language plpgsql security definer set search_path to 'public'
  as $fn$
  DECLARE
    v_annonce text := nullif(btrim(coalesce(target_annonce, '')), '');
    v_numero  text := nullif(btrim(coalesce(target_numero_mandat, '')), '');
    v_date    text := nullif(btrim(coalesce(cloture_date, '')), '');
    v_claims jsonb; v_sub text; v_role text; v_email text;
    v_avant_app text; v_avant_hektor text; v_trouve boolean := false;
  BEGIN
    BEGIN
      v_claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;
    EXCEPTION WHEN others THEN v_claims := null; END;
    v_sub   := nullif(btrim(coalesce(v_claims ->> 'sub',   '')), '');
    v_role  := nullif(btrim(coalesce(v_claims ->> 'role',  '')), '');
    v_email := nullif(btrim(coalesce(v_claims ->> 'email', '')), '');
    IF v_sub is null AND coalesce(v_role, '') <> 'service_role' THEN
      RETURN jsonb_build_object('ok', false, 'erreur', 'non_authentifie');
    END IF;
    IF v_annonce is null OR v_numero is null THEN
      RETURN jsonb_build_object('ok', false, 'erreur', 'parametres_incomplets');
    END IF;
    IF v_date is not null THEN
      IF v_date !~ '^\d{4}-\d{2}-\d{2}$' THEN
        RETURN jsonb_build_object('ok', false, 'erreur', 'date_illisible', 'valeur', v_date);
      END IF;
      BEGIN PERFORM v_date::date;
      EXCEPTION WHEN others THEN
        RETURN jsonb_build_object('ok', false, 'erreur', 'date_inexistante', 'valeur', v_date);
      END;
    END IF;
    SELECT true, r.mandat_date_cloture_app, r.mandat_date_cloture
      INTO v_trouve, v_avant_app, v_avant_hektor
      FROM public.app_mandat_register_current r
     WHERE r.hektor_annonce_id::text = v_annonce AND r.numero_mandat::text = v_numero;
    IF NOT coalesce(v_trouve, false) THEN
      RETURN jsonb_build_object('ok', false, 'erreur', 'mandat_introuvable',
                                'annonce', v_annonce, 'numero_mandat', v_numero);
    END IF;
    IF v_date is null THEN
      DELETE FROM public.app_mandat_champ_app
       WHERE hektor_annonce_id = v_annonce AND numero_mandat = v_numero
         AND champ = 'mandat_date_cloture' AND origine = 'cloture_app';
    ELSE
      INSERT INTO public.app_mandat_champ_app
        (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
      VALUES (v_annonce, v_numero, 'mandat_date_cloture', v_date, 'cloture_app',
              coalesce(v_email, v_sub), now())
      ON CONFLICT (hektor_annonce_id, numero_mandat, champ) DO UPDATE
         SET valeur_app = excluded.valeur_app, origine = 'cloture_app',
             ecrit_par = excluded.ecrit_par, ecrit_le = now();
    END IF;
    UPDATE public.app_mandat_register_current
       SET mandat_date_cloture_app = v_date
     WHERE hektor_annonce_id::text = v_annonce AND numero_mandat::text = v_numero;
    RETURN jsonb_build_object('ok', true, 'annonce', v_annonce, 'numero_mandat', v_numero,
      'date_cloture', v_date, 'efface', (v_date is null), 'avant_app', v_avant_app,
      'date_hektor', v_avant_hektor, 'ecrit_par', coalesce(v_email, v_sub, 'service_role'));
  END $fn$;
  $ddl$;

  EXECUTE 'revoke all on function public.app_set_mandat_cloture_optimistic(text,text,text) from public';
  EXECUTE 'grant execute on function public.app_set_mandat_cloture_optimistic(text,text,text) to authenticated, service_role';

  -- =================================================================
  -- MESURES APRES LE PATCH
  -- =================================================================
  m_vue_apres    := md5(replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true), chr(13), ''));
  m_alerte_apres := md5(replace(pg_get_functiondef(c_sig_alerte::regprocedure), chr(13), ''));

  SELECT count(*), array_agg(attname ORDER BY attnum)
    INTO m_col_apres, m_noms_apres
    FROM pg_attribute
   WHERE attrelid = 'public.app_registre_mandats_current'::regclass
     AND attnum > 0 AND NOT attisdropped;
  m_prefixe_ok := (m_noms_apres[1:m_col_avant] = m_noms_avant);

  SELECT count(*) INTO m_autres_apres
    FROM public.app_registre_mandats_current v
   WHERE nullif(btrim(coalesce(v.mandat_date_cloture, '')), '') IS NOT NULL
     AND NOT EXISTS (
       SELECT 1 FROM public.app_mandat_champ_app k
        WHERE k.champ = 'mandat_date_cloture' AND k.origine = 'cloture_app'
          AND k.hektor_annonce_id = v.hektor_annonce_id::text
          AND k.numero_mandat     = v.numero_mandat::text);

  SELECT count(*) INTO m_nos_apres
    FROM public.app_registre_mandats_current v
   WHERE nullif(btrim(coalesce(v.mandat_date_cloture_app, '')), '') IS NOT NULL;

  -- le detail des notres, APRES : ce que l'ecran montre maintenant
  SELECT m_detail || E'\n   --- APRES le patch ---\n      ' ||
         string_agg(format('%s/%s : ecran=%s (notre=%s · hektor=%s)',
                           k.hektor_annonce_id, k.numero_mandat,
                           coalesce(v.mandat_date_cloture, '(vide)'),
                           coalesce(v.mandat_date_cloture_app, '(vide)'),
                           coalesce(v.mandat_date_cloture_hektor, '(vide)')),
                    E'\n      ' ORDER BY k.valeur_app)
    INTO m_detail
    FROM public.app_mandat_champ_app k
    LEFT JOIN public.app_registre_mandats_current v
      ON v.hektor_annonce_id::text = k.hektor_annonce_id
     AND v.numero_mandat::text     = k.numero_mandat
   WHERE k.champ = 'mandat_date_cloture' AND k.origine = 'cloture_app';

  -- LES ALERTES : combien de dossiers changent de sort A CAUSE de notre colonne ?
  SELECT count(*) INTO m_divergence
    FROM public.app_dossier_current d
   WHERE d.negociateur_email IS NOT NULL AND d.negociateur_email <> ''
     AND coalesce(d.numero_mandat, '') <> ''
     AND d.mandat_date_fin ~ '^\d{4}-\d{2}-\d{2}$'
     AND d.mandat_date_fin::date < current_date
     AND coalesce(d.archive, '0') <> '1'
     AND lower(coalesce(d.statut_annonce, '')) NOT SIMILAR TO '%(clos|clotur|vendu|vente)%'
     AND EXISTS (SELECT 1 FROM public.app_mandat_register_current r
                  WHERE r.hektor_annonce_id = d.hektor_annonce_id
                    AND r.numero_mandat = d.numero_mandat
                    AND nullif(btrim(coalesce(r.mandat_date_cloture_app, '')), '') IS NOT NULL)
     AND NOT EXISTS (SELECT 1 FROM public.app_mandat_register_current r
                  WHERE r.hektor_annonce_id = d.hektor_annonce_id
                    AND r.numero_mandat = d.numero_mandat
                    AND nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') IS NOT NULL);

  SELECT count(*) INTO m_rpc_apres
    FROM pg_proc p JOIN pg_namespace ns ON ns.oid = p.pronamespace
   WHERE ns.nspname = 'public' AND p.proname = 'app_set_mandat_cloture_optimistic';

  -- =================================================================
  -- ③ LES EPREUVES DU RPC, SUR DE VRAIES LIGNES
  -- =================================================================
  PERFORM set_config('request.jwt.claims', c_moi, true);

  -- (a) UNE SAISIE. On choisit un mandat SANS aucune date de cloture, et on
  --     ordonne la recherche : un LIMIT sans ORDER BY ne prouve rien.
  SELECT r.hektor_annonce_id::text, r.numero_mandat::text
    INTO v_t_annonce, v_t_numero
    FROM public.app_mandat_register_current r
   WHERE nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') IS NULL
     AND nullif(btrim(coalesce(r.mandat_date_cloture_app, '')), '') IS NULL
   ORDER BY r.register_row_id
   LIMIT 1;

  r_saisie := public.app_set_mandat_cloture_optimistic(v_t_annonce, v_t_numero, '2026-10-13');

  SELECT v.mandat_date_cloture INTO r_relu
    FROM public.app_registre_mandats_current v
   WHERE v.hektor_annonce_id::text = v_t_annonce AND v.numero_mandat::text = v_t_numero;

  SELECT k.valeur_app, k.origine, k.ecrit_par INTO r_carnet, r_origine, r_auteur
    FROM public.app_mandat_champ_app k
   WHERE k.hektor_annonce_id = v_t_annonce AND k.numero_mandat = v_t_numero
     AND k.champ = 'mandat_date_cloture';

  -- (b) L'EFFACEMENT, sur 24933 : notre date part, CELLE DE HEKTOR REAPPARAIT.
  r_efface := public.app_set_mandat_cloture_optimistic('24933', '11939', NULL);
  SELECT v.mandat_date_cloture INTO r_apres_efface
    FROM public.app_registre_mandats_current v
   WHERE v.hektor_annonce_id::text = '24933' AND v.numero_mandat::text = '11939';

  -- (c) LES QUATRE REFUS.
  r_inconnu     := public.app_set_mandat_cloture_optimistic('999999999', '999999999', '2026-10-13');
  r_forme       := public.app_set_mandat_cloture_optimistic(v_t_annonce, v_t_numero, '13/10/2026');
  r_inexistante := public.app_set_mandat_cloture_optimistic(v_t_annonce, v_t_numero, '2026-13-32');

  PERFORM set_config('request.jwt.claims', '', true);
  r_anon := public.app_set_mandat_cloture_optimistic(v_t_annonce, v_t_numero, '2026-10-13');
  PERFORM set_config('request.jwt.claims', c_moi, true);

  -- =================================================================
  -- ④ LE VRAI RETOUR ARRIERE
  -- =================================================================
  v_def := replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true), chr(13), '');
  b := '    mandants_json,' || chr(10)
       || '    mandat_date_cloture_app,' || chr(10)
       || '    mandat_date_cloture AS mandat_date_cloture_hektor' || chr(10)
       || '   FROM app_mandat_register_current r;';
  a := '    mandants_json' || chr(10) || '   FROM app_mandat_register_current r;';
  v_ancien := replace(v_def, b, a);
  b := chr(10) || '    COALESCE(NULLIF(btrim(mandat_date_cloture_app), ''''::text), mandat_date_cloture) AS mandat_date_cloture,' || chr(10);
  a := chr(10) || '    mandat_date_cloture,' || chr(10);
  v_ancien := replace(v_ancien, b, a);

  IF md5(v_ancien) <> c_emp_vue THEN
    RAISE EXCEPTION 'ESSAI ANNULE : la vue reconstruite porte % au lieu de %', md5(v_ancien), c_emp_vue;
  END IF;
  DROP VIEW public.app_registre_mandats_current;
  EXECUTE 'create view public.app_registre_mandats_current with (security_invoker=on) as ' || v_ancien;
  EXECUTE 'grant select on public.app_registre_mandats_current to authenticated';
  EXECUTE 'grant all    on public.app_registre_mandats_current to service_role';

  v_def := replace(pg_get_functiondef(c_sig_alerte::regprocedure), chr(13), '');
  b := replace($b2$          and (nullif(btrim(coalesce(r.mandat_date_cloture_app, '')), '') is not null
               or nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null)$b2$, chr(13), '');
  a := replace($a2$          and nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null$a2$, chr(13), '');
  EXECUTE replace(v_def, b, a);

  EXECUTE 'drop function if exists public.app_set_mandat_cloture_optimistic(text,text,text)';

  UPDATE public.app_mandat_register_current
     SET mandat_date_cloture_app = NULL
   WHERE mandat_date_cloture_app IS NOT NULL;

  -- =================================================================
  -- ⑤ TOUT EST-IL REVENU ?
  -- =================================================================
  m_vue_rendue    := md5(replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true), chr(13), ''));
  m_alerte_rendue := md5(replace(pg_get_functiondef(c_sig_alerte::regprocedure), chr(13), ''));

  SELECT count(*) INTO m_col_rendue
    FROM pg_attribute
   WHERE attrelid = 'public.app_registre_mandats_current'::regclass
     AND attnum > 0 AND NOT attisdropped;

  SELECT count(*) INTO m_autres_rendu
    FROM public.app_registre_mandats_current v
   WHERE nullif(btrim(coalesce(v.mandat_date_cloture, '')), '') IS NOT NULL
     AND NOT EXISTS (
       SELECT 1 FROM public.app_mandat_champ_app k
        WHERE k.champ = 'mandat_date_cloture' AND k.origine = 'cloture_app'
          AND k.hektor_annonce_id = v.hektor_annonce_id::text
          AND k.numero_mandat     = v.numero_mandat::text);

  SELECT count(*) INTO m_rpc_rendu
    FROM pg_proc p JOIN pg_namespace ns ON ns.oid = p.pronamespace
   WHERE ns.nspname = 'public' AND p.proname = 'app_set_mandat_cloture_optimistic';

  -- =================================================================
  -- ⑥ L'ERREUR VOLONTAIRE : elle annule TOUT et rend les mesures.
  --    Le message est bati dans une variable : le premier argument de
  --    format() est une EXPRESSION, donc les E'...' peuvent s'y joindre
  --    par || -- ce qu'une concatenation implicite de RAISE refuse
  --    (erreur 42601 mesuree le 13/10).
  -- =================================================================
  v_msg := format(
       E'ESSAI ANNULE -- RIEN N''EST ECRIT. Mesures :\n'
    || E'\n  --- LA VUE --------------------------------------------\n'
    || E'   empreinte   avant %s\n'
    || E'               apres %s\n'
    || E'               rendue %s\n'
    || E'   colonnes    avant %s  ->  apres %s  ->  rendue %s   (attendu 71 -> 73 -> 71)\n'
    || E'   les %s anciens noms sont-ils tous la, dans l''ordre ? %s   (attendu true)\n'
    || E'\n  --- L''ALERTE << MANDAT ECHU >> ------------------------\n'
    || E'   empreinte   avant %s\n'
    || E'               apres %s\n'
    || E'               rendue %s\n'
    || E'   dossiers dont le sort CHANGE a cause de notre colonne : %s   (attendu 0)\n'
    || E'\n  --- LE TEMOIN INVERSE --------------------------------\n'
    || E'   lignes a date de cloture QUI NE SONT PAS LES NOTRES :\n'
    || E'      avant %s  /  apres %s  /  rendue %s   (les trois doivent etre EGAUX)\n'
    || E'   nos clotures au carnet : %s     reposees a la vitrine : %s\n'
    || E'   visibles par l''ecran apres le patch : %s   (attendu : autant que reposees)\n'
    || E'\n  --- NOS CLOTURES, AVANT ET APRES ---------------------\n'
    || E'      %s\n'
    || E'\n  --- LE RPC, EPROUVE POUR DE VRAI ---------------------\n'
    || E'   mandat d''essai            %s/%s\n'
    || E'   (a) saisie                %s\n'
    || E'       relu dans la vue      %s   (attendu 2026-10-13)\n'
    || E'       au carnet             %s · origine %s · auteur %s\n'
    || E'   (b) effacement 24933      %s\n'
    || E'       l''ecran montre        %s   (attendu 2026-10-05, LA DATE DE HEKTOR)\n'
    || E'   (c) mandat inconnu        %s\n'
    || E'   (d) date mal formee       %s\n'
    || E'   (e) date inexistante      %s\n'
    || E'   (f) anonyme               %s\n'
    || E'\n  --- APRES LE RETOUR ARRIERE --------------------------\n'
    || E'   le RPC existe-t-il ? apres le patch %s , apres le retour %s   (attendu 1 puis 0)'
    ,
    m_vue_avant,
    m_vue_apres,
    m_vue_rendue,
    m_col_avant,
    m_col_apres,
    m_col_rendue,
    m_col_avant,
    m_prefixe_ok,
    m_alerte_avant,
    m_alerte_apres,
    m_alerte_rendue,
    m_divergence,
    m_autres_avant,
    m_autres_apres,
    m_autres_rendu,
    m_nos_avant,
    m_reposees,
    m_nos_apres,
    m_detail,
    v_t_annonce,
    v_t_numero,
    r_saisie,
    coalesce(r_relu, '(vide)'),
    coalesce(r_carnet, '(absent)'),
    coalesce(r_origine, '-'),
    coalesce(r_auteur, '-'),
    r_efface,
    coalesce(r_apres_efface, '(vide)'),
    r_inconnu,
    r_forme,
    r_inexistante,
    r_anon,
    m_rpc_apres,
    m_rpc_rendu
  );
  RAISE EXCEPTION '%', v_msg;
END $rep$;

COMMIT;
