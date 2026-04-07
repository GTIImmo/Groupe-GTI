# Note delta annonces / contacts

Date: 19/03/2026

## Constat valide

### Annonces

- `ListAnnonces` expose bien un champ `datemaj`
- le tri `sort=datemaj&way=DESC` fonctionne sur l'instance
- cela permet une vraie logique de delta fiable a partir de :
  - `id`
  - `datemaj`

### Contacts

- `ListContacts` expose bien un champ `datemaj`
- en revanche, sur cette instance, `sort=datemaj` renvoie `metadata.total` mais `data=[]`
- le champ est donc visible, mais le tri `datemaj` n'est pas exploitable tel quel

## Decision de travail

### Annonces

- ajouter / conserver `date_maj` dans `hektor_annonce`
- alimenter `date_maj` depuis les listings `ListAnnonces`
- preparer ensuite un vrai mode delta :
  - nouvelle annonce = `id` inconnu
  - annonce modifiee = `id` connu mais `date_maj` differente
  - `AnnonceById` seulement pour les nouvelles ou modifiees

### Contacts

- ajouter / conserver `date_maj` dans `hektor_contact`
- alimenter `date_maj` depuis les listings `ListContacts`
- ne pas utiliser `sort=datemaj` tant qu'il reste casse sur l'instance
- raisonner a part :
  - les contacts actifs
  - les contacts archives
- comparer localement :
  - `id`
  - `date_maj`
- accepter qu'un run court ne garantisse pas a lui seul la couverture de toutes les anciennes fiches modifiees

## Correctif deja applique

- `hektor_annonce.date_maj` est ajoute au schema SQL et alimente depuis les listings annonces
- `hektor_contact.date_maj` existait deja dans le schema et reste alimente depuis les listings contacts

## Suite a faire

1. amorcer un stock global `datemaj` annonces via un run listings annonces complet en mode `update`
2. relancer `normalize_source.py`
3. seulement apres cela, ajouter un vrai arret intelligent / delta dans `sync_raw.py` pour les annonces
4. pour les contacts, tester ensuite une strategie plus fine si un ordre API exploitable est confirme

## Point d'arret de reprise

Au point actuel, il ne faut pas encore lancer un nouveau run global uniquement pour amorcer `datemaj`.

Decision de reprise retenue :

- attendre d'abord le retour de Romain sur l'anomalie `ListContacts` avec `sort=datemaj`
- si Romain confirme / corrige ce point, reevaluer :
  - un run global annonces pour amorcer proprement `datemaj`
  - puis eventuellement un run global contacts si le tri / filtre `datemaj` devient exploitable

Etat avant attente :

- le code sait maintenant stocker `hektor_annonce.date_maj`
- `normalize_source.py` peut deja remplir `date_maj` pour les annonces vues dans les runs `update`
- mais le full historique annonces ne contenait pas `datemaj`
- et les contacts ne doivent pas etre re-amorces globalement avant clarification cote API
