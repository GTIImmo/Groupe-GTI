## Reprise chantier emails / relances

### Contexte

Le socle utilisateurs et droits est maintenant en place.

Le chantier en cours porte sur :

1. optimisation des emails de notification
2. mise en place du workflow de relance
3. ensuite seulement nettoyage / mise au propre avant GitHub

---

## 1. Etat actuel valide

### Utilisateurs

Le module utilisateurs est fonctionnel :

- creation utilisateur
- mise a jour utilisateur
- activation / archivage via `is_active`
- gestion des roles
- mot de passe oublie depuis login
- reset mot de passe depuis l'admin
- ecran de recovery apres clic mail Supabase

### Cloisonnement des droits

Le role `commercial` est maintenant limite :

- dans le front
- et via RLS Supabase

Regle actuelle :

- `commercial` : voit seulement les annonces liees a son `negociateur_email`
- `admin` : vue globale
- `manager` : vue globale
- `lecture` : vue globale

### SMTP

L'envoi SMTP fonctionne.

Les emails partent automatiquement apres :

- acceptation
- refus

---

## 2. Etat actuel des emails

### Ce qui est deja en place

Les mails de decision sont maintenant :

- automatiques
- en `text + html`
- envoyes au negociateur
- signes avec le nom utilisateur si disponible

### Evolution deja faite

Le template a ete simplifie pour ressembler a une notification :

- format compact
- une seule action utile
- bouton `Ouvrir dans l'application`
- plus de lien Hektor dans le mail
- plus de photo
- moins de blabla

### Deep link application

Le bouton application embarque un lien profond qui ouvre :

- l'ecran `mandats`
- le bon `app_dossier_id`
- directement le popup de demande

Format de lien :

```text
/?screen=mandats&app_dossier_id=123&open=request&role=nego
```

### Correction deja faite

Le motif de refus utilise maintenant le libelle lisible.

Exemple :

- `Validation interne requise`

et non plus :

- `validation_interne_requise`

---

## 3. Direction retenue pour les emails

### But

Avoir un rendu :

- plus propre
- plus pro
- plus GTI
- plus utile

sans revenir a un mail trop bavard.

### Intention retenue

Le mail doit rester une notification d'action :

- court
- hierarchise
- clair
- centré sur ce qu'il faut faire

### Contenu a garder

- dossier
- mandat
- bien
- ville
- motif ou statut
- commentaire si present
- action attendue
- bouton app

### Contenu a ne pas remettre pour l'instant

- lien Hektor
- trop de texte
- photo
- formules longues

---

## 4. Travail restant sur les emails

### A reprendre

Faire une nouvelle passe visuelle plus qualitative sur le template HTML :

- meilleure composition
- meilleure respiration
- plus premium
- plus coherent avec le style de l'app

Sans alourdir le contenu.

### Cible

Deux templates definitifs :

- notification refus
- notification acceptation

avec meme systeme visuel et meme langage.

---

## 5. Motifs de refus actuellement disponibles

- `Éléments manquants`
- `Mandat non valide`
- `Bien non diffusable`
- `Diagnostic de performance énergétique manquant`
- `Justificatif de propriété manquant`
- `Justificatif d'identité manquant`
- `Photos non conformes`
- `Texte d'annonce incomplet`
- `Barème d'honoraires non respecté`
- `Validation interne requise`
- `Correction de la fiche bien`
- `Autre`

---

## 6. Relances : sujet suivant

### Situation

Le systeme de demande possede deja des champs utiles :

- `follow_up_needed`
- `follow_up_at`
- `relaunch_count`

Il y a donc deja une base de suivi.

### Ce qui reste a definir

Il faut maintenant cadrer la logique metier :

1. dans quels cas on relance
2. qui relance
3. a quel moment
4. sous quelle forme
5. avec quel mail

### Direction recommandee

Commencer simple :

- relance manuelle ou semi-assistee
- pas d'automatisme cron tout de suite

Puis seulement si le besoin est clair :

- relance automatique

### Premier objectif concret

Creer une notification de relance courte avec :

- dossier
- motif de relance
- date prevue / echeance
- bouton pour rouvrir la demande dans l'app

---

## 7. Avant GitHub

Avant de publier / commit proprement, il restera a faire :

- purge des demandes de test si necessaire
- verification des mails
- verification des deep links
- revue visuelle finale
- eventuel nettoyage des notes

---

## 8. Fichiers a revoir a la reprise

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/vite.config.ts`
- `notice/NOTE_MAIL_HTML_DIFFUSION_2026-04-01.md`
- `notice/NOTE_MODULE_UTILISATEURS_2026-04-01.md`

---

## 9. Prochaine reprise recommandee

Ordre conseille :

1. finition visuelle du template email notification
2. cadrage du workflow de relance
3. implementation du mail de relance
4. tests de bout en bout
5. nettoyage avant GitHub
