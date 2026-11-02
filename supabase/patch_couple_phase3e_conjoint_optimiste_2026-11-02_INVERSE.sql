-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE E — RETOUR ARRIÈRE                                   02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⛔ D'ABORD : éteindre l'interrupteur contacts_couples_modif (sinon l'écran appellerait une fonction absente ;
--   il l'attrape et le dit en console, la saisie part quand même à Hektor par la principale).
-- La fonction est NEUVE : la retirer ne touche rien d'autre. Les fiches déjà écrites restent : la nuit les relit.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
drop function if exists public.app_edit_conjoint_optimistic(text, jsonb);
DO $controle$
BEGIN
  IF to_regprocedure('public.app_edit_conjoint_optimistic(text,jsonb)') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRET : la fonction est toujours la. Tout est annule.';
  END IF;
END
$controle$;
COMMIT;
