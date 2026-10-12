-- =====================================================================
-- RETOUR ARRIERE du patch « ARCHIVER + NEGOCIATEUR sur un vendu / clos » -- 12/10/2026
-- Patch : supabase/patch_chantier3_repli_index_archiver_negociateur_2026-10-12.sql
--
-- Il retire le bloc de CHACUNE des deux fonctions et ne reexecute QUE si le texte obtenu est,
-- au caractere pres, celui d'avant le patch. Si l'une des deux refuse, la transaction annule
-- les DEUX.
--
-- ⚠ CE QUI N'EST PAS DEFAIT : rien d'autre. Ce script ne touche aucune donnee. Les travaux
--   deja crees pour des biens vendus/clos restent -- ils portent un VRAI numero de dossier.
-- =====================================================================

BEGIN;

DO $inverse$
DECLARE
  sigs constant text[] := ARRAY[
    'public.app_archive_annonce_optimistic(bigint,jsonb,integer)',
    'public.app_assign_negotiator_optimistic(bigint,text,jsonb,integer)'];
  emps constant text[] := ARRAY[
    'b9bf9d40d32be0a16959ee4a35548ac9',
    '275f8d9d1000fb4100889c10314c8cf5'];

  c_deb constant text := '  -- @repli-debut';
  c_fin constant text := '  -- @repli-fin';
  c_ancre text;
  v_def text; v_retour text; v_apres text;
  i int; n int; j int;
BEGIN
  c_ancre := replace($anc$  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode = '22023'; end if;$anc$, chr(13), '');

  FOR i IN 1 .. 2 LOOP
    v_def := replace(pg_get_functiondef(sigs[i]::regprocedure), chr(13), '');

    IF position(c_deb in v_def) = 0 THEN
      IF md5(v_def) = emps[i] THEN
        RAISE NOTICE 'RIEN A FAIRE : % est deja revenue a l''identique (%)', sigs[i], emps[i];
        CONTINUE;
      END IF;
      RAISE EXCEPTION 'STOP : % n''a pas le repli, et son empreinte (%) n''est pas celle d''avant (%)',
        sigs[i], md5(v_def), emps[i];
    END IF;

    n := (length(v_def) - length(replace(v_def, c_deb, ''))) / length(c_deb);
    IF n <> 1 THEN RAISE EXCEPTION 'STOP : dans %, repere de debut trouve % fois', sigs[i], n; END IF;
    n := (length(v_def) - length(replace(v_def, c_fin, ''))) / length(c_fin);
    IF n <> 1 THEN RAISE EXCEPTION 'STOP : dans %, repere de fin trouve % fois', sigs[i], n; END IF;

    -- on remplace tout le bloc (du repere d'ouverture au repere de fermeture inclus) par
    -- la garde d'origine
    n := position(c_deb in v_def);
    j := position(c_fin in v_def);
    v_retour := substr(v_def, 1, n - 1) || c_ancre || substr(v_def, j + length(c_fin));

    IF md5(v_retour) <> emps[i] THEN
      RAISE EXCEPTION 'STOP : pour %, en retirant le bloc on obtient % au lieu de % -- retrait annule',
        sigs[i], md5(v_retour), emps[i];
    END IF;

    EXECUTE v_retour;

    v_apres := replace(pg_get_functiondef(sigs[i]::regprocedure), chr(13), '');
    IF md5(v_apres) <> emps[i] THEN
      RAISE EXCEPTION 'STOP : apres retrait, % porte % au lieu de %', sigs[i], md5(v_apres), emps[i];
    END IF;
    IF position('@repli' in v_apres) > 0 THEN
      RAISE EXCEPTION 'STOP : le repli est encore dans %', sigs[i];
    END IF;

    RAISE NOTICE 'OK : % -- repli retire, revenue a l''identique (%)', sigs[i], md5(v_apres);
  END LOOP;
END $inverse$;

COMMIT;
