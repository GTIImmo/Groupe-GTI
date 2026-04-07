# Note de reprise diffusion API

Date : 01/04/2026

## Objet

Documenter précisément :

- ce qui a été mis en place sur le flux `Demande de diffusion`
- ce qui a été validé localement
- ce qui bloque encore côté Hektor
- où reprendre après le retour de Romain

## Contexte métier retenu

Le workflow cible retenu est désormais :

1. Pauline accepte une demande de diffusion
2. cette action ne doit concerner qu'un seul dossier / une seule annonce
3. l'annonce doit être dans un état de validation compatible
4. seulement ensuite :
   - l'annonce peut devenir `diffusable`
   - les passerelles peuvent être activées

Règle métier clarifiée pendant les tests :

- une annonce non validée ne doit pas être considérée diffusable dans l'application
- une annonce non validée ne doit pas tenter l'écriture sur les passerelles
- l'acceptation Pauline peut rester possible côté métier, mais elle ne doit pas forcer artificiellement la diffusion

## Ce qui a été modifié

### 1. Front `hektor-v1`

Fichiers principaux touchés :

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/vite.config.ts`

Etat actuel du front :

- le popup `Demande de diffusion` peut accepter une demande
- si l'annonce n'est pas validée côté Hektor :
  - l'acceptation métier reste possible
  - l'app n'essaie plus de marquer le bien diffusable localement
  - l'app affiche un message de blocage explicite
- la console `Diffusion` bloque l'envoi passerelles si la validation Hektor n'est pas jugée compatible

Règle d'affichage `Suivi` clarifiée :

- si un bien est déjà `diffusable`, l'état diffusion doit rester prioritaire
- même s'il n'existe aucune demande de diffusion
- l'absence de demande ne doit afficher `Aucune demande` que si :
  - le bien n'est pas diffusable
  - et aucune demande n'existe

Messages actuellement branchés :

- après acceptation sans validation Hektor :
  - `Demande acceptee. Diffusion sur passerelles impossible pour l'instant : l'annonce n'est pas encore validee dans Hektor.`
- dans la console `Diffusion` :
  - `Diffusion impossible : l'annonce n'est pas encore validee dans Hektor.`

### 2. API locale de dev Vite

Un endpoint local existe pour piloter les scripts Python :

- `/api/hektor-diffusion/apply`
- `/api/hektor-diffusion/accept`

Le front appelle :

- `acceptDiffusionRequestOnHektor(...)`

pour le flux d'acceptation

### 3. Script Python write-back

Fichier principal :

- `phase2/sync/hektor_diffusion_writeback.py`

Principales évolutions apportées :

- ajout du root projet dans `sys.path`
- seed automatique des cibles si absentes
- seed par agence au lieu de prendre tout le catalogue writable
- création / alimentation automatique de la table locale :
  - `app_diffusion_agency_target`
- ajout d'une sous-commande :
  - `accept-request`
- ajout d'une sous-commande :
  - `test-single-target`
- élargissement des variantes de test sur :
  - `/Api/Annonce/Diffuse/`
  - `/Api/Passerelle/addAnnonceToPasserelle/`

### 4. Paramétrage par agence

Le seed par défaut repose maintenant sur l'agence du dossier, lue depuis :

- `app_view_generale.agence_nom`

Le mapping est stocké dans :

- `app_diffusion_agency_target`

Exemple documenté et validé pour le dossier test :

- agence : `Groupe GTI Craponne-sur-Arzon`
- `bienicidirect -> 5`
- `leboncoinDirect -> 42`

## Dossier test principal utilisé

Pendant les essais, le dossier de référence a été :

- `app_dossier_id = 20124`
- `hektor_annonce_id = 61909`
- `numero_dossier = V770061909`
- `numero_mandat = 18494`
- agence : `Groupe GTI Craponne-sur-Arzon`

Autre dossier ayant servi sur l'app :

- `app_dossier_id = 869`
- `hektor_annonce_id = 12224`

## Ce qui a été vérifié dans la data locale

### 1. Détail annonce disponible

Pour `20124 / 61909`, le détail est bien présent :

- localement dans `phase2.sqlite`
- côté Supabase dans `app_dossier_details_current`

Conclusion :

- les problèmes de popup détail rencontrés à un moment ne venaient pas d'une absence de donnée

### 2. Corrélation diffusable / passerelles actives

Contrôle fait sur `app_view_generale` :

- `417` biens ont des passerelles actives
- parmi eux :
  - `417` ont `diffusable = '1'`
  - `0` ont `diffusable != '1'`

Conclusion :

- dans la donnée actuelle, une annonce avec passerelles actives est toujours `diffusable`

### 3. Corrélation validation / diffusion

Sur les annonces avec passerelles actives observées :

- `diffusable = 1`
- `valide = 1`
- `detail_statut_name = Actif`

Pour le dossier test `61909` avant validation :

- `diffusable = 0`
- `valide = 0`
- `detail_statut_name = Actif`
- `0` portail actif

Conclusion de travail :

- la validation semble être une précondition avant diffusion

## Ce qui a été prouvé sur l'API Hektor

### 1. Lecture : OK

Les lectures utilisées fonctionnent :

- `/Api/Annonce/AnnonceById/`
- `/Api/Annonce/ListPasserelles/`

La lecture des portails actifs et du détail annonce est donc exploitable.

### 2. `Diffuse` : partiellement validé

Des essais ont été faits autour de :

- `/Api/Annonce/Diffuse/`

Variantes testées :

