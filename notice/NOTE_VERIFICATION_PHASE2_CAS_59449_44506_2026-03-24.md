# Note verification phase 2 - cas 59449 / 44506

Date: 24/03/2026

## Objet

Documenter la verification du cas annonce `59449` et du cas annonce `44506` apres reprise des mandats, afin de confirmer si la phase 2 est encore bloquee ou non.

## Resume executif

Conclusion retenue:

- la phase 2 n'est pas en cause pour `59449`
- le cas `59449` reste un probleme de donnees source
- le cas `44506` prouve au contraire que la chaine phase 2 sait bien integrer un mandat quand le rattachement source existe
- on peut donc continuer la phase 2

Reserve pratique:

- `phase2.sqlite` doit etre consideree comme la source de verite
- les exports HTML `phase2/app_metier.html` et `phase2/vue_generale.html` semblent pouvoir etre en retard ou filtres par rapport a la base phase 2

## Cas 59449

### Constat dans les donnees source

Dans `data/hektor.sqlite`:

- `hektor_annonce.hektor_annonce_id = 59449`
- `no_dossier = 18350`
- `no_mandat = 18350`

Dans `raw_api_response`:

- `mandats_by_annonce` pour `59449` existe bien
- mais il renvoie `data: []`

Le detail mandat `mandat_detail` pour `18350` existe aussi en brut, mais il ne correspond pas au dossier `59449`:

- `id = 18350`
- `numero = 12960`
- ce mandat normalise est rattache a `hektor_annonce_id = 44506`

### Conclusion sur 59449

Le point important est le suivant:

- `18350` est utilise comme `no_dossier` et `no_mandat` dans l'annonce `59449`
- mais l'ID mandat Hektor `18350` pointe en realite vers un autre mandat, numero `12960`, rattache a `44506`

Donc:

- le probleme n'est pas une absence de detail mandat dans la phase 2
- le probleme n'est pas non plus une absence de `MandatById(18350)` dans le brut
- le probleme est un conflit de sens entre:
  - un numero de dossier / numero de mandat visible dans l'annonce
  - et un identifiant technique de mandat Hektor

Pour `59449`, la relation brute `MandatsByIdAnnonce` etant vide, la phase 2 reste coherente en classant ce dossier sans mandat exploitable.

## Cas 44506

### Constat dans les donnees source

Dans `data/hektor.sqlite`:

- `hektor_annonce.hektor_annonce_id = 44506`
- `no_dossier = VM18892`
- `no_mandat = 12960`
- `diffusable = 0`
- `valide = 0`

Dans `hektor_mandat`:

- `hektor_mandat_id = 18350`
- `hektor_annonce_id = 44506`
- `numero = 12960`
- `type = SIMPLE`

Dans `hektor_annonce_detail`:

- le tableau `mandats_json` contient bien un mandat:
  - `id = 18350`
  - `numero = 12960`

### Constat dans la phase 2

Dans `phase2/phase2.sqlite`:

- `app_dossier` contient bien `hektor_annonce_id = 44506`
- `app_dossier.hektor_mandat_id = 18350`
- `app_dossier.numero_mandat = 12960`

Le dossier est aussi present dans:

- `app_view_generale`
- `app_view_demandes_mandat_diffusion`

Etat metier observe:

- `event_type = mandat_actif_non_diffusable`
- `validation_diffusion_state = a_controler`
- `etat_visibilite = non_diffusable`
- `diffusable = 0`
- `valide = 0`

### Conclusion sur 44506

Le cas `44506` montre que:

- la phase 2 integre correctement le mandat
- le rattachement `annonce -> mandat` fonctionne bien quand la source le fournit
- le dossier remonte ensuite en vue metier pour une raison fonctionnelle de diffusion, pas a cause d'une perte de mandat

Autrement dit:

- `44506` n'est pas un contre-exemple de la phase 2
- c'est au contraire une validation du bon fonctionnement de la chaine consolidee sur un cas avec mandat

## Consequence pour la phase 2

Decision retenue:

- la phase 2 peut continuer

Justification:

- `59449` est un sujet amont de qualite / interpretation des donnees source
- `44506` confirme que la phase 2 sait exploiter un mandat lorsque le lien existe
- il n'y a donc pas de blocage structurel de phase 2 sur ce point

## Point de vigilance complementaire

Lors du controle rapide:

- `44506` est present dans `phase2.sqlite`
- mais il n'a pas ete retrouve par recherche textuelle simple dans `phase2/app_metier.html` ni dans `phase2/vue_generale.html`

Hypothese la plus probable:

- les exports HTML n'ont pas ete regeneres apres les derniers rebuilds
- ou ils embarquent un sous-ensemble / filtrage different de la base

Regle pratique pour la suite:

- raisonner d'abord sur `phase2/phase2.sqlite`
- ne valider les HTML qu'apres regeneration explicite

## Impact sur l'analyse precedente

La formulation precedente "le mandat `18350` n'existe toujours pas dans `hektor_mandat` pour `59449`" etait incorrecte.

Formulation corrigee:

- le mandat `18350` existe bien
- mais il appartient au dossier `44506`
- il ne peut donc pas etre utilise comme preuve d'un mandat rattache a `59449`

## Conclusion finale

Point tranche au 24/03/2026:

- `59449` n'est pas un bug de phase 2
- `44506` valide le bon passage du mandat dans la phase 2
- la suite du travail phase 2 peut continuer
- les controles futurs doivent s'appuyer d'abord sur `phase2.sqlite`, puis sur les exports HTML une fois regeneres
