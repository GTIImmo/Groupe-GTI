-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE G — « AJOUTER UN CONJOINT » À UNE PERSONNE SEULE          03/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER avec l'accord de Frédéric, APRÈS la répétition. Note : synthèse couples §52-53.
--
-- LE GESTE (décisions de Frédéric, 03/11) : sur la fiche d'une personne seule, lui donner un conjoint --
--   (a) un NOUVEAU contact (créé d'abord par la création habituelle) OU une FICHE EXISTANTE de l'annuaire ;
--   (b) admins ET négociateurs, derrière un cran ; (c) le conjoint reçoit LES MÊMES BIENS que la personne.
--   Chez Hektor : UNE requête, `contacts-create-transformeContactToConjunct` (conjoint, refCouple), prouvée
--   le 02/11 sur 3 fiches fictives et sur le vrai cas EA32621 (synthèse §36, §39).
--
-- CE QUE FAIT CE PATCH — ADDITIF :
--   1. un CRAN neuf, app_setting 'contacts_couples_ajout', posé à 'off' ('admin' = admins seuls, 'on' = tous) ;
--   2. le type de travail `link_hektor_conjoint` aux TROIS verrous (mémoire « nouveau type de travail ») :
--      la contrainte de app_console_job, les droits (app_console_can_request_contact_job, même règle que
--      la modification d'un contact), et la DISTRIBUTION (app_console_claim_next_job, service `actions`) ;
--   3. app_ajouter_conjoint_optimistic(personne, conjoint) -- pour l'écran : vérifie, écrit le couple CHEZ
--      NOUS À LA SECONDE (photo d'avant gardée dans la charge), choisit les biens à relier (ceux où la
--      personne est mandant ou propriétaire, bien vivant, droit du demandeur vérifié bien par bien), et pose
--      le travail ;
--   4. app_conjoint_relier_biens(travail) -- pour le worker, APRÈS le lien prouvé chez Hektor : pose, pour
--      chaque bien retenu, ce que pose un rattachement de mandant (travail `link_hektor_mandant`, ligne
--      provisoire, ligne du registre, type recalculé) ;
--   5. app_conjoint_annuler_optimiste(travail) -- pour le worker, si Hektor refuse : remet les deux fiches
--      comme avant, SEULEMENT si elles portent encore ce que le geste avait écrit.
--
-- CE QU'IL NE FAIT PAS : il ne touche ni la création d'un contact, ni « Modifier / Compléter le conjoint »,
--   ni la nuit. Les 680 coquilles ne passent PAS par cette fonction (une coquille n'est pas une personne
--   seule) : elles auront leur propre porte, le même travail.
--
-- ⛔ GARDES : chaque fonction existante n'est modifiée que si son empreinte est celle relevée le 03/11, et
--    chaque ancre (sur UNE ligne, leçon 30) n'y apparaît qu'UNE fois. Sinon : ARRÊT, rien n'est écrit.
-- ALLUMER (admins) : update public.app_setting set value = 'admin', updated_at = now() where key = 'contacts_couples_ajout';
-- RETOUR ARRIÈRE : supabase/patch_couple_phase3g_ajouter_conjoint_2026-11-03_INVERSE.sql
-- RÉPÉTITION JOUÉE le 03/11 (transaction annulée, admin simulé, 3 fiches fictives, bien d'essai 63331) : 10/10 vertes, rien n'est resté.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '5s';

-- 0. LES GARDES
DO $garde$
BEGIN
  IF md5(replace(pg_get_functiondef('public.app_console_claim_next_job(text,text)'::regprocedure), chr(13), '')) <> 'ce7d7a76dc307b2e4e72801133b525c8' THEN
    RAISE EXCEPTION 'ARRET : app_console_claim_next_job a change depuis le 03/11. Rien n''est ecrit.';
  END IF;
  IF md5(replace(pg_get_functiondef('public.app_console_can_request_contact_job(text,text,text)'::regprocedure), chr(13), '')) <> '19d0fc0b1f4f22b0a91a05809ebe94bb' THEN
    RAISE EXCEPTION 'ARRET : app_console_can_request_contact_job a change depuis le 03/11. Rien n''est ecrit.';
  END IF;
  IF md5((SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'app_console_job_job_type_check')) <> 'fe19373481b1a68edc273d3a276643c7' THEN
    RAISE EXCEPTION 'ARRET : la contrainte app_console_job_job_type_check a change depuis le 03/11. Rien n''est ecrit.';
  END IF;
  IF to_regprocedure('public.app_ajouter_conjoint_optimistic(text,text,integer)') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRET : app_ajouter_conjoint_optimistic existe deja. Rien n''est ecrit.';
  END IF;
END
$garde$;

-- 1. LE CRAN, FERMÉ
insert into public.app_setting (key, value, description, updated_at)
values ('contacts_couples_ajout', 'off',
        'Couples 03/11/2026 : « Ajouter un conjoint » sur une personne seule. off = invisible et refuse ; admin = admins seuls ; on = tous (avec le droit de gerer le contact). Voir supabase/patch_couple_phase3g_ajouter_conjoint_2026-11-03.sql.',
        now())
on conflict (key) do nothing;

-- 2a. LA CONTRAINTE : le type neuf s'ajoute à la fin de la liste, rien d'autre ne bouge.
DO $contrainte$
DECLARE
  def   text := (SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'app_console_job_job_type_check');
  ancre text := '''youtrust_signing_link''::text]';
BEGIN
  IF (length(def) - length(replace(def, ancre, ''))) / length(ancre) <> 1 THEN
    RAISE EXCEPTION 'ARRET : ancre de la contrainte introuvable ou multiple. Rien n''est ecrit.';
  END IF;
  def := replace(def, ancre, '''youtrust_signing_link''::text, ''link_hektor_conjoint''::text]');
  EXECUTE 'alter table public.app_console_job drop constraint app_console_job_job_type_check, add constraint app_console_job_job_type_check ' || def;
END
$contrainte$;

-- 2b. LA DISTRIBUTION : service `actions`, à côté des autres gestes contact.
DO $distribution$
DECLARE
  porte text := 'public.app_console_claim_next_job(text,text)';
  ancre text := $a$'unlink_hektor_mandant','archive_hektor_contact'))$a$;
  neuf  text := $n$'unlink_hektor_mandant','archive_hektor_contact',
                    -- COUPLES 03/11/2026 : « Ajouter un conjoint ». Sans cette ligne, le travail reste « pending » a vie.
                    'link_hektor_conjoint'))$n$;
  src   text;
