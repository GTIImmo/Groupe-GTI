-- ════════════════════════════════════════════════════════════════════════════
-- DEDOUBLONNAGE DE L'ANNONCE 59578 -- les 17 lignes en double     21/10/2026
-- ════════════════════════════════════════════════════════════════════════════
--
-- LE PROBLEME. 59578 porte 35 fiches de documents pour 18 documents reels : 17
-- sont en DOUBLE. C'est la seule annonce du parc dans ce cas, parce que c'est la
-- seule dont la suppression est tombee en panne -- partout ailleurs le bug du
-- domaine REMPLACAIT la fiche au lieu d'en creer une deuxieme.
-- Voir notice/AUDIT_COMMENT_EST_ARRIVE_LE_DOMAINE_DOCUMENTS_2026-10-20.md.
--
-- ⚠ ET DEPUIS LE 20/10 A 20:30, MON GARDE-FOU LES PROTEGE : le niveau 1 refuse de
--   supprimer une fiche dont le chemin est dans la liste qu'on vient de lire --
--   c'est le cas des 17 anciennes. Elles ne partiront donc plus jamais toutes
--   seules : il faut ce geste exprès.
--
-- MESURE DU 21/10, les 17 paires :
--   meme chemin, meme source, MEME EMPREINTE sha256 et MEME TAILLE : 17 sur 17
--   aucune signature, aucun PDF signe, aucun modelo ImmoSign : 0 sur 34
--   les ANCIENNES nees le 2026-08-17 22:00:13 ; les NEUVES le 2026-10-20 12:22:20
--   ⭐ 12:22, soit HUIT HEURES AVANT la pose du correctif : ce sont les dernieres
--     victimes, pas une fuite. Zero doublon n'est apparu apres 20:30:47.
--   les deux cotes ont leur fichier au coffre (17/17) et leur archive locale (17/17)
--
-- CE QU'ON FAIT : on supprime les 17 NEUVES et on garde les 17 ANCIENNES.
--   POURQUOI LES ANCIENNES : elles portent le numero d'origine de l'app et leur
--   date de naissance du 17 aout -- « un numero ne se perd jamais ». Les neuves
--   n'apportent rien : meme fichier, meme taille, meme empreinte.
--   ⭐ ET LEUR ADRESSE MORTE NE GENE PERSONNE : l'ecran ouvre un document par
--     storage_path (createSignedUrl), JAMAIS par console_url -- verifie, zero
--     occurrence de console_url dans un chemin d'ouverture du front.
--   ⭐⭐ ET LE CORRECTIF LES REPARERA TOUT SEUL : 59578 est VIVANTE et « Actif »,
--     donc le balayage la resynchronisera, et reconcilierParChemin les RE-CLERA
--     par leur chemin (numero + adresse neufs, meme id, meme fichier).
--     Ce geste est donc aussi un second essai reel du correctif.
--
-- CE QUE CA POURRAIT CASSER AILLEURS -- examine :
--   · un travail en file qui citerait une fiche supprimee ? MESURE : 0.
--   · un lien du front vers une fiche neuve ? elles ont 1 jour, et l'ecran ne
--     retient pas d'identifiant de document entre deux chargements.
--   · les 17 fichiers du coffre des fiches supprimees deviennent ORPHELINS
--     (+17 fichiers, ~39 Mo). Ils rejoignent le menage des 7,2 Go deja identifie.
--     ⚠ ON NE LES SUPPRIME PAS ICI : un seul geste a la fois.
--   · l'unicite (hektor_annonce_id, source, hektor_document_id) n'est pas touchee :
--     on ne fait que RETIRER des lignes, jamais en ecrire.
--   · aucune signature nulle part sur cette annonce -> aucun risque juridique.
--
-- IL NE SUPPRIME QUE CE QU'IL A IDENTIFIE. Le predicat n'est pas une date : c'est
-- « cette fiche a une jumelle sur l'ancien domaine, meme chemin, meme source ET
-- MEME EMPREINTE ». Une fiche seule ne peut donc pas etre touchee, meme par erreur.
-- Relance-le deux fois si tu veux : la deuxieme fois il ne trouve plus de paire.
--
-- A COLLER EN UNE SEULE FOIS DANS L'EDITEUR SQL DE SUPABASE.
-- ⚠ L'editeur n'affiche PAS les RAISE NOTICE : ce patch rend donc une TABLE.
-- ⛔ EN CAS DE PROBLEME : patch_dedoublonnage_59578_2026-10-21_INVERSE.sql
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 1. LES PAIRES, identifiees par leur CONTENU ────────────────────────────
CREATE TEMP TABLE _paires ON COMMIT DROP AS
WITH f AS (
  SELECT id, document_name, hektor_document_id, sha256, file_size, created_at,
         source,
         regexp_replace(metadata_json->>'console_url', '^https?://[^/]+', '') AS chemin,
         (metadata_json->>'console_url' LIKE '%la-boite-immo.com%') AS ancien
    FROM app_console_document
   WHERE hektor_annonce_id = '59578'
     AND source LIKE 'hektor_console%'
     AND metadata_json->>'console_url' IS NOT NULL
     AND sha256 IS NOT NULL
     -- ⛔ ceinture : on ne touche JAMAIS une fiche qui porte une signature
     AND metadata_json->'signature'->>'status' IS NULL
     AND NOT (metadata_json ? 'signed_document')
     AND metadata_json->'modelo'->>'kind' IS DISTINCT FROM 'immosign'
)
SELECT a.id AS id_ancienne, n.id AS id_neuve, n.document_name, n.sha256, n.file_size
  FROM f a
  JOIN f n
    ON  n.chemin = a.chemin
    AND n.source = a.source
    AND n.sha256 = a.sha256          -- ⭐ MEME FICHIER, c'est le coeur du predicat
    AND a.ancien AND NOT n.ancien
    AND n.id <> a.id;

