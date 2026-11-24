-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — RECRUTEMENT R3 (schéma à part, robot, bandeau, 7 battements)                 24/11/2026
-- À coller APRÈS patch_recrutement_schema_2026-11-24.sql. RIEN n'est écrit : la 1re partie se joue dans
-- une transaction ANNULÉE ; la 2e est une lecture.
--
-- 1re PARTIE — dans la peau de l'app. Un administrateur, un non-administrateur et la clé publique appellent
--   le bandeau ; la clé publique tente de lire une fiche. Le moindre écart ARRÊTE le script avec un message
--   « [n] KO … » (une erreur se voit dans l'éditeur ; une notice, non). Les personnes sont choisies par la
--   requête (aucune identité écrite ici) et la mise en scène est VÉRIFIÉE avant l'appel.
-- 2e PARTIE — le tableau des contrôles : chaque ligne doit dire OK.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare
  v_admin  uuid;
  v_autre  uuid;
  v_etat   text;
  v_msg    text;
  v_rendu  jsonb;
begin
  -- [A0] mise en scène VÉRIFIÉE : un administrateur actif ET un utilisateur actif qui ne l'est pas
  select id into v_admin from public.app_user_profile where role = 'admin' and is_active order by id limit 1;
  -- ⚠ role est un ENUM (app_role) : coalesce(role, '') échoue (mesuré le 24/11) -> role::text
  select id into v_autre from public.app_user_profile where coalesce(role::text, '') <> 'admin' and is_active order by id limit 1;
  if v_admin is null or v_autre is null then
    raise exception '[A0] mise en scene impossible : il faut un administrateur actif et un non-administrateur actif';
  end if;

  -- [A1] un ADMINISTRATEUR lit le bandeau (témoin positif)
  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_admin::text, true);
  execute 'set local role authenticated';
  begin
    v_rendu := public.rec_etat_collecte();
  exception when others then
    v_etat := sqlstate; v_msg := sqlerrm;
  end;
  execute 'reset role';
  if v_etat is not null then
    raise exception '[A1] KO : un administrateur est refuse (% %)', v_etat, v_msg;
  end if;
  if v_rendu is null or not (v_rendu ? 'fiches') then
    raise exception '[A1] KO : le bandeau ne rend pas sa forme attendue (%)', v_rendu;
  end if;

  -- [A2] un NON-ADMINISTRATEUR reçoit « Réservé aux administrateurs » (témoin inverse)
  v_etat := null; v_msg := null;
  perform set_config('request.jwt.claims', json_build_object('sub', v_autre, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_autre::text, true);
  execute 'set local role authenticated';
  begin
    perform public.rec_etat_collecte();
  exception when others then
    v_etat := sqlstate; v_msg := sqlerrm;
  end;
  execute 'reset role';
  if v_etat is distinct from '42501' or v_msg not like 'Réservé aux administrateurs%' then
    raise exception '[A2] KO : un non-administrateur n''est pas refuse comme attendu (% %)', v_etat, v_msg;
  end if;

  -- [A3] la clé PUBLIQUE (anon) ne peut pas appeler le bandeau
  v_etat := null; v_msg := null;
  perform set_config('request.jwt.claims', '{"role":"anon"}', true);
  perform set_config('request.jwt.claim.sub', '', true);
  execute 'set local role anon';
  begin
    perform public.rec_etat_collecte();
  exception when others then
    v_etat := sqlstate; v_msg := sqlerrm;
  end;
  execute 'reset role';
  if v_etat is distinct from '42501' then
    raise exception '[A3] KO : la cle publique peut appeler le bandeau (% %)', v_etat, v_msg;
  end if;

  -- [A4] ni la clé publique NI un utilisateur connecté ne lisent une fiche en direct
  v_etat := null; v_msg := null;
  execute 'set local role anon';
  begin
    perform 1 from recrutement.fiche limit 1;
  exception when others then
    v_etat := sqlstate; v_msg := sqlerrm;
  end;
  execute 'reset role';
  if v_etat is distinct from '42501' then
    raise exception '[A4] KO : la cle publique lit recrutement.fiche (% %)', v_etat, v_msg;
  end if;
  v_etat := null; v_msg := null;
  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  execute 'set local role authenticated';
  begin
    perform 1 from recrutement.fiche limit 1;
  exception when others then
    v_etat := sqlstate; v_msg := sqlerrm;
  end;
  execute 'reset role';
  if v_etat is distinct from '42501' then
    raise exception '[A4] KO : un utilisateur connecte lit recrutement.fiche en direct (% %) -- il doit passer par rec_*', v_etat, v_msg;
  end if;
end $$;

rollback;

-- ── 2e PARTIE : le tableau des contrôles (lecture seule) ─────────────────────────────────────────────
SELECT 1 AS "#", 'la 1re partie (administrateur lit, non-administrateur et clé publique refusés)' AS controle,
       'OK (sinon l''éditeur aurait montré une erreur « [A…] KO » et ce tableau ne serait pas affiché)' AS verdict
UNION ALL SELECT 2, 'le schéma et ses 6 tables existent',
       CASE WHEN (SELECT count(*) FROM pg_tables WHERE schemaname = 'recrutement'
                   AND tablename IN ('fiche', 'entreprise', 'collecte', 'source_etat', 'correction', 'liste_noire')) = 6
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'RLS active sur les 6 tables',
       (SELECT CASE WHEN count(*) = 6 THEN 'OK' ELSE '⛔ ' || count(*) || ' sur 6' END
          FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = 'recrutement' AND c.relkind = 'r' AND c.relrowsecurity)
UNION ALL SELECT 4, 'anon et authenticated : aucun droit sur le schéma ni sur une table',
       CASE WHEN NOT has_schema_privilege('anon', 'recrutement', 'usage')
             AND NOT has_schema_privilege('authenticated', 'recrutement', 'usage')
             AND NOT EXISTS (SELECT 1 FROM pg_tables t, (VALUES ('anon'), ('authenticated')) r(role)
                              WHERE t.schemaname = 'recrutement'
                                AND has_table_privilege(r.role, 'recrutement.' || t.tablename, 'select,insert,update,delete'))
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'le robot ne peut pas encore se connecter (NOLOGIN)',
       (SELECT CASE WHEN NOT rolcanlogin AND NOT rolbypassrls AND NOT rolsuper THEN 'OK' ELSE '⛔ ECHEC' END
          FROM pg_roles WHERE rolname = 'recrutement_robot')
UNION ALL SELECT 6, 'le robot écrit les 4 tables montées, sans pouvoir supprimer',
       -- ⚠ une liste « select,insert » répond OUI si UN des droits suffit : chaque droit est demandé seul
       CASE WHEN (SELECT bool_and(has_table_privilege('recrutement_robot', 'recrutement.' || t, 'select')
                                  AND has_table_privilege('recrutement_robot', 'recrutement.' || t, 'insert')
                                  AND has_table_privilege('recrutement_robot', 'recrutement.' || t, 'update')
                                  AND NOT has_table_privilege('recrutement_robot', 'recrutement.' || t, 'delete'))
                    FROM unnest(ARRAY['fiche', 'entreprise', 'collecte', 'source_etat']) t)
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 7, 'le robot LIT seulement le carnet et la liste « ne plus contacter »',
       CASE WHEN (SELECT bool_and(has_table_privilege('recrutement_robot', 'recrutement.' || t, 'select')
                                  AND NOT has_table_privilege('recrutement_robot', 'recrutement.' || t, 'insert,update,delete'))
                    FROM unnest(ARRAY['correction', 'liste_noire']) t)
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 8, 'TÉMOIN INVERSE : le robot n''a AUCUN droit sur les tables de l''app',
       CASE WHEN NOT has_table_privilege('recrutement_robot', 'public.app_user_profile', 'select,insert,update,delete')
             AND NOT has_table_privilege('recrutement_robot', 'public.app_worker_registry', 'select,insert,update,delete')
             AND NOT has_table_privilege('recrutement_robot', 'public.app_dossier_current', 'select,insert,update,delete')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 9, 'le bandeau : fonction « security definer », anon sans droit, authenticated avec',
       CASE WHEN (SELECT prosecdef FROM pg_proc WHERE oid = 'public.rec_etat_collecte()'::regprocedure)
             AND NOT has_function_privilege('anon', 'public.rec_etat_collecte()', 'execute')
             AND has_function_privilege('authenticated', 'public.rec_etat_collecte()', 'execute')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 10, 'les 7 battements recrutement.* : actifs, « bimonthly »',
       (SELECT CASE WHEN count(*) = 7 AND bool_and(frequency = 'bimonthly' AND status = 'active') THEN 'OK : ' || string_agg(worker_key, ', ' ORDER BY worker_key)
                    ELSE '⛔ ' || count(*) || ' ligne(s) : ' || coalesce(string_agg(worker_key || '=' || frequency, ', '), '') END
          FROM public.app_worker_registry WHERE worker_key LIKE 'recrutement.%')
UNION ALL SELECT 11, 'les tables sont vides (la montée viendra à R4)',
       (SELECT CASE WHEN (SELECT count(*) FROM recrutement.fiche) + (SELECT count(*) FROM recrutement.collecte)
                         + (SELECT count(*) FROM recrutement.correction) + (SELECT count(*) FROM recrutement.liste_noire) = 0
                    THEN 'OK' ELSE '⚠ des lignes existent déjà' END);
