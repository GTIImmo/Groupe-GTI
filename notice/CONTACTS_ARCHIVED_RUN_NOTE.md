Etat au 11/03/2026

- Le run `#39` en cours traite les `contacts` non archives uniquement.
- Verification en base `data/hektor.sqlite` :
  - `list_contacts` existe avec `archive=0`
  - aucun `list_contacts_archived` present
  - aucun `contact_detail` archive present

Dernieres modifications appliquees

- `sync_raw.py`
  - ajout de deux variantes pour `contacts` :
    - `list_contacts_active` avec `archive=0`
    - `list_contacts_archived` avec `archive=1`
  - ajout de `--contacts-archive-scope active|archived|both`
  - `--details-only` permet de sauter les listings
  - `--missing-only` permet de ne pas refaire les `ById` deja presents
  - optimisation de la collecte des IDs pour eviter le blocage observe sur les gros volumes

- `sync_progress.py`
  - prise en charge des nouveaux endpoints `list_contacts_active` et `list_contacts_archived`

- `normalize_source.py`
  - la normalisation des contacts lit maintenant :
    - `list_contacts_active`
    - `list_contacts_archived`
    - `list_contacts` (compatibilite ancien stock)

Commande a lancer apres la fin du run #39

Cette commande lance uniquement :
- le listing des contacts archives
- les `ContactById` des contacts archives

Commande :

`.\.venv\Scripts\python.exe sync_raw.py --resources contacts --contacts-archive-scope archived --max-pages 0 --detail-limit 0 --missing-only`

Effet attendu

- recupere `ListContacts` avec `archive=1`
- recupere tous les `ContactById` pour ces IDs archives
- n'interrompt pas le stock deja present pour les contacts non archives
- ne relance pas `mandats`, `offres`, `compromis`, `ventes`, `broadcasts`

Sequence a faire

1. attendre la fin du run `#39`
2. lancer la commande `contacts archived` ci-dessus
3. lancer les deux derniers scripts de la phase 1 :
   - `.\.venv\Scripts\python.exe normalize_source.py`
   - `.\.venv\Scripts\python.exe build_case_index.py`

But

- completer la phase 1 brute avec les contacts archives en `list` et `ById`
- puis reconstruire les tables source normalisees
- puis reconstruire l'index dossier consolide

Correction du 13/03/2026

- `sync_progress.py` a ete corrige pour que `detail:contacts` repose sur les IDs uniques reels extraits des listings, et non sur la somme des `metadata.total`.
- avant correction, le compteur pouvait afficher un faux ecart du type `344133/398866` car `list_contacts` (equivalent a `archive=0` sur cette API) et `list_contacts_archived` etaient additionnes sans dedoublonnage.
- apres correction, `detail:contacts` affiche le total reel attendu a partir de l'union des IDs de listing presents en base.

Relation annonces -> mandats

- `sync_raw.py` accepte maintenant `--relations-only` pour recalculer uniquement `mandats_by_annonce` a partir des listings d'annonces deja presents en base.
- avec `--missing-only`, la relation ne relance que les annonces qui n'ont pas encore d'entree `mandats_by_annonce`.
- commande ciblee :
  `.\.venv\Scripts\python.exe sync_raw.py --resources annonces --relations-only --missing-only --detail-limit 0`
- modifications apportees au script :
  - ajout de l'option CLI `--relations-only`
  - ajout d'un chemin d'execution dedie pour `annonces_to_mandats` sans relancer listings ni `AnnonceById`
  - ajout d'un mode relation `missing-only` qui exclut les IDs deja presents dans `mandats_by_annonce`
  - conservation du comportement historique quand `--relations-only` n'est pas utilise

Etat du 13/03/2026

- le run `#62` est en cours pour completer `relation:annonces_to_mandats`
- commande lancee :
  `.\.venv\Scripts\python.exe sync_raw.py --resources annonces --relations-only --missing-only --detail-limit 0`
- une fois le run termine, la phase 1 pourra etre reprise

Consigne a reprendre apres le run #62

1. verifier l'etat de progression :
   `.\.venv\Scripts\python.exe sync_progress.py`
2. relancer la normalisation source :
   `.\.venv\Scripts\python.exe normalize_source.py`
3. reconstruire l'index dossier :
   `.\.venv\Scripts\python.exe build_case_index.py`
