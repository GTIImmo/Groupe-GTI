-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ types §52 : remettre la vue des liens comme avant (empreinte 647c3285, 28/10/2026)
-- Il ne juge que SA part : il remet la définition d'avant, verbatim, et vérifie son empreinte. Aucune table n'est touchée.
-- Les marques 'acheteur' du registre restent (la nuit les remet à vide si l'interrupteur APP_RELATION_ACHETEUR_SANS_VENTE
-- est éteint) ; sans ce patch, la vue ne les lit plus.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
create or replace view public.app_contact_relations_current with (security_invoker = true) as
 SELECT r.relation_key,
    r.app_contact_id_texte AS hektor_contact_id,
    r.hektor_annonce_id,
    r.app_dossier_id,
    b.numero_dossier,
    b.numero_mandat,
    b.titre_bien,
    COALESCE(
        CASE
            WHEN (r.origine = 'vente'::text) THEN 'proprietaire'::text
            WHEN (NULLIF(btrim(COALESCE(b.numero_mandat, ''::text)), ''::text) IS NOT NULL) THEN 'mandant'::text
            ELSE NULL::text
        END, r.role_hektor, 'proprietaire'::text) AS role_contact,
    NULL::text AS contact_date_maj,
    r.source AS relation_source,
    NULL::text AS transaction_type,
    NULL::text AS transaction_id,
    NULL::text AS transaction_state,
    NULL::text AS transaction_date,
    NULL::text AS transaction_amount,
    COALESCE(b.au_parc, false) AS is_active_annonce,
    r.last_seen_at,
    r.last_seen_at AS refreshed_at,
    r.origine,
    r.proprietaire_depuis
   FROM (app_relation r
     LEFT JOIN LATERAL ( SELECT s.numero_dossier,
            s.numero_mandat,
            s.titre_bien,
            s.au_parc
           FROM ( SELECT d.numero_dossier,
                    d.numero_mandat,
                    d.titre_bien,
                    true AS au_parc,
                    1 AS rang
                   FROM app_dossiers_current d
                  WHERE (d.hektor_annonce_id = (r.hektor_annonce_id)::bigint)
                UNION ALL
                 SELECT a.numero_dossier,
                    a.numero_mandat,
                    a.titre_bien,
                    false,
                    2
                   FROM app_archive_annonce_index_current a
                  WHERE (a.hektor_annonce_id = (r.hektor_annonce_id)::bigint)
                UNION ALL
                 SELECT h.numero_dossier,
                    h.numero_mandat,
                    h.titre_bien,
                    false,
                    3
                   FROM app_historical_annonce_index_current h
                  WHERE (h.hektor_annonce_id = (r.hektor_annonce_id)::bigint)) s
          ORDER BY s.rang
         LIMIT 1) b ON (true))
  WHERE ((r.present_in_hektor OR ((r.source = 'app'::text) AND (r.absent_depuis IS NULL))) AND (r.retire_le IS NULL))
UNION ALL
 SELECT (((('aff_'::text || (l.app_affaire_id)::text) || '_'::text) || (p.app_contact_id)::text) ||
        CASE
            WHEN (p.role = 'acquereur'::text) THEN ''::text
            ELSE ('_'::text || p.role)
        END) AS relation_key,
    p.app_contact_id_texte AS hektor_contact_id,
    (l.hektor_annonce_id)::text AS hektor_annonce_id,
    l.app_dossier_id,
    b.numero_dossier,
    l.numero_mandat,
    b.titre_bien,
        CASE
            WHEN (p.role = 'acquereur'::text) THEN ('acquereur_'::text || l.kind)
            ELSE p.role
        END AS role_contact,
    k.date_maj AS contact_date_maj,
    'registre_transactions'::text AS relation_source,
    l.kind AS transaction_type,
    l.hektor_affaire_id AS transaction_id,
        CASE
            WHEN (l.kind = 'vente'::text) THEN 'vente'::text
            ELSE l.state
        END AS transaction_state,
    l.date AS transaction_date,
        CASE
            WHEN (l.kind = 'offre'::text) THEN NULL::text
            ELSE l.montant
        END AS transaction_amount,
    (NOT (EXISTS ( SELECT 1
           FROM app_archive_annonce_index_current x
          WHERE (x.hektor_annonce_id = l.hektor_annonce_id)))) AS is_active_annonce,
    (l.last_seen_at)::text AS last_seen_at,
    (l.last_seen_at)::text AS refreshed_at,
    NULL::text AS origine,
    NULL::text AS proprietaire_depuis
   FROM (((app_affaire_partie p
     JOIN app_affaire_ledger l ON ((l.app_affaire_id = p.app_affaire_id)))
     LEFT JOIN app_contact_current k ON ((k.hektor_contact_id = (p.app_contact_id)::text)))
     LEFT JOIN LATERAL ( SELECT s.numero_dossier,
            s.titre_bien
           FROM ( SELECT d.numero_dossier,
                    d.titre_bien,
                    1 AS rang
                   FROM app_dossiers_current d
                  WHERE (d.hektor_annonce_id = l.hektor_annonce_id)
                UNION ALL
                 SELECT a.numero_dossier,
                    a.titre_bien,
                    2
                   FROM app_archive_annonce_index_current a
                  WHERE (a.hektor_annonce_id = l.hektor_annonce_id)
                UNION ALL
                 SELECT h.numero_dossier,
                    h.titre_bien,
                    3
                   FROM app_historical_annonce_index_current h
                  WHERE (h.hektor_annonce_id = l.hektor_annonce_id)) s
          ORDER BY s.rang
         LIMIT 1) b ON (true))
  WHERE ((p.role = ANY (ARRAY['acquereur'::text, 'notaire_vendeur'::text, 'notaire_acquereur'::text])) AND (NOT ((btrim(COALESCE(l.hektor_affaire_id, ''::text)) <> ''::text) AND (l.present_in_hektor IS FALSE))) AND (p.app_contact_id IS NOT NULL));

DO $v$
BEGIN
    IF md5(pg_get_viewdef('public.app_contact_relations_current'::regclass)) <> '647c32855a9b4d8db7b3db8f19247e1e' THEN
        RAISE EXCEPTION '%', 'ARRET : la vue remise ne porte pas l''empreinte d''avant (647c3285). Tout est annule.';
    END IF;
END
$v$;
-- la fonction de la règle b ne sert plus à personne une fois la vue remise
DROP FUNCTION IF EXISTS public.app_lien_vente_devenu_acheteur(text, text);
COMMIT;
