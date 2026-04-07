# Notes projet ACTIF

## Statut au 23/03/2026

Le projet `ACTIF` est abandonne pour l'instant.

Decision de cadrage :

- ne plus en faire un chantier actif
- ne plus le considerer comme priorite de reprise
- se concentrer uniquement sur le pipeline principal

Le perimetre de travail souhaite maintenant est uniquement :

- `sync_raw.py`
- `normalize_source.py`
- `build_case_index.py`
- la base principale `data/hektor.sqlite`
- les notes du projet principal

Les scripts et la base `ACTIF` restent seulement comme archive technique et historique de reflexion.

Date: 20/03/2026

## Objet

Le projet `ACTIF` est un nouveau projet separe du pipeline principal.

Objectif :

- construire une surcouche metier separee du projet principal
- avec une logique d'extraction differente
- centree sur la liste des annonces actuellement en state actif
- sans chercher a reconstruire ici les offres, compromis, ventes ou l'historique transactionnel

## Strategie retenue pour les annonces actives

Source de verite quotidienne :

- `GET /Api/Annonce/ListAnnonces/`
- avec `archive=0`
- et tri :
  - `sort=datemaj`
  - `way=DESC`

Le listing actif quotidien sert a representer le parc actif courant.

## Logique quotidienne retenue

1. lire tout le listing des annonces actives (`archive=0`)
2. pour chaque annonce, recuperer au minimum :
   - `id`
   - `datemaj`
3. comparer avec la base locale
4. cas metier :
   - `id` inconnu => nouvelle annonce active
   - `id` connu + `datemaj` differente => annonce modifiee
   - `id` connu + `datemaj` identique => inchangée
5. appeler `AnnonceById` seulement pour :
   - les nouvelles annonces
   - les annonces modifiees

## Gestion des sorties du parc actif

Mode retenu : `riche`

Principe :

- si une annonce etait active localement au run precedent
- mais n'apparait plus dans `ListAnnonces archive=0`
- alors elle sort du parc actif courant

Dans ce cas :

- elle est mise de cote du parc actif
- un appel `AnnonceById` est relance
- le detail permet de recuperer son nouveau `statut`

But :

- savoir qu'elle n'est plus dans le parc actif courant
- et mettre a jour son dernier `statut` connu via `AnnonceById`

## Pourquoi cette approche

- elle couvre tout le parc actif du jour
- elle detecte :
  - les nouvelles annonces actives
  - les annonces actives modifiees
  - les annonces sorties du parc actif
- elle evite de rejouer les details sur toutes les annonces
- elle s'appuie sur un comportement API deja valide :
  - `ListAnnonces` expose `datemaj`
  - `sort=datemaj&way=DESC` fonctionne sur l'instance

## Point de vigilance

- le full historique du projet principal n'avait pas de `datemaj` annonces en brut
- pour `ACTIF`, il faudra donc raisonner avec son propre stock et ses propres runs
- il faut bien separer les notes et scripts de `ACTIF` de ceux du projet principal

## Ou nous en sommes

Etat de reflexion retenu au 20/03/2026 :

- `ListAnnonces archive=0` peut servir de source de verite quotidienne pour le parc actif
- `datemaj` est exploitable sur `annonces`
- le mode `riche` est retenu pour les sorties du parc actif :
  - si une annonce n'apparait plus dans le listing actif
  - elle est mise de cote
  - puis `AnnonceById` est rejoue pour recuperer son nouveau `statut`

### Point important identifie

Le projet `ACTIF` ne vise pas a reconstruire les transactions.

Le besoin retenu ici est plus simple :

- suivre quotidiennement la liste des annonces actuellement actives
- recuperer leur detail
- detecter celles qui sortent du parc actif
- mettre a jour leur `statut` connu

### Decision a ce stade

- la logique `ACTIF` peut rester centree uniquement sur les annonces
- il n'est pas necessaire dans ce projet secondaire d'ajouter les offres, compromis, ventes ou mandats
- le run quotidien devra couvrir :
  - les entrees dans le parc actif
  - les modifications de fiches annonces
  - les sorties du parc actif

## Point de reprise pour demain

Etat retenu en fin de session :

- `ACTIF` doit suivre principalement :
  - les annonces actuellement actives
  - leur detail
  - les contacts associes
  - le mandat associe
- `ACTIF` ne doit pas reconstruire :
  - offres
  - compromis
  - ventes

### Strategie annonces retenue

