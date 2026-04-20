# Note de reprise projet

Date : 09/04/2026

## Objet

Cette note sert de point de reprise simple apres interruption du projet.

Elle doit permettre de repondre rapidement a 4 questions :

1. ou en est le projet aujourd'hui
2. ce qui marche deja en local et en ligne
3. ce qui reste provisoire
4. dans quel ordre reprendre sans melanger plusieurs sujets

## Etat global du projet

Architecture actuelle :

- front React / Vite :
  - `apps/hektor-v1`
- base et auth :
  - `Supabase`
- backend prod :
  - `Render`
  - URL :
    - `https://gti-backend-xlyf.onrender.com`
- front prod :
  - `Vercel`
  - URL :
    - `https://groupe-gti.vercel.app`

Logique retenue :

- local = environnement de reference pour prouver les flux Hektor
- Render = backend prod qui reprend progressivement la logique locale
- Vercel = interface publique

## Ce qui est deja stable

### 1. Utilisateurs admin

Le flux `admin-users` est maintenant aligne entre l'app et Supabase.

Correctif important deja applique :

- `backend/app/services/supabase_admin.py`
- commit :
  - `8dcc7ac`
  - `Harden backend admin user profile creation`

Probleme corrige :

- un utilisateur pouvait etre cree dans `auth.users`
- sans ligne correspondante dans `public.app_user_profile`
- resultat :
  - connexion OK
  - mais aucun listing visible

Etat valide apres correctif :

- creation utilisateur depuis l'app OK
- `auth.users.id = app_user_profile.id`
- role admin bien reconnu

### 2. Backend Render

Le backend Render est en place et deja utilise par l'app.

Routes deja migrees :

- `admin-users`
- `hektor-diffusion`
- `notifications/diffusion-decision`

### 3. Emails de decision

Le flux email fonctionne maintenant via le backend Render avec Gmail API.

Point d'attention :

- l'identite d'envoi depend encore du compte / alias Google autorise
- selon la config, l'expediteur visible peut encore etre `frederic...`

### 4. Liens email vers l'app

Le deep-link des emails a ete corrige :

- une demande de baisse de prix ouvre maintenant la bonne demande
- une demande de validation ouvre la bonne demande

### 5. UI / colonnes / titres

Des changements UI ont ete prepares ou appliques selon les commits :

- simplification de certains titres et libelles
- reordonnancement des colonnes listing :
  - `Mandat`
  - `Bien`
  - `Negociateur`
  - `Statut`

Point de vigilance :

- certains changements peuvent encore n'exister qu'en local s'ils n'ont pas encore ete pushes au moment de la reprise

## Sujet principal encore ouvert

Le vrai sujet encore ouvert n'est plus :

- ni Supabase
- ni Render
- ni Vercel

Le vrai sujet encore ouvert est :

- le pilotage Hektor fiable de :
  - `validation`
  - puis `diffusable`
  - puis `passerelles`

## Ce qui a ete fait provisoirement

Jusqu'ici, en local, un contournement provisoire avait ete retenu :

- si `validation = non`
  - l'app n'essayait pas de piloter Hektor automatiquement
  - elle ouvrait Hektor
  - et demandait de cocher manuellement :
    - `validation`
    - `diffusable`
    - les passerelles

Ce provisoire existe parce qu'a ce moment :

- l'endpoint `Diffuse` etait teste avec une mauvaise methode
- et aucun endpoint clair n'etait encore retenu pour `PropertyValidation`

## Nouveau retour de Romain

Le retour le plus recent de Romain change le cadre.

Endpoints a retenir :

- validation / invalidation :
  - `PATCH /Api/Annonce/PropertyValidation/?idAnnonce=PROPERTY_ID&state=STATE&version=v2`
- pilotage `diffusable` :
  - `PATCH /Api/Annonce/Diffuse/?idAnnonce=PROPERTY_ID&version=v2`

Regles communiquees :

- `state=1`
  - validation
- `state=0`
  - invalidation
- `Diffuse` en `GET` etait faux
- l'erreur :
  - `Method Diffuse does not exist`
  etait coherente avec cette mauvaise methode

Conclusion :

- le provisoire local peut probablement etre remplace
- mais uniquement apres validation par test reel local

## Strategie retenue pour la reprise

Ne pas travailler plusieurs sujets Hektor en meme temps.

Ordre retenu :

### Etape 1

Traiter uniquement :

- `Validation : Oui / Non`

Dans l'app :

- ajouter ce controle dans la fiche detail annonce
- uniquement visible dans la vue :
  - `Suivi des mandats`
- seulement pour les profils admin / manager

Au debut :

- `Diffusion` reste visible en lecture seule
- pas encore de bouton `Diffusion : Oui / Non`

Pourquoi :

- `Validation` est le nouveau point confirme par Romain
- il faut d'abord prouver ce flux seul
- ne pas modifier validation et diffusion en edition en meme temps