- `GET` avec `idAnnonce`
- `POST` avec `idAnnonce`
- `GET` avec `id`
- `POST` avec `id`

Constat intermédiaire :

- sur une annonce non validée, l'appel pouvait renvoyer `500`
- après validation manuelle de l'annonce, le script a fini par remonter :
  - `diffusable_result = already_diffusable`

Conclusion de travail :

- le champ `diffusable` peut être piloté ou au moins relu correctement une fois l'annonce dans le bon état métier
- le vrai point métier en amont semble être la validation

### 3. Ecriture passerelles : échec confirmé

Le point bloquant actuel est :

- `/Api/Passerelle/addAnnonceToPasserelle/`

Pour `idAnnonce = 61909`, plusieurs passerelles valides ont été testées :

- `idPasserelle = 5` (`bienicidirect`)
- `idPasserelle = 42` (`leboncoinDirect`)
- `idPasserelle = 21` (`superimmo`)

Les IDs sont cohérents :

- ils existent dans `hektor_broadcast_portal`
- ils sont déjà observés sur d'autres annonces exportées

Variantes testées sur la route `addAnnonceToPasserelle` :

- `GET` query
- `POST` query
- `POST` form-data
- avec `idAnnonce`
- avec `id`
- avec `version=v2`
- sans version
- avec `version=v1`
- avec `version=v0`

Résultat :

- toutes les variantes testées répondent `405 Method Not Allowed`

Conclusion forte :

- le problème n'est pas l'ID annonce
- le problème n'est pas l'ID passerelle
- le problème n'est pas le paramètre `version`
- le problème n'est pas la forme simple du payload
- sur l'instance testée, l'endpoint d'écriture passerelle n'est pas utilisable tel quel malgré la note/doc fournie

## Retour Romain du 03/04/2026

Romain a répondu point par point sur les 3 sujets encore ouverts.

### 1. Ecriture passerelles : cause réelle du `405`

Le `405 Method Not Allowed` ne vient pas du payload mais de la méthode HTTP utilisée.

Règle confirmée :

- `addAnnonceToPasserelle` :
  - route : `/Api/Passerelle/addAnnonceToPasserelle/`
  - méthode : `PUT`
- `removeAnnonceToPasserelle` :
  - route : `/Api/Passerelle/removeAnnonceToPasserelle/`
  - méthode : `DELETE`

Paramètres attendus :

- `idPasserelle`
- `idAnnonce`

Précisions confirmées :

- le paramètre `version` n'est pas pris en compte par ces routes
- authentification possible via JWT ou OAuth
- prérequis technique :
  - annonce `diffusable = 1`
  - annonce non archivée

Conclusion mise à jour :

- notre campagne précédente de tests était fondée sur une indication erronée en `GET`
- il faut reprendre les essais writeback avec :
  - `PUT addAnnonceToPasserelle`
  - `DELETE removeAnnonceToPasserelle`

### 2. Validation métier avant diffusion

Réponse produit confirmée :

- il n'existe pas aujourd'hui d'endpoint REST dédié pour valider / invalider une annonce au sens métier `validation mandat`
- les endpoints passerelles ne contrôlent pas cette notion métier
- ils contrôlent uniquement :
  - `diffusable = 1`
  - annonce non archivée

Conséquence projet :

- la validation métier reste une notion distincte de la diffusion technique
- elle ne peut pas être pilotée aujourd'hui par un endpoint REST Hektor dédié
- notre logique applicative doit donc continuer à distinguer :
  - validation métier
  - diffusion technique

### 3. IDs négociateurs absents de `listNegos`

Romain confirme que c'est un comportement attendu :

- `listNegos` ne retourne que les négociateurs actifs et non expirés

Donc :

- des IDs comme `23` et `93` peuvent rester référencés sur des annonces
- tout en étant absents de `listNegos`

Contournement confirmé :

- utiliser `GET /Api/Negociateur/getNegoById?id=<id>`

Règle fiable retenue :

- pour le rattachement annonce -> négociateur, la référence fiable reste le champ `negociateur` sur la donnée annonce
- `listNegos` ne doit pas être considérée comme le référentiel exhaustif historique

## Impact de ce retour

Le statut projet sur les 3 blocages devient :

1. `405` endpoints passerelle
- cause identifiée
- reprise à faire avec les bonnes méthodes `PUT` / `DELETE`

2. validation mandat
- pas d'endpoint REST Hektor dédié aujourd'hui
- le workflow applicatif doit rester séparé de la diffusion technique

3. IDs négociateurs manquants
- comportement API confirmé comme normal
- repli à faire via `getNegoById`

## Reprise projet - séparation des 2 sujets

Pour la suite du projet, il faut désormais distinguer strictement deux points techniques.

### 1. Pilotage de `diffusable`

Endpoint historiquement communiqué par Romain en mars :

- `GET /Api/Annonce/Diffuse/?idAnnonce={{idAnnonce}}&version={{version}}`

Constat local le plus récent sur le cas test :

- `idAnnonce = 61909`
- appel brut exécuté avec :
  - authentification OAuth
  - JWT SSO
  - `GET /Api/Annonce/Diffuse/?idAnnonce=61909&version=v2`
- retour obtenu :
  - `status_code = 500`
  - body :
    - `{"data":null,"metadata":null,"refresh":null,"error":"Method Diffuse does not exist"}`

Conclusion de reprise :

- le pilotage de `diffusable` n'est pas considéré comme fiabilisé
- l'endpoint communiqué en mars ne fonctionne pas proprement sur l'instance testée
- le sujet doit être repris avec Romain comme blocage API distinct

