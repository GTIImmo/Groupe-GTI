# Note filtres transactions offres / compromis

Date : 02/04/2026

## Objet

Recadrer l'alimentation des filtres transactions dans l'app en se basant sur la source brute phase 1, et non sur une lecture simplifiee de `offre_state`.

## Verification brute realisee

Source controlee :

- `data/hektor.sqlite`
- table `hektor_offre`
- table `hektor_compromis`

Constats observes :

- `hektor_compromis.compromis_state` porte bien les etats utiles :
  - `active`
  - `cancelled`
- `hektor_offre.offre_state` est insuffisant pour filtrer les offres :
  - `accepted`
  - `proposed`
  - vide
- `hektor_offre.raw_status` n'apporte pas de statut exploitable
- `hektor_offre.propositions_json` contient en revanche l'historique transactionnel fin des offres :
  - `proposition`
  - `accepte`
  - `refus`

Des cas bruts existent avec des successions du type :

- `proposition -> refus`
- `proposition -> accepte`
- `proposition -> accepte -> refus`

Conclusion :

- pour les compromis, la bonne source metier reste `compromis_state`
- pour les offres, la bonne source metier est `propositions_json`
- il faut prendre le **dernier evenement** de `propositions_json`

## Regle retenue

### Offres

On derive un champ applicatif :

- `offre_last_proposition_type`

Il correspond au dernier `type` observe dans `propositions_json`, trie par date puis par position dans le tableau.

Lecture metier :

- `proposition` => offre en cours
- `accepte` => offre en cours
- `refus` => offre refusee

### Compromis

- `compromis_state = active` => compromis en cours
- `compromis_state = cancelled` => compromis annule

## Impact app

Les filtres transactionnels doivent donc s'appuyer sur :

- `offre_last_proposition_type` pour les offres
- `compromis_state` pour les compromis

Libelles retenus :

- `Offre d'achat en cours`
- `Offre d'achat refusee`
- `Compromis en cours`
- `Compromis annule`

## Implementation

Le champ derive `offre_last_proposition_type` est calcule dans :

- `phase2/sync/export_app_payload.py`

Il est pousse ensuite vers Supabase via :

- `phase2/sync/push_upgrade_to_supabase.py`

Et consomme dans le front via :

- `apps/hektor-v1/src/lib/api.ts`

## Point d'attention

Un `full-rebuild` seul ne suffit pas si le schema Supabase n'expose pas le nouveau champ.

Il faut :

1. ajouter la colonne `offre_last_proposition_type` cote Supabase
2. republier les donnees
3. recharger le front
