-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a — le patch, l'essai réel des deux portes, puis l'inverse,
-- et TOUT EST ANNULÉ à la fin                                         21/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A COLLER EN ENTIER dans l'éditeur SQL Supabase. Il se termine VOLONTAIREMENT
-- par une erreur « ESSAI ANNULE -- … » : c'est elle qui annule tout. Recopier
-- ce message à Claude.
--
-- CE QU'IL JOUE : le VRAI patch (texte identique, généré depuis le fichier) ·
-- un VRAI appel des deux portes, au nom du compte admin de Frédéric, sur un
-- contact d'essai « ESSAI 8A » (interrupteur éteint, puis allumé) · le VRAI inverse.
-- ⚠ Une séquence ne revient pas en arrière : l'essai consomme 3 numéros de
--   contact et 1 numéro de lien. Un trou dans la série, rien de plus.
-- Aucun travail n'atteint le worker : rien n'est jamais validé (pas de COMMIT).
-- Fichier GÉNÉRÉ depuis le patch et l'inverse (gen_repetition_8a.py) : ne pas
-- le retoucher à la main.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('contact_nait_complet', 'off',
        'Chantier 8 / 8a 21/10/2026 : on = un contact cree dans l''app recoit tout de suite les champs saisis qui ont une colonne (voir supabase/patch_8a_contact_nait_complet_2026-10-21.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION NEUVE
create or replace function public.app_contact_champs_naissance(p jsonb)
 returns jsonb
 language plpgsql
 stable
 set search_path to 'public'
as $f$
declare
  v_allume boolean;
  v_naiss  text;
  r        jsonb;
begin
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui')
    into v_allume
    from public.app_setting s
   where s.key = 'contact_nait_complet';
  if not coalesce(v_allume, false) or p is null or jsonb_typeof(p) <> 'object' then
    return null;
  end if;

  -- les noms que l'ecran donne a chaque champ (memes alias que app_edit_contact_optimistic)
  r := jsonb_strip_nulls(jsonb_build_object(
    'civilite',        nullif(trim(coalesce(p->>'civilite', p->>'civility', '')), ''),
    'phone_secondary', nullif(trim(coalesce(p->>'phone_secondary', p->>'telephone2', p->>'phoneSecondary', '')), ''),
    'adresse',         nullif(trim(coalesce(p->>'address', p->>'adresse', '')), ''),
    'code_postal',     nullif(trim(coalesce(p->>'postal_code', p->>'code_postal', '')), ''),
    'ville',           nullif(trim(coalesce(p->>'city', p->>'ville', '')), ''),
    'birth_place',     nullif(trim(coalesce(p->>'birth_place', '')), ''),
    'marital_status',  nullif(trim(coalesce(p->>'marital_status', '')), ''),
    'commentaires',    nullif(trim(coalesce(p->>'comments', p->>'commentaires', '')), '')));

  -- la date de naissance : l'ecran la saisit en texte libre « jj-mm-aaaa ».
  -- La base ne porte que de l'aaaa-mm-jj (261 sur 261 le 21/10). Une autre forme
  -- n'est PAS ecrite : Hektor ou le lecteur du formulaire la donneront.
  v_naiss := nullif(trim(coalesce(p->>'birth_date', '')), '');
  if v_naiss ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$' then
    r := r || jsonb_build_object('birth_date', v_naiss);
  elsif v_naiss ~ '^(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[0-2])[-/.][0-9]{4}$' then
    r := r || jsonb_build_object('birth_date',
           substr(v_naiss, 7, 4) || '-' || substr(v_naiss, 4, 2) || '-' || substr(v_naiss, 1, 2));
  end if;

  return r;
end
$f$;

-- ⚠ lecon du 13/10 : un « revoke from public » n'enleve pas un droit par defaut.
revoke all on function public.app_contact_champs_naissance(jsonb) from public;
revoke all on function public.app_contact_champs_naissance(jsonb) from anon;
revoke all on function public.app_contact_champs_naissance(jsonb) from authenticated;
grant execute on function public.app_contact_champs_naissance(jsonb) to service_role;

-- 3. LE BLOC, DANS LES DEUX PORTES
DO $patch$
DECLARE
    bloc text := $blk$
  -- === CHANTIER 8 / 8a (21/10/2026) : LE CONTACT NAIT COMPLET ===
  -- La ligne qu'on vient de poser recoit aussi ce que l'ecran a SAISI et qui a
  -- deja sa colonne (civilite, 2e telephone, adresse, code postal, ville,
  -- naissance, lieu, situation, commentaire). Hektor la remplacera par sa version
  -- a la relecture (~40 s) ; naissance, lieu et situation y sont reinjectes.
  -- Interrupteur : app_setting 'contact_nait_complet'. Eteint, la fonction
  -- app_contact_champs_naissance rend NULL et cette mise a jour ne touche rien.
  -- Un echec ici ne doit JAMAIS empecher ni defaire la creation : bloc a part.
  begin
    update public.app_contact_current c set
      civilite        = coalesce(n.v->>'civilite',        c.civilite),
      phone_secondary = coalesce(n.v->>'phone_secondary', c.phone_secondary),
      adresse         = coalesce(n.v->>'adresse',         c.adresse),
      code_postal     = coalesce(n.v->>'code_postal',     c.code_postal),
      ville           = coalesce(n.v->>'ville',           c.ville),
      birth_date      = coalesce(n.v->>'birth_date',      c.birth_date),
      birth_place     = coalesce(n.v->>'birth_place',     c.birth_place),
      marital_status  = coalesce(n.v->>'marital_status',  c.marital_status),
      commentaires    = coalesce(n.v->>'commentaires',    c.commentaires)
    from (select public.app_contact_champs_naissance(contact_payload) as v) n
    where c.hektor_contact_id = v_identite
      and n.v is not null;
  exception when others then
    raise warning 'contact_nait_complet : champs en plus non poses pour % (%)', v_identite, sqlerrm;
  end;
  -- === fin 8a ===
$blk$;
    marque  text := 'CHANTIER 8 / 8a (21/10/2026)';
    -- les deux portes : nom, signature, empreinte du 21/10, ancre
    portes  text[][] := array[
      array['public.app_create_contact_optimistic(jsonb,integer)',
            'f1563f572a8f2b4ea985e5f111144b37',
            $a1$    '[]'::jsonb, 'app_creation_' || v_identite, now());
$a1$],
      array['public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)',
            'e787461fd5efed34663e93ba5c92fea6',
            $a2$    on conflict (app_contact_id, hektor_annonce_id) do nothing;
  exception when others then
    null;
  end;
$a2$]];
    i       int;
    src     text;
    ancre   text;
    combien int;