Question ouverte à conserver :

- comment piloter de façon fiable `diffusable` par API sur l'instance GTI ?

### 2. Endpoints passerelle

Ce point est désormais validé par test réel.

Cas testé :

- `idAnnonce = 61909`
- `idPasserelle = 5` (`bienicidirect`)
- `idPasserelle = 42` (`leboncoinDirect`)

Méthode utilisée :

- `PUT /Api/Passerelle/addAnnonceToPasserelle/`
- paramètres :
  - `idPasserelle`
  - `idAnnonce`

Résultats observés :

- passerelle `5` :
  - `status_code = 200`
  - `{"res":"Listing published.","refresh":null}`
- passerelle `42` :
  - `status_code = 200`
  - `{"res":"Listing published.","refresh":null}`

Conclusion de reprise :

- l'écriture passerelle fonctionne
- les endpoints `PUT` / `DELETE` donnés par Romain en avril sont corrects
- le blocage projet ne porte plus sur les portails
- le blocage résiduel porte uniquement sur le pilotage fiable de `diffusable`

## Reprise acceptation demande de validation

Suite au retour de Romain, la reprise du flux d'acceptation doit désormais suivre cette séquence :

1. accepter la `Demande de validation`
2. recharger d'abord les cibles agence depuis `app_diffusion_agency_target`
3. rendre l'annonce `diffusable = 1` via le flux Hektor déjà branché
4. ajouter les passerelles agence avec :
   - `PUT /Api/Passerelle/addAnnonceToPasserelle/`
   - paramètres :
     - `idPasserelle`
     - `idAnnonce`

Le script `phase2/sync/hektor_diffusion_writeback.py` a été recadré dans ce sens :

- l'acceptation recharge systématiquement le jeu de cibles par défaut de l'agence
- ajout passerelle :
  - `PUT`
- retrait passerelle :
  - `DELETE`
- plus de tentative `GET` / `POST`
- plus de paramètre `version` sur ces routes

Le flux métier côté app reste inchangé :

- la demande de validation acceptée doit faire apparaître `Diffusion`
- les KPI et filtres existants restent inchangés

## Commandes de test utilisées

### Compilation

```powershell
npx.cmd tsc -b
```

```powershell
.\.venv\Scripts\python.exe -m py_compile phase2\sync\hektor_diffusion_writeback.py
```

### Seed agence

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py seed-default-targets --app-dossier-id 20124
```

### Dry-run acceptation

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py accept-request --app-dossier-id 20124 --dry-run
```

Résultat attendu et obtenu :

- `diffusable_changed = true`
- `targets_count = 2`
- `to_add_count = 2`
- `bienicidirect = 5`
- `leboncoinDirect = 42`

### Test réel acceptation

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py accept-request --app-dossier-id 20124
```

Constat final après validation manuelle :

- `diffusable_result = already_diffusable`
- ensuite échec sur les passerelles

### Test ciblé une seule passerelle

Commande dédiée ajoutée :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py test-single-target --app-dossier-id 20124 --broadcast-id 21 --portal-key superimmo
```

Constat :

- même en testant uniquement `superimmo`
- l'écriture passe toujours par `405 Method Not Allowed`

## Etat actuel exact du projet

### Ce qui est considéré comme stable

- lecture Hektor
- seed agence
- ciblage d'un seul dossier
- mapping agence -> passerelles
- blocage UX si validation Hektor absente
- acceptation métier sans forçage de diffusion

### Ce qui reste ouvert

1. comprendre comment modifier l'état de validation côté Hektor
2. comprendre pourquoi `addAnnonceToPasserelle` renvoie `405` sur toutes les variantes
3. confirmer si l'écriture passerelle exige :
   - un autre type de JWT
   - une autre route
   - une autre version d'API
   - un prérequis métier ou technique non documenté

## Ce qu'il faut demander / confirmer avec Romain

### Sujet 1

Comment modifier par API le champ de validation de l'annonce, puisque cette validation semble être obligatoire avant diffusion.

### Sujet 2

Pourquoi l'écriture sur les passerelles échoue en `405` alors que :

- l'ID annonce est bon
- l'ID passerelle est bon
- la doc fournie indique explicitement :
  - `GET /Api/Passerelle/addAnnonceToPasserelle/`
  - `idPasserelle`, `idAnnonce`, `version`

### Informations factuelles utiles à lui transmettre

Exemple testé :

- `idAnnonce = 61909`
- `idPasserelle = 5`
- `idPasserelle = 42`
- `idPasserelle = 21`

Résultat :

- `405 Method Not Allowed` sur toutes les variantes testées

## Reprise après retour de Romain

Quand on aura sa réponse, reprendre dans cet ordre :

1. intégrer sa réponse sur la validation
2. intégrer sa réponse sur l'écriture passerelle
3. retester localement sur :
   - `app_dossier_id = 20124`
   - `hektor_annonce_id = 61909`
4. si le write-back passe :
   - rebrancher le flux complet d'acceptation jusqu'aux passerelles
5. ajuster ensuite seulement les messages UX finaux

## Point de vigilance

Ne plus faire d'hypothèse forte sur `addAnnonceToPasserelle` sans nouvelle information.

Les tests menés sont suffisamment larges pour considérer que :

- le blocage n'est plus un simple bug local
- il manque une information serveur / API / auth côté Hektor

## Mise a jour 03/04/2026 - acceptation Pauline

Les tests suivants ont ensuite ete confirmes :

