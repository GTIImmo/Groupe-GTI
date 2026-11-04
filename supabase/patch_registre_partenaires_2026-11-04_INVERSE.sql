-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — patch_registre_partenaires_2026-11-04.sql                                 04/11/2026
-- Il ne juge que SA part : les deux tables et les deux fonctions du registre des partenaires.
-- ⚠ Une ligne écrite n'est JAMAIS perdue : avant de retirer les tables, leur contenu est recopié dans deux tables
--   datées (app_partenaire_metier_avant_inverse_<date>, app_partenaire_lien_avant_inverse_<date>), lisibles par
--   service_role seulement. Rien d'autre n'est touché.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $i$
DECLARE
    v_suffixe text := to_char(now(), 'YYYYMMDD_HH24MI');
BEGIN
    IF to_regclass('public.app_partenaire_metier') IS NOT NULL THEN
        EXECUTE format('CREATE TABLE public.%I AS TABLE public.app_partenaire_metier', 'app_partenaire_metier_avant_inverse_' || v_suffixe);
        EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC, anon, authenticated', 'app_partenaire_metier_avant_inverse_' || v_suffixe);
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', 'app_partenaire_metier_avant_inverse_' || v_suffixe);
    END IF;
    IF to_regclass('public.app_partenaire_lien') IS NOT NULL THEN
        EXECUTE format('CREATE TABLE public.%I AS TABLE public.app_partenaire_lien', 'app_partenaire_lien_avant_inverse_' || v_suffixe);
        EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC, anon, authenticated', 'app_partenaire_lien_avant_inverse_' || v_suffixe);
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', 'app_partenaire_lien_avant_inverse_' || v_suffixe);
    END IF;
END
$i$;

DROP FUNCTION IF EXISTS public.app_partenaire_lien_ecrire(bigint, text, text, text, bigint, bigint, bigint, text, boolean);
DROP FUNCTION IF EXISTS public.app_partenaire_metier_ecrire(text, text, boolean);
DROP TABLE IF EXISTS public.app_partenaire_lien;
DROP TABLE IF EXISTS public.app_partenaire_metier;

-- Il vérifie qu'il ne reste aucune trace de SA part.
DO $v$
BEGIN
    IF to_regclass('public.app_partenaire_metier') IS NOT NULL OR to_regclass('public.app_partenaire_lien') IS NOT NULL
       OR EXISTS (SELECT 1 FROM pg_proc WHERE proname IN ('app_partenaire_lien_ecrire', 'app_partenaire_metier_ecrire')) THEN
        RAISE EXCEPTION '%', 'Le retour arrière n''a pas tout retiré : rien n''est validé.';
    END IF;
END
$v$;

COMMIT;