BEGIN
    bloc := replace(bloc, chr(13), '');
    FOR i IN 1 .. array_length(portes, 1) LOOP
        src   := replace(pg_get_functiondef(portes[i][1]::regprocedure), chr(13), '');
        ancre := replace(portes[i][3], chr(13), '');
        IF position(marque in src) > 0 THEN
            RAISE EXCEPTION '%', format('ARRET : le bloc 8a est DEJA dans %s. Rien n''est ecrit.', portes[i][1]);
        END IF;
        IF md5(src) <> portes[i][2] THEN
            RAISE EXCEPTION '%', format('ARRET : %s a change depuis le 21/10 (empreinte %s, attendue %s). Rien n''est ecrit.',
                                        portes[i][1], md5(src), portes[i][2]);
        END IF;
        combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
        IF combien <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre de %s apparait %s fois (1 attendue). Rien n''est ecrit.',
                                        portes[i][1], combien);
        END IF;
        EXECUTE replace(src, ancre, ancre || bloc);
    END LOOP;
END
$patch$;


-- ── MESURES APRÈS LE PATCH ──────────────────────────────────────────────────
insert into _m values
 (1, 'empreinte_contact_apres', md5(replace(pg_get_functiondef('public.app_create_contact_optimistic(jsonb,integer)'::regprocedure), chr(13), ''))),
 (2, 'empreinte_mandant_apres', md5(replace(pg_get_functiondef('public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), ''))),
 (3, 'interrupteur', (select value from public.app_setting where key = 'contact_nait_complet')),
 (4, 'fonction_eteinte', coalesce(public.app_contact_champs_naissance('{"address":"x"}'::jsonb)::text, 'NULL'));

-- ── L'ESSAI RÉEL DES DEUX PORTES ────────────────────────────────────────────
DO $essai$
DECLARE
  v_uid     uuid;
  v_dossier bigint;
  v_annonce text;
  v_job     public.app_console_job;
  c         public.app_contact_current%rowtype;
  v_payload jsonb := '{"last_name":"ESSAI 8A","first_name":"Repetition","civilite":"M.","email":"essai.8a.21102026@example.invalid","phone":"0600000001","phone_secondary":"0600000002","address":"1 rue de l''Essai","postal_code":"42000","city":"SAINT-ETIENNE","birth_date":"21-09-1978","birth_place":"SAINT ETIENNE","marital_status":"married","comments":"essai 8a, annule","hektor_user_email":"frederic.gerphagnon@gti-immobilier.fr"}';
  v_mandant jsonb := '{"civilite":"Mme.","last_name":"ESSAI 8A MANDANT","first_name":"Repetition","email":"essai.8a.mandant.21102026@example.invalid","phone":"0600000003","address":"2 rue de l''Essai","postal_code":"42100","city":"SAINT-ETIENNE","hektor_user_email":"frederic.gerphagnon@gti-immobilier.fr"}';
  v_err     text := '';
  a_nom text; a_plus int; b_nom text; b_plus int; b_naiss text; m_plus int; m_lien int;
BEGIN
  select id into v_uid from public.app_user_profile
   where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1;
  if v_uid is null then raise exception 'ESSAI IMPOSSIBLE : compte admin de Frederic introuvable'; end if;
  perform set_config('request.jwt.claims', json_build_object('sub', v_uid::text, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_uid::text, true);

  -- A : interrupteur ETEINT -> exactement comme avant
  begin
    v_job := public.app_create_contact_optimistic(v_payload, 18);
    select * into c from public.app_contact_current where hektor_contact_id = v_job.payload_json->>'app_identite';
    a_nom  := c.nom;
    a_plus := (c.civilite is not null)::int + (c.phone_secondary is not null)::int + (c.adresse is not null)::int + (c.code_postal is not null)::int + (c.ville is not null)::int + (c.birth_date is not null)::int + (c.birth_place is not null)::int + (c.marital_status is not null)::int + (c.commentaires is not null)::int;
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' A:' || sqlerrm; end if;
  end;

  update public.app_setting set value = 'on', updated_at = now() where key = 'contact_nait_complet';

  -- B : interrupteur ALLUME, porte CONTACT
  begin
    v_job := public.app_create_contact_optimistic(v_payload, 18);
    select * into c from public.app_contact_current where hektor_contact_id = v_job.payload_json->>'app_identite';
    b_nom   := c.nom;
    b_plus  := (c.civilite is not null)::int + (c.phone_secondary is not null)::int + (c.adresse is not null)::int + (c.code_postal is not null)::int + (c.ville is not null)::int + (c.birth_date is not null)::int + (c.birth_place is not null)::int + (c.marital_status is not null)::int + (c.commentaires is not null)::int;
    b_naiss := c.birth_date;
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' B:' || sqlerrm; end if;
  end;

  -- C : interrupteur ALLUME, porte MANDANT (sur la premiere annonce active)
  select app_dossier_id, hektor_annonce_id::text into v_dossier, v_annonce
    from public.app_dossier_current
   where hektor_annonce_id is not null and statut_annonce = 'Actif'
   order by app_dossier_id limit 1;
  begin
    v_job := public.app_create_mandant_contact_optimistic(v_dossier, v_annonce, v_mandant, 18);
    select * into c from public.app_contact_current where hektor_contact_id = v_job.payload_json->>'app_identite';
    m_plus := (c.civilite is not null)::int + (c.adresse is not null)::int + (c.code_postal is not null)::int + (c.ville is not null)::int;
    select count(*) into m_lien from public.app_relation where app_contact_id = (v_job.payload_json->>'app_identite')::bigint;
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' C:' || sqlerrm; end if;
  end;

  insert into _m values
   (5,  'A_eteint_nom',             coalesce(a_nom, '?')),
   (6,  'A_eteint_champs_en_plus',  coalesce(a_plus::text, '?')),
   (7,  'B_allume_nom',             coalesce(b_nom, '?')),
   (8,  'B_allume_champs_en_plus',  coalesce(b_plus::text, '?')),
   (9,  'B_naissance',              coalesce(b_naiss, '?')),
   (10, 'C_mandant_champs_en_plus', coalesce(m_plus::text, '?')),
   (11, 'C_mandant_lien',           coalesce(m_lien::text, '?')),
   (12, 'D_date_inconnue_ecrite',   case when public.app_contact_champs_naissance('{"birth_date":"1978/21/09"}'::jsonb) ? 'birth_date' then 'OUI' else 'non' end),
   (17, 'erreurs',                  coalesce(nullif(trim(v_err), ''), 'aucune'));
END
$essai$;

-- ── LE VRAI INVERSE ─────────────────────────────────────────────────────────
DO $inverse$
DECLARE
    bloc text := $blk$
  -- === CHANTIER 8 / 8a (21/10/2026) : LE CONTACT NAIT COMPLET ===
  -- La ligne qu'on vient de poser recoit aussi ce que l'ecran a SAISI et qui a
  -- deja sa colonne (civilite, 2e telephone, adresse, code postal, ville,
  -- naissance, lieu, situation, commentaire). Hektor la remplacera par sa version
  -- a la relecture (~40 s) ; naissance, lieu et situation y sont reinjectes.
  -- Interrupteur : app_setting 'contact_nait_complet'. Eteint, la fonction
  -- app_contact_champs_naissance rend NULL et cette mise a jour ne touche rien.
  -- Un echec ici ne doit JAMAIS empecher ni defaire la creation : bloc a part.
  begin
    update public.app_contact_current c set
      civilite        = coalesce(n.v->>'civilite',        c.civilite),
      phone_secondary = coalesce(n.v->>'phone_secondary', c.phone_secondary),
      adresse         = coalesce(n.v->>'adresse',         c.adresse),
      code_postal     = coalesce(n.v->>'code_postal',     c.code_postal),
      ville           = coalesce(n.v->>'ville',           c.ville),
      birth_date      = coalesce(n.v->>'birth_date',      c.birth_date),
      birth_place     = coalesce(n.v->>'birth_place',     c.birth_place),
      marital_status  = coalesce(n.v->>'marital_status',  c.marital_status),
      commentaires    = coalesce(n.v->>'commentaires',    c.commentaires)
    from (select public.app_contact_champs_naissance(contact_payload) as v) n
    where c.hektor_contact_id = v_identite
      and n.v is not null;
  exception when others then
    raise warning 'contact_nait_complet : champs en plus non poses pour % (%)', v_identite, sqlerrm;
  end;
  -- === fin 8a ===
$blk$;
    marque  text := 'CHANTIER 8 / 8a (21/10/2026)';
    portes  text[][] := array[
      array['public.app_create_contact_optimistic(jsonb,integer)',
            'f1563f572a8f2b4ea985e5f111144b37',
            $a1$    '[]'::jsonb, 'app_creation_' || v_identite, now());
$a1$],
      array['public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)',
            'e787461fd5efed34663e93ba5c92fea6',
            $a2$    on conflict (app_contact_id, hektor_annonce_id) do nothing;
  exception when others then
    null;
  end;
$a2$]];
    i       int;
    src     text;
    ancre   text;
    retour  text;
BEGIN
    bloc := replace(bloc, chr(13), '');
    FOR i IN 1 .. array_length(portes, 1) LOOP
        src   := replace(pg_get_functiondef(portes[i][1]::regprocedure), chr(13), '');
        ancre := replace(portes[i][3], chr(13), '');
        IF position(marque in src) = 0 THEN
            RAISE NOTICE '%', format('Rien a retirer de %s : le bloc 8a n''y est pas.', portes[i][1]);
            CONTINUE;
        END IF;
        retour := replace(src, ancre || bloc, ancre);
        IF md5(retour) <> portes[i][2] THEN
            RAISE EXCEPTION '%', format('ARRET : sans le bloc, %s ne redonne PAS l''empreinte du 21/10 (%s au lieu de %s). Elle a change depuis le patch : rien n''est ecrit.',
                                        portes[i][1], md5(retour), portes[i][2]);
        END IF;
        EXECUTE retour;
    END LOOP;
END
$inverse$;

drop function if exists public.app_contact_champs_naissance(jsonb);
delete from public.app_setting where key = 'contact_nait_complet';


-- ── MESURES APRÈS L'INVERSE ─────────────────────────────────────────────────
insert into _m values
 (13, 'empreinte_contact_retour', md5(replace(pg_get_functiondef('public.app_create_contact_optimistic(jsonb,integer)'::regprocedure), chr(13), ''))),
 (14, 'empreinte_mandant_retour', md5(replace(pg_get_functiondef('public.app_create_mandant_contact_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), ''))),
 (15, 'fonction_retiree',    case when to_regprocedure('public.app_contact_champs_naissance(jsonb)') is null then 'oui' else 'NON' end),
 (16, 'interrupteur_retire', case when not exists (select 1 from public.app_setting where key = 'contact_nait_complet') then 'oui' else 'NON' end);

-- ── L'ERREUR VOLONTAIRE QUI ANNULE TOUT ─────────────────────────────────────
DO $fin$
BEGIN
  RAISE EXCEPTION '%', (select 'ESSAI ANNULE -- ' || string_agg(lpad(n::text, 2, '0') || ' ' || cle || '=' || valeur, ' | ' order by n) from _m);
END
$fin$;

ROLLBACK;
