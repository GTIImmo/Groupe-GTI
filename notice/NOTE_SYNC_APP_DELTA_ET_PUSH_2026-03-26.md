# Note sync app delta et push

Date: 2026-03-26

## 1. Point d'arret reel

Le sync app courant termine et exploitable est:

- `sync_run_id`: `0392e722-53b8-42f5-a8e2-22b3132b635b`

Etat final valide sur ce run:

- `app_dossier_v1`: `55976`
- `app_dossier_detail_v1`: `55976`
- `app_work_item_v1`: `21377`
- `app_filter_catalog_v1`: `62`

Ce run a ete complete en reprenant un sync partiel et en terminant les tables manquantes par `upsert`.

## 2. Ce qui a pose probleme

Les points de blocage observes pendant les essais:

- `app_dossier_detail_v1` est la table la plus lourde.
- un push global classique peut echouer sur:
  - `500` avec `statement timeout`
  - `520` cote edge / proxy Supabase
- quand le push s'arrete avant `app_filter_catalog_v1`, l'app charge un catalogue incomplet.
- si `app_filter_catalog_v1` est incomplet, les filtres `Commercial` et autres listes deviennent incomplets.

Probleme specifique constate:

- `offre_id`, `compromis_id`, `vente_id` existaient bien dans le detail, mais etaient retires du bloc `dossiers`.
- consequence:
  - le filtre `Affaires` retournait `0`
  - alors que les donnees transaction existaient bien en phase 1

Correctif applique:

- `phase2/sync/export_app_payload.py`
- les champs suivants restent maintenant aussi dans `dossiers`:
  - `offre_id`
  - `compromis_id`
  - `vente_id`

## 3. Methode de push qui a marche

La methode fiable observee n'est pas:

- `delete` massif sur les tables app
- puis `upsert` massif sur le sync courant

Cette methode provoque trop facilement des `500`.

La methode qui a fonctionne:

- reprendre le `sync_run` courant incomplet
- faire des `upsert` par lots
- avec detail plus petit que le reste

Tailles de lot fiables constatees:

- `app_dossier_v1`: `100`
- `app_dossier_detail_v1`: `50`
- `app_work_item_v1`: `100`
- `app_filter_catalog_v1`: `100`

Conclusion operationnelle:

- pour les prochains push lourds, garder `detail` en `50`
- ne pas considerer `100` comme fiable pour `app_dossier_detail_v1`

## 4. Pourquoi un vrai delta n'est pas encore natif

Le schema Supabase actuel est un schema de snapshots par `sync_run`:

- `app_dossier_v1`
- `app_dossier_detail_v1`
- `app_work_item_v1`
- `app_filter_catalog_v1`

Toutes ces tables sont liees a:

- `sync_run_id`

et les vues courantes pointent vers:

- `app_latest_sync_run`

Donc aujourd'hui, le contrat est:

- un run = un snapshot complet coherent

Ce point est critique:

- si on pousse seulement une partie du nouveau delta dans un nouveau `sync_run`
- alors `app_latest_sync_run` bascule sur un snapshot incomplet
- et l'app devient incoherente

Conclusion:

- avec le schema actuel, un vrai mode incremental pur n'est pas encore naturel
- il faut soit:
  - finir integralement chaque nouveau `sync_run`
  - soit changer l'architecture de sync

## 5. Solution recommandee pour une vraie mise a jour reguliere

Si le projet doit etre mis a jour regulierement comme l'upgrade phase 1, la bonne direction est:

### Option recommandee

Passer d'un modele `snapshot par sync_run` a un modele `tables courantes upsertables`.

En pratique:

- garder `app_sync_run` pour l'historique
- mais ne plus faire de `app_latest_sync_run` comme source unique de lecture
- lire l'app depuis des tables courantes uniques, par exemple:
  - `app_dossier_current`
  - `app_dossier_detail_current`
  - `app_work_item_current`
  - `app_filter_catalog_current`

Et sur ces tables:

- `upsert` des nouveautes
- `upsert` des modifications
- suppression ciblee seulement si un dossier disparait vraiment

Avantages:

- vrai delta possible
- pas besoin de reconstruire tout un snapshot complet
- plus adapte a des mises a jour frequentes

## 6. Strategie delta recommande pour la phase 1

Pour ne pousser que les nouveautes et modifications, y compris les transactions:

### 6.1 Detecteur principal

Utiliser la phase 1 comme source de verite du delta:

- `hektor_annonce_id`
- `datemaj`

Principe:

- un dossier est a repusher si:
  - il est nouveau
  - ou `datemaj` a change

### 6.2 Detecteur transactions

Le delta annonce seul ne suffit pas toujours.

Il faut aussi surveiller les changements sur:

- offres
- compromis
- ventes

Selon les champs source disponibles, il faut prendre:

- `offre_id` + date / statut offre
- `compromis_id` + date / statut compromis
- `vente_id` + date vente

Regle pratique:

