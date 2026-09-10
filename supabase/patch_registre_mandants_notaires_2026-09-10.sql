-- ═══════════════════════════════════════════════════════════════════════════════
-- LE REGISTRE PORTE LES MANDANTS, LES NOTAIRES, LES PROPOSITIONS
-- ET LA PART DE L'AGENCE                                          10/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnée de la migration `registre_affaire_mandants_notaires`.
--
-- SUITE DIRECTE DU PATCH DU 08/09, et même cible :
--     « le registre des transactions autonome doit comporter tous les champs
--       possibles A B C, donc tous les champs Hektor. L'app lit et saisit dedans. »
-- Le 08/09 : trois champs quittaient payload_json. Ici, quatre de plus.
--
-- ─── L'INVENTAIRE QUI A DÉCIDÉ DE CES QUATRE-LÀ (10/09) ───
-- Les 29 349 lignes du registre relues clé par clé, avec le taux de remplissage :
--     propositions      offre       11 088 / 11 142    99 %
--     mandants          compromis   10 587 / 10 597    99 %
--     notaires          vente        7 610 /  7 610   100 %
--     mandants          vente        7 605 /  7 610    99 %
--     commissionAgence  vente        6 472 /  7 610    85 %
-- Et ce qui NE VAUT RIEN, mesuré et donc écarté sans regret :
--     partAdmin  0/18 207   ·   note (compromis)  0/10 597   ·   retro_*  0/7 610
--
-- ⚠ DEUX CHAMPS ÉCARTÉS APRÈS MESURE, ET C'EST LE POINT IMPORTANT :
--     honoraires    = honorairesEntree + honorairesSortie sur 7 608 / 7 608
--                     EXACT, toujours. Deux colonnes le portent déjà depuis le
--                     08/09 : le stocker une troisième fois, c'est se préparer
--                     une divergence.
--     honorairesHT  = honoraires sur 7 403 / 7 608 (97 %). LE NOM MENT : ce
--                     n'est pas un montant hors taxes. Une colonne
--                     `honoraires_ht` aurait menti sur 7 403 lignes.
--   Arbitrage de Frédéric, 10/09 : aucune colonne pour ces deux-là.
--
-- ⚠ ET commissionAgence N'EST PAS UN MONTANT HORS TAXES NON PLUS. Rapports
--   honoraires ÷ commission mesurés sur le parc : 1,2 · 2,4 · 4,8 — soit la
--   TOTALITÉ, la MOITIÉ, le QUART. C'est LA PART QUI RESTE À L'AGENCE après
--   partage, et 1 138 ventes ne la portent pas du tout. C'est la seule trace
--   actuelle de ce que gouvernera le lot 4 (unitesEntreePercent /
--   unitesSortiePercent, lus dans l'assistant et jamais rendus par l'API).
--
-- ─── POURQUOI DU BRUT, ET PAS UN « PRINCIPAL » ───
-- mandants_json et notaires_json gardent LA LISTE ENTIÈRE, comme acquereurs_json
-- depuis le 04/09. On ne refait pas l'erreur de 1.8 : garder le seul acquéreur
-- principal avait caché 4 536 acquéreurs réels pendant des mois.
-- notaires_json garde les DEUX rôles tels que Hektor les rend :
--     { "entree": {…notaire du VENDEUR…}, "sortie": {…notaire de l'ACQUÉREUR…} }
-- Remplissage mesuré : sortie 7 017 · entrée 2 931.
--
-- ⚠ NE PAS CONFONDRE AVEC LA COLONNE `notaire_id`, QUI RESTE À L'APP.
--   Celle-là est de CLASSE A (l'app seule l'écrit, elle figure dans
--   COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS). notaires_json vient de HEKTOR et se relit
--   à chaque run. Les deux ne se touchent jamais : l'une est une saisie, l'autre
--   une lecture. Mesure du 10/09 : notaire_id est rempli 0 fois sur 29 349.
--
-- ⚠ CLASSE B/C — RELUES À CHAQUE RUN, comme prix_net_vendeur depuis le 08/09 et
--   jours_validite depuis 1.2b. Elles entrent donc dans le ON CONFLICT DO UPDATE
--   de refresh_ledger. Les figer serait le gel que 1.2 avait évité.
--
-- ⚠ LE COMPROMIS N'A PAS DE NOTAIRE DANS L'API — 0 sur 10 586, et la clé
--   `notaires` n'existe même pas dans sa charge. Hektor le connaît pourtant : le
--   formulaire du compromis 24933, capturé le 03/09, porte
--       <input name="notairesAcquereur[]" value="49708">
--   avec les deux rôles (notairesAcquereur[] et notairesMandant[]). Seule une
--   lecture CONSOLE peut le récupérer — c'est le rattrapage estimé à 4-6 h, sur
--   le patron du run chauffage. La colonne l'accueillera sans changer de forme.
--
-- RETOUR ARRIÈRE : ALTER TABLE ... DROP COLUMN (les quatre), PUIS les retirer de
-- la liste de migration ET de LEDGER_SQL dans phase2/sync/affaire_ledger.py —
-- sinon le push (SELECT * moins une liste noire) les enverrait en trop et
-- échouerait, pour les 29 349 lignes d'un coup.
-- ═══════════════════════════════════════════════════════════════════════════════

alter table public.app_affaire_ledger
  add column if not exists mandants_json     jsonb,
  add column if not exists notaires_json     jsonb,
  add column if not exists propositions_json jsonb,
  add column if not exists commission_agence text;

comment on column public.app_affaire_ledger.mandants_json is
  'Classe B, relu a chaque run. LA LISTE ENTIERE des mandants, telle que Hektor la rend. Compromis 10 587 / ventes 7 605. Pas de « principal » : lecon de 1.8 (4 536 acquereurs caches).';
comment on column public.app_affaire_ledger.notaires_json is
  'Classe B, relu a chaque run. { entree: notaire du VENDEUR, sortie: notaire de l''ACQUEREUR }. VENTE UNIQUEMENT : l''API ne rend aucun notaire sur le compromis (0/10 586) alors que Hektor en tient un — lecture console requise. Ne pas confondre avec notaire_id, qui est la saisie de l''app (classe A, jamais poussee).';
comment on column public.app_affaire_ledger.propositions_json is
  'Classe B, relu a chaque run. L''historique DATE des propositions d''une offre (11 088 / 11 142). C''est deja la source de montant, date et jours_validite ; ici on garde la suite complete.';
comment on column public.app_affaire_ledger.commission_agence is
  'Classe C. LA PART DE L''AGENCE apres partage — PAS un montant hors taxes. Rapports honoraires/commission mesures : 1,2 (tout) 2,4 (moitie) 4,8 (quart). Vide sur 1 138 ventes. Vente uniquement.';

-- ─── REMPLISSAGE IMMÉDIAT, depuis le brut déjà stocké ───
-- ⚠ SEULES les quatre colonnes neuves sont touchées : ni montant, ni state, ni
--   date. On ne lance PAS le run pour cela — leçon du 07/09 : un
--   `--refresh --push` en pleine journée pousse l'état du miroir de 05:00 et
--   efface les gestes de la matinée.
-- `->` rend le JSON `null` comme une valeur ; on ne veut pas l'écrire, d'où le
-- test sur jsonb_typeof.
update public.app_affaire_ledger
   set mandants_json = case when jsonb_typeof(payload_json->'mandants') in ('array','object')
                            then payload_json->'mandants' end
 where payload_json ? 'mandants';

update public.app_affaire_ledger
   set notaires_json = case when jsonb_typeof(payload_json->'notaires') in ('array','object')
                            then payload_json->'notaires' end
 where payload_json ? 'notaires';

update public.app_affaire_ledger
   set propositions_json = case when jsonb_typeof(payload_json->'propositions') in ('array','object')
                                then payload_json->'propositions' end
 where payload_json ? 'propositions';

update public.app_affaire_ledger
   set commission_agence = nullif(btrim(coalesce(payload_json->>'commissionAgence','')), '')
 where payload_json ? 'commissionAgence';
