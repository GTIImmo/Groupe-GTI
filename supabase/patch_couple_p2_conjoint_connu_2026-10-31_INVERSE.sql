-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · P2 — RETOUR ARRIÈRE                                      31/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⛔ D'ABORD : APP_COUPLE_CONJOINT=0 (ou retiré) dans C:\Hektor\Projet\.env, sinon le
--   push des contacts de la nuit échouerait sur la colonne disparue.
-- Retire le bloc P2 de app_contact_creer_conjoint (garde : le bloc doit y être UNE
-- fois), remet couple_role à vide sur les lignes « conjoint », supprime la colonne
-- et la clé de battement. Les autres rôles (menage_*) ne sont pas touchés.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inverse$
DECLARE
    fonction text := 'public.app_contact_creer_conjoint(jsonb,text,text,text)';
    debut    text := '  -- === COUPLES · P2 (31/10/2026)';
    fin      text := E'  -- === fin couples P2 ===\n';
    src      text;
    i        int;
    j        int;
BEGIN
    src := replace(pg_get_functiondef(fonction::regprocedure), chr(13), '');
    i := position(debut in src);
    j := position(fin in src);
    IF i = 0 OR j = 0 OR j < i THEN
        RAISE EXCEPTION 'ARRET : le bloc P2 n''est pas dans %. Rien n''est ecrit.', fonction;
    END IF;
    EXECUTE substr(src, 1, i - 1) || substr(src, j + length(fin));
END
$inverse$;

revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from public;
revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from anon;
revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from authenticated;
grant execute on function public.app_contact_creer_conjoint(jsonb, text, text, text) to service_role;

update public.app_contact_current set couple_role = null where couple_role = 'conjoint';
alter table public.app_contact_current drop column if exists couple_json;
delete from public.app_worker_registry where worker_key = 'phase2.conjoints_couples';

COMMIT;

-- CONTROLE : tout doit valoir 0 / false
select
  (select count(*) from information_schema.columns
    where table_schema = 'public' and table_name = 'app_contact_current' and column_name = 'couple_json') as colonne,
  (select count(*) from public.app_worker_registry where worker_key = 'phase2.conjoints_couples') as battement,
  position('COUPLES · P2' in pg_get_functiondef('public.app_contact_creer_conjoint(jsonb,text,text,text)'::regprocedure)) > 0 as bloc_encore_la,
  (select count(*) from public.app_contact_current where couple_role = 'conjoint') as conjoints;
