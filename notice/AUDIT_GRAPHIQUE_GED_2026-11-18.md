# AUDIT GRAPHIQUE ET ERGONOMIQUE — LES ÉCRANS DE LA GED (18/11/2026)

> Demande de Frédéric (18/11) : *« l'outil est performant et utile mais l'ergonomie et le design général ne le montrent
> pas. Il faut un audit graphique d'expert puis fais-moi une maquette optimisée ; pense aux animations dynamiques, effets
> graphiques et design. »*
> Méthode (mémoires « refonte design », « raisonnement métier avant graphisme », « design = mêmes contenus ») : écrans vus
> EN PRODUCTION dans sa session Chrome (1280 × 665) sur deux cas réels contrastés, sans rien envoyer ; inventaire exact du
> code (textes et gestes) ; diagnostic métier PUIS graphisme ; ce qui change un comportement est rangé à part, « à
> trancher ». Rien n'est codé. Maquette : https://claude.ai/artifact/VxtNCjmAVXkThs641fHX1z
> Chantier : `notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md`.

## 1. Les écrans audités

- **L'onglet Documents de la fiche** (cockpit, `ConsoleDocumentsPanel`, App.tsx l. 11923) : en-tête « Documents », bouton
  « Ajouter un document », puis **« Le dossier »** (`RecuManque.tsx`, 727 l.) — les 4 moments, les feuilles des pièces,
  « À remplir », « À regarder », « La fiche du bien », « Voir le document », « Lu par l'IA » — puis **l'ancienne liste**
  des documents (filtres Tous / À préparer / Signés / Cloud, cartes Ouvrir / Signature / Supprimer).
- **La fenêtre « Déposer des documents »** (`DepotDocuments.tsx`, 907 l.) et son panneau photo du téléphone.
- **La fenêtre « Ce que dit le compromis »** et ses 6 variantes (`BilanCompromis.tsx`, 371 l.).
- Cas réels regardés : **62850** (sous compromis, 20 documents, le compromis lu, 1 à trancher, 1 alerte) et **59541**
  (mise en vente, 24 documents, un avenant lu, 1 alerte).

## 2. Ce que l'utilisateur vient faire (diagnostic métier)

1. **Savoir si le dossier est complet pour le moment de la vente** — c'est la promesse de « Le dossier ».
2. **Déposer, vite, en lot** — la fenêtre de dépôt le fait bien.
3. **Traiter ce que l'IA a trouvé** — trancher un écart, remplir une case, juger une alerte. C'est LA valeur du chantier :
   l'outil a LU les documents et confronté leur contenu au registre et à la fiche.
4. **Retrouver et ouvrir un document** — l'ancienne liste.

L'écran actuel montre ces quatre besoins **dans l'ordre inverse de leur valeur** : la grille des pièces d'abord (et
surtout ce qui MANQUE), le travail de l'IA ensuite en petit, et ce que l'IA a lu replié dans une pastille grise tout en
bas. **C'est pour ça que l'outil « ne se voit pas » : son intelligence est rangée sous un mur d'alertes.**

## 3. Les constats d'expert (mesurés ou vus)

1. **Le mur rose.** Sur 62850, au moment « Compromis » : 9 feuilles « Non trouvée : déposer » hachurées rose pour 1
   reçue. « Obligatoire », « selon le cas » et « bonne pratique » ont **le même traitement** : rien ne dit ce qui compte.
   Le magenta sert à la fois à l'action principale, à l'étape en cours ET au manque : il ne veut plus rien dire.
2. **La feuille reçue ne montre pas ce qu'elle contient.** Elle affiche un nom de fichier tronqué (« Copie AAE
   PROMESS… ») ; ce que l'IA y a lu (signé le 23/10, 124 000 €, acte au plus tard le 01/02/2027…) n'apparaît que dans une
   phrase repliée, ses morceaux joints par « · ».
3. **Le travail de l'IA est en bas, et en gris.** « À remplir » et « À regarder » sont sous la grille, en deux styles de
   cartes différents (étiquette bleue d'un côté, rouge de l'autre), et « Lu par l'IA : 1 document » est une pastille grise
   fermée par défaut.
4. **Deux langages visuels sur une page.** Le bloc GED (encre #1F2121, magenta, Plus Jakarta Sans / Hanken Grotesk, tout
   en dur — **aucune variable `--bv-*`**) et l'ancienne liste (bouton indigo « Ajouter un document », étiquettes en
   CAPITALES « DOCUMENT », pastilles beiges « À préparer »). Trois couleurs « primaires » se battent : indigo, magenta,
   vert.
5. **Le bruit des états dans la liste.** Sur les biens vivants, **5 887 documents sur 22 188 (27 %)** affichent « À
   préparer » + « À envoyer en signature » (statut par défaut `to_send`) — sur 59541, **23 sur 24**. Un état que
   presque tout le monde porte ne dit plus rien ; il couvre les 368 vrais signés.
6. **Trois niveaux de titres en concurrence** : « Documents » (titre de panneau + sous-titre « synchronisé avec Hektor »),
   « Le dossier » (avec une phrase d'aide), puis « À remplir (1) » / « À regarder (1) » au même poids que « Le dossier ».
7. **Les animations sont partout, donc nulle part** : entrées décalées sur chaque feuille (70 ms), chaque carte (80 ms),
   chaque alerte (120 ms + 80 ms), chaque ligne de fenêtre (60 ms), plus scintillements et icône qui flotte en boucle.
   La SEULE animation qui raconte quelque chose — **le vol de la valeur vers sa case** — se perd dans le lot.
8. **La fenêtre « Ce que dit… » a la bonne idée et un défaut de rendu.** Les deux plaques face à face (le document / la
   transaction) sont la meilleure trouvaille du chantier. Mais : la colonne de droite (340 px) est **vide par défaut**
   (« Touche « page » sur une ligne ») ; et **le style « papier » de la plaque du document ne s'applique jamais** (la CSS
   vise `.bc-plaque.is-compromis`, le code pose `is-document` — BilanCompromis.tsx l. 235) : rien ne distingue
   visuellement « ce que dit le papier » de « ce que dit le registre ».