- `PUT /Api/Passerelle/addAnnonceToPasserelle/` fonctionne bien
- `GET /Api/Negociateur/getNegoById?id=<id>` fonctionne bien
- le point encore fragile reste le passage ou la reactivation de `diffusable`

La regle metier retenue est maintenant plus simple :

1. Pauline accepte une `Demande de validation`
2. si l'annonce est encore en `validation = non` :
   - aucun appel API Hektor n'est lance
   - l'app affiche un message clair
   - la fiche Hektor de l'annonce s'ouvre automatiquement dans une fenetre reduite
   - consigne affichee :
     - cocher manuellement `validation`
     - cocher manuellement `diffusable`
     - cocher manuellement les passerelles
3. si l'annonce est deja en `validation = oui` :
   - l'app n'essaie pas non plus d'activer automatiquement les passerelles
   - la demande est acceptee
   - la console `Diffusion` devient ensuite le point d'entree normal pour gerer les passerelles

Consequence UX :

- l'acceptation Pauline ne declenche plus de writeback Hektor automatique
- la console `Diffusion` reste l'outil de gestion passerelles une fois le bien valide
- l'app ne doit pas basculer visuellement en `Diffusion` uniquement parce que la demande est `accepted`
- le passage a `Diffusion` doit dependre de la validation effective du bien

Fichiers recables :

- `apps/hektor-v1/src/App.tsx`

## Mise a jour 04/04/2026 - refresh automatique apres acceptation

Le projet embarque maintenant un refresh cible apres `accept-request` :

- endpoint local Vite :
  - `/api/hektor-diffusion/accept`
- sequence automatique :
  1. execution de `phase2/sync/hektor_diffusion_writeback.py accept-request`
  2. si un `hektor_annonce_id` est retourne et si on n'est pas en `dry-run`
  3. execution automatique de `phase2/sync/refresh_single_annonce.py --id-annonce <id>`

But :

- relire Hektor juste apres l'acceptation
- remettre a jour localement :
  - `diffusable`
  - detail annonce
  - relation mandats annonce
  - etat passerelles actives

Fichiers concernes :

- `apps/hektor-v1/vite.config.ts`
- `phase2/sync/refresh_single_annonce.py`

Commande manuelle equivalente si besoin :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py accept-request --app-dossier-id <app_dossier_id>
.\.venv\Scripts\python.exe phase2\sync\refresh_single_annonce.py --id-annonce <hektor_annonce_id>
```

## Mise a jour 04/04/2026 - console Diffusion

La regle UI/metier retenue est maintenant la suivante :

- si `validation = oui`, la `Demande de validation` n'est plus proposee
- l'entree normale devient la console `Diffusion`
- depuis cette console, le bouton principal doit :
  - tenter `diffusable = 1`
  - puis appliquer les passerelles cochees
  - puis relire Hektor via le refresh cible

Implementation :

- `apply-targets` accepte maintenant `--ensure-diffusable`
- l'API locale Vite transmet `ensureDiffusable`
- la console `Diffusion` appelle ce mode pour faire :
  - diffusion globale
  - puis activation / desactivation des passerelles

Fichiers concernes :

- `phase2/sync/hektor_diffusion_writeback.py`
- `apps/hektor-v1/vite.config.ts`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/App.tsx`

Test valide du 04/04/2026 :

- dossier test :
  - `app_dossier_id = 5547`
  - `hektor_annonce_id = 24113`
  - agence : `Groupe GTI Firminy`
- mapping agence confirme :
  - `bienicidirect -> 15`
  - `leboncoinDirect -> 39`
- la console `Diffusion` charge bien ces cibles
- execution manuelle validee :
  - `Ajouts vises : 2`
  - `Retraits vises : 0`
  - `Actions reussies : 2`
  - `Actions en erreur : 0`

Conclusion :

- le flux console `validation = oui -> diffusable + passerelles` fonctionne
- le mapping agence -> `idPasserelle` est correctement applique sur ce dossier test

## Mise a jour 04/04/2026 - ajout / retrait passerelles depuis la console

Cas concret documente sur le dossier test :

- `app_dossier_id = 5547`
- `hektor_annonce_id = 24113`
- agence : `Groupe GTI Firminy`
- mapping :
  - `bienicidirect -> 15`
  - `leboncoinDirect -> 39`

Constats et correctifs importants :

1. Ouverture de la console
- l'ouverture ne doit plus rien ecrire
- si aucune cible dossier n'existe, la console ne fait plus de `seed` automatique persistant
- elle ne fait qu'un `preview` des passerelles agence

2. Source locale hors Supabase
- hors Supabase, la console ne doit plus se reposer sur les mocks ou sur `localStorage` seul
- les cibles doivent etre lues via l'endpoint local :
  - `/api/hektor-diffusion/targets`
- les broadcasts doivent etre lus via :
  - `/api/hektor-diffusion/broadcasts`

3. Persistance des coches
- si Supabase est configure mais que la table `app_diffusion_target` n'existe pas, le fallback doit passer par l'API locale du projet
- il ne faut plus tomber sur un faux fallback navigateur qui donne l'illusion d'une sauvegarde reussie

4. Retrait des passerelles
- le calcul initial des retraits etait trop strict :
  - il dependait d'une lecture live des passerelles actives
  - si cette lecture revenait vide, aucun `DELETE` ne partait
- regle finale retenue :
  - `enabled` => `PUT addAnnonceToPasserelle`
  - `disabled` => `DELETE removeAnnonceToPasserelle`
