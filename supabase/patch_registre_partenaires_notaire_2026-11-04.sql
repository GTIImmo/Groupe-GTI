-- ═══════════════════════════════════════════════════════════════════════════
-- PARTENAIRES — LE NOTAIRE ENTRE AU REGISTRE DES PARTENAIRES                                04/11/2026
-- Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §17.
--
-- POURQUOI : décision de Frédéric du 04/11 au soir (« A ») : l'annuaire des partenaires lit UNE SEULE source pour tous
--   les métiers, notaires compris. Le registre posé le 04/11 (patch_registre_partenaires_2026-11-04.sql) les écartait.
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE (deux contrôles remplacés sur app_partenaire_metier) :
--   1. le métier accepte aussi « notaire » ;
--   2. la source accepte aussi « transactions » : le notaire lu dans la table des parties (app_affaire_partie,
--      rôles notaire_vendeur / notaire_acquereur). Les sources netty, hektor, ecran ne changent pas.
--   Aucune ligne n'est écrite ici : c'est la reprise de nuit (registre_partenaires_reprise.py) qui remplira.
-- ⛔ CE QUI NE CHANGE PAS : le type « Notaire » d'un contact (il vient toujours de la table des parties), la fiche
--   notaire du 28/10, la vue app_contact_relations_current, les liens (app_partenaire_lien n'a pas de rôle notaire :
--   le notaire d'une affaire est déjà dans la table des parties). Rien chez Hektor.
-- Le bloc vérifie l'empreinte des deux contrôles (celle du 04/11) et S'ARRÊTE si elle a changé.
-- Retour arrière : patch_registre_partenaires_notaire_2026-11-04_INVERSE.sql
-- Contrôle       : patch_registre_partenaires_notaire_2026-11-04_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $notaire$
DECLARE
    d_metier text;
    d_source text;
BEGIN
    SELECT pg_get_constraintdef(oid) INTO d_metier FROM pg_constraint
     WHERE conrelid = 'public.app_partenaire_metier'::regclass AND conname = 'app_partenaire_metier_metier_check';
    SELECT pg_get_constraintdef(oid) INTO d_source FROM pg_constraint
     WHERE conrelid = 'public.app_partenaire_metier'::regclass AND conname = 'app_partenaire_metier_source_check';
    IF position('''notaire''' in coalesce(d_metier, '')) > 0 AND position('''transactions''' in coalesce(d_source, '')) > 0 THEN
        RAISE NOTICE '%', 'Le registre accepte deja le notaire : rien a faire.';
        RETURN;
    END IF;
    IF md5(coalesce(d_metier, '')) <> '64401c405122a4e858880f29b69fed85' THEN
        RAISE EXCEPTION '%', format('ARRET : le controle du metier a change depuis le 04/11 (empreinte %s) ; rien n''est ecrit.', md5(coalesce(d_metier, '')));
    END IF;
    IF md5(coalesce(d_source, '')) <> '90bff85f3df2921d6f82bcb7cd994b5b' THEN
        RAISE EXCEPTION '%', format('ARRET : le controle de la source a change depuis le 04/11 (empreinte %s) ; rien n''est ecrit.', md5(coalesce(d_source, '')));
    END IF;

    ALTER TABLE public.app_partenaire_metier DROP CONSTRAINT app_partenaire_metier_metier_check;
    ALTER TABLE public.app_partenaire_metier ADD CONSTRAINT app_partenaire_metier_metier_check CHECK (metier IN (
        'notaire', 'syndic', 'diagnostiqueur', 'courtier', 'banque', 'apporteur', 'parrain', 'administration', 'societe',
        'agent_immobilier', 'mandataire', 'promoteur', 'marchand_de_biens', 'investisseur', 'avocat', 'huissier',
        'technicien', 'autre'));
    ALTER TABLE public.app_partenaire_metier DROP CONSTRAINT app_partenaire_metier_source_check;
    ALTER TABLE public.app_partenaire_metier ADD CONSTRAINT app_partenaire_metier_source_check
        CHECK (source IN ('netty', 'hektor', 'ecran', 'transactions'));

    EXECUTE format('comment on table public.app_partenaire_metier is %L',
        coalesce(obj_description('public.app_partenaire_metier'::regclass), '')
        || ' -- NOTAIRE (04/11/2026, decision A) : le metier notaire entre au registre ; source « transactions » = la table'
        || ' des parties (notaire_vendeur / notaire_acquereur).');
END
$notaire$;

COMMIT;
