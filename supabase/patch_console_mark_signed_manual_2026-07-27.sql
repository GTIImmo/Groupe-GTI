-- Voie manuscrite (rubrique Mandat V3, Lot 7)
-- ---------------------------------------------------------------------------
-- Exceptionnellement, un commercial peut faire signer le mandat SUR PAPIER,
-- puis joindre le PDF signé dans les Documents (ce qui déclenche déjà le worker
-- upload_document_to_hektor). Il ne reste qu'à marquer ce document comme signé
-- pour que le cockpit passe le mandat de « édité » à « Signé » (mandatSig='signed').
--
-- app_console_document n'a AUCUNE policy UPDATE pour `authenticated` (seul SELECT
-- existe) : le front ne peut donc pas écrire metadata_json directement. On ajoute
-- une RPC SECURITY DEFINER dédiée, calquée EXACTEMENT sur app_console_touch_document
-- (même garde d'accès app_console_can_access_dossier), qui pose :
--   metadata_json.signature = { status:'signed', source:'manuscrite', signed_at, marked_manual_at }
-- en PRÉSERVANT les autres clés de signature déjà présentes.
--
-- Additif et réversible : `drop function app_console_mark_document_signed_manual(uuid, date)`.

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

grant execute on function public.app_console_mark_document_signed_manual(uuid, date) to authenticated;
