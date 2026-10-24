-- ============================================================================
-- PATCH -- l'index qui manque a `app_photos_remplir_adresses_app` (24/10/2026)
-- ============================================================================
-- Audit complet : notice/AUDIT_ALERTES_MONITORING_2026-10-24.md, section 2 bis.
--
-- LE DEFAUT. Le patch du 20/10 (« la galerie suit le retrait d'une photo »,
--   patch_chantier7_8_galerie_photo_retiree_2026-10-20.sql) cherche les photos
--   bougees en 48 h avec   greatest(derives_generes_le, absent_depuis) >= ...
--   Aucun index ne porte cette formule : la base relit les 442 142 photos
--   (783 Mo). Mesure du 24/10 : 3 486 ms au lieu de 43 ms. Appelee par l'API,
--   la fonction est coupee a 8 s (57014) : 1er essai rate le 21 et le 23/10,
--   les deux le 24/10. Et le worker (masquer / afficher / reordonner) l'appelle
--   aussi, avec le run de nuit pour seul filet.
--
-- LE CORRECTIF : AJOUTER L'INDEX QUI MANQUE, SUR LA FORMULE EXACTE.
--   ⭐ LA FONCTION N'EST PAS TOUCHEE : son empreinte reste
--     ec8066616381cdb90df38ec561f1441f (celle posee par le patch du 20/10).
--     Ni le verrou des masquees (`visible is not false`), ni le correctif du
--     20/10, ni le worker ne bougent. Purement additif.
--   ⭐ L'EXPRESSION EST ECRITE A L'IDENTIQUE de la fonction :
--     greatest(derives_generes_le, absent_depuis). La base ne prend un index
--     d'expression que si la formule est la meme.
--   ⭐ `p_tout or ...` ne gene pas : la base prepare un plan SUR MESURE avec
--     la vraie valeur (false), tant que le plan generique coute plus cher
--     (107 000 contre 14 mesure le 24/10). Prouve sur l'index qui existe deja.
--
-- ⛔ AVANT DE COLLER : AVOIR JOUE LA REPETITION (..._REPETITION.sql) ET LU SON
--    COMPTE RENDU. Elle pose l'index DANS une transaction annulee et prouve
--    qu'il est utilise.
--
-- ⚠ QUAND : PAS entre 05:00 et 07:45 (run + descente), PAS pendant un geste
--   photo (masquer, reordonner). L'etape ① le verifie. Eviter aussi 21:00
--   (GTI Entretien Photos) et 00:00 (GTI Balayage Photos Masquees, dont les
--   travaux sont vus par l'etape ①). Fenetres sures : 08:00-20:45, ou 21:15-22:00.
-- ⚠ COMMENT : TROIS COLLAGES SEPARES. La pose ② doit etre collee SEULE :
--   `create index concurrently` refuse de tourner dans une transaction, et
--   l'editeur SQL en ouvre une s'il y a plusieurs ordres.
-- ⛔ EN CAS DE PROBLEME : patch_photos_index_derniere_date_2026-10-24_INVERSE.sql
-- ============================================================================


-- ============================================================================
-- ① LES CONTROLES AVANT -- coller et lancer SEULS (lecture seule)
--    Toutes les lignes doivent dire OK.
-- ============================================================================
select 'empreinte de la fonction' as controle,
       case when md5(replace(pg_get_functiondef('public.app_photos_remplir_adresses_app(integer,boolean)'::regprocedure), chr(13), ''))
                 = 'ec8066616381cdb90df38ec561f1441f'
            then 'OK (ec806661, celle du 20/10)'
            else 'STOP : la fonction a change depuis le 24/10, la RELIRE avant tout' end as verdict
union all
select 'index deja present ?',
       case when to_regclass('public.app_console_photo_derniere_bouge_idx') is null
            then 'OK (absent)' else 'STOP : il existe deja -- verifier sa validite (etape ③)' end
union all
select 'heure de Paris',
       case when (now() at time zone 'Europe/Paris')::time between '05:00' and '07:45'
            then 'STOP : run ou descente en cours, attendre 07:45'
            else 'OK (' || to_char(now() at time zone 'Europe/Paris', 'HH24:MI') || ')' end
union all
select 'gestes photo en cours',
       case when count(*) = 0 then 'OK (aucun)'
            else 'ATTENDRE : ' || count(*) || ' geste(s) photo pending/running' end
  from public.app_console_job
 where job_type in ('set_hektor_photo_visibility', 'reorder_hektor_photos', 'upload_hektor_photo',
                    'delete_hektor_photo', 'sync_hektor_photos')
   and status in ('pending', 'running');


-- ============================================================================
-- ② LA POSE -- coller et lancer CETTE LIGNE SEULE
--    `concurrently` : la table reste lisible ET modifiable pendant la creation.
--    Duree attendue : de quelques secondes a une minute.
-- ============================================================================
create index concurrently if not exists app_console_photo_derniere_bouge_idx
    on public.app_console_photo ((greatest(derives_generes_le, absent_depuis)));


-- ============================================================================
-- ② bis LES STATISTIQUES -- coller et lancer CETTE LIGNE SEULE, juste apres ②
--    ⚠ INDISPENSABLE : la base ne connait la repartition d'une FORMULE que
--      par une analyse. Sans elle, elle estime « un tiers des lignes » et peut
--      preferer relire toute la table, index ou pas. Derniere analyse
--      automatique de cette table : le 27/09 (mesure du 24/10).
--    Elle ne modifie AUCUNE donnee : elle relit un echantillon et met a jour
--    les statistiques (ce que le nettoyage automatique aurait du faire).
--    Effet de bord : les plans des autres requetes sur cette table se
--    recalculent avec des statistiques A JOUR (elles dataient de 4 semaines).
-- ============================================================================
analyze public.app_console_photo;


-- ============================================================================
-- ③ LE CONTROLE APRES -- coller et lancer SEULS (lecture seule)
--    Attendu : valide = OK, prete = OK, empreinte = OK, plan = OK.
--    ⚠ Si `valide` dit NON : la creation a ete interrompue. Lancer SEULE
--      `drop index concurrently if exists public.app_console_photo_derniere_bouge_idx;`
--      puis recommencer a ①.
-- ============================================================================
select 'index valide' as controle,
       case when i.indisvalid then 'OK' else 'NON -- voir la consigne ci-dessus' end as verdict
  from pg_index i where i.indexrelid = to_regclass('public.app_console_photo_derniere_bouge_idx')
union all
select 'index pret',
       case when i.indisready then 'OK' else 'NON' end
  from pg_index i where i.indexrelid = to_regclass('public.app_console_photo_derniere_bouge_idx')
union all
select 'taille',
       pg_size_pretty(pg_relation_size(to_regclass('public.app_console_photo_derniere_bouge_idx')))
union all
select 'empreinte de la fonction (doit etre INCHANGEE)',
       case when md5(replace(pg_get_functiondef('public.app_photos_remplir_adresses_app(integer,boolean)'::regprocedure), chr(13), ''))
                 = 'ec8066616381cdb90df38ec561f1441f'
            then 'OK (ec806661)' else 'NON -- quelqu un a modifie la fonction' end;

-- puis, toujours en lecture seule, le plan : doit contenir
--   « Index Scan using app_console_photo_derniere_bouge_idx » (ou Bitmap Index Scan)
explain analyze
select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis)) as dernier
  from public.app_console_photo p
 where false or greatest(p.derives_generes_le, p.absent_depuis) >= now() - interval '48 hours'
 group by p.app_dossier_id;


-- ============================================================================
-- ④ LE RATTRAPAGE ET LA VRAIE PREUVE -- PAR L'API, COMME LA NUIT
--    (PowerShell, depuis C:\Hektor\Projet ; il ECRIT : il refait les galeries
--     en retard, le registre et le « sans photo » qui n'ont pas tourne le 24/10)
--
--      node Console\remplir_adresses_photos.js
--
--    Attendu dans la sortie :
--      (app_photos_remplir_adresses_app : X s)   avec X < 2   <- LA PREUVE
--      adresses    : {"statut":"ok", ...}
--      registre    : {...}        sans photo  : {...}
--    ⚠ Sa fenetre est de 48 h : le dernier succes date du 23/10 a 07:04. Si on
--      le lance APRES le 25/10 07:04, des galeries resteraient en retard ->
--      le dire avant de lancer, on l'appellera sur une fenetre plus large.
-- ============================================================================
