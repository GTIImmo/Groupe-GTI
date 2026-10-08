-- =====================================================================
-- REPETITION du POINT 5e -- NE CHANGE RIEN A LA BASE
-- Date : 2026-10-08 . Detail : notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md
--
-- Elle joue LE VRAI patch (sans son BEGIN/COMMIT ni son garde-fou), essaie le
-- rattachement AVANT et APRES, PUIS joue le vrai script inverse, PUIS leve
-- volontairement une erreur : Postgres ANNULE TOUT. Chaque essai qui ECRIT est en
-- plus annule immediatement (savepoint) : aucun travail pour Hektor n'existe une
-- seconde de trop.
--
-- LE CAS D'ESSAI, REEL : le contact 10355712 (Sophie TEST MANDANT 25-08, cible
-- Hektor 605030) a ete RETIRE du bien d'essai 62963 le 03/10 a 18:22. On rejoue
-- le rattachement, comme le ferait un negociateur.
--
-- RESULTAT ATTENDU : une erreur rouge "ESSAI ANNULE" qui dit :
--   role_vu_par_la_base=admin
--   avant_empreinte=9db5b9a664647ea1026eb11405a5b3c2
--   avant_retrait=pose le 2026-10-03 (present_in_hektor=false)
--   AVANT_PATCH=travail cree=oui | retire_le APRES=TOUJOURS POSE   <- LE BUG
--   APRES_PATCH=travail cree=oui | retire_le APRES=EFFACE          <- repare
--   apres_retrait=pose le 2026-10-03 (present_in_hektor=false)     <- rien laisse
--   apres_inverse_empreinte=9db5b9a664647ea1026eb11405a5b3c2       <- = l'avant
--
-- Toute AUTRE erreur = un garde-fou a parle : me la recopier, ne pas appliquer.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='120s';

CREATE TEMP TABLE _e5e(ord int, cle text, val text);

DO $$
DECLARE u uuid;
BEGIN
  SELECT id INTO u FROM public.app_user_profile WHERE role='admin' AND is_active ORDER BY id LIMIT 1;
  IF u IS NULL THEN RAISE EXCEPTION 'STOP : aucun administrateur actif'; END IF;
  PERFORM set_config('request.jwt.claims', json_build_object('sub', u)::text, true);
  INSERT INTO pg_temp._e5e VALUES (0,'role_vu_par_la_base', coalesce(public.app_console_current_role(),'(null)'));
END $$;

INSERT INTO pg_temp._e5e SELECT 1,'avant_empreinte',
  md5(replace(pg_get_functiondef('public.app_link_mandant_optimistic(bigint,text,text,text,integer)'::regprocedure), chr(13), ''));
INSERT INTO pg_temp._e5e SELECT 2,'avant_retrait',
  'pose le '||coalesce(retire_le::date::text,'(aucun)')||' (present_in_hektor='||coalesce(present_in_hektor::text,'?')||')'
  FROM public.app_relation WHERE app_contact_id=10355712 AND hektor_annonce_id::text='62963';

-- LE BUG, REPRODUIT
DO $$
DECLARE j public.app_console_job; info text; v_ret text;
BEGIN
  BEGIN
    j := public.app_link_mandant_optimistic(5880239::bigint, '62963', '605030', 'ESSAI 5E', 18);
    SELECT CASE WHEN retire_le IS NULL THEN 'EFFACE' ELSE 'TOUJOURS POSE' END INTO v_ret
      FROM public.app_relation WHERE app_contact_id=10355712 AND hektor_annonce_id::text='62963';
    info := 'travail cree='||CASE WHEN j.id IS NULL THEN 'non' ELSE 'oui' END||' | retire_le APRES='||coalesce(v_ret,'(ligne absente)');
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN info := 'ERREUR '||SQLSTATE||'/'||SQLERRM; END IF;
  END;
  INSERT INTO pg_temp._e5e VALUES (3,'AVANT_PATCH', coalesce(info,'(rien)'));
END $$;

-- ---------------------------------------------------------------------
-- LE VRAI PATCH (corps recopie tel quel)
-- ---------------------------------------------------------------------
create or replace function public.app_link_mandant_optimistic(
  target_app_dossier_id    bigint,
  target_hektor_annonce_id text,
  target_contact_id        text,
  contact_label            text    default null::text,
  job_priority             integer default 18
)
returns app_console_job
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  created_job public.app_console_job;
  clean_id    text;
  clean_ann   text;
  v_token     uuid := gen_random_uuid();
  v_app_contact    bigint;
  v_hektor_contact text;
