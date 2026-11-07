-- ═══════════════════════════════════════════════════════════════════════════
-- ANNUAIRE DES PARTENAIRES · PLAN ÉTAPE 1 — RELIER UN PARTENAIRE À UN BIEN
-- QUI N'A PAS ENCORE DE NUMÉRO HEKTOR                                06/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.5
--
-- LE DÉFAUT : une annonce créée dans l'app naît dans app_dossier_current avec
--   NOTRE numéro (app_dossier_id, plage 10000000+) et hektor_annonce_id = NULL ;
--   Hektor ne rend le sien que ~90 s plus tard. Les deux gestes refusent alors :
--   « Le bien n'a pas encore de numéro d'annonce ». Le choix du syndic et du
--   diagnostiqueur à la création (étape 2 du plan) serait donc impossible.
--
-- CE QUE FAIT CE PATCH — rien n'est encore appelé sans numéro Hektor (le front ne le
--   fait pas avant l'étape 2) ; les appels d'aujourd'hui gardent EXACTEMENT leur effet :
--   1. deux index uniques NEUFS par notre numéro : un syndic actif et un diagnostiqueur
--      actif par bien, même sans numéro Hektor (ceux par numéro Hektor restent) ;
--   2. app_partenaire_du_bien et app_partenaire_syndic_du_bien (signatures inchangées) :
--      sans numéro Hektor, ils acceptent notre numéro, À CONDITION que le bien soit dans
--      app_dossier_current ; ils y reprennent le numéro Hektor s'il est déjà arrivé ;
--      le partenaire actuel se cherche par l'un OU l'autre numéro ;
--   3. les deux lectures (…_lire) prennent un 3e paramètre FACULTATIF p_app_dossier_id
--      (les appels actuels à 1 ou 2 paramètres marchent tels quels) ;
--   4. app_partenaire_lien_completer_numeros() : pose le numéro Hektor sur les liens qui
--      ne l'ont pas, dès que la fiche le porte ; l'app gagne (un lien « hektor » actif
--      sur le même bien et le même rôle est retiré, daté) ; service_role seulement ;
--   5. pg_cron 'partenaire-lien-numeros' à :50 chaque heure (avant la reprise de nuit,
--      qui ne voit que les liens munis d'un numéro Hektor).
--
-- ⛔ GARDES : chaque fonction n'est remplacée que si son empreinte est celle mesurée le
--    06/11 ; sinon ARRÊT, rien n'est écrit (tout est dans une seule transaction).
-- RETOUR ARRIÈRE : supabase/patch_partenaire_bien_sans_numero_2026-11-06_INVERSE.sql
-- CONTRÔLE       : supabase/patch_partenaire_bien_sans_numero_2026-11-06_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 0. LES GARDES : on ne remplace que ce qu'on a lu
DO $garde$
DECLARE
  attendu record;
BEGIN
  FOR attendu IN SELECT * FROM (VALUES
      ('public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)',      '713b6c0fb19cdea37c9d9f280464c1e6'),
      ('public.app_partenaire_du_bien_lire(text,bigint)',                     '7551bf569db3c15fb4c8f9c3d52ed232'),
      ('public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)',    'cacb639dfb27eea8b78d1f816fd4534a'),
      ('public.app_partenaire_syndic_du_bien_lire(bigint)',                   '6e4c905dbcd5a13c3238c914ccecea73')
    ) AS t(signature, empreinte)
  LOOP
    IF to_regprocedure(attendu.signature) IS NULL THEN
      RAISE EXCEPTION 'ARRÊT : % introuvable, rien n''est écrit.', attendu.signature;
    END IF;
    IF md5(pg_get_functiondef(to_regprocedure(attendu.signature))) <> attendu.empreinte THEN
      RAISE EXCEPTION 'ARRÊT : % a changé depuis la mesure du 06/11, rien n''est écrit.', attendu.signature;
    END IF;
  END LOOP;
  IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'partenaire-lien-numeros') THEN
    RAISE EXCEPTION 'ARRÊT : la tâche partenaire-lien-numeros existe déjà, rien n''est écrit.';
  END IF;
END
$garde$;

-- 1. UN PARTENAIRE ACTIF PAR BIEN ET PAR RÔLE, AUSSI PAR NOTRE NUMÉRO
CREATE UNIQUE INDEX app_partenaire_lien_un_syndic_dossier_uidx ON public.app_partenaire_lien (app_dossier_id)
  WHERE role = 'syndic' AND objet = 'bien' AND retire_le IS NULL AND app_dossier_id IS NOT NULL;
