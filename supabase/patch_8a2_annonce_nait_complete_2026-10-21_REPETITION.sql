-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE 8a PIÈCE 2 — le patch, l'essai réel de la création d'annonce,
-- puis l'inverse, et TOUT EST ANNULÉ à la fin                         21/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A COLLER EN ENTIER dans l'éditeur SQL Supabase. Il se termine VOLONTAIREMENT
-- par une erreur « ESSAI ANNULE -- … » : c'est elle qui annule tout. Recopier
-- ce message à Claude.
--
-- CE QU'IL JOUE : le VRAI patch (texte identique, généré depuis le fichier) ·
-- un VRAI appel de la création d'annonce, au nom du compte admin de Frédéric,
-- avec une saisie d'essai « ESSAI 8A2 » (interrupteur éteint, puis allumé) ·
-- le VRAI inverse.
-- ⚠ Une séquence ne revient pas en arrière : l'essai consomme 2 numéros
--   d'annonce de l'app (10000002 et 10000003 si personne ne crée entre-temps).
--   Un trou dans la série, rien de plus.
-- Aucun travail n'atteint le worker : rien n'est jamais validé (pas de COMMIT).
-- Fichier GÉNÉRÉ depuis le patch et l'inverse (gen_repetition_8a2.py) : ne pas
-- le retoucher à la main.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

create temp table _m (n int, cle text, valeur text) on commit drop;

