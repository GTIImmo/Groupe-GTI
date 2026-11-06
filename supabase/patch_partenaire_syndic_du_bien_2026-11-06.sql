-- CHANTIER PARTENAIRES · LOT 4, PIÈCE 4.2a (06/11/2026) — CHOISIR LE SYNDIC D'UN BIEN, CHEZ NOUS SEULEMENT.
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §27.3 (audit) et §27.4. « Oui, vas-y 4.2 » (Frédéric, 06/11).
-- Décision du 04/11 (D2) : les liens des partenaires vivent CHEZ NOUS ; rien n'est écrit chez Hektor.
--
-- CE QUE CE PATCH FAIT, dans UNE transaction (tout ou rien) — UNIQUEMENT DE L'AJOUT :
--   0. vérifie que la table est là, que rien ne porte déjà ces noms, et qu'AUCUN bien n'a deux syndics actifs — sinon ARRÊT ;
--   1. un index « UN SEUL syndic actif par bien » (0 doublon au 06/11 : 80 liens, 80 biens) ;
--   2. app_partenaire_syndic_du_bien(p_app_dossier_id, p_hektor_annonce_id, p_partenaire, p_retirer) : poser, CHANGER ou
--      retirer le syndic d'un bien, en une opération. Gardes : compte actif ; DROIT SUR LE BIEN
--      (`app_console_can_access_dossier` : admin / manager partout, négociateur ses biens) ; le partenaire EST un syndic au
--      registre (`app_partenaire_metier`) ; l'ancien lien est RETIRÉ (daté, avec l'auteur), jamais effacé ;
--   3. app_partenaire_syndic_du_bien_lire(p_hektor_annonce_id) : le syndic actif du bien, son nom, d'où il vient, qui l'a
--      posé (lecture, compte actif).
-- `app_partenaire_lien_ecrire` (04/11) n'est PAS touchée. Rien chez Hektor.
-- Retour arrière : ..._INVERSE.sql. Contrôles : ..._REPETITION.sql.

BEGIN;

DO $verif$
BEGIN
  IF to_regclass('public.app_partenaire_lien') IS NULL OR to_regclass('public.app_partenaire_metier') IS NULL THEN
    RAISE EXCEPTION 'ARRÊT : le registre des partenaires n''est pas là.';
  END IF;
  IF to_regclass('public.app_partenaire_lien_un_syndic_uidx') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRÊT : l''index app_partenaire_lien_un_syndic_uidx existe déjà.';
  END IF;
  IF to_regprocedure('public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)') IS NOT NULL
     OR to_regprocedure('public.app_partenaire_syndic_du_bien_lire(bigint)') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRÊT : une fonction app_partenaire_syndic_du_bien existe déjà.';
  END IF;
  IF EXISTS (SELECT 1 FROM public.app_partenaire_lien
              WHERE role = 'syndic' AND objet = 'bien' AND retire_le IS NULL AND hektor_annonce_id IS NOT NULL
              GROUP BY hektor_annonce_id HAVING count(*) > 1) THEN
    RAISE EXCEPTION 'ARRÊT : un bien a déjà deux syndics actifs — à regarder avant de poser l''index.';
  END IF;
END
$verif$;

-- 1. Un seul syndic actif par bien (le bien = son numéro d'annonce, la clé que lit aussi la nuit).
CREATE UNIQUE INDEX app_partenaire_lien_un_syndic_uidx ON public.app_partenaire_lien (hektor_annonce_id)
  WHERE role = 'syndic' AND objet = 'bien' AND retire_le IS NULL AND hektor_annonce_id IS NOT NULL;

-- 2. Poser / changer / retirer.
CREATE FUNCTION public.app_partenaire_syndic_du_bien(p_app_dossier_id bigint, p_hektor_annonce_id bigint, p_partenaire text, p_retirer boolean DEFAULT false)
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

-- 3. Lire le syndic d'un bien (nom, origine, auteur).
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

REVOKE ALL ON FUNCTION public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean) TO authenticated;
GRANT EXECUTE ON FUNCTION public.app_partenaire_syndic_du_bien_lire(bigint) TO authenticated;

COMMIT;
