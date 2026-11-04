-- ═══════════════════════════════════════════════════════════════════════════
-- CONTRÔLE de patch_registre_partenaires_notaire_2026-11-04.sql — 6 lignes, toutes « vert » attendues.
-- Lecture seule.
-- ═══════════════════════════════════════════════════════════════════════════
WITH c AS (
    SELECT conname, pg_get_constraintdef(oid) AS d FROM pg_constraint
     WHERE conrelid = 'public.app_partenaire_metier'::regclass AND contype = 'c'
)
SELECT '1 le metier accepte notaire' AS controle,
       CASE WHEN (SELECT position('''notaire''' in d) > 0 FROM c WHERE conname = 'app_partenaire_metier_metier_check') THEN 'vert' ELSE 'ROUGE' END AS etat
UNION ALL
SELECT '2 les 17 metiers d''avant sont toujours la',
       CASE WHEN (SELECT bool_and(position(quote_literal(m) in d) > 0) FROM c, unnest(ARRAY['syndic','diagnostiqueur','courtier','banque',
            'apporteur','parrain','administration','societe','agent_immobilier','mandataire','promoteur','marchand_de_biens',
            'investisseur','avocat','huissier','technicien','autre']) m WHERE conname = 'app_partenaire_metier_metier_check')
            THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '3 la source accepte transactions, et garde netty / hektor / ecran',
       CASE WHEN (SELECT position('''transactions''' in d) > 0 AND position('''netty''' in d) > 0 AND position('''hektor''' in d) > 0
                   AND position('''ecran''' in d) > 0 FROM c WHERE conname = 'app_partenaire_metier_source_check') THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '4 trois controles, pas un de plus ni de moins',
       CASE WHEN (SELECT count(*) FROM c) = 3 THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '5 les lignes d''avant sont intactes (213 au 04/11, aucune retiree par le patch)',
       CASE WHEN (SELECT count(*) FROM public.app_partenaire_metier WHERE metier <> 'notaire') >= 213
             AND (SELECT count(*) FROM public.app_partenaire_metier WHERE retire_le IS NOT NULL) = 0 THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '6 l''ecriture par l''ecran reste fermee aux anonymes',
       CASE WHEN NOT has_function_privilege('anon', 'public.app_partenaire_metier_ecrire(text, text, boolean)', 'EXECUTE')
            THEN 'vert' ELSE 'ROUGE' END;
