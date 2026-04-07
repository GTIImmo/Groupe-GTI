# Reprise Phase 1 SQL

Date de reprise visée: après redémarrage machine.

## État actuel

Le pipeline SQL phase 1 est en place et séparé en 4 scripts:

- `probe_api.py`
- `sync_raw.py`
- `normalize_source.py`
- `build_case_index.py`

Base commune:

- `hektor_pipeline/common.py`

Schéma SQL documenté:

- `sql/schema_phase1.sql`

Note d'usage:

- `PHASE1_SQL.md`

Base SQLite actuelle:

- `data/hektor.sqlite`

## Ce qui fonctionne

Le pipeline tourne réellement contre l'API Hektor.

Chaîne validée:

1. `sync_raw.py`
2. `normalize_source.py`
3. `build_case_index.py`

Une synchro plus large a été lancée avec:

```powershell
.\.venv\Scripts\python.exe sync_raw.py --resources agences negos annonces contacts mandats offres compromis ventes broadcasts --max-pages 10 --detail-limit 200
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
```

## Volumétrie observée sur cette synchro

- `raw_api_response`: `1111`
- `hektor_agence`: `19`
- `hektor_negociateur`: `97`
- `hektor_annonce`: `180`
- `hektor_annonce_detail`: `178`
- `hektor_contact`: `180`
- `hektor_mandat`: `180`
- `hektor_offre`: `59`
- `hektor_compromis`: `84`
- `hektor_vente`: `180`
- `hektor_broadcast`: `22`
- `case_dossier_source`: `180`

## Couverture dossier observée

Après rebuild de `case_dossier_source`:

- dossiers avec `hektor_negociateur_id`: `180/180`
- dossiers avec coordonnées négociateur exploitables: `169/180`
- dossiers avec `mandat_id`: `0/180`
- dossiers avec `offre_id`: `2/180`
- dossiers avec `compromis_id`: `0/180`
- dossiers avec `vente_id`: `0/180`

## Diagnostic honnête

Le problème restant n'est plus le socle SQL ni l'insertion.

La vraie faiblesse est le rapprochement transactionnel:

- lien `mandat -> annonce` encore non fiable sur l'échantillon actuel
- `MandatsByIdAnnonce` retourne souvent vide sur les annonces récentes testées
- les objets `offre`, `compromis`, `vente` existent bien dans la base source, mais ils ne sont pas encore correctement exploités pour reconstruire les dossiers transactionnels

Le build de `case_dossier_source` fonctionne.
La requête SQL de consolidation renvoie bien des lignes.
Le point bloquant est la qualité des liens source, pas un crash du script.

## Ce qui a déjà été tenté

Dans `sync_raw.py`:

- ajout des détails `ById` pour:
  - annonces
  - contacts
  - mandats
  - offres
  - compromis
  - ventes
- ajout de `MandatsByIdAnnonce`

Dans `normalize_source.py`:

- préférence aux payloads `ById`
- tentative de rattachement des mandats via:
  - `idAnnonce`
  - `AnnonceById.mandats`
  - `NO_MANDAT`
  - `MandatsByIdAnnonce`

Dans `common.py`:

- retries HTTP
- meilleure tolérance JSON
- index SQL ajoutés

## Prochaine étape à faire

Ne pas repartir d'abord des annonces récentes.

Construire / fiabiliser le dossier depuis les objets transactionnels eux-mêmes:

1. partir de `hektor_offre`, `hektor_compromis`, `hektor_vente`
2. exploiter leurs propres `annonce.id` et `mandat.id`
3. créer un rapprochement SQL plus intelligent:
   - par `annonce.id`
   - par `mandat.id`
   - par `NO_MANDAT`
   - éventuellement par `numero` de mandat
4. revoir `build_case_index.py` pour qu'il ne dépende pas uniquement de `hektor_annonce` comme pivot de vérité transactionnelle

## Action concrète recommandée à la reprise

1. inspecter en SQL:

```sql
SELECT hektor_annonce_id, COUNT(*) FROM hektor_offre GROUP BY hektor_annonce_id;
SELECT hektor_annonce_id, COUNT(*) FROM hektor_compromis GROUP BY hektor_annonce_id;
SELECT hektor_annonce_id, COUNT(*) FROM hektor_vente GROUP BY hektor_annonce_id;
SELECT hektor_mandat_id, hektor_annonce_id, numero FROM hektor_mandat LIMIT 50;
```

2. vérifier si les IDs annonces des transactions correspondent bien aux annonces synchronisées

3. ajuster `build_case_index.py` pour indexer le dossier à partir des transactions quand elles existent

## Message de contexte pour reprise

