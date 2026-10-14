-- =====================================================================
-- REPETITION du troisieme verrou du bloc 2 (la distribution) -- RIEN NE RESTE
-- Date : 2026-10-14
--
-- A COLLER DANS L'EDITEUR SQL. Elle fait tout pour de vrai, puis ANNULE TOUT. L'editeur
-- affichera une ERREUR : c'est le SUCCES, le tableau est dans son message.
--
-- ⭐ LA PREUVE LA PLUS DIRECTE : elle APPELLE LA VRAIE FONCTION DE DISTRIBUTION, comme le
--   ferait un service, sur le travail d'essai reellement en attente (b7519387…) :
--     ① AVANT le correctif : le service documents ne le recoit PAS (temoin inverse)
--     ② APRES : le service documents le recoit
--     ③ et les services `admin` et `actions` ne le recoivent pas
--     ④ l'inverse rend la fonction a son empreinte d'origine, au caractere pres
--
-- ⚠ COMMENT CHAQUE APPEL EST ISOLE. Un appel « prend » des travaux (il les passe en
--   running). Chaque epreuve se fait donc UNE SEULE FOIS, dans un bloc qui s'annule
--   lui-meme par une levee interne ; le resultat est garde dans une VARIABLE, qui survit
--   a cette annulation (une table, elle, serait annulee avec). Les vrais services sautent
--   ces lignes pendant ce temps (for update skip locked), et tout est annule a la fin.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '60s';

CREATE TEMP TABLE _res (n int, titre text, attendu text, obtenu text, ok boolean);
CREATE TEMP TABLE _t AS
SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), '')) AS md5_distribution
  FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
 WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';

-- « Ce service, s'il vidait la file, recevrait-il ce travail ? » -- jusqu'a 60 prises de
-- suite. Elle laisse des travaux en running : on l'appelle TOUJOURS dans un bloc annule.
CREATE FUNCTION pg_temp.recoit(p_kind text, p_job uuid) RETURNS boolean
LANGUAGE plpgsql AS $f$
DECLARE v_id uuid; i int := 0;
BEGIN
  LOOP
    i := i + 1;
    v_id := NULL;
    SELECT j.id INTO v_id FROM public.app_console_claim_next_job('repetition:service:v9', p_kind) j LIMIT 1;
    IF v_id IS NULL OR i > 60 THEN RETURN false; END IF;
    IF v_id = p_job THEN RETURN true; END IF;
  END LOOP;
END $f$;

-- Un appel isole : il se fait, puis s'annule ; seul le booleen reste.
CREATE FUNCTION pg_temp.recoit_isole(p_kind text, p_job uuid) RETURNS boolean
LANGUAGE plpgsql AS $f$
DECLARE v boolean;
BEGIN
  BEGIN
    v := pg_temp.recoit(p_kind, p_job);
    RAISE EXCEPTION USING ERRCODE = 'P0099', MESSAGE = 'annulation volontaire des prises';
  EXCEPTION WHEN SQLSTATE 'P0099' THEN
    NULL;   -- les prises sont annulees ; v garde sa valeur
  END;
  RETURN v;
END $f$;

DO $etat$
DECLARE n int; v boolean;
BEGIN
  SELECT count(*) INTO n FROM public.app_console_job
   WHERE id = 'b7519387-980a-4faa-8f5e-6477c3f18ac1' AND status = 'pending' AND job_type = 'delete_hektor_photo';
  INSERT INTO _res VALUES (0, 'le travail d''essai est bien en attente', '1', n::text, n = 1);
  INSERT INTO _res SELECT 1, 'etat de depart : l''empreinte mesuree le 14/10', '8447b6cf...',
    left(md5_distribution, 8) || '...', md5_distribution = '8447b6cfd7530134ded46056e39d2e4e' FROM _t;

  -- ① AVANT le correctif
  v := pg_temp.recoit_isole('documents', 'b7519387-980a-4faa-8f5e-6477c3f18ac1');
  INSERT INTO _res VALUES (2, '① TEMOIN INVERSE : AVANT le correctif, le service documents ne le recoit PAS',
    'false', v::text, v IS FALSE);
END $etat$;