- autrement dit, une passerelle decochée doit toujours partir en `DELETE`, sans dependre d'un etat live prealable

Conclusion retenue :

- ajout : OK
- retrait : OK apres correction
- ouverture console : lecture seule
- application console : ecriture explicite uniquement

## Mise a jour 06/04/2026 - regle finale console Diffusion et limite sur `diffusable = non`

Synthese fonctionnelle a retenir pour reprendre le projet :

1. Entrees metier
- si `validation = non`
  - ne pas lancer d'appel API automatique
  - afficher un message a Pauline :
    - il faut cocher manuellement `validation`
    - puis `diffusable`
    - puis les passerelles dans Hektor
  - ouvrir le lien Hektor de l'annonce
- si `validation = oui`
  - l'entree normale devient la console `Diffusion`
  - l'utilisateur choisit les passerelles
  - puis clique sur le bouton d'application

2. Regle de la console
- a l'ouverture :
  - lecture seule
  - lecture des cibles dossier si elles existent
  - sinon `preview` simple du mapping agence
  - aucune ecriture automatique
- au clic sur le bouton :
  1. sauvegarder exactement les coches visibles
  2. verifier que la sauvegarde reelle correspond a la selection
  3. si `validation = oui`, tenter `diffusable = 1`
  4. appliquer les passerelles
  5. relire Hektor via le refresh cible

3. Formule finale appliquee sur les passerelles
- `enabled` => `PUT /Api/Passerelle/addAnnonceToPasserelle/`
- `disabled` => `DELETE /Api/Passerelle/removeAnnonceToPasserelle/`
- le retrait ne doit plus dependre d'une lecture live prealable
- une passerelle decochee part directement en `DELETE`

4. Cas test de reference
- dossier :
  - `app_dossier_id = 5547`
  - `hektor_annonce_id = 24113`
- agence :
  - `Groupe GTI Firminy`
- mapping :
  - `bienicidirect -> 15`
  - `leboncoinDirect -> 39`
- ajout valide :
  - `diffusable = 1`
  - ajout passerelle OK
- retrait valide apres correction :
  - decochage console
  - `DELETE` correctement envoye

5. Limite actuelle sur `diffusable = non`
- a ce jour, on n'a pas de methode API Hektor fiable prouvee pour remettre une annonce en `non diffusable`
- route testee, conformement aux mails :
  - `GET /Api/Annonce/Diffuse/?idAnnonce=<id>&version=v2`
- test direct sur `24113` :
  - avant : `diffusable = 1`
  - appel : `GET /Api/Annonce/Diffuse/?idAnnonce=24113&version=v2`
  - retour : `500`
  - body : `{"error":"Method Diffuse does not exist"}`
  - apres : `diffusable = 1`

Conclusion actuelle :

- `diffusable = 1` :
  - flux empirique encore exploitable via tentative + relecture
- `diffusable = 0` :
  - aucune route fiable prouvee a ce stade
- donc la console peut piloter les passerelles
- mais il ne faut pas encore promettre un vrai bouton `diffusable = non` tant que Hektor n'a pas fourni la bonne methode

## Mise a jour 06/04/2026 - tentative de refactor lecture demandes puis retour arriere

Une tentative de centralisation de la lecture metier des demandes a ete faite le 06/04/2026 :

- helper central front pour interpreter `request_status`
- alignement des KPI et filtres sur cette lecture

Constat :

- le gain fonctionnel n'etait pas assez visible
- la logique d'origine etait plus lisible pour reprendre rapidement le projet

Decision retenue :

- retour arriere complet vers la logique precedente
- les ecrans continuent donc a s'appuyer directement sur `request_status`
- aucun changement conserve sur les appels API
- aucun changement conserve sur les payloads
- aucun changement de schema

Lecture retenue a ce stade :

- `pending` et `in_progress`
  - comptes ensemble dans certains KPI
- `waiting_commercial` et `refused`
  - restent regroupes dans certaines vues de correction
- les conditions restent exprimees directement dans le front, comme avant

Conclusion :

- le projet reste sur la logique d'origine pour les demandes
- si une refonte est retentee plus tard, il faudra qu'elle produise un vrai gain visible avant d'etre gardee

## Mise a jour 06/04/2026 - alignement baisse de prix refusee sur diffusion

Regle metier retenue :

- une demande de `baisse de prix` refusee doit se comporter comme une demande de diffusion refusee
- cote Pauline :
  - elle reste visible comme `Rejetee`
- cote listing mandats / negociateur :
  - elle doit repasser en `A corriger`
- cote KPI correction :
  - elle doit continuer a entrer dans `Correction en attente`

Correctif retenu :

- la fonction `latestActionRequest(...)` doit aussi retenir les demandes `refused` pour `demande_baisse_prix`
- avant correction, les demandes de baisse de prix refusees pouvaient sortir de la logique d'action
- apres correction, elles sont de nouveau reprises dans la meme famille de traitement que la diffusion

Fichier concerne :

- `apps/hektor-v1/src/App.tsx`

Rollback si besoin :

- remettre `latestActionRequest(...)` sur l'ancienne logique :
  - diffusion : `pending|in_progress|waiting_commercial|refused`
  - baisse de prix : `pending|in_progress|waiting_commercial` uniquement

La version retenue est bien celle qui inclut aussi `refused` pour la baisse de prix.

## Mise a jour 06/04/2026 - KPI demandes basees sur la derniere demande par dossier et par type

Cas metier observe :

