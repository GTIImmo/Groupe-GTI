-- 09/11/2026 (note partenaires §28.19) : REPRISE DES APPORTS DE NETTY — les 14 liens sûrs (décision de Frédéric : « Les 14 »).
-- Netty (l'ancien logiciel) notait « tel contact a apporté telle affaire » (relations *_business_provider). L'audit §28.18 a
-- rapproché les 53 apports de nos contacts (nom + prénom + jour de création, correspondance UNIQUE seulement) : 14 couples
-- apporteur ↔ client sont sûrs — l'apporteur a déjà le métier apporteur ou parrain au catalogue, le client existe chez nous.
-- Écrit CHEZ NOUS seulement (rien chez Hektor). origine = 'netty', pose_le = la date de la relation dans Netty, pose_par vide
-- (personne de l'app ne l'a posé). Chaque garde est vérifiée ; s'il manque UN lien, RIEN n'est écrit.
-- Retour arrière : patch_reprise_apports_netty_2026-11-09_INVERSE.sql.
BEGIN;
SET LOCAL lock_timeout = '3s';

DO $reprise$
DECLARE
  n_avant int; n_pose int;
BEGIN
  SELECT count(*) INTO n_avant FROM public.app_partenaire_lien WHERE origine = 'netty';
  IF n_avant <> 0 THEN
    RAISE EXCEPTION 'Reprise déjà passée : % lien(s) d''origine netty existent. Rien n''est écrit.', n_avant;
  END IF;

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
  SELECT count(*) INTO n_pose FROM poses;

  IF n_pose <> 14 THEN
    RAISE EXCEPTION 'Reprise annulée : % lien(s) passent les gardes sur 14 attendus. Rien n''est écrit.', n_pose;
  END IF;
  RAISE NOTICE 'Reprise Netty : 14 liens apporteur ↔ client posés.';
END
$reprise$;

COMMIT;
