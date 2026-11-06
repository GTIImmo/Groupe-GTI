-- RETOUR ARRIÈRE de patch_a2_p8_2_signe_main_garde_2026-11-06.sql : la fonction du 27/07, à l'identique (sans garde).
-- Ne juge que SA part : il ne touche à rien d'autre que cette fonction.

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
begin
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

do $$
begin
  if pg_get_functiondef('public.app_console_mark_document_signed_manual(uuid,date)'::regprocedure) ilike '%signature_en_cours%' then
    raise exception 'RETOUR ARRIERE RATE : la garde est encore la.';
  end if;
end $$;
