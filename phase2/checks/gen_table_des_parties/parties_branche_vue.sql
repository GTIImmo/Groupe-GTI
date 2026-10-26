 SELECT (('aff_'::text || (l.app_affaire_id)::text) || '_'::text) || (p.app_contact_id)::text AS relation_key,
    (p.app_contact_id)::text AS hektor_contact_id,
    (l.hektor_annonce_id)::text AS hektor_annonce_id,
    l.app_dossier_id,
    b.numero_dossier,
    l.numero_mandat,
    b.titre_bien,
    'acquereur_'::text || l.kind AS role_contact,
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
    (l.last_seen_at)::text AS refreshed_at
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
  WHERE ((p.role = 'acquereur'::text) AND p.transaction_presente AND (p.app_contact_id IS NOT NULL))
