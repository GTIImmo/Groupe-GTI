-- ═══════════════════════════════════════════════════════════════════════════════
-- app_link_mandant_optimistic : un lien NE DANS L'APP n'est pas « mandant » d'office
-- ═══════════════════════════════════════════════════════════════════════════════
-- TROUVE A L'EPREUVE, le 03/10 au soir, juste apres avoir rendu le rattachement
-- optimiste : le lien apparaissait bien tout de suite -- MAIS SON BOUTON « RETIRER »
-- ETAIT GRISE. Rattacher puis corriger son erreur restait donc impossible, ce qui
-- vidait de son sens le travail qu'on venait de faire.
--
-- LA CAUSE : la RPC ecrit `role_hektor = 'mandant'` EN DUR.
--     'proprietaire_du_bien', 'mandant', 'app', ...
--            ^fait              ^role_hektor
-- La vue en deduit role_contact = 'mandant', et le bouton grise -- puisque la regle
-- de Frederic est « un mandat signe => retrait impossible ».
--
-- ⛔ OR IL N'Y AVAIT AUCUN MANDAT. Mesure sur les deux liens d'essai :
--     role_hektor = 'mandant'   ·   mandat du bien = AUCUN   ·   mandats connus = 0
-- C'est exactement le cas de SUR-PROTECTION (« l'ecran grise / le serveur accepte »)
-- que j'avais mesure a ZERO le matin meme -- reintroduit par les liens nes dans l'app.
--
-- ⚠ ET CA CONTREDIT LA TAXONOMIE DU PROJET, posee le 24/07 :
--     MANDANT      = lie a une annonce AVEC un numero de mandat
--     PROPRIETAIRE = lie a une annonce SANS mandat
--
-- LE CORRECTIF, ET IL EST A LA SOURCE : `role_hektor` devient NULL. Ce n'est pas un
-- pis-aller, c'est la verite -- cette colonne dit « le role TEL QUE HEKTOR LE
-- NOMME », et au moment du clic Hektor n'a RIEN nomme du tout : le worker n'a pas
-- encore tourne.
--
-- ⭐ ET LA VUE FAIT DEJA LE RESTE, SANS QU'ON TOUCHE A RIEN :
--     COALESCE(CASE WHEN numero_mandat IS NOT NULL THEN 'mandant' END,
--              r.role_hektor,
--              'proprietaire')
--   · le bien a un mandat  -> 'mandant'      (et le bouton grise, a juste titre)
--   · pas de mandat        -> 'proprietaire' (et le bouton est actif)
--   Une seule regle, un seul endroit. On ne duplique pas la taxonomie dans la RPC.
--
-- ⚠ ON NE TOUCHE PAS a `fait` ('proprietaire_du_bien') : il porte LE FAIT, pas le
--   libelle, et il etait deja juste. Ni a la ligne provisoire, qui est un affichage.
--
-- RETOUR ARRIERE : rejouer ce fichier en remettant 'mandant' a la place de null.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

CREATE OR REPLACE FUNCTION public.app_link_mandant_optimistic(target_app_dossier_id bigint, target_hektor_annonce_id text, target_contact_id text, contact_label text DEFAULT NULL::text, job_priority integer DEFAULT 18)
 RETURNS app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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

-- ─── LA REPARATION DES LIGNES DEJA POSEES ────────────────────────────────────
-- Les liens nes dans l'app portent aujourd'hui l'etiquette fausse. On ne la
-- corrige QUE sur eux (source = 'app') : une ligne venue du miroir Hektor porte
-- une etiquette que HEKTOR a donnee, et on n'y touche jamais.
UPDATE public.app_relation
   SET role_hektor = null
 WHERE source = 'app'
   AND role_hektor = 'mandant';

-- ─── LE GARDE-FOU : on verifie, on ne suppose pas ─────────────────────────────
DO $$
DECLARE n_app_mandant int; n_miroir_mandant int; src text;
BEGIN
    SELECT pg_get_functiondef(p.oid) INTO src
      FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname='public' AND p.proname='app_link_mandant_optimistic';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : la RPC app_link_mandant_optimistic est introuvable.';
    END IF;
    IF position('''proprietaire_du_bien'', null, ''app''' in src) = 0 THEN
        RAISE EXCEPTION 'ARRET : la RPC ecrit toujours un role en dur.';
    END IF;

    SELECT count(*) INTO n_app_mandant
      FROM public.app_relation WHERE source = 'app' AND role_hektor = 'mandant';
    IF n_app_mandant > 0 THEN
        RAISE EXCEPTION 'ARRET : % lien(s) de l app portent encore l etiquette en dur.', n_app_mandant;
    END IF;

    -- ⛔ ET SURTOUT : on ne doit avoir touche AUCUNE ligne du miroir.
    SELECT count(*) INTO n_miroir_mandant
      FROM public.app_relation
     WHERE coalesce(source, '') <> 'app' AND role_hektor = 'mandant';
    IF n_miroir_mandant = 0 THEN
        RAISE EXCEPTION 'ARRET : plus aucune ligne du miroir ne porte role_hektor=mandant -- on a trop efface.';
    END IF;

    RAISE NOTICE 'OK : la RPC n ecrit plus de role en dur ; 0 lien app mal etiquete ; % lignes du miroir intactes.', n_miroir_mandant;
END $$;

COMMIT;
