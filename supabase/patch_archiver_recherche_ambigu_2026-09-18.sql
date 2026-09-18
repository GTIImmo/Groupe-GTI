-- ═══════════════════════════════════════════════════════════════════════════════
-- ARCHIVER UNE RECHERCHE DEPUIS L'APP : « search_index is ambiguous »     18/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- LE DEFAUT. La fonction recoit un PARAMETRE nomme `search_index` ; ses tables ont
-- une COLONNE `search_index`. A trois endroits elle ecrivait `search_index` seul,
-- et Postgres refuse de deviner : « column reference "search_index" is ambiguous ».
-- Toute la transaction etait annulee -- rien chez nous, rien chez Hektor.
--
-- DEPUIS QUAND : C.4 du 30/08 (4c5745f), qui a ajoute « on ecrit chez nous
-- d'abord » sans essai. Mesure : 2 archivages dans toute l'histoire, tous deux en
-- juin, AVANT le defaut. Trouve le 18/09 par Frederic, en archivant la recherche de
-- test de M. Test CLOTURE (605075).
--
-- LA CORRECTION : on dit a chaque endroit DE QUEL search_index on parle.
--   lecture           s.search_index = <parametre>
--   passage archivee  s.search_index = <parametre>
--   verrou            ON CONFLICT ON CONSTRAINT app_search_pending_pkey
--                     (la meme cle -- (hektor_contact_id, search_index) --
--                      designee par son nom, sans nommer la colonne)
-- RIEN D'AUTRE NE CHANGE : memes gardes, meme travail, meme charge.
--
-- ⚠ PAS DE `#variable_conflict use_variable` : il aurait fait de
--   `search_index = search_index` une comparaison TOUJOURS VRAIE, et archive
--   d'un coup TOUTES les recherches du contact.
--
-- SIGNATURE INCHANGEE -> CREATE OR REPLACE, les droits sont conserves.
-- RETOUR ARRIERE : la definition precedente est dans l'historique git de
--   patch_c4_supprimer_recherche_2026-08-30.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_console_create_delete_contact_search_job(target_contact_id text, search_index integer DEFAULT NULL::integer, target_critere_id text DEFAULT NULL::text, job_priority integer DEFAULT 14)
 RETURNS app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare created_job public.app_console_job; clean_contact_id text; existing_contact public.app_contact_current%rowtype;
        target_email text; target_user_id text; clean_critere_id text;
        cur public.app_contact_search_current%rowtype; v_base jsonb;
begin
    clean_contact_id := nullif(trim(coalesce(target_contact_id, '')), '');
    if clean_contact_id is null or clean_contact_id !~ '^[0-9]+$' then raise exception 'invalid_contact_id' using errcode = '22023'; end if;
    clean_critere_id := nullif(trim(coalesce(target_critere_id, '')), '');
    if search_index is null and (clean_critere_id is null or clean_critere_id !~ '^[0-9]+$') then
        raise exception 'missing_search_target' using errcode = '22023'; end if;
    select * into existing_contact from public.app_contact_current where hektor_contact_id = clean_contact_id limit 1;
    if existing_contact.hektor_contact_id is null then raise exception 'contact_not_found' using errcode = '22023'; end if;
    select r.target_email, r.target_user_id into target_email, target_user_id
    from public.app_console_resolve_contact_hektor_user(existing_contact) r;
    if not public.app_console_can_request_contact_job('delete_hektor_contact_search', clean_contact_id, target_email) then
        raise exception 'forbidden_delete_contact_search' using errcode = '42501'; end if;

    insert into public.app_console_job (job_type, payload_json, status, priority, requested_by, requested_at)
    values ('delete_hektor_contact_search',
        jsonb_build_object('hektor_contact_id', clean_contact_id, 'contact_id', clean_contact_id,
            'search_index', search_index, 'idCritere', clean_critere_id,
            'hektor_user_email', target_email, 'target_hektor_user_email', target_email,
            'hektor_user_id', target_user_id, 'target_hektor_user_id', target_user_id,
            'contact_negociateur_email', existing_contact.negociateur_email, 'contact_hektor_negociateur_id', existing_contact.hektor_negociateur_id),
        'pending', coalesce(job_priority, 14), auth.uid(), now())
    returning * into created_job;

    -- ─── C.4 (30/08) : ON ECRIT CHEZ NOUS, DANS LA MEME TRANSACTION ───
    -- Seulement si on sait de quelle ligne il s'agit. Sans search_index on ne
    -- devine pas : le travail part quand meme, et l'archivage viendra du run.
    -- 18/09 : chaque search_index est QUALIFIE (s. = la colonne, le nom de la
    -- fonction = le parametre) -- voir l'en-tete.
    if search_index is not null then
      select s.* into cur from public.app_contact_search_current s
       where s.hektor_contact_id = clean_contact_id
         and s.search_index = app_console_create_delete_contact_search_job.search_index
       limit 1;

      if cur.contact_search_key is not null and coalesce(cur.archive, false) is not true then
        v_base := jsonb_build_object('archive', cur.archive, 'is_active', cur.is_active,
                                     'criteres_json', cur.criteres_json, 'prix_max', cur.prix_max);

        update public.app_contact_search_current s
           set archive = true, is_active = false, refreshed_at = now()
         where s.hektor_contact_id = clean_contact_id
           and s.search_index = app_console_create_delete_contact_search_job.search_index;

        -- Le verrou porte le numero du travail : le balayage l'efface quand le
        -- travail aboutit, le rearme quand il echoue. Il ne reste pas eternel.
        insert into public.app_search_pending(hektor_contact_id, search_index, base_snapshot,
                                              push_search, push_after, source, dirty_by, push_job_id)
        values (clean_contact_id, app_console_create_delete_contact_search_job.search_index, v_base,
                null, now(), 'nego_app', auth.uid()::text, created_job.id)
        on conflict on constraint app_search_pending_pkey do update
          set push_job_id = excluded.push_job_id,
              conflict    = false,
              updated_at  = now();
      end if;
    end if;

    return created_job;
end; $function$;
