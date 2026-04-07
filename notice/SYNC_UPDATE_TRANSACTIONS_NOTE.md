# Note update transactions

Date: 19/03/2026

## Objet

Finalisation du cadrage `update` dans `sync_raw.py` pour les ressources transactionnelles :

- `mandats`
- `ventes`
- `compromis`
- `offres`

Le choix retenu suit les regles fixees pendant la reprise.

## Regles retenues

### Mandats

Test API realise le 19/03/2026 :

- `ListMandat` avec une fenetre courte du type `2026-01-18 -> 2026-03-19` retourne `0`
- pourtant `ListMandat` sur une fenetre large `2010-01-01 -> 2030-12-31` retourne bien des mandats avec `debut` en `2026`
- les variantes testees avec `state`, `sort`, `way` et `idAgence` ne debloquent pas la fenetre courte
- `sort=debut` et `sort=fin` se revelent non fiables sur cette instance : `metadata.total` remonte mais `data` reste vide

Conclusion retenue :

- sur cette instance, le filtrage `beginDate / endDate` n'est pas suffisamment fiable pour servir de base au mode `update`
- la strategie update des `mandats` est alignee sur une logique de recence, comme pour les `offres` et `compromis`

Implementation retenue :

- `sort = id`
- `way = DESC`
- objectif : rafraichir les `500` mandats les plus recents

Parametre ajoute :

- `--mandat-recent-limit` (defaut `500`)

Implementation :

- calcul du nombre minimal de pages a lire en supposant `20` lignes par page
- lecture des pages recentes seulement
- relance des `MandatById` sur les `500` IDs les plus recents

### Ventes

En mode `update` :

- fenetre fixe de `2 mois`
- `dateStart = today - 2 mois`
- `dateEnd = today`

Parametre ajoute :

- `--vente-lookback-months` (defaut `2`)

### Compromis

En mode `update` :

- tri explicite sur la recence
- `sort = dateStart`
- `way = DESC`
- objectif : rafraichir les `500` plus recents

Parametre ajoute :

- `--compromis-recent-limit` (defaut `500`)

Implementation retenue :

- calcul du nombre minimal de pages a lire en supposant `20` lignes par page
- lecture des pages recentes seulement
- relance des `CompromisById` sur les `500` IDs les plus recents

### Offres

En mode `update` :

- tri explicite sur la recence
- `sort = date`
- `way = DESC`
- objectif : rafraichir les `500` plus recentes

Parametre ajoute :

- `--offre-recent-limit` (defaut `500`)

Implementation retenue :

- calcul du nombre minimal de pages a lire en supposant `20` lignes par page
- lecture des pages recentes seulement
- relance des `OffreById` sur les `500` IDs les plus recents

## Test live realise sur ListOffres

Test API execute sur l'instance Hektor le 19/03/2026.

Cas verifies :

- appel par defaut
- `sort=date&way=DESC`
- `sort=date&way=ASC`
- `sort=id&way=DESC`

Resultat observe :

- `default` et `sort=date&way=DESC` commencent sur l'ID `32830`
- `sort=date&way=ASC` commence sur l'ID `3`
- total remonte : `10938`

Conclusion :

- `ListOffres` accepte bien un tri exploitable
- la recence peut etre pilotee avec `sort=date` et `way=DESC`

## Commande cible de travail

Exemple de mise a jour transactionnelle :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources mandats ventes compromis offres --mandat-recent-limit 500 --missing-only
```

Lecture :

- `mandats` : 500 plus recents via `sort=id&way=DESC`
- `ventes` : 2 mois
- `compromis` : 500 plus recents
- `offres` : 500 plus recentes

## Point de reprise restant

La logique `update` transactionnelle est maintenant cadree dans `sync_raw.py`.
Le sujet qui restera ensuite sera surtout :

- verifier en pratique le comportement sur `ListCompromis` avec `sort=dateStart`
- puis reprendre la couche metier de rapprochement si necessaire