- source quotidienne : `ListAnnonces` avec `archive=0`
- tri exploitable confirme :
  - `sort=datemaj`
  - `way=DESC`
- logique retenue :
  - lire le listing actif
  - comparer localement `id + datemaj`
  - produire :
    - `new_ids`
    - `updated_ids`
    - `removed_ids`
- pour ces 3 lots :
  - relancer `AnnonceById`
- but :
  - obtenir le vrai `statut`
  - identifier les sorties du parc actif avec leur nouveau state

### Strategie contacts retenue a ce stade

Tests API realises le 20/03/2026 :

- `ListContacts` expose bien `datemaj`
- `sort=datemaj` est toujours casse :
  - `metadata.total` non nul
  - `data=[]`
- `sort=id&way=DESC` fonctionne
- `sort=dateenr&way=DESC` fonctionne
- `sort=nom`, `sort=prenom`, `sort=id_negociateur` et `sort=dateAutoArchiv` fonctionnent aussi
- le listing actif par defaut semble remonter des contacts tres recents

Points observes :

- sur les tests, `page=0` et `page=1` semblent renvoyer la meme premiere page
- `page=2` change bien
- il existe donc probablement une bizarrerie de pagination a verifier

Decision provisoire :

- ne pas encore coder de logique globale delta contacts
- ne pas baser `ACTIF` sur un scan complet quotidien des contacts
- garder les contacts comme enrichissement secondaire des annonces du delta

### Decision de travail retenue apres tests

- ne pas utiliser `ListContacts` comme source de delta autonome
- ne pas piloter les contacts avec `sort=datemaj` tant que l'API renvoie `data=[]`
- considerer `sort=id&way=DESC` comme le tri recent le plus exploitable
- considerer `sort=dateenr&way=DESC` comme un tri de creation, pas de modification
- piloter `ACTIF` d'abord par le delta annonces actives
- pour chaque annonce nouvelle, modifiee ou sortie du parc actif :
  - relancer `AnnonceById`
  - extraire les contacts associes
  - relancer `ContactById` si un enrichissement contact est necessaire
- stocker quand meme `datemaj` des contacts quand il est present dans les payloads
- ne pas s'en servir comme cle de scan global tant que `ListContacts sort=datemaj` reste defectueux

### Consequence pour l'implementation ACTIF

- source primaire quotidienne : annonces actives
- source secondaire : contacts references par les annonces du delta
- option possible plus tard :
  - ajouter une veille courte `ListContacts?archive=0&sort=id&way=DESC`
  - uniquement pour capter les creations tres recentes
  - sans pretendre couvrir toutes les modifications de fiches anciennes

### Question ouverte a reprendre

Verifier si les `contacts actifs` sont pilotables de facon raisonnable via :

- `ListContacts?archive=0&sort=id&way=DESC`

Test restant a faire :

- comparer plusieurs pages consecutives reelles :
  - `page=1`
  - `page=2`
  - `page=3`
  - `page=4`
  - `page=5`
- verifier si l'ordre reste exploitable avec `id DESC`
- verifier si la pagination a un decalage `0/1`

### Avant de coder le projet ACTIF

Confirmer demain :

1. la strategie finale sur les contacts
2. le modele local minimal :
   - annonces
   - details annonces
   - contacts associes
   - mandat associe
3. la structure des scripts du dossier `ACTIF`

## Implementation retenue

Script autonome :

- `ACTIF/actif_sync.py`

Principes d'autonomie :

- base SQLite dediee : `ACTIF/actif.sqlite`
- pas de dependance au schema SQLite principal
- pas d'import du script principal de sync
- authentification API geree directement dans le script ACTIF
- chargement de configuration depuis `ACTIF/.env`, puis fallback sur `../.env`

Commande de lancement :

- `.\.venv\Scripts\python.exe ACTIF\actif_sync.py`

Commande de test court :

- `.\.venv\Scripts\python.exe ACTIF\actif_sync.py --max-pages 1`

## Couche normalized ACTIF

Script :

- `ACTIF/actif_normalize.py`

But :

- repartir de `ACTIF/actif.sqlite`
- ne pas relire l'API
- produire une couche metier legere au-dessus de `actif_annonce`

Tables produites dans `ACTIF/actif.sqlite` :

- `actif_parc_courant`
  - 1 ligne = 1 annonce connue par ACTIF
  - annonce centrale
  - mandat aplati quand il existe
  - le mandat reste optionnel
