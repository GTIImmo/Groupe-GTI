-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ types : la table des parties                                              26/10/2026
-- Lecture seule. À rejouer après la pose, puis le lendemain de la première nuit.
-- ═══════════════════════════════════════════════════════════════════════════
WITH
neuf AS (SELECT * FROM public.app_contact_relations_current WHERE relation_source = 'registre_transactions'),
nuit AS (SELECT * FROM public.app_contact_relation_current WHERE role_contact LIKE 'acquereur%'),
j AS (SELECT n.*, v.relation_key vk, v.transaction_state vs, v.transaction_date vd, v.transaction_amount va,
             v.is_active_annonce vact, v.app_dossier_id vdos
        FROM nuit n LEFT JOIN neuf v ON v.hektor_contact_id = n.hektor_contact_id AND v.hektor_annonce_id = n.hektor_annonce_id
                                    AND v.role_contact = n.role_contact AND v.transaction_id = n.transaction_id)
SELECT 1 AS "#", 'la sentinelle ne voit aucun ecart (table contre recalcul, erreurs du declencheur)' AS controle,
       (SELECT CASE WHEN count(*) = 0 THEN 'OK' ELSE '⛔ ECHEC (' || count(*) || ')' END FROM public.app_v_affaire_partie_ecarts) AS verdict
UNION ALL SELECT 2, 'les parties par role',
       (SELECT string_agg(role || ' ' || n, ' · ' ORDER BY role) FROM (SELECT role, count(*) n FROM public.app_affaire_partie GROUP BY 1) x)
UNION ALL SELECT 3, 'chaque lien acquereur de la nuit se retrouve dans la vue',
       (SELECT CASE WHEN count(*) = count(vk) THEN 'OK (' || count(vk) || ' sur ' || count(*) || ')'
                    ELSE '⛔ ECHEC (' || count(vk) || ' sur ' || count(*) || ')' END FROM j)
UNION ALL SELECT 4, 'aucune cle en double dans la vue neuve',
       (SELECT CASE WHEN count(*) = count(DISTINCT relation_key) THEN 'OK' ELSE '⛔ ECHEC' END FROM neuf)
UNION ALL SELECT 5, 'dossier, etat, date, montant, bien actif : identiques a la nuit',
       (SELECT CASE WHEN count(*) FILTER (WHERE vk IS NOT NULL AND (vdos IS DISTINCT FROM app_dossier_id OR vs IS DISTINCT FROM transaction_state
                    OR vd IS DISTINCT FROM transaction_date OR va IS DISTINCT FROM transaction_amount OR vact IS DISTINCT FROM is_active_annonce)) = 0
                    THEN 'OK' ELSE '⛔ ECHEC' END FROM j)
UNION ALL SELECT 6, 'la branche des mandants / proprietaires est inchangee',
       CASE WHEN (SELECT count(*) FROM public.app_contact_relations_current WHERE relation_source <> 'registre_transactions')
                 = (SELECT count(*) FROM public.app_relation r WHERE (r.present_in_hektor OR (r.source = 'app' AND r.absent_depuis IS NULL)) AND r.retire_le IS NULL)
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 7, 'vendeurs sans notre numero (58 550 le 26/10 ; ~36 apres la nuit du 27/10, C4 allume)',
       (SELECT count(*)::text FROM public.app_affaire_partie WHERE role = 'vendeur' AND app_contact_id IS NULL)
ORDER BY 1;
-- LE TEMPS : explain analyze select * from public.app_contact_relations_current where hektor_contact_id = '10354701';
