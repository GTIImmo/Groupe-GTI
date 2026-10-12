-- =====================================================================
-- RETOUR ARRIERE du patch CHANTIER ③ POINT 3a (12/10/2026)
-- Patch : supabase/patch_chantier3_3a_etat_chez_nous_2026-10-12.sql
--
-- IL Y A DEUX RETOURS ARRIERE, ET LE PREMIER SUFFIT PRESQUE TOUJOURS :
--
--   1. ETEINDRE (immediat, une ligne, aucun risque) -- la fonction reste en place mais
--      n'ecrit plus rien chez nous, exactement comme avant le patch :
--
--        update public.app_setting set value = 'off', updated_at = now()
--         where key = 'etat_annonce_ecrit_chez_nous';
--
--   2. RETIRER (ce fichier) -- on enleve le bloc de la fonction et on CONTROLE qu'on
--      retombe sur l'empreinte d'avant, au caractere pres.
--
-- CE QUI N'EST PAS DEFAIT, ET C'EST VOULU : les valeurs deja ecrites (fiche et carnet)
-- restent. Elles sont justes -- Hektor les a confirmees -- et le run de nuit garde de
-- toute facon le dernier mot sur statut_annonce et diffusable.
-- Pour effacer les lignes de carnet posees par ce geste, si on le voulait vraiment :
--   delete from public.app_annonce_champ_app where origine = 'geste_statut';
-- =====================================================================

BEGIN;

DO $inverse$
DECLARE
  c_sig   constant text := 'public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)';
  c_emp   constant text := '302852e8dc23c44d6e0442b81e6cb577';
  c_deb   constant text := '  -- @3a-debut';
  c_fin   constant text := '  -- @3a-fin';
  v_def   text;
  v_nu    text;
  v_apres text;
  i       int;
  j       int;
  n       int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  -- Deja revenu en arriere ? On ne fait rien, et on le dit.
  IF position(c_deb in v_def) = 0 THEN
    IF md5(v_def) = c_emp THEN
      RAISE NOTICE 'RIEN A FAIRE : le bloc n''est pas la et l''empreinte est deja celle d''avant (%)', c_emp;
      RETURN;
    END IF;
    RAISE EXCEPTION 'STOP : le bloc @3a n''est pas dans la fonction, et l''empreinte (%) n''est pas celle d''avant (%) -- a regarder a la main',
      md5(v_def), c_emp;
  END IF;

  -- Les deux reperes, une seule fois chacun.
  n := (length(v_def) - length(replace(v_def, c_deb, ''))) / length(c_deb);
  IF n <> 1 THEN RAISE EXCEPTION 'STOP : repere de debut trouve % fois, il en faut 1', n; END IF;
  n := (length(v_def) - length(replace(v_def, c_fin, ''))) / length(c_fin);
  IF n <> 1 THEN RAISE EXCEPTION 'STOP : repere de fin trouve % fois, il en faut 1', n; END IF;

  -- On coupe du debut du repere d'ouverture jusqu'au retour a la ligne qui suit la fermeture.
  i := position(c_deb in v_def);
  j := position(c_fin in v_def);
  v_nu := substr(v_def, 1, i - 1) || substr(v_def, j + length(c_fin) + 1);

  -- ⚠ LE CONTROLE QUI COMPTE : on ne reexecute QUE si le texte obtenu est, au caractere
  --   pres, la fonction d'avant le patch. Sinon on ne touche a rien.
  IF md5(v_nu) <> c_emp THEN
    RAISE EXCEPTION 'STOP : en retirant le bloc on obtient % au lieu de % -- la fonction a change depuis le patch, retrait annule',
      md5(v_nu), c_emp;
  END IF;

  EXECUTE v_nu;

  -- Controle de sortie : la base porte bien la fonction d'avant, et le bloc a DISPARU.
  v_apres := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');
  IF md5(v_apres) <> c_emp THEN
    RAISE EXCEPTION 'STOP : apres retrait la base porte % au lieu de %', md5(v_apres), c_emp;
  END IF;
  IF position('@3a' in v_apres) > 0 THEN
    RAISE EXCEPTION 'STOP : le bloc est encore la apres le retrait';
  END IF;

  RAISE NOTICE 'OK : bloc retire, la fonction est revenue a l''identique (empreinte %)', md5(v_apres);
END $inverse$;

-- L'interrupteur n'a plus d'objet une fois le bloc retire.
DELETE FROM public.app_setting WHERE key = 'etat_annonce_ecrit_chez_nous';

COMMIT;
