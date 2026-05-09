# Note ergonomie annonces / estimations

Date: 2026-05-07

## Objet

Cette note documente le recadrage produit de la navigation React / Supabase autour des annonces actives et des estimations.

## Decision produit

La vue historique "Liste des annonces" est renommee "Annonces actives".

Raison: une annonce active Hektor peut deja etre dans le flux commercial sans avoir encore de numero de mandat. Le terme "annonce active" est donc plus juste que "annonce en mandat".

Une nouvelle vue "Estimations" est ajoutee dans l'application. Elle represente les annonces Hektor dont le statut est `Estimation`, c'est-a-dire les futurs mandats potentiels.

## Perimetre donnees

La Phase 1 recupere deja les estimations. Le blocage etait dans le perimetre d'export applicatif vers Supabase:

`phase2/sync/export_app_payload.py`

Le filtre d'export inclut maintenant:

- `Actif`
- `Sous offre`
- `Sous compromis`
- `Estimation`

Cote application:

- "Annonces actives" force le perimetre `Actif`, `Sous offre`, `Sous compromis`.
- "Estimations" force le perimetre `Estimation`.
- Les deux vues continuent a lire `app_dossiers_current`, donc aucune nouvelle table Supabase ni nouvelle policy RLS n'est necessaire pour cette premiere version.

## Evolution des libelles

La vue "Annonces actives" garde sa mise en page historique. Seul son nom change dans la navigation.

La vue "Estimations" utilise des libelles plus adaptes au suivi de futurs mandats.

Dans cette vue, la colonne "Mandat" devient "Projet".

Elle affiche:

- le numero de dossier;
- le numero de mandat si present;
- sinon "Sans mandat";
- le type de bien et la ville en contexte.

Dans cette vue, la colonne "Statut" devient "Avancement".

Elle affiche une synthese metier calculee a partir des donnees existantes:

- `Estimation en cours`;
- `Annonce creee - mandat manquant`;
- `Mandat a valider`;
- `Mandat valide - non diffuse`;
- `Diffuse`;
- `Offre en cours`;
- `Compromis en cours`;
- `Vendu`.

## Ergonomie de la vue Estimations

La vue "Estimations" reprend la structure de la liste des annonces pour rester rapide a comprendre.

Les actions de validation / diffusion sont masquees dans cette premiere version, car une estimation n'est pas encore un mandat a diffuser.

Le bouton d'action principal devient "Voir le projet".

Les filtres de cette premiere version restent volontairement simples:

- negociateur;
- agence;
- archive;
- recherche rapide.

Les filtres de diffusion, validation, passerelle, offre et compromis restent reserves aux annonces actives / mandats.

## Suite logique

La prochaine evolution utile sera de definir les actions metier propres aux estimations:

- suivre une relance estimation;
- detecter une estimation transformee en mandat;
- distinguer estimation active, abandonnee, gagnee;
- preparer une vue commerciale de conversion estimation -> mandat.

## Correctif detail annonce du 2026-05-08

Probleme observe: au clic sur une ligne, la fiche detail pouvait afficher immediatement les donnees enrichies de l'annonce precedente, puis remplacer l'affichage par la bonne annonce apres chargement.

Cause: le composant conservait temporairement `detail_payload_json` du `selectedDossier` precedent pendant le chargement de `loadDossierDetail(...)`.

Correction appliquee:

- au changement d'annonce, la fiche rapide reprend seulement les donnees de la ligne selectionnee;
- `detail_payload_json` n'est conserve que si l'utilisateur rouvre exactement le meme `app_dossier_id`;
- le chargement detail n'est plus relance quand la liste visible se met simplement a jour.

## Correctif perimetre suivi mandats du 2026-05-08

Probleme observe: l'ajout du statut `Estimation` dans le perimetre exporte vers Supabase pouvait modifier les volumes de la vue "Suivi des mandats".

Cause: la vue "Suivi des mandats" chargeait les mandats avec le filtre statut global lorsqu'il etait vide. Depuis l'ajout des estimations, un filtre statut vide pouvait donc inclure aussi les lignes `Estimation`.

Regle produit retenue:

