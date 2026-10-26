-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, CHANTIER 2 — c : LA TRANSACTION PORTE NOTRE NUMÉRO DE MANDAT                   26/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §10.5 et §12.
--
-- Le registre des transactions désignait son mandat par le numéro métier (+ l'id de Hektor, RECYCLÉ).
-- La nuit (phase2/sync/affaire_ledger.py, notre_mandat_par_cle) retrouve désormais le mandat par LA CLÉ du
-- registre des mandats — « bien + numéro de mandat » (0 doublon le 26/10) — et pose NOTRE `app_mandat_id`.
--
-- CE PATCH : UNE COLONNE ADDITIVE. Personne ne l'écrit tant que APP_AFFAIRE_MANDAT_NOTRE_NUMERO n'est pas
-- allumé dans `.env`. ⛔ L'ordre : CE PATCH D'ABORD, l'interrupteur ENSUITE (le push envoie toutes les
-- colonnes locales : une colonne inconnue d'ici ferait tomber le lot entier).
-- ⛔ RIEN N'EST ÉCRIT CHEZ HEKTOR. Retour arrière : _INVERSE.sql (éteindre d'abord).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

alter table public.app_affaire_ledger add column if not exists app_mandat_id bigint;
comment on column public.app_affaire_ledger.app_mandat_id is
  '⑧ 26/10 : NOTRE numero du mandat de la transaction (app_mandat.app_mandat_id), retrouve par la cle bien + numero de mandat -- jamais par l''id de Hektor (recycle). Pose par la nuit, affaire_ledger.py.';

SELECT 1 AS "#", 'la colonne existe' AS controle,
       CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public'
                          AND table_name = 'app_affaire_ledger' AND column_name = 'app_mandat_id')
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'personne ne l''a encore remplie (interrupteur eteint)',
       CASE WHEN (SELECT count(*) FROM public.app_affaire_ledger WHERE app_mandat_id IS NOT NULL) = 0 THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
