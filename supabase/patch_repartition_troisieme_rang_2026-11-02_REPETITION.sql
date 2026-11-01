-- ===========================================================================
-- CONTROLES DU TROISIEME RANG -- N'ECRIT RIEN                     02/11/2026
-- ===========================================================================
-- ⭐ IL EPROUVE POUR DE VRAI, DANS UNE TRANSACTION ANNULEE : il INSERE un rang 3
--   (temoin POSITIF) et un rang 4 (temoin INVERSE), puis ROLLBACK. Rien ne reste.
--   Lire une definition ne prouve pas qu'un INSERT passe : on execute.
-- 6 controles. Tous doivent dire OK. Le dernier mot est « ROLLBACK ».
-- ===========================================================================

BEGIN;

DO $rep$
DECLARE
  v_chk text; v_rpc text; v_pk text;
  v_lignes_avant int; v_lignes_apres int;
  v_rang3_passe boolean := false;
  v_rang4_refuse boolean := false;
  v_essai_chaine bigint := -999999;
BEGIN
  SELECT count(*) INTO v_lignes_avant FROM public.app_affaire_repartition;

  -- 1. le CHECK accepte 1, 2, 3 --------------------------------------------
  SELECT pg_get_constraintdef(con.oid) INTO v_chk
    FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname='public' AND c.relname='app_affaire_repartition'
     AND con.conname='app_affaire_repartition_rang_chk';
  RAISE NOTICE '1. CHECK      : %', v_chk;
  IF v_chk <> 'CHECK ((rang = ANY (ARRAY[1, 2, 3])))' THEN
     RAISE EXCEPTION 'CONTROLE 1 ROUGE : %', v_chk; END IF;

  -- 2. la CLE PRIMAIRE est INTACTE -- elle ne devait PAS etre touchee -------
  SELECT pg_get_constraintdef(con.oid) INTO v_pk
    FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname='public' AND c.relname='app_affaire_repartition' AND con.contype='p';
  RAISE NOTICE '2. cle primaire: %', v_pk;
  IF v_pk <> 'PRIMARY KEY (app_chaine_id, cote, rang)' THEN
     RAISE EXCEPTION 'CONTROLE 2 ROUGE : la cle primaire a bouge (%)', v_pk; END IF;

  -- 3. le RPC accepte le rang 3 --------------------------------------------
  SELECT pg_get_functiondef(p.oid) INTO v_rpc
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_repartition_commission_set' AND p.prokind='f';
  IF position('not in (''1'', ''2'', ''3'')' in v_rpc) = 0 THEN
     RAISE EXCEPTION 'CONTROLE 3 ROUGE : le RPC refuse encore le rang 3'; END IF;
  IF NOT v_rpc LIKE '%SECURITY DEFINER%' THEN
     RAISE EXCEPTION 'CONTROLE 3 ROUGE : le RPC a perdu SECURITY DEFINER'; END IF;
  RAISE NOTICE '3. RPC        : accepte 1, 2, 3 et garde SECURITY DEFINER';

  -- 4. TEMOIN POSITIF : un rang 3 ENTRE pour de vrai ------------------------
  BEGIN
    INSERT INTO public.app_affaire_repartition(app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage)
    VALUES (v_essai_chaine, 'entree', 3, 'temoin-repetition', 'TEMOIN REPETITION', 10);
    v_rang3_passe := true;
  EXCEPTION WHEN check_violation THEN
    v_rang3_passe := false;
  END;
  RAISE NOTICE '4. rang 3     : %', CASE WHEN v_rang3_passe THEN 'ACCEPTE (temoin positif OK)' ELSE 'REFUSE' END;
  IF NOT v_rang3_passe THEN
     RAISE EXCEPTION 'CONTROLE 4 ROUGE : le rang 3 est encore refuse a l''insertion'; END IF;

  -- 5. TEMOIN INVERSE : un rang 4 reste REFUSE ------------------------------
  BEGIN
    INSERT INTO public.app_affaire_repartition(app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage)
    VALUES (v_essai_chaine, 'sortie', 4, 'temoin-repetition', 'TEMOIN REPETITION', 10);
    v_rang4_refuse := false;
  EXCEPTION WHEN check_violation THEN
    v_rang4_refuse := true;
  END;
  RAISE NOTICE '5. rang 4     : %', CASE WHEN v_rang4_refuse THEN 'REFUSE (temoin inverse OK)' ELSE 'ACCEPTE -- ANORMAL' END;
  IF NOT v_rang4_refuse THEN
     RAISE EXCEPTION 'CONTROLE 5 ROUGE : le rang 4 passe, le garde-fou ne tient plus'; END IF;

  -- 6. rien d'autre n'a bouge ----------------------------------------------
  SELECT count(*) INTO v_lignes_apres FROM public.app_affaire_repartition;
  RAISE NOTICE '6. lignes     : % avant, % pendant l''essai (+1 attendu, annule par le ROLLBACK)',
               v_lignes_avant, v_lignes_apres;
  IF v_lignes_apres <> v_lignes_avant + 1 THEN
     RAISE EXCEPTION 'CONTROLE 6 ROUGE : % lignes au lieu de %', v_lignes_apres, v_lignes_avant + 1; END IF;

  RAISE NOTICE '>>> LES 6 CONTROLES SONT VERTS. Le ROLLBACK qui suit annule les essais.';
END $rep$;

-- ⛔ ON ANNULE : les deux lignes d'essai ne doivent PAS rester.
ROLLBACK;

-- Apres le ROLLBACK, cette lecture doit rendre 0 :
SELECT count(*) AS lignes_d_essai_restantes
  FROM public.app_affaire_repartition
 WHERE hektor_user_id = 'temoin-repetition';
