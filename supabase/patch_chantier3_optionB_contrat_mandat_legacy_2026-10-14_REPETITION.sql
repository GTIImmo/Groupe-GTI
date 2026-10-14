-- =====================================================================
-- REPETITION de l'option B (2 inscriptions en legacy) -- RIEN NE RESTE
-- Date : 2026-10-14
--
-- A COLLER DANS L'EDITEUR SQL. Elle fait tout pour de vrai, puis ANNULE TOUT par une levee
-- volontaire a la fin. L'editeur affichera une ERREUR : c'est le SUCCES, le tableau des
-- epreuves est dans son message.
--
-- CE QU'ELLE PROUVE :
--   ① le patch passe les 2 lignes en legacy, et SEULEMENT elles
--   ② la sonde des battements ne les voit plus ; la re-pose reste surveillee
--   ③ la note est ajoutee derriere son marqueur
--   ④ ⭐ le patch REFUSE de s'appliquer deux fois
--   ⑤ l'inverse les remet en active
--   ⑥ ⭐ TEMOIN INVERSE : statut ET note reviennent AU CARACTERE PRES
--   ⑦ aucune autre ligne du registre n'a bouge, ni pendant, ni apres
--
-- ⚠ Les temoins sont figes AVANT les epreuves (lecon du 13/10).
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '60s';

CREATE TEMP TABLE _res (n int, titre text, attendu text, obtenu text, ok boolean);

-- ---------------------------------------------------------------------
-- 0. LES TEMOINS, FIGES
-- ---------------------------------------------------------------------
CREATE TEMP TABLE _t_deux AS
SELECT worker_key, status, source_notes FROM public.app_worker_registry
 WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat');

CREATE TEMP TABLE _t_autres AS
SELECT md5(string_agg(worker_key || '|' || coalesce(status, '') || '|' || coalesce(source_notes, ''),
                      E'\n' ORDER BY worker_key)) AS empreinte,
       count(*) AS n
  FROM public.app_worker_registry
 WHERE worker_key NOT IN ('phase2.magasin_mandat', 'phase2.contrat_mandat');

INSERT INTO _res
SELECT 0, 'etat de depart : les 2 lignes sont active, sans marqueur', '2',
       count(*)::text, count(*) = 2
  FROM _t_deux
 WHERE status = 'active' AND position('[[RETIREE DU RUN' in coalesce(source_notes, '')) = 0;

-- ---------------------------------------------------------------------
-- 1. LE PATCH, TEL QUEL (sans son BEGIN/COMMIT)
-- ---------------------------------------------------------------------
DO $garde$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.app_worker_registry
   WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
     AND status = 'active'
     AND position('[[RETIREE DU RUN 14/10/2026]]' in coalesce(source_notes, '')) = 0;
  IF n <> 2 THEN
    RAISE EXCEPTION 'STOP : % inscription(s) dans l''etat attendu au lieu de 2 -- deja applique, ou le registre a change', n;
  END IF;
END $garde$;

UPDATE public.app_worker_registry
   SET status       = 'legacy',
       source_notes = coalesce(source_notes, '')
                      || ' [[RETIREE DU RUN 14/10/2026]] Decision de Frederic (chantier 3, option B) : '
                      || 'l''etape ne servait plus : le registre lit la fiche detail depuis le 30/09, et aucune de ses '
                      || 'valeurs n''arrivait a l''ecran (mesure du 14/10). '
                      || 'Le script est garde ; la date de l''app vit dans le carnet et mandat_date_cloture_app, '
                      || 'reposee par phase2.repose_cloture_mandat.',
       updated_at   = now()
 WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
   AND status = 'active';

-- ---------------------------------------------------------------------
-- 2. LES EPREUVES APRES LE PATCH
-- ---------------------------------------------------------------------
INSERT INTO _res
SELECT 1, 'les 2 lignes sont en legacy', '2', count(*)::text, count(*) = 2
  FROM public.app_worker_registry
 WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat') AND status = 'legacy';

INSERT INTO _res
SELECT 2, 'la sonde des battements ne les voit plus (coalesce(status,active)=active)', '0',
       count(*)::text, count(*) = 0
  FROM public.app_worker_registry
 WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
   AND coalesce(status, 'active') = 'active';

INSERT INTO _res
SELECT 3, 'la re-pose reste surveillee (active)', 'active',
       coalesce(max(status), '(absente)'), max(status) = 'active'
  FROM public.app_worker_registry WHERE worker_key = 'phase2.repose_cloture_mandat';

