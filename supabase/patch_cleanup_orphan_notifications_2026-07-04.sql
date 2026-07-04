-- ============================================================================
-- patch_cleanup_orphan_notifications_2026-07-04.sql
--
-- Nettoyage des 91 notifications ORPHELINES (negociateur_email IS NULL) :
-- toutes de type 'nouveau_rapprochement' (20/06 -> 02/07), residus de l'ancienne
-- logique d'alerte (avant les garde-fous du cron). Verifie en amont :
--   * sans destinataire => invisibles pour tout le monde (cloche filtre par nego) ;
--   * les 91 sont DES DOUBLONS : pour chacune il existe deja une notification
--     'nouveau_rapprochement' correcte et attribuee au bon negociateur
--     (collisions_avec_existantes = 91).
-- Les backfiller violerait l'index unique partiel app_notif_unread_uq ; on les
-- supprime donc (aucune perte : la vraie notif existe deja).
-- ============================================================================

delete from public.app_notification
where negociateur_email is null
  and type = 'nouveau_rapprochement';
