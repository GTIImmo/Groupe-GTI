# Analyse « identité / clés » — surface des ID Hektor et stratégie de reprise de séquence

**Date : 2026-08-08. Analyse Claude sur la base live (`dwaqxfrinihnychuoptk`) + code pipeline.**
**Complément de `ETUDE_FAISABILITE_DECOUPLAGE_HEKTOR_APP_FIRST_2026-08-08.md` et `INVENTAIRE_WORKERS_ET_PLAN_INDEPENDANCE_2026-08-08.md`.**

## Objet
Répondre à : « l'app utilise déjà l'ID Hektor comme clé, on continue juste la suite de la séquence à la coupure ». Vérifier si c'est exact, mesurer la surface des ID, et donner la stratégie sûre.

---

## 1. Découverte principale (contre-intuitive)

**L'affirmation « l'app utilise l'ID Hektor comme clé » n'est vraie QUE pour les contacts, PAS pour les dossiers/annonces.**

| Entité | Clé primaire app | Rapport à l'ID Hektor | Découplée ? |
|---|---|---|---|
| **Dossier / annonce** | `app_dossier_id` = `d.id` (auto-incrément de phase2.sqlite, `view_generale.py:227`) | `hektor_annonce_id` stocké **à côté** en attribut | ✅ **DÉJÀ découplée** |
| **Contact** | `hektor_contact_id` (c'est l'ID Hektor lui-même) | la clé EST l'ID Hektor | ❌ non découplée |
| **Numéro de mandat** | `numero_mandat` (valeur **affichée**, pas une clé) | généré par protexa Hektor | attribut, pas clé |

Preuve dossier : sur 13 205 dossiers, `app_dossier_id = hektor_annonce_id` → **0 fois**. Plages : `app_dossier_id` 118 → 4 563 643 ; `hektor_annonce_id` max 62 868. Le couple est 1:1 mais **non monotone** (ex. hektor 62853 → app 4397224, hektor 62852 → app 4449967) → `app_dossier_id` est un substitut auto-incrémenté, pas une fonction de l'ID Hektor.

**Conséquence** : le plus gros morceau (dossiers/annonces, référencé par 42 tables) porte **déjà** le motif « identité interne + `hektor_ref` ». Moins de travail que prévu. Le seul vrai point « clé = ID Hektor » est le **contact**.

---

## 2. La surface des ID (ce qui pointe sur Hektor aujourd'hui)

Colonnes d'identité et nombre de tables/vues qui les portent :

| Colonne | Tables | Nature |
|---|---|---|
| `app_dossier_id` | **42** | clé interne app (déjà app-owned) |
| `hektor_annonce_id` | **42** | correspondance Hektor de l'annonce |
| `hektor_contact_id` | **21** | **clé = ID Hektor** (à découpler) |
| `numero_mandat` | **19** | numéro affiché (handover de séquence) |
| `hektor_negociateur_id` | 4 | identité négo (source Hektor) |
| `hektor_agence_id` | 3 | identité agence (source Hektor) |
| `hektor_broadcast_id` | 2 | diffusion |
| `hektor_document_id` | 2 | doc |
| `hektor_user_id` | 2 | mapping Google↔Hektor |
| `mandat_source_id`, `primary_candidate_hektor_contact_id`, `hektor_acquereur_id`, `hektor_affaire_id`, `hektor_mandat_id`, `hektor_photo_id` | 1 chacun | divers |

**Bornes hautes réelles (pour le high-water mark de reprise de séquence) :**
| Espace | Max ID observé | Sources à couvrir |
|---|---|---|
| Annonce (Hektor) | **62 868** | dossier_current (62868), archive (62788), historical (62153), brouillon (62864), **deleted_log (62741)** |
| Contact (Hektor) | **604 866** | contact_current (604866), **deleted_contact_log (604135)** |

> Le high-water mark doit inclure **archivés + supprimés** (les logs `*_deleted_*`), sinon on risque de réattribuer un ID que Hektor a « brûlé » et qu'un lien externe (doc, email, QR déjà émis) pointe encore.

---

## 3. Verdict sur le plan « continuer la suite de la séquence »