CREATE UNIQUE INDEX app_partenaire_lien_un_diag_dossier_uidx ON public.app_partenaire_lien (app_dossier_id)
  WHERE role = 'diagnostiqueur' AND objet = 'bien' AND retire_le IS NULL AND app_dossier_id IS NOT NULL;

-- 2a. LE GESTE GÉNÉRIQUE (syndic ou diagnostiqueur)
CREATE OR REPLACE FUNCTION public.app_partenaire_du_bien(p_role text, p_app_dossier_id bigint, p_hektor_annonce_id bigint, p_partenaire text, p_retirer boolean DEFAULT false)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_partenaire text := nullif(btrim(coalesce(p_partenaire, '')), '');
  v_actuel public.app_partenaire_lien%ROWTYPE;
  v_id bigint;
  v_libelle text := CASE p_role WHEN 'syndic' THEN 'syndic' WHEN 'diagnostiqueur' THEN 'diagnostiqueur' END;
  v_annonce bigint := p_hektor_annonce_id;
BEGIN
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif : le partenaire du bien ne peut pas être changé.' USING ERRCODE = '42501';
  END IF;
  IF v_libelle IS NULL THEN
    RAISE EXCEPTION '%', 'Rôle inconnu pour un bien (syndic ou diagnostiqueur).';
  END IF;
  -- Étape 1 du plan (06/11) : une annonce née dans l'app n'a pas encore de numéro Hektor ;
  -- notre numéro suffit, si le bien est bien chez nous. Le numéro Hektor est repris s'il est arrivé,
  -- sinon app_partenaire_lien_completer_numeros() le posera.
  IF v_annonce IS NULL THEN
    IF p_app_dossier_id IS NULL THEN
      RAISE EXCEPTION '%', 'Bien inconnu : ni numéro de dossier ni numéro d''annonce.';
    END IF;
    SELECT d.hektor_annonce_id INTO v_annonce FROM public.app_dossier_current d WHERE d.app_dossier_id = p_app_dossier_id;
    IF NOT FOUND THEN
      RAISE EXCEPTION '%', 'Ce bien est introuvable : le ' || v_libelle || ' se choisira quand la fiche sera là.';
    END IF;
  END IF;
  IF NOT public.app_console_can_access_dossier(p_app_dossier_id, v_annonce::text) THEN
    RAISE EXCEPTION '%', 'Ce bien n''est pas dans ton périmètre : tu ne peux pas en changer le ' || v_libelle || '.' USING ERRCODE = '42501';
  END IF;

  SELECT * INTO v_actuel FROM public.app_partenaire_lien
   WHERE role = p_role AND objet = 'bien' AND retire_le IS NULL
     AND ((v_annonce IS NOT NULL AND hektor_annonce_id = v_annonce)
       OR (p_app_dossier_id IS NOT NULL AND app_dossier_id = p_app_dossier_id))
   ORDER BY id DESC
   LIMIT 1
   FOR UPDATE;

  IF coalesce(p_retirer, false) THEN
    IF v_actuel.id IS NULL THEN RAISE EXCEPTION '%', 'Ce bien n''a pas de ' || v_libelle || ' à retirer.'; END IF;
    UPDATE public.app_partenaire_lien SET retire_le = now(), retire_par = auth.uid() WHERE id = v_actuel.id;
    RETURN jsonb_build_object('action', 'retire', 'retire_id', v_actuel.id);
  END IF;

  IF v_partenaire IS NULL THEN RAISE EXCEPTION '%', 'Le ' || v_libelle || ' est obligatoire.'; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.app_partenaire_metier
                  WHERE contact_id = v_partenaire AND metier = p_role AND retire_le IS NULL) THEN
    RAISE EXCEPTION '%', 'Ce contact n''est pas un ' || v_libelle || ' du catalogue des partenaires.';
  END IF;
  IF v_actuel.id IS NOT NULL AND v_actuel.partenaire_id = v_partenaire THEN
    RETURN jsonb_build_object('action', 'inchange', 'id', v_actuel.id);
  END IF;
  IF v_actuel.id IS NOT NULL THEN
    UPDATE public.app_partenaire_lien SET retire_le = now(), retire_par = auth.uid() WHERE id = v_actuel.id;
  END IF;
  INSERT INTO public.app_partenaire_lien (partenaire_id, role, objet, app_dossier_id, hektor_annonce_id, origine, pose_par)
  VALUES (v_partenaire, p_role, 'bien', p_app_dossier_id, v_annonce, 'app', auth.uid())
  RETURNING id INTO v_id;
  RETURN jsonb_build_object('action', CASE WHEN v_actuel.id IS NULL THEN 'pose' ELSE 'change' END, 'id', v_id, 'retire_id', v_actuel.id);
END
$function$;

