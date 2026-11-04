-- Retour arrière de patch_registre_negociateurs_nuit_2026-11-04.sql (registre des négociateurs, étape 2).
-- Retire la fonction de nuit, ses aides, la vue des signaux, la RPC « vu » et la clé de battement ; rend au journal sa
-- forme de l'étape 1. ⚠ Les lignes que la nuit a écrites au journal partent avec ses colonnes nouvelles : les sauver
-- d'abord si une nuit a tourné en mode 1 (create table … as select * from app_negociateur_journal).
-- Le registre lui-même (personnes, fiches) n'est PAS touché.
drop view if exists public.app_v_negociateur_signaux;
drop function if exists public.app_negociateur_signal_traiter(bigint);
drop function if exists public.app_negociateur_registre_maintenir(text[], boolean);
drop function if exists public.app_neg_adopter(text, text, text, text, text, text);
drop function if exists public.app_neg_email_partage(text);
drop function if exists public.app_neg_cle_agence(text);
drop function if exists public.app_neg_cle_nom(text);
delete from public.app_worker_registry where worker_key = 'phase2.registre_negociateurs';
delete from public.app_negociateur_journal where app_fiche_id is null;
drop index if exists public.app_negociateur_journal_ouverts_idx;
alter table public.app_negociateur_journal
    drop column if exists app_personne_id, drop column if exists evenement, drop column if exists a_signaler,
    drop column if exists nuit, drop column if exists traite_le, drop column if exists traite_par,
    alter column app_fiche_id set not null;
select (select count(*) from pg_proc where proname like 'app_neg%' and proname <> 'app_negociateur_signal_traiter') as fonctions_restantes,
       (select count(*) from information_schema.columns where table_name = 'app_negociateur_journal') as colonnes_du_journal;
