-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ types §53 P4-a : retirer le bloc « mandant existant au clic de la création »        28/10/2026
-- Il ne juge que SA part : il retire le bloc, de « @P4a-debut » à « @P4a-fin », à l'octet, et vérifie que la fonction
-- retrouve son empreinte d'avant (a5e70b57). Les liens déjà posés restent (le worker et la nuit les tiennent comme les autres).
-- ⚠ Le worker reste capable de les mener (numéro, établi, refus) : sans liens nés au clic, ses trois gestes ne trouvent rien.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $p$
DECLARE
    d   text := pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure);
    i   int  := position(E'\n\n  -- @P4a-debut' in d);
    j   int  := position('  -- @P4a-fin' in d);
BEGIN
    IF i = 0 OR j = 0 OR j < i THEN
        RAISE EXCEPTION '%', 'ARRET : le bloc @P4a est introuvable ; rien n''est ecrit.';
    END IF;
    d := substr(d, 1, i - 1) || substr(d, j + length('  -- @P4a-fin'));
    IF md5(d) <> 'a5e70b5734876f74ecd0083681a1ebe8' THEN
        RAISE EXCEPTION '%', format('ARRET : sans le bloc, la fonction ne retrouve pas son empreinte d''avant (%s) ; rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$p$;

-- ① la colonne redevient obligatoire SEULEMENT si aucune ligne n'attend son numéro de bien ; sinon on le DIT et on s'arrête
--   (retirer ces lignes réécrirait le registre : décision à part).
DO $n$
DECLARE n int;
BEGIN
    SELECT count(*) INTO n FROM public.app_relation WHERE hektor_annonce_id IS NULL;
    IF n > 0 THEN
        RAISE EXCEPTION '%', format('ARRET : %s lien(s) attendent encore leur numero de bien ; la colonne reste facultative. Tout est annule.', n);
    END IF;
END
$n$;
ALTER TABLE public.app_relation ALTER COLUMN hektor_annonce_id SET NOT NULL;

COMMIT;
