-- RETOUR ARRIÈRE de patch_partenaire_interlocuteur_2026-11-06.sql (pièce 3.4, 06/11/2026).
-- ⚠ Il ne juge que SA part (leçon 31) : il remet le nom app_notaire_interlocuteur, la colonne notaire_contact_id, les deux
-- fonctions dans leur forme EXACTE du 06/11 (empreintes vérifiées à la fin, sinon tout est annulé) et retire la fonction
-- neuve. Les lignes écrites entre-temps NE SONT PAS effacées : elles suivent la table (un renommage ne recopie rien). Leur
-- nombre est dit (NOTICE) : des interlocuteurs de syndics ou de courtiers resteraient alors dans la table « notaire ».
-- ⛔ Avant de le coller : redéployer l'app d'avant (elle appelle app_notaire_interlocuteur_ecrire, qui redevient la vraie).

BEGIN;

DO $verif$
DECLARE n bigint;
BEGIN
  IF to_regclass('public.app_partenaire_interlocuteur') IS NULL OR to_regclass('public.app_notaire_interlocuteur') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRÊT : la base n''est pas dans l''état laissé par le patch du 06/11.';
  END IF;
  SELECT count(*) INTO n FROM public.app_partenaire_interlocuteur;
  RAISE NOTICE 'Lignes présentes (gardées, rien n''est effacé) : %', n;
END
$verif$;

ALTER POLICY app_partenaire_interlocuteur_lire ON public.app_partenaire_interlocuteur RENAME TO app_notaire_interlocuteur_lire;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_partenaire_interlocuteur_contact_id_check TO app_notaire_interlocuteur_notaire_contact_id_check;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_partenaire_interlocuteur_nom_check TO app_notaire_interlocuteur_nom_check;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_partenaire_interlocuteur_role_check TO app_notaire_interlocuteur_role_check;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_partenaire_interlocuteur_telephone_check TO app_notaire_interlocuteur_telephone_check;
ALTER TABLE public.app_partenaire_interlocuteur RENAME CONSTRAINT app_partenaire_interlocuteur_email_check TO app_notaire_interlocuteur_email_check;
ALTER INDEX public.app_partenaire_interlocuteur_contact_idx RENAME TO app_notaire_interlocuteur_notaire_idx;
ALTER INDEX public.app_partenaire_interlocuteur_pkey RENAME TO app_notaire_interlocuteur_pkey;
ALTER SEQUENCE public.app_partenaire_interlocuteur_id_seq RENAME TO app_notaire_interlocuteur_id_seq;
ALTER TABLE public.app_partenaire_interlocuteur RENAME COLUMN contact_id TO notaire_contact_id;
ALTER TABLE public.app_partenaire_interlocuteur RENAME TO app_notaire_interlocuteur;
COMMENT ON TABLE public.app_notaire_interlocuteur IS NULL;

-- La fiche notaire relit l'ancien nom (remplacements inverses, chacun vérifié trouvé UNE fois). ⚠ APRÈS le renommage :
-- une fonction en SQL est vérifiée à sa création, la table doit déjà porter l'ancien nom (essai du 06/11).
DO $fiche$
DECLARE
  v_def text := replace(pg_get_functiondef('public.app_notaire_fiche(text)'::regprocedure), chr(13), '');
  a1 text := 'FROM public.app_partenaire_interlocuteur i';
  a2 text := 'WHERE i.contact_id = btrim(p_contact)';
BEGIN
  IF (length(v_def) - length(replace(v_def, a1, ''))) / length(a1) <> 1 OR (length(v_def) - length(replace(v_def, a2, ''))) / length(a2) <> 1 THEN
    RAISE EXCEPTION 'ARRÊT : app_notaire_fiche n''est pas dans la forme laissée par le patch.';
  END IF;
  v_def := replace(v_def, a1, 'FROM public.app_notaire_interlocuteur i');
  v_def := replace(v_def, a2, 'WHERE i.notaire_contact_id = btrim(p_contact)');
  EXECUTE v_def;
END
$fiche$;


-- La fonction d'écriture du notaire, dans sa forme EXACTE du 28/10 (empreinte e5bb5130… vérifiée plus bas).
CREATE OR REPLACE FUNCTION public.app_notaire_interlocuteur_ecrire(p_id bigint, p_notaire text, p_nom text, p_role text, p_telephone text, p_email text, p_retirer boolean DEFAULT false)
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
        UPDATE public.app_notaire_interlocuteur SET retire_le = now(), retire_par = auth.uid()
         WHERE id = p_id AND retire_le IS NULL RETURNING id INTO v_id;
        IF v_id IS NULL THEN RAISE EXCEPTION '%', 'Interlocuteur introuvable (ou déjà retiré).'; END IF;
        RETURN v_id;
    END IF;
    IF nullif(btrim(coalesce(p_nom, '')), '') IS NULL THEN RAISE EXCEPTION '%', 'Le nom de l''interlocuteur est obligatoire.'; END IF;
    IF p_id IS NULL THEN
        IF nullif(btrim(coalesce(p_notaire, '')), '') IS NULL THEN RAISE EXCEPTION '%', 'Le notaire est obligatoire.'; END IF;
        INSERT INTO public.app_notaire_interlocuteur (notaire_contact_id, nom, role, telephone, email, ecrit_par)
        VALUES (btrim(p_notaire), btrim(p_nom), nullif(btrim(coalesce(p_role, '')), ''), nullif(btrim(coalesce(p_telephone, '')), ''),
                nullif(btrim(coalesce(p_email, '')), ''), auth.uid())
        RETURNING id INTO v_id;
    ELSE
        UPDATE public.app_notaire_interlocuteur
           SET nom = btrim(p_nom), role = nullif(btrim(coalesce(p_role, '')), ''), telephone = nullif(btrim(coalesce(p_telephone, '')), ''),
               email = nullif(btrim(coalesce(p_email, '')), ''), ecrit_le = now(), ecrit_par = auth.uid()
         WHERE id = p_id AND retire_le IS NULL RETURNING id INTO v_id;
        IF v_id IS NULL THEN RAISE EXCEPTION '%', 'Interlocuteur introuvable (ou retiré).'; END IF;
    END IF;
    RETURN v_id;
END
$function$;

DROP FUNCTION public.app_partenaire_interlocuteur_ecrire(bigint,text,text,text,text,text,boolean);

DO $fin$
DECLARE
  v_ecrire text := md5(replace(pg_get_functiondef('public.app_notaire_interlocuteur_ecrire(bigint,text,text,text,text,text,boolean)'::regprocedure), chr(13), ''));
  v_fiche  text := md5(replace(pg_get_functiondef('public.app_notaire_fiche(text)'::regprocedure), chr(13), ''));
BEGIN
  IF v_ecrire <> 'e5bb5130c9db16a2a2cc3275bfd526fc' OR v_fiche <> '3e575d5365b7f498f1d31a7624a4d959' THEN
    RAISE EXCEPTION 'ARRÊT : les fonctions ne reviennent pas à leur forme du 06/11 (écrire %, fiche %) — tout est annulé.', v_ecrire, v_fiche;
  END IF;
END
$fin$;

COMMIT;
