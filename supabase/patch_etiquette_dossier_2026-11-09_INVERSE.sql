-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE DE L'ÉTIQUETTE DE DOSSIER                        09/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- L'audit du 29/10 promettait « le retour arrière est gratuit ». Il l'est tant
-- que le patch est DORMANT : rien n'est posé, donc rien n'est perdu.
--
-- ⛔⛔ IL NE L'EST PLUS APRÈS B3. Une fois les étiquettes posées, ce fichier
--     EFFACE DES IDENTIFIANTS, et un identifiant effacé ne se refait pas
--     identique : la pose suivante tirera d'autres UUID. Si la colonne
--     « affair_uuid » du classeur en porte déjà, le lien est rompu.
--
-- ➡ AVANT DE LE LANCER, LIRE CE CONTRÔLE. S'il ne rend pas 0, s'arrêter.
--   select count(app_dossier_uuid) as etiquettes_posees,
--          (select count(*) from public.app_dossier_etiquette_journal) as journal
--   from public.app_affaire_ledger;
--
-- ⚠ ET SI DES ÉTIQUETTES SONT POSÉES et qu'on veut quand même revenir : faire
--   d'abord une sauvegarde datée, comme pour tout geste destructif.
--     create table app_affaire_ledger_etiquettes_sauvegarde_20261109 as
--       select app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero
--       from public.app_affaire_ledger where app_dossier_uuid is not null;
-- ═══════════════════════════════════════════════════════════════════════════

drop policy if exists app_dossier_etiquette_journal_lecture
  on public.app_dossier_etiquette_journal;

drop function if exists public.app_poser_etiquettes_dossier(integer, boolean);
drop function if exists public.app_dossier_annee_ouverture(bigint);
drop function if exists public.app_dossier_numero_format(integer, integer);

drop table if exists public.app_dossier_etiquette_journal;
drop table if exists public.app_dossier_numero_compteur;

drop index if exists public.app_affaire_ledger_dossier_uuid_idx;

alter table public.app_affaire_ledger
  drop column if exists app_dossier_uuid,
  drop column if exists app_dossier_numero;

-- ⓘ Côté local, retirer aussi les deux noms de COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS
--   dans phase2/sync/affaire_ledger.py, sinon le SELECT de redescente les
--   demande à Supabase qui ne les a plus. Le filet d'ordre (l. ~2204) demande
--   à Supabase ce qu'il a, donc la nuit ne tombe pas -- mais autant être net.

-- Témoin : les deux colonnes ont bien disparu (attendu 0), et la table existe
-- toujours (témoin positif, attendu 45).
select 'retour arriere' as controle,
       count(*) filter (where column_name in ('app_dossier_uuid','app_dossier_numero'))
         as colonnes_etiquette_attendu_0,
       count(*) as colonnes_du_registre_temoin_positif
from information_schema.columns
where table_schema = 'public' and table_name = 'app_affaire_ledger';
