-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — les personnes d'une transaction portent nos deux numéros    24/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste.
-- Personnes d'essai : l'acquéreur de l'essai 5 (nous 20000015 / Hektor 605976) et les deux notaires
-- (10355906 / 605227, 10064499 / 122190), pris comme simples contacts.
--   T1 ÉTEINT : 605976 introuvable (le défaut), 20000015 trouvé, id = 20000015, sans app_contact_id
--   T2 allumé : 605976 trouvé, id = 605976, app_contact_id = 20000015
--   T3 allumé : 20000015 trouvé, id = 605976 (le numéro de Hektor), app_contact_id = 20000015
--   T4 allumé : la même personne donnée sous ses deux numéros ne sort qu'une fois
--   T5 allumé : l'ordre demandé est gardé, quel que soit le numéro (605227 puis 10064499)
--   T6 allumé : un numéro inconnu ne fabrique personne
--   T7 allumé : LA CRÉATION, appelée comme l'écran sur le bien d'essai 10000009, avec l'acquéreur sous son numéro
--      de Hektor : la ligne du registre porte l'acquéreur (id 605976, app_contact_id 20000015) — avant, rien
--   T8 l'inverse rend 1b82fdda.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    res jsonb;
    j jsonb;
    lig record;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.app_contact_current WHERE hektor_contact_id = '20000015' AND hektor_target_id = '605976') THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai 20000015 / 605976 a change -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('affaire_personnes_deux_numeros', 'off',
            'Chantier 8 / 24/10/2026 : on = les personnes d''une transaction (acquereurs a la creation, mandants a la modification) sont trouvees par leurs DEUX numeros et portent les deux : id = numero de Hektor, app_contact_id = le notre. off = comportement d''avant (une personne passee sous son numero de Hektor disparaissait). Voir supabase/patch_personnes_deux_numeros_2026-10-24.sql.',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_p$ DO $pose_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        c.hektor_contact_id,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      )
      order by array_position(p_ids, c.hektor_contact_id)
    ),
    '[]'::jsonb)
  from app_contact_current c
  where c.hektor_contact_id = any(p_ids);$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- ⑧ (24/10/2026) : LES PERSONNES D'UNE TRANSACTION PORTENT NOS DEUX NUMEROS.
  -- Regle de Frederic : « l'id Hektor pour communiquer avec Hektor, mon id app pour le registre ».
  -- AVANT : on ne trouvait une personne que par NOTRE identite (`hektor_contact_id`, nom trompeur depuis
  --   la bascule du 23/09) ; passee sous son numero de Hektor -- ce que la modale preremplit depuis le
  --   registre -- elle DISPARAISSAIT de la liste, en silence (mesure : ['605976'] -> 0 personne).
  -- ALLUME : on la trouve par ses DEUX numeros ; `id` porte le numero de HEKTOR, comme la relecture du
  --   worker et la nuit le rangent deja (une seule signification pour `id`, du clic au lendemain) ;
  --   `app_contact_id` porte le NOTRE. Une meme personne donnee deux fois ne sort qu'une fois.
  --   Inconnue : rien (on n'invente pas). Sans numero de Hektor encore : `id` garde notre identite.
  -- Sert a la creation (acquereurs, principal en tete) et a la modification (mandants).
  -- Interrupteur 'affaire_personnes_deux_numeros'. Etude : ETUDE_NUMEROS_PERSONNES_..._2026-10-24.md.
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        case when s.allume
                          then coalesce(nullif(btrim(c.hektor_target_id), ''), c.hektor_contact_id)
                          else c.hektor_contact_id end,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      ) || case when s.allume then jsonb_build_object('app_contact_id', c.app_contact_id) else '{}'::jsonb end
      order by coalesce(array_position(p_ids, c.hektor_contact_id),
                        case when s.allume then array_position(p_ids, c.hektor_target_id) end)
    ),
    '[]'::jsonb)
  from app_contact_current c
  cross join (select coalesce((select v.value from public.app_setting v
                                where v.key = 'affaire_personnes_deux_numeros'), 'off') = 'on' as allume) s
  where c.hektor_contact_id = any(p_ids)
     or (s.allume and c.hektor_target_id = any(p_ids));$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '69904a53433eacf9f06ce2bbfa9ff889' THEN
        RAISE NOTICE '%', 'Deja pose : app_acquereurs_json porte deja l''empreinte 69904a53. Rien n''est ecrit.'; RETURN;
    END IF;
    IF md5(d) <> '1b82fddad4387a5965b6cf16c49a9b1a' THEN
        RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json a l''empreinte %s, attendu 1b82fdda. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '69904a53433eacf9f06ce2bbfa9ff889' THEN
        RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json, le texte rendu a l''empreinte %s, attendu 69904a53 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '')) <> '69904a53433eacf9f06ce2bbfa9ff889' THEN
        RAISE EXCEPTION '%', 'ARRET : app_acquereurs_json, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_rep$ $exec_p$;

    -- T1 ETEINT
    j := public.app_acquereurs_json(array['20000015']);
    total := total + 1;
    IF jsonb_array_length(public.app_acquereurs_json(array['605976'])) = 0 and j->0->>'id' = '20000015' and not (j->0 ? 'app_contact_id') THEN ok := ok + 1; r := r || ' | T1 OK eteint : comportement d avant';
    ELSE r := r || ' | T1 ECHEC eteint : comportement d avant : ' || coalesce(j::text, 'null'); END IF;

    update public.app_setting set value = 'on' where key = 'affaire_personnes_deux_numeros';
    -- T2
    j := public.app_acquereurs_json(array['605976']);
    total := total + 1;
    IF jsonb_array_length(j) = 1 and j->0->>'id' = '605976' and j->0->>'app_contact_id' = '20000015' THEN ok := ok + 1; r := r || ' | T2 OK allume : trouve par le numero de Hektor';
    ELSE r := r || ' | T2 ECHEC allume : trouve par le numero de Hektor : ' || coalesce(j::text, 'null'); END IF;
    -- T3
    j := public.app_acquereurs_json(array['20000015']);
    total := total + 1;
    IF jsonb_array_length(j) = 1 and j->0->>'id' = '605976' and j->0->>'app_contact_id' = '20000015' THEN ok := ok + 1; r := r || ' | T3 OK allume : trouve par notre numero, id = Hektor';
    ELSE r := r || ' | T3 ECHEC allume : trouve par notre numero, id = Hektor : ' || coalesce(j::text, 'null'); END IF;
    -- T4
    j := public.app_acquereurs_json(array['20000015', '605976']);
    total := total + 1;
    IF jsonb_array_length(j) = 1 THEN ok := ok + 1; r := r || ' | T4 OK allume : une personne sous ses deux numeros sort une fois';
    ELSE r := r || ' | T4 ECHEC allume : une personne sous ses deux numeros sort une fois : ' || coalesce(j::text, 'null'); END IF;
    -- T5
    j := public.app_acquereurs_json(array['605227', '10064499']);
    total := total + 1;
    IF jsonb_array_length(j) = 2 and j->0->>'app_contact_id' = '10355906' and j->1->>'app_contact_id' = '10064499' THEN ok := ok + 1; r := r || ' | T5 OK allume : l ordre demande est garde';
    ELSE r := r || ' | T5 ECHEC allume : l ordre demande est garde : ' || coalesce(j::text, 'null'); END IF;
    -- T6
    j := public.app_acquereurs_json(array['999999999']);
    total := total + 1;
    IF jsonb_array_length(j) = 0 THEN ok := ok + 1; r := r || ' | T6 OK allume : un inconnu ne fabrique personne';
    ELSE r := r || ' | T6 ECHEC allume : un inconnu ne fabrique personne : ' || coalesce(j::text, 'null'); END IF;
    -- T7 LA CREATION, comme l'ecran
    res := public.app_change_annonce_status_optimistic(10000009, 'offer',
             jsonb_build_object('amount', '100000', 'buyer_contact_id', '605976', 'buyer_contact_ids', jsonb_build_array('605976')), 9);
    delete from public.app_console_job where id::text = res->>'job_id';
    SELECT acquereur_json::jsonb AS a1, acquereurs_json::jsonb AS al, app_contact_id, hektor_acquereur_id INTO lig
      FROM public.app_affaire_ledger WHERE app_dossier_id = 10000009 ORDER BY app_affaire_id DESC LIMIT 1;
    total := total + 1;
    IF lig.a1->>'id' = '605976' and lig.a1->>'app_contact_id' = '20000015' and jsonb_array_length(lig.al) = 1 and lig.app_contact_id = 20000015 and lig.hektor_acquereur_id = '605976' THEN ok := ok + 1; r := r || ' | T7 OK la creation range l acquereur passe sous son numero de Hektor';
    ELSE r := r || ' | T7 ECHEC la creation range l acquereur passe sous son numero de Hektor : ' || coalesce(coalesce(lig.a1::text, 'acquereur_json vide') || ' / ' || coalesce(lig.al::text, '-'), 'null'); END IF;

    -- T8 L'INVERSE
    EXECUTE $exec_i$ DO $retour_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        c.hektor_contact_id,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      )
      order by array_position(p_ids, c.hektor_contact_id)
    ),
    '[]'::jsonb)
  from app_contact_current c
  where c.hektor_contact_id = any(p_ids);$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- ⑧ (24/10/2026) : LES PERSONNES D'UNE TRANSACTION PORTENT NOS DEUX NUMEROS.
  -- Regle de Frederic : « l'id Hektor pour communiquer avec Hektor, mon id app pour le registre ».
  -- AVANT : on ne trouvait une personne que par NOTRE identite (`hektor_contact_id`, nom trompeur depuis
  --   la bascule du 23/09) ; passee sous son numero de Hektor -- ce que la modale preremplit depuis le
  --   registre -- elle DISPARAISSAIT de la liste, en silence (mesure : ['605976'] -> 0 personne).
  -- ALLUME : on la trouve par ses DEUX numeros ; `id` porte le numero de HEKTOR, comme la relecture du
  --   worker et la nuit le rangent deja (une seule signification pour `id`, du clic au lendemain) ;
  --   `app_contact_id` porte le NOTRE. Une meme personne donnee deux fois ne sort qu'une fois.
  --   Inconnue : rien (on n'invente pas). Sans numero de Hektor encore : `id` garde notre identite.
  -- Sert a la creation (acquereurs, principal en tete) et a la modification (mandants).
  -- Interrupteur 'affaire_personnes_deux_numeros'. Etude : ETUDE_NUMEROS_PERSONNES_..._2026-10-24.md.
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',        case when s.allume
                          then coalesce(nullif(btrim(c.hektor_target_id), ''), c.hektor_contact_id)
                          else c.hektor_contact_id end,
        'civilite',  coalesce(c.civilite, ''),
        'nom',       coalesce(c.nom, ''),
        'prenom',    coalesce(c.prenom, ''),
        'coordonnees', jsonb_build_object(
          'email',    coalesce(c.email, ''),
          'portable', coalesce(c.phone_primary, '')
        )
      ) || case when s.allume then jsonb_build_object('app_contact_id', c.app_contact_id) else '{}'::jsonb end
      order by coalesce(array_position(p_ids, c.hektor_contact_id),
                        case when s.allume then array_position(p_ids, c.hektor_target_id) end)
    ),
    '[]'::jsonb)
  from app_contact_current c
  cross join (select coalesce((select v.value from public.app_setting v
                                where v.key = 'affaire_personnes_deux_numeros'), 'off') = 'on' as allume) s
  where c.hektor_contact_id = any(p_ids)
     or (s.allume and c.hektor_target_id = any(p_ids));$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '1b82fddad4387a5965b6cf16c49a9b1a' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_acquereurs_json porte deja l''empreinte d''avant (1b82fdda).'; RETURN;
    END IF;
    IF md5(d) <> '69904a53433eacf9f06ce2bbfa9ff889' THEN
        RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json a l''empreinte %s, attendu 69904a53. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '1b82fddad4387a5965b6cf16c49a9b1a' THEN
        RAISE EXCEPTION '%', format('ARRET : app_acquereurs_json, le texte rendu a l''empreinte %s, attendu 1b82fdda (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '')) <> '1b82fddad4387a5965b6cf16c49a9b1a' THEN
        RAISE EXCEPTION '%', 'ARRET : app_acquereurs_json, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$retour_rep$ $exec_i$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_acquereurs_json(text[])'::regprocedure), chr(13), '')) = '1b82fddad4387a5965b6cf16c49a9b1a' THEN ok := ok + 1; r := r || ' | T8 OK l inverse rend l empreinte d avant';
    ELSE r := r || ' | T8 ECHEC l inverse rend l empreinte d avant : ' || coalesce('empreinte differente', 'null'); END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