begin
  clean_id  := nullif(trim(coalesce(target_contact_id, '')), '');
  clean_ann := nullif(trim(coalesce(target_hektor_annonce_id, '')), '');

  if clean_ann is null then
    raise exception 'missing_hektor_annonce_id' using errcode = '22023';
  end if;
  if clean_id is null or clean_id !~ '^[0-9]+$' then
    raise exception 'invalid_contact_id' using errcode = '22023';
  end if;
  -- Le garde-fou qui manquait : le front écrivait le travail sans le demander.
  if not public.app_console_can_request_job('link_hektor_mandant',
                                            target_app_dossier_id, clean_ann) then
    raise exception 'forbidden_link_mandant' using errcode = '42501';
  end if;

  -- ── 1. LE TRAVAIL ── INCHANGE. Le worker fait ce qu'il a toujours fait.
  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json,
     status, priority, requested_by, requested_at)
  values
    ('link_hektor_mandant', target_app_dossier_id, clean_ann,
     jsonb_build_object(
       'contact_id',      clean_id,
       'contact_label',   nullif(trim(coalesce(contact_label, '')), ''),
       'creation_token',  v_token),
     'pending', coalesce(job_priority, 18), auth.uid(), now())
  returning * into created_job;

  -- ── 2. LA LIGNE PROVISOIRE, best effort ── INCHANGE.
  --    C'est elle qui assure l'affichage immediat, et elle n'a pas change.
  begin
    insert into public.app_relation_provisional
      (creation_token, hektor_annonce_id, app_dossier_id,
       hektor_contact_id, contact_label, role_contact, status, created_by)
    values
      (v_token, clean_ann, target_app_dossier_id,
       clean_id, nullif(trim(coalesce(contact_label, '')), ''),
       'mandant', 'pending', auth.uid()::text);
  exception when others then
    null;
  end;

  -- ══ 3. LA LIGNE DURABLE AU REGISTRE -- L'ETAPE NEUVE, best effort ══════════
  -- BEST EFFORT AU SENS STRICT : quoi qu'il arrive ici, le geste reussit et le
  -- worker fait son travail. Une ligne de registre manquante se rattrape au run
  -- de nuit ; un geste casse ne se rattrape pas.
  begin
    -- UNE SEULE LECTURE REND LES DEUX NUMEROS, quel que soit celui qui arrive.
    select c.hektor_contact_id::bigint, c.hektor_target_id
      into v_app_contact, v_hektor_contact
      from public.app_contact_current c
     where c.hektor_contact_id = clean_id
        or c.hektor_target_id  = clean_id
     limit 1;

    -- Pas de traduction -> PAS DE LIGNE. Mieux vaut pas de ligne qu'une ligne
    -- fausse ; le run de nuit la posera.
    if v_app_contact is not null and v_app_contact >= 10000000 then
      insert into public.app_relation
        (app_relation_id, app_contact_id, app_dossier_id, hektor_annonce_id,
         hektor_contact_id, fait, role_hektor, source, relation_key,
         first_seen_at, last_seen_at, present_in_hektor, absent_depuis)
      values
        (nextval('public.app_relation_id_app_seq'),
         v_app_contact, target_app_dossier_id, clean_ann,
         -- LE NUMERO HEKTOR DE LA PERSONNE. C'est ici qu'il arrive tout cuit :
         -- ou bien le front l'a passe, ou bien la lecture ci-dessus le rend.
         -- Sans cette ligne, le run devrait le rattraper -- et apres la coupure,
         -- plus personne ne pourrait le donner.
         coalesce(v_hektor_contact,
                  case when clean_id !~ '^[0-9]+$' or clean_id::bigint < 10000000
                       then clean_id end),
         -- ⭐ 03/10/2026 : `role_hektor` = NULL, et PAS 'mandant'.
         --   Cette colonne dit « le role TEL QUE HEKTOR LE NOMME ». Au moment du
         --   clic, Hektor n'a rien nomme : le worker n'a pas encore tourne.
         --   La vue derive alors le bon mot du NUMERO DE MANDAT -- la taxonomie
         --   du 24/07, appliquee a un seul endroit.
         'proprietaire_du_bien', null, 'app', 'app:' || v_token::text,
         now()::text, now()::text,
         false,          -- Hektor ne le connait pas encore : le worker n'a pas tourne
         null)
      -- Le couple existe deja ? On ne renumerote JAMAIS une ligne connue, et on
      -- ne rembarre pas ce qu'on sait deja.
      -- ⭐ 5e (08/10/2026) : RETIRER PUIS RATTACHER LE MEME MANDANT.
      --   `do nothing` laissait en place le `retire_le` pose par le retrait
      --   precedent. Or la vue exige `retire_le IS NULL` : le mandant NE
      --   REAPPARAISSAIT PAS, alors que le worker venait de recreer le lien chez
      --   Hektor. Et rien ne le rattrapait -- le registre de nuit ne sait que
      --   POSER un retrait, jamais l'effacer (relation_ledger.py : le UPDATE est
      --   filtre sur `retire_le IS NULL`), et il POUSSE cette colonne.
      --   On efface donc le retrait ICI, la ou l'intention est explicite :
      --   quelqu'un vient de redemander ce lien.
      -- ⚠ `app_relation_id` reste HORS du SET : on ne renumerote JAMAIS une
      --   ligne connue. `present_in_hektor` n'est pas touche non plus : c'est au
      --   worker de le poser quand Hektor a confirme (etape `relation_etablie`,
      --   reparee au point 5d).
      on conflict (app_contact_id, hektor_annonce_id) do update
         set retire_le     = null,
             retire_par    = null,
             absent_depuis = null;
    end if;
  exception when others then
    null;
  end;

  return created_job;
