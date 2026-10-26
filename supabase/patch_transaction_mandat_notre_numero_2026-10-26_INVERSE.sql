-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ types, chantier 2 — c : notre numéro de mandat sur la transaction      26/10/2026
-- ⛔ D'ABORD ÉTEINDRE APP_AFFAIRE_MANDAT_NOTRE_NUMERO dans `.env` : allumé, le push enverrait la colonne que
--   ce fichier retire, et le lot entier des transactions tomberait.
-- Ce que la colonne portait se RECALCULE (la clé bien + numéro est dans le code) : rien n'est perdu.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

alter table public.app_affaire_ledger drop column if exists app_mandat_id;

SELECT 1 AS "#", 'la colonne est retiree' AS controle,
       CASE WHEN NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public'
                              AND table_name = 'app_affaire_ledger' AND column_name = 'app_mandat_id')
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict;

COMMIT;