- une demande de baisse de prix est `acceptee`
- ensuite le commercial cree une nouvelle demande de baisse de prix sur le meme dossier
- dans ce cas :
  - le KPI `Demandes acceptees` ne doit plus continuer a compter l'ancienne demande
  - le listing doit suivre uniquement la nouvelle etape

Cause :

- les KPI comptaient toutes les demandes historiques
- alors que les listings travaillent sur la derniere demande par dossier et par type

Regle retenue :

- pour les KPI demandes et les statistiques de suivi :
  - ne compter que la derniere demande
  - par `app_dossier_id`
  - et par `request_type`

Effet attendu :

- une ancienne `baisse de prix acceptee` est remplacee dans les KPI des qu'une nouvelle demande de baisse de prix est creee sur le meme dossier
- KPI et listing racontent alors la meme chose

Fichier concerne :

- `apps/hektor-v1/src/lib/api.ts`

Rollback si besoin :

- revenir au comptage historique brut de toutes les lignes de `app_diffusion_requests_current`
- la version retenue est celle basee sur la derniere demande par dossier et par type

## Mise a jour 06/04/2026 - ajout d'un acces historique aux demandes acceptees

Besoin metier :

- garder des KPI courants bases sur la derniere demande
- mais pouvoir retrouver aussi les annonces qui ont deja eu une demande acceptee

Regle retenue :

- `Demandes acceptees`
  - KPI courant
  - base sur la derniere demande par dossier et par type
- `Annonces validees`
  - KPI historique
  - base sur l'existence d'au moins une demande `accepted`
  - par dossier et par type

Effet :

- si une ancienne baisse de prix acceptee a ete remplacee par une nouvelle demande
  - elle sort du KPI courant `Demandes acceptees`
  - mais reste retrouvable via le KPI historique `Annonces validees`

Fichiers concernes :

- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/App.tsx`

Rollback :

- retirer `acceptedHistorical` des stats
- retirer l'action `suivi_acceptees_historique`
- revenir a un seul KPI `Demandes acceptees`

## Mise a jour 06/04/2026 - simplification KPI suivi et popup Actions

Decision UX retenue :

- le KPI courant `Demandes acceptees` devient inutile pour l'usage metier
- il est remplace par le KPI historique base sur `acceptedHistorical`
- le libelle final conserve est :
  - `Demandes acceptees`

Donc :

- il n'y a plus deux KPI differents pour l'accepte
- le bouton `Demandes acceptees` ouvre maintenant la vue historique utile

Popup `Actions` :

- suppression du texte :
  - `Les actions respectent les regles actuelles du bien...`
- suppression de la ligne :
  - `Annonce <id>`
- ajout d'une action simple :
  - `Ouvrir Hektor`

But :

- popup plus court
- lecture plus directe
- acces Hektor immediat sans bouton secondaire ailleurs

Fichier concerne :

- `apps/hektor-v1/src/App.tsx`

Rollback :

- remettre le KPI courant `accepted`
- retirer l'action `Ouvrir Hektor`
- remettre l'entete descriptive du popup si besoin

## Mise a jour 07/04/2026 - console Diffusion sur Vercel / Supabase

Cas constate en production sur `https://groupe-gti.vercel.app/` :

- si une annonce n'a encore aucune ligne dans `app_diffusion_target`
- la console `Diffusion` pouvait afficher :
  - `Aucune passerelle n'est configuree pour ce mandat. Le mapping agence n'a pas ete trouve.`
- alors meme que le mapping agence existe dans les scripts locaux

Cause retenue :

- en local, la console pouvait faire un `preview` via les routes Vite :
  - `/api/hektor-diffusion/preview-targets`
- en production Vercel, cette route locale n'existe pas
- de plus, la table `app_diffusion_agency_target` n'est pas garantie dans le schema Supabase actuel

Correctif retenu :

- `apps/hektor-v1/src/lib/api.ts`
- la fonction `previewDefaultDiffusionTargets(...)` suit maintenant cette logique :
  1. si Supabase est disponible, charger le dossier depuis `app_dossiers_current`
  2. tenter de lire `app_diffusion_agency_target` si la table existe
  3. sinon retomber sur le mapping agence integre, aligne sur `phase2/sync/hektor_diffusion_writeback.py`
  4. retourner des cibles par defaut en `disabled`
- la fonction `loadDiffusionTargets(...)` n'essaie plus de tomber sur les routes Vite de dev en production quand `app_diffusion_target` manque
- la fonction `saveDiffusionTargets(...)` garde aussi un fallback navigateur propre si la table n'existe pas, au lieu d'exiger les endpoints locaux

Principe conserve :

- local / dev :
  - les routes Vite de dev restent utilisables
- production / Vercel :
  - la console doit privilegier Supabase
  - et ne plus dependre des routes Python locales pour simplement afficher les passerelles

But :

- retrouver les cases a cocher en console meme quand rien n'est encore actif
- rester coherent avec le mapping agence deja porte par les scripts locaux

## Mise a jour 07/04/2026 - limite Vercel actuelle et piste cible Supabase Functions

Constat de production sur `https://groupe-gti.vercel.app/` :

- la sauvegarde simple des cibles diffusion peut vivre cote Supabase
- mais le bouton :
  - `Activer la diffusion et appliquer`
  depend encore du flux local historique
- ce flux appelle aujourd'hui des routes de dev :
  - `/api/hektor-diffusion/apply`
  - `/api/hektor-diffusion/accept`
- ces routes sont alimentees localement par :
  - `apps/hektor-v1/vite.config.ts`
  - `phase2/sync/hektor_diffusion_writeback.py`

