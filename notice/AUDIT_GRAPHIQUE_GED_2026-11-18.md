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

## 7. VERSION 2 (18/11 après-midi) — ses quatre retours

> *« Ajoute plus de cas, pas uniquement le compromis : aussi un scan de plusieurs documents que l'IA découpe d'abord,
> puis ces fenêtres. On a décidé que désormais toutes les corrections sont réellement faites dans l'app, on n'attend
> plus la période de test : ton visuel avec « à valider » me fait douter. Rehausse encore le niveau visuel, plus
> moderne, mais garde le principe. La liste des documents doit rester facilement visible : moins de place, des
> boutons à déplier. Je veux un vrai travail de société missionnée. »*

**1. Plus de cas — une histoire suivie, sur le même bien (18849, au compromis)** : le vendeur envoie un scan de 9 pages.
- 2a : la fenêtre de dépôt voit **3 pièces** (« Ce fichier réunit 3 pièces : taxe foncière (p. 1 à 2), titre de
  propriété (p. 3 à 7), DPE (p. 8 à 9) ») — l'aperçu montre les **9 pages, chacune marquée de sa pièce** ;
  « Séparer en 3 fichiers » ;
- 2b : 3 lignes « Scan dossier vendeur - partie 1 / 2 / 3 », type proposé par l'IA, à vérifier (c'est ce que fait le
  code : `separer`, DepotDocuments.tsx l. 386) — les feuilles tombent en éventail ;
- 2c : envoyés ; « L'IA lit les valeurs… », puis la feuille de chaque pièce se remplit (année et montant de la taxe ;
  vente du 12/05/2011, 2 propriétaires ; classes, consommation, date du DPE) ;
- 3a « Ce que dit le compromis » (corriger la transaction) et **3b « Ce que dit le DPE » (remplir la fiche)** — un même
  composant, ses deux destinations ; « Enregistrer » montre le résultat écrit, pour de vrai.

**2. Le doute « à valider » — tranché par le vocabulaire et par une fusion d'affichage** :
- plus aucun mot d'essai : chaque carte dit **où part la correction** (« part chez Hektor », « sur la fiche, puis chez
  Hektor ») et le panneau le dit en tête : « Chaque correction s'écrit pour de vrai, là où elle le dit » ;
