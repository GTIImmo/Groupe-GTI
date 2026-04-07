# Note sync_raw update

Date: 19/03/2026

## Objet

Premier lot de modifications sur `sync_raw.py` pour preparer un usage double :

- extraction globale
- extraction de mise a jour

Le choix retenu est de conserver un seul moteur d'extraction, sans creer un deuxieme script pour l'instant.

## Modifications apportees

### 1. Ajout d'un mode de synchro

`sync_raw.py` accepte maintenant :

- `--mode full`
- `--mode update`

Le mode par defaut reste `full` pour ne pas casser les usages existants.

### 2. Parametres de mise a jour ajoutes

Nouveaux arguments :

- `--lookback-days`
- `--update-max-pages`
- `--update-detail-limit`

But :

- definir une fenetre recente pour les mises a jour
- limiter le nombre de pages relues en mode `update`
- augmenter le nombre de `ById` rejoues quand on travaille en mise a jour

### Valeurs quotidiennes retenues au 22/03/2026

Les valeurs par defaut du script ont ete recalees pour l'usage quotidien courant :

- `--offre-recent-limit = 1000`
- `--compromis-recent-limit = 1000`
- `--vente-lookback-months = 12`

But :

- ne pas dependre d'une commande trop longue au quotidien
- garder un update transactionnel plus large par defaut

### 3. Annonces et contacts

En mode `update`, les listings `annonces` et `contacts` sont maintenant prepares avec :

- `sort=datemaj`
- `way=DESC`

But :

- commencer par les fiches les plus recemment modifiees
- rendre la mise a jour quotidienne plus coherente avec le retour de Romain

### 4. Mandats et ventes

En mode `update`, si aucune plage n'est fournie explicitement :

- `mandats` prend une fenetre `today - lookback_days` -> `today`
- `ventes` prend une fenetre `today - lookback_days` -> `today`

Si des dates sont passees manuellement, elles restent prioritaires.

### 5. Refactoring interne minimal

`sync_raw.py` n'utilise plus directement la configuration globale modifiee en place.
Une copie locale de `RESOURCE_CONFIG` est construite au lancement, puis adaptee selon le mode choisi.

But :

- eviter les effets de bord
- garder le comportement `full` stable

### 6. Separation correcte des endpoints full / update

Correction ajoutee apres reprise :

- en mode `update`, les ressources sans bloc `variants` (`mandats`, `offres`, `compromis`, `ventes`) ecrivaient encore dans les endpoints canoniques :
  - `list_mandats`
  - `list_offres`
  - `list_compromis`
  - `list_ventes`
- cause : le renommage en `_update` ne s'appliquait qu'aux variantes explicites, pas aux ressources simples
- correctif applique :
  - `annonces` / `contacts` continuent a utiliser leurs variantes `_update`
  - `mandats` / `offres` / `compromis` / `ventes` utilisent maintenant bien :
    - `list_mandats_update`
    - `list_offres_update`
    - `list_compromis_update`
    - `list_ventes_update`

But :

- separer proprement le stock brut `full` du stock brut `update`
- permettre a `normalize_source.py` et aux scripts de controle de distinguer clairement les deux usages

## Ce que ce lot ne fait pas encore

- pas d'arret intelligent quand on retombe sur des objets deja connus
- pas encore de vrai mode "recent only" explicite pour `compromis`
- pas encore de logique metier speciale pour les `offres` basee sur les `propositions`
- pas encore de commande prete a l'emploi documentee pour la mise a jour quotidienne

## Lecture de reprise

Ce lot prepare le socle de la mise a jour dans `sync_raw.py`, mais ne cloture pas encore tout le sujet incremental.
Le prochain lot devra surtout :

- verifier les parametres exacts supportes par Hektor pour la recence sur `compromis`
- definir une commande quotidienne cible
- decider si l'on ajoute un vrai mecanisme d'arret sur objets deja connus

## Commande de travail a tester ensuite

Exemple de mise a jour ciblee :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources annonces contacts mandats ventes --lookback-days 7 --missing-only
```

Lecture :

- `annonces` et `contacts` tries par `datemaj DESC`
- `mandats` et `ventes` limites aux 7 derniers jours si aucune date n'est fournie
- `missing-only` evite de rejouer les details deja presents
