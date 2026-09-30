-- ═══════════════════════════════════════════════════════════════════════════════
-- LES FONCTIONS DES GESTES MANDANT -- ETAT DE LA PRODUCTION AU 30/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⚠⚠ CE FICHIER N'EST PAS UN PATCH A APPLIQUER. C'est une COPIE FIDELE de ce qui
--    tourne aujourd'hui, relue depuis `pg_get_functiondef`. Le rejouer ne
--    changerait rien -- mais ce n'est pas son role : son role est qu'on puisse
--    REFAIRE ces fonctions si elles se perdent.
--
-- ─── POURQUOI CE FICHIER EXISTE ────────────────────────────────────────────────
-- L'audit du registre des liens (30/09) a releve ceci :
--
--     « Les fonctions SQL des gestes mandant ne sont versionnees NULLE PART
--       dans supabase/ -- elles n'existent qu'en production. »
--
-- Quatre fonctions dans ce cas. Si la base tombait, ou si quelqu'un les
-- remplacait, PERSONNE NE SAURAIT LES REFAIRE : ni leur corps, ni leurs
-- garde-fous, ni les raisons ecrites dans leurs commentaires.
-- C'est le meme defaut que « le code corrige n'a jamais tourne » ou « la
-- descente s'arretait en croyant avoir fini » : une chose qui marche, que
-- personne ne peut reconstruire.
--
-- ⚠ LA CINQUIEME, `app_link_mandant_optimistic`, N'EST PAS ICI : elle est
--   versionnee dans son propre patch, `patch_lien_durable_a_la_saisie_2026-09-30.sql`,
--   AVEC sa definition d'origine en bas de fichier.
--
-- ─── COMMENT ELLES S'EMBOITENT ─────────────────────────────────────────────────
--   le front appelle          ... qui appelle ...          et le worker prend
--   ─────────────────────────────────────────────────────────────────────────
--   app_create_mandant_       app_console_create_          create_hektor_
--     contact_optimistic        mandant_contact_job          mandant_contact
--   app_update_mandant_       app_console_create_update_   update_hektor_
--     contact_optimistic        mandant_contact_job          mandant_contact
--
-- Les `_optimistic` ajoutent ce que l'app garde chez elle ; les `_job` portent
-- LES GARDE-FOUS (nom, email, permission) et posent le travail. C'est un
-- recouvrement volontaire : l'optimiste ne re-valide pas, elle s'appuie dessus.
-- ═══════════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────────
-- 1/4  app_create_mandant_contact_optimistic
--      « creer un contact ET le rattacher », depuis la fiche annonce.
--      ⛔ ELLE NE POSE AUCUNE LIGNE DURABLE, et c'est le point F du plan :
--         a cet instant le contact n'a AUCUN numero, ni le notre ni celui de
--         Hektor. Il n'y a rien a quoi rattacher. Il faudra le faire NAITRE
--         d'abord (app_create_contact_optimistic sait deja le faire, L4-b).
-- ───────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.app_create_mandant_contact_optimistic(
    target_app_dossier_id bigint, target_hektor_annonce_id text,
    contact_payload jsonb, job_priority integer DEFAULT 18)
 RETURNS app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  created_job public.app_console_job;
  v_token     uuid := gen_random_uuid();
  v_label     text;
