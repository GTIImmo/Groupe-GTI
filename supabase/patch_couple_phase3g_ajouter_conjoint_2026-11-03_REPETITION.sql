-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE G — RÉPÉTITION (rien ne reste)                           03/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Joue le PATCH dans une transaction, sous l'identité d'un ADMIN (Frédéric), sur TROIS FICHES FICTIVES posées
-- pour l'occasion (29999991 « ESSAI AJOUT Un », 29999992 « Deux », 29999993 « Trois », notaire témoin), la
-- première reliée à UN bien vivant (l'annonce d'essai 63331, née dans l'app le 22/10), mesure, puis LÈVE « ESSAI ANNULE » : tout est
-- annulé (fonctions, contrainte, cran, fiches, travaux, liens).
-- JOUÉE le 03/11 : 01 ferme=ok | 02 ajout=ok | 03 chez_nous=ok | 04 travail=ok | 05 deja=ok(conjoint_pas_seul) | 06 temoins=ok
--                  10 distribution=ok | 07 biens=ok | 08 retour=ok | 09 droits=ok -- et RIEN n'est resté (vérifié après).
-- Attendu : 01 ferme · 02 ajout · 03 chez_nous · 04 travail · 05 deja · 06 temoins · 10 distribution
--           07 biens · 08 retour · 09 droits   -- tous « ok »
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '5s';

CREATE TEMP TABLE _rep(t text) ON COMMIT DROP;
INSERT INTO _rep VALUES ('');


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


-- ── LE DÉCOR (annulé avec le reste) : trois fiches fictives, un bien vivant pour la première ──
insert into app_contact_current (hektor_contact_id, app_contact_id, nom, prenom, display_name, email, archive, date_enregistrement,
  date_maj, typologies_json, source_hash, refreshed_at, negociateur_email, hektor_target_id, nature_fiche)
values ('29999991', 29999991, 'ESSAI AJOUT', 'Un', 'Un ESSAI AJOUT', 'essai.ajout.un@example.com', false, now()::date::text, now()::text,
        '[]'::jsonb, 'rep_g_1', now(), 'frederic.gerphagnon@gti-immobilier.fr', '999999991', 'personne_seule'),
       ('29999992', 29999992, 'ESSAI AJOUT', 'Deux', 'Deux ESSAI AJOUT', 'essai.ajout.deux@example.com', false, now()::date::text, now()::text,
        '[]'::jsonb, 'rep_g_2', now(), 'frederic.gerphagnon@gti-immobilier.fr', '999999992', 'personne_seule'),
       ('29999993', 29999993, 'ESSAI AJOUT', 'Trois', 'Trois ESSAI AJOUT', 'essai.ajout.trois@example.com', false, now()::date::text, now()::text,
        '[]'::jsonb, 'rep_g_3', now(), 'frederic.gerphagnon@gti-immobilier.fr', '999999993', 'notaire');
insert into app_relation (app_relation_id, app_contact_id, app_dossier_id, hektor_annonce_id, hektor_contact_id, fait, role_hektor,
  source, relation_key, first_seen_at, last_seen_at, present_in_hektor)
select nextval('public.app_relation_id_app_seq'), 29999991, d.app_dossier_id, d.hektor_annonce_id::text, '999999991',
       'proprietaire_du_bien', 'mandant', 'app', 'rep_g', now()::text, now()::text, true
  from app_dossier_current d where d.hektor_annonce_id = 63331 limit 1;

DO $appel$
DECLARE r jsonb; r_ferme jsonb; r_deja jsonb; r_notaire jsonb; r_meme jsonb; rb jsonb; ra jsonb; v_job uuid;
        avant_p text; avant_c text; apres_p text; apres_c text; v_claim app_console_job; v_autres int;
BEGIN
  select md5(row(hektor_couple_contact_id, app_couple_contact_id, couple_role, couple_json, nature_fiche, couple_deuxieme)::text) into avant_p
    from app_contact_current where hektor_contact_id = '29999991';
  select md5(row(hektor_couple_contact_id, app_couple_contact_id, couple_role, couple_json, nature_fiche, couple_deuxieme)::text) into avant_c
    from app_contact_current where hektor_contact_id = '29999992';
  select count(*) into v_autres from app_console_job where status = 'pending';

  perform set_config('request.jwt.claims',
    json_build_object('sub', (select id from auth.users where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr'), 'role', 'authenticated')::text, true);
  perform set_config('role', 'authenticated', true);
  r_ferme := public.app_ajouter_conjoint_optimistic('29999991', '29999992');
  perform set_config('role', 'postgres', true);
  update app_setting set value = 'admin' where key = 'contacts_couples_ajout';
  perform set_config('role', 'authenticated', true);
  r := public.app_ajouter_conjoint_optimistic('29999991', '29999992');
  r_deja := public.app_ajouter_conjoint_optimistic('29999991', '29999992');
  r_notaire := public.app_ajouter_conjoint_optimistic('29999993', '29999992');
  r_meme := public.app_ajouter_conjoint_optimistic('29999992', '29999992');
  perform set_config('role', 'postgres', true);
  v_job := (r->>'job_id')::uuid;

  update _rep set t =
       ' | 01 ferme=' || case when r_ferme->>'raison' = 'cran_ferme' then 'ok' else 'FAUX:' || r_ferme::text end
    || ' | 02 ajout=' || case when coalesce((r->>'ok')::boolean, false) and (r->>'biens')::int = 1 then 'ok' else 'FAUX:' || r::text end
    || ' | 03 chez_nous=' || coalesce((select case when p.nature_fiche = 'couple' and p.couple_json->>'etat' = 'nomme'
                                                   and p.couple_json->'conjoint'->>'id' = '29999992' and p.hektor_couple_contact_id = '29999991'
                                                   and c.hektor_couple_contact_id = '29999991' and c.couple_role = 'conjoint' and c.nature_fiche = 'conjoint'
                                                   and c.app_couple_contact_id = 29999991
                                              then 'ok' else 'FAUX' end
                                         from app_contact_current p, app_contact_current c
                                        where p.hektor_contact_id = '29999991' and c.hektor_contact_id = '29999992'), 'ABSENT')
    || ' | 04 travail=' || coalesce((select case when j.job_type = 'link_hektor_conjoint' and j.status = 'pending' and j.priority = 25
                                                  and j.payload_json->>'hektor_contact_id' = '29999991' and j.payload_json->>'conjoint_id' = '29999992'
                                                  and jsonb_array_length(j.payload_json->'biens') = 1 and j.payload_json ? 'avant'
                                                  and j.requested_by is not null
                                             then 'ok' else 'FAUX' end from app_console_job j where j.id = v_job), 'ABSENT')
    || ' | 05 deja=' || case when r_deja->>'raison' in ('personne_deja_en_couple', 'conjoint_pas_seul', 'deja_en_cours') then 'ok(' || (r_deja->>'raison') || ')' else 'FAUX:' || r_deja::text end
    || ' | 06 temoins=' || case when r_notaire->>'raison' = 'notaire' and r_meme->>'raison' = 'meme_fiche' then 'ok'
                               else 'FAUX:' || r_notaire::text || r_meme::text end;

  -- la distribution : seulement si la file est vide, sinon on ne prend pas le travail d'un autre
  if v_autres = 0 then
    select * into v_claim from public.app_console_claim_next_job('repetition:service:v9', 'actions');
    update _rep set t = t || ' | 10 distribution=' || case when v_claim.id = v_job then 'ok' else 'FAUX:' || coalesce(v_claim.job_type, 'rien') end;
  else
    update _rep set t = t || ' | 10 distribution=NON_JOUEE(file non vide : ' || v_autres || ')';
  end if;

  -- le worker, après le lien prouvé : les biens
  rb := public.app_conjoint_relier_biens(v_job);
  update _rep set t = t || ' | 07 biens=' ||
    case when (rb->>'poses')::int = 1
          and exists (select 1 from app_console_job j where j.job_type = 'link_hektor_mandant' and j.payload_json->>'parent_job_id' = v_job::text
                         and j.payload_json->>'contact_id' = '29999992' and j.requested_by is not null)
          and exists (select 1 from app_relation x where x.app_contact_id = 29999992 and x.retire_le is null and x.present_in_hektor = false)
         then 'ok' else 'FAUX:' || rb::text end;

  -- le worker, si Hektor refuse : le retour arrière
  ra := public.app_conjoint_annuler_optimiste(v_job);
  select md5(row(hektor_couple_contact_id, app_couple_contact_id, couple_role, couple_json, nature_fiche, couple_deuxieme)::text) into apres_p
    from app_contact_current where hektor_contact_id = '29999991';
  select md5(row(hektor_couple_contact_id, app_couple_contact_id, couple_role, couple_json, nature_fiche, couple_deuxieme)::text) into apres_c
    from app_contact_current where hektor_contact_id = '29999992';
  update _rep set t = t || ' | 08 retour=' ||
    case when avant_p = apres_p and avant_c = apres_c and (ra->>'principal_remis')::int = 1 and (ra->>'conjoint_remis')::int = 1
         then 'ok' else 'FAUX:' || ra::text end;

  update _rep set t = t || ' | 09 droits=' ||
    case when not has_function_privilege('anon', 'public.app_ajouter_conjoint_optimistic(text,text,integer)', 'EXECUTE')
          and not has_function_privilege('authenticated', 'public.app_conjoint_relier_biens(uuid)', 'EXECUTE')
          and not has_function_privilege('authenticated', 'public.app_conjoint_annuler_optimiste(uuid)', 'EXECUTE')
          and has_function_privilege('authenticated', 'public.app_ajouter_conjoint_optimistic(text,text,integer)', 'EXECUTE')
         then 'ok' else 'FAUX' end;
END
$appel$;

DO $essai$
DECLARE v text;
BEGIN
  select _rep.t into v from _rep;
  RAISE EXCEPTION 'ESSAI ANNULE --%', v;
END
$essai$;

ROLLBACK;
