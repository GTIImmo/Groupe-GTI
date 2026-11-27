-- INVERSE de patch_socle_du_protocole_en_base_2026-11-27 : retire les 5 tables (et ce qu'elles portent).
-- Il ne juge que SA part (lecon 31) : il ne touche a aucune autre table. ⚠ Le socle.sqlite local reste la, intact.

begin;
drop table if exists public.app_classeur_protocole_passage, public.app_classeur_protocole_verdict, public.app_classeur_protocole_temoin, public.app_classeur_protocole_motif, public.app_classeur_protocole_fichier;
do $$ begin
  if to_regclass('public.app_classeur_protocole_passage') is not null or to_regclass('public.app_classeur_protocole_verdict') is not null or to_regclass('public.app_classeur_protocole_temoin') is not null or to_regclass('public.app_classeur_protocole_motif') is not null or to_regclass('public.app_classeur_protocole_fichier') is not null then raise exception '⛔ inverse : une table reste'; end if;
  raise notice '✅ inverse : les 5 tables sont retirees';
end $$;
commit;
