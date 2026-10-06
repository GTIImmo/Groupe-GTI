-- ============================================================================
-- app_mandat PERD SA COLONNE `montant`                              06/10/2026
-- ============================================================================
-- A APPLIQUER APRES le retrait de la colonne en local, et apres le deploiement
-- du code (mandat_ledger.py ne la nomme plus ni au schema, ni a l'INSERT, ni
-- dans COLONNES_POUSSEES). L'ordre n'est pas critique dans ce sens-la : le push
-- filtre ses colonnes sur celles qui existent EN LOCAL
-- (`{c: r[c] for c in COLONNES_POUSSEES if c in r.keys()}`), donc une colonne
-- Supabase orpheline ne casse rien -- elle rancit, c'est tout. C'est bien pour
-- cela qu'on la retire.
--
-- POURQUOI ELLE PART
-- ------------------
-- Elle etait une RECOPIE EXACTE de versions_json[0].montant. Mesure du 06/10 sur
-- les 26 839 lignes : 26 839 identiques, 0 remplie d'un seul cote, 0 divergente.
-- Et personne ne la lisait :
--   · le registre prend ses versions dans le blob -- charger_mandats_depuis_app_mandat
--     ne SELECTe que hektor_annonce_id, numero_mandat et versions_json
--   · le front n'interroge JAMAIS la table app_mandat (0 occurrence de
--     from('app_mandat') dans apps/hektor-v1/src)
--   · aucune vue, aucune regle, aucun index ne la nomme -- verifie sur
--     pg_depend / pg_rewrite / pg_indexes le 06/10 : ZERO dependance
-- Et depuis le 06/10 le registre n'affiche plus de montant de mandat du tout :
-- il affiche LE PRIX DE L'ANNONCE (export_app_payload.normalize_history_version).
--
-- ⚠ RIEN N'EST PERDU. Le chiffre reste dans `versions_json`, colonne voisine de
--   la meme table, cote serveur ET cote Supabase. Le retour arriere est donc
--   complet (voir tout en bas), et le filet local est le fichier
--   montants_app_mandat_avant_drop.json, les 26 839 triplets
--   (hektor_annonce_id, numero_mandat, montant).
--
-- ⚠ CREATE OR REPLACE / ALTER, JAMAIS DROP TABLE : les GRANT de ce projet ne
--   sont pas uniformes (memoire renommer-parametre-rpc-supabase-piege). Un
--   DROP COLUMN ne touche pas aux GRANT de la table -- verifier quand meme
--   apres coup que anon / authenticated / service_role sont intacts.
-- ============================================================================
-- ⭐ APPLIQUE LE 06/10/2026 -- migration `app_mandat_sans_montant_2026_10_06`
--    AVANT  : 26 839 lignes · 24 182 montants remplis · 0 divergence avec le blob
--    APRES  : 26 839 lignes · 24 colonnes · `montant` absente
--             le chiffre toujours dans versions_json sur 24 182 lignes
--    GRANT  : anon / authenticated / service_role / postgres INTACTS, verifie
-- ⚠ LE COTE LOCAL N'EST PAS FAIT : l'ALTER TABLE sur phase2.sqlite a ete refuse
--   a l'assistant (garde-fou « irreversible »). La colonne locale rancit sans
--   consequence -- le push ne l'envoie plus (COLONNES_POUSSEES) et rien ne la lit.
--   La commande est dans la reponse du 06/10 au soir.
-- ============================================================================

-- ── 1. L'ETAT AVANT, a lire et a garder ────────────────────────────────────
select count(*) as lignes,
       count(montant) as montant_rempli,
       count(*) filter (
         where coalesce(montant, '') is distinct from
               coalesce((versions_json::jsonb -> 0 ->> 'montant'), '')
       ) as divergences_avec_le_blob
  from public.app_mandat;
-- ATTENDU : 26 839 lignes · 24 182 remplies · 0 divergence.
-- ⛔ SI `divergences_avec_le_blob` N'EST PAS 0, NE PAS CONTINUER : la colonne
--    porterait alors quelque chose que le blob n'a pas, et ce patch la perdrait.

-- ── 2. LE RETRAIT ──────────────────────────────────────────────────────────
alter table public.app_mandat drop column if exists montant;

-- ── 3. L'ETAT APRES ────────────────────────────────────────────────────────
select count(*) as lignes,
       count(*) filter (where (versions_json::jsonb -> 0 ->> 'montant') is not null)
         as le_chiffre_est_toujours_dans_le_blob
  from public.app_mandat;
-- ATTENDU : 26 839 lignes, et le chiffre toujours la.

select column_name
  from information_schema.columns
 where table_schema = 'public' and table_name = 'app_mandat'
 order by ordinal_position;
-- ATTENDU : 24 colonnes, plus de `montant`.

-- ── RETOUR ARRIERE, si jamais ──────────────────────────────────────────────
--   alter table public.app_mandat add column montant text;
--   update public.app_mandat
--      set montant = versions_json::jsonb -> 0 ->> 'montant';
--   -- puis remettre "montant" dans COLONNES_POUSSEES et dans le schema local
--   -- (mandat_ledger.py), et relancer `--refresh --push`.