- "Estimations" reste la seule vue dediee aux annonces `Estimation`;
- "Suivi des mandats" suit le parc mandat actif et exclut les estimations par defaut;
- son perimetre par defaut est aligne sur "Annonces actives": `Actif`, `Sous offre`, `Sous compromis`.

Correction appliquee dans l'application:

- a l'ouverture ou a la reinitialisation de "Suivi des mandats", le filtre statut par defaut devient `__active_listings__`;
- si le filtre statut est vide dans cette vue, l'application force aussi `__active_listings__` avant d'appeler Supabase;
- les KPI et le listing du suivi ne sont donc plus pollues par les estimations.

## Correctif experience KPI annonces actives du 2026-05-08

Probleme observe: au clic sur un KPI de la vue "Annonces actives", le titre/filtres changeaient avant le listing, tandis que les anciennes lignes restaient visibles sans retour clair.

Cause: le chargement principal attendait en bloc `loadDossiersPage`, `loadMandatsPage` et `loadWorkItemsPage` avant d'appliquer les nouvelles lignes mandats.

Correction appliquee:

- le KPI clique est marque actif immediatement;
- le tableau affiche "Chargement du listing..." pendant la mise a jour;
- les anciennes lignes sont visuellement attenuees pendant le rafraichissement;
- `loadMandatsPage` met a jour le listing des qu'il repond;
- `loadDossiersPage` et `loadWorkItemsPage` continuent de se charger a part pour garder le contexte global coherent;
- les KPI/statistiques continuent de se recalculer independamment, sans bloquer l'experience du tableau.

## Chantier cockpit detail annonce du 2026-05-08

Objectif: transformer la page detail des annonces actives en espace de pilotage plus lisible, sans retirer les informations deja disponibles.

Sauvegarde de travail:

- branche creee: `codex/detail-cockpit`;
- `main` reste utilisable sur le dernier etat pousse avant refonte;
- seuls `apps/hektor-v1/src/App.tsx`, `apps/hektor-v1/src/styles.css` et cette notice doivent porter le chantier.

Organisation retenue:

- `Synthese`: resume rapide du dossier, statut, validation, diffusion, passerelles, commercial et action suivante;
- `Commercialisation`: historique des prix, offre, compromis, vente et rendez-vous annonce;
- `Mandat & contacts`: detail mandat et mandants dans une meme zone;
- `Diffusion`: validation Hektor, etat diffusable et passerelles activees;
- `Contenu annonce`: descriptif, caracteristiques, notes et commentaires;
- `Historique`: demandes de diffusion et demandes de baisse de prix;
- `Visites virtuelles`: groupes et modeles Matterport.

Principe ergonomique:

- les 7 boutons servent de navigation metier stable;
- l'utilisateur retrouve tous les blocs existants, mais ils ne sont plus empiles dans une seule page longue;
- les passerelles sont affichees sous forme de badges marques, par exemple Leboncoin, Bien'ici, GTI ou SeLoger;
- une colonne d'actions rapides garde l'acces a Hektor, Diffusion et Historique.

Iteration visuelle ajoutee:

- le conteneur detail devient un panneau cockpit dedie;
- le haut de page est plus visuel, avec photo, titre, statut, validation et passerelles;
- les 7 onglets deviennent de vrais boutons de pilotage;
- la colonne droite devient une zone "Pilotage" plus visible, avec actions rapides;
- le rendu reste volontairement limite a la page detail, sans changement de requete Supabase ni modification de la logique API.

Reprise pro apres controle visuel:

- la colonne de pilotage n'est plus rendue apres le hero, elle est placee dans une grille cockpit a droite du contenu principal;
- le hero est compacte pour eviter une page vitrine trop haute;
- la largeur de la modale detail est elargie pour retrouver une composition dashboard;
- les onglets sont reduits en barre de navigation compacte;
- les cartes, titres, images et espacements sont resserres pour donner une ergonomie outil metier.

Controle popup reel:

- la popup a ete ouverte localement sur une annonce reelle (`EM4048`, mandat `18562`);
- les onglets sont maintenant visibles des l'ouverture de la popup;
- la colonne `Pilotage` est visible a droite, avec fond sombre et actions lisibles;
- le hero ne pousse plus toute la navigation sous la ligne de flottaison;
- le build production a ete relance apres ce controle.