-- 2b. LE GESTE DU SYNDIC (pièce 4.2) — même règle
CREATE OR REPLACE FUNCTION public.app_partenaire_syndic_du_bien(p_app_dossier_id bigint, p_hektor_annonce_id bigint, p_partenaire text, p_retirer boolean DEFAULT false)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_partenaire text := nullif(btrim(coalesce(p_partenaire, '')), '');
  v_actuel public.app_partenaire_lien%ROWTYPE;
  v_id bigint;
  v_annonce bigint := p_hektor_annonce_id;
BEGIN
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif : le syndic ne peut pas être changé.' USING ERRCODE = '42501';
  END IF;
  -- Étape 1 du plan (06/11) : voir app_partenaire_du_bien.
  IF v_annonce IS NULL THEN
    IF p_app_dossier_id IS NULL THEN
      RAISE EXCEPTION '%', 'Bien inconnu : ni numéro de dossier ni numéro d''annonce.';
    END IF;
    SELECT d.hektor_annonce_id INTO v_annonce FROM public.app_dossier_current d WHERE d.app_dossier_id = p_app_dossier_id;
    IF NOT FOUND THEN
      RAISE EXCEPTION '%', 'Ce bien est introuvable : le syndic se choisira quand la fiche sera là.';
    END IF;
  END IF;
  IF NOT public.app_console_can_access_dossier(p_app_dossier_id, v_annonce::text) THEN
    RAISE EXCEPTION '%', 'Ce bien n''est pas dans ton périmètre : tu ne peux pas en changer le syndic.' USING ERRCODE = '42501';
  END IF;

  -- Le syndic actif du bien, verrouillé le temps du geste (deux clics en même temps ne font pas deux syndics).
  SELECT * INTO v_actuel FROM public.app_partenaire_lien
   WHERE role = 'syndic' AND objet = 'bien' AND retire_le IS NULL
     AND ((v_annonce IS NOT NULL AND hektor_annonce_id = v_annonce)
       OR (p_app_dossier_id IS NOT NULL AND app_dossier_id = p_app_dossier_id))
   ORDER BY id DESC
   LIMIT 1
   FOR UPDATE;

  IF coalesce(p_retirer, false) THEN
    IF v_actuel.id IS NULL THEN RAISE EXCEPTION '%', 'Ce bien n''a pas de syndic à retirer.'; END IF;
    UPDATE public.app_partenaire_lien SET retire_le = now(), retire_par = auth.uid() WHERE id = v_actuel.id;
    RETURN jsonb_build_object('action', 'retire', 'retire_id', v_actuel.id);
  END IF;

  IF v_partenaire IS NULL THEN RAISE EXCEPTION '%', 'Le syndic est obligatoire.'; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.app_partenaire_metier
                  WHERE contact_id = v_partenaire AND metier = 'syndic' AND retire_le IS NULL) THEN
    RAISE EXCEPTION '%', 'Ce contact n''est pas un syndic du catalogue des partenaires.';
  END IF;
  IF v_actuel.id IS NOT NULL AND v_actuel.partenaire_id = v_partenaire THEN
    RETURN jsonb_build_object('action', 'inchange', 'id', v_actuel.id);
  END IF;
  IF v_actuel.id IS NOT NULL THEN
    UPDATE public.app_partenaire_lien SET retire_le = now(), retire_par = auth.uid() WHERE id = v_actuel.id;
  END IF;
  INSERT INTO public.app_partenaire_lien (partenaire_id, role, objet, app_dossier_id, hektor_annonce_id, origine, pose_par)
  VALUES (v_partenaire, 'syndic', 'bien', p_app_dossier_id, v_annonce, 'app', auth.uid())
  RETURNING id INTO v_id;
  RETURN jsonb_build_object('action', CASE WHEN v_actuel.id IS NULL THEN 'pose' ELSE 'change' END,
                            'id', v_id, 'retire_id', v_actuel.id);
END
$function$;

