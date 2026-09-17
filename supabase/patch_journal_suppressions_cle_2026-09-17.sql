-- ═══════════════════════════════════════════════════════════════════════════════
-- LE JOURNAL DES SUPPRESSIONS GARDE CHAQUE SUPPRESSION, PAS UNE PAR NUMERO   17/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Complete patch_suppression_transaction_2026-09-16.sql.
--
-- ─── LE DEFAUT, CONSTATE PENDANT L'ESSAI 3.5 ───
-- La cle primaire etait `app_affaire_id` SEUL, et le worker ecrit en
-- `merge-duplicates`. Or UN MEME NUMERO D'APP PEUT PORTER PLUSIEURS TRANSACTIONS
-- SUCCESSIVES : sur l'annonce 24933, le 1001352 a porte le compromis 50084, puis
-- 50086. Resultat mesure le 17/09 :
--     la trace de 50084 a ete ECRASEE par celle de 50086 ;
--     la ligne restante mentait sur la date : `supprime_le` gardait le 16/09
--       08:29 (celle de 50084), alors que 50086 a ete supprime le 17/09 09:41 ;
--     et son `kind` etait vide.
-- Le code promettait pourtant « le journal ne s'efface JAMAIS » et « il repond a
-- la question de Frederic : qui a supprime quoi, et quand ».
--
-- ➡ LA CLE DEVIENT (app_affaire_id, kind, hektor_affaire_id).
--   `kind` en fait partie, et ce n'est pas une precaution : Hektor tient TROIS
--   compteurs qui se telescopent. Le registre porte AUJOURD'HUI le compromis
--   23307 (affaire 3606) ET la vente 23307 (affaire 1001353, supprimee ce matin).
--
-- ─── ET LES TROIS COLONNES DEVIENNENT OBLIGATOIRES ───
-- Une trace sans genre ni numero Hektor ne dit pas CE QUI a ete supprime. Le
-- worker ne peut plus en produire (il les tient de son propre type de travail,
-- plus de la charge -- qui les omettait, c'est la cause des `kind` vides).
--
-- ─── REPARATION DE L'HISTORIQUE, TIREE DES TRAVAUX ET DE LEURS JOURNAUX ───
--     1001352  compromis 50086  la ligne existante : genre, date et auteur corriges
--     1001352  compromis 50084  la trace ecrasee, REINSCRITE
--     1001353  vente     23307  genre et preuve completes
-- ⚠ PAS DE TRACE POUR 50085 (supprime le 16/09 09:02) : sa demande ne portait
--   aucun `app_affaire_id`, le worker a donc journalise « rien a retirer ». On ne
--   devine pas un numero pour remplir une case.
--
-- RETOUR ARRIERE :
--     DELETE FROM app_affaire_supprimee WHERE app_affaire_id = 1001352
--        AND hektor_affaire_id = '50084';
--     ALTER TABLE app_affaire_supprimee DROP CONSTRAINT app_affaire_supprimee_pkey;
--     ALTER TABLE app_affaire_supprimee ADD PRIMARY KEY (app_affaire_id);
--   ⚠ Le worker du 17/09 et affaire_ledger.py filtrent desormais par la cle
--     complete : ils fonctionnent aussi avec l'ancienne cle.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. Les genres manquants, lus dans le type du travail qui a supprime.
UPDATE public.app_affaire_supprimee
   SET kind = 'compromis',
       supprime_le = '2026-09-17 09:41:48.463+00',
       supprime_par = '0548613b-7654-42fa-a65d-d9adc815d2c0',
       preuve = 'Travail caab6a1e (delete_hektor_compromis) : relecture API apres le geste, '
             || 'trouve=false. Reponse Hektor : {"empty":"1"} -- un indice sur l''annonce, '
             || 'pas une preuve. Genre, date et auteur REPARES le 17/09 : la ligne portait '
             || 'ceux de la suppression de 50084, ecrasee par celle-ci.'
 WHERE app_affaire_id = 1001352 AND hektor_affaire_id = '50086';

UPDATE public.app_affaire_supprimee
   SET kind = 'vente',
       preuve = 'Travail 6f6cafec (delete_hektor_vente) : relecture API apres le geste, '
             || 'trouve=false. Reponse Hektor vide -- la vente ne rend rien, succes '
             || 'comme echec. Genre et preuve completes le 17/09.'
 WHERE app_affaire_id = 1001353 AND hektor_affaire_id = '23307';

-- 2. Les colonnes de la cle deviennent obligatoires. Echoue -- et annule tout --
--    s'il reste une trace sans genre ou sans numero : c'est voulu.
ALTER TABLE public.app_affaire_supprimee ALTER COLUMN kind SET NOT NULL;
ALTER TABLE public.app_affaire_supprimee ALTER COLUMN hektor_affaire_id SET NOT NULL;

-- 3. La cle.
ALTER TABLE public.app_affaire_supprimee DROP CONSTRAINT app_affaire_supprimee_pkey;
ALTER TABLE public.app_affaire_supprimee
  ADD CONSTRAINT app_affaire_supprimee_pkey PRIMARY KEY (app_affaire_id, kind, hektor_affaire_id);

-- 4. La trace ecrasee, reinscrite. `serveur_aligne = true` : le registre local ne
--    porte plus aucune ligne 50084 (verifie le 17/09).
INSERT INTO public.app_affaire_supprimee
    (app_affaire_id, hektor_annonce_id, kind, hektor_affaire_id, preuve, origine,
     supprime_le, supprime_par, serveur_aligne)
VALUES
    (1001352, 24933, 'compromis', '50084',
     'Travail 384787a6 (delete_hektor_compromis) : relecture API apres le geste, '
     || 'trouve=false. Reponse Hektor : {"empty":"1"}. Trace ECRASEE le 17/09 par la '
     || 'suppression de 50086 (meme numero d''app), REINSCRITE le 17/09 depuis le '
     || 'journal du travail.',
     'geste_app', '2026-09-16 08:29:59.853+00', NULL, true)
ON CONFLICT DO NOTHING;

COMMENT ON CONSTRAINT app_affaire_supprimee_pkey ON public.app_affaire_supprimee IS
    'UNE LIGNE PAR SUPPRESSION. Un meme app_affaire_id peut porter plusieurs '
    'transactions successives (1001352 : 50084 puis 50086), et un meme numero '
    'Hektor existe dans deux genres (23307 compromis ET vente). D''ou les trois.';

COMMIT;
