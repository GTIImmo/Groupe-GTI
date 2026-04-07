# Cartographie des donnees V1

Date: 23/03/2026

## Objet

Cette note precise quelles donnees sont recuperees via les annonces, lesquelles viennent d'autres endpoints, et ce que la V1 de l'outil pourra exploiter.

## Point important

Il ne faut pas considerer l'annonce comme l'unique source de toutes les donnees metier.

La fiche annonce est un noyau central, mais elle doit etre completee par d'autres objets API.

## Ce qui vient des annonces

Source principale :

- `ListAnnonces`
- `AnnonceById`

Usage retenu :

- `ListAnnonces` pour reperer le parc et les deltas
- `AnnonceById` comme source de verite detaillee sur la fiche annonce

Donnees principalement attendues sur l'annonce :

- identifiant annonce
- numero dossier
- numero mandat
- titre
- type de bien
- prix
- surface
- localisation
- negociateur
- archive
- diffusable
- valide
- statut annonce
- corps / descriptif
- photo
- blocs contact presents dans la fiche
- certaines informations mandat presentes dans la fiche enrichie

## Ce qui ne doit pas etre porte uniquement par l'annonce

Certaines donnees metier doivent continuer a venir d'endpoints dedies.

### Mandats

Sources :

- `ListMandat`
- `MandatById`
- `MandatsByIdAnnonce`

But :

- recuperer la logique mandat de facon plus fiable qu'en s'appuyant uniquement sur le bloc embarque dans l'annonce

### Offres

Sources :

- `ListOffres`
- eventuellement `OffreById` si besoin futur

But :

- reconstruire la couche offre
- derive `offre_state`
- derive `offre_event_date`

### Compromis

Sources :

- `ListCompromis`
- eventuellement `CompromisById` si besoin futur

But :

- reconstruire la couche compromis
- derive `compromis_state`

### Ventes

Sources :

- `ListVentes`
- eventuellement `VenteById` si besoin futur

But :

- reconstruire la couche vente

### Diffusion

Sources :

- `exportReporting`
- `DetailedBroadcastList`

But :

- connaitre l'etat reel de diffusion par portail
- connaitre le detail annonce x passerelle x commercial

### Contacts

Sources :

- `ListContacts`
- bloc contact de `AnnonceById`

But :

- suivre les modifications utiles
- garder le lien contact / annonce

## Ecriture Hektor actuellement documentee

Le seul perimetre d'ecriture clairement documente a ce stade concerne la diffusion.

Endpoints identifies :

- `/Api/Passerelle/addAnnonceToPasserelle/`
- `/Api/Passerelle/removeAnnonceToPasserelle/`
- `/Api/Annonce/ListPasserelles/`
- `/Api/Annonce/Diffuse/`

Conclusion :

- la V1 peut etre en lecture sur la quasi-totalite de la donnee
- la V1 peut viser une action API uniquement sur la diffusion

## Etat actuel retenu sur la base principale

Constat au 23/03/2026 :

- `hektor_annonce` contient le parc source
- `hektor_annonce_detail` contient la fiche annonce enrichie
- `hektor_mandat`, `hektor_offre`, `hektor_compromis`, `hektor_vente` completent l'annonce
- `case_dossier_source` sert de synthese metier

## Ce que la V1 peut exploiter

La V1 de l'outil peut deja s'appuyer sur :

- la fiche annonce
- le mandat rattache
- l'etat de diffusion
- l'etat transactionnel reconstruit
- le negociateur / commercial
- des champs locaux internes ajoutes dans la surcouche

## Lecture fonctionnelle de la V1

Une vue `portefeuille commercial` peut donc raisonnablement afficher :

- le commercial
- le bien
- le mandat
- l'etat de validation
- l'etat de diffusion
- l'etat de commercialisation
- des notes internes
- une priorite
- une prochaine action

## Conclusion

La V1 ne doit pas etre pensee comme une simple vue de `hektor_annonce`.

Elle doit etre pensee comme une vue metier composee a partir de :

- l'annonce
- le mandat
- la diffusion
- le transactionnel
- la surcouche interne
