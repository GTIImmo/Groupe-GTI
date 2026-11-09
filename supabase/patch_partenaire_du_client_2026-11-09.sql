-- ═══════════════════════════════════════════════════════════════════════════
-- PARTENAIRES · LOT 7 · RELIER UN APPORTEUR (OU UN COURTIER) À UN CLIENT   09/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.17. Décision Q1 « A » (04/11) : un partenaire se relie à
-- un CLIENT dès le premier jour. La table app_partenaire_lien accepte déjà ce lien (objet 'client', client_contact_id,
-- rôles apporteur / courtier) ; il manquait la fonction pour l'écrire.
-- Ajoute (rien n'est remplacé) : la fonction public.app_partenaire_du_client(text,text,text,boolean) et l'index unique app_partenaire_lien_un_client_uidx (un même lien actif une seule fois).
-- Écrit CHEZ NOUS seulement. Aucun lien de ce genre n'existe au 09/11 (vérifié par la garde).
-- A APPLIQUER avec l'accord de Frédéric, APRES la répétition. RETOUR ARRIERE : patch_partenaire_du_client_2026-11-09_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '3s';

DO $garde$
BEGIN
  IF to_regprocedure('public.app_partenaire_du_client(text,text,text,boolean)') IS NOT NULL THEN RAISE EXCEPTION 'ARRET : la fonction existe deja. Rien n''est ecrit.'; END IF;
  IF to_regclass('public.app_partenaire_lien_un_client_uidx') IS NOT NULL THEN RAISE EXCEPTION 'ARRET : l''index existe deja. Rien n''est ecrit.'; END IF;
  IF EXISTS (SELECT 1 FROM public.app_partenaire_lien WHERE objet = 'client' AND retire_le IS NULL
              GROUP BY role, client_contact_id, partenaire_id HAVING count(*) > 1) THEN
    RAISE EXCEPTION 'ARRET : un lien client actif existe deja en double. Rien n''est ecrit.';
  END IF;
END
$garde$;

CREATE UNIQUE INDEX app_partenaire_lien_un_client_uidx ON public.app_partenaire_lien (role, client_contact_id, partenaire_id)
  WHERE objet = 'client' AND retire_le IS NULL;

CREATE FUNCTION public.app_partenaire_du_client(p_role text, p_client text, p_partenaire text, p_retirer boolean DEFAULT false)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_client text := nullif(btrim(coalesce(p_client, '')), '');
  v_partenaire text := nullif(btrim(coalesce(p_partenaire, '')), '');
  v_metiers text[] := CASE p_role WHEN 'apporteur' THEN ARRAY['apporteur', 'parrain'] WHEN 'courtier' THEN ARRAY['courtier', 'banque'] END;
  v_id bigint;
BEGIN
  -- 09/11/2026 (note partenaires §28.17, lot 7) : relier un partenaire à un CLIENT (Q1 « A », dès le premier jour) —
  -- « Noter une affaire apportée ». Écrit CHEZ NOUS seulement (rien chez Hektor). Un même lien actif n'existe qu'une fois ;
  -- un retrait garde la trace (qui, quand). Rôle apporteur (métier apporteur ou parrain) ; courtier (courtier ou banque)
  -- préparé pour le lot 6.
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif : le lien ne peut pas être écrit.' USING ERRCODE = '42501';
  END IF;
  IF v_metiers IS NULL THEN
    RAISE EXCEPTION '%', 'Rôle inconnu pour un client (apporteur ou courtier).';
  END IF;
  IF v_client IS NULL OR v_partenaire IS NULL THEN
    RAISE EXCEPTION '%', 'Le client et le partenaire sont obligatoires.';
  END IF;
  IF v_client = v_partenaire THEN
    RAISE EXCEPTION '%', 'Un partenaire ne peut pas s''apporter lui-même.';
  END IF;

  IF coalesce(p_retirer, false) THEN
    UPDATE public.app_partenaire_lien SET retire_le = now(), retire_par = auth.uid()
     WHERE objet = 'client' AND role = p_role AND client_contact_id = v_client AND partenaire_id = v_partenaire AND retire_le IS NULL
    RETURNING id INTO v_id;
    IF v_id IS NULL THEN RAISE EXCEPTION '%', 'Ce lien n''existe pas (ou il est déjà retiré).'; END IF;
    RETURN jsonb_build_object('action', 'retire', 'retire_id', v_id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM public.app_partenaire_metier
                  WHERE contact_id = v_partenaire AND metier = ANY (v_metiers) AND retire_le IS NULL) THEN
    RAISE EXCEPTION '%', 'Ce contact n''a pas le métier ' || array_to_string(v_metiers, ' ou ') || ' au catalogue des partenaires.';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.app_contact_current WHERE hektor_contact_id::text = v_client) THEN
    RAISE EXCEPTION '%', 'Client introuvable.';
  END IF;

  SELECT id INTO v_id FROM public.app_partenaire_lien
   WHERE objet = 'client' AND role = p_role AND client_contact_id = v_client AND partenaire_id = v_partenaire AND retire_le IS NULL;
  IF v_id IS NOT NULL THEN RETURN jsonb_build_object('action', 'inchange', 'id', v_id); END IF;

  INSERT INTO public.app_partenaire_lien (partenaire_id, role, objet, client_contact_id, origine, pose_par)
  VALUES (v_partenaire, p_role, 'client', v_client, 'app', auth.uid())
  RETURNING id INTO v_id;
  RETURN jsonb_build_object('action', 'pose', 'id', v_id);
END
$function$;

REVOKE ALL ON FUNCTION public.app_partenaire_du_client(text,text,text,boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.app_partenaire_du_client(text,text,text,boolean) FROM anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_du_client(text,text,text,boolean) TO authenticated, service_role;

COMMIT;
