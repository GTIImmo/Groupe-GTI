-- ===========================================================================
-- RETOUR ARRIERE DU TROISIEME RANG                                02/11/2026
-- ===========================================================================
-- IL NE JUGE QUE SA PART (lecon 31) : il verifie D'ABORD qu'aucune ligne de
--   rang 3 n'existe. S'il en reste une, il S'ARRETE au lieu de la detruire --
--   c'est de l'argent, et une part supprimee ne se retrouve pas.
--   ➡ Dans ce cas : retirer d'abord ces lignes par l'ecran, puis rejouer.
-- ⚠ LA CLE PRIMAIRE N'EST PAS TOUCHEE ICI NON PLUS (elle ne l'a jamais ete).
-- ===========================================================================

BEGIN;

-- 0. GARDE-FOU : aucune ligne de rang 3 ne doit subsister --------------------
DO $garde$
DECLARE v_rang3 int;
BEGIN
  SELECT count(*) INTO v_rang3 FROM public.app_affaire_repartition WHERE rang = 3;
  RAISE NOTICE '[0] lignes de rang 3 : %', v_rang3;
  IF v_rang3 > 0 THEN
     RAISE EXCEPTION '% ligne(s) de rang 3 existent -- les retirer par l''ecran AVANT le retour arriere', v_rang3;
  END IF;
END $garde$;

-- 1. LE CHECK, remis a 1 et 2 ----------------------------------------------
DO $inv1$
DECLARE v_def text;
BEGIN
  SELECT pg_get_constraintdef(con.oid) INTO v_def
    FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname='public' AND c.relname='app_affaire_repartition'
     AND con.conname='app_affaire_repartition_rang_chk';

  IF v_def = 'CHECK ((rang = ANY (ARRAY[1, 2])))' THEN
     RAISE NOTICE '[1] le CHECK est deja revenu a 1, 2 : rien a faire'; RETURN; END IF;
  IF v_def <> 'CHECK ((rang = ANY (ARRAY[1, 2, 3])))' THEN
     RAISE EXCEPTION 'le CHECK n''est pas celui pose par le patch : %', v_def; END IF;

  ALTER TABLE public.app_affaire_repartition
    DROP CONSTRAINT app_affaire_repartition_rang_chk;
  ALTER TABLE public.app_affaire_repartition
    ADD CONSTRAINT app_affaire_repartition_rang_chk CHECK (rang = ANY (ARRAY[1, 2]));
  RAISE NOTICE '[1] CHECK remis a 1, 2';
END $inv1$;

-- 2. LE RPC, remis a ('1','2') ---------------------------------------------
DO $inv2$
DECLARE v_def text; v_neuf text;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_repartition_commission_set' AND p.prokind='f';

  IF position('not in (''1'', ''2'', ''3'')' in v_def) = 0 THEN
     RAISE NOTICE '[2] le RPC est deja revenu a 1, 2 : rien a faire'; RETURN; END IF;

  v_neuf := replace(v_def, 'not in (''1'', ''2'', ''3'')', 'not in (''1'', ''2'')');
  EXECUTE v_neuf;

  -- il doit redevenir EXACTEMENT celui d'avant le patch
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_repartition_commission_set' AND p.prokind='f';
  IF md5(v_def) <> '42cc94fb6fd9d2805ce40fce4faa50a3' THEN
     RAISE EXCEPTION 'le RPC ne retrouve pas son empreinte d''origine (%) -- quelqu''un l''a modifie entre-temps', md5(v_def);
  END IF;
  RAISE NOTICE '[2] RPC revenu a son empreinte d''origine';
END $inv2$;

-- 3. CONTROLES -------------------------------------------------------------
DO $ctrl$
DECLARE v_chk text; v_lignes int;
BEGIN
  SELECT pg_get_constraintdef(con.oid) INTO v_chk
    FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname='public' AND c.relname='app_affaire_repartition'
     AND con.conname='app_affaire_repartition_rang_chk';
  SELECT count(*) INTO v_lignes FROM public.app_affaire_repartition;
  RAISE NOTICE '[3] CHECK = % | lignes %', v_chk, v_lignes;

  IF v_chk <> 'CHECK ((rang = ANY (ARRAY[1, 2])))' THEN
     RAISE EXCEPTION 'le CHECK n''est pas revenu : %', v_chk; END IF;
  IF EXISTS (SELECT 1 FROM public.app_affaire_repartition WHERE rang = 3) THEN
     RAISE EXCEPTION 'il reste des lignes de rang 3'; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint con
                   JOIN pg_class c ON c.oid = con.conrelid
                   JOIN pg_namespace n ON n.oid = c.relnamespace
                  WHERE n.nspname='public' AND c.relname='app_affaire_repartition'
                    AND con.contype='p'
                    AND pg_get_constraintdef(con.oid) = 'PRIMARY KEY (app_chaine_id, cote, rang)') THEN
     RAISE EXCEPTION 'la cle primaire a bouge'; END IF;
END $ctrl$;

COMMIT;
