-- ═══════════════════════════════════════════════════════════════════════════════
-- LE COMMENTAIRE DU CONTACT ENTRE DANS app_contact_current       02/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Instantane, aucun verrou long, AUCUNE donnee modifiee.
--
-- ─── POURQUOI ───────────────────────────────────────────────────────────────────
-- La rubrique « Contact » d'une annonce doit lire NOTRE REGISTRE
-- (app_contact_relations_current) au lieu de `proprietaires_json`, la copie du
-- detail Hektor. Decision de Frederic du 02/10, et l'audit montre qu'elle y gagne :
--
--     complétude   0 ligne perdue sur 3 000 biens compares, +19 GAGNEES
--     la personne  app_contact_current donne identite, tel, email, adresse,
--                  dates, negociateur, et le lien de MENAGE
--     le worker    hektor_target_id donne le numero HEKTOR dont degroupproprio
--                  a besoin -- verifie : 10215521 -> 414472
--     l'instant    une ecriture devient visible A LA SECONDE, au lieu d'attendre
--                  le run de la nuit
--
-- ⛔ UN SEUL CHAMP MANQUE A L'APPEL, ET C'EST CELUI-CI.
--    La rubrique affiche le commentaire du mandant. Mesure du 02/10 :
--      · 18,8 % des mandants en ont un (439 sur 2 336 examines)
--      · app_contact_current : AUCUNE colonne de commentaire (43 colonnes)
--      · app_contact_override.comments existe, mais c'est la table des CORRECTIONS
--        faites dans l'app -- pas le miroir de Hektor
--    Basculer sans cette colonne ferait perdre l'information a pres d'un mandant
--    sur cinq. Frederic a tranche : on l'ajoute.
--
-- ⭐ ET LE SERVEUR L'A DEJA -- il dormait dans un blob :
--      data/hektor.sqlite -> hektor_contact.raw_json -> cle « commentaires »
--      61,5 % des contacts en portent un (24 610 sur 40 000 examines)
--    Il n'a jamais ete extrait en colonne. Rien a aller chercher chez Hektor.
--
-- ─── CE QU'IL FAIT, ET CE QU'IL NE FAIT PAS ─────────────────────────────────────
--   · une colonne `commentaires text`, NULLABLE, SANS defaut
--     -> depuis PostgreSQL 11 (ici 17.6), c'est une ecriture de METADONNEE :
--        aucune reecriture des 310 Mo, aucun verrou long sur les 62 103 lignes
--   · ⛔ IL NE REMPLIT RIEN. Toutes les lignes restent a NULL jusqu'a ce que
--     l'etape ② (l'extraction cote serveur) soit posee et qu'un run passe.
--   · ⛔ IL NE TOUCHE AUCUNE VUE. Les 11 vues qui lisent cette table listent leurs
--     colonnes UNE A UNE : elles ignoreront la nouvelle, et c'est voulu a ce stade.
--     app_contacts_current devra l'exposer a l'etape ③, quand on saura par quel
--     chemin la rubrique lit. Un patch, un but.
--
-- ⚠⚠ L'ORDRE EST OBLIGATOIRE, ET C'EST CE PATCH QUI DOIT PASSER EN PREMIER.
--    push_contacts_to_supabase.py lit les lignes locales par `SELECT * FROM table`.
--    Si la colonne etait creee EN LOCAL avant d'exister ici, le push partirait avec
--    un champ inconnu de Supabase -> « column does not exist » -> ET LE RUN
--    S'ARRETERAIT. C'est exactement ce qui est arrive les 01 et 02/09 sur le ledger
--    d'affaires : dix-huit heures de retard sans que rien ne le dise.
--    Donc : CE PATCH D'ABORD, l'extraction ensuite.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
--   ALTER TABLE public.app_contact_current DROP COLUMN IF EXISTS commentaires;
--   ⚠ a ne faire QUE si l'extraction cote serveur n'a pas ete posee -- sinon le
--     push suivant tomberait, pour la raison inverse.
--
-- ─── EPROUVE AVANT ENVOI, le 02/10 ──────────────────────────────────────────────
--   En BEGIN/ROLLBACK sur la base reelle :
--      colonne creee ............  1
--      lignes toujours la .......  62 103   (aucune touchee)
--      valeurs posees ...........  0        (toutes a NULL)
--      exposee par la vue .......  0        (attendu : la vue liste ses colonnes)
--      la vue repond toujours ...  62 103   (rien n'est casse)
--   Puis ROLLBACK verifie : 0 colonne restante, 43 colonnes comme avant.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ⛔ GARDE-FOU 1 : la table est bien celle qu'on croit.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                  WHERE table_schema='public' AND table_name='app_contact_current') THEN
    RAISE EXCEPTION 'ARRET : public.app_contact_current est introuvable.';
  END IF;
END $$;

-- ⛔ GARDE-FOU 2 : on ne recouvre pas une colonne qui existerait deja sous ce nom
--   avec un autre type ou un autre sens.
DO $$
DECLARE t text;
BEGIN
  SELECT data_type INTO t FROM information_schema.columns
   WHERE table_schema='public' AND table_name='app_contact_current'
     AND column_name='commentaires';
  IF t IS NOT NULL AND t <> 'text' THEN
    RAISE EXCEPTION 'ARRET : commentaires existe deja en % -- a regarder avant.', t;
  END IF;
END $$;

-- ① LA COLONNE
ALTER TABLE public.app_contact_current
  ADD COLUMN IF NOT EXISTS commentaires text;

COMMENT ON COLUMN public.app_contact_current.commentaires IS
  'Le commentaire du contact chez Hektor. Pose le 02/10/2026 pour que la rubrique '
  '« Contact » d''une annonce puisse lire NOTRE registre au lieu de proprietaires_json '
  '(la copie du detail Hektor) sans perdre ce champ -- 18,8 % des mandants en ont un. '
  'Rempli par le run depuis hektor_contact.raw_json -> « commentaires », ou il dormait '
  'deja pour 61,5 % des contacts. NULL tant que l''etape ② n''est pas posee.';

-- ⛔ GARDE-FOU 3 : elle est la, elle est vide, et RIEN D'AUTRE N'A BOUGE.
--   Une migration qui ne verifie que sa propre ligne ne prouve pas qu'elle est sans
--   effet de bord : on controle aussi que la table et sa vue repondent toujours.
DO $$
DECLARE n_lignes bigint; n_vals bigint; n_vue bigint;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name='app_contact_current'
                    AND column_name='commentaires' AND data_type='text') THEN
    RAISE EXCEPTION 'La colonne n''a pas ete creee, ou pas en text.';
  END IF;
  SELECT count(*) INTO n_lignes FROM public.app_contact_current;
  SELECT count(*) INTO n_vals   FROM public.app_contact_current WHERE commentaires IS NOT NULL;
  SELECT count(*) INTO n_vue    FROM public.app_contacts_current;
  IF n_vals <> 0 THEN
    RAISE EXCEPTION 'ARRET : % valeur(s) posee(s) -- ce patch ne doit RIEN remplir.', n_vals;
  END IF;
  IF n_lignes <> n_vue THEN
    RAISE EXCEPTION 'ARRET : la table rend % lignes et la vue % -- incoherent.', n_lignes, n_vue;
  END IF;
  RAISE NOTICE 'OK : colonne posee, % lignes intactes, 0 valeur, la vue repond.', n_lignes;
END $$;

COMMIT;

-- ─── A LIRE APRES LE COMMIT ─────────────────────────────────────────────────────
-- SELECT column_name, data_type FROM information_schema.columns
--  WHERE table_schema='public' AND table_name='app_contact_current'
--    AND column_name='commentaires';
--   -> doit rendre une ligne : commentaires | text
--
-- PUIS, et seulement apres, l'etape ② cote serveur :
--   build_contacts_layer.py  ->  hektor_contact.raw_json ->> 'commentaires'
--   (le push suit tout seul : il fait SELECT *)
