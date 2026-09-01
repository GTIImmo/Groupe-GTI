# Note dev projet — Câbler la couche transaction (offre/compromis/vente) dans le read-through

Date : 25/06/2026
Statut : **À FAIRE** (dev en projet, non implémenté)
Priorité : moyenne (contournable manuellement ; pas bloquant au quotidien)

## Problème à résoudre

Le read-through (`phase2/sync/refresh_single_annonce.py`) rafraîchit **l'annonce**
(statut, type, prix, diffusion) mais **PAS la couche transaction** :
- aucun appel `OffreById`,
- aucune mise à jour de `hektor_offre` / des propositions,
- aucune relecture de `hektor_compromis` / `hektor_vente`.

Conséquence : si on **refuse une offre** (ou **annule un compromis**) dans Hektor,
le bien repasse bien « Actif » (statut annonce relu), **mais l'offre/le compromis
reste figé dans notre base** → l'état de transaction reste périmé jusqu'au prochain
run quotidien. Aujourd'hui on corrige **à la main** (rappel `OffreById` + recalcul
`offre_state`).

Cas réel ayant motivé la note : annonce 24113 / offre 32849 refusée (juin 2026).

## Ce qui est DÉJÀ fait (ne pas refaire)

- **Dérivation offre** : `normalize_source.py::derive_offre_state_and_event_date`
  prend le **dernier événement** des propositions (`refus` → `offre_state='refused'`)
  — commit 883beeb. Conforme à `notice/NOTE_FILTRES_TRANSACTIONS_OFFRES_2026-04-02.md`.
- **Affichage front** : badge + tables lisent l'état réel via `hasOffreAchatEnCours` /
  `hasCompromisEnCours` (api.ts) — commit b8fc48e.
- **Vue quotidienne** : `view_generale.py::etat_transaction` exclut
  `offre_state='refused'` et `compromis_state IN (cancelled…)` — commit cfe3483.

→ Donc la chaîne fonctionne **dès que la donnée transaction est fraîche**. Il ne
manque que le **rafraîchissement temps réel** de cette donnée par le read-through.

## Travail à faire

Ajouter au read-through un rafraîchissement ciblé de la couche transaction du bien,
sur le **même modèle que le fix diffusion** (`rebuild_broadcast_state_from_listing`) :

1. **Offre** : appeler `OffreById` (ou l'endpoint listant les offres de l'annonce),
   réécrire **uniquement** `hektor_offre` en local (+ propositions), recalculer
   `offre_state` via la logique existante `derive_offre_state_and_event_date`
   (réutiliser, ne pas dupliquer).
2. **Compromis** : relire `compromis_state` (active/cancelled) → `hektor_compromis`.
3. **Vente** : relire `hektor_vente` (pas d'annulation, mais une vente créée/supprimée
   doit se refléter).

### Points de vigilance (repris des fix précédents)

- **Garde-fou anti-vide** : ne jamais écraser une valeur existante par du vide si
  l'API renvoie partiel (`CASE WHEN NULLIF(TRIM(excluded.x),'') IS NULL THEN x ELSE excluded.x END`).
- **Gestion du « retiré »** : si une offre/compromis n'existe plus côté Hektor, décider
  explicitement (supprimer la ligne locale vs marquer) — comme la diffusion reconstruite
  depuis la source d'autorité, pas un parse approximatif.
- **Ne PAS supprimer puis réinsérer** la ligne unique (fenêtre vide → fiche qui disparaît,
  cf. fb36772). Upsert en place.
- **Respect du dirty-skip / verrou optimiste** : ne pas reverter une édition optimiste
  en cours (cf. verrou diffusion c41c727 et conflit non gelant 0da8d0f).
- **Source d'autorité** : prendre le bon champ (ex. offre dans `offre_type.props`, pas
  keyData ; diffusion depuis `hektor_broadcast_listing`, pas ListPasserelles).
- **Pas de restart** : les scripts Python du read-through se relancent par job → effet
  immédiat (contrairement au worker Node).

### Après écriture locale

Le push ciblé (`push_single_annonce_to_supabase.py`) propage déjà la couche dossier ;
vérifier que `etat_transaction` / `offre_id` / `offre_last_proposition_type` /
`compromis_state` repartent bien (ils viennent de `app_view_generale` via
`export_app_payload.py`).

## Test de recette

1. Créer une offre sur un bien de test dans Hektor → ouvrir la fiche → badge « Offre reçue ».
2. Refuser l'offre dans Hektor → **rouvrir la fiche** → le read-through doit repasser
   le badge à « Actif » **sans correction manuelle**.
3. Idem compromis : créer puis annuler → « Sous compromis » puis retour au statut réel.
4. Vérifier qu'aucune édition optimiste en cours n'est reverted.

## Références

- `notice/NOTE_FILTRES_TRANSACTIONS_OFFRES_2026-04-02.md` (design offre/compromis)
- `GRILLE_STATUTS_SOUS_STATUTS_2026-03-23.md` (priorité des statuts, vente sans annulation)
- Commits : 883beeb (derive), b8fc48e (front), cfe3483 (vue), 7c64eb6 (modèle diffusion),
  fb36772 (anti-fenêtre), c41c727 (verrou optimiste), 0da8d0f (conflit non gelant)