-- 1. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('annonce_nait_complete', 'off',
        'Chantier 8 / 8a piece 2 21/10/2026 : on = une annonce creee dans l''app recoit tout de suite sa fiche detaillee de depart (voir supabase/patch_8a2_annonce_nait_complete_2026-10-21.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

-- 2. LA FONCTION NEUVE
create or replace function public.app_annonce_corps_de_naissance(p jsonb)
 returns jsonb
 language plpgsql
 stable
 set search_path to 'public'
as $f$
declare
  v_allume  boolean;
  wiz       jsonb := '{}'::jsonb;
  calque    jsonb;
  k         text;
  m         text;
  mots      text[] := '{}';
  vus       text[] := '{}';
  v_date    text := to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD HH24:MI:SS');
begin
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui')
    into v_allume
    from public.app_setting s
   where s.key = 'annonce_nait_complete';
  if not coalesce(v_allume, false) or p is null or jsonb_typeof(p) <> 'object' then
    return null;
  end if;

  -- les equipements : l'ecran les envoie DEJA aux noms de Hektor (App.tsx:16068-16086,
  -- niveaux, garages, jardin, piscine, exposition, vue y sont recopies avant l'envoi)
  if jsonb_typeof(p->'hektor_wizard_fields') = 'object' then
    for k in select jsonb_object_keys(p->'hektor_wizard_fields') loop
      if jsonb_typeof(p->'hektor_wizard_fields'->k) in ('string', 'number')
         and nullif(trim(p->'hektor_wizard_fields'->>k), '') is not null then
        wiz := wiz || jsonb_build_object(k, trim(p->'hektor_wizard_fields'->>k));
      end if;
    end loop;
  end if;

  -- les champs principaux, vers les noms que la fiche lit (wizardDetailValue, App.tsx:2651)
  calque := wiz || jsonb_strip_nulls(jsonb_build_object(
    'titre',          nullif(trim(coalesce(p->>'title', '')), ''),
    'corps',          nullif(trim(coalesce(p->>'description', '')), ''),
    'prix',           nullif(trim(coalesce(p->>'price', '')), ''),
    'PRIXNETVENDEUR', nullif(trim(coalesce(p->>'net_seller_price', '')), ''),
    'surfappart',     nullif(trim(coalesce(p->>'surface', p->>'living_surface', '')), ''),
    'nbpieces',       nullif(trim(coalesce(p->>'room_count', '')), ''),
    'NB_CHAMBRES',    nullif(trim(coalesce(p->>'bedroom_count', '')), ''),
    'adresse',        nullif(trim(coalesce(p->>'address', '')), ''),
    'codeprive',      nullif(trim(coalesce(p->>'postal_code', '')), ''),
    'villeprivee',    nullif(trim(coalesce(p->>'city', '')), ''),
    'codepublique',   nullif(trim(coalesce(p->>'postal_code', '')), ''),
    'villepublique',  nullif(trim(coalesce(p->>'city', '')), '')));

  -- le texte de recherche, comme build_search_text() du serveur : titre, ville, code
  -- postal, negociateur, agence ; chaque mot une seule fois (sans tenir compte de la casse)
  foreach m in array regexp_split_to_array(
      trim(concat_ws(' ', p->>'title', p->>'city', p->>'postal_code', p->>'hektor_user_label', p->>'agence_nom')),
      '\s+') loop
    if m <> '' and not (lower(m) = any(vus)) then
      vus  := vus  || lower(m);
      mots := mots || m;
    end if;
  end loop;

  return jsonb_build_object(
    'colonnes', jsonb_strip_nulls(jsonb_build_object(
      -- le TYPE est un CODE (« 2 » = appartement), jamais le libellé
      'type_bien',                   nullif(trim(coalesce(p->>'hektor_id_type', '')), ''),
      'adresse_detail',              nullif(trim(coalesce(p->>'address', '')), ''),
      'code_postal_prive_detail',    nullif(trim(coalesce(p->>'postal_code', '')), ''),
      'ville_privee_detail',         nullif(trim(coalesce(p->>'city', '')), ''),
      'date_enregistrement_annonce', v_date,
      'search_text',                 nullif(array_to_string(mots, ' '), ''))),
    'detail', jsonb_strip_nulls(jsonb_build_object(
      'surface',                     calque->>'surfappart',
      'nb_pieces',                   calque->>'nbpieces',
      'nb_chambres',                 calque->>'NB_CHAMBRES',
      'date_enregistrement_annonce', v_date))
      || jsonb_build_object(
      'app_optimistic_overlay', calque,
      -- la saisie telle quelle, pour qu'elle existe chez nous -- SANS le mandant
      -- (ses coordonnees vivent dans les contacts, pas dans la fiche du bien)
      'app_saisie_creation', p - 'creation_token' - 'initial_mandant'
                               - 'initial_mandant_contact_id' - 'initial_mandant_contact_label'));
end
$f$;

revoke all on function public.app_annonce_corps_de_naissance(jsonb) from public;
revoke all on function public.app_annonce_corps_de_naissance(jsonb) from anon;
revoke all on function public.app_annonce_corps_de_naissance(jsonb) from authenticated;
grant execute on function public.app_annonce_corps_de_naissance(jsonb) to service_role;

-- 3. LE BLOC, DANS LA CRÉATION
DO $patch$
DECLARE
    bloc text := $blk$
  -- === CHANTIER 8 / 8a piece 2 (21/10/2026) : L'ANNONCE NAIT COMPLETE ===
  -- La fiche qu'on vient de poser recoit aussi ce qui la rend TROUVABLE (texte de
  -- recherche, date d'enregistrement, type en code, adresse), et une fiche detaillee
  -- de depart : le calque que l'ecran lit en premier + la saisie telle quelle.
  -- La relecture de Hektor la remplacera par la sienne (~90 s).
  -- Interrupteur : app_setting 'annonce_nait_complete'. Eteint, la fonction
  -- app_annonce_corps_de_naissance rend NULL et ce bloc ne touche rien.
  -- Un echec ici ne doit JAMAIS empecher ni defaire la creation : bloc a part.
  begin
    update public.app_dossier_current d set
      type_bien                   = coalesce(n.c->'colonnes'->>'type_bien',                d.type_bien),
      adresse_detail              = coalesce(n.c->'colonnes'->>'adresse_detail',           d.adresse_detail),
      code_postal_prive_detail    = coalesce(n.c->'colonnes'->>'code_postal_prive_detail', d.code_postal_prive_detail),
      ville_privee_detail         = coalesce(n.c->'colonnes'->>'ville_privee_detail',      d.ville_privee_detail),
      date_enregistrement_annonce = coalesce(d.date_enregistrement_annonce, n.c->'colonnes'->>'date_enregistrement_annonce'),
      search_text                 = coalesce(n.c->'colonnes'->>'search_text',              d.search_text)
    from (select public.app_annonce_corps_de_naissance(draft_payload) as c) n
    where d.app_dossier_id = v_id
      and n.c is not null;

    insert into public.app_dossier_detail_current
      (app_dossier_id, hektor_annonce_id, source_updated_at, source_hash, detail_payload_json, refreshed_at)
    select v_id, null, null, 'c9e3:' || p_token::text, (n.c->'detail')::text, now()
      from (select public.app_annonce_corps_de_naissance(draft_payload) as c) n
     where n.c is not null
    on conflict (app_dossier_id) do nothing;
  exception when others then
    raise warning 'annonce_nait_complete : corps de naissance non pose pour % (%)', v_id, sqlerrm;
  end;
  -- === fin 8a piece 2 ===
$blk$;
    marque   text := 'CHANTIER 8 / 8a piece 2 (21/10/2026)';
    porte    text := 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)';
    attendue text := '3407a05cd7d1125b9320e468f4e0cf4f';
    ancre    text := $a$      'c9e3:' || p_token::text,
      now());
