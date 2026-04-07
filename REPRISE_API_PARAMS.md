# Parametres API a retenir

Points confirmes dans les mails avec Romain:

- `ListCompromis`: utiliser `withCompromisStatus=false` pour remonter tous les IDs
- `ListOffres`: utiliser `withOfferStatus=false` pour remonter tous les IDs
- `ListVentes`: toujours passer une plage `dateStart` / `dateEnd`

Alignement applique dans le code:

- `sync_raw.py`
- `probe_api.py`

Exemple de synchro:

```powershell
.\.venv\Scripts\python.exe sync_raw.py --resources offres compromis ventes --max-pages 0 --detail-limit 0 --no-with-offer-status --no-with-compromis-status --vente-date-start 2010-01-01 --vente-date-end 2030-12-31
```

Rappel:

- `--max-pages 0` = pagination complete jusqu'a `metadata.nextPage = null`
- `--detail-limit 0` = details `ById` pour tous les IDs recuperes

## Statuts API : offres, compromis, ventes

### Constats actuels

Des verifications ont ete realisees directement sur l'API Hektor afin de confirmer la presence ou non de champs de statut exploitables sur les objets `offre`, `compromis` et `vente`.

#### Compromis

- L'API expose bien un champ `status` sur les compromis.
- Ce champ est recupere et stocke dans `hektor_compromis.status`.
- Dans la base actuelle, les valeurs observees sont principalement :
  - `1` : `10416` lignes
  - `2` : `8` lignes
- L'interpretation metier exacte de ces codes reste a confirmer aupres de Hektor.

#### Offres

- Le pipeline prevoit un mapping d'un statut brut dans `hektor_offre.raw_status`.
- En pratique, les tests API effectues montrent que les champs `status` et `statut` sont `null` dans les reponses offres.
- Verification API realisee :
  - `ListOffres` avec `withOfferStatus=false` : `10927` offres controlees, `0` avec `status` ou `statut` non nul
  - `ListOffres` avec `withOfferStatus=true` : `61` offres controlees, `0` avec `status` ou `statut` non nul
  - `OffreById` teste sur des offres reelles : `status = null`, `statut = null`
- Conclusion a date :
  - `hektor_offre.raw_status` ne peut pas etre considere comme une source metier fiable tant qu'il reste non alimente
  - l'etat de l'offre semble devoir etre reconstruit a partir de `propositions_json`

#### Ventes

- Aucun champ de statut metier explicite n'a ete observe dans les payloads `ListVentes` / `VenteById`.
- A ce stade, une vente semble etre caracterisee uniquement par :
  - sa presence dans l'API
  - sa date (`date` / `date_vente`)
  - ses montants et parties liees

### Hypothese de lecture metier actuelle

#### Offres

En l'absence de `raw_status` exploitable, l'etat de l'offre semble porte par les evenements contenus dans `propositions_json`, par exemple :

- `type = proposition`
- `type = accepte`

Cela conduit a privilegier la logique suivante :

- `raw_status` = champ brut conserve a titre technique
- `offre_state` = champ metier derive a partir de `propositions_json`

### Points en attente de confirmation Hektor

Questions transmises / a transmettre a Hektor :

- confirmer la signification metier de `hektor_compromis.status`
  - `1 = en cours ?`
  - `2 = annule ?`
- confirmer si les offres disposent reellement d'un statut metier dedie dans l'API
- confirmer s'il faut interpreter l'etat des offres uniquement via `propositions`
- confirmer qu'il n'existe pas de statut metier dedie pour les ventes

### Impacts potentiels sur le pipeline

#### Si `raw_status` reste null

- pas de refonte majeure de l'extraction brute des offres
- evolution a faire principalement dans la normalisation metier
- ajout recommande d'un champ derive `offre_state` calcule depuis `propositions_json`

#### Si `raw_status` doit en realite etre alimente

- revoir l'extraction offre pour identifier pourquoi le champ n'est pas recupere
- verifier :
  - endpoint exact
  - emplacement reel du champ dans le JSON
  - eventuel parametre API manquant
  - eventuel changement de contrat sur l'instance

### Point d'attention complementaire

La table `case_dossier_source` ne conserve actuellement qu'une seule offre, un seul compromis et une seule vente par `hektor_annonce_id` (le plus recent selon la logique de ranking).
Si l'objectif est de reconstituer l'historique transactionnel complet d'un dossier, cette synthese est insuffisante a elle seule.

## Note API a retenir apres travail sur le projet ACTIF

### Contacts

Retour corrige de Romain dans `notice/ROMAIN MAIL 2.txt` :

- pour `GET /Api/Contact/ListContacts/`, le bon tri de liste pour suivre les modifications est :
  - `sort=dateLastTraitement`
  - `way=ASC|DESC`
- les combinaisons `sort=datemaj` + `way=ASC|DESC` ne sont pas correctement prises en charge cote API sur l'instance
- symptome observe :
  - `metadata.total` coherent
  - `data=[]`
- le champ `datemaj` reste bien present dans les fiches contact / blocs contact, mais ne doit pas servir comme cle de tri de `ListContacts`

Lecture metier a retenir :

- `dateLastTraitement` sert a detecter des contacts existants modifies
- une modification contact peut ne pas modifier `datemaj` de l'annonce

### Verification API reelle au 22/03/2026

Test direct refait sur l'instance :

- `GET /Api/Contact/ListContacts/?sort=dateLastTraitement&way=DESC`
- la liste est bien retournee
- les items ne contiennent pas le champ `dateLastTraitement`
- les items contiennent bien `datemaj`
- sur plusieurs pages testees, l'ordre observe sur `datemaj` est coherent avec le tri demande

Decision de correction retenue dans `sync_raw.py` :

- conserver `sort=dateLastTraitement` pour interroger l'API
- utiliser `datemaj` comme horloge observable stockee localement
- alimenter `contact_cursor_active` / `contact_cursor_archived` avec `datemaj`
- conserver `date_last_traitement` dans `sync_contact_state` uniquement s'il est un jour renvoye par l'API

### Logique API generale semblee

Le comportement observe sur plusieurs objets confirme une logique en deux niveaux :

- `List...` sert a reperer les objets a rejouer
- `...ById` sert a recuperer l'objet riche complet

Exemples :

- `ListAnnonces` -> `AnnonceById`
- `ListCompromis` -> `CompromisById`
- `ListVentes` -> `VenteById`
- `ListOffres` -> `OffreById`

Conclusion pratique :

- `AnnonceById` est une bonne source de verite pour la fiche annonce enrichie
- mais il ne faut pas lui demander de porter tout le transactionnel
- les objets transactionnels (`offre`, `compromis`, `vente`) doivent continuer a etre recuperes par leurs endpoints dedies, puis rapproches par `annonce.id` et `mandat.id`

### Consequence de conception pour le pipeline principal

Point utile identifie pendant le travail sur `ACTIF` :

- si un contact est modifie, il peut etre pertinent de retrouver les annonces qui le referencent
- puis de rejouer `AnnonceById` sur ces annonces pour remettre a jour leur bloc contact

Cela n'enleve rien au pipeline principal transactionnel, mais ajoute une regle utile pour toute surcouche orientee annonces :

- delta annonces : via `ListAnnonces` + `datemaj`
- delta contacts : via `ListContacts` + `dateLastTraitement`
- rehydratation annonce : via `AnnonceById` sur les annonces liees aux contacts modifies

Cette logique est surtout utile pour une couche metier orientee portefeuille actif / CRM annonce, meme si le pipeline principal garde en plus la collecte dediee des transactions.
