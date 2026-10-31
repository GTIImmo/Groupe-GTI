-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE A — LA PAIRE NAÎT ENSEMBLE, CHEZ NOUS              31/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'éditeur SQL Supabase, APRES la répétition.
-- Note : notice/COUPLES_ERGONOMIE_ET_ECRITURE_PROPOSITION_2026-10-30.md (§12, §15, §16)
-- Plan : C.9-couple-b (CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md, CH17).
--
-- LE DÉFAUT. Créer un couple dans l'app écrit UNE seule ligne chez nous (la
-- personne 1). Hektor, lui, fabrique DEUX fiches (essai E1 du 30/10). La personne 2
-- n'arrive chez nous qu'avec la nuit -- et sous un numéro neuf de la série 10 M, qui
-- n'est relié à rien de ce que l'app a vu.
--
-- CE QUE FAIT CE PATCH — ADDITIF, RIEN N'EST RETIRÉ :
--   1. un INTERRUPTEUR, app_setting 'couple_nait_complet', posé à 'off' ;
--   2. une fonction NEUVE, app_contact_creer_conjoint(...) : interrupteur allumé,
--      contact « couple » et nom du conjoint saisi (l'écran l'exige, App.tsx:40909),
--      elle tire un DEUXIÈME numéro de notre plage (>= 20 000 000), écrit la ligne de
--      la personne 2 et relie les deux lignes COMME LA NUIT LES RELIE :
--          personne 1 : hektor_couple_contact_id = elle-même
--          personne 2 : hektor_couple_contact_id = la personne 1, couple_role vide
--      (mesuré le 31/10 : 24 093 premières « elle-même », 1 609 secondes nommées
--      « la première », couple_role vide). Sinon elle rend NULL et ne touche rien ;
--   3. dans app_create_contact_optimistic, APRÈS le bloc 8a, un bloc À PART qui
--      l'appelle, et la charge du travail emporte 'app_identite_m2' quand il y a une
--      personne 2 (le worker y rangera le numéro Hektor de la seconde fiche, pièce B).
--      Un échec dans ce bloc ne peut ni empêcher ni défaire la création (WARNING).
--
-- CE QU'IL NE FAIT PAS, VOLONTAIREMENT :
--   · la porte « créer un mandant » n'est PAS touchée : elle envoie toujours une
--     personne seule à Hektor (statut 1, console_job_worker.js l. 20778) ;
--   · rien n'est écrit dans `app_contact_provisional` pour la personne 2 : le jeton
--     sert à retrouver LA création, il y en a une ;
--   · la personne 2 n'a que ce que l'écran saisit pour elle (nom, prénom, e-mail,
--     portable, adresse, code postal, ville) : un champ absent reste vide.
--
-- ⛔ GARDES : la fonction n'est modifiée que si son empreinte est celle relevée le
--    31/10 (95fde328…), si le bloc n'y est pas déjà, et si chaque ancre y apparaît
--    UNE fois. Sinon : ARRÊT, rien n'est écrit.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'couple_nait_complet';
-- ÉTEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'couple_nait_complet';
-- ⚠ NE PAS ALLUMER avant la pièce B (le worker) ET son essai : sans elle, la seconde
--   fiche de Hektor n'a pas de case cible et la nuit lui donne un numéro de plus.
-- RETOUR ARRIÈRE COMPLET : supabase/patch_couple_paire_a_la_creation_2026-10-31_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('couple_nait_complet', 'off',
        'Couples 31/10/2026 : on = creer un couple dans l''app ecrit tout de suite la ligne de la personne 2, reliee a la personne 1 (voir supabase/patch_couple_paire_a_la_creation_2026-10-31.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION NEUVE
create or replace function public.app_contact_creer_conjoint(
    p jsonb, p_identite text, p_negociateur_email text, p_agence_nom text)
 returns text
 language plpgsql
 set search_path to 'public'
as $f$
declare
  v_allume boolean;
  v_type   text;
  v_nom    text;
  v_prenom text;
  v_m2     text;
begin
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui')
    into v_allume
    from public.app_setting s
   where s.key = 'couple_nait_complet';
  if not coalesce(v_allume, false) or p is null or jsonb_typeof(p) <> 'object'
     or nullif(trim(coalesce(p_identite, '')), '') is null then
    return null;
  end if;

  -- les noms que l'ecran et le worker donnent au type de personne
  -- (normalizeHektorContactStatus : « couple » ou « 2 »)
  v_type := lower(trim(coalesce(p->>'person_type', p->>'personType', p->>'statut',
                                p->>'contact_status', '')));
  if v_type not in ('couple', '2') then
    return null;
  end if;

  -- memes alias que le worker (normalizeHektorContactPayload)
  v_nom    := nullif(trim(coalesce(p->>'spouse_last_name',  p->>'spouseLastName',  p->>'nom_m2',    p->>'conjoint_nom',    '')), '');
  v_prenom := nullif(trim(coalesce(p->>'spouse_first_name', p->>'spouseFirstName', p->>'prenom_m2', p->>'conjoint_prenom', '')), '');
  -- Le worker n'envoie le bloc membre 2 que s'il a un nom (l. 18502) : sans nom,
  -- Hektor n'aurait rien a mettre sur la seconde fiche, on n'en invente pas une.
  if v_nom is null then
    return null;
  end if;

  v_m2 := nextval('public.app_contact_identite_seq')::text;

  insert into public.app_contact_current(
    hektor_contact_id, app_contact_id, nom, prenom, display_name, email, phone_primary,
    adresse, code_postal, ville,
    negociateur_email, agence_nom, archive, date_enregistrement, date_maj,
    typologies_json, source_hash, refreshed_at,
    hektor_couple_contact_id, app_couple_contact_id)
  values (
    v_m2, v_m2::bigint, v_nom, v_prenom,
    trim(coalesce(v_prenom, '') || ' ' || v_nom),
    nullif(trim(coalesce(p->>'spouse_email', p->>'spouseEmail', p->>'email_m2', '')), ''),
    nullif(trim(coalesce(p->>'spouse_phone', p->>'spousePhone', p->>'telephone_m2', p->>'conjoint_phone', '')), ''),
    nullif(trim(coalesce(p->>'spouse_address', p->>'spouseAddress', p->>'adresse_m2', '')), ''),
    nullif(trim(coalesce(p->>'spouse_postal_code', p->>'spousePostalCode', p->>'codeprivee', p->>'code_m2', '')), ''),
    nullif(trim(coalesce(p->>'spouse_city', p->>'spouseCity', p->>'villeprivee', p->>'ville_m2', '')), ''),
    p_negociateur_email, p_agence_nom, false, now()::date::text, now()::text,
    '[]'::jsonb, 'app_creation_' || v_m2, now(),
    p_identite, p_identite::bigint);

  -- la personne 1 porte le menage : elle se designe elle-meme, comme chez Hektor
  update public.app_contact_current
     set hektor_couple_contact_id = p_identite,
         app_couple_contact_id    = p_identite::bigint
   where hektor_contact_id = p_identite;

  return v_m2;
end
$f$;

-- ⚠ lecon du 13/10 : un « revoke from public » n'enleve pas un droit par defaut.
revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from public;
revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from anon;
revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from authenticated;
grant execute on function public.app_contact_creer_conjoint(jsonb, text, text, text) to service_role;

-- 3. LE BLOC, DANS LA PORTE CONTACT
-- Trois ancres, chacune sur UNE ligne (lecon 30), chacune presente UNE fois.
DO $patch$
DECLARE
    porte   text := 'public.app_create_contact_optimistic(jsonb,integer)';
    empreinte text := '95fde3280af1dff65ab45596f4b3bead';
    marque  text := 'COUPLES · LA PAIRE (31/10/2026)';
    -- (a) la variable
    a_decl  text := $a1$  v_identite     text;
$a1$;
    n_decl  text := $n1$  v_identite_m2  text;
$n1$;
    -- (b) le bloc, apres 8a
    a_bloc  text := $a2$  -- === fin 8a ===
$a2$;
    n_bloc  text := $n2$
  -- === COUPLES · LA PAIRE (31/10/2026) : LA PERSONNE 2 NAIT AVEC LA 1 ===
  -- Interrupteur : app_setting 'couple_nait_complet'. Eteint, ou si ce n'est pas
  -- un couple, app_contact_creer_conjoint rend NULL et ne touche rien.
  -- Un echec ici ne doit JAMAIS empecher ni defaire la creation : bloc a part.
  begin
    v_identite_m2 := public.app_contact_creer_conjoint(
        contact_payload, v_identite, target_email,
        nullif(trim(coalesce(contact_payload->>'target_agency_label', contact_payload->>'agence_nom', '')), ''));
  exception when others then
    v_identite_m2 := null;
    raise warning 'couple_nait_complet : personne 2 non posee pour % (%)', v_identite, sqlerrm;
  end;
  -- === fin couples ===
$n2$;
    -- (c) la charge du travail
    a_job   text := $a3$          'creation_mode', coalesce(nullif(trim(contact_payload->>'creation_mode'), ''), 'contact_global_identity')),
