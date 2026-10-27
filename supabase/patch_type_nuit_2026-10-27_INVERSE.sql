-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ÉTAPE 2, la nuit : retirer la fonction du calcul pour tous et la ligne de suivi   27/10/2026
-- ⚠ D'ABORD éteindre l'interrupteur APP_TYPE_PAR_NOS_REGISTRES dans .env (sinon l'étape de nuit appellerait une
--   fonction absente : elle échouerait, non bloquante, et son battement le dirait).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
DROP FUNCTION IF EXISTS public.app_recalculer_tous_les_types();
DELETE FROM public.app_worker_registry WHERE worker_key = 'supabase.type_contacts';
COMMIT;
