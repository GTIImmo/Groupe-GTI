-- =====================================================================
-- RETOUR ARRIERE du patch 3c (pieces 1 et 2) -- 2026-10-13
-- Rend la vue, l'alerte et les droits EXACTEMENT a leur etat d'avant, supprime
-- le RPC de saisie, et vide notre colonne.
--
-- ⚠ LA COLONNE `mandat_date_cloture_app` EST CONSERVEE, VIDE.
--    Un `drop column` detruirait toutes les clotures saisies dans l'app depuis
--    le patch -- une donnee que PERSONNE d'autre ne porte (Hektor ne la recoit
--    pas). Vidée, elle est inerte : plus rien ne la lit, puisque la vue et
--    l'alerte sont revenues a leur version d'avant.
--    Pour la supprimer vraiment, apres s'etre assure qu'aucune saisie n'est a
--    garder -- et le carnet app_mandat_champ_app en garde une trace, lui :
--        alter table public.app_mandat_register_current
--          drop column if exists mandat_date_cloture_app;
--
-- ⚠ LE CARNET N'EST PAS TOUCHE. Les lignes `origine='cloture_app'` restent :
--    c'est la source de verite, et le worker y ecrivait deja avant ce patch.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. LA VUE. Un `CREATE OR REPLACE VIEW` ne sait pas RETIRER des colonnes :
--    il faut DROP puis CREATE -- et donc RENDRE LES DROITS, que le drop emporte.
--    Droits releves le 13/10 avant le patch :
--        postgres=arwdDxtm | authenticated=r | service_role=arwdDxtm
--        reloptions : security_invoker=true
--    ⚠ `anon` n'en avait AUCUN. On ne lui en donne pas.
-- ---------------------------------------------------------------------
DO $retour$
DECLARE
  c_emp constant text := '5c64469d579405d028554350d3d44883';

  v_def text; v_ancien text;
  a text; b text; n int;
BEGIN
  v_def := replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true),
                   chr(13), '');

  IF position('mandat_date_cloture_app' in v_def) = 0 THEN
    RAISE EXCEPTION 'STOP : la vue ne porte pas le patch -- rien a defaire';
  END IF;

  -- R2 inverse : on retire les deux colonnes nues.
  b := '    mandants_json,' || chr(10)
       || '    mandat_date_cloture_app,' || chr(10)
       || '    mandat_date_cloture AS mandat_date_cloture_hektor' || chr(10)
       || '   FROM app_mandat_register_current r;';
  a := '    mandants_json' || chr(10) || '   FROM app_mandat_register_current r;';
  n := (length(v_def) - length(replace(v_def, b, ''))) / length(b);
  IF n <> 1 THEN
    RAISE EXCEPTION 'STOP : ancre R2 inverse trouvee % fois, il en faut 1', n;
  END IF;
  v_ancien := replace(v_def, b, a);

  -- R1 inverse : la colonne redevient celle de Hektor, nue.
  b := chr(10) || '    COALESCE(NULLIF(btrim(mandat_date_cloture_app), ''''::text), mandat_date_cloture) AS mandat_date_cloture,' || chr(10);
  a := chr(10) || '    mandat_date_cloture,' || chr(10);
  n := (length(v_ancien) - length(replace(v_ancien, b, ''))) / length(b);
  IF n <> 1 THEN
    RAISE EXCEPTION 'STOP : ancre R1 inverse trouvee % fois, il en faut 1', n;
  END IF;
  v_ancien := replace(v_ancien, b, a);

  -- LE CONTROLE QUI AUTORISE LE DROP : on ne detruit la vue que si on sait
  -- rendre EXACTEMENT celle d'avant, caractere pour caractere.
  IF md5(v_ancien) <> c_emp THEN
    RAISE EXCEPTION 'STOP : la vue reconstruite porte % au lieu de % -- on ne detruit rien',
      md5(v_ancien), c_emp;
  END IF;

  DROP VIEW public.app_registre_mandats_current;
  EXECUTE 'create view public.app_registre_mandats_current '
          || 'with (security_invoker=on) as ' || v_ancien;

  -- LES DROITS, rendus a l'identique.
  EXECUTE 'grant select on public.app_registre_mandats_current to authenticated';
  EXECUTE 'grant all    on public.app_registre_mandats_current to service_role';

  IF md5(replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true),
                 chr(13), '')) <> c_emp THEN
    RAISE EXCEPTION 'STOP : apres remise en place la vue porte une autre empreinte';
  END IF;

  RAISE NOTICE 'OK vue rendue a l''identique (%)', c_emp;
END $retour$;

-- ---------------------------------------------------------------------
-- 2. L'ALERTE « MANDAT ECHU », rendue a sa version d'avant.
-- ---------------------------------------------------------------------
DO $retour$
DECLARE
  c_sig constant text := 'public.app_generate_mandat_echu_alerts()';
  c_emp constant text := 'd45b9290d12bfca81f37713c4d361150';

  v_def text; a text; b text; n int;
BEGIN
  v_def := replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '');

  IF position('mandat_date_cloture_app' in v_def) = 0 THEN
    RAISE EXCEPTION 'STOP alerte : elle ne porte pas le patch -- rien a defaire';
  END IF;

  b := replace($b1$          and (nullif(btrim(coalesce(r.mandat_date_cloture_app, '')), '') is not null
               or nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null)$b1$,
               chr(13), '');
  a := replace($a1$          and nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null$a1$,
               chr(13), '');

  n := (length(v_def) - length(replace(v_def, b, ''))) / length(b);
  IF n <> 2 THEN
    RAISE EXCEPTION 'STOP alerte : ancre inverse trouvee % fois, il en faut 2', n;
  END IF;

  EXECUTE replace(v_def, b, a);

  IF md5(replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '')) <> c_emp THEN
    RAISE EXCEPTION 'STOP alerte : apres remise en place l''empreinte est % au lieu de %',
      md5(replace(pg_get_functiondef(c_sig::regprocedure), chr(13), '')), c_emp;
  END IF;

  RAISE NOTICE 'OK alerte rendue a l''identique (%)', c_emp;
END $retour$;

-- ---------------------------------------------------------------------
-- 3. LE RPC DE SAISIE : supprime.
-- ---------------------------------------------------------------------
drop function if exists public.app_set_mandat_cloture_optimistic(text, text, text);

-- ---------------------------------------------------------------------
-- 4. NOTRE COLONNE : vidée, conservée (voir l'avertissement en tete).
-- ---------------------------------------------------------------------
update public.app_mandat_register_current
   set mandat_date_cloture_app = null
 where mandat_date_cloture_app is not null;

comment on column public.app_mandat_register_current.mandat_date_cloture_app is
  'INERTE depuis le retour arriere du 13/10/2026 : plus rien ne la lit. '
  'Conservee vide pour ne pas detruire une saisie ; voir le script INVERSE.';

notify pgrst, 'reload schema';

COMMIT;