- les boutons disent le geste : « Voir et corriger » (une valeur qui diffère), « Voir et ajouter » (une case vide) —
  ⚠ CHANGEMENT DE TEXTE (aujourd'hui « Voir et trancher ») ;
- **l'alerte liée à une ligne de la fenêtre n'a plus sa propre carte** : son jugement se déduit déjà du choix
  (`verdictDesChoix`, « plus de double clic » depuis le 17/11) ; la carte du compromis le dit (« l'alerte liée se note
  d'elle-même »). Sur 62850, la même date apparaissait DEUX fois (« À remplir » et « À regarder »), c'est ce doublon qui
  faisait « validation de test ». ⚠ CHANGEMENT D'AFFICHAGE, à trancher ;
- les alertes SANS fenêtre gardent « Vrai / Faux / Déjà su », en petit, sous le titre « Noter l'alerte » : c'est la
  mesure du morceau 10, en production jusqu'au 30/11. ⚠ **À TRANCHER PAR FRÉDÉRIC : la garder après le 30/11, ou la
  retirer** (si « on n'attend plus la période de test », elle n'a plus d'objet).

**3. Plus moderne, même principe (la feuille qui se remplit)** : surfaces blanches à ombre douce sur fond pierre,
segments à la iOS pour les filtres et onglets, barres de progression des moments, **le panneau « À traiter » en encre**
(le langage des fenêtres de dépôt et de bilan, qui ont déjà un bandeau encre) avec ses accents magenta, la feuille de
papier gardée pour tout ce que l'IA a lu, typographie resserrée (Plus Jakarta Sans 800 / Hanken Grotesk), chiffres
tabulaires.

**4. La liste des documents toujours visible — c'est le changement d'ergonomie majeur** :
- **la liste DEVIENT le dossier** : les documents sont rangés sous les pièces attendues, par moment (Compromis, Offre,
  Mise en vente, Prise de mandat), plus « Autres documents » pour ceux qui ne correspondent à aucune pièce ; chaque
  moment se **déplie** (le moment en cours ouvert, les autres repliés) ;
- une ligne par document (56 px) : sa pièce, deux valeurs lues, son état ; **un clic la déplie** : la feuille avec tout
  ce que l'IA a lu, et les gestes Ouvrir, Signature, Supprimer, Revoir ce qu'il dit — les boutons ne prennent plus de
  place sur chaque ligne ;
- les pièces manquantes sont des lignes « Déposer » à leur place, plus un mur de tuiles ; « selon le cas » et « bonne
  pratique » tiennent en une ligne chacun ;
- les filtres À préparer / Signés / Cloud passent la liste à plat (comme aujourd'hui) ; « Tous » montre le dossier rangé.
- Effet mesuré sur la maquette : au compromis de 62850, le bloc « Le dossier » + la liste tenaient sur ~2,5 hauteurs
  d'écran ; ici, moments + liste du moment en cours + « À traiter » tiennent sur ~1.

**Anti-perte, ce qui change par rapport au §6** : les feuilles et l'ancienne liste fusionnent (mêmes informations, mêmes
gestes, à un clic) ; « Lu par l'IA » est remplacé par les valeurs sur chaque ligne et la feuille dépliée ; les boutons
« Voir et trancher » sont renommés ; la carte d'alerte liée à une fenêtre disparaît (son jugement reste, déduit).
Maquette, côté démonstration seulement : « Rejouer l'arrivée » et le clic « Voir et ajouter » qui fait voler la valeur
dans la case (dans l'app, ce vol suit l'enregistrement de la fenêtre).

## 8. VERSION 3 (20/11) — « rehausser le niveau, c'est un peu vieux » ; la période de test retirée

> *« Le niveau graphique et le design peuvent être rehaussés car c'est un peu vieux ; ensuite cette maquette doit
> s'adapter comme le point 6 : désormais tout est corrigé directement, il faut retirer la période de test. »*

Même toile, mêmes quatre écrans réécrits en place (`Main`, `Bilan`, `Depot`, `Telephone` ; les écrans 2b, 2c et 3b les
reprennent) : https://claude.ai/artifact/VxtNCjmAVXkThs641fHX1z

**Le parti pris graphique** : la charte bienvu, rien d'autre -- UNE police (Plus Jakarta Sans, celle de la charte, au lieu
du couple Plus Jakarta / Hanken Grotesk) et UN magenta (#C5005F). Le papier beige, les coins cornés et les bandeaux
encre sont retirés : surfaces blanches sur un fond gris froid très clair, ombres douces, rayons réguliers. Chaque document
est une petite page blanche avec une bande de couleur par famille (vente magenta, diagnostics bleu, propriété ambre,
fiscalité vert). Les valeurs lues sont des pastilles sur la ligne, et la feuille dépliée devient une grille « Ce que l'IA
a lu ». Le moment en cours a un anneau de progression (3 sur 10) ; les moments finis, une coche verte.
**L'élément fort** : « À traiter » ouvre sur un bloc magenta plein avec le NOMBRE en grand ; les cartes sous lui sont
blanches. Une correction se lit « avant barré -> après en magenta ».
**« Ce que dit… »** : en-tête clair ; deux choix côte à côte (« Le compromis dit » / « La transaction dit »), boutons radio,
« sera corrigé » / « reste tel quel » ; la page du document s'ouvre D'OFFICE à la première ligne (point 2 du §5).

**La période de test retirée (point 6, décision de Frédéric du 20/11)** : plus de « Vrai / Faux / Déjà su », plus de
« Noter l'alerte ». Une alerte sans fenêtre devient un « Point d'attention » avec SES gestes (« Voir le titre »,
« Déposer un pouvoir ») et un « Masquer » discret (« 1 point d'attention masqué, Réafficher »).
⚠ **« Masquer » est une PROPOSITION de la maquette** : aujourd'hui, c'est le jugement qui range une alerte. Sans jugement,
il faut un geste pour l'écarter -- à confirmer par Frédéric, et à décider : la table `app_ged_jugement` garde-t-elle ce
« masqué », ou une autre trace ?

**Restent à trancher** (§5) : 1 « À préparer » sur les documents non destinés à la signature ; 3 le bouton « Remplir la
transaction » ; 4 « Voir et trancher » -> « Voir et corriger / Voir et ajouter » (la maquette le montre) ; 5 l'alerte en
double d'une ligne de fenêtre (la maquette ne la montre plus). Rien n'est codé.

**V3.1 (20/11, « problème de mise en page, les boutons dépassent ; as-tu ajouté des animations dynamiques ? »)** :
- **Corrigé, vu à l'écran dans son Chrome** : les « Déposer » sortaient du cadre (une ligne `div` en `width:100%` + marges
  intérieures, sans `box-sizing:border-box` -> 72 px de trop ; règle posée sur les quatre écrans) ; au téléphone, la liste du
  Compromis était ÉCRASÉE à zéro de hauteur (enfant `overflow:hidden` d'une colonne flexible -> `flex-shrink:0`) ; la date du
  DPE tronquée ; l'aperçu des 9 pages qui passait à la ligne ; « Taille : partie 2.pdf » (lu au mauvais endroit).
- **Les animations, chacune répond à un geste ou raconte l'arrivée** (toutes coupées par `prefers-reduced-motion`) :
  l'arrivée -- les traits des moments se tracent, les coches sautent, l'anneau du Compromis se remplit, le compteur
  « À traiter » monte 1, 2, 3, un reflet passe sur le bloc, les cartes arrivent en cascade, un faisceau balaie la miniature
  des pièces qui viennent d'être lues ; « Voir et ajouter » -- chaque valeur vole dans SA case l'une après l'autre, la case
  passe au vert, la carte devient « 3 ajoutées » avec une coche tracée et le compteur descend ; « Masquer » -- la carte glisse
  et se replie ; le dépôt -- le scan tombe dans la liste, « Séparer » pulse, les 9 pages s'écartent en 3 groupes, l'envoi
  remplit une barre fichier après fichier, « Déposé » saute, les valeurs lues apparaissent une à une ; « Ce que dit… » --
  les lignes arrivent en cascade, la coche du choix saute, la page tourne quand on change de ligne, « Enregistrer » passe
  en « Envoi… » puis la coche se trace ; au survol, les cartes se soulèvent.
- **Les écrans s'enchaînent en lecture** : « Ajouter un document » ouvre le dépôt, « Voir et corriger » ouvre « Ce que
  dit le compromis », « Fermer » revient au dossier.