INSERT INTO _res
SELECT 4, 'la note est ajoutee derriere son marqueur, l''ancienne est intacte devant', '2',
       count(*)::text, count(*) = 2
  FROM public.app_worker_registry r JOIN _t_deux t USING (worker_key)
 WHERE r.source_notes LIKE coalesce(t.source_notes, '') || ' [[RETIREE DU RUN 14/10/2026]]%';

INSERT INTO _res
SELECT 5, 'aucune AUTRE ligne n''a bouge pendant le patch',
       a.empreinte || ' (' || a.n || ')',
       x.empreinte || ' (' || x.n || ')',
       a.empreinte = x.empreinte AND a.n = x.n
  FROM _t_autres a,
       (SELECT md5(string_agg(worker_key || '|' || coalesce(status, '') || '|' || coalesce(source_notes, ''),
                              E'\n' ORDER BY worker_key)) AS empreinte, count(*) AS n
          FROM public.app_worker_registry
         WHERE worker_key NOT IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')) x;

-- ④ le patch REFUSE de s'appliquer une seconde fois (sa garde doit mordre)
DO $double$
DECLARE v_msg text;
BEGIN
  BEGIN
    PERFORM 1 FROM public.app_worker_registry
     WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
       AND status = 'active'
       AND position('[[RETIREE DU RUN 14/10/2026]]' in coalesce(source_notes, '')) = 0
    HAVING count(*) = 2;
    IF FOUND THEN
      INSERT INTO _res VALUES (6, 'un second passage du patch est REFUSE', 'refus', 'ACCEPTE (defaut)', false);
    ELSE
      INSERT INTO _res VALUES (6, 'un second passage du patch est REFUSE', 'refus',
        'refuse : la garde ne trouve plus 2 lignes dans l''etat attendu', true);
    END IF;
  END;
END $double$;

-- ---------------------------------------------------------------------
-- 3. L'INVERSE, TEL QUEL (sans son BEGIN/COMMIT)
-- ---------------------------------------------------------------------
DO $garde_inv$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.app_worker_registry
   WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
     AND status = 'legacy'
     AND position(' [[RETIREE DU RUN 14/10/2026]]' in coalesce(source_notes, '')) > 0;
  IF n <> 2 THEN
    RAISE EXCEPTION 'STOP : % inscription(s) portent le patch au lieu de 2 -- rien a defaire, ou elles ont change', n;
  END IF;
END $garde_inv$;

UPDATE public.app_worker_registry
   SET status       = 'active',
       source_notes = left(source_notes, position(' [[RETIREE DU RUN 14/10/2026]]' in source_notes) - 1),
       updated_at   = now()
 WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
   AND status = 'legacy'
   AND position(' [[RETIREE DU RUN 14/10/2026]]' in coalesce(source_notes, '')) > 0;

-- ---------------------------------------------------------------------
-- 4. LE TEMOIN INVERSE, ET LE TABLEAU
-- ---------------------------------------------------------------------
INSERT INTO _res
SELECT 7, 'TEMOIN INVERSE : statut ET note reviennent au caractere pres', '2 sur 2',
       count(*) || ' sur 2',
       count(*) = 2
  FROM public.app_worker_registry r JOIN _t_deux t USING (worker_key)
 WHERE r.status = t.status
   AND coalesce(r.source_notes, '') = coalesce(t.source_notes, '');

INSERT INTO _res
SELECT 8, 'aucune AUTRE ligne n''a bouge apres l''inverse',
       a.empreinte || ' (' || a.n || ')',
       x.empreinte || ' (' || x.n || ')',
       a.empreinte = x.empreinte AND a.n = x.n
  FROM _t_autres a,
       (SELECT md5(string_agg(worker_key || '|' || coalesce(status, '') || '|' || coalesce(source_notes, ''),
                              E'\n' ORDER BY worker_key)) AS empreinte, count(*) AS n
          FROM public.app_worker_registry
         WHERE worker_key NOT IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')) x;

DO $fin$
DECLARE l record; v_msg text; v_total int; v_rates int;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE NOT ok) INTO v_total, v_rates FROM _res;
  v_msg := format(E'\n%s\n  REPETITION OPTION B (contrat de mandat en legacy) -- %s epreuve(s), %s echec(s)\n%s\n',
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
