-- RÉPÉTITION de patch_partenaire_interlocuteur_2026-11-06.sql (pièce 3.4) — LECTURE SEULE, à lancer après la pose.
-- Chaque ligne doit dire « OK ». Empreintes relevées par l'essai du 06/11 dans une transaction annulée (le patch, une écriture,
-- un relais, la fiche notaire, une modification, un retrait, un nom vide refusé, puis l'inverse : empreintes revenues).
SELECT '1 la table porte le nouveau nom, l''ancien est libre' AS controle,
       CASE WHEN to_regclass('public.app_partenaire_interlocuteur') IS NOT NULL AND to_regclass('public.app_notaire_interlocuteur') IS NULL THEN 'OK' ELSE 'ECHEC' END AS etat
UNION ALL SELECT '2 la colonne s''appelle contact_id',
       CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'app_partenaire_interlocuteur' AND column_name = 'contact_id')
             AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'app_partenaire_interlocuteur' AND column_name = 'notaire_contact_id') THEN 'OK' ELSE 'ECHEC' END
UNION ALL SELECT '3 la fonction neuve, empreinte 77a9f674',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_partenaire_interlocuteur_ecrire(bigint,text,text,text,text,text,boolean)'::regprocedure), chr(13), '')) = '77a9f6747a341b520aa86795e95fa8f9' THEN 'OK' ELSE 'ECHEC' END
UNION ALL SELECT '4 l''ancien nom est le relais, empreinte 4f338e8e',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_notaire_interlocuteur_ecrire(bigint,text,text,text,text,text,boolean)'::regprocedure), chr(13), '')) = '4f338e8e45ccb92629cc01d7d8ac93bc' THEN 'OK' ELSE 'ECHEC' END
UNION ALL SELECT '5 la fiche notaire lit le nouveau nom, empreinte f13c23b8',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_notaire_fiche(text)'::regprocedure), chr(13), '')) = 'f13c23b8c12ccafe17c82d652f599318' THEN 'OK' ELSE 'ECHEC' END
UNION ALL SELECT '6 la fiche notaire répond (un notaire à dossiers, 10008890)',
       CASE WHEN jsonb_typeof(public.app_notaire_fiche('10008890')->'interlocuteurs') = 'array' THEN 'OK' ELSE 'ECHEC' END
UNION ALL SELECT '7 droits de la fonction neuve : authenticated et service_role, pas anon ni public',
       CASE WHEN (SELECT array_to_string(proacl, ',') FROM pg_proc WHERE oid = 'public.app_partenaire_interlocuteur_ecrire(bigint,text,text,text,text,text,boolean)'::regprocedure)
                 = 'postgres=X/postgres,authenticated=X/postgres,service_role=X/postgres' THEN 'OK' ELSE 'ECHEC' END
UNION ALL SELECT '8 lecture de la table : la règle renommée, comptes actifs seulement',
       CASE WHEN EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'app_partenaire_interlocuteur' AND policyname = 'app_partenaire_interlocuteur_lire' AND cmd = 'SELECT') THEN 'OK' ELSE 'ECHEC' END
UNION ALL SELECT '9 aucune ligne perdue (0 au 06/11 avant la pose)',
       CASE WHEN (SELECT count(*) FROM public.app_partenaire_interlocuteur) >= 0 THEN 'OK (' || (SELECT count(*) FROM public.app_partenaire_interlocuteur) || ' lignes)' ELSE 'ECHEC' END;
