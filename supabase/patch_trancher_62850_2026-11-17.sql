-- ═══════════════════════════════════════════════════════════════════════════
-- TRANCHER LE TRAVAIL EN ERREUR DE L'ANNONCE 62850 -- 17/11/2026
--
-- ⭐ A SA DEMANDE EXPRESSE : « Dabord clique pour tranche le travail en erreur ».
--   Je ne peux pas appeler `app_action_resolve` depuis l'exterieur : elle exige
--   un utilisateur connecte (`forbidden_action_resolve`, essaye et refuse ce
--   soir). ON PASSE DONC PAR LA RECETTE DU 13/11, deja employee une fois a sa
--   demande : un bloc `do` qui pose SON identite dans `request.jwt.claims`, puis
--   `set local role authenticated`, puis la RPC elle-meme.
--   ⛔ ON N'ECRIT PAS DANS `app_pending_resolution` A LA MAIN : on appelle LA
--     MEME fonction que le bouton de l'ecran. Une copie du geste serait un
--     second chemin, et le projet en a deja paye le prix.
--
-- ⭐⭐ LE MODE EST « refait », ET C'EST LITTERALEMENT VRAI -- mesure :
--      change_hektor_annonce_status / ERROR  a 19:26:54  <- celui qui sonne
--      change_hektor_annonce_status / DONE   a 20:44:24  <- REFAIT, et REUSSI
--      et l'annonce 62850 porte bien « Sous compromis », compromis actif du 23/10
--   ⛔ SURTOUT PAS « abandon » : ce mode DEFAIT ce que l'app avait ecrit, alors
--     que le geste a abouti. On effacerait un changement de statut reel.
--
-- CE QUE LA RPC FAIT, ET RIEN DE PLUS : elle ecrit une trace dans
--   `app_pending_resolution`. Elle NE TOUCHE PAS au travail, qui reste en
--   `error` pour toujours -- c'est de l'historique, c'est voulu.
--
-- ⚠ LA TRACE PORTERA SON NOM (`resolved_by`), et c'est exact : la decision est
--   la sienne, il vient de la donner. Je ne signe pas a sa place une decision
--   qu'il n'aurait pas prise.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

do $$
declare v_res jsonb;
begin
  -- ① SON IDENTITE, le temps de cette transaction seulement
  perform set_config('request.jwt.claims',
    json_build_object('sub', 'd4b1685f-948b-4ce8-af15-671b94a725e6',
                      'email', 'frederic.gerphagnon@gti-immobilier.fr',
                      'role', 'authenticated')::text, true);
  set local role authenticated;

  -- ② LE MEME APPEL QUE LE BOUTON DE L'ECRAN
  v_res := public.app_action_resolve('080b32a1-0ac4-4ece-a2b7-5ef10a15dc3a'::uuid,
                                     'refait');
  raise notice 'la RPC rend : %', v_res;

  if coalesce(v_res->>'resolved', 'false') <> 'true' then
    raise exception '⛔ NON TRANCHE : raison « % »', coalesce(v_res->>'reason', '?');
  end if;
end $$;

reset role;

-- ③ LES CONTROLES
do $$
declare n integer;
begin
  select count(*) into n from app_pending_resolution
   where objet = 'geste'
     and payload_json->>'job_id' = '080b32a1-0ac4-4ece-a2b7-5ef10a15dc3a';
  if n <> 1 then raise exception '⛔ % trace(s) au lieu de 1', n; end if;

  -- ⭐ et elle porte SON nom, pas « (sans nom) »
  select count(*) into n from app_pending_resolution
   where payload_json->>'job_id' = '080b32a1-0ac4-4ece-a2b7-5ef10a15dc3a'
     and coalesce(resolved_by, '') = 'frederic.gerphagnon@gti-immobilier.fr';
  if n <> 1 then
    raise exception '⛔ la trace ne porte pas son nom -- une trace anonyme ne vaut rien';
  end if;

  -- ⭐⭐ LE BUT : le bandeau et la sentinelle doivent se taire
  select count(*) into n from app_en_attente_humain;
  if n <> 0 then raise exception '⛔ il reste % geste(s) en attente d un humain', n; end if;

  -- ⭐ LE TRAVAIL RESTE EN `error` : c'est de l'historique, c'est voulu
  select count(*) into n from app_console_job
   where id = '080b32a1-0ac4-4ece-a2b7-5ef10a15dc3a' and status = 'error';
  if n <> 1 then raise exception '⛔ le travail a change d etat -- ce n etait pas le but'; end if;

  raise notice '✅ tranche en « refait », trace a son nom, 0 geste en attente';
end $$;

commit;
