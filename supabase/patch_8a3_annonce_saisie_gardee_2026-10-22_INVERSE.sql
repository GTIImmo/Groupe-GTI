-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE 8a PIÈCE 3 — la saisie gardée, le verdict, la remise à l'écran
--                                                                    22/10/2026
-- Il retire le déclencheur, la vue, les fonctions et l'interrupteur.
-- ⛔ IL NE PERD AUCUNE SAISIE (« une saisie ne se perd jamais ») : si la table porte des
--    lignes, elle est RENOMMÉE app_annonce_saisie_naissance_avant_inverse_<aaaammjj>,
--    pas supprimée. Vide, elle est supprimée.
-- Il ne touche ni la création d'annonce (a5e70b57) ni la fonction de naissance (944db16b).
-- ⚠ Il ne juge que SA part : les calques déjà reposés dans des fiches y restent jusqu'à
--   leur prochaine relecture (qui les remplacera, comme avant le patch).
-- Pour seulement SUSPENDRE, inutile de jouer ce fichier : éteindre l'interrupteur.
--   update public.app_setting set value = 'off', updated_at = now() where key = 'annonce_saisie_gardee';
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

drop trigger if exists app_annonce_saisie_naissance_trg on public.app_dossier_detail_current;
drop view if exists public.app_v_annonce_naissance_ecarts;
drop function if exists public.app_annonce_saisie_naissance_trg();
drop function if exists public.app_annonce_naissance_ecart_traiter(bigint);
drop function if exists public.app_annonce_verdict_naissance(jsonb, jsonb);
drop function if exists public.app_annonce_meme_valeur(text, text);
drop function if exists public.app_annonce_lecture_hektor(jsonb, text);
drop function if exists public.app_annonce_porteur_present(jsonb, text);
drop function if exists public.app_annonce_bloc(jsonb, text);
drop function if exists public.app_annonce_champs_console();

DO $garde_saisie$
DECLARE
    n int;
    nom text := 'app_annonce_saisie_naissance_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_annonce_saisie_naissance') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_annonce_saisie_naissance n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_annonce_saisie_naissance' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_annonce_saisie_naissance';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_annonce_saisie_naissance rename to %I', nom);
        RAISE NOTICE '%', format('%s saisie(s) gardee(s) sous public.%s', n, nom);
    END IF;
END
$garde_saisie$;

delete from public.app_setting where key = 'annonce_saisie_gardee';

SELECT 1 AS "#", 'le declencheur est retire (aucun sur la fiche detaillee)' AS controle,
       CASE WHEN NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'public.app_dossier_detail_current'::regclass AND NOT tgisinternal) THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'les fonctions et la vue sont retirees',
       CASE WHEN to_regprocedure('public.app_annonce_lecture_hektor(jsonb,text)') IS NULL
             AND to_regprocedure('public.app_annonce_saisie_naissance_trg()') IS NULL
             AND to_regclass('public.app_v_annonce_naissance_ecarts') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'l''interrupteur est retire',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'annonce_saisie_gardee') THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'aucune saisie perdue : la table n''existe plus sous son nom (supprimee vide, ou renommee)',
       CASE WHEN to_regclass('public.app_annonce_saisie_naissance') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'la creation d''annonce n''est PAS retouchee (a5e70b57)',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure), chr(13), '')) = 'a5e70b5734876f74ecd0083681a1ebe8' THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