Le socle phase 1 extraction SQL est fait.
Le sujet restant est la qualité du rapprochement métier transactionnel.
Il faut maintenant fiabiliser la reconstruction du dossier autour des transactions, pas refaire la base brute.
## Note projet ajoutee le 10 mars 2026

Point confirme pendant la synchro complete:

- le volume de `ListAnnonces` ne correspond pas a l'ensemble des biens
- l'appel actuel sans parametre `archive` remonte en pratique uniquement des annonces `archive=0`
- les `AnnonceById` recuperes ensuite ne couvrent donc eux aussi que les annonces actives

Decision:

- attendre la fin de l'extraction complete en cours
- ne pas finaliser la phase 1 tant que la collecte des annonces archivees n'est pas integree

Prochaine etape avant finalisation de la phase 1:

1. ajouter une double synchro annonces:
   - `archive=0`
   - `archive=1`
2. recuperer les `AnnonceById` sur les IDs issus des deux jeux
3. revalider la volumetrie finale annonces / mandats / dossiers
4. seulement ensuite cloturer la phase 1

Regroupement fonctionnel a retenir pour la suite:

- priorite immediate: integrer les annonces archivees pour ne plus travailler sur un parc incomplet
- juste apres: exploiter correctement les diffusions passerelles a partir de `DetailedBroadcastList`

Objectif fonctionnel diffusions:

- savoir quels biens sont diffuses sur quelles passerelles
- savoir quel commercial est rattache a chaque diffusion
- savoir si la diffusion est en succes ou en erreur

Constat actuel:

- le bon endpoint est deja utilise: `GET /Api/Passerelle/DetailedBroadcastList/`
- les donnees detaillees existent deja dans les payloads recuperes
- mais elles restent stockees au niveau passerelle dans `hektor_broadcast`, avec les annonces enfouies dans `listings_json`

Etape fonctionnelle a faire apres les archivees:

1. conserver comme priorite 1 la double synchro annonces `archive=0` et `archive=1`
2. une fois ce point valide, passer au niveau diffusion detaillee
3. raisonner non plus seulement par passerelle, mais par ligne de diffusion
4. obtenir une structure exploitable du type:
   - `annonce_id`
   - `passerelle`
   - `commercial`
   - `export_status`
5. avec cela, pouvoir repondre simplement a:
   - quels biens sont sur Leboncoin, Bien'ici, SeLoger, etc.
   - quels biens ne sont pas diffuses
   - quels biens sont en erreur de diffusion
   - quel commercial porte quelle diffusion

Ordre logique retenu:

- d'abord completer le parc de biens avec les archivees
- ensuite exploiter proprement les diffusions passerelles
- ensuite seulement envisager la finalisation complete de la phase 1

## Note a retenir apres fin de la premiere extraction complete

Le pipeline actuel sait rejouer des synchronisations et mettre a jour les donnees existantes:

- `raw_api_response` est gere en upsert par endpoint/page ou par objet detail
- les tables normalisees sont rechargees en upsert
- `case_dossier_source` est reconstruit a chaque rebuild

En revanche, il ne faut pas encore le considerer comme une vraie synchronisation incrementale stricte:

- pas de logique visible de delta metier du type `updated_since`
- pas de checkpoint metier explicite par ressource
- fonctionnement plutot base sur relecture des pages et des IDs puis remise a jour locale
- gestion des disparitions cote source non confirmee

Conclusion de reprise:

- apres une premiere extraction complete, le pipeline pourra servir aux mises a jour regulieres
- mais il faudra valider plus tard si un vrai mode incremental propre est necessaire
- en l'etat, le comportement doit etre considere comme une resynchronisation / remise a jour, pas comme un delta minimal garanti

## Note metier a retenir

- `statut_name` dans `case_dossier_source` correspond a l'etat courant de l'annonce dans le CRM
- `offre_id`, `compromis_id`, `vente_id` dans `case_dossier_source` correspondent aux objets transactionnels que le pipeline a effectivement rapproches
- il ne faut pas confondre ces deux niveaux
- pour savoir ou en est actuellement un bien, il faut regarder d'abord `statut_name`
- pour savoir quels evenements transactionnels ont existe et ont ete relies, il faut regarder `offre_id`, `compromis_id`, `vente_id` et les tables sources associees
- il ne faut donc pas conclure qu'une transaction n'existe pas seulement parce que le rapprochement est absent dans `case_dossier_source`
- inversement, la presence d'une transaction rapprochee ne definit pas a elle seule le statut courant de l'annonce

## Photographie precise apres rebuild complet

Date de constat: 13/03/2026

Volumetrie observee:

