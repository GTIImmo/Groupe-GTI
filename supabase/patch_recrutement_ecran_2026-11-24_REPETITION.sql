-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — RECRUTEMENT R6 (ce que l'écran écrit et lit)                                 24/11/2026
-- À jouer APRÈS patch_recrutement_ecran_2026-11-24.sql. RIEN n'est écrit : la 1re partie se joue dans une
-- transaction ANNULÉE, sur une fiche TÉMOIN fictive (« Élodie BRUN-DUPRÉ », numéro de la plage fictive
-- 06 39 98), posée en propriétaire puis jouée dans la peau d'un administrateur. Le moindre écart ARRÊTE
-- le script (« [n] KO … »). La 2e partie est une lecture.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare
  v_admin uuid; v_autre uuid;
  v_etat text; v_msg text; v_j jsonb; v_id bigint; n integer;
begin
  select id into v_admin from public.app_user_profile where role = 'admin' and is_active order by id limit 1;
  select id into v_autre from public.app_user_profile where coalesce(role::text, '') <> 'admin' and is_active order by id limit 1;
  if v_admin is null or v_autre is null then raise exception '[0] mise en scene impossible'; end if;

  -- [1] LES EMPREINTES SQL SONT CELLES DU COLLECTEUR PYTHON (valeurs calculées en Python le 24/11)
  if (select string_agg(nature || '=' || empreinte, ' ' order by nature)
        from recrutement.empreintes('123 456 782', '06 39 98 12 41', ' Camille.Roux@Exemple.FR ', 'Élodie', 'BRUN-DUPRÉ', '42'))
     <> 'email=114bb06025e8776c3b7e9e5e1ecb6cba2ce82adad8a0e34e21d699603c606d7d '
     || 'nom=22187411c27ce8dabd7c825ca28aa106ae20adbf9db0980308d55819a10330de '
     || 'siren=3e169d3fbb576ee5dc0cbdebc4ce1aee027e4e6033342098c63d25ed53655467 '
     || 'telephone=3ef0fde2bffdbbcfc629486f10247085437baacd042d93c102b81ef32a01b115' then
    raise exception '[1] KO : les empreintes SQL different de celles du collecteur Python';
  end if;
  if recrutement.cle_nom('Œdipe', 'D''AUBIGNÉ') <> 'aubigne-d-dipe' or recrutement.cle_nom('Straße', 'MÜLLER') <> 'e-muller-stra' then
    raise exception '[1] KO : la cle de nom differe de celle du collecteur Python';
  end if;

  -- mise en scène EN PROPRIÉTAIRE : une fiche témoin, vérifiée
  insert into recrutement.fiche (reseau, identifiant, prenom, nom, commune, code_postal, departement, telephone, source_contact, siren)
  values ('essai_r6', 'temoin', 'Élodie', 'BRUN-DUPRÉ', 'Saint-Étienne', '42000', '42', '06 39 98 12 41', 'répétition R6', '123456782');
  insert into recrutement.fiche (reseau, identifiant, prenom, nom, commune, code_postal, departement)
  values ('essai_r6', 'temoin_bis', 'Elodie', 'Brun Dupre', 'Firminy', '42700', '42');   -- MÊME personne (même nom, même département)
  if (select count(*) from recrutement.fiche where reseau = 'essai_r6') <> 2 then raise exception '[0] mise en scene : les fiches temoins ne sont pas posees'; end if;

  -- [2] un NON-ADMINISTRATEUR est refusé partout (témoin inverse)
  perform set_config('request.jwt.claims', json_build_object('sub', v_autre, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_autre::text, true);
  execute 'set local role authenticated';
  begin perform public.rec_candidats(); v_etat := 'aucun refus'; exception when others then v_etat := sqlstate; end;
  execute 'reset role';
  if v_etat <> '42501' then raise exception '[2] KO : rec_candidats ne refuse pas un non-administrateur (%)', v_etat; end if;
  execute 'set local role authenticated';
  begin perform public.rec_noter('essai_r6', 'temoin', 'note', 'x'); v_etat := 'aucun refus'; exception when others then v_etat := sqlstate; end;
  execute 'reset role';
  if v_etat <> '42501' then raise exception '[2] KO : rec_noter ne refuse pas un non-administrateur (%)', v_etat; end if;

  -- dans la peau d'un ADMINISTRATEUR, pour toute la suite
  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_admin::text, true);

  -- [3] la liste : autant de candidats que de fiches, la fiche témoin y est
  execute 'set local role authenticated';
  v_j := public.rec_candidats();
  execute 'reset role';
  if jsonb_array_length(v_j -> 'candidats') <> (select count(*) from recrutement.fiche) then
    raise exception '[3] KO : rec_candidats ne rend pas toutes les fiches';
  end if;
  if not exists (select 1 from jsonb_array_elements(v_j -> 'candidats') c where c ->> 'identifiant' = 'temoin' and (c ->> 'etape')::int = 1) then
    raise exception '[3] KO : la fiche temoin manque, ou son etape par defaut n''est pas 1 (Reperee)';
  end if;

  -- [4] noter, marquer une étape, mettre à jour le suivi, corriger : tout se voit dans la fiche
  execute 'set local role authenticated';
  v_id := public.rec_noter('essai_r6', 'temoin', 'appel', 'premier appel', 'interesse');
  perform public.rec_etape('essai_r6', 'temoin', 2);
  perform public.rec_suivi_maj('essai_r6', 'temoin', '{"prochaine_action":"la rappeler","prochaine_le":"2026-12-01","info_donnee":true}');
  perform public.rec_corriger('essai_r6', 'temoin', 'telephone', '06 39 98 77 03');
  v_j := public.rec_candidat('essai_r6', 'temoin');
  execute 'reset role';
  if (v_j -> 'suivi' ->> 'etape')::int <> 2 or v_j -> 'suivi' ->> 'prochaine_action' <> 'la rappeler'
     or v_j -> 'suivi' ->> 'info_donnee_le' is null then
    raise exception '[4] KO : le suivi ne porte pas ce qui a ete ecrit (%)', v_j -> 'suivi';
  end if;
  if jsonb_array_length(v_j -> 'fil') <> 4 then   -- appel, étape, information, correction
    raise exception '[4] KO : le fil porte % evenements au lieu de 4', jsonb_array_length(v_j -> 'fil');
  end if;
  if v_j -> 'carnet' -> 0 ->> 'valeur' <> '06 39 98 77 03' then raise exception '[4] KO : le carnet ne porte pas la correction'; end if;
  -- … et la liste montre la valeur CORRIGÉE, la fiche garde celle de l'annuaire
  execute 'set local role authenticated';
  v_j := public.rec_candidats();
  execute 'reset role';
  if (select c ->> 'telephone' from jsonb_array_elements(v_j -> 'candidats') c where c ->> 'identifiant' = 'temoin') <> '06 39 98 77 03'
     or (select telephone from recrutement.fiche where identifiant = 'temoin') <> '06 39 98 12 41' then
    raise exception '[4] KO : le carnet ne gagne pas dans la liste, ou il a ecrase la fiche';
  end if;

  -- [5] un champ hors liste est refusé
  v_etat := null;
  execute 'set local role authenticated';
  begin perform public.rec_suivi_maj('essai_r6', 'temoin', '{"etape":6}'); exception when others then v_etat := sqlstate; end;
  execute 'reset role';
  if v_etat is distinct from '22023' then raise exception '[5] KO : rec_suivi_maj accepte un champ hors liste (%)', v_etat; end if;

  -- [6] les doublons : la même personne sous une autre fiche est trouvée
  execute 'set local role authenticated';
  v_j := public.rec_doublons('Élodie', 'Brun-Dupré', null, null, null, '42');
  execute 'reset role';
  if jsonb_array_length(v_j -> 'fiches') <> 2 or (v_j ->> 'sur_liste_noire')::boolean then
    raise exception '[6] KO : rec_doublons ne trouve pas les 2 fiches temoins (%)', v_j;
  end if;

  -- [7] « ne plus contacter » : ses DEUX fiches partent (la seconde par le nom), ses empreintes restent,
  --     son nom et son SIREN restent lisibles dans retrait ; et elle ne peut plus être ajoutée à la main
  execute 'set local role authenticated';
  v_j := public.rec_retirer('essai_r6', 'temoin', 'ne_plus_contacter', 'elle_meme', '2026-11-24');
  execute 'reset role';
  if (v_j ->> 'fiches_effacees')::int <> 2 then raise exception '[7] KO : % fiche(s) effacee(s) au lieu de 2', v_j ->> 'fiches_effacees'; end if;
  if exists (select 1 from recrutement.fiche where reseau = 'essai_r6') then raise exception '[7] KO : une fiche temoin reste'; end if;
  if exists (select 1 from recrutement.evenement where reseau = 'essai_r6') or exists (select 1 from recrutement.correction where reseau = 'essai_r6') then
    raise exception '[7] KO : son fil ou son carnet reste';
  end if;
  select count(*) into n from recrutement.liste_noire
   where empreinte in (select empreinte from recrutement.empreintes('123456782', '06 39 98 12 41', null, 'Élodie', 'BRUN-DUPRÉ', '42'))
     and niveau = 'ne_plus_contacter';
  if n <> 3 then raise exception '[7] KO : % empreinte(s) sur la liste au lieu de 3 (siren, telephone, nom)', n; end if;
  if not exists (select 1 from recrutement.empreintes(null, '06 39 98 77 03', null, null, null, null) x
                   join recrutement.liste_noire l on l.empreinte = x.empreinte) then
    raise exception '[7] KO : le numero CORRIGE n''est pas sur la liste';
  end if;
  if not exists (select 1 from recrutement.retrait where nom_affiche = 'Élodie BRUN-DUPRÉ' and siren = '123456782' and qui = 'elle_meme') then
    raise exception '[7] KO : la trace de la demande (nom, SIREN, date) manque';
  end if;
  v_etat := null;
  execute 'set local role authenticated';
  begin
    perform public.rec_ajouter('{"prenom":"Élodie","nom":"BRUN-DUPRÉ","departement":"42","telephone":"06 39 98 12 41","source_contact":"essai"}');
  exception when others then v_etat := sqlstate; v_msg := sqlerrm; end;
  execute 'reset role';
  if v_etat is distinct from '42501' then raise exception '[7] KO : une personne « ne plus contacter » peut etre rajoutee (% %)', v_etat, v_msg; end if;

  -- [8] ajouter une personne NEUVE (témoin inverse du [7]) ; une coordonnée sans source est refusée
  execute 'set local role authenticated';
  v_j := public.rec_ajouter('{"prenom":"Zoé","nom":"ESSAI-R6","departement":"43","commune":"Tence","telephone":"06 39 98 00 01","source_contact":"rencontrée au salon","etape":2}');
  begin
    perform public.rec_ajouter('{"nom":"SANS-SOURCE","telephone":"06 39 98 00 02"}'); v_etat := 'accepte';
  exception when others then v_etat := sqlstate; end;
  execute 'reset role';
  if not exists (select 1 from recrutement.fiche f join recrutement.suivi s using (reseau, identifiant)
                  where f.reseau = 'saisie' and f.identifiant = v_j ->> 'identifiant' and f.origine = 'saisie' and s.etape = 2) then
    raise exception '[8] KO : la personne ajoutee a la main n''est pas la (ou pas a l''etape 2)';
  end if;
  if v_etat <> '22023' then raise exception '[8] KO : une coordonnee sans source est acceptee (%)', v_etat; end if;

  -- [9] « effacer » : rien de lisible ne reste
  execute 'set local role authenticated';
  perform public.rec_retirer('saisie', v_j ->> 'identifiant', 'effacer', 'elle_meme', '2026-11-24');
  execute 'reset role';
  if exists (select 1 from recrutement.fiche where nom = 'ESSAI-R6') then raise exception '[9] KO : la fiche effacee reste'; end if;
  if exists (select 1 from recrutement.retrait where niveau = 'effacer' and (nom_affiche is not null or siren is not null)) then
    raise exception '[9] KO : un effacement garde un nom ou un SIREN';
  end if;

  -- [10] « archiver » : la fiche reste, retirée de ma liste
  insert into recrutement.fiche (reseau, identifiant, nom, departement) values ('essai_r6', 'archive', 'ARCHIVE-R6', '63');
  execute 'set local role authenticated';
  perform public.rec_retirer('essai_r6', 'archive', 'archiver');
  execute 'reset role';
  if not exists (select 1 from recrutement.suivi s join recrutement.fiche f using (reseau, identifiant)
                  where f.identifiant = 'archive' and s.archive and s.archive_le is not null) then
    raise exception '[10] KO : l''archivage ne garde pas la fiche, ou ne la marque pas';
  end if;
end $$;

rollback;

-- ── 2e PARTIE : le tableau des contrôles (lecture seule) ─────────────────────────────────────────────
SELECT 1 AS "#", 'la 1re partie (empreintes = Python, refus du non-admin, parcours complet de l''admin, 3 niveaux de retrait)' AS controle,
       'OK (sinon l''éditeur aurait montré une erreur « [n] KO » et ce tableau ne serait pas affiché)' AS verdict
UNION ALL SELECT 2, 'les 4 tables neuves existent, RLS active',
       (SELECT CASE WHEN count(*) = 4 AND bool_and(c.relrowsecurity) THEN 'OK' ELSE '⛔ ' || count(*) || ' table(s)' END
          FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = 'recrutement' AND c.relname IN ('agence_gti', 'suivi', 'evenement', 'retrait'))
UNION ALL SELECT 3, 'anon et authenticated : aucun droit direct sur les 4 tables',
       CASE WHEN NOT EXISTS (SELECT 1 FROM unnest(ARRAY['agence_gti', 'suivi', 'evenement', 'retrait']) t, (VALUES ('anon'), ('authenticated')) r(role)
                              WHERE has_table_privilege(r.role, 'recrutement.' || t, 'select,insert,update,delete'))
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'le robot : agences en écriture, RIEN sur le suivi, le fil, les retraits',
       CASE WHEN has_table_privilege('recrutement_robot', 'recrutement.agence_gti', 'insert')
             AND NOT has_table_privilege('recrutement_robot', 'recrutement.agence_gti', 'delete')
             AND NOT EXISTS (SELECT 1 FROM unnest(ARRAY['suivi', 'evenement', 'retrait']) t
                              WHERE has_table_privilege('recrutement_robot', 'recrutement.' || t, 'select,insert,update,delete'))
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'les 9 fonctions de l''écran : security definer, anon sans droit, authenticated avec',
       (SELECT CASE WHEN count(*) = 9 AND bool_and(p.prosecdef)
                         AND bool_and(NOT has_function_privilege('anon', p.oid, 'execute'))
                         AND bool_and(has_function_privilege('authenticated', p.oid, 'execute'))
                    THEN 'OK' ELSE '⛔ ' || count(*) || ' fonction(s)' END
          FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace
           AND p.proname IN ('rec_candidats', 'rec_candidat', 'rec_noter', 'rec_etape', 'rec_suivi_maj', 'rec_corriger',
                             'rec_doublons', 'rec_ajouter', 'rec_retirer'))
UNION ALL SELECT 6, 'les fonctions internes (clé de nom, empreintes, garde) : personne d''autre ne les appelle',
       (SELECT CASE WHEN count(*) = 5 AND bool_and(NOT has_function_privilege('authenticated', p.oid, 'execute'))
                         AND bool_and(NOT has_function_privilege('anon', p.oid, 'execute'))
                    THEN 'OK' ELSE '⛔ ' || count(*) || ' fonction(s)' END
          FROM pg_proc p WHERE p.pronamespace = 'recrutement'::regnamespace
           AND p.proname IN ('cle_nom', 'empreinte', 'empreintes', 'valeur', 'exiger_admin'))
UNION ALL SELECT 7, 'TÉMOIN : rien ne reste de la 1re partie (fiches d''essai, retraits, liste noire)',
       CASE WHEN NOT EXISTS (SELECT 1 FROM recrutement.fiche WHERE reseau IN ('essai_r6') OR nom IN ('ESSAI-R6', 'SANS-SOURCE'))
             AND (SELECT count(*) FROM recrutement.retrait) = 0
             AND (SELECT count(*) FROM recrutement.liste_noire) = 0
            THEN 'OK' ELSE '⛔ des lignes d''essai restent' END
UNION ALL SELECT 8, 'les 2 116 fiches montées sont intactes',
       (SELECT CASE WHEN count(*) = 2116 THEN 'OK (' || count(*) || ')' ELSE '⚠ ' || count(*) || ' fiches' END
          FROM recrutement.fiche WHERE origine = 'collecte');
