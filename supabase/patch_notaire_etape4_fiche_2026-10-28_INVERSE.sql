-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ notaire étape 4 : retirer la fonction de lecture de la fiche notaire         28/10/2026
-- ⚠ D'ABORD éteindre l'interrupteur FICHE_NOTAIRE_V2 dans le front (App.tsx), sinon la fiche d'un notaire afficherait
--   « fiche notaire indisponible » à la place des blocs notaire (le reste de la fiche ne bouge pas).
-- La fonction ne fait que LIRE : la retirer n'efface aucune donnée.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
DROP FUNCTION IF EXISTS public.app_notaire_fiche(text);
COMMIT;
