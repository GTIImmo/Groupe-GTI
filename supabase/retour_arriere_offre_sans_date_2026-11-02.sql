-- =====================================================================
-- RETOUR ARRIERE -- OFFRES SANS DATE (§ 2.9 + colonne `date`)  02/11/2026
-- =====================================================================
--
-- CE QUI A ETE FAIT LE 02/11, et qu'il faut defaire DANS CET ORDRE.
--
-- Frederic, en voyant VA30102 (annonce 22902, vendue en 2008) : « pourquoi il
-- y a 2 offres en date du 02/11/2026 !!!! » -- puis « FAIS LE 1 ET 2 ».
--
--   GESTE 1  la colonne `date` d'une offre ne vaut plus `synced_at` (l'heure de
--            notre lecture). 68 offres sont rendues SANS DATE : 54 que Hektor
--            livre VIDES, et 14 qu'il livre a « 0000-00-00 ».
--            -> phase2/sync/affaire_ledger.py, LEDGER_SQL (bloc offre)
--            -> phase2/contacts/build_contacts_layer.py, premiere_date_exploitable
--
--   GESTE 2  § 2.9 : l'offre sans date rejoint son affaire par le nom.
--            -> phase2/sync/affaire_ledger.py, chainage_offre_sans_date_actif
--            -> .env : APP_CHAINAGE_OFFRE_SANS_DATE=1
--
-- ⛔⛔ LES DEUX NE SE DEFONT PAS SEPAREMENT, et c'est MESURE, pas suppose :
--   sans le § 2.9, le geste 1 laisse 10 offres (5 paires jumelles, dont les
--   DEUX de VA30102) dans des dossiers SEPARES -- parce qu'une transaction sans
--   date ouvre sa propre chaine. Retirer le seul interrupteur ferait donc PIRE
--   qu'avant le 02/11. Defaire, c'est defaire les deux.
--
-- ─── CE QU'IL FAUT FAIRE, DANS L'ORDRE ───────────────────────────────────
--   1. .env : APP_CHAINAGE_OFFRE_SANS_DATE=0 (ou retirer la ligne)
--   2. code : remettre `COALESCE(offre_event_date, raw_date, synced_at) AS dt`
--      dans LEDGER_SQL, et `first_non_empty(..., row["synced_at"])` dans les
--      trois relations de build_contacts_layer.py
--   3. ce fichier, pour rendre a Supabase son etat du 02/11 AVANT l'ecriture
--   ⚠ Sans l'etape 2, le prochain run reposerait `synced_at` : la date
--     recommencerait a glisser chaque nuit. Et sans l'etape 1, le rattachement
--     serait refait. L'etape 3 seule ne tient donc pas une nuit.
-- =====================================================================

BEGIN;

-- ⚠ ON VERIFIE QUE LA SAUVEGARDE EST LA, ET COMPLETE, AVANT DE TOUCHER QUOI
--   QUE CE SOIT. 178 lignes : les 63 biens qui portent une offre sans date,
--   transactions voisines comprises (ce sont elles qui portent les chaines
--   d'arrivee). Sans ce controle, un retour arriere sur une sauvegarde
--   tronquee ECRASERAIT avec du vide.
DO $$
DECLARE n integer;
BEGIN
    SELECT count(*) INTO n FROM app_affaire_ledger_avant_offre_sans_date_20261102;
    IF n <> 178 THEN
        RAISE EXCEPTION 'sauvegarde inattendue : % lignes au lieu de 178 -- ON NE TOUCHE A RIEN', n;
    END IF;
END $$;

-- ─── ON REND LEUR DATE ET LEUR DOSSIER AUX 178 LIGNES ───
UPDATE app_affaire_ledger s
   SET date = b.date,
       app_chaine_id = b.app_chaine_id
  FROM app_affaire_ledger_avant_offre_sans_date_20261102 b
 WHERE s.app_affaire_id = b.app_affaire_id
   AND (coalesce(s.date, chr(1)) <> coalesce(b.date, chr(1))
        OR coalesce(s.app_chaine_id, -1) <> coalesce(b.app_chaine_id, -1));

-- ─── CONTROLES, AVANT DE VALIDER ───
-- ⚠ ON EXIGE LA PREUVE DU RETOUR, pas l'absence d'erreur. Les 54 dates
--   glissantes portaient l'heure du run du 02/11 (2026-11-02T04:33:4xZ) : si
--   elles ne sont pas revenues, le retour arriere n'a pas eu lieu.
DO $$
DECLARE glissantes integer; zeros integer; sans_date integer;
BEGIN
    SELECT count(*) INTO glissantes FROM app_affaire_ledger
     WHERE kind = 'offre' AND date LIKE '%T%Z';
    SELECT count(*) INTO zeros FROM app_affaire_ledger
     WHERE kind = 'offre' AND date LIKE '0000%';
    SELECT count(*) INTO sans_date FROM app_affaire_ledger
     WHERE kind = 'offre' AND date IS NULL;
    RAISE NOTICE 'retour arriere : % offres a l heure du run (54 attendu), % a 0000 (14 attendu), % sans date (0 attendu)',
                 glissantes, zeros, sans_date;
    IF glissantes <> 54 OR zeros <> 14 OR sans_date <> 0 THEN
        RAISE EXCEPTION 'le retour arriere n est PAS complet -- rien n est valide';
    END IF;
END $$;

COMMIT;

-- ⚠ LA TABLE DE SAUVEGARDE N'EST PAS SUPPRIMEE ICI, DELIBEREMENT : si le
--   retour arriere devait etre rejoue, elle est la seule trace de l'etat du
--   02/11. La retirer est un geste a part, et une DECISION de Frederic :
--       DROP TABLE app_affaire_ledger_avant_offre_sans_date_20261102;