$a$;
    src      text;
    combien  int;
BEGIN
    bloc  := replace(bloc, chr(13), '');
    ancre := replace(ancre, chr(13), '');
    src   := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
    IF position(marque in src) > 0 THEN
        RAISE EXCEPTION '%', 'ARRET : le bloc 8a piece 2 est DEJA dans la creation d''annonce. Rien n''est ecrit.';
    END IF;
    IF md5(src) <> attendue THEN
        RAISE EXCEPTION '%', format('ARRET : la creation d''annonce a change depuis le 21/10 (empreinte %s, attendue %s). Rien n''est ecrit.',
                                    md5(src), attendue);
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois (1 attendue). Rien n''est ecrit.', combien);
    END IF;
    EXECUTE replace(src, ancre, ancre || bloc);
END
$patch$;


-- ── MESURES APRÈS LE PATCH ──────────────────────────────────────────────────
insert into _m values
 (1, 'empreinte_apres', md5(replace(pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure), chr(13), ''))),
 (2, 'interrupteur', (select value from public.app_setting where key = 'annonce_nait_complete')),
 (3, 'fonction_eteinte', coalesce(public.app_annonce_corps_de_naissance('{"title":"x"}'::jsonb)::text, 'NULL'));

-- ── L'ESSAI RÉEL DE LA CRÉATION ─────────────────────────────────────────────
DO $essai$
DECLARE
  v_uid     uuid;
  v_job     public.app_console_job;
  v_id      bigint;
  d         public.app_dossier_current%rowtype;
  j         jsonb;
  v_champs  jsonb := '{"titre_bien":"ESSAI 8A2 - ne pas diffuser","prix":"150000","ville":"Firminy","code_postal":"42700","type_bien":"Appartement","statut_annonce":"Estimation","commercial_nom":"Emmanuelle PEREIRA","negociateur_email":"pereira@gti-immobilier.fr","agence_nom":"Groupe GTI Firminy"}';
  v_saisie  jsonb := '{"title":"ESSAI 8A2 - ne pas diffuser","description":"Essai 8a2, annule.","price":"150000","net_seller_price":"142000","surface":"85","room_count":"4","bedroom_count":"3","address":"3 rue de l''Essai","postal_code":"42700","city":"Firminy","hektor_id_type":"2","property_type":"Appartement","status_label":"Estimation","statut_annonce":"1","creation_mode":"draft_only","creation_status":"estimation","offer_type":"sale","hektor_user_id":"51","hektor_user_email":"pereira@gti-immobilier.fr","hektor_user_label":"Emmanuelle PEREIRA","agence_nom":"Groupe GTI Firminy","requested_agence_nom":"Groupe GTI Firminy","hektor_negociator_form_id":"26","initial_mandant":{"last_name":"NE PAS COPIER","phone":"0600000009"},"initial_mandant_contact_label":"NE PAS COPIER","hektor_wizard_fields":{"CAVE":"OUI","BALCON":"OUI","NB_SDB":"1","dpe_cons":"180","dpe_ges":"30","ANNEE_CONS":"1975","VIDE":"","OBJET":{"x":1}}}';
  v_err     text := '';
  a_detail int; a_search text; a_type text; a_date text;
  b_detail int; b_search text; b_type text; b_date text; b_adr text; b_hash text;
  b_calque int; b_titre text; b_cave text; b_vide text; b_objet text; b_mandant text; b_pieces text; b_match text;
