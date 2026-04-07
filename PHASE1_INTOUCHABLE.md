# Phase 1 intouchable

Date: 23/03/2026

## Principe

La phase 1 constitue le socle technique de reference du projet.

Elle ne doit pas etre modifiee dans le cadre de la construction de la surcouche metier.

## Regle de travail

Sauf decision explicite contraire, il ne faut pas toucher :

- aux scripts de phase 1
- aux tables de phase 1
- aux donnees produites par la phase 1
- a la logique de synchronisation / normalisation / build de phase 1

## Perimetre concerne

Scripts concernes :

- `sync_raw.py`
- `normalize_source.py`
- `build_case_index.py`

Base de reference concernee :

- `data/hektor.sqlite`

Tables source / consolidees concernees :

- toutes les tables issues du pipeline principal
- toutes les tables de synthese construites en phase 1

## Consequence pratique

Toutes les evolutions suivantes doivent etre faites :

- dans une surcouche separee
- avec de nouvelles tables locales
- avec de nouvelles vues
- avec de nouveaux scripts
- avec une nouvelle interface

## Architecture retenue

- phase 1 = socle Hektor local
- phase 2 = surcouche metier locale
- phase 3 = interface, workflows, actions

## But de cette regle

Eviter de melanger :

- le socle de donnees de reference
- et l'outil metier en construction

Eviter aussi :

- les regressions sur le pipeline principal
- la perte de stabilite acquise
- les refontes inutiles du socle

## Exception

Une modification de phase 1 ne peut etre faite que si :

- elle est volontaire
- elle est explicitement decidee
- elle repond a un vrai besoin sur le socle lui-meme

Par defaut :

- phase 1 = intouchable
