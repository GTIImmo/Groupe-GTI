-- =====================================================================
-- REPETITION de la piece 4 de 3c -- 2026-10-13
--
-- ELLE FAIT TOUT POUR DE VRAI, PUIS TOUT DEFAIT, PUIS ANNULE LA TRANSACTION.
--   ① fige le TEMOIN INVERSE **avant** toute epreuve (ma lecon du jour : mon temoin
--      precedent dependait d'une table que l'epreuve modifiait -> 117/117/118)
--   ② pose la fonction
--   ③ sept epreuves, sur de VRAIES lignes :
--        1. plancher impossible            -> REFUS prouve
--        2. appel normal                   -> 0 pose, 0 efface (deja juste : idempotent)
--        3. ON SIMULE LA NUIT (on vide notre colonne) -> 2 posees, les dates reviennent
--        4. on efface une ligne du CARNET  -> 1 effacee, la colonne se vide
--        5. on remet la ligne du carnet    -> 1 posee, la valeur revient
--        6. PORTEE : on vide, on appelle sur UNE annonce -> 1 posee, l'autre reste vide
--        7. appel sans portee              -> l'autre revient
--   ④ retire la fonction et verifie que l'etat de depart est rendu
--   ⑤ se termine par une erreur VOLONTAIRE qui porte toutes les mesures
--      -> transaction annulee. RIEN N'EST ECRIT.
--
-- A COLLER EN UNE SEULE FOIS. Le resultat attendu est une ERREUR « ESSAI ANNULE »
-- suivie des mesures : c'est le succes.
-- =====================================================================

BEGIN;

SET LOCAL statement_timeout = '120s';

DO $rep$
DECLARE
  -- l'etat de depart
  d_carnet   bigint; d_posees_registre bigint; d_lignes bigint;
  d_62966    text;   d_24933 text;
  -- le temoin inverse, FIGE AVANT LES EPREUVES
  t_nb       bigint; t_md5 text;  t_nb_fin bigint; t_md5_fin text;
  -- les epreuves
  r1 jsonb; r2 jsonb; r3 jsonb; r4 jsonb; r5 jsonb; r6 jsonb; r7 jsonb;
  v3_62966 text; v3_24933 text;
  v4_62966 text; v4_24933 text;
  v5_62966 text;
  v6_62966 text; v6_24933 text;
  v7_62966 text;
  f_62966  text;  f_24933 text;  f_fonction int;
  -- l'enregistrement du battement de coeur
  g_avant int; g_apres int; g_rendu int; g_orphelines int;
  v_msg text;
