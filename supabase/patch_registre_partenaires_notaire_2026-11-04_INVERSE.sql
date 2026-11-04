-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE de patch_registre_partenaires_notaire_2026-11-04.sql
-- 1. les lignes « notaire » et celles de source « transactions » sont COPIÉES dans une table datée, puis retirées de
--    app_partenaire_metier (sinon les anciens contrôles refuseraient de revenir) ;
-- 2. les deux contrôles reprennent leur forme du 04/11 ;
-- 3. il vérifie qu'il ne reste AUCUNE trace de ce qu'il devait retirer, et que les autres lignes sont intactes.
-- ⚠ Éteindre d'abord la reprise des notaires (sinon la nuit suivante échouerait sur le contrôle revenu).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inverse$
DECLARE
    n_copie int; n_autres_avant int; n_autres_apres int;
BEGIN
    SELECT count(*) INTO n_autres_avant FROM public.app_partenaire_metier WHERE metier <> 'notaire' AND source <> 'transactions';
    IF to_regclass('public.app_partenaire_metier_notaire_retire_20261104') IS NULL THEN
        CREATE TABLE public.app_partenaire_metier_notaire_retire_20261104 AS
            SELECT * FROM public.app_partenaire_metier WHERE metier = 'notaire' OR source = 'transactions';
        REVOKE ALL ON TABLE public.app_partenaire_metier_notaire_retire_20261104 FROM PUBLIC, anon, authenticated;
    END IF;
    SELECT count(*) INTO n_copie FROM public.app_partenaire_metier_notaire_retire_20261104;
    DELETE FROM public.app_partenaire_metier WHERE metier = 'notaire' OR source = 'transactions';

    ALTER TABLE public.app_partenaire_metier DROP CONSTRAINT app_partenaire_metier_metier_check;
    ALTER TABLE public.app_partenaire_metier ADD CONSTRAINT app_partenaire_metier_metier_check CHECK (metier IN (
        'syndic', 'diagnostiqueur', 'courtier', 'banque', 'apporteur', 'parrain', 'administration', 'societe',
        'agent_immobilier', 'mandataire', 'promoteur', 'marchand_de_biens', 'investisseur', 'avocat', 'huissier',
        'technicien', 'autre'));
    ALTER TABLE public.app_partenaire_metier DROP CONSTRAINT app_partenaire_metier_source_check;
    ALTER TABLE public.app_partenaire_metier ADD CONSTRAINT app_partenaire_metier_source_check
        CHECK (source IN ('netty', 'hektor', 'ecran'));

    SELECT count(*) INTO n_autres_apres FROM public.app_partenaire_metier;
    IF EXISTS (SELECT 1 FROM public.app_partenaire_metier WHERE metier = 'notaire' OR source = 'transactions') THEN
        RAISE EXCEPTION '%', 'ARRET : il reste des lignes notaire / transactions ; tout est annule.';
    END IF;
    IF n_autres_apres <> n_autres_avant THEN
        RAISE EXCEPTION '%', format('ARRET : %s autres lignes avant, %s apres ; tout est annule.', n_autres_avant, n_autres_apres);
    END IF;
    IF md5((SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'public.app_partenaire_metier'::regclass
             AND conname = 'app_partenaire_metier_metier_check')) <> '64401c405122a4e858880f29b69fed85'
       OR md5((SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'public.app_partenaire_metier'::regclass
             AND conname = 'app_partenaire_metier_source_check')) <> '90bff85f3df2921d6f82bcb7cd994b5b' THEN
        RAISE EXCEPTION '%', 'ARRET : les controles ne sont pas revenus a leur forme exacte du 04/11 ; tout est annule.';
    END IF;
    RAISE NOTICE '%', format('Retour fait : %s lignes copiees dans app_partenaire_metier_notaire_retire_20261104, %s autres intactes.', n_copie, n_autres_apres);
END
$inverse$;

COMMIT;