$a3$;
    n_job   text := $n3$          'creation_mode', coalesce(nullif(trim(contact_payload->>'creation_mode'), ''), 'contact_global_identity'))
          -- COUPLES · LA PAIRE (31/10) : le numero de la personne 2, seulement s'il existe
          || case when v_identite_m2 is not null
                  then jsonb_build_object('app_identite_m2', v_identite_m2)
                  else '{}'::jsonb end,
$n3$;
    src     text;
    ancres  text[];
    i       int;
    combien int;
BEGIN
    src    := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
    a_decl := replace(a_decl, chr(13), '');  n_decl := replace(n_decl, chr(13), '');
    a_bloc := replace(a_bloc, chr(13), '');  n_bloc := replace(n_bloc, chr(13), '');
    a_job  := replace(a_job,  chr(13), '');  n_job  := replace(n_job,  chr(13), '');

    IF position(marque in src) > 0 THEN
        RAISE EXCEPTION '%', format('ARRET : le bloc des couples est DEJA dans %s. Rien n''est ecrit.', porte);
    END IF;
    IF md5(src) <> empreinte THEN
        RAISE EXCEPTION '%', format('ARRET : %s a change depuis le 31/10 (empreinte %s, attendue %s). Rien n''est ecrit.',
                                    porte, md5(src), empreinte);
    END IF;
    ancres := array[a_decl, a_bloc, a_job];
    FOR i IN 1 .. 3 LOOP
        combien := (length(src) - length(replace(src, ancres[i], ''))) / length(ancres[i]);
        IF combien <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre n° %s apparait %s fois (1 attendue). Rien n''est ecrit.', i, combien);
        END IF;
    END LOOP;

    src := replace(src, a_decl, a_decl || n_decl);
    src := replace(src, a_bloc, a_bloc || n_bloc);
    src := replace(src, a_job,  n_job);
    EXECUTE src;
