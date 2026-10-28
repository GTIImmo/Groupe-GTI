-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ NOTAIRE — LES 4 BLOCS « EN CONSTRUCTION » DE LA FICHE NOTAIRE                          28/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §50 (audit) et §51 (recommandations validées).
--
-- CE QUE CE PATCH FAIT :
--   1. une table NEUVE app_notaire_interlocuteur : les interlocuteurs de l'étude d'un notaire (clerc, formaliste, associé…),
--      SAISIS dans l'app (Hektor n'a pas la notion d'étude). Lue par tout compte actif ; écrite SEULEMENT par la fonction 2 ;
--      jamais effacée : « retirer » pose retire_le (un numéro ne se perd jamais) ;
--   2. app_notaire_interlocuteur_ecrire(...) : ajouter, modifier, retirer. Tout compte actif (comme une fiche contact) ;
--      l'auteur (auth.uid()) et l'heure sont écrits à chaque geste ;
--   3. app_notaire_fiche (même signature, mêmes droits) rend EN PLUS : les conditions suspensives de chaque dossier (registre
--      existant app_affaire_condition, LECTURE SEULE), le nom des documents des compromis sans vente (les pièces du dossier,
--      reconnues dans le front par leur nom), et les interlocuteurs de l'étude.
-- ⛔ RIEN CHEZ HEKTOR. Rien d'existant n'est modifié, hors le corps de app_notaire_fiche (posé le 28/10, étape 4).
-- Retour arrière : patch_notaire_blocs_2026-10-28_INVERSE.sql · Contrôle : _REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

CREATE TABLE IF NOT EXISTS public.app_notaire_interlocuteur (
    id                 bigserial PRIMARY KEY,
    notaire_contact_id text        NOT NULL CHECK (btrim(notaire_contact_id) <> ''),
    nom                text        NOT NULL CHECK (btrim(nom) <> '' AND length(nom) <= 200),
    role               text                 CHECK (role IS NULL OR length(role) <= 120),
    telephone          text                 CHECK (telephone IS NULL OR length(telephone) <= 60),
    email              text                 CHECK (email IS NULL OR length(email) <= 200),
    ecrit_le           timestamptz NOT NULL DEFAULT now(),
    ecrit_par          uuid,
    retire_le          timestamptz,
    retire_par         uuid
);
CREATE INDEX IF NOT EXISTS app_notaire_interlocuteur_notaire_idx ON public.app_notaire_interlocuteur (notaire_contact_id) WHERE retire_le IS NULL;
COMMENT ON TABLE public.app_notaire_interlocuteur IS
  '⑧ notaire (28/10/2026) : les interlocuteurs de l''étude d''un notaire, saisis dans l''app. Écrits par app_notaire_interlocuteur_ecrire seulement ; jamais effacés (retire_le). Note des types §50-51.';
ALTER TABLE public.app_notaire_interlocuteur ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS app_notaire_interlocuteur_lire ON public.app_notaire_interlocuteur;
CREATE POLICY app_notaire_interlocuteur_lire ON public.app_notaire_interlocuteur FOR SELECT TO authenticated
    USING ((SELECT public.is_app_user_active()));
REVOKE ALL ON TABLE public.app_notaire_interlocuteur FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.app_notaire_interlocuteur TO authenticated;
GRANT ALL ON TABLE public.app_notaire_interlocuteur TO service_role;
REVOKE ALL ON SEQUENCE public.app_notaire_interlocuteur_id_seq FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION public.app_notaire_interlocuteur_ecrire(
    p_id bigint, p_notaire text, p_nom text, p_role text, p_telephone text, p_email text, p_retirer boolean DEFAULT false)
RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $w$
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
$w$;
REVOKE ALL ON FUNCTION public.app_notaire_interlocuteur_ecrire(bigint, text, text, text, text, text, boolean) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_notaire_interlocuteur_ecrire(bigint, text, text, text, text, text, boolean) TO authenticated, service_role;