### Etape 2

Recabler le flux local Python de reference.

Fichier principal :

- `phase2/sync/hektor_diffusion_writeback.py`

Corrections a faire :

- ajouter `PATCH PropertyValidation`
- remplacer l'ancien `GET Diffuse` par `PATCH Diffuse`
- relire `AnnonceById` apres chaque action
- relire `ListPasserelles` en fin de sequence

But :

- faire du local le chemin de preuve

### Etape 3

Brancher la fiche detail locale.

Fichiers cibles :

- `apps/hektor-v1/vite.config.ts`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/App.tsx`

Comportement vise :

- bouton `Validation : Oui`
- bouton `Validation : Non`
- appel API local
- relecture Hektor
- mise a jour visible immediate dans l'app

### Etape 4

Reprendre les deux flux metier locaux :

- `Demande de validation`
- `Console Diffusion`

Nouveau comportement cible :

- `Demande de validation`
  - tente validation API
  - relit l'annonce
  - tente `Diffuse` si necessaire
  - applique les passerelles
- `Console Diffusion`
  - meme logique
  - mais basee sur les cibles cochees

### Etape 5

Quand le local est prouve :

- reporter la meme logique dans :
  - `backend/app/services/hektor_bridge.py`

Alors seulement :

- Render recupere le nouveau chemin
- puis l'app en ligne Vercel devient coherente avec le local

## Pourquoi local d'abord

Le choix retenu est :

- local d'abord
- prod ensuite

Raison :

- le local est l'environnement de reference pour les tests Hektor reels
- Render contient deja plusieurs couches de migration
- si on change directement la prod sans preuve locale, on melange :
  - nouveau chemin Hektor
  - logique Render
  - comportement UI

Donc :

- local = preuve fonctionnelle
- Render = portage du chemin valide

## Fichiers de reprise principaux

### Front

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/vite.config.ts`

### Local Python

- `phase2/sync/hektor_diffusion_writeback.py`

### Backend Render

- `backend/app/services/hektor_bridge.py`

### Notes

- `notice/NOTE_REPRISE_DIFFUSION_API_2026-04-01.md`
- `notice/NOTE_REPRISE_VACANCES_PROJET_2026-04-09.md`
- `notice/romain retour avril .txt`

## Resume tres court pour reprise rapide

Au retour :

1. ne pas toucher tout de suite a Render
2. reprendre le nouveau mail de Romain
3. travailler d'abord `Validation : Oui / Non` dans la fiche detail `Suivi`
4. recabler et tester localement :
   - `PATCH PropertyValidation`
   - puis `PATCH Diffuse`
5. seulement ensuite reporter le meme chemin sur Render
6. puis aligner :
   - `Demande de validation`
   - `Console Diffusion`
   - app en ligne

## Etat mental de reprise

Le projet n'est pas bloque au sens architectural.

Le point restant est maintenant assez clair :

- prouver proprement le nouveau chemin Hektor donne par Romain

Le plus important a ne pas refaire :

- ne pas relancer plusieurs chantiers en meme temps
- ne pas modifier `Validation` et `Diffusion` en edition simultanee
- ne pas porter sur Render avant validation locale

## Reprise effective 20/04/2026 - premiere implementation locale Validation

Premiere etape lancee apres reprise :

- ajouter uniquement le pilotage `Validation : Oui / Non`
- dans la fiche detail annonce
- visible seulement :
  - en vue `Suivi des mandats`
  - pour admin / manager
  - sur environnement local `localhost`

Choix confirme :

- ne pas travailler `Validation` et `Diffusion` en edition en meme temps
- `Diffusion` reste affichee en lecture seule dans ce premier passage
- le controle direct `Passer cette annonce en diffusable` est desactive dans la fiche detail pour eviter deux chemins concurrents

Fichiers modifies :

- `phase2/sync/hektor_diffusion_writeback.py`
- `apps/hektor-v1/vite.config.ts`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/App.tsx`

Implementation locale ajoutee :

- nouvelle commande Python :
  - `set-validation`
- appel Hektor :
  - `PATCH /Api/Annonce/PropertyValidation/?idAnnonce=<id>&state=0|1&version=v2`
- relecture immediate :
  - `AnnonceById`
- payload retourne au front :
  - `observed_validation_before`
  - `observed_validation`
  - `observed_diffusable_before`
  - `observed_diffusable`
  - `response_payload`
  - `error`

Nouvelle route Vite locale :

- `POST /api/hektor-diffusion/set-validation`

Nouvelle fonction front :

- `setDossierValidationOnHektor(...)`

Verification faite :

- compilation Python :
  - OK
- TypeScript :
  - `tsc -b` OK
- build Vite complet :
  - bloque sur `spawn EPERM` dans l'environnement local
  - pas sur une erreur de code TypeScript

Prochaine etape :

- lancer l'app en local
- ouvrir une fiche detail depuis `Suivi des mandats`
- tester `Validation : Oui`
- tester ensuite `Validation : Non` sur un dossier de test seulement
- lire le payload retourne avant de modifier les flux `Demande de validation` et `Console Diffusion`

## Test reel 20/04/2026 - PropertyValidation sur dossier 5547

Cas teste :

- `app_dossier_id = 5547`
- `hektor_annonce_id = 24113`
- objectif :
  - passer `Validation = Oui`

Commande lancee :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py set-validation --app-dossier-id 5547 --state 1
```