BEGIN
  src := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
  neuf := replace(neuf, chr(13), '');
  IF (length(src) - length(replace(src, ancre, ''))) / length(ancre) <> 1 THEN
    RAISE EXCEPTION 'ARRET : ancre de la distribution introuvable ou multiple. Rien n''est ecrit.';
  END IF;
  EXECUTE replace(src, ancre, neuf);
END
$distribution$;

-- 2c. LES DROITS : la même règle que la modification d'un contact (admin/manager oui ; un négociateur
--     sur un contact qu'il voit par son négociateur ou par un bien de son périmètre).
DO $droits$
DECLARE
  porte text := 'public.app_console_can_request_contact_job(text,text,text)';
  ancre text := $a$'delete_hektor_contact_search','archive_hektor_contact')$a$;
  neuf  text := $n$'delete_hektor_contact_search','archive_hektor_contact','link_hektor_conjoint')$n$;
  src   text;
BEGIN
  src := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
  IF (length(src) - length(replace(src, ancre, ''))) / length(ancre) <> 1 THEN
    RAISE EXCEPTION 'ARRET : ancre des droits introuvable ou multiple. Rien n''est ecrit.';
  END IF;
  EXECUTE replace(src, ancre, neuf);
END
$droits$;

-- 3. LA PORTE DE L'ÉCRAN
create or replace function public.app_ajouter_conjoint_optimistic(
    target_contact_id text, conjoint_contact_id text, job_priority integer default 25)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  p          app_contact_current%rowtype;
  c          app_contact_current%rowtype;
  v_cran     text;
  v_role     text;
  v_biens    jsonb := '[]'::jsonb;
  v_refuses  int := 0;
  v_avant    jsonb;
  v_job      app_console_job;
  b          record;
  v_p        text := nullif(trim(coalesce(target_contact_id, '')), '');
  v_c        text := nullif(trim(coalesce(conjoint_contact_id, '')), '');
