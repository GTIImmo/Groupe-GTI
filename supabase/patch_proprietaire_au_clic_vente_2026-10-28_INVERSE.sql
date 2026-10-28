-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ types §52 C : retirer le bloc « propriétaire au clic de la vente »                28/10/2026
-- Il ne juge que SA part : il retire le bloc, de « @C-proprio-au-clic » à « @C-fin », à l'octet, et vérifie que la fonction
-- retrouve son empreinte d'avant (fce35139). Les liens déjà posés restent (la nuit les confirme ou les lève, comme tout lien).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $p$
DECLARE
    d   text := pg_get_functiondef('public.app_change_annonce_status_optimistic'::regproc);
    i   int  := position('-- @C-proprio-au-clic' in d);
    j   int  := position(E'-- @C-fin\n  ' in d);
BEGIN
    IF i = 0 OR j = 0 OR j < i THEN
        RAISE EXCEPTION '%', 'ARRET : le bloc @C-proprio-au-clic est introuvable ; rien n''est ecrit.';
    END IF;
    d := substr(d, 1, i - 1) || substr(d, j + length(E'-- @C-fin\n  '));
    IF md5(d) <> 'fce35139d02f8f4f995392a9f8566891' THEN
        RAISE EXCEPTION '%', format('ARRET : sans le bloc, la fonction ne retrouve pas son empreinte d''avant (%s) ; rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$p$;

COMMIT;
