-- =====================================================================
-- REPETITION -- les controles de la charge au mandat, rejouables
--              02/11/2026. LECTURE SEULE : aucun ecrit, recollable a volonte.
-- =====================================================================

-- 1. LA COLONNE EXISTE, ET ELLE EST A NOUS
select 'A. la colonne' as controle,
       count(*) as trouvee, 1 as attendu,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from information_schema.columns
 where table_schema='public' and table_name='app_mandat_register_current'
   and column_name='mandat_charge_honoraires_app';

-- 2. LA VUE LA PORTE
select 'B. la vue' as controle,
       count(*) as trouvee, 1 as attendu,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from information_schema.columns
 where table_schema='public' and table_name='app_registre_mandats_current'
   and column_name='mandat_charge_honoraires_app';

-- 3. ⭐ TEMOIN INVERSE : LA CLOTURE EST INTACTE (la vue a ete refaite)
select 'B bis. la cloture intacte' as controle,
       count(*) as trouvee, 3 as attendu,
       case when count(*) = 3 then 'VERT' else 'ROUGE' end as verdict
  from information_schema.columns
 where table_schema='public' and table_name='app_registre_mandats_current'
   and column_name in ('mandat_date_cloture','mandat_date_cloture_app',
                       'mandat_date_cloture_hektor');

-- 4. LES DEUX FONCTIONS, ET LEURS DROITS
select 'D+E. les fonctions' as controle,
       count(*) as trouvee, 2 as attendu,
       case when count(*) = 2 then 'VERT' else 'ROUGE' end as verdict
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname='public'
   and p.proname in ('app_reposer_charge_mandat_app','app_set_mandat_charge_optimistic');

-- 4 bis. ⭐ LES DROITS, CHIFFRES -- ce controle a sorti un ROUGE le 02/11 :
--   un droit par defaut du schema public donne authenticated a toute fonction
--   neuve, et `revoke all from public` ne l'enleve pas. La SAISIE doit etre
--   ouverte a authenticated (c'est le front qui l'appelle, pour garder
--   l'auteur) ; LA RE-POSE NON (geste de service).
select 'les droits, par fonction' as controle,
       p.proname,
       has_function_privilege('anon', p.oid, 'execute') as anon_peut,
       has_function_privilege('authenticated', p.oid, 'execute') as authenticated_peut,
       has_function_privilege('service_role', p.oid, 'execute') as service_peut
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname='public'
   and p.proname in ('app_reposer_charge_mandat_app','app_set_mandat_charge_optimistic')
 order by p.proname;

select 'les droits : authenticated sur LA SAISIE SEULE' as controle,
       count(*) as trouvee, 1 as attendu,
       case when count(*) = 1 then 'VERT' else 'ROUGE' end as verdict
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname='public'
   and p.proname in ('app_reposer_charge_mandat_app','app_set_mandat_charge_optimistic')
   and has_function_privilege('authenticated', p.oid, 'execute');

select 'les droits : anon sur AUCUNE' as controle,
       count(*) as trouvee, 0 as attendu,
       case when count(*) = 0 then 'VERT' else 'ROUGE' end as verdict
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname='public'
   and p.proname in ('app_reposer_charge_mandat_app','app_set_mandat_charge_optimistic')
   and has_function_privilege('anon', p.oid, 'execute');

-- 4 ter. ⭐⭐ TEMOIN DE COMPARAISON : les JUMELLES de la cloture. C'est en les
--   regardant qu'on a vu le rouge -- la re-pose de la cloture est fermee, la
--   mienne ne l'etait pas.
select 'temoin : les jumelles de la cloture' as controle,
       p.proname,
       has_function_privilege('anon', p.oid, 'execute') as anon_peut,
       has_function_privilege('authenticated', p.oid, 'execute') as authenticated_peut
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname='public'
   and p.proname in ('app_reposer_cloture_mandat_app','app_set_mandat_cloture_optimistic')
 order by p.proname;

-- 5. LA RE-POSE TOURNE A BLANC (elle ne touche rien si tout est deja juste)
select 'D. la re-pose, a blanc' as controle,
       public.app_reposer_charge_mandat_app() as compte_rendu;

-- 6. L'ETAT DES DONNEES -- le carnet et la vitrine doivent CONCORDER
select 'les donnees' as controle,
       (select count(*) from public.app_mandat_champ_app
         where champ='charge_commission' and origine='mandat_app'
           and nullif(btrim(coalesce(valeur_app,'')),'') is not null) as au_carnet,
       (select count(mandat_charge_honoraires_app)
          from public.app_mandat_register_current) as a_la_vitrine,
       (select count(*) from public.app_mandat_champ_app
         where champ='charge_commission') as carnet_toutes_origines;

-- 7. ⛔ LE TEMOIN QUI COMPTE VRAIMENT : LES DEUX VALEURS
--    Le defaut de la transaction a dormi 17 jours parce qu'on n'avait que des
--    « acquereur » et aucun « vendeur ». Un seul cote ne prouve RIEN.
select 'les deux valeurs' as controle, valeur_app, count(*) as lignes
  from public.app_mandat_champ_app
 where champ='charge_commission'
 group by valeur_app
 order by valeur_app;

-- 8. ET AUCUNE VALEUR HORS DU VOCABULAIRE
select 'vocabulaire' as controle,
       count(*) as hors_vocabulaire, 0 as attendu,
       case when count(*) = 0 then 'VERT' else 'ROUGE' end as verdict
  from public.app_mandat_champ_app
 where champ='charge_commission'
   and nullif(btrim(coalesce(valeur_app,'')),'') is not null
   and valeur_app not in ('vendeur','acquereur');