begin
  -- le cran
  select lower(trim(coalesce(s.value, ''))) into v_cran from app_setting s where s.key = 'contacts_couples_ajout';
  v_role := public.app_console_current_role();
  if coalesce(v_cran, 'off') not in ('on', 'true', '1', 'yes', 'admin')
     or (v_cran = 'admin' and coalesce(v_role, '') <> 'admin') then
    return jsonb_build_object('ok', false, 'raison', 'cran_ferme');
  end if;

  if v_p is null or v_c is null or v_p !~ '^[0-9]+$' or v_c !~ '^[0-9]+$' then
    raise exception 'invalid_contact_id' using errcode = '22023';
  end if;
  if v_p = v_c then
    return jsonb_build_object('ok', false, 'raison', 'meme_fiche');
  end if;

  select * into p from app_contact_current where hektor_contact_id = v_p;
  if not found then raise exception 'contact_not_found' using errcode = '22023'; end if;
  select * into c from app_contact_current where hektor_contact_id = v_c;
  if not found then return jsonb_build_object('ok', false, 'raison', 'conjoint_introuvable'); end if;

  -- les droits : sur la personne ET sur la fiche choisie
  if not public.app_console_can_request_contact_job('link_hektor_conjoint', p.hektor_contact_id, p.negociateur_email) then
    raise exception 'forbidden_link_conjoint' using errcode = '42501';
  end if;
  if not public.app_console_can_request_contact_job('link_hektor_conjoint', c.hektor_contact_id, c.negociateur_email) then
    raise exception 'forbidden_link_conjoint_fiche' using errcode = '42501';
  end if;

  -- ce qu'on refuse, et pourquoi (l'écran le dit tel quel)
  if coalesce(p.archive, false) then return jsonb_build_object('ok', false, 'raison', 'personne_archivee'); end if;
  if coalesce(c.archive, false) then return jsonb_build_object('ok', false, 'raison', 'conjoint_archive'); end if;
  if coalesce(p.nature_fiche, '') = 'notaire' or coalesce(c.nature_fiche, '') = 'notaire'
     or coalesce(p.relation_roles_json::text, '') ~ 'notaire_(vendeur|acquereur)'
     or coalesce(c.relation_roles_json::text, '') ~ 'notaire_(vendeur|acquereur)' then
    return jsonb_build_object('ok', false, 'raison', 'notaire');
  end if;
  if coalesce(p.nature_fiche, '') in ('case_conjoint_vide', 'case_vide_orpheline', 'conjoint', 'conjoint_sans_prenom') then
    return jsonb_build_object('ok', false, 'raison', 'personne_pas_seule');
  end if;
  if coalesce(c.nature_fiche, '') in ('case_conjoint_vide', 'case_vide_orpheline', 'conjoint', 'conjoint_sans_prenom') then
    return jsonb_build_object('ok', false, 'raison', 'conjoint_pas_seul');
  end if;
  if coalesce(nullif(p.couple_json->>'etat', ''), 'aucun') <> 'aucun'
     or (p.hektor_couple_contact_id is not null and p.hektor_couple_contact_id <> p.hektor_contact_id)
     or exists (select 1 from app_contact_current x
                 where x.hektor_couple_contact_id = p.hektor_contact_id and x.hektor_contact_id <> p.hektor_contact_id) then
    return jsonb_build_object('ok', false, 'raison', 'personne_deja_en_couple');
  end if;
  if coalesce(nullif(c.couple_json->>'etat', ''), 'aucun') <> 'aucun'
     or (c.hektor_couple_contact_id is not null and c.hektor_couple_contact_id <> c.hektor_contact_id)
     or exists (select 1 from app_contact_current x
                 where x.hektor_couple_contact_id = c.hektor_contact_id and x.hektor_contact_id <> c.hektor_contact_id) then
    return jsonb_build_object('ok', false, 'raison', 'conjoint_deja_en_couple');
  end if;
  if p.hektor_target_id is null then
    return jsonb_build_object('ok', false, 'raison', 'personne_sans_numero_hektor');
  end if;
  -- Un conjoint NOUVEAU n'a pas encore son numéro Hektor : c'est permis SEULEMENT si sa création est en file
  -- (le worker l'attend). Une fiche de l'app sans numéro et sans création en cours ne peut pas être visée.
  if c.hektor_target_id is null and not exists (
       select 1 from app_console_job j
        where j.job_type = 'create_hektor_contact' and j.status in ('pending', 'running')
          and j.payload_json->>'app_identite' = c.hektor_contact_id) then
    return jsonb_build_object('ok', false, 'raison', 'conjoint_sans_numero_hektor');
  end if;
  if exists (select 1 from app_console_job j
              where j.job_type = 'link_hektor_conjoint' and j.status in ('pending', 'running')
                and (j.payload_json->>'hektor_contact_id' in (v_p, v_c) or j.payload_json->>'conjoint_id' in (v_p, v_c))) then
    return jsonb_build_object('ok', false, 'raison', 'deja_en_cours');
  end if;

  -- la photo d'avant : ce que le retour arrière du worker remettra
  v_avant := jsonb_build_object(
    'principal', jsonb_build_object('hektor_couple_contact_id', p.hektor_couple_contact_id, 'app_couple_contact_id', p.app_couple_contact_id,
                                    'couple_role', p.couple_role, 'couple_json', p.couple_json, 'nature_fiche', p.nature_fiche,
                                    'couple_deuxieme', p.couple_deuxieme),
    'conjoint',  jsonb_build_object('hektor_couple_contact_id', c.hektor_couple_contact_id, 'app_couple_contact_id', c.app_couple_contact_id,
                                    'couple_role', c.couple_role, 'couple_json', c.couple_json, 'nature_fiche', c.nature_fiche,
                                    'couple_deuxieme', c.couple_deuxieme));

  -- les biens à relier : ceux où la personne est mandant ou propriétaire (pas une marque d'acheteur ni de vente),
  -- bien VIVANT, que le conjoint n'a pas déjà ; le droit du demandeur vérifié bien par bien
  for b in
    select distinct rel.app_dossier_id, rel.hektor_annonce_id
      from app_relation rel
      join app_dossier_current d on d.app_dossier_id = rel.app_dossier_id
     where rel.app_contact_id = p.hektor_contact_id::bigint
       and rel.retire_le is null
       and rel.fait = 'proprietaire_du_bien'
       and coalesce(rel.origine, '') not in ('acheteur', 'vente')
       and not exists (select 1 from app_relation x
                        where x.app_contact_id = c.hektor_contact_id::bigint
                          and x.hektor_annonce_id = rel.hektor_annonce_id and x.retire_le is null)
  loop
    if public.app_console_can_request_job('link_hektor_mandant', b.app_dossier_id, b.hektor_annonce_id) then
      v_biens := v_biens || jsonb_build_array(jsonb_build_object('app_dossier_id', b.app_dossier_id, 'hektor_annonce_id', b.hektor_annonce_id));
    else
      v_refuses := v_refuses + 1;
    end if;
  end loop;

  -- CHEZ NOUS, À LA SECONDE : le couple comme la nuit le range (porteuse -> elle-même, conjoint -> la porteuse)
  update app_contact_current
     set hektor_couple_contact_id = p.hektor_contact_id,
         app_couple_contact_id    = p.hektor_contact_id::bigint,
         couple_role              = 'conjoint',
         nature_fiche             = 'conjoint'
   where hektor_contact_id = c.hektor_contact_id;
  update app_contact_current
     set hektor_couple_contact_id = p.hektor_contact_id,
         app_couple_contact_id    = p.hektor_contact_id::bigint,
         nature_fiche             = 'couple',
         couple_deuxieme          = case when nullif(trim(coalesce(c.prenom, '')), '') is not null
                                         then 'conjoint_avec_prenom' else 'nom_recopie' end,
         couple_json = jsonb_build_object('etat', 'nomme', 'autres', 0, 'conjoint', jsonb_build_object(
                         'id', c.hektor_contact_id, 'nom', c.nom, 'prenom', c.prenom, 'email', c.email,
                         'telephone', c.phone_primary, 'civilite', c.civilite, 'archive', false, 'envoye', true,
                         'hektor_id', c.hektor_target_id))
   where hektor_contact_id = p.hektor_contact_id;

  insert into app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json, status, priority, requested_by, requested_at)
  values ('link_hektor_conjoint', null, null,
          jsonb_build_object(
            'hektor_contact_id', p.hektor_contact_id,
            'conjoint_id',       c.hektor_contact_id,
            'contact_label',     nullif(trim(coalesce(p.display_name, '')), ''),
            'conjoint_label',    nullif(trim(coalesce(c.display_name, '')), ''),
            'avant',             v_avant,
            'biens',             v_biens,
            'biens_refuses',     v_refuses),
          'pending', coalesce(job_priority, 25), auth.uid(), now())
  returning * into v_job;

  return jsonb_build_object('ok', true, 'job_id', v_job.id, 'conjoint', c.hektor_contact_id,
                            'biens', jsonb_array_length(v_biens), 'biens_refuses', v_refuses);
end
$function$;

revoke all on function public.app_ajouter_conjoint_optimistic(text, text, integer) from public;
revoke all on function public.app_ajouter_conjoint_optimistic(text, text, integer) from anon;
grant execute on function public.app_ajouter_conjoint_optimistic(text, text, integer) to authenticated, service_role;

-- 4. LES BIENS, APRÈS LE LIEN PROUVÉ (worker seulement)
--    Même écriture qu'un rattachement de mandant (app_link_mandant_optimistic), pour le demandeur d'origine :
--    ses droits ont été vérifiés bien par bien au clic.
create or replace function public.app_conjoint_relier_biens(p_job_id uuid)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  j          app_console_job%rowtype;
  v_c        text;
  v_label    text;
  v_hektor_c text;
  v_token    uuid;
  v_poses    int := 0;
  v_deja     int := 0;
  b          jsonb;
  v_ann      text;
  v_dos      bigint;
begin
  select * into j from app_console_job where id = p_job_id and job_type = 'link_hektor_conjoint';
  if not found then return jsonb_build_object('ok', false, 'raison', 'travail_introuvable'); end if;
  v_c := j.payload_json->>'conjoint_id';
  select nullif(trim(coalesce(display_name, '')), ''), hektor_target_id into v_label, v_hektor_c
    from app_contact_current where hektor_contact_id = v_c;

  for b in select * from jsonb_array_elements(coalesce(j.payload_json->'biens', '[]'::jsonb))
  loop
    v_ann := b->>'hektor_annonce_id';
    v_dos := (b->>'app_dossier_id')::bigint;
    if exists (select 1 from app_relation x where x.app_contact_id = v_c::bigint and x.hektor_annonce_id = v_ann and x.retire_le is null) then
      v_deja := v_deja + 1;
      continue;
    end if;
    v_token := gen_random_uuid();
    insert into app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json, status, priority, requested_by, requested_at)
    values ('link_hektor_mandant', v_dos, v_ann,
            jsonb_build_object('contact_id', v_c, 'contact_label', v_label, 'creation_token', v_token,
                               'parent_job_id', j.id, 'raison', 'ajouter_conjoint'),
            'pending', 18, j.requested_by, now());
    begin
      insert into app_relation_provisional
        (creation_token, hektor_annonce_id, app_dossier_id, hektor_contact_id, contact_label, role_contact, status, created_by)
      values (v_token, v_ann, v_dos, v_c, v_label, 'mandant', 'pending', j.requested_by::text);
    exception when others then null;
    end;
    begin
      insert into app_relation
        (app_relation_id, app_contact_id, app_dossier_id, hektor_annonce_id, hektor_contact_id, fait, role_hektor,
         source, relation_key, first_seen_at, last_seen_at, present_in_hektor, absent_depuis)
      values (nextval('public.app_relation_id_app_seq'), v_c::bigint, v_dos, v_ann, v_hektor_c,
              'proprietaire_du_bien', null, 'app', 'app:' || v_token::text, now()::text, now()::text, false, null)
      on conflict (app_contact_id, hektor_annonce_id) do update set retire_le = null, retire_par = null, absent_depuis = null;
    exception when others then null;
    end;
    begin
      perform public.app_recalculer_type_du_bien(v_ann, v_dos);
    exception when others then null;
    end;
    v_poses := v_poses + 1;
  end loop;
  return jsonb_build_object('ok', true, 'poses', v_poses, 'deja', v_deja);