BEGIN
  -- =================================================================
  -- ① L'ETAT DE DEPART, ET LE TEMOIN FIGE
  -- =================================================================
  SELECT count(*) INTO d_lignes FROM public.app_mandat_register_current;

  SELECT count(*) INTO d_carnet
    FROM public.app_mandat_champ_app
   WHERE champ = 'mandat_date_cloture' AND origine = 'cloture_app'
     AND nullif(btrim(coalesce(valeur_app, '')), '') IS NOT NULL;

  SELECT count(*) INTO d_posees_registre
    FROM public.app_mandat_register_current
   WHERE nullif(btrim(coalesce(mandat_date_cloture_app, '')), '') IS NOT NULL;

  SELECT mandat_date_cloture_app INTO d_62966
    FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text = '62966' AND numero_mandat::text = '18842';
  SELECT mandat_date_cloture_app INTO d_24933
    FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text = '24933' AND numero_mandat::text = '11939';

  -- ⭐ LE TEMOIN INVERSE, FIGE DANS UNE TABLE TEMPORAIRE, AVANT TOUTE EPREUVE.
  --    Il ne depend donc d'AUCUNE table que les epreuves vont modifier.
  CREATE TEMP TABLE _temoin ON COMMIT DROP AS
    SELECT r.register_row_id,
           r.hektor_annonce_id::text AS annonce,
           r.numero_mandat::text     AS numero,
           r.mandat_date_cloture     AS date_hektor
      FROM public.app_mandat_register_current r
     WHERE nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') IS NOT NULL;

  SELECT count(*), md5(string_agg(register_row_id::text || '=' || date_hektor, '|'
                                  ORDER BY register_row_id::text))
    INTO t_nb, t_md5 FROM _temoin;

  -- =================================================================
  -- ② LA FONCTION
  -- =================================================================
  EXECUTE $ddl$
  create or replace function public.app_reposer_cloture_mandat_app(
    target_annonce text default null, plancher_registre int default 10000
  ) returns jsonb language plpgsql security definer set search_path to 'public'
  as $fn$
  DECLARE
    v_annonce  text   := nullif(btrim(coalesce(target_annonce, '')), '');
    v_plancher int    := greatest(coalesce(plancher_registre, 10000), 0);
    v_lignes bigint; v_carnet bigint; v_posees bigint := 0; v_effacees bigint := 0;
  BEGIN
    SELECT count(*) INTO v_lignes FROM public.app_mandat_register_current;
    IF v_lignes < v_plancher THEN
      RETURN jsonb_build_object('statut','refus',
        'raison', format('le registre ne porte que %s lignes, sous le plancher de %s',
                         v_lignes, v_plancher),
        'lignes_registre', v_lignes);
    END IF;
    SELECT count(*) INTO v_carnet FROM public.app_mandat_champ_app
     WHERE champ='mandat_date_cloture' AND origine='cloture_app'
       AND nullif(btrim(coalesce(valeur_app,'')),'') IS NOT NULL;
    WITH poses AS (
      UPDATE public.app_mandat_register_current r
         SET mandat_date_cloture_app = nullif(btrim(k.valeur_app), '')
        FROM public.app_mandat_champ_app k
       WHERE k.champ='mandat_date_cloture' AND k.origine='cloture_app'
         AND nullif(btrim(coalesce(k.valeur_app,'')),'') IS NOT NULL
         AND r.hektor_annonce_id::text = k.hektor_annonce_id
         AND r.numero_mandat::text     = k.numero_mandat
         AND (v_annonce IS NULL OR r.hektor_annonce_id::text = v_annonce)
         AND coalesce(r.mandat_date_cloture_app,'') <> nullif(btrim(k.valeur_app),'')
      RETURNING 1)
    SELECT count(*) INTO v_posees FROM poses;
    WITH effacements AS (
      UPDATE public.app_mandat_register_current r
         SET mandat_date_cloture_app = NULL
       WHERE nullif(btrim(coalesce(r.mandat_date_cloture_app,'')),'') IS NOT NULL
         AND (v_annonce IS NULL OR r.hektor_annonce_id::text = v_annonce)
         AND NOT EXISTS (
           SELECT 1 FROM public.app_mandat_champ_app k
            WHERE k.champ='mandat_date_cloture' AND k.origine='cloture_app'
              AND nullif(btrim(coalesce(k.valeur_app,'')),'') IS NOT NULL
              AND k.hektor_annonce_id = r.hektor_annonce_id::text
              AND k.numero_mandat     = r.numero_mandat::text)
      RETURNING 1)
    SELECT count(*) INTO v_effacees FROM effacements;
    RETURN jsonb_build_object('statut','ok','portee', coalesce(v_annonce,'tout le parc'),
      'carnet', v_carnet, 'posees', v_posees, 'effacees', v_effacees,
      'lignes_registre', v_lignes);
  END $fn$;
  $ddl$;

  EXECUTE 'revoke all on function public.app_reposer_cloture_mandat_app(text,int) from public';
  EXECUTE 'grant execute on function public.app_reposer_cloture_mandat_app(text,int) to service_role';

  -- =================================================================
  -- ③ LES SEPT EPREUVES
  -- =================================================================

  -- 1. LE GARDE-FOU. Un plancher impossible doit faire REFUSER, sans rien ecrire.
  r1 := public.app_reposer_cloture_mandat_app(NULL, 1000000);

  -- 2. UN APPEL NORMAL sur un etat deja juste : 0 pose, 0 efface (idempotent).
  r2 := public.app_reposer_cloture_mandat_app();

  -- 3. ON SIMULE LA NUIT : on vide notre colonne, comme le fait le delete+insert.
  UPDATE public.app_mandat_register_current
     SET mandat_date_cloture_app = NULL
   WHERE mandat_date_cloture_app IS NOT NULL;
  r3 := public.app_reposer_cloture_mandat_app();
  SELECT mandat_date_cloture_app INTO v3_62966 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='62966' AND numero_mandat::text='18842';
  SELECT mandat_date_cloture_app INTO v3_24933 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='24933' AND numero_mandat::text='11939';

  -- 4. ON EFFACE UNE LIGNE DU CARNET (une cloture annulee) -> la colonne doit se vider,
  --    et SEULEMENT celle-la.
  DELETE FROM public.app_mandat_champ_app
   WHERE hektor_annonce_id='62966' AND numero_mandat='18842'
     AND champ='mandat_date_cloture';
  r4 := public.app_reposer_cloture_mandat_app();
  SELECT mandat_date_cloture_app INTO v4_62966 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='62966' AND numero_mandat::text='18842';
  SELECT mandat_date_cloture_app INTO v4_24933 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='24933' AND numero_mandat::text='11939';

  -- 5. ON REMET LA LIGNE DU CARNET -> la valeur doit revenir.
  INSERT INTO public.app_mandat_champ_app
    (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
  VALUES ('62966','18842','mandat_date_cloture','2026-08-28','cloture_app',
          'gonzalez@gti-immobilier.fr', now());
  r5 := public.app_reposer_cloture_mandat_app();
  SELECT mandat_date_cloture_app INTO v5_62966 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='62966' AND numero_mandat::text='18842';

  -- 6. LA PORTEE : on vide tout, on appelle sur UNE SEULE annonce.
  UPDATE public.app_mandat_register_current
     SET mandat_date_cloture_app = NULL
   WHERE mandat_date_cloture_app IS NOT NULL;
  r6 := public.app_reposer_cloture_mandat_app('24933');
  SELECT mandat_date_cloture_app INTO v6_62966 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='62966' AND numero_mandat::text='18842';
  SELECT mandat_date_cloture_app INTO v6_24933 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='24933' AND numero_mandat::text='11939';

  -- 7. PUIS SANS PORTEE : l'autre revient.
  r7 := public.app_reposer_cloture_mandat_app();
  SELECT mandat_date_cloture_app INTO v7_62966 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='62966' AND numero_mandat::text='18842';

  -- 8. L'ENREGISTREMENT DU BATTEMENT DE COEUR.
  --    ⚠ SANS LUI LE GARDE-FOU EST DECORATIF : heartbeat.py ecrit en PATCH FILTRE,
  --      donc une cle sans ligne touche 0 ligne, recoit 204, et COMPTE POUR UN
  --      SUCCES ; et check_gti_health ENUMERE la table, donc il ne la regarde jamais.
  --    On mesure aussi combien de cles du run sont dans ce cas AUJOURD'HUI -- un
  --    sujet du chantier ④, signale et non corrige ici.
  SELECT count(*) INTO g_avant FROM public.app_worker_registry
   WHERE worker_key = 'phase2.repose_cloture_mandat';

  SELECT count(*) INTO g_orphelines FROM (VALUES
    ('phase1.archived_details'),('phase2.adresses_photos'),
    ('phase2.correspondance_annonces'),('phase2.correspondance_identite'),
    ('phase2.derives_photos'),('phase2.doublure_mandat'),
    ('phase2.doublure_relation'),('phase2.rattrapage_photos'),
    ('phase2.sonde_photos')) AS c(k)
   WHERE NOT EXISTS (SELECT 1 FROM public.app_worker_registry r WHERE r.worker_key = c.k);

  INSERT INTO public.app_worker_registry
    (worker_key, worker_name, worker_role, worker_type, criticality, frequency,
     status, owner, script_path, expected_max_runtime_minutes, monitoring_domain,
     source_notes)
  VALUES
    ('phase2.repose_cloture_mandat', 'Re-pose de la cloture de mandat',
     'Repose, APRES le push, notre date de cloture de mandat. Chantier 3c, piece 4.',
     'node_worker', 'medium', 'optional_pipeline_step', 'active', 'frederic',
     'Console/reposer_cloture_mandat.js', 5, 'business', 'Repetition du 13/10/2026.')
  ON CONFLICT (worker_key) DO NOTHING;

  SELECT count(*) INTO g_apres FROM public.app_worker_registry
   WHERE worker_key = 'phase2.repose_cloture_mandat';

  -- =================================================================
  -- ④ ON RETIRE LA FONCTION ET ON VERIFIE L'ETAT RENDU
  -- =================================================================
  EXECUTE 'drop function if exists public.app_reposer_cloture_mandat_app(text,int)';
  DELETE FROM public.app_worker_registry WHERE worker_key = 'phase2.repose_cloture_mandat';
  SELECT count(*) INTO g_rendu FROM public.app_worker_registry
   WHERE worker_key = 'phase2.repose_cloture_mandat';
  SELECT count(*) INTO f_fonction FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_reposer_cloture_mandat_app';

  SELECT mandat_date_cloture_app INTO f_62966 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='62966' AND numero_mandat::text='18842';
  SELECT mandat_date_cloture_app INTO f_24933 FROM public.app_mandat_register_current
   WHERE hektor_annonce_id::text='24933' AND numero_mandat::text='11939';

  -- LE TEMOIN INVERSE, RECOMPARE : les lignes a date de cloture AFFICHEE ne doivent
  -- pas avoir bouge d'un caractere pendant les sept epreuves.
  SELECT count(*), md5(string_agg(x.register_row_id::text || '=' || x.date_hektor, '|'
                                  ORDER BY x.register_row_id::text))
    INTO t_nb_fin, t_md5_fin
    FROM (SELECT r.register_row_id, r.mandat_date_cloture AS date_hektor
            FROM public.app_mandat_register_current r
           WHERE nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') IS NOT NULL) x;

  -- =================================================================
  -- ⑤ L'ERREUR VOLONTAIRE
  -- =================================================================
  v_msg := format(
       E'ESSAI ANNULE -- RIEN N''EST ECRIT. Mesures :\n'
    || E'\n  --- L''ETAT DE DEPART ---------------------------------\n'
    || E'   lignes du registre          %s   (plancher 10 000)\n'
    || E'   clotures au carnet          %s\n'
    || E'   deja posees au registre     %s\n'
    || E'   62966 = %s   ·   24933 = %s\n'
    || E'\n  --- 1. LE GARDE-FOU (plancher impossible) ------------\n'
    || E'   %s\n'
    || E'   (attendu statut=refus, et AUCUNE ecriture)\n'
    || E'\n  --- 2. APPEL NORMAL, etat deja juste ------------------\n'
    || E'   %s\n'
    || E'   (attendu posees=0 effacees=0 : il est idempotent)\n'
    || E'\n  --- 3. ON SIMULE LA NUIT (colonne videe) -------------\n'
    || E'   %s\n'
    || E'   62966 -> %s   ·   24933 -> %s   (attendu 2026-08-28 et 2026-09-18)\n'
    || E'   ⭐ C''EST L''EPREUVE QUI COMPTE : la nuit efface, la re-pose rend.\n'
    || E'\n  --- 4. UNE CLOTURE ANNULEE AU CARNET -----------------\n'
    || E'   %s\n'
    || E'   62966 -> %s   (attendu vide)   ·   24933 -> %s   (attendu intact)\n'
    || E'\n  --- 5. ON REMET LA LIGNE DU CARNET -------------------\n'
    || E'   %s\n'
    || E'   62966 -> %s   (attendu 2026-08-28)\n'
    || E'\n  --- 6. LA PORTEE (une seule annonce) -----------------\n'
    || E'   %s\n'
    || E'   62966 -> %s   (attendu vide)   ·   24933 -> %s   (attendu 2026-09-18)\n'
    || E'\n  --- 7. PUIS SANS PORTEE ------------------------------\n'
    || E'   %s\n'
    || E'   62966 -> %s   (attendu 2026-08-28)\n'
    || E'\n  --- 8. LE BATTEMENT DE COEUR (sans lui, garde-fou decoratif) --\n'
    || E'   notre cle au registre des workers : %s avant, %s apres, %s au retour\n'
    || E'   (attendu 0 -> 1 -> 0)\n'
    || E'   ⚠ cles du run SANS ligne de registre, aujourd''hui : %s sur 9 mesurees\n'
    || E'     (leur battement part dans le vide ET compte pour un succes -- chantier ④)\n'
    || E'\n  --- LE TEMOIN INVERSE (FIGE AVANT LES EPREUVES) ------\n'
    || E'   lignes a date de cloture affichee : %s au depart, %s a la fin\n'
    || E'   leur empreinte : %s\n'
    || E'                    %s\n'
    || E'   (les deux nombres ET les deux empreintes doivent etre EGAUX)\n'
    || E'\n  --- APRES LE RETRAIT --------------------------------\n'
    || E'   la fonction existe-t-elle encore ? %s   (attendu 0)\n'
    || E'   62966 = %s   ·   24933 = %s   (attendu : l''etat de depart)'
    ,
    d_lignes, d_carnet, d_posees_registre,
    coalesce(d_62966,'(vide)'), coalesce(d_24933,'(vide)'),
    r1, r2,
    r3, coalesce(v3_62966,'(vide)'), coalesce(v3_24933,'(vide)'),
    r4, coalesce(v4_62966,'(vide)'), coalesce(v4_24933,'(vide)'),
    r5, coalesce(v5_62966,'(vide)'),
    r6, coalesce(v6_62966,'(vide)'), coalesce(v6_24933,'(vide)'),
    r7, coalesce(v7_62966,'(vide)'),
    g_avant, g_apres, g_rendu, g_orphelines,
    t_nb, t_nb_fin, t_md5, t_md5_fin,
    f_fonction, coalesce(f_62966,'(vide)'), coalesce(f_24933,'(vide)')
  );
  RAISE EXCEPTION '%', v_msg;
END $rep$;

COMMIT;