begin
  -- ── 1. LE TRAVAIL, avec ses garde-fous d'origine (par recouvrement) ──
  -- Le jeton voyage dans la charge : app_console_create_mandant_contact_job fait
  -- « contact_payload || jsonb_build_object(...) » et n'écrase pas cette clé.
  created_job := public.app_console_create_mandant_contact_job(
      target_app_dossier_id,
      target_hektor_annonce_id,
      coalesce(contact_payload, '{}'::jsonb) || jsonb_build_object('creation_token', v_token),
      job_priority);

  -- ── 2. LA LIGNE PROVISOIRE, best effort ──
  -- Le contact n'existe pas encore : on n'a pas de numéro, seulement le nom
  -- saisi. C'est lui qu'on affiche en attendant -- « l'app n'inscrit que ce
  -- qu'elle sait dire ».
  begin
    v_label := nullif(trim(
      coalesce(contact_payload->>'civilite', '') || ' ' ||
      coalesce(contact_payload->>'first_name', '') || ' ' ||
      coalesce(contact_payload->>'last_name', '')), '');

    insert into public.app_relation_provisional
      (creation_token, hektor_annonce_id, app_dossier_id,
       contact_creation_token, contact_label, role_contact, status, created_by)
    values
      (v_token, trim(target_hektor_annonce_id), target_app_dossier_id,
       v_token, v_label, 'mandant', 'pending', auth.uid()::text);
  exception when others then
    null;
  end;

  return created_job;
end;
$function$;


-- ───────────────────────────────────────────────────────────────────────────────
-- 2/4  app_update_mandant_contact_optimistic
--      « modifier un mandant », depuis la carte mandant.
--      ⚠ LE CONTACT change, LE LIEN ne change pas -- c'est voulu : modifier une
--        personne ne modifie pas le fait qu'elle possede ce bien.
--      ⚠ LA LISTE BLANCHE `connues` EST UN GARDE-FOU, pas une commodite : sans
--        elle, les identifiants et le contexte negociateur partiraient dans
--        push_fields et pollueraient l'envoi.
-- ───────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.app_update_mandant_contact_optimistic(
    target_app_dossier_id bigint, target_hektor_annonce_id text,
    target_contact_id text, contact_payload jsonb, job_priority integer DEFAULT 16)
 RETURNS app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  created_job public.app_console_job;
  champs      jsonb := '{}'::jsonb;
  cle         text;
  -- Seules ces cles sont des CHAMPS du contact. Le reste du payload
  -- (identifiants, contexte negociateur) n'a rien a faire dans une edition :
  -- il partirait dans push_fields et polluerait l'envoi.
  connues     text[] := array['civilite','last_name','first_name','email',
                              'phone','address','postal_code','city'];
begin
  -- ── 1. LE TRAVAIL, avec ses garde-fous d'origine (par recouvrement) ──
  created_job := public.app_console_create_update_mandant_contact_job(
      target_app_dossier_id, target_hektor_annonce_id,
      target_contact_id, contact_payload, job_priority);

  -- ── 2. PUIS l'ecriture chez nous, best effort ──
  begin
    foreach cle in array connues loop
      if nullif(trim(coalesce(contact_payload->>cle, '')), '') is not null then
        champs := champs || jsonb_build_object(cle, contact_payload->>cle);
      end if;
    end loop;

    if champs <> '{}'::jsonb then
      perform public.app_edit_contact_optimistic(target_contact_id, champs);

      -- ── 3. UN SEUL ENVOI : on designe NOTRE travail au balayage ──
      update public.app_contact_pending
         set push_job_id = created_job.id, updated_at = now()
       where hektor_contact_id = target_contact_id;
    end if;
  exception when others then
    -- Le geste part quand meme chez Hektor. L'app n'aura simplement pas la
    -- valeur d'avance -- c'est le comportement d'avant, pas une regression.
    null;
  end;

  return created_job;
end;
$function$;


-- ───────────────────────────────────────────────────────────────────────────────
-- 3/4  app_console_create_mandant_contact_job
--      LES GARDE-FOUS : annonce, forme du payload, NOM, EMAIL, permission.
--      Un contact sans nom ou sans email est REFUSE -- la regle « l'app
--      n'inscrit que ce qu'elle sait dire » s'applique avant l'envoi.
-- ───────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.app_console_create_mandant_contact_job(
    target_app_dossier_id bigint, target_hektor_annonce_id text,
    contact_payload jsonb, job_priority integer DEFAULT 18)
 RETURNS app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
    created_job public.app_console_job;
