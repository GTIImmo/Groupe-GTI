-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, P3 — LA GARDE « PAS DE GESTE SANS NUMÉRO HEKTOR » DANS LA BASE AUSSI          27/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §38.
--
-- POURQUOI : l'écran refuse déjà tout geste (refuser, accepter, annuler, supprimer) sur une transaction sans
--   numéro Hektor (App.tsx, « Cette transaction n'a pas encore de numéro Hektor : le geste ne peut pas partir »).
--   La fonction de la base, elle, ne le vérifiait pas : un autre appelant pouvait poser le geste, et une
--   suppression passée AVANT la confirmation de la création était défaite par cette confirmation
--   (poserIdTransactionSurAffaire remet present_in_hektor = true sans condition) -- la transaction ressuscitait.
--   Et avec la vue « vivante chez nous » (§37), une suppression sans numéro laisserait la ligne affichée.
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE : app_geste_affaire_optimistic refuse le geste, avec le MÊME message que
--   l'écran, quand la transaction n'a pas de numéro Hektor. Placé APRÈS les contrôles existants (droits, genre,
--   verrou de l'offre, « déjà dans cet état ») et AVANT toute écriture. Rien d'autre ne change.
--   `create or replace` garde le propriétaire, les droits et SECURITY DEFINER.
-- ⚠ À LA COUPURE (étape 3), cette garde sera à revoir avec celle de l'écran : plus aucune transaction n'aura de
--   numéro Hektor. Note §38.3.
-- ⛔ RIEN N'EST ÉCRIT DANS UNE TABLE, RIEN CHEZ HEKTOR.
-- Le bloc vérifie l'empreinte de la fonction et S'ARRÊTE si elle a changé depuis l'audit.
-- Retour arrière : patch_p3_garde_geste_sans_numero_hektor_2026-10-27_INVERSE.sql
-- Contrôle       : patch_p3_garde_geste_sans_numero_hektor_2026-10-27_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
DECLARE
    f      text;
    ancre  text := '  etat_avant := a.state;';
    garde  text := '  -- ⑧ P3 (27/10/2026) : PAS DE GESTE SANS NUMÉRO HEKTOR, comme l''écran (note des types §38).' || chr(10)
                || '  IF btrim(coalesce(a.hektor_affaire_id::text, '''')) = '''' THEN' || chr(10)
                || '    RAISE EXCEPTION ''sans_numero_hektor: Cette transaction n''''a pas encore de numéro Hektor : le geste ne peut pas partir.'' USING errcode = ''22023'';' || chr(10)
                || '  END IF;' || chr(10) || chr(10);
    n      int;
BEGIN
    SELECT pg_get_functiondef(p.oid) INTO f FROM pg_proc p JOIN pg_namespace s ON s.oid = p.pronamespace
     WHERE s.nspname = 'public' AND p.proname = 'app_geste_affaire_optimistic';
    IF position('sans_numero_hektor' in f) > 0 THEN
        RAISE NOTICE '%', 'La fonction porte deja la garde : rien a faire.';
        RETURN;
    END IF;
    IF md5(f) <> 'a65692290a679d603916b9d635192b80' THEN
        RAISE EXCEPTION '%', format('ARRET : app_geste_affaire_optimistic a change depuis l''audit du 27/10 (empreinte %s au lieu de a6569229...) ; rien n''est ecrit.', md5(f));
    END IF;
    f := replace(f, chr(13), '');
    n := (length(f) - length(replace(f, ancre, ''))) / length(ancre);
    IF n <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre est trouvee %s fois (1 attendue) ; rien n''est ecrit.', n);
    END IF;
    EXECUTE replace(f, ancre, garde || ancre);
    IF position('sans_numero_hektor' in (SELECT pg_get_functiondef(p.oid) FROM pg_proc p JOIN pg_namespace s ON s.oid = p.pronamespace
                                           WHERE s.nspname = 'public' AND p.proname = 'app_geste_affaire_optimistic')) = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : la garde n''est pas dans la fonction apres la pose ; tout est annule.';
    END IF;
END
$garde$;

COMMIT;
