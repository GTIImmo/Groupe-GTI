# Recrutement — nouvelles sources possibles (recherche du 24/11/2026)

> Demande de Frédéric (24/11, ~16:10) : refaire une collecte d'essai « et en profiter pour ajouter des sites » —
> « les réseaux de mandataires présents dans les 4 départements, ou des agences locales avec un annuaire de
> collaborateurs ». Recherche web en LECTURE SEULE (2 à 4 pages par site, rien collecté, aucun nom de personne
> noté). ⏸ **Rien n'est codé : Frédéric choisit.** Chantier : `notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md`.

**Le constat** : les 25 sources déjà lues couvrent l'essentiel des mandataires de la région (témoin : MeilleursRéseaux,
pages par département — 437 dans la Loire, 402 dans le Puy-de-Dôme, 259 en Ardèche, 91 en Haute-Loire). Les réseaux
restants pèsent ~150 personnes en tout. **Le meilleur rendement est chez les agences locales** : deux fournisseurs de
sites (La Boîte Immo, Netty/Modelo) en équipent beaucoup, avec une page « équipe » toujours bâtie pareil → un lecteur par
fournisseur. Écartés inchangés : Efficity (robots.txt « Disallow: / »), Keymex (absent des 4 départements).

## A. Réseaux de mandataires non couverts

- **Les Porteclés** (~18, surtout Ardèche) — robots.txt « Disallow: / » pour tous → **impossible**.
- **Ikami** (~16, surtout Ardèche) — liste chargée en JavaScript, pas de robots.txt → **à vérifier** (contacts en clair ?).
- **TeamFi / Team France Immobilier** (~8-10 : 63, 43, 07) — nom, fonction, téléphone en clair, e-mail derrière un bouton ;
  robots.txt « Crawl-delay: 5 » ; site Netty → **faisable**.
- **Gateway Immobilier** (13, Puy-de-Dôme) — noms, téléphone derrière un bouton → **noms seulement**.
- **Immo Réseau** (~6) — numéro encodé, e-mail par formulaire → **à vérifier, faible**.
- **We Invest** (5, Ardèche, sur 23 pages) — robots.txt autorise → **faisable mais cher pour 5**.
- **Casarèse** (~6, Ardèche) et **AXO** (~4, Puy-de-Dôme) — sites Adapt Immo, téléphone en clair → **faisable, très peu**.
- **MeilleursBiens** (~4), **AgentMandataire.fr** (4, noms seulement), **Teatime Immo** (2, Netty), **Effectimmo** (~4, à vérifier).
- **E-mobilier.fr** (4, Loire) — HTTP 403 → **impossible en l'état**. AV Transaction et une dizaine de très petits
  réseaux (2 à 5 personnes chacun) : site non trouvé, **non vérifiés**.

## B. Agences locales avec une page « équipe »

- **Loire** : **Ginet Immobilier** (Roanne, ~32 rattachés à l'agence de Roanne, téléphone + e-mail ; inclut sans doute
  gestion et syndic → filtrer la transaction) — la plus grosse équipe trouvée ; **42bis Immo** (Roanne, 10, La Boîte Immo) ;
  **Henri Pardon** (Saint-Étienne, 3). Sans intérêt ou impossible : Cogecoop (2 dirigeants seulement), Fides Hermes (404),
  Chalton Dubanchet (site indisponible), Lyaudet Drajnudel / HB Immo / Di Gusto (défi anti-robot AWS), Curtis, Serre,
  Dugourd, Horizon, Immoreve (page équipe vide) ; Giraud Immo (équipe chargée à part, à vérifier).
- **Puy-de-Dôme** : **Vos Agents** (Clermont, 10, téléphone + e-mail, La Boîte Immo) ; **iMMO.PRO Consultants** (~10, noms) ;
  **EID Immobilier** (5-6) ; **Fontana Immobilier** (Châtel-Guyon, 10, téléphone, Netty) ; **Chauvel** (2), **Cantard** (1).
  ⛔ **Domia** : ses mentions légales interdisent la reproduction des données → **impossible sans autorisation**.
  Impossibles : AU16IMMO (robots.txt interdit les pages équipe), Régie Emery (« Disallow: / »), Okey et Comme chez vous
  (défi AWS). Sans équipe : Accord Immobilier, Bostimmo ; six sites La Boîte Immo non testés.
- **Haute-Loire** : **Roche Immobilier** (Brioude, 6) ; **Mon @gence Immobilière** (Brioude, 8 — relire ses mentions légales
  d'abord : même fabricant que Domia) ; **Brioude Immobilier** (~6, noms) ; **Pietrapolis** (agence du Puy, à vérifier).
  Impossible : Gibert (défi AWS). Immobilière 43 (directrice seule), JB Transactions (pas de réponse).
- **Ardèche** : **Agence Thomas** (Aubenas, ~4, e-mail + téléphone) ; **STB Immobilier** (Le Pouzin, 7) et **KB Immobilier**
  (Privas, 4), Netty ; **Bel Ange** (Ruoms, ~5, noms). Sans résultat : Annonay Immobilier, JP Immobilier, Eurosud ; à vérifier :
  Immobilier MG, IRS Immobilier.

**Les fournisseurs** : **La Boîte Immo** (~25 des 60 sites testés ; page `/equipe/` ; 3 gabarits ; même robots.txt partout,
qui ne bloque pas) ; **Netty/Modelo** (page `/conseillers` rendue côté serveur, données structurées nom/fonction/
téléphone/code postal, e-mail derrière un bouton ; « Crawl-delay: 5 ») ; Adapt Immo (Casarèse, AXO) ; Agence IE (Domia,
Mon @gence) ; plusieurs sites derrière un défi AWS (fournisseur commun probable, non vérifié).

## C. Autres annuaires

- **MeilleursRéseaux** : pas de noms, des COMPTES par réseau et département — un bon témoin de couverture.
- **FNAIM** (pages par département : 26 / 17 / 50 / 50 agences) : représentant légal et site web — **excellent pour
  TROUVER les sites d'agences**, pas d'équipe.
- **RealAdvisor**, **Immodvisor** : agents nommés par commune, toutes enseignes ; robots.txt et conditions à relire → à vérifier.
- Impossibles : fichier des cartes professionnelles de la CCI (défi Cloudflare), Zimo (Cloudflare), MeilleursAgents
  (robots.txt interdit ces pages).

## Les 5 recommandations (effort / personnes)

1. **Un lecteur La Boîte Immo** (page `/equipe/`, 3 gabarits) : ~45 personnes déjà repérées, la plupart avec téléphone et
   e-mail en clair, et une quinzaine de sites du même fournisseur à tester.
2. **Un lecteur Netty/Modelo** (page `/conseillers`) : ~30 personnes avec téléphone (Fontana, STB, KB, TeamFi, Teatime).
3. **Ginet Immobilier** (Roanne) : une page, ~32 personnes ; filtrer les métiers de la transaction.
4. **Les pages isolées** : iMMO.PRO, Mon @gence (après ses mentions légales), EID, Agence Thomas.
5. **Gateway** (noms seulement), puis **Ikami** (à vérifier dans un navigateur).

## ⚠ À trancher par Frédéric avant de coder

- Le **périmètre** : les équipes d'agences sont souvent des **salariés** (pas des agents commerciaux) — les solliciter
  est une décision commerciale, et certaines équipes mêlent gestion, syndic, accueil (à filtrer sur la transaction).
- Les sources « **noms seulement** » (sans contact en clair) ont peu d'intérêt pour un premier contact par e-mail.
- Chaque site retenu : **relire ses mentions légales** (cas Domia) et son robots.txt au moment du lecteur.
