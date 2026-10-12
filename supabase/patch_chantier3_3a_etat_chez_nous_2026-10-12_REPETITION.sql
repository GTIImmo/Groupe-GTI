-- =====================================================================
-- REPETITION du patch CHANTIER ③ POINT 3a (12/10/2026)
--
-- A COLLER DANS L'EDITEUR SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- ⚠ ELLE N'ECRIT RIEN. Tout se passe dans UNE transaction qui se termine par une erreur
--   volontaire : PostgreSQL annule donc l'integralite. Le message d'erreur porte les
--   mesures -- recopie-le-moi tel quel.
--
-- CE QU'ELLE EPROUVE, dans les DEUX SENS :
--   1. l'etat d'AVANT (empreinte, taille, ancre unique)
--   2. le VRAI patch applique
--   3. ESSAI A -- mise sous mandat sur le bien d'essai 62774 : le statut et le diffusable
--      doivent CHANGER chez nous, le carnet doit GAGNER 2 lignes, l'etat d'avant doit
--      etre dans la charge du travail, et `archive` / `offre_id` ne doivent PAS bouger
--   4. ESSAI B -- « Mandat clos » sur le bien d'essai 62963 : idem en sens inverse
--   5. ESSAI C -- interrupteur ETEINT : RIEN ne doit changer chez nous, et le travail
--      doit partir quand meme (le comportement d'avant, a l'identique)
--   6. le VRAI inverse : le bloc doit DISPARAITRE et l'empreinte REVENIR a l'identique
--
--   Les trois essais appellent la VRAIE fonction, en empruntant l'identite de Frederic
--   (admin), chacun dans un point de reprise annule aussitot : les ecritures sont reelles
--   le temps de la mesure, puis effacees.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '120s';

DO $rep$
DECLARE
  c_sig    constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp    constant text := '302852e8dc23c44d6e0442b81e6cb577';
  c_taille constant int  := 8446;
  c_ancre  constant text := $ancre$  -- Le travail emporte le numero d'affaire : c'est lui qui permettra de la retrouver.$ancre$;
  c_deb    constant text := '  -- @3a-debut';
  c_fin    constant text := '  -- @3a-fin';
  c_moi    constant text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6"}';
  c_bienA  constant bigint := 3828957;   -- annonce Hektor 62774
  c_bienB  constant bigint := 5880239;   -- annonce Hektor 62963

  v_def    text;
  v_bloc   text;
  v_apres  text;
  v_nu     text;
  i int; j int; n int;

  m_emp_avant     text;  m_taille_avant int;  m_ancre_avant  int;
  m_emp_apres     text;  m_taille_apres int;  m_ancre_apres  int;
  m_bloc_present  int;   m_emp_nue      text; m_bloc_octets  int;
  m_emp_final     text;  m_bloc_final   int;

  a_st_av text; a_di_av text; a_ar_av text; a_of_av text; a_ca_av int;
  a_st_ap text; a_di_ap text; a_ar_ap text; a_of_ap int;  a_ca_ap int;
  a_ret jsonb;  a_charge jsonb;

  b_st_av text; b_di_av text; b_ca_av int;
  b_st_ap text; b_di_ap text; b_ca_ap int;
  b_ret jsonb;  b_charge jsonb;

  c_st_ap text; c_di_ap text; c_ca_ap int; c_jobs_av int; c_jobs_ap int;
  c_ret jsonb;

  rapport text;
