-- =====================================================================
-- RETOUR ARRIERE de la charge des honoraires au mandat     02/11/2026
--
-- ⚠ LECON 31 : un retour arriere ne juge que SA part. Il verifie d'abord
--   qu'il ne reste aucune trace de ce qu'il devait retirer, et il NE TOUCHE PAS
--   a la cloture de mandat, qui partage la meme table et la meme vue.
--
-- ⭐ CE QU'IL NE DETRUIT PAS, ET C'EST VOULU : le carnet app_mandat_champ_app.
--   Les charges deja saisies y restent. C'est tout l'interet du patron : la
--   verite vit au carnet, la colonne n'est qu'un reflet. Recoller le patch
--   principal puis appeler app_reposer_charge_mandat_app() les remettrait
--   toutes a l'ecran.
-- =====================================================================

BEGIN;

drop function if exists public.app_set_mandat_charge_optimistic(text, text, text);
drop function if exists public.app_reposer_charge_mandat_app(text, int);

-- LA VUE, refaite depuis elle-meme SANS la colonne.
DO $do$
DECLARE
  v_def   text;
  v_ancre text := ',' || chr(10) || '    mandat_charge_honoraires_app';
  v_occ   int;
BEGIN
  v_def := replace(pg_get_viewdef('public.app_registre_mandats_current'::regclass, true),
                   chr(13), '');

  IF position('mandat_charge_honoraires_app' in v_def) = 0 THEN
    RAISE NOTICE 'la vue ne cite pas la colonne : rien a defaire';
  ELSE
    v_occ := (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre);
    IF v_occ <> 1 THEN
      RAISE EXCEPTION 'STOP : l''ancre inverse est presente % fois, il en faut 1', v_occ;
    END IF;
    v_def := replace(v_def, v_ancre, '');
    EXECUTE 'CREATE OR REPLACE VIEW public.app_registre_mandats_current AS ' || v_def;
    RAISE NOTICE 'la vue ne porte plus mandat_charge_honoraires_app';
  END IF;
END $do$;

alter table public.app_mandat_register_current
  drop column if exists mandat_charge_honoraires_app;

-- LES CONTROLES DU RETOUR ARRIERE.
DO $do$
DECLARE
  v_col int; v_vue int; v_f int; v_cloture int; v_carnet bigint;
BEGIN
  SELECT count(*) INTO v_col FROM information_schema.columns
   WHERE table_schema='public' AND table_name='app_mandat_register_current'
     AND column_name='mandat_charge_honoraires_app';
  IF v_col <> 0 THEN RAISE EXCEPTION 'INVERSE : la colonne est encore la'; END IF;

  SELECT count(*) INTO v_vue FROM information_schema.columns
   WHERE table_schema='public' AND table_name='app_registre_mandats_current'
     AND column_name='mandat_charge_honoraires_app';
  IF v_vue <> 0 THEN RAISE EXCEPTION 'INVERSE : la vue la cite encore'; END IF;

  SELECT count(*) INTO v_f FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname='public'
     AND p.proname in ('app_reposer_charge_mandat_app','app_set_mandat_charge_optimistic');
  IF v_f <> 0 THEN RAISE EXCEPTION 'INVERSE : % fonction(s) restante(s)', v_f; END IF;

  -- ⭐ TEMOIN INVERSE : la cloture est INTACTE.
  SELECT count(*) INTO v_cloture FROM information_schema.columns
   WHERE table_schema='public' AND table_name='app_registre_mandats_current'
     AND column_name in ('mandat_date_cloture','mandat_date_cloture_app',
                         'mandat_date_cloture_hektor');
  IF v_cloture <> 3 THEN
    RAISE EXCEPTION 'INVERSE : la cloture a ete abimee (% sur 3)', v_cloture;
  END IF;

  SELECT count(*) INTO v_carnet FROM public.app_mandat_champ_app
   WHERE champ = 'charge_commission';
  RAISE NOTICE 'RETOUR ARRIERE COMPLET. La cloture est intacte (3/3). % ligne(s) de charge GARDEE(S) au carnet.', v_carnet;
END $do$;

COMMIT;
