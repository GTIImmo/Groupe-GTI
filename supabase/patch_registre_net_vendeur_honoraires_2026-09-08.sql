-- ═══════════════════════════════════════════════════════════════════════════════
-- LE REGISTRE PORTE LE NET VENDEUR ET LES HONORAIRES          08/09/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Copie versionnée de la migration `registre_affaire_prix_net_et_honoraires`.
--
-- PREMIER MORCEAU RÉEL DE LA CIBLE ÉNONCÉE PAR FRÉDÉRIC LE 08/09 :
--     « je souhaite avoir à la fin le registre des transactions autonome qui
--       intègre si nécessaire des mises à jour de Hektor grâce au miroir ; ce
--       registre doit comporter tous les champs possibles A B C, donc tous les
--       champs Hektor. L'app lit et saisit dans ce registre. »
-- Trois champs quittent `payload_json` pour devenir des colonnes lisibles.
--
-- POURQUOI CES TROIS-LÀ D'ABORD. Question de Frédéric, le même jour :
--     « pourquoi dans la modale on ne vérifie pas avant, pour aider
--       l'utilisateur, que Net + Commission = Prix de vente ? »
-- La modale ne le POUVAIT pas : elle porte les honoraires de l'ACQUÉREUR
-- (sortie) et pas ceux du VENDEUR (entrée). Il lui manquait le terme du milieu.
-- C'est le manque n°1 de la tâche 0.1, celui dont elle dit :
--     « le taux VENDEUR détermine les honoraires d'entrée, donc LA COMMISSION DE
--       L'AGENCE. Il est aujourd'hui invisible ET non modifiable. »
--
-- L'INVARIANT QU'ILS PERMETTENT DE VÉRIFIER :
--     prix public = prix net vendeur + honoraires d'ENTRÉE + honoraires de SORTIE
--
-- MESURÉ AVANT D'Y CROIRE, sur les 10 583 compromis mesurables du registre :
--     10 055 le vérifient          95,01 %
--        528 en écart, dont 508 ANTÉRIEURS À 2025
-- Sur les données récentes il tient. C'est ce qui rend l'alerte de la modale
-- utile : elle ne crie pas dans le vide.
--
-- ⚠ CLASSE C — Hektor les CALCULE (tâche 0.1 : « net_seller_price vide ->
--   prixNetVendeur 170 000 ; (rien envoyé) -> honorairesEntree 10 000, posé
--   seul, du mandat »). Ils sont donc RELUS À CHAQUE RUN, comme jours_validite
--   depuis 1.2b. Les figer serait le gel que 1.2 avait justement évité.
-- ⚠ LA VENTE NE PORTE PAS prixNetVendeur (elle a prix + honoraires) : la colonne
--   y reste NULL. Vérifié au remplissage — 7 610 ventes, 0 net, 7 610 honoraires.
--   « Mieux vaut un champ absent qu'un champ menteur. »
-- ⚠ L'OFFRE n'en porte aucun des trois : 11 138 lignes, 0 rempli. Normal.
-- ⚠ TEXTE, comme montant et sequestre : on recopie ce que Hektor écrit
--   (« 162500.00 »), on ne le réinterprète pas.
--
-- RETOUR ARRIÈRE : ALTER TABLE ... DROP COLUMN (les trois), PUIS les retirer de
-- la liste de migration dans phase2/sync/affaire_ledger.py — sinon le push
-- (SELECT * moins une liste noire) les enverrait en trop et échouerait.
-- ═══════════════════════════════════════════════════════════════════════════════

alter table public.app_affaire_ledger
  add column if not exists prix_net_vendeur  text,
  add column if not exists honoraires_entree text,
  add column if not exists honoraires_sortie text;

comment on column public.app_affaire_ledger.prix_net_vendeur is
  'Classe C, relu a chaque run. Ce que Hektor rend dans prixNetVendeur. Absent de la vente (elle ne porte que prix + honoraires).';
comment on column public.app_affaire_ledger.honoraires_entree is
  'Classe C. Honoraires du VENDEUR = la commission de l''agence. Pose seul par Hektor depuis le mandat.';
comment on column public.app_affaire_ledger.honoraires_sortie is
  'Classe C. Honoraires de l''ACQUEREUR. C''est ce que la modale appelle aujourd''hui « Honoraires acquereur ».';

-- ─── REMPLISSAGE IMMÉDIAT, depuis le brut déjà stocké ───
-- ⚠ SEULES les trois colonnes neuves sont touchées : ni montant, ni state, ni
--   date. On ne lance PAS le run pour cela — le miroir date de 05:00 et le
--   compromis d'essai a bougé trois fois depuis ; un `--refresh --push` en
--   pleine journée écraserait les gestes du jour (leçon du 07/09).
update public.app_affaire_ledger
   set prix_net_vendeur  = nullif(btrim(coalesce(payload_json->>'prixNetVendeur','')), ''),
       honoraires_entree = nullif(btrim(coalesce(payload_json->>'honorairesEntree','')), ''),
       honoraires_sortie = nullif(btrim(coalesce(payload_json->>'honorairesSortie','')), '')
 where payload_json is not null
   and (payload_json ? 'prixNetVendeur' or payload_json ? 'honorairesEntree'
        or payload_json ? 'honorairesSortie');
