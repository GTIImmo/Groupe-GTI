# Definition V1 outil metier

Date: 23/03/2026

## Objet

Cette note fixe la premiere version fonctionnelle de l'outil metier a construire au-dessus de la base locale Hektor.

Elle sert de cadre de travail pour la suite du projet.

## Positionnement de la V1

La V1 n'a pas pour but de refaire tout Hektor.

La V1 doit fournir un premier outil utile, simple et exploitable au quotidien, a partir de la base locale deja synchronisee.

## Principe general

La V1 repose sur :

- lecture de la base locale issue du pipeline principal
- ajout de donnees metier locales
- action Hektor limitee au perimetre diffusion

## Perimetre fonctionnel V1

La V1 doit couvrir prioritairement :

- portefeuille commercial
- suivi diffusion
- suivi validation mandat
- suivi commercialisation

## Point d'entree principal

Le point d'entree principal de la V1 est :

- `portefeuille commercial`

Cette vue devient l'ecran central de consultation et de pilotage.

## Logique de la vue portefeuille commercial

Une ligne correspond a un bien / dossier / mandat exploitable.

Cette vue doit permettre a un utilisateur de :

- voir rapidement les biens dont il a la charge
- comprendre leur etat de diffusion
- comprendre leur etat de validation
- comprendre leur etat de commercialisation
- identifier les actions a mener

## Ecrans V1

### 1. Liste portefeuille commercial

Ecran principal.

But :

- afficher les biens sous forme de liste filtrable
- servir de point d'entree quotidien

Fonctions attendues :

- filtres
- tri
- recherche
- lecture rapide des statuts utiles

### 2. Fiche bien / dossier

Ecran detail.

But :

- afficher la fiche d'un bien de maniere exploitable
- centraliser la lecture Hektor et les donnees internes

Fonctions attendues :

- lecture des informations annonce
- lecture des informations mandat
- lecture de la diffusion
- lecture transactionnelle utile
- ajout de notes internes
- ajout d'actions internes

### 3. Vue actions / priorites

Ecran de pilotage.

But :

- mettre en avant les biens a traiter
- aider a la relance et au suivi quotidien

Fonctions attendues :

- biens a relancer
- biens non diffuses
- biens en erreur de diffusion
- biens a priorite haute
- biens a valider

## Donnees a lire dans la V1

La V1 doit lire des informations issues de plusieurs couches.

### Donnees Hektor locales

Issues du pipeline principal :

- annonce
- detail annonce
- mandat
- offre
- compromis
- vente
- diffusion
- synthese `case_dossier_source`

### Donnees metier locales

A ajouter dans la surcouche :

- note interne
- priorite
- statut interne
- prochaine action
- date de relance
- resultat de relance
- blocage identifie

## Ecriture dans la V1

### Ecriture locale

La V1 doit permettre d'editer localement :

- notes
- priorites
- statuts internes
- relances
- actions a faire

### Ecriture Hektor

Le seul perimetre d'ecriture Hektor clairement documente pour la V1 est la diffusion.

Actions visees :

- ajouter une annonce sur une passerelle
- retirer une annonce d'une passerelle
- consulter l'etat reel de diffusion

Endpoints identifies :

- `/Api/Passerelle/addAnnonceToPasserelle/`
- `/Api/Passerelle/removeAnnonceToPasserelle/`
- `/Api/Annonce/ListPasserelles/`
- `/Api/Annonce/Diffuse/`

## Champs metier utiles pour la vue principale

Champs prioritaires :

- commercial
- negociateur
- hektor_annonce_id
- numero_dossier
- numero_mandat
- titre_bien
- ville
- type_bien
- prix
- statut_annonce
- statut_mandat
- validation_mandat
- etat_commercialisation
- etat_diffusion
- nb_portails_actifs
- portails
- date_derniere_maj
- priorite_interne
- prochaine_action
- date_relance_prevue
- note_interne_resume

## Filtres prioritaires

La V1 doit permettre au minimum de filtrer par :

- commercial
- etat diffusion
- statut mandat
- validation mandat
- etat commercialisation
- priorite
- ville
- type de bien

## Premiers usages quotidiens

La V1 doit rendre possibles des usages simples et immediats :

- voir les biens d'un commercial
- voir les biens diffuses / non diffuses
- voir les biens a traiter
- voir les biens prioritaires
- noter une action interne
- preparer une relance
- lancer une action de diffusion ou de retrait

## Ce que la V1 ne doit pas chercher a faire

La V1 ne doit pas encore chercher a :

- modifier librement tous les champs Hektor
- reconstituer toute l'interface Hektor
- couvrir tous les workflows internes de l'agence
- gerer tous les reportings avances

## Strategie de construction

Ordre recommande :

1. preparer une vue SQL metier principale
2. definir les tables locales de surcouche
3. construire l'ecran liste
4. construire la fiche bien
5. ajouter la vue actions
6. brancher ensuite les actions API diffusion

## Definition de reussite de la V1

La V1 sera consideree comme utile si elle permet deja :

- a un commercial ou responsable de voir son portefeuille
- d'identifier l'etat de diffusion d'un bien
- d'ajouter des informations internes de suivi
- d'identifier les priorites
- de lancer une premiere action API sur la diffusion

## Suite logique apres la V1

Apres validation de la V1, les evolutions logiques seront :

- enrichissement de la surcouche CRM
- relances automatisees
- reporting
- vues par role
- extension progressive des actions de retour API
