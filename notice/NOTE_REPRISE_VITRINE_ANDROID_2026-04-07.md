# Note de reprise vitrine Android

## Contexte

Dans `Ecrans Android`, on a actuellement :

- le script Python historique :
  - `Ecrans Android/vitrine6.py`
- le front vitrine HTML :
  - `Ecrans Android/vitrine-main/`

Le front vitrine consomme aujourd'hui un JSON de catalogue :

- `Ecrans Android/vitrine-main/data/catalogue_vitrine.json`

Le script `vitrine6.py` sert a reconstruire une data catalogue a partir d'une extraction console / back-office Hektor, avec enrichissement :

- biens actifs
- photos
- pieces / chambres / sdb / wc
- terrain / terrasse / parkings
- telephone
- DPE
- URL

## Objectif vise

L'objectif n'est plus de dependre d'une extraction console Hektor pour alimenter la vitrine.

La cible projet est :

1. utiliser la data du projet comme source
2. repartir de la phase 1 locale synchronisee
3. reproduire le contrat JSON attendu par `vitrine-main`
4. ecrire ce JSON dans le dossier de la vitrine
5. pousser ensuite cette data sur GitHub

En clair :

- source future = data projet
- sortie finale = `catalogue_vitrine.json`
- consommation = `vitrine-main/script.js`

## Structure constatee

### Script actuel

- `Ecrans Android/vitrine6.py`

Role actuel :

- interroge Hektor / console
- parse HTML / GraphQL / photos
- construit un catalogue de biens

### Front actuel

- `Ecrans Android/vitrine-main/index.html`
- `Ecrans Android/vitrine-main/script.js`
- `Ecrans Android/vitrine-main/style.css`
- `Ecrans Android/vitrine-main/data/catalogue_vitrine.json`
- `Ecrans Android/vitrine-main/exports/catalogue_vitrine.json`

Role actuel :

- lit un JSON de catalogue
- affiche les biens sur un ecran Android / vitrine HTML

## Intention de reprise

La reprise devra porter sur :

1. comprendre le contrat exact attendu par `vitrine-main/script.js`
2. identifier les tables phase 1 / phase 2 a lire dans le projet
3. mapper les champs projet vers le format vitrine
4. produire un nouveau script d'export depuis le projet
5. choisir le mecanisme de publication GitHub

## Point important

Le besoin exprime est bien :

- reproduire les HTML de la vitrine
- mais a partir du projet et de la data phase 1
- puis alimenter GitHub avec cette data

Ce n'est donc pas un simple maintien du script `vitrine6.py` existant.
Il s'agit d'un basculement de source de verite.

## Suite logique a la reprise

Au prochain passage, faire dans cet ordre :

1. lire `Ecrans Android/vitrine-main/script.js`
2. figer le schema JSON attendu
3. comparer ce schema avec les champs disponibles en phase 1 / phase 2
4. choisir la bonne source de chaque champ
5. preparer un nouveau script export projet -> vitrine

