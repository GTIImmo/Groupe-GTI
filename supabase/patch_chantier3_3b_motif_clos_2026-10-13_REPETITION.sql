-- =====================================================================
-- REPETITION -- le motif du statut « Clos » au carnet (13/10/2026)
-- A COLLER DANS : https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
-- ⚠ ELLE N'ECRIT RIEN : une transaction qui finit par une erreur volontaire.
--
-- LES ESSAIS :
--   A  « Mandat clos » avec un motif  -> le carnet doit porter `clos_motif`
--   B  « Actif » (pas de motif)       -> AUCUNE ligne `clos_motif` -- le TEMOIN
--   C  apres l'inverse : l'empreinte revient
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '120s';

DO $rep$
DECLARE
  c_sig constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp constant text := '97ef1f2538d16dadee7ce6129286adbe';
  c_moi constant text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6"}';
  c_vif constant bigint := 5941336;   -- parc VIVANT, annonce Hektor 62965

  a text; b text; v_def text; v_apres text; v_retour text; n int;
  m_emp_avant text; m_taille_avant int; m_ancre int; m_taille_apres int;
  m_emp_retour text; m_emp_final text;
  ra jsonb; ra_carnet text;
  rb jsonb; rb_carnet text;
  rapport text;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_emp_avant := md5(v_def); m_taille_avant := length(v_def);
  IF m_emp_avant <> c_emp THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- empreinte % au lieu de %', m_emp_avant, c_emp;
  END IF;
  IF position('clos_motif' in v_def) > 0 THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- le patch est deja passe';
  END IF;

  a := replace($a1$          from (values ('statut'::text,     v_statut_cible),
                       ('diffusable'::text, v_diff_cible)) as x(champ, valeur)$a1$, chr(13), '');
  b := replace($b1$          from (values ('statut'::text,     v_statut_cible),
                       ('diffusable'::text, v_diff_cible),
                       -- @clos-motif (13/10/2026) : LE MOTIF DE LA CLOTURE, GARDE CHEZ NOUS.
                       --   Il est saisi a l'ecran (3 etats, 7 raisons, plus un texte libre),
                       --   le worker le normalise et le controle -- puis la seule fonction qui
                       --   l'utilise est derriere `CONSOLE_HEKTOR_CLOTURE_MANDAT`, ETEINT
                       --   depuis le 28/08 : le formulaire `validerClos` echouait sur 98,8 %
                       --   du parc (il exige un n° de mandat, et la cloture est irreversible
                       --   chez Hektor). Le motif n'allait donc NULLE PART.
                       --   Decision de Frederic du 13/10 : au carnet, comme celui de
                       --   l'archivage. ⚠ Seulement pour « closed » -- la condition
                       --   `where x.valeur is not null` ecarte les autres toute seule.
                       ('clos_motif'::text, case when target_status = 'closed'
                          then nullif(concat_ws(' · ',
                                 nullif(trim(coalesce(v_payload->>'close_etat',   '')), ''),
                                 nullif(trim(coalesce(v_payload->>'close_raison', '')), ''),
                                 nullif(trim(coalesce(v_payload->>'close_reason', '')), '')), '')
                          else null end)) as x(champ, valeur)$b1$, chr(13), '');

  m_ancre := (length(v_def) - length(replace(v_def, a, ''))) / length(a);
  IF m_ancre <> 1 THEN RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- ancre trouvee % fois', m_ancre; END IF;

  EXECUTE replace(v_def, a, b);
  v_apres := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_taille_apres := length(v_apres);
  m_emp_retour := md5(replace(v_apres, b, a));

  -- ═══ A -- « Mandat clos » AVEC un motif ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    ra := public.app_change_annonce_status_optimistic(c_vif, 'closed',
            '{"close_etat":"choiceNonRenouv","close_raison":"concurence"}'::jsonb, 7);
    SELECT string_agg(champ||'='||valeur_app, ' | ' ORDER BY champ) INTO ra_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_vif;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN ra_carnet := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ B -- LE TEMOIN : « Actif », aucun motif attendu ═══
  BEGIN
    PERFORM set_config('request.jwt.claims', c_moi, true);
    rb := public.app_change_annonce_status_optimistic(c_vif, 'active', '{}'::jsonb, 7);
    SELECT string_agg(champ, ', ' ORDER BY champ) INTO rb_carnet
      FROM public.app_annonce_champ_app WHERE app_dossier_id = c_vif;
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN rb_carnet := 'ERREUR: ' || SQLERRM; END IF;
  END;

  -- ═══ L'INVERSE ═══
  v_def := replace(replace(pg_get_functiondef(c_sig::regprocedure), chr(13), ''), b, a);
  IF md5(v_def) <> c_emp THEN RAISE EXCEPTION 'INVERSE IMPOSSIBLE -- rend %', md5(v_def); END IF;
  EXECUTE v_def;
  m_emp_final := md5(replace(pg_get_functiondef(c_sig::regprocedure), chr(13), ''));

  rapport :=
    'ESSAI ANNULE -- rien n''a ete ecrit. Mesures :'
    || chr(10) || 'empreinte_avant  = ' || m_emp_avant || '  (attendu 97ef1f2538d16dadee7ce6129286adbe)'
    || chr(10) || 'taille_avant     = ' || m_taille_avant || '  (attendu 14685)'
    || chr(10) || 'ancre            = ' || m_ancre || '  (attendu 1)'
    || chr(10) || 'taille_apres     = ' || m_taille_apres
    || chr(10) || 'empreinte_RETOUR = ' || m_emp_retour || '  (attendu = empreinte_avant)'
    || chr(10) || '--- A. « Mandat clos » avec motif « non renouvele / concurrence » ---'
    || chr(10) || 'carnet = ' || coalesce(ra_carnet,'?')
    || chr(10) || '  (attendu : clos_motif=choiceNonRenouv · concurence, a cote de statut=Clos et diffusable=0)'
    || chr(10) || '--- B. LE TEMOIN : « Actif », aucun motif ---------------------------'
    || chr(10) || 'champs au carnet = ' || coalesce(rb_carnet,'?')
    || chr(10) || '  (attendu : PAS de clos_motif)'
    || chr(10) || '--- C. APRES L''INVERSE ---------------------------------------------'
    || chr(10) || 'empreinte_finale = ' || m_emp_final || '  (attendu = empreinte_avant)';

  RAISE EXCEPTION '%', rapport;
END $rep$;

ROLLBACK;
