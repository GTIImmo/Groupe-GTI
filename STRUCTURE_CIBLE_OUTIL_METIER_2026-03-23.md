# Structure cible de l'outil metier

Date: 23/03/2026

## Objet

Cette note documente la meilleure proposition de structure fonctionnelle de l'outil metier a construire au-dessus de Hektor.

Elle synthétise les usages reels de :

- Pauline
- Delphine
- les managers
- les negociateurs

## Positionnement de l'outil

L'outil ne doit pas remplacer Hektor.

Hektor reste :

- l'outil principal de saisie CRM
- l'outil quotidien principal des commerciaux / negociateurs

L'outil a construire doit etre :

- un outil complementaire de pilotage
- un outil de controle
- un outil de coordination
- un outil de visibilite
- un outil de relance et de suivi

## Probleme metier a resoudre

Hektor ne donne pas assez bien :

- la vision globale des dossiers
- la vision claire des biens reellement diffuses
- la lecture par passerelle
- la coordination entre administratif, negociateurs et managers
- la gestion simple des demandes et validations
- la lecture des retards et blocages
- les relances structurees
- les reportings metier utiles

## Principe d'organisation

L'outil ne doit pas etre pense comme une simple liste de biens.

Il doit etre organise par processus metier / files de travail.

Le coeur du systeme est :

- un dossier
- des evenements detectes
- des statuts
- des decisions
- des relances
- des actions

## Logique metier generale

Cycle metier simplifie :

1. mandat cree
2. demande de diffusion / validation
3. validation administrative
4. bien autorise a etre diffuse
5. choix des passerelles par le negociateur
6. diffusion effective sur portails
7. offre
8. compromis
9. vente
10. pilotage global, relances, suivi des retards

## Distinction importante sur la diffusion

Il faut distinguer plusieurs niveaux :

- bien non valide pour diffusion
- bien valide / autorise a diffuser
- bien diffuse sur le site / diffusable
- bien effectivement diffuse sur une ou plusieurs passerelles

Cette distinction est essentielle pour ne pas melanger :

- la validation par Pauline
- le choix de diffusion par le negociateur
- l'etat reel lu sur les passerelles

## Structure cible proposee

Je recommande 5 blocs principaux.

### 1. Demandes mandat / diffusion

Public principal :

- Pauline

But :

- traiter les demandes administratives autour du mandat et de la diffusion

Cas principaux :

- demande de diffusion
- avenant baisse de prix
- annulation de mandat
- mandat genere mais non encore diffuse
- bien non visible mais non annule
- demande incomplete
- demande a corriger

Apport de l'outil :

- file claire
- vision globale
- suivi des validations
- suivi des refus
- suivi des demandes en attente

### 2. Diffusion passerelles

Public principal :

- negociateurs

But :

- voir clairement les biens autorises a diffuser
- choisir les portails
- controler la diffusion reelle
- voir les erreurs de diffusion

Cas principaux :

- bien valide mais non encore pousse
- bien diffuse sur certains portails seulement
- bien en erreur de diffusion
- bien diffusable mais oublie
- bien non valide donc non actionnable

Apport de l'outil :

- vision claire des biens reellement diffuses
- choix simple des passerelles
- lecture fiable par portail
- completement de Hektor sur son point faible diffusion

### 3. Suivi transaction

Public principal :

- Delphine

But :

- suivre les offres jusqu'a la vente definitive

Cas principaux :

- offre recue
- offre a saisir / a suivre
- date de compromis fixee
- compromis signe
- offre sans compromis avec delai depasse
- offre de pret
- date de vente fixee
- dossier bloque
- vente avec delai trop important

Apport de l'outil :

- sortie du suivi disperse mails + Excel
- lecture claire du cycle transactionnel
- detection des retards
- support a la relance

### 4. Pilotage global

Public principal :

- managers

But :

- superviser le parc, les retards, les blocages et les resultats

Cas principaux :

- dossiers en retard
- demandes non traitees
- commerciaux souvent relances
- blocages repetes
- suivi des resultats par commercial
- lecture managériale des mandats, diffusions, offres, compromis, ventes

Apport de l'outil :

- vision globale
- meilleur pilotage des equipes
- detection des defaillances
- aide a la motivation / valorisation

### 5. Fiche dossier

Public :

- commun a tous les profils

But :

- fournir la synthese partagee d'un dossier

Contenu attendu :

- annonce
- mandat
- commercial / negociateur
- diffusion
- detail passerelles
- transaction
- notes
- commentaires internes
- relances
- blocages
- prochaines actions

## Proposition d'ecrans

### Accueil

But :

- donner un tableau de bord rapide de la journee

Elements utiles :

- demandes en attente
- biens valides non diffuses
- erreurs de diffusion
- offres a traiter
- dossiers bloques
- alertes managers

### Ecrans principaux

- `Demandes mandat / diffusion`
- `Diffusion passerelles`
- `Suivi transaction`
- `Pilotage global`
- `Fiche dossier`

## Donnees a exploiter

L'outil doit s'appuyer sur la base principale deja construite.

### Couche Hektor locale

- annonces
- details annonce
- mandats
- offres
- compromis
- ventes
- diffusion
- synthese dossier

### Couche locale interne a ajouter

- notes internes
- priorites
- statuts internes
- relances
- motifs de blocage
- commentaires administratifs
- commentaires managers
- decisions

## Ecriture Hektor retenue pour la V1

Le seul perimetre d'ecriture Hektor clairement documente a ce stade est la diffusion.

Actions visees :

- ajouter une annonce a une passerelle
- retirer une annonce d'une passerelle
- lire les passerelles disponibles
- lire l'etat reel de diffusion

Endpoints documentes :

- `/Api/Passerelle/addAnnonceToPasserelle/`
- `/Api/Passerelle/removeAnnonceToPasserelle/`
- `/Api/Annonce/ListPasserelles/`
- `/Api/Annonce/Diffuse/`

## Proposition de construction par etapes

### V1.1

Priorite immediate :

- `Demandes mandat / diffusion`
- `Diffusion passerelles`
- `Fiche dossier`

Raison :

- gain direct pour Pauline et les negociateurs
- valeur immediate sur la diffusion et la validation

### V1.2

Ajout :

- `Suivi transaction`

Raison :

- sortir Delphine du suivi Excel / mails

### V1.3

Ajout :

- `Pilotage global`

Raison :

- consolider les indicateurs managers apres stabilisation des files precedentes

## Conclusion

La meilleure structure cible n'est pas :

- un CRM bis
- une simple liste de biens
- une vue purement commerciale

La meilleure structure cible est :

- un outil complementaire a Hektor
- organise par processus metier
- centre sur les files de travail
- partage autour d'une fiche dossier commune

## Suite logique

La prochaine etape de conception peut porter sur :

1. le modele des vues / ecrans
2. le modele des tables metier locales
3. la couche SQL a exposer a l'interface
