-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, P3 (préalable) — LA VUE DES LIENS COMPTE LES TRANSACTIONS « VIVANTES CHEZ NOUS »      27/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §36.5, §36.6 et §37.
--
-- LE DÉFAUT : la 2e branche de `app_contact_relations_current` (les acheteurs, depuis la table des parties) ne
--   gardait que `p.transaction_presente`, c'est-à-dire « PRÉSENTE CHEZ HEKTOR ». Une offre, un compromis ou une
--   vente créés dans l'app existent pourtant dès le geste, sous NOTRE numéro (app_affaire_id >= 1 000 000) ; seul
--   le numéro Hektor arrive à la confirmation. Entre les deux, l'acheteur n'apparaissait ni dans la fiche contact,
--   ni dans son type -- et après la coupure, il n'apparaîtrait jamais.
--   Frédéric (27/10) : « nous enregistrons bien la transaction au geste […] nos transactions sont portées par leur
--   propre id ».
--
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE : la condition devient LA RÈGLE « VIVANTE » QUE LE PROJET APPLIQUE DÉJÀ
--   (app_geste_affaire_optimistic, le verrou d'une offre) : une transaction compte, SAUF si elle porte un numéro
--   Hektor ET qu'elle n'est plus chez Hektor (supprimée chez nous ou retirée chez Hektor).
--     née chez nous, pas encore confirmée -> compte   (nouveau)
--     confirmée                            -> compte   (comme avant)
--     supprimée / retirée, avec son numéro -> ne compte pas (comme avant : les 17 du 27/10)
--   Aujourd'hui, AUCUNE ligne ne change (les 341 transactions nées dans l'app sont toutes confirmées).
--   Les 20 colonnes, security_invoker, le propriétaire et les droits sont gardés (create or replace).
-- ⚠ Reste pour l'étape 3 (pas ici) : une transaction née chez nous et supprimée AVANT son numéro Hektor (§36.6).
-- ⛔ RIEN N'EST ÉCRIT DANS UNE TABLE, RIEN CHEZ HEKTOR.
-- Le bloc vérifie l'empreinte de la vue (celle de P2) et S'ARRÊTE si elle a changé.
-- Retour arrière : patch_p3_transactions_vivantes_chez_nous_2026-10-27_INVERSE.sql
-- Contrôle       : patch_p3_transactions_vivantes_chez_nous_2026-10-27_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $vue$
DECLARE
    d       text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    -- ⚠ ancre et ajout sur UNE SEULE LIGNE (leçon 30)
    ancre   text := 'p.transaction_presente';
    regle   text := '(NOT ((btrim(COALESCE(l.hektor_affaire_id, ''''::text)) <> ''''::text) AND (l.present_in_hektor IS FALSE)))';
    n       int;
    nb      int;
BEGIN
    IF position('l.present_in_hektor IS FALSE' in d) > 0 THEN
        RAISE NOTICE '%', 'La vue porte deja la regle « vivante » : rien a faire.';
        RETURN;
    END IF;
    IF md5(d) <> '0021f0f1681dcaab4ef12fd21514d254' THEN
        RAISE EXCEPTION '%', format('ARRET : la vue app_contact_relations_current a change depuis l''audit du 27/10 (empreinte %s au lieu de 0021f0f1...) ; rien n''est ecrit.', md5(d));
    END IF;
    d := replace(d, chr(13), '');
    n := (length(d) - length(replace(d, ancre, ''))) / length(ancre);
    IF n <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre est trouvee %s fois (1 attendue) ; rien n''est ecrit.', n);
    END IF;
    d := replace(d, ancre, regle);
    d := rtrim(rtrim(d), ';');
    EXECUTE 'create or replace view public.app_contact_relations_current with (security_invoker = true) as ' || d;

    SELECT count(*) INTO nb FROM pg_attribute
     WHERE attrelid = 'public.app_contact_relations_current'::regclass AND attnum > 0 AND NOT attisdropped;
    IF nb <> 20 THEN
        RAISE EXCEPTION '%', format('ARRET : la vue a %s colonnes (20 attendues) ; tout est annule.', nb);
    END IF;
    IF position('p.transaction_presente' in pg_get_viewdef('public.app_contact_relations_current'::regclass)) > 0 THEN
        RAISE EXCEPTION '%', 'ARRET : la vue lit encore « presente chez Hektor » ; tout est annule.';
    END IF;

    EXECUTE format('comment on view public.app_contact_relations_current is %L',
        coalesce(obj_description('public.app_contact_relations_current'::regclass), '')
        || ' -- P3 (27/10/2026) : les acheteurs comptent quand la transaction est VIVANTE CHEZ NOUS (regle de'
        || ' app_geste_affaire_optimistic), plus seulement « presente chez Hektor ».');
END
$vue$;

COMMIT;
