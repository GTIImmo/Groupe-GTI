-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE « COUPLES · PIÈCE A » — le patch, l'essai réel de la porte, puis
-- l'inverse, et TOUT EST ANNULÉ à la fin                              31/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A COLLER EN ENTIER dans l'éditeur SQL Supabase. Il se termine VOLONTAIREMENT
-- par une erreur « ESSAI ANNULE -- … » : c'est elle qui annule tout.
--
-- CE QU'IL JOUE : le VRAI patch (texte identique, généré depuis le fichier) ·
-- un VRAI appel de la porte, au nom du compte admin de Frédéric, sur des contacts
-- d'essai fictifs (interrupteur éteint, puis allumé : couple, personne seule,
-- couple sans nom de conjoint) · le VRAI inverse.
-- ⚠ Une séquence ne revient pas en arrière : l'essai consomme quelques numéros de
--   contact. Un trou dans la série, rien de plus.
-- Aucun travail n'atteint le worker : rien n'est jamais validé (pas de COMMIT).
-- Fichier GÉNÉRÉ (gen_repetition_couple_a.py) : ne pas le retoucher à la main.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

insert into _m values
 (0, 'empreinte_contact_avant', md5(replace(pg_get_functiondef('public.app_create_contact_optimistic(jsonb,integer)'::regprocedure), chr(13), '')));

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

