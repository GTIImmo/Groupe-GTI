-- ═══════════════════════════════════════════════════════════════════════════════
-- A.3-tech phase 1 -- LES 5 COLONNES QUI MANQUENT A app_mandat DANS SUPABASE
-- ═══════════════════════════════════════════════════════════════════════════════
-- 30/09/2026. Additif pur : ALTER TABLE ADD COLUMN IF NOT EXISTS, aucune donnee
-- touchee, aucune vue recreee, aucune politique modifiee.
--
-- ─── POURQUOI CES CINQ-LA ───────────────────────────────────────────────────────
-- La table a ete posee le 29/09 avec 20 colonnes. La table LOCALE en a gagne
-- cinq depuis, et ce n'est pas du confort : QUATRE D'ENTRE ELLES SONT LUES PAR
-- L'ECRAN, aujourd'hui, a travers le registre.
--
--     versions_json / version_count   l'ecran affiche « +N versions »
--                                     (App.tsx:23286, register_version_count)
--     avenants_json / avenant_count   l'ecran affiche les avenants
--                                     (App.tsx:8856, register_avenants_json)
--
-- Sans elles, le jour ou le registre prend ses colonnes de mandat dans cette
-- table, l'ecran PERD CES DEUX FONCTIONS -- en silence, sans erreur.
--
-- La cinquieme, `nature`, dit CE QU'EST le mandat (VENTE / GESTION / RECHERCHE /
-- LOCATION). ⚠ A NE PAS CONFONDRE AVEC `famille`, qui dit DE QUEL REGISTRE vient
-- le numero (HEKTOR / PROTEXA). Deux axes differents, comme les « couleurs » et
-- les « lettres » de la carte A1.
--
-- ─── TEXT, PAS JSONB, ET C'EST DELIBERE ─────────────────────────────────────────
-- `payload_json` est deja `text` dans cette table. On garde le meme choix : le
-- push envoie alors des chaines, sans decodage. Le piege inverse est ecrit dans
-- affaire_ledger.py -- « toute colonne jsonb cote Supabase doit etre decodee ;
-- sans le decodage PostgREST accepte la chaine et range du texte dans du jsonb,
-- SANS ERREUR, donc invisible ». En restant en `text` on ne peut pas y tomber.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- ALTER TABLE public.app_mandat
--   DROP COLUMN nature, DROP COLUMN versions_json, DROP COLUMN version_count,
--   DROP COLUMN avenants_json, DROP COLUMN avenant_count;
-- Rien ne les lit encore : les supprimer ne casse rien.
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_mandat
  ADD COLUMN IF NOT EXISTS nature         text,
  ADD COLUMN IF NOT EXISTS versions_json  text,
  ADD COLUMN IF NOT EXISTS version_count  integer,
  ADD COLUMN IF NOT EXISTS avenants_json  text,
  ADD COLUMN IF NOT EXISTS avenant_count  integer;

COMMENT ON COLUMN public.app_mandat.nature IS
  'CE QU''EST le mandat : VENTE | GESTION | RECHERCHE | LOCATION | INCONNUE. '
  'A NE PAS CONFONDRE AVEC `famille`, qui dit de quel REGISTRE vient le numero '
  '(HEKTOR / PROTEXA). Les INCONNUE restent inconnues -- les ranger d''office en '
  'VENTE serait compter comme perdu ce qui est ecarte volontairement.';

COMMENT ON COLUMN public.app_mandat.versions_json IS
  'TOUTES les versions du couple (annonce, numero), LA RETENUE EN TETE -- ordre de '
  'compute_mandat_version_score, la formule du registre, importee et non recopiee. '
  'C''est de la que le registre tire register_history_json.';

COMMENT ON COLUMN public.app_mandat.version_count IS
  'Nombre de versions. L''ecran l''affiche : « +N versions ».';

COMMENT ON COLUMN public.app_mandat.avenants_json IS
  'Les avenants depouilles (normalize_embedded_avenants). ⚠ Le parc n''en porte '
  'QU''UN SEUL, le n° 18499 du 02/04/2026 -- mesure du 30/09. La colonne existe '
  'parce que l''ecran la lit, pas parce qu''elle est pleine. Et il n''y a PAS de '
  'mandat successeur pour un avenant : le « 18500 » vit DANS la fiche 18499.';
