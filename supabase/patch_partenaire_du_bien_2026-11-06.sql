-- CHANTIER PARTENAIRES · LOT 5 (06/11/2026) — CHOISIR LE DIAGNOSTIQUEUR D'UN BIEN (geste générique « partenaire d'un bien »).
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.2. Plan accéléré (§28) : « Vas-y » (Frédéric, 06/11).
-- Même geste que celui du syndic (pièce 4.2, `app_partenaire_syndic_du_bien`, NON touché), pour un rôle donné.
--
-- CE QUE CE PATCH FAIT, dans UNE transaction — UNIQUEMENT DE L'AJOUT :
--   0. vérifie que rien ne porte déjà ces noms et qu'AUCUN bien n'a deux diagnostiqueurs actifs — sinon ARRÊT ;
--   1. un index « UN SEUL diagnostiqueur actif par bien » (0 doublon au 06/11 : 4 liens, 4 biens) ;
--   2. app_partenaire_du_bien(p_role, p_app_dossier_id, p_hektor_annonce_id, p_partenaire, p_retirer) : poser, CHANGER ou
--      retirer le partenaire d'un bien pour le rôle 'syndic' ou 'diagnostiqueur'. Gardes : compte actif ; DROIT SUR LE BIEN
--      (`app_console_can_access_dossier`) ; le partenaire a CE métier au registre ; l'ancien lien retiré daté avec l'auteur ;
--   3. app_partenaire_du_bien_lire(p_role, p_hektor_annonce_id) : le partenaire actif du bien pour ce rôle.
-- Rien chez Hektor. Retour arrière : ..._INVERSE.sql. Contrôles : ..._REPETITION.sql.

BEGIN;

DO $verif$
BEGIN
  IF to_regclass('public.app_partenaire_lien_un_diag_uidx') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRÊT : l''index app_partenaire_lien_un_diag_uidx existe déjà.';
  END IF;
  IF to_regprocedure('public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)') IS NOT NULL
     OR to_regprocedure('public.app_partenaire_du_bien_lire(text,bigint)') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRÊT : une fonction app_partenaire_du_bien existe déjà.';
  END IF;
  IF EXISTS (SELECT 1 FROM public.app_partenaire_lien
              WHERE role = 'diagnostiqueur' AND objet = 'bien' AND retire_le IS NULL AND hektor_annonce_id IS NOT NULL
              GROUP BY hektor_annonce_id HAVING count(*) > 1) THEN
    RAISE EXCEPTION 'ARRÊT : un bien a déjà deux diagnostiqueurs actifs — à regarder avant de poser l''index.';
  END IF;
END
$verif$;

CREATE UNIQUE INDEX app_partenaire_lien_un_diag_uidx ON public.app_partenaire_lien (hektor_annonce_id)
  WHERE role = 'diagnostiqueur' AND objet = 'bien' AND retire_le IS NULL AND hektor_annonce_id IS NOT NULL;

CREATE FUNCTION public.app_partenaire_du_bien(p_role text, p_app_dossier_id bigint, p_hektor_annonce_id bigint, p_partenaire text, p_retirer boolean DEFAULT false)
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

REVOKE ALL ON FUNCTION public.app_partenaire_du_bien(text,bigint,bigint,text,boolean) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.app_partenaire_du_bien_lire(text,bigint) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_du_bien(text,bigint,bigint,text,boolean) TO authenticated;
GRANT EXECUTE ON FUNCTION public.app_partenaire_du_bien_lire(text,bigint) TO authenticated;

COMMIT;
