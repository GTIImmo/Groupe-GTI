-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DES DEUX COLONNES D'ANNULATION            10/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⭐ IL EST GRATUIT TANT QUE LES COLONNES SONT VIDES, et elles le sont a la pose :
--   le patch ne remplit rien.
--
-- ⛔⛔ IL NE L'EST PLUS DES QU'ELLES PORTENT QUELQUE CHOSE. `motif_annulation_app`
--   n'a AUCUNE AUTRE SOURCE : ni le classeur ni Hektor ne portent la raison d'une
--   annulation. Une raison effacee ici est perdue pour toujours -- personne ne
--   peut la reconstituer. `date_annulation_app`, elle, se retrouve au classeur
--   (colonne Z, 896 dates), donc elle est reconstituable.
--
-- ➡ AVANT DE LE LANCER, LIRE CE CONTROLE. S'il ne rend pas 0 et 0, S'ARRETER :
--   select count(date_annulation_app)  as dates_posees,
--          count(motif_annulation_app) as motifs_poses
--     from public.app_affaire_ledger;
--
-- ⚠ ET S'IL Y A DES VALEURS et qu'on veut quand meme revenir : sauvegarde datee
--   d'abord, comme pour tout geste destructif.
--     create table app_affaire_ledger_annulation_sauvegarde_20261110 as
--       select app_affaire_id, app_chaine_id, date_annulation_app, motif_annulation_app
--         from public.app_affaire_ledger
--        where date_annulation_app is not null or motif_annulation_app is not null;
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── LE GARDE-FOU : on refuse d'effacer des valeurs sans le dire ───────────
do $$
declare
  portees int;
begin
  select count(*) into portees
    from public.app_affaire_ledger
   where date_annulation_app is not null or motif_annulation_app is not null;
  if portees > 0 then
    raise exception 'REFUS : % ligne(s) portent une annulation. Faire la sauvegarde datee de l''en-tete, PUIS retirer ce bloc.', portees;
  end if;
  raise notice 'ⓘ les deux colonnes sont vides : le retour arriere ne perd rien.';
end $$;

alter table public.app_affaire_ledger
  drop column if exists date_annulation_app,
  drop column if exists motif_annulation_app;

-- ⓘ Cote local, retirer aussi les deux noms de la boucle de creation ET de
--   COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS dans phase2/sync/affaire_ledger.py, sinon
--   le SELECT de redescente les demande a Supabase qui ne les a plus. Le filet
--   d'ordre demande a Supabase ce qu'il a, donc la nuit ne tombe pas -- mais
--   autant etre net. C'est exactement la situation ou dort app_dossier_uuid.

-- ─── LE TEMOIN : un retour arriere ne juge que SA part (lecon 31) ───────────
-- Attendu : 0 pour les deux colonnes retirees, ET 3 pour le temoin positif --
-- les trois autres colonnes _app doivent etre INTACTES.
select 'retour arriere des colonnes d''annulation' as controle,
       count(*) filter (where column_name in ('date_annulation_app',
                                              'motif_annulation_app'))    as retirees_attendu_0,
       count(*) filter (where column_name in ('charge_commission_app',
                                              'honoraires_entree_app',
                                              'honoraires_sortie_app'))   as temoin_positif_attendu_3,
       count(*)                                                           as colonnes_du_registre
from information_schema.columns
where table_schema = 'public' and table_name = 'app_affaire_ledger';
