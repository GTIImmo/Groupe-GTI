## Notification mail decision diffusion

### Objectif

Informer le commercial quand Pauline :

- accepte une demande de diffusion
- refuse une demande de diffusion

### Etat du projet

Il n'existe pas aujourd'hui de vrai service d'envoi d'email dans le projet :

- pas de provider type Resend / Mailjet / Brevo
- pas de configuration SMTP
- pas de backend dedie a l'envoi

### Solution mise en place

Solution pragmatique retenue :

- generation automatique d'un lien `mailto:`
- adresse cible = `negociateur_email`
- ouverture du brouillon juste apres la mise a jour de la demande

Le branchement est fait dans :

- `apps/hektor-v1/src/App.tsx`

apres :

- `updateDiffusionRequest(...)`

### Donnees injectees dans le brouillon

Le mail pre-rempli contient :

- le numero de dossier
- le numero de mandat
- le titre du bien
- la ville
- le commentaire Pauline
- ou le motif de refus

### Limite connue

Ce n'est pas un envoi automatique.

Le comportement actuel depend du poste utilisateur :

- ouverture du client mail par defaut
- validation / envoi manuel ensuite

### Evolution future si besoin

Pour un envoi automatique reel, il faudra ajouter :

- un endpoint backend dedie
- un provider email ou un SMTP
- des variables de configuration
- une gestion des erreurs d'envoi
