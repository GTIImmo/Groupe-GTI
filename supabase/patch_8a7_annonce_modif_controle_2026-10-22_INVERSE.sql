-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a-C — le contrôle au retour d'une modification d'annonce    22/10/2026
-- Il retire les deux déclencheurs, la vue, les fonctions et l'interrupteur.
-- ⛔ IL NE PERD AUCUNE SAISIE : si la table porte des lignes, elle est RENOMMÉE
--    app_annonce_saisie_modif_avant_inverse_<aaaammjj>, pas supprimée.
-- Il ne touche ni la pièce 3 ni aucune fonction existante.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

drop trigger if exists app_annonce_saisie_modif_job_trg on public.app_console_job;
drop trigger if exists app_annonce_saisie_modif_juge_trg on public.app_dossier_detail_current;
drop view if exists public.app_v_annonce_modif_ecarts;
drop function if exists public.app_annonce_saisie_modif_job_trg();
drop function if exists public.app_annonce_saisie_modif_juge_trg();
drop function if exists public.app_annonce_modif_ecart_traiter(uuid);
drop function if exists public.app_annonce_calque_modif(jsonb);

DO $garde_saisie$
DECLARE
    n int;
    nom text := 'app_annonce_saisie_modif_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_annonce_saisie_modif') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_annonce_saisie_modif n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_annonce_saisie_modif' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_annonce_saisie_modif';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_annonce_saisie_modif rename to %I', nom);
        RAISE NOTICE '%', format('%s saisie(s) gardee(s) sous public.%s', n, nom);
    END IF;
END
$garde_saisie$;

delete from public.app_setting where key = 'annonce_retour_controle';

SELECT 1 AS "#", 'les deux declencheurs sont retires' AS controle,
       CASE WHEN NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname IN ('app_annonce_saisie_modif_job_trg', 'app_annonce_saisie_modif_juge_trg')) THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'les fonctions et la vue sont retirees',
       CASE WHEN to_regprocedure('public.app_annonce_calque_modif(jsonb)') IS NULL
             AND to_regprocedure('public.app_annonce_saisie_modif_juge_trg()') IS NULL
             AND to_regclass('public.app_v_annonce_modif_ecarts') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'annonce_retour_controle') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'aucune saisie perdue : la table n''existe plus sous son nom (supprimee vide, ou renommee)',
       CASE WHEN to_regclass('public.app_annonce_saisie_modif') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la piece 3 est intacte (son declencheur est la)',
       CASE WHEN EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'app_annonce_saisie_naissance_trg') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
