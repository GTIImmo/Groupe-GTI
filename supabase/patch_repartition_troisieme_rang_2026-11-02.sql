-- ===========================================================================
-- JUSQU'A TROIS INTERVENANTS PAR COTE DANS LA REPARTITION          02/11/2026
-- ===========================================================================
-- Demande de Frederic (02/11) : « dans la modale mettre un champ entree un
--   sortie et ajouter un + pour ajouter des intervenants jusqu'a 3 par cote ».
-- Besoin reel : 13 lignes du classeur portent TROIS negociateurs (75/12,5/12,5,
--   50/25/25 huit fois, 25/50/25, 30/30/40), de juillet 2018 a janvier 2026.
--
-- ⭐⭐ LA CLE PRIMAIRE N'EST PAS TOUCHEE. Elle vaut (app_chaine_id, cote, rang)
--   et CONTIENT DEJA LE RANG : `rang = 3` y entre sans aucune modification. Elle
--   garantit « un seul nom par emplacement », ce qu'on garde.
--   ⚠ J'avais annonce « trois verrous dont la cle primaire » le 01/11 : c'etait
--     FAUX, et ca grossissait le risque. Il y en a DEUX, et aucun ne reecrit une
--     ligne : les 16 106 lignes respectent deja la regle elargie.
--
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE :
--   1. CHECK app_affaire_repartition_rang_chk : ARRAY[1, 2] -> ARRAY[1, 2, 3]
--   2. RPC app_repartition_commission_set : rang not in ('1','2') -> ('1','2','3')
--      (par remplacement de chaine sur sa PROPRE definition, donc le reste du
--       corps est intouche ; CREATE OR REPLACE conserve les droits authenticated
--       et service_role, verifie le 02/11)
--
-- ⚠ CHAQUE BLOC VERIFIE SON EMPREINTE ET S'ARRETE si quelqu'un est passe avant.
-- ⚠ IL EST REJOUABLE : pose deux fois, il ne fait rien la seconde fois.
-- RETOUR ARRIERE : ..._INVERSE.sql    CONTROLES : ..._REPETITION.sql
-- ===========================================================================

BEGIN;

-- 1. LE CHECK ---------------------------------------------------------------
DO $maj1$
DECLARE v_def text;
BEGIN
  SELECT pg_get_constraintdef(con.oid) INTO v_def
    FROM pg_constraint con
    JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'public'
     AND c.relname = 'app_affaire_repartition'
     AND con.conname = 'app_affaire_repartition_rang_chk';

  IF v_def IS NULL THEN
     RAISE EXCEPTION 'le CHECK du rang est introuvable -- ne rien poser';
  END IF;
  IF position('3' in v_def) > 0 THEN
     RAISE NOTICE '[1] le CHECK accepte deja 3 : rien a faire (%)', v_def;
     RETURN;
  END IF;
  IF v_def <> 'CHECK ((rang = ANY (ARRAY[1, 2])))' THEN
     RAISE EXCEPTION 'le CHECK a change, relire avant de poser : %', v_def;
  END IF;

  ALTER TABLE public.app_affaire_repartition
    DROP CONSTRAINT app_affaire_repartition_rang_chk;
  ALTER TABLE public.app_affaire_repartition
    ADD CONSTRAINT app_affaire_repartition_rang_chk CHECK (rang = ANY (ARRAY[1, 2, 3]));

  RAISE NOTICE '[1] CHECK elargi a 1, 2, 3';
END $maj1$;

-- 2. LE RPC -----------------------------------------------------------------
DO $maj2$
DECLARE v_def text; v_neuf text;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public'
     AND p.proname = 'app_repartition_commission_set'
     AND p.prokind = 'f';

  IF v_def IS NULL THEN
     RAISE EXCEPTION 'le RPC app_repartition_commission_set est introuvable';
  END IF;
  IF position('not in (''1'', ''2'', ''3'')' in v_def) > 0 THEN
     RAISE NOTICE '[2] le RPC accepte deja 3 : rien a faire';
     RETURN;
  END IF;
  IF md5(v_def) <> '42cc94fb6fd9d2805ce40fce4faa50a3' THEN
     RAISE EXCEPTION 'le RPC a change (empreinte %, taille %) -- relire avant de poser',
                     md5(v_def), length(v_def);
  END IF;

  v_neuf := replace(v_def, 'not in (''1'', ''2'')', 'not in (''1'', ''2'', ''3'')');
  IF v_neuf = v_def THEN
     RAISE EXCEPTION 'ancre du rang introuvable dans le RPC';
  END IF;

  EXECUTE v_neuf;
  RAISE NOTICE '[2] RPC mis a jour (il accepte desormais le rang 3)';
END $maj2$;

-- 3. CONTROLES --------------------------------------------------------------
DO $ctrl$
DECLARE v_chk text; v_rpc text; v_lignes int; v_chaines int;
BEGIN
  SELECT pg_get_constraintdef(con.oid) INTO v_chk
    FROM pg_constraint con JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname='public' AND c.relname='app_affaire_repartition'
     AND con.conname='app_affaire_repartition_rang_chk';

  SELECT pg_get_functiondef(p.oid) INTO v_rpc
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_repartition_commission_set' AND p.prokind='f';

  SELECT count(*), count(DISTINCT app_chaine_id) INTO v_lignes, v_chaines
    FROM public.app_affaire_repartition;

  RAISE NOTICE '[3] CHECK = % | lignes % sur % chaines', v_chk, v_lignes, v_chaines;

  IF v_chk <> 'CHECK ((rang = ANY (ARRAY[1, 2, 3])))' THEN
     RAISE EXCEPTION 'le CHECK n''est pas celui attendu : %', v_chk; END IF;
  IF position('not in (''1'', ''2'', ''3'')' in v_rpc) = 0 THEN
     RAISE EXCEPTION 'le RPC ne porte pas le rang 3'; END IF;
  -- la cle primaire doit etre INTACTE : c'est tout l'interet du patch
  IF NOT EXISTS (SELECT 1 FROM pg_constraint con
                   JOIN pg_class c ON c.oid = con.conrelid
                   JOIN pg_namespace n ON n.oid = c.relnamespace
                  WHERE n.nspname='public' AND c.relname='app_affaire_repartition'
                    AND con.contype='p'
                    AND pg_get_constraintdef(con.oid) = 'PRIMARY KEY (app_chaine_id, cote, rang)') THEN
     RAISE EXCEPTION 'la cle primaire a bouge -- elle ne devait PAS etre touchee'; END IF;
  -- aucune ligne ne doit avoir disparu (mesure du 01/11)
  IF v_lignes <> 16106 THEN
     RAISE WARNING '[3] lignes = % (16 106 le 01/11) -- normal si la nuit a tourne depuis', v_lignes; END IF;
END $ctrl$;

COMMIT;
