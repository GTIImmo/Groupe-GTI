-- ═══════════════════════════════════════════════════════════════════════════
-- LES CONTROLES DES GESTES SANS BIEN -- a rejouer autant de fois qu'on veut
-- 17/11/2026. ⛔ IL N'ECRIT RIEN.
-- ⭐ Chaque ligne porte CE QU'ON ATTEND, pour qu'un ecart saute aux yeux.
-- ═══════════════════════════════════════════════════════════════════════════
select 'la fonction existe (attendu 1)' as controle,
       count(*)::text as mesure,
       case when count(*) = 1 then '✅' else '⛔' end as verdict
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'app_action_status_sans_bien'
union all
select 'authenticated peut l executer (attendu true)',
       has_function_privilege('authenticated',
         'public.app_action_status_sans_bien()', 'EXECUTE')::text,
       case when has_function_privilege('authenticated',
              'public.app_action_status_sans_bien()', 'EXECUTE')
            then '✅' else '⛔' end
union all
select '⛔ TEMOIN INVERSE -- anon NE peut PAS (attendu false)',
       has_function_privilege('anon',
         'public.app_action_status_sans_bien()', 'EXECUTE')::text,
       case when not has_function_privilege('anon',
              'public.app_action_status_sans_bien()', 'EXECUTE')
            then '✅' else '⛔' end
union all
select '⭐⭐ TEMOIN POSITIF -- des gestes sans bien a montrer (attendu >= 1)',
       count(*)::text, case when count(*) >= 1 then '✅' else '⚠ piece vide' end
  from app_console_job j
 where j.app_dossier_id is null and j.hektor_annonce_id is null
   and j.status = 'error'
   and (coalesce(j.attempt_count, 0) >= 5 or j.requested_at < now() - interval '3 hours')
   and j.requested_at > now() - interval '30 days'
   and not exists (select 1 from app_pending_resolution r
                    where r.objet = 'geste' and r.payload_json->>'job_id' = j.id::text)
union all
select '⭐ et ils sont les MEMES que ceux de app_en_attente_humain (attendu 0 ecart)',
       abs((select count(*) from app_en_attente_humain where reference = 'sans annonce')
         - (select count(*) from app_console_job j
             where j.app_dossier_id is null and j.hektor_annonce_id is null
               and j.status = 'error'
               and (coalesce(j.attempt_count, 0) >= 5
                    or j.requested_at < now() - interval '3 hours')
               and j.requested_at > now() - interval '30 days'
               and not exists (select 1 from app_pending_resolution r
                                where r.objet = 'geste'
                                  and r.payload_json->>'job_id' = j.id::text)))::text,
       case when (select count(*) from app_en_attente_humain where reference = 'sans annonce')
               = (select count(*) from app_console_job j
                   where j.app_dossier_id is null and j.hektor_annonce_id is null
                     and j.status = 'error'
                     and (coalesce(j.attempt_count, 0) >= 5
                          or j.requested_at < now() - interval '3 hours')
                     and j.requested_at > now() - interval '30 days'
                     and not exists (select 1 from app_pending_resolution r
                                      where r.objet = 'geste'
                                        and r.payload_json->>'job_id' = j.id::text))
            then '✅' else '⛔ la sentinelle et l ecran ne verraient PAS la meme chose' end
union all
select '⭐ VOISINES -- les 4 fonctions soeurs (attendu 4)', count(*)::text,
       case when count(*) = 4 then '✅' else '⛔' end
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('app_action_status', 'app_action_resolve',
                     'app_console_can_request_job', 'app_negociateur_signal_traiter')
union all
select '⭐ les deux lectures NE SE CHEVAUCHENT PAS (attendu 0)', count(*)::text,
       case when count(*) = 0 then '✅' else '⛔' end
  from app_console_job j
 where j.status = 'error'
   and j.app_dossier_id is null and j.hektor_annonce_id is null
   and j.app_dossier_id is not null
union all
select 'signaux de negociateurs OUVERTS (le bouton « vu » les videra)',
       count(*)::text, 'pour memoire'
  from app_negociateur_journal where a_signaler and traite_le is null;
