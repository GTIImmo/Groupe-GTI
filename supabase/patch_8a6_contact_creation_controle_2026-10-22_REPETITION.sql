-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a-B2 — la création de contact entre dans le contrôle — TOUT EST ANNULÉ
--                                                                    22/10/2026
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … ». Elle pose LE VRAI PATCH, joue 7 essais
-- (fausses créations, faux retours, sur le contact d'essai 20000007), puis LE VRAI RETOUR
-- ARRIÈRE. Rien ne reste. Fichier GÉNÉRÉ (phase2/checks/gen_patch_8a6_contact_creation_controle.py).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

DO $pose$
DECLARE
    d text := replace(pg_get_functiondef('public.app_contact_saisie_modif_job_trg()'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$    if coalesce(new.result_json->>'status', '') <> 'updated' then return null; end if;  -- held_conflict, etc.$a1$, chr(13), ''),
        replace($a2$    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', '')), '');$a2$, chr(13), ''),
        replace($a3$     where c.hektor_contact_id = ident or c.hektor_target_id = ident$a3$, chr(13), '')];
    neufs text[] := array[
        replace($n1$    -- 8a-B2 (22/10) : la CREATION aussi -- created (contact), created_and_linked (mandant).
    if coalesce(new.result_json->>'status', '') not in ('updated', 'created', 'created_and_linked') then return null; end if;  -- held_conflict, etc.$n1$, chr(13), ''),
        replace($n2$    -- a la creation, notre numero est dans la charge (app_identite), celui de Hektor dans le resultat
    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', new.payload_json->>'app_identite', new.result_json->>'hektor_contact_id', '')), '');$n2$, chr(13), ''),
        replace($n3$     where c.hektor_contact_id = ident or c.hektor_target_id = ident
        or c.hektor_target_id = nullif(trim(coalesce(new.result_json->>'hektor_contact_id', '')), '')$n3$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '7a1b2292ce75c60cfc636208ebe7e0a7' THEN
        RAISE NOTICE '%', 'Deja dans l''etat voulu (7a1b2292) : la fonction n''est pas reecrite.';
    ELSE
        IF md5(d) <> '4af27d6a8dd2aa1153c1b1426db6a563' THEN
            RAISE EXCEPTION '%', format('ARRET : app_contact_saisie_modif_job_trg a l''empreinte %s, attendu 4af27d6a. Rien n''est ecrit.', md5(d));
        END IF;
        FOR i IN 1 .. array_length(ancres, 1) LOOP
            nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
            IF nb <> 1 THEN
                RAISE EXCEPTION '%', format('ARRET : le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
            END IF;
            d := replace(d, ancres[i], neufs[i]);
        END LOOP;
        IF md5(d) <> '7a1b2292ce75c60cfc636208ebe7e0a7' THEN
            RAISE EXCEPTION '%', format('ARRET : le texte obtenu a l''empreinte %s, attendu 7a1b2292 (calcule d''avance). Rien n''est ecrit.', md5(d));
        END IF;
        EXECUTE d;
    END IF;
    -- le declencheur : sa clause WHEN porte la liste des travaux
    EXECUTE 'drop trigger if exists app_contact_saisie_modif_job_trg on public.app_console_job';
    EXECUTE $t$create trigger app_contact_saisie_modif_job_trg
  after update on public.app_console_job
  for each row
  when (new.status = 'done' and old.status is distinct from 'done'
        and new.job_type in ('update_hektor_contact', 'update_hektor_mandant_contact', 'create_hektor_contact', 'create_hektor_mandant_contact'))
  execute function public.app_contact_saisie_modif_job_trg()$t$;
END
$pose$;

DO $essai$
DECLARE
    cid  text := '20000007';
    tgt  text;
    j1 uuid; j2 uuid; j3 uuid; j4 uuid; j5 uuid;
    n int;
    v jsonb;
    paris text;
    avant_on text;
BEGIN
    select hektor_target_id into tgt from public.app_contact_current where hektor_contact_id = cid;
    IF tgt IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : le contact d''essai 20000007 n''a pas de numero Hektor -- la repetition ne prouverait rien.';
    END IF;
    select value into avant_on from public.app_setting where key = 'contact_retour_controle';
    update public.app_setting set value = 'on' where key = 'contact_retour_controle';
    delete from public.app_contact_saisie_modif where hektor_contact_id = cid and etat = 'attente';

    -- (1) une CREATION de contact : notre numero dans la charge, celui de Hektor dans le resultat
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('create_hektor_contact', 'running',
            jsonb_build_object('app_identite', cid, 'creation_token', gen_random_uuid()::text,
                               'last_name', 'ESSAI 8A BIS', 'civilite', 'Mme.', 'city', 'Firminy', 'postal_code', '42000',
                               'comments', 'Creation B2', 'birth_date', '03-05-1982', 'company_name', 'X'),
            now() - interval '10 seconds')
    returning id into j1;
    update public.app_console_job set status = 'done', finished_at = now(),
           result_json = jsonb_build_object('status', 'created', 'hektor_contact_id', tgt) where id = j1;
    select saisie into v from public.app_contact_saisie_modif where job_id = j1 and hektor_contact_id = cid and etat = 'attente';
    insert into _m values (1, 'creation de contact (created) : la saisie est gardee par notre cle, sans naissance ni societe',
        case when v->>'ville' = 'Firminy' and v->>'code_postal' = '42000' and v->>'civilite' = 'Mme.' and v->>'commentaires' = 'Creation B2'
                  and not v ? 'birth_date' and not v ? 'company_name' then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (2) le retour de Hektor apres la creation : la ville recalculee d'apres le code postal
    paris := to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS');
    update public.app_contact_current set refreshed_at = now() + interval '1 second', date_maj = paris,
           nom = 'ESSAI 8A BIS', civilite = 'Mme.', ville = 'Saint-Étienne', code_postal = '42000', commentaires = 'Creation B2'
     where hektor_contact_id = cid;
    select verdict into v from public.app_contact_saisie_modif where job_id = j1 and etat = 'juge';
    insert into _m values (2, 'le retour de la creation est juge : ville remplace, le reste identique',
        case when v->'ville'->>'etat' = 'remplace' and v->'code_postal'->>'etat' = 'identique' and v->'nom'->>'etat' = 'identique'
                  and v->'commentaires'->>'etat' = 'identique' then 'OK' else 'ECHEC ' || coalesce(v::text, 'pas juge') end);
    select count(*) into n from public.app_v_contact_modif_ecarts where job_id = j1 and champ = 'ville' and etat = 'remplace';
    insert into _m values (3, 'la vue montre l''ecart de la creation', case when n = 1 then 'OK' else 'ECHEC ' || n end);

    -- (4) une creation de MANDANT (created_and_linked) : PAS de numero de l'app dans la charge, seulement Hektor dans le resultat
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('create_hektor_mandant_contact', 'running',
            jsonb_build_object('app_dossier_id', 3828957, 'hektor_annonce_id', '62774', 'last_name', 'ESSAI 8A BIS', 'email', 'b2.mandant@example.invalid'),
            now() - interval '5 seconds')
    returning id into j2;
    update public.app_console_job set status = 'done', finished_at = now(),
           result_json = jsonb_build_object('status', 'created_and_linked', 'hektor_contact_id', tgt, 'hektor_annonce_id', '62774') where id = j2;
    select hektor_contact_id into v from (select to_jsonb(s.hektor_contact_id) as hektor_contact_id from public.app_contact_saisie_modif s where job_id = j2) x;
    insert into _m values (4, 'creation de mandant (created_and_linked) : retrouvee par le numero Hektor du resultat, rangee par NOTRE cle',
        case when v #>> '{}' = cid then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (5) la MODIFICATION marche toujours comme avant (non-regression de B)
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('update_hektor_contact', 'running', jsonb_build_object('hektor_contact_id', cid, 'from_pending', true, 'city', 'Lyon'), now())
    returning id into j3;
    update public.app_console_job set status = 'done', result_json = '{"status":"updated"}'::jsonb, finished_at = now() where id = j3;
    select saisie into v from public.app_contact_saisie_modif where job_id = j3;
    insert into _m values (5, 'la modification (updated) est toujours gardee', case when v->>'ville' = 'Lyon' then 'OK' else 'ECHEC ' || coalesce(v::text, 'aucune ligne') end);

    -- (6) une creation qui ECHOUE ou un conflit ne garde rien
    select count(*) into n from public.app_contact_saisie_modif;
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('create_hektor_contact', 'running', jsonb_build_object('app_identite', cid, 'last_name', 'Z'), now())
    returning id into j4;
    update public.app_console_job set status = 'done', result_json = '{"status":"duplicate_found"}'::jsonb, finished_at = now() where id = j4;
    insert into _m values (6, 'un autre resultat (pas created) ne garde rien', case when (select count(*) from public.app_contact_saisie_modif) = n then 'OK' else 'ECHEC' end);

    -- (7) ETEINT : une creation ne garde rien
    update public.app_setting set value = 'off' where key = 'contact_retour_controle';
    select count(*) into n from public.app_contact_saisie_modif;
    insert into public.app_console_job (job_type, status, payload_json, started_at)
    values ('create_hektor_contact', 'running', jsonb_build_object('app_identite', cid, 'last_name', 'Y'), now())
    returning id into j5;
    update public.app_console_job set status = 'done', result_json = jsonb_build_object('status', 'created', 'hektor_contact_id', tgt), finished_at = now() where id = j5;
    insert into _m values (7, 'interrupteur eteint : une creation ne garde rien (temoin inverse)', case when (select count(*) from public.app_contact_saisie_modif) = n then 'OK' else 'ECHEC' end);
    update public.app_setting set value = avant_on where key = 'contact_retour_controle';
END
$essai$;

DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('public.app_contact_saisie_modif_job_trg()'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$    if coalesce(new.result_json->>'status', '') <> 'updated' then return null; end if;  -- held_conflict, etc.$a1$, chr(13), ''),
        replace($a2$    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', '')), '');$a2$, chr(13), ''),
        replace($a3$     where c.hektor_contact_id = ident or c.hektor_target_id = ident$a3$, chr(13), '')];
    neufs text[] := array[
        replace($n1$    -- 8a-B2 (22/10) : la CREATION aussi -- created (contact), created_and_linked (mandant).
    if coalesce(new.result_json->>'status', '') not in ('updated', 'created', 'created_and_linked') then return null; end if;  -- held_conflict, etc.$n1$, chr(13), ''),
        replace($n2$    -- a la creation, notre numero est dans la charge (app_identite), celui de Hektor dans le resultat
    ident := nullif(trim(coalesce(new.payload_json->>'hektor_contact_id', new.payload_json->>'contact_id', new.payload_json->>'app_identite', new.result_json->>'hektor_contact_id', '')), '');$n2$, chr(13), ''),
        replace($n3$     where c.hektor_contact_id = ident or c.hektor_target_id = ident
        or c.hektor_target_id = nullif(trim(coalesce(new.result_json->>'hektor_contact_id', '')), '')$n3$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '4af27d6a8dd2aa1153c1b1426db6a563' THEN
        RAISE NOTICE '%', 'Deja dans l''etat voulu (4af27d6a) : la fonction n''est pas reecrite.';
    ELSE
        IF md5(d) <> '7a1b2292ce75c60cfc636208ebe7e0a7' THEN
            RAISE EXCEPTION '%', format('ARRET : app_contact_saisie_modif_job_trg a l''empreinte %s, attendu 7a1b2292. Rien n''est ecrit.', md5(d));
        END IF;
        FOR i IN 1 .. array_length(neufs, 1) LOOP
            nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
            IF nb <> 1 THEN
                RAISE EXCEPTION '%', format('ARRET : le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
            END IF;
            d := replace(d, neufs[i], ancres[i]);
        END LOOP;
        IF md5(d) <> '4af27d6a8dd2aa1153c1b1426db6a563' THEN
            RAISE EXCEPTION '%', format('ARRET : le texte obtenu a l''empreinte %s, attendu 4af27d6a (calcule d''avance). Rien n''est ecrit.', md5(d));
        END IF;
        EXECUTE d;
    END IF;
    -- le declencheur : sa clause WHEN porte la liste des travaux
    EXECUTE 'drop trigger if exists app_contact_saisie_modif_job_trg on public.app_console_job';
    EXECUTE $t$create trigger app_contact_saisie_modif_job_trg
  after update on public.app_console_job
  for each row
  when (new.status = 'done' and old.status is distinct from 'done'
        and new.job_type in ('update_hektor_contact', 'update_hektor_mandant_contact'))
  execute function public.app_contact_saisie_modif_job_trg()$t$;
END
$retour$;

DO $fin$
DECLARE
    r text;
    ok int;
    total int;
BEGIN
    insert into _m values (8, 'l''inverse rend 4af27d6a et le declencheur a 2 types',
        case when md5(replace(pg_get_functiondef('public.app_contact_saisie_modif_job_trg()'::regprocedure), chr(13), '')) = '4af27d6a8dd2aa1153c1b1426db6a563'
                  AND (SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') NOT LIKE '%create_hektor_contact%'
                  AND (SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'app_contact_saisie_modif_job_trg') LIKE '%update_hektor_mandant_contact%'
             then 'OK' else 'ECHEC' end);
    select count(*) filter (where valeur = 'OK'), count(*), string_agg(n || ' ' || valeur || ' ' || cle, ' | ' order by n)
      into ok, total, r from _m;
    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s | %s', ok, total, r);
END
$fin$;
