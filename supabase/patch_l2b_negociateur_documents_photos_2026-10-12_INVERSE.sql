-- ============================================================================
-- RETOUR ARRIERE DU LOT L2-B
-- Inverse exact de patch_l2b_negociateur_documents_photos_2026-10-12.sql
--
-- Il retire les 9 types et VERIFIE qu'il retombe exactement sur l'empreinte
-- laissee par L2-A : 7eea707fd7bd93b9f34473d57b5371fa.
--
-- ⚠ Il ne remet PAS l'etat d'avant L2-A. Pour cela, enchainer ensuite
--    patch_l2a_negociateur_champs_mandants_2026-10-12_INVERSE.sql.
--    La chaine est : L2-B_INVERSE -> etat L2-A ; puis L2-A_INVERSE -> etat du matin.
-- ============================================================================

begin;

-- ----------------------------------------------------------------------------
-- 1. LE VIDEUR : les 9 types quittent la liste du commercial
-- ----------------------------------------------------------------------------
do $fermer$
declare
    v_def text;
    v_ancre text := '''update_hektor_mandant_contact''';
    v_ajout text;
begin
    v_ajout := v_ancre || ','
        || chr(10) || '            ''delete_document_from_hektor'',''generate_estimation_pdf'','
        || chr(10) || '            ''generate_mandat_document'',''generate_cadastre_document'','
        || chr(10) || '            ''upload_hektor_photo'',''sync_hektor_photos'',''matterport_action'','
        || chr(10) || '            ''create_hektor_mandat_auto_number'',''restore_hektor_annonce''';

    select pg_get_functiondef(p.oid) into v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job';

    if position('upload_hektor_photo' in v_def) = 0 then
        raise notice 'VIDEUR : rien a retirer, les 9 types ne sont pas la.';
    else
        execute replace(v_def, v_ajout, v_ancre);
        raise notice 'VIDEUR : les 9 types sont retires (21 -> 12).';
    end if;
end
$fermer$;


-- ----------------------------------------------------------------------------
-- 2. CONTROLE : retombe-t-on sur l'empreinte laissee par L2-A ?
-- ----------------------------------------------------------------------------
do $controle$
declare
    v_trouve text;
    v_attendu text := '7eea707fd7bd93b9f34473d57b5371fa';
    v_types int := 0;
    v_t text;
    v_def text;
begin
    select md5(replace(pg_get_functiondef(p.oid), chr(13), '')),
           pg_get_functiondef(p.oid)
      into v_trouve, v_def
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname = 'public' and p.proname = 'app_console_can_request_job'
     limit 1;

    if v_trouve is distinct from v_attendu then
        raise exception 'RETOUR ARRIERE INCOMPLET : le videur ne retombe pas sur l''empreinte de L2-A (trouve %, attendu %).',
            coalesce(v_trouve, '(aucune)'), v_attendu;
    end if;

    -- et les 12 types de L2-A doivent etre tous la
    foreach v_t in array array[
        'prepare_document_cloud','upload_document_to_hektor','prepare_archived_annonce_detail',
        'prepare_historical_annonce_detail','sync_console_documents','relance_signature',
        'cancel_signature_procedure','update_hektor_annonce_fields','link_hektor_mandant',
        'unlink_hektor_mandant','create_hektor_mandant_contact','update_hektor_mandant_contact'
    ] loop
        if position(v_t in v_def) > 0 then v_types := v_types + 1; end if;
    end loop;
    if v_types <> 12 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % types sur les 12 de L2-A.', v_types;
    end if;

    raise notice 'RETOUR ARRIERE COMPLET : le videur est revenu a l''etat L2-A (12 types), a l''empreinte.';
end
$controle$;

commit;