BEGIN
  -- ═══ 1. L'ETAT D'AVANT ═══
  v_def          := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_emp_avant    := md5(v_def);
  m_taille_avant := length(v_def);
  m_ancre_avant  := (length(v_def) - length(replace(v_def, c_ancre, ''))) / length(c_ancre);

  IF m_emp_avant <> c_emp THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- la fonction n''est plus celle mesuree le 12/10 (empreinte %, attendue %)', m_emp_avant, c_emp;
  END IF;
  IF position('@3a-debut' in v_def) > 0 THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- le patch est deja passe';
  END IF;
  IF m_ancre_avant <> 1 THEN
    RAISE EXCEPTION 'ESSAI IMPOSSIBLE -- ancre trouvee % fois', m_ancre_avant;
  END IF;

  -- ═══ 2. L'INTERRUPTEUR ET LE VRAI PATCH ═══
  INSERT INTO public.app_setting (key, value, description, updated_at)
  VALUES ('etat_annonce_ecrit_chez_nous', 'on', 'repetition 12/10', now())
  ON CONFLICT (key) DO UPDATE SET value = 'on', updated_at = now();

  v_bloc := $bloc$  -- @3a-debut   CHANTIER 3, POINT 3a (12/10/2026) : CHEZ NOUS D'ABORD, PUIS HEKTOR
  --
  -- POURQUOI. « Actif » et « Mandat clos » n'ecrivaient RIEN chez nous : v_kind est null
  -- pour eux, et tout ce que cette fonction ecrivait etait enferme dans
  -- `if v_kind is not null`. Notre base attendait donc la relecture de Hektor pour savoir
  -- l'etat de notre propre bien -- 78 s mesurees sur l'annonce 62963 le 08/10.
  -- Regle de Frederic du 12/10 : « d'abord ecrire sur l'app puis envoyer a Hektor, ne pas
  -- dependre », « SUR TOUS LES GESTES ».
  --
  -- LES VALEURS SONT CELLES DU WORKER, mot pour mot -- HEKTOR_STATUS_CONFIG,
  -- Console/console_job_worker.js:10924-10930 (statut 2/3/4/5/6 ; diffusable 1 pour Actif,
  -- 0 pour Mandat clos, rien pour les trois transactions : c'est Hektor qui decide).
  --
  -- ⚠ ON NE TOUCHE PAS offre_id / compromis_id / vente_id. Hektor seul les cree, et ils
  --   servent a ANNULER : les inventer casserait l'annulation (etude du 29/06). La pastille
  --   de l'ecran retombe sur statut_annonce quand ils sont vides (App.tsx:23554-23560) --
  --   le statut suffit donc a la faire bouger.
  -- ⚠ ON NE TOUCHE PAS `archive` : c'est un autre geste (point 3b).
  declare
    v_statut_cible text;
    v_diff_cible   text;
  begin
    if coalesce((select s.value from public.app_setting s
                  where s.key = 'etat_annonce_ecrit_chez_nous'), 'off') = 'on' then

      v_statut_cible := case target_status
                          when 'active'     then 'Actif'
                          when 'offer'      then 'Sous offre'
                          when 'compromise' then 'Sous compromis'
                          when 'sold'       then 'Vendu'
                          when 'closed'     then 'Mandat clos'
                          else null end;
      v_diff_cible   := case target_status
                          when 'active' then '1'
                          when 'closed' then '0'
                          else null end;

      if v_statut_cible is not null then
        -- 1. L'ETAT D'AVANT VOYAGE DANS LA CHARGE. `d` a ete lu en tete de la fonction :
        --    ce sont bien les valeurs d'AVANT. Personne ne les relit encore (le worker n'a
        --    pas de chemin de retour pour ce geste) : elles sont posees maintenant pour que
        --    le second temps n'ait plus rien a changer ici.
        v_payload := v_payload || jsonb_build_object(
          'statut_avant',     d.statut_annonce,
          'diffusable_avant', d.diffusable);

        -- 2. LA FICHE DU BIEN : visible tout de suite, par l'ecran et par tout le monde.
        update public.app_dossier_current
           set statut_annonce = v_statut_cible,
               diffusable     = coalesce(v_diff_cible, d.diffusable)
         where app_dossier_id = target_dossier_id;

        -- 3. LE CARNET : ce que l'app DETIENT, champ par champ. Il n'est relu par personne
        --    aujourd'hui (CHAMPS_APP_ANNONCE est vide dans phase2/identite/contrat_autorite.py)
        --    et c'est voulu : il devient la verite le jour ou Frederic allume l'interrupteur
        --    du contrat d'autorite. Meme patron que le geste « archiver ».
        insert into public.app_annonce_champ_app
          (app_dossier_id, champ, valeur_app, origine, ecrit_le, ecrit_par)
        select target_dossier_id, x.champ, x.valeur, 'geste_statut', now(),
               coalesce(auth.uid()::text, 'app')
          from (values ('statut'::text,     v_statut_cible),
                       ('diffusable'::text, v_diff_cible)) as x(champ, valeur)
         where x.valeur is not null
        on conflict (app_dossier_id, champ) do update
           set valeur_app = excluded.valeur_app,
               origine    = excluded.origine,
               ecrit_le   = excluded.ecrit_le,
               ecrit_par  = excluded.ecrit_par;
      end if;
    end if;
  end;
  -- @3a-fin