end
$function$;

revoke all on function public.app_conjoint_relier_biens(uuid) from public;
revoke all on function public.app_conjoint_relier_biens(uuid) from anon;
revoke all on function public.app_conjoint_relier_biens(uuid) from authenticated;
grant execute on function public.app_conjoint_relier_biens(uuid) to service_role;

-- 5. LE RETOUR ARRIÈRE CHEZ NOUS, SI HEKTOR REFUSE (worker seulement)
--    On ne remet une fiche que si elle porte ENCORE ce que le geste a écrit : jamais on n'écrase une relecture.
create or replace function public.app_conjoint_annuler_optimiste(p_job_id uuid)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  j   app_console_job%rowtype;
  v_p text;
  v_c text;
  a   jsonb;
  n_p int := 0;
  n_c int := 0;
begin
  select * into j from app_console_job where id = p_job_id and job_type = 'link_hektor_conjoint';
  if not found then return jsonb_build_object('ok', false, 'raison', 'travail_introuvable'); end if;
  v_p := j.payload_json->>'hektor_contact_id';
  v_c := j.payload_json->>'conjoint_id';
  a := j.payload_json->'avant';

  update app_contact_current set
    hektor_couple_contact_id = a->'principal'->>'hektor_couple_contact_id',
    app_couple_contact_id    = (a->'principal'->>'app_couple_contact_id')::bigint,
    couple_role              = a->'principal'->>'couple_role',
    couple_json              = case when jsonb_typeof(a->'principal'->'couple_json') = 'null' then null else a->'principal'->'couple_json' end,
    nature_fiche             = a->'principal'->>'nature_fiche',
    couple_deuxieme          = a->'principal'->>'couple_deuxieme'
  where hektor_contact_id = v_p
    and couple_json->'conjoint'->>'id' = v_c;
  get diagnostics n_p = row_count;

  update app_contact_current set
    hektor_couple_contact_id = a->'conjoint'->>'hektor_couple_contact_id',
    app_couple_contact_id    = (a->'conjoint'->>'app_couple_contact_id')::bigint,
    couple_role              = a->'conjoint'->>'couple_role',
    couple_json              = case when jsonb_typeof(a->'conjoint'->'couple_json') = 'null' then null else a->'conjoint'->'couple_json' end,
    nature_fiche             = a->'conjoint'->>'nature_fiche',
    couple_deuxieme          = a->'conjoint'->>'couple_deuxieme'
  where hektor_contact_id = v_c
    and hektor_couple_contact_id = v_p;
  get diagnostics n_c = row_count;

  return jsonb_build_object('ok', true, 'principal_remis', n_p, 'conjoint_remis', n_c);