-- 3. LES DEUX LECTURES : un 3e paramètre FACULTATIF, notre numéro
--    (ancienne signature retirée pour éviter deux fonctions homonymes côté API)
DROP FUNCTION public.app_partenaire_du_bien_lire(text, bigint);
CREATE FUNCTION public.app_partenaire_du_bien_lire(p_role text, p_hektor_annonce_id bigint, p_app_dossier_id bigint DEFAULT NULL)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE v jsonb;
BEGIN
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif.' USING ERRCODE = '42501';
  END IF;
  SELECT jsonb_build_object(
           'id', l.id, 'partenaire_id', l.partenaire_id, 'origine', l.origine, 'pose_le', l.pose_le,
           'pose_par', coalesce(nullif(btrim(coalesce(u.display_name, '')), ''), u.email),
           'nom', coalesce(nullif(btrim(coalesce(c.display_name, '')), ''), nullif(btrim(concat_ws(' ', c.prenom, c.nom)), ''), 'Contact ' || l.partenaire_id),
           'ville', c.ville, 'telephone', c.phone_primary, 'email', c.email)
    INTO v
    FROM public.app_partenaire_lien l
    LEFT JOIN public.app_contact_current c ON c.hektor_contact_id::text = l.partenaire_id
    LEFT JOIN public.app_user_profile u ON u.id = l.pose_par
   WHERE l.role = p_role AND l.objet = 'bien' AND l.retire_le IS NULL
     AND ((p_hektor_annonce_id IS NOT NULL AND l.hektor_annonce_id = p_hektor_annonce_id)
       OR (p_app_dossier_id IS NOT NULL AND l.app_dossier_id = p_app_dossier_id))
   ORDER BY l.id DESC
   LIMIT 1;
  RETURN v;
END
$function$;
REVOKE ALL ON FUNCTION public.app_partenaire_du_bien_lire(text, bigint, bigint) FROM public;
REVOKE ALL ON FUNCTION public.app_partenaire_du_bien_lire(text, bigint, bigint) FROM anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_du_bien_lire(text, bigint, bigint) TO authenticated, service_role;

DROP FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint);
CREATE FUNCTION public.app_partenaire_syndic_du_bien_lire(p_hektor_annonce_id bigint, p_app_dossier_id bigint DEFAULT NULL)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT public.app_partenaire_du_bien_lire('syndic', p_hektor_annonce_id, p_app_dossier_id)
$function$;
REVOKE ALL ON FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint, bigint) FROM public;
REVOKE ALL ON FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint, bigint) FROM anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint, bigint) TO authenticated, service_role;

-- 4. LE NUMÉRO HEKTOR, POSÉ DÈS QUE LA FICHE LE PORTE
CREATE FUNCTION public.app_partenaire_lien_completer_numeros()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_retires int := 0;
  v_completes int := 0;
  v_restes int := 0;
BEGIN
  -- l'app gagne (règle de la reprise de nuit) : un lien « hektor » actif sur le même bien et
  -- le même rôle est retiré, daté, avant que le lien de l'app reçoive le numéro.
  UPDATE public.app_partenaire_lien h SET retire_le = now()
    FROM public.app_partenaire_lien l
    JOIN public.app_dossier_current d ON d.app_dossier_id = l.app_dossier_id
   WHERE l.objet = 'bien' AND l.retire_le IS NULL AND l.hektor_annonce_id IS NULL AND d.hektor_annonce_id IS NOT NULL
     AND h.objet = 'bien' AND h.retire_le IS NULL AND h.origine = 'hektor'
     AND h.role = l.role AND h.hektor_annonce_id = d.hektor_annonce_id;
  GET DIAGNOSTICS v_retires = ROW_COUNT;

  UPDATE public.app_partenaire_lien l SET hektor_annonce_id = d.hektor_annonce_id
    FROM public.app_dossier_current d
   WHERE d.app_dossier_id = l.app_dossier_id
     AND l.objet = 'bien' AND l.retire_le IS NULL AND l.hektor_annonce_id IS NULL AND d.hektor_annonce_id IS NOT NULL
     AND NOT EXISTS (SELECT 1 FROM public.app_partenaire_lien o
                      WHERE o.objet = 'bien' AND o.retire_le IS NULL AND o.role = l.role
                        AND o.hektor_annonce_id = d.hektor_annonce_id);
  GET DIAGNOSTICS v_completes = ROW_COUNT;

  SELECT count(*) INTO v_restes FROM public.app_partenaire_lien
   WHERE objet = 'bien' AND retire_le IS NULL AND hektor_annonce_id IS NULL;

  RETURN jsonb_build_object('completes', v_completes, 'liens_hektor_retires', v_retires, 'restent_sans_numero', v_restes);
END
$function$;
REVOKE ALL ON FUNCTION public.app_partenaire_lien_completer_numeros() FROM public;
REVOKE ALL ON FUNCTION public.app_partenaire_lien_completer_numeros() FROM anon;
REVOKE ALL ON FUNCTION public.app_partenaire_lien_completer_numeros() FROM authenticated;
GRANT EXECUTE ON FUNCTION public.app_partenaire_lien_completer_numeros() TO service_role;

-- 5. CHAQUE HEURE À :50
SELECT cron.schedule('partenaire-lien-numeros', '50 * * * *', 'select public.app_partenaire_lien_completer_numeros()');

COMMIT;

NOTIFY pgrst, 'reload schema';
