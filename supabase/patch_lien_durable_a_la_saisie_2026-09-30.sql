-- ═══════════════════════════════════════════════════════════════════════════════
-- L'APP POSE LE LIEN DURABLE AU MOMENT DU GESTE                 30/09/2026
-- ⚠ VERSION 2 -- la version 1 est PERIMEE, ne pas la coller.
--   Elle a ete ecrite AVANT la colonne `hektor_contact_id` (patch B) : elle
--   aurait pose des lignes sans le numero Hektor de la personne, alors que
--   c'est PRECISEMENT ici qu'il arrive tout cuit -- le front le passe deja.
--   On aurait creuse le trou a l'endroit meme ou on venait de le boucher.
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL.
--
-- ⭐⭐ LE WORKER NE BOUGE PAS D'UNE LIGNE -- consigne de Frederic, 30/09 :
--     « le worker doit toujours etre identique actuellement, il fonctionne.
--       C'est l'app qui doit creer en meme temps une ligne. »
--     Le travail `link_hektor_mandant` est pose EXACTEMENT comme avant : memes
--     garde-fous, meme charge, meme jeton. ON AJOUTE UNE ETAPE, ON N'EN MODIFIE
--     AUCUNE -- et elle est en best effort STRICT : quoi qu'il arrive, le geste
--     reussit et le worker fait son travail.
--
-- ─── CE QUI MANQUAIT ────────────────────────────────────────────────────────────
-- Rattacher un mandant posait UNE ETIQUETTE PROVISOIRE, purgee sous 24 h. Le
-- lien n'existait chez nous qu'apres le run de nuit.
--     si le run echoue, LE GESTE EST PERDU
--     a la coupure, il ne reviendra jamais
-- Desormais la ligne DURABLE est posee dans le meme geste, avec ses QUATRE
-- numeros.
--
-- ─── LA DOUBLE TRADUCTION, ET POURQUOI ELLE EST INDISPENSABLE ───────────────────
-- ⚠ MESURE DU 30/09 : le seul travail `link_hektor_mandant` jamais envoye portait
--   `contact_id = 603953` -- UN NUMERO HEKTOR. Mais rien ne garantit que ce sera
--   toujours le cas : le front pourrait aussi bien passer le notre.
--   ON NE SUPPOSE DONC RIEN : une seule lecture de `app_contact_current` rend LES
--   DEUX numeros, quel que soit celui qui est arrive.
--       hektor_contact_id  = LE NOTRE     (>= 10 000 000)
--       hektor_target_id   = CELUI DE HEKTOR
--   Verifie sur quatre cas le 30/09 : 603953 -> 10354641 · 41 -> 10000023 ·
--   10000023 -> 10000023 (idempotent) · 999999999 -> rien.
--
-- ⚠ SI LA TRADUCTION ECHOUE, ON N'ECRIT PAS. Mieux vaut pas de ligne qu'une
--   ligne fausse : la sentinelle `relation_disparue` compte tout numero de
--   contact sous 10 000 000 comme une AVARIE (« la substitution d'identite n'a
--   pas eu lieu »). Et le run de nuit rattrapera la ligne de toute facon.
--
-- ─── present_in_hektor = FALSE, ET C'EST VOULU ──────────────────────────────────
-- A cet instant le worker n'a pas tourne : Hektor ne connait pas encore le lien.
-- La colonne dit « le miroir le montre », donc `false`.
-- ⚠ ET CELA PROTEGE LA LIGNE : le balayage delete-never du run ne touche que les
--   lignes a `present_in_hektor = 1`. Une ligne neuve ne sera donc pas marquee
--   « sortie du miroir » avant meme d'y etre entree.
-- ⚠ EN REVANCHE ELLE N'APPARAIT PAS ENCORE A L'ECRAN : la vue exclut
--   `present_in_hektor = false` (patch A). Elle s'affichera quand Hektor l'aura
--   confirmee. C'est un choix : on montre ce qui est etabli, on GARDE ce qui est
--   en cours. L'etiquette provisoire, elle, continue d'assurer l'affichage
--   immediat -- elle n'a pas change.
--
-- ─── L'ADOPTION EST DEJA POSEE COTE SERVEUR ─────────────────────────────────────
-- relation_ledger.py reprend le numero de la plage app au lieu d'en fabriquer un
-- second pour le meme couple. Sans elle, le push heurterait
-- app_relation_couple_unique et LE RUN S'ARRETERAIT -- ce qui est arrive deux
-- nuits de suite les 01 et 02/09.
--
-- ─── CE QUE CE PATCH NE FAIT PAS, ET IL FAUT LE DIRE ────────────────────────────
-- ⛔ `app_create_mandant_contact_optimistic` (creer un contact ET le rattacher)
--    N'EST PAS TOUCHEE. A cet instant le contact n'a AUCUN numero. C'est le point
--    F du plan, ajoute par Frederic le 30/09 : il faudra faire NAITRE le contact
--    d'abord (app_create_contact_optimistic sait deja le faire, L4-b), PUIS poser
--    le lien. L'ordre est impose : le contact AVANT le lien.
-- ⛔ « RETIRER UN MANDANT » n'existe toujours nulle part.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- Rejouer la DEFINITION D'ORIGINE, gardee mot pour mot en bas de ce fichier.
-- ⚠ Ce fichier est aussi LA PREMIERE TRACE de cette fonction dans le depot :
--   l'audit du 30/09 a releve que les fonctions des gestes mandant n'etaient
--   versionnees NULLE PART -- elles n'existaient qu'en production.
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
         'proprietaire_du_bien', 'mandant', 'app', 'app:' || v_token::text,
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


-- ═══════════════════════════════════════════════════════════════════════════════
-- LA DEFINITION D'ORIGINE -- gardee mot pour mot pour le retour arriere
-- ═══════════════════════════════════════════════════════════════════════════════
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