- `actif_annonce_contact`
  - 1 ligne = 1 contact lie a 1 annonce
  - contacts eclates par role :
    - `proprietaire`
    - `mandant`
    - `acquereur`
    - `notaire_entree`
    - `notaire_sortie`
- `actif_contact_courant`
  - 1 ligne = 1 contact detaille connu via `ContactById`
  - conserve la fiche contact detaillee et les `recherches`
- `actif_broadcast_courant`
  - 1 ligne = 1 diffusion reelle par annonce et par passerelle
  - issu de `DetailedBroadcastList`

Principes metier retenus :

- une annonce active peut exister sans mandat
- ce cas doit etre accepte comme normal
- l'absence de mandat n'exclut pas l'annonce du parc courant
- les contacts restent secondaires et derives de `AnnonceById`
- quand `ContactById` a ete relance, la normalized enrichit les lignes contact avec ce detail
- `actif_annonce_contact` reste la table de lien annonce/contact
- `actif_contact_courant` devient le stock detaille des contacts enrichis
- `diffusable` reste un champ annonce
- la diffusion reelle par portail est collecte a part via `DetailedBroadcastList`

## Strategie finale retenue

### Perimetre annonces

- le parc quotidien de base reste `ListAnnonces` avec `archive=0`
- le delta annonces continue de reposer sur :
  - `annonce_id`
  - `ListAnnonces.datemaj`
- cela sert a detecter :
  - nouvelles annonces
  - annonces modifiees
  - annonces sorties du parc non archive

### Point valide par test metier

Test realise sur l'annonce `61802` le 20/03/2026 :

- modification d'un contact lie uniquement
- `contact.datemaj` a bien change dans `AnnonceById`
- `ListAnnonces.datemaj` de l'annonce n'a pas change

Conclusion :

- le delta annonces seul ne suffit pas pour detecter les changements de contacts lies

### Strategie quotidienne contacts retenue

- ne pas utiliser `ListContacts` comme moteur principal
- utiliser `AnnonceById` comme detecteur quotidien des changements de contacts lies
- cible quotidienne :
  - annonces encore dans `archive=0`
  - avec dernier `statut_name = actif` connu localement

Pour ces annonces :

- relire `AnnonceById`
- extraire les contacts presents dans `data`
- comparer localement :
  - `contact_id`
  - `contact.datemaj`
- appeler `ContactById` seulement pour :
  - les nouveaux contacts lies
  - les contacts lies dont `datemaj` a change

### Consequence implementation

`ACTIF/actif_sync.py` fait maintenant 3 choses :

1. delta annonces via `ListAnnonces archive=0`
2. refresh quotidien `AnnonceById` sur les annonces `statut_name = actif`
3. `ContactById` cible uniquement sur les contacts detectes comme nouveaux ou modifies

### Diffusion reelle par portail

Point retenu apres relecture des mails de Romain :

- `diffusable` ne signifie pas "effectivement diffuse"
- pour la diffusion reelle, il faut utiliser :
  - `GET /Api/Passerelle/DetailedBroadcastList/`

Le script `ACTIF/actif_sync.py` integre maintenant aussi :

4. extraction de la diffusion reelle par portail via `DetailedBroadcastList`

Stock local dedie :

- `actif_broadcast`
- `actif_broadcast_listing`

Stock local dedie :

- `actif_annonce` : coeur annonce
- `actif_contact` : details `ContactById`
- `actif_broadcast` : liste des passerelles
- `actif_broadcast_listing` : diffusion detaillee par annonce
- `actif_parc_courant` : couche metier normalisee
- `actif_annonce_contact` : liens annonce/contact normalises
- `actif_contact_courant` : contacts enrichis
- `actif_broadcast_courant` : diffusion reelle normalisee

Commande de normalisation :

- `.\.venv\Scripts\python.exe ACTIF\actif_normalize.py`

Commande d'extraction partielle diffusion uniquement :

- `.\.venv\Scripts\python.exe ACTIF\actif_sync.py --broadcasts-only`

But de cette commande :

- ne pas refaire tout le run annonces / contacts
- extraire uniquement ce qui manque sur la diffusion reelle par portail
- alimenter :
  - `actif_broadcast`
  - `actif_broadcast_listing`

Usage recommande :

1. lancer `actif_sync.py`
2. verifier le run
3. lancer `actif_normalize.py`
4. exploiter :
   - `actif_parc_courant`
   - `actif_annonce_contact`
   - `actif_contact_courant`
   - `actif_broadcast_courant`

## Couche build ACTIF

