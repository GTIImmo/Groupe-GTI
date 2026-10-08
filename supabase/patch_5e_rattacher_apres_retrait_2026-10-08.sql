-- =====================================================================
-- CHANTIER (5) . POINT 5e -- RETIRER PUIS RATTACHER LE MEME MANDANT
-- Date : 2026-10-08 . Detail : notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md
--
-- LE PROBLEME. La RPC de rattachement finit par
--   `on conflict (app_contact_id, hektor_annonce_id) do nothing`.
-- Si le couple a deja ete RETIRE, la ligne existe avec son `retire_le` : rien
-- n'est ecrit, le retrait reste. Or la vue des mandants exige `retire_le IS NULL`
-- (relu dans la base le 08/10). Donc :
--     au clic      un bandeau "mandant en creation" s'affiche
--     ~30 s apres  le worker recree le lien CHEZ HEKTOR, pour de vrai
--     puis         le mandant ne rejoint JAMAIS la liste reelle
--     24 h apres   la ligne provisoire est purgee (patch_purge_provisoires,
--                  status 'linked' > 24 h) -> le mandant DISPARAIT de l'ecran
--                  alors qu'il est lie chez Hektor, et il le restera
-- Et rien ne le rattrape : le registre de nuit ne sait que POSER un retrait,
-- jamais l'effacer -- et il POUSSE cette colonne (relation_ledger.py).
--
-- LE GESTE EST ATTEIGNABLE SANS AVERTISSEMENT : la recherche de rattachement
-- interroge la table des CONTACTS, pas les liens -- elle propose donc un contact
-- dont le lien est retire (verifie dans le front, api.ts:8967).
--
-- LE CORRECTIF : effacer le retrait LA OU L'INTENTION EST EXPLICITE -- quelqu'un
-- vient de redemander ce lien. `do nothing` devient `do update set retire_le =
-- null, retire_par = null, absent_depuis = null`.
--
-- CE QUI NE CHANGE PAS (verifie) :
--   . `app_relation_id` reste HORS du SET : on ne renumerote JAMAIS une ligne
--     connue (regle du registre, relation_ledger.py) ;
--   . `present_in_hektor` n'est pas touche : c'est au worker de le poser quand
--     Hektor a confirme (etape `relation_etablie`, reparee au point 5d) ;
--   . `source` n'est pas touche : on ne reecrit jamais l'origine d'une ligne ;
--   . le travail pour Hektor, la ligne provisoire, les garde-fous de droits :
--     inchanges. Le worker ne voit aucune difference, AUCUN redemarrage.
--
-- ATTENTION, CE PATCH NE SUFFIT PAS SEUL. Le registre de nuit garderait son
-- ancien retrait et le repousserait des le lendemain. Le complement cote serveur
-- est dans phase2/sync/relation_ledger.py (meme commit).
--
-- RETOUR ARRIERE : supabase/patch_5e_rattacher_apres_retrait_2026-10-08_INVERSE.sql
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_proc
                  WHERE oid='public.app_link_mandant_optimistic(bigint,text,text,text,integer)'::regprocedure) THEN
    RAISE EXCEPTION 'STOP : la fonction a corriger n''existe pas sous cette signature';
  END IF;
  IF md5(replace(pg_get_functiondef('public.app_link_mandant_optimistic(bigint,text,text,text,integer)'::regprocedure), chr(13), ''))
     <> '9db5b9a664647ea1026eb11405a5b3c2' THEN
    RAISE EXCEPTION 'STOP : la fonction a change depuis la mesure du 08/10 -- me prevenir avant d''appliquer';
  END IF;
END $$;

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

DO $$
DECLARE e text;
BEGIN
  IF has_function_privilege('anon','public.app_link_mandant_optimistic(bigint,text,text,text,integer)','EXECUTE') THEN
    RAISE EXCEPTION 'CONTROLE : anon peut executer la fonction -- chantier (1) casse';
  END IF;
  IF NOT has_function_privilege('authenticated','public.app_link_mandant_optimistic(bigint,text,text,text,integer)','EXECUTE') THEN
    RAISE EXCEPTION 'CONTROLE : authenticated a PERDU le droit d''executer la fonction';
  END IF;
  e := md5(replace(pg_get_functiondef('public.app_link_mandant_optimistic(bigint,text,text,text,integer)'::regprocedure), chr(13), ''));
  RAISE NOTICE 'droits apres patch : anon=non authenticated=oui';
  RAISE NOTICE 'empreinte de la fonction posee : % (attendu f39e01658e438ab085710a6ecae1a6f2)', e;
END $$;

COMMIT;