-- ---------------------------------------------------------------------
-- LE CORRECTIF, TEL QUEL (sans son BEGIN/COMMIT)
-- ---------------------------------------------------------------------
DO $distribution$
DECLARE
  v_def   text;
  v_ancre text := '''sync_hektor_photos'',''upload_hektor_photo'',';
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_claim_next_job introuvable'; END IF;
  IF md5(replace(v_def, chr(13), '')) <> '8447b6cfd7530134ded46056e39d2e4e' THEN
    RAISE EXCEPTION 'STOP : la fonction de distribution n''est pas celle mesuree le 14/10 (empreinte %)',
      md5(replace(v_def, chr(13), ''));
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre de la liste documents n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    '''sync_hektor_photos'',''upload_hektor_photo'',''delete_hektor_photo'',');
END $distribution$;

-- ② et ③ APRES le correctif
DO $apres$
DECLARE v boolean;
BEGIN
  v := pg_temp.recoit_isole('documents', 'b7519387-980a-4faa-8f5e-6477c3f18ac1');
  INSERT INTO _res VALUES (3, '② ⭐ APRES le correctif, le service DOCUMENTS le recoit', 'true', v::text, v IS TRUE);

  v := pg_temp.recoit_isole('admin', 'b7519387-980a-4faa-8f5e-6477c3f18ac1');
  INSERT INTO _res VALUES (4, '③ le service ADMIN ne le recoit pas', 'false', v::text, v IS FALSE);

  v := pg_temp.recoit_isole('actions', 'b7519387-980a-4faa-8f5e-6477c3f18ac1');
  INSERT INTO _res VALUES (5, '③ le service ACTIONS ne le recoit pas', 'false', v::text, v IS FALSE);
END $apres$;

-- ---------------------------------------------------------------------
-- L'INVERSE, TEL QUEL (sans son BEGIN/COMMIT)
-- ---------------------------------------------------------------------
DO $distribution_inv$
DECLARE
  v_def  text;
  v_ajout text := '''delete_hektor_photo'',';
  v_restaure text;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF (length(v_def) - length(replace(v_def, v_ajout, ''))) / length(v_ajout) <> 1 THEN
    RAISE EXCEPTION 'STOP : delete_hektor_photo n''est pas present une seule fois dans la distribution';
  END IF;
  v_restaure := replace(v_def, v_ajout, '');
  IF md5(replace(v_restaure, chr(13), '')) <> '8447b6cfd7530134ded46056e39d2e4e' THEN
    RAISE EXCEPTION 'STOP : la fonction restauree n''a pas l''empreinte d''origine (%)', md5(replace(v_restaure, chr(13), ''));
  END IF;
  EXECUTE v_restaure;
END $distribution_inv$;

INSERT INTO _res
SELECT 6, '④ TEMOIN INVERSE : la fonction retrouve son empreinte d''origine, au caractere pres',
       t.md5_distribution, x.m, x.m = t.md5_distribution
  FROM _t t,
       (SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), '')) AS m
          FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
         WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job') x;

INSERT INTO _res
SELECT 7, 'le travail d''essai est toujours en attente (rien n''a ete pris pour de vrai)', 'pending',
       coalesce(status, '(absent)'), status = 'pending'
  FROM public.app_console_job WHERE id = 'b7519387-980a-4faa-8f5e-6477c3f18ac1';

DO $fin$
DECLARE l record; v_msg text; v_total int; v_rates int;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE NOT ok) INTO v_total, v_rates FROM _res;
  v_msg := format(E'\n%s\n  REPETITION BLOC 2 -- LA DISTRIBUTION -- %s epreuve(s), %s echec(s)\n%s\n',
                  repeat('=', 76), v_total, v_rates, repeat('=', 76));
  FOR l IN SELECT * FROM _res ORDER BY n LOOP
    v_msg := v_msg || format(E'%s  [%s] %s\n       attendu : %s\n       obtenu  : %s\n',
      CASE WHEN l.ok THEN 'OK  ' ELSE 'RATE' END, l.n, l.titre, l.attendu, l.obtenu);
  END LOOP;
  v_msg := v_msg || format(E'%s\n%s\n%s\n', repeat('=', 76),
    CASE WHEN v_rates = 0
         THEN 'TOUT EST VERT. Le patch peut etre colle. RIEN N''A ETE ECRIT : la transaction est annulee.'
         ELSE format('%s EPREUVE(S) RATEE(S) -- NE PAS COLLER LE PATCH.', v_rates) END,
    repeat('=', 76));
  RAISE EXCEPTION '%', v_msg;
END $fin$;

ROLLBACK;