- si une transaction change pour une annonce
- alors re-pusher:
  - `app_dossier`
  - `app_dossier_detail`
  - les `work_items` lies

### 6.3 Sous-ensemble a recalculer

Pour chaque run delta:

1. identifier les `app_dossier_id` modifies
2. reconstruire seulement ces dossiers depuis `app_view_generale`
3. reconstruire seulement leurs details
4. reconstruire seulement les work items lies
5. recalculer le catalogue de filtres

### 6.4 Catalogue des filtres

Le catalogue de filtres est un point sensible.

Deux options:

- soit le recalculer completement a chaque run
- soit le regenerer depuis les tables courantes completes

Recommendation:

- ne pas le faire en delta partiel "naif"
- sinon on perd des valeurs de filtre

## 7. Mise en oeuvre conseillee

Ordre recommande:

1. conserver le pipeline phase 1 / phase 2 actuel
2. ajouter des tables courantes app dediees au delta
3. faire un script `push_current_to_supabase.py`
4. faire un mode `delta` pilote par:
   - `datemaj` annonces
   - changements offres / compromis / ventes
5. garder le push snapshot complet uniquement comme outil de secours

## 8. Regles a retenir pour les prochains push

- ne pas purger massivement les tables app comme reflexe
- ne pas faire de `delete` global puis `upsert` global sur un sync courant
- ne pas lancer un nouveau `sync_run` si on n'est pas certain de pouvoir le finir
- si reprise partielle necessaire:
  - `dossiers` en `100`
  - `detail` en `50`
  - `work_items` en `100`
  - `filter_catalog` en `100`
- verifier a la fin:
  - `app_dossier_v1`
  - `app_dossier_detail_v1`
  - `app_work_item_v1`
  - `app_filter_catalog_v1`

## 9. Decision projet recommandee

Decision recommandee a court terme:

- garder le schema actuel pour stabiliser l'app
- faire les pushes complets avec detail en `50`

Decision recommandee a moyen terme:

- ouvrir un lot de travail pour un vrai mode delta applicatif
- base sur des tables courantes upsertables
- pilote par les nouveautes phase 1 + modifications transactionnelles

## 10. Methode cible sans coder

Objectif:

- garder une app coherente
- permettre des mises a jour regulieres
- eviter le repush complet systematique
- prendre en compte les nouveautes phase 1 et les changements de transactions

Methode recommandeee:

### A. Garder 2 modes distincts

1. mode `snapshot complet`

- sert de base propre
- utile apres gros changement de schema ou en reprise
- produit un run complet coherent

2. mode `mise a jour courante`

- sert au quotidien
- ne pousse que les dossiers impactes
- ne doit pas reposer sur un `sync_run` partiel

### B. Principe cle

Si l'app continue a lire uniquement `app_latest_sync_run`, alors un delta partiel casse la coherence.

Donc pour un vrai mode mise a jour reguliere, il faut viser:

- historique des snapshots d'un cote
- tables courantes de lecture de l'autre

### C. Cible d'architecture

Conserver:

- `app_sync_run`
- les snapshots complets ponctuels

Ajouter ensuite une couche courante exploitable:

- `app_dossier_current`
- `app_dossier_detail_current`
- `app_work_item_current`
- `app_filter_catalog_current`

L'app du quotidien doit lire cette couche courante.

### D. Detection du delta

Le delta doit partir de la phase 1.

Declencheurs principaux:

- nouvelle annonce
- annonce modifiee via `datemaj`
- changement mandat
- changement offre
- changement compromis
- changement vente
- changement nego / diffusion si remonte par la source

Regle simple:

- un dossier est a recalculer si lui-meme change
- ou si une transaction liee change

### E. Unite de recalcul

Pour un run courant:

1. identifier les `app_dossier_id` impactes
2. recalculer uniquement ces dossiers
3. mettre a jour leur detail
4. mettre a jour les demandes liees
5. regenerer proprement le catalogue des filtres

### F. Catalogue de filtres

Le catalogue ne doit pas etre gere en delta naive.

Recommendation:

- le recalculer completement a chaque mise a jour courante
- ou le reconstruire depuis les tables courantes completes

Il est petit, donc il vaut mieux privilegier la coherence.

### G. Rythme de fonctionnement conseille

- 1 snapshot complet de reference chaque nuit ou chaque semaine
- plusieurs mises a jour courantes pendant la journee
- si une mise a jour courante echoue, l'app reste sur l'etat courant precedent
- si gros incident, on refait un snapshot complet

### H. Ce qu'il faut eviter

- nouveau `sync_run` partiel lu directement par l'app
- `delete` massif avant recharge
- `upsert` geant sans separation listing / detail
- catalogue de filtres incomplet

### I. Resume decisionnel

Court terme:

- stabiliser avec snapshot complet + detail en batch `50`

Moyen terme:

- mettre en place une couche courante upsertable
- piloter les updates par delta phase 1 + transactions

Cette methode est la plus adaptee si le projet doit etre mis a jour regulierement comme l'upgrade phase 1.
