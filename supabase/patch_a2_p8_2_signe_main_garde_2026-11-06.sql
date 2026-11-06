-- A.2 P8-2 (06/11/2026, D42) -- « SIGNÉ À LA MAIN » REFUSE PENDANT UNE SIGNATURE ÉLECTRONIQUE EN COURS
-- ---------------------------------------------------------------------------------------------------------
-- Audit P8 du 06/11 : la fonction posait `status: signed, source: manuscrite` sans regarder l'état existant. Sur un
-- document Youtrust EN COURS (ou une procédure ImmoSign en attente), elle aurait marqué « signé » une demande encore
-- ouverte chez le fournisseur. Frédéric (06/11) : « uniquement si une procédure est lancée, laisser le bouton mais
-- faire un message qui explique à l'utilisateur d'annuler la procédure pour pouvoir signer à la main le doc ».
-- L'écran le dit déjà (lib/choixSignature.ts) ; cette garde est la même règle CÔTÉ BASE, pour tout appelant.
--
-- Ce qui change : UN refus, avant l'écriture, si la signature du document est
--   - Youtrust ET « pending », ou
--   - porte un procedure_id ET « pending » (ImmoSign en attente).
-- Tout le reste est IDENTIQUE au patch du 27/07 (mêmes paramètres, même garde d'accès, même écriture).
-- `create or replace` garde les droits existants (aucun grant/revoke ici).
-- Retour arrière : patch_a2_p8_2_signe_main_garde_2026-11-06_INVERSE.sql (le corps du 27/07, à l'identique).

do $$
declare v_def text;
begin
  select pg_get_functiondef('public.app_console_mark_document_signed_manual(uuid,date)'::regprocedure) into v_def;
  -- On ne remplace QUE la version du 27/07 (sans garde) : si quelqu'un est passé avant, on s'arrête.
  if v_def ilike '%signature_en_cours%' then
    raise exception 'DEJA POSE : la garde est deja dans la fonction -- rien a faire.';
  end if;
  if v_def not ilike '%''source'', ''manuscrite''%' or v_def not ilike '%app_console_can_access_dossier%' then
    raise exception 'VERSION INATTENDUE de app_console_mark_document_signed_manual : on ne remplace pas a l''aveugle.';
  end if;
end $$;

create or replace function public.app_console_mark_document_signed_manual(
    document_id uuid,
    signed_date date default null
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_signed text;
    v_sig jsonb;
begin
    -- A.2 P8-2 : une signature électronique EN COURS sur ce document -> refus, avec le message pour l'écran.
    select d.metadata_json -> 'signature' into v_sig
      from public.app_console_document d
     where d.id = document_id
       and public.app_console_can_access_dossier(d.app_dossier_id, d.hektor_annonce_id);
    if v_sig is not null and v_sig ->> 'status' = 'pending'
       and (v_sig ->> 'provider' = 'youtrust' or nullif(trim(coalesce(v_sig ->> 'procedure_id', '')), '') is not null) then
        raise exception 'Une signature électronique est en cours sur ce document : annulez-la d''abord pour pouvoir le marquer signé à la main.'
          using errcode = 'P0001', detail = 'signature_en_cours';
    end if;

    -- Date de signature affichée par la pastille (repli : aujourd'hui, heure de Paris).
    v_signed := coalesce(signed_date::text, (now() at time zone 'Europe/Paris')::date::text);

    update public.app_console_document d
    set metadata_json = jsonb_set(
            coalesce(d.metadata_json, '{}'::jsonb),
            '{signature}',
            coalesce(d.metadata_json -> 'signature', '{}'::jsonb)
                || jsonb_build_object(
                        'status', 'signed',
                        'source', 'manuscrite',
                        'signed_at', v_signed,
                        'marked_manual_at', to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD"T"HH24:MI:SS')
                    ),
            true
        ),
        updated_at = now()
    where d.id = document_id
      and public.app_console_can_access_dossier(d.app_dossier_id, d.hektor_annonce_id);

    if not found then
        raise exception 'document_not_found_or_forbidden';
    end if;
end;
$$;
