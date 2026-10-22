-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a-B — le contrôle au retour d'une modification de contact  22/10/2026
-- Il retire les deux déclencheurs, la vue, les fonctions et l'interrupteur.
-- ⛔ IL NE PERD AUCUNE SAISIE : si la table porte des lignes, elle est RENOMMÉE
--    app_contact_saisie_modif_avant_inverse_<aaaammjj>, pas supprimée. Vide, elle est supprimée.
-- Il ne touche aucune fonction existante (il n'en a modifié aucune).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

drop trigger if exists app_contact_saisie_modif_job_trg on public.app_console_job;
drop trigger if exists app_contact_saisie_modif_juge_trg on public.app_contact_current;
drop view if exists public.app_v_contact_modif_ecarts;
drop function if exists public.app_contact_saisie_modif_job_trg();
drop function if exists public.app_contact_saisie_modif_juge_trg();
drop function if exists public.app_contact_modif_ecart_traiter(uuid);
drop function if exists public.app_contact_verdict_modif(jsonb, jsonb);
drop function if exists public.app_contact_meme_valeur(text, text);
drop function if exists public.app_contact_champs_modif(jsonb);

DO $garde_saisie$
DECLARE
    n int;
    nom text := 'app_contact_saisie_modif_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_contact_saisie_modif') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_contact_saisie_modif n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_contact_saisie_modif' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_contact_saisie_modif';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_contact_saisie_modif rename to %I', nom);
        RAISE NOTICE '%', format('%s saisie(s) gardee(s) sous public.%s', n, nom);
    END IF;
END
$garde_saisie$;

delete from public.app_setting where key = 'contact_retour_controle';

SELECT 1 AS "#", 'les deux declencheurs sont retires' AS controle,
       CASE WHEN NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname IN ('app_contact_saisie_modif_job_trg', 'app_contact_saisie_modif_juge_trg')) THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'les fonctions et la vue sont retirees',
       CASE WHEN to_regprocedure('public.app_contact_verdict_modif(jsonb,jsonb)') IS NULL
             AND to_regprocedure('public.app_contact_saisie_modif_juge_trg()') IS NULL
             AND to_regclass('public.app_v_contact_modif_ecarts') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contact_retour_controle') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'aucune saisie perdue : la table n''existe plus sous son nom (supprimee vide, ou renommee)',
       CASE WHEN to_regclass('public.app_contact_saisie_modif') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