9. **La fenêtre de dépôt est le meilleur écran** (bandeau encre, liste + aperçu, badges d'état, bande « pas fini ») : à
   garder, à aligner sur le reste.
10. **Hors GED, vu en passant** : le fil d'Ariane **accumule les biens visités** (« Annonces › #63331 › 18849 › EA32610 »
    en ouvrant 59541) — défaut de navigation, à traiter à part.

## 4. Le parti pris de la maquette

- **UN élément fort, propre au sujet : la FEUILLE QUI SE REMPLIT.** La phrase est déjà à l'écran (« Une pièce arrive, sa
  feuille se remplit ») : la maquette la rend littérale. Une pièce reçue est une vraie feuille de papier qui porte **2 ou
  3 valeurs lues** (date, montant, échéance) ; à l'arrivée d'une lecture, ces lignes **s'écrivent** sur la feuille et
  l'anneau du moment avance. C'est la seule animation orchestrée.
- **Le travail de l'IA monte en tête** : « À traiter » réunit « À remplir » et « À regarder » (mêmes cartes, mêmes
  gestes, un seul langage), juste sous les moments.
- **Le manque se hiérarchise** : les pièces **obligatoires** restent des feuilles vides (contour net, « Déposer ») ;
  « selon le cas » et « bonne pratique » deviennent une liste courte et calme. Plus de hachures roses.
- **Une couleur, un sens** : magenta = l'action et le moment en cours ; vert = reçu / d'accord ; ambre = à trancher ;
  framboise = erreur. L'indigo disparaît.
- **Animations qui répondent à un geste** : la feuille déposée se pose dans sa case ; « Remplir la fiche » garde son vol ;
  trancher fait basculer la plaque prise au premier plan ; juger « Vrai / Faux / Déjà su » replie la carte.
  `prefers-reduced-motion` coupe tout.
- **Mêmes contenus, mêmes gestes** : tableau anti-perte au §6.

## 5. À TRANCHER — ce qui changerait un COMPORTEMENT (pas dans la maquette par défaut)

1. Ne plus afficher « À préparer / À envoyer en signature » sur un document qui n'a pas vocation à être signé (27 % des
   documents vivants le portent).
2. Ouvrir la page du document D'OFFICE dans « Ce que dit… » (la première ligne à trancher), au lieu d'une colonne vide.
3. Retirer le bouton mort « Remplir la transaction » (le geste est toujours refusé, App.tsx l. 12011).
4. Corriger la classe de la plaque « papier » (`is-compromis` -> `is-document`) — défaut de rendu, sans risque.
5. Le fil d'Ariane qui accumule les biens (hors GED).

## 6. Anti-perte — chaque information et chaque geste d'aujourd'hui, et sa place dans la maquette

- « Ajouter un document » -> bouton principal magenta de l'en-tête du dossier (même geste : ouvre la fenêtre de dépôt).
- Les 4 moments (pastille, « x pièces sur N », « complet », « N non trouvées », clic sur un moment passé) -> le rail des
  moments, avec un anneau ; mêmes états, même clic.
- Feuille reçue (coche, cadenas des pièces privées, « Dans un dossier de diagnostics », noms, « (+N) », info-bulle) ->
  la feuille de papier, qui affiche EN PLUS les valeurs déjà lues (le résumé de lecture existant, mis en lignes).
- Feuille non trouvée « Non trouvée : déposer » + niveau + pourquoi -> obligatoires : feuille vide « Déposer » ; selon le
  cas / bonne pratique : liste « À prévoir » avec le même bouton « Déposer ».
- Feuille « selon le cas » (« La fiche ne dit pas si elle est due ») -> même liste « À prévoir », même texte.
- « À remplir (N) » : carte « Ce que dit… » + « Voir et trancher » ; carte proposition (« Fiche : vide », « lu dans »,
  « Remplir la fiche », « Ignorer », « Voir le document ») ; décisions repliées -> « À traiter », groupe « À remplir »,
  mêmes boutons.
- « À regarder (N) » (Alerte / Pièce / Info, pourquoi, « Déposer la pièce », Vrai / Faux / Déjà su, « Jugé … le … ») ->
  « À traiter », groupe « À regarder », mêmes gestes.
- « La fiche du bien » (les cases, « vide », l'allumage, la note) et « Voir le document » (page, croix, erreurs) ->
  colonne de droite de « À traiter », inchangés dans leurs contenus.
- « Lu par l'IA : N · N refusés » + « Revoir ce qu'il dit » + « C'est bien ce type : garder la lecture » -> les valeurs
  sont sur les feuilles ; la liste complète reste, dépliable, sous les feuilles.
- L'ancienne liste (Tous / À préparer / Signés / Cloud ; nom, type, Privé, taille, état ; Ouvrir / Signature /
  Supprimer) -> « Tous les documents », en lignes compactes, mêmes filtres et mêmes trois boutons.
- Fenêtre de dépôt (tous ses états, badges, aperçu, bande « pas fini », panneau photo) -> même structure, recolorée.
- Fenêtre « Ce que dit… » (groupes, plaques, verbes, « page N », notes, « Changer », pied, « Enregistrer… ») -> même
  structure ; la plaque du document en papier ; la page lue surlignée.
