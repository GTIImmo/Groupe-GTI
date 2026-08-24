-- =====================================================================
-- Tache 0.7 -- l'audit des fonctions appelables sans etre connecte
-- Date : 2026-08-24
-- Appliquee via les migrations `fermer_execution_publique_fonctions_maintenance`
-- puis `fermer_execution_publique_fonctions_maintenance_via_public` (la seconde
-- corrige la premiere, qui n'avait rien fait -- voir plus bas).
--
-- CE QU'IL Y AVAIT A AUDITER
-- Supabase exposait 124 fonctions. Parmi elles, 85 en SECURITY DEFINER -- c'est-a-dire
-- qui s'executent avec les droits de leur proprietaire et contournent donc les regles
-- d'acces par nature -- dont 81 appelables avec la cle PUBLIQUE du front.
--
-- LE CLASSEMENT, fait sur le CODE des fonctions et non sur leur nom :
--
--    33 VERIFIENT leur appelant     (requester_role, requester_active, auth.uid(),
--                                    is_app_admin, app_console_can_request_job...)
--    48 ne verifient RIEN
--
-- LA BONNE NOUVELLE, et c'est la plus importante : les 33 qui verifient sont exactement
-- celles qui font des degats. TOUTES les app_console_create_*_job y sont -- supprimer une
-- annonce, supprimer un contact, supprimer une recherche, modifier un mandant. Un visiteur
-- ne pouvait pas declencher une suppression chez Hektor.
--
-- CE QU'ON A FERME, ET CE QU'ON N'A PAS FERME
-- On ne corrige PAS les 48 en bloc : beaucoup sont les RPC de lecture que le front appelle
-- legitimement, et les fermer casserait l'app. On ferme la famille problematique PAR
-- NATURE, quel que soit ce qu'elle rend -- celles qui FONT TRAVAILLER la base :
--
--    app_sweep_search_orphans           app_bulk_recompute_chunk
--    app_sweep_stale_provisionals       app_process_rapprochement_dirty
--    app_generate_rapprochement_alerts  app_annonce_enqueue_due_pushes
--    app_generate_mandat_echu_alerts    app_contact_enqueue_due_pushes
--    app_refresh_search_count_high_water app_search_enqueue_due_pushes
--    app_cron_health                    app_console_claim_next_job
--
-- Un visiteur pouvait appeler app_bulk_recompute_chunk en boucle : un moyen de charger
-- l'instance a volonte. C'est exactement ce qui l'a fait redemarrer dans la nuit du 21 au
-- 22/08 -- sauf que la, c'etait involontaire.
--
-- VERIFIE AVANT DE FERMER : aucune de ces douze n'est appelee par le front, le backend ou
-- le worker. Elles ne sont declenchees que par pg_cron, qui execute en tant que
-- proprietaire. Seule app_console_claim_next_job est appelee par console_job_worker.js,
-- mais avec SUPABASE_SERVICE_ROLE_KEY (ligne 1144), pas avec la cle publique.
--
-- ⚠ LE PIEGE QUI A FAIT ECHOUER LA PREMIERE MIGRATION EN SILENCE
-- Postgres accorde EXECUTE a `PUBLIC` par defaut sur toute fonction creee. Retirer le
-- droit a `anon` ne sert donc A RIEN tant que PUBLIC l'a : anon en herite. La premiere
-- migration a ete appliquee sans erreur, et les fonctions repondaient TOUJOURS a la cle
-- publique -- constate en les rappelant apres coup.
--
-- C'est le meme genre de piege que le `revoke select` de la veille, qui laissait INSERT,
-- UPDATE, DELETE et TRUNCATE en place. La lecon est la meme dans les deux cas :
-- RETIRER UN DROIT NOMME NE DIT RIEN DES DROITS HERITES. Il faut reverifier en appelant.
--
-- VERIFIE APRES : les 6 fonctions testees repondent HTTP 401 a la cle publique ;
-- app_console_claim_next_job passe toujours avec la cle de service ; les 10 taches cron
-- affichent 0 echec sur les 10 dernieres minutes ; les 21 sondes du moniteur repondent et
-- ecrivent leurs resultats. Aucune regression.
--
-- RESTE OUVERT, et assume : 36 fonctions sans controle interne restent appelables sans
-- etre connecte (48 moins les 12 fermees ici). Ce sont pour l'essentiel des lectures que
-- le front appelle. Les caracteriser une par une demande de lire 36 corps de fonction ;
-- ce n'est pas fait. C'est une dette CONNUE, pas un trou ignore.
-- =====================================================================

do $$
declare r record; n int := 0;
begin
  for r in
    select p.oid::regprocedure as sig
      from pg_proc p join pg_namespace n2 on n2.oid = p.pronamespace
     where n2.nspname = 'public'
       and p.proname in (
         'app_sweep_search_orphans', 'app_sweep_stale_provisionals',
         'app_generate_rapprochement_alerts', 'app_generate_mandat_echu_alerts',
         'app_annonce_enqueue_due_pushes', 'app_contact_enqueue_due_pushes',
         'app_search_enqueue_due_pushes', 'app_refresh_search_count_high_water',
         'app_cron_health', 'app_bulk_recompute_chunk',
         'app_process_rapprochement_dirty', 'app_console_claim_next_job')
  loop
    -- PUBLIC d'abord : c'est lui qui portait le droit.
    execute format('revoke execute on function %s from public, anon, authenticated', r.sig);
    execute format('grant  execute on function %s to service_role', r.sig);
    n := n + 1;
  end loop;
  raise notice 'execution fermee au public sur % signature(s)', n;
end $$;

-- --- Retour arriere ----------------------------------------------------
--   grant execute on function public.<signature complete> to public;
-- (la signature complete, avec ses parametres : pg_proc.oid::regprocedure la donne)