Retour obtenu :

- HTTP :
  - `200`
- payload Hektor :
  - `{"code":0,"error":"Method PropertyValidation does not exist"}`

Diagnostic complementaire effectue :

- `PATCH /Api/Annonce/PropertyValidation/`
- `PATCH /Api/Annonce/PropertyValidation`
- `PATCH /Api/Annonce/propertyValidation/`
- variante avec `idAnnonce`
- variante avec `id`

Resultat :

- toutes les variantes retournent :
  - `Method PropertyValidation does not exist`

Conclusion du test :

- la methode `PATCH` est bien envoyee
- l'endpoint repond en JSON
- mais l'instance GTI ne reconnait pas encore la methode `PropertyValidation`
- ce n'est pas un probleme de slash final
- ce n'est pas un probleme simple `id` vs `idAnnonce`

Point a remonter a Romain :

- horodatage du test :
  - 20/04/2026
- annonce :
  - `idAnnonce = 24113`
- appel exact :
  - `PATCH /Api/Annonce/PropertyValidation/?idAnnonce=24113&state=1&version=v2`
- reponse :
  - `HTTP 200`
  - `{"code":0,"error":"Method PropertyValidation does not exist"}`

Etat de reprise :

- ne pas brancher les flux `Demande de validation` et `Console Diffusion` sur cet endpoint tant que Romain n'a pas confirme son activation effective sur l'instance GTI
- conserver le controle UI local comme outil de test, mais ne pas le porter sur Render

### Retest apres passage annonce en Actif

Le dossier `5547 / idAnnonce 24113` etait initialement dans un etat `Offre`.

Action manuelle faite dans Hektor :

- repasser l'annonce en `Actif`

Retest effectue ensuite avec le meme appel :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py set-validation --app-dossier-id 5547 --state 1
```

Retour obtenu :

- HTTP :
  - `200`
- payload :
  - `{"code":0,"error":"Method PropertyValidation does not exist"}`

Conclusion complementaire :

- le blocage ne vient pas du statut `Offre`
- meme en annonce `Actif`, l'instance GTI ne reconnait pas la methode `PropertyValidation`

## Decision provisoire 20/04/2026 - avancer sans `PropertyValidation`

Tests API directs effectues sur `idAnnonce = 24113` / `NO_DOSSIER = VA6482` :

- `PATCH /Api/Annonce/PropertyValidation/?idAnnonce=24113&state=1&version=v2`
  - retourne `{"code":0,"error":"Method PropertyValidation does not exist"}`
- meme retour sur `idAnnonce = 62055`
- `PATCH /Api/Annonce/Diffuse/?idAnnonce=24113&version=v2`
  - retourne `{"diffusable":"1","refresh":null}`
- relecture par `searchAnnonces` :
  - `diffusable = 1`
  - `valide = 0`
- `PUT /Api/Passerelle/addAnnonceToPasserelle/?idPasserelle=39&idAnnonce=24113`
  - retourne `{"code":200,"error":"Annonce ajoutee."}`
- `GET /Api/Annonce/ListPasserelles/?idAnnonce=24113&version=v2`
  - confirme `Le Bon Coin` actif avec `idPasserelle = 39`

Decision applicative provisoire :

- ne plus bloquer automatiquement la console `Diffusion` si `validation = non`
- tenter `Diffuse` puis appliquer les passerelles choisies
- garder l'etat `valide` tel que remonte par Hektor, sans le forcer artificiellement a `oui`
- attendre la reponse de Romain pour savoir comment piloter officiellement `valide = 1`

Correctifs faits :

- front :
  - retrait du blocage "Diffusion impossible : l'annonce n'est pas encore validee dans Hektor"
  - acceptation d'une demande de validation lance maintenant le flux `Diffuse + passerelles` meme si Hektor indique encore `validation = non`
- backend Render :
  - confirmation de `diffusable` par `searchAnnonces` si `AnnonceById` ne renvoie pas un JSON exploitable
  - appel `Diffuse` limite a la methode confirmee par Romain : `PATCH`
- script local :
  - meme fallback de confirmation via `searchAnnonces`

Point restant ouvert :

- le flux peut rendre diffusable et ajouter des portails, mais il ne sait toujours pas passer officiellement `valide = 1`