Conclusion technique :

- GitHub heberge le code
- Vercel heberge le front
- Supabase heberge la data
- mais l'automatisation Hektor reelle vit encore seulement sur le poste local

Effet concret en prod :

- un clic sur `Activer la diffusion et appliquer` ne peut pas executer le writeback Hektor complet
- sans backend serveur, Vercel ne sait ni lancer les scripts Python locaux ni exposer les routes Vite de dev

Decision de reprise retenue :

- garder en prod :
  - lecture / ecriture des cibles diffusion via Supabase
- ne plus considerer les routes Vite locales comme solution prod
- cible architecture a moyen terme :
  - remplacer le writeback Hektor local par une vraie fonction serveur
  - piste privilegiee : `Supabase Edge Functions`

Pourquoi cette piste est retenue :

- l'app est deja branchee a Supabase
- les secrets Hektor pourront rester cote serveur
- Vercel pourra appeler une fonction prod stable
- cela evitera de dependre du poste local pour :
  - `diffusable`
  - `PUT/DELETE` passerelles
  - relecture de retour Hektor

Ordre de reprise recommande :

1. stabiliser la lecture / sauvegarde des targets en prod
2. figer le contrat attendu pour :
   - `apply`
   - `accept`
3. porter ensuite la logique utile de `hektor_diffusion_writeback.py` vers une `Supabase Edge Function`

## Mise a jour 07/04/2026 - premier branchement `Supabase Edge Function`

Implementation posee :

- nouvelle fonction :
  - `supabase/functions/hektor-diffusion/index.ts`
- le front prod appelle maintenant cette fonction pour :
  - `apply`
  - `accept`
- en local, le projet garde les routes Vite de dev existantes

Principe retenu :

- prod :
  - `apps/hektor-v1/src/lib/api.ts`
  - `applyDiffusionTargetsOnHektor(...)`
    - `supabase.functions.invoke('hektor-diffusion', { action: 'apply', ... })`
  - `acceptDiffusionRequestOnHektor(...)`
    - `supabase.functions.invoke('hektor-diffusion', { action: 'accept', ... })`
- local :
  - conservation des routes :
    - `/api/hektor-diffusion/apply`
    - `/api/hektor-diffusion/accept`

Ce que fait deja la fonction :

- charge le dossier depuis `app_dossiers_current`
- lit les cibles depuis `app_diffusion_target`
- si `accept` ou si aucune cible existe :
  - recharge les passerelles par defaut depuis `app_diffusion_agency_target`
- tente `diffusable`
- applique les `PUT/DELETE` de passerelles
- renvoie un payload compatible avec le front actuel

Variables d'environnement a prevoir cote Supabase Function :

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `HEKTOR_API_BASE_URL`
- `HEKTOR_CLIENT_ID`
- `HEKTOR_CLIENT_SECRET`
- `HEKTOR_API_VERSION`

Point de vigilance :

- cette premiere version remplace l'appel prod aux routes Vite locales
- elle doit encore etre deployee cote Supabase Functions
- l'auth Hektor retenue doit rester alignee avec `hektor_pipeline.common` :
  - OAuth `Authenticate`
  - puis `Sso`
  - puis header `jwt`

## Mise a jour 07/04/2026 - migration admin utilisateurs vers Supabase Function

Constat :

- les fonctions d'administration utilisateurs restaient branchees sur les routes locales Vite :
  - `/api/admin/users/create`
  - `/api/admin/users/list`
  - `/api/admin/users/update`
  - `/api/admin/users/send-reset`
- en production Vercel, ces routes n'existent pas

Correctif retenu :

- nouvelle function :
  - `supabase/functions/admin-users/index.ts`
- le front prod appelle maintenant cette function pour :
  - creer un utilisateur
  - lister les utilisateurs
  - modifier un utilisateur
  - envoyer un reset password
- le mode local conserve les endpoints Vite existants

Regle d'acces retenue :

- seul un profil `admin` ou `manager` actif peut utiliser cette function
- le controle se fait en lisant `app_user_profile`

Variables attendues cote function :

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `APP_BASE_URL` pour le lien de reset si besoin

Etat de debug atteint apres premier branchement :

- le front prod n'appelle plus la route locale Vite
- la function Supabase `hektor-diffusion` est bien invoquee
- le message remonte maintenant :
  - `Edge Function returned a non-2xx status code`

Conclusion :

- le crash est maintenant bien dans la function serveur ou dans la reponse Hektor
- plus dans Vercel ni dans les anciennes routes locales

Correction retenue ensuite :

- la function Supabase doit reprendre la logique locale sur `Diffuse`
- en pratique :
  - un retour HTTP `500` ou un message d'erreur Hektor ne doit pas suffire a conclure a un echec
  - il faut relire ensuite `AnnonceById`
  - si `diffusable = 1`, alors l'action est consideree comme reussie malgre l'erreur HTTP

But :

- rester aligne avec le comportement deja observe localement
- eviter les faux echecs quand Hektor agit mais repond mal

Extension retenue ensuite :

- la tolerance ne doit pas concerner seulement `Diffuse`
- plus generalement, la function ne doit plus remonter un echec bloquant si :
  - Hektor a probablement execute l'action
  - mais la confirmation technique est sale ou incomplete
- dans ce cas :
  - retour `waiting_on_hektor = true`
  - message explicite
  - pas de `500` brutal cote app

## Mise a jour 07/04/2026 - cible backend Python dedie