-- ── 2. ARRET SI LA SITUATION N'EST PAS CELLE QU'ON A MESUREE ───────────────
DO $v$
DECLARE
  n_paires int;
  n_total  int;
BEGIN
  SELECT count(*) INTO n_paires FROM _paires;
  SELECT count(*) INTO n_total FROM app_console_document WHERE hektor_annonce_id = '59578';

  IF n_paires = 0 THEN
    RAISE EXCEPTION 'ARRET : aucune paire trouvee. Soit le dedoublonnage est deja fait, soit la situation a change. Rien n''a ete supprime.';
  END IF;
  IF n_paires <> 17 THEN
    RAISE EXCEPTION 'ARRET : % paire(s) trouvee(s) au lieu des 17 mesurees le 21/10. Quelqu''un est passe avant, ou l''annonce a bouge. Rien n''a ete supprime -- remesurer avant de forcer.', n_paires;
  END IF;
  IF n_total <> 35 THEN
    RAISE EXCEPTION 'ARRET : 59578 porte % fiches au lieu des 35 mesurees. Rien n''a ete supprime.', n_total;
  END IF;
  -- une fiche ne doit apparaitre que dans UNE paire, d'un seul cote
  IF (SELECT count(DISTINCT id_neuve) FROM _paires) <> n_paires
     OR (SELECT count(DISTINCT id_ancienne) FROM _paires) <> n_paires THEN
    RAISE EXCEPTION 'ARRET : une fiche apparait dans plusieurs paires -- le predicat n''est pas univoque ici. Rien n''a ete supprime.';
  END IF;
END
$v$;

-- ── 3. SAUVEGARDE DATEE, avant de retirer quoi que ce soit ─────────────────
CREATE TABLE IF NOT EXISTS app_console_document_avant_dedoublonnage_59578_20261021
  (LIKE app_console_document);

INSERT INTO app_console_document_avant_dedoublonnage_59578_20261021
SELECT d.*
  FROM app_console_document d
  JOIN _paires p ON p.id_neuve = d.id
 WHERE NOT EXISTS (
   SELECT 1 FROM app_console_document_avant_dedoublonnage_59578_20261021 s
    WHERE s.id = d.id);

-- ⛔ la sauvegarde doit porter les 17, sinon on n'avance pas
DO $v$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n
    FROM app_console_document_avant_dedoublonnage_59578_20261021 s
    JOIN _paires p ON p.id_neuve = s.id;
  IF n <> 17 THEN
    RAISE EXCEPTION 'ARRET : la sauvegarde ne porte que % ligne(s) sur 17. Rien n''a ete supprime.', n;
  END IF;
END
$v$;

-- ── 4. LE GESTE : on retire les 17 NEUVES ──────────────────────────────────
DELETE FROM app_console_document d
 USING _paires p
 WHERE d.id = p.id_neuve;

-- ── 5. LE COMPTE RENDU, en TABLE (l'editeur n'affiche pas les NOTICE) ──────
SELECT
  'RETIREE' AS geste,
  p.document_name AS document,
  left(p.sha256, 12) AS empreinte,
  p.file_size AS octets,
  p.id_neuve AS fiche_retiree,
  p.id_ancienne AS fiche_conservee
  FROM _paires p
UNION ALL
SELECT '--- TOTAL ---',
       (SELECT count(*)::text || ' paire(s) traitee(s)' FROM _paires),
       (SELECT count(*)::text || ' fiches restantes sur 59578' FROM app_console_document WHERE hektor_annonce_id = '59578'),
       NULL, NULL, NULL
ORDER BY 1 DESC, 2;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- APRES LE COLLAGE : 59578 doit porter 18 fiches (35 - 17), toutes distinctes.
-- Puis COLLER patch_dedoublonnage_59578_2026-10-21_REPETITION.sql.
-- ⏰ ET AU PROCHAIN PASSAGE DU BALAYAGE, le correctif doit RE-CLER les 17
--    anciennes par leur chemin : on le verra dans
--    python phase2/checks/controle_domaine_documents.py (le temoin monte de 17).
-- ════════════════════════════════════════════════════════════════════════════
