-- ═══════════════════════════════════════════════════════════════════════════════
-- 2.7 -- D'OU VIENT LE MANDAT D'UNE TRANSACTION                    16/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnee de la migration `ledger_mandat_origine`.
--
-- ─── POURQUOI CETTE COLONNE ───
-- Le registre porte deja `numero_mandat`, mais seulement quand HEKTOR le donne :
-- 88 % des ventes, 74 % des compromis, et 2 % des offres -- soit 48 % du registre.
-- La cascade de 2.7 (affaire_ledger.py, `_mandat_de_la_transaction`) comble le
-- reste par DEDUCTION. Sans cette colonne, un mandat deduit serait indiscernable
-- d'un mandat donne.
--
-- ⚠ C'EST LA MEME LECON QUE TROIS AUTRES CORRECTIFS DU MEME JOUR : le gel du
--   contrat d'autorite, la photo de la saisie, le verdict du carnet. On distingue
--   TOUJOURS ce qu'on sait de ce qu'on infere -- sinon l'inference devient un
--   fait, et plus personne ne peut la remettre en cause.
--
-- ─── LES VALEURS, ET LEUR RENDEMENT MESURE LE 16/09 ───
--     hektor           Hektor l'a envoye                         14 858   48,0 %
--     deduit_unique    l'annonce n'a qu'UN mandat                 +8 305  -> 74,8 %
--     deduit_periode   la date tombe entre debut et fin               +4
--     deduit_mandant   un seul mandat porte ce vendeur                +0
--     indetermine      on ne devine pas                               21
--     NULL             l'annonce n'a AUCUN mandat au miroir         7 770
--
-- ⚠ LES 7 770 SONT HISTORIQUES : 92 % datent de 2006-2011, des affaires closes
--   depuis quinze ans. Le plafond reel de 2.7 est ~75 %, pas 100 %, et c'est tres
--   bien -- il ne faut pas le prendre pour une dette.
-- ⚠ `deduit_mandant` RAPPORTE ZERO AUJOURD'HUI, et c'est structurel : les 25
--   transactions qui arrivent jusque-la sont TOUTES des offres, et Hektor
--   n'envoie pas de mandants sur une offre. La marche est gardee pour le jour ou
--   il s'y mettra -- comme il vient de le faire pour le mandat des offres.
--
-- ⚠ ON NE DEDUIT JAMAIS `hektor_mandat_id`, SEULEMENT LE NUMERO. L'identifiant
--   sert de CLE ailleurs (le couple annonce+mandat), et Hektor reutilise ses id
--   bas : 342 sont partages entre annonces. Ecrire une deduction dans une colonne
--   qui sert de cle, c'est fabriquer du faux qui voyage.
--
-- RETOUR ARRIERE : la colonne peut rester (personne n'est oblige de la lire), ou
-- `ALTER TABLE public.app_affaire_ledger DROP COLUMN mandat_origine`.
-- ⚠ Le run local la pousse avec le reste (le push fait SELECT *), et la descente
--   l'absorbe seule : elle refait la doublure depuis la spec OpenAPI.
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_affaire_ledger
  ADD COLUMN IF NOT EXISTS mandat_origine text;

COMMENT ON COLUMN public.app_affaire_ledger.mandat_origine IS
  'D''ou vient numero_mandat (2.7, 16/09/2026) : hektor (il l''a envoye) · '
  'deduit_unique (l''annonce n''a qu''un mandat) · deduit_periode (la date tombe '
  'dans ses bornes) · deduit_mandant (un seul mandat porte ce vendeur) · '
  'indetermine (on ne devine pas). Sans elle, un mandat DEDUIT serait '
  'indiscernable d''un mandat DONNE.';
