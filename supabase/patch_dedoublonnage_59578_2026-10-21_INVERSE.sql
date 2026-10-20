-- ════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE du dedoublonnage de 59578                        21/10/2026
-- ════════════════════════════════════════════════════════════════════════════
-- Il remet les 17 fiches retirees, telles qu'elles etaient, depuis la sauvegarde
-- datee app_console_document_avant_dedoublonnage_59578_20261021.
--
-- ⚠ LECON 31 DU PROJET : « un retour arriere ne juge que SA part ». Il verifie donc
--   D'ABORD que les 17 sont bien ABSENTES. Si elles sont deja la, il s'arrete sans
--   rien faire -- sinon il creerait des doublons de doublons.
--
-- ⚠ IL NE DEFAIT PAS CE QU'IL N'A PAS FAIT. Si le balayage est passe entre-temps et
--   que le correctif a RE-CLE les 17 anciennes (numero et adresse neufs), remettre
--   les neuves recreerait exactement les doublons qu'on venait d'enlever -- et cette
--   fois avec un conflit possible sur l'unicite. Il DETECTE ce cas et s'arrete en le
--   disant. Dans ce cas, il n'y a rien a defaire : la situation est MEILLEURE.
--
-- A COLLER EN UNE SEULE FOIS. Il rend une TABLE (l'editeur n'affiche pas les NOTICE).
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

DO $v$
DECLARE
  n_sauvegardees int;
  n_deja_la      int;
  n_reclees      int;
BEGIN
  IF to_regclass('public.app_console_document_avant_dedoublonnage_59578_20261021') IS NULL THEN
    RAISE EXCEPTION 'ARRET : la sauvegarde n''existe pas. Le patch n''a jamais tourne -- il n''y a rien a defaire.';
  END IF;

  SELECT count(*) INTO n_sauvegardees
    FROM app_console_document_avant_dedoublonnage_59578_20261021;
  IF n_sauvegardees = 0 THEN
    RAISE EXCEPTION 'ARRET : la sauvegarde est VIDE. Rien a remettre.';
  END IF;

  -- SA PART : les lignes qu'il doit remettre sont-elles bien absentes ?
  SELECT count(*) INTO n_deja_la
    FROM app_console_document_avant_dedoublonnage_59578_20261021 s
    JOIN app_console_document d ON d.id = s.id;
  IF n_deja_la > 0 THEN
    RAISE EXCEPTION 'ARRET : % des % lignes sauvegardees sont DEJA presentes. Le retour arriere a peut-etre deja ete joue. Rien n''a ete touche.', n_deja_la, n_sauvegardees;
  END IF;

  -- ⚠ LE CAS « LE CORRECTIF EST PASSE » : si une fiche VIVANTE de 59578 porte
  --   desormais le numero d'une fiche sauvegardee, c'est que reconcilierParChemin
  --   a RE-CLE l'ancienne. Remettre la neuve creerait un conflit d'unicite.
  SELECT count(*) INTO n_reclees
    FROM app_console_document_avant_dedoublonnage_59578_20261021 s
    JOIN app_console_document d
      ON  d.hektor_annonce_id = s.hektor_annonce_id
      AND d.source = s.source
      AND d.hektor_document_id = s.hektor_document_id;
  IF n_reclees > 0 THEN
    RAISE EXCEPTION 'ARRET : % fiche(s) ancienne(s) ont DEJA ete re-clees par le correctif (elles portent maintenant le numero des neuves). Remettre les neuves recreerait les doublons ET un conflit d''unicite. IL N''Y A RIEN A DEFAIRE : l''etat actuel est celui qu''on voulait.', n_reclees;
  END IF;
END
$v$;

-- ── LE GESTE INVERSE ───────────────────────────────────────────────────────
INSERT INTO app_console_document
SELECT * FROM app_console_document_avant_dedoublonnage_59578_20261021;

-- ── LE COMPTE RENDU ────────────────────────────────────────────────────────
SELECT 'REMISE' AS geste,
       s.document_name AS document,
       s.id AS fiche_remise,
       (SELECT count(*) FROM app_console_document WHERE hektor_annonce_id = '59578') AS fiches_sur_59578
  FROM app_console_document_avant_dedoublonnage_59578_20261021 s
UNION ALL
SELECT '--- TOTAL ---',
       (SELECT count(*)::text || ' ligne(s) remise(s)' FROM app_console_document_avant_dedoublonnage_59578_20261021),
       NULL,
       (SELECT count(*) FROM app_console_document WHERE hektor_annonce_id = '59578')
ORDER BY 1 DESC, 2;

COMMIT;

-- ⚠ LA SAUVEGARDE N'EST PAS SUPPRIMEE : elle reste la trace du geste. Pour la
--   retirer un jour, deliberement :
--     DROP TABLE app_console_document_avant_dedoublonnage_59578_20261021;
