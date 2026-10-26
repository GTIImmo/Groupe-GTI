-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ types, chantier 3 : la pièce 5                                          26/10/2026
-- Lecture seule. La vue neuve comparée à la table de nuit (toujours refaite chaque nuit), sur TOUS les contacts.
-- Le temps d'une fiche se mesure à part : EXPLAIN ANALYZE (voir la fin du fichier).
-- ═══════════════════════════════════════════════════════════════════════════

WITH
neuf AS (SELECT * FROM public.app_contact_relations_current WHERE relation_source = 'registre_transactions'),
nuit AS (SELECT * FROM public.app_contact_relation_current WHERE role_contact LIKE 'acquereur%'),
j AS (SELECT n.*, v.relation_key vk, nullif(v.numero_mandat, '') vnm, v.transaction_state vs, v.transaction_date vd,
             v.transaction_amount va, v.is_active_annonce vact, v.app_dossier_id vdos
        FROM nuit n LEFT JOIN neuf v ON v.hektor_contact_id = n.hektor_contact_id AND v.hektor_annonce_id = n.hektor_annonce_id
                                    AND v.role_contact = n.role_contact AND v.transaction_id = n.transaction_id)
SELECT 1 AS "#", 'chaque lien de la nuit se retrouve dans la vue neuve' AS controle,
       (SELECT CASE WHEN count(*) = count(vk) THEN 'OK (' || count(vk) || ' sur ' || count(*) || ')'
                    ELSE '⛔ ECHEC (' || count(vk) || ' sur ' || count(*) || ')' END FROM j) AS verdict
UNION ALL SELECT 2, 'aucune cle en double dans la vue neuve',
       (SELECT CASE WHEN count(*) = count(DISTINCT relation_key) THEN 'OK' ELSE '⛔ ECHEC' END FROM neuf)
UNION ALL SELECT 3, 'dossier, etat, date, montant, bien actif : identiques a la nuit',
       (SELECT CASE WHEN count(*) FILTER (WHERE vk IS NOT NULL AND (vdos IS DISTINCT FROM app_dossier_id OR vs IS DISTINCT FROM transaction_state
                    OR vd IS DISTINCT FROM transaction_date OR va IS DISTINCT FROM transaction_amount OR vact IS DISTINCT FROM is_active_annonce)) = 0
                    THEN 'OK' ELSE '⛔ ECHEC' END FROM j)
UNION ALL SELECT 4, 'numero de mandat : seulement les ecarts connus (~20, celui de la transaction)',
       (SELECT CASE WHEN count(*) FILTER (WHERE vk IS NOT NULL AND vnm IS DISTINCT FROM nullif(numero_mandat, '')) <= 40
                    THEN 'OK (' || count(*) FILTER (WHERE vk IS NOT NULL AND vnm IS DISTINCT FROM nullif(numero_mandat, '')) || ')'
                    ELSE '⚠ A REGARDER' END FROM j)
UNION ALL SELECT 5, 'la branche des mandants / proprietaires est inchangee (le registre des liens)',
       CASE WHEN (SELECT count(*) FROM public.app_contact_relations_current WHERE relation_source <> 'registre_transactions')
                 = (SELECT count(*) FROM public.app_relation r WHERE (r.present_in_hektor OR (r.source = 'app' AND r.absent_depuis IS NULL)) AND r.retire_le IS NULL)
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

-- LE TEMPS (à jouer à part) :
--   explain analyze select * from public.app_contact_relations_current where hektor_contact_id = '10354701';   -- une fiche contact
--   explain analyze select hektor_contact_id, role_contact from public.app_contact_relations_current where app_dossier_id = 1376593;  -- par bien
