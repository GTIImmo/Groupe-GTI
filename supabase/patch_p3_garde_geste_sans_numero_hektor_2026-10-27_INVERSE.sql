-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — P3 : retirer la garde « pas de geste sans numéro Hektor » de app_geste_affaire_optimistic   27/10/2026
-- Le bloc retire EXACTEMENT les lignes posées et EXIGE de retrouver l'empreinte de l'audit (a6569229...).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inv$
DECLARE
    f      text;
    garde  text := '  -- ⑧ P3 (27/10/2026) : PAS DE GESTE SANS NUMÉRO HEKTOR, comme l''écran (note des types §38).' || chr(10)
                || '  IF btrim(coalesce(a.hektor_affaire_id::text, '''')) = '''' THEN' || chr(10)
                || '    RAISE EXCEPTION ''sans_numero_hektor: Cette transaction n''''a pas encore de numéro Hektor : le geste ne peut pas partir.'' USING errcode = ''22023'';' || chr(10)
                || '  END IF;' || chr(10) || chr(10);
BEGIN
    SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO f FROM pg_proc p JOIN pg_namespace s ON s.oid = p.pronamespace
     WHERE s.nspname = 'public' AND p.proname = 'app_geste_affaire_optimistic';
    IF position('sans_numero_hektor' in f) = 0 THEN
        RAISE NOTICE '%', 'La fonction ne porte pas la garde : rien a defaire.';
        RETURN;
    END IF;
    IF position(garde in f) = 0 THEN
        RAISE EXCEPTION '%', 'ARRET : la garde n''est pas sous la forme posee (quelqu''un est passe apres) ; rien n''est ecrit.';
    END IF;
    EXECUTE replace(f, garde, '');
    IF (SELECT md5(pg_get_functiondef(p.oid)) FROM pg_proc p JOIN pg_namespace s ON s.oid = p.pronamespace
         WHERE s.nspname = 'public' AND p.proname = 'app_geste_affaire_optimistic') <> 'a65692290a679d603916b9d635192b80' THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction n''a pas retrouve son empreinte d''avant ; tout est annule.';
    END IF;
END
$inv$;

COMMIT;
