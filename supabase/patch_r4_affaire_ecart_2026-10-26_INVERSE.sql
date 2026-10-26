-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE R4 — les écarts du carnet des transactions                    26/10/2026
-- Fichier GÉNÉRÉ (phase2/checks/gen_patch_r4_affaire_ecart.py).
-- Il retire la fonction et la vue. ⛔ IL NE PERD AUCUNE DÉCISION : si la table porte des lignes (dont les
-- saisies rangées par « prendre la valeur de Hektor »), elle est RENOMMÉE
-- app_affaire_carnet_decision_avant_inverse_<aaaammjj>, pas supprimée.
-- ⚠ Il ne REMET PAS au carnet les lignes retirées par « prendre Hektor » : c'était une décision de l'humain.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

drop function if exists public.app_affaire_carnet_ecart_trancher(bigint, text, text);
drop view if exists public.app_v_affaire_carnet_ecarts;

DO $garde_decisions$
DECLARE
    n int;
    nom text := 'app_affaire_carnet_decision_avant_inverse_' || to_char(now() at time zone 'Europe/Paris', 'YYYYMMDD');
BEGIN
    IF to_regclass('public.app_affaire_carnet_decision') IS NULL THEN
        RAISE NOTICE '%', 'Rien a retirer : la table app_affaire_carnet_decision n''existe pas.';
        RETURN;
    END IF;
    EXECUTE 'select count(*) from public.app_affaire_carnet_decision' INTO n;
    IF n = 0 THEN
        EXECUTE 'drop table public.app_affaire_carnet_decision';
    ELSE
        IF to_regclass('public.' || nom) IS NOT NULL THEN
            RAISE EXCEPTION '%', format('ARRET : %s existe deja ; rien n''est ecrit (choisir un autre nom a la main).', nom);
        END IF;
        EXECUTE format('alter table public.app_affaire_carnet_decision rename to %I', nom);
        RAISE NOTICE '%', format('%s decision(s) gardee(s) sous public.%s (les saisies rangees par « prendre Hektor » y sont)', n, nom);
    END IF;
END
$garde_decisions$;

SELECT 1 AS "#", 'la fonction et la vue sont retirees' AS controle,
       CASE WHEN to_regprocedure('public.app_affaire_carnet_ecart_trancher(bigint,text,text)') IS NULL
             AND to_regclass('public.app_v_affaire_carnet_ecarts') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la table des decisions est retiree ou renommee',
       CASE WHEN to_regclass('public.app_affaire_carnet_decision') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'le carnet est intact',
       CASE WHEN to_regclass('public.app_affaire_champ_app') IS NOT NULL THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
