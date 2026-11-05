-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE de patch_partenaire_metier_creation_2026-11-05.sql
-- Retire le déclencheur, sa fonction et l'interrupteur. ⚠ Les lignes du registre DÉJÀ écrites (source « ecran ») RESTENT :
-- ce sont de vrais métiers choisis par un utilisateur ; les retirer est une autre décision (retirer en datant, jamais effacer).
-- Il vérifie qu'il ne reste AUCUNE trace de ce qu'il devait retirer, et que les deux autres déclencheurs de
-- app_console_job sont toujours là.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

drop trigger if exists app_partenaire_metier_a_la_creation_trg on public.app_console_job;
drop function if exists public.app_partenaire_metier_a_la_creation_trg();
delete from public.app_setting where key = 'partenaire_metier_a_la_creation';

DO $verif$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'app_partenaire_metier_a_la_creation_trg')
       OR to_regprocedure('public.app_partenaire_metier_a_la_creation_trg()') IS NOT NULL
       OR EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'partenaire_metier_a_la_creation') THEN
        RAISE EXCEPTION '%', 'ARRET : une trace du patch reste ; tout est annule.';
    END IF;
    IF (SELECT count(*) FROM pg_trigger WHERE tgrelid = 'public.app_console_job'::regclass
         AND tgname IN ('app_annonce_saisie_modif_job_trg', 'app_contact_saisie_modif_job_trg')) <> 2 THEN
        RAISE EXCEPTION '%', 'ARRET : un declencheur voisin de app_console_job a disparu ; tout est annule.';
    END IF;
    RAISE NOTICE '%', 'Retour fait : declencheur, fonction et interrupteur retires ; les lignes du registre deja ecrites restent.';
END
$verif$;

COMMIT;
