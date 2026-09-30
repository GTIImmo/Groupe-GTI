-- ═══════════════════════════════════════════════════════════════════════════════
-- A.3-tech etape D -- UN MANDAT PEUT NAITRE DANS L'APP
-- ═══════════════════════════════════════════════════════════════════════════════
-- 30/09/2026. UNE SEULE LIGNE UTILE. Additif, reversible, aucune donnee touchee.
--
-- ─── POURQUOI UN DEFAUT, ET PAS UNE FONCTION ────────────────────────────────────
-- Le patron du projet pour « ca nait dans l'app » est une RPC qui fait nextval
-- puis insert (app_dossier : patch_c9e3, l. 79 ; affaire : patch_commission,
-- l. 99). Ici elle serait inutile : le worker n'a rien a calculer, il a deja
-- toutes les valeurs. Il lui manque UNIQUEMENT un numero.
--
-- En posant la sequence en DEFAUT de la colonne, le worker ecrit une ligne
-- ORDINAIRE, sans numero, et Postgres lui en donne un de la bonne plage. Pas de
-- fonction a maintenir, pas de signature a ne jamais renommer (le piege deja
-- paye : Postgres REFUSE de renommer un parametre d'RPC, il faut DROP+CREATE).
--
-- ─── CE QUE LE DEFAUT NE FAIT PAS ───────────────────────────────────────────────
-- Il ne se declenche QUE sur un INSERT sans app_mandat_id. Le push du run envoie
-- TOUJOURS la colonne (COLONNES_POUSSEES, mandat_ledger.py) : il n'est pas
-- concerne. Et sur un conflit de couple, la ligne existante garde SON numero --
-- « on ne renumerote jamais une ligne connue ».
--
-- ⚠ UN NUMERO DE SEQUENCE EST CONSOMME MEME QUAND LA LIGNE EST EN CONFLIT.
--   C'est sans consequence : la serie n'a pas a etre continue, elle a a etre
--   UNIQUE. (La continuite, elle, est l'affaire du registre LEGAL -- phase 2 --
--   et c'est PROTEXA qui la tient aujourd'hui.)
--
-- ─── LES DEUX SERIES NE SE CROISENT JAMAIS ──────────────────────────────────────
--     sous 1 000 000   le run local, « le plus grand SOUS LA PLAGE + 1 »
--     au-dessus        cette sequence, pour les mandats nes dans l'app
-- C'est le ratage de cette regle qui a coute cinq jours en aout cote affaires :
-- le run regardait le MAX GLOBAL, sautait dans la plage de l'app, et la sequence
-- rendait des numeros DEJA PRIS -- plus aucune creation ne passait, sous un
-- message qui parlait d'autre chose.
-- Cote serveur la regle est appliquee depuis le premier jour, et `adoptes_du_
-- cloud` (mandat_ledger.py) reprend le numero du cloud au lieu d'en fabriquer un
-- second : sans lui, le push heurterait app_mandat_couple_unique et LE RUN
-- S'ARRETERAIT LA -- ce qui est arrive deux nuits de suite les 01 et 02/09.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- ALTER TABLE public.app_mandat ALTER COLUMN app_mandat_id DROP DEFAULT;
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_mandat
  ALTER COLUMN app_mandat_id SET DEFAULT nextval('public.app_mandat_id_app_seq');

COMMENT ON COLUMN public.app_mandat.app_mandat_id IS
  'NOTRE numero de mandat. Sous 1 000 000 : distribue par le run local, qui ne '
  'regarde JAMAIS le MAX global. Au-dessus : app_mandat_id_app_seq, posee en '
  'DEFAUT de cette colonne depuis le 30/09 -- le worker ecrit une ligne sans '
  'numero et Postgres lui en donne un de la bonne plage. Les deux series ne se '
  'croisent jamais ; c''est la regle qui a manque a l''affaire en aout.';
