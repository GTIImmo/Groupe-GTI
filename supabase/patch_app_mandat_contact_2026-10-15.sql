-- ═══════════════════════════════════════════════════════════════════════════════
-- app_mandat : LE PORTEUR QUAND CE N'EST PAS UNE ANNONCE
-- ═══════════════════════════════════════════════════════════════════════════════
-- 15/10/2026. A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Je ne l'execute pas : c'est une ecriture en base de production.
--
-- ─── POURQUOI ──────────────────────────────────────────────────────────────────
-- Un MANDAT DE RECHERCHE n'est pas porte par un bien : il est porte par la
-- PERSONNE qui nous mandate pour chercher. Hektor le range sur la fiche du
-- CONTACT, et aucune de ses trois routes Mandat ne le sert -- elles sont gelees
-- au n 18339 / 30-01-2026 (verifie par appels reels le 21/07).
--
-- Decision de Frederic, 15/10 : UN SEUL registre, pas une table jumelle.
--
-- ─── LA CLE NE CHANGE PAS, ET C'EST TOUT L'INTERET ─────────────────────────────
-- Un mandat sans annonce portera hektor_annonce_id = '' -- la chaine VIDE,
-- JAMAIS NULL. Eprouve le 15/10 :
--
--     ('',   '18741')  deux fois  ->  REFUSE     l'index unique protege
--     (NULL, '18741')  deux fois  ->  ⚠ ACCEPTE  en SQL, deux NULL ne sont
--                                     jamais egaux : UNIQUE ne protege plus RIEN
--
-- Et on ne peut pas se rabattre sur le numero seul : 8 116 numeros sont portes
-- par PLUSIEURS annonces (le n 1311 sur 13 annonces) -- Hektor les recycle.
--
-- La valeur '' est LIBRE : mesure du 15/10, 0 des 26 859 lignes la porte.
-- Les 91 mandats de recherche connus (65 au registre + 26 de l'export) ont
-- 91 numeros TOUS DISTINCTS : aucune collision possible entre eux.
--
-- ⚠ QUI LIT CES LIGNES DOIT LE SAVOIR : une annonce vide ne veut pas dire
--   « on ne sait pas », elle veut dire « il n'y en a pas, regarder app_contact_id ».
--
-- ─── CE QUE CE PATCH NE FAIT PAS ───────────────────────────────────────────────
-- Il n'ajoute AUCUNE ligne, n'en modifie AUCUNE, ne touche NI la cle primaire,
-- NI la contrainte unique, NI le NOT NULL. Deux colonnes facultatives, un index.
-- Les 26 859 lignes existantes gardent leur annonce et ne sont pas relues.
--
-- ─── RETOUR ARRIERE ────────────────────────────────────────────────────────────
-- DROP INDEX IF EXISTS public.idx_app_mandat_contact;
-- ALTER TABLE public.app_mandat DROP COLUMN IF EXISTS app_contact_id;
-- ALTER TABLE public.app_mandat DROP COLUMN IF EXISTS hektor_contact_id;
-- Rien ne les lit tant que la lecture console n'est pas ecrite.
--
-- ─── ORDRE DES OPERATIONS ──────────────────────────────────────────────────────
-- 1. CE PATCH (ici).
-- 2. Le code est deja pose et porte son propre filet : tant que ce patch n'est
--    pas passe, mandat_ledger.py RETIRE les deux colonnes du push et l'ECRIT sur
--    stderr (il ne fait pas tomber le lot -- PostgREST refuse tout le lot des
--    qu'une colonne lui est inconnue, PGRST204).
-- 3. La DESCENTE n'a rien a faire : pull_from_supabase lit le schema OpenAPI et
--    recree app_mandat__sb avec les colonnes qu'il y trouve. Elles arriveront
--    seules a la prochaine descente.
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_mandat
    ADD COLUMN IF NOT EXISTS app_contact_id    bigint;

ALTER TABLE public.app_mandat
    ADD COLUMN IF NOT EXISTS hektor_contact_id text;

CREATE INDEX IF NOT EXISTS idx_app_mandat_contact
    ON public.app_mandat (app_contact_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- AJOUT DU 15/10 (second temps) : CE QUE NOUS SAVONS QUAND HEKTOR SE TAIT
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⚠ CE FICHIER EST IDEMPOTENT. S'il a deja ete colle, le recoller ne fait rien
--   de plus : tous les ADD COLUMN sont en IF NOT EXISTS.
--
-- LE FAIT MESURE : 2 902 mandats (10 % du registre) n'ont AUCUN type chez Hektor.
-- Tous sont anciens (2009-2024), tous ECHUS, et Hektor ne les remplira jamais.
-- Sans type, _nature() ne peut rien affirmer -- elle dit INCONNUE, et c'est juste.
--
--     521 lignes INCONNUE, 503 numeros
--     dont 491 que l'export Modelo tranche en VENTE
--     dont 123 pour lesquels il rend AUSSI le type (SIMPLE / EXCLUSIF / ACCORD)
--     ⭐ et notre propre base confirme : 509 de ces lignes portent sur une
--        annonce dont offre_type = vente. Deux sources independantes.
--
-- POURQUOI DEUX COLONNES, ET PAS UN UPDATE DE `nature` :
--   le run REECRIT `nature` et `type` a chaque nuit (ON CONFLICT DO UPDATE SET
--   nature = excluded.nature). Un UPDATE ne tiendrait pas une nuit.
--   Ces deux colonnes-ci sont HORS du INSERT du run : il ne les ecrit jamais.
--   C'est le meme patron que `date_cloture` et `first_seen_at`, qui sont deja
--   posees a la naissance et plus jamais touchees dans cette meme table.
--
-- L'ORDRE DE LECTURE RESTE : HEKTOR D'ABORD.
--   COALESCE(nature, nature_app) -- si Hektor parle un jour, c'est lui qui gagne.
--   Nos valeurs ne servent que la ou il se tait.

ALTER TABLE public.app_mandat
    ADD COLUMN IF NOT EXISTS nature_app      text;

ALTER TABLE public.app_mandat
    ADD COLUMN IF NOT EXISTS type_app        text;

ALTER TABLE public.app_mandat
    ADD COLUMN IF NOT EXISTS source_app      text;

COMMENT ON COLUMN public.app_mandat.nature_app IS
    'La nature etablie par NOUS quand Hektor n''en donne aucune (mandat sans '
    'type). Lire COALESCE(nature, nature_app) : Hektor garde la priorite. '
    'Jamais ecrite par le run. Posee le 15/10/2026.';

COMMENT ON COLUMN public.app_mandat.type_app IS
    'Le type (SIMPLE / EXCLUSIF / ACCORD) retrouve dans une source legale quand '
    'Hektor l''a perdu. Jamais ecrit par le run. Pose le 15/10/2026.';

COMMENT ON COLUMN public.app_mandat.source_app IS
    'D''OU vient la valeur : « modelo » (les deux exports Excel) ou '
    '« registre_legal » (le PDF certifie). Sans elle, on ne saurait pas qui a '
    'ecrit quoi -- la lecon du 13/10 sur la boucle fermee. Posee le 15/10/2026.';

COMMENT ON COLUMN public.app_mandat.app_contact_id IS
    'Le PORTEUR du mandat quand ce n''est pas une annonce (mandat de recherche). '
    'Dans ce cas hektor_annonce_id vaut la chaine VIDE, jamais NULL : un NULL '
    'ferait sauter la protection de l''index unique (deux NULL ne sont jamais '
    'egaux en SQL). Pose le 15/10/2026.';

COMMENT ON COLUMN public.app_mandat.hektor_contact_id IS
    'Le numero du meme contact chez Hektor. Meme forme que app_search_registry, '
    'qui porte deja les deux numeros. Pose le 15/10/2026.';

-- ─── CONTROLE APRES APPLICATION ────────────────────────────────────────────────
-- Les deux colonnes sont la, et AUCUNE ligne n'a bouge :
--
--   SELECT count(*)                                   AS lignes,
--          count(*) FILTER (WHERE app_contact_id IS NOT NULL) AS avec_contact,
--          count(*) FILTER (WHERE coalesce(trim(hektor_annonce_id),'') = '') AS sans_annonce
--     FROM public.app_mandat;
--
-- ATTENDU : lignes = 26 859 (ou plus si le run a tourne entre-temps),
--           avec_contact = 0, sans_annonce = 0.
