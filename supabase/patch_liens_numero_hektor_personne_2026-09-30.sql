-- ===============================================================================
-- LE REGISTRE DES LIENS PORTE LES QUATRE NUMEROS               30/09/2026
-- ===============================================================================
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL. Additif pur : une colonne.
--
-- --- TROUVE PAR FREDERIC ---------------------------------------------------
-- « Est-ce que mon registre des liens genere bien deux numeros, celui de Hektor
--   et celui de mon app, pour anticiper la coupure ? Comme les autres registres. »
--
-- Il avait raison. UN LIEN NOMME DEUX OBJETS -- une personne et un bien -- il
-- faut donc QUATRE numeros. On en avait trois :
--     LE BIEN       notre numero  +  celui de Hektor   OK
--     LA PERSONNE   notre numero  +  RIEN              <- le trou
--
-- Les autres registres, eux, les portent tous :
--     app_affaire_ledger   app_contact_id  +  hektor_acquereur_id
--     app_mandat           app_dossier_id  +  hektor_annonce_id + hektor_mandat_id
--
-- --- A QUOI IL SERT --------------------------------------------------------
-- A PARLER A HEKTOR DE CETTE PERSONNE : « retire M. X des mandants de ce bien ».
-- Notre numero ne lui dit rien. Le worker traduit aujourd'hui a la volee ; apres
-- la coupure, plus personne ne pourra donner ce numero.
--
-- --- ET J'AVAIS ANNONCE UNE PERTE QUI N'EXISTE PAS -------------------------
-- J'ai d'abord dit « 50 982 contacts sur 96 070 ne sont plus traduisibles ».
-- FAUX : j'interrogeais `app_contact_identite_app` (62 038 lignes), qui est le
-- JOURNAL DE LA BASCULE, pas la correspondance.
-- La correspondance complete vit dans `app_contact_current` COTE SERVEUR :
--     356 270 contacts
--     hektor_contact_id  = NOTRE numero   (tous >= 10 000 000)
--     hektor_target_id   = celui de HEKTOR (tous <  10 000 000)
-- MESURE : 96 070 contacts du registre, 96 070 traduisibles -- 100 %.
-- Remplissage verifie cote serveur : 132 622 lignes sur 132 622, 0 sans numero.
-- ==> LECON : une absence mesuree sur la mauvaise source n'est pas une absence,
--     c'est une erreur de lecture.
--
-- --- QUI LE REMPLIT, PAR LES DEUX BOUTS ------------------------------------
--   LE RUN   relation_ledger.py le lit dans app_contact_current et le pose.
--            Il COMBLE, il n'ecrase jamais (COALESCE sur la valeur existante).
--   L'APP    la RPC du geste mandant recoit DEJA le numero Hektor du front
--            (mesure du 30/09 : contact_id = 603953). Elle l'ecrira au lieu de
--            le jeter apres traduction.
--
-- --- RETOUR ARRIERE ---------------------------------------------------------
-- ALTER TABLE public.app_relation DROP COLUMN hektor_contact_id;
-- ===============================================================================

ALTER TABLE public.app_relation
  ADD COLUMN IF NOT EXISTS hektor_contact_id text;

CREATE INDEX IF NOT EXISTS idx_app_relation_hektor_contact
  ON public.app_relation (hektor_contact_id);

COMMENT ON COLUMN public.app_relation.hektor_contact_id IS
  'Le numero de la PERSONNE chez Hektor. Sert a lui parler de cette personne -- '
  'notre numero ne lui dit rien. PERIME AVEC HEKTOR : le run le voit chaque nuit '
  'dans le miroir ; sans cette colonne il le jetait. Rempli par le run (depuis '
  'app_contact_current.hektor_target_id, 100 % de couverture) et par la RPC du '
  'geste mandant, qui le recoit deja du front.';