-- la fiche notaire : la fonction de l'étape 4, plus les conditions, les documents et les interlocuteurs
CREATE OR REPLACE FUNCTION public.app_notaire_fiche(p_contact text)
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $f$
WITH mes AS (
    SELECT p.app_affaire_id, array_agg(DISTINCT p.role ORDER BY p.role) AS cotes
      FROM public.app_affaire_partie p
     WHERE p.app_contact_id_texte = btrim(p_contact)
       AND p.role IN ('notaire_vendeur', 'notaire_acquereur')
     GROUP BY p.app_affaire_id
),
l AS (
    SELECT l.*, m.cotes
      FROM public.app_affaire_ledger l
      JOIN mes m ON m.app_affaire_id = l.app_affaire_id
     WHERE NOT (btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS FALSE)
),
d AS (
    SELECT l.app_affaire_id, l.kind, l.state, l.date, l.date_acte, l.date_fin_retractation, l.montant,
           l.commission_agence, l.honoraires_entree, l.honoraires_sortie, l.prix_net_vendeur, l.sequestre, l.app_chaine_id, l.numero_mandat,
           l.hektor_annonce_id, l.app_dossier_id, l.cotes,
           -- l'issue de la chaîne : la vente la plus récente de la même chaîne, vivante chez nous
           (SELECT jsonb_build_object('date', v.date, 'montant', v.montant)
              FROM public.app_affaire_ledger v
             WHERE l.app_chaine_id IS NOT NULL AND v.app_chaine_id = l.app_chaine_id AND v.kind = 'vente'
               AND NOT (btrim(coalesce(v.hektor_affaire_id, '')) <> '' AND v.present_in_hektor IS FALSE)
             ORDER BY v.date DESC NULLS LAST, v.app_affaire_id DESC LIMIT 1) AS vente_chaine,
           -- pour une vente : le compromis de sa chaîne (le délai compromis -> acte)
           (SELECT c.date
              FROM public.app_affaire_ledger c
             WHERE l.kind = 'vente' AND l.app_chaine_id IS NOT NULL AND c.app_chaine_id = l.app_chaine_id
               AND c.kind = 'compromis' AND coalesce(c.state, '') <> 'cancelled'
               AND NOT (btrim(coalesce(c.hektor_affaire_id, '')) <> '' AND c.present_in_hektor IS FALSE)
             ORDER BY c.date ASC NULLS LAST, c.app_affaire_id ASC LIMIT 1) AS compromis_chaine,
           (SELECT coalesce(jsonb_agg(jsonb_build_object('id', p.app_contact_id_texte, 'nom', coalesce(k.display_name, ''))
                                      ORDER BY p.rang NULLS LAST, p.app_contact_id_texte), '[]'::jsonb)
              FROM public.app_affaire_partie p LEFT JOIN public.app_contact_current k ON k.hektor_contact_id = p.app_contact_id_texte
             WHERE p.app_affaire_id = l.app_affaire_id AND p.role = 'vendeur') AS vendeurs,
           (SELECT coalesce(jsonb_agg(jsonb_build_object('id', p.app_contact_id_texte, 'nom', coalesce(k.display_name, ''))
                                      ORDER BY p.rang NULLS LAST, p.app_contact_id_texte), '[]'::jsonb)
              FROM public.app_affaire_partie p LEFT JOIN public.app_contact_current k ON k.hektor_contact_id = p.app_contact_id_texte
             WHERE p.app_affaire_id = l.app_affaire_id AND p.role = 'acquereur') AS acquereurs,
           (SELECT coalesce(jsonb_agg(DISTINCT jsonb_build_object('id', p.app_contact_id_texte, 'nom', coalesce(k.display_name, ''),
                                                                   'ville', coalesce(k.ville, ''))), '[]'::jsonb)
              FROM public.app_affaire_partie p LEFT JOIN public.app_contact_current k ON k.hektor_contact_id = p.app_contact_id_texte
             WHERE p.app_affaire_id = l.app_affaire_id AND p.role IN ('notaire_vendeur', 'notaire_acquereur')
               AND p.app_contact_id_texte IS DISTINCT FROM btrim(p_contact)) AS confreres,
           -- ⑧ blocs (28/10) : les conditions suspensives du registre (app_affaire_condition, lu par tous), LECTURE SEULE
           (SELECT coalesce(jsonb_agg(jsonb_build_object('libelle', c.libelle, 'jours', c.jours, 'date_echeance', c.date_echeance,
                                                         'etat', c.etat, 'date_levee', c.date_levee) ORDER BY c.rang), '[]'::jsonb)
              FROM public.app_affaire_condition c WHERE c.app_affaire_id = l.app_affaire_id) AS conditions,
           -- ⑧ blocs (28/10) : le NOM des documents du bien, seulement pour un compromis sans vente (les pièces du dossier).
           --   La colonne indexée (texte) n'est pas convertie : c'est le numéro du registre qui l'est (leçon du 20/10).
           (SELECT coalesce(jsonb_agg(DISTINCT doc.document_name), '[]'::jsonb)
              FROM public.app_console_document doc
             WHERE l.kind = 'compromis' AND doc.hektor_annonce_id = l.hektor_annonce_id::text
               AND NOT EXISTS (SELECT 1 FROM public.app_affaire_ledger v2 WHERE l.app_chaine_id IS NOT NULL
                                 AND v2.app_chaine_id = l.app_chaine_id AND v2.kind = 'vente')) AS documents,
           b.bien
      FROM l
      LEFT JOIN LATERAL (
          SELECT to_jsonb(s) - 'rang' AS bien FROM (
              SELECT x.numero_mandat, x.numero_dossier, x.titre_bien, x.ville, x.agence_nom, x.commercial_nom, x.statut_annonce,
                     coalesce(nullif(x.photo_url_listing_app, ''), x.photo_url_listing) AS photo, true AS au_parc, 1 AS rang
                FROM public.app_dossiers_current x WHERE x.hektor_annonce_id = l.hektor_annonce_id
              UNION ALL
              SELECT a.numero_mandat, a.numero_dossier, a.titre_bien, a.ville, a.agence_nom, a.commercial_nom, a.statut_annonce,
                     coalesce(nullif(a.photo_url_listing_app, ''), a.photo_url_listing), false, 2
                FROM public.app_archive_annonce_index_current a WHERE a.hektor_annonce_id = l.hektor_annonce_id
              UNION ALL
              SELECT h.numero_mandat, h.numero_dossier, h.titre_bien, h.ville, h.agence_nom, h.commercial_nom, h.statut_annonce,
                     coalesce(nullif(h.photo_url_listing_app, ''), h.photo_url_listing), false, 3
                FROM public.app_historical_annonce_index_current h WHERE h.hektor_annonce_id = l.hektor_annonce_id
          ) s ORDER BY s.rang LIMIT 1) b ON true
)
SELECT jsonb_build_object(
    'contact', btrim(p_contact),
    'calcule_le', now(),
    -- la référence de la carte « Compromis -> acte » : la médiane de l'agence, sur les ventes des 3 dernières années, CE QUE
    -- LE COMPTE VOIT (décision 1 : un négociateur compare à ses propres dossiers). Délais hors 0-400 jours écartés (saisies).
    'mediane_agence_jours', (
        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY (v.date::date - c.date::date))
          FROM public.app_affaire_ledger v
          JOIN public.app_affaire_ledger c ON c.app_chaine_id = v.app_chaine_id AND c.kind = 'compromis' AND coalesce(c.state, '') <> 'cancelled'
         WHERE v.kind = 'vente' AND v.app_chaine_id IS NOT NULL
           AND v.date ~ '^\d{4}-\d{2}-\d{2}$' AND c.date ~ '^\d{4}-\d{2}-\d{2}$'
           AND v.date >= to_char(now() - interval '3 years', 'YYYY-MM-DD')
           AND CASE WHEN v.date ~ '^\d{4}-\d{2}-\d{2}$' AND c.date ~ '^\d{4}-\d{2}-\d{2}$'
                    THEN (v.date::date - c.date::date) BETWEEN 0 AND 400 ELSE false END),
    'interlocuteurs', coalesce((SELECT jsonb_agg(jsonb_build_object('id', i.id, 'nom', i.nom, 'role', i.role, 'telephone', i.telephone,
                                                     'email', i.email, 'ecrit_le', i.ecrit_le) ORDER BY i.nom, i.id)
                                  FROM public.app_notaire_interlocuteur i
                                 WHERE i.notaire_contact_id = btrim(p_contact) AND i.retire_le IS NULL), '[]'::jsonb),
    'dossiers', coalesce((SELECT jsonb_agg(to_jsonb(d) ORDER BY d.date DESC NULLS LAST, d.app_affaire_id DESC) FROM d), '[]'::jsonb))
$f$;

REVOKE ALL ON FUNCTION public.app_notaire_fiche(text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_notaire_fiche(text) TO authenticated, service_role;

COMMIT;