BEGIN
  select id into v_uid from public.app_user_profile
   where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1;
  if v_uid is null then raise exception 'ESSAI IMPOSSIBLE : compte admin de Frederic introuvable'; end if;
  perform set_config('request.jwt.claims', json_build_object('sub', v_uid::text, 'role', 'authenticated')::text, true);
  perform set_config('request.jwt.claim.sub', v_uid::text, true);

  -- A : interrupteur ETEINT -> exactement comme avant
  begin
    v_job := public.app_create_annonce_job_optimistic(gen_random_uuid(), v_champs, v_saisie, 18);
    v_id  := (v_job.payload_json->>'app_dossier_id')::bigint;
    select * into d from public.app_dossier_current where app_dossier_id = v_id;
    a_search := coalesce(d.search_text, 'NULL');
    a_type   := coalesce(d.type_bien, 'NULL');
    a_date   := coalesce(d.date_enregistrement_annonce, 'NULL');
    select count(*) into a_detail from public.app_dossier_detail_current where app_dossier_id = v_id;
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' A:' || sqlerrm; end if;
  end;

  update public.app_setting set value = 'on', updated_at = now() where key = 'annonce_nait_complete';

  -- B : interrupteur ALLUME
  begin
    v_job := public.app_create_annonce_job_optimistic(gen_random_uuid(), v_champs, v_saisie, 18);
    v_id  := (v_job.payload_json->>'app_dossier_id')::bigint;
    select * into d from public.app_dossier_current where app_dossier_id = v_id;
    b_search := coalesce(d.search_text, 'NULL');
    b_type   := coalesce(d.type_bien, 'NULL');
    b_date   := coalesce(d.date_enregistrement_annonce, 'NULL');
    b_adr    := coalesce(d.adresse_detail, 'NULL') || ' / ' || coalesce(d.code_postal_prive_detail, 'NULL') || ' / ' || coalesce(d.ville_privee_detail, 'NULL');
    select count(*) into b_detail from public.app_dossier_detail_current where app_dossier_id = v_id;
    select detail_payload_json::jsonb, source_hash into j, b_hash from public.app_dossier_detail_current where app_dossier_id = v_id;
    b_calque  := (select count(*) from jsonb_object_keys(coalesce(j->'app_optimistic_overlay', '{}'::jsonb)));
    b_titre   := coalesce(j->'app_optimistic_overlay'->>'titre', 'NULL');
    b_cave    := coalesce(j->'app_optimistic_overlay'->>'CAVE', 'NULL');
    b_vide    := case when j->'app_optimistic_overlay' ? 'VIDE' then 'PRESENT' else 'absent' end;
    b_objet   := case when j->'app_optimistic_overlay' ? 'OBJET' then 'PRESENT' else 'absent' end;
    b_mandant := case when (j->'app_saisie_creation') ? 'initial_mandant' or (j->'app_saisie_creation') ? 'initial_mandant_contact_label'
                      then 'PRESENT' else 'absent' end;
    b_pieces  := coalesce(j->>'surface', 'NULL') || ' m2 / ' || coalesce(j->>'nb_pieces', 'NULL') || ' p / ' || coalesce(j->>'nb_chambres', 'NULL') || ' ch';
    b_match   := coalesce(public.app_dossier_match_payload(v_id)::jsonb->>'nb_pieces', 'NULL');
    raise exception 'ANNULATION_INTERNE';
  exception when others then
    if sqlerrm <> 'ANNULATION_INTERNE' then v_err := v_err || ' B:' || sqlerrm; end if;
  end;

  insert into _m values
   (4,  'A_eteint_fiche_detaillee',   coalesce(a_detail::text, '?')),
   (5,  'A_eteint_texte_recherche',   coalesce(a_search, '?')),
   (6,  'A_eteint_type_date',         coalesce(a_type, '?') || ' / ' || coalesce(a_date, '?')),
   (7,  'B_allume_fiche_detaillee',   coalesce(b_detail::text, '?')),
   (8,  'B_texte_recherche',          coalesce(b_search, '?')),
   (9,  'B_type_et_date',             coalesce(b_type, '?') || ' / ' || coalesce(b_date, '?')),
   (10, 'B_adresse_cp_ville',         coalesce(b_adr, '?')),
   (11, 'B_empreinte_source',         coalesce(left(b_hash, 5), '?')),
   (12, 'B_calque_nb_champs',         coalesce(b_calque::text, '?')),
   (13, 'B_calque_titre_et_cave',     coalesce(b_titre, '?') || ' / ' || coalesce(b_cave, '?')),
   (14, 'B_calque_vide_et_objet',     coalesce(b_vide, '?') || ' / ' || coalesce(b_objet, '?')),
   (15, 'B_mandant_dans_la_saisie',   coalesce(b_mandant, '?')),
   (16, 'B_surface_pieces_chambres',  coalesce(b_pieces, '?')),
   (17, 'B_rapprochement_nb_pieces',  coalesce(b_match, '?')),
   (22, 'erreurs',                    coalesce(nullif(trim(v_err), ''), 'aucune'));
END
$essai$;

