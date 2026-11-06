-- CHANTIER PARTENAIRES · LOT 3, PIÈCE 3.4 (06/11/2026) — LES INTERLOCUTEURS POUR TOUS LES MÉTIERS.
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §26 decies. Décision de Frédéric (06/11) : « A et on change le
-- nom » — UNE seule table, celle du notaire (vide : 0 ligne au 06/11), RENOMMÉE pour servir à tous les métiers.
--
-- CE QUE CE PATCH FAIT, dans UNE transaction (tout ou rien) :
--   0. vérifie les EMPREINTES des deux fonctions qui lisent / écrivent la table, et que le nouveau nom est libre — sinon ARRÊT ;
--   1. app_notaire_interlocuteur → app_partenaire_interlocuteur ; colonne notaire_contact_id → contact_id ; séquence,
--      index, contrainte et règle de lecture renommés (les droits suivent la table : lecture `authenticated`, rien d'autre) ;
--   2. crée app_partenaire_interlocuteur_ecrire(p_id, p_contact, p_nom, p_role, p_telephone, p_email, p_retirer) : le MÊME
--      geste (compte actif, retirer = dater, jamais effacer) ;
--   3. app_notaire_interlocuteur_ecrire devient un RELAIS vers la nouvelle (l'app en ligne l'appelle encore) — même signature,
--      mêmes droits ;
--   4. app_notaire_fiche lit la table sous son nouveau nom (deux remplacements, chacun vérifié trouvé UNE fois).
-- Rien chez Hektor. Retour arrière : patch_partenaire_interlocuteur_2026-11-06_INVERSE.sql. Contrôles : ..._REPETITION.sql.
-- ⚠ Leçon 30 : les empreintes et les remplacements se font sur le texte SANS retour chariot (chr(13)).

BEGIN;

DO $verif$
DECLARE
  v_ecrire text := md5(replace(pg_get_functiondef('public.app_notaire_interlocuteur_ecrire(bigint,text,text,text,text,text,boolean)'::regprocedure), chr(13), ''));
  v_fiche  text := md5(replace(pg_get_functiondef('public.app_notaire_fiche(text)'::regprocedure), chr(13), ''));
BEGIN
  IF v_ecrire <> 'e5bb5130c9db16a2a2cc3275bfd526fc' THEN
    RAISE EXCEPTION 'ARRÊT : app_notaire_interlocuteur_ecrire a changé (empreinte %), quelqu''un est passé avant.', v_ecrire;
  END IF;
  IF v_fiche <> '3e575d5365b7f498f1d31a7624a4d959' THEN
    RAISE EXCEPTION 'ARRÊT : app_notaire_fiche a changé (empreinte %), quelqu''un est passé avant.', v_fiche;
  END IF;
  IF to_regclass('public.app_notaire_interlocuteur') IS NULL THEN
    RAISE EXCEPTION 'ARRÊT : la table app_notaire_interlocuteur n''existe plus.';
  END IF;
  IF to_regclass('public.app_partenaire_interlocuteur') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRÊT : app_partenaire_interlocuteur existe déjà.';
  END IF;
END
$verif$;

-- 1. Le renommage (les lignes, s'il y en avait, suivent : un renommage ne recopie rien).
ALTER TABLE public.app_notaire_interlocuteur RENAME TO app_partenaire_interlocuteur;
ALTER TABLE public.app_partenaire_interlocuteur RENAME COLUMN notaire_contact_id TO contact_id;
ALTER SEQUENCE public.app_notaire_interlocuteur_id_seq RENAME TO app_partenaire_interlocuteur_id_seq;
ALTER INDEX public.app_notaire_interlocuteur_pkey RENAME TO app_partenaire_interlocuteur_pkey;
ALTER INDEX public.app_notaire_interlocuteur_notaire_idx RENAME TO app_partenaire_interlocuteur_contact_idx;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_notaire_interlocuteur_notaire_contact_id_check TO app_partenaire_interlocuteur_contact_id_check;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_notaire_interlocuteur_nom_check TO app_partenaire_interlocuteur_nom_check;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_notaire_interlocuteur_role_check TO app_partenaire_interlocuteur_role_check;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_notaire_interlocuteur_telephone_check TO app_partenaire_interlocuteur_telephone_check;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_notaire_interlocuteur_email_check TO app_partenaire_interlocuteur_email_check;
ALTER POLICY app_notaire_interlocuteur_lire ON public.app_partenaire_interlocuteur RENAME TO app_partenaire_interlocuteur_lire;
COMMENT ON TABLE public.app_partenaire_interlocuteur IS
  'Interlocuteurs d''un partenaire (notaire, syndic, diagnostiqueur, courtier, apporteur), SAISIS dans l''app. Ex-app_notaire_interlocuteur (renommée le 06/11/2026, pièce 3.4). Écriture : app_partenaire_interlocuteur_ecrire. Retirer = dater, jamais effacer.';

-- 2. La fonction d'écriture, au nouveau nom (même geste que celle du notaire du 28/10).
CREATE FUNCTION public.app_partenaire_interlocuteur_ecrire(p_id bigint, p_contact text, p_nom text, p_role text, p_telephone text, p_email text, p_retirer boolean DEFAULT false)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE v_id bigint;
BEGIN
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif : les interlocuteurs ne peuvent pas être écrits.' USING ERRCODE = '42501';
  END IF;
  IF coalesce(p_retirer, false) THEN
    UPDATE public.app_partenaire_interlocuteur SET retire_le = now(), retire_par = auth.uid()
     WHERE id = p_id AND retire_le IS NULL RETURNING id INTO v_id;
    IF v_id IS NULL THEN RAISE EXCEPTION '%', 'Interlocuteur introuvable (ou déjà retiré).'; END IF;
    RETURN v_id;
  END IF;
  IF nullif(btrim(coalesce(p_nom, '')), '') IS NULL THEN
    RAISE EXCEPTION '%', 'Le nom de l''interlocuteur est obligatoire.';
  END IF;
  IF p_id IS NULL THEN
    IF nullif(btrim(coalesce(p_contact, '')), '') IS NULL THEN
      RAISE EXCEPTION '%', 'Le partenaire est obligatoire.';
    END IF;
    INSERT INTO public.app_partenaire_interlocuteur (contact_id, nom, role, telephone, email, ecrit_par)
    VALUES (btrim(p_contact), btrim(p_nom), nullif(btrim(coalesce(p_role, '')), ''), nullif(btrim(coalesce(p_telephone, '')), ''),
            nullif(btrim(coalesce(p_email, '')), ''), auth.uid())
    RETURNING id INTO v_id;
  ELSE
    UPDATE public.app_partenaire_interlocuteur
       SET nom = btrim(p_nom), role = nullif(btrim(coalesce(p_role, '')), ''), telephone = nullif(btrim(coalesce(p_telephone, '')), ''),
           email = nullif(btrim(coalesce(p_email, '')), ''), ecrit_le = now(), ecrit_par = auth.uid()
     WHERE id = p_id AND retire_le IS NULL RETURNING id INTO v_id;
    IF v_id IS NULL THEN RAISE EXCEPTION '%', 'Interlocuteur introuvable (ou retiré).'; END IF;
  END IF;
  RETURN v_id;
END
$function$;
REVOKE ALL ON FUNCTION public.app_partenaire_interlocuteur_ecrire(bigint,text,text,text,text,text,boolean) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_interlocuteur_ecrire(bigint,text,text,text,text,text,boolean) TO authenticated, service_role;

-- 3. L'ancien nom devient un relais (même signature : ses droits restent ceux d'aujourd'hui).
CREATE OR REPLACE FUNCTION public.app_notaire_interlocuteur_ecrire(p_id bigint, p_notaire text, p_nom text, p_role text, p_telephone text, p_email text, p_retirer boolean DEFAULT false)
 RETURNS bigint
 LANGUAGE sql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  -- RELAIS (06/11/2026, pièce 3.4) : la table est devenue app_partenaire_interlocuteur ; l'app d'avant appelle encore ce nom.
  SELECT public.app_partenaire_interlocuteur_ecrire(p_id, p_notaire, p_nom, p_role, p_telephone, p_email, p_retirer)
$function$;

-- 4. La fiche notaire lit la table sous son nouveau nom.
DO $fiche$
DECLARE
  v_def text := replace(pg_get_functiondef('public.app_notaire_fiche(text)'::regprocedure), chr(13), '');
  a1 text := 'FROM public.app_notaire_interlocuteur i';
  a2 text := 'WHERE i.notaire_contact_id = btrim(p_contact)';
BEGIN
  IF (length(v_def) - length(replace(v_def, a1, ''))) / length(a1) <> 1 THEN
    RAISE EXCEPTION 'ARRÊT : « % » n''est pas trouvé UNE fois dans app_notaire_fiche.', a1;
  END IF;
  IF (length(v_def) - length(replace(v_def, a2, ''))) / length(a2) <> 1 THEN
    RAISE EXCEPTION 'ARRÊT : « % » n''est pas trouvé UNE fois dans app_notaire_fiche.', a2;
  END IF;
  v_def := replace(v_def, a1, 'FROM public.app_partenaire_interlocuteur i');
  v_def := replace(v_def, a2, 'WHERE i.contact_id = btrim(p_contact)');
  EXECUTE v_def;
END
$fiche$;

COMMIT;