end
$function$;

revoke all on function public.app_conjoint_annuler_optimiste(uuid) from public;
revoke all on function public.app_conjoint_annuler_optimiste(uuid) from anon;
revoke all on function public.app_conjoint_annuler_optimiste(uuid) from authenticated;
grant execute on function public.app_conjoint_annuler_optimiste(uuid) to service_role;

-- 6. LES CONTRÔLES
SELECT 1 AS "#", 'cran pose, FERME' AS controle,
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'contacts_couples_ajout') = 'off' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'contrainte : le type neuf y est',
       CASE WHEN (SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'app_console_job_job_type_check') LIKE '%''link_hektor_conjoint''::text%' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'distribution : le service actions le reclame',
       CASE WHEN (SELECT prosrc FROM pg_proc WHERE oid = 'public.app_console_claim_next_job(text,text)'::regprocedure) LIKE '%''link_hektor_conjoint''))%' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'droits : le type neuf suit la regle de la modification',
       CASE WHEN (SELECT prosrc FROM pg_proc WHERE oid = 'public.app_console_can_request_contact_job(text,text,text)'::regprocedure) LIKE '%''archive_hektor_contact'',''link_hektor_conjoint'')%' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'porte de l''ecran : authenticated oui, anon non',
       CASE WHEN has_function_privilege('authenticated', 'public.app_ajouter_conjoint_optimistic(text,text,integer)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_ajouter_conjoint_optimistic(text,text,integer)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 6, 'fonctions du worker : fermees a anon et authenticated',
       CASE WHEN NOT has_function_privilege('authenticated', 'public.app_conjoint_relier_biens(uuid)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_conjoint_relier_biens(uuid)', 'EXECUTE')
             AND NOT has_function_privilege('authenticated', 'public.app_conjoint_annuler_optimiste(uuid)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_conjoint_annuler_optimiste(uuid)', 'EXECUTE') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