Script :

- `ACTIF/actif_build.py`

But :

- repartir de la couche normalized
- produire une table finale consolidee
- 1 ligne = 1 annonce

Table produite :

- `actif_case_index`

Cette table consolide :

- annonce
- mandat
- contacts agreges
- diffusion reelle par portail
- flags de presence utiles

Champs d'agregation principaux :

- `has_mandat`
- `nb_contacts_total`
- `nb_proprietaires`
- `nb_mandants`
- `nb_acquereurs`
- `nb_notaires`
- `has_contact_detail`
- `nb_broadcasts`
- `has_broadcast`
- `is_broadcasted`
- `broadcast_names`
- `broadcast_status_summary`

Commande de build :

- `.\.venv\Scripts\python.exe ACTIF\actif_build.py`

Sequence recommandee complete :

1. `.\.venv\Scripts\python.exe ACTIF\actif_sync.py`
2. `.\.venv\Scripts\python.exe ACTIF\actif_normalize.py`
3. `.\.venv\Scripts\python.exe ACTIF\actif_build.py`

## Etat de reprise

Etat retenu en fin de session :

- `ACTIF` a maintenant 3 couches :
  - `sync`
  - `normalize`
  - `build`
- `actif_sync.py` gere desormais :
  - `ListAnnonces archive=0`
  - `AnnonceById`
  - `ContactById` cible
  - `DetailedBroadcastList`
- `actif_normalize.py` produit :
  - `actif_parc_courant`
  - `actif_annonce_contact`
  - `actif_contact_courant`
  - `actif_broadcast_courant`
- `actif_build.py` produit :
  - `actif_case_index`

### Point metier valide important

Test realise sur l'annonce `61802` :

- modification d'un contact lie uniquement
- `contact.datemaj` change bien dans `AnnonceById`
- `ListAnnonces.datemaj` de l'annonce ne change pas

Conclusion retenue :

- le delta annonce seul ne suffit pas pour suivre les changements de contacts lies
- `AnnonceById` doit servir de detecteur quotidien de changement contact
- `ContactById` doit rester cible sur les contacts nouveaux ou modifies

### Point de vigilance script

Un bug de fin de run sur `finish_run()` a ete corrige.

Bug identifie puis corrige :

- `extract_status()` ne lisait pas la vraie structure API de `AnnonceById`
- le statut reel est expose comme :
  - `data.statut.id`
  - `data.statut.name`
- consequence observee :
  - `statut_name` restait `NULL`
  - aucune annonce ne passait le filtre `statut_name = actif`
  - `ContactById` ne se declenchait pas

Correctif applique :

- lecture explicite de `data.statut.id/name` dans `actif_sync.py`

### Commandes de reprise demain

Depuis `C:\Users\frede\Desktop\Projet` :

1. lancer le run complet :
   - `.\.venv\Scripts\python.exe ACTIF\actif_sync.py`
2. suivre le run :
   - `.\.venv\Scripts\python.exe ACTIF\actif_watch.py --interval 1`
3. reconstruire la normalized :
   - `.\.venv\Scripts\python.exe ACTIF\actif_normalize.py`
4. construire la table finale :
   - `.\.venv\Scripts\python.exe ACTIF\actif_build.py`

### Commande partielle utile

Si besoin de ne recuperer que la diffusion reelle :

- `.\.venv\Scripts\python.exe ACTIF\actif_sync.py --broadcasts-only`

## Reprise rapide demain

Point de reprise exact en fin de session :

- le run precedent a montre que `actif_contact` restait vide
- analyse faite :
  - ce n'etait pas un probleme de base vide au premier run
  - ce n'etait pas un probleme normal de logique metier
  - le vrai bug etait dans la lecture du statut annonce

### Cause identifiee

Dans `AnnonceById`, le statut reel est expose sous :

- `data.statut.id`
- `data.statut.name`

Le script lisait seulement des variantes du type :

- `statut_id`
- `statut_name`
- `statutId`
- `statutName`

Consequence :

- `statut_name` restait `NULL` partout
- le filtre :
  - `archive=0`
  - `statut_name = actif`
  ne laissait passer aucune annonce
- donc `ContactById` ne se declenchait jamais

### Correctif applique

- `actif_sync.py` lit maintenant explicitement :
  - `data.statut.id`
  - `data.statut.name`

### Consequence pratique

Il faut refaire un run complet sur base propre.

Pourquoi :