end;
$function$;

-- LE MEME GESTE, APRES LE PATCH
DO $$
DECLARE j public.app_console_job; info text; v_ret text;
BEGIN
  BEGIN
    j := public.app_link_mandant_optimistic(5880239::bigint, '62963', '605030', 'ESSAI 5E', 18);
    SELECT CASE WHEN retire_le IS NULL THEN 'EFFACE' ELSE 'TOUJOURS POSE' END INTO v_ret
      FROM public.app_relation WHERE app_contact_id=10355712 AND hektor_annonce_id::text='62963';
    info := 'travail cree='||CASE WHEN j.id IS NULL THEN 'non' ELSE 'oui' END||' | retire_le APRES='||coalesce(v_ret,'(ligne absente)');
    RAISE EXCEPTION 'ANNULATION_INTERNE';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM <> 'ANNULATION_INTERNE' THEN info := 'ERREUR '||SQLSTATE||'/'||SQLERRM; END IF;
  END;
  INSERT INTO pg_temp._e5e VALUES (4,'APRES_PATCH', coalesce(info,'(rien)'));
END $$;

INSERT INTO pg_temp._e5e SELECT 5,'apres_retrait',
  'pose le '||coalesce(retire_le::date::text,'(aucun)')||' (present_in_hektor='||coalesce(present_in_hektor::text,'?')||')'
  FROM public.app_relation WHERE app_contact_id=10355712 AND hektor_annonce_id::text='62963';

-- ---------------------------------------------------------------------
-- LE VRAI SCRIPT INVERSE (corps recopie tel quel)
-- ---------------------------------------------------------------------
create or replace function public.app_link_mandant_optimistic(
  target_app_dossier_id    bigint,
  target_hektor_annonce_id text,
  target_contact_id        text,
  contact_label            text    default null::text,
  job_priority             integer default 18
)
returns app_console_job
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  created_job public.app_console_job;
  clean_id    text;
  clean_ann   text;
  v_token     uuid := gen_random_uuid();
  v_app_contact    bigint;
  v_hektor_contact text;