$bloc$;

  v_def := replace(v_def, c_ancre, v_bloc || c_ancre);
  EXECUTE v_def;

  v_apres        := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_emp_apres    := md5(v_apres);
  m_taille_apres := length(v_apres);
  m_bloc_present := CASE WHEN position(c_deb in v_apres) > 0 AND position(c_fin in v_apres) > 0 THEN 1 ELSE 0 END;
  m_ancre_apres  := (length(v_apres) - length(replace(v_apres, c_ancre, ''))) / length(c_ancre);

  i := position(c_deb in v_apres);
  j := position(c_fin in v_apres);
  v_nu          := substr(v_apres, 1, i - 1) || substr(v_apres, j + length(c_fin) + 1);
  m_emp_nue     := md5(v_nu);
  m_bloc_octets := length(v_apres) - length(v_nu);

  -- ═══ 3. ESSAI A -- MISE SOUS MANDAT sur 62774, interrupteur ALLUME ═══
  BEGIN
    SELECT statut_annonce, diffusable, archive, coalesce(offre_id::text, '(vide)')
      INTO a_st_av, a_di_av, a_ar_av, a_of_av
      FROM public.app_dossier_current WHERE app_dossier_id = c_bienA;
    SELECT count(*) INTO a_ca_av FROM public.app_annonce_champ_app WHERE app_dossier_id = c_bienA;

    PERFORM set_config('request.jwt.claims', c_moi, true);
    a_ret := public.app_change_annonce_status_optimistic(c_bienA, 'active', '{}'::jsonb, 7);

    SELECT statut_annonce, diffusable, archive,
           CASE WHEN coalesce(offre_id::text, '(vide)') = a_of_av THEN 1 ELSE 0 END
      INTO a_st_ap, a_di_ap, a_ar_ap, a_of_ap
      FROM public.app_dossier_current WHERE app_dossier_id = c_bienA;
    SELECT count(*) INTO a_ca_ap FROM public.app_annonce_champ_app WHERE app_dossier_id = c_bienA;
    SELECT payload_json INTO a_charge
      FROM public.app_console_job WHERE id = (a_ret->>'job_id')::uuid;

    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN RAISE; END IF;
  END;

  -- ═══ 4. ESSAI B -- MANDAT CLOS sur 62963, interrupteur ALLUME ═══
  BEGIN
    SELECT statut_annonce, diffusable INTO b_st_av, b_di_av
      FROM public.app_dossier_current WHERE app_dossier_id = c_bienB;
    SELECT count(*) INTO b_ca_av FROM public.app_annonce_champ_app WHERE app_dossier_id = c_bienB;

    PERFORM set_config('request.jwt.claims', c_moi, true);
    b_ret := public.app_change_annonce_status_optimistic(c_bienB, 'closed', '{}'::jsonb, 7);

    SELECT statut_annonce, diffusable INTO b_st_ap, b_di_ap
      FROM public.app_dossier_current WHERE app_dossier_id = c_bienB;
    SELECT count(*) INTO b_ca_ap FROM public.app_annonce_champ_app WHERE app_dossier_id = c_bienB;
    SELECT payload_json INTO b_charge
      FROM public.app_console_job WHERE id = (b_ret->>'job_id')::uuid;

    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN RAISE; END IF;
  END;

  -- ═══ 5. ESSAI C -- LE TEMOIN : interrupteur ETEINT, rien ne doit changer ═══
  BEGIN
    SELECT count(*) INTO c_jobs_av FROM public.app_console_job
     WHERE app_dossier_id = c_bienA AND job_type = 'change_hektor_annonce_status';

    UPDATE public.app_setting SET value = 'off', updated_at = now()
     WHERE key = 'etat_annonce_ecrit_chez_nous';

    PERFORM set_config('request.jwt.claims', c_moi, true);
    c_ret := public.app_change_annonce_status_optimistic(c_bienA, 'active', '{}'::jsonb, 7);

    SELECT statut_annonce, diffusable INTO c_st_ap, c_di_ap
      FROM public.app_dossier_current WHERE app_dossier_id = c_bienA;
    SELECT count(*) INTO c_ca_ap FROM public.app_annonce_champ_app WHERE app_dossier_id = c_bienA;
    SELECT count(*) INTO c_jobs_ap FROM public.app_console_job
     WHERE app_dossier_id = c_bienA AND job_type = 'change_hektor_annonce_status';

    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN others THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN RAISE; END IF;
  END;

  -- ═══ 6. LE VRAI INVERSE ═══
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  i := position(c_deb in v_def);
  j := position(c_fin in v_def);
  v_nu := substr(v_def, 1, i - 1) || substr(v_def, j + length(c_fin) + 1);
  IF md5(v_nu) <> c_emp THEN
    RAISE EXCEPTION 'INVERSE IMPOSSIBLE -- en retirant le bloc on obtient % au lieu de %', md5(v_nu), c_emp;
  END IF;
  EXECUTE v_nu;

  v_apres      := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  m_emp_final  := md5(v_apres);
  m_bloc_final := (length(v_apres) - length(replace(v_apres, '@3a', ''))) / 3;

  -- ═══ 7. LE RAPPORT, PUIS L'ANNULATION TOTALE ═══
  rapport :=
    'ESSAI ANNULE -- rien n''a ete ecrit. Mesures :'
    || chr(10) || '--- 1. AVANT -------------------------------------------------------'
    || chr(10) || 'empreinte_avant      = ' || m_emp_avant    || '   (attendu 302852e8dc23c44d6e0442b81e6cb577)'
    || chr(10) || 'taille_avant         = ' || m_taille_avant  || '   (attendu 8446)'
    || chr(10) || 'ancre_avant          = ' || m_ancre_avant   || '   (attendu 1)'
    || chr(10) || '--- 2. APRES LE PATCH ---------------------------------------------'
    || chr(10) || 'bloc_present         = ' || m_bloc_present  || '   (attendu 1)'
    || chr(10) || 'ancre_apres          = ' || m_ancre_apres   || '   (attendu 1 -- pas doublee)'
    || chr(10) || 'bloc_octets          = ' || m_bloc_octets
    || chr(10) || 'taille_apres         = ' || m_taille_apres  || '   (attendu 8446 + bloc_octets)'
    || chr(10) || 'empreinte_NUE        = ' || m_emp_nue       || '   (attendu = empreinte_avant : RIEN D''AUTRE N''A CHANGE)'
    || chr(10) || '--- 3. ESSAI A : 62774, mise sous mandat, interrupteur ALLUME ------'
    || chr(10) || 'statut      ' || coalesce(a_st_av,'(null)') || ' -> ' || coalesce(a_st_ap,'(null)') || '   (attendu Sous offre -> Actif)'
    || chr(10) || 'diffusable  ' || coalesce(a_di_av,'(null)') || ' -> ' || coalesce(a_di_ap,'(null)') || '   (attendu 0 -> 1)'
    || chr(10) || 'archive     ' || coalesce(a_ar_av,'(null)') || ' -> ' || coalesce(a_ar_ap,'(null)') || '   (attendu INCHANGE)'
    || chr(10) || 'offre_id_inchange    = ' || a_of_ap || '   (attendu 1 = oui, on n''y touche pas)'
    || chr(10) || 'carnet      ' || a_ca_av || ' -> ' || a_ca_ap || ' lignes   (attendu +2 : statut et diffusable)'
    || chr(10) || 'charge.statut_avant     = ' || coalesce(a_charge->>'statut_avant','(absent)')     || '   (attendu Sous offre)'
    || chr(10) || 'charge.diffusable_avant = ' || coalesce(a_charge->>'diffusable_avant','(absent)') || '   (attendu 0)'
    || chr(10) || '--- 4. ESSAI B : 62963, Mandat clos, interrupteur ALLUME -----------'
    || chr(10) || 'statut      ' || coalesce(b_st_av,'(null)') || ' -> ' || coalesce(b_st_ap,'(null)') || '   (attendu Actif -> Mandat clos)'
    || chr(10) || 'diffusable  ' || coalesce(b_di_av,'(null)') || ' -> ' || coalesce(b_di_ap,'(null)') || '   (attendu 1 -> 0)'
    || chr(10) || 'carnet      ' || b_ca_av || ' -> ' || b_ca_ap || ' lignes   (attendu +2)'
    || chr(10) || 'charge.statut_avant     = ' || coalesce(b_charge->>'statut_avant','(absent)')     || '   (attendu Actif)'
    || chr(10) || 'charge.diffusable_avant = ' || coalesce(b_charge->>'diffusable_avant','(absent)') || '   (attendu 1)'
    || chr(10) || '--- 5. ESSAI C : LE TEMOIN, interrupteur ETEINT -------------------'
    || chr(10) || 'statut apres         = ' || coalesce(c_st_ap,'(null)') || '   (attendu Sous offre : INCHANGE)'
    || chr(10) || 'diffusable apres     = ' || coalesce(c_di_ap,'(null)') || '   (attendu 0 : INCHANGE)'
    || chr(10) || 'carnet apres         = ' || c_ca_ap || ' lignes   (attendu ' || a_ca_av || ' : INCHANGE)'
    || chr(10) || 'travaux Hektor  ' || c_jobs_av || ' -> ' || c_jobs_ap || '   (attendu +1 : le geste part quand meme)'
    || chr(10) || '--- 6. APRES L''INVERSE -------------------------------------------'
    || chr(10) || 'empreinte_finale     = ' || m_emp_final  || '   (attendu = empreinte_avant)'
    || chr(10) || 'marqueurs_3a_restants= ' || m_bloc_final || '   (attendu 0 : LE BLOC A DISPARU)'
    || chr(10) || '-------------------------------------------------------------------';

  RAISE EXCEPTION '%', rapport;
END $rep$;

ROLLBACK;