**C'est un plan sain et à faible risque** (rien à voir avec le « renuméroter les lignes existantes » dangereux — ici on garde les valeurs existantes et on minte seulement les suivantes). Il est même plus simple que prévu grâce au §1. Conditions pour qu'il soit sûr :

1. **Un seul émetteur d'ID à la fois.** Pendant la transition, la création passe encore par Hektor → **Hektor est le seul à minter** (pas de collision). À la coupure, bascule nette : Hektor s'arrête, l'app prend le relais. Jamais les deux en même temps.
2. **High-water mark sur TOUTES les sources** (actifs + archivés + supprimés) + **marge de sécurité**. Repartir strictement au-dessus (contacts : > 604 866 ; annonces : > 62 868 — mais voir §4, les dossiers n'ont pas besoin de suivre l'espace Hektor).
3. **Cas du mandat (couple).** `hektor_mandat` a une clé composite `(annonce, mandat)` **parce que Hektor réutilise les petits ID de mandat** (idnego). Post-coupure, l'app minte ses propres numéros monotones → le problème de réutilisation disparaît de lui-même. Mais pendant la transition, garder le couple.
4. **Continuité du `numero_mandat`.** Handover avec le partenaire : reprendre **au numéro suivant** du dernier mandat Hektor, **même format légal**, jamais un redémarrage.

---

## 4. Précision importante selon l'entité

- **Dossiers/annonces** : tu n'as PAS besoin de « continuer la séquence Hektor » — `app_dossier_id` est déjà ta séquence (auto-incrément app). Le vrai travail = **minter `app_dossier_id` au moment de la création dans l'app** (aujourd'hui c'est le pipeline qui l'assigne à l'import depuis Hektor). `hektor_annonce_id` reste en attribut pour les 3 workers, puis devient inutile à la coupure.
- **Contacts** : c'est là que ton plan s'applique littéralement (clé = `hektor_contact_id`). Deux options :
  - (a) **Reprendre la séquence** : post-coupure, minter `hektor_contact_id` > 604 866 + marge. Simple, mais tu gardes un nom de colonne « hektor_* » comme clé pérenne (cosmétique) et tu restes exposé à l'idnego contact pendant la transition.
  - (b) **Découpler comme les dossiers** : introduire un `app_contact_id` (substitut app) + `hektor_ref`. Plus propre, aligne les 2 entités, rend la coupure non-événement. Recommandé si tu veux la même robustesse partout.
- **Numéro de mandat** : handover de séquence avec le partenaire (cf. §3.4).

---

## 5. ⚠️ Risque latent à vérifier AVANT d'en faire l'identité pérenne

`app_dossier_id` monte à **4,5 M pour seulement 13 k lignes** → soupçon que le pipeline **réattribue** des `id` lors de delete+reinsert (rebuild). Si `app_dossier_id` **change** entre deux runs, c'est un **bug d'identité indépendant de Hektor** : 42 tables (dont 58 k rapprochements, 28 k affaires) pointent dessus. **À confirmer** : `app_dossier_id` est-il stable dans le temps pour un même bien ? Si non, il faut le **geler** (le rendre immuable) avant d'en faire la clé pérenne — c'est un prérequis à toute la stratégie « app source de vérité ».

---

## 6. Mon avis (synthèse)

- « Continuer la suite de la séquence à la coupure » = **oui, viable et peu risqué** — à condition du §3 (émetteur unique, high-water mark incluant archivés/supprimés, continuité mandat).
- **Bonne nouvelle** : les dossiers/annonces sont **déjà découplés** (`app_dossier_id` ≠ ID Hektor). Le seul vrai chantier « clé = ID Hektor » = les **contacts**.
- **Recommandation** : profiter de ce que les dossiers montrent déjà le bon motif pour **faire pareil sur les contacts** (option 4b) → identité 100 % app partout, la coupure ne touche plus aucun ID. Sinon, l'option 4a (reprendre la séquence contact) reste acceptable et plus légère.
- **Prérequis bloquant** : trancher le §5 (stabilité de `app_dossier_id`). Une clé interne qui bouge est un danger, avec ou sans Hektor.

Rien codé — pure analyse.