Reprise apres comparaison avec la maquette:

- les onglets affichent des reperes numerotes pour mieux ressembler a une navigation cockpit;
- la colonne `Pilotage` affiche maintenant une priorite metier visible dans le premier ecran;
- les passerelles sont visibles directement dans la colonne de droite, et plus seulement dans l'onglet `Diffusion`;
- la synthese garde les cartes operationnelles sous le hero pour le detail, mais les signaux critiques sont remontes dans le premier viewport.

Correction ordre maquette:

- le bloc fixe `photo + infos rapides` repasse au-dessus des 7 boutons;
- la colonne `Pilotage` reste alignee a droite du bloc principal;
- les boutons de navigation arrivent sous le bloc principal, comme dans la proposition visuelle.

Correction densite popup:

- le probleme principal restant etait l'echelle visuelle: titre, boutons, cartes et colonne droite etaient trop gros dans la popup reelle;
- la largeur de la popup, la grille cockpit, les hauteurs de photos, les tailles de boutons et les cartes d'information ont ete resserrees;
- l'objectif est que le premier viewport montre le bloc photo/infos, le pilotage, les passerelles et les 7 boutons sans effet de maquette agrandie.

Correction structure head pleine largeur:

- la grille detail place maintenant `photo + infos rapides` et `Pilotage` sur la premiere ligne du cockpit;
- les 7 boutons de navigation occupent la ligne suivante sur toute la largeur de la popup;
- le contenu d'onglet demarre sous cette navigation, ce qui reprend la structure de la maquette.

Correction position Pilotage:

- apres controle visuel, `Pilotage` ne doit pas etre au-dessus des menus;
- le head pleine largeur contient uniquement `photo + infos rapides`;
- les 7 boutons restent sous le head sur toute la largeur;
- `Pilotage` demarre ensuite dans la zone contenu, a droite de l'onglet actif.

Alignement maquette de reference:

- le header detail est redevenu compact, avec miniature et informations principales;
- les onglets prennent un style de petits tabs sobres avec accent turquoise;
- la colonne droite redevient une colonne claire `Actions rapides`, et non un bloc sombre de pilotage;
- les couleurs reviennent vers la reference: fond blanc, lignes gris clair, accent turquoise, badges et passerelles colorees;
- la photo grand format ne doit plus dominer le head fixe.

Correction header maquette:

- les informations rapides `prix`, `surface`, `dossier` et `mandat` sont placees a droite du header compact;
- la miniature reste a gauche et le titre/adresse/agence au centre;
- le header correspond davantage a la reference fournie, avec les infos principales sur une seule bande compacte.

Correction integration Actions rapides:

- le menu `Actions rapides` ne partage plus la meme zone de grille que le contenu de l'onglet actif;
- la fiche detail utilise maintenant des zones explicites: `head`, `tabs`, `main`, `side`;
- le header compact et les onglets restent pleine largeur;
- le contenu principal et la colonne actions demarrent ensuite cote a cote, sans superposition;
- en mobile, ces zones sont empilees dans l'ordre `head`, `tabs`, `main`, `side`.

Correction comportement du panneau Actions rapides:

- le panneau `Actions rapides` n'est plus `sticky`;
- il reste dans le flux normal de la grille, aligne avec le contenu de l'onglet actif;
- objectif: eviter tout effet de panneau flottant qui passe au-dessus des autres blocs pendant le scroll.

Convergence maquette 7 pages:

- les pages `Diffusion` et `Historique` ne sont plus rendues dans le panneau `Actions rapides`;
- elles reprennent la zone principale de la fiche, comme les autres onglets;
- `Actions rapides` redevient uniquement une colonne d'accompagnement;
- l'onglet `Contenu annonce` ajoute une grille photos au-dessus du descriptif;
- l'onglet `Diffusion` affiche aussi les dernieres demandes dans une table compacte;
- les cartes sont resserrees avec des rayons plus courts pour se rapprocher de la maquette fournie.
