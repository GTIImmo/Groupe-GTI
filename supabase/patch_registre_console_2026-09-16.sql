-- ═══════════════════════════════════════════════════════════════════════════
-- LE MIROIR CONSOLE ENTRE DANS LE REGISTRE DES AFFAIRES          16/09/2026
--
-- Demande de Frederic : « le rattrapage et l'entretien quotidien console pour
-- notaire et le reste doivent etre recuperes comme une sorte de miroir de
-- Hektor puis envoyes au registre des affaires ou il y a les chaines, sur le
-- serveur et l'app ».
--
-- CE QUE CES COLONNES ACCUEILLENT, et d'ou elles viennent :
--     notaire_acquereur_*   l'API pour les ventes, la CONSOLE pour les compromis
--     notaire_mandant_*     idem
--     taux_honoraire_entree le taux VENDEUR -- « manque n°1 de la tache 0.1 »,
--                           present sur la TOTALITE des 18 442 lectures console
--     unites_*_percent      le partage de la commission, brut
--     notaires_origine      'api' · 'console' · 'saisie'
--
-- ⚠ LE SERVEUR EST LE MAITRE DE CETTE TABLE. C'est `registre_depuis_console.py`
--   qui calcule, EN LOCAL, et le push existant porte le resultat ici. Rien dans
--   Supabase n'ecrit ces colonnes -- sauf une saisie humaine a venir, qui posera
--   `notaires_origine = 'saisie'` et que l'etape locale ne touchera plus jamais.
--
-- ⚠ AUCUN DEFAUT, AUCUN NOT NULL. Une colonne vide dit « on ne sait pas », et
--   c'est une information juste : « mieux vaut un champ absent qu'un champ
--   menteur ». 12 535 lignes du registre resteront vides -- ce sont les offres,
--   pour lesquelles Hektor n'a pas d'assistant a ouvrir.
--
-- RETOUR ARRIERE : ALTER TABLE ... DROP COLUMN sur les huit. Les donnees de
-- `app_affaire_console` ne bougent pas -- elles restent la source.
-- ═══════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_affaire_ledger
  ADD COLUMN IF NOT EXISTS notaire_acquereur_id   text,
  ADD COLUMN IF NOT EXISTS notaire_acquereur_nom  text,
  ADD COLUMN IF NOT EXISTS notaire_mandant_id     text,
  ADD COLUMN IF NOT EXISTS notaire_mandant_nom    text,
  ADD COLUMN IF NOT EXISTS taux_honoraire_entree  text,
  ADD COLUMN IF NOT EXISTS unites_entree_percent  text,
  ADD COLUMN IF NOT EXISTS unites_sortie_percent  text,
  ADD COLUMN IF NOT EXISTS notaires_origine       text;

-- L'ecran cherchera « qui est le notaire de ce dossier », jamais « quels
-- dossiers a ce notaire » : un index sur les identifiants ne servirait a rien.
-- On n'en pose donc aucun -- un index inutile est une ecriture de plus a chaque
-- push, sur 30 976 lignes.

COMMENT ON COLUMN public.app_affaire_ledger.notaire_acquereur_id IS
  'Notaire de l''ACQUEREUR. Vient de notaires_json.entree (ventes) ou de la lecture console (compromis). Pose par registre_depuis_console.py, en local.';
COMMENT ON COLUMN public.app_affaire_ledger.notaire_mandant_id IS
  'Notaire du MANDANT. Vient de notaires_json.sortie (ventes) ou de la lecture console (compromis).';
COMMENT ON COLUMN public.app_affaire_ledger.taux_honoraire_entree IS
  'Le taux d''honoraires du VENDEUR, celui qui determine la commission de l''agence. A ne pas confondre avec taux_honoraires (saisie de l''app, cote acquereur).';
COMMENT ON COLUMN public.app_affaire_ledger.notaires_origine IS
  'api | console | saisie. ''saisie'' fige la ligne : l''etape locale ne la touche plus.';
