-- ═══════════════════════════════════════════════════════════════════════════
-- PARTENAIRES — LOT 2, PIÈCE 1 : LE REGISTRE DES PARTENAIRES (MÉTIER + LIENS)                04/11/2026
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md (§6 bis décisions, §8 lot 2, §9 audit final).
--
-- CE QUE CE PATCH FAIT (sur le patron EXACT de app_notaire_interlocuteur, patch_notaire_blocs_2026-10-28.sql) :
--   1. une table NEUVE app_partenaire_metier : le MÉTIER d'un contact partenaire (décision D1 : « petite table »).
--      Un contact peut avoir plusieurs métiers (banque ET courtier) ; la source est dite (netty, hektor, ecran).
--   2. une table NEUVE app_partenaire_lien : les LIENS d'un partenaire à un BIEN (syndic, diagnostiqueur), à une
--      AFFAIRE (courtier, banque, apporteur) ou à un CLIENT avant toute affaire (courtier, apporteur — décision Q1).
--      Ils vivent ICI, pas dans app_relation ni app_affaire_partie (reflets de Hektor, l'une recalculée) — audit §9.
--   3. deux fonctions d'écriture, app_partenaire_metier_ecrire et app_partenaire_lien_ecrire : tout compte actif
--      (comme une fiche contact) ; l'auteur (auth.uid()) et l'heure sont écrits à chaque geste ; « retirer » pose
--      retire_le, rien n'est jamais effacé (un numéro ne se perd jamais).
--   Lecture : tout compte actif (RLS), comme les interlocuteurs du notaire.
-- Les contacts sont désignés par NOTRE numéro (hektor_contact_id de app_contact_current, plage 10 000 000+), comme la
-- fiche notaire — jamais le numéro Hektor. ⚠ SANS clé étrangère vers app_contact_current : la nuit y SUPPRIME un contact
-- qui sort de l'app ; le registre garde son numéro, et la fiche revient avec le contact (audit §9, point 3).
-- ⛔ RIEN CHEZ HEKTOR (décision D2). Rien d'existant n'est modifié.
-- Retour arrière : patch_registre_partenaires_2026-11-04_INVERSE.sql · Contrôle : _REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- Garde : le patch ne se colle qu'une fois.
DO $g$
BEGIN
    IF to_regclass('public.app_partenaire_metier') IS NOT NULL OR to_regclass('public.app_partenaire_lien') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'Le registre des partenaires existe déjà : patch déjà collé. Rien n''est fait.';
    END IF;
END
$g$;

-- 1. LE MÉTIER ───────────────────────────────────────────────────────────────
CREATE TABLE public.app_partenaire_metier (
    id                 bigserial PRIMARY KEY,
    contact_id         text        NOT NULL CHECK (btrim(contact_id) <> ''),
    metier             text        NOT NULL CHECK (metier IN (
                           'syndic', 'diagnostiqueur', 'courtier', 'banque', 'apporteur', 'parrain',
                           'administration', 'societe', 'agent_immobilier', 'mandataire', 'promoteur',
                           'marchand_de_biens', 'investisseur', 'avocat', 'huissier', 'technicien', 'autre')),
    source             text        NOT NULL CHECK (source IN ('netty', 'hektor', 'ecran')),
    confirme_le        timestamptz,
    confirme_par       uuid,
    ecrit_le           timestamptz NOT NULL DEFAULT now(),
    ecrit_par          uuid,
    retire_le          timestamptz,
    retire_par         uuid
);
-- Un métier actif au plus une fois par contact.
CREATE UNIQUE INDEX app_partenaire_metier_actif_uidx ON public.app_partenaire_metier (contact_id, metier) WHERE retire_le IS NULL;
CREATE INDEX app_partenaire_metier_metier_idx ON public.app_partenaire_metier (metier) WHERE retire_le IS NULL;
COMMENT ON TABLE public.app_partenaire_metier IS
  'Partenaires, lot 2 (04/11/2026) : le métier d''un contact partenaire (notre numéro de contact). Source netty / hektor / ecran. Écrit par app_partenaire_metier_ecrire (ou la reprise de nuit) ; jamais effacé (retire_le). Note CHANTIER_ANNUAIRE_PARTENAIRES §6 bis, §8.';

-- 2. LES LIENS ───────────────────────────────────────────────────────────────
CREATE TABLE public.app_partenaire_lien (
    id                   bigserial PRIMARY KEY,
    partenaire_id        text        NOT NULL CHECK (btrim(partenaire_id) <> ''),
    role                 text        NOT NULL CHECK (role IN ('syndic', 'diagnostiqueur', 'courtier', 'banque', 'apporteur')),
    objet                text        NOT NULL CHECK (objet IN ('bien', 'affaire', 'client')),
    app_dossier_id       bigint,
    hektor_annonce_id    bigint,
    app_affaire_id       bigint,
    client_contact_id    text,
    origine              text        NOT NULL CHECK (origine IN ('app', 'hektor', 'netty')),
    pose_le              timestamptz NOT NULL DEFAULT now(),
    pose_par             uuid,
    retire_le            timestamptz,
    retire_par           uuid,
    -- l'objet dit quelle colonne porte la cible, et elle seule
    CHECK (
        (objet = 'bien'    AND (app_dossier_id IS NOT NULL OR hektor_annonce_id IS NOT NULL) AND app_affaire_id IS NULL AND client_contact_id IS NULL)
     OR (objet = 'affaire' AND app_affaire_id IS NOT NULL AND app_dossier_id IS NULL AND hektor_annonce_id IS NULL AND client_contact_id IS NULL)
     OR (objet = 'client'  AND nullif(btrim(coalesce(client_contact_id, '')), '') IS NOT NULL AND app_dossier_id IS NULL AND hektor_annonce_id IS NULL AND app_affaire_id IS NULL)
    ),
    -- quel rôle sur quel objet (décisions §6.2 et Q1)
    CHECK (
        (objet = 'bien'    AND role IN ('syndic', 'diagnostiqueur'))
     OR (objet = 'affaire' AND role IN ('courtier', 'banque', 'apporteur'))
     OR (objet = 'client'  AND role IN ('courtier', 'apporteur'))
    )
);
-- Un même lien actif au plus une fois.
CREATE UNIQUE INDEX app_partenaire_lien_actif_uidx ON public.app_partenaire_lien
    (partenaire_id, role, objet, coalesce(app_dossier_id, -1), coalesce(hektor_annonce_id, -1), coalesce(app_affaire_id, -1), coalesce(client_contact_id, ''))
    WHERE retire_le IS NULL;
CREATE INDEX app_partenaire_lien_partenaire_idx ON public.app_partenaire_lien (partenaire_id) WHERE retire_le IS NULL;
CREATE INDEX app_partenaire_lien_dossier_idx ON public.app_partenaire_lien (app_dossier_id) WHERE retire_le IS NULL AND app_dossier_id IS NOT NULL;
CREATE INDEX app_partenaire_lien_annonce_idx ON public.app_partenaire_lien (hektor_annonce_id) WHERE retire_le IS NULL AND hektor_annonce_id IS NOT NULL;
CREATE INDEX app_partenaire_lien_affaire_idx ON public.app_partenaire_lien (app_affaire_id) WHERE retire_le IS NULL AND app_affaire_id IS NOT NULL;
CREATE INDEX app_partenaire_lien_client_idx ON public.app_partenaire_lien (client_contact_id) WHERE retire_le IS NULL AND client_contact_id IS NOT NULL;
COMMENT ON TABLE public.app_partenaire_lien IS
  'Partenaires, lot 2 (04/11/2026) : les liens d''un partenaire à un bien (syndic, diagnostiqueur), une affaire (courtier, banque, apporteur) ou un client (courtier, apporteur). Origine app / hektor / netty. Écrit par app_partenaire_lien_ecrire (ou la reprise de nuit) ; jamais effacé (retire_le). Rien ne part chez Hektor. Note CHANTIER_ANNUAIRE_PARTENAIRES §6 bis, §8.';

-- 3. LES DROITS : lecture par tout compte actif, écriture par les fonctions seulement ─────
ALTER TABLE public.app_partenaire_metier ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_partenaire_lien   ENABLE ROW LEVEL SECURITY;
CREATE POLICY app_partenaire_metier_lire ON public.app_partenaire_metier FOR SELECT TO authenticated
    USING ((SELECT public.is_app_user_active()));
CREATE POLICY app_partenaire_lien_lire ON public.app_partenaire_lien FOR SELECT TO authenticated
    USING ((SELECT public.is_app_user_active()));
-- ⚠ « REVOKE FROM PUBLIC » ne ferme pas authenticated : on nomme les trois rôles (mémoire du projet).
REVOKE ALL ON TABLE public.app_partenaire_metier FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.app_partenaire_lien   FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.app_partenaire_metier TO authenticated;
GRANT SELECT ON TABLE public.app_partenaire_lien   TO authenticated;
GRANT ALL ON TABLE public.app_partenaire_metier TO service_role;
GRANT ALL ON TABLE public.app_partenaire_lien   TO service_role;
REVOKE ALL ON SEQUENCE public.app_partenaire_metier_id_seq FROM PUBLIC, anon, authenticated;
REVOKE ALL ON SEQUENCE public.app_partenaire_lien_id_seq   FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SEQUENCE public.app_partenaire_metier_id_seq TO service_role;
GRANT USAGE ON SEQUENCE public.app_partenaire_lien_id_seq   TO service_role;

-- 4. ÉCRIRE LE MÉTIER : poser (ou confirmer) un métier, ou le retirer ──────────────
CREATE FUNCTION public.app_partenaire_metier_ecrire(p_contact text, p_metier text, p_retirer boolean DEFAULT false)
RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $w$
DECLARE v_id bigint;
BEGIN
    IF NOT public.is_app_user_active() THEN
        RAISE EXCEPTION '%', 'Compte inactif : le métier ne peut pas être écrit.' USING ERRCODE = '42501';
    END IF;
    IF nullif(btrim(coalesce(p_contact, '')), '') IS NULL THEN RAISE EXCEPTION '%', 'Le contact est obligatoire.'; END IF;
    IF coalesce(p_retirer, false) THEN
        UPDATE public.app_partenaire_metier SET retire_le = now(), retire_par = auth.uid()
         WHERE contact_id = btrim(p_contact) AND metier = p_metier AND retire_le IS NULL RETURNING id INTO v_id;
        IF v_id IS NULL THEN RAISE EXCEPTION '%', 'Métier introuvable pour ce contact (ou déjà retiré).'; END IF;
        RETURN v_id;
    END IF;
    -- Déjà porté (par Netty ou Hektor) : l'écran le CONFIRME, sans changer sa source.
    UPDATE public.app_partenaire_metier SET confirme_le = now(), confirme_par = auth.uid()
     WHERE contact_id = btrim(p_contact) AND metier = p_metier AND retire_le IS NULL RETURNING id INTO v_id;
    IF v_id IS NOT NULL THEN RETURN v_id; END IF;
    INSERT INTO public.app_partenaire_metier (contact_id, metier, source, confirme_le, confirme_par, ecrit_par)
    VALUES (btrim(p_contact), p_metier, 'ecran', now(), auth.uid(), auth.uid())
    RETURNING id INTO v_id;
    RETURN v_id;
END
$w$;
REVOKE ALL ON FUNCTION public.app_partenaire_metier_ecrire(text, text, boolean) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_metier_ecrire(text, text, boolean) TO authenticated, service_role;

-- 5. ÉCRIRE UN LIEN : poser un lien, ou le retirer (par son numéro) ──────────────────
CREATE FUNCTION public.app_partenaire_lien_ecrire(
    p_id bigint, p_partenaire text, p_role text, p_objet text,
    p_app_dossier_id bigint, p_hektor_annonce_id bigint, p_app_affaire_id bigint, p_client text,
    p_retirer boolean DEFAULT false)
RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $w$
DECLARE v_id bigint;
BEGIN
    IF NOT public.is_app_user_active() THEN
        RAISE EXCEPTION '%', 'Compte inactif : le lien ne peut pas être écrit.' USING ERRCODE = '42501';
    END IF;
    IF coalesce(p_retirer, false) THEN
        UPDATE public.app_partenaire_lien SET retire_le = now(), retire_par = auth.uid()
         WHERE id = p_id AND retire_le IS NULL RETURNING id INTO v_id;
        IF v_id IS NULL THEN RAISE EXCEPTION '%', 'Lien introuvable (ou déjà retiré).'; END IF;
        RETURN v_id;
    END IF;
    IF nullif(btrim(coalesce(p_partenaire, '')), '') IS NULL THEN RAISE EXCEPTION '%', 'Le partenaire est obligatoire.'; END IF;
    -- Le même lien déjà actif : on le rend tel quel (un double-clic ne fait pas deux lignes).
    SELECT id INTO v_id FROM public.app_partenaire_lien
     WHERE retire_le IS NULL AND partenaire_id = btrim(p_partenaire) AND role = p_role AND objet = p_objet
       AND coalesce(app_dossier_id, -1) = coalesce(p_app_dossier_id, -1)
       AND coalesce(hektor_annonce_id, -1) = coalesce(p_hektor_annonce_id, -1)
       AND coalesce(app_affaire_id, -1) = coalesce(p_app_affaire_id, -1)
       AND coalesce(client_contact_id, '') = coalesce(nullif(btrim(coalesce(p_client, '')), ''), '');
    IF v_id IS NOT NULL THEN RETURN v_id; END IF;
    INSERT INTO public.app_partenaire_lien (partenaire_id, role, objet, app_dossier_id, hektor_annonce_id, app_affaire_id,
                                            client_contact_id, origine, pose_par)
    VALUES (btrim(p_partenaire), p_role, p_objet, p_app_dossier_id, p_hektor_annonce_id, p_app_affaire_id,
            nullif(btrim(coalesce(p_client, '')), ''), 'app', auth.uid())
    RETURNING id INTO v_id;
    RETURN v_id;
END
$w$;
REVOKE ALL ON FUNCTION public.app_partenaire_lien_ecrire(bigint, text, text, text, bigint, bigint, bigint, text, boolean) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_partenaire_lien_ecrire(bigint, text, text, text, bigint, bigint, bigint, text, boolean) TO authenticated, service_role;

COMMIT;
