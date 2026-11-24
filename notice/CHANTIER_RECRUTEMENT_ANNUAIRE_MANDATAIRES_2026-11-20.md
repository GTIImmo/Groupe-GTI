# Chantier à part — RECRUTEMENT : l'annuaire des mandataires

> **Ouvert le 20/11/2026 à la demande de Frédéric.** Hors du plan d'autonomie, **aucun lien
> avec Hektor**. Distinct du « site de recrutement » du 22/10 (mémoire `projet-site-recrutement`),
> qui reste en attente : ici on parle de **trouver** les candidats, pas de les **accueillir**.
>
> **État : CADRAGE.** Rien n'est codé, aucune table n'existe, aucune collecte n'a tourné.
> Seule une sonde de lecture a été faite (une dizaine de pages publiques, à la main).

---

## 1. La demande, dans ses mots

Une rubrique annexe **« Recrutement »** dans l'app : la liste de **tous les candidats possibles
pour devenir agent commercial chez nous**.

- **Étape 1** : constituer la liste en **parsant les annuaires de mandataires**, **sans téléphone
  ni e-mail** — uniquement nom, prénom, secteur, etc. Une **vue « Recrutement »** dans l'app
  avec **tous les filtres**.
- **Étape 2** (plus tard) : comment récupérer téléphone et e-mail. *« À voir après. »*

---

## 2. Ce que la sonde du 20/11 a mesuré

### Les réseaux, un par un

- **iad France** — **16 038 conseillers** dans un plan de site public
  (`/sitemap/fr/agents.xml`, mis à jour chaque nuit). Les fiches
  `/conseiller-immobilier/<prenom.nom>` sont **autorisées** par le robots.txt (seuls `/agent/*`,
  `/conseiller/*`, `/consultant/*` sont interdits, et le robot nommé « Scrapy »). Une fiche
  donne : nom complet, commune, code postal, **n° RSAC + ville du RSAC**, nombre d'avis et note,
  nombre d'annonces. Le téléphone est **masqué** (haché, révélé au clic).
  ⚠ **Mentions légales iad** : « l'ensemble des données (textes et images) » du site sont déclarées
  propriété exclusive d'iad, toute exploitation « en partie ou en totalité » interdite.
- **SAFTI** — **6 568 conseillers** dans un plan de site public
  (`/sitemaps/sitemap.mandataires.xml`, déclaré dans le robots.txt). Une fiche
  `/votre-conseiller-safti/<prenom-nom>` donne : prénom, nom, commune, code postal,
  **coordonnées GPS**, **n° RSAC + ville**, secteurs couverts, distinction « Club Excellence ».
  ⚠ **Le téléphone et l'e-mail y sont écrits en clair** (données structurées de la page) :
  l'étape 1 devra **volontairement ne pas les lire**.
- **Capifrance** et **Optimhome** (même plateforme) — `Disallow: /nos-conseillers`,
  **`Crawl-delay: 20`** (20 s entre deux pages). Capifrance publie **1 930 pages par commune**
  (`/fr/conseillers/<commune>_<dept>`) dans son plan de site. Fiche non encore ouverte.
- **Efficity** — **refuse tous les robots** sauf les moteurs de recherche nommés
  (`User-agent: *` → `Disallow: /`). **À exclure.**
- **Megagence** — robots ouvert (`Allow: /`, réserve « pas d'entraînement d'IA »). Non sondé plus loin.
- **Expertimo** — robots ouvert. Non sondé plus loin.
- **Propriétés-privées, BSK** — le robots.txt n'a pas répondu (blocage probable). Non mesuré.
- **Non sondés** : eXp France, Keller Williams, Sextant, Dr House Immo, 3G Immo, Lafourmi…

### La découverte qui compte : le n° RSAC est un SIREN

Le numéro RSAC affiché sur chaque fiche (obligation légale de l'agent commercial) **est son
SIREN**. Essai fait : `530 547 108` → API publique **Recherche d'entreprises**
(`recherche-entreprises.api.gouv.fr`, données ouvertes de l'État, Licence Ouverte) → nom,
**code NAF 68.31Z**, **date de création 2011-03-01**, **état actif**, nature 1000 (EI).

Ce que ça permet :

1. **Dédoublonner entre réseaux** : un même SIREN vu chez iad puis chez SAFTI = la même personne
   qui a **changé de réseau**.
2. **L'ancienneté réelle** (date de création de l'entreprise individuelle), pas celle déclarée.
3. **Savoir s'il exerce encore** (état actif / cessé).

### Les signaux de recrutement qu'on obtient gratuitement en repassant chaque semaine

- **Nouveau dans un réseau** (fiche apparue depuis le dernier passage).
- **Disparu d'un réseau** (fiche retirée du plan de site) → il part, ou il est parti : le
  meilleur moment pour l'appeler.
- **Passé d'un réseau à l'autre** (même SIREN, deux réseaux).
- **Son activité** : nombre d'annonces, d'avis, distinction (Club Excellence).

---

## 3. Ce que je propose — à valider, rien n'est décidé

### 3.1 La collecte (hors de l'app, sur le PC serveur)

- Un script Python à part, **`recrutement/collecte_annuaires.py`**, un « adaptateur » par réseau.
- Il part du **plan de site** de chaque réseau (pas de navigation dans les moteurs de recherche
  internes), lit **une page toutes les 3 s** au plus (20 s pour Capifrance/Optimhome),
  **respecte le robots.txt**, **reprend où il s'est arrêté**, **écrit au fil**
  (cf. mémoire « mesure longue : découpée, écrite au fil »).
- Il ne garde **que** : réseau, adresse de la fiche, prénom, nom, commune, code postal,
  département, coordonnées GPS (ou celles de la commune), SIREN + ville du RSAC, nombre
  d'annonces, nombre d'avis + note, distinction, **date de première vue**, **date de dernière vue**.
  **Ni téléphone, ni e-mail, ni photo, ni texte de présentation.**
- Puis l'enrichissement par le SIREN (API ouverte de l'État) : date de création, état actif.
- Il écrit dans un fichier local, puis pousse vers **une table Supabase dédiée**.

### 3.2 La base

- **Une table neuve**, sans aucun lien avec les tables Hektor : `rec_candidat` (une ligne par
  personne, clé = SIREN quand on l'a) + `rec_fiche_reseau` (une ligne par fiche dans un réseau,
  pour garder l'historique des changements de réseau) + `rec_suivi` (nos notes : statut
  « à contacter / contacté / intéressé / pas intéressé / recruté / **ne plus contacter** »,
  commentaire, qui suit).
- **Lecture réservée aux administrateurs** par RLS. ⚠ Leçon déjà payée : `revoke from public`
  ne ferme pas `authenticated` — à vérifier explicitement (mémoire
  `revoke-from-public-ne-ferme-pas-authenticated`).

### 3.3 La vue « Recrutement »

- Même modèle que l'écran **Pilotage** (`PilotageScreen.tsx`) : un écran à part
  `RecrutementScreen.tsx`, une valeur `'recrutement'` dans le type `Screen` d'`App.tsx`
  (l. 431), une entrée de menu à côté de « Pilotage » (l. 27255 et 27260), l'adresse
  `?ecran=recrutement` (l. 14350-14354), **réservé admin** comme Pilotage (l. 22818).
- Filtres proposés : réseau · département · commune · **rayon en km autour d'une agence GTI** ·
  nombre d'annonces mini · ancienneté (date de création SIREN) · nouveau / parti / a changé de
  réseau · distinction · statut de suivi · recherche par nom.
- Une fiche à droite : ce qu'on sait, le lien vers sa page publique, nos notes, le statut.
- Export CSV.

### 3.4 Ce que ça touche, ce qui pourrait casser ailleurs

- **Additif** : un dossier `recrutement/` neuf, des tables neuves préfixées `rec_`, un
  composant neuf. **Rien du run de nuit, des workers, ni de Hektor.**
- **Seul code existant modifié** : `App.tsx`, à 5 endroits (type `Screen`, deux tables
  d'adresses, le routage, le menu). Risque : une faute de frappe qui casse le build →
  vérifié par `npm run build`.
- **Retour arrière** : retirer l'entrée de menu ; supprimer les tables `rec_*`.
- **Écriture en base de production** (création des tables) et **déploiement** :
  accord obligatoire (§0).

---

## 4. Les points juridiques — à trancher par Frédéric, pas par moi

1. **Droit du producteur de base de données** (art. L342-1 du Code de la propriété
   intellectuelle) : extraire une **partie substantielle** d'un annuaire est interdit même si
   chaque page est publique (jurisprudence Leboncoin c/ Entreparticuliers, 2021). Aspirer
   **les 16 000 fiches d'iad** est exactement ce cas ; **se limiter à une région** réduit
   fortement le risque. Les mentions légales d'iad interdisent toute exploitation.
2. **RGPD** : nom + commune d'un agent commercial = donnée personnelle, même professionnelle.
   Possible au titre de l'**intérêt légitime** (prospection B2B liée à la profession), à
   condition de : collecter le **minimum**, **informer la personne au plus tard au premier
   contact** (art. 14 : d'où vient la donnée, son droit d'opposition), tenir une liste
   « **ne plus contacter** » respectée par la collecte suivante, **effacer** au bout de 3 ans
   sans contact, inscrire le traitement au registre de GTI. La CNIL a sanctionné une société
   pour ce type de collecte faite sans information (KASPR, 240 000 €, 2024).
3. **Ne jamais contourner une protection** : le téléphone masqué d'iad n'est pas à lire.

---

## 5. Étape 2 — pistes seulement, à voir après (demande de Frédéric)

- La **page publique du réseau** affiche parfois le contact en clair (SAFTI) ; iad le cache.
- Le **format d'adresse e-mail professionnelle** du réseau (souvent `prenom.nom@reseau.fr`).
- Des **services d'enrichissement** (certains français et déclarés conformes RGPD).
- **LinkedIn** à la main ; ou l'inverse : les faire venir (le site de recrutement du 22/10).
- Dans tous les cas : message lié à la profession, lien de désinscription, information art. 14.

---

## 6. Questions à Frédéric

1. **Périmètre géographique** : France entière (~23 000 fiches iad + SAFTI seuls, plusieurs
   nuits de collecte, risque juridique maximal) **ou** notre région (Loire et départements
   voisins : quelques centaines à 2 000 fiches, collecte en une heure, risque faible) **ou**
   un rayon en km autour de nos agences ?
2. **Quels réseaux** : iad + SAFTI d'abord (plans de site propres) puis Capifrance/Optimhome,
   puis les autres ? Efficity exclu (refuse les robots).
3. **Qui voit la rubrique** : administrateurs seulement, ou aussi les responsables ?
4. **Le cadre juridique** : OK pour la règle « minimum + information au 1er contact + liste
   ne-plus-contacter + effacement à 3 ans » ? Faut-il un avis de votre conseil avant la
   première collecte ?
5. **Fréquence** : une collecte à la main d'abord, puis chaque semaine (pour voir qui arrive
   et qui part) ?

---

## 7. Réponses de Frédéric (20/11, 2e message) et ce qu'elles ont permis de mesurer

> *« notre région d'abord IAD SAFTI KELLER WILLIAMS pour commencer ensuite on utilise les outils
> déjà en place ? »*

- **Périmètre** : notre région d'abord. **Réseaux** : iad, SAFTI, Keller Williams.
- **Restent ouvertes** : les questions 3 (qui voit la rubrique), 4 (cadre RGPD), 5 (fréquence).

### « Notre région » = les 4 départements de nos 17 agences

