-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — patch_partenaire_bien_sans_numero_2026-11-06.sql
-- ═══════════════════════════════════════════════════════════════════════════
-- Remet les quatre fonctions telles que mesurées le 06/11, retire les deux index par
-- notre numéro, la fonction de complétion et sa tâche horaire.
-- ⛔ Il REFUSE si un lien actif n'a toujours pas de numéro Hektor après une dernière
--    complétion : les anciennes fonctions ne le verraient plus (il deviendrait invisible).
--    Dans ce cas : retirer ou compléter ces liens d'abord, à la main.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
DECLARE r jsonb;
BEGIN
  IF to_regprocedure('public.app_partenaire_lien_completer_numeros()') IS NULL THEN
    RAISE EXCEPTION 'ARRÊT : le patch n''est pas posé (fonction de complétion absente), rien à défaire.';
  END IF;
  r := public.app_partenaire_lien_completer_numeros();
  IF (r->>'restent_sans_numero')::int > 0 THEN
    RAISE EXCEPTION 'ARRÊT : % lien(s) actif(s) sans numéro Hektor ; les anciennes fonctions ne les verraient plus. Rien n''est défait.', r->>'restent_sans_numero';
  END IF;
END
$garde$;

SELECT cron.unschedule('partenaire-lien-numeros');
DROP FUNCTION public.app_partenaire_lien_completer_numeros();

DROP FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint, bigint);
CREATE FUNCTION public.app_partenaire_syndic_du_bien_lire(p_hektor_annonce_id bigint)
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
   WHERE l.role = 'syndic' AND l.objet = 'bien' AND l.retire_le IS NULL AND l.hektor_annonce_id = p_hektor_annonce_id
   LIMIT 1;
  RETURN v;
END
$function$;
REVOKE ALL ON FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint) FROM public;
REVOKE ALL ON FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint) FROM anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint) TO authenticated, service_role;

DROP FUNCTION public.app_partenaire_du_bien_lire(text, bigint, bigint);
CREATE FUNCTION public.app_partenaire_du_bien_lire(p_role text, p_hektor_annonce_id bigint)
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
   WHERE l.role = p_role AND l.objet = 'bien' AND l.retire_le IS NULL AND l.hektor_annonce_id = p_hektor_annonce_id
   LIMIT 1;
  RETURN v;
END
$function$;
REVOKE ALL ON FUNCTION public.app_partenaire_du_bien_lire(text, bigint) FROM public;
REVOKE ALL ON FUNCTION public.app_partenaire_du_bien_lire(text, bigint) FROM anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_du_bien_lire(text, bigint) TO authenticated, service_role;

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
BEGIN
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif : le syndic ne peut pas être changé.' USING ERRCODE = '42501';
  END IF;
  IF p_hektor_annonce_id IS NULL THEN
    RAISE EXCEPTION '%', 'Le bien n''a pas encore de numéro d''annonce : le syndic se choisira quand il l''aura.';
  END IF;
  IF NOT public.app_console_can_access_dossier(p_app_dossier_id, p_hektor_annonce_id::text) THEN
    RAISE EXCEPTION '%', 'Ce bien n''est pas dans ton périmètre : tu ne peux pas en changer le syndic.' USING ERRCODE = '42501';
  END IF;

  -- Le syndic actif du bien, verrouillé le temps du geste (deux clics en même temps ne font pas deux syndics).
  SELECT * INTO v_actuel FROM public.app_partenaire_lien
   WHERE role = 'syndic' AND objet = 'bien' AND retire_le IS NULL AND hektor_annonce_id = p_hektor_annonce_id
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
  VALUES (v_partenaire, 'syndic', 'bien', p_app_dossier_id, p_hektor_annonce_id, 'app', auth.uid())
  RETURNING id INTO v_id;
  RETURN jsonb_build_object('action', CASE WHEN v_actuel.id IS NULL THEN 'pose' ELSE 'change' END,
                            'id', v_id, 'retire_id', v_actuel.id);
END
$function$;

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
BEGIN
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif : le partenaire du bien ne peut pas être changé.' USING ERRCODE = '42501';
  END IF;
  IF v_libelle IS NULL THEN
    RAISE EXCEPTION '%', 'Rôle inconnu pour un bien (syndic ou diagnostiqueur).';
  END IF;
  IF p_hektor_annonce_id IS NULL THEN
    RAISE EXCEPTION '%', 'Le bien n''a pas encore de numéro d''annonce : le partenaire se choisira quand il l''aura.';
  END IF;
  IF NOT public.app_console_can_access_dossier(p_app_dossier_id, p_hektor_annonce_id::text) THEN
    RAISE EXCEPTION '%', 'Ce bien n''est pas dans ton périmètre : tu ne peux pas en changer le ' || v_libelle || '.' USING ERRCODE = '42501';
  END IF;

  SELECT * INTO v_actuel FROM public.app_partenaire_lien
   WHERE role = p_role AND objet = 'bien' AND retire_le IS NULL AND hektor_annonce_id = p_hektor_annonce_id
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
  VALUES (v_partenaire, p_role, 'bien', p_app_dossier_id, p_hektor_annonce_id, 'app', auth.uid())
  RETURNING id INTO v_id;
  RETURN jsonb_build_object('action', CASE WHEN v_actuel.id IS NULL THEN 'pose' ELSE 'change' END, 'id', v_id, 'retire_id', v_actuel.id);
END
$function$;

DROP INDEX public.app_partenaire_lien_un_syndic_dossier_uidx;
DROP INDEX public.app_partenaire_lien_un_diag_dossier_uidx;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- APRÈS : les empreintes doivent redevenir celles du 06/11
-- select md5(pg_get_functiondef('public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)'::regprocedure)) = '713b6c0fb19cdea37c9d9f280464c1e6';
-- (les fonctions recréées par DROP/CREATE peuvent différer d'un octet de mise en forme : comparer le texte si besoin)
