-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ NOTAIRE, ÉTAPE 4 — LA FICHE NOTAIRE : UNE FONCTION DE LECTURE                         28/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §49 (audit et décisions de Frédéric).
--
-- app_notaire_fiche(p_contact) rend, pour un notaire (notre numéro de contact, en texte), SES dossiers :
--   · UNE ligne par TRANSACTION (un notaire des deux côtés n'est pas compté deux fois, §49.2-3), avec son ou ses côtés ;
--   · seulement les transactions VIVANTES chez nous (même règle que la vue des liens : « sans numéro Hektor ou présente
--     chez Hektor ») ;
--   · L'ISSUE DE LA CHAÎNE : la vente de la même chaîne (date, prix), même quand le notaire n'y figure pas (§49.2-2) ;
--     pour une vente, le compromis de sa chaîne (pour le délai compromis -> acte) ;
--   · les parties : vendeurs, acheteurs, et les CONFRÈRES (les autres notaires de la transaction, jamais lui-même) ;
--   · le bien : mandat, titre, ville, agence, négociateur, statut, photo (parc, sinon archives, sinon historique).
-- ⭐ SECURITY INVOKER (décision 1, §49.6) : les règles d'accès s'appliquent telles quelles. Un négociateur n'y voit que les
--   transactions de SON portefeuille (décision du chantier ② du 12/10) ; un admin voit tout. Rien d'ouvert en plus.
-- ⛔ LECTURE SEULE. Rien n'est écrit, nulle part. Les règles d'écran (« en cours », « à vérifier », étapes) sont dans le front,
--   où elles sont essayées (apps/hektor-v1/test_fiche_notaire.cjs).
-- Retour arrière : patch_notaire_etape4_fiche_2026-10-28_INVERSE.sql · Contrôle : _REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

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
    'dossiers', coalesce((SELECT jsonb_agg(to_jsonb(d) ORDER BY d.date DESC NULLS LAST, d.app_affaire_id DESC) FROM d), '[]'::jsonb))
$f$;
REVOKE ALL ON FUNCTION public.app_notaire_fiche(text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_notaire_fiche(text) TO authenticated, service_role;
COMMENT ON FUNCTION public.app_notaire_fiche(text) IS
  '⑧ notaire étape 4 (28/10/2026) : les dossiers d''un notaire (une ligne par transaction, issue de la chaîne, parties, confrères, bien). SECURITY INVOKER : les règles d''accès s''appliquent (décision 1, §49.6). Lecture seule.';

COMMIT;
