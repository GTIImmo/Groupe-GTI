-- ============================================================================
-- RETOUR ARRIERE : les photos redeviennent « ses biens »
-- Inverse exact de patch_photos_reseau_2026-10-12.sql
--
-- Il remet les DEUX regles telles qu'elles etaient le 12/10 (meme condition pour
-- les photos et les documents, empreinte bbd47dafebf6cada5d990b659902fa4a) et le
-- verifie.
--
-- ⚠ Il remet donc aussi le defaut : un negociateur ne verra plus les photos du
--    bien d'un collegue, et la regle des documents redeviendra lente sur un
--    comptage global. C'est volontaire : un retour arriere rend l'etat precedent,
--    defauts compris.
-- ============================================================================

begin;

drop policy if exists app_console_photo_select_scope on public.app_console_photo;
create policy app_console_photo_select_scope
    on public.app_console_photo
    for select
    using (app_console_can_access_dossier(app_dossier_id, hektor_annonce_id));

drop policy if exists app_console_document_select_scope on public.app_console_document;
create policy app_console_document_select_scope
    on public.app_console_document
    for select
    using (app_console_can_access_dossier(app_dossier_id, hektor_annonce_id));

do $controle$
declare
    v_conformes int;
begin
    select count(*) into v_conformes
      from pg_policies
     where schemaname = 'public' and cmd = 'SELECT'
       and tablename in ('app_console_photo', 'app_console_document')
       and md5(coalesce(qual, '')) = 'bbd47dafebf6cada5d990b659902fa4a';

    if v_conformes <> 2 then
        raise exception 'RETOUR ARRIERE INCOMPLET : % regle(s) sur 2 a leur empreinte du 12/10.', v_conformes;
    end if;

    raise notice 'RETOUR ARRIERE COMPLET : photos et documents sont revenus a leur regle du 12/10.';
end
$controle$;

commit;
