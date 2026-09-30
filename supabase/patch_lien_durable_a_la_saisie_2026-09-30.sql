-- ═══════════════════════════════════════════════════════════════════════════════
-- L'APP POSE LE LIEN DURABLE AU MOMENT DU GESTE                 30/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL.
--
-- ⭐⭐ LE WORKER NE BOUGE PAS D'UNE LIGNE -- consigne de Frederic, 30/09 :
--     « le worker doit toujours etre identique actuellement, il fonctionne.
--       C'est l'app qui doit creer en meme temps une ligne. »
--     Le travail (`link_hektor_mandant`) est pose exactement comme avant, avec
--     les memes garde-fous, la meme charge, le meme jeton. Le worker le prend et
--     fait ce qu'il a toujours fait : creer le lien chez Hektor.
--     ON AJOUTE UNE ETAPE, ON N'EN MODIFIE AUCUNE.
--
-- ─── CE QUI MANQUAIT ────────────────────────────────────────────────────────────
-- Aujourd'hui, rattacher un mandant pose UNE ETIQUETTE PROVISOIRE, purgee sous
-- 24 h. Le lien n'existe chez nous qu'apres le passage du run de nuit.
--     si le run echoue, LE GESTE EST PERDU
--     a la coupure, il ne reviendra jamais
-- Desormais la ligne DURABLE est posee dans le meme geste, avec son numero.
--
-- ─── LA TRADUCTION DU NUMERO, ET POURQUOI ELLE EST INDISPENSABLE ────────────────
-- ⚠ MESURE DU 30/09 : le seul travail `link_hektor_mandant` jamais envoye portait
--   `contact_id = 603953` -- UN NUMERO HEKTOR, pas le notre.
--   Or `app_relation.app_contact_id` ne doit contenir QUE nos numeros : la
--   sentinelle `relation_disparue` compte tout numero sous 10 000 000 comme une
--   AVARIE (« la substitution d'identite n'a pas eu lieu »).
--   On traduit donc avant d'ecrire, par `app_contact_current`, qui porte les deux
--   numeros : `hektor_contact_id` (le NOTRE, malgre son nom) et `hektor_target_id`
--   (celui de Hektor). C'est la meme traduction que le correctif de l'ecran.
--   Si la traduction echoue, ON N'ECRIT PAS la ligne durable -- mieux vaut pas de
--   ligne qu'une ligne fausse ; l'etiquette provisoire et le run font le reste.
--
-- ─── present_in_hektor = FALSE, ET C'EST VOULU ──────────────────────────────────
-- A cet instant Hektor ne connait pas encore le lien : le worker n'a pas tourne.
-- La colonne dit « le miroir le montre », donc `false`. Le run la passera a `true`
-- quand Hektor le redescendra.
-- ⚠ ET CELA PROTEGE LA LIGNE : le balayage delete-never du run ne touche que les
--   lignes a `present_in_hektor = 1`. Une ligne neuve ne sera donc pas marquee
--   « sortie du miroir » avant meme d'y etre entree.
--
-- ─── L'ADOPTION EST DEJA POSEE COTE SERVEUR ─────────────────────────────────────
-- relation_ledger.py reprend le numero de la plage app au lieu d'en fabriquer un
-- second pour le meme couple. Sans elle, le push heurterait
-- app_relation_couple_unique et LE RUN S'ARRETERAIT -- ce qui est arrive deux
-- nuits de suite les 01 et 02/09.
--
-- ─── CE QUE CE PATCH NE FAIT PAS, ET IL FAUT LE DIRE ────────────────────────────
-- ⛔ `app_create_mandant_contact_optimistic` (creer un contact ET le rattacher)
--    N'EST PAS TOUCHEE. A cet instant le contact n'existe pas : il n'a AUCUN
--    numero, ni le notre ni celui de Hektor. Il n'y a donc rien de durable a
--    ecrire. Ce cas reste suspendu a la creation du contact -- c'est le defaut
--    deja note au plan (« ni contact ni lien avant Hektor »), et il se resoudra
--    quand le contact naitra dans l'app AVANT son lien.
-- ⛔ « RETIRER UN MANDANT » n'existe toujours nulle part.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- Rejouer la DEFINITION D'ORIGINE, gardee mot pour mot en bas de ce fichier.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_link_mandant_optimistic(
    target_app_dossier_id bigint,
    target_hektor_annonce_id text,
    target_contact_id text,
    contact_label text DEFAULT NULL::text,
    job_priority integer DEFAULT 18)
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
  v_app_contact bigint;
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
    -- La traduction : le front envoie le numero HEKTOR (mesure du 30/09).
    -- app_contact_current porte les deux -- hektor_contact_id est le NOTRE.
    select c.hektor_contact_id::bigint
      into v_app_contact
      from public.app_contact_current c
     where c.hektor_contact_id = clean_id
        or c.hektor_target_id  = clean_id
     limit 1;

    -- Pas de traduction -> PAS DE LIGNE. Mieux vaut pas de ligne qu'une ligne
    -- fausse : la sentinelle compte tout numero sous 10 000 000 comme une avarie.
    if v_app_contact is not null and v_app_contact >= 10000000 then
      insert into public.app_relation
        (app_relation_id, app_contact_id, app_dossier_id, hektor_annonce_id,
         fait, role_hektor, source, relation_key,
         first_seen_at, last_seen_at, present_in_hektor, absent_depuis)
      values
        (nextval('public.app_relation_id_app_seq'),
         v_app_contact, target_app_dossier_id, clean_ann,
         'proprietaire_du_bien', 'mandant', 'app', 'app:' || v_token::text,
         now()::text, now()::text,
         false,          -- Hektor ne le connait pas encore : le worker n'a pas tourne
         null)
      -- Le couple existe deja ? On ne renumerote JAMAIS une ligne connue.
      on conflict (app_contact_id, hektor_annonce_id) do nothing;
    end if;
  exception when others then
    null;
  end;

  return created_job;