- `case_dossier_source`: `55997`
- `hektor_annonce`: `55873`
- `hektor_annonce_detail`: `55871`
- `hektor_mandat`: `40868`
- `hektor_contact`: `344133`
- `hektor_offre`: `10925`
- `hektor_compromis`: `10424`
- `hektor_vente`: `3203`
- `hektor_broadcast`: `22`
- `hektor_broadcast_listing`: `1299`

Couverture observee dans `case_dossier_source`:

- avec `no_dossier`: `55946`
- avec `no_mandat`: `23592`
- avec `hektor_agence_id`: `55997`
- avec `hektor_negociateur_id`: `24031`
- avec `statut_name`: `55869`
- avec `prix`: `55996`
- avec `mandat_id`: `23485`
- avec `offre_id`: `9862`
- avec `compromis_id`: `9802`
- avec `vente_id`: `3078`

Repartition archive:

- `archive=1`: `34211`
- `archive=0`: `21786`

Statuts principaux observes:

- `Actif`: `34556`
- `Estimation`: `12278`
- `Vendu`: `8640`
- `Clos`: `252`
- `Sous compromis`: `80`
- `Sous offre`: `63`

Lecture metier a retenir:

- `case_dossier_source` contient un parc large et exploitable, avec integration des archivees
- la couverture annonces et details annonces est quasi complete
- `offre_id`, `compromis_id`, `vente_id` representent des transactions reellement rapprochees, pas l'etat courant de l'annonce
- `case_dossier_source` ne conserve qu'une transaction de reference par type et par annonce
- il peut donc exister plusieurs offres, compromis ou ventes en source pour une meme annonce, alors qu'une seule remontera dans l'index dossier

Qualite de rattachement des tables transactionnelles source:

- `hektor_offre`: `10925/10925` avec `hektor_annonce_id`, seulement `49/10925` avec `hektor_mandat_id`
- `hektor_compromis`: `10424/10424` avec `hektor_annonce_id`, `7181/10424` avec `hektor_mandat_id`
- `hektor_vente`: `3203/3203` avec `hektor_annonce_id`, `2459/3203` avec `hektor_mandat_id`

Conclusion de ce constat:

- le pipeline phase 1 est operationnel
- le vrai sujet restant n'est plus la collecte brute
- le point de vigilance principal reste la qualite du rapprochement metier, en particulier autour des mandats et du choix de la transaction de reference par annonce

## Note SQL a retenir sur les statuts transactionnels

### Situation observee

- `hektor_compromis.status` est bien alimente dans les donnees source et devra etre conserve comme champ brut de reference
- `hektor_offre.raw_status` existe dans le schema mais n'est pas alimente dans les donnees actuellement observees
- `hektor_vente` ne montre pas de statut metier explicite dans les payloads recuperes

### Si Hektor confirme que `raw_status` offre reste null / non exploite

Impacts SQL et metier a prevoir :

- ne pas utiliser `hektor_offre.raw_status` comme source metier
- conserver `raw_status` uniquement comme champ brut technique
- ajouter dans la couche de restitution ou de modele derive un etat metier du type `offre_state`
- calculer `offre_state` a partir de `propositions_json`
- conserver `propositions_json` comme source de verite pour l'historique d'offre

Lecture cible recommandee :

- presence de `type = proposition` => offre deposee / en attente
- presence de `type = accepte` => offre acceptee
- ajouter ensuite d'autres mappings si Hektor confirme d'autres types exploitables

### Si Hektor confirme que `raw_status` devrait etre alimente

Impacts a prevoir :

- revoir la chaine d'extraction offre, pas seulement la couche SQL
- verifier si le champ doit venir de `ListOffres`, `OffreById` ou d'un autre attribut API
- garder ensuite `hektor_offre.raw_status` comme champ brut principal
- ajouter un mapping metier `raw_status -> offre_state`
- conserver `propositions_json` pour le controle de coherence et l'historique

### Compromis

Si Hektor confirme le sens des codes :

- `1 = en cours`
- `2 = annule`

alors il faudra ajouter un mapping metier explicite en sortie, tout en conservant `hektor_compromis.status` brut en base.

### Ventes

Si Hektor confirme l'absence de statut metier dedie :

- ne pas ajouter de faux champ `vente_state` sans source API explicite
- considerer qu'une vente est definie par sa presence dans `hektor_vente` et par `date_vente`

### Point structurel deja identifie

`case_dossier_source` ne conserve qu'une seule transaction par type et par annonce :

- une offre
- un compromis
- une vente

Cette structure est suffisante pour une vue de synthese, mais pas pour restituer l'historique transactionnel complet.

Si l'objectif metier devient la restitution complete du cycle dossier, il faudra prevoir une evolution de modele, par exemple :

- une table d'historique transactionnel par annonce
- ou une restitution multi-lignes par annonce et par type d'evenement