- l'ancienne base a ete remplie avec un statut mal interprete
- les contacts n'ont pas ete extraits correctement
- il vaut mieux repartir proprement

### Regle d'amorcage retenue

Au premier run sur base vide :

- `ACTIF` force `AnnonceById` sur tout le parc `ListAnnonces archive=0`
- il ne se limite pas au simple delta annonces

Pourquoi :

- le vrai `statut_name` n'existe que dans `AnnonceById`
- le ciblage quotidien des contacts repose ensuite sur :
  - annonces `archive=0`
  - et `statut_name = actif`
- sans amorcage complet des `AnnonceById`, ce ciblage serait incomplet

Donc :

- base vide = run d'amorcage complet du detail annonces
- runs suivants = delta annonces + refresh quotidien du sous-ensemble `statut_name = actif`

### Commandes exactes a relancer demain

Depuis `C:\Users\frede\Desktop\Projet` :

1. supprimer la base ACTIF :
   - `Remove-Item ACTIF\actif.sqlite -Force -ErrorAction SilentlyContinue`
   - `Remove-Item ACTIF\actif.sqlite-wal -Force -ErrorAction SilentlyContinue`
   - `Remove-Item ACTIF\actif.sqlite-shm -Force -ErrorAction SilentlyContinue`

2. lancer le run complet :
   - `.\.venv\Scripts\python.exe ACTIF\actif_sync.py`

3. suivre le run :
   - `.\.venv\Scripts\python.exe ACTIF\actif_watch.py --interval 1`

4. une fois fini :
   - `.\.venv\Scripts\python.exe ACTIF\actif_normalize.py`
   - `.\.venv\Scripts\python.exe ACTIF\actif_build.py`

### Point de controle apres prochain run

Verifier en priorite :

- que `statut_name` n'est plus `NULL` partout
- que `actif_contact` contient bien des lignes
- que la suite `normalize` puis `build` s'executent correctement

## Mise a jour retenue le 20/03/2026 fin de session

Evolution metier validee :

- `ListAnnonces` reste le detecteur principal du delta annonces
- regle annonces :
  - `id` absente localement => `AnnonceById`
  - `datemaj` differente => `AnnonceById`
  - annonce sortie du parc actif => `AnnonceById` si on veut recalculer le statut reel
- le detail `AnnonceById` reste la source principale de verite sur l'annonce
- le bloc contacts embarque dans `AnnonceById` reste la reference principale rattachee a l'annonce

Evolution contacts retenue apres lecture du mail `notice/ROMAIN MAIL 2.txt` :

- `ListContacts` doit etre lu avec :
  - `sort=dateLastTraitement`
  - `way=DESC`
- `sort=datemaj` ne doit plus etre utilise pour la liste des contacts
- `dateLastTraitement` sert a detecter des contacts existants modifies
- une modification contact peut ne pas modifier `datemaj` de l'annonce

Strategie finale du `sync` :

1. lire `ListAnnonces archive=0 sort=datemaj way=DESC`
2. calculer le delta annonces local
3. lire `ListContacts archive=0 sort=dateLastTraitement way=DESC`
4. recuperer les `contact_id` modifies depuis le dernier run contact
5. retrouver localement les `annonce_id` qui referencent ces contacts
6. rejouer `AnnonceById` sur l'union :
   - annonces nouvelles
   - annonces modifiees
   - annonces sorties
   - annonces liees a des contacts modifies
7. mettre a jour le detail annonce complet en base

Decision importante :

- on ne pilote plus le flux principal avec `ContactById`
- si un contact change, on privilegie le rechargement de l'annonce liee via `AnnonceById`
- cela garde une source principale unique et coherente cote annonce

Regle de bootstrap retenue :

- premier run sur base vide :
  - recharger tout `ListAnnonces`
  - faire `AnnonceById` sur tout le parc actif
  - lire tout `ListContacts sort=dateLastTraitement`
  - ne pas filtrer les contacts par date de dernier run
- runs suivants :
  - delta annonces par `id + datemaj`
  - delta contacts par `dateLastTraitement > last_contact_run_at`
  - puis `AnnonceById` sur les annonces liees a ces contacts

Etat code en fin de session :

- `ACTIF/actif_sync.py` a ete recale sur cette logique
- `ACTIF/actif_normalize.py` reste compatible
- `ACTIF/actif_build.py` reste compatible
- validations locales faites :
  - compilation Python OK
  - test SQLite local `init_db -> normalize -> build` OK
- pas encore de run API complet relance apres cette mise a jour
