-- RÉPÉTITION — patch_reprise_apports_netty_2026-11-09.sql : pose les 14 liens DANS le bloc, contrôle, joue l'inverse, contrôle,
-- puis finit par une erreur volontaire qui porte les verdicts : RIEN n'est gardé. Attendu : 8 OK, 0 KO.
DO $essai$
DECLARE
  n int; n_autres int; d_min timestamptz; d_max timestamptz; v_refus text;
  ok int := 0; ko int := 0; journal text := '';
BEGIN
  SET LOCAL lock_timeout = '3s';
  SELECT count(*) INTO n_autres FROM public.app_partenaire_lien WHERE origine <> 'netty';

  -- (1) avant : aucun lien netty
  SELECT count(*) INTO n FROM public.app_partenaire_lien WHERE origine = 'netty';
  IF n = 0 THEN ok := ok + 1; journal := journal || E'\nOK  (1) aucun lien netty avant';
  ELSE ko := ko + 1; journal := journal || E'\nKO  (1) déjà ' || n || ' lien(s) netty'; END IF;

  -- le corps du patch, à l'identique
  WITH netty (apporteur, client, le) AS (VALUES
    ('10026453','10049214','2023-10-05T14:27:26Z'),('10091890','10089893','2016-03-31T09:19:24Z'),
    ('10091890','10089895','2016-03-31T09:19:24Z'),('10091890','10094087','2016-03-31T09:19:24Z'),
    ('10091890','10094089','2016-03-31T09:19:24Z'),('10091890','10094115','2016-03-31T09:19:24Z'),
    ('10093903','10093907','2016-03-03T10:06:17Z'),('10093903','10094418','2016-03-03T10:06:17Z'),
    ('10095396','10095412','2016-09-07T07:55:45Z'),('10175293','10175294','2025-09-23T13:40:19Z'),
    ('10176248','10058189','2024-05-03T07:53:54Z'),('10176248','10184823','2025-09-10T13:02:26Z'),
    ('10214785','10214714','2025-05-09T14:01:35Z'),('10214858','10215403','2025-12-30T13:23:35Z')
  ), surs AS (
    SELECT n.* FROM netty n
     WHERE n.apporteur <> n.client
       AND EXISTS (SELECT 1 FROM public.app_partenaire_metier m
                    WHERE m.contact_id = n.apporteur AND m.metier IN ('apporteur', 'parrain') AND m.retire_le IS NULL)
       AND EXISTS (SELECT 1 FROM public.app_contact_current c WHERE c.hektor_contact_id::text = n.client)
       AND NOT EXISTS (SELECT 1 FROM public.app_partenaire_lien l
                        WHERE l.objet = 'client' AND l.role = 'apporteur' AND l.retire_le IS NULL
                          AND l.partenaire_id = n.apporteur AND l.client_contact_id = n.client)
  ), poses AS (
    INSERT INTO public.app_partenaire_lien (partenaire_id, role, objet, client_contact_id, origine, pose_le, pose_par)
    SELECT apporteur, 'apporteur', 'client', client, 'netty', le::timestamptz, NULL FROM surs
    RETURNING id
  )
  SELECT count(*) INTO n FROM poses;

  -- (2) les 14 passent les gardes
  IF n = 14 THEN ok := ok + 1; journal := journal || E'\nOK  (2) 14 liens posés';
  ELSE ko := ko + 1; journal := journal || E'\nKO  (2) ' || n || ' liens posés sur 14'; END IF;

  -- (3) forme : apporteur / client / sans auteur / actifs
  SELECT count(*) INTO n FROM public.app_partenaire_lien
   WHERE origine = 'netty' AND role = 'apporteur' AND objet = 'client' AND pose_par IS NULL AND retire_le IS NULL
     AND app_dossier_id IS NULL AND hektor_annonce_id IS NULL AND app_affaire_id IS NULL;
  IF n = 14 THEN ok := ok + 1; journal := journal || E'\nOK  (3) 14 liens bien formés';
  ELSE ko := ko + 1; journal := journal || E'\nKO  (3) ' || n || ' bien formés'; END IF;

  -- (4) les dates d'origine sont celles de Netty, pas aujourd'hui
  SELECT min(pose_le), max(pose_le) INTO d_min, d_max FROM public.app_partenaire_lien WHERE origine = 'netty';
  IF d_min = '2016-03-03T10:06:17Z'::timestamptz AND d_max = '2025-12-30T13:23:35Z'::timestamptz THEN
    ok := ok + 1; journal := journal || E'\nOK  (4) dates Netty 03/03/2016 -> 30/12/2025';
  ELSE ko := ko + 1; journal := journal || E'\nKO  (4) dates ' || d_min || ' -> ' || d_max; END IF;

  -- (5) lecture comme l'écran « Affaires apportées » : 8 apporteurs, dont 10091890 avec 5 clients
  SELECT count(DISTINCT partenaire_id) INTO n FROM public.app_partenaire_lien WHERE origine = 'netty';
  IF n = 8 AND (SELECT count(*) FROM public.app_partenaire_lien
                 WHERE partenaire_id = '10091890' AND objet = 'client' AND role = 'apporteur' AND retire_le IS NULL) = 5 THEN
    ok := ok + 1; journal := journal || E'\nOK  (5) 8 apporteurs, 10091890 a 5 clients';
  ELSE ko := ko + 1; journal := journal || E'\nKO  (5) ' || n || ' apporteurs'; END IF;

  -- (6) l'index unique refuse un doublon (le geste « Noter » de l'écran répondra « inchangé »)
  v_refus := NULL;
  BEGIN
    INSERT INTO public.app_partenaire_lien (partenaire_id, role, objet, client_contact_id, origine)
    VALUES ('10091890', 'apporteur', 'client', '10089893', 'app');
  EXCEPTION WHEN unique_violation THEN v_refus := 'refusé';
  END;
  IF v_refus IS NOT NULL THEN ok := ok + 1; journal := journal || E'\nOK  (6) doublon refusé par l''index';
  ELSE ko := ko + 1; journal := journal || E'\nKO  (6) doublon accepté'; END IF;

  -- l'inverse, à l'identique
  DELETE FROM public.app_partenaire_lien WHERE origine = 'netty' AND objet = 'client' AND role = 'apporteur';
  GET DIAGNOSTICS n = ROW_COUNT;

  -- (7) l'inverse retire exactement les 14
  IF n = 14 AND NOT EXISTS (SELECT 1 FROM public.app_partenaire_lien WHERE origine = 'netty') THEN
    ok := ok + 1; journal := journal || E'\nOK  (7) inverse : 14 retirés, 0 reste';
  ELSE ko := ko + 1; journal := journal || E'\nKO  (7) inverse : ' || n || ' retirés'; END IF;

  -- (8) témoin inverse : les autres liens sont intacts
  SELECT count(*) INTO n FROM public.app_partenaire_lien WHERE origine <> 'netty';
  IF n = n_autres THEN ok := ok + 1; journal := journal || E'\nOK  (8) les ' || n || ' autres liens intacts';
  ELSE ko := ko + 1; journal := journal || E'\nKO  (8) autres liens ' || n_autres || ' -> ' || n; END IF;

  RAISE EXCEPTION 'RÉPÉTITION FINIE (rien gardé) : % OK, % KO%', ok, ko, journal;
END
$essai$;