begin
    if nullif(trim(coalesce(target_hektor_annonce_id, '')), '') is null then
        raise exception 'missing_hektor_annonce_id' using errcode = '22023';
    end if;

    if coalesce(jsonb_typeof(contact_payload), '') <> 'object' then
        raise exception 'invalid_contact_payload' using errcode = '22023';
    end if;

    if nullif(trim(coalesce(contact_payload->>'last_name', contact_payload->>'nom', contact_payload->>'name', '')), '') is null then
        raise exception 'missing_contact_name' using errcode = '22023';
    end if;

    if nullif(trim(coalesce(contact_payload->>'email', '')), '') is null then
        raise exception 'missing_contact_email' using errcode = '22023';
    end if;

    if not public.app_console_can_request_job('create_hektor_mandant_contact', target_app_dossier_id, target_hektor_annonce_id) then
        raise exception 'forbidden_create_mandant_contact' using errcode = '42501';
    end if;

    insert into public.app_console_job (
        job_type, app_dossier_id, hektor_annonce_id, payload_json,
        status, priority, requested_by, requested_at
    )
    values (
        'create_hektor_mandant_contact',
        target_app_dossier_id,
        trim(target_hektor_annonce_id),
        contact_payload || jsonb_build_object(
            'hektor_annonce_id', trim(target_hektor_annonce_id),
            'app_dossier_id', target_app_dossier_id
        ),
        'pending',
        coalesce(job_priority, 18),
        auth.uid(),
        now()
    )
    returning * into created_job;

    return created_job;
end;
$function$;


-- ───────────────────────────────────────────────────────────────────────────────
-- 4/4  app_console_create_update_mandant_contact_job
--      Memes garde-fous, plus la validation du numero de contact.
--      ⚠ Elle pose LE NUMERO SOUS DEUX CLES (`hektor_contact_id` ET
--        `contact_id`) : le worker lit l'une ou l'autre selon le chemin.
--        A ne pas « nettoyer » -- ce doublon est intentionnel.
-- ───────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.app_console_create_update_mandant_contact_job(
    target_app_dossier_id bigint, target_hektor_annonce_id text,
    target_contact_id text, contact_payload jsonb, job_priority integer DEFAULT 16)
 RETURNS app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
    created_job public.app_console_job;
    clean_contact_id text;
begin
    clean_contact_id := nullif(trim(coalesce(target_contact_id, '')), '');

    if nullif(trim(coalesce(target_hektor_annonce_id, '')), '') is null then
        raise exception 'missing_hektor_annonce_id' using errcode = '22023';
    end if;

    if clean_contact_id is null or clean_contact_id !~ '^[0-9]+$' then
        raise exception 'invalid_contact_id' using errcode = '22023';
    end if;

    if coalesce(jsonb_typeof(contact_payload), '') <> 'object' then
        raise exception 'invalid_contact_payload' using errcode = '22023';
    end if;

    if nullif(trim(coalesce(contact_payload->>'last_name', contact_payload->>'nom', contact_payload->>'name', '')), '') is null then
        raise exception 'missing_contact_name' using errcode = '22023';
    end if;

    if nullif(trim(coalesce(contact_payload->>'email', '')), '') is null then
        raise exception 'missing_contact_email' using errcode = '22023';
    end if;

    if not public.app_console_can_request_job('update_hektor_mandant_contact', target_app_dossier_id, target_hektor_annonce_id) then
        raise exception 'forbidden_update_mandant_contact' using errcode = '42501';
    end if;

    insert into public.app_console_job (
        job_type, app_dossier_id, hektor_annonce_id, payload_json,
        status, priority, requested_by, requested_at
    )
    values (
        'update_hektor_mandant_contact',
        target_app_dossier_id,
        trim(target_hektor_annonce_id),
        contact_payload || jsonb_build_object(
            'hektor_annonce_id', trim(target_hektor_annonce_id),
            'app_dossier_id', target_app_dossier_id,
            'hektor_contact_id', clean_contact_id,
            'contact_id', clean_contact_id
        ),
        'pending',
        coalesce(job_priority, 16),
        auth.uid(),
        now()
    )
    returning * into created_job;

    return created_job;
end;
$function$;
