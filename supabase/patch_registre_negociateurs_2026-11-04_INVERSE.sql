-- Retour arrière de patch_registre_negociateurs_2026-11-04.sql. Le registre n'est lu par personne à l'étape 1 :
-- le retirer ne touche rien d'autre. ⚠ Une fois l'étape 2 posée (la nuit écrit le journal), le journal partirait avec.
drop table if exists public.app_negociateur_journal;
drop table if exists public.app_negociateur_fiche;
drop table if exists public.app_negociateur_personne;
select count(*) as tables_restantes from pg_class where relname in ('app_negociateur_personne', 'app_negociateur_fiche', 'app_negociateur_journal');