-- ── MESURES APRÈS LE PATCH ──────────────────────────────────────────────────
insert into _m values
 (1, 'empreinte_contact_apres', md5(replace(pg_get_functiondef('public.app_create_contact_optimistic(jsonb,integer)'::regprocedure), chr(13), ''))),
 (2, 'interrupteur', (select value from public.app_setting where key = 'couple_nait_complet')),
 (3, 'fonction_eteinte', coalesce(public.app_contact_creer_conjoint('{"person_type":"couple","spouse_last_name":"x"}'::jsonb, '1', null, null), 'NULL')),
 (4, 'mandant_intact', case when md5(replace(pg_get_functiondef('public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = '67e690fd235044e12b32c087c4273a45' then 'oui' else 'NON' end);

-- ── L'ESSAI RÉEL DE LA PORTE ────────────────────────────────────────────────
DO $essai$
DECLARE
  v_uid     uuid;
  v_job     public.app_console_job;
  c1        public.app_contact_current%rowtype;
  c2        public.app_contact_current%rowtype;
  v_couple  jsonb := '{"last_name":"ESSAI PAIRE","first_name":"Un","email":"essai.paire.un.31102026@example.invalid","phone":"0600000011","address":"1 rue de l''Essai","postal_code":"42000","city":"SAINT-ETIENNE","person_type":"couple","spouse_last_name":"ESSAI PAIRE","spouse_first_name":"Deux","spouse_email":"essai.paire.deux.31102026@example.invalid","spouse_phone":"0600000012","target_agency_label":"Compte formation","hektor_user_email":"frederic.gerphagnon@gti-immobilier.fr"}';
  v_seul    jsonb;
  v_sansnom jsonb;
  v_err     text := '';
  a_m2 text; a_lien text; a_lignes int;
  b_m2 text; b_lien1 text; b_lien2 text; b_role2 text; b_champs2 int; b_nom2 text; b_agence2 text; b_nego2 text; b_cible2 text; b_suite text;
  c_m2 text; c_lien text; d_m2 text;
BEGIN
  v_seul    := (v_couple - 'spouse_last_name' - 'spouse_first_name' - 'spouse_email' - 'spouse_phone') || '{"person_type":"personne_seule"}';
  v_sansnom := v_couple - 'spouse_last_name';

  select id into v_uid from public.app_user_profile
   where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1;
  if v_uid is null then raise exception 'ESSAI IMPOSSIBLE : compte admin de Frederic introuvable'; end if;
  perform set_config('request.jwt.claims', json_build_object('sub', v_uid::text, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_uid::text, true);

  -- A : interrupteur ETEINT, un couple -> exactement comme avant (une seule ligne)
  begin
    v_job := public.app_create_contact_optimistic(v_couple, 18);
    select * into c1 from public.app_contact_current where hektor_contact_id = v_job.payload_json->>'app_identite';
    a_m2    := coalesce(v_job.payload_json->>'app_identite_m2', 'absent');
    a_lien  := coalesce(c1.hektor_couple_contact_id, 'vide');
    select count(*) into a_lignes from public.app_contact_current where source_hash like 'app_creation_%' and email like 'essai.paire.%@example.invalid';
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' A:' || sqlerrm; end if;
  end;

  update public.app_setting set value = 'on', updated_at = now() where key = 'couple_nait_complet';

  -- B : interrupteur ALLUME, un couple -> deux lignes reliees
  begin
    v_job := public.app_create_contact_optimistic(v_couple, 18);
    select * into c1 from public.app_contact_current where hektor_contact_id = v_job.payload_json->>'app_identite';
    b_m2 := v_job.payload_json->>'app_identite_m2';
    select * into c2 from public.app_contact_current where hektor_contact_id = b_m2;
    b_lien1  := case when c1.hektor_couple_contact_id = c1.hektor_contact_id and c1.app_couple_contact_id = c1.hektor_contact_id::bigint then 'elle-meme' else coalesce(c1.hektor_couple_contact_id, 'vide') end;
    b_lien2  := case when c2.hektor_couple_contact_id = c1.hektor_contact_id and c2.app_couple_contact_id = c1.hektor_contact_id::bigint then 'la personne 1' else coalesce(c2.hektor_couple_contact_id, 'vide') end;
    b_role2  := coalesce(c2.couple_role, 'vide');
    b_nom2   := case when c2.nom = 'ESSAI PAIRE' and c2.prenom = 'Deux' and c2.display_name = 'Deux ESSAI PAIRE' then 'ok' else coalesce(c2.display_name, '?') end;
    b_champs2 := (c2.email = 'essai.paire.deux.31102026@example.invalid')::int + (c2.phone_primary = '0600000012')::int;
    b_agence2 := case when c2.agence_nom = 'Compte formation' then 'ok' else coalesce(c2.agence_nom, 'vide') end;
    b_nego2   := case when c2.negociateur_email = c1.negociateur_email then 'ok' else coalesce(c2.negociateur_email, 'vide') end;
    b_cible2  := coalesce(c2.hektor_target_id, 'vide');
    b_suite   := case when b_m2::bigint > c1.hektor_contact_id::bigint and b_m2::bigint >= 20000000 then 'oui' else 'NON' end;
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' B:' || sqlerrm; end if;
  end;

  -- C : interrupteur ALLUME, une personne seule -> rien ne change
  begin
    v_job := public.app_create_contact_optimistic(v_seul, 18);
    select * into c1 from public.app_contact_current where hektor_contact_id = v_job.payload_json->>'app_identite';
    c_m2   := coalesce(v_job.payload_json->>'app_identite_m2', 'absent');
    c_lien := coalesce(c1.hektor_couple_contact_id, 'vide');
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' C:' || sqlerrm; end if;
  end;

  -- D : interrupteur ALLUME, couple SANS nom de conjoint -> pas de personne 2
  begin
    v_job := public.app_create_contact_optimistic(v_sansnom, 18);
    d_m2 := coalesce(v_job.payload_json->>'app_identite_m2', 'absent');
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' D:' || sqlerrm; end if;
  end;

  insert into _m values
   (5,  'A_eteint_m2_dans_la_charge',  coalesce(a_m2, '?')),
   (6,  'A_eteint_lien_personne1',     coalesce(a_lien, '?')),
   (7,  'A_eteint_lignes_essai',       coalesce(a_lignes::text, '?')),
   (8,  'B_m2_dans_la_charge',         case when b_m2 is null then 'ABSENT' else 'present' end),
   (9,  'B_numero_m2_suit_et_plage',   coalesce(b_suite, '?')),
   (10, 'B_lien_personne1',            coalesce(b_lien1, '?')),
   (11, 'B_lien_personne2',            coalesce(b_lien2, '?')),
   (12, 'B_role_personne2',            coalesce(b_role2, '?')),
   (13, 'B_nom_personne2',             coalesce(b_nom2, '?')),
   (14, 'B_mail_et_tel_personne2_sur2', coalesce(b_champs2::text, '?')),
   (15, 'B_agence_personne2',          coalesce(b_agence2, '?')),
   (16, 'B_negociateur_personne2',     coalesce(b_nego2, '?')),
   (17, 'B_cible_personne2',           coalesce(b_cible2, '?')),
   (18, 'C_seule_m2',                  coalesce(c_m2, '?')),
   (19, 'C_seule_lien',                coalesce(c_lien, '?')),
   (20, 'D_sans_nom_m2',               coalesce(d_m2, '?')),
   (25, 'erreurs',                     coalesce(nullif(trim(v_err), ''), 'aucune'));
END
$essai$;

-- ── LE VRAI INVERSE ─────────────────────────────────────────────────────────
DO $inverse$
DECLARE
    porte   text := 'public.app_create_contact_optimistic(jsonb,integer)';
    empreinte text := '95fde3280af1dff65ab45596f4b3bead';
    marque  text := 'COUPLES · LA PAIRE (31/10/2026)';
    a_decl  text := $a1$  v_identite     text;
$a1$;
    n_decl  text := $n1$  v_identite_m2  text;
$n1$;
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
    a_job   text := $a3$          'creation_mode', coalesce(nullif(trim(contact_payload->>'creation_mode'), ''), 'contact_global_identity')),
$a3$;
    n_job   text := $n3$          'creation_mode', coalesce(nullif(trim(contact_payload->>'creation_mode'), ''), 'contact_global_identity'))
          -- COUPLES · LA PAIRE (31/10) : le numero de la personne 2, seulement s'il existe
          || case when v_identite_m2 is not null
                  then jsonb_build_object('app_identite_m2', v_identite_m2)
                  else '{}'::jsonb end,
$n3$;
    src     text;
    retour  text;
BEGIN
    src    := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
    a_decl := replace(a_decl, chr(13), '');  n_decl := replace(n_decl, chr(13), '');
    a_bloc := replace(a_bloc, chr(13), '');  n_bloc := replace(n_bloc, chr(13), '');
    a_job  := replace(a_job,  chr(13), '');  n_job  := replace(n_job,  chr(13), '');

    IF position(marque in src) = 0 THEN
        RAISE NOTICE '%', format('Rien a retirer de %s : le bloc des couples n''y est pas.', porte);
    ELSE
        retour := replace(src, a_decl || n_decl, a_decl);
        retour := replace(retour, a_bloc || n_bloc, a_bloc);
        retour := replace(retour, n_job, a_job);
        IF md5(retour) <> empreinte THEN
            RAISE EXCEPTION '%', format('ARRET : sans les ajouts, %s ne redonne PAS l''empreinte du 31/10 (%s au lieu de %s). Elle a change depuis le patch : rien n''est ecrit.',
                                        porte, md5(retour), empreinte);
        END IF;
        EXECUTE retour;
    END IF;
END
$inverse$;

drop function if exists public.app_contact_creer_conjoint(jsonb, text, text, text);
delete from public.app_setting where key = 'couple_nait_complet';

-- ── MESURES APRÈS L'INVERSE ─────────────────────────────────────────────────
insert into _m values
 (21, 'empreinte_contact_retour', md5(replace(pg_get_functiondef('public.app_create_contact_optimistic(jsonb,integer)'::regprocedure), chr(13), ''))),
 (22, 'retour_egal_avant', case when (select valeur from _m where n = 0) = md5(replace(pg_get_functiondef('public.app_create_contact_optimistic(jsonb,integer)'::regprocedure), chr(13), '')) then 'oui' else 'NON' end),
 (23, 'fonction_retiree',    case when to_regprocedure('public.app_contact_creer_conjoint(jsonb,text,text,text)') is null then 'oui' else 'NON' end),
 (24, 'interrupteur_retire', case when not exists (select 1 from public.app_setting where key = 'couple_nait_complet') then 'oui' else 'NON' end);

-- ── L'ERREUR VOLONTAIRE QUI ANNULE TOUT ─────────────────────────────────────
DO $fin$
BEGIN
  RAISE EXCEPTION '%', (select 'ESSAI ANNULE -- ' || string_agg(lpad(n::text, 2, '0') || ' ' || cle || '=' || valeur, ' | ' order by n) from _m);
END
$fin$;

ROLLBACK;