-- ── LE VRAI INVERSE ─────────────────────────────────────────────────────────
DO $inverse$
DECLARE
    bloc text := $blk$
  -- === CHANTIER 8 / 8a piece 2 (21/10/2026) : L'ANNONCE NAIT COMPLETE ===
  -- La fiche qu'on vient de poser recoit aussi ce qui la rend TROUVABLE (texte de
  -- recherche, date d'enregistrement, type en code, adresse), et une fiche detaillee
  -- de depart : le calque que l'ecran lit en premier + la saisie telle quelle.
  -- La relecture de Hektor la remplacera par la sienne (~90 s).
  -- Interrupteur : app_setting 'annonce_nait_complete'. Eteint, la fonction
  -- app_annonce_corps_de_naissance rend NULL et ce bloc ne touche rien.
  -- Un echec ici ne doit JAMAIS empecher ni defaire la creation : bloc a part.
  begin
    update public.app_dossier_current d set
      type_bien                   = coalesce(n.c->'colonnes'->>'type_bien',                d.type_bien),
      adresse_detail              = coalesce(n.c->'colonnes'->>'adresse_detail',           d.adresse_detail),
      code_postal_prive_detail    = coalesce(n.c->'colonnes'->>'code_postal_prive_detail', d.code_postal_prive_detail),
      ville_privee_detail         = coalesce(n.c->'colonnes'->>'ville_privee_detail',      d.ville_privee_detail),
      date_enregistrement_annonce = coalesce(d.date_enregistrement_annonce, n.c->'colonnes'->>'date_enregistrement_annonce'),
      search_text                 = coalesce(n.c->'colonnes'->>'search_text',              d.search_text)
    from (select public.app_annonce_corps_de_naissance(draft_payload) as c) n
    where d.app_dossier_id = v_id
      and n.c is not null;

    insert into public.app_dossier_detail_current
      (app_dossier_id, hektor_annonce_id, source_updated_at, source_hash, detail_payload_json, refreshed_at)
    select v_id, null, null, 'c9e3:' || p_token::text, (n.c->'detail')::text, now()
      from (select public.app_annonce_corps_de_naissance(draft_payload) as c) n
     where n.c is not null
    on conflict (app_dossier_id) do nothing;
  exception when others then
    raise warning 'annonce_nait_complete : corps de naissance non pose pour % (%)', v_id, sqlerrm;
  end;
  -- === fin 8a piece 2 ===
$blk$;
    marque   text := 'CHANTIER 8 / 8a piece 2 (21/10/2026)';
    porte    text := 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)';
    attendue text := '3407a05cd7d1125b9320e468f4e0cf4f';
    ancre    text := $a$      'c9e3:' || p_token::text,
      now());
$a$;
    src      text;
    retour   text;
BEGIN
    bloc  := replace(bloc, chr(13), '');
    ancre := replace(ancre, chr(13), '');
    src   := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
    IF position(marque in src) = 0 THEN
        RAISE NOTICE '%', 'Rien a retirer : le bloc 8a piece 2 n''est pas dans la creation d''annonce.';
    ELSE
        retour := replace(src, ancre || bloc, ancre);
        IF md5(retour) <> attendue THEN
            RAISE EXCEPTION '%', format('ARRET : sans le bloc, la creation d''annonce ne redonne PAS l''empreinte du 21/10 (%s au lieu de %s). Elle a change depuis le patch : rien n''est ecrit.',
                                        md5(retour), attendue);
        END IF;
        EXECUTE retour;
    END IF;
END
$inverse$;

drop function if exists public.app_annonce_corps_de_naissance(jsonb);
delete from public.app_setting where key = 'annonce_nait_complete';


-- ── MESURES APRÈS L'INVERSE ─────────────────────────────────────────────────
insert into _m values
 (18, 'empreinte_retour', md5(replace(pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure), chr(13), ''))),
 (19, 'fonction_retiree',    case when to_regprocedure('public.app_annonce_corps_de_naissance(jsonb)') is null then 'oui' else 'NON' end),
 (20, 'interrupteur_retire', case when not exists (select 1 from public.app_setting where key = 'annonce_nait_complete') then 'oui' else 'NON' end),
 (21, 'droits_creation',     case when has_function_privilege('authenticated', 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)', 'EXECUTE')
                                   and not has_function_privilege('anon', 'public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)', 'EXECUTE')
                                  then 'inchanges' else 'CHANGES' end);

-- ── L'ERREUR VOLONTAIRE QUI ANNULE TOUT ─────────────────────────────────────
DO $fin$
BEGIN
  RAISE EXCEPTION '%', (select 'ESSAI ANNULE -- ' || string_agg(lpad(n::text, 2, '0') || ' ' || cle || '=' || valeur, ' | ' order by n) from _m);
END
$fin$;

ROLLBACK;