Apres comparaison complete entre le mode local Vite et la prod Vercel/Supabase, la cible retenue pour la suite n'est plus de pousser toute la logique serveur dans des `Supabase Edge Functions`.

Constat :

- le projet local sous Vite expose aujourd'hui trois familles de routes serveur :
  - diffusion Hektor
  - administration utilisateurs
  - notifications email
- toutes les routes locales ne doivent pas devenir un backend public complet
- les vraies actions metier sensibles sont seulement :
  - administration utilisateurs
  - application Hektor depuis la console `Diffusion`
  - acceptation d'une `Demande de validation`

Architecture retenue pour la suite :

- `Phase 1`
  - reste le flux de lecture / sync Hektor
- `Phase 2`
  - reste le flux de consolidation / enrichissement / push vers Supabase
- `Supabase`
  - reste la source de donnees prod
  - auth
  - tables app
  - profils utilisateurs
- `Vercel`
  - reste le front React public
- `Backend Python dedie`
  - prend seulement les actions serveur sensibles
  - remplace les routes Vite locales qui ne peuvent pas vivre durablement en prod

Endpoints cibles a porter dans ce backend Python :

- `POST /admin/users/create`
- `GET /admin/users/list`
- `POST /admin/users/update`
- `POST /admin/users/send-reset`
- `POST /hektor-diffusion/apply`
- `POST /hektor-diffusion/accept`

Endpoint optionnel ensuite si besoin de parite totale :

- `POST /notifications/diffusion-decision`

Routes locales Vite qui ne seront pas portees telles quelles :

- `/api/hektor-diffusion/targets`
- `/api/hektor-diffusion/preview-targets`
- `/api/hektor-diffusion/seed`
- `/api/hektor-diffusion/broadcasts`

Regle retenue pour ces cas :

- `targets`
  - restent dans Supabase
- `preview-targets`
  - doit etre calculable depuis Supabase + mapping agence
- `broadcasts`
  - doit venir de la donnee synchronisee `Phase 1 / Phase 2`
- `seed`
  - reste un outil de debug / maintenance local si besoin

But :

- ne pas refondre tout le projet
- conserver `Phase 1` et `Phase 2` comme moteurs de data
- sortir seulement les commandes serveur qui cassent en prod
- rester au plus proche de la logique Python locale deja stabilisee

## Mise a jour 07/04/2026 - difference `apply` / `accept`

Les deux routes Hektor ne sont pas des doublons. Elles correspondent a deux entrees metier distinctes.

### `POST /hektor-diffusion/apply`

Origine :

- bouton principal de la console `Diffusion`

Regle :

- utilise les cibles actuellement visibles / sauvegardees dans `app_diffusion_target`
- tente `diffusable = 1` si necessaire
- applique ensuite exactement les coches choisies :
  - `enabled` => `PUT`
  - `disabled` => `DELETE`

Interpretation :

- action manuelle issue de la console
- suit le choix explicite de l'utilisateur au moment du clic

### `POST /hektor-diffusion/accept`

Origine :

- acceptation d'une `Demande de validation`

Regle :

- ne depend pas d'un choix manuel en console a cet instant
- recharge d'abord les cibles par defaut de l'agence
- applique ensuite le flux d'acceptation avec ces passerelles par defaut

Interpretation :

- action issue du workflow de validation
- suit la politique agence par defaut
- pas la selection manuelle courante de la console

Conclusion retenue :

- `apply`
  - console manuelle
- `accept`
  - workflow d'acceptation Pauline

Les deux endpoints doivent donc exister dans le futur backend Python.

## Mise a jour 07/04/2026 - squelette backend Python et branchement front

Le squelette du backend Python a ete cree dans :

- `backend/`

Structure posee :

- `backend/app/main.py`
- `backend/app/settings.py`
- `backend/app/auth.py`
- `backend/app/models.py`
- `backend/app/services/supabase_admin.py`
- `backend/app/services/hektor_bridge.py`
- `backend/app/routers/admin_users.py`
- `backend/app/routers/hektor_diffusion.py`
- `backend/requirements.txt`
- `backend/README.md`

Principes retenus :

- `admin-users`
  - passe par Supabase REST / Auth Admin avec la `service role`
- `hektor-diffusion/apply`
  - reutilise `phase2/sync/hektor_diffusion_writeback.py apply-targets`
- `hektor-diffusion/accept`
  - reutilise `phase2/sync/hektor_diffusion_writeback.py accept-request`
- apres `apply` ou `accept`
  - appel automatique de `phase2/sync/refresh_single_annonce.py` si un `hektor_annonce_id` est retourne

But :

- ne pas reecrire la logique Hektor stable
- garder le comportement local comme reference

Branchement front pose ensuite dans :

- `apps/hektor-v1/src/lib/api.ts`

Regle du front :

- si `localhost`
  - conserver les routes Vite locales
- si `VITE_BACKEND_API_URL` est renseignee
  - utiliser le backend Python pour :
    - `POST /admin/users/create`
    - `GET /admin/users/list`
    - `POST /admin/users/update`
    - `POST /admin/users/send-reset`
    - `POST /hektor-diffusion/apply`
    - `POST /hektor-diffusion/accept`
- sinon
  - garder provisoirement le fallback `Supabase Functions`

Variable a ajouter cote front prod quand le backend sera heberge :

- `VITE_BACKEND_API_URL`
  - exemple futur :
    - `https://gti-backend.onrender.com`

Conclusion :

- le projet peut maintenant migrer progressivement
- sans casser le local
- sans bloquer le front tant que le backend Python n'est pas encore heberge