begin
  clean_id  := nullif(trim(coalesce(target_contact_id, '')), '');
  clean_ann := nullif(trim(coalesce(target_hektor_annonce_id, '')), '');

  if clean_ann is null then
    raise exception 'missing_hektor_annonce_id' using errcode = '22023';
  end if;
  if clean_id is null or clean_id !~ '^[0-9]+$' then
    raise exception 'invalid_contact_id' using errcode = '22023';
  end if;
  -- Le garde-fou qui manquait : le front écrivait le travail sans le demander.
  if not public.app_console_can_request_job('link_hektor_mandant',
                                            target_app_dossier_id, clean_ann) then
    raise exception 'forbidden_link_mandant' using errcode = '42501';
  end if;

  -- ── 1. LE TRAVAIL ── INCHANGE. Le worker fait ce qu'il a toujours fait.
  insert into public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json,
     status, priority, requested_by, requested_at)
  values
    ('link_hektor_mandant', target_app_dossier_id, clean_ann,
     jsonb_build_object(
       'contact_id',      clean_id,
       'contact_label',   nullif(trim(coalesce(contact_label, '')), ''),
       'creation_token',  v_token),
     'pending', coalesce(job_priority, 18), auth.uid(), now())
  returning * into created_job;

  -- ── 2. LA LIGNE PROVISOIRE, best effort ── INCHANGE.
  --    C'est elle qui assure l'affichage immediat, et elle n'a pas change.
  begin
    insert into public.app_relation_provisional
      (creation_token, hektor_annonce_id, app_dossier_id,
       hektor_contact_id, contact_label, role_contact, status, created_by)
    values
      (v_token, clean_ann, target_app_dossier_id,
       clean_id, nullif(trim(coalesce(contact_label, '')), ''),
       'mandant', 'pending', auth.uid()::text);
  exception when others then
    null;
  end;

  -- ══ 3. LA LIGNE DURABLE AU REGISTRE -- L'ETAPE NEUVE, best effort ══════════
  -- BEST EFFORT AU SENS STRICT : quoi qu'il arrive ici, le geste reussit et le
  -- worker fait son travail. Une ligne de registre manquante se rattrape au run
  -- de nuit ; un geste casse ne se rattrape pas.
  begin
    -- UNE SEULE LECTURE REND LES DEUX NUMEROS, quel que soit celui qui arrive.
    select c.hektor_contact_id::bigint, c.hektor_target_id
      into v_app_contact, v_hektor_contact
      from public.app_contact_current c
     where c.hektor_contact_id = clean_id
        or c.hektor_target_id  = clean_id
     limit 1;

    -- Pas de traduction -> PAS DE LIGNE. Mieux vaut pas de ligne qu'une ligne
    -- fausse ; le run de nuit la posera.
    if v_app_contact is not null and v_app_contact >= 10000000 then
      insert into public.app_relation
        (app_relation_id, app_contact_id, app_dossier_id, hektor_annonce_id,
         hektor_contact_id, fait, role_hektor, source, relation_key,
         first_seen_at, last_seen_at, present_in_hektor, absent_depuis)
      values
        (nextval('public.app_relation_id_app_seq'),
         v_app_contact, target_app_dossier_id, clean_ann,
         -- LE NUMERO HEKTOR DE LA PERSONNE. C'est ici qu'il arrive tout cuit :
         -- ou bien le front l'a passe, ou bien la lecture ci-dessus le rend.
         -- Sans cette ligne, le run devrait le rattraper -- et apres la coupure,
         -- plus personne ne pourrait le donner.
         coalesce(v_hektor_contact,
                  case when clean_id !~ '^[0-9]+$' or clean_id::bigint < 10000000
                       then clean_id end),
         -- ⭐ 03/10/2026 : `role_hektor` = NULL, et PAS 'mandant'.
         --   Cette colonne dit « le role TEL QUE HEKTOR LE NOMME ». Au moment du
         --   clic, Hektor n'a rien nomme : le worker n'a pas encore tourne.
         --   La vue derive alors le bon mot du NUMERO DE MANDAT -- la taxonomie
         --   du 24/07, appliquee a un seul endroit.
         'proprietaire_du_bien', null, 'app', 'app:' || v_token::text,
         now()::text, now()::text,
         false,          -- Hektor ne le connait pas encore : le worker n'a pas tourne
         null)
      -- Le couple existe deja ? On ne renumerote JAMAIS une ligne connue, et on
      -- ne rembarre pas ce qu'on sait deja.
      on conflict (app_contact_id, hektor_annonce_id) do nothing;
    end if;
  exception when others then
    null;
  end;

  return created_job;
end;
$function$;

INSERT INTO pg_temp._e5e SELECT 6,'apres_inverse_empreinte',
  md5(replace(pg_get_functiondef('public.app_link_mandant_optimistic(bigint,text,text,text,integer)'::regprocedure), chr(13), ''));

DO $$
DECLARE msg text;
BEGIN
  SELECT string_agg(cle||'='||val, ' || ' ORDER BY ord) INTO msg FROM pg_temp._e5e;
  RAISE EXCEPTION 'ESSAI ANNULE -- %', msg;
END $$;