END
$patch$;

-- 4. LES CONTROLES
SELECT 1 AS "#", 'interrupteur pose, ETEINT' AS controle,
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'couple_nait_complet') = 'off'
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'le bloc est dans la porte CONTACT, une fois',
       CASE WHEN (SELECT (length(prosrc) - length(replace(prosrc, '=== COUPLES · LA PAIRE (31/10/2026)', '')))
                         / length('=== COUPLES · LA PAIRE (31/10/2026)')
                    FROM pg_proc WHERE oid = 'public.app_create_contact_optimistic(jsonb,integer)'::regprocedure) = 1
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'interrupteur eteint : la fonction neuve rend NULL',
       CASE WHEN public.app_contact_creer_conjoint('{"person_type":"couple","spouse_last_name":"x"}'::jsonb, '1', null, null) IS NULL
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'droits de la porte INCHANGES (authenticated oui, anon non)',
       CASE WHEN has_function_privilege('authenticated', 'public.app_create_contact_optimistic(jsonb,integer)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_create_contact_optimistic(jsonb,integer)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la fonction neuve est FERMEE a anon et authenticated',
       CASE WHEN NOT has_function_privilege('anon', 'public.app_contact_creer_conjoint(jsonb,text,text,text)', 'EXECUTE')
             AND NOT has_function_privilege('authenticated', 'public.app_contact_creer_conjoint(jsonb,text,text,text)', 'EXECUTE')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 6, 'la porte MANDANT n''est pas touchee (empreinte du 31/10)',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), ''))
                 = '67e690fd235044e12b32c087c4273a45'
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
