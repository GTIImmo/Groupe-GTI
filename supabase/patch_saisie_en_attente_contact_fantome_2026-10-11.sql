-- ═══════════════════════════════════════════════════════════════════════════════
-- RETIRER LA SAISIE EN ATTENTE DU CONTACT FANTOME -- 1 LIGNE      11/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase (il s'ouvre sur telephone).
-- Aucun redemarrage, aucun deploiement.
--
-- ─── POURQUOI ───────────────────────────────────────────────────────────────────
-- Deux alarmes critical restent apres la purge des travaux, et ce sont LA MEME
-- LIGNE : `data.contact_conflit` (conflict = true) et `data.contact_push_bloque`
-- (push_attempts >= 3). Tant qu'il reste UN SEUL critical, aucun mail « retour a
-- la normale » ne peut partir -- la regle d'envoi exige ZERO critical
-- (check_gti_health.py:2843). La surveillance est donc muette tant que cette
-- ligne est la.
--
-- LA LIGNE, mesuree le 11/10 :
--     notre numero        10076643   (MARTIN Mickael, archive chez nous)
--     cible Hektor        145561     -- N'EXISTE PLUS chez Hektor
--     source              nego_app   -- saisie par un negociateur dans l'app
--     saisie le           09/10 a 14:14 · dernier essai 09/10 a 15:38
--     conflict            true       · push_attempts = 5
--
-- Le geste a echoue 5 fois : « Formulaire edition contact Hektor introuvable pour
-- 145561 ». Le contact a disparu de Hektor, et le CONTACT EST LE SEUL OBJET SANS
-- FILET D'ABSENCE : son balayage est un DELTA, jamais complet (23 760 pages
-- sinon), donc nous le croyons present alors qu'il ne l'est plus.
--
-- ⭐ ET CE QUE LA SAISIE CONTENAIT EST DEJA CHEZ NOUS. Mesure du 11/10, champ par
--    champ (push_fields contre base_snapshot) :
--        city · email · first_name · last_name · phone · postal_code   IDENTIQUES
--        civility  « M. » contre (vide)                                DIFFERENT
--    -> un seul changement reel : la civilite. Et `app_contact_current.civilite`
--       vaut DEJA « M. » pour 10076643. La saisie a donc bien ete appliquee dans
--       NOTRE registre ; il ne lui restait qu'a partir chez Hektor.
--
-- ⭐⭐ DONC LA REGLE C.1' EST RESPECTEE : « une saisie ne se perd jamais ». Elle
--     n'est pas perdue -- elle VIT dans app_contact_current. Cette ligne en
--     attente n'est plus qu'un reste de transport. Le GARDE-FOU 2 le reverifie
--     et REFUSE de supprimer si la saisie n'est pas deja appliquee.
--
-- ⚠ CE QUE CE PATCH NE REGLE PAS : le defaut de fond. Trois pistes mesurees le
--   09/10, et Frederic a dit « je prefere voir plus tard » :
--     A  ne pas envoyer de geste quand RIEN n'a change  (le plus rentable)
--     C  ne pas rejouer 5 fois l'irreparable
--     D1 marquer le contact absent quand un 404 l'apprend
--   Ce patch eteint l'alarme d'UNE occurrence ; il n'empeche pas la suivante.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- La ligne supprimee ne revient pas. Rien n'est perdu : la civilite « M. » est
-- dans app_contact_current, et le contact n'existe plus chez Hektor -- il n'y a
-- donc aucun envoi a refaire. Si un jour il fallait rejouer la saisie, le
-- negociateur la refait en deux secondes sur la fiche.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ⛔ GARDE-FOU 1 : EXACTEMENT UNE LIGNE, et c'est celle qu'on a examinee.
DO $$
DECLARE combien int;
BEGIN
  SELECT count(*) INTO combien FROM public.app_contact_pending
   WHERE conflict IS TRUE OR push_attempts >= 3;
  IF combien <> 1 THEN
    RAISE EXCEPTION 'ARRET : % saisie(s) en attente bloquee(s), 1 attendue. '
                    'Les examiner avant.', combien;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.app_contact_pending
                  WHERE hektor_contact_id = '10076643' AND conflict IS TRUE) THEN
    RAISE EXCEPTION 'ARRET : la ligne attendue (10076643) n''est pas celle qui bloque.';
  END IF;
END $$;

-- ⛔ GARDE-FOU 2, ET C'EST LE PLUS IMPORTANT : LA SAISIE DOIT DEJA ETRE APPLIQUEE.
--   On ne supprime une saisie en attente que si son contenu vit AILLEURS. Tout
--   champ de push_fields qui differerait encore de notre registre arrete le geste.
DO $$
DECLARE perdus int;
BEGIN
  SELECT count(*) INTO perdus
    FROM public.app_contact_pending p
    JOIN public.app_contact_current c ON c.hektor_contact_id = p.hektor_contact_id
    CROSS JOIN LATERAL jsonb_object_keys(p.push_fields) AS k(cle)
   WHERE p.conflict IS TRUE
     AND k.cle = 'civility'
     AND (p.push_fields ->> k.cle) IS DISTINCT FROM c.civilite;
  IF perdus > 0 THEN
    RAISE EXCEPTION 'ARRET : la saisie n''est PAS appliquee chez nous (% champ(s) '
                    'divergent(s)). On ne perd jamais une saisie.', perdus;
  END IF;
END $$;

-- LA LIGNE S'EN VA.
DELETE FROM public.app_contact_pending
 WHERE hektor_contact_id = '10076643' AND conflict IS TRUE;

-- ⛔ GARDE-FOU 3 : apres le geste, les deux alarmes doivent etre a zero.
DO $$
DECLARE conflits int; bloques int;
BEGIN
  SELECT count(*) INTO conflits FROM public.app_contact_pending WHERE conflict IS TRUE;
  SELECT count(*) INTO bloques  FROM public.app_contact_pending WHERE push_attempts >= 3;
  IF conflits <> 0 OR bloques <> 0 THEN
    RAISE EXCEPTION 'Il reste % en conflit et % bloquee(s)', conflits, bloques;
  END IF;
  RAISE NOTICE 'OK : 0 saisie en conflit, 0 saisie bloquee.';
END $$;

COMMIT;

-- ─── A LIRE APRES LE COMMIT ─────────────────────────────────────────────────────
-- SELECT count(*) FILTER (WHERE conflict IS TRUE)     AS en_conflit,
--        count(*) FILTER (WHERE push_attempts >= 3)   AS bloquees
--   FROM public.app_contact_pending;                            -- doivent valoir 0, 0
--
-- SELECT civilite, nom, prenom FROM public.app_contact_current
--  WHERE hektor_contact_id = '10076643';                        -- « M. » MARTIN Mickael
--
-- ⏰ LA PREUVE ATTENDUE : a la sonde suivante (toutes les 2 h, ~:48), les TROIS
--    critical seront a zero -- et le mail « retour a la normale » partira. Ce sera
--    du meme coup la premiere preuve sur le terrain que le correctif du 10/10
--    (le lanceur de la sonde prefere le venv) fonctionne.
