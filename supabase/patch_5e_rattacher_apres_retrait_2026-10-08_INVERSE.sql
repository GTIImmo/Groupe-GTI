-- =====================================================================
-- RETOUR ARRIERE du POINT 5e -- repose la fonction d'AVANT, mot pour mot
-- Date : 2026-10-08
--
-- Le corps ci-dessous est la definition exacte en production avant le patch du
-- 08/10 : il a ete RECUPERE ENCODE depuis la base (base64) puis decode, et son
-- empreinte a ete verifiee hors ligne contre pg_proc.prosrc --
-- md5 a7213743cbede951bd13ce9e47f3cd14, 4 569 caracteres. Pas une lettre retapee.
--
-- ATTENTION : `create or replace`, JAMAIS `drop function`.
--
-- EFFET : rattacher un mandant precedemment retire ne le fera plus reapparaitre.
-- A faire AVEC le retour arriere cote serveur (relation_ledger.py).
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

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

DO $$
DECLARE e text;
BEGIN
  e := md5(replace(pg_get_functiondef('public.app_link_mandant_optimistic(bigint,text,text,text,integer)'::regprocedure), chr(13), ''));
  RAISE NOTICE 'empreinte reposee : % (attendu 9db5b9a664647ea1026eb11405a5b3c2)', e;
  IF e <> '9db5b9a664647ea1026eb11405a5b3c2' THEN
    RAISE EXCEPTION 'CONTROLE : la fonction reposee n''est pas celle d''avant (empreinte %)', e;
  END IF;
END $$;

COMMIT;