end;
$function$;


-- ═══════════════════════════════════════════════════════════════════════════════
-- LA DEFINITION D'ORIGINE -- gardee mot pour mot pour le retour arriere
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⚠⚠ ET CE FICHIER EST AUSSI LA PREMIERE TRACE DE CETTE FONCTION DANS LE DEPOT.
--    L'audit du 30/09 l'a relevee : les fonctions des gestes mandant
--    (app_link_mandant_optimistic, app_create_mandant_contact_optimistic,
--     app_update_mandant_contact_optimistic) n'etaient versionnees NULLE PART --
--    elles n'existaient qu'en production. Si elles se perdaient, on ne savait pas
--    les refaire.
--
-- CREATE OR REPLACE FUNCTION public.app_link_mandant_optimistic(
--     target_app_dossier_id bigint, target_hektor_annonce_id text,
--     target_contact_id text, contact_label text DEFAULT NULL::text,
--     job_priority integer DEFAULT 18)
--  RETURNS app_console_job LANGUAGE plpgsql SECURITY DEFINER
--  SET search_path TO 'public'
-- AS $function$
-- declare
--   created_job public.app_console_job;
--   clean_id    text;
--   clean_ann   text;
--   v_token     uuid := gen_random_uuid();
-- begin
--   clean_id  := nullif(trim(coalesce(target_contact_id, '')), '');
--   clean_ann := nullif(trim(coalesce(target_hektor_annonce_id, '')), '');
--   if clean_ann is null then
--     raise exception 'missing_hektor_annonce_id' using errcode = '22023';
--   end if;
--   if clean_id is null or clean_id !~ '^[0-9]+$' then
--     raise exception 'invalid_contact_id' using errcode = '22023';
--   end if;
--   if not public.app_console_can_request_job('link_hektor_mandant',
--                                             target_app_dossier_id, clean_ann) then
--     raise exception 'forbidden_link_mandant' using errcode = '42501';
--   end if;
--   insert into public.app_console_job
--     (job_type, app_dossier_id, hektor_annonce_id, payload_json,
--      status, priority, requested_by, requested_at)
--   values
--     ('link_hektor_mandant', target_app_dossier_id, clean_ann,
--      jsonb_build_object('contact_id', clean_id,
--        'contact_label', nullif(trim(coalesce(contact_label, '')), ''),
--        'creation_token', v_token),
--      'pending', coalesce(job_priority, 18), auth.uid(), now())
--   returning * into created_job;
--   begin
--     insert into public.app_relation_provisional
--       (creation_token, hektor_annonce_id, app_dossier_id,
--        hektor_contact_id, contact_label, role_contact, status, created_by)
--     values
--       (v_token, clean_ann, target_app_dossier_id, clean_id,
--        nullif(trim(coalesce(contact_label, '')), ''),
--        'mandant', 'pending', auth.uid()::text);
--   exception when others then
--     null;
--   end;
--   return created_job;
-- end;
-- $function$
-- ═══════════════════════════════════════════════════════════════════════════════
