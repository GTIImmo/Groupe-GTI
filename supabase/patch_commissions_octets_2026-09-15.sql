-- =====================================================================
-- SAVOIR QUE LA PAGE DES COMMISSIONS EST REVENUE VIDE      15/09/2026
-- Chantier C.19-d, tache 3.2e, lot 5 -- etape 2 du plan de sortie.
-- =====================================================================
--
-- CE QUI EST ARRIVE DANS LA NUIT DU 14 AU 15
-- ------------------------------------------
-- La 2e requete de l'assistant (`step=2`, la page des commissions) est partie,
-- a repondu, et `contenuDeLEtape` n'en a rien tire. Le lecteur a rendu
-- `commissions = 0`, aucun intervenant, et la piece a ete comptee `done`.
-- Pendant 64 minutes, de 20:03 a 21:07 UTC. Puis la couverture est remontee
-- SEULE a 100 %.
--
-- PREUVE QUE C'EST UN MECANISME ET NON LES DONNEES -- l'annee 2017 est a cheval
-- sur la fenetre, donc c'est la MEME population des deux cotes :
--     dans la fenetre   290 ventes lues   35 % avec commission
--     hors fenetre      162 ventes lues   98 %
-- Sur toute la fenetre : 1 228 lues, 350 seulement portent leur commission,
-- contre 97 % partout ailleurs. ~880 ventes sont donc a relire.
--
-- POURQUOI CETTE COLONNE, ET PAS UN FILTRE SUR `intervenants_json IS NULL`
-- -----------------------------------------------------------------------
-- ⚠ 14 % DES VENTES N'ONT LEGITIMEMENT PERSONNE D'ATTRIBUE. « Part Reseau »
--   prend alors tout, et c'est un etat VRAI, pas un trou. Un selecteur fonde sur
--   l'absence d'intervenants les relirait a chaque passage, indefiniment, sans
--   jamais rien trouver de plus -- et il noierait les vraies pieces manquantes
--   dans un millier de fausses.
--
-- ➡ SEUL LE COMPTE D'OCTETS DISTINGUE LES DEUX CAS :
--       NULL  la page n'a pas ete demandee (lecture d'avant le 14/09,
--             ou `--sans-commissions`)
--       0     DEMANDEE, ET REVENUE VIDE   <- le signal qui manquait
--       > 0   lue ; s'il n'y a pas d'intervenant, c'est que personne n'est
--             attribue, et c'est la verite
--
-- ⭐ CE QUE CA CHANGE POUR TOUJOURS. Le trou devient AUTO-REPARABLE : une page
--   qui se vide une nuit est reprise par l'entretien du lendemain, sans que
--   personne ait a compter des lignes en base un matin. C'est la lecon la plus
--   chere de la journee -- le lecteur RENDAIT deja cette mesure, et c'est le
--   pilote qui la jetait. Le defaut n'etait pas d'ignorer la panne, c'etait de
--   jeter la seule mesure qui l'aurait montree.
--
-- ⚠ ELLE NE VAUT QUE POUR LA LECTURE CONSOLE. Le worker, lui, traverse les trois
--   pages quand il ecrit ; il ne renseigne pas cette colonne et n'a pas a le
--   faire. Une ligne ecrite par le worker gardera donc NULL -- ce qui est exact :
--   on ne sait pas ce que SA page 2 pesait.
--
-- RETOUR ARRIERE : ALTER TABLE ... DROP COLUMN. Rien ne la lit encore au moment
-- ou ce patch est applique ; le pilote l'ecrira ensuite, le selecteur la lira.
-- =====================================================================

ALTER TABLE public.app_affaire_console
    ADD COLUMN IF NOT EXISTS commissions_octets integer;

COMMENT ON COLUMN public.app_affaire_console.commissions_octets IS
    'Taille du contenu rendu par l''etape 2 de l''assistant (la page des '
    'commissions), en caracteres. NULL = page non demandee · 0 = DEMANDEE ET '
    'REVENUE VIDE · > 0 = lue. C''est le SEUL moyen de distinguer « la page s''est '
    'videe » de « page lue, personne d''attribue » -- et 14 % des ventes sont '
    'legitimement dans le second cas. Mesure du 15/09 : ~880 ventes perdues entre '
    '20:03 et 21:07 UTC sans qu''aucune erreur ne soit levee.';

-- Le selecteur `--sans-commission` du pilote cherche exactement ceci : une piece
-- LUE dont la page 2 est revenue vide. L'index le rend immediat sur 16 831 lignes
-- et ne coute rien -- il ne porte que les lignes concernees.
CREATE INDEX IF NOT EXISTS app_affaire_console_page2_vide_idx
    ON public.app_affaire_console (kind, app_affaire_id)
    WHERE commissions_octets = 0;