Lu dans `app_registre_agence` (17 agences actives) : **Loire (42)** Firminy, Montbrison,
Saint-Bonnet-le-Château, Saint-Étienne, Saint-Just-Saint-Rambert · **Haute-Loire (43)** Brioude,
Craponne-sur-Arzon, Dunières, Le Puy-en-Velay, Monistrol-sur-Loire, Saint-Didier-en-Velay, Tence,
Yssingeaux · **Puy-de-Dôme (63)** Ambert, Courpière, Issoire · **Ardèche (07)** Annonay.
⚠ Les colonnes adresse / CP / ville du registre des agences sont **vides** : la position d'une
agence viendra de sa commune (table `ref_commune_geo`, qui existe déjà : CP, commune, lat/lon,
département).
Proposition : **collecter les 4 départements entiers**, puis l'écran filtre par **distance à
l'agence GTI la plus proche** (Clermont-Ferrand est en 63, Privas en 07 : le filtre de distance
les écartera si on veut).

### Ce que chaque réseau donne pour la région (sonde du 20/11)

- **iad** : les pages département sont autorisées et paginées (`?page=N`, ~15 par page) —
  **Loire 139 · Puy-de-Dôme 87 · Ardèche 74 · Haute-Loire 21 = 321 conseillers** (2 % de
  l'annuaire national). ~25 pages de liste + 321 fiches.
- **SAFTI** : pas de page département (`/trouver-un-conseiller/loire-42` est compris comme la
  commune de Caloire). Les pages **par commune** portent dans leurs données la liste « dans la
  commune » + « aux alentours », **complète** (essai Caloire : 1 + 11, sans pagination), avec
  commune, CP, GPS, **nombre d'annonces**, note Google. ⇒ interroger une grille de communes
  couvrant les 4 départements, unir par identifiant. Estimation : **~130 conseillers** (au
  prorata iad), ~100 pages de commune + les fiches pour le RSAC.
- **Keller Williams France** (`kwfrance.com`) : robots ouvert, **`Crawl-delay: 5`**, plan de site
  avec **205 conseillers seulement** (le réseau est petit en France). **2 agences dans la région** :
  KW FOREZ (Saint-Étienne) et KW ARVERN (Clermont-Ferrand). La fiche donne le nom et le **RSAC**
  (SIREN), **pas la commune** ⇒ la commune viendra du SIREN (API ouverte de l'État). 205 fiches
  × 5 s = ~17 min. ⚠ Le téléphone y est aussi en clair : ne pas le lire.

**Total attendu : ~450 à 500 personnes, ~650 pages, ~50 min de collecte.**

### Les outils déjà en place qu'on réutilise

- **Python** et le chargement du `.env` comme les scripts de `phase2/sync/`.
- **Les tâches planifiées Windows** (`scheduled/*.ps1`) pour le repassage — ⚠ une tâche neuve se
  **déclare à la surveillance AVANT** d'être enregistrée (règle du §2 de `CLAUDE.md`).
- **Supabase**, même projet : tables neuves `rec_*` posées par **patch + répétition + inverse**
  collés par Frédéric (patron du projet ; l'outil refuse d'écrire en production).
- **`ref_commune_geo`** (positions des communes) et **`app_registre_agence`** (nos 17 agences).
- **L'écran Pilotage** comme modèle, la feuille de style commune, `npm run build`, Vercel qui
  déploie seul au push.
- **Ce qui est neuf** : les 3 adaptateurs (un par réseau), les tables `rec_*`, l'écran.
  **Rien ne touche Hektor, ni le worker, ni le run de nuit.**

### Le découpage proposé en 4 pièces

1. **Le collecteur** — `recrutement/collecte_annuaires.py`, local, écrit un **CSV** à ouvrir dans
   Excel, **rien en base**. Code neuf, réversible (on efface le dossier).
2. **La base** — patch `rec_*` + RLS admin, puis chargement du CSV. *Accord obligatoire.*
3. **L'écran « Recrutement »** — `RecrutementScreen.tsx` + 5 touches dans `App.tsx`.
   *« vas-y » puis accord pour déployer.*
4. **Le repassage** (qui arrive, qui part, qui change de réseau) — une tâche planifiée.

---

## 8. PIÈCE 1 — le collecteur (« Vas-y pièce 1 », 20/11)

**Le code** : `recrutement/collecte_annuaires.py` (dans le dépôt). **Les données** : HORS du dépôt,
parce que ce sont des noms de personnes — `C:\Hektor\recrutement_donnees\` (base SQLite locale,
`journal.txt` écrit au fil, `sortie\candidats_region_<date>.csv`).

**Comment il marche** (règle « mesure longue : découpée, écrite au fil ») : des sous-commandes
(`communes`, `iad liste|fiches`, `safti liste|fiches`, `kw liste|fiches`, `siren`, `csv`,
`controle`), chacune **s'arrête seule à 9 min** et **reprend** où elle en était (code 3 = relancer).
Toujours `python -X utf8 -u recrutement/collecte_annuaires.py <commande>`.

**Ce qu'il garde** : réseau, prénom, nom, commune, CP, département, position, SIREN + ville du
RSAC, nombre d'annonces, nombre d'avis et note, distinction (Club Excellence SAFTI), date de
création et état de l'entreprise, première et dernière vue. **Un verrou dans le code refuse toute
autre colonne.** Ni téléphone, ni e-mail, ni photo, ni texte.

**La politesse** : robots.txt lu et respecté (avec ses jokers), `Crawl-delay` respecté, 3 s entre
deux pages (5 s chez KW), arrêt net d'un réseau sur un 403.

### ⭐ Ce que l'essai a appris (20/11, 11:20)

1. **L'opposition à la prospection existe dans le registre, et l'API publique la donne**
   (`opposition_diffusion_commerciale`). Une personne qui l'a cochée a refusé que les données du
   registre servent à la prospection. **Choix par défaut, à confirmer par Frédéric** : pour elle, on
   ne garde **RIEN** qui vienne du registre (ni création, ni état, ni siège) ; le CSV porte une
   colonne `opposition_prospection_registre = OUI`. Le contrôle le **vérifie** (témoin : 0 donnée de
   registre gardée pour une personne en opposition). Conséquence pour **KW**, dont la commune ne
   vient QUE du registre : une personne KW en opposition **ne peut pas être placée**, elle sort.
2. **La diffusion partielle** : chez certains, le code postal du registre vaut `[NON-DIFFUSIBLE]`
   (la commune reste donnée). Le collecteur ne le recopie jamais ; pour KW, il place alors par la
   commune si elle est **unique** dans nos 4 départements.
3. **Toutes les fiches KW n'ont pas de RSAC** : certaines affichent « Carte pro. n/a » à la place.
   Sans SIREN, impossible de les situer : elles sortent (comptées au compte rendu).
4. **iad peut afficher un RSAC dont l'entreprise est CESSÉE au registre** (vu sur 1 fiche de l'essai,
   0 annonce) : le CSV le montre (`entreprise_active = CESSEE`), c'est un signal à regarder.
5. **SAFTI** : la grille couvre les 4 départements avec **142 pages de commune** (espacement 10 km,
   nos 17 agences d'abord, puis par population), sur 1 375 communes.

---

## 9. ⭐ CORRECTION DU CHANTIER — décidée par Frédéric le 20/11 (fin de matinée)

> *« on va ajouter une correction au chantier : 1 - ajouter plusieurs autres annuaires [...] 2 - créer
> un parser perso par site 3 - lancer la collecte de tous les candidats de la région de ces nouveaux
> sites 4 - tenter aussi la collecte des coordonnées »* — puis *« ok vas-y avec toute la liste + eXp
> France, Keymex, Sextant, 3G Immo, Dr House Immo, Côté Particuliers, Lafourmi, DOHM, Century 21,
> Laforêt, Orpi, ALTI Immo, 42ème Avenue, La Manufacture de l'Immo »* et *« fais une recherche aussi
> de ton côté pour avoir une liste importante »*.
> Sur l'opposition au registre : *« pour opposition on verra plus tard »* → **rien n'est bloqué**,
> la colonne reste affichée, le défaut de §8 (ne pas garder les données du registre de ces
> personnes) reste en place en attendant.

### ⛔ La règle des coordonnées change (elle remplace « sans téléphone ni e-mail »)

- **On prend** le téléphone et l'e-mail **quand la page les AFFICHE à tout visiteur, sans clic**
  (SAFTI : téléphone + e-mail @safti.fr ; KW : téléphone). Chaque coordonnée garde **la page et le
  champ** d'où elle vient.
- **On ne force jamais** un contact **caché derrière un clic, masqué ou encodé** (iad : le numéro
  n'apparaît qu'au clic et il est volontairement masqué dans le code de la page). Le démasquer en
  série, c'est contourner une protection mise là contre cette collecte — même nature que l'affaire
  KASPR (CNIL, 240 000 €, coordonnées que les personnes avaient restreintes) et que la jurisprudence
  Bluetouff (Cass. crim. 20/05/2015). **Signalé site par site, décidé avec Frédéric.**
- Rappel RGPD inchangé : au premier contact, dire d'où vient la coordonnée et offrir le
  « ne plus me contacter ».

### Les sources de la correction

- **Réseaux de mandataires** : Capifrance, Optimhome, Megagence, Expertimo, Propriétés-privées,
  BSK Immobilier, eXp France, Keymex, Sextant, 3G Immo, Dr House Immo, Côté Particuliers, Lafourmi.
  *(Efficity : refuse tous les robots → exclu.)*
- **Franchises d'agences** : Century 21, Laforêt, Orpi.
- **Locaux** : DOHM, ALTI Immo, 42ème Avenue, La Manufacture de l'Immo.
- **Le registre public** (API « Recherche d'entreprises » : entreprises individuelles, NAF 68.31Z,
  actives, dans 07/42/43/63) — tous réseaux confondus, la source la plus sûre juridiquement.
- **Trouvés par ma recherche, À VALIDER par Frédéric** : réseaux Maxihome, Immo-Diffusion,
  Groupement Immobilier, À La Lucarne de l'immobilier, Liberkeys ; agences présentes dans la région
  Square Habitat (Crédit Agricole Loire Haute-Loire : Saint-Étienne, Firminy, Saint-Just-Saint-Rambert…),
  Guy Hoquet, Immonial.

### La méthode

1. **Sonde** de chaque source (robots.txt, forme de l'annuaire, champs de la fiche, contacts en
   clair ou non, nombre dans la région) — 4 sondes en parallèle le 20/11 ; résultats ci-dessous.
2. **Un lecteur par site faisable**, dans `recrutement/collecte_annuaires.py`, sur le même modèle.
3. **Collecte de la région**, puis **les coordonnées affichées**.
4. **Un seul CSV** de tous les candidats, coordonnées comprises quand elles sont publiques, et une
   colonne qui dit pourquoi une case reste vide.

---

## 10. Les sondes du 20/11 (4 en parallèle, lecture seule) et les lecteurs écrits

**La ligne tenue pour les coordonnées** (précision de §9, appliquée site par site) : on prend ce que
le site **envoie en clair à tout visiteur** (texte, lien d'appel, données de la page ou fichier public
qu'elle charge), même quand un bouton le replie à l'écran. On ne prend **jamais** ce qui est
**masqué ou encodé** (iad : numéro encodé ; Optimhome : « 06 ** ** » sur le mini-site ; Keymex :
e-mail chiffré par Cloudflare) ni ce qui **n'arrive qu'après un appel au clic** (3G Immo : e-mail).

### Par source — verdict, nombre dans la région, coordonnées

- **iad** (fait) — 321 — téléphone ENCODÉ, derrière un clic → **non pris** · e-mail absent.
- **SAFTI** (fait) — 106 — téléphone ✅ (106) · e-mail @safti.fr ✅ (84).
- **Keller Williams** (fait) — 10 — téléphone ✅ (9) · e-mail absent (formulaire).
- **Capifrance** — ~115 (comptes du site : Loire 60, Ardèche 23, Puy-de-Dôme 29, Haute-Loire 3) —
  52 pages ville du plan de site ; JSON-LD par conseiller (nom, CP, SIRET, avis, **e-mail**) ;
  téléphone dans le lien d'appel de la carte. ⚠ La règle `Crawl-delay: 20` vise un robot nommé,
  pas tous ; `Disallow: /nos-conseillers` est un ancien chemin ; `?page=` est interdit (non utilisé).
- **Optimhome** — ~117 (dont 96 en Puy-de-Dôme) — même plateforme ; téléphone pris sur la **page
  ville** (en clair), jamais sur le mini-site (masqué).
- **BSK Immobilier** (`bskimmobilier.com`, sans www) — 59 — API publique de la page « conseillers » :
  nom, SIRET, ville du RSAC, annonces, avis, téléphone, e-mail.
- **Megagence** — 24 — un seul JSON pour tout le réseau (924) : téléphone ✅, e-mail absent.
- **Expertimo** (annuaire sur `reseau-expertimo.fr`) — 17 mandataires — un JSON de carte :
  téléphone et e-mail ✅. ⛔ La fiche **462** est interdite par robots.txt → **la personne est écartée**.
- **Dr House Immo** (`drhouse-immo.com`) — ~50 estimés — 114 pages de liste, JSON-LD par conseiller
  (le code postal vient de l'adresse de la fiche : le JSON-LD ne donne que le département).
- **3G Immo** — ~40 estimés — carte GeoJSON publique (680) ; la commune par l'API géo de l'État ;
  téléphone ✅. ⛔ **E-mail non pris** : il est dans un champ caché, affiché seulement par un appel
  au clic (et l'adresse de cet appel est interdite par robots.txt). **À trancher par Frédéric.**
- **LF immo** (ex-Lafourmi, `lfimmo.fr`) — 4 — téléphone et e-mail affichés ✅.
- **Sextant** — 2 — carte JSON de la page « nos conseillers » ; téléphone ✅, e-mail absent.
  ⚠ Le robots.txt porte une réserve « pas d'entraînement d'IA » : sans rapport avec cette collecte.
- **Côté Particuliers** — 1 agence (Clermont-Ferrand), 18 collaborateurs — téléphone et e-mail ✅.
- **eXp France** — 805 en France, ~5 à 15 dans la région — l'annuaire ne donne pas la commune →
  placés par le SIREN (comme KW). Téléphone et e-mail ✅. On n'interroge PAS leur base privée.
- **Orpi** — 24 agences (42 : 6, 07 : 10, 63 : 8, 43 : 0) — équipe sur la page d'agence ; téléphone
  ✅ (souvent le mobile), le standard de l'agence est écarté ; e-mail par formulaire seulement.
- **Laforêt** — 14 agences — noms et fonctions, aucune coordonnée personnelle.
- **Century 21** — 10 agences — l'équipe est sur le mini-site de chaque agence ; aucune coordonnée.
- **42ème Avenue** — 26 personnes — SIREN (« Numéro RCS ») et mobile ✅.
- **La Manufacture de l'Immo** — 15 profils — SIREN (« RSAC » ou « RCS »), téléphone et e-mail ✅.
- **Le registre public** — 1 568 entreprises individuelles 68.31Z actives (dont ~950-1 250 avec le
  siège dans la région) ; ⛔ **une personne en opposition n'est PAS gardée** (sa seule source est le
  registre) ; la date de naissance que l'API renvoie n'est **jamais** lue. Une personne déjà connue
  par un réseau n'a qu'une ligne (celle du réseau).
- **IMPOSSIBLES** : **Propriétés-privées** (le site n'ouvre aucune connexion depuis notre serveur —
  rien tenté pour contourner) · **DOHM** et **ALTI Immo** (ils ne listent que des agences, aucune
  personne) · **Efficity** (refuse tous les robots) · **Keymex** (0 dans la région).

### ✅ R1 — les sources restantes, sondées et lues le 20/11 au soir (délégation, §15)

Sonde : robots.txt, accueil, puis pages d'annuaire, avec le lecteur poli du collecteur (une requête
à la fois, 3 s par hôte). Les lecteurs sont dans `collecte_annuaires.py`, section « R1 ».
- **Groupement Immobilier** (`groupementimmo.fr`) — **3** (Ardèche, Haute-Loire, Loire). Une page
  par département : identifiant interne, lu sur la carte, pas le numéro INSEE. La fiche porte
  « Mandataire Commune (CP) », le mobile et l'e-mail de la personne, tous deux pris. Le standard
  et l'e-mail du réseau sont écartés. Le nom est lu dans le bloc « Service » du JSON-LD.
- **Immo-Diffusion** (`immo-diffusion.fr`) — **9** (Loire 6, Ardèche 2, Puy-de-Dôme 1). Une page par
  département. Le titre de la fiche porte la commune, le nom et le département. Le téléphone est
  pris quand la fiche l'affiche en texte (6 sur 9). Aucun e-mail n'est publié.
- **À La Lucarne** (`alalucarne.com`, et non `.fr`, qui est le site de recrutement) — **1**
  (Puy-de-Dôme). Il n'y a pas de liste : le formulaire public « où recherchez-vous ? » par
  département, c'est-à-dire ce que fait un visiteur.
  - Le **numéro est pris sur la fiche publique** de la conseillère, jamais dans la réponse du
    formulaire : la règle des coordonnées (§9) est tenue.
  - Aucun conseiller en Loire, en Haute-Loire ni en Ardèche.
- **Liberkeys** — 287 agents en France (plan du site), lus fiche par fiche (« Secteur 49 –
  Maine-et-Loire »).
  - Le mobile et l'e-mail @liberkeys.com sont affichés.
  - ⭐ **Minimisation** : l'adresse d'une fiche porte le nom de l'agent. Pour un agent **hors
    région**, seule une **empreinte** de la page est gardée (pour reprendre une lecture coupée),
    jamais l'adresse.
- **Maxihome** — 54 conseillers en France, nom, e-mail et mobile affichés, mais **aucune commune
  nulle part**.
  - Une personne n'est gardée que si le **registre public** la place dans la région : même prénom
    et même nom qu'**une seule** entreprise individuelle immobilière de la région, déjà lue.
    Celle-ci n'est donc jamais une personne en opposition.
  - En cas d'homonyme, la personne n'entre pas. Résultat : **1** personne.
- **Écartées** :
  - **Square Habitat** : les pages d'agence (Firminy relue) ne nomment personne ;
  - **Guy Hoquet** : la recherche d'agences passe par le service d'un tiers, avec sa clé ;
  - **Immonial** : plus de site, le domaine est à vendre ;
  - **Propriétés-privées** : 2ᵉ essai, toujours aucune connexion. Noté comme refus, rien tenté
    d'autre.

### ⚠ Une erreur de ma part, dite

Vers 11:55, j'ai cru arrêtée la relecture SAFTI (contrôle des processus fait avec `ps` dans Git Bash,
qui **ne voit pas** les processus Windows) et je l'ai relancée : **deux processus ont lu SAFTI en même
temps pendant ~4 min** (double charge sur leur site). Arrêté dès que je l'ai vu. Le bon contrôle est
`Get-CimInstance Win32_Process` (PowerShell).

---

## 11. ✅ RÉSULTAT DE LA COLLECTE — 20/11/2026, 12:28 (contrôle VERT)

**Le fichier** : `C:\Hektor\recrutement_donnees\sortie\candidats_region_2026-11-20.csv` (point-virgule,
UTF-8, s'ouvre dans Excel) — **1 920 candidats**, une ligne par personne, triés par distance à
l'agence GTI la plus proche.

- Par département : Loire 797 · Puy-de-Dôme 628 · Ardèche 326 · Haute-Loire 169.
- **À 15 km au plus d'une agence GTI : 839** · à 30 km au plus : 1 371.
- **Coordonnées affichées** : 626 téléphones, 395 e-mails, **629 personnes joignables**.
- Par source : registre public 792 *(indépendants hors des réseaux lus ; 180 autres sont déjà dans
  un réseau, ils n'ont qu'une ligne)* · iad 321 · Orpi 144 · SAFTI 106 · Century 21 82 · Optimhome 68
  · Capifrance 65 · Dr House 64 · Laforêt 61 · BSK 59 · 3G Immo 39 · 42ème Avenue 26 · Megagence 24
  · Côté Particuliers 18 · Expertimo 17 · La Manufacture 15 · Keller Williams 10 · LF immo 4 ·
  eXp 3 *(805 en France, 802 hors région ou non localisables)* · Sextant 2.
- **298** personnes des réseaux sont **en opposition** à la prospection au registre (colonne
  `opposition_prospection_registre = OUI`) — *« on verra plus tard »*. **421** autres, présentes
  seulement au registre, **ne sont pas dans le fichier** (écartées).
- **10** entreprises **CESSÉES** au registre alors que la fiche du réseau existe encore.
- **Aucune personne n'est dans deux réseaux à la fois** (les 180 doublons de SIREN sont tous
  « réseau + registre »).

**Le contrôle** (`controle`, code 0) : 0 coordonnée là où elle est cachée (iad), 0 coordonnée sans
source, 0 au format invalide, 0 coordonnée hors de sa colonne ; témoin positif présent ; 1 SIREN à
clé invalide (`135120000`, laissé tel quel) ; 1 SIREN introuvable.

**Ce qui a raté puis été corrigé** : le 1er contrôle était ROUGE — mon identifiant des fiches Dr House
contenait un « @ » (`nom@CP`) et le contrôle refuse tout « @ » hors des colonnes de contact. Corrigé
dans le code et la base (séparateur `/`), **sans affaiblir le contrôle**. Au passage, 1 fiche Dr House
qui était une AGENCE et 1 dont l'adresse est en Haute-Marne ont été retirées (le lecteur les écarte
désormais). Sauvegarde d'avant : `recrutement_avant_correction_drhouse_20261120.sqlite`.

**Limites connues** : Capifrance et Optimhome annoncent 115 et 117 conseillers dans la région ; leurs
pages par ville n'en montrent que 65 et 68 (le reste est derrière une pagination interdite par leur
robots.txt). Le registre a répondu lentement (connexions coupées, un 429) : l'étape s'est faite en
deux tranches, sans perte.

**Fichiers temporaires effacés** : les pages des sondes et la base d'essai (noms et numéros réels).

**La suite (accord de Frédéric nécessaire)** : pièce 2 (tables `rec_*` dans la base de l'app, réservées
aux administrateurs) puis pièce 3 (l'écran « Recrutement » et ses filtres).

---

## 12. MAQUETTES (20/11 après-midi, demande de Frédéric) — NON validées

> *« propose-moi une maquette visuelle pour la vue recrutement type listing avec des colonnes [...],
> une maquette pour la page candidat avec quelques fonctions utiles, audite mon app pour connaître les
> outils déjà disponibles [...], et une maquette de la modale d'ajout et le mécanisme de modification
> et suppression de ces fiches. »*

**Canevas (artifact privé)** : https://claude.ai/artifact/5FjabqxzxGCPYwkhKbFQDc — 5 planches :
1. **Listing** — élément fort : « Où recruter », la carte des 17 agences (disque = vivier à 15 km,
   cœur = joignables) + le classement des agences + la zone choisie (fond encre). Colonnes : candidat
   (réseau, fonction), où (commune, distance à l'agence), activité (annonces, avis), entreprise
   (ancienneté, cessée), à savoir (Club Excellence, opposition, cessée), joindre (téléphone / e-mail
   publics ou « derrière un clic »), suivi (étape + prochaine action). Vues : Tous, Joignables, Mes
   relances, En cours de recrutement.
2. **Fiche candidat** — élément fort : « Son parcours avec nous » (Repérée → Contactée → Rendez-vous →
   Proposition → Contrat signé → Accès ouvert, coche du logo pour une étape faite) + « Ensuite : … ».
   Blocs : la joindre (chaque coordonnée avec sa source), « Au premier contact » (la phrase RGPD et
   la case « je l'ai informée »), son entreprise, le fil des échanges (Appel / Note / E-mail /
   Rendez-vous), son activité dans le réseau, documents, « quand elle nous rejoint ».
3. **Ajouter** — doublon détecté, distance à l'agence calculée, champs selon la situation (réseau /
   indépendant / salarié d'agence / hors immobilier), origine du contact → phrase RGPD adaptée.
4. **Modifier** — chaque champ dit sa provenance : lu dans un annuaire (relu le jeudi) / corrigé par
   toi (la relecture n'y touche plus) / saisi par toi ; historique des changements.
5. **Retirer ou effacer** — 3 niveaux : retirer de ma liste (archives, réversible) · ne plus jamais
   la contacter (reste nom + SIREN + date, pour que la collecte ne la remette pas) · effacer toutes
   ses données (reste une empreinte illisible ; confirmation en tapant EFFACER).
Volumes réels du 20/11 ; **noms, numéros (plage fiction 06 39 98) et e-mails FICTIFS**.

### Ce que l'audit du 20/11 dit qu'on réutilise (lecture seule, fichier:ligne dans le rapport)

- **FACILE** : envoyer un e-mail (`sendGoogleWorkspaceCrmEmail`, api.ts:716, tracé dans
  `app_google_workspace_action_log`, `related_entity_type` libre) ; poser un RDV Google
  (`createGoogleCalendarEvent`, `eventType 'autre'`, `relatedEntityType 'other'` → visible dans
  l'Agenda) ; appeler (`tel:`) ; la fenêtre modale générique `ContactWorkflowModal` (App.tsx:45513) et
  la confirmation « tapée » des suppressions ; les droits (6 points calqués sur Pilotage,
  `is_app_admin()` + la RLS du registre des négociateurs) ; l'export CSV (`FicheNotaire`) ; le PDF par
  impression ; les variables `--ds-*` (toujours actives, `--bv-*` seulement sous `.bv`).
- **MOYEN** : la liste (copier `RegistreTransactionsScreen` : recherche, tri, pastilles, pagination) ;
  le fil et le journal (modèles `app_registre_journal`, `app_affaire_note`) ; la fenêtre d'e-mail
  (modèles à écrire : « premier contact » avec la source et le refus) ; lister les RDV d'un candidat
  (filtre `related_entity_id` à ajouter au backend) ; la carte (Leaflet + fond IGN déjà là, mais une
  seule carte à un point ; nos agences n'ont pas de lat/lon en base) ; ranger un CV (aucun dépôt libre
  durable : schéma de `assistant_fichiers` à recopier) ; créer l'accès d'un recruté (`createAppUser` ;
  le pré-remplissage exige une personne du registre) ; notifications (le clic n'ouvre qu'une URL).
- **DIFFICILE** : suivi d'ouverture des e-mails (seulement pour le rapprochement) ; signature Youtrust
  d'un contrat (le circuit exige un document d'annonce : nouveau travail du worker) ; `DepotDocuments`.
- **ABSENT** : SMS ; corbeille (**par décision de Frédéric du 13/10**, d'où « archiver + journal »).

### ⛔ À trancher par Frédéric (ce sont des FONCTIONS, pas du dessin)

1. Les étapes du parcours et les statuts de suivi (noms, nombre).
2. Le modèle d'e-mail « premier contact » (texte, mention de la source, lien de refus).
3. Le CV et le contrat d'agent commercial (rangement neuf ; signature Youtrust = chantier à part).
4. « Créer son accès à bienvu » depuis la fiche.
5. La carte : schéma dessiné (comme la maquette) ou vraie carte IGN (Leaflet).
6. Les 3 niveaux de retrait/effacement.
7. Le principe « ta correction gagne sur la relecture du jeudi ».
8. Toujours ouvertes : qui voit la rubrique (admins seuls ?), la fréquence de relecture, l'opposition
   au registre, l'e-mail caché de 3G, les 8 sources trouvées par ma recherche.

---

## 13. ⭐ PLAN DE DÉVELOPPEMENT — demandé par Frédéric le 20/11 (maquettes VALIDÉES)

> *« j'aime bien ta maquette, je pense qu'il est temps de faire un chantier de dev : récupérer de la
> même manière les sites web non testés mais listés ; prévoir un système qui permettrait de mettre à
> jour ces fiches, refaire une collecte pour dire lesquelles ne sont plus sur les sites et collecter
> les nouvelles ; prévoir l'architecture de la data recrutement, serveur et app, sauvegarde, mais sans
> perturber le reste, c'est indépendant. Donc maintenant je te valide cette maquette et toi donne-moi
> un plan dev. »*
>
> **Maquettes validées le 20/11** : https://claude.ai/artifact/5FjabqxzxGCPYwkhKbFQDc (5 planches).
> ⛔ Les points « à trancher » du §12 restent des QUESTIONS : la validation porte sur le dessin.

### 13.1 L'architecture — bâtie comme le reste de l'app, et indépendante de lui

> ⭐ **Révisée le 20/11 au soir, à la demande de Frédéric** : *« d'abord une collecte mensuelle est
> suffisante, et peux-tu faire une architecture similaire au reste de l'app ? tâche planifiée
> Windows, run, mise à jour, monitoring, etc. »*. La 1ʳᵉ version (tâche hebdomadaire, pousseur seul)
> est remplacée ; l'ancien texte reste lisible dans l'historique git de cette note.
>
> ⭐⭐ **Révisée encore le 24/11 : TOUS LES DEUX MOIS** — Frédéric : *« peut-on le passer à tous les
> 2 mois »*. Les changements :
> - la tâche devient **« GTI Recrutement »** : plus de fréquence dans le nom, il ne mentira plus si
>   on la rechange. L'installeur retire « GTI Recrutement Mensuel », enregistrée le 24/11 au matin ;
> - le lanceur devient **`run_recrutement.ps1`** ;
> - le déclencheur : le **1er dimanche de décembre, février, avril, juin, août et octobre**, à 10:00 ;
>   le 1er passage reste le 06/12 ;
> - la fréquence de surveillance devient **`bimonthly` = 64 jours** (jusqu'à 9 semaines entre deux
>   passages) ;
> - **6 sauvegardes** gardées, soit toujours un an.
> Ailleurs dans cette note, « mensuel », « monthly » et « 12 gardées » décrivent la version du 20/11.
> Le journal les garde tels quels.

```
                 TÂCHE WINDOWS « GTI Recrutement »   (1er dimanche, TOUS LES DEUX MOIS, 10:00)
                 └─ scheduled/run_recrutement.ps1    (le RUN : 8 étapes, un battement chacune)

  ① descente     Supabase ─► local   liste « ne plus contacter », effacements, corrections de l'app
  ② collecte     sites des réseaux + registre public ─► recrutement.sqlite (une source à la fois)
  ③ mise à jour  collecte N comparée à N-1 : nouveaux, partis, revenus, changés ; garde-fou de source
  ④ contrôle     règle des coordonnées, opposition, témoins ─ ROUGE = on s'arrête, rien ne monte
  ⑤ montée       local ─► Supabase, schéma à part « recrutement »  (interrupteur RECRUTEMENT_MONTEE)
  ⑥ sauvegarde   copie datée ─► C:\Hektor\Backups\recrutement\  (6 gardées = 1 an)
  ⑦ compte rendu la ligne de la collecte en base ─► bandeau de l'écran + écran Santé

  SURVEILLANCE   monitoring/check_gti_health.py : la tâche (résultat ≠ 0) + les 7 battements
                 (app_worker_registry, fréquence neuve « bimonthly ») ─► écran Santé, e-mail du matin

  APP bienvu     écran « Recrutement » (admin, interrupteur recrutement_visible) ─► fonctions
                 public.rec_* ─► schéma recrutement ; e-mail et RDV par Google Workspace (déjà en place)
```

**Chaque brique a son modèle dans le projet** (relu le 20/11 au soir, rien inventé) :

| brique | le modèle qu'on recopie |
|---|---|
| le code dans le dépôt, les données hors dépôt | `phase2/` et `phase2.sqlite` ignoré par git ; ici `recrutement/` et `C:\Hektor\recrutement_donnees\` (données personnelles : jamais dans le dépôt) |
| le lanceur et son journal | `scheduled/run_menage_temporaires.ps1`, `run_nuit_contacts_et_recherches.ps1` : transcription dans `logs\scheduled\recrutement_<date>.log`, `-DryRun`, sortie en **1** dès qu'il y a quelque chose à voir |
| la reprise d'un run arrêté | `-StartAtLabel` de `run_quotidien.ps1` (les vraies commandes, jamais des recopies) ; plus `-Source <réseau>` pour relire un seul site après la réparation d'un lecteur |
| l'enregistrement de la tâche | `scheduled/installer_tache_menage_temporaires.ps1` : réglages dans le dépôt, puis **comparaison réglage par réglage** à une sœur qui marche (S4U, IgnoreNew, Win7, moteur unifié…) ; seule différence voulue, nommée et vérifiée : le déclencheur mensuel et la durée limite |
| le déclencheur mensuel | `Hektor-IngestSemestriel`, seule tâche du serveur en calendrier (`CalendarTrigger` / `ScheduleByMonth`, relu le 20/11) ; ici `ScheduleByMonthDayOfWeek`, 1ʳᵉ semaine, dimanche |
| les battements | `monitoring/heartbeat.py` ; ⚠ **chaque clé a SA ligne dans `app_worker_registry` avant le 1er run** (sinon le battement part dans le vide : 23 étapes l'ont fait jusqu'au 13/10) |
| la surveillance de la tâche | `TASK_CRITICALITY` + la liste des tâches suivies de `check_gti_health.py`, **déclarée AVANT d'être enregistrée** (12 noms aujourd'hui, ce serait 13) |
| la sauvegarde à part | `run_backup.ps1` : dossier daté sous `C:\Hektor\Backups\`, rétention glissante, un échec sort en 1 |
| l'interrupteur | côté serveur une ligne du `.env` (patron `APP_BALAYAGE_PHOTOS_PERIMETRES`) ; côté écran `app_setting` |

**Pourquoi un schéma à part, et pas des tables `public.rec_*`** (mesuré le 20/11) : la descente du
matin (`phase2/sync/pull_from_supabase.py`) **découvre seule** toutes les tables publiques (spec OpenAPI
de PostgREST, « pas de liste à tenir »). Une table publique de recrutement serait recopiée chaque
matin dans `phase2.sqlite` — charge en plus ET données personnelles copiées. Un schéma `recrutement`
non exposé est **invisible** pour la descente, le run de nuit, les sentinelles et l'assistant
(liste blanche). L'écran y accède par des **fonctions** `public.rec_*` (`security definer`, qui
commencent par `if not is_app_admin() then raise exception`) — le patron du registre des négociateurs.
⭐ **Et c'est aussi ce qui rend l'effacement RGPD complet** : une personne effacée dans l'app l'est
dans le schéma, puis dans la base locale à la descente ① du run suivant ; elle n'a jamais été copiée
dans `phase2.sqlite` ni dans ses sauvegardes de 90 jours. Ce que le run a, lui, sa propre descente
et sa propre sauvegarde, qu'il purge lui-même.

**Pourquoi le 1er dimanche du mois à 10:00** (proposition, à valider) : la nuit est pleine de 20:00
à 09:00 (entretien photos et documents, balayage, recherches, run, descente 07:45, sauvegarde 09:00
qui fait le dimanche son instantané complet). Le collecteur ne parle jamais à Hektor et n'ouvre
jamais `phase2.sqlite` (aucun risque de verrou), mais il utilise le serveur et le réseau : on le
met en plein jour, un dimanche, entre la sauvegarde et la reprise de 20:00. ⚠ La 1ʳᵉ collecte a
tenu une matinée ; la durée limite sera de **8 h** et se mesurera au premier run.

**Pourquoi un schéma à part, et pas des tables `public.rec_*`** (mesuré le 20/11) : la descente du
matin (`phase2/sync/pull_from_supabase.py`) **découvre seule** toutes les tables publiques (spec OpenAPI
de PostgREST, « pas de liste à tenir »). Une table publique de recrutement serait recopiée chaque
matin dans `phase2.sqlite` — charge en plus ET données personnelles copiées. Un schéma `recrutement`
non exposé est **invisible** pour la descente, le run de nuit, les sentinelles et l'assistant
(liste blanche). L'écran y accède par des **fonctions** `public.rec_*` (`security definer`, qui
commencent par `if not is_app_admin() then raise exception`) — le patron du registre des négociateurs.

**Ce qui n'est JAMAIS touché** : Hektor, le worker et ses 4 services, le run de nuit, la descente,
`phase2.sqlite`, les tables existantes, les 12 tâches planifiées existantes.
**Les fichiers partagés modifiés, tous en ajout** :
- `App.tsx` : 6 points calqués sur Pilotage, derrière l'interrupteur `recrutement_visible` dans `app_setting` ;
- `monitoring/check_gti_health.py` : 1 nom de tâche dans la liste suivie, 1 ligne dans
  `TASK_CRITICALITY`, 1 fréquence `"monthly"` dans `WORKER_STALE_POLICY`.
  ⚠ Une autre session a déjà eu des changements non commités dans ce fichier (04/11) : relire
  `git status` et stager ce seul morceau.
- `app_worker_registry` : 7 lignes neuves (`recrutement.*`), dans le patch R3.

**Ce que ça pourrait casser ailleurs, et la parade** :
- la surveillance, si une fréquence inconnue retombe sur le seuil par défaut. Une étape mensuelle
  y serait « en retard » dès le 2ᵉ jour : d'où la fréquence `monthly` posée **avant** les lignes ;
- l'e-mail du matin, si la tâche est mise en `critical` : un défaut qui attend un mois n'a pas à
  sonner. Elle sera en `warning` : visible à l'écran Santé et dans l'e-mail, sans alerte ;
- le serveur, si la collecte déborde sur la reprise de 20:00 : durée limite 8 h,
  `MultipleInstances = IgnoreNew`.

### 13.2 Les chapitres

Chaque chapitre suit la méthode du §0 de `CLAUDE.md` : audit → explication → code additif → contrôle
→ note à jour. Une seule tâche en code à la fois.

**R1 — Les sources listées mais pas encore lues** *(additif, local ; j'enchaîne)*
- Sonder puis lire : Maxihome, Immo-Diffusion, Groupement Immobilier, À La Lucarne de l'immobilier,
  Liberkeys, Square Habitat, Guy Hoquet, Immonial ; **réessayer Propriétés-privées** (une requête :
  s'il refuse encore, on le note comme refus).
- Un lecteur par site faisable, mêmes règles (robots.txt, pauses, coordonnées affichées seulement).
- Contrôle : comptes par source, témoin positif par source, règle des coordonnées verte.
- Retour arrière : retirer le lecteur et ses fiches (`delete from fiche where reseau=…`).

**R2 — La mise à jour : qui arrive, qui part, qui change** *(additif, local ; j'enchaîne)*
- Chaque passage devient une **COLLECTE numérotée et datée** ; chaque fiche lue est une
  **OBSERVATION** (fiche × collecte). On ne supprime plus rien sur une absence.
- États calculés : **nouveau** (vu pour la 1ʳᵉ fois), **présent**, **absent** (pas vu cette fois),
  **parti** (absent **deux collectes de suite**, source saine), **revenu**, **a changé de réseau**
  (même SIREN vu dans un autre réseau), **entreprise cessée** (registre).
  ⚠ **Au rythme de tous les deux mois (24/11)**, « deux collectes de suite » veut dire **quatre
  mois**. D'où l'importance de la **preuve positive**, qui fait partir tout de suite : sa propre
  page répond 404 ou 410, ou renvoie vers
  l'accueil du réseau. Sans preuve, il reste « absent, à vérifier » jusqu'au mois suivant.
- ⛔ **LE GARDE-FOU DE SOURCE** (leçon « un zéro ne se croit pas sans témoin positif ») : si une
  source rend **moins de 70 %** de ses fiches de la fois d'avant, ou perd un de ses **témoins
  positifs**, la collecte de cette source est déclarée **MALADE** : aucun départ n'est tiré d'elle,
  une alerte part. Sans ça, un site qui change sa page ferait « partir » tout son réseau d'un coup.
- **Le carnet des corrections** : ce que l'humain corrige (téléphone, commune…) n'est plus jamais
  écrasé par la relecture (règle de la planche 4, même principe que « écriture app non écrasée »).
- **La liste « ne plus contacter / effacé »** : lue AVANT tout enregistrement ; une personne qui y est
  ne rentre jamais (empreinte du SIREN, du téléphone, du nom + commune).
- Contrôle hors ligne : rejouer deux collectes fabriquées (une normale, une où un site « casse ») —
  la seconde doit sortir MALADE, avec 0 départ.

**R3 — La base** *(accord OBLIGATOIRE : écriture en production)*
- Patch `supabase/patch_recrutement_schema_<date>.sql` + `_REPETITION.sql` + `_INVERSE.sql`, collés
  par Frédéric (patron du projet ; l'outil refuse d'écrire en production).
- Tables `recrutement.` : `collecte`, `source_etat` (santé par source et par collecte), `fiche`
  (une par réseau), `personne` (la même personne vue partout, clé SIREN quand on l'a), `observation`,
  `correction` (le carnet), `suivi` (étape, prochaine action, qui suit), `evenement` (le fil :
  appel, note, e-mail, RDV, changement d'étape, retrait), `liste_noire`, `journal`.
- Droits : RLS active, rien pour `anon`/`public`, ⚠ `revoke insert, update, delete, truncate … from
  authenticated` (Supabase donne tout par défaut sur une table neuve — leçon du registre).
- **Les 7 lignes de `app_worker_registry`** (`recrutement.descente`, `.collecte`, `.mise_a_jour`,
  `.controle`, `.montee`, `.sauvegarde`, `.compte_rendu`), fréquence `monthly`, gravité `medium`.
  Elles sont dans le **même patch**, pour qu'aucun battement ne parte dans le vide.
- Répétition : un administrateur lit, un négociateur reçoit « Réservé aux administrateurs », la
  descente du lendemain ne voit **aucune** table nouvelle (témoin inverse) ; la répétition **extrait
  les 7 clés du patch** au lieu de les recopier (leçon de la parenthèse en trop du 13/10).
- Retour arrière : `drop schema recrutement cascade` + les fonctions `rec_*` (l'inverse vérifie
  qu'il ne reste rien).

**R4 — Les deux ponts : la montée et la descente** *(accord pour le premier envoi)*
- **La montée**, `recrutement/pousser.py` : envoie la dernière collecte (clé de service du `.env`,
  comme `refresh_contact_inproc.py`), par lots, en reprenant où il s'est arrêté ; ne touche
  **jamais** une valeur du carnet des corrections ni le suivi. Elle ne part que si
  `RECRUTEMENT_MONTEE=1` dans le `.env` : on peut collecter et contrôler sans rien envoyer.
- **La descente**, `recrutement/descendre.py` : rapporte de la base, AVANT toute collecte, la liste
  « ne plus contacter », les effacements et les corrections faits dans l'app. Un effacement est
  appliqué tout de suite dans la base locale. ⛔ Si la base ne répond pas, **le run s'arrête** : on
  ne collecte jamais sans savoir qui ne doit plus revenir.
- Contrôle : comptes identiques des deux côtés, 0 coordonnée iad, 0 donnée de registre pour une
  personne en opposition, 0 personne de la liste noire, et un effacement fait dans l'app absent de
  la base locale après la descente (témoin positif).

**R5 — Le run mensuel, la tâche, la surveillance, la sauvegarde** *(« vas-y » pour
`check_gti_health.py` ; accord pour enregistrer la tâche)*
- **Le run** `scheduled/run_recrutement_mensuel.ps1` enchaîne les 7 étapes du §13.1, chacune avec son
  battement (`running` en entrée, `success` ou `error` en sortie). Comportement par étape :
  - descente en échec → arrêt ;
  - une source en échec → **les autres continuent** ; la source est notée et le run sortira en 1 ;
  - un lecteur qui rend la main au bout de 9 min (code 3) est **relancé**, il reprend où il en
    était, avec un plafond de relances ;
  - contrôle rouge → **rien ne monte**.
  Le journal de la tâche ne porte **que des comptes**, jamais un nom : le détail par page reste dans
  `recrutement_donnees\journal.txt`, que la purge RGPD atteint.
- **Paramètres**, comme les sœurs :
  - `-DryRun` : collecte et contrôle, sans montée ni sauvegarde ;
  - `-StartAtLabel "<étape>"` ;
  - `-Source <réseau>` : relire un seul site, par exemple après la réparation d'un lecteur.
- **Les codes de sortie** (convention du projet) :
  - **0** : tout est vert ;
  - **1** : une source MALADE, un lecteur en échec, un contrôle rouge ou une étape tombée.
  Tout ce qui sort en 1 se voit au Planificateur ET à l'écran Santé.
- **La tâche** `GTI Recrutement Mensuel` est posée par `scheduled/installer_tache_recrutement.ps1`,
  recopié de `installer_tache_menage_temporaires.ps1` :
  - sœur de référence `GTI Menage Temporaires` : S4U, Limited, Win7, moteur unifié, IgnoreNew,
    StartWhenAvailable faux ;
  - ce qui diffère de la sœur, vérifié contre la valeur **voulue** : le déclencheur calendrier
    (1ʳᵉ semaine, dimanche, 10:00, les 12 mois) et la durée limite de 8 h ;
  - le script doit être lancé dans une PowerShell **administrateur**, par Frédéric : mon shell n'est
    pas élevé (vécu le 31/07).
- **La surveillance**, déclarée **AVANT** l'enregistrement de la tâche :
  - **`warning`** et non `critical`, sur le raisonnement déjà écrit pour « GTI Entretien Photos » :
    un mois raté se rejoue à la main sans rien perdre. Un e-mail d'alerte pour un défaut qui attend
    un mois, c'est du bruit. Visible à l'écran Santé et dans l'e-mail du matin ;
  - la fréquence `monthly` = **36 jours** : il peut y avoir 5 semaines entre deux premiers
    dimanches, plus un jour de marge.
- **La sauvegarde** (étape ⑥), dans `C:\Hektor\Backups\recrutement\` :
  - une copie datée de `recrutement.sqlite`, faite par l'API de sauvegarde de SQLite (pas une copie
    de fichier pendant l'écriture), et du CSV du mois ;
  - **12 gardées**, soit un an ; elle sort en 1 si la copie ne se relit pas.
  ⚠ À vérifier : si l'agent OVH (Veeam) couvre `C:\Hektor\Backups\` et `C:\Hektor\recrutement_donnees\`.
- **R5 bis, quand l'écran existera (avec R6)** : ce que l'app écrit (suivi, fil, corrections, liste
  noire) change tous les jours, pas tous les mois. Une petite tâche quotidienne
  `GTI Recrutement Sauvegarde` (quelques secondes, après la sauvegarde de 09:00) en fait la descente
  et une copie datée (90 jours, comme les tables critiques). C'est le pendant de `GTI Descente` +
  `GTI Sauvegarde`, et elle est déclarée à la surveillance de la même façon.
- **Purge RGPD**, en fin de run : une personne sans aucun échange depuis **3 ans** est effacée
  (empreinte gardée). Elle est effacée aussi des sauvegardes au fil de leur rotation : un an au plus
  pour les mensuelles, 90 jours pour les quotidiennes. La durée est **écrite** dans la mention
  d'information.

**R6 — L'écran** *(code neuf, puis « vas-y » pour `App.tsx`, puis accord pour déployer)*
- `RecrutementScreen.tsx` (+ `recrutement.css`, préfixe `rc-`, variables `--ds-*`) en partant de
  `RegistreTransactionsScreen` (recherche, tri, pastilles, pagination) ; « Où recruter » (carte des
  agences : dessin, ou Leaflet + fond IGN selon la décision) ; `FicheCandidat.tsx` ; les fenêtres
  Ajouter / Modifier / Retirer (patron `ContactWorkflowModal`, confirmation tapée).
- Gestes branchés sur l'existant : appeler (`tel:`), e-mail (`sendGoogleWorkspaceCrmEmail`,
  `related_entity_type = 'candidat'`), RDV (`createGoogleCalendarEvent`, `eventType 'autre'`,
  `relatedEntityType 'other'` — + filtre `related_entity_id` à ajouter au backend pour lister les RDV
  d'un candidat).
- **Le bandeau de la dernière collecte**, en tête du listing, lu dans `recrutement.collecte` :
  - la date ;
  - le nombre de nouveaux et de partis ;
  - les sources malades, nommées : « SAFTI n'a pas pu être relu ce mois-ci, ses fiches gardent
    l'état d'avant ».
  Les mots « relu chaque jeudi » des planches Modifier et Supprimer deviennent « relu chaque mois ».
- Contrôle : `npm run build` ; **la maquette ouverte à côté, capture contre capture** (règle « une
  maquette validée se suit à l'écran ») ; téléphone ; un négociateur ne voit ni le menu ni les données.

**R7 — Les fonctions à trancher** *(une par une, après décision)*
- Modèle d'e-mail « premier contact » (source des coordonnées + refus) · rangement du CV (coffre neuf)
  · contrat d'agent commercial et signature (chantier à part : le circuit Youtrust exige un document
  d'annonce) · « créer son accès à bienvu » (`createAppUser`) · notification « nouveaux candidats
  près de chez toi cette semaine ».

### 13.3 L'ordre proposé et ce qui attend Frédéric

L'ordre :
1. `R1 → R2` tout de suite : additifs, en local, aucune décision bloquante. Frédéric tranche les
   questions pendant ce temps.
2. Le run `run_recrutement_mensuel.ps1` s'écrit **dès R2**, en `-DryRun`. Il ne monte rien et ne
   bat dans aucune ligne tant que R3 n'est pas posé : les battements sont désactivés par
   l'interrupteur. On l'éprouve à la main, en entier, sur la vraie collecte.
3. `R3 → R4 → R5` : quatre gestes à accord.
   - coller le patch : les tables, les fonctions et les 7 lignes de battement ;
   - le premier envoi ;
   - le « vas-y » sur `check_gti_health.py`, pour déclarer la tâche AVANT ;
   - l'enregistrement de la tâche, par Frédéric, en administrateur.
4. `R6`, avec R5 bis.
5. `R7`, au fil des décisions.

**Décisions qui bloquent un chapitre** :
- le **1er dimanche du mois à 10:00**, à confirmer ou à changer (R5) ;
- la gravité `warning` de la tâche (R5) ;
- qui voit la rubrique : administrateurs seuls ? (R3, R6) ;
- la carte dessinée ou IGN (R6) ;
- le texte de l'e-mail de premier contact (R7) ;
- l'opposition au registre et l'e-mail caché de 3G (R2).

---

## 14. ⭐ LA LISTE DES TÂCHES — la seule, à cocher ici et nulle part ailleurs

> Demandée par Frédéric le 20/11 au soir : *« montre-moi la liste des tâches du dev, je ne veux pas
> que tu te perdes »*. Le **pourquoi** de chaque tâche est au §13 ; ici, seulement le **quoi** et
> l'**état**. Une case ne se coche qu'avec sa **mesure** écrite à côté.
> ⏸ = attend Frédéric (un accord, un geste ou une décision).

**Déjà fait (20/11)**
- [x] Pièce 1 : le collecteur, iad + SAFTI + KW — 437 personnes, contrôle vert
- [x] Correction du chantier : 17 sources de plus, registre public, coordonnées affichées — 1 920
      candidats, 629 joignables, contrôle vert (§11)
- [x] Maquettes : 5 planches, **validées** (§12)
- [x] Plan R1-R7 (§13), révisé : run mensuel bâti comme le reste de l'app
- [x] La délégation (§15) **en vigueur**, et sa garde de session posée — 59 cas sur 59 hors ligne,
      témoin inverse compris ; refus réel prouvé à 18:12:27

**R1 — Les sources restantes** *(local, j'enchaîne)*
- [x] R1.1 Sonder les 8 sites — 5 faisables, 3 écartés (Square Habitat, Guy Hoquet, Immonial) ;
      verdicts au §10
- [x] R1.2 Réessayer Propriétés-privées, une seule fois — toujours aucune connexion (refus noté)
- [x] R1.3 Un lecteur par site faisable — `groupement`, `immodiffusion`, `lucarne`, `liberkeys`,
      `maxihome` (+ la méthode `post` du lecteur poli, pour le formulaire Lucarne)
- [x] R1.4 Lire la région ; contrôle vert — **16 personnes de plus**, sur 18:23-18:41 :
  - Groupement Immobilier 3, Immo-Diffusion 9, Lucarne 1, Liberkeys 2, Maxihome 1 ;
  - Liberkeys : 287 fiches lues, 2 adresses gardées, 285 empreintes seulement ;
  - **contrôle VERT**, export **1 935 lignes** (1 920 + 16 − 1 : la ligne Maxihome remplace celle du
    registre, même SIREN).
  - ⚠ Le témoin positif par source vient avec R2 : le garde-fou prend les 3 plus anciennes fiches
    de chaque source.
- [x] R1.5 §10 et §11 à jour

**R2 — La mise à jour** *(local, j'enchaîne)*
- [x] R2.1 Sauvegarde datée de la base locale, puis les tables.
  - Copie `recrutement_avant_R1_20261120.sqlite`, faite par l'API de SQLite et relue : 2 100
    fiches, intégrité « ok ». ⚠ Ma 1ʳᵉ copie, par fichier, ignorait le journal WAL : refaite.
  - Tables `collecte`, `observation`, `source_etat`, `correction`, `liste_noire`, `evenement_fiche`.
  - Colonnes `etat_suivi`, `etat_depuis`, `absences`, `motif_depart`. ⚠ Le nom n'est pas `etat`,
    parce que l'export joint déjà `entreprise.etat`.
- [x] R2.2 La collecte du 20/11 devient la collecte n° 1 — posée à 18:41:32 : **2 116 observations**,
      toutes les fiches en « présent » (personne n'est « nouveau » dans la collecte de référence)
- [x] R2.3 Les états : nouveau, présent, absent, parti, revenu, changé de réseau, avec la preuve
      positive (404, 410, renvoi vers l'accueil, au plus 50 vérifications par collecte). Une
      entreprise cessée reste signalée par le registre (colonne `entreprise_active`).
- [x] R2.4 Le garde-fou de source : moins de 70 % (sources de 5 fiches et plus), ou moins de 2
      témoins revus sur 3 (sources de 10 et plus), ou aucune fiche lue → MALADE, aucun départ
- [x] R2.5 Le carnet des corrections : il vit à part et s'applique à l'export. La base garde ce que
      dit l'annuaire. 8 champs sont corrigeables.
- [x] R2.6 La liste « ne plus contacter », lue AVANT tout enregistrement. Elle ne contient que des
      empreintes : SIREN, téléphone, e-mail, nom + département.
- [x] R2.7 Essai hors ligne `recrutement/test_mise_a_jour.py` : 4 collectes fabriquées, **tout
      vert**.
  - Cas éprouvés : un site qui casse (3 sur 12) et une source qui perd ses 3 témoins sont déclarés
    MALADES, avec 0 départ.
  - Témoin inverse : une fiche absente de la liste noire reste.
  - ⭐ **Il a trouvé un vrai défaut** : repérer les nouveaux absents par la DATE réécrivait le
    « changement de réseau » à chaque collecte du même jour. Corrigé : on les repère par ce que la
    collecte vient de changer.

**RUN — le lanceur, en essai à blanc** *(local, j'enchaîne)*
- [x] RUN.1 `scheduled/run_recrutement_mensuel.ps1` : 8 étapes (l'export du CSV est devenu la
      sienne).
  - Options : `-DryRun`, `-StartAtLabel` (une étape inconnue lève une erreur), `-Source`.
  - Un verrou garantit un seul run à la fois. Sortie 0 ou 1.
  - Le journal de la tâche ne porte que des comptes ; le détail va dans `recrutement_donnees`.
  - Script enregistré avec la signature UTF-8 (BOM), comme ses voisins ; l'analyse PowerShell ne
    trouve aucune erreur.
- [x] RUN.2 Les battements, la descente et la montée sont coupés par interrupteur :
      `recrutement_donnees\interrupteurs.env`, tout à 0, hors de `.env`.
- [ ] RUN.3 Essai à blanc sur la vraie base — **la tuyauterie est éprouvée le 20/11** :
  - `-DryRun -Source groupement` : les 8 étapes, contrôle VERT, sortie 0, 25 s ;
  - la reprise à « sauvegarde » : sortie 0 ;
  - une étape inconnue : sortie 1, avec l'erreur écrite ;
  - le verrou est retiré dans les deux cas.
  - ⭐ L'essai a trouvé un défaut : la sortie des scripts Python manquait à la transcription de
    PowerShell 5.1. Corrigé en la faisant passer par `Write-Output`.
  - ⏳ **Reste la durée d'une collecte COMPLÈTE** : 2 à 3 h estimées sur le journal du 20/11.
    Relire tous les sites une 2ᵉ fois le même jour doublerait la charge sur eux pour rien. Elle se
    mesurera au **1er run complet** (dimanche 06/12, ou lancé à la main avant). La limite de 8 h
    laisse la marge.

**R3 — La base** *(accord obligatoire)*
- [x] R3.1 Le patch `supabase/patch_recrutement_schema_2026-11-24.sql` (24/11) :
  - le schéma `recrutement` et 6 tables : `fiche`, `entreprise`, `collecte`, `source_etat`,
    `correction`, `liste_noire`. RLS partout, aucun droit pour `public`, `anon` ni `authenticated` ;
  - des **contraintes qui tiennent les règles dans la base** :
    - une fiche collectée est dans les 4 départements. ⚠ Il faut un `coalesce` : un CHECK laisse
      passer un NULL ;
    - une coordonnée porte sa source ;
    - une entreprise en opposition ne garde aucune donnée du registre ;
  - le **robot `recrutement_robot`**, né NOLOGIN : il lit, ajoute et met à jour les 4 tables
    montées, jamais de suppression ; il ne fait que lire le carnet et la liste noire ; il n'a aucun
    droit ailleurs ;
  - `public.rec_etat_collecte()`, le bandeau, réservé aux administrateurs ;
  - les 7 lignes de battement, en `bimonthly`.
  - ⚠ **Le suivi et le fil d'échanges sont reportés au patch de l'écran (R6)** : leurs étapes se
    décideront avec l'écran.
  - Mesuré avant d'écrire, en lecture seule :
    - Supabase ne pose aucun droit par défaut sur un schéma neuf ;
    - l'administrateur se reconnaît à `app_user_profile.role = 'admin'` et à un compte actif ;
    - `app_worker_registry` a 6 contraintes, toutes respectées ;
    - Postgres 17.6 ; l'éditeur peut prendre les rôles `anon` et `authenticated` et créer un rôle.
- [x] R3.2 La répétition et l'inverse.
  - **La répétition** joue d'abord une transaction ANNULÉE, dans la peau de l'app : un
    administrateur lit ; un non-administrateur reçoit « Réservé aux administrateurs » ; la clé
    publique est refusée ; personne ne lit une fiche en direct. Tout écart arrête le script, et
    les personnes sont choisies par la requête, sans identité écrite. Elle montre ensuite un
    tableau de 11 contrôles, dont le témoin inverse : le robot n'a aucun droit sur les tables de
    l'app.
  - **L'inverse** refuse de tourner si l'app a déjà écrit des corrections ou des demandes « ne plus
    contacter ». Il vérifie ensuite qu'il ne reste rien, et que `app_worker_registry` et
    `is_app_admin` sont intacts.
  - **Contrôles hors ligne** : les 7 clés, extraites du patch, sont celles qu'envoie le lanceur ;
    les parenthèses, chaînes et `$$` sont équilibrés.
  - ⭐ **Un vrai défaut trouvé avant le collage** : `app_user_profile.role` est un ENUM, et
    `coalesce(role, '')` aurait fait échouer la répétition → `role::text`.
- [x] R3.3 **POSÉ le 24/11 par Claude, sur l'accord écrit de Frédéric** (*« fais-le toi-même, je te
      donne mon accord »*), par `execute_sql`. Le garde-fou de la session ne l'a pas refusé.
  - Le patch est passé sans erreur, exactement le contenu du fichier.
  - **La répétition : 11 contrôles sur 11 OK**, dont la 1re partie dans la peau de l'app.
  - **Le témoin refait à part**, dans une transaction annulée :
    - l'administrateur reçoit le bandeau `{"fiches": 0, "sources": [], "collecte": null, "par_etat": {}}` ;
    - le non-administrateur reçoit « 42501 Réservé aux administrateurs ».
  - Après coup : le schéma est présent, les 7 battements aussi, et aucune table de témoin ne reste.
  - ⏳ **Témoin inverse à lire demain** : la descente du 25/11 doit compter le même nombre de
    tables qu'avant. Le schéma n'est pas exposé à l'API.

**R4 — La montée et la descente** *(accord pour le premier envoi)*
- [x] R4.0 La connexion du robot, `recrutement/robot.py`.
  - Elle passe par le pooler, avec l'utilisateur `recrutement_robot.<projet>`.
  - Elle lit **seulement** `recrutement_donnees\robot.env`, **jamais** le `.env` du projet.
  - Interprète : le **Python système**, qui a psycopg2 2.9.12 ; le `.venv` ne l'a pas. Le lanceur le
    sait (`$pyBase`, avec une erreur claire s'il manque).
- [x] R4.0 bis **Frédéric a donné son mot de passe au robot le 24/11** avec
      `recrutement/poser_mot_de_passe_robot.ps1`. Vérifié sans jamais l'afficher :
  - `robot.env` complet : hôte du pooler, port 5432, utilisateur, mot de passe de 32 caractères ;
  - en base : `rolcanlogin` vrai, ni BYPASSRLS ni superutilisateur, secret rangé en `SCRAM-SHA-256$` ;
  - le robot se connecte par le pooler : un rôle sur mesure y est accepté.
  - Le script fabrique un mot de passe aléatoire et l'écrit dans `robot.env`.
  - Il ne copie dans le presse-papiers que son **empreinte SCRAM-SHA-256** : le mot de passe ne
    quitte jamais le serveur et Claude ne le voit jamais.
  - ⭐ Calcul de l'empreinte vérifié : PowerShell et Python donnent la même sur 2 essais, dont le
    vecteur « pencil » de la RFC 7677.
- [x] R4.1 `recrutement/descendre.py`.
  - Elle rapporte la liste noire et l'APPLIQUE en local : fiche, observations, événements, adresse
    de page, et entreprise si plus personne ne la cite.
  - Le carnet des corrections remplace le carnet local.
  - Si la base ne répond pas : sortie 1, et le lanceur s'arrête.
  - **Essai hors ligne `recrutement/test_descente.py` : tout vert.** L'essai à blanc ne touche à
    rien. Les 3 personnes de la liste sortent, par téléphone, SIREN et nom. Un autre réseau ne
    peut plus les remettre. Témoin inverse : une personne neuve hors liste entre.
- [x] R4.2 `recrutement/pousser.py`.
  - Des « insert … on conflict do update », en une seule transaction ; jamais de suppression.
  - Le carnet et la liste noire ne sont jamais touchés.
  - Chaque ligne est vérifiée contre les règles du schéma AVANT tout envoi.
  - `--preparer`, sans réseau, sur la vraie base locale : **2 116 fiches, 1 487 entreprises,
    1 collecte, 25 états de source, 0 faute**.
- [x] R4.3 Les contrôles sont codés dans la montée, AVANT la validation ; un rouge ANNULE tout :
  - comptes des deux côtés ;
  - 0 coordonnée iad ;
  - 0 donnée de registre pour une personne en opposition ;
  - 0 personne de la liste noire.
  - Le témoin « effacement » est éprouvé par `test_descente.py`.
- [x] R4.4 **Le premier envoi est fait le 24/11 à 11:30**, sous délégation (§15), par le robot.
  - **D'abord `--essai`** : tout est passé, les contrôles étaient à 0, puis tout a été annulé.
    Témoin : la base a été relue à 0 partout après l'annulation.
  - **Puis le vrai** : 2 116 fiches, 1 487 entreprises, 1 collecte, 25 états de source. Contrôles :
    manquantes 0, en trop 0, iad 0, opposition 0, liste noire 0. Validé.
  - **Recontrôlé à part**, base contre local : les 25 réseaux, les 4 départements (07 346 · 42 891 ·
    43 183 · 63 696) et les 642 joignables sont identiques.
  - Côté base seulement : 2 106 fiches ont une agence GTI la plus proche, et 298 entreprises en
    opposition n'ont aucune donnée du registre.
  - **La descente**, en essai puis en vrai : 0 empreinte, 0 fiche retirée, 0 correction. La liste
    est vide, comme attendu.
  - **Les interrupteurs sont ALLUMÉS** (`interrupteurs.env` : descente, montée, battements à 1).
  - **Cycle éprouvé** `-StartAtLabel controle` : contrôle VERT, export, montée validée, sauvegarde
    relue, compte rendu, sortie 0. Les battements de 4 étapes sont arrivés en « success » dans
    `app_worker_registry`. Les 3 autres parleront au 1er run complet.
  - Défaut d'affichage trouvé et corrigé : les « » de Python étaient déformés dans le journal
    (`[Console]::OutputEncoding` en UTF-8).

**R5 — La tâche, la surveillance, la sauvegarde**
- [x] R5.1 Les 3 ajouts de `check_gti_health.py` (délégué, §15), recopiés du geste du 18/11 :
      fréquence `monthly` (36 j), gravité `warning`, 13ᵉ nom suivi — **AVANT** l'enregistrement.
  - ⚠ Le module de confidentialité refuse de lancer ce fichier, parce qu'il contient l'e-mail
    des alertes.
  - Vérifié donc par relecture du diff (17 lignes ajoutées, 1 retirée), puis par le passage de
    « GTI Health Monitor » de 18:48 : **code 0**, et son journal porte « Tache planifiee GTI
    Recrutement Mensuel : tache introuvable ». C'est l'avertissement voulu tant que la tâche
    n'est pas enregistrée.
  - Le module refuse aussi un `git add` qui nomme ce fichier : **Frédéric l'a commité lui-même le
    24/11 (`98f29f2`)**.
- [x] R5.2 `recrutement/sauvegarder.py` : API de SQLite, copie relue (intégrité + nombre de fiches),
      12 gardées, CSV du mois à côté. **1ʳᵉ copie réelle le 20/11 à 18:41** :
      `C:\Hektor\Backups\recrutement\recrutement_2026-11-20_184149.sqlite`, 2 116 fiches, intégrité « ok ».
- [ ] R5.3 La purge RGPD des 3 ans
- [x] R5.4 `scheduled/installer_tache_recrutement.ps1`, recopié de l'installeur du 18/11.
  - Il enregistre la tâche comme la sœur, puis remplace son déclencheur par le calendrier mensuel
    dans le XML. PowerShell ne sait pas créer un déclencheur mensuel.
  - Il compare ensuite 17 réglages, un par un.
  - Mode `-Essai` vert : le déclencheur est fabriqué et le XML transformé se relit.
- [ ] R5.5 ⏸ **À REFAIRE après le passage à tous les deux mois (24/11)** : Frédéric relance
      l'installeur en administrateur. Il crée « GTI Recrutement » et retire « GTI Recrutement
      Mensuel ».
  - *1ʳᵉ fois, le 24/11 au matin, sous le nom « GTI Recrutement Mensuel » ; relue par moi : état
    « Ready », S4U, PT8H, IgnoreNew, les 12 mois, 1er passage le 06/12 à 10:00.*
  - ⏸ et avant cela, il commite à nouveau `check_gti_health.py`, qui porte le nouveau nom et la
    fréquence `bimonthly`.
- [ ] R5.6 Le premier run réel, puis son contrôle
- [ ] R5.7 Vérifier si l'agent OVH (Veeam) couvre `Backups\recrutement` et `recrutement_donnees`

**R6 — L'écran** *(« vas-y » pour `App.tsx`, accord pour déployer)*
- [ ] R6.1 L'interrupteur `recrutement_visible`
- [ ] R6.2 Le listing, son bandeau de la dernière collecte, « Où recruter »
- [ ] R6.3 La fiche candidat et son parcours
- [ ] R6.4 Les fenêtres Ajouter, Modifier, Retirer
- [ ] R6.5 Les gestes : appeler, e-mail, RDV (+ le filtre `related_entity_id` au backend)
- [ ] R6.6 Contrôle : capture contre maquette, téléphone, négociateur refusé
- [ ] R6.7 ⏸ Le déploiement
- [ ] R6.8 R5 bis : la tâche quotidienne `GTI Recrutement Sauvegarde`, déclarée avant

**R7 — Les fonctions, une par une après décision**
- [ ] R7.1 Le modèle d'e-mail de premier contact
- [ ] R7.2 Le rangement du CV
- [ ] R7.3 Le contrat d'agent commercial et sa signature (chantier à part)
- [ ] R7.4 « Créer son accès à bienvu »
- [ ] R7.5 La notification « nouveaux candidats près de chez toi »

**Les décisions** — prises par délégation le 20/11 (§15), **sauf avis contraire de Frédéric** :
- [x] D1 ~~Le 1er dimanche du mois à 10:00~~ → **changé par Frédéric le 24/11 : le 1er dimanche TOUS
      LES DEUX MOIS** (décembre, février, avril, juin, août, octobre), à 10:00
- [x] D2 La gravité `warning`
- [x] D3 Rubrique réservée aux administrateurs
- [x] D4 La carte dessinée (celle de la maquette, aucune dépendance neuve)
- [ ] D5 Le texte de l'e-mail de premier contact : j'écris un **brouillon**, ⏸ Frédéric le relit
      avant le premier envoi
- [x] D6 L'opposition au registre : la règle d'aujourd'hui
- [x] D7 L'e-mail caché de 3G : non pris

---

## 15. ⭐ LA DÉLÉGATION — EN VIGUEUR depuis le 20/11/2026 au soir (« Oui, pose-la »)

> Sa demande (20/11 soir) : *« je souhaite te donner plus d'autonomie pour que tu finisses ce
> chantier, sauf cas ou problème ; peux-tu me dire comment ? Je souhaite juste de la sécurité pour
> le serveur et le reste de mon app. »* Sa réponse à la proposition ci-dessous : **« Oui, pose-la »**.
> ⛔ **Elle ne vaut que pour ce chantier, et que pour une session inscrite à la garde** (voir plus
> bas). Hors de ce périmètre, la règle du §0 de `CLAUDE.md` s'applique telle quelle.

**⭐ LA GARDE, POSÉE ET PROUVÉE LE 20/11 À 18:12** — elle remplace les « interdits dans les réglages » :
- ⚠ **Pourquoi pas des règles `deny` du projet** : elles s'appliqueraient à **toutes** les sessions
  du projet. Elles auraient interdit à la session du classeur d'écrire dans `phase2/` et `Console/`,
  où elle travaille.
- **La forme retenue** : un crochet `PreToolUse` dans les réglages utilisateur
  (`C:\Users\admin\.claude\settings.json`), qui lance `recrutement/garde_session.py`.
  - Il ne refuse **que** pour les sessions listées dans
    `C:\Hektor\recrutement_donnees\garde\sessions.txt`.
  - Chaque refus est écrit dans `garde\refus.txt`.
  - En cas d'erreur interne, il **refuse** pour une session gardée et **laisse passer** les autres.
- **Essai hors ligne : 59 cas, 0 rouge** (`essai_garde.py`, dans le brouillon de la session), dont
  le **témoin inverse** : service, `phase2/`, push et migration venus d'une autre session passent.
- **Preuve en réel** : `echo "… git push"` lancé par cette session a été **refusé** (18:12:27).
- ⛔ **Une nouvelle conversation sur ce chantier s'inscrit d'abord** : elle ajoute son identifiant
  à `sessions.txt`, et le prouve par le même essai. Sans cela, la délégation ne vaut pas pour elle.
- Pour la **retirer** : vider `sessions.txt`, ou enlever le bloc `hooks` des réglages utilisateur.
- ⚠ **C'est un garde-fou, pas un bac à sable** : une écriture déguisée, comme un script qui ouvre
  un fichier, peut lui échapper. La règle écrite reste la vraie limite.

**Ce que je ferais seul, sans redemander** — et seulement dans ce périmètre :
- écrire tout le code NEUF du chantier : `recrutement/`, les deux scripts `scheduled/*recrutement*`,
  les patchs `supabase/patch_recrutement_*`, les fichiers d'écran neufs ;
- trois retouches de fichiers existants, en ajout seulement :
  - `check_gti_health.py` : 3 lignes ;
  - `App.tsx` : 6 points, derrière l'interrupteur ÉTEINT ;
  - le backend : un paramètre facultatif, comportement inchangé sans lui ;
- lancer le collecteur et le run en local, réparer un lecteur, cocher le §14 avec ses mesures ;
- commiter les fichiers du chantier, un par un, jamais `git add .` ;
- prendre les décisions D1 à D7 selon mes recommandations, sauf avis contraire de Frédéric :
  - D1 : 1er dimanche, 10:00 ;
  - D2 : `warning` ;
  - D3 : administrateurs seuls ;
  - D4 : carte dessinée ;
  - D5 : le texte est un brouillon qu'il relit avant le premier envoi ;
  - D6 : la règle d'aujourd'hui ;
  - D7 : non pris.

**Ce qui reste à Frédéric, par construction** — ce sont les seules portes entre le chantier et le reste :
1. coller le patch de la base (une fois, R3) : l'outil refuse d'écrire en production, même avec un oui ;
2. pousser (2 ou 3 fois) : un push redéploie toute l'app, et l'outil le refuse aussi ;
3. enregistrer la tâche (une commande en administrateur) : mon terminal n'est pas administrateur ;
4. tout envoi d'e-mail à un candidat : c'est lui qui clique, jamais un automate.

**Les garde-fous techniques** (ils tiennent même si je me trompe) :
- **la garde de session** (ci-dessus, posée). Elle me bloque sur :
  - redémarrer ou arrêter un service ;
  - créer, modifier ou supprimer une tâche planifiée ;
  - `git push`, `reset --hard`, `rebase`, `clean` ;
  - écrire dans `Console/` (le worker), `phase2/`, `.env`, les scripts planifiés existants, le reste
    de `monitoring/`, les patchs `supabase/` existants, les réglages de Claude Code et la garde ;
  - tuer un processus, installer un logiciel, toucher au registre, au pare-feu ou aux droits ;
  - `stash`, `checkout`, `switch`, `pull`, `merge`, `add .`, `commit -a` : le dossier est partagé
    avec l'autre session ;
  - les outils de déploiement (Vercel), de migration Supabase, et les tâches planifiées de Claude.
- **un robot à clé restreinte** : la montée et la descente du recrutement passent par un rôle de
  base qui n'a de droits **que sur le schéma `recrutement`**. Frédéric pose lui-même son mot de
  passe. Un défaut du pousseur ne peut donc toucher aucune autre table. Les battements gardent
  `heartbeat.py`, comme partout.
- **les interrupteurs du chantier dans un fichier à lui**, `recrutement_donnees\interrupteurs.env`,
  et non dans `.env`, qui reste intact.
- **le serveur** : le collecteur ne télécharge et n'exécute jamais rien, il lit du texte. Aucun
  logiciel n'est installé sans demander. Ses données restent hors du dépôt.

**Les cas où je m'arrête et préviens** :
- un contrôle rouge que je ne sais pas expliquer ;
- un site qui nous refuse : on abandonne la source, on ne contourne jamais ;
- tout besoin de toucher hors du périmètre (une table existante, Hektor, le worker, le run de nuit,
  un service, une autre tâche) ;
- une question juridique : une donnée d'un genre nouveau, un contact caché ;
- un rouge ailleurs dans la surveillance après un de mes changements ;
- un conflit avec l'autre session sur un fichier partagé.

---

## Journal

- **20/11/2026** — demande de Frédéric ; sonde de lecture (robots.txt de 10 réseaux, plans de
  site iad / SAFTI / Capifrance, une fiche iad, une fiche SAFTI, mentions légales iad, un essai
  de l'API Recherche d'entreprises). Cette note écrite. **Rien d'autre.**
- **20/11/2026, 2e message** — périmètre « notre région d'abord », réseaux iad / SAFTI / KW.
  Mesures : agences lues en base (4 départements), comptes iad par département (321), forme des
  pages SAFTI par commune, plan de site et agences KW. Section 7 écrite. **Rien codé.**
- **20/11/2026, journée** — pièce 1 (collecteur, 3 réseaux), correction du chantier (coordonnées
  affichées, 17 sources de plus, registre public), collecte finie à 12:28 (1 920 candidats, contrôle
  vert), maquettes (§12) **validées par Frédéric**, plan de développement R1 à R7 (§13). Rien en base,
  rien déployé, rien commité.
- **20/11/2026, soir** — Frédéric : **collecte mensuelle**, et une architecture **comme le reste de
  l'app** (tâche Windows, run, mise à jour, surveillance). Relu sur le serveur :
  - les 13 tâches et leurs déclencheurs ; le calendrier de `Hektor-IngestSemestriel` ;
  - le patron installer et lanceur (`installer_tache_menage_temporaires.ps1`,
    `run_menage_temporaires.ps1`, `run_nuit_contacts_et_recherches.ps1`, `run_backup.ps1`) ;
  - `heartbeat.py` ; dans `check_gti_health.py`, `TASK_CRITICALITY`, la liste des 12 tâches
    suivies et `WORKER_STALE_POLICY` (pas de fréquence mensuelle : un seuil par défaut aurait
    crié dès le 2ᵉ jour).
  
  Réécrits : §13.1 (le run en 7 étapes, chaque brique avec son modèle), R2 (preuve positive de
  départ), R3 (les 7 lignes de battement), R4 (montée ET descente), R5 (run, tâche, surveillance
  `warning`, sauvegarde, R5 bis quotidien), R6 (bandeau), §13.3. Rien codé.
- **20/11/2026, soir (2)** — à la demande de Frédéric, **§14 : la liste des tâches**, la seule
  liste à cocher du chantier (4 faites, 42 à faire, 7 décisions). Rien codé.
- **20/11/2026, 18:12** — **délégation acceptée** (« Oui, pose-la », §15). La garde de session est
  posée : `recrutement/garde_session.py`, avec un crochet dans les réglages utilisateur.
  - Pourquoi pas des règles `deny` du projet : elles auraient bloqué l'autre session.
  - Essai hors ligne : 59 cas sur 59, témoin inverse compris. Refus réel prouvé à 18:12:27.
  - D1 à D7 sont prises par défaut, sauf D5, qui reste un brouillon à relire.
- **20/11/2026, 18:15-18:45 (délégation)** :
  - **R1** : 5 sources sondées et lues, +16 personnes (export 1 935 lignes, contrôle VERT) ;
    4 sources écartées. Le témoin iad est sorti du code, vers `recrutement_donnees\temoins.txt`.
  - **R2** : codé, éprouvé hors ligne (tout vert, un vrai défaut trouvé et corrigé). Appliqué à la
    vraie base : collecte n° 1 = 2 116 observations.
  - **RUN** : le lanceur mensuel est éprouvé à blanc ; un défaut de transcription trouvé et corrigé.
  - **R5** : la tâche est déclarée à la surveillance ; installeur `-Essai` vert ; 1ʳᵉ sauvegarde
    réelle.
  - Rien en base, rien chez Hektor, aucune tâche enregistrée.
  - **Commit `5e68fbd`** (7 fichiers, ajoutés un par un ; l'index relu avant). `check_gti_health.py`
    reste à commiter par Frédéric.
  - Les noms réels laissés en exemple dans trois commentaires ont été remplacés avant le commit.
- **24/11/2026** — Frédéric a fait ses deux gestes :
  - le commit de la surveillance, `98f29f2` ;
  - l'enregistrement de « GTI Recrutement Mensuel », relu réglage par réglage, avec un 1er
    passage le **06/12 à 10:00**.
  - La garde de session est re-prouvée après la reprise de la conversation : un faux push est
    refusé.
  - Le 1er run fera une collecte **locale** seulement (interrupteurs à 0) et mesurera la durée
    d'une collecte complète (RUN.3).
- **24/11/2026, 11:00** — Frédéric : *« peut-on le passer à tous les 2 mois »*. Fait, sous
  délégation (le détail est en tête du §13.1) :
  - l'installeur : les 6 mois pairs depuis décembre ; il retire l'ancienne tâche et vérifie l'ordre
    des mois et l'absence de l'ancienne ; `-Essai` vert ;
  - le lanceur renommé `run_recrutement.ps1` (`git mv`) ; l'analyse PowerShell ne trouve aucune
    erreur ;
  - la surveillance : « GTI Recrutement », `bimonthly` = 64 jours ;
  - la sauvegarde : 6 copies gardées.
  - ⏸ Deux gestes reviennent à Frédéric : recommiter `check_gti_health.py`, puis relancer
    l'installeur.
- **24/11/2026, après-midi** — **R3 posé en base** par Claude, sur l'accord écrit de Frédéric.
  Répétition 11/11 ; le témoin administrateur / non-administrateur est refait à part. Détail en
  R3.3. Prochaine étape : R4, la montée et la descente par le robot.
- **24/11/2026, 11:30** — **R4 fini**.
  - Frédéric a posé le mot de passe du robot : seule l'empreinte est sortie du serveur.
  - Premier envoi : essai annulé, puis le vrai, avec les contrôles à 0 et le recontrôle base contre
    local identique.
  - La descente est verte. Les interrupteurs sont allumés, et le cycle est éprouvé avec ses
    battements.
  - Le run du 06/12 fera donc tout seul : descente, collecte, mise à jour, contrôle, montée,
    sauvegarde.
