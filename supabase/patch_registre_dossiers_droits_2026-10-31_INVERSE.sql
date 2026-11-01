-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE de patch_registre_dossiers_droits_2026-10-31.sql                                31/10/2026
-- Remet la règle du registre EXACTEMENT comme au 31/10 (empreinte 73d92b58), rouvre la répartition à
-- tout compte connecté (USING true, comme le 14/09), retire les deux fonctions.
-- Il ne juge que SA part : il vérifie l'empreinte retrouvée et qu'il ne reste aucune trace.
-- ⚠ L'écran du registre, s'il est déjà en ligne, perdra sa liste (app_registre_dossiers) : éteindre
--   son interrupteur AVANT de coller ce fichier.
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

DO $garde$
BEGIN
    IF to_regprocedure('public.app_mes_chaines_nommees()') IS NULL
       AND to_regprocedure('public.app_registre_dossiers(integer)') IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : les fonctions du registre ne sont pas la -- rien a retirer.';
    END IF;
END
$garde$;

ALTER POLICY app_affaire_ledger_select_active_users ON public.app_affaire_ledger
USING (
    (( SELECT is_app_global_reader() AS is_app_global_reader)
     OR (app_dossier_id IN ( SELECT m.id FROM app_mes_biens_portefeuille() m(id, hid)))
     OR ((hektor_annonce_id)::text IN ( SELECT m.hid FROM app_mes_biens_portefeuille() m(id, hid))))
);

ALTER POLICY app_affaire_repartition_read ON public.app_affaire_repartition USING (true);

DROP FUNCTION IF EXISTS public.app_registre_dossiers(integer);
DROP FUNCTION IF EXISTS public.app_mes_chaines_nommees();

DO $preuve$
BEGIN
    IF (SELECT md5(qual) FROM pg_policies WHERE schemaname = 'public' AND tablename = 'app_affaire_ledger'
          AND policyname = 'app_affaire_ledger_select_active_users') IS DISTINCT FROM '73d92b58e78ee20e7b249416929fba53' THEN
        RAISE EXCEPTION '%', 'ARRET : la regle du registre n''a pas retrouve son empreinte du 31/10 (73d92b58). Rien n''est garde.';
    END IF;
    IF (SELECT qual FROM pg_policies WHERE schemaname = 'public' AND tablename = 'app_affaire_repartition'
          AND policyname = 'app_affaire_repartition_read') IS DISTINCT FROM 'true' THEN
        RAISE EXCEPTION '%', 'ARRET : la repartition n''est pas revenue a « true ». Rien n''est garde.';
    END IF;
    IF to_regprocedure('public.app_mes_chaines_nommees()') IS NOT NULL
       OR to_regprocedure('public.app_registre_dossiers(integer)') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : une fonction du registre est encore la. Rien n''est garde.';
    END IF;
END
$preuve$;

COMMIT;
