# Plan de développement actualisé — 20/08/2026

Remplace le plan du 18/08. Établi après quatre audits mesurés :
identifiants (19/08), workers (20/08), diffusion (20/08), contacts et modales (20/08).

> **Dernière mise à jour : 08/10/2026** — **AUDIT PAR OBJET** refait
> (`notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md`) et section **« 🧭 LES CHANTIERS DE L'ÉTAPE 2 »**
> (8 chantiers, avec leur suivi), qui remplace les 46 chapitres.
> *(Mise à jour précédente : 07/10/2026)* — l'AUDIT COMPLET est intégré : section
> « 🔎 L'AUDIT COMPLET DU 07/10 » sous les lots, L1 et L2 rouverts, lot **L10** créé.
> *(Mise à jour précédente : 20/09/2026)* — la CHARTE DE L'ÉTAPE 2, le JOURNAL DES
> DÉCISIONS et LES DIX LOTS ouvrent ce document.
> *(Mise à jour précédente : 18/09/2026)* — « MISE À JOUR DU 18/09 » ci-dessous : la liste ① relue contre le code.
> *(Mise à jour précédente : 03/09/2026.)* C.19-d requalifié en **« LE REGISTRE DES
> TRANSACTIONS »** après audit complet — voir la révision ③ du 03/09 dans
> « L'ordre retenu », et le détail item par item dans la liste, section « 2 ter ».
> *(Mise à jour précédente : 28/08 — voir « CE QUI A BOUGÉ LES 27-28/08 ».)*

---

## 🧭 LA CHARTE DE L'ÉTAPE 2 — *validée par Frédéric le 20/09/2026*

> **La cible.** Mon logiciel métier assure **toutes ses fonctions actuelles sans Hektor**,
> sauf trois : **le numéro de mandat**, **la signature électronique**, **les passerelles
> publicitaires**. Hektor devient une copie **tenue à jour par nos workers**, et il fait
> remonter certains éléments.

**Les cinq règles**

1. **L'app fait autorité** : une saisie ne se perd jamais et ne s'écrase jamais.
2. **Hektor ne remonte que s'il diffère réellement** de ce que l'app lui a envoyé. Égal =
   confirmation. Différent = vraie modification : on la reprend **et on la signale**.
3. **Certains gestes sont des mises à jour sans retour** — on envoie, on n'attend ni
   confirmation ni remontée. *Premier cas tranché : l'archivage d'une recherche.*
4. **Tant que la diffusion passe par Hektor, Hektor doit rester à jour.**
5. **Un numéro ne se perd jamais · une action a toujours une fin visible · le miroir se met
   à jour, il ne se remplace pas.**

**Hors périmètre de l'étape 2** — les **leads** (chantier suivant) · la création d'un
**collaborateur** (passe par Hektor) · le **numéro de dossier** EM…/VA… (Hektor le fournit
tant qu'il vit) · tout ce qui relève de la coupure (A.1, A.2, extinction du miroir, jour J).

---

## 🗒 LE JOURNAL DES DÉCISIONS — *une ligne par décision, il fait foi*

*Posé le 20/09 : les décisions vivaient dans le chat, les commits et la mémoire. Quand une
question semble revenir, c'est ici qu'on regarde avant de la reposer.*

| Date | Décision |
|---|---|
| 20/08 | **Les recherches ne remontent plus à Hektor** — la modale n'exprime que 7 critères sur 12, les renvoyer les appauvrit |
| 24/08 | **À l'étape 2, les négociateurs n'ouvrent plus Hektor** |
| 25/08 | La bascule de la clé des contacts est **séparée** de la doublure : c'est un second chantier *(il s'appelle **5b**)* |
| 28/08 | Le registre des mandats doit devenir **un vrai registre**, avec trois couches de numérotation *(Hektor · PROTEXA · app)* |
| 14/09 | **La répartition de commission reste dans l'app** : rien ne part chez Hektor |
| 15/09 | Une répartition **saisie dans l'app écrase** toute modification venue de Hektor |
| **19/09** | **DÉFINITION DE L'ÉTAPE 2** *(charte ci-dessus)*. L'app reprend une mise à jour de Hektor **seulement si elle diffère réellement** |
| 19/09 | Les **leads** sont un chantier séparé, **après** celui-ci |
| 19/09 | Un **nouveau collaborateur** se crée dans Hektor : le worker agit en son nom |
| **20/09** | **L'archivage d'une recherche continue de partir chez Hektor** — utile à la typologie des transactions ; l'erreur en cas de recherches multiples est **acceptée** ; **aucun retour attendu** |
| 20/09 | Une recherche créée dans Hektor entre dans l'app par le **passage en acquéreur** *(livré, `d7a3586`)*. Pas de balayage tournant. Le **rattrapage global** reste pour avant la coupure |
| 20/09 | **Une étape non surveillée doit au moins avoir une sonde** *(`fb6abbd`)* |
| 20/09 | **Le registre électronique des mandats remplacera PROTEXA** — étudié **juste avant la coupure** *(lot L9)* |
| 20/09 | **La méthode de travail** : auditer → expliquer → coder → contrôler → mettre à jour le plan → suivant. Feu vert **au cas par cas selon le risque** *(voir `CLAUDE.md` §0)* |
| **21/09** | **L'identité et la cible se séparent — option B.** Plutôt que de basculer les 340 endroits qui relient nos données *(6 à 9 j, échecs silencieux)*, on ne touche qu'aux **88 qui visent Hektor**. `hektor_contact_id` devient **l'identité**, `hektor_target_id` **le numéro pour viser Hektor**. C'est E.4/6.2, avancé. ➡ **4-suite devient sans objet** : les 500 000 lignes accrochées aux recherches ne bougent pas |
| **21/09** | **Pendant toute la migration, les commerciaux saisissent encore dans Hektor.** L'app et le serveur doivent continuer d'être alimentés par lui **sans interruption**. Rien de ce qu'on construit ne doit inverser le courant aujourd'hui |
| **21/09** | **UN AUDIT BALAIE LES OBJETS ET LES GESTES.** Un audit qui n'avait mesure que la MODIFICATION d'une annonce (53 champs) a manque les **167 champs de la CREATION**. Frederic : *« tu vas trop vite dans tes audits, il faut les rendre plus approfondis »*. ➡ Tableau obligatoire **objets × gestes** avant toute conclusion, une case non mesuree se DIT *(voir `CLAUDE.md` §0)* |
| **21/09** | **PREMIER CONTACT NÉ DANS L'APP, EN RÉEL** *(« Jean ESSAI L4B », 13:06)*. Chaîne complète en **36 s** : fiche visible dans l'app en **5 s** avec l'identité **10 000 001** *(la plage app)*, Hektor crée **605450** en 18 s, recherche acquéreur partie avec *(commune Dunières)*, resynchronisation à 13:06:47. ⚠ **Deux défauts trouvés** : ① la case cible est restée **vide** — le PATCH portait `updated_at`, colonne absente de `app_contact_current`, PostgREST a rejeté le tout en 400 *(corrigé : on n'envoie plus que `hektor_target_id`)* ; ② **deux fiches pour une personne** — le retour de synchronisation pousse 605450 comme une identité neuve, **rien ne lui dit que 605450 EST 10 000 001**. ➡ ② est un défaut de conception, pas un bug : il reste ouvert |
| **21/09** | **LA SUBSTITUTION D'IDENTITÉ SE FAIT DANS LE BUILD, PAS DANS LE PUSH.** J'avais annoncé une traduction au moment d'envoyer : **c'était faux et dangereux**. Les clés des relations et des recherches ne *contiennent* pas le numéro de contact, elles sont **calculées dessus** *(`relation_key = stable_hash({"contact_id": …})`)* — traduire après coup laisserait empreintes et colonnes sur deux numéros différents, et le run suivant **supprimerait** ces lignes en les prenant pour des disparues. ➡ La substitution a lieu **à l'entrée du build**, avant tout calcul, alimentée par une correspondance redescendue de Supabase *(la case cible)*. **Aucun remue-ménage** : elle ne concerne que les fiches dont l'identité diffère de la cible — 2 sur 356 002 |
| **21/09** | **UNE PERSONNE, UN NUMÉRO — la doublure du contact devient l'identité *(lot L4-c, AVANT C.9)*.** La mesure refaite après l'option B : le coût du **code** s'est effondré *(la substitution écrite le 21/09 EST le mécanisme ; sa table de correspondance passe de 1 ligne à 356 111)*, et les « 599 221 lignes » n'en étaient pas — **505 210 sont recalculables**, **92 655 sont refaites chaque nuit**, **il en reste 1 356 saisies par des humains**. ⚠ **Le risque n'est pas le volume, c'est le COUPLAGE** : aucune clé étrangère, et la reconstruction nocturne est un DELETE+INSERT — code et données doivent tomber **la même nuit** *(précédent du 01/08 : 1 104 recherches absentes, 13 384 rapprochements orphelins)*. ➡ `notice/MESURE_BASCULE_CLE_CONTACT_2026-09-21.md` |
| **21/09** | ⚠ **LE REGISTRE DES RECHERCHES DOIT BOUGER AVEC LE CONTACT, PAS APRÈS** *(trouvé parce que Frédéric a exigé un audit : « les recherches ne fonctionnent pas comme le reste »)*. Le nom d'une recherche est le haché de **tout son contenu** ; ce qui le rend stable est un mécanisme **extérieur** — `app_search_registry` **fige** le nom et le redonne à chaque run — et son ancrage est la paire **`(hektor_contact_id, rang)`**, donc une **position**. Si l'identité change sans que le registre suive, **aucune recherche n'est reconnue le lendemain** : 11 368 clés neuves, et tout ce qui pend dessous orphelin, **sans un bruit**. ✅ Le registre est déjà prêt *(`app_contact_id` rempli 77 065/77 065 réels, index unique `(app_contact_id, rang)` posé)* : **le changement tient en une ligne** |
| **22/09** | **LES DEUX SÉRIES DE NUMÉROS DE CONTACT SE RECOUVRAIENT — c'est réparé.** Mesuré par deux chemins indépendants : **194 683 numéros** existaient dans les deux séries en désignant des personnes **différentes**, et seulement 4 contacts où les deux coïncidaient. Rien n'était cassé *(chaque lecteur nomme sa colonne)*, mais **j'étais à une ligne d'écrire le lecteur tolérant** qui aurait rendu la mauvaise fiche 194 683 fois, sans trace. ➡ **La doublure est montée de +10 000 000** : sous 10 M c'est Hektor, au-dessus c'est nous — **un numéro dit enfin d'où il vient**. Fait le 22/09 : **244 834 lignes** côté serveur, **463 543** en local, build complet par-dessus, **0 clé changée**, local et Supabase **d'accord**. ⚠ Les 2 contacts d'essai ont été supprimés pour libérer la plage. Retour arrière : `--annuler` / `p_sens = -1` |
| **22/09** | ⚠ **TROIS DÉFAUTS DANS MON PROPRE SCRIPT, TOUS TROUVÉS PAR LA RÉPÉTITION SUR COPIE** — et aucun n'aurait planté : ① le garde-fou de collision était **par table** alors que l'espace des numéros est **global** *(le contact n°1 serait tombé sur un numéro pris dans une AUTRE table)* · ② les tables de **sauvegarde** étaient décalées avec les autres · ③ j'écrivais dans **20 copies de Supabase** que la descente de 7 h 30 aurait effacées en silence — la règle était pourtant écrite depuis le 21/08 en tête de `pull_from_supabase.py`. ➡ **Les trois auraient fait des dégâts muets. C'est exactement pour ça qu'on répète sur une copie.** |
| **22/09** | ⛔ **LE RUN MOURAIT D'IMPATIENCE, PAS DE HEKTOR.** Un run est mort après 48 min sur **une** page du listing des archivées *(1711 sur ~1888)* qui a renvoyé **500**. Analyse : **pas une page empoisonnée** — les 20 mêmes annonces avaient été lues sans problème à 04:24 le matin même, c'était le **seul 500 en 30 jours**, et Hektor répondait parfaitement à la seconde d'avant. ⛔ **Le défaut était chez nous** : les 4 tentatives tenaient dans **2,5 secondes**. ➡ **2 s · 8 s · 30 s**, soit 40 s — et le run relancé est **passé** *(85 min sur la même étape)*. ⚠ Le nombre de tentatives ne bouge pas *(leçon de « l'amplification par 16 », 07/09)*, et **les 403 lèvent toujours immédiatement** : la patience ne vaut que pour les 5xx. ⛔ **Frédéric a REFUSÉ d'isoler l'étape des archives** — *« il n'y a pas de raison que cette partie du run plante »* : on ne masque pas une panne, on rend le run capable d'y survivre. Contrôle : `phase2/checks/test_patience_hektor.py`, faux serveur, n'appelle jamais Hektor |
| **22/09** | ⛔ **MON PROPRE DÉCALAGE AVAIT CASSÉ LE COULOIR DU REGISTRE — deux défauts muets.** ① `registre_contacts.py` cherchait « le plus grand numéro **sous** 10 000 000 » ; la doublure étant montée au-dessus, plus rien ne passait le filtre et le prochain contact aurait reçu **1**, puis 2, 3 — **et l'INSERT aurait réussi**, les numéros 1 à 100 étant libres depuis le décalage. ② Retirer le filtre ne suffisait pas : le registre **local** et le distributeur **Supabase** auraient donné `10 356 138` **à deux personnes différentes**. ➡ **Trois étages** : `< 10 M` Hektor · `10 M–20 M` la doublure · `≥ 20 M` les contacts nés dans l'app. **Prouvé en réel le 22/09** : 12 contacts livrés par Hektor ont reçu **10 356 138 à 10 356 149**, et 0 sous 1 000 000 |
| **22/09** | ⛔ **SANS LA CASE CIBLE DANS LA COUCHE, LA BASCULE COUPAIT TOUT HEKTOR.** Le push écrit en **fusion**, donc une colonne absente est préservée — rassurant et **hors sujet** : la bascule ne modifie pas une ligne, elle **change sa clé**. `605449` devient `10356127`, qui n'entre en conflit avec rien → **ligne neuve, sans cible** ; le déclencheur ne la remplit pas *(il ne le fait que sous 10 M)* ; et l'ancienne, n'étant plus produite, est **supprimée**. ➡ 62 000 lignes remplacées, **toutes sans cible**, plus un contact joignable — **sans une erreur**. ✅ **Corrigé** : la couche porte `hektor_target_id` *(= le numéro du miroir, capturé à l'instant où l'identité le remplace)*, et le push le transporte tout seul *(`SELECT *`)*. **Éprouvé sur la vraie base sans un appel à Hektor : 59 217 contacts, 59 217 avec leur cible** |
| **22/09** | ⚠ **MA DEUXIÈME ERREUR ARRIVÉE EN PRODUCTION** *(la 1re : `updated_at`, 21/09)*. J'ai lancé le push **sans les options du run de nuit** → **7 201 recherches archivées supprimées** de Supabase. Vu dans le compte-rendu du push, drapeau manquant identifié *(`--include-archived-searches`, dont le commentaire du script dit exactement pourquoi il existe)*, **réparé en 3 minutes**, et confronté ligne à ligne : serveur **11 269 dont 4 182 actives**, Supabase **11 269 dont 4 182 actives**, orphelins **0**. ➡ **C'est mot pour mot la faute écrite en tête de la liste** — *« rejouer un run en recopiant ses ÉTAPES sans son ENVIRONNEMENT »*. Je l'avais citée le matin même. **RÈGLE : écrire la commande complète, avec toutes ses options, et la MONTRER avant de l'exécuter** |
| **21/09** | **PAS D'INTERRUPTEUR — la règle est permanente et symétrique.** Saisir dans Hektor **ou** dans l'app doit fonctionner, des deux côtés, dès maintenant ; ce qu'on interdit, c'est de saisir **des deux côtés à la fois sur le même champ**. L'arbitre est donc **la récence**, toujours, et non une bascule d'autorité datée. ➡ **Le contrat d'autorité ne sert qu'aux champs EXCLUSIFS à l'app** *(ceux que Hektor ignore)* — il reste vide côté annonce tant qu'il n'y en a aucun |
| **24/09** | ⛔ **LE PREMIER RUN APRÈS LA BASCULE A DOUBLÉ 294 179 IDENTITÉS** dans le registre local — le registre était juste, le build aussi : c'est leur **désaccord de portée** *(registre traduit en entier, correspondance descendue du seul périmètre éligible)* qui a fait le dégât. Réparé, cause fermée *(la correspondance vient d'abord du registre local)*, contrôle `registre_couche_desaccord` **chaque nuit** *(`f974ef9`, `376dc7b`)*. **Leçon : un contrôle vérifie que deux côtés sont D'ACCORD, pas qu'un mécanisme existe** |
| **24/09** | **C.9 : l'ordre est fixé par un audit en deux passes.** D'abord **le serveur apprend le numéro de l'annonce avant le bootstrap** *(sinon le run de nuit lui donne un second numéro, dans le cas NORMAL)*, puis **l'œil** *(accord serveur ↔ Supabase)* et **la protection au push** ; la RPC de création **ensuite seulement**, drapeau éteint. **Pas de porte worker** pour l'annonce : ses deux numéros vivent dans deux colonnes. ➡ `notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md` |
| **24/09** | **C.9 : e AVANT d** *(accord de Frédéric)*. d et f préparent la **coupure** — tant que Hektor vit, le lien d'une annonce née dans l'app revient par le miroir ; e est le livrable de l'étape 2. Et **d vivra DANS le build** : la clé d'un lien ne se recalcule depuis la table que pour 57 % des lignes (le rôle est réécrit après le hache, `build_contacts_layer.py` l. 1107) |
| **24/09** | ⛔ **D8 — le rafraîchissement effaçait le numéro de l'app une minute après la création** (`reconcile_annonce_dossiers` le prenait pour un fantôme). Corrigé par **e1** (le rafraîchissement adopte) et **e2** (le worker pose le numéro Hektor sur notre ligne AVANT de rafraîchir) |
| **24/09** | ✅ **PREMIÈRE ANNONCE NÉE DANS L'APP, EN RÉEL** : « ESSAI C9 bis », **10 000 000 ↔ Hektor 63147**, un seul numéro dans Supabase et sur le serveur. **Les patchs SQL de production sont appliqués par Frédéric** : l'écriture par l'outil de la session est bloquée par son garde-fou |
| **24/09** | ⛔ **L4-c-bis AVANT LA SUITE DE C.9** *(décision de Frédéric, 14 h 45)* : les contacts créés chez Hektor **depuis la bascule** restent sous leur numéro Hektor (23 au 24/09). Le registre met leur identité dans `app_contact_id`, le build ne lit que `hektor_contact_id`. **Corriger d'abord** (registre et couche d'un seul geste, répété sur copie — le correctif naïf refait le doublement du matin), **puis reprendre C.9** *(bilan de la descente, C.9-d dans le build, C.9-f)* |
| **24/09** | ✅ **L4-c-bis CORRIGÉ** : le registre range l'identité d'un contact neuf dans la bonne colonne et **reconnaît un contact sous ses deux numéros** (sinon, la nuit de la traduction : second numéro). Répété sur une **copie de la vraie base** (registre → build → registre : 23 traduits, 0 second numéro), puis 23 fiches réparées en réel. **Leçon : le contrôle ne cherchait que les doublons, pas les oubliés** — sonde `data.contacts_identite` ajoutée, et une seconde copie de la règle (dans le contrôle manuel) remplacée par la lecture de l'unique |
| **24/09** | ⛔→✅ **LES TABLES SATELLITES NE SUIVAIENT PAS LE CONTACT** (audit demandé par Frédéric, `notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md`) : 13 tables figent le numéro du contact à la naissance de la ligne, les écrans lisent par lui → 69 rapprochements sans nom. La clé de RECHERCHE, elle, est saine (100 %). Réparation : fonction `app_contact_retraduire_satellites` appelée chaque nuit avant la propagation + sonde. Prouvée sur copies annulées (74 traduites, 0 écart) — la 1re preuve a trouvé mon propre trou (comparaison avec NULL). **Appliquée le 25/09 à 00 h 07** (patch collé par Frédéric, corps installé = corps prouvé) : **72 lignes retraduites, 0 rapprochement sans contact sur 50 204**, l'écran du bien affiche de nouveau le nom |
| **25/09** | ⚠ **LA VITRINE PUBLIQUE ET LES DEUX SYSTÈMES DE RDV N'ÉTAIENT DANS AUCUN AUDIT** *(signalés par Frédéric)* — alors que ce sont **deux étapes du run de nuit**. Sain : l'hébergement GitHub ne doit rien à Hektor, les **2 227 liens publics ont déjà un jeton ET notre numéro (100 %)**, et les RDV Google portent les deux numéros. À corriger : la vitrine fabrique ses liens avec le **numéro Hektor** · le service de RDV **retombe sur `hektor_annonce_id`** après avoir reconnu le jeton · la **fiche visite PDF est produite par Hektor** et disparaîtra. ⚠⚠ **Ces liens sont PUBLICS et déjà diffusés (QR codes, imprimés)** : il faut servir l'ancienne et la nouvelle forme **en parallèle** tant que Hektor vit — **un recouvrement, pas un remplacement** ➡ `notice/AUDIT_VITRINE_ET_RDV_2026-09-25.md` |
| **25/09** | ⚠ **`C.9-couple` a une DATE DE PÉREMPTION, comme `L9`** *(rappelé par Frédéric — je l'avais omis de la liste des choses à faire)*. Aujourd'hui l'app envoie le bloc conjoint et **c'est Hektor qui crée la seconde fiche et pose le lien** ; à la coupure, personne ne le fera. **C'est le seul moment où l'on peut comparer notre paire à la sienne.** Déjà fait : le lien de ménage est traduit chaque nuit *(37 404 liens sur 40 157 ; 2 753 non traduisibles)*. **Reste une MESURE d'1 h, jamais faite : quand l'app envoie un couple, Hektor crée-t-il UNE fiche ou DEUX ?** — puis, selon la réponse, savoir produire la paire |
| **25/09** | **Les recherches invisibles passent en RATTRAPAGE DE COUPURE** *(décision de Frédéric)*. **Le trou est fermé depuis le 20/09** : le run détecte les contacts qui *deviennent* acquéreurs et relit leur fiche le matin même *(carnet vérifié le 25/09 : 2 détectés, 0 restant)*. **Le stock ne grossit donc plus** — une seule passe suffira, la veille de la coupure. État : **130 829 contacts jamais relus** *(au-delà du 427258, où le rattrapage s'est arrêté le 23/08)*. ⚠ **Le « ~270 » n'est pas une mesure** : il vient d'**un seul cas observé sur 249**, fourchette 50 à 1 600 — et le 22/08, 7 500 contacts relus ont donné **zéro** découverte. ⚠ **Et la « dernière occasion » n'est pas E.2 mais LA COUPURE** : après E.2, Hektor vit encore et reste lisible |
| **25/09** | ⛔ **LES PHOTOS NE SURVIVRONT PAS À LA COUPURE** *(mesuré)* : les **13 437 vignettes** d'annonces pointent vers `staticlbi`, **chez Hektor** ; Supabase n'en a que des **liens**. Seules **1 355 photos (1,7 %)** sont sur le serveur — et **elles y sont invisibles**, le front (Vercel) et le backend (Render) ne pouvant pas lire le disque. **Trois pièces** : rapatrier ~125 Go · le worker écrit sur le serveur **d'abord** · **le chemin d'affichage, qui est l'arbitrage de Frédéric** *(tout dans Supabase = 33 → ~158 Go, au-delà des 100 Go du plan Pro · exposer le serveur · ou les deux, vignettes seules dans Supabase)*. ⚠ **Ce n'est pas une limite de nombre, c'est le poids et le prix.** **Décision du 25/09 : visible au plan, à faire APRÈS les documents** ➡ `notice/AUDIT_PHOTOS_2026-09-25.md` |
| **25/09** | **`D.0` confirmé par la base : arrêté depuis 33 jours** *(dernier `sync_console_documents` le 23/08 à 16 h 09)*, **0 travail en erreur — c'est arrêté, pas cassé**. Deux trous connus : les blocs **ImmoSign** et **« Mes documents »** n'ont pas de `force_transfert` donc **ne sont jamais indexés** ; les boutons de signature sont **masqués en connexion administrateur**. **Et 22 493 documents (28 Go) ne sont que sur le serveur, donc invisibles dans l'app** — même problème que les photos ➡ `notice/AUDIT_DOCUMENTS_ET_ETAT_DES_FONCTIONS_2026-09-25.md` |
| **25/09** | ✅ **LE RESTE DU PLAN FONCTIONNE** *(mesuré)* : sur les **36 types de travaux** envoyés à Hektor, **aucun n'est en erreur ni en attente** — 55 509 terminés. Annonce *(créer, modifier 182 champs, statut, archiver, restaurer, supprimer, négociateur)*, contact, recherche, transaction, documents *(envoyer, supprimer, PDF)*. ⚠ **« 0 en erreur » ≠ « prouvé »** : `relance_signature` et `cancel_signature_procedure` n'ont servi **qu'une fois, fin juin**. Les 3 exceptions citées par Frédéric sont confirmées : **numéro de mandat** *(= `L9`)*, **signature** *(ImmoSign appartient à Hektor, `A.2` à zéro)*, **portails** *(`A.1` à zéro)* |
| **25/09** | ⭐ **e3 ALLUMÉ par Frédéric à 08 h 15** — `c9_annonce_nait_dans_app = 'on'`. **Une annonce créée dans l'app naît désormais avec NOTRE numéro** (la prochaine : 10 000 001). Vérifié avant : e1/e2 inchangés, les 4 services en marche (redémarrés APRÈS e2), 0 travail en cours. Retour arrière : la même requête avec `'off'`. ⚠ **Le mécanisme est prouvé, l'usage réel ne l'est pas encore** : l'essai du 24/09 a duré 13 min, sur le compte formation, depuis l'écran Estimations — **le chemin « + Nouveau » n'a jamais été emprunté avec e3 allumé** |
| **25/09** | ⛔→✅ **`L5` : son gros morceau n'existait pas.** Le plan annonçait « 102 champs d'annonce, 40 de contact créables mais jamais corrigibles ». Mesure refaite : **0 créable sans être corrigible** *(annonce 178 / 182 / 173 communs ; contact 8 / 24)*. La modification par groupes existe depuis le **02/06/2026**. ⚠ **Ma première mesure était fausse elle aussi, et Frédéric l'a vue** — elle comparait une liste partielle à une liste complète, et deux vocabulaires. **Leçon : un écart énorme entre deux listes qui devraient se recouvrir accuse la mesure, pas le code.** `L5` tombe de 2-3 sem à **6-10 j** : restent le mandat existant, les photos, la fusion de doublons ➡ `notice/AUDIT_L5_GESTES_MANQUANTS_2026-09-25.md` |
| **25/09** | **La liste et le plan réconciliés** : ils ne parlaient pas la même langue *(lots `L0`…`L9` d'un côté, tâches `C.9`, `D.0`, `E.0-bis` de l'autre)*. Table de correspondance posée en tête de liste, **11 cases périmées corrigées** — ce qui a **révélé 3 vraies tâches dessous**. État : **36 ouvertes + 5 gestes de Frédéric** ➡ `notice/AUDIT_CORRESPONDANCE_PLAN_LISTE_2026-09-25.md` |
| **25/09** | ✅ **C.9-f CODÉ — l'identifiant d'un lien se fabrique avec NOTRE numéro de bien.** Le carnet (C.9-d) rend à chaque lien déjà connu l'identifiant qu'il avait : **0 changé sur 167 496** (répétition sur copie, vrai build). Deux garde-fous : carnet trop court → pas de substitution ; plus de 1 000 identifiants disparus → le build **recommence sans substituer**. L'audit a montré que cette clé **n'est clé de rien d'autre** (1 table, 0 fonction, 0 écran) — le seul vrai danger était le volume, car le push contacts n'a aucun garde-fou. ⚠ Mon 1er contrôle **rejouait** la règle au lieu d'appeler la vraie fonction : il restait vert quand je cassais la reprise du carnet. Réécrit de bout en bout, il a alors révélé un piège réel (valeurs vides vs chaînes vides) |
| **25/09** | ⛔→ℹ️ **9 liens de propriété pointent vers 6 biens que Hektor ne connaît plus** (absents des 12 tables du miroir, alors que leurs voisins immédiats y sont) : le lien vient de la **fiche du contact**, pas du listing. Pendant « bien » du défaut C.16. Ils gardent leur numéro Hektor. **Noté, non traité** |
| **24/09** | **ORDRE DU SOIR** *(Frédéric : « Oui, d'abord le plan »)* : rien n'attend plus la nuit sauf la preuve réelle de la seconde passe — le run de jour de 16:05 a prouvé C.9-d, D6, L4-c-bis et **rempli le carnet dans la vraie base**. Donc : (1) mesure en lecture des 97 rapprochements sous un ancien numéro ; (2) **C.9-f** audité, expliqué, codé, répété sur copie — **en service dès la nuit du 25/09 si 0 clé changée** ; (3) contrôle de la nuit le 25/09 ; (4) allumage de e3, décision de Frédéric |
| **24/09** | ⛔→✅ **Un contact neuf passait une nuit sous son numéro Hektor** (question de Frédéric : « POURQUOI ??? ») : le registre le numérote APRÈS le build, et le push l'envoyait sous l'ancien numéro — ce que l'app lui accrochait le jour même restait derrière (67 rapprochements mesurés). **Seconde passe du build** après le registre, avant le push, seulement s'il y a des contacts à traduire. Répétée sur copie : 8/8 traduits, 0 autre clé changée, 0 second numéro. J'avais écrit « normal » : c'était un défaut toléré, pas une règle |
| **24/09** | ✅ **D6 CODÉ** : `contacts_app_seuls.py` pose désormais `absent_depuis` sur ce qui n'est plus « connu de l'app seule » — seulement après une relecture complète et pleine (planchers côté app). Aucun lecteur ne s'en sert : observation pure. Répété sur base jetable : 26 lignes périmées marquées, 0 objet « app seule » ce jour |
| **24/09** | ✅ **C.9-d CODÉ — le carnet des liens** (`app_relation_registry`, dans le build complet, SAVEPOINT) : chaque lien noté avec **la recette exacte de son identifiant**, prise avant la réécriture du rôle. Doublure, lu par personne avant C.9-f. Répétition sur copie : **167 486 / 167 486 recettes refabriquent leur clé**, 0 conflit, 9 sans n° de bien. **D6 (expiration du recensement) reste à faire, go séparé** |
| **30/09** | ⛔ **LA RELATION EST LE SEUL OBJET À UN SEUL ROBINET** *(audit en lecture seule, parti d'un bug : fiche contact vide ouverte depuis une annonce)*. Le lien a son **identité** chez nous (C.9-d/f) mais pas son **existence** : la table est refaite chaque nuit depuis 6 sources Hektor, l'app n'écrit qu'une ligne provisoire, aucun contrat d'autorité, 0 sentinelle. **Exigence de Frédéric** : *un registre des relations autonome, mis à jour selon un contrat d'autorité entre le run de nuit Hektor et les workers de l'app* (ajouter un mandant, un acquéreur, un mandant depuis le registre des affaires). **L2 « relations » était surestimé.** ➡ section **« LE REGISTRE DES RELATIONS DEVIENT AUTONOME »** + `notice/AUDIT_REGISTRE_RELATIONS_AUTONOME_2026-09-30.md` · ⏳ **5 questions à trancher avant tout code** |
| **07/10** | ⛔ **AUDIT COMPLET : L'ÉTAPE 2 N'EST PAS TERMINÉE.** *(10 dimensions, chaque constat grave remesuré par un contradicteur, puis un contrôle de complétude ; lecture seule)*. La fondation est vraie : nos numéros, nos registres, la mémoire, et la chaîne « l'app écrit d'abord » pour les **modifications**. Mais la liste « il ne reste que documents + n° de mandat + signature + passerelles » est **incomplète d'une vingtaine de chantiers**, dont ceux-ci : une annonce née après la coupure serait **orpheline** (n° Hektor `NOT NULL` dans 16 tables, 8 fonctions qui refusent sans lui) ; créer reste suspendu à Hektor (recherche provisoire **effacée en 24 h**) ; mise sous mandat et clôture passent par Hektor ; le drapeau **diffusable**, qui commande le rapprochement, n'est posé que par Hektor ; les bons de visite sont faits par Hektor ; le **DNS** de gti-immobilier.fr est servi par La Boîte Immo ; le canal des **leads** est inconnu depuis le 01/02. ➡ `notice/AUDIT_AUTONOMIE_COMPLET_2026-10-07.md` |
| **07/10** | **L'AUDIT S'INTÈGRE AU PLAN, PAS DE CHANTIER À PART** *(Frédéric : « va s'y »)*. Les points connus complètent leur case existante. **L1 et L2 sont rouverts** : leur énoncé n'est pas couvert (règle CLAUDE.md §4). Les points sans place vont dans un **lot neuf `L10` « Préparer la coupure »**, et les points hors code dans la section 12 de la liste (**A.4** DNS et site web, **A.5** leads). Méthode inchangée : une tâche de code à la fois, chacune **ré-auditée au moment d'y entrer** (l'audit est une carte, pas la vérité). |
| 07/10 | **Le rattrapage des documents garde son lot de 2 500 et son périmètre** *(Frédéric)*. G.2 se fera sur **toutes les annonces vivantes, estimations comprises**. Un périmètre, une taille ou un ordre ne se décident jamais sans Frédéric |
| **08/10** | **LES DEUX ÉTAPES, DÉFINIES PAR FRÉDÉRIC.** *Étape 2* : « on utilise encore Hektor pour générer les id afin de faire fonctionner les workers ». *Étape 3* : notre registre électronique des mandats (nos numéros), puis la signature, puis la pub — « tant que les 3 ne sont pas chez nous, impossible de couper Hektor » — plus site web, DNS, e-mail. ➡ **Les 46 chapitres du 07/10 sont refusés** : ils mélangeaient les deux étapes |
| **08/10** | ⛔ **AUDIT PAR OBJET : l'audit du 07/10 se trompait sur plusieurs objets** (11 champs de l'annonce, recherche « effacée en 24 h », transaction « fabriquée chez Hektor », bon de visite). Refait en lecture seule, objet par objet, contre le code ET l'historique → `notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md`. **Le socle tient** ; les trous sont les droits, des gestes encore « Hektor d'abord », des échecs silencieux, des bugs précis (désarchiver est impossible depuis le 30/08), et **6 fonctions ouvertes à un visiteur non connecté** |
| **08/10** | **L'ORDRE DES CHANTIERS, décidé par Frédéric** : ① (fait) puis **⑤ → ④ → ② → ③ → ⑥ → ⑦ → ⑧** — réparer ce qui est cassé, ne plus rien perdre en silence, ouvrir aux négociateurs, changer les flux, compléter. « Il faut bien tous les faire » : aucun n'est abandonné |
| **08/10** | **LA MÉTHODE PAR CHANTIER** *(Frédéric : « chantier par chantier mais avec à chaque fois audit sur le sujet pour revérifier puis explication des correctifs proposés puis contrôle du résultat du travail »)*. Les 8 chantiers et leur suivi : section « 🧭 LES CHANTIERS DE L'ÉTAPE 2 ». Ordre proposé ① ⑤ ④ ②, **à valider** |
| **08/10** | ✅ **CHANTIER ⑤ FINI — les 9 gestes cassés**. **7** prouvés par un essai réel (5a désarchiver, 5b modifier un mandant, 5d le filet du rattachement, 5e rattacher après un retrait, 5g supprimer un contact, 5a ter ouvrir une archive sans Hektor) · 5h sentinelle verte · 5f actif, éprouvé hors ligne · 5c et 5e-B attendent le run du 09/10. Détail et mesures : `notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md` |
| **08/10** | ⚠ **UNE COLONNE NOMMÉE `hektor_contact_id` NE CONTIENT PAS LA MÊME CHOSE SELON LA TABLE** — `app_contact_current.hektor_contact_id` porte **NOTRE** numéro, `app_relation.hektor_contact_id` porte celui de **Hektor**. Le discriminant sûr est **LA PLAGE** (contacts : < 10 000 000 = Hektor, ≥ 10 000 000 = nous ; `app_relation_id` et `app_mandat_id` ≥ 1 000 000 = posé par l'app). **C'est la cause commune de 5b, 5d et 5g.** Ne jamais déduire du NOM d'une colonne : mesurer min/max des deux côtés, recouper avec le miroir local |
| **08/10** | ⚠ **LA HIÉRARCHIE DES PREUVES : LA BASE > LE CODE > LES NOTES** *(Frédéric : « cela m'étonne que nous n'avions pas prévu, audit avant pour confirmer ton analyse »)*. J'avais conclu de deux commentaires que la doublure `app_mandat__sb` « n'était jamais descendue » : elle existe, 26 847 lignes, et le run la descend déjà 3 fois. Un commentaire dit l'intention **du jour où il a été écrit**. Les horaires se lisent dans les tâches planifiées Windows (run **05:00**, sauvegarde 08:00, descente **08:15**, documents 21:00, recherches 03:00), pas dans les commentaires |
| **08/10** | **SUPPRIMER UN CONTACT EFFACE PHYSIQUEMENT SES LIGNES DU REGISTRE DES RELATIONS** *(Frédéric : « je veux que les lignes soient physiquement effacées, en plus normalement Hektor fera tout seul de même »)*. **Première exception assumée au `delete-never`** : elle ne vaut que pour une suppression **délibérée** d'un contact, jamais pour une absence constatée. Les deux tables (en ligne et locale) sont nettoyées dans le même geste, donc la sentinelle `relation_disparue` reste verte |
| **08/10** | **LE GARDE-FOU ANTI-ÉCRASEMENT DEMANDE D'ABORD *QUI* A FAIT BOUGER HEKTOR** *(5i — née de la remarque de Frédéric « ce ne sont pas vraiment les mêmes demandes »)*. La règle du 20/09 « Hektor plus récent gagne, la saisie est soldée » est **amendée** : si c'est **notre propre geste d'état** (statut, archive, négociateur, transaction, mandant) qui a rafraîchi la fiche, la saisie n'est plus soldée, elle part. Deux circuits séparés, aucun champ commun : l'édition de champs passe par `app_annonce_pending` (10 min, fusionnée), les gestes d'état partent **tout de suite** en travail |
| **08/10** | **OUVRIR UNE ARCHIVE N'APPELLE PLUS LA CONSOLE HEKTOR** *(Frédéric : « on n'a pas besoin de faire appel à Hektor, normalement le serveur a déjà tout — cette tâche doit être autonome »)*. Interrupteur `CONSOLE_DETAIL_LEGER_EXTRACTION` : **2 s au lieu de 13-22 s**. Les ~25 champs que l'API ne rend jamais (chauffage, 5 textes de secteur, 2 images DPE/GES, le détail de la grille d'honoraires) restent à traiter — **sujet du chantier ⑥** |
| **09/10** | ✅ **LE RUN DU 09/10 VALIDE LE CHANTIER ⑤** (05:00:02 → 07:34:16, 50 étapes, 4 sautées, 0 plantage). **5c** : l'étape neuve tourne en 19 s, juste avant le registre · **5e-B** : le retrait n'est pas reposé · **5a** : le bien désarchivé est dans l'index des **vendus/clos**, pas au parc vivant — parce que son statut est « Clos » et que le parc vivant ne prend que *Actif / Sous offre / Sous compromis / Estimation* (`ANNONCES_SCOPE_WHERE`) : **mon contrôle était faux, pas le code**. ⚠ Trois suites : le compte `retraits_leves` calculé mais **jamais imprimé** (`relation_ledger.py` l. 865) · le contrôle « L'ALLOCATEUR EST FAUX » **périmé** depuis que l'app pose des `app_relation_id ≥ 1 000 000` (il a crié pour la première fois cette nuit, parce que 5e marche) · le rattrapage des documents de 21 h déborde sur le run et fait **sauter 2 étapes** (garde-fou « travaux console en cours », pas un refus de droits) |
| **09/10** | **LE LOT DU RATTRAPAGE DES DOCUMENTS PASSE DE 2 500 À 1 000** *(décision de Frédéric)*. Mesure : les **35 317 archives sont finies**, le rattrapage est entré dans les **vendus/clos**, qui portent **8,60 documents par annonce au lieu de 2,45** (21,9 s au lieu de 10,2). Le lot de 2 500 demandait **~16 h** et sa file pleine a bloqué **trois** étapes du run (chauffage delta, entretien compromis, entretien ventes) — leur garde-fou a bien fait son travail : c'est ce rattrapage qui a déjà fait **bannir notre IP**. **Rien n'est perdu**, les trois se rattrapent seules. 1 000 = ~6 h, file vide avant le run. Reste **6 910** annonces → ~7 nuits, fin vers le 16-17/10, et **G.1-b (515 brouillons) n'est atteint que la nuit du 15 au 16/10** au lieu du 11/10. ⚠ À remettre à 2 500 quand les vendus/clos seront finis |
| **09/10** | ⚠ **LE STATUT DES ARCHIVES : DEUX DÉFAUTS MESURÉS, NON CORRIGÉS** — note `notice/STATUT_DES_ARCHIVES_2026-10-09.md`. ① **785 archives sans statut sont INVISIBLES** : l'écran exclut toujours « Estimation » et, en SQL, « différent de » rejette aussi les cases vides. ② **5 246 fiches détail d'archive à rattraper** (3 241 absentes + ~2 005 périmées) : le statut ne vit QUE dans la fiche détail (`build_case_index` l. 169 la recopie), le listing de Hektor n'en porte aucun (19 champs vérifiés sur la réponse brute), et les **5 variantes « archived » du balayage ne téléchargent jamais le détail** (`sync_details: False`, décision du 24/08 pour le débit) — donc **une archive modifiée chez Hektor n'est jamais actualisée**. ✅ Vérifié par 10 appels API : Hektor a bien le statut. ✅ Le trou est **limité aux archives** (parc vivant 0, vendus/clos 0 : ils portent `archive=0`). ⭐ **L'outil existe déjà** (`sync_archived_annonce_details.py`) et traite les deux cas, mais **il n'est branché nulle part** ; le maintenir coûterait **~2 appels par nuit**. ⚠ Au passage : `--missing-only`, passé chaque soir par le run, est **SANS APPELANT depuis le 21/07** — il ne fait rien (chantier ④) |

---

## 🧱 LES DIX LOTS DE L'ÉTAPE 2 — *l'ordre de travail, identifiants d'origine*

**État vérifié le 20/09, contre le code et la base** : les **transactions** sont prêtes ·
les **contacts** ont leur doublure remplie *(356 108 numéros, 20 tables, 0 incohérence)* mais
**pas la bascule de clé** · le **corps de l'annonce** est réécrit chaque nuit *(la liste des
champs de l'app est **vide**)* · les **relations** sont effacées et reconstruites en entier
chaque nuit · la **redescente des documents** est arrêtée depuis le **22/08** · une **photo**
ajoutée par l'app est effacée de chez nous après envoi · **aucun objet ne peut naître dans
l'app**, sauf une transaction.

| Lot | Objectif | Contenu *(identifiants d'origine)* | Durée | Fini quand |
|---|---|---|---|---|
| **L0** ✅ | **Ne plus rien perdre** *(fait le 20/09)* | **C.1'** la relecture efface une saisie en conflit *(`push_single_annonce_to_supabase.py`, ligne 582)* · le renvoi partiel sans fin · **C.4** supprimer un contact laisse ses rapprochements · **C.17-ter** 13 étapes du run sans sonde, sonde « IP bannie », script de reprise versionné | **~3 j** | Aucune saisie ne disparaît sans trace, et un arrêt se voit |
| **L1** 🟡 *(rouvert le 07/10 : la RECHERCHE ne naît pas dans l'app — distributeur `app_search_id_app_seq` jamais appelé, ligne provisoire effacée en 24 h ; reprise en `L10-2`)* | **Les numéros à la naissance** *(fait le 21/09 pour le contact et l'annonce, option B — voir le journal)* | **5b** bascule de la clé des contacts · **4-suite** clé des recherches · clé des relations sur les numéros app · **E.4 / 6.1-6.3** le distributeur, dans Supabase · la case « numéro app » dans les tables de création | **1,5–2,5 sem** | Un contact, une recherche, un bien naissent dans l'app avec leur numéro |
| **L2** 🟡 *(rouvert le 07/10 : le corps de l'ANNONCE est refait chaque nuit depuis le miroir — 26bis-3 = N.4 ouvert — et le serveur ne tient une TRANSACTION qu'une fois revue de Hektor — 26bis-TRANSACTIONS ouvert)* | **Les corps chez l'app** ⚠ *dernière chance* — **fait le 21/09** : contacts, relations *(⚠ **CORRIGÉ LE 30/09 : pour la relation, seul un OBSERVATEUR a été livré** — son identité est venue avec C.9-d/f, son EXISTENCE reste au miroir ; voir « LE REGISTRE DES RELATIONS DEVIENT AUTONOME »)*, couples, inventaire, **et 26bis-RECHERCHES** *(trouvée le jour même par l'audit d'autonomie)* ; **26bis-3** rejoint L3 ; ⚠ **le filet couvre désormais les quatre objets** — l'audit d'autonomie des recherches a trouvé que le filet existe pour l'annonce, le contact et la relation, **pas pour la recherche** *(notice/AUDIT_RECHERCHES_AUTONOMIE_2026-09-21.md)* | **26bis-3** · **26bis-CONTACTS** · **26bis-RELATIONS** · **26bis-COUPLES** · **INVENTAIRE** *(les 16 tables refaites chaque nuit)* | **2–3 sem** | Le serveur tient un objet que le miroir ignore |
| **L3** ✅ | **La règle de récence, par CHAMP** *(fait le 21/09)* *(renommé le 21/09 : ce n'est pas un interrupteur)* | **26bis-3** la carte des champs *(où vit la valeur de chacun : 5 en colonne, 38 dans le grand bloc, 9 à vérifier)* · **la protection par CHAMP** au lieu du bien entier · **Chantier 2** *(2.3, 2.4)* la même règle dans le run de nuit · la relecture à l'ouverture · **C.16** *(825 contacts disparus)* | **1–2 sem** | Le run de nuit **confirme**, il n'écrase plus |
| **L4-b′** | **FERMER LA PORTE** *(décidé le 22/09, **avant L4-c et avant C.9**)* — l'audit a trouvé **9 sortants qui envoient un numéro à Hektor sans passer par `cibleHektorContact`**, dont 5 sans aucun garde-fou. ⚠ **C'est un problème de C.9, pas de L4-c** : ce sont exactement les chemins qu'emprunte une annonce créée depuis l'app *(mandants, acquéreurs, mandat)* | les 9 sortants traduisent · `normalizeMandatContactIds` **traduit** au lieu d'écarter *(l. 14130 — « le contact rejoindra la liste » : rien ne le fait rejoindre)* · la traduction de la qualification cesse d'être **jetée** *(l. 13390)* | **~1 j** | Aucun numéro d'app ne peut partir chez Hektor |
| **L4-c** | **UNE PERSONNE, UN NUMÉRO** *(décidé le 21/09, **avant C.9**)* — la doublure `app_contact_id` devient l'identité du contact, comme `app_dossier_id` l'est pour l'annonce depuis le 19/08. ⚠ **Le registre des recherches bouge DANS LE MÊME GESTE**. ⚠ **ET TOUT CE QUE L'AUDIT DU 22/09 A RÉVÉLÉ EN FAIT PARTIE** *(exigence de Frédéric, 22/09 — liste ci-dessous)* | ① L4-b′ d'abord · ② répétition sur **copie** + un run par-dessus + le compte des orphelins · ③ passage réel, **code et données la même nuit** · ④ **les 3 dépendances hors base** *(jetons signés 60 j, numéro figé dans le JSON d'agenda, lien « Ouvrir Hektor » hors job)* · ⑤ **les 12 endroits ambigus**, dont le garde-fou `isdigit()` qui ne distinguera plus rien, le nom `hektor_contact_id` **paramètre public de l'API**, et les sentinelles `''` / `'invite'` / une adresse email · ⑥ la 3ᵉ empreinte `duplicate_group_id` · puis la clé de la recherche elle-même | **~2 j** *(hors ④⑤ à chiffrer)* | Un contact porte un seul numéro, et il survivra à Hektor |
| **L4** 🟡 | **La création part de l'app** — **le contact y arrive**, prouvé deux fois en réel le 21/09 *(36 s puis 51 s de bout en bout ; identité 10 000 002, case cible 605 453, une seule fiche)* | **L4-a** ✅ distributeurs et plages · **L4-b** ✅ le contact naît dans l'app *(case cible `4e82f25` · substitution d'identité dans le build + sonde « une personne, une fiche »)* · **C.9** l'annonce ✅ *(a→f codés, e3 allumé le 25/09)* · **C.9-couple** ⚠ **DATE DE PÉREMPTION : à écrire pendant que Hektor vit — son 1er pas est une mesure d'1 h (une fiche ou deux ?)** · **26bis-TRANSACTIONS** · **4.3** *(contact + recherche + mandant d'un coup)* | **1,5–2 sem** | On crée **sans attendre Hektor** ; il reçoit ensuite, et **une personne = une fiche** |
| **L5** | **Les gestes manquants** | **E.0-bis** *(mandat existant, photos, fusion de doublons)* · ⛔ ~~**RENDRE MODIFIABLE CE QU'ON NE SAIT QUE CREER**~~ **— MESURE REFUTEE LE 25/09** : **0 champ creable sans etre corrigible** (annonce : 178 creables, 182 modifiables, 173 communs ; les 5 restants ont tous un chemin propre — contact : 8 / 24 / 0). La modification par groupes existe depuis le **02/06/2026**. Le chiffre du 21/09 venait d'une comparaison entre deux listes incompletes ecrites en deux vocabulaires. ➡ `notice/AUDIT_L5_GESTES_MANQUANTS_2026-09-25.md`. *(mesure d'origine du 21/09 : **102 champs d'annonce, 40 de contact** -- creables, jamais corrigibles depuis l'app. **PAS la recherche** : ajout et archivage seuls passent par Hektor, le reste est autonome depuis le 20/08)* · ⭐ **LE MANDAT, MESURÉ LE 30/09 APRÈS `A.3-technique`** : son registre est désormais au niveau de l'annonce sur la **mémoire** *(corps durable 26 826 lignes, copie cloud + doublure, 2 sentinelles sur 2 axes, le numéro entre au registre à la seconde)* — **et très en retard sur les GESTES** : **2 gestes de worker contre 9** pour l'annonce et 9 pour le contact, **1 RPC contre 9 et 17**, **2 sentinelles contre 5 et 11**, et le carnet `app_mandat_champ_app` ne porte **qu'un seul champ, 2 lignes** *(`mandat_date_cloture`)*. On sait **créer** un mandat, pas le **corriger** : type, dates, montant, mandants ne sont modifiables depuis aucun écran — l'avenant ne sait changer **que le prix**. ⚠ **Pas de chaîne optimiste** non plus *(ni `_conflit` ni `_push_bloque`)*, parce qu'aucune valeur de mandat ne remonte chez Hektor. ⛔ **À ne pas confondre avec `L9`** : le **numéro** vient toujours de PROTEXA, et c'est une décision de Frédéric du 29/09, pas un manque · **C.13** clôture du mandat · supprimer une annonce · contrôle de baisse de prix et validation **lus dans l'app** · reprise des brouillons · retirer les liens « Ouvrir Hektor » | ~~2–3 sem~~ **6–10 j** *(revu le 25/09 : son gros morceau n'existait pas)* | Plus aucun écran ne renvoie vers Hektor |
| **L6** | **Ce que Hektor fait remonter** | **D.0** documents et mandats signés · état de la signature · état de la diffusion · numéro de mandat | **1–1,5 sem** | Les trois exceptions remontent proprement, le reste ne remonte plus |
| **L7** | **Les fichiers chez l'app** | **D.1a** · **D.1** · **D.2** · garder la copie de chaque photo ajoutée | **1–2 sem** | Afficher un document ou une photo ne dépend plus de Hektor |
| **L8** | **Exploitation et bascule** | **C.4-bis** élargi *(création, numéro de mandat, photo, document)* · **E.3** · **0.3 / E.1** rattrapage des recherches, dont **19-R2** la veille · **E.2** | **~1 sem** | Les négociateurs travaillent dans l'app |
| **L9** | **Le registre électronique des mandats** *(juste avant la coupure)* | **A.3-technique** *(table `app_mandat`, remplissage depuis le miroir, sonde, puis le registre **lit la table**)* · les **trois couches de numérotation** · la **série propre**, à la place de PROTEXA · **C.13-c** *(23 715 dates de clôture)* · le négociateur manquant *(3 318 lignes)* · **A.3-juridique**, étudié le moment venu | **~1 sem** + l'étude | Un mandat neuf s'enregistre sans Hektor — **la 1re des 3 exceptions tombe** |
| **L10** ⬜ *(créé le 07/10)* | **Préparer la coupure** — tout ce que l'audit complet du 07/10 a trouvé et qui n'avait **aucune place** dans L0→L9 | **L10-1** le numéro Hektor de l'annonce devient facultatif · **L10-2** créer sans Hektor · **L10-3** les statuts chez nous (mise sous mandat, clôture, archiver) · **L10-4** le drapeau diffusable à l'app · **L10-5** la baisse de prix lue dans l'app · **L10-6** interrupteur et ordre d'extinction · **L10-7** le run d'après · **L10-8** les planchers « Hektor répond vide » · **L10-9** la sauvegarde d'après · **L10-10** la surveillance d'après · **L10-11** les négociateurs (droits, comptes, annuaire) · **L10-12** visites et documents-modèles · **L10-13** ce que Hektor envoie aux clients · **L10-14** le numéro de dossier · **L10-15** le côté public · **L10-16** sécurité *(détail : section « 🔎 L'AUDIT COMPLET DU 07/10 » ci-dessous, et section 13 de la liste)* | à chiffrer tâche par tâche | Le serveur et l'app **vivent une semaine sans Hektor** sur une copie, sans perte ni alerte fausse |

### 🔎 L'AUDIT COMPLET DU 07/10 — *ce qu'il change au plan*

> ➡ Le détail, les preuves et les mesures : `notice/AUDIT_AUTONOMIE_COMPLET_2026-10-07.md`
> (§0 à §12, plus le §13 du contrôle de complétude). **Cette section ne recopie pas l'audit :
> elle dit OÙ chaque point vit désormais dans le plan et la liste.**
> ⚠ L'audit est une **carte du 07/10**, pas la vérité : chaque tâche est **ré-auditée dans le
> code au moment d'y entrer** (CLAUDE.md §0, étape 1).

**Le verdict.** La fondation est vraie : la mémoire est à nous, ainsi que les numéros, les
registres, et la chaîne « l'app écrit d'abord » pour **modifier**. Mais **l'étape 2 n'est pas
terminée**. Créer, mettre sous mandat, ajouter un fichier, valider pour la diffusion : tout cela
dépend encore de Hektor. Et **personne ne saisit encore dans l'app** : 0 travail demandé par un
commercial en 120 jours, 0 annonce née dans l'app depuis le 25/09.

#### Où va chaque point

| point de l'audit | va dans | état |
|---|---|---|
| rattrapage des documents (≈ 10 650 annonces, ≥ 6 nuits) · les 508 brouillons **échoueront** (`loadDossier` sans branche brouillon) · le parc vivant n'est **plus relu depuis le 20/08** · le relais G.6 ne s'allume pas tel quel | liste **G.1**, **G.2**, **G.6** (section 10bis) | complété |
| ajouter un document, une photo, un PDF généré : Hektor d'abord | liste **G.5** (devient bloquant) | complété |
| corps de l'annonce refait depuis le miroir | **N.4** = liste **26bis-3** → **L2 rouvert** | complété |
| la recherche ne naît pas dans l'app | **L1 rouvert** → **L10-2** | neuf |
| C.9-couple : la sonde existe depuis le 07/10 (`033e946`) | liste **C.9-couple** : reste le geste humain | complété |
| gestes manquants (photos, mandat existant, fusion, brouillon, suppressions) | liste **E.0-bis** | complété |
| dates de clôture des mandats | liste **C.13-c** | inchangé, date de péremption |
| registre légal : série, inaltérabilité, export, avenants et mandats de recherche dans la même série, 25 trous, 2 défauts dormants de l'étape D | liste **A.3** (sections 9 et 12) | complété |
| signature : 50 procédures en cours, bouton sur l'ancien domaine | liste **A.2** | complété |
| passerelles : il faut aussi un flux à nous (0 ligne) | liste **A.1** | complété |
| liens publics : **le jeton RDV n'est pas stable** | liste **11bis ①** | ⚠ recette à corriger |
| droits des commerciaux, comptes, F.1 **avant** E.2 | liste **E.2** / **F.1** → **L10-11** | complété |
| agenda des visites, 230 documents sans fichier, 111 documents de fin de vie, signatures en cours | liste **E.1** | complété |
| zone DNS et site web chez La Boîte Immo | liste **A.4** (neuf, hors code) | neuf |
| leads : canal inconnu depuis le 01/02 (module Leads de Hektor ?) | liste **A.5** (neuf, hors code) | neuf |
| tout le reste | **L10-1 → L10-16** (section 13 de la liste) | neuf |

#### Les questions à Frédéric — *à trancher avant d'entrer dans les tâches concernées*

1. **Registre des mandats** : continuer la série PROTEXA, ou repartir de 0 ? *(le plan
   recommande de continuer — « TROIS CORRECTIONS QUE LA RECHERCHE IMPOSE », section FINIR
   L'ANNONCE ; la mémoire du 28/09 dit l'inverse ; rien n'est au journal des décisions)*
2. **Visites** : importer l'agenda de Hektor, ou y renoncer ? Faire **notre** bon de visite
   (numéroté, archivé, plusieurs biens) ?
3. **Droits** : que peut faire un négociateur seul ? *(aujourd'hui il peut créer une annonce,
   mais ne peut plus la modifier ensuite)*
4. **Après la coupure** : suppressions et fusion de doublons dans l'app, ou réservées à l'admin ?
5. **Numéro de dossier EM/VA** : continuer les séries, ou passer à notre numéro ?
6. **Validation pour la diffusion** : qui pose « diffusable » quand Hektor n'existe plus ?
7. **Locations et gestion** : les 2 locations vivantes (62309, 62504) et la carte G ?
8. **Questions de fait**, que seul Frédéric peut dire : par où arrivent les leads ? Les
   négociateurs utilisent-ils les SMS, les tâches et rappels, l'envoi de fiches de Hektor ? Les
   automatismes CRM (nouveau mandat, échéance, anniversaire) sont-ils allumés ? Properstar
   diffuse-t-il nos biens ?

### 🧭 LES CHANTIERS DE L'ÉTAPE 2 — *posés le 08/10, ils remplacent les 46 chapitres*

> **D'où ils viennent.** Frédéric a refusé les 46 chapitres : ils mélangeaient l'étape 2 et
> l'étape 3, et traitaient des détails avant les grosses anomalies. Un **audit par objet**
> a été refait le 08/10, en lecture seule, avec la bonne grille :
> ➡ **`notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md`** (tableau, détail par objet, preuves).
>
> **La grille.** *Étape 2* : l'app fait tout le travail quotidien ; Hektor vit, **il fournit
> les numéros**, les workers lui envoient les mises à jour. *Étape 3* : registre
> électronique des mandats (nos numéros), puis signature, puis passerelles, plus site, DNS,
> e-mail. Ce qui ne compte qu'après la coupure n'entre pas ici.
>
> **LA MÉTHODE, À CHAQUE CHANTIER** *(Frédéric, 08/10 : « chantier par chantier mais avec
> à chaque fois audit sur le sujet pour revérifier puis explication des correctifs proposés
> puis contrôle du résultat du travail »)* :
> **① audit du sujet** (le code et la base d'aujourd'hui, plus l'historique : rien n'est
> refait de ce qui l'est déjà) → **② explication des correctifs proposés** (ce que ça touche,
> retour arrière, vérification, et **« ce que ça pourrait casser ailleurs »** : le correctif ne doit pas écraser un raisonnement global de l'app — appelants, chemins de secours, usages publics, décisions écrites, *règle de Frédéric du 08/10*) → **③ « vas-y » de Frédéric** (accord obligatoire pour la
> base de production, un redémarrage, un déploiement) → **④ code** → **⑤ contrôle du
> résultat** (dire aussi ce qui a raté) → **⑥ plan, liste et CLAUDE.md à jour**.
>
> **L'ORDRE, décidé par Frédéric le 08/10** : ① puis **⑤ → ④ → ② → ③ → ⑥ → ⑦ → ⑧** (tous seront
> faits ; ② attend d'abord sa décision sur les droits). Les points marqués ⏳ ont
> une **date de péremption** : ils doivent se faire tant que Hektor vit.

**LE SUIVI** — *une ligne par chantier, mise à jour à chaque étape. Légende : ⬜ pas commencé
· 🔎 audit · 💬 expliqué, attend « vas-y » · 🔧 en code · 🧪 contrôle · ✅ fini (avec sa mesure)*

| # | Chantier | Ce qu'il couvre *(détail : audit du 08/10, §2)* | État |
|---|---|---|---|
| **①** | **Sécurité** | 6 fonctions `SECURITY DEFINER` exécutables par `anon` sans contrôle de rôle (dont `app_bascule_identite_contact_annuler`) · la vue `app_contact_relations_current` lisible sans connexion · *(L10-16)* | 💬 08/10 audit fait : **136 fonctions sur 172 ouvertes à `anon`** (53 à pleins droits sans garde), 15 vues qui contournent la RLS, 2 tables sans RLS ; suite de la « dette assumée » 0.7 du 24/08 → `notice/CHANTIER_1_SECURITE_2026-10-08.md` · 🔧 « vas-y » le 08/10 : patch SQL + inverse + **répétition** écrits (`supabase/patch_chantier1_*`), `hektor-diffusion` contrôlée comme Render (option a, non déployée) · ✅ répétition exacte, **patch appliqué par Frédéric le 08/10 à 08:22** : 0 fonction et 0 table/vue ouvertes à `anon` (136 avant), 6/6 appels publics refusés, vitrine/photos/RDV OK, fuite `app_searches_to_complete` fermée · app connectée contrôlée (158/160, les 2 échecs antérieurs) · `hektor-diffusion` **déployée v15** (refuse sans compte) · **reste : la nuit du 09/10 (run, crons, worker)** |
| **②** | **Les droits du négociateur** | annonce (modifier, statut, archiver, négociateur) · mandant (tout) · transaction (tout, aucun circuit de demande) · documents et photos (générer, ajouter) · numéro de mandat · comptes (2 commerciaux contre 39 négociateurs) · *(L10-11, F.1)* — **attend d'abord la décision de Frédéric : que fait un négociateur seul, que demande-t-il ?** | 🔎 **09/10 audit fait, CONFIRMÉ** → `notice/CHANTIER_2_DROITS_NEGOCIATEUR_2026-10-09.md`. Découverte qui allège tout : **il n'y a que CINQ portes**, et la première (`app_console_can_request_job`) commande à elle seule **16 RPC *et* la règle RLS d'écriture de `app_console_job`** — donc aussi les travaux que le front insère en direct (avis de valeur, PDF de mandat, cadastre, photo, suppression de document). Les autres : `app_console_can_request_contact_job` *(déjà ouverte au commercial sur ses contacts)*, `is_app_admin()` dans les **6** fonctions « affaire », deux contrôles en dur (brouillon, suppression), et le front (`isAdmin = role === 'admin'`, **49 endroits**) — un **manager** ne voit rien de plus qu'un commercial. **La lecture est déjà cloisonnée** (RLS sur `app_dossier_current` et `app_contact_current`) : le trou est uniquement à l'écriture. Mesures du 09/10 : **43** adresses de négociateur portent 21 149 lignes d'annonce, **4** ont un compte actif · 4 admins, 2 commerciaux, **0 manager** · **0 travail demandé par un commercial depuis toujours** · le circuit de demande existe mais **dort** (9 demandes, toutes d'un admin, la dernière le 02/06). Historique : statut et archivage réservés à l'admin le **21/05**, **sans raison écrite** ; le patch du 30/08 était un correctif de sécurité, pas une décision métier · 💬 **attend les 3 réponses de Frédéric** (que fait un négociateur seul · garde-t-on le rôle manager · pilote ou les 39 comptes) |
| **③** | **Hektor d'abord → chez nous d'abord** | mise sous mandat et « Mandat clos » · archiver et changer de négociateur (le carnet n'est lu par personne) · clôture d'un mandat (la date n'arrive pas au registre) · ajout de document et de photo (G.5 dort) · suppression d'un document (notre copie détruite) · *(L10-3, G.5)* | ⬜ |
| **④** | **Aucun échec silencieux** | suite de la création d'une annonce marquée « réussie » malgré l'échec · créations (annonce, contact, recherche), dépôts et gestes mandant jamais rejoués · « Annonce en création » sans marque d'erreur · photos de création dans la mémoire du navigateur · alarme « travaux en erreur » figée à 15 · gestes de transaction sans notification · *(L10-10)* | ⬜ |
| **⑤** | **Les gestes cassés** | 5a désarchiver impossible · ✅ **5b FINI le 08/10** (la carte d'un mandant envoyait le n° Hektor là où la fonction attend le nôtre — 62 162 contacts sur 62 162 concernés depuis la bascule du 23/09 ; patch SQL seul, répétition 13/13, essai réel sur le bien d'essai 62774 : valeur chez nous immédiate, travail désigné, Hektor modifié en 26 s, redescente conforme, file vidée) · 🧪 **5c** premier numéro de mandat depuis l'app : la DATE `JJ-MM-AAAA` était un **FAUX** de l'audit (3 usages réels, dates enregistrées exactes) ; le vrai défaut est un **décalage d'horaire** — le run passe à 05:00, la descente des doublures à 08:15, donc le run lit la copie de la veille et ne peut pas **adopter** l'id posé par l'app → une nuit de registre perdue (pas « chaque nuit »). Étape de descente ciblée `pull_from_supabase.py --table app_mandat` ajoutée au run, comme pour les 3 autres registres ; chronométrée le 08/10 : **26 847 lignes en 28 s**. Reste : le journal du run du 09/10 · ✅ **5d FINI le 08/10** : le worker cherchait NOTRE numéro dans `app_relation.hektor_contact_id`, colonne qui porte celui de **Hektor** (132 713 lignes sur 132 713, vérifié par la PLAGE et recoupé avec le miroir) — deux endroits : le filet d'échec et le marquage de réussite. Corrigé, workers redémarrés, essai réel : lien posé sous `app_relation_id 1000010`, puis `relation_etablie: done` en 28 s et `present_in_hektor` à vrai — **première exécution de cette étape, elle trouve sa ligne**. Le filet du refus reste non éprouvé · 🧪 **5e** retirer puis rattacher : la RPC laissait le `retire_le` (`do nothing`) → le mandant recréé chez Hektor **disparaissait de l'écran au bout de 24 h** (purge de la ligne provisoire) ; et le registre de nuit ne savait que **poser** un retrait, jamais l'effacer. **Deux correctifs indissociables** : la RPC efface le retrait au clic (patch appliqué le 08/10, empreinte `f39e0165…`) **et** `relation_ledger.py` sait lever un retrait que la doublure **du jour** ne porte plus (3 gardes : fraîcheur, pilotage depuis la petite table, on n'efface que ce qui est contredit). ✅ **essai réel du 08/10 17:40** : le contact retiré est bien PROPOSÉ par l'écran sans avertissement (fiche « 0 mandant »), et au clic `retire_le` passe à NULL **sans renuméroter la ligne** (1000008), puis le marquage de 5d bascule `present_in_hektor` en 35 s. **Reste le seul contrôle du morceau B : le run du 09/10 ne doit pas reposer le retrait** (voir la liste « À VÉRIFIER APRÈS LE RUN DU 09/10 » dans la note du chantier) · 5e d'origine · 5f retour d'état sur échec passager (contraire au 29/08) · 5g suppression d'un contact · 5h mandant créé en échec · ✅ **5f** l'échec passager ne jette plus l'état : c'était la **seconde moitié de C.4-bis**, décidée le 29/08 et jamais appliquée (éprouvé hors ligne 6/6) · ✅ **5g** suppression d'un contact : le miroir reçoit enfin le bon numéro, et les liens sont **physiquement effacés** des deux côtés (décision de Frédéric) — **essai réel réussi** · ✅ **5h** sentinelle `contact_sans_numero_hektor`, lue par le moniteur, verte · ✅ **5i** le garde-fou demande **qui** a fait bouger Hektor avant de jeter une saisie — règle née de la remarque de Frédéric « ce ne sont pas les mêmes demandes » : deux circuits, aucun champ commun (non éprouvé en réel) | ✅ **CHANTIER ⑤ FINI le 08/10** — les **9 points traités** (5a → 5i), 6 prouvés en réel, note `notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md` · **5a : audit refait, CONFIRMÉ** (35 317 archives, 0 dans `app_dossier_current` ; dernier désarchivage réussi le 30/08 07:42 UTC, une minute avant `e7b9df7`) → 💬 correctif expliqué → 🔧 « vas-y » option A le 08/10 : patch SQL **additif** + inverse + répétition (`supabase/patch_5a_desarchiver_archive_2026-10-08*`), aucune ligne de front, aucun déploiement → 🧪 répétition **13/14 exacte** (la 14e = mes empreintes md5 faussées par les fins de ligne Windows, prouvé hors ligne au bit près ; a révélé que ma garde de retour arrière aurait refusé de rejouer — corrigée) · **patch appliqué par Frédéric le 08/10 ~09:55**, contrôlé en base : empreinte `709571469083a76b1be384e879ca523b` conforme, `anon=non`, 15 travaux et 3 lignes de carnet inchangés · **5a bis** trouvé en essai réel : le bouton n'existait pour **aucune** archive (statut jamais « Archivé » : 0/35 317 ; `isLightweightDetail` toujours vrai) → corrigé dans `CockpitDetail`, build vert, **déployé** (`78e6574`, Vercel READY) · ✅ **5a FINI le 08/10 10:45** : essai réel VA2380 (bien 78), travail `app_dossier_id=NULL hektor=78 source=index_archives`, **done en 43 s**, Hektor confirme `archive=0` — premier désarchivage depuis 39 jours ; à surveiller : le bien reste invisible chez nous (ni archives ni parc vivant) jusqu'à la descente de nuit · ⏰ **CE QUI RESTE** : le journal du **run du 09/10** (5c et 5e-B, liste dans la note du chantier) · ✅ **5i PROUVÉ EN RÉEL le 08/10 au soir**, après redémarrage des 4 workers (mesuré : processus partis à 20:39, fichier modifié à 19:15) — essai réel du 08/10 au soir sur le bien 62963 : saisie `corps` à 18:46:22 UTC, geste d'état `change_hektor_annonce_status` fini à 18:49:00, et au push de 18:57 le journal du worker dit **« Hektor a bouge, mais c'est NOTRE geste d'etat : aucun champ commun, la saisie part »** (`base_date_maj` 03/10 16:40 → `fresh_date_maj` 08/10 20:48) ; Hektor répond `result: 1`, `skipped_fields` vide, la saisie est effacée, **0 conflit**, et le texte revient à l'écran par la resynchro · **5f** : l'abandon réel (5 tentatives ou « abandon » humain) ne rend toujours pas l'état — 2 fonctions SQL, chantier ④ |
| **⑥** | **Ce qui ne redescend pas de Hektor** | ⏳ documents du parc vivant figés depuis le 20/08 (**G.2 puis G.6**, après le rattrapage, périmètre = toutes les vivantes) · ⏳ **G.1-b** les brouillons du rattrapage · photos : retraits et ordre · ⏳ agenda des visites Hektor *(question à Frédéric)* · recherche créée dans Hektor (carnet aveugle) · 2 recherches disparues · RDV déplacé dans Google | ⬜ |
| **⑦** | **Les gestes qui manquent** | modifier ou prolonger un mandat · photos : ordre, principale, visible, retirer (E.0-bis) · renommer un document · *(L5)* | ⬜ |
| **⑧** | **Gardé chez nous en entier** | contact : 6 champs à la création, 12 à la modification · périmètre cloud 62 000 sur 356 000 *(question à Frédéric)* · corps des archives seulement dans le miroir · sauvegarde quotidienne (`app_relation`, `app_mandat`, carnets) · bon de visite non archivé · document retiré dans Hektor supprimé sans trace · ⏳ C.9-couple (geste humain) | ⬜ |

**Ce qui n'est PAS ici** *(étape 3, audit du 08/10 §4)* : numéro Hektor obligatoire dans 16
tables (L10-1), corps serveur refait depuis le miroir (N.4, 26bis), `diffusable`, numéro de
dossier, série légale et registre électronique (L9), signature, diffusion, DNS et site (A.4),
interrupteur et run d'après (L10-6, L10-7).

#### 🧭 LES 46 CHAPITRES — *⚠ REMPLACÉS le 08/10 par « LES CHANTIERS DE L'ÉTAPE 2 » ci-dessus, gardés pour mémoire*

> **Proposée le 07/10, refusée par Frédéric le 08/10** (mélange des étapes 2 et 3). Construite à partir de 110
> sous-tâches mesurées dans le code, de trois ordonnancements (péremption, usage, fondations),
> d'un jury et d'un contradicteur (« la séquence tient, aucun problème bloquant »).
> ➡ **Le détail de chaque chapitre** (ordre interne, fichier:ligne, prérequis, feu vert,
> critère de fin, vérification, gestes de Frédéric) :
> `notice/CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md`.
> **Règles** : une tâche de code à la fois · chaque chapitre est **ré-audité en entrant** ·
> chaque redémarrage du worker se fait **l'après-midi, file documents VIDE** · tout ce qui
> inverserait le courant reste derrière un réglage éteint tant que les commerciaux saisissent
> dans Hektor · **aucun push hors de `run_full_pipeline.ps1`** sans
> `APP_BROUILLON_BUCKET_ENABLED=1` (incident du 07/10, `38ad468`).
> **Volume** : environ 145 à 215 jours de code. Pilote vers la 2e quinzaine de novembre si les
> décisions suivent. Coupure réaliste **au plus tôt au printemps 2027**.

```
 N°  CHAPITRE                                              CONTENU                         TAILLE   PÉRIME
 ──  ────────────────────────────────────────────────────  ──────────────────────────────  ───────  ──────
 1   Le rattrapage tient dans la nuit, ses erreurs se       G.1-e ⛔ AVANT LE 08/10 21:00 ·   2-3,5 j   oui
     voient                                                G.1-b-1 · L10-10a · L10-8c ·
                                                           L10-10e (disque, plantages)
 2   Une seule fenêtre de redémarrage du worker            G.1-b-2 · G.5-a · A.3-a          1,3-2 j   oui
 3   EN PARALLÈLE des ch.1-10 : mesurer ce qui périme      L10-6a · E.4a · L10-7a · A.5-a ·  3-5 j     oui
     (pas de code de prod)                                 L10-13-a · E.1b · C.9-couple-a ·
                                                           E.1c
 4   Relire le parc vivant chaque nuit                     L10-10c · G.2 · G.6 · G.1-c ·     2,5-3,5 j oui
                                                           G.1-d
 5   Les planchers « Hektor répond vide »                  L10-8a/b/d/f · L10-8e (annuaire,  3-4 j     non
                                                           vitrine)
 6   Sauvegarde et surveillance d'aujourd'hui              L10-9a/b/c · 35 docs cloud seul · 3,5-5,5 j non
                                                           L10-10b/d
 7   Fermer les portes ouvertes (sécurité)                 L10-16a/b/c                       1,8-2,5 j non
 8   Les filets du pilote, un seul déploiement du front    L10-2a · L10-1a · E.0-bis-a ·     2,6-4,1 j non
                                                           L10-15-a · A.3-b (export registre)
 9   Les droits en gestes métier, comptes des pilotes      L10-11-a · L10-11-b (pilotes)     2,5-3,5 j non
 10  ▶ LE PILOTE S'OUVRE : quelques négociateurs dans      E.2 (ouverture)                   1-2 j +   oui
     l'app pendant que Hektor vit                                                            2-4 sem.
 11  Les statuts chez nous d'abord                         L10-3-0 « LE CARNET CÈDE » ⚠ ·    5,5-8 j   non
                                                           L10-3a/b/c/d
 12  Documents et photos chez nous d'abord                 claim_next_job ouvert ⚠ · G.5-b · 5-7,5 j   oui
                                                           G.5-c · G.5-e · E.0-bis-c1
 13  Les 3 PDF naissent chez nous                          G.5-d · L10-15-c · logos worker ⚠ 1,5-2 j   non
 14  Bilan du pilote, puis tous les négociateurs           E.2 · L10-11-b (tous)             1-3 j     oui
 15  Les mandats existants vivent chez nous                applicateur par mandat ⚠ ·        4-6 j     oui
                                                           C.13-c · E.0-bis-d1
 16  Capturer ce qui ne vit que chez Hektor                E.0-bis-f(1) · RGPD · E.1b ·      1,5-7 j   oui
                                                           A.5-b (historique)
 17  Comparer tant que Hektor vit : corps et ménage        26bis-3b · C.9-couple-b           3,5-5 j   oui
 18  Une seule porte vers Hektor (dormante)                L10-1b · L10-1c · L10-6b/c/d      4-5,5 j   non
 19  Le corps de l'annonce née dans l'app chez nous        L10-2d · 26bis-3a                 3-4,5 j   non
 20  ⚠ LA NUIT DE BASCULE : n° Hektor facultatif           L10-1d (17 tables, 7 clés)        3-5 j     non
 21  Gestes et transactions sans n° Hektor                 L10-1e · 26bis-TRANSACTIONS       3-4,5 j   non
 22  N° de dossier, fichiers sans n° Hektor                L10-14 · G.5-f                    2-4 j     non
 23  Diffusable et baisse de prix sur les valeurs app      L10-4 · L10-5                     3-4 j     non
 24  La recherche naît chez nous                           4-suite · L10-2b                  3-5 j +   non
 25  Les mandants naissent chez nous                       registre des relations · L10-2c   1-2 j +   non
 26  L'annuaire des négociateurs devient le nôtre          L10-11-c                          3-5 j     non
 27  Le côté public stable                                 11bis-2 · 11bis-1a/1b · L10-8e    3,5-4,5 j oui
                                                           (RDV) · L10-15-b (DPE)
 28  Le registre lit nos tables, mandat complet            A.3-c · A.3-d                     5-8 j     oui
 29  La série légale des numéros, l'avenant complet        A.3-e · L10-12-c                  6-9 j     oui
 30  L'inaltérabilité du registre                          A.3-f                             3-5 j     non
 31  Notre bon de visite, l'offre d'achat                  L10-12-a · L10-12-b               6-9 j     non
 32  Signature en propre (1/2) : envoyer, suivre           A.2 (partie 1)                    4-8 j     non
 33  Signature (2/2), prolonger un mandat                  A.2 (partie 2) · E.0-bis-d2       6-10 j    non
 34  Diffusion (1/2) : notre flux d'annonces               A.1 (partie 1)                    5-10 j    non
 35  Diffusion (2/2) : reprise des 346, retrait API        A.1 (partie 2)                    5-10 j    oui
 36  Les leads entrent dans l'app                          A.5-b                             3-5 j     non
 37  Gérer les photos dans l'app                           E.0-bis-c2                        3-5 j     non
 38  Reprendre un brouillon, supprimer « app d'abord »     E.0-bis-f(2) · E.0-bis-g          4-6 j     non
 39  Fusionner les doublons                                E.0-bis-e (peut glisser)          4-6 j     non
 40  Ce que Hektor envoyait aux clients                    L10-13-b · L10-13-c (si Q8)       1-7 j     non
 41  Vitrine depuis Supabase, corps serveur prêt           L10-7c · 26bis-3c                 3,5-5 j   oui
 42  Le run d'après, notre fiche visite                    L10-7b · L10-15-d                 3,5-5 j   non
 43  Sauvegarde et surveillance de l'après                 L10-9d/e/f · L10-10f/g            4-6,5 j   non
 44  L'écran sans Hektor                                   E.3 · E.0-bis-b                   2,5-3,5 j non
 45  La fenêtre finale                                     E.1d · E.4a · E.1a · E.1c ·       1-2 j +   oui
                                                           copie figée du miroir             sessions
 46  ▶ LE JOUR J : répétition sur copie, puis la coupure   E.4b                              1-2 j +   oui
                                                                                             1 sem.
REPORTÉS APRÈS LA COUPURE (à confirmer) : G.3 (purge cloud), G.4 (état cloud qui suit
l'annonce). PEUVENT GLISSER : E.0-bis-e (fusion), L10-12-b (offre d'achat). CONDITIONNEL :
L10-13-c (si la question 8 dit que les automatismes servent).
```

**⚠ Les 3 corrections du contradicteur, intégrées ci-dessus** (marquées ⚠) :
1. **Ch.11 — « le carnet cède » est une TÂCHE, pas une vérification** (1-2 j, en tête du
   chapitre). Rien ne fait céder `app_annonce_champ_app` ni `app_mandat_champ_app` quand Hektor
   confirme. Sans elle, une valeur posée une fois dans l'app écraserait Hektor chaque nuit. C'est
   la condition d'allumage de L10-3, de l'application de C.13-c, de E.0-bis-d1 et de L10-4. Patron :
   `nettoyer_carnet_affaire.py` et le retrait à chaud `prouverTransactionModifiee` des affaires.
2. **Ch.15 — l'applicateur des mandats choisit par ANNONCE, pas par MANDAT**
   (`appliquer_contrat_mandat.py`). 39 annonces ont plusieurs mandats. Il faut le corriger
   **avant** d'écrire en masse les ~23 600 dates de C.13-c.
3. **Ch.12 — `app_console_claim_next_job` exige le fichier temporaire** des envois de document
   ou de photo. Un envoi « chez nous d'abord » resterait `pending` pour toujours, sans erreur. Il
   faut l'ouvrir dans le même patch que G.5-c.

**Corrections mineures, également retenues :**
- **G.1-e** = changer seulement `--limit 2500` dans `run_rattrapage_documents.ps1:75`, pas de
  nouvelle option ; et corriger le commentaire « 22:00 » (la tâche part à 21:00).
- **Ch.4** ne dépend que de G.1-e, pas du ch.2.
- **Ch.13** : les logos de l'avis de valeur et du plan cadastral (`console_job_worker.js:6679`,
  `:7476`). Et **le site www ne déménage pas avant la coupure** : l'admin Hektor, le worker et
  `pdf.php` passent par ce nom.
- **L10-10a** : ne jamais solder de `sync_console_documents` en erreur, car c'est la liste
  « ne jamais rejouer » du rattrapage.
- **L10-6b** : l'essai demande une option `--job-id`. `--once` réclame le prochain travail de
  prod.
- **Ch.5, 10 et 14** : critères rendus mesurables. Comparaison aux 30 dernières nuits ; chaque
  geste du journal des pilotes est retrouvé dans `app_console_job` ou un carnet.

**⛔ La seule heure limite : avant le 08/10 à 21:00**, Frédéric fixe la taille du lot des VENTES
(proposition : 400 la première nuit, puis 400 à 600 selon la durée mesurée) et dit « vas-y » pour
G.1-e. À défaut : désactiver la tâche « GTI Rattrapage Documents » une nuit.

### 🎯 FINIR L'ANNONCE — *la mettre au niveau du contact, de la recherche et de la transaction*

*Section posée le **28/09/2026**, à la demande de Frédéric : « finir les annonces comme les
contacts, recherches et transactions pour qu'il reste uniquement le registre des mandats, la
génération du numéro de mandat, la signature électronique et les passerelles ».*

**Le niveau à atteindre n'est pas une opinion : c'est ce que les trois autres objets ont déjà.**
Mesuré dans le code et les deux bases le 28/09.

| | contact | recherche | transaction | **annonce** |
|---|---|---|---|---|
| naît dans l'app | ✅ *(par l'annuaire)* · ⛔ *créé comme mandant : NON (30/09)* | ⚠ *la RPC n'écrit qu'une ligne PROVISOIRE (30/09) — à confirmer* | ✅ | ✅ *(e3, 25/09)* |
| **corps local persistant** | ✅ `app_contact_current` *(`CREATE IF NOT EXISTS`)* | ✅ | ✅ `app_affaire_ledger` | ⛔ **`app_view_generale` est `DROP` + `CREATE` chaque nuit** |
| registre de clés | ✅ | ✅ `app_search_registry` | — | ✅ `app_relation_registry` *(C.9-d)* |
| **classes A/B/C des champs** | implicite *(3 champs que Hektor ignore)* | sans objet *(porte fermée, C.3)* | ✅ **mesurées** *(campagne 0.1, close 18/09)* | ⛔ **jamais faite** |
| **carnet des saisies** | — | — | ✅ 10 colonnes | ⚠ 6 colonnes, et **3 gestes seulement** |
| **verdict sur la saisie** | — | — | ✅ `etat` + valeur d'avant + valeur relue | ⛔ **absent** |
| écran qui montre la divergence | — | — | ✅ modale affaire | ⛔ absent |
| l'œil serveur ↔ Supabase | ✅ `registre_couche_desaccord` | ✅ journal des doublures | ✅ journal | ✅ **`annonce_un_numero`** *(C.9-b)* — 0 écart sur 13 439 |
| sentinelles | ✅ | ✅ | ✅ | ✅ **4** *(un_numero · conflit · partielle · push_bloque)*, toutes à 0 |

> ⚠ **CE QUI EST DÉJÀ FAIT EST PLUS GRAND QUE JE NE L'AI DIT LE 28/09 AU MATIN.** J'ai écrit
> « personne ne compare l'annonce » et « pas de verdict » : **faux dans les deux cas**.
> `C.9-b` a posé **l'œil** le 24/09 *(il répond nommément au défaut D4)*, et la sentinelle
> `data.annonce_partielle` détecte **un champ ignoré par Hektor** — c'est-à-dire la classe A —
> avec seuil zéro et sévérité *critical*. L'erreur venait de m'être arrêté au premier fichier
> lu au lieu de balayer un mois de travail.

#### Les quatre tâches qui restent — et rien d'autre

| | quoi | modèle à copier | pourquoi maintenant |
|---|---|---|---|
| **N.1** ⚠ | ⚠⚠ **DECOCHEE LE 28/09 AU SOIR — LA CAMPAGNE A MESURE 53 CHAMPS SUR 189.** Le chiffre de 189 n'est pas une estimation : il est **remesure dans le worker ce soir** *(`HEKTOR_CLEANFIELD_TEXT_KEYS` **27** + `HEKTOR_CLEANFIELD_NUMBER_KEYS` **26** + `HEKTOR_WIZARD_FIELDS_BY_PROFILE` **136**)*, et il **tombe exactement** sur celui que la carte A1 annonçait le 19/08 — la carte n'a pas dérivé en 40 jours. La campagne, elle, tirait son périmètre de **68 travaux historiques** : elle n'ouvre **ni les constantes du worker, ni les 136 champs d'équipement** *(vérifié : le script ne les nomme nulle part)*. ➡ **Les 136 équipements ne sont pas mesurés**, et ce sont précisément ceux que la carte A1 signalait déjà en §6 : *« les 136 champs d'équipement n'ont pas été croisés un par un avec les 134 clés du blob »*. | **CE QUI RESTE VRAI DE LA CAMPAGNE** : sur les 53 champs qu'elle a vus, **B = 24 · A = 0 · C ou modifié = 16 · non concluant = 13**, et la conclusion *« `CHAMPS_APP_ANNONCE` reste VIDE »* **tient toujours** — un seul champ de classe A suffirait à la renverser, et il n'y en a aucun dans les 53. Mais elle repose sur **28 %** du périmètre. ↪ `605762a` |
| | ✅ **CE QU'ON N'A PAS BESOIN DE REFAIRE, ET C'EST L'ESSENTIEL** : la classification des champs d'annonce **EXISTE DEPUIS LE 19/08** — `notice/A1_CHAMPS_PROPRIETE_APP_2026-08-19.md`. Elle ne s'appelle pas A/B/C, elle est en **COULEURS**, et c'est pour ça qu'on ne la retrouvait pas : **VERT** *(l'app est l'auteur, l'import n'a pas le droit de réécrire — les 189 par défaut)* · **BLEU** *(Hektor produit, l'app ne sait pas fabriquer — `numero_mandat`, la diffusion, le cycle transaction, l'annuaire, le technique)* · **ORANGE** *(3 arbitrages)*. | ⚠ **DEUX VOCABULAIRES, DEUX AXES, ET ILS NE SE REMPLACENT PAS.** Les **couleurs** répondent à *« qui est l'auteur »* → elles commandent la **DESCENTE** *(l'import de nuit a-t-il le droit de réécrire ?)*. Les **lettres A/B/C** répondent à *« Hektor accepte-t-il l'écriture »* → elles commandent le **PUSH**. La campagne A/B/C a été menée sur **l'affaire** *(0.1, close le 18/09)*, **jamais sur l'annonce**. Les deux sont nécessaires ; aucune ne dispense de l'autre |
| | ✅ **ET LES 3 ARBITRAGES ORANGE NE SONT PAS UN OUBLI : ILS SONT VOLONTAIREMENT OUVERTS.** `statut_annonce`/`archive` · `negociateur_email`/`commercial_id` · les champs de mandat. Le plan **l. 1129** le dit déjà : *« c'est ICI que se répondent les 3 arbitrages de A1 »*, dans **C.4**, et **pas avant** — *« trancher plus tôt serait figer une carte sur un état qui va bouger »* *(décision de Frédéric, 24/08)*. Et **l. 1329** ajoute qu'ils ne sont pas des décisions de fond : le jour de la coupure Hektor n'existe plus, **l'app gagne tout** — ce sont **trois réglages de transition réversibles**. ⚠ `negociateur_email` reste bleu **jusqu'à la dernière phase** : le worker s'impersonne avec cet identifiant |
| | ➡ **N.1 EST DONC REDEFINIE, ET ELLE RETRECIT.** Il ne s'agit plus de *construire* une classification — elle existe. Il s'agit de **(a)** mesurer l'axe A/B/C sur les **136 champs d'équipement** jamais vus, avec la méthode de la phase 0 des transactions *(pousser, **relire**, comparer)*, et **(b)** faire enfin la **correspondance nom du worker ↔ colonne ou clé de blob**, que la carte A1 §6 réclame nommément : *« À faire avant A2, sinon on retire du paquet une colonne qui ne correspond à rien »*. Les noms diffèrent vraiment *(`title` → `titre_bien` + `texte_principal_titre`)* | ⚠ **(b) est un préalable de (a)**, pas une finition : sans la correspondance, une mesure sur un nom du worker ne sait pas quelle colonne relire |
| **A.3-tech — correction du 29/09** ⚠ | ⚠⚠ **J'AI FABRIQUÉ UNE URGENCE QUI N'EXISTAIT PAS.** J'ai écrit que la **famille** *(HEKTOR / PROTEXA)* était *« déduite, donc fragile »* et que **l'export PROTEXA bloquait les DEUX phases**. Frédéric : *« je comprends pas ta question, nous avions déjà audité cela »*. **Il avait raison, et c'était audité deux fois.** | ✅ **Feuille de route du 24/08** : `params[typeMandat]` vaut `mandat` ou `protexaMandat` — *« faux ami : ce n'est PAS le type juridique mais **la famille de registre** »*. Et **plan l. 1170** : *« les deux familles — `SIMPLE`/`EXCLUSIF`/`ACCORD` → HEKTOR ; libellé français → PROTEXA, **vérifié 10/10** »* |
| | ➡ **`_famille()` code EXACTEMENT cette règle** — je ne l'ai pas inventée, et elle n'est pas fragile. **Le doute ne porte que sur les lignes SANS TYPE** : 3 263, dont **2 342 locations** *(hors périmètre, sans importance)* et **921** dedans. Pas sur les 24 000. Et il ne bloque rien : au moment d'une offre, le worker **lit** la valeur chez Hektor au lieu de la déduire *(correctif du 25/08)*. | ➡ **L'export PROTEXA reste utile pour la PHASE 2** *(clore le registre, expliquer les 23 numéros sans trace)*. **La phase 1 n'en a pas besoin** |
| | ✅ **ET LE PÉRIMÈTRE EST DÉJÀ JUSTE — confirmé juridiquement par Frédéric** : les **271 mandats de GESTION** relèvent de la **carte G** *(registre-répertoire)*, pas du registre des mandats de la carte T. Ils doivent être exclus, **et ils le sont déjà** *(toutes sur des annonces de location)*. Les **63 RECHERCHE** sont sur vente ou commerce, **donc dedans**. | ➡ **Le filtre sur le type d'offre les sépare tout seul, sans le savoir. RIEN À CHANGER** |
| **A.3-tech — phase 1** ✅ | **QUATRE ÉTAPES SUR SIX, FAITES LE 29/09.** **A** `app_mandat`, table durable dormante — **26 822 lignes** *(24 750 fiches mandat + **2 072 numéros portés par l'annonce**, 2e source trouvée par le 4e contrôle : le registre en a **deux**, je n'en lisais qu'une)*. Clé = **(annonce, numéro)** — ⚠ **pas** `hektor_mandat_id` : Hektor range le même mandat sous plusieurs ids *(annonce 1972 / n° 17925 → trois ids)*. **B** branchée dans le run, **une** étape neuve non bloquante. **C** le registre ne suit plus `stale_ids` — **la seule modification d'existant**, retour arrière en un jeton. **E** la sentinelle `data.mandat_disparu`. ↪ `ffee94d` `7183934` `39374bf` `e26b2e4` `6c790eb` `40edc35` | ✅ **Contrôles** : 0 doublon · 0 trou · 0 dans la plage réservée · **rejeu à empreinte identique**. ⚠ **La table porte TOUT, locations comprises** *(« le serveur reçoit tous les types »)* — **c'est la VUE qui filtre** |
| | ⛔ **IL RESTE DEUX ÉTAPES, ET LES DEUX DEMANDENT FRÉDÉRIC.** **D** le worker écrit après `step5` *(+ la doublure)* → **redémarrage des 4 services**, en journée 06 h-22 h. **F** **LA RÉPARATION** — `push_upgrade_to_supabase.py --rebuild-register-only` : elle **vide le registre puis le refait depuis le miroir ENTIER** *(vérifié : `dossier_ids=None` → aucun filtre ; c'est elle qui a produit l'état du 31/07)*. Les **635** reviennent **et** les **23 091 lignes figées** se rafraîchissent. | ⚠⚠ **`F` ÉTAIT ABSENTE DU PLAN, ET FRÉDÉRIC L'A VU** : *« pourquoi tu ne le prévois pas dans le plan alors ? »*. J'avais décrit la réparation comme évidente sans la planifier — or **sans elle la sentinelle reste rouge et une alerte part chaque jour**. ⚠ pendant l'opération **le registre est VIDE** : jamais pendant le run de nuit |
| | ➡ **LE CHIFFRE, CORRIGÉ TROIS FOIS PAR FRÉDÉRIC** : **2 983** absents du registre — dont **2 348 LOCATIONS**, écartées par sa décision du 26/08. ➡ **la vraie perte est 635, dont 80 mandats EN COURS**. *(Et avant ça : 1 105 le 28/08, 175 le 28/09 — trois tranches d'une seule maladie, mesurée pour la première fois sur la totalité.)* | ⚠ **Un total qui mélange le voulu et le subi ne veut rien dire.** La formule rend désormais **trois** chiffres, jamais un seul |
| **A.3-tech** 🔴 | **LE REGISTRE DES MANDATS — CADRAGE DU 29/09, DANS L'ORDRE DE FRÉDÉRIC.** ⭐ **Deux phases, et c'est LUI qui les a mises dans le bon ordre** : je faisais dépendre le petit chantier du gros. **Phase 1 = la DONNÉE, maintenant. Phase 2 = le REGISTRE LÉGAL, plus tard.** | ⛔ **Le mandat est le SEUL des 8 objets sans identité** *(mesuré le 28/09 sur 705 551 lignes)*. Ses deux repères actuels ne tiennent ni l'un ni l'autre : **23 452 id Hektor distincts pour 23 840 mandats** *(Hektor réutilise)* et **17 721 numéros légaux pour 23 840** *(6 119 doublons)* |
| | **PHASE 1 — NOTRE REGISTRE, LA DONNÉE SEULE.** ⚠ **Hektor et PROTEXA ne bougent pas : le numéro continue de venir d'eux, par le worker, exactement comme aujourd'hui.** ① **arrêter la perte** — le push nocturne supprime les lignes des annonces qui quittent le parc *(`stale_ids`, et le commentaire l. 1293 le dit : le registre est traité comme une table jetable)* et l'incrémental ne les remet pas ; ② **`app_mandat` + `app_mandat_id`** en plage réservée *(patron `app_affaire_id_app_seq`)*, `delete-never` ; ③ **le rattrapage des 24 995 mandats du miroir** — clé = **couple (annonce, mandat)**, vérifiée unique *(24 995 couples pour 24 995 mandats)* ; ④ **le worker écrit AUSSI chez nous après `step5`** — les deux sens alimentent la même table ; ⑤ **une sentinelle `mandat_disparu`** *(le mandat n'en a qu'UNE sur les 24 du projet)*. | ✅ **AUCUN RISQUE JURIDIQUE EN PHASE 1** : tant que PROTEXA fabrique le numéro, **c'est LUI le registre légal**. `app_mandat_register_current` n'est qu'un outil de travail. ⚠ **PÉRISSABLE** : les 24 995 ne se recopient que depuis le miroir |
| | **PHASE 2 — LE REGISTRE ÉLECTRONIQUE LÉGAL.** Le jour où le bouton « générer un numéro » bascule sur nous. **~3 à 4 semaines, et ce n'est pas que du code.** ⚠ **RÉGLEMENTATION VÉRIFIÉE AUX TEXTES LE 29/09** — *décret 72-678 art. 65* : le registre est *« à l'avance **coté sans discontinuité** et relié »*, son numéro est *« **reporté sur l'exemplaire du mandat qui reste en la possession du mandant** »*, et il *« peut être tenu sous forme électronique **dans les conditions des articles 1365 et suivants du code civil** »* *(autorisé depuis le décret du 21/10/2005)*. | ⚠ **AUCUN texte ne pose de règle technique** : le code civil exige **deux choses** — ① **identifier de façon certaine** la personne dont émane l'écrit ② l'**établir et le conserver dans des conditions garantissant l'INTÉGRITÉ**. ➡ **C'est une obligation de PREUVE, pas une liste à cocher** |
| | ⛔⛔ **TROIS CORRECTIONS QUE LA RECHERCHE IMPOSE À LA PROPOSITION DU MATIN.** ① **le préfixe `RE-` est probablement interdit** — PROTEXA l'écrit : *« un numéro séquentiel, sans trou **ni préfixe ni suffixe** »* ; ② **repartir de 1 est risqué** : sans préfixe, le « n° 1 » du nouveau registre ne se distingue plus du « n° 1 » de 2015 → **recommandation : CONTINUER la série là où PROTEXA s'arrête** *(« coté sans discontinuité » respecté à la lettre)* ; ③ **l'horodatage tiers n'est pas une option** — *« en l'absence de date certaine, la formalité d'enregistrement chronologique n'est pas régulièrement accomplie et **le mandat est NUL** »*. | ⚠ **SANCTIONS** : jusqu'à **2 ans d'emprisonnement et 3 000 €**, + suspension ou retrait de la carte professionnelle, + **un mandat mal enregistré est nul → plus de droit aux honoraires** |
| | ✅ **CE QUI N'EST PAS À FAIRE, ET QUE J'AI FAILLI CASSER.** J'ai proposé de *« sortir le numéro du worker et le mettre derrière une porte unique »*. **Frédéric : « s'il y a 5 portes, il y a sûrement une raison ».** Il avait raison : **les 5 étapes SONT l'assistant PROTEXA**, rejoué pas à pas faute d'API — et la note du **18/05** dit que la séparation est **volontaire** : *« Hektor **consomme un vrai numéro** au moment de la validation »*, *« si aucun mandant n'est détecté, le job passe en erreur **sans consommer de numéro** »*. | ⭐ **ET LA PORTE UNIQUE EXISTE DÉJÀ, DEPUIS MAI** : le front appelle **une seule RPC** *(`app_console_create_mandat_auto_number_job`)*, envoie la **description** du mandat *(type, dates, durée, mandants, négociateur)* et **ne reçoit jamais de numéro**. ➡ **le jour de la bascule, le front ne change pas d'une ligne.** L'anticipation demandée est faite par construction |
| | ⛔ **CE QUI NE DÉPEND PAS DE MOI, ET QUI BLOQUE LA PHASE 2** : ① **demander à PROTEXA l'export complet de sa série** *(un mail)* — bloquant, et c'est le seul moyen de savoir **où reprendre la numérotation** ; **23 numéros de la série n'ont aucune trace chez nous** *(mesuré le 28/09)* ; ② **faire valider la forme légale par un juriste** — elle dimensionne l'inaltérabilité et l'horodatage ; ③ **choisir le tiers d'horodatage** *(un abonnement)*. | ⏳ **Les lots de la phase 1 n'attendent aucune des trois.** Ils peuvent commencer tout de suite |
| **AUDIT FINAL** ✅ | ⭐ **L'ANNONCE N'EST PAS AU NIVEAU DES AUTRES OBJETS : ELLE EST AU-DESSUS** *(28/09, tout mesuré dans le code et les deux bases)*. **gestes du worker 15** *(contact 6 · recherche 3 · relation 1 · transaction 4)* · **tables Supabase 17** *(12 · 6 · 1 · 9)* · **RPC optimistes vivantes 6** *(3 · 2 · 2 · 3)* · corps durable en local **189/189**. | ✅ **DEUX CHOSES QU'ELLE SEULE SAIT FAIRE** : ① **détecter un envoi partiel** — sa file porte `partial` + `skipped_fields`, **15 colonnes contre 13** pour le contact et la recherche ; ② **un œil dédié** *(`annonce_un_numero`, `C.9-b`)*, 0 écart sur 13 439 |
| | ⚠⚠ **CHIFFRE PÉRIMÉ CORRIGÉ : « 5 workers sur 16 écrivent d'abord dans l'app » DATAIT DU 29/08.** Sept RPC optimistes ont été construites depuis *(archiver, restaurer, affecter le négociateur, créer un contact, créer un mandant, mettre à jour un mandant, créer une recherche)*. **Vérifié qu'aucune n'est dormante : les 15 sont appelées par le front.** ➡ **la vraie couverture est 13 SUR 16**. ⚠ **NUANCE DU 30/09** : « créer un mandant » et « rattacher un mandant » n'écrivent qu'une ligne **PROVISOIRE** de lien, jamais la ligne durable — pour la relation, « écrire d'abord » n'est pas atteint. | ✅ **Et les 3 manquantes sont VOLONTAIRES** : ce sont les trois **suppressions**, exclues par l'arbitrage du 30/08 — *« une suppression n'est pas une correction, c'est un événement : l'annonce s'en va, il n'y a plus rien à comparer »* |
| | ✅ **LES 5 SENTINELLES NE SONT PAS UN RETARD SUR LES 10 DU CONTACT — il faut les déplier** : les **3 de base** *(conflit · push_bloqué · sans_numéro)* sont là des deux côtés ; l'annonce en a **deux de plus** *(partielle · un_numéro)* que le contact n'a pas ; et les **7 supplémentaires du contact** surveillent les **doublons et les fiches de couple** — un problème qui **n'existe pas** pour l'annonce. | ➡ même famille d'erreur que le reste de la journée : **un total ne se compare pas, il se déplie**. Comparés tels quels, 5 contre 10 disait « retard » ; dépliés, ils disent **l'inverse** |
| | ⚠ **LA SEULE VRAIE FAIBLESSE TROUVÉE, ET ELLE N'EST PAS SUR L'ANNONCE : `RELATION`.** **1 table** *(`app_relation_provisional`)*, **0 sentinelle**, **pas de file d'attente**. Un lien mandant se crée par RPC optimiste *(`app_link_mandant_optimistic`, vivante)*, mais **personne ne surveille qu'il arrive chez Hektor**. | ⚠ **NOTÉ, PAS ENCHAÎNÉ** — c'est hors du sujet « annonces » *(règle « rester sur le plan d'autonomie »)*. ⏳ à reprendre après `L9` · ➡ **AUDITÉE EN PROFONDEUR LE 30/09 — voir « LE REGISTRE DES RELATIONS DEVIENT AUTONOME »** : le trou est plus large qu'une sentinelle, le lien n'existe que par le miroir |
| | ✅✅ **CONCLUSION : LE SUJET « ANNONCES » PEUT ÊTRE CLOS.** Il y reste **deux gestes de confort** *(supprimer/réordonner une photo · modifier un mandat existant)*, qui **ne périment pas**, et les **quatre exceptions** connues. | ➡ **la suite utile n'est pas l'annonce, c'est ce qui PÉRIME** : `L9` le registre des mandats · les liens publics *(11bis)* · `C.9-couple` |
| **N.4** ⚠ | ✅✅ **MESURÉ LE 28/09, ET LE RÉSULTAT EST MEILLEUR QUE L'ÉNONCÉ : POUR UN BIEN VIVANT, LA DOUBLURE EST **COMPLÈTE**.** Les **189** champs du worker sont **tous** présents dans la copie descendue de Supabase — **189 présents, 0 absent**. Répartition : **70** colonnes `app_dossiers_current` *(la façade)* + **134** clés de `detail_payload_json` + **216** noms sous `props` / `fields`. | ⚠ **CE QUI TROMPE, C'EST LES 70 COLONNES** : on regarde la façade en croyant voir la maison. Équipements, diagnostics, terrain, copropriété, textes vivent **dans le blob**, à trois niveaux. Même piège que le « 180 absents » de `N.1-(b)` le matin même |
| | ✅ **ET LE TROU DE `N.4` N'EST PAS OUVERT AUJOURD'HUI — mesuré DEUX FOIS, par deux chemins indépendants** *(jointure SQL, puis comparaison par ensembles)* : **0 annonce de la copie manque à la vue**, sur 13 439. Et ce ne peut pas être autrement tant que **chaque annonce reçoit un numéro Hektor à la naissance** *(vérifié : 0 sur 13 439 sans numéro)*. ➡ **le trou s'ouvrira le jour où Hektor cessera d'en donner, pas avant.** | *(La vue porte 61 286 et la copie 13 439 : la vue garde tout depuis l'origine, la copie ne porte que les vivantes. Les 47 847 d'écart sont les archives, qui ont leurs propres tables.)* |
| | ⚠⚠ **LE VRAI SUJET N'EST PAS `N.4`, IL EST PLUS SIMPLE ET PLUS URGENT : LE DÉTAIL DES ARCHIVES N'EXISTE QU'EN UN SEUL EXEMPLAIRE.** La doublure ne descend, pour un bien archivé, qu'un **index de 35 colonnes** *(35 301 archives · 8 922 historiques · 485 brouillons)* — ni équipements, ni diagnostics, ni textes. Le détail des **34 515** archives vit **uniquement** dans `data/hektor.sqlite` *(3,9 Go)*, et le compte se répond : l'index annonce `has_local_detail` pour **34 515**, le miroir en porte **34 515**. | ✅ **Ce n'est pas un oubli** : c'est la règle écrite *(« serveur = tout / cloud = biens vivants »)*, et la **RÈGLE 5** protège le miroir — *« il ne se vide jamais pour se remplir »*, *« après la coupure il **GÈLE**, il ne devient pas inutile »*. Le miroir **accumule** : 61 284 annonces pour 13 439 vivantes |
| | ⛔ **LA SEULE QUESTION OUVERTE DE TOUTE LA MESURE — À TRANCHER PAR FRÉDÉRIC.** `data/hektor.sqlite` **n'entre pas dans la sauvegarde automatique** : c'est le **niveau 4**, `--full`, *« sur demande »*. La tâche planifiée *(`scheduled/run_backup.ps1`)* passe `--weekly` le dimanche — **jamais `--full`**. ➡ soit on l'ajoute, soit on confirme que l'agent OVH le prend au niveau du disque *(la note dit qu'il couvre les documents locaux, ce qui le laisse penser, mais ce n'est **pas écrit**)*. | ⚠ **Une ligne dans les deux cas** — et c'est le contenu de **34 515 biens archivés** qui en dépend. ⏳ en attente |
| **N.2** ⚠ | ⚠⚠ **À REDESSINER — MON ÉNONCÉ ÉTAIT FAUX** *(audit du 28/09)*. J'avais écrit « ajouter à `app_annonce_champ_app` les 4 colonnes que `app_affaire_champ_app` possède ». **Mesuré en production : le carnet d'annonce porte 3 LIGNES EN TOUT** *(un `geste_archiver`, un `geste_affecter_negociateur`, une `redescente_transaction`)*, et le worker ne le touche **qu'à un seul endroit**, pour le seul champ `statut`, sur le chemin « Hektor a refusé ». Poser un verdict sur une table que personne n'écrit ne jugerait rien. | ⚠ **ET CE N'EST PAS UN MANQUE : C'EST SA DÉFINITION.** `magasin_annonce_app.py` le dit en tête : *« ce n'est PAS une copie de la liste des annonces — c'est un carnet d'**EXCEPTIONS**, une ligne par champ dont l'app est l'auteur »*, et `CHAMPS_CONNUS` n'en compte que **quatre** : `archive`, `negociateur_email`, `statut_annonce`, `diffusable` — **exactement les ORANGE de A1**. ➡ **`N.3` « le front écrit au carnet à chaque modification » est donc À ABANDONNER : elle transformerait le carnet d'exceptions en doublon du registre** |
| | ✅ **CE QUE L'ANNONCE A DÉJÀ, ET QUE JE N'AVAIS PAS MESURÉ — LE MODÈLE B EST LÀ, DE BOUT EN BOUT** *(`console_job_worker.js` l. 10505-10580)* : ① **la photo** — `app_annonce_pending.base_snapshot`, avec `_date_maj` ; ② **le garde-fou anti-écrasement** — le worker **relit la date de Hektor** avant d'écrire, et si Hektor est plus récent **il gagne et la saisie est SOLDÉE au journal des résolutions**, jamais perdue ; ③ **le bilan du push** — `skipped` → `markAnnoncePartial`, et **le pending est CONSERVÉ** pour que le badge du front et la sentinelle le voient *« au lieu d'un faux enregistré »* ; ④ **le pending n'est effacé que si tout est passé** ; ⑤ une **resynchro est mise en file** *(`refresh_console_data`)*. | ✅ **Le patch de l'affaire le disait déjà, et je l'ai lu sans le voir** : *« Pour l'annonce, `partial` + `skipped_fields` disent ‹ 7 champs sur 10 sont passés › »*. **C'est l'affaire qui a copié l'annonce**, pas l'inverse — et elle a **délibérément divergé** pour le reste *(« on ne recopie donc pas le patron à la lettre — c'est voulu »)*. Ma comparaison « l'annonce est en retard sur l'affaire » était **fausse dans son principe** |
| | ➡ **LE VRAI TROU, ET IL EST ÉTROIT.** `skipped` ne nomme que les champs **que le worker lui-même a jetés** *(un `<select>` non résolu, par exemple)*. Un champ que Hektor **accepte puis ne retient pas** — parce qu'il le recalcule, la **classe C** — sort avec `wrote = true`, `skipped = []` : **le pending est effacé, l'app affiche « arrivé », et Hektor porte autre chose.** Rien ne le voit, ni le badge ni la sentinelle. | ➡ **N.2 REDEVIENT UTILE, MAIS AUTREMENT** : non pas quatre colonnes sur un carnet vide, mais **comparer, après la resynchro déjà mise en file, ce qui est REVENU à ce qui a été ENVOYÉ**, champ par champ. La matière existe entièrement : la photo, la saisie, et la cible à relire que **`N.1-(b)` vient de fournir** |
| | ⚠ **ET C'EST LÀ QUE LES 9 AMBIGUS MORDENT.** Relire `surface` dans la colonne, dans le blob ou dans `ag_interieur_json/props/surfappart` peut donner **trois réponses**. Et `titre_bien` est un COALESCE qui préfère le **listing** au **détail** : relire là rendrait l'ancienne valeur et crierait au conflit sans raison. **La cible de relecture doit être figée champ par champ avant d'écrire une ligne de N.2** | ⏳ **cadrage fini, aucun code.** Prochaine étape : arbitrage de Frédéric sur la forme |
| **N.1-(a)** ❌ | ❌❌ **DISSOUTE LE 28/09, SANS ÉCRIRE UNE LIGNE — ET FRÉDÉRIC L'AVAIT DIT** *(« je comprends pas, nous avions déjà vu cela »)*. Je voulais mesurer l'axe A/B/C sur les **136 champs d'équipement** en poussant chez Hektor. **Ce travail existe, et il est clos depuis le 25/09** : `notice/CARTE_CHAMPS_ANNONCE_2026-09-21.md` puis `notice/AUDIT_L5_GESTES_MANQUANTS_2026-09-25.md`. | ✅ **AUCUN CHAMP N'EST CRÉABLE SANS ÊTRE CORRIGIBLE.** `HEKTOR_WIZARD_UPDATE_GROUPS` — la modification par groupes *(secteur, intérieur, extérieur, terrain, équipements, diagnostics, copropriété, construction récente, visite, mandat)* — **existe depuis le 02/06/2026** *(`a2e8160`)* |
| | ✅ **REMESURÉ LE 28/09 CONTRE LE CODE D'AUJOURD'HUI, et le compte tombe :** les groupes portent **179 champs** et couvrent **177 des 189**. Les **12** restants ont tous un chemin connu : **8** passent par la voie *cleanfield* *(`title`, `description`, `private_city`, `private_postal`, `fees`… — ce sont les « 53 modifiables » de la carte du 21/09)*, **3** par `applyHektorChauffage` *(le chauffage a **son propre chemin**, appelé à chaque modification)*. | ➡ **IL NE RESTE QUE LES QUATRE `mandate_*`** — et ce n'est pas un trou nouveau : c'est le geste **« modifier un mandat existant »**, déjà nommé dans `L5` *(2-3 j)* |
| | ⚠⚠ **D'OÙ VENAIT LE « 102 champs créables mais non modifiables » DU PLAN** — et c'est le piège le plus coûteux de ce chantier : `HEKTOR_WIZARD_FIELDS_BY_PROFILE` *(création)* parle **le vocabulaire Hektor** *(`NB_CHAMBRES`, `surfappart`)*, `HEKTOR_UPDATE_FIELDS_BY_PROFILE` parle **celui de l'app** *(`bedroom_count`, `surface`)*. Comparées telles quelles, les deux listes n'ont **aucun** champ commun et rendent un écart de **136** — l'ordre de grandeur du « 102 ». **Deux listes incomplètes, deux langues, un chiffre faux resté six jours dans le plan.** | ➡ **C'est exactement la même famille d'erreur que « les couleurs ne sont pas des lettres », trouvée le même jour.** Ce chantier a **plusieurs vocabulaires** pour les mêmes objets ; toute comparaison de listes doit d'abord vérifier **qu'elles sont complètes et qu'elles parlent la même langue** |
| | ➡ **CE QUE ÇA CHANGE POUR LA SUITE : N.1 EST CLOSE EN ENTIER.** L'axe A/B/C n'a plus d'objet pour l'annonce — non parce qu'il serait sans intérêt, mais parce que **la protection ne passe pas par lui** : `CHAMPS_APP_ANNONCE` reste **vide** *(le GEL)*, et ce qui protège est le **modèle B** — pousser, **relire**, écrire ce que Hektor a retenu, **montrer le verdict**. Un champ de classe A se dénoncerait **tout seul** par ce mécanisme, et `data.annonce_partielle` le guette déjà en *critical*, seuil zéro. | ➡ **La suite est donc `N.2` puis `N.3`**, qui construisent précisément ce verdict. `N.1-(b)` leur a donné **la cible à relire** ; sans elle, le verdict relirait la mauvaise colonne |
| **N.1-(b)** ✅ | **LA CORRESPONDANCE EST FAITE — 189 SUR 189, ZÉRO ABSENT** *(28/09)*. `phase2/checks/correspondance_champs_annonce.py`, **lecture seule** : aucun appel Hektor, aucune écriture, aucune connexion Supabase. **UN SEUL 170 · AMBIGU 9 · SUFFIXE 3 · À LA MAIN 7 · ABSENT 0.** ↪ `7acebc6` | ✅ **ELLE FERME LE TROU DE A1 §6**, qui réclamait nommément *« la correspondance exacte entre chaque champ du worker et sa colonne ou sa clé de blob »* **avant A2** |
| | ✅ **TROIS FORMES DE RANGEMENT, PAS UNE** — et c'est la vraie trouvaille : **163** colonnes de `app_view_generale` · **134** clés au premier niveau de `detail_payload_json` · **216** noms sous un porteur **`props`** *(détail d'API)* **ou `fields`** *(capture de console : `console_missing_fields_json/groups/<g>/editer/fields`)*. | ⚠ **Les noms du worker ne sont pas traduits, ils sont ENFOUIS** : `ASCENSEUR` côté worker est `ASCENSEUR` côté blob — mais à **trois niveaux**, derrière un maillon qui est une **chaîne contenant du JSON**. Il n'y avait rien à traduire ; il y avait un chemin à suivre |
| | ⚠⚠ **TROIS DÉFAUTS TROUVÉS DANS MON PROPRE OUTIL AVANT DE LE CROIRE.** ① profondeur limitée à 6, or le chemin des diagnostics en fait **six pile** — la coupe tombait sur le dernier maillon, et `diag_termites` était annoncé **absent** alors qu'il est dans **12 814 lignes sur 13 439**. ② échantillon des **4 000 premières lignes, dans l'ordre du fichier** : `PISCINE_CHAUFFEE` *(96)*, `SHON` *(111)*, `typeChauff` *(101)*, `syndic` *(250)*, `terrain_viabilise` *(48)* sont **tous au-delà du rang 4 000**. ③ un seul porteur lu sur deux. | ➡ **UN ÉCHANTILLON PRIS DANS L'ORDRE N'EST PAS UN ÉCHANTILLON, C'EST UN DÉBUT.** Et **un champ rare est précisément celui qu'on croira perdu**. La première mesure rendait *« 180 absents sur 189 »* : elle ne mesurait pas l'absence, elle mesurait **sa propre profondeur**. On lit désormais **tout le miroir** |
| | ✅ **LA MESURE TOMBE SUR LA LISTE D'EXCEPTIONS DE A1, TOUTE SEULE.** Les **7** champs qu'aucune règle ne trouve sont **exactement** ceux que la carte nommait : `title` et `description` *(son exemple, mot pour mot)* et les **quatre `mandate_*`** *(ses champs **ORANGE**)*, plus `private_postal`. Tous résolus à la main et **vérifiés un par un** contre les colonnes | C'est la meilleure preuve qu'on pouvait attendre que la carte et le code parlent du même objet |
| | ⚠⚠ **LE PIÈGE À EMPORTER DANS N.1-(a)** : `titre_bien` est un **COALESCE** qui préfère `ann.titre` *(le **listing**)* à `det.texte_principal_titre` *(le **détail**)*. Pousser un titre puis le relire dans `titre_bien` peut donc rendre **l'ancienne valeur sans que rien n'échoue**. ➡ la relecture doit viser `texte_principal_titre`. | ⚠ **Et les 9 AMBIGUS sont le même risque, généralisé** : un nom, plusieurs cibles *(`surface` → colonne **et** blob **et** `ag_interieur_json/props/surfappart`)*. **Relire la mauvaise cible rend un verdict faux sans rien signaler** — c'est sur eux que se joue N.1-(a) |
| **N.1-bis** ✅ | **LA REVUE DES 34 WORKERS EXISTE AUSSI, et elle est du 20/08** — `notice/ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20.md`. Fermeture transitive à profondeur 4 dans `console_job_worker.js`. **4 familles** : **A** l'app seule *(3 workers, **0 appel Hektor** — les 3 PDF)* · **B** vers Hektor *(19)* · **C** aller-retour *(8)* · **D** interne *(4)*. **7 workers sur 34 tournent déjà sans Hektor.** | ✅ **ELLE CONFIRME LES QUATRE EXCEPTIONS DE FRÉDéRIC, par la mesure et non par la mémoire** : seuls `create_hektor_mandat_auto_number` *(19 appels)*, `relance_signature` et `cancel_signature_procedure` dépendent de Hektor **parce qu'il PRODUIT** quelque chose. Les 31 autres n'en dépendent que **parce qu'il détient encore la donnée** — ils *disparaissent* à la coupure, ils ne se *portent* pas |
| **N.1** ✓ | ~~**LA CAMPAGNE DES CHAMPS D'ANNONCE**~~ **partie FAITE le 28/09** — `phase2/checks/campagne_champs_annonce.py`, lecture seule, aucun appel à Hektor. **Résultat : B = 24 champs · A = 0 · C ou modifié = 16 · non concluant = 13** *(noms de l'app traduits par le worker, ou valeur vide sur ces biens)*. ↪ `605762a` | ⚠⚠ **CE QUE ÇA DÉCIDE** : **aucun champ d'annonce n'est ignoré par Hektor**, donc `CHAMPS_APP_ANNONCE` doit **RESTER VIDE** — comme `CHAMPS_APP_AFFAIRE` depuis le 16/09. Y inscrire un champ que Hektor connaît le **figerait** *(le GEL)*. ➡ **la protection de l'annonce passe par le MODÈLE B**, pas par le contrat : pousser, **relire**, écrire ce que Hektor a retenu, **afficher le verdict**. **N.2 et N.3 sont donc confirmées, et N.4 reste indépendante.** ⚠ Défaut de l'outil corrigé avant de conclure : la 1re version ne lisait que `raw_json` et inventait 8 absences — le chauffage revient par la **console**, pas par l'API *(11 cas résolus en élargissant)* |
| | ~~**LA CAMPAGNE DES CHAMPS D'ANNONCE**~~ — classer en A / B / C. **Mesure, aucun code.** ⚠ **ÉNONCÉ D'ORIGINE, CONSERVÉ POUR MÉMOIRE, ET FAUX SUR LE PÉRIMÈTRE** — « les données existent déjà : **68 travaux `update_hektor_annonce_fields`**, ~110 champs distincts, et chaque payload porte la valeur envoyée **et** `base_snapshot` *(ce que Hektor portait avant)*, aux **noms Hektor** — donc comparable au miroir sans table de correspondance. | **phase 0** des transactions *(« le cycle complet avait envoyé des valeurs connues, il suffisait de relire ce que Hektor a RETENU »)* | **BLOQUANTE**, comme elle l'était pour les transactions : *« rien ne se code avant cette phase, c'est elle qui décide de la forme des autres »* |
| **N.2** | **LE VERDICT AU CARNET DE L'ANNONCE** — ajouter à `app_annonce_champ_app` les 4 colonnes que `app_affaire_champ_app` possède déjà : `valeur_hektor_au_moment`, `etat`, `valeur_hektor_relue`, `constate_le` ; le worker les pose après chaque envoi. | `app_affaire_champ_app` + le verdict du 16/09 | sans lui, une saisie qui n'arrive pas **se tait** — c'est ce qui rend la liste de contrat vide *sûre* pour l'affaire, et pas encore pour l'annonce |
| **N.3** | **LE FRONT ÉCRIT AU CARNET** à chaque modification d'annonce. Aujourd'hui le carnet ne capte que **3 gestes** *(`geste_archiver`, `geste_affecter_negociateur`, `redescente_transaction`)* : quand un négociateur corrige un prix, **rien n'est noté**. | `loadAffaireChampsApp` / la modale affaire | c'est ce qui alimente N.2 |
| **N.4** | **LE CORPS LOCAL PERSISTANT** — `26bis-(3)`. Le contact a `CREATE IF NOT EXISTS` + upsert ; l'annonce a `DROP TABLE` + `CREATE TABLE AS`. Méthode déjà tranchée le 28/08 : **une ligne de 10 colonnes dans `app_dossier`**, la vue se reconstruit autour. ⚠ **surtout pas `--injecter`** *(163 colonnes réécrites chaque nuit, « réparateur par construction »)* | `app_contact_current` | ⚠ **date de péremption** : le remplissage vient du miroir, il exige que **Hektor vive encore** |

**Ordre : N.1 → N.2 → N.3 → N.4.** N.4 est indépendante des trois premières et peut avancer en
parallèle ; N.1 commande la forme de N.2 et N.3.

#### Ce qui reste APRÈS, et qui ne fait pas partie de l'annonce

Ce sont les **quatre exceptions** que Frédéric a nommées le 28/09 — elles ne dépendent pas du
code de l'annonce et gardent leur place dans le plan :

```
   le registre des mandats            L9 / A.3-technique
   la generation du numero de mandat  L6  (Hektor le fabrique encore)
   la signature electronique          A.2 (abonnement Hektor -- ImmoSign)
   les passerelles de diffusion       A.1
```

⚠ **Ne pas confondre avec les gestes de `L5`**, qui restent ouverts mais ne bloquent pas
l'autonomie : prolonger un mandat, les gestes photo *(supprimer, réordonner, choisir la
principale)*, la fusion de doublons, retirer un mandant, et le ménage des liens « Ouvrir
Hektor ».

---

**Total : ~3 à 4 mois.**

> ⚠ **CORRECTION DU 21/09, ET ELLE VAUT POUR TOUT LE PLAN.** On écrivait « tout se construit
> dormant, derrière un interrupteur ». **Frédéric a corrigé** : il n'y a pas d'interrupteur à
> actionner un jour. Saisir dans Hektor **ou** dans l'app doit fonctionner **des deux côtés,
> dès maintenant** — ce qu'on interdit, c'est de saisir **des deux côtés à la fois sur le même
> champ**. L'arbitre est **la récence**, en permanence.
>
> Conséquence : chaque lot doit améliorer le comportement **tout de suite**, dans la
> configuration actuelle *(les commerciaux dans Hektor)*, et non préparer une bascule. Ce qui
> reste « dormant » au sens strict, ce sont seulement les mécanismes qui ne peuvent servir
> qu'à un objet né dans l'app — la porte, la barrière, les recensements — puisqu'il n'en
> existe encore aucun.

⚠ **Deux lots ont une date de péremption** : **L2** et **L9** se remplissent **depuis le
miroir**. Ils exigent que **Hektor vive encore** — L9 doit donc être **fini avant** la
coupure, pas pendant.

**Quand l'utilisateur cesse d'attendre** *(mesuré le 20/09 sur 60 jours)* : créer un contact
coûte **18 s**, une annonce **58 s**, une photo **25 s**, un document **16 s** — la connexion
à froid chez Hektor en explique ~35. **L3** fait que la saisie ne revient plus modifiée ;
**L4** rend la **création immédiate** ; **L7** rend photos et documents immédiats ; **L8**
rend les workers invisibles.

**Ce qui attend une décision de Frédéric** : les gestes de **L5** *(fusion de doublons,
suppression d'annonce, reprise d'un brouillon : tout dans l'app ou exception admin ?)* ·
**RDV et visites** *(audit fait le 19/09 : tout est construit, presque rien n'est utilisé ;
les visites Hektor ne sont importées nulle part)* · **le rapprochement automatique**
*(automatique pur ou validé en un clic · seuil 75 ou 80 · base RGPD · relances)*.

---

## 🔗 LE REGISTRE DES RELATIONS DEVIENT AUTONOME — *audité le 30/09, AUCUN CODE*

> **Pour le chat de chantier : lire CETTE section, puis la note complète**
> `notice/AUDIT_REGISTRE_RELATIONS_AUTONOME_2026-09-30.md` *(mesures, lignes de code,
> historique)*. **Rien n'est décidé tant que Frédéric n'a pas répondu aux 5 questions du
> point ⑦.** Audit limité à l'objet RELATION ; les autres objets ne sont pas mesurés.

### ① Le point de départ — un bug à l'écran

Fiche contact de **Julien SAURA** ouverte depuis l'annonce V790062411 : *« Aucune annonce
liée »*, alors que l'annonce le montre mandant. **Les données sont justes** (3 liens sous son
identité `10058265`). La fiche annonce passe le **n° Hektor** `110090` ; `loadContactById`
cherche sous les deux numéros, **`loadContactRelations` et `loadContactSearches` non**
(`App.tsx:13060`). C'est la décision **G-6 du 23/09** (« cohérentes par construction »),
**jamais vérifiée sur ce chemin** et **figée par un test** (`test_genants_front.cjs:83`).
En tirant ce fil, on a trouvé le vrai sujet :

### ② La situation, en simple

```
LE LIEN A SON NUMERO CHEZ NOUS            OUI  carnet app_relation_registry (C.9-d, C.9-f)
LE LIEN EXISTE PARCE QUE NOUS LE DISONS   NON  la table est VIDEE puis REFAITE chaque nuit
                                               depuis 6 sources Hektor
L'APP ECRIT UN LIEN DURABLE               NON  une ligne PROVISOIRE, purgee sous 24 h
LE WORKER ECRIT UN LIEN DURABLE           NON  il sait seulement EFFACER (suppression)
CONTRAT D'AUTORITE HEKTOR <-> APP         AUCUN
SENTINELLE                                AUCUNE
LA FICHE ANNONCE LIT LE REGISTRE          NON  elle lit proprietaires_json (copie Hektor)
```

**Un lien naît toujours chez Hektor.** Quand un négociateur ajoute un mandant : étiquette
provisoire → le worker crée le lien chez Hektor → la nuit, le run recopie Hektor → alors
seulement le lien existe chez nous. **Le jour de la coupure, plus rien n'arrive** : le plan
l'avait écrit dès le **03/09** (révision du 03/09, bloc « 26bis-relations n'avait jamais été décrit » : *« ce patron meurt à la coupure »*).

**C'est le seul objet à un seul robinet.** L'annonce, le contact et la transaction ont les
deux (le run ET l'app) ; le mandat les aura avec l'étape D.

### ③ Ce que contient le registre aujourd'hui *(mesuré le 30/09)*

```
serveur   167 547 liens · 109 605 contacts · 58 622 biens      (6 sources, toutes Hektor)
          carnet 167 583 cles, 36 absentes (jamais effacees) · 45 « app seule », jamais reinjectees
Supabase   81 379 = les biens ACTIFS seulement (push : WHERE is_active_annonce = 1)
          contacts nes dans l'app (>= 20 M) : 0 — le compteur est encore a 20 000 000

mandant       74 166   (fiche annonce 45 134 · lien annonce-contact 24 617 · fiche contact 4 415)
proprietaire  58 456   (fiche annonce 30 409 · lien annonce-contact 25 977 · fiche contact 2 070)
acquereur     34 925   (compromis 13 269 · offre 11 145 · vente 10 511)
```

**TROIS FAITS QUI COMMANDENT LA CONCEPTION :**

- **« Mandant » et « propriétaire » sont UN SEUL fait Hektor** (« propriétaire du bien »).
  Le build réécrit le rôle **après** le calcul de la clé : `mandant` si l'annonce a un n° de
  mandat, sinon `proprietaire` (`build_contacts_layer.py:1337`). ➡ le registre stocke le
  **fait brut**, le libellé se **dérive** — sinon chaque mandat signé change l'identité du lien.
- **Le même lien arrive par trois fenêtres de Hektor** (fiche annonce, lien annonce-contact,
  fiche contact) : même clé, la dernière lue gagne.
- **Les acquéreurs sont DÉJÀ tenus chez nous**, durablement et à deux robinets, dans
  `app_affaire_ledger` (30 364 sur 31 017 avec l'acquéreur). Les 34 925 liens acquéreurs sont
  une **seconde copie** venue du miroir.

### ④ Les gestes — objets × gestes, pour la relation

| geste | où | ce qui reste DANS L'APP |
|---|---|---|
| rattacher un mandant existant | fiche annonce | provisoire ; **aucun** rafraîchissement du contact → le lien n'arrive qu'au run de nuit |
| créer un contact comme mandant | fiche annonce | provisoire ; **ni contact ni lien** avant Hektor *(≠ création par l'annuaire, qui naît dans l'app)* |
| modifier un mandant | carte mandant | le contact oui, le lien ne change pas |
| **retirer un mandant** | — | **LE GESTE N'EXISTE PAS** |
| mandant à la création d'annonce | assistant | **rien**, pas même un provisoire |
| propriétaire à la création d'un contact | annuaire | le contact oui, le lien non |
| acquéreurs d'une offre / compromis / vente | modale transaction | **durable dans `app_affaire_ledger`** à la création ; en modification, seul ce que Hektor relit |
| mandants d'une affaire (`mandantsVoulus`) | modale transaction | **rien de durable** |
| supprimer un contact / une annonce | fiches | le worker **efface** ses liens dans Supabase |
| lire — fiche contact | | registre, n° app ✅ *(bug ①)* |
| lire — fiche annonce | | `proprietaires_json`, n° Hektor ❌ |
| co-mandant / conjoint | | aucun geste |

⚠ **Les fonctions SQL des gestes mandant** (`app_link_mandant_optimistic`,
`app_create_mandant_contact_optimistic`, `app_update_mandant_contact_optimistic`) **ne sont
versionnées nulle part** dans `supabase/` — elles n'existent qu'en production.

### ⑤ Le contrat d'autorité : ce que les autres registres ont déjà

| | annonce | contact | transaction | mandat | **relation** |
|---|---|---|---|---|---|
| numéro frappé par une séquence | ✅ | ✅ | ✅ | ✅ | ❌ haché calculé en Python |
| l'app écrit la ligne durable au geste | ✅ | ✅ annuaire / ❌ mandant | ✅ | 🟡 D | ❌ |
| le run **adopte** ce que l'app a créé | ✅ | ✅ | ✅ | ✅ | ❌ |
| le run **ne supprime jamais** | ✅ | ✅ | ✅ | ✅ | ❌ DELETE + INSERT |
| saisie en attente protégée au push | ✅ | ✅ | ✅ | ✅ | ❌ |
| suppression ordonnée par l'app, journalisée | — | — | ✅ | — | ❌ |
| sentinelles | 4 | 4+ | ✅ | ✅ | **0** |

> ⚠ **MESURE DU 08/10 : CE TABLEAU EST PÉRIMÉ SUR DEUX LIGNES** *(vérifié dans le code et en base,
> chantier ⑤ point 5b)*. Depuis les 02-03/10, `app_link_mandant_optimistic` **écrit bien la ligne
> durable** au registre, et `relation_ledger.py` porte les trois règles des registres qui marchent :
> **deux distributeurs, deux plages** (le run prend `MAX(id) WHERE id < 1 000 000`, l'app sa séquence
> `app_relation_id_app_seq` — mesuré le 08/10 : run à 132 714, app à 1 000 009, elles ne se croisent
> pas) · **on ne renumérote jamais une ligne connue** · **DELETE-NEVER** (un lien que le miroir ne
> montre plus est MARQUÉ `present_in_hektor = 0` + `absent_depuis`, jamais supprimé : 4 marquées).
> Une ligne née dans l'app porte `present_in_hektor = false` et **le run ne la marque pas sortie**
> (le balayage ne vise que les lignes à 1) : Hektor ne contredit pas une saisie qu'il ne connaît pas
> encore. Et les **retraits décidés dans l'app** sont respectés (décision du 30/09, codée le 02/10).
> **Les 5 questions du point ⑦ restent ouvertes** : ce qui précède décrit ce qui EXISTE, pas une décision.

**La règle existe, écrite le 21/09** (journal) : *pas d'interrupteur, la règle est permanente
et symétrique ; l'arbitre est la RÉCENCE ; Hektor confirme, il n'écrase pas.* Codée pour
l'annonce (`app_annonce_reappliquer_saisies`), le contact (`push_contacts_to_supabase.py:451-504`)
et la transaction (`affaire_ledger.py:763-903`, « le silence ne gagne pas »). **Jamais pour la
relation**, faute de ligne durable à protéger.

### ⑥ La piste — le patron déjà appliqué trois fois *(à valider, PAS une décision)*

1. **Un numéro de lien FRAPPÉ** par une séquence, jamais calculé — la leçon que les
   transactions ont reçue le 03/09 en citant la relation (LISTE, registre des transactions, tâche 1.1 « LE LIEN ENTRE LES ÉTAPES »). **Clé d'adoption** :
   (identité du contact, `app_dossier_id`, famille de rôle). Le haché actuel reste en doublure
   le temps de la transition (le carnet C.9-d le permet).
2. **Deux robinets, une table** :
   - **l'app** — la RPC du geste écrit la ligne durable **tout de suite**, avec son numéro,
     comme `app_create_contact_optimistic` pour le contact ;
   - **le run** — il **adopte** par la clé métier, ne crée que l'inconnu, **ne supprime
     jamais** (`absent_depuis` / `present_in_hektor`), et laisse gagner une saisie app en
     attente.
3. **Le fait brut, pas le libellé** : « propriétaire du bien » est stocké, « mandant » se dérive.
4. **Les acquéreurs ne se recopient pas** : le registre les **projette** depuis
   `app_affaire_ledger`.
5. **Retirer devient un geste**, journalisé comme `app_affaire_supprimee`.
6. **Les deux fiches lisent la même table** ; `proprietaires_json` reste en secours derrière
   un interrupteur.
7. **Sentinelles** : lien app non adopté après N jours · lien disparu · œil serveur ↔ Supabase.
8. **Versionner** les fonctions SQL des gestes mandant.

### ⑦ Les 5 questions à Frédéric — AVANT toute ligne de code

1. Supabase porte-t-il **tous** les liens (167 547, archives comprises) ou seulement ceux des
   biens actifs, comme aujourd'hui (81 379) ?
2. Acquéreurs : **projection** depuis `app_affaire_ledger` (recommandé) ou copie ?
3. « Retirer un mandant » part-il chez Hektor tant qu'il vit ?
4. Les mandants choisis dans une affaire sont-ils des **liens au bien**, ou seulement des
   **parties de la transaction** ?
5. Ordre : les 5 défauts du point ⑧ d'abord, ou directement le registre ?

### ⑧ Les défauts trouvés en chemin — petits, indépendants du registre

- [ ] **R-1** fiche contact vide quand on l'ouvre depuis une annonce *(bug ①)*. Correctif :
      traduire le numéro reçu **avant** de charger liens et recherches — et corriger le test
      qui fige l'erreur.
- [ ] **R-2** `update_hektor_mandant_contact` rafraîchit le contact avec la **cible** au lieu
      de l'identité (`console_job_worker.js:17439`) — le défaut décrit par C-12 (l. 4138).
- [ ] **R-3** un lien en attente est **invisible** hors de `DossierDetailLayoutBase` : ni dans
      le cockpit (`App.tsx:28515`), ni sur mobile (`:33833`), ni sur un bien sans mandant (`:29862`).
- [ ] **R-4** `constaterLesPersonnes` range un n° Hektor dans
      `app_affaire_personne_ecart.contact_id` puis cherche le nom par identité : le bandeau peut
      afficher un numéro.
- [ ] **R-5** `link_hektor_mandant` et les mandants de création d'annonce ne rafraîchissent pas
      le contact : même confirmé, le lien attend la nuit.

### ⑨ Pourquoi le plan ne l'a pas vu — à retenir pour les prochains audits

- **03/09** : la conséquence est écrite (« meurt à la coupure »), la solution est donnée aux
  transactions… **pas à la relation**.
- **21/09** : **L2 marqué ✅ « relations »** alors que le livrable (`bc359b6`) est un
  **observateur**. La case `26bis-RELATIONS` de la liste est restée `[ ]` — la liste disait vrai,
  le résumé non.
- **24-25/09** : C.9-d / C.9-f règlent l'**identité** du lien, pas son **existence**.
- **28/09** : « seule vraie faiblesse » — notée, pas enchaînée.
- **Leçon** : un audit de bascule doit **essayer chaque CHEMIN D'ENTRÉE** vers un écran, pas
  seulement lire les fonctions ; et « cohérent par construction » est une **supposition**
  tant qu'aucun appel réel ne l'a montré.

*Non mesuré : le détail de `delete_hektor_compromis`, la partie Protexa de
`create_hektor_mandat_auto_number`, le chemin « passage en acquéreur » de la recherche
(`d7a3586`).*

---

## 🎯 MISE À JOUR DU 18/09/2026 — la liste ① relue contre le code

> **On reprend le plan, on ne le refait pas.** L'audit global du 18/09 (annonces-mandats,
> contacts-recherches, transactions, robustesse), fait **en lisant le code et la base**, a été
> rangé **dans les rubriques existantes** de la liste `① CE QUI RESTE À FAIRE` (1 à 12), sous
> leurs identifiants d'origine. La page de tête de la liste donne l'ordre avant **E.2**.
>
> Les nouveautés ont pris la place que le plan leur donnait déjà : **C.4** (archiver une
> recherche vise la mauvaise), **C.4-bis / C.1'** (la relecture efface une saisie en conflit),
> **C.19-d 3.5** (une suppression peut ressusciter), **C.17-ter** (ce que le moniteur ne voit
> pas), **D.0** (redescente des documents arrêtée depuis le 23/08), **E.0-bis** (mandat
> existant, photos, fusion de doublons — E.0 était incomplet), **A.2 / §5.2** (lancer une
> signature).
>
> **Corrections de nos propres documents :** sauvegarde à 08:15 (pas 07:00) · le calque de
> création optimiste est allumé depuis le 26/06 · quatre listes de champs app, pas une
> (contact 3 · annonce 0 · mandat 1 · transaction 0) · la modification d'une recherche fusionne
> les critères depuis le 30/08.

---

## 📋 LA LISTE À COCHER — `LISTE_TACHES_A_COCHER_2026-08-29.md`

> **Ce plan dit le POURQUOI. La liste dit le QUOI, item par item.**

Posée le 29/08 sur ce constat de Frédéric : *« je ne comprends pas pourquoi la liste des tâches
à exécuter n'est pas claire »*. La réponse était structurelle — **1 700 lignes, 0 case à cocher,
0 nom de worker** alors que C.4 en couvre seize. Une ligne de synthèse comme *« C.4 — les
workers, un par un »* ne permet pas de savoir qu'il en reste **onze**.

C'est la même racine que les deux dérives trouvées par l'audit : **C.1' et C.4 ont pu être
cochées parce que rien ne listait ce qu'elles contenaient.**

---

## ⚖ LA RÈGLE DU « FAIT » — posée le 29/08 après l'audit

> **Une tâche n'est cochée que si son ÉNONCÉ est couvert, et la mesure qui le prouve doit
> répondre à la question que la tâche posait.**

L'audit du 29/08 *(`AUDIT_PLAN_ET_REALITE_2026-08-29.md`)* a trouvé **deux tâches cochées sur
un périmètre plus étroit que leur énoncé** — C.1' et C.4. Aucune n'était un mensonge : chacune
avait produit du code qui tourne. Mais **la mesure produite ne répondait pas à la question
posée** :

| | la tâche demandait | la preuve apportée |
|---|---|---|
| **C.1'** | *« l'échec **se reprend** »* | la purge retirée sur **3 fonctions d'édition** |
| **C.4** | *« **écrire d'abord**, envoyer, comparer »* sur 16 workers | **127 archivages, 14 affectations** — des exécutions, pas des conversions · ✅ **CLOS le 01/09 : 14 convertis + 2 sans objet** |

**Ce n'est pas une faute de rigueur, c'est une faute de cadrage** : on mesure ce qui marche au
lieu de mesurer ce qui reste. La règle ci-dessus existe pour ça.

⚠ **Et elle vaut aussi pour l'auditeur.** Pendant cet audit même, **trois mesures fausses** ont
été produites avant d'obtenir la bonne — dont **deux fois le même chiffre**, par recherche de
motif dans le code au lieu de lecture des définitions. **Une mesure approximative vaut une
mesure fausse.**

---

## CE QUI A BOUGÉ LA NUIT DU 29 AU 30/08 — détecter, prouver, rattraper

*Trois points de l'audit menés à leur terme. **Chaque défaut ci-dessous a été trouvé en
éprouvant, aucun en relisant.** C'est le fait marquant de la nuit.*

### ① Les deux gestes qui n'avaient jamais tourné

`cancel_hektor_compromis` et `delete_hektor_vente` avaient **zéro travail à leur actif**. Le
premier passage a immédiatement révélé un défaut **dans le correctif lui-même** : la relecture
lisait le HTML de la fiche, où le bloc suivi-vente **n'est pas** — il est monté côté client.

```
   ?page=/mes-biens/mon-bien       208 274 car  ->  0 marqueur
   mode=chargeannonce_Accueil      217 397 car  ->  cloture:1 clore:1 supprimerVente:1
```

> **Dans le navigateur le bloc EST là, parce que le JavaScript l'a mis. Le worker ne voit que
> ce que le serveur envoie.** Aucun essai à la main ne pouvait révéler ce défaut.

Corrigé, rejoué : les deux gestes passent, effets confirmés *(fiche pour le compromis, API 404
pour la vente)*.

### ② Six contrôles fermés — trois ne vérifiaient rien, quatre s'ouvraient

| | avant | maintenant |
|---|---|---|
| `change_hektor_annonce_status` | relisait, **journalisait**, ne comparait jamais | compare le statut à la cible ✅ éprouvé |
| `assign_hektor_annonce_negotiator` | `confirmed_negotiator_id` valait **toujours `null`** | compare `keyData.NEGOCIATEUR` ✅ éprouvé |
| `archive` · `restore` | `if (after && …)` : relecture ratée = acquittement | exigent l'état ✅ éprouvés |
| `delete_hektor_annonce` | testait un drapeau ; journal « vérifiée » sans le savoir | prouve par l'**absence** ✅ éprouvé |
| `delete_hektor_contact` | partait **même quand `exists` valait `null`** | on ne supprime pas ce qu'on ne voit pas |

*`relance_signature` écarté par Frédéric — « pas vraiment vérifiable ».*

**La source qui a tout débloqué** : le worker n'a pas de JWT, mais le pont Python existait déjà
*(`annonce_datemaj_from_api.py`, écrit pour le garde-fou anti-écrasement)*. Deux scripts frères
posés : `annonce_etat_from_api.py` et `transaction_etat_from_api.py`. **Une requête, aucune
famille, pas de pagination** — là où le listing GraphQL ne voyait que `SALE` sur 2 pages.

### ③ La seconde relecture, demandée par Frédéric — trois durcissements de trop

*« vérifie que tu ne risques pas d'endommager tes workers […] il faut vérifier deux fois »*

| | |
|---|---|
| je durcissais **sur du non mesuré** | pour les statuts transactionnels, c'est **Hektor** qui décide : durcir aurait rejoué le piège de l'annonce 62962. Avertissement au lieu d'échec |
| la suppression **se prouvait toute seule** | « absente après » ne prouve rien si elle n'a jamais existé. On exige qu'elle ait existé **avant** |
| mon garde-fou **sautait le ménage local** | je sortais du handler en laissant nos lignes derrière |

### ④ C.4-bis — le filet de rejeu, enfin

**7 travaux en erreur, `attempt_count` à 1 partout, aucun jamais rejoué.** Le geste (c) de C.1',
coché en août sur les seules éditions de champs.

Il a d'abord fallu rendre les vérifications **absolues** : la mienne comparait un avant/après,
et rejouée sur un compromis déjà annulé elle aurait déclaré en échec un geste **réussi**, à
chaque tentative. *Le filet aurait fabriqué de faux échecs en série.*

```
   rejoue      9 gestes idempotents, attente 5/10/15/20 min
   exclut      les CREATIONS et les DEPOTS -- rejouer une creation la DOUBLE
   abandonne   a 5 tentatives, sans nouvel etat : attempt_count suffit
   ne rejoue   pas au-dela de 24 h -- un filet rattrape un incident, il ne
               ressuscite pas une decision oubliee
   montre      app_console_action_abandonnees, avec le motif
   tourne      app-action-retry-due, toutes les minutes (jobid 13)
```

**Éprouvé** : le filet a repris un travail bloqué depuis la veille et l'a mené à `done`.
Premier rejeu automatique du projet.

### Ce que la nuit enseigne, et qui vaut pour la suite du chantier

> **Éprouver trouve ce que relire ne trouve pas.** Sept défauts cette nuit : le verbe du
> compromis, quatre formulations de refus, la mauvaise source de relecture, le durcissement
> prématuré, la suppression qui se prouvait seule, le contact supprimé à l'aveugle, le filet
> qui aurait fabriqué de faux échecs. **Aucun n'est sorti d'une relecture** — tous d'un essai
> ou d'une question de Frédéric.

---

## 🔎 AUDIT DU 29/08 AU SOIR — les quatre choses qui bloquent

*Demandé par Frédéric : « dis-moi clairement où on en est ». Tout ce qui suit est **mesuré le
soir même**, pas recopié.*

```
   62 taches      37 faites      15 ouvertes      5 annulees      4 partielles
```

| mesure | valeur | ce que ça veut dire |
|---|---|---|
| travaux en erreur | **7**, tentatives max = **1** | **aucun n'a jamais été rejoué** |
| workers convertis | **5 sur 16** | 11 écrivent encore chez Hektor d'abord |
| `cancel_hektor_compromis` · `delete_hektor_vente` | **0 travail, jamais** | le code corrigé ce soir **n'a jamais tourné dans la chaîne** |
| commits non poussés | **53** *(origin/main au 28/08)* | **le front de C.19 n'est pas déployé** |

### ① Le code corrigé n'a jamais tourné — 1 h

Les deux handlers réparés n'ont **aucun travail à leur actif**. On les a éprouvés **à la main
dans le navigateur**, pas par le worker. Tant qu'un vrai travail n'a pas traversé la chaîne, on
ne sait pas si la relecture de fiche tient en conditions réelles.

### ② Rien n'est rejoué — 2 à 3 j

7 travaux en erreur depuis le 27/08, **zéro reprise**. Une saisie qui échoue est perdue en
silence. C'est **C.4-bis**, moitié d'une tâche cochée trop vite en août.

### ③ 53 commits ne sont pas poussés

Les boutons Refuser / Accepter / Annuler / Supprimer existent dans le code, **pas dans l'app**.

### ④ A.1 et A.2 sont à zéro

Portails et signature. **Aucun travail technique ne permet de couper Hektor** tant qu'ils ne
sont pas réglés, et chaque semaine de retard s'ajoute intégralement à la date de coupure.

### L'ordre retenu

```
   1. C.19        VRAI travail par le worker + front deploye        FAIT 31/08
   2. C.4-bis-0   relire les 18 handlers                            FAIT 01/09  18/20
   3. C.4         les workers + la branche « Vendu »                FAIT 01/09  16/16
   ------------------------------------------------------------------- ci-dessus : fait
   4. C.19-d      LE REGISTRE DES TRANSACTIONS                     <- EN COURS
   5. C.4-bis     le filet de rejeu des ACTIONS                     2 a 3 j
   6. C.19-c      le choix actif/archive remonte jusqu'a l'ecran    2 j (ou 1/2 j, voir note)
   7. C.16        825 contacts qui n'existent plus                  1 a 2 j
   8. LE BLOC DE LA DERNIERE CHANCE -- il exige que HEKTOR VIVE ENCORE   1 a 2 sem.
      26bis-3         le corps de l'annonce
      26bis-contacts  le corps du contact
      26bis-relations le NOM des relations
      C.9             la creation part de l'app
   9. A.3-tech    le registre des mandats en propre                 3 a 5 j
```

> **REVISION DU 03/09 -- DEUX CHANGEMENTS, ET ILS SONT ARGUMENTES.**
>
> **① C.19-d entre en poste 4.** Le protocole des statuts (01/09) a ferme sa
> question centrale en cinq mesures, et il a decouvert au passage que **le projet
> n'a JAMAIS su modifier une transaction chez Hektor** : aucun travail
> `update_hektor_*` pour offre / compromis / vente, et l'assistant est toujours
> ouvert sans `idCompromis`, donc il CREE. Preuve involontaire le 02/09 : le
> compromis 50060 a ete cree alors que 50059 existait.
> La route de modification est desormais connue -- `getStepCompromis` avec
> `idCompromis`, capturee en direct -- et `findProspect` est code. C.19-d est donc
> la suite naturelle de C.19 : l'app cree, change l'etat, et doit pouvoir CORRIGER.
> Il repousse C.4-bis d'un cran, et c'est assume.
>
> **② Le poste 8 est REGROUPE et NOMME.** Ses quatre taches partagent une seule
> contrainte, et c'est la plus dure du plan : *« le remplissage initial vient du
> miroir, donc il exige que Hektor vive encore »*. Elles ne peuvent pas etre
> remises apres la coupure -- elles deviendraient IMPOSSIBLES. C'est le seul bloc
> du plan qui a une date de peremption.
>
> ⚠ **26bis-relations n'avait jamais ete decrit.** Mesure du 03/09 :
> **165 870 relations** (74 045 mandants, 58 375 proprietaires, 33 450 acquereurs).
> Leur cle est un hache STABLE -- elle exclut deliberement l'etat, le montant et la
> date, et c'est documente depuis le 19/06 (*« maj en place, pas d'orphelin »*,
> 0 relation orpheline mesuree le 08/08). **Le probleme n'est donc PAS la
> stabilite** : c'est que cette cle est batie sur `contact_id` et `annonce_id` --
> **les numeros de HEKTOR**. Le jour ou l'app cree une fiche qu'il ignore (C.9),
> la formule ne peut plus fabriquer de nom, et le lien n'a nulle part ou vivre.
> `26bis-relations` n'est donc pas une reparation : c'est le TROISIEME PIED de C.9,
> au meme titre que le corps de l'annonce et celui du contact.
>
> ⚠ Et le detour par l'app est ferme : la cle est calculee EN PYTHON par le run.
> La recopier cote app est explicitement refuse par le projet -- *« deux copies
> d'une formule divergent tot ou tard, et ce jour-la le lien se dedouble en
> silence »* (console_job_worker.js). D'ou le patron actuel du mandant : une ligne
> PROVISOIRE pivotee sur un jeton, que la descente remplace. **Ce patron meurt a la
> coupure** : la provisoire attendrait une confirmation qui ne viendrait jamais.

> **③ C.19-d EST REQUALIFIE — ajout du 03/09 au soir, apres l'audit complet.**
> Frederic : *« refaire un audit precis du code actuel et de l'ensemble du projet
> pour ne rien oublier »*. Checklist des 5 points appliquee, 12 notes supprimees
> relues dans git, deux essais reels sur 24933. **Le detail item par item est dans
> la liste, section « 2 ter ».** Ici, le POURQUOI.
>
> **Le poste ne s'appelle plus « modifier une transaction » mais « LE REGISTRE DES
> TRANSACTIONS ».** La modification n'en est qu'une piece : ce qui se joue, c'est
> de faire d'`app_affaire_ledger` un registre a part entiere, au meme titre que
> l'annonce et le contact.
>
> ⚠ **ET IL FAUT CORRIGER UNE TRAJECTOIRE AVANT QU'ELLE NE PORTE DES DONNEES.**
> `CHAMPS_APP_AFFAIRE` declare **10 champs comme appartenant a l'app** -- et ce
> sont **tous des champs que Hektor connait**. C'etait juste le 29/08 : l'app ne
> savait pas pousser une correction, proteger etait la seule facon de ne pas
> perdre la saisie. Mais un champ protege que Hektor connait, c'est exactement
> l'ecueil que ce plan enonce pour les ANNONCES -- *« tant qu'ils saisissent dans
> Hektor, inscrire un champ ici le FIGERAIT sur une valeur perimee »*. **Frederic
> l'a repere avant moi** (*« il faut prevoir que le run nous retourne certaines
> donnees a mettre a jour »*), et il a eu raison de refuser les deux rustines que
> je proposais ensuite (empreinte de contenu, date de maj maison).
>
> **La bonne reponse etait deja dans le projet, en trois mecanismes que j'avais
> confondus :** la DOUBLURE protege le NUMERO ; le CONTRAT D'AUTORITE protege la
> VALEUR, et **uniquement pour les champs que Hektor IGNORE** ; le PENDING +
> GARDE-FOU protege l'ECRITURE, pour tout ce que Hektor connait. C'est ce
> troisieme mecanisme -- deja en production sur l'annonce et le contact -- que les
> transactions doivent adopter.
>
> > **On ne protege pas la donnee, on protege l'ECRITURE.** Ce que l'app a saisi
> > n'est pas une valeur qu'elle possede : c'est une ecriture EN ATTENTE, qui
> > verifie avant de partir et qui reste en attente tant qu'elle n'est pas partie.
>
> ⚠ **Une piste NON TECHNIQUE, a trancher par Frederic.** Volume mesure le 03/09 :
> **116 transactions sur 30 jours** (89 offres, 18 compromis, 9 ventes), soit 4 a 5
> gestes par jour pour toute l'agence. A ce volume, decider que *« une transaction
> se saisit dans l'app »* rend le garde-fou rare et sans enjeu, au lieu d'en faire
> une piece critique. C'est la doctrine du plan appliquee aux transactions.
>
> **Le chantier est desormais en 5 phases, dont la premiere ne code rien** :
> mesurer ce que Hektor accepte / refuse / ignore, champ par champ. Ce classement
> commande la forme de tout le reste -- si Hektor refuse presque tout, la phase 3
> se reduit et la phase 2 (l'ecran) devient l'essentiel. **STOP et relecture avec
> Frederic apres la phase 0.**

> **REVISION DU 01/09.** Les trois premiers postes sont clos, et deux d'entre eux
> l'etaient DEJA sans que ce plan le sache -- voir la revision de C.4 et de
> C.4-bis-0 plus bas. **C.4-bis devient le prochain**, et il est desormais
> debloque : la detection est bonne sur 18 gestes sur 20.
>
> ⚠ **C.19-c est peut-etre une demi-journee, pas deux.** Frederic, 30/08 : *« on
> devrait laisser que le choix, pas proposer le choix dans l'app puisqu'il est
> automatiquement sur actif »*. RETIRER le choix au lieu de l'exposer -- point
> jamais tranche.

> **Pourquoi cet ordre.** On vient de découvrir qu'un worker peut se tromper de verbe pendant
> des jours sans que personne le sache. Détecter, prouver, rattraper — tant que les trois ne
> sont pas en place, chaque nouveau worker ajoute une panne possible et **muette**.

---

## CE QUI A BOUGÉ LE 29/08 — l'essai réel sur Hektor

*Une journée qui a commencé par un doute de Frédéric — « je ne suis pas sûr qu'Hektor, même en
cas de succès, nous envoie autre chose » — et qui a fini par trouver **un verbe faux et quatre
formulations de refus non reconnues**. Aucune n'aurait été vue en relisant le code.*

| | |
|---|---|
| 🔴 **trouvé** | le worker appelait **le chargeur de formulaire** au lieu de l'action pour annuler un compromis. Le geste n'aurait **jamais rien annulé** |
| 🔴 **trouvé** | **trois formulations de refus** échappaient au détecteur — et elles sont **non vides**, donc comptées comme des **succès** |
| 🔴 **trouvé** | la réponse de `ventes-deleteVente` est **vide au succès comme à l'échec**. La règle uniforme posée la veille aurait rejeté **chaque suppression réussie** |
| ✅ **corrigé** | verbe, vocabulaire du refus, et **un arbitre par geste** *(la réponse pour l'offre, la relecture de la fiche pour le compromis et la vente)* — `779e2bf`, `dd02299` |
| 📖 **consigné** | **les codes relevés et les interactions avec le statut** → section *« LES GESTES DE TRANSACTION CHEZ HEKTOR »* plus bas dans ce plan |
| 🆕 **C.19-c** | le choix **« laisser actif » / « archiver »** à l'enregistrement d'une vente agit sur le statut de l'annonce : **décision métier, à remonter jusqu'à l'écran** |
| ⏳ **reste** | éprouver la suppression d'une vente posée sur un compromis **actif**, et la branche « archiver » — *demande une session administrateur* |

> **La règle de méthode qui en sort, et elle vaut pour tout le reste du chantier :**
> **lire le code ne remplace pas regarder passer l'appel.** Le nom du mauvais verbe figurait
> bien dans le JavaScript de Hektor — il n'est simplement pas celui qui part.

---

## CE QUI A BOUGÉ LES 27-28/08

*Cinq changements. Trois chantiers avancent, deux défauts inconnus ont été trouvés — et
aucun des deux n'a été cherché : ils sont sortis d'une vérification.*

| | |
|---|---|
| ✅ **C.15 — TERMINÉ** | les six types d'offre entrent *(miroir 61 091, serveur 61 092)* · l'immobilier professionnel est **lisible ET créable** · prouvé de bout en bout sur l'annonce 62964 |
| ✅ **C.17-bis** | le moniteur ne meurt plus à l'instant où il a quelque chose à dire |
| ✅ **C.13-a et C.13-b** | le mandat obtient son domicile, et le contrat d'autorité s'allume — **premier champ jamais inscrit** |
| 🔴 **trouvé** | une annonce créée pour un négociateur multi-agences partait dans **la mauvaise agence** — 3 fois depuis juin, corrigé |
| 🔴 **mesuré** | **23 715 mandats devraient porter une date de clôture. 94 la portent.** |
| 🏛 **ouvert** | **le registre des mandats n'est pas un registre, c'est une vue des annonces** — 1 105 mandats invisibles, dont 642 *parce qu'ils sont clos*. Nouveau chantier **A.3-technique**, 3 à 5 j, **à faire tant que Hektor vit** |
| 🗺 **26bis simplifiée** | **la vue est `FROM app_dossier`, sans `WHERE`** — une annonce app a besoin de **10 colonnes écrites une fois**, pas de 163 réécrites chaque nuit. Reste à trancher **46 colonnes**, dont **37 dans un seul blob**. Carte : `CARTE_ANNONCE_NEE_DANS_APP_2026-08-28.md` |
| ✅ **C.13 finie** | **la clôture de mandat a enfin un domicile durable** — elle écrivait dans une table vidée chaque nuit, sur une ligne qui n'existait pas, **et annonçait un succès**. Corrigée et éprouvée de bout en bout *(`ce57749`)*. ➡ **C.4 est débloquée** |
| ✅ **remesuré** | **C.16 était très surestimée** — pas 284 269 contacts, mais **825 fiches actives** qui n'existent plus chez Hektor *(sonde avec témoin : 0/12 contre 12/12)*. **1 à 2 j** au lieu de « à chiffrer » |

#### ⚠ LE CHIFFRE QUI CHANGE LA LECTURE DE C.13

```
   mandats du parc                                    24 939
   portant une date de cloture                            94    0,38 %
   devant en porter une (annonce Vendue ou Close)     23 715
   annonces etiquetees « Mandat clos », avec mandat       642
             dont le mandat est vraiment clos               0
```

**Vendre un bien ne clôt jamais son mandat** : sur 6 719 annonces vendues portant un
mandat, **deux** ont une date de clôture. Et le registre affiche pourtant « Clos »,
parce qu'il se rabat sur le statut de l'annonce quand la date manque — ce qui arrive
99,6 % du temps.

> **C.13 n'est donc pas la réparation d'un défaut : c'est un geste qui n'a jamais été
> outillé.** Les correctifs ne réparent aucune régression, ils rendent exécutable
> quelque chose qui, à l'échelle du parc, n'a pratiquement jamais eu lieu.

#### 🔑 LE VIRAGE DÉCIDÉ PAR FRÉDÉRIC LE 28/08

> *« On peut créer le système de clôture du mandat uniquement dans l'environnement
> serveur + app, sans tenir Hektor informé de la clôture — puisque s'il est informé du
> changement de statut, cela suffit. »*

Et c'est vérifié : **le changement de statut suffit déjà à obtenir l'effet métier chez
Hektor** — statut 6 coupe la diffusion, statut 5 enregistre la vente. La clôture du
mandat n'ajoute rien de son côté ; c'est une écriture dans **son** registre à lui.

Ce que ça retire du plan :

| | |
|---|---|
| ❌ | le correctif du 500 sur la famille PROTEXA *(cause jamais élucidée)* |
| ❌ | le suivi du formulaire de clôture de Hektor, qui peut changer sans préavis |
| ❌ | six appels HTTP et une opération **irréversible chez un tiers** à chaque clôture |

Ce que ça coûte, et c'est le seul arbitrage : **tant que Hektor vit, les deux registres
diront des choses différentes sur ce point.** Le tien dira clos, le sien dira ouvert.

---

## CE QUI EST FAIT

| | | Commit |
|---|---|---|
| Un dossier ne perd jamais son numéro | on marque `absent_depuis`, on ne supprime plus | `dc45c62` |
| Le correctif anti-fantôme couvre 21 tables au lieu de 5 | ~600 annonces abîmées depuis juin | `aa8a374` |
| **Les identifiants d'annonce sont alignés** | 13 215 / 13 215, vérifié après un run complet | `99e262f` |
| Pipeline et surveillance fiabilisés | chauffage non bloquant, sauvegarde surveillée, 4 sentinelles en critique | 5 commits |

---

## ⛔ AVANT DE COMMENCER UN CHANTIER — à relire, sans exception

**Cette liste existe parce que le 20/08 j'ai oublié trois fois un point déjà documenté.**
Un plan ne protège de rien s'il n'est pas relu avant chaque geste.

| | À relire | Pourquoi |
|---|---|---|
| **1** | **Ce document en entier** — pas seulement la tâche visée | les pièges sont dans les sections voisines |
| **2** | Les **notes citées** par le chantier concerné | elles contiennent les décisions déjà prises |
| **3** | `ls notice/*.md` **et la racine**, par mot-clé | ~158 notes ; celles qui comptent ne sont pas toujours dans `notice/` |
| **4** | **L'historique git** : `git log --all --diff-filter=D -- 'notice/*'` | 12 notes supprimées le 19/08 portent encore de la doctrine active |
| **5** | La **mémoire projet** de l'assistant | la réponse y était déjà, deux fois, le 20/08 |

**Trois questions à se poser avant d'affirmer qu'une chose est cassée :**

1. **Est-ce documenté ?** Dans ce projet, ce qui ressemble à une négligence est presque toujours
   une décision écrite quelque part.
2. **Est-ce mesuré ?** Une détection `ILIKE` mal écrite m'a fait affirmer l'inverse de la vérité
   sur `app_edit_search_optimistic`. **Mesurer, puis conclure.**
3. **Qu'est-ce que j'oublie ?** Lister les cas voisins : si on traite « la recherche modifiée »,
   a-t-on traité « la recherche supprimée » ? Si on traite les annonces, et les contacts ?
   les affaires ? les recherches ?

---

## LES TÂCHES, DANS L'ORDRE

*Ordre **validé par Frédéric le 21/08/2026**, après l'audit de la data locale
(`notice/AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md`). Il remplace la liste plate précédente.*

### ⛔ LA MÉTHODE — arrêtée le 21/08, sans exception

Avant **chaque étape** et **avant tout code**, quatre phrases :

```
   ce que ca fait  ·  ce que ca touche  ·  comment on revient en arriere  ·  comment on verifie
```

Frédéric valide, **puis** on code. Jamais l'inverse. *« Je ne veux pas d'ambiguïté. »*

### 📚 LES NOTES QUI FONT AUTORITÉ — rattachées le 24/08

*L'audit du 24/08 a trouvé que **19 des 21 notes les plus récentes n'étaient citées nulle part
dans ce plan**. C'est ce qui m'a fait réinventer, cinq jours plus tard, un travail déjà fait.
Ce qui suit répare la cause, pas le symptôme.*

| Note | Ce qu'elle tranche | Lue par |
|---|---|---|
| `METHODE_DE_TRAVAIL_2026-08-20` | **le contrat de travail** : lire, mesurer, expliquer, faire valider, prouver | **avant chaque tâche** |
| `A1_CHAMPS_PROPRIETE_APP_2026-08-19` | **189 champs** que l'app possède · la règle « l'import n'a pas le droit de réécrire » · le mécanisme « c'est une soustraction » · **3 arbitrages en attente** | **C.4** |
| `ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20` | les 4 familles · **16 workers** sont le gisement réel · **7 sur 34 marchent déjà sans Hektor** · **3 seulement** dépendent vraiment de lui | **C.4** |
| `PLAN_DEV_MANDAT_CLOTURE.md` | **cadrage validé le 30/07, dev non commencé** · les déclencheurs · les motifs Hektor · la clôture cible par **ID interne** · « échu ≠ clos » | **C.13** · 🔴 **REQUALIFIÉ LE 27/08 : CE N'EST PAS DORMANT.** Le plan disait « drapeau `VITE_APP_MANDAT_CLOTURE_ENABLED` éteint » — **ce drapeau n'existe nulle part dans le code**, seulement dans les notes. Le chemin est **vivant et non protégé** : `App.tsx:14576` envoie `closeMandatOnSale: statusChangeStatus === 'sold'` à **chaque** passage en Vendu, et le worker enchaîne `submitHektorTransactionStatus()` **puis** `closeHektorMandatAfterSale()` dans un `try…finally` **sans `catch`**. Donc au premier « Vendu » depuis l'app : **la vente part chez Hektor**, la clôture échoue *(91 % des annonces actives ont un mandat unique)*, l'exception fait tomber le travail, la resynchronisation ne tourne jamais — **Hektor a la vente, l'app l'ignore**. ✅ **Le seul point rassurant** : le payload du front porte `numero_mandat` mais **pas** `id_mandat`, donc c'est la branche qui **REFUSE** qui joue, jamais celle qui fabrique une cible — **aucune clôture abusive n'est possible** sur une opération irréversible. ⏳ **Jamais déclenché à ce jour** : c'est ce qui explique « 0 mandat clos en base » |
| `ETUDE_OU_EN_SOMMES_NOUS_2026-08-25` | **E.0** · les deux circuits chronométrés · ce que l'app sait déjà écrire dans Hektor · les 4 manques | **E.0, C.4** |
| `NOTE_CHAINE_DES_MANDATS_2026-08-25` | la chaîne des mandats de bout en bout · `mandat_source_id` **est** `hektor_mandat_id` · pourquoi le registre se défie de `hektor_mandat` · **342 identifiants partagés entre annonces** → toujours interroger par le **couple** | **C.4, C.5** |
| `AUDIT_IDENTITE_CONTACTS_2026-08-20` | l'état des lieux du 20/08 · **son verrou est levé**, voir la relecture ci-dessous | **C.2** |
| `RELECTURE_IDENTITE_CONTACTS_2026-08-24` | **C.2a, fait** · 4 tables portent 95 % · 3 fonctions à basculer, pas 11 · `hektor_contact_id` **est la clé primaire** | **C.2b, C.9** |
| `AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21` | le sens unique · le régime de chaque table · les 3 trous | **B, C.6, C.7** |
| `AUDIT_ET_PLAN_REALISTE_2026-08-22` | l'état mesuré des 5 supports · les durées | **le calendrier** |
| `AUDIT_SESSION_ET_PLAN_2026-08-24` | cet audit · la duplication · l'ordre corrigé | |
| `ETUDE_HISTORIQUE_RECHERCHES_ACQUEREUR_2026-08-21` | pourquoi les recherches sont autonomes depuis le 19/06 | **C.3** |
| `ETUDE_ORIGINE_CLE_RECHERCHE_2026-08-21` | un seul fabricant de nom · la doublure | *fait* |
| `VISION_GLOBALE_DEV_INDEPENDANCE_2026-08-18` | la vision d'ensemble | |
| `NOTE_PLAN_SAUVEGARDE_2026-08-18` | les 4 niveaux · pourquoi le niveau 3 est désactivé | **0.1, D** |

> **Règle** : une tâche qui cite une note **la lit avant de commencer**. Une note qui n'est
> citée nulle part est une note perdue.

---

### 🛤 LES TROIS PISTES — posées par Frédéric le 24/08 au soir

*Ce qui suit **affine** la section des trois étapes ci-dessous. Les étapes racontaient l'histoire ;
elles laissaient croire que le code attendait une décision d'organisation. **C'est faux.** Trois
choses avancent indépendamment, et il ne faut jamais les confondre :*

```
   PISTE 1 -- LE CODE EST PRET       C.2b C.12 C.6 C.5 C.7 C.8 C.9 C.4 C.11
                                     puis E.0 : que ne sait pas faire l'app ?
                                     -> se construit MAINTENANT, dormant
                                     -> ne depend de PERSONNE

   PISTE 2 -- LES GENS BOUGENT       quand ils veulent, un par un
                                     jamais les deux systemes pour LA MEME personne
                                     -> depend de Frederic seul

   PISTE 3 -- ON COUPE LES WORKERS   quand A.1 / A.2 / A.3 sont faits
                                     -> depend de contrats exterieurs
```

#### Ce que ça change, concrètement

**On construit tout, dormant, et le jour J n'est plus qu'un paramétrage.** C'est le patron déjà
utilisé quatre fois ici — `VITE_APP_COCKPIT_V2_ENABLED`, `VITE_APP_CONTACT_V2_ENABLED`,
`VITE_APP_MANDAT_V3_ENABLED`, `APP_BROUILLON_BUCKET_ENABLED` — et c'est la méthode de la
doublure, qui a marché trois fois : `app_dossier`, `app_affaire_ledger`, `app_search_registry`.

> ⚠ **La condition, mesurée le 24/08** : ces quatre drapeaux ont été posés les 17/07, 23/07,
> 26/07 et 22/06 — **aucun n'a jamais été allumé en production**. 29 à 38 jours de sommeil.
> **Construire dormant est facile ; c'est l'allumage qui ne se fait pas.**
>
> Et le journal des doublures dit `app seule = 45`, **plat trois jours sur trois** — parce que
> personne n'utilise l'app. **Tout ce qu'on sait de « l'app comme auteur » est mesuré sur une app
> que personne n'exerce.** L'antidote est de Frédéric : **il passe sur l'app pendant qu'eux restent
> dans Hektor**. Ça rend les mesures vraies, et ça éprouve C.1' avec son seul travail en jeu.

#### Le modèle, dans les mots de Frédéric — et ce qui existe en face

```
        L'APP ecrit
             |
             +--> Supabase --(la DESCENTE)--> LE SERVEUR      [FAIT le 22/08, B.1]
             |
             +--> worker --------------------> HEKTOR

        HEKTOR --(import de nuit)--> LE MIROIR --> LE SERVEUR  [depuis toujours]
```

> *« Le miroir de Hektor devient une **source d'information** ».* C'est le nom exact de **C.7**.
> Aujourd'hui le miroir n'est pas *une* source, il est **la** source — le serveur se reconstruit
> depuis lui chaque nuit. C.7 le fait passer de **vérité** à **témoignage**.

**Les deux sortes d'écart ont déjà chacune leur instrument :**

| L'écart | Ce que c'est | L'instrument | Depuis |
|---|---|---|---|
| **conflit de worker** | l'envoi vers Hektor a été bloqué ou a échoué | `app_*_pending.conflict` · 8 sondes · bandeau + boutons | **24/08** *(C.1')* |
| **conflit de miroir** | le miroir dit autre chose que ce que l'app détient | les 10 doublures + le journal de 07:30 | **22/08** *(B.2/B.4)* |

> **Mais détecter n'est pas résoudre.** Les doublures voient l'écart, elles ne le tranchent pas —
> et chaque nuit le serveur se reconstruit depuis le miroir, donc **Hektor regagne par défaut**.
> Pas parce qu'on l'a décidé : **parce qu'il est seul dans la pièce**. C.7 est l'endroit où
> l'écart se résout ; C.6 fournit le *quoi* à réconcilier.

#### La réserve sur « pas les deux en même temps »

Ça se lit **par personne**, pas par système. Si l'un passe sur l'app pendant que l'autre reste
dans Hektor, **les deux systèmes sont vivants** à l'échelle de l'agence. Ce qui rend ça tenable,
c'est que les dossiers sont en **portefeuilles** *(mesuré le 24/08 : Sylvie 2 181 · Marion 1 878 ·
Groupe GTI 1 702 · Nicolas 1 522 · Christèle 1 330 · Arnaud 1 122…)*.

Le risque ne porte donc pas sur le volume : il porte sur les **dossiers partagés** — un acquéreur
suivi par deux négociateurs, un mandat en co-listing. **C'est exactement ce que le journal des
doublures verra chaque matin.**

---

### 🗝 LES TROIS ÉTAPES — posées par Frédéric le 24/08

*Ce n'est pas un détail d'organisation : **c'est ce qui décide de la moitié du travail
technique**. Le plan précédent supposait que l'app et Hektor seraient utilisés en même temps.
Ils ne le seront pas.*

```
   ETAPE 1  (aujourd'hui)   tout se fait dans HEKTOR
                            les negociateurs n'ont pas acces a l'app, sauf Frederic

   ETAPE 2                  les negociateurs utilisent L'APP
                            et il leur est INTERDIT d'ouvrir Hektor en meme temps

   ETAPE 3                  la coupure
```

#### Ce que l'étape 2 supprime

Il y a **trois** façons pour l'app et Hektor de diverger :

| | | À l'étape 2 |
|---|---|---|
| **①** | l'envoi n'est jamais parti | **reste** |
| **②** | l'envoi a raté *(Hektor injoignable, session morte, refus)* | **reste** |
| **③** | quelqu'un a modifié dans Hektor entre-temps | **disparaît** |

**Le cas ③ disparaît, et avec lui tout l'arbitrage** — la règle de priorité, la tolérance de
comparaison, la notification de conflit. C'était la moitié de l'ancienne tâche C.1.

Mieux : si personne ne touche à Hektor, le run de nuit ne rapporte plus *les modifications de
quelqu'un d'autre*. Il rapporte **ce que l'app vient d'y écrire**. Le va-et-vient devient une
**confirmation**, plus une compétition.

#### Ce qu'elle ne supprime PAS — et c'est le vrai danger

```
   l'envoi echoue  ->  la protection tombe  ->  le run de nuit ECRASE la saisie
```

**Démontré sur le contact 602197, le 24/08.** Un négociateur affine une recherche à 120 000 €.
L'envoi est bloqué. Le travail est marqué `done`. La ligne de protection disparaît. Le run
suivant rapporte la valeur de Hektor. **Les trois supports disent aujourd'hui `prix_min = 0` —
la saisie n'existe nulle part.** Et personne n'a rien modifié dans Hektor.

> ⚠ **La doublure ne protège pas de ça.** Elle copie ce que Supabase contient. Si Supabase est
> écrasé, elle copie l'écrasement. Elle donne au serveur une **copie fidèle**, pas une
> **mémoire**.

#### Les trois garde-fous d'aujourd'hui ne se ressemblent pas

*Relevé dans `console_job_worker.js` le 24/08 — ils ont été écrits à des moments différents.*

| | **Recherche** | **Contact** | **Annonce** |
|---|---|---|---|
| Compare | **le contenu** *(empreinte villes/types/critères)* | une **date** | une **date** |
| Relit avant | **oui**, read-through complet | non | non |
| Si la relecture échoue | **bloque** | **écrit quand même** | **écrit quand même** |
| Prévient le négociateur | **oui** | **oui** | **non** |
| Sans photo | aucun garde-fou | aucun garde-fou | aucun garde-fou |
| Après blocage | `done` · **jamais repris** | `done` · **jamais repris** | `done` · **jamais repris** |

**Les trois savent détecter. Aucun ne sait retenir.** C'est le seul défaut qui compte, et c'est
le seul que l'étape 2 ne corrige pas.

*(Le « best-effort » du contact et de l'annonce mérite d'être nommé : ligne 11421,
« si la relecture API échoue, on écrit ». Le moment où l'on est le moins sûr est celui où l'on
protège le moins.)*

---

### 📍 LE TABLEAU DE BORD — posé le 22/08 après l'audit

*Le plan disait QUOI faire, jamais COMBIEN DE TEMPS ni QUI BLOQUE QUI.*

#### Le chemin critique — et il n'est pas technique

```
   A.1 PORTAILS  +  A.2 SIGNATURE   ------------------------->  LA COUPURE
   semaines a mois, ne depend pas de moi, A ZERO

   PISTE 1, le code       -- ORDRE REVU LE 29/08, APRES AUDIT --

     FAITS   C.2b C.6 C.7 C.12 C.13 C.14 C.15 C.17 C.17bis C.18 C.19

       1.  C.4        finir : la branche Vendu (jamais executee)
                      PUIS convertir les 11 workers restants (5/16 seulement)
       2.  C.4-bis-0  VERIFIER LA DETECTION, worker par worker
                      (prealable : on ne rejoue pas ce qu'on ne sait pas rate)
       3.  C.4-bis    le filet de rejeu des ACTIONS -- geste (c) de C.1'
       3.  C.16       825 contacts actifs qui n'existent plus chez Hektor
       4.  C.9        la creation part de l'app        } collees
       5.  26bis-(3)  le serveur tient une annonce app } l'une a l'autre
       6.  C.11       menage des tables mortes
       7.  A.3-tech   le registre des mandats en propre (tant que Hektor vit)
       8.  D.1a D.1 D.2   rapatrier documents et photos
       9.  C.13-c     rattraper les dates de cloture   } fin de plan,
      10.  A.1 A.2 A.3     portails, signature, registre } avec les 3 arbitrages

     POURQUOI CET ORDRE. C.4 d'abord parce que ses 11 workers non convertis sont la
     plus grosse dette mesuree, et que la branche Vendu est enfin debloquee. C.4-bis
     juste apres, parce qu'un filet posé sur des workers convertis vaut mieux qu'un
     filet pose deux fois. C.16 ensuite : 1 a 2 jours, et 825 fiches mentent
     aujourd'hui. C.9 apres, car elle depend du contrat d'autorite (C.7, fait).
                          (C.5 ANNULEE le 25/08 au soir : retour arriere)
                          -> C.11 -> E.0 [FAIT le 25/08]
                                                     4 a 6 semaines
                          SE CONSTRUIT MAINTENANT, dormant. N'attend personne.

   PISTE 2, les gens      quand ils veulent, un par un.   Frederic seul.
   PISTE 3, la coupure    quand A.1/A.2/A.3 sont faits.   A ZERO.

   Fait a ce jour : 0.1 0.2 0.4 0.5 0.6 0.7 0.8 | B.1 B.2 B.4 B.5
                    C.1' C.2a C.2b C.3 C.6 C.7 C.12
                    C.14 C.15 C.17 C.17bis C.13-a C.13-b   [27-28/08]
```

> **Aucun travail technique ne permet de couper Hektor tant que A.1 et A.2 ne sont pas faits.**
> Tes annonces passent par **son** abonnement portails, tes mandats se signent avec **son**
> contrat. Chaque semaine de retard sur A s'ajoute **intégralement** à la date de coupure.

> **Corrigé le 24/08** : la colonne « sans Hektor » était une contrainte de la panne du 22,
> pas une règle. Hektor répond en 0,23 s. Ce qui commande désormais l'ordre, c'est **avant** ou
> **pendant** l'étape 2 — voir la section des trois étapes.

#### Ce qui peut avancer SANS Hektor *(section de la panne du 22/08, conservée pour mémoire)*

| | Tâche | Durée |
|---|---|---|
| **0.4 → 0.7** | Les quatre gestes de sécurité du bloc 0 | **1 h** |
| **D.1a** | Mesurer le vrai périmètre du rapatriement des documents | **1 h** |
| ✅ **C.2a** | Identité des contacts — la relecture | **FAIT le 24/08** |
| **C.6** | La table « ce que l'app détient » pour l'annonce | **1 à 2 jours** |

#### Ce qui exige Hektor vivant

| | Tâche | Durée | Sur quoi repose l'estimation |
|---|---|---|---|
| **C.1** | La règle de comparaison | **3 à 5 j** | le garde-fou existe ; c'est le verdict qu'on inverse |
| **C.3** | L'exception recherches | **1 à 2 j** | la doublure existe déjà |
| **C.2b** | Identité des contacts — le code | **3 à 5 j** *(revu par C.2a)* | 4 tables, 3 fonctions. **Sans le changement de clé primaire**, qui est un second chantier |
| **C.4** | Les workers, un par un | **2 à 3 sem.** | 35 types de travaux |
| **C.7** | Le serveur lit sa base | **2 à 3 j** | collée à C.1 |
| **C.9** | La création part de l'app | **1 à 2 sem.** | après C.7 |

> ⚠ **Ces durées sont des FOURCHETTES, et c'est volontaire.** Trois fois cette semaine j'ai
> donné un chiffre précis là où la donnée ne portait qu'un ordre de grandeur — « ~270
> recherches invisibles » *(réalité : environ 5)*, « 20 000 rapprochements disparus »
> *(réalité : zéro — j'avais comparé une estimation à un comptage)*, « ~2,7 Go » *(réalité :
> 4,32)*. **Un chiffre qui entre dans une décision se mesure, il ne s'estime pas.**

#### Une dette signalée, pas mise au plan

`App.tsx` fait **37 204 lignes** — les trois quarts du front dans un seul fichier. Ça marche,
et le découper serait un chantier sans valeur métier. Mais **C.9 va beaucoup y toucher**, et
c'est le genre de dette qui se paie au pire moment. À savoir, pas à traiter maintenant.

---

### LE BUT, redit par Frédéric le 21/08

> *« Je veux que mon app et mon serveur fonctionnent comme une vraie solution métier, sauf que
> dans un premier temps les données rafraîchies proviennent d'une API avec Hektor, et que chaque
> modification doit lui être envoyée pour qu'il reste à jour — mandat, pub, etc. »*

C'est le chantier 3, mot pour mot : **écrire chez soi d'abord, envoyer ensuite, confirmer au
retour.** Deux précisions à ne jamais perdre de vue :

- **Les recherches sont la seule exception** — décision de Frédéric du 20/08 : elles ne remontent
  plus à Hektor, parce que la modale n'exprime que 7 critères sur 12 et que les renvoyer les
  appauvrit. *Décision prise, geste pas encore fait.*
- **On lit par une API, on n'écrit PAS par une API.** L'écriture passe par un robot qui remplit le
  formulaire web avec les cookies d'un négociateur. C'est la vraie fragilité de « Hektor reste à
  jour », et elle disparaîtra avec Hektor — elle ne se corrigera pas.

---

### ✅ CE QUI EST FAIT

| | Tâche | |
|---|---|---|
| ✅ | Avertissement d'échec des workers | `48e475a` |
| ✅ **1** | ~~**Rattacher l'irremplaçable**~~ — 15 lignes déplacées, 0 perdue — propositions, relances, retours acquéreur, envois | 15 lignes, **0 ambiguïté** |
| **1bis** | *(cas des recherches SUPPRIMÉES chez Hektor : 31 clés, 681 rapprochements — **rien d'irremplaçable dessous**)* | traité par la tâche 2 |
| ✅ **2** | ~~**Supprimer le recalculable**~~ — 13 339 lignes — 1 373 rapprochements + 11 966 lignes d'historique | après le 1 |
| ✅ **2bis** | ~~**Poser le balayage nocturne**~~ — `app_sweep_search_orphans`, 07:00 | sinon la fuite reprend dès le lendemain |
| ✅ **2ter** | ~~**Sentinelle**~~ sur les orphelins NON rattachables | attendu 0 |
| ✅ **2quater** | ~~**Le balayage tient un carnet**~~ — `app_sweep_search_orphans_log` | une réparation qui ne dit pas ce qu'elle répare ne se surveille pas |
| ✅ **3** | ~~Le numéro Hektor d'**annonce** a le droit d'être vide~~ + sa sentinelle | |
| ✅ **4** | ~~**Identité des transactions**~~ **20/08** — 28 980 affaires numérotées par l'app, clé basculée | **confirmé par lecture** : le worker envoie `idOffre=""` — il ne sait que créer |
| ✅ **4bis** | ~~MESURER : supprimée ou archivée ?~~ **ARCHIVÉE, toujours.** Hektor ne sait pas supprimer une recherche (`console_job_worker.js:11878-11890`) | ⇒ **le rang ne glisse jamais.** Les « 184 contacts à risque » n'existent pas |
| ✅ **4bis-A** | ~~**Les recherches archivées ne sont plus supprimées de Supabase**~~ — 6 777 récupérées | **C'ÉTAIT LA FUITE.** Règle *delete-never* |
| ✅ **4bis-B** | ~~**Le verrou du moteur de rapprochement**~~ — il ne score que les actives | **posé AVANT les données** |
| ✅ **4ter** | ~~Un numéro propre pour la recherche, en doublure~~ — `app_search_id` + `app_search_registry` | table à part, car le run complet **vide** la couche |
| ✅ **4quater** | ~~**Observer** la doublure~~ — **close le 21/08** | le cas limite a été provoqué et vérifié en direct |
| ✅ **4quinquies** | ~~**FIGER le nom de la recherche**~~ — 76 841 noms figés, 0 doublon | **L'empreinte n'est PAS touchée** — c'était la condition posée |
| ✅ **4sexies** | ~~**SENTINELLE « une recherche ne disparaît jamais »**~~ **21/08** — `app_search_count_high_water` + cron + sonde, seuil 0 | **entendue sonner**, puis restaurée. Ferme le risque de position introduit par 4quinquies |

---

### BLOC 0 — PROTÉGER L'EXISTANT · *cette semaine, quelques heures*

| | Tâche | Pourquoi maintenant |
|---|---|---|
| ✅ **0.1** | ~~**Mettre `app_search_registry` et `app_affaire_ledger` dans la sauvegarde de nuit**~~ **FAITE le 22/08** | vérifié **en décompressant l'archive**, pas en lisant ce que le script affiche : 76 841 et 28 981 lignes dedans |
| ✅ **0.2** | ~~**Écrire la règle : le miroir ne se supprime jamais**~~ **FAITE le 22/08** — règle 5 du plan + en tête de `backup_critical.py` | formulation corrigée sur objection de Frédéric : **une mise à jour n'a jamais besoin d'une suppression**, elle écrase en place |
| ⏳ **0.3** | **Finir 19-R1** — le rattrapage acquéreurs, ≈ 4 h 35 | à cocher quand le journal rend `termine OK` |
| ✅ **0.4** | ~~**Fermer l'accès public à `app_dossiers_current`**~~ **FAIT le 24/08** — 13 210 annonces, 10 510 adresses privées et 12 488 noms de mandants cessent d'être lisibles avec la clé publique | **c'était pire que la lecture** : `anon` avait aussi INSERT, UPDATE, DELETE et TRUNCATE. `revoke all`, pas `revoke select`. Vérifié : HTTP 401 |
| ✅ **0.5** | ~~**Fermer les 5 vues de surveillance et `app_search_count_high_water`**~~ **FAIT le 24/08** — `anon` **et** `authenticated` retirés, RLS activée sur la table | n'importe qui pouvait **effacer** cette table : aucune RLS et TRUNCATE accordé. Le trou était de moi |
| ✅ **0.6** | ~~**Supprimer `tmp_etape12_avant`**~~ **FAIT le 24/08** | |
| ✅ **0.7** | ~~**Auditer les fonctions appelables sans être connecté**~~ **FAIT le 24/08** — **85 SECURITY DEFINER, 81 ouvertes à la clé publique. 33 vérifient leur appelant, 48 non** | **la bonne nouvelle** : les 33 qui vérifient sont exactement celles qui font des dégâts — **toutes** les `app_console_create_*_job` *(supprimer une annonce, un contact, une recherche)*. Un visiteur ne pouvait pas déclencher de suppression |
| | **12 fonctions de maintenance fermées** — balayages, recalculs, mises en file, alertes, `claim_next_job` | un visiteur pouvait appeler `app_bulk_recompute_chunk` en boucle et **charger l'instance à volonté** — ce qui l'a fait redémarrer le 21/08, mais involontairement. Vérifié : 401 à la clé publique, le worker passe toujours, **0 échec cron**, 21 sondes OK |
| ⚠ | **DETTE ASSUMÉE** — 36 fonctions sans contrôle interne restent appelables sans être connecté | ce sont surtout des **lectures** que le front appelle. Les caractériser demande de lire 36 corps de fonction. **Connu, pas ignoré** |
| ✅ **0.8** | ~~**Le correctif d'une ligne, sur les trois fonctions**~~ **FAIT le 24/08** — `and p.conflict = false` ajouté à la suppression qui annulait la protection | **prouvé par un essai contrôlé** : une ligne en conflit **survit** désormais au passage de la mise en file, une ligne sans conflit est toujours nettoyée. Motif vérifié et non deviné — la migration lève une exception si elle ne trouve pas, si elle s'applique deux fois, ou si le compte n'est pas 3 |
| | **QUAND LE FAIRE : MAINTENANT, et précisément parce que rien n'est en jeu** | **0 ligne en attente, 0 en conflit sur les trois tables aujourd'hui.** Le rayon d'action est donc **nul**. Attendre l'étape 2, ce serait poser le correctif au moment où les négociateurs en dépendent — l'inverse de la prudence. Et d'ici là on aura des **semaines de preuve** que rien ne s'accumule |
| | **Ce qu'il faut surveiller ensuite** — le nombre de lignes en conflit sur les trois tables | il était fatalement à zéro *(elles étaient effacées)*. S'il monte, **c'est une information, pas une panne** : ce sont des saisies qu'on perdait sans le savoir. La règle des 24 h borne l'accumulation — **rien ne peut geler indéfiniment** |

---

### BLOC A — OUVRIR LES DOSSIERS LONGS · *cette semaine, en parallèle de tout le reste*

> **La correction d'ordonnancement la plus importante du plan.** Ces deux dossiers étaient rangés
> en 29 et 30, à la toute fin. Or leur délai **ne dépend pas de nous**. Les commencer après vingt
> tâches techniques, c'est ajouter leur durée *après* tout le reste. Ouverts maintenant, ils se
> déroulent pendant qu'on code.

| | Tâche | |
|---|---|---|
| ⏳ **A.1** | **Portails** — engager la sortie en nom propre, et la reprise des ~350 annonces en ligne *(ex-29)* | délai non maîtrisé. La partie commerciale peut démarrer tout de suite ; le flux de diffusion se construit en parallèle |
| ⏳ **A.2** | **Signature** — ton propre contrat *(ex-30, Yousign)* | ImmoSign appartient à l'abonnement Hektor : le jeton est lu dans une iframe. À la coupure, la signature s'arrête |
| ⏳ **A.3** | **Registre de mandats en propre** *(ex-31)* | obligation légale ; aujourd'hui adossé à Hektor |
| | 🏛 **SA MOITIÉ TECHNIQUE ENTRE DANS LE PLAN DE DEV — 28/08.** Le « registre » d'aujourd'hui est **une vue des annonces**, reconstruite chaque nuit et filtrée sur leur statut : **1 105 mandats n'y apparaissent pas**, dont **642 parce qu'ils sont clos**. Et il se reconstruit depuis le miroir — à la coupure il gèlerait, incapable d'accueillir un mandat neuf, alors que **181 des 182 mandats créés depuis juin viennent de l'app**. ➡ chiffrage, trois couches de numérotation et place dans l'ordre : section **A.3-TECHNIQUE** plus bas. **3 à 5 jours**, à faire **tant que Hektor vit** | |

**Tant que A.1 et A.2 ne sont pas faits, on ne peut pas couper** — même si toutes les données
étaient déjà chez toi.

---

### BLOC B — LE SERVEUR APPREND DE L'APP · *le morceau qui manquait*

> **Ce bloc n'existait pas dans le plan.** L'audit du 21/08 a montré que **rien ne remonte
> jamais** de Supabase vers le serveur : sur les 11 scripts qui touchent les deux, aucun n'écrit
> une valeur venue de Supabase dans une table locale. Le plan supposait cette moitié acquise.

| | Tâche | Risque |
|---|---|---|
| ✅ **B.1** | ~~**La descente de ce que Hektor ignore**~~ **FAITE le 22/08** — `phase2/sync/pull_from_supabase.py` — **110 tables, 1 337 162 lignes**, 0 en échec. La base locale passe de 2,26 à 3,76 Go | **le serveur apprend de Supabase pour la première fois.** Rapprochements, documents, registre de mandats, DVF, estimations, notifications : tout cela n'existait qu'en ligne, sans aucune copie ni sauvegarde |
| | **Ce qui a été construit** — découverte des tables par la spec OpenAPI *(aucune liste à tenir, donc rien à oublier)* · garde-fou : le script refuse d'écrire dans une table qu'il n'a pas créée *(les 10 exclues sont les bonnes)* · `SupabaseReader` n'a qu'une méthode `get` : **il ne peut pas écrire en ligne** | |
| | **Les trois freins**, posés après l'incident — **copier puis renommer** avec comptage avant bascule · **frein** entre les requêtes et tables triées légère→lourde · **verrou** contre deux descentes simultanées | ils ont servi dès le premier run réel : une copie amputée de 4 lignes a été **refusée** avant de remplacer la bonne |
| | ⚠ **INCIDENT du 21 au 22/08** — deux descentes lancées en une heure, ~2 800 requêtes sans frein : l'API de données a rendu HTTP 522 pendant ~20 min et l'instance a redémarré. Nuit, personne au travail, **aucune donnée perdue**. Compte rendu complet dans `AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md` | la même leçon que le rattrapage des documents chez Hektor, que je n'avais pas transposée |
| | ⚠⚠ **DEFAUT DE PAGINATION TROUVE ET CORRIGE LE 28/09 — il dormait depuis le 15/09.** La boucle ajuste la taille de page au poids *(réduction au-delà de 4 Mo, remontée en dessous de 512 ko)*, **puis** se demandait si la page était la dernière — en comparant à une taille **qui venait de changer** : `on demande 125 → on reçoit 125 → la page est légère, la taille passe à 250 → « 125 < 250 ? » → on croit avoir fini`. Résultat le 28/09 : **`app_dossiers_current` refusée, 9 250 lignes lues sur 13 439**. La taille demandée est désormais **figée avant tout ajustement** (`demandee`), dans **les deux boucles** *(clé composite et clé simple, même défaut)*. ↪ `7ae13f0` | **Pourquoi il dormait** : sans page lourde, la taille ne bougeait jamais de ses 1 000 lignes — donc jamais d'écart entre ce qu'on demande et ce à quoi on compare. Il s'est réveillé quand une vue a grossi *(colonnes sœurs des photos, G.15-d)*, et **il se serait réveillé pareil sur n'importe quelle table qui grossit un jour**. ⚠ Le **contrôle de complétude a tenu** : copie tronquée **refusée**, ancienne conservée, rien perdu |
| | ✅ **EPROUVE, rouge puis vert.** En simulation *(13 439 lignes lourdes puis légères)* : ancienne version **9 500** lignes → tronquée, nouvelle **13 439** → complète — le 9 500 simulé encadre le 9 250 observé. Puis **descente entière relancée le 28/09 10:26→11:02** *(go de Frédéric)* : **exit 0**, `app_dossiers_current` **13 439**, `dernier_echec` effacé, **0 table en échec**, **149 tables / 2 134 148 lignes**, aucune régression | ⚠ **Ni les vues ni le front n'ont été touchés** : les 38 Mo de galeries sont toujours là et descendent sans broncher. C'était **le copieur**, pas le poids — retirer les colonnes aurait **masqué** le défaut |
| ✅ **B.2** | ~~**La descente des fiches, en doublure**~~ **FAITE le 22/08** — **10 doublures, 174 720 lignes**. Total : **120 tables, 1 511 882 lignes**, base locale à 3,90 Go | **aucun arbitrage** : la table dérivée garde la version Hektor, la doublure `__sb` porte celle de l'app. Elles cohabitent, personne ne tranche |
| | **La règle n'a plus d'exception** — *un nom qui se heurte →* `<nom>__sb`, toujours. L'ancienne « le nom existe en local → on ne touche pas » m'obligeait à juger qui était le maître, **et je me suis trompé 2 fois sur 10** | découvert sur demande de vérification de Frédéric |
| | ⚠ **Ce que cette vérification a trouvé** — `app_diffusion_request` (**9**) et `app_diffusion_request_event` (**29**) sont créées par le **front seul** ; la table locale du même nom est une **coquille vide**. Mon garde-fou les prenait pour des tables natives et les laissait **sans aucune copie locale**. Et `app_diffusion_target` (42 local / 13 en ligne) est **deux vies parallèles** : le local écrit par un script **manuel**, absent du run de nuit ; l'en-ligne par le front | |
| | **L'annonce était déjà faite par B.1** — `app_dossier_current` et `app_dossier_detail_current` n'entraient pas en collision de nom, donc elles étaient déjà descendues, à côté de `app_view_generale`. B.2 se réduisait au contact | |
| | **Vérifié en 14 contrôles** — intégrité SQLite · les 14 tables natives **inchangées à la ligne près** · 0 résidu · 0 copie en cours · 0 script du projet ne lit ou n'écrit une table descendue · reconstruction d'un contact en 5 s · sauvegarde et 20 sentinelles inchangées · **et le CONTENU comparé valeur par valeur** : 225 + 550 valeurs relues chez Supabase, **0 écart** | les comptes ne prouvent pas le contenu |
| ⏳ **B.3** | **Le déclencheur** — le worker appelle la descente pour la fiche qu'il vient de traiter *(idée de Frédéric, 21/08)* | **en attente de ce que dira le journal.** La doublure ne se rafraîchit qu'à la descente : une modification faite à 9 h n'apparaît qu'à 7 h 30 le lendemain. Suffisant pour **observer**, pas pour **arbitrer**. Si la colonne « app seule » reste plate pendant trois semaines, B.3 est inutile ; si elle grimpe, il se justifie **avec un chiffre** |
| | ❗ **LE CRITÈRE NE PEUT PAS BOUGER — corrigé le 26/08.** Le relevé de la descente montre de quoi la colonne « app seule = 45 » est faite : `app_diffusion_request` **9** + `app_diffusion_request_event` **29** + `app_diffusion_target` **7**. **Que des demandes de diffusion** — les seuls objets que Hektor ne connaît pas. Les trois essais du 25/08 *(un contact modifié, un contact créé, un mandant créé et rattaché)* **ne l'ont pas bougée d'un point**, et c'est normal : tout est passé par Hektor et en est revenu | |
| | ➡ **Donc attendre trois semaines ne prouverait rien.** Cette colonne ne montera que le jour où l'app possédera des objets que Hektor ignore — c'est-à-dire **après 26bis et C.9**. **La décision sur B.3 dépend de 26bis, pas du calendrier** | |
| ✅ **B.4** | ~~**Le serveur dit-il la même chose que Supabase ?**~~ **FAITE le 22/08** — `phase2/checks/comparer_doublures.py` + `app_doublure_journal` + **2 sondes** (`data.doublure_journal`, `data.recherche_divergente`) | **un journal, pas une alarme globale.** Un seuil sur « les deux diffèrent » sonnerait toujours pour rien : Supabase ne porte qu'un sous-ensemble. Une sentinelle qui sonne toujours ne protège de rien |
| | **Premier relevé** — `app_affaire_ledger__sb` 28 981 d'accord, **0 écart** · `app_diffusion_target__sb` **6 / 36 / 7** *(les deux vies parallèles, enfin chiffrées)* · **45 lignes** connues de l'app SEULE | |
| | **L'alarme est étroite et elle a du sens** — les recherches présentes **des deux côtés** dont les critères diffèrent. Une seule ligne = un négociateur a affiné une recherche que Hektor n'a jamais reçue. **0 sur 10 762** | **entendue sonner** : `prix_max` modifié dans la doublure → CRITICAL 1 ; restauré → OK 0 |
| ✅ **B.5** | ~~**La tâche planifiée**~~ **FAITE le 22/08** — `GTI Descente`, **07:30**, descente puis relevé. S4U, limite 2 h, rattrapage si manquée | après le run de 05:30 *(qui pousse la journée)* et après la sauvegarde de 07:00 *(qui fait l'instantané)*. **Les 6 tâches GTI sont désormais en S4U** : elles tournent sans session ouverte |

**B.1 a rendu un service double.** Ce million de lignes n'avait **aucune copie ni sauvegarde
hors de Supabase**. Il est desormais dans `phase2.sqlite`, donc couvert par l'instantane
**hebdomadaire** (niveau 2 de `backup_critical.py`).

> **A trancher plus tard** : `phase2.sqlite` passe de 2,26 a **3,76 Go**, donc l'instantane
> hebdomadaire grossit d'autant. Et le rafraichissement des vues du run de 05:30 est passe de
> **37 a 56 secondes** -- mesure sur le run du 22/08. Modeste, mais reel : a surveiller si la
> base continue de grandir.

### Les trois incidents du 21-22/08, et le garde-fou que chacun a produit

Aucune donnée perdue dans les trois cas. Mais chacun a révélé un manque, et c'est ce qui rend
le bloc B solide aujourd'hui — pas la relecture du code.

| Incident | Cause | Ce qu'il a produit |
|---|---|---|
| **Supabase saturée jusqu'au redémarrage** | 2 descentes lancées en 1 h, ~2 800 requêtes sans frein | le **frein** entre requêtes, les tables **légères d'abord**, et le **verrou** |
| **Le rattrapage de l'autre session tué** à 7 500 | mes écritures concurrentes dans `phase2.sqlite` — les `CREATE INDEX` du relevé, hors verrou | `busy_timeout` **30 s** *(autre session)* + le **verrou étendu aux deux étapes** |
| **Un verrou désarmé sur un run vivant** | `Stop-ScheduledTask` tue le PowerShell parent, **pas le python enfant** : il devient orphelin et va au bout. J'ai retiré un verrou qui protégeait un run en cours | le verrou **vérifie que son processus est vivant** *(OpenProcess, jamais `os.kill` sous Windows — il tuerait le processus)* |

**Trois défauts trouvés en testant, pas en relisant** : la copie tronquée prise pour une fin de
table *(elle remplaçait la bonne, en silence)*, le `--dry-run` du relevé qui écrivait quand même
*(il pose les index)*, et la comparaison sans index qui tournait **dix minutes** au lieu de 26 s.

> **Deux leçons de méthode, valables au-delà de ce bloc :**
> **① Arrêter la tâche planifiée n'arrête pas le travail.** Pour couper, il faut tuer le python.
> **② Un message d'erreur qui accuse le mauvais coupable coûte une heure.** Le coupe-circuit
> criait « bannissement d'IP » sur une panne locale ; mon verrou disait « une descente tourne »
> quand c'était le relevé. Les deux sont corrigés.

**Pourquoi la descente et pas la double écriture** *(question de Frédéric, tranchée le 21/08)* :
une double livraison ne couvre que ce qui passe par un worker — **5 % des lignes** — elle exige
que chaque fonction future **pense** à s'y brancher, et elle place le risque **dans le chemin
d'écriture du négociateur**. La descente couvre tout, ne demande rien à l'app, et si elle échoue
personne n'est bloqué. Et surtout : après la coupure, l'app écrira toujours dans Supabase — **le
serveur devra de toute façon apprendre de Supabase.** La descente n'est pas une rustine, c'est la
moitié manquante de l'architecture finale.

---

### BLOC C — L'APP DEVIENT L'AUTEUR · *réduit le 24/08 par la stratégie en trois étapes*

> **Quatre morceaux ont été supprimés** et le plus gros divisé par deux. Ce n'est pas un
> renoncement : l'interdiction d'ouvrir Hektor à l'étape 2 les rend **sans objet**.

#### À FAIRE AVANT L'ÉTAPE 2 — *pendant que les négociateurs sont encore dans Hektor*

| | Tâche | Durée | Pourquoi maintenant |
|---|---|---|---|
| ✅ **C.3** | ~~**Fermer la porte sortante des recherches**~~ **FAIT le 24/08** — `push_search` devient `null` dans les **deux** fonctions d'édition *(négociateur **et** espace client)*. La ligne d'attente devient un **registre** : elle survit, elle protège, elle ne part jamais | **le mécanisme le prévoyait déjà** — la boucle d'enfilage exige `push_search is not null`, et aucune suppression n'atteint une telle ligne. Pas de table neuve, pas de cron touché. **Vérifié** : survit à 2 passages, 0 travail créé |
| | **L'alarme a été adaptée en même temps** — les recherches du registre sortent de `data.recherche_divergente` | sans quoi elle passerait en CRITICAL dès le premier affinage, **alors que la divergence est désormais voulue**. Une sentinelle qui sonne quand tout va bien cesse d'être lue |
| ⚠ | **Ce que ça change pour tes clients** — un acquéreur qui affine sa recherche dans son espace croira peut-être que son négociateur la verra dans Hektor. **Ce n'est plus le cas** | 28 envois en 90 jours : l'effet est nul aujourd'hui, il compte pour l'étape 2 |
| 🟡 **C.1'** | **« UNE SAISIE NE SE PERD JAMAIS »** — **a et b FAITS le 24/08 · le geste (c) REOUVERT le 29/08**, il n'a jamais couvert les actions *(voir C.4-bis)*. Ce qui suit reste exact pour les éditions — la purge des 24 h retirée des 3 fonctions · la sortie de conflit *(`app_pending_resolution` + `app_annonce_pending_resolve`)* · les 3 marqueurs du worker cessent d'avaler leur échec · 4 sondes ajoutées · le bandeau distingue les deux causes et permet de clore | **FAIT** | **Deux des trois gestes existaient déjà** — la saisie était gardée, et la reprise était écrite *(5 tentatives, délai croissant)*. Le défaut réel tenait en **une ligne** : la purge des 24 h. **L'avertissement avait une durée de vie d'un jour**, et n'était visible que de qui rouvrait cette fiche précise |
| ✅ **C.2a** | **Identité des contacts — la relecture** — `RELECTURE_IDENTITE_CONTACTS_2026-08-24` | **FAIT le 24/08** | **Le verrou du 20/08 est levé** : un seul fabricant de nom de recherche, local, et il consulte le registre — **0 fonction Supabase sur 27 n'en fabrique**. Ajouter une colonne ne peut plus déplacer une clé. Et le périmètre est plus petit qu'annoncé : **4 tables sur 18 portent 95 % des 202 404 lignes**, 6 sont vides |

> ⚠ **Ce que ça change pour la surveillance** : la sonde ne mesure plus une perte déjà
> consommée, mais **du travail en attente de décision**. Elle reste rouge tant qu'un humain
> n'a pas tranché — c'est voulu, c'est l'objet même de la tâche.
>
> ℹ **Reste ouvert, et ça porte un numéro : C.12** — **les contacts seulement**. Les
> recherches n'en ont pas besoin : **C.3 a fermé la porte**, elles ne peuvent plus produire
> de conflit *(vérifié)*. Les annonces ont leur bouton depuis C.1'.
> *Écrit d'abord ici en simple commentaire, ça se serait perdu — et j'avais dit « contact ET
> recherche ». Frédéric a relevé les deux le jour même : une chose qui n'est pas une TÂCHE
> n'existe pas, et un périmètre qu'on n'a pas mesuré est toujours trop large.*

#### C.1' — la règle qui remplace l'arbitrage

Trois gestes, et **aucun n'est de l'arbitrage** :

| | |
|---|---|
| **a** | Une saisie dont l'envoi a échoué **n'est jamais écrasée** par le run. Aujourd'hui la protection est une ligne **temporaire** qui disparaît ; elle doit devenir **durable** |
| **b** | L'échec est **visible**. Aujourd'hui le travail est marqué `done` et personne ne sait |
| **c** | Et il **se reprend**. Aujourd'hui il ne repart jamais |

> C'est le patron qui a déjà marché **trois fois** dans ce projet : `app_dossier` qui marque
> `absent_depuis` au lieu de supprimer, `app_affaire_ledger` en *delete-never*,
> `app_search_registry` qui survit à la reconstruction.
> **Ne jamais laisser le passager effacer le durable.**

#### À CONSTRUIRE MAINTENANT, DORMANT — *(ex-« pendant l'étape 2 », corrigé le 24/08)*

*Aucune de ces tâches n'attend que les négociateurs bougent. Chacune se construit et se livre
**éteinte** ; seul son **interrupteur** attend — voir le tableau plus bas.*

| | Tâche | Durée |
|---|---|---|
| ✅ **C.2b** | ~~**Identité des contacts — le code**~~ **FAIT le 25/08** — `app_contact` locale (355 687 numéros, patron d'`app_dossier`) · `app_contact_id` sur **19 tables** Supabase · **144 985 lignes remplies** · sonde · branché dans le run de nuit | **FAIT** | **0 incohérence** : aucune ligne ne porte un numéro différent de sa fiche contact, et **0 numéro ne sert à deux contacts**. La clé primaire n'est **pas** touchée, et **personne ne lit encore la colonne** — c'est une doublure |
| | ⚠ **Ce que le chantier a révélé, absent du plan** : *le registre doit se **maintenir**, pas seulement se créer*. Le jour même, **15 contacts créés la veille** étaient déjà dans Supabase et pas encore en local. Le script est devenu incrémental et tourne chaque nuit | |
| | ℹ **35 vrais orphelins** trouvés dans `app_search_count_high_water` — des compteurs qui pointent un contact qui n'existe plus. **Exactement ce que C.2a annonçait** : sans clé étrangère, les orphelins existent sans que rien ne le signale. *Signalé, pas corrigé* | |
| ✅ **C.12** | ~~**La sortie de conflit — contacts**~~ **FAIT le 25/08** — `app_contact_edit_status` + `app_contact_pending_resolve` · bandeau à deux causes posé dans **les DEUX versions** de la fiche | **FAIT** | Un défaut trouvé **par l'essai, avant mise en service** : la trace lisait le numéro sur la ligne d'attente, que seule une ligne déjà rattrapée porte. Elle le résout désormais **à la source** |
| | ✅ **Les recherches n'en ont PAS besoin** — *vu par Frédéric, vérifié de bout en bout*. C.3 a fermé la porte : aucun travail créé, aucun `push_job_id`, donc **aucun conflit possible**. Le bouton aurait été mort-né | |
| | ℹ **Nom du paramètre** : `target_hektor_contact_id`, pas `target_contact_id`. Le renommage des 11 fonctions ambiguës reste **rayé**, mais pour des fonctions **neuves** le nom clair ne coûte rien. *On arrête d'en créer des ambiguës* | |
| ✅ **C.6** | ~~**Le domicile de l'annonce**~~ **FAIT le 25/08** — table `app_annonce_champ_app`, clé/valeur, **jamais reconstruite** · branchée en 3/3 de la descente · sous sauvegarde critique | **FAIT** | Le plan annonçait *36 champs calculés à l'export* : c'est **13**, presque tous techniques. Et le paquet de détail est un blob de 134 clés dont **l'app n'en écrit que 7** |
| | ❗ **Le vrai problème n'était pas la conservation mais l'ÉCRITURE** : `view_generale.py` fait `DROP TABLE` puis `CREATE TABLE AS` — une valeur écrite par l'app **ne survivrait pas à 05:30**. Cette table est le seul endroit où elle survit | |
| | ℹ **Résultat mesuré : 0 divergence sur ~581 000 comparaisons.** Mais **quatre faux écarts** ont dû être éliminés d'abord — `NULL` vs `0.0` *(7 143 !)*, entier `0` vs texte `'0'` *(23, piège GLOB)*, la date sentinelle `0000-00-00`, et **un jour de décalage** *(89)*. C'est ce dernier qui dicte le placement : les deux côtés doivent être de la même heure | |
| 🟡 **C.4** | **Les workers — 16, et non 35** *(mesuré : `ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20`)*. Familles B1+B2. Statut + affaire *(le plus riche)* · archiver/désarchiver · créer contact et mandant · **affectation du négociateur EN DERNIER** *(impersonation)* | **7 sur 34 marchent déjà sans Hektor.** Et **3 seulement** en dépendent vraiment — numéro de mandat, relance et annulation de signature — soit **exactement A.1 et A.2** | · 🟡 **TERMINÉ SAUF LA VENTE** *(corrigé le 27/08 après-midi — ma première conclusion « terminé » était fausse)*. **Faits et éprouvés** : archiver / désarchiver / supprimer *(127 exécutions)* · affectation du négociateur *(14)* · le **lot 3** posé le 27/08. **Il reste la branche « Vendu » du lot 1** : elle appelle la clôture de mandat, donc **elle dépend de C.13**, et elle **n'a jamais été exécutée une seule fois** *(14 changements de statut depuis mai : `offer`, `active`, `closed` — jamais `sold`)*. ⚠ **DEUX ERREURS DE MÉTHODE À NE PAS REFAIRE.** ① `app_console_job.status` est un **état courant, pas un historique** : un travail qui rate puis passe redevient `done` et son échec s'efface — le vrai journal est **`app_console_job_log`**, qui porte **41 erreurs** *(dont 3 sur l'affectation du négociateur et 2 sur le changement de statut, donc « 0 échec » était faux)*. ② **J'ai conclu sans témoin** : « 1 seule erreur sur 54 806 » aurait dû m'alerter immédiatement |
| | ❗ **LE MANDAT D'UNE TRANSACTION** *(enquête du 25/08, `NOTE_CHAINE_DES_MANDATS_2026-08-25`)*. **a)** Quand le négociateur changera un statut **depuis l'app**, celle-ci doit **transmettre le numéro de mandat de la fiche** — pas laisser le worker chercher. ⚠ **Et la valeur doit être ENTIÈRE** : Hektor attend `<id>-<FAMILLE>` *(`648-PROTEXA`)*, jamais le numéro seul — c'est ce qui a fait annuler C.5. Tant que Hektor vit, **le worker recopie sa valeur** ; le formulaire n'a rien à envoyer. *La modale actuelle est **réservée aux admins** : `isAdmin ? openStatusChangeModal : undefined`* | |
| | ⚠ **b)** **Si un négociateur crée un nouveau mandat et que la fiche Hektor ne bascule pas tout de suite**, le numéro de la fiche pointerait encore l'**ancien**. Ce n'est pas théorique : le même défaut a été corrigé le 28/07 sur les dates *(VA6482 — numéro neuf + date de fin échue → annonce bloquée en « échu »)* | |
| | 🔎 **DEUX MANQUES TROUVÉS LE 28/08 AU SOIR — tous deux DANS LE MÊME WORKER, `change_hektor_annonce_status`.** Ce ne sont pas de nouveaux workers : ce sont des **branches** de celui qui porte déjà *Actif · Offre · Compromis · Vendu · Clos*. **Et tous deux sont RÉVERSIBLES**, donc éprouvables sans risque — contrairement à la branche « Vendu » | |
| | ① **ANNULER UN COMPROMIS : l'app sait les LIRE, pas les POSER.** Hektor le fait par le champ **`status`** de l'objet compromis — **`1` = actif, `2` = annulé**, correspondance vérifiée un pour un sur **10 573** compromis *(9 206 actifs / **1 367 annulés**, 13 %)*. Et le geste passe par **le même écran que la création** : le JavaScript de Hektor montre `if (id_compromis === '0') créer; else MODIFIER`. **Côté app** : la statistique « Compromis annulés », le filtre « État compromis = Annulé » et la vue existent — mais la modale de statut ne propose que **5 cibles**, aucune n'annule. Aujourd'hui, un compromis qui tombe se corrige **dans Hektor** | |
| | ② **LE WORKER NE SAIT QUE CRÉER, JAMAIS MODIFIER.** Il fait toujours `body.set("idCompromis", "")` — **l'id vide veut dire « créer »**. Passer deux fois par « Compromis » en créerait donc deux. ⚠ **Ce n'est PAS une régression** : sur les **16** changements de statut envoyés depuis mai *(8 clos, 6 actifs, 2 offres)*, il y a **ZÉRO compromis** — **l'app n'en a jamais créé un seul**, le cas ne s'est jamais produit | |
| | ✅ **ET LES COMPROMIS MULTIPLES SONT NORMAUX** *(intuition de Frédéric, confirmée par la mesure)*. **578 annonces** portent plusieurs compromis *(5,8 %)*, mais **561 sont une succession légitime** — annulé, puis un nouvel acquéreur. Seules **17** ont deux actifs en même temps, et elles se lisent en deux groupes : de **vieux dossiers** dont l'annulation n'a jamais été saisie *(2009-2016)*, et une poignée de **doublons de saisie** à la même date. **Rien de tout cela ne vient de nous** | |
| | 🔬 **LA LECTURE A ETE FAITE LE 28/08 AU SOIR — ET ELLE M'A DONNE TORT.** *(3 requêtes, lecture seule, HTTP 200, `Console/capture_transaction_actions.js`)*. J'avais posé une mécanique de « reprise » — passer l'identifiant pour que Hektor MODIFIE au lieu de créer. Elle reposait sur une hypothèse, **fausse**, et c'est le **témoin** qui l'a montrée : *popin offre avec `id_offre` = **208 506 car.** / sans identifiant = **208 506 car.**, popin compromis avec `idCompromis` = **85 915** / sans = **85 915*** — **IDENTIQUES octet pour octet**. ➡ **Hektor ignore l'identifiant à l'ouverture.** Le formulaire rendu est donc toujours VIERGE, or c'est lui qui sert de repli à `sequestre` et `prixNetVendeur` : si l'enregistrement honorait l'identifiant, **modifier EFFACERAIT** ces champs. Invérifiable sans écrire pour de vrai ➡ **tout est suspendu** *(`0032d92`)*. **Le worker crée toujours, exactement comme avant** — 12 cas de test le vérifient | |
| | 📌 **CE QUE LA LECTURE A QUAND MÊME RAPPORTÉ** : ① le formulaire d'offre **porte bien un champ `idOffre`** et ses **22 champs** sont relevés — le mécanisme existe, c'est la manière de faire **charger** l'existant qui reste à trouver ; ② le compromis est un formulaire **PAR ÉTAPES** *(`compromisStepper`, gabarits Mustache chargés après)*, d'où sa réponse sans aucun champ ; ③ **ni l'un ni l'autre ne porte de commande accepter / refuser / annuler** — ces gestes vivent ailleurs dans Hektor, **encore à localiser** | |
| | ➕ **UN TROISIÈME GESTE MANQUE, signalé par Frédéric : REFUSER UNE OFFRE.** Et c'est le plus rassurant des trois : une offre chez Hektor est **une conversation**, pas un état — son `propositions_json` empile des événements *(**11 061** propositions, **9 988** acceptations, **1 096** refus)*. Refuser **ajoute une ligne**, n'écrase rien. Donc contrairement à la reprise implicite qui devinait, c'est un geste **explicite et sans danger** : l'utilisateur désigne l'offre. Même chose pour **accepter** | |
| | ✅ **RÉSOLU LE 28/08 AU SOIR — `ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md`.** **L'idée vient de Frédéric** : *« pourquoi ne pas utiliser ta session Hektor ouverte avec administrateur sur Chrome ? »*. Les boutons sont **sur l'écran**, leur `onclick` porte le nom de la fonction. Lecture du DOM, **aucun clic, aucune écriture**. Après deux tentatives ratées *(nos captures ne contenaient que le JS d'en-tête ; et les formulaires demandés au serveur ignorent l'identifiant)* | |
| | 📋 **LES TROIS GESTES, SPÉCIFIÉS** : **refuser** une offre → `annonce-SuiviVente-updateOffre` avec `id` + `type='refus'` · **accepter** → même mode, `type='accepte'` · **clore un compromis** → `annonce-SuiviVente-compromis-popinClotureCompromis` *(une popin, donc un formulaire encore à relever)*. Et en prime : supprimer une offre *(`deleteOffre`)*, un compromis *(`deleteCompromis`)*, une vente *(`ventes-deleteVente`)* | |
| | 🔴 **CORRECTION AU PROJET — LA VENTE N'EST PAS CE QU'ON CROYAIT.** Le projet affirme **trois fois** *« la vente : pas d'annulation possible »* *(commits `cfe3483`, `b8fc48e` du 25/06, et un commentaire d'`App.tsx`)* — et j'ai répété cette phrase toute la soirée pour justifier de ne pas éprouver « Vendu ». **C'est à moitié faux** : Hektor porte `annuleVente()` et `supprimerVente(id)`, tous deux vers le mode **`ventes-deleteVente`**. **Une vente ne s'annule pas : elle se SUPPRIME** — d'où l'absence de colonne d'état dans `hektor_vente`, il n'y a rien à marquer. ➡ **la branche « Vendu » de C.4 PEUT être éprouvée** : une vente d'essai se retire. La suppression reste définitive, mais ce n'est plus le point de non-retour qui bloquait l'essai | |
| | ⚠ **CONTRAINTE TROUVÉE EN PASSANT** : un bouton de la fiche porte *« Un compte administrateur ne peux pas saisir une offre »*. **Le worker devra donc passer par un compte négociateur** pour ces gestes — comme il le fait déjà pour l'affectation. Même famille que les blocs de signature invisibles en root admin. **À vérifier avant de coder** | |
| | ⛔ **CE QUI MANQUE POUR CODER ①** : le nom du champ **dans le FORMULAIRE** *(`PopinCompromis`)*. L'API rend `status`, mais le formulaire peut l'appeler autrement — et **un mauvais nom n'écrirait rien en silence**, exactement la classe de défaut corrigée le jour même sur la clôture. Le formulaire est chargé à la demande, donc **absent de nos captures**. ➡ **le lire d'abord, en LECTURE SEULE** *(ouvrir la popin avec un `idCompromis` ne sauvegarde rien)* | |
| | 📐 **COUVERTURE RÉELLE : 5 SUR 16 — mesurée le 29/08, après DEUX mesures fausses.** Le principe fondateur de C.4 est *« **écrire d'abord**, envoyer, comparer au retour »*, déclaré applicable *« entièrement »* aux 16 workers B1+B2. **Cinq l'appliquent** : `update_hektor_annonce_fields` · `update_hektor_contact` · `update_hektor_contact_search` *(les trois par `app_edit_*_optimistic`)* · `change_hektor_annonce_status` *(écrit l'affaire)* · `create_hektor_draft_annonce` *(ligne provisoire)*. **Onze ne l'appliquent pas** : archiver · désarchiver · supprimer une annonce · affecter le négociateur · lier un mandant · supprimer un contact · ajouter et supprimer une recherche · créer un contact · créer un mandant · mettre à jour un mandant. ➡ **quand on archive un bien, rien n'est écrit chez nous** : le travail part, et l'utilisateur attend | |
| | 🔬 **COMMENT CE CHIFFRE A ÉTÉ OBTENU, parce que les deux premiers étaient faux.** Une recherche de motif dans `api.ts` a rendu *« 10 sur 26 »*, puis *« 0 sur 16 »* — les deux fois en attribuant les types de travaux à la mauvaise fonction. Le bon chiffre vient de la **lecture des définitions dans `pg_proc`**, puis d'une **troisième vérification à bornes exactes** dans le front, **avec quatre témoins négatifs** *(archiver, désarchiver, affecter, lier un mandant → `insert direct`)* | |
| | ℹ **C.4 n'est PAS l'ouverture des droits** *(corrigé le 25/08)*. Elle rend l'app capable de faire ces gestes **sans Hektor** — c'est un chantier de **coupure**, pas de permission. Les droits sont un sujet à part : **bloc F** | |
| | **C'est ICI que se répondent les 3 arbitrages de A1** — `statut_annonce`/`archive`, `negociateur_email`, les champs de mandat | **pas avant** : la carte de A1 dit « si l'app sait écrire un champ », et **c'est précisément ce que cette tâche change**. Trancher plus tôt serait figer une carte sur un état qui va bouger *(décision de Frédéric, 24/08)* |
| ❌ **C.5** | ~~Registre d'affaires et mandat des transactions~~ — **ANNULÉE le 25/08 au soir, le jour même.** Le worker **recopie de nouveau** la valeur de Hektor. *Le registre d'affaires, lui, reste acquis (tâche 4 du 20/08).* | **RETOUR ARRIÈRE** | **La moitié était déjà faite** : `app_affaire_ledger` porte `app_affaire_id` et `app_dossier_id` depuis le 20/08. Vérifié **avant** de refaire |
| | ❗ **POURQUOI ELLE A ÉTÉ ANNULÉE.** Hektor n'identifie pas un mandat par un nombre : son formulaire attend **`<id>-<FAMILLE>`** — `648-PROTEXA`, `9887-HEKTOR` — parce qu'il tient **deux registres parallèles**. C.5 envoyait `648` : aucune option ne correspond, Hektor range « mandat non renseigné », **sans erreur**. Constaté en vraie grandeur : l'offre **33026** est chez Hektor **sans mandat**, alors que toutes les offres créées depuis septembre 2025 en portent un | |
| | ℹ **Ce qui marchait avant, et pourquoi.** Le worker **recopiait** la valeur de Hektor, lue dans l'`<input>` caché `selectedMandatId`. *(Le plan et l'audit du 20/08 nommaient `id_mandat` : c'est un `<select>`, que `htmlInputValue` ne sait pas lire. Le constat de fond — « le worker dépend du HTML » — était juste ; le champ nommé, non.)* | |
| | ✅ **POURQUOI LE RETOUR ARRIÈRE PLUTÔT QU'UN CORRECTIF** *(arbitrage de Frédéric, 25/08)*. **① Ce worker meurt avec Hektor** — le rendre autonome de Hektor est sans objet. **② Le gain de C.5 était nul, et c'est mesuré** : Hektor pré-sélectionne le mandat courant, et la fiche de l'app désigne le même courant **24 fois sur 24**. **③ Règle du plan** : les workers sont **maintenus, pas refondus** | |
| | 🔎 **Ce qui reste acquis** : la valeur composite, les **deux familles** de registre *(`SIMPLE`/`EXCLUSIF`/`ACCORD` → HEKTOR ; libellé français → PROTEXA, vérifié 10/10)*, et le **livrable A0** de la clôture, jamais produit en juillet. Versé dans **C.13** | |
| ❌ **C.8** | ~~Le **calque** disparaît · la **barrière**~~ **DISSOUTE le 25/08, après mesure** — ses deux moitiés n'étaient pas des tâches | |
| | **2.5, le calque** : `app_edit_annonce_optimistic` **écrit déjà dans la fiche** (`app_dossier_current` + son détail) et garde une photo d'avant dans la file. Le « calque » n'est pas un objet à supprimer : c'est le **statut provisoire** de ce que l'app écrit. Il cesse d'être provisoire **quand le contrat de C.7 cesse d'être vide** — **c'est une bascule d'interrupteur, pas un développement**. Et le faire maintenant, contrat vide, retirerait l'affichage instantané **sans** donner l'autorité à l'app : une régression | |
| | **2.6, la barrière** : **aucun travail n'échoue faute de numéro Hektor** — 456 travaux sans numéro, **0 en erreur**, et ce sont des travaux qui n'en ont pas besoin *(363 rafraîchissements de contact, 26 créations de brouillon)*. Le cas naît avec **C.9** : la barrière y est **fondue** | |
| ⏳ **C.16** | ~~**LES CONTACTS NE SONT JAMAIS REBALAYÉS ENTIÈREMENT**~~ → **REMESURÉE LE 28/08 : 825 FICHES ACTIVES QUI N'EXISTENT PLUS** *(trouvé le 26/08, corrigé le 28/08)* | **1 à 2 j** |
| | 🔴 **LE CHIFFRE DU PLAN ÉTAIT FAUX, SA CONCLUSION ÉTAIT JUSTE.** Il annonçait *« 284 269 contacts ont pour dernière vue 2026-05 »* : c'était une **confusion entre deux dates**. `synced_at` *(quand NOUS l'avons vu)* : **100 % en 2026**, dont 98,2 % en août. `date_maj` *(quand HEKTOR l'a modifié)* : 2025 pour 56 %, 2023 pour 22 % — et c'est normal, un contact ne change pas. **Le listing EST relu.** | |
| | ✅ **LE PÉRIMÈTRE RÉEL, mesuré le 28/08** : miroir **355 756**, Hektor en déclarait **348 053** → écart **+7 703**. Non revus depuis mai : **6 279**, dont **5 454 archivés** et **825 ACTIFS**. Les **611 références orphelines** sont distinctes — **aucun recoupement** *(elles portent `archive` vide et un talon `raw_json`)* | |
| | ✅ **SONDE DÉCISIVE, AVEC TÉMOIN** *(lecture seule, 12 par groupe, rythme du projet)* : **actifs non revus depuis mai → 0/12 existent encore** · **témoin, actifs revus en août → 12/12 existent**. Le défaut est donc réel, et **825 fiches s'affichent comme actives dans l'app alors que Hektor ne les connaît plus** | |
| | ℹ **POURQUOI L'ESSAI DU 26/08 N'AVAIT RIEN VU** — et il n'était pas faux. Il échantillonnait **120 actifs au hasard** et concluait « 120/120 existent ». Or sur 171 046 actifs, les 825 fantômes font **0,5 %** : un échantillon de 120 avait une chance sur deux de n'en croiser aucun. **Il ne visait pas la bonne population** : il fallait interroger ceux que le listing ne rend PLUS, pas les actifs en général | |
| | ➡ **CE QUE LA TÂCHE DEVIENT** : marquer disparues les 825 fiches actives *(jamais supprimer — règle du projet)*, traiter les 5 454 archivées de même, et poser le mécanisme qui **apprend qu'un contact a quitté le listing**. Ce dernier existe déjà pour les annonces — c'est `reconcile_annonce_scope`, tracé depuis le 26/08. **Le patron est là, il faut l'appliquer aux contacts** | |
| | ⚠ **LEÇON DE MÉTHODE, deux fois le même jour.** ① Ma première lecture *(« seulement 6 278 remontent à mai »)* était fausse aussi : je lisais une tranche mensuelle là où la vue annuelle dit 100 % en 2026. ② Et ma première sonde lisait **la mauvaise clé** de la réponse Hektor *(`data` au lieu de `contact`)* : elle rendait « 0/12 existent » **dans les deux groupes**. **C'est le groupe témoin qui a montré que la sonde était cassée** — sans lui, j'annonçais 825 disparitions pour une faute de frappe | |
| | ❗ **LE RUN DES CONTACTS EST EN DELTA, PAS EN BALAYAGE.** Contrairement aux annonces *(balayage complet chaque nuit, 2 847 pages)*, les contacts ne sont revus que s'ils ont bougé. **Le listing complet n'a pas été rebalayé depuis mai** : 284 269 contacts ont pour dernière vue `2026-05`. **Conséquence : si Hektor archive ou supprime un contact, nous ne l'apprenons pas** | |
| | ℹ **L'écart mesuré** : Hektor déclare **348 053** contacts *(169 448 actifs + 178 605 archivés)*, notre miroir en a **355 712** — **+7 659** | |
| | ✅ **ESSAI A (26/08), échantillon stratifié de 300 contacts interrogés un par un** : **actifs 120/120 existent — 0 supprimé** · **archivés 117/120, soit 2,5 % absents** *(≈ 4 600 sur 184 100)* · **sans indicateur d'archivage : 0/60, soit 100 % absents** | |
| | 🔴 **LES 611 « SANS INDICATEUR » NE SONT PAS DES CONTACTS SUPPRIMÉS — CE N'EN ONT JAMAIS ÉTÉ.** Leur charge brute est un talon : `raw_json = {"id": "56974"}`. Ce sont des **RÉFÉRENCES ORPHELINES** : une annonce, une offre ou un mandat de Hektor cite un identifiant de contact, nous en gardons le nom et la typologie — et `ContactById` répond **404**. **C'est une incohérence dans les données de Hektor, que le miroir a fidèlement recopiée** | |
| | ℹ **Ce n'est pas de la déduplication** : sur 11 absents testés, **2 seulement** appartiennent à un groupe de doublons — alors que le parc en compte 37 144 groupes / 80 992 membres | |
| | ✅ **Écarté avec preuve** : doublons d'identifiant *(355 712 lignes = 355 712 identifiants distincts, en texte comme en entier)* · périmètre d'agence *(la somme par agence égale exactement le total)* · filtre `type` *(`type=0` rend le total, et les types se chevauchent — un contact peut être propriétaire ET acquéreur)* | |
| | ⚠ **CORRECTION D'UNE ERREUR À MOI** : j'avais expliqué les 7 659 par « des contacts supprimés que nous accumulons, faute de mécanisme de suppression ». **Faux sur deux points** — la règle « on ne supprime jamais » date du **22/08**, elle ne peut pas expliquer un écart antérieur ; et les actifs ne montrent **aucune** suppression. Frédéric a refusé cette explication, il avait raison | |
| ✅ **C.15** | ~~**LE RUN NE VOYAIT QU'UN TYPE D'OFFRE SUR SIX — 4 165 ANNONCES N'ENTRENT JAMAIS** *(trouvé le 26/08)* · `sync_raw.py` appelle `ListAnnonces` **sans le paramètre `offre`**, et Hektor rend alors **uniquement les ventes** | 🔴 **LE PLUS GROS TROU CONNU** · **① ② ③ faits · ④ le canari POSÉ le 27/08** *(annonce **62483**, Bourg-Argental, diffusée depuis le 11/06, absente de `raw_api_response`)* — code écrit + banc de non-régression, **pas encore passé dans un run**. Détail, couplage et attendus : `FEUILLE_DE_ROUTE_2026-08-24.md` § ④ |
| ✅ **C.17-bis** | **LE MONITEUR MOURAIT À L'INSTANT OÙ IL AVAIT QUELQUE CHOSE À DIRE** *(trouvé le 28/08)* · **CORRIGÉ** `9c8bdc7` | **FAIT** |
| | Passages de 05:48 et 07:48 : journal de **164 octets** — l'en-tête seul, sans le pied — et code 1. Relancé à la main, le moniteur rend son rapport complet et juste. **La cause : deux choses inoffensives séparément.** `$ErrorActionPreference = "Stop"` en tête du wrapper *(d'origine)*, et la redirection `*>>` qui recopie **aussi** la sortie d'erreur de Python. Sous Windows PowerShell, recopier la sortie d'erreur d'un programme externe emballe **chaque ligne dans une erreur** ; avec « Stop » la première devient terminante. Le wrapper meurt donc en notant la phrase — **avant de l'avoir écrite** | |
| | ⚠ **L'ironie, et le danger** : tant que tout va bien le moniteur ne dit rien, donc rien ne le tue et son rapport s'écrit *(01:49 et 03:49 : 55 Ko chacun)*. **Il ne se taisait QUE quand il avait quelque chose à dire** — mot pour mot la leçon de C.17, une seconde fois | |
| | ✅ **Reproduit sur banc isolé** : ancien patron → en-tête seul, code 1 ; nouveau → journal complet, code **2** *(le vrai)* préservé. Et un défaut introduit la veille corrigé au passage : `*>>` écrit en UTF-16 alors que l'en-tête était en UTF-8 — journaux à deux encodages depuis le 27/08 | |
| | ℹ **Ce défaut préexistait au correctif du 27/08.** Ce que celui-ci a apporté, c'est l'en-tête : avant, ces passages laissaient un fichier de **0 octet** et l'on ne pouvait pas distinguer « Python n'a jamais démarré » de « il est mort en route ». **C'est cet en-tête qui a permis de trouver la vraie cause le lendemain** | |
| ✅ **C.18** | **UNE ANNONCE CRÉÉE POUR UN NÉGOCIATEUR MULTI-AGENCES PARTAIT DANS LA MAUVAISE AGENCE** *(trouvé le 28/08)* · **CORRIGÉ** `53f817c` | **FAIT** |
| | Vincent-Lucas GONZALEZ existe **trois fois** chez Hektor — Firminy *(actif)*, Saint-Étienne et Monistrol *(inactifs)* — **avec le même email**. Avant d'écrire, le worker vérifie que le négociateur est actif : il interrogeait l'annuaire **par email, une seule ligne, sans ordre imposé**. Il tombait sur Saint-Étienne, inactive → « négociateur inactif » → repli « écriture via l'agence » → **qui résolvait l'agence de la même façon ambiguë** | |
| | ❗ **Ce n'était pas théorique** : **3 annonces** créées depuis l'app sont parties à Saint-Étienne alors qu'on demandait Firminy — 30/06, 06/07 et 27/08. Témoin : les annonces du même négociateur **non créées par l'app** sont toutes à Firminy | |
| | ⚠ **Et ce n'est pas un défaut de l'immobilier professionnel** : l'identité se choisit **trois secondes avant** que le type de bien soit prononcé *(journal : contexte agence à 22:15:13, `offredem`/`idType` à 22:15:16)*. **Une maison** créée pour l'une des **25 personnes multi-agences** partait pareil. Le défaut dormait parce que les créations depuis l'app sont rares et presque toutes faites pour des mono-agence | |
| | ✅ **Deux causes exactes** : l'app envoie `hektor_negociator_form_id`, les deux fonctions du repli lisaient `hektor_negociateur_id` — **l'identifiant sans ambiguïté était ignoré** ; et `payload.agence_nom` n'était consulté **ni** par le test d'activité **ni** par le repli. Correctif : on interroge d'abord les identifiants qui ne trompent pas, l'email en dernier recours, et on **choisit** alors la ligne *(agence demandée, puis identité active)*. **10 cas sur 10**, et prouvé en conditions réelles : même paquet, 62963 → Saint-Étienne *(avant)*, 62964 → **Firminy** *(après)* | |
| 🟢 **C.17** | **LE MONITORING EST AVEUGLE QUAND LE RÉSEAU TOMBE** *(trouvé le 27/08)* · `check_gti_health.py` sonde Vercel, la vitrine, le portail RDV et Supabase **avant** d'arriver à l'étape d'alerte. Réseau coupé → il meurt sur une sonde, journal de **0 octet**, `exit 1`, **aucun email, aucun WhatsApp**. Observé les 25, 26 et 27/08 — à chaque fenêtre de coupure. Le 27/08 il est passé à **05:48, 18 min après l'échec du run de 05:30**, et n'a rien dit. Relancé à la main le même matin il donne le bon diagnostic : `[CRITICAL] GTI Quotidien : dernier resultat 1`. **Il ne sait rapporter que quand tout va bien.** Correctif : envelopper chaque sonde réseau, et alerter **même en échec partiel** | 🟢 **CORRIGÉ le 27/08** · **① l'alerte est SORTIE du `try` d'écriture** — elle était *après* `upsert_status()` dans le même bloc : Supabase injoignable → `upsert` lève → le dispatch n'était **jamais atteint**. Désormais lue-dispatchée-**puis** écrite, chacune dans son `try`. Quand l'état précédent est illisible on alerte **sans déduplication**, en le disant *(mieux un doublon qu'un silence)* · **② `print_report` dans un `finally`** — le diagnostic atteint le disque quoi qu'il arrive en aval · **③ garde-fou `--no-alerts`** : il n'empêche **pas** l'écriture du statut, donc il **consomme la bascule** et fait taire le passage suivant — *(erreur commise le 27/08 au matin ; le bon drapeau est `--dry-run`)*. Un avertissement le dit maintenant · **④ en-tête + pied dans le wrapper** : ⚠ **la cause du journal de 0 octet n'est PAS élucidée** — le `main()` Python ne rend jamais 1, donc le processus était tué de l'extérieur ou ne démarrait pas. L'en-tête rendra les deux distinguables · **banc 4 cas sur 4** + essai réel *(1 897 lignes, code 0)* |
| | ❗ **MESURÉ, PAR TROIS CHEMINS INDÉPENDANTS QUI DONNENT LE MÊME CHIFFRE** : *(a)* GraphQL 61 076 − REST 56 911 = **4 165** · *(b)* somme des totaux par type : 927 actives + 3 238 archivées = **4 165** · *(c)* `hektor_annonce.offre_type` vaut **0 sur les 56 910 lignes, sans exception** — aucune autre n'est jamais entrée | |
| | | **actives · archivées · total** |
| | `0` vente — *tout ce que le run voit aujourd'hui* | 22 424 · 34 487 · **56 911** |
| | `2` location | 621 · 2 248 · 2 869 |
| | `10` vente immo pro | 251 · 782 · 1 033 |
| | `11` location immo pro | 54 · 208 · 262 |
| | `6` neuf · `8` saisonnier | 1 · 0 · 1 |
| | **INVISIBLES** | **927 · 3 238 · 4 165** |
| | ✅ **DÉCISION DE FRÉDÉRIC, 26/08** : le **SERVEUR** reçoit **tous** les types *(61 076)* — il devient réellement le maître. **SUPABASE, LE FRONT ET LES WORKERS** ne reçoivent que **`0` + `10` + `6`** *(57 945, soit +1 034)*. Les locations *(3 131)* restent au serveur et **n'apparaissent pas dans l'app** | |
| | ❗ **ET LES QUATRE INDEX SUPABASE — point relevé par Frédéric, 26/08.** Ce n'est pas « un seau » : les quatre index sont **tous dérivés de `app_view_generale`**, donc **ajouter les types au serveur les ferait partir automatiquement vers Supabase**, locations comprises | |
| | | **la carte du routage** |
| | `app_dossier_current` *(actives)* — `ANNONCES_SCOPE_WHERE` | `archive='0'` ET statut ∈ (`Actif`, `Sous offre`, `Sous compromis`, `Estimation`) |
| | `app_archive_annonce_index_current` | `archive='1'` |
| | `app_historical_annonce_index_current` | `archive='0'` ET statut ∈ (`Vendu`, `Clos`) |
| | `app_brouillon_annonce_index_current` | `archive='0'` ET id ∈ brouillons *(`hektor_annonce_draft_state`)* |
| | ✅ **LA COLONNE EXISTE DÉJÀ** : `app_view_generale.offre_type` vient de `ann.offre_type` *(`view_generale.py:273`)* et vaut **`0` sur les 56 910 lignes**. Le filtre `offre_type IN ('0','10','6')` peut donc être posé **sans rien ajouter à la vue** | |
| | 🔑 **D'OÙ L'ORDRE À RESPECTER, ET IL EST GRATUIT** : poser le filtre **AVANT** d'ouvrir le run. Aujourd'hui `offre_type` vaut 0 partout, donc **le filtre est totalement inerte** — il ne change pas une ligne. Une fois posé, on ouvre le robinet : **il n'existe alors aucun instant où une location peut fuir vers Supabase**. Faire l'inverse, c'est publier 3 131 locations puis courir après | |
| | ⚠ `ANNONCES_SCOPE_WHERE` sert **aussi aux compteurs** *(total_dossiers, total_sans_mandat, total_bloques, total_valides_diffusion…)* : le filtre s'y applique donc d'un seul geste, mais il faut vérifier que c'est bien voulu partout | |
| | ⚠ **PIÈGE À NE PAS RATER** : `reconcile_active_annonce_scope` calcule `known_ids − active_annonce_ids` et **SUPPRIME** la différence *(état, liens contacts, détail brut)*. Si le balayage couvre les six types mais que la réconciliation compare à un seul, **elle effacera les 4 165 à chaque run**. La réconciliation doit être **scopée par type d'offre** | |
| | ✅ **LA SÉQUENCE, EN QUATRE TEMPS — arrêtée avec Frédéric le 26/08. Ne pas intervertir.** | |
| | ✅ **①-a FAIT le 26/08 — LA RÉCONCILIATION TRACE CE QU'ELLE SUPPRIME.** Elle renvoyait déjà la liste des annonces effacées, **et l'appelant l'ignorait** : aucun journal, aucun compteur — **personne ne pouvait dire combien d'annonces disparaissaient chaque nuit, ni lesquelles**. C'est ce silence qui a laissé vivre le défaut. Désormais : table `sync_annonce_scope_purge_log` *(miroir)* + deux lignes au journal du run. **Comportement strictement inchangé**, éprouvé sur banc isolé — **7 attendus sur 7** *(mêmes lignes supprimées, variante `archived` intacte, retour identique, trace écrite, second passage sans effet)* | |
| | ✅ **①-a bis FAIT le 26/08 — DEUX REFUS, ET UN DANGER FERMÉ.** Avec `--max-pages`, le balayage s'arrête tôt et `active_annonce_ids` ne contient qu'une poignée d'annonces : la comparaison portait alors sur presque tout le parc. **Une simple commande de test aurait effacé l'état, les liens contacts et le détail brut de ~22 300 annonces, en silence.** Désormais : refus si le balayage est partiel *(`--max-pages`)*, et refus si le listing rend moins de **50 %** de ce qu'on connaît *(incident Hektor en cours de balayage)* | |
| | ℹ **Le run de nuit ne passe jamais `--max-pages`** *(défaut 0 = sans limite)* : son comportement est **strictement inchangé**. Éprouvé sur banc isolé — balayage partiel → 0 suppression · balayage tronqué → 0 suppression · balayage normal → mêmes 3 suppressions qu'avant, trace écrite | |
| | ✅ **①-b FAIT le 26/08 — ON N'EFFACE PLUS L'ARCHIVE, et c'est tout.** La tâche s'est **réduite** après vérification, et c'est mieux : des trois suppressions, **une seule est irremplaçable**. `sync_annonce_state` se refait à chaque balayage · `sync_annonce_contact_link` se refait par `normalize_source` · mais les charges brutes `annonce_detail` et `mandats_by_annonce` **ne se reconstruisent pas** — il faudrait les redemander à Hektor, or une annonce sortie du listing **ne peut plus y être redécouverte** | |
| | ➡ **C'est exactement ce qui a coûté vos trois annonces** *(62815, 62825, 62855)* : leur détail effacé, il n'en est resté qu'une coquille « [Sans titre] ». **Avec leur détail archivé, `normalize_source` aurait pu les reconstruire entièrement** | |
| | ℹ **Règle 5 au pied de la lettre** : `data/hektor.sqlite` est *« l'archive de tout ce que Hektor a jamais dit »* — 465 155 charges, 3,89 Go. Une archive ne se vide pas parce que la source a changé d'avis. Coût de la conservation : **zéro** *(0 disparition mesurée en 10 h 30)* | |
| | ✅ **Éprouvé, 6 attendus sur 6** : état et liens retirés · **archive intacte** · les 3 détails retrouvables · trace écrite · retour inchangé. Et le message du journal a été corrigé — il annonçait une purge qu'il ne fait plus | |
| | ⚠ **REVIREMENT ASSUMÉ, sur remarque de Frédéric.** J'avais d'abord voulu *« demander à Hektor avant d'effacer »* — c'était **laisser Hektor décider du contenu de notre base**, l'inverse du but. Puis j'ai voulu blinder `prune_annonce_scope` contre une reconstruction du miroir : **inutile aussi**, le miroir est FAIT pour être refait, et j'avais surestimé le dégât *(les charges de détail ne sont pas dans les pages de listing : un rebalayage de 2 847 appels suffit à tout reconstruire)* | |
| | ⏳ ~~①-b — à décider après avoir le chiffre~~ **remplacé par la ligne ci-dessus** : vérifier chaque disparition par un appel `AnnonceById` avant d'effacer, et distinguer « archivée » *(légitime)* de « disparue ». **Sans le volume réel, tout correctif serait posé à l'aveugle** — trois par nuit ne se traite pas comme trois cents | |
| | **① Scoper la réconciliation par type d'offre** — `reconcile_active_annonce_scope` compare `known_ids` au balayage. Tant qu'elle compare six types à un seul balayage, **elle efface les 4 165 à chaque run**. *Vérif : provoquer un balayage partiel et constater **0 suppression**.* | **le préalable absolu** |
| | ✅ **② FAIT le 26/08 — LE FILTRE EST POSÉ, ET IL EST INERTE.** `FILTRE_OFFRE_APP` défini **une seule fois** dans `export_app_payload.py`, appliqué aux **quatre** points : `ANNONCES_SCOPE_WHERE` *(actives + tous les compteurs)* et les trois index *(archives, historiques, brouillons)*, par un marqueur `__FILTRE_OFFRE_APP__` substitué après la définition des requêtes | |
| | ✅ **L'INERTIE EST VÉRIFIÉE, attendu écrit avant** : actives **13 575 → 13 575** · archives **34 487 → 34 487** · historiques **8 800 → 8 800** · brouillons **0 → 0**. Et sur les **56 913** lignes de `app_view_generale`, le filtre en retient **56 913** — **0 exclue**. Il ne peut rien casser aujourd'hui | |
| | ⚠ **Un raté rattrapé en chemin** : j'avais laissé le marqueur `__FILTRE_OFFRE_APP__` dans les trois requêtes **sans rien pour le remplacer** — le SQL aurait été invalide au premier appel. Vu et corrigé avant tout commit, mais c'est exactement le genre d'oubli que seule la vérification attrape | |
| | **② Poser le filtre `offre_type IN ('0','10','6')`** sur les 4 index **et** sur `ANNONCES_SCOPE_WHERE` *(qui sert aussi aux compteurs)*. **Inerte aujourd'hui** : tout vaut 0. *Vérif : après application, les comptes Supabase doivent être **identiques au caractère près** — c'est la preuve de l'inertie.* | gratuit, zéro risque |
| | ✅ **③ FAIT le 26/08 — LA PHOTO D'AVANT EST PRISE, et c'est un outil, pas un relevé.** `phase2/checks/photo_avant_c15.py` : **lecture seule**, il mesure les trois supports d'un coup *(miroir, serveur, Supabase)*, l'enregistre, et **compare automatiquement à la photo précédente** en affichant les écarts. Il se rejoue après chaque palier d'ouverture | |
| | | **les repères du 26/08, avant toute ouverture** |
| | miroir | annonces **56 910** *(offre_type = 0 sur 100 %)* · mandats **24 130** · offres **10 992** · compromis **10 455** · ventes **7 537** · contacts **355 712** |
| | serveur | `app_dossier` **56 913** · `app_view_generale` **56 913** · `app_contact` **355 712** · ledger **28 984** · recherches **76 899** |
| | index | actives **13 575** · archives **34 487** · historiques **8 800** |
| | registre | avec mandat **23 854** · sans mandat **33 059** |
| | statuts | Clos 33 989 · Estimation 12 718 · Vendu 9 095 · Actif 923 · Sous compromis 94 · Sous offre 41 |
| | Supabase | `app_dossier_current` **13 210** · archives **34 487** · historiques **8 800** · brouillons **412** · registre mandats **23 817** · contacts **57 559** |
| | **③ Mesurer l'aval AVANT d'ouvrir** — relever les compteurs de `app_view_generale`, du registre des mandats, des rapprochements et des statistiques. **Tous ont été calculés jusqu'ici sur un parc amputé** ; sans photo d'avant, on ne saura pas distinguer un effet voulu d'une régression. | la photo d'avant |
| | **④ Ouvrir le run, un type à la fois** — commencer par **`offre=6` : UNE seule annonce**, le canari parfait. Puis `10` *(1 033)*, puis `2` et `11` *(serveur seul, 3 131)*. Surveiller le **frein de débit** à chaque palier : notre IP a déjà été bannie une fois. | progressif |
| | ℹ **Ce que ça explique** : les 3 annonces cherchées par Frédéric *(62815, 62823, 62825)* sont des **ventes immo pro**. Elles ne sont pas « tombées » du miroir — elles n'auraient jamais dû y entrer, et n'y sont entrées que par le canal brouillon avant d'être effacées par cette même réconciliation | |
| | ⚠ **À VÉRIFIER AVANT DE CODER** : le volume de détails à rapatrier au premier run *(+927 `AnnonceById` actives)* et le **frein de débit** *(notre IP a déjà été bannie une fois)* · l'effet sur `app_view_generale`, le registre, les rapprochements et les statistiques, **tous calculés jusqu'ici sur un parc amputé** · le sort d'un contact rattaché à une location, absente de Supabase | |
| | ❗ **QUATRE AUTRES ÉCARTS, RELEVÉS LE 26/08 SUR TOUS LES ENDPOINTS DU RUN** — Frédéric : *« as-tu vérifié entièrement mon projet ? »*. Non, je ne l'avais pas fait. Le contrôle complet donne : **mandats +2 279** *(Hektor 26 409 / miroir 24 130)* · **ventes +1 674** *(9 211 / 7 537)* · **offres +116** · **compromis +116** *(le même chiffre des deux côtés — cause commune probable)* | |
| | ➡ **Hypothèse à remesurer APRÈS C.15** : ce sont vraisemblablement les mandats et les ventes des **4 165 annonces absentes** — le mandat arrive par le détail de l'annonce *(`AnnonceById.mandats`)*, donc une annonce absente emporte son mandat. Si les écarts se referment après correction, l'hypothèse était bonne. **Un mandat manquant sur un registre légal n'est pas une nuance d'affichage** | |
| | ℹ **L'agence 20 « Gestion site »** est déclarée par Hektor et **absente de notre miroir** *(nous en avons 19 sur 20)*. Petit, mais net | |
| | ✅ **Écarté avec preuve, sur les annonces** : ce n'est **pas** un problème de périmètre d'agence — la somme par agence égale exactement le total. Le seul filtre en cause est `offre` | |
| | 📌 **Comment ça a été trouvé** : Frédéric a refusé deux fois ma conclusion *(« c'est impossible »)*. La réponse était dans **`notice/Hektor API v2 - Documentation`**, que je n'avais pas ouverte : *« `offre` : 0 vente, 2 location, 6 neuf, 8 saisonnier, 10 vente immo pro, 11 location immo pro »*. J'avais sondé `offredem` — le nom du champ **dans la réponse** — au lieu de `offre`, le paramètre de la **requête**. Même piège que `mandat` / `id_mandat` le matin même | |
| ⏳ **26bis** | **DONNER UN CORPS À L'ANNONCE CÔTÉ SERVEUR** — *décrite depuis le 21/08 dans « LE TROU DE STOCKAGE », **sans jamais avoir de numéro de tâche**. Numérotée le 25/08 pour qu'elle cesse d'être invisible* · **(1)** ✅ **FAITE le 26/08** · **(2)** observer *(en cours)* · **(3)** basculer, collée à C.9 | ⚡ |
| | ✅ **26bis-(1)** — `phase2/identite/annonces_app_seule.py` · table `app_annonce_app_seule` *(accumule, `absent_depuis`, jamais de suppression)* · **branchée dans le run après le contrat d'autorité** · **sous sauvegarde critique**. Relit Supabase **en direct et paginé** *(la copie locale a 22 h de retard à 05:30 — même raison que C.7 ; et PostgREST plafonne à 1 000 lignes : 13 210 annonces lues, pas 1 000)* | |
| | ℹ **SEUL `--recenser` EST BRANCHÉ, PAS `--injecter`.** C'est l'étape (3), elle se décide champ par champ. **Ici on observe** | |
| | ❌ **LE CHIFFRE « 84 colonnes vides sur 130 » EST PÉRIMÉ — corrigé le 28/08.** C.15 a ajouté **33 colonnes commerce** à la vue le 27/08 **sans les ajouter côté Supabase**. La vue fait désormais **163 colonnes**, dont **58** communes avec Supabase : **105 vides**, pas 84. ➡ **l'écart se creuse tout seul à chaque chantier** — c'est l'argument pour trancher maintenant plutôt que « collé à C.9 » | |
| | 🏛 **DÉCOUVERTE STRUCTURELLE DU 28/08 — `--injecter` N'EST PAS LE BON REMÈDE.** La vue n'est **pas** pilotée par le miroir : `FROM app_dossier d` *(table LOCALE, jamais reconstruite)*, et **le miroir n'est qu'une série de `LEFT JOIN`**. **Il n'y a aucun `WHERE`** — d'où l'égalité exacte vérifiée **`app_dossier` 61 094 = `app_view_generale` 61 094**. ➡ pour qu'une annonce née dans l'app existe côté serveur, il suffit de lui donner **une ligne dans `app_dossier` (10 colonnes, écrite UNE FOIS, déjà sous sauvegarde critique)** — et la vue se reconstruit autour d'elle. `--injecter` écrit **163 colonnes CHAQUE NUIT** après le `DROP` de 05:30 : il est **réparateur par construction**, et une nuit ratée = l'annonce disparaît du serveur. **À garder comme filet, pas comme mécanisme** | |
| | ✅ **PROUVÉ EN LECTURE SEULE** *(une CTE masque `app_dossier` par une ligne fabriquée sans numéro Hektor — rien n'est écrit)* : **1 ligne produite, aucun rejet**, et **13 colonnes se remplissent seules** avec des valeurs saines *(`titre_bien` = « [Sans titre] », `internal_status` = `a_qualifier`, `etat_transaction` = `sans_transaction`, `is_blocked` = 0…)*. Une annonce app-seule n'arrive pas « cassée » : elle arrive **neuve, à qualifier** | |
| | 🗺 **LA CARTE DES 163 COLONNES — `notice/CARTE_ANNONCE_NEE_DANS_APP_2026-08-28.md`** : **13** remplies seules · **50** que Supabase détient *(C.7 sait déjà les poser)* · **54** dont le vide est **NORMAL** pour une annonce neuve *(offre, compromis, vente, mandat, commerce : elle n'en a pas encore)* · **46 à trancher**. Et les 46 se décomposent en **37 qui viennent d'UN SEUL blob** *(`app_dossier_detail_current.detail_payload_json`, ~134 clés, dont **l'app en écrit déjà 7**)* **+ 9 champs de listing**. ⚠ **`surface` en premier** : **100 %** du parc, **lue par le front**, et **absente des 71 colonnes Supabase** | |
| | ✅ **Éprouvé** : essai contrôlé avec une annonce fabriquée n'existant que côté app → **posée dans `app_view_generale` avec `hektor_annonce_id` VIDE** *(tout l'objet)* · deuxième injection → **0 doublon** · nettoyage complet. Et **aujourd'hui : 0 annonce dans ce cas**, l'étape est donc inerte | |
| | ❗ **La seule tâche du plan qui devient IMPOSSIBLE si on la remet à plus tard** : le remplissage initial vient du miroir, donc il exige que **Hektor vive encore**. Mesure du 25/08 : `app_dossier` = **56 899 lignes mais 10 colonnes** *(identité pure)*, `app_annonce_champ_app` = **0 ligne**. Le contact et la recherche, eux, ont leur corps *(355 687 et 76 889 lignes)* | |
| | ⚠ **ORDRE IMPÉRATIF** : *« la création app-first écrit dans Supabase. **Sans 26bis, une annonce créée dans l'app n'existe QUE là.** Ce serait creuser le trou pendant qu'on le rebouche. »* Et **l'interrupteur `CHAMPS_APP_ANNONCE` ne peut s'allumer qu'après** — sans corps local, une valeur écrite par l'app n'a nulle part où survivre | |
| | ❌ **CONSTAT DU 26/08 MATIN — RETIRÉ LE MÊME JOUR, IL ÉTAIT FAUX.** J'avais écrit que le lien bien ↔ mandant n'existait que dans le miroir. **C'est faux** : il vit dans `app_contact_relation_current` — **165 474 lignes sur le serveur, 77 376 dans Supabase** — avec `hektor_annonce_id` **et** `app_dossier_id`, le rôle, le numéro de mandat. Vérifié sur notre mandant d'essai : contact 605030 · annonce 62774 · `app_dossier_id` 3828957 · rôle `mandant` | |
| | ⚠ **L'ERREUR DE MÉTHODE, à ne pas refaire** : j'ai conclu à une absence après **trois recherches par nom** (`sync_annonce_contact_link`, `app_annonce_contact_link`, `app_contact_annonce_link`) au lieu de faire l'inventaire des tables. **Une recherche qui échoue ne prouve pas une absence** | |
| | ✅ **CE QUE L'INVENTAIRE A ÉTABLI, LUI** — et le trou en sort **plus précis** : le contact possède **tout** *(`app_contact` identité · `app_contact_current` corps 34 col · `app_contact_relation_current` liens — tous en `CREATE IF NOT EXISTS` + upsert)*. L'annonce possède son identité *(`app_dossier`)* mais **PAS son corps** : `app_view_generale` est en **`DROP TABLE` + `CREATE TABLE AS` inconditionnel, chaque nuit, depuis le miroir** | |
| | ❌ **ET CETTE PHRASE-LÀ AUSSI ÉTAIT FAUSSE — retirée le 26/08.** J'avais écrit que le `DROP` de 05:30 effacerait les 56 913 lignes. **Non** : le miroir **GÈLE, il ne disparaît pas** *(c'est écrit dans l'en-tête de C.6)*. Le fichier reste, la reconstruction reproduit le même contenu. Les annonces existantes gardent leur corps, figé | |
| | ✅ **LE TROU RÉEL, ENFIN CERNÉ.** La machinerie est déjà complète pour les annonces EXISTANTES : le miroir gelé les redonne, et `appliquer_contrat.py` (C.7) **ré-applique chaque nuit ce que l'app détient**, relu dans Supabase. Il ne manque que l'interrupteur `CHAMPS_APP_ANNONCE`. **Ce qui manque vraiment, c'est autre chose** : une annonce **NÉE DANS L'APP** n'a aucune ligne dans le miroir → aucune ligne dans `app_view_generale` → **le serveur ne la connaît pas du tout**. Et C.7 ne sait que *mettre à jour* des lignes existantes, pas en *créer* | |
| | ➡ **Donc 26bis n'est pas « donner un corps à l'annonce »** *(elle en a un)* **mais « rendre le serveur capable de tenir une annonce que le miroir ignore »**. C'est exactement ce que le plan disait depuis le 21/08 : *« sans 26bis, une annonce créée dans l'app n'existe QUE dans Supabase »*. Plus petit, plus net — et toujours à faire avant C.9 | |
| 🟡 **C.19** | **LES CHAMPS DE TRANSACTION APPARTIENNENT À L'APP** *(**ex-tâche 13**, « la modale de statut »)* — **retrouvée le 28/08, elle avait disparu au renumérotage** · **étapes 1-2-3 FAITES le 29/08** · reste l'étape 4 | **1 à 2 j** |
| | ✅ **ÉPROUVÉE CONTRE UN VRAI RUN DE NUIT, pas seulement à la main.** Journal du 29/08 : *06:14:20 refresh views* **détruit et refait la vue** → *06:19:44 affaire ledger refresh* **relit le registre depuis Hektor** → *06:19:45 magasin* « 2 saisies lues » → *06:19:47 contrat* « **1 dans le ledger, 1 dans Supabase, 2 dans la vue** » → *06:19:47 push*. **Les trois étapes qui devaient effacer la correction l'ont effacée, les deux nôtres l'ont reposée, et le push est parti avec la bonne valeur** | |
| | 🧱 **CE QUI EST POSÉ** : ① `app_affaire_champ_app` des deux côtés, rangée par **`app_affaire_id`** *(l'identité du 20/08, pas le numéro Hektor — sinon on reconstruisait la dépendance qu'on venait de retirer)* ; ② `CHAMPS_APP_AFFAIRE` **10 champs** + `appliquer_contrat_affaire.py`, branchés au run ; ③ la RPC `app_edit_affaire_optimistic` *(garde-fous éprouvés : `affaire_not_found`, `not_allowed`)* et le bouton **« Corriger sans envoyer à Hektor »** dans la modale | |
| | ⚖ **DIX CHAMPS ET PAS TREIZE, délibérément.** `jours_retractation` → `compromis_date_end` est une **date**, pas un nombre ; `notaire_id` → `vente_notaires_resume` est un **résumé de noms** ; `jours_validite` n'a **aucune colonne**. Les y ranger rendrait la donnée fausse. Et l'**acquéreur** est écarté pour une autre raison : changer qui achète n'est pas une correction, c'est une autre affaire | |
| | 🔧 **DEUX DÉFAUTS TROUVÉS EN PRÉPARANT L'ESSAI** — et c'est l'essai qui les a fait voir, avant qu'ils ne coûtent quoi que ce soit. ① **l'ordre du run** : mes étapes tournaient **avant** `affaire_ledger.py`, qui relit Hektor et reposait sa valeur par-dessus — la correction survivait dans la vue et disparaissait du registre ; ② **le push** : `affaire_ledger.py --push` envoie à Supabase juste avant, donc le serveur aurait eu la correction et l'app non. Le contrat repose désormais lui-même ses corrections en ligne, en **écriture bornée** aux affaires corrigées | |
| | ⏳ **ÉTAPE 4, À FAIRE** : les trois gestes vers Hektor — **refuser/accepter une offre** *(`annonce-SuiviVente-updateOffre`, `id` + `type`)*, **annuler un compromis** *(`annonce-SuiviVente-clotureCompromis`, `idComp` + `isCloture`)*, **supprimer une vente** *(`ventes-deleteVente`)*. Préalable : **confirmer le compte** — l'admin est refusé pour *saisir* une offre, mais les boutons refuser/accepter sont bien présents en session admin | |
| | 🧹 **TRACE D'ESSAI À RETIRER EN FIN DE CHANTIER** *(décision de Frédéric, 29/08 : on la garde jusque-là)*. **Affaire 9** — une vente sur l'annonce **29**, archivée — porte **123 456** au lieu de **79 000**, et un `prix_net_vendeur` de **111 111**. C'est un **faux prix dans les données** tant qu'il est là. L'état d'avant est conservé dans `notice/ESSAI_NUIT_C19_2026-08-29.json`. ➡ pour l'effacer : `python phase2/identite/verifier_essai_nuit_c19.py --restaurer` | |
| | 📌 **COMMENT ELLE A ÉTÉ RETROUVÉE.** Frédéric : *« je pensais avoir déjà fait les tables transactions sur l'app, contrôle »*. **Il avait raison.** Le patch `patch_identite_transactions_2026-08-20.sql` renvoie explicitement à *« la tâche 13 (saisie directe dans l'app) »*, et la fiche **1.4** du plan dit *« Débloque la modale de statut (tâche 13) »*. Or la table de correspondance des anciens numéros donne ex-19, ex-23/24/25, ex-26, ex-29, ex-31 — **aucun ex-13**. La tâche a été **perdue**, alors que son socle était posé | |
| | ✅ **LE SOCLE EST FAIT ET SAIN** *(20/08, vérifié le 28/08)* : `app_affaire_ledger` — **29 293 lignes, 29 293 numéros distincts, 0 sans numéro**. `app_affaire_id` en clé primaire *(**une seule série** pour offre/compromis/vente — Hektor tient trois compteurs qui se télescopent, **7 541 numéros portés par deux types**)*, `hektor_annonce_id` et `hektor_affaire_id` rendus **facultatifs**, triplet Hektor en **index unique PARTIEL** pour la réconciliation, et une **sentinelle** `app_affaires_sans_numero_hektor` branchée au moniteur, **seuil 0** | |
| | 🎯 **CE QUE LA TÂCHE EST, précisée par Frédéric le 28/08** : *« tous les champs de la modale changer statut doivent pouvoir se modifier dans l'app puis le serveur **sans envoyer à Hektor** — sauf refuser/accepter pour l'offre, annuler pour le compromis, supprimer pour la vente »*. ➡ **les VALEURS restent chez nous, seuls les CHANGEMENTS D'ÉTAT partent**. Et cela **contourne l'obstacle** trouvé le même jour : modifier un compromis chez Hektor passe par un module ES impilotable — **on ne le modifie plus chez lui** | |
| | 🧱 **CE QU'IL RESTE À CONSTRUIRE** : ① un **magasin durable** des champs d'affaire, au grain `app_affaire_id` — **patron éprouvé le 28/08** sur `mandat_date_cloture`, de bout en bout ; ② `CHAMPS_APP_AFFAIRE` dans le contrat d'autorité, avec la règle déjà validée *« l'app gagne seulement quand elle a quelque chose à dire »* ; ③ les champs éditables à l'écran, hors changement d'état. **12 des 13 champs de la modale existent déjà** comme colonnes de `app_view_generale` — seul *« jours de validité de l'offre »* manque | |
| | ⚠ **LA CONSÉQUENCE À ASSUMER, dite à Frédéric et confirmée par lui** : un prix corrigé chez nous et pas chez Hektor **diverge définitivement**. C'est le but — nos chiffres deviennent les bons — mais **tout reporting encore lu dans Hektor affichera l'ancienne valeur** | |
| 🆕 **C.4-bis-0** | **VÉRIFIER LA DÉTECTION, WORKER PAR WORKER — préalable au filet** *(29/08)* | **1/2 j** |
| | ❗ **ON NE REJOUE PAS CE QU'ON NE SAIT PAS RATÉ.** Un travail marqué `done` n'est **jamais** repris. Poser C.4-bis avant cette vérification, ce serait tendre un filet sous un trou qu'on ne voit pas | |
| | 🔬 **PROUVÉ PAR UN ESSAI, pas déduit.** Le 29/08, un refus demandé sur une offre **inexistante** *(99999999)* est passé **`done`**, l'état optimiste est resté affiché, et le retour en arrière n'a jamais joué. **Le geste n'a rien fait et l'app affichait le contraire.** Relevé chez Hektor sur le même appel : **`[]` = échec · `1` = succès** — *il DIT quand il échoue*. Mon détecteur ne cherchait que des mots de refus et concluait au succès en leur absence | |
| | ⚖ **LE PRINCIPE, désormais posé sur les 3 gestes** *(`2b55a37`)* : **on exige la PREUVE du succès, on ne le déduit jamais de l'absence d'échec.** Une réponse vide, `[]`, `{}`, `0` ou `null` lève une erreur explicite | |
| | ✅ **RÉVISION DU 01/09 — C'ÉTAIT DÉJÀ FAIT. 18 handlers sur 20 exigent la preuve** *(mesuré en suivant les fonctions appelées sur deux niveaux)*. Les **2 restants** sont `handleRelanceSignature` et `handleCancelSignatureProcedure` : ils envoient l'ordre puis rendent `reminded`/`cancelled` sans vérifier. **Gelés avec A.2** — ils dépendent de l'abonnement ImmoSign et disparaîtront avec le contrat de signature en propre. ➡ **C.4-bis n'est plus bloqué.** *(Et ma 1ʳᵉ passe n'en voyait que 15 : la preuve est souvent dans la fonction APPELÉE — 5ᵉ mesure fausse par recherche de motif, l'avertissement ci-dessous était juste)* |
| | ⚠ **UN SECOND SENS, non prévu par la tâche** *(31/08)* : elle ne cherchait que « déduire du silence » *(un échec pris pour un succès)*. Le cas symétrique existe — **« relire à l'aveugle »**, un succès pris pour un échec, et le filet rejouerait alors un geste déjà fait. Constaté sur le rattachement de mandant du 28/08. **Chercher les DEUX sens en posant C.4-bis** |
| | ➡ ~~**RESTE : les 18 handlers qui parlent à Hektor, un par un, EN LISANT le code.**~~ Pas par recherche de motif — cette méthode m'a donné **quatre mesures fausses le 29/08**, dont une qui disait aveugle un handler qui vérifie bien *(`handleUpdateHektorContactSearch`)*. Seul indice à confirmer : `handleRelanceSignature` ne semble vérifier que son message d'entrée | |
| 🆕 **C.4-bis** | **AUCUNE ACTION N'EST JAMAIS REJOUÉE** — le filet des éditions n'existe pas pour les gestes *(validé par Frédéric le 29/08)* | **1 à 2 j** |
| | 📊 **MESURE DU 29/08** : **6 travaux en erreur, 0 rejoué**, sur six types différents — création d'annonce, numéro de mandat auto, lien mandant, changement de statut, refus d'offre, relecture. Le `attempt_count` reste à **1** partout. Un « Hektor 500 » du 28/08 n'a jamais été retenté, et personne ne l'a su | |
| | ⚖ **LA DIFFÉRENCE DE TRAITEMENT, mesurée.** Les **éditions de champs** ont un filet complet : un balayage tourne **toutes les minutes** *(cron `app-annonce-push-due`, `app-contact-push-due`, `app-search-push-due`)*, il **nettoie** ce qui a abouti, **rejoue** ce qui a raté avec un espacement croissant *(5 · 10 · 15 · 20 · 25 min)*, et **abandonne après 5 tentatives** en posant `conflict` — un humain tranche alors. C'est C.1' : *« la purge des 24 h est retirée, la saisie reste jusqu'à ce qu'un humain la traite »*. Les **actions**, elles, n'ont **rien** | |
| | 🎯 **CE QU'IL FAUT CONSTRUIRE** : une file `app_affaire_pending` sur le modèle des trois autres · un balayage à la minute, même espacement, même abandon à 5 · un bandeau sur la fiche. **Périmètre : les trois gestes de transaction ET le changement de statut** *(demande de Frédéric)* — et les autres actions suivront, puisque le trou est le même | |
| | ⚠ **UN CHOIX DE CONCEPTION, TRANCHÉ PAR FRÉDÉRIC LE 29/08** : aujourd'hui, quand Hektor refuse, le worker **remet l'état d'avant**. Avec un rejeu, ce sera l'inverse — **on garde l'état affiché et on réessaie en arrière-plan**, comme une édition qui attend. Contrepartie assumée : pendant **jusqu'à 25 minutes**, l'app peut montrer un état que Hektor n'a pas encore. C'est le prix de « rien ne se perd », et c'est cohérent avec C.1' | |
| ⏳ **C.9** | La **création** part de l'app *(ex-23,24,25)* | **1 à 2 sem.** — après C.7 |
| | ℹ *Le patron « naître sans numéro Hektor » est **déjà dans le schéma** — `app_dossier.id` autoincrement + `hektor_annonce_id` **nullable** + UNIQUE. Il n'a jamais servi (0 ligne sur 56 894) : la création optimiste est derrière un drapeau éteint. C'est ici qu'il s'exerce pour la première fois* | |
| 🟡 **C.13** | **LA CLÔTURE DE MANDAT DANS L'APP** — *réécrite le 28/08 : elle ne passe plus par Hektor* · `PLAN_DEV_MANDAT_CLOTURE.md` | **a et b FAITS · c en fin de plan** |
| | 🔴 **LE DÉFAUT SILENCIEUX, trouvé le 28/08 au soir en préparant la branche « Vendu » de C.4 — et c'était du code posé le matin même.** La clôture locale modifiait `app_mandat_register_current`. **Elle n'écrivait rien**, pour deux raisons mesurées : ① **le registre est FILTRÉ SUR LE STATUT de l'annonce** — une annonce qui passe à *Clos* ou *Vendu* en **sort**, donc la ligne disparaît au moment précis où l'on veut y poser la date *(annonce 62966 : **0 ligne** ; et **642 des 1 105** mandats absents du registre le sont « parce qu'ils sont clos »)* ; ② **le registre est VIDÉ PUIS REFAIT** à chaque push *(`push_upgrade_to_supabase.py:1126`, `delete_all_rows`)*. ⚠ **Et une modification PostgREST qui ne correspond à AUCUNE ligne renvoie 200** : le travail annonçait `done`, le journal disait « mandat clôturé », **et rien n'était écrit** | |
| | ✅ **CORRIGÉ — `ce57749`.** **①** table `app_mandat_champ_app` **dans Supabase** — à part, **jamais reconstruite**, RLS fermée *(service_role seul)*, clé **(annonce, NUMÉRO de mandat, champ)** parce que **le numéro est ce que le worker DÉTIENT** *(le payload du front ne porte jamais l'identifiant Hektor)*. **C'est le patron éprouvé quatre fois** — `app_dossier`, `app_affaire_ledger`, `app_search_registry`, `app_contact`. Retour arrière : `DROP TABLE`. **②** la clôture y écrit avec `return=representation` et **refuse de dire `done` si aucune ligne ne lui est rendue**. **③** `magasin_mandat_app.py` lit une **seconde source** — ce que l'app a écrit — résout numéro → identifiant par le miroir, et **refuse de trancher quand l'index est ambigu** plutôt que deviner *(Hektor réutilise ses identifiants : 342 sont partagés entre annonces)* | |
| | ✅ **ÉPROUVÉ DE BOUT EN BOUT, SANS TOUCHER À HEKTOR** *(annonce de test 62966, mandat 660, numéro 18842)* : écriture vérifiée *(PostgREST rend bien la ligne, **y compris sur upsert** — donc pas de faux échec sur une re-clôture)* → magasin : *« SAISIES DE L APP reprises : 1 »* → contrat : *« 1 ligne arbitrée en faveur de l'app »* → `app_view_generale` : **`mandat_date_cloture` = 2026-08-28** → **miroir Hektor : clôture toujours VIDE**. **Le mandat est clos chez nous et Hektor n'en sait rien — c'est exactement l'objectif.** Comportement existant inchangé : les **3 mêmes écarts** observés qu'avant | |
| | ℹ **CE N'EST PAS LE REGISTRE DES MANDATS.** Confusion que j'ai moi-même introduite le 28/08 en proposant *« créer une table »* sans dire que je commençais **A.3-technique** par la petite porte — **Frédéric m'a arrêté, à raison**. Ceci est le magasin d'**UN champ**, l'équivalent exact des **trois champs de contact** *(`birth_date`, `birth_place`, `marital_status`)* qui tournent depuis des semaines. Le registre reste **en fin de plan, avec A.1 et A.2** | |
| | ❌ **DEUX PHRASES DU CADRAGE SONT FAUSSES, vérifiées le 28/08.** Le document dit « dev non commencé, rien de codé » : or le commit `1b6ef04` du **30/07** a livré A1, A2, A3, A5 et A7 — le plan a été écrit *dans le même commit que le code*, puis jamais relu. Et le drapeau `VITE_APP_MANDAT_CLOTURE_ENABLED` **n'existe nulle part** : le front n'en connaît que quatre. **Ce chemin est donc ACTIF en production depuis le 30/07.** | |
| | ℹ **La clôture a déjà tourné pour de vrai**, deux fois le 30/07 *(mandat 9887, trace dans le miroir : `date_cloture = 2026-07-30`)* — mais les deux fois sur l'annonce **24113**, l'une des rares à DEUX mandats. Le cas normal n'avait jamais été essayé, et le commit du 25/08 le disait : *« NON VÉRIFIÉ, assumé : une vraie clôture »* | |
| | 🔴 **LE DÉFAUT, prouvé en lecture seule le 28/08** *(annonce 62933)* : sur une annonce à mandat unique Hektor ne rend **aucune `<option>`** — il propose la cible par un `<input type="hidden" id="selectedMandatId" value="646" data="protexaMandat">`. Le worker ne lisait que les `<option>` : il refusait donc de clôturer sur **7 668 des 7 760** annonces actives portant un mandat — **98,8 %** | |
| ✅ | **Les quatre correctifs, faits le 28/08** *(`f1d2ac2`)* — ① le contexte lit aussi le champ caché · ② le mandat unique n'est accepté **que si** Hektor et le registre concordent *(divergence → refus : le 28/07, une fiche pointait encore l'ANCIEN mandat)* · ③ la vente survit à une clôture ratée *(elle était dans un `try…finally` **sans `catch`** : la vente partait chez Hektor et le job tombait après)* · ④ `selected_mandat` est enfin lu. **Et l'asymétrie est refermée** : la fonction *fabriquait* une cible que Hektor n'avait jamais proposée, sur une opération irréversible. **16 cas sur 16** | |
| | ⚠ **Ce qui reste inexpliqué, et n'a plus à l'être** : l'enregistrement rend un **500** sur la famille PROTEXA *(le mandat 660 de l'annonce de test 62966)*. Quatre pistes éliminées avec preuve — l'appel « à froid » *(l'archivage fait pareil, 127 fois sans échec)*, le `reportingId` manquant *(absent des deux pages, Hektor l'enverrait vide aussi)*, un point d'entrée PROTEXA dédié *(aucun)*, la précédence de `typeMandat` *(la bonne valeur était partie)*. **Le virage du 28/08 rend ce correctif sans objet** | |
| ✅ **C.13-a** | ~~**LE DOMICILE DU MANDAT**~~ **FAIT le 28/08** — `app_mandat_champ_app`, table à côté, jamais reconstruite. **La clé a été MESURÉE, pas choisie** : `(annonce, hektor_mandat_id)` est la seule unique — 24 939 sur 24 939, quand `(annonce, numéro)` collisionne 157 fois et le numéro seul 6 803 fois. Premier passage : **23 830 couples comparés, 0 mandat introuvable dans le miroir** | **FAIT** |
| | ℹ **Pourquoi `app_annonce_champ_app` ne pouvait pas suffire** : il est clé par annonce, or une annonce porte plusieurs mandats dans sa vie *(24 939 mandats pour 24 657 annonces)*. Au grain de l'annonce, on ne saurait pas QUEL mandat est clos | |
| ✅ **C.13-b** | ~~**LE CONTRAT S'ALLUME**~~ **FAIT le 28/08** — `CHAMPS_APP_MANDAT = ("mandat_date_cloture",)`. **C'est le premier champ jamais inscrit à ce contrat** : la liste était vide depuis l'origine, et c'était l'interrupteur du chantier | **FAIT** |
| | 🔑 **Pourquoi ce champ d'abord.** La réserve du contrat — *« inscrire un champ ici le FIGERAIT sur une valeur périmée »* — ne s'y applique pas : Hektor ne porte une date de clôture que **94 fois sur 24 939 (0,4 %)**, quand il renseigne les dates, le montant et le type à ~100 %. C'est un champ que l'app **crée**, pas un champ qu'il entretient — et son rythme s'effondre : 24 clôtures en juin, 7 en août | |
| | ⚠ **LA RÈGLE DIFFÈRE DE CELLE DES CONTACTS** *(arbitrage de Frédéric, 28/08)* : **l'app gagne quand elle a quelque chose à dire ; sinon on ne touche à rien.** Le contrat des contacts applique « l'app gagne » sans condition, et c'est sans danger — Hektor ne connaît pas ces champs. Ici il en connaît 94, et **le tout premier passage du magasin en a trouvé trois que Supabase ignore** *(30673/12264, 61513/74415, 61521/74417)*. Un « l'app gagne » aveugle les aurait **effacées dès la première nuit, en silence** | |
| | ✅ **Éprouvé** : à vide *« aucune valeur détenue par l'app »* · avec un témoin factice *« 1 valeur à poser »*, les 3 clôtures de Hektor toujours écartées · témoin retiré, vue intacte. Les deux étapes tournent chaque nuit **après** la reconstruction de la vue, pour la même raison que le contrat d'annonce | |
| | ℹ **Le dernier câblage reste à faire** : le constructeur du registre lit la clôture **uniquement** dans `mandats_json`. Tant que l'app n'en produit aucune, ça ne change rien — c'est le premier geste de **C.13-c** | |
| ⏳ **C.13-c** | **LE RATTRAPAGE DES 23 715** — *reporté **EN FIN DE PLAN**, avec A.1/A.2/A.3 (décision de Frédéric, 28/08)* | **plus tard** |
| | **Les trois règles, formulées par Frédéric** — `vente enregistrée → date de la vente` · `date butoir dépassée → date d'échéance` · `annulation acceptée → date saisie` · *le reste : à trancher*. **Aucune des trois dates ne vient de Hektor** : le ledger d'affaires porte 7 605 ventes, **100 % datées et 88,4 % rattachées à un mandat précis** ; `date_fin` est renseignée à 92,3 % ; les annulations acceptées sont dans `app_diffusion_request` | |
| | ⚠ **Pourquoi en fin de plan et pas maintenant** : c'est une écriture de masse sur 23 715 lignes. Réversible puisque rien ne part chez Hektor, mais elle fixe le registre qui fera foi — elle se décide quand l'app est le maître, pas pendant la cohabitation | |
| | ❗ **ENQUÊTE DU 25/08 — le cadrage était incomplet, et sa portée est de 91 %.** Le formulaire de clôture a **deux visages** : avec plusieurs mandats il affiche un `<select>` ; **avec un seul, AUCUNE option** — tout est dans un `<input>` caché `selectedMandatId` *(valeur **et** attribut `data`)*. Le worker ne sait lire que des `<option>` : il **refuse de clôturer** sur **694 annonces actives sur 759**. Et sur les **98 clôtures réelles du parc, 74 portent sur une annonce à mandat unique** | |
| | ℹ **Pourquoi personne ne l'a vu** : tout le cadrage du 30/07 a été relevé sur **l'annonce 24113**, l'une des rares à deux mandats *(ses mandats 9887/553 sont les exemples du document)*. Et son sous-lot **A0** — *« verrouiller le format exact, en lecture seule, sans coder »* — **n'a jamais été produit** ; A1 a été codé le même jour | |
| | ✅ **A0 EST FAIT (25/08)**, lu dans le JavaScript de Hektor : `mandatFrom = '#selectedMandatId'` **par défaut**, la liste ne prime que si elle existe ; `idMandat = .val()` · `typeMandat = .attr('data')` ∈ `mandat` \| `protexaMandat`. ⚠ **Faux ami** : `typeMandat` est la **famille de registre**, PAS le type juridique — et le code laisse `payload.type_mandat` passer **avant** Hektor : piège armé | |
| | ⚠ **Asymétrie à refermer** : la branche « l'app fournit l'identifiant » **fabrique** une cible sans vérifier que Hektor la propose ; l'autre branche, elle, refuse. **La clôture est IRRÉVERSIBLE côté Hektor** | |
| | ❗ **Ce chantier existait et n'était cité NULLE PART dans ce plan** — 20ᵉ note orpheline, trouvée le 25/08 en cherchant autre chose. Les déclencheurs, les motifs Hektor et les arbitrages sont **verrouillés depuis le 30/07** | |
| | ✅ **Sa source est désormais prouvée** : le formulaire Hektor cible le mandat par son **ID INTERNE**, et la mesure du 25/08 établit que `mandat_source_id` **EST** `hektor_mandat_id` — **23 814 / 23 814**. Le registre peut donc remplacer la liste déroulante de Hektor le jour où elle disparaît | |
| | ℹ **Rappel de l'arbitrage** : un mandat **échu reste « en cours »**, il n'est PAS clos automatiquement — seule une **alerte négo** part. C'est pourquoi **22 749 mandats sont échus et non clos, et 85 seulement portent une date de clôture** : ce n'est pas un défaut, c'est la règle | |
| ✅ **C.14** | ~~**Le titre français côté serveur, et le calque lu par l'en-tête**~~ **FAIT le 25/08** — `view_generale` préfère l'entrée **française** au lieu de `$[0]` *(qui prenait le premier bloc quelle que soit sa langue)* · `optimisticOverlayValue()` branché sur l'en-tête **et** le fil d'Ariane | **FAIT** |
| | ℹ **Portée re-mesurée le 25/08 au soir** *(mon chiffre de l'après-midi, « 3 annonces », était approximatif)* : sur **13 475 annonces actives**, **701** avaient un `texte_principal_titre` faux *(686 vides)* — et **1 seule** avait son titre **visible** affecté. Les 701 comptent quand même : le front lit `texte_principal_titre` **en premier** pour le titre de la rubrique « Le Bien » et l'en-tête du bloc descriptif | |
| | ⏳ **C.14-bis, petit, non urgent** : le front a **son propre repli** avec le même défaut — `api.ts:4097` prend `textBlocks.find(item => item.html \|\| item.text)`, **le premier bloc quelle que soit sa langue**. Ne se déclenche que si le champ arrive vide, donc rare après C.14 — mais faux quand il sert | |
| | Le calque (`app_optimistic_overlay`) **contient bien** le champ modifié, titre compris — vérifié en base. La **rubrique** le lit et affiche la nouvelle valeur. Mais `App.tsx:22527` fait `const heroTitle = dossier.titre_bien || …` : **l'en-tête, le fil d'Ariane et le bandeau lisent la colonne en direct**. Résultat : *la fiche se contredit elle-même* — nouveau titre dans la rubrique, ancien titre partout ailleurs | |
| | ℹ **Ce n'est pas une régression du calque** : c'est un composant **jamais raccordé**. Le cockpit V2 est arrivé après *(17/07)* et son en-tête lit la donnée comme le faisait l'ancienne fiche. La note `calque-cles-hektor-vs-front` porte déjà la trace du chantier « overlay-first », branché écran par écran | |
| ⏳ **C.11** | Ménage des tables mortes *(ex-19)* | |
| ✅ **E.0** | ~~**AUDIT : que ne peut-on PAS faire dans l'app ?**~~ **FAIT le 25/08** — `ETUDE_OU_EN_SOMMES_NOUS_2026-08-25` | **FAIT** | **31 types de travaux éprouvés, 0 erreur sur 54 737.** Quatre manques, et **un seul est du code** |
| | ❌ **CONCLUSION CORRIGÉE LE 25/08 PAR FRÉDÉRIC.** J'avais écrit que le bridage admin *(passer une offre, un compromis, une vente)* était le manque qui sépare de l'étape 2. **C'est FAUX : ce bridage est VOULU.** Le négociateur ne décide pas seul — il fait une **demande de validation** à l'admin. Le circuit existe et il est éprouvé : `demande_diffusion` · `demande_baisse_prix` · `demande_annulation_mandat`, **9 demandes, 8 acceptées et traitées** | |
| | ✅ **Ce qui reste avant l'étape 2 n'est donc PAS du code** : créer la dizaine de comptes manquants *(5 actifs, dont 2 commerciaux)*, éprouver la création de mandat, et **s'en servir soi-même une semaine** | |
| | ℹ Et trois manques qui **ne sont pas du code** : **5 comptes actifs** dont 2 commerciaux pour une douzaine de négociateurs · la création de mandat **éprouvée une seule fois** · et l'usage réel par Frédéric, sans lequel tout est mesuré sur une app que personne n'exerce | |


#### 🔌 LES INTERRUPTEURS — « construit » ne veut jamais dire « actif »

| Tâche | Constructible maintenant | Ce qui attend |
|---|---|---|
| **C.2b** · **C.11** · **C.12** | oui, entièrement | **rien** — additif |
| **C.6** | oui, en doublure | qui **lit** la table |
| **C.8** | oui | le calque, côté front |
| **C.9** | oui, derrière drapeau | le drapeau |
| **C.7** | oui, **contrat vide** | ⬇ **la liste des champs app** |
| **C.4** | oui, worker par worker | ⬇ **la liste des champs app** *(les 3 arbitrages)* |

**Il n'y a donc qu'UN interrupteur de fond, et deux tâches le partagent.**

#### 🗝 LA LISTE DES CHAMPS APP — le seul vrai interrupteur

*Elle existe déjà. Elle fait trois lignes. Elle marche.*

```
   phase2/sync/push_contacts_to_supabase.py:476
   APP_OWNED_CONTACT_FIELDS = ("birth_date", "birth_place", "marital_status")
```

Le commentaire du code dit pourquoi ce sont ceux-là : *« Hektor ne les renvoie **jamais**, seule
l'app les écrit »*. **Il n'y a rien à arbitrer : Hektor n'a rien à dire.**

**À quoi elle sert.** Aujourd'hui, tout ce que l'app écrit doit faire l'aller-retour par Hektor
pour survivre — `app → worker → Hektor → import de nuit → retour`. Si un maillon casse, l'import
ramène la valeur de Hektor et **la saisie est remplacée**. La liste, c'est ce qui permet à une
valeur de **survivre sans l'aller-retour**.

| | Hektor connaît le champ ? | Faut-il décider ? |
|---|---|---|
| **les 3 qui marchent déjà** | **non** | non — personne à contredire |
| **les 189 de la carte A1** | **oui** | **oui, pour 3 d'entre eux** |
| **côté ANNONCE** | — | ⚠ **aucune liste n'existe** *(vérifié le 24/08)* |

> ❗ **Le point qui change la nature des 3 arbitrages.** Le jour de la coupure, Hektor n'existe
> plus : **il n'y a plus rien à arbitrer, l'app gagne tout.** Donc `statut_annonce`,
> `negociateur_email` et les champs de mandat ne sont **pas** trois décisions de fond sur le
> métier. Ce sont **trois réglages de transition**, réversibles, qui ne valent que pendant la
> cohabitation — et qu'on peut laisser à « Hektor gagne » aussi longtemps qu'on veut.

#### SUPPRIMÉ le 24/08 — rendu sans objet par l'étape 2

| | | |
|---|---|---|
| ~~**C.1**~~ | ~~la règle d'arbitrage, ses 3 cas d'écart, sa tolérance de comparaison~~ | le cas ③ disparaît |
| ~~**la notification de conflit**~~ | ~~unifier les 3 objets~~ | il n'y aura plus de conflit à notifier |
| ~~**C.10**~~ | ~~corriger le modèle « au moins » de la modale recherche~~ | **une fois la porte fermée (C.3), l'app n'a plus à exprimer ce que Hektor comprend** |
| ~~**5a**~~ | ~~renommer seul les 11 paramètres ambigus~~ | **RAYÉE le 20/08** — Postgres refuse le rename, l'appel se fait par NOM |

---

### BLOC D — RAPATRIER LES FICHIERS · *irréversible*

| | Tâche | |
|---|---|---|
| ⏳ **D.1a** | **MESURER d'abord** — combien de `cloud_available` n'ont pas de fichier local ? | **1 heure.** L'audit du 22/08 a montré que la tâche est bien plus petite qu'annoncée |
| ⏳ **D.1** | **Documents** — ~~40 493~~ **à redimensionner** : 44 512 indexés, dont **22 491 déjà `local_only`** et 22 021 `cloud_available` ; et **46 359 fichiers, 65,6 Go déjà sur le disque** — donc une part du cloud est déjà là | ⚠ avec le frein anti-bannissement, et **sans JAMAIS rejouer les annonces déjà en échec** |
| ⏳ **D.2** | **Photos** — 1 397 | ⚠️ |

---

### BLOC E — COUPER

| | Tâche | |
|---|---|---|
| | → **E.0 est passée en PISTE 1** *(24/08)* — si l'on construit tout maintenant, il faut savoir **maintenant** ce que l'app ne sait pas faire, sinon on bâtit six semaines et on découvre le trou à la fin | |
| ⏳ **E.1** | **19-R2 — RATTRAPAGE, LA VEILLE DE LA BASCULE** | ⚠️ **dernière occasion.** Après, plus personne ne crée de recherche dans Hektor |
| ⏳ **E.2** | **BASCULE DES NÉGOCIATEURS SUR L'APP** *(ex-19bis)* | **décision d'organisation** — c'est elle qui débloque tout le bloc recherches |
| ⏳ **E.3** | Les workers deviennent invisibles *(ex-26)* | une fois l'avertissement éprouvé |
| ⏳ **E.4** | Le jour J — le distributeur démarre à 100 000 · le serveur remplit **les deux cases** · le numéro est **imposé** · on éteint l'aspirateur *(ex-32→35)* | |

---

### BLOC F — APRÈS LA COUPURE · *rien d'urgent, mais à ne pas perdre*

| | Tâche | |
|---|---|---|
| ⏳ **F.1** | **UTILISATEURS, RÔLES ET DROITS** — revoir qui peut faire quoi | *après la coupure, décision de Frédéric le 25/08* |
| | **Aujourd'hui le modèle est délibérément serré** : trois profils *(admin, commercial, administratif)*, et le négociateur **demande** au lieu de décider — baisse de prix, diffusion, annulation de mandat. **C'est un contrôle voulu, pas une limite technique** | |
| | Ce qu'il faudra reprendre alors : le périmètre de chaque rôle, ce qui reste soumis à validation, et ce qui peut s'ouvrir | |

---

### 📒 LE REGISTRE DES MANDATS SERA-T-IL EXPLOITABLE APRÈS LA COUPURE ?

*Question de Frédéric, 28/08. Mesurée sur les 26 729 lignes de registre.*

**Oui — l'ossature est là, et rien n'en dépend de Hektor pour survivre.** Elle est déjà
dans la base, clé par le couple (annonce, mandat), sous sauvegarde critique.

```
   Numero du mandat      100,0 %      Date de prise      92,3 %
   Designation du bien   100,0 %      Date de fin        92,3 %
   Prix                  100,0 %      Nom des mandants   92,1 %
   Agence                100,0 %      Honoraires         91,5 %
   Adresse                99,2 %      Type de mandat     87,8 %
   Commune                98,4 %
   ------------------------------------------------------------
   Negociateur            42,9 %   <-- 3 318 lignes ACTIVES sans negociateur
   Date de cloture         0,3 %   <-- C.13
```

**Trois trous, et un seul a une échéance :**

| | après la coupure |
|---|---|
| **date de clôture** | ✅ se calcule chez toi — c'est C.13-c |
| **négociateur** | ❌ **si la donnée est chez Hektor, elle part avec lui** |
| **collisions de numéros** | ⚠️ se corrige chez toi, mais mieux vaut savoir avant |

> ⚠ **Le trou du négociateur ne se rattrapera plus après la coupure** — c'est le seul
> des trois dans ce cas. Mais **ce n'est PAS une priorité** *(décision de Frédéric,
> 28/08)*. Signalé pour qu'il ne se perde pas, à traiter quand le reste sera fait.

**Sur les numéros** : 6 803 numéros servent à plusieurs mandats, mais un registre se
tient **par agence**. Au bon grain : 4 090 doublons s'expliquent par des agences
différentes, 39 par les **deux registres** de Hektor *(HEKTOR et PROTEXA, qui n'écrivent
même pas les clôtures au même format — `2026-08-26 10:26:42` contre `2026-08-25`)*, et
il reste **663 vraies collisions** — 3,7 %, surtout des reprises anciennes *(le n°10249
sert dix fois, même agence, même jour de 2016, sur dix annonces consécutives)*.

*Réserve : je peux dire ce que contiennent les données ; dire si elles satisfont aux
exigences de forme de la loi Hoguet relève du notaire ou du juriste.*

---

### 🏛 A.3-TECHNIQUE — LE REGISTRE DES MANDATS DEVIENT UN VRAI REGISTRE

*Chantier ouvert le 28/08, par une question de Frédéric : « il faut créer dans l'app et
le serveur un registre des mandats au lieu de réutiliser les données annonces ? »*
**Oui — et c'est plus gros que la date de clôture.**

#### Le constat

**Ce qui s'appelle « registre des mandats » n'est pas un registre : c'est une vue des
annonces.** Il est entièrement reconstruit chaque nuit depuis le miroir, puis **filtré sur
le statut de l'annonce**. Ses lignes vont et viennent avec elle.

Constaté en vraie grandeur le 28/08 : passer une annonce en « Clos » a **fait disparaître
sa ligne de registre** — pas par erreur, par construction. Et à l'échelle du parc :

```
   mandats dans le miroir        24 939
   publies au registre           23 834
                                 ------
   invisibles                     1 105
        dont l'annonce est « Mandat clos »     642   <-- le mandat sort au moment ou il est clos
        dont l'annonce est inconnue du serveur  94
        dont l'annonce n'a plus de statut       88
```

> **Un registre qui perd ses mandats à leur clôture n'est pas un registre.**

#### Pourquoi ce n'est pas optionnel

Le registre se reconstruit **depuis le miroir de Hektor**. Le jour de la coupure, le miroir
gèle : le registre gèlerait avec lui — il existerait encore, figé, mais **ne pourrait plus
accueillir un seul mandat neuf**.

Or les mandats naissent **déjà** dans l'app : depuis juin, **181 créés par l'app contre 1
dans Hektor**. Ils transitent aujourd'hui par lui pour être enregistrés ; après la coupure,
ce chemin n'existe plus.

**Sans registre durable, on ne peut pas couper.**

#### 🔑 LA PRÉCISION DE FRÉDÉRIC (28/08) — TROIS COUCHES DE NUMÉROTATION

> *« Ce registre devrait se comporter un peu comme le ledger d'affaires, avec les numéros
> de mandat historiques — numéro Hektor, numéro PROTEXA — et ensuite un nouveau système de
> numérotation lié à un registre de mandat électronique. »*

C'est le patron d'`app_affaire_ledger`, qui porte déjà `app_affaire_id` **et**
`hektor_affaire_id`. Ici il en faut **trois**, et la raison est mesurée :

```
   numero HEKTOR    familles SIMPLE / EXCLUSIF / ACCORD
   numero PROTEXA   libelles francais (« Mandat de vente… »)
   numero APP       la serie a venir, liee au registre electronique
```

**Ce ne sont pas trois noms pour la même chose : ce sont deux registres réels, plus un
troisième à naître.** Ils ne s'écrivent même pas pareil — une clôture PROTEXA est
enregistrée `2026-08-26 10:26:42`, une clôture HEKTOR `2026-08-25`.

Et c'est ce qui explique les collisions de numéros mesurées le 28/08 : sur 18 136 numéros,
**4 090 sont partagés entre agences** *(normal — un registre se tient par agence)*, **39
s'expliquent par les deux familles**, et il reste **663 vraies collisions**. Une table qui
ne distingue pas la famille les rendrait indémêlables.

> ⚠ **À retenir le jour où on ouvrira ce chantier** : chaque ligne doit porter **son
> numéro ET son registre d'origine**. Un numéro seul ne désigne rien — c'est déjà pour
> cette raison que le projet interroge les mandats par le **couple** (annonce, mandat).

#### Le chiffrage

**Ce qui existe déjà** — le miroir porte tout, et à des taux très élevés :

```
   identifiant  100,0 %    montant   99,1 %      date de cloture   0,4 %  <-- l'app le produira
   numero       100,0 %    mandants  98,8 %
   date debut   100,0 %    type      95,2 %
   date fin     100,0 %    note      94,4 %
```

**Le remplissage initial est donc entièrement faisable — mais depuis le miroir, donc tant
que Hektor vit.**

**Ce qu'il faut construire** : une table `app_mandat` sur le modèle exact d'`app_dossier`,
~16 colonnes *(les 10 du mandat + les trois numéros + `vu_le` / `absent_depuis`)*. Le
registre publie 66 colonnes, mais **10 seulement concernent le mandat** — le reste est
joint à l'affichage. On ne déplace pas le registre, on lui donne son noyau.

| | |
|---|---|
| la table + son alimentation depuis le miroir *(patron déjà servi 4 fois)* | **1 à 2 j** |
| le remplissage initial — 24 939 lignes, une passe | *compris* |
| la sonde « un mandat ne disparaît jamais » | quelques heures |
| **le registre lit la table au lieu de se reconstruire** | **2 à 3 j** — le morceau délicat |
| la numérotation propre | **déjà prévue en E.4**, elle s'y branche |
| **TOTAL** | **3 à 5 jours** |

*Même ordre de grandeur que l'identité des contacts (3 à 5 j pour 355 687 lignes et 19
tables) — ici c'est 24 939 lignes et une seule table.*

⚠ **Un point à prévoir dès le départ** : **0,9 %** des annonces portent plusieurs versions
sous un même numéro *(les avenants)*. Marginal, mais le rattraper après serait un second
chantier.

#### Où ça se place

**Même contrainte que 26bis** : le remplissage vient du miroir, donc **Hektor doit vivre
encore**. Ces deux tâches forment la famille « impossible si on la remet à plus tard ».

Et elle bloque trois choses en aval : **C.13-c** *(le rattrapage écrirait sur du sable)*,
**A.3** *(c'en est la moitié technique)*, et **la coupure elle-même**.

> ➡ **`A.3` quitte la colonne « hors code ».** Sa moitié juridique reste chez le juriste ;
> sa moitié technique entre dans le plan de dev, **juste après 26bis**.

#### L'ordre révisé — 28/08

```
   1.  C.16                  825 fiches actives qui n existent plus  (1 a 2 j)
   2.  26bis                 le corps de l'annonce            } meme contrainte :
   3.  A.3-technique         LE REGISTRE DURABLE              } Hektor doit vivre
   4.  C.9                   la creation part de l'app
   5.  C.11 · C.14-bis · 0.3 le petit reste
   6.  le negociateur        signale, PAS prioritaire (Frederic, 28/08)
   7.  D.1a -> D.1 -> D.2    rapatrier les fichiers
   8.  E.1 -> E.2 -> E.3 -> E.4  +  C.13-c
```

---

### CE QU'IL NE FAUT PAS OUBLIER

*Liste tenue à jour. Ce qui n'est dans aucun bloc et qui se perdrait autrement.*

- **Les 4 services Windows et les 33 workers** : ils deviennent inutiles au jour J. Décider quand
  on les éteint, et dans quel ordre.
- **Le monitoring doit survivre à la coupure** — 20 sentinelles, dont plusieurs interrogent des
  objets liés à Hektor. À relire une par une avant E.4.
- **Deux alertes ouvertes** : `data.notif_orphelines` 57 *(seuil 20)*, `data.notif_non_lues` 851
  *(seuil 300)*.
- **Une recherche de test** sur le contact 603953 *(Maison · Firminy · 180 000 €)*, que ni l'app
  ni l'interface Hektor n'ont laissé retirer — l'agence du contact est 12, pas 1.
- **L'espace client tourne sur Render** : vérifier qu'il ne dépend de rien de Hektor.
- **Le premier remplissage de C.6** doit se faire **pendant que Hektor vit** : c'est le miroir qui
  alimente.

---

## LES GESTES DE TRANSACTION CHEZ HEKTOR — codes relevés et interactions de statut

*Relevé en conditions réelles le 29/08/2026 sur le bac à sable 62774, en sessions
**administrateur** puis **négociateur**. Chaque ligne ci-dessous a été **vue passer dans le
réseau**, pas lue dans le code. Détail complet et récit de l'essai :
`ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md`.*

> ⚠ **La leçon de méthode, avant les codes.** Le verbe d'annulation du compromis avait été lu
> **dans le JavaScript** de `annuleCompromis`, où il figure bel et bien. Ce n'est pourtant
> **pas** celui que le navigateur émet. Le worker a tourné plusieurs jours avec un verbe qui
> n'aurait rien annulé. **Lire le code ne remplace pas regarder passer l'appel.**

### Les verbes, tels qu'ils partent

| geste | méthode | mode | paramètres |
|---|---|---|---|
| **refuser une offre** | GET | `annonce-SuiviVente-updateOffre` | `id`, `type=refus` |
| **accepter une offre** | GET | `annonce-SuiviVente-updateOffre` | `id`, `type=accepte` |
| **annuler un compromis** | **GET** | **`annonce-SuiviVente-cloture`** | **`idCompromis`, `notes`** |
| **supprimer une vente** | GET | `ventes-deleteVente` | `id` |
| supprimer un compromis | — | `delete_compromis_vente(id)` *(front)* | confirmation Oui/Non |

**Et les faux amis, à ne pas confondre avec l'action :**

| | |
|---|---|
| `annonce-SuiviVente-clotureCompromis` *(POST)* | **le chargeur du formulaire** — rend 7 214 caractères de HTML. C'est lui que le worker appelait par erreur |
| `annonce-SuiviVente-compromis-popinClotureCompromis` | la popin de confirmation *(1 823 c.)* |
| `ajoutebien` *(POST)* | **appel annexe** : il échoue souvent sans empêcher le geste. Il a échoué 8 fois pendant la création — réussie — de la vente 23287 |

**Le parcours d'annulation d'un compromis a TROIS temps**, pas un : bouton « Annuler » → popin
de confirmation → **un second formulaire** *(prix net vendeur, date, note)* → « Clôturer ».
C'est ce troisième temps qui émet l'appel.

### Ce que Hektor répond — et qui n'est pas uniforme

| geste | succès | échec |
|---|---|---|
| **offre** | `"1"` *(mesuré 3×)* | `"[]"` *(2 causes distinctes)* |
| **compromis** | **`true`** *(4 caractères, capté le 29/08 sur le compromis 50046)* | **vide** |
| **vente** | **vide** | **vide** |

➡ **La vente est le seul geste dont la réponse ne dit RIEN.** Pour elle, seule la relecture de
la fiche fait foi. Une règle uniforme « toute réponse vide = échec » — posée le 28/08 —
aurait rejeté **chaque suppression réussie** et défait un geste qui avait marché.

### Le vocabulaire du refus — Hektor refuse en HTTP 200, en français

Quatre formulations relevées **en une seule journée**, dont trois manquaient au détecteur :

```
   « Un compte administrateur ne peux pas saisir une offre »
   « Vous ne pouvez pas creer un bien »                          <- `ne pouvez` != `ne peux`
   « Vous n'avez pas les droits pour creer un compromis... »     <- `les droits` != `le droit`
   {"result":false}                                              <- et pas seulement `success`
```

➡ **Une liste de phrases ne se devine pas, elle se relève.** Le motif du worker est
volontairement large, et toute nouvelle formulation rencontrée doit y être ajoutée.

### 🔴 LES INTERACTIONS AVEC LE STATUT DE L'ANNONCE

**C'est le point que Frédéric a demandé de consigner, et il commande la branche « Vendu ».**

| geste | effet sur le statut de l'annonce |
|---|---|
| **annuler un compromis** | l'annonce **reste** « Sous compromis » ; le compromis passe « Clôturé » |
| **supprimer un compromis** | l'annonce **redescend seule** à « **Sous offre** » |
| **supprimer une vente** | l'annonce **redescend seule** à l'étape **compromis**, et « BIEN VENDU » disparaît |
| **créer une vente** | **ne clôture PAS le compromis** — 50046 est resté actif avec la vente 23289 en place |
| **annuler le compromis** | **ne supprime PAS la vente** — 23289 a survécu à la clôture de 50046 |
| **enregistrer une vente** | **deux issues au choix** : « laisser actif » ou « **archiver** » |
| cliquer « SOUS COMPROMIS » dans la modale | change **le statut seul**, *sans créer de compromis* — sauf si l'annonce n'en a aucun, auquel cas l'assistant s'ouvre |

> **La règle qui s'en dégage : chez Hektor, la transaction commande le statut ; le statut ne
> commande pas la transaction.** La modale de statut n'est pas un créateur de transaction —
> elle en ouvre un *quand il n'y a rien*.

### Le choix « actif / archivé » — mécanisme complet *(mesuré, tâche C.19-c)*

**Ce n'est pas une case à cocher : c'est un parcours, et il crée la vente.**

```
   « Transformer en vente »
        -> popin ARCHIVAGE : « pour quelle raison ? »
              [ LE BIEN EST VENDU ]        [ AUTRE ]
        -> si VENDU, une sous-raison :  reseau / confrere / proprietaire
        -> « Sauvegarder »   ->  l'annonce passe archive=1 IMMEDIATEMENT
        -> PUIS l'assistant « Enregistrer une vente » s'ouvre
        -> etape 4 : deux boutons  « Enregistrer & laisser actif »
                                   « Enregistrer & archiver »
```

Verbe de l'archivage relevé : **`annonce-panneauArchive`** *(POST)*. Et le
**désarchivage** est un simple `upval` — `mode=upval&id=<annonce>&champ=archive&val=0`, qui
rend `"1"` au succès. **Notre worker `restore_hektor_annonce` l'utilise déjà**, et il a remis
62774 en actif de bout en bout le 29/08 *(travail pris en 3 secondes, `archive=0` vérifié)*.

⚠ **« Transformer en vente » n'ouvre PAS la popin d'archivage** — il va droit à l'assistant de
vente. La popin d'archivage vient du clic sur le **statut VENDU**. Deux chemins distincts vers
la même vente, et un seul demande l'archivage.

**Trois conséquences mesurées sur l'annonce 62774 :**

| | |
|---|---|
| après l'enregistrement | `archive=1`, `isArchive=1`, et « BIEN VENDU » affiché |
| **le compromis n'est PAS clôturé** | 50046 est resté **actif** alors que la vente 23288 existait |
| l'archivage est demandé **avant** la vente | on peut donc archiver puis abandonner la saisie de la vente — l'annonce reste archivée |

> **Le point qui compte pour l'app** : l'archivage et la vente sont **deux gestes distincts que
> l'écran enchaîne**. Notre branche « Vendu » doit donc porter **deux décisions**, pas une :
> *crée-t-on la vente ?* et *archive-t-on l'annonce, et pour quelle raison ?*
> Câbler l'un des deux en dur, c'est décider à la place du négociateur.

### ⚠ DANGER MESURÉ — ré-enregistrer une vente existante peut la DÉTRUIRE

Sur la vente **23288**, déjà enregistrée : rouvrir l'assistant *(« Modifier »)* et cliquer
**« Enregistrer & laisser actif »** a fait **disparaître la vente**. Après coup : plus de bloc
« Vente du bien », plus de « BIEN VENDU », et « Transformer en vente » reproposé.

Le seul appel anormal du parcours est `ajoutebien` → *« Vous ne pouvez pas creer un bien »*.
L'enregistrement semble **recréer** la vente ; la recréation est refusée pour l'admin ; il ne
reste rien.

**Le facteur a été isolé le 29/08 au soir**, en refaisant l'essai à l'identique dans l'autre
configuration — c'est Frédéric qui a poussé à le chercher, en soupçonnant un lien avec
l'annulation du compromis :

| vente | compromis | annonce avant | choix à l'enregistrement | résultat |
|---|---|---|---|---|
| **23288** | actif | **ARCHIVÉE** | « laisser actif » *(= désarchiver)* | **DÉTRUITE** |
| **23289** | clôturé | active | « laisser actif » *(= ne rien changer)* | survit |
| **23289** | clôturé | active | « archiver » | survit, et l'annonce passe archivée |

> **Ce n'est donc ni le compromis, ni « l'enregistrement » en soi.** Enregistrer une vente
> existante ne la détruit pas : elle a survécu deux fois sur trois. **Le seul cas destructeur
> est celui où l'enregistrement doit DÉSARCHIVER l'annonce.**
>
> Ce qui colle exactement au reste : sortir de l'archive impose un **supprimer-puis-recréer**,
> et la recréation est refusée *(`ajoutebien`)*. La suppression, elle, passe. Il ne reste rien.

*Frédéric a poussé deux fois sur ce point — d'abord en soupçonnant le compromis, puis en
soupçonnant l'enregistrement lui-même. Les deux pistes étaient fausses, mais c'est en les
éprouvant qu'on a isolé la vraie : le **sens** du changement d'archivage.*

**Corrige au passage une affirmation fausse de cette note** : le choix agit bel et bien à la
**modification** — « archiver » a archivé une annonce active. C'est le sens inverse, le
désarchivage, qui casse.

### La règle pratique

```
   modifier une vente sur une annonce ACTIVE      ->  sans danger
   modifier une vente sur une annonce ARCHIVEE    ->  DANGER : desarchiver la detruit
   desarchiver proprement                         ->  upval&champ=archive&val=0
                                                      (notre worker restore_hektor_annonce)
```

➡ **Si l'app doit un jour toucher une vente archivée, elle désarchive d'abord par `upval`,
puis modifie.** Jamais l'inverse, et jamais par l'assistant.

➡ **Aucun de nos workers ne doit « modifier » une vente par ce chemin** tant que ce n'est pas
éclairci. Et si l'app doit un jour corriger une vente, elle le fera **chez nous**
*(`app_affaire_champ_app`)*, pas en rejouant l'assistant de Hektor.



*⚠ Piège relevé au passage : `canCallMvcPopin` répond `{"result":false}` — c'est une **sonde de
capacité**, pas un refus du geste. Le motif de refus du worker contient `"result":false` ; il
reste sûr **parce que le worker n'appelle jamais cette sonde**, mais la nuance est à garder en
tête si on élargit le périmètre.*

**Conséquence pour l'app.** Nos gestes ne doivent pas poser le statut de l'annonce à la main
après coup : Hektor le recalcule. Poser les deux, c'est se préparer une divergence. Et le
choix **actif / archivé** de la vente est une **décision métier** qui doit remonter jusqu'à
l'écran — elle ne peut pas rester câblée dans le worker *(tâche **C.19-c**)*.

### Les droits, mesurés — ils ne sont pas où on les croit

| | administrateur | négociateur |
|---|---|---|
| créer une **vente** | ✅ | ❌ *(le statut VENDU disparaît de la modale)* |
| créer un **compromis** | ✅ | ✅ |
| **supprimer** un compromis | ✅ | ✅ |
| voir le bouton *supprimer une vente* | ❌ *(présent en DOM mais masqué, 0×0)* | — |

Et une contrainte qui n'a **rien à voir avec le compte** : **un seul compromis à la fois par
annonce**. Tant qu'il en existe un — *même clôturé* — toute création est refusée, dans les deux
sessions. Le supprimer libère la place.

*Le bouton masqué en admin est le même phénomène que les blocs de signature invisibles en root
admin (idUser 4). **Un contrôle masqué dans l'écran ne veut pas dire un verbe refusé par le
serveur** : `ventes-deleteVente` a parfaitement fonctionné en HTTP depuis cette même session.*

---

## LE BLOB DE DETAIL — faux obstacle, leve le 21/08

Le contrat d'autorite du 17/08 reclamait *« un inventaire exhaustif des ~130 cles du blob avant
d'ecrire quoi que ce soit dessus »*. **Cet inventaire est sans objet** : la question n'etait pas
« que contient le blob » mais « qui l'ecrit ».

**Une seule fonction ecrit dans le blob** : `app_edit_annonce_optimistic`. Et elle n'y touche
que **7 cles** :

```
   surface . nb_pieces . nb_chambres . surface_terrain_detail
   latitude_detail . longitude_detail . garage_box_detail
```

Elle range en plus ce que le negociateur vient de saisir dans un **compartiment dedie**,
`app_optimistic_overlay`. **Le paquet a deja un tiroir reserve a l'app.**

Les 127 autres cles sont une photocopie de Hektor : l'app les lit, les affiche, s'en sert pour
le rapprochement -- elle n'en ecrit aucune.

> **Ce qui reste a faire est minuscule** : proteger ces 7 cles de la reecriture de nuit, avec le
> mecanisme qui existe deja (celui qui protege naissance / lieu / situation matrimoniale cote
> contact). Ce n'est pas un chantier a part : ca rentre dans « Hektor confirme, il n'ecrase plus ».

**Ce qui reste valide de la mise en garde du 17/08** : ne PAS declarer « tout le descriptif est a
l'app ». Le blob transporte de la diffusion, des affaires, des mandats et des photos bien
vivants -- une regle en bloc les aurait geles.

---

## LE TROU DE STOCKAGE DES ANNONCES — decouvert et tranche le 21/08

> ### ⚠ DIAGNOSTIC CORRIGÉ LE 21/08 AU SOIR — lire ceci d'abord
>
> **Tout ce qui suit reposait sur une affirmation fausse.** L'audit de la data locale
> (`notice/AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md`) a ouvert la base au lieu de lire le
> nom des fichiers :
>
> ```
>    ce que cette section affirme   « le serveur ne detient pas les annonces »
>    ce que la base contient        app_view_generale : 56 890 lignes, 130 COLONNES
>                                   refaite chaque nuit en 37 SECONDES
>                                   132 des 168 champs sont deja des colonnes locales
> ```
>
> `view_generale.py` n'est pas une vue : c'est un `DROP TABLE` suivi d'un
> `CREATE TABLE AS`. **Le serveur détient déjà les annonces**, et il les gardera après la
> coupure — le miroir gèle, il ne disparaît pas.
>
> **Le vrai problème n'est donc pas la conservation, c'est l'écriture** : la table étant jetée et
> refaite chaque nuit, une valeur écrite par l'app n'y survivrait pas jusqu'à 05:30. Il faut une
> table à côté, jamais reconstruite — patron `app_search_registry`. **C'est la tâche C.6, et
> elle est beaucoup plus petite que ce que décrit la suite de cette section.**
>
> La suite est conservée telle quelle : elle porte des mesures justes (le partage 59/134, le
> calendrier, les trois gestes) et le raisonnement qui a mené à l'erreur.

**Constat, mesure a l'appui.** Cote annonces, le serveur local **ne detient pas les donnees** :

```
   app_dossier  (local)  =  10 colonnes seulement
      id . hektor_annonce_id . hektor_mandat_id . numero_dossier
      numero_mandat . commercial_id . commercial_nom . dates . absent_depuis
```

Le contenu vit **uniquement dans le miroir de Hektor** (`data/hektor.sqlite`, 34 tables,
464 952 reponses API brutes). `view_generale.py` recompose a la volee **une ligne a plat
d'environ 200 champs**, qui part ensuite vers Supabase, coupee en deux :

| | |
|---|---|
| **59 champs** | colonnes de `app_dossier_current` -- chercher, filtrer, trier |
| **134 champs** | le paquet `app_dossier_detail_current` -- afficher |

Le partage est decide par deux listes explicites dans le code. **Rien n'est opaque** : les
134 cles sont nommees et calculees une par une. *(C'est pourquoi l'« inventaire des 130 cles »
reclame par le contrat d'autorite du 17/08 est sans objet -- voir plus bas.)*

> **Le probleme** : le jour ou Hektor s'eteint, le miroir cesse d'etre alimente. Or c'est lui
> qui fabrique la ligne a plat. **Le serveur local n'aurait plus de quoi la recalculer.**

*(Le contact et la recherche n'ont PAS ce trou : le local a ses propres tables --
355 641 contacts, 76 839 recherches.)*

### La decision (Frederic, 21/08) : option ②

**Le serveur local recoit ses propres tables d'annonces** et reste le maitre, comme pour les
contacts et les recherches. Supabase garde son role : le sous-ensemble utile, en ligne.

**Consequence de calendrier, non negociable** : le remplissage initial doit se faire **pendant
que Hektor vit encore**, puisque c'est le miroir qui alimente. Apres la coupure il serait trop
tard. -> tache **26bis**.

### Les trois gestes, et OU ils sont dans la liste

```
   26bis-(1)  CREER + REMPLIR   juste apres la bascule du numero de recherche
   26bis-(2)  OBSERVER          en parallele, personne ne lit
   ------------------------------------------------------------------
   26bis-(3)  BASCULER          juste apres la tache 9 -- COLLEE au contrat d'autorite
```

**Pourquoi ce n'est plus a la fin (corrige le 21/08).** Je l'avais rangee avec le rapatriement
des documents et des photos, dans la famille « sortir de chez Hektor avant la coupure ».
**Fausse ressemblance** :

- **Ce n'est PAS irreversible.** Documents et photos, oui. Une table locale, on la jette.
- **Elle demande une longue observation.** La poser tard, c'est repousser la coupure d'autant.
- **(3) va avec 6-9.** Les laisser a vingt taches d'ecart, c'est se condamner a faire l'un sans
  l'autre : le contrat aurait un arbitrage sans endroit ou l'ecrire.
- **Et surtout** : la creation app-first (23-25) ecrit dans Supabase. Sans 26bis, une annonce
  creee dans l'app n'existe QUE la, et le serveur ne l'apprend que si Hektor la confirme.
  **Ce serait creuser le trou pendant qu'on le rebouche.**

**Une seule reserve, assumee** : (2) attend la bascule du numero de recherche, pour ne pas avoir
deux doublures a surveiller en meme temps. C'est une affaire de jours. Six chiffres a lire chaque
matin au lieu de trois, ca cesse d'etre une surveillance et ca devient une corvee -- et une
sentinelle qu'on ne lit plus ne protege de rien.

### (3) EXIGE le contrat d'autorite -- trouve par Frederic le 21/08

L'app n'ecrit QUE dans Supabase (aucune porte d'entree vers le serveur, et il ne faut pas en
creer). Donc une table locale alimentee seulement par le miroir **apprendrait les modifications
uniquement par Hektor** -- et seulement si Hektor les a recues. **Une saisie en conflit, ou dont
l'envoi a echoue, n'arriverait JAMAIS dans la base locale.**

Le serveur doit donc **venir lire dans Supabase ce que l'app a ecrit**. Ce mecanisme existe deja,
pour trois champs de contact : `fetch_app_owned_contact_fields` relit dans Supabase ce que Hektor
ne connait pas, et le reinjecte. **Meme geste, a etendre.**

```
   la nuit :
        ce que dit HEKTOR (le miroir)  +  ce que dit L'APP (relu dans Supabase)
              -> arbitre selon le CONTRAT D'AUTORITE du 17/08
              -> ecrit dans LA BASE LOCALE
              -> envoye vers Supabase
```

> **La table locale devient l'endroit ou l'arbitrage a lieu.** Aujourd'hui il n'y a pas d'endroit :
> c'est pour cela que Hektor gagne par defaut -- il est seul dans la piece.

**Consequence sur l'ordre** : les taches **6-9** et **26bis** ne sont plus independantes.
`26bis sans le contrat` = une base qui oublie les saisies.
`le contrat sans 26bis` = un arbitrage sans endroit ou se faire.

### Ce que 26bis debloque en plus

Apres la coupure, une annonce **creee dans l'app** puis archivee n'aura jamais existe dans le
miroir : son detail ne serait nulle part. La consultation des archives doit donc changer de
source -- et 26bis est ce qui le permet.

---

## LE BLOC RECHERCHES — ce que les audits du 20/08 au soir ont changé

**Trois choses que je croyais et qui sont fausses**, vérifiées dans le code, pas déduites :

| Ce qui était écrit | Ce que la lecture montre |
|---|---|
| L'étiquette sert à détecter qu'une recherche a changé chez Hektor | **Non.** La détection vient de la **redemande de la fiche** (run 03:00, sans filtre de date) et de la comparaison de contenu `stable_payload_hash`. L'étiquette n'est que le **nom de rangement** de la ligne |
| Il faut reprendre ≈ 493 000 lignes | **Non.** **Un seul endroit fabrique l'étiquette** : `build_contacts_layer.py:827` |
| Le renommage seul est sans risque | **Non.** Postgres refuse le rename, l'appel se fait par NOM, la compilation ne voit rien |

**La preuve que le numéro suffit est dans le projet lui-même.** Dans le *même* script d'envoi,
deux tables voisines :

| Table | Rangée sous | Quand Hektor modifie |
|---|---|---|
| `app_contact_current` | `hektor_contact_id` — **un numéro** | ligne **mise à jour sur place** ✅ |
| `app_contact_search_current` | l'étiquette — **un haché de contenu** | ligne **supprimée puis recréée** ❌ |

Les modifications de contact faites dans Hektor remontent parfaitement. **Le mécanisme
fonctionne déjà avec un numéro stable — il n'est pas appliqué aux recherches, voilà tout.**

### Le fond, formule par Frederic le 20/08 au soir : **il y a DEJA deux haches**

Preuve dans `phase2.sqlite`, table `app_contact_supabase_push_state` :

```
   UNE RECHERCHE
   nom de la ligne : 001697ad4134b105219d5549       <- un hache (la cle)
   empreinte       : 742548023fb03575338def20...    <- un AUTRE hache

   UN CONTACT
   nom de la ligne : 100030                         <- un NUMERO
   empreinte       : 03dd0f0f5e96c4c031bec5b88...   <- un hache
```

**L'empreinte de contenu existe deja sur les 3 962 recherches.** Elle est calculee et
stockee a chaque run. **Et elle n'est jamais consultee** : le nom ayant change en meme temps
que le contenu, la ligne d'avant est introuvable et l'empreinte connue reste rangee sous un
nom mort.

> **Deux haches sur chaque recherche. Le premier fait mal le travail du second.
> Le second, qui le ferait bien, n'est jamais lu.**

**Ce que le chantier fait, exactement :**

```
   AVANT   nom : 001697ad4134b105219d5549     empreinte : 742548...
   APRES   nom : 412                          empreinte : 742548...
                  ^                                        ^
             on remplace CA                      on ne touche pas a CA
```

Le run de nuit retrouve alors la ligne d'avant, compare les deux empreintes, voit que le
contenu a bouge, **et met a jour au lieu de detruire**.

> **On ne construit rien. On enleve un doublon qui bloque un mecanisme deja present.**

Le detail de la boucle : `push_contacts_to_supabase.py:206-211`
`known_hashes.get(row_key(row)) != stable_payload_hash(row)` -- le nom sert a retrouver ce
qu'on savait, l'empreinte sert a comparer. Deux metiers, une seule ligne de code.

**La méthode retenue est celle de Frédéric (20/08) : la doublure.**

```
   poser le numero A COTE, sans rien lui confier
        -> l'etiquette continue de commander, rien ne casse
   observer pendant des semaines : tombe-t-il toujours juste ?
        -> une sentinelle repond, pas une supposition
   basculer seulement une fois qu'il a fait ses preuves
```

> C'est l'inverse de ce que j'avais proposé — basculer puis vérifier. **Et c'est ce qu'on
> aurait dû faire pour les annonces** : `app_dossier_id` a dérivé de mars à juin sans que
> personne le voie, précisément parce que personne ne l'observait.

**Tâche 4bis — RÉPONDUE le 21/08.** **Hektor ne sait pas supprimer une recherche.**
Le worker, même pour un « Supprimer » demandé depuis l'app, appelle
`archiveHektorContactSearch` → `mode=contacts-contactProfile-modifDateArchiveCritere` avec une
`dateArchive` : il **pose une date**, il n'efface rien (`console_job_worker.js:11878-11890`, `:11918`).

> **Donc le rang ne glisse jamais, et `(contact + rang)` est une poignée stable.**
> Confirmé par les données : 72 872 archivées en local occupant des rangs jusqu'à 15, et
> seulement **9** recherches actives précédées d'une archivée. Capturer l'`idCritere` n'est
> plus un préalable — ça reste un confort.

⚠️ **Mais l'archivage détache quand même**, pour une raison de **périmètre**, pas de rang :
le local garde les archivées, **Supabase ne garde que les actives**. Une recherche archivée
disparaît donc de Supabase, et ce qui pointait sur sa clé devient orphelin. C'est ce rythme
que mesure le carnet du balayage (`app_sweep_search_orphans_log`, posé le 21/08).

*(Correction : les « 31 recherches supprimées chez Hektor » notées le 20/08 étaient selon toute
vraisemblance des recherches **archivées**.)*

### Le nom figé épingle une POSITION — conséquence relevée le 21/08

Objection de Frédéric sur « la tâche 22 est déclassée ». **Elle portait juste.**

Ce qui a été vérifié et tient : **un seul endroit du projet fabrique un nom de recherche**,
`build_contacts_layer.py:828`, et le registre lui reprend la main à la ligne 1235. Le front, le
worker et les fonctions Postgres n'en fabriquent aucun *(vérifié le 21/08)*. Donc oui : plus
personne ne peut recalculer un nom et ne plus rien retrouver.

**Mais figer le nom déplace le risque, il ne le supprime pas :**

```
   AVANT   le nom designait UN CONTENU   -> le contenu change, le nom change, la ligne s'orpheline
   APRES   le nom designe UNE POSITION   -> la position glisse, le nom se recolle sur la MAUVAISE
                                            recherche -- et SANS BRUIT
```

Le second est plus rare mais **plus grave** : l'orphelinage se voit *(le balayage le compte)*, la
mauvaise attache ne se voit pas. Et ce sont précisément les **4 portes** qui relisent les rangs
chez Hektor. **La tâche 22 reprend donc un rôle de stabilité — un autre que celui qu'elle perd.**

**Ce qui a été mesuré**, sur l'ordre dans lequel Hektor rend les recherches :

```
   9 contacts seulement melent archivee(s) et active(s)
      8  toutes les archivees AVANT les actives   -> ajout en FIN de liste
      0  toutes les archivees APRES les actives   -> insertion en tete
      1  entrelacee  (archivee / active / archivee)
```

L'entrelacée n'est pas un contre-exemple : c'est exactement ce que produit un ajout en fin de
liste quand on archive après coup. **Zéro contre-exemple — mais 9 contacts, ce n'est pas une
preuve.** À dire ainsi, et pas autrement.

**D'où la tâche 4sexies**, qui remplace l'observation par un fait vérifiable : *le nombre de
recherches d'un contact ne peut que croître.* Toute diminution signale un glissement.

**Posée le 21/08** — `patch_sentinelle_recherche_disparue_2026-08-21.sql`. Le repère ne redescend jamais *(`greatest`)* : sinon le relevé du lendemain effacerait l'anomalie de la veille. **Vérifiée en la faisant sonner**, pas seulement en la voyant à 0.

---

## LE CHANTIER D'IDENTITÉ — trois objets, un seul dessin

**Le dessin, valable pour les trois :**

```
   case 1 : un numero A TOI        <- la cle, remplie des la creation, jamais remplacee
   case 2 : le numero de Hektor    <- simple reference, vide en attendant son retour
```

**Arbitrage Frédéric (20/08) : pas de solution mixte.** Un objet ne peut pas avoir une case pour
les anciens et deux pour les nouveaux. **Tout le parc bascule d'un coup, ou rien.**

**Deuxième arbitrage : on double ET on bascule dans la foulée.** Jamais de numéro « secondaire »
généré mais inutilisé — c'est ce qui a laissé `app_dossier_id` dériver de mars à juin sans que
personne le voie. *Ce qui est utilisé est ce qui est vérifié.*

### L'ordre, établi par l'audit des points d'appel (20/08)

| Ordre | Objet | Volume | Points d'appel ambigus | Risque |
|---|---|---|---|---|
| **1** | **Transactions** | ≈ 29 100 | **0 sur 12** — jamais envoyés au worker | **le plus faible** |
| — | *Annonces* | *341 394* | *3 sur 56, dont 2 `null`* | *fait le 19/08* |
| **2** | **Contacts** | ≈ 186 500 | **3 réels**, ≈ 10 fonctions à relire | **le plus élevé** |
| **3** | **Recherches** *(3 961)* | ≈ 1 300 rapprochements à rebrancher | clé = **hachage du contenu**, elle bouge seule | **cas à part — voir le dossier ci-dessous** |

> **Pourquoi les contacts sont les plus risqués** : ils n'ont qu'une seule colonne, donc **aucune
> couche n'a jamais eu a faire la distinction**. Mesure du 20/08 :
>
> | | Front | Fonctions de la base | Worker |
> |---|---|---|---|
> | Annonces | 53 explicites / 56 | explicites | lit un champ nomme |
> | **Contacts** | **3 ambigus**, ~10 fonctions | **6 fonctions ambigues** | lit un champ nomme |
> | Transactions | 12 / 12 explicites | jamais envoyees | ne les connait pas |
>
> Les six fonctions concernees : `app_console_create_update_contact_job`,
> `..._delete_contact_job`, `..._contact_search_job`, `..._update_contact_search_job`,
> `..._delete_contact_search_job`, `..._update_mandant_contact_job` — toutes ecrivent
> `hektor_contact_id` a partir de `target_contact_id`.

### La méthode, par objet — jamais deux à la fois

```
   0. AUDIT COMPLET DES POINTS D'APPEL, sur les TROIS couches -- prealable absolu.
      Partout ou un identifiant part vers un worker, il doit etre lu dans la
      colonne NOMMEE, jamais dans "la cle".
        a) le front        : modales, api.ts, App.tsx
        b) les fonctions de la base : les 14 app_console_create_*_job
        c) le worker       : il lit deja un champ nomme -> a confirmer, pas a modifier
      Puis renommer ce qui est ambigu : input.contactId -> input.hektorContactId.
      Aucun effet fonctionnel aujourd'hui, verifie par la compilation.
   1. ajouter la case (Supabase + local, parent et tables enfants)
   2. renumeroter le stock  : table de correspondance conservee, essai a blanc
                              qui annule tout, transaction unique, verification chiffree
   3. basculer la cle DANS LA FOULEE : les jointures lisent la nouvelle case,
      ET LA CASE HEKTOR DEVIENT FACULTATIVE -> c'est CE geste qui autorise
      la creation depuis l'app. Il est impossible avant l'etape 3, puisque
      la case Hektor est encore la cle.
   4. poser la sentinelle   : doublons = 0, orphelins = 0, ecart local/Supabase = 0
   5. le worker NE CHANGE PAS : il lit toujours le champ nomme hektor_*_id
```

**Preuve avant la masse** : basculer un seul objet, le modifier depuis l'app, vérifier que le
worker aboutit et que Hektor a bien reçu. Dix annonces avaient servi de test le 19/08 avant les
12 162 — aucun orphelin créé.

**Garde-fou pendant la transition** : la RPC de création de travail **refuse** de créer un travail
Hektor si la case Hektor est vide — elle le met en attente. Un travail ne peut donc pas partir
avec un mauvais numéro : il ne part pas du tout.

---

## LE DOSSIER RECHERCHES — enquête du 20/08, à lire avant d'y toucher

**Trois facettes distinctes**, identifiées par `RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md` :

| | Facette | État |
|---|---|---|
| **A** | **Clé instable** — `contact_search_key` hache le **contenu éditable** | ❌ jamais corrigée |
| **B** | **Écrasement** — l'édition renvoie TOUTE la recherche depuis une copie peut-être périmée | ❌ jamais corrigée |
| **C** | **Angle mort `date_maj`** — éditer une recherche dans Hektor ne bump pas la date du contact | ✅ **corrigée le 20/06** |

**C a été corrigée par un run dédié** : `scheduled/run_recherches_actives.ps1` ->
`sync_active_searches.py`, **03:00 chaque nuit**, ~3 590 contacts, sans filtre `date_maj`.

> **Le noeud : la correction de C amplifie A.**
> Avant le 20/06, une édition faite dans Hektor était invisible -> la clé ne bougeait pas.
> Depuis, elle est détectée -> **la clé bouge** -> l'historique se détache.
> **Orphelins : 327 le 19/06 -> 1 332 le 20/08. Multiplié par quatre en deux mois.**

**Ce n'est PAS voulu — vérifié le 20/08 :**

- **6 clés du projet sur 7 hachent une identité** (relation, registre, contact, dossier, doublons).
  La recherche est **la seule** à hacher du contenu.
- **Deux consommateurs s'en protègent déjà en production** : `app_email_envoi.search_index`
  (migration du 17/06 : *« la contact_search_key change à l'édition »*) et
  `espace_client._load_search_for_envoi` (3 niveaux, *« on ne s'y fie qu'en tout dernier recours »*).
  **Le contrat de fait est déjà : ne pas se fier à cette clé.**
- **Personne ne dépend de son instabilité.** Le rapprochement est le seul à ne pas se protéger.

**Pourquoi ça n'a jamais été corrigé** : le correctif proposé en juin était `hash(contact_id, index)`.
Il est **mauvais** — l'`index` est la **position**, qui bouge à chaque suppression et n'est pas
alignée entre l'API et le grattage Console. **La bonne réponse est un identifiant propre à l'app.**

**Gravité** : le moteur de rapprochement est **app-only par décision métier**
(`NOTE_MOTEUR_RAPPROCHEMENT_ACQUEREUR_2026-06-14.md`). Ce qui se détache — propositions, retours
acquéreur, relances, emails — **n'existe nulle part ailleurs**. Hektor ne peut rien reconstruire.

**Vérifié en direct le 20/08**, contact 604020 : édition à 14:36 -> clé inchangée, 41
rapprochements recalculés ; retour de Hektor à 14:48:07 -> **nouvelle clé**, les 41 deviennent
orphelins. Et **aucune des 4 fonctions** qui suppriment des rapprochements ne nettoie par absence.

### Ce qui pend sous la clé — mesuré le 20/08, SEPT tables

| Table | Total | Orphelins | Recalculable ? |
|---|---|---|---|
| Historique de score | 450 046 | **11 966** | ✅ oui |
| Rapprochements | 47 547 | **1 373** | ✅ oui |
| **Notifications** | 843 | **13** | ❌ **non** |
| **Propositions** | 11 | **6 — 55 %** | ❌ **non** |
| **Relances** | 10 | **5 — 50 %** | ❌ **non** |
| **Envois d'email** | 82 | **2** | ❌ **non** |
| **Retours acquéreur** | 7 | **2 — 29 %** | ❌ **non** |

> ⛔ **NE PAS « nettoyer les orphelins » d'un bloc.** Plus de la moitié des propositions et des
> relances sont détachées : ce sont des traces d'actions réelles, **app-only**, que Hektor n'a
> jamais eues. Les supprimer les détruirait définitivement.

**Deux gestes distincts, dans cet ordre :**

1. **REBRANCHER l'irremplaçable** — propositions, relances, retours acquéreur, envois,
   notifications — par *(contact + search_index)*, **exactement comme le fait déjà
   `espace_client._load_search_for_envoi`**. ~28 lignes aujourd'hui, mais 50 % des propositions.
2. **NETTOYER le recalculable** — rapprochements et historique de score, 13 339 lignes, sans risque.
3. **CLÉ PROPRE**, pour que ça ne recommence pas.

**Rebrancher AVANT de nettoyer.** Dans l'autre sens, on détruit ce qu'on voulait sauver.

> **L'espace client ne changera pas de comportement** : il ne s'appuie déjà plus sur la clé
> (résolution à 3 niveaux). C'est le seul consommateur déjà immunisé.

### Les recherches deviennent-elles indépendantes en coupant le run de 03:00 ?

**Presque — il y a TROIS portes entrantes, pas une :**

| | Porte | Fréquence |
|---|---|---|
| **1** | Run dédié `sync_active_searches` | 03:00 |
| **2** | Run quotidien — `push_contacts_to_supabase` **supprime puis réécrit** les recherches d'un contact | 05:30 |
| **3** | **Read-through** — `refresh_console_contact_data` appelle le **même code** avec `--contact-id` | à chaque ouverture de fiche |

**Et une porte sortante** : les 3 travaux `*_hektor_contact_search`.

Couper les quatre rend les recherches entièrement app-owned — **et la clé cesse alors de bouger
toute seule, donc le problème A disparaît sans être corrigé**. Mais il faut d'abord :

- **corriger le modèle « au moins »** : la modale n'expose que des minimums, le worker sait envoyer
  20 critères. Ce que l'app ne sait pas exprimer sera perdu (cf. mémoire projet) ;
- **mesurer combien de recherches Hektor portent des critères invisibles dans l'app** ;
- **rebrancher l'irremplaçable** (point 1 ci-dessus) avant de couper quoi que ce soit.

**Ne pas ajouter de garde-fou sur la suppression** — décision Frédéric du 18/08 : il ferait échouer
les cas où le repli `list[0]` tombe juste.

### ✅ LA MESURE QUE CE PLAN RÉCLAMAIT — faite le 30/08

*Le plan pose ici, en préalable à la fermeture des portes entrantes : « **mesurer combien de
recherches Hektor portent des critères invisibles dans l'app** ». C'est fait.*

```
   10 910 recherches au total
    1 234 portent au moins un critere que l'app ne sait pas reconstruire   11,3 %
    1 129 portent un maximum que la modale n'expose pas                    10,3 %
```

**Les critères en cause**, par fréquence :

```
   ITEM_QUARTIER_PONDERATION     979      ponderation de quartier
   ITEM_SURFACE_MAX            1 065         ITEM_CHAMBRE_MAX            1 005       |  des MAXIMUMS -- la modale
   ITEM_PIECES_MAX               960       |  n'expose que des minimums
   ITEM_SURFACE_TERRAIN_MAX      269      /
   ITEM_SURFACE_MIN_COMMERCE      67      immobilier professionnel
   ITEM_MITTOYEN                  25
   ITEM_NB_NIVEAU_MIN / MAX    20 + 20
   ITEM_FLOORS_MIN / MAX         8 + 8
   ITEM_PARTICULARITE              8
```

#### Ce que ça veut dire, exactement

**Aujourd'hui, rien n'est perdu.** Deux raisons, toutes deux vérifiées :

| | |
|---|---|
| **la modale n'expose que 7 champs** | `priceMin/Max`, `surfaceMin`, `landSurfaceMin`, `roomsMin`, `bedroomsMin`, `bathroomsMin` — et l'app persiste **les sept**. Aucune saisie ne se perd |
| **aucune recherche n'a jamais été éditée depuis l'app** | `app_search_pending` : **0 ligne**, jamais. Le chemin existe, il n'a pas servi |

**Mais le risque est réel, et il se déclenchera à la coupure.** La RPC d'édition fait
`criteres_json = app_search_criteres_from_input(...)` — elle **remplace** la liste riche venue
d'Hektor par une liste que l'app ne sait construire qu'à partir de **quatre** sortes
*(équipements, DPE, marge, salles de bain min)*.

```
   AUJOURD'HUI    une edition appauvrit criteres_json
                  -> le run de nuit le repare depuis Hektor
   A LA COUPURE   le run n'existe plus
                  -> l'appauvrissement devient DEFINITIF, sur 1 234 recherches
```

#### Le correctif, quand il faudra

**Fusionner au lieu de remplacer** : à l'édition, conserver les clés que l'app ne connaît pas,
et ne réécrire que celles qu'elle sait produire. C'est petit, additif, et ça retire le risque
sans toucher au modèle « au moins » — que **C.10 a eu raison d'abandonner**, puisque la porte
sortante fermée, l'app n'a plus à parler la langue d'Hektor.

*Ce n'est pas un blocage pour C.4 : le chemin n'est pas emprunté. C'est un préalable à la
fermeture des portes entrantes, et il est désormais chiffré.*

---

### Le trou des NOUVELLES recherches — mesuré le 21/08

Les trois portes ci-dessus font entrer les **modifications**. Aucune ne fait entrer une
**première** recherche :

```
   les recherches ne sont PAS dans le listing -- uniquement dans ContactById
   creer une recherche ne bouge PAS la date_maj du contact
   le run de 03:00 ne relit que les contacts dont l'app connait deja une recherche active
   -> un contact qui gagne sa PREMIERE recherche n'entre dans aucun run. Jamais.
```

**Combien ?** Sonde du 21/08, **249 fiches tirées au hasard et lues en direct** chez Hektor parmi
les 67 483 contacts de typologie « acquéreur » sans recherche connue : **1 seule** portait une
recherche que l'app ignorait. Soit **≈ 270 recherches invisibles**, pas 67 000. *L'image de l'app
est juste à 99,6 %.*

**Ce que la sonde a écarté** : la typologie « acquéreur » **enveloppe** les recherches (aucune
recherche connue hors d'elle) mais elle est posée à la main sur des contacts qui n'ont jamais
rempli de critères, et elle ne bouge pas quand une recherche est créée. **Inutilisable comme
signal.** Il faut relire les fiches.

**Le remède** — `sync_active_searches.py --scope acquereurs`, c'est-à-dire *le run de 03:00 avec
une autre liste d'entrée* : mêmes quatre étapes, mêmes drapeaux, seule la sélection change
(`acquereur_contact_ids`). 71 337 fiches, **≈ 4 h 35**.

> ⚠️ **La pause de 20 s entre les lots ne doit pas être retirée.** Le run de 03:00 tient
> 6 appels/s pendant 10 minutes ; ici il faudrait les tenir 3 h. C'est exactement la forme qui a
> fait **bannir notre IP** au rattrapage des documents. Avec la pause : 4,2 appels/s en moyenne.

**Ce n'est pas un stock, c'est un débit.** La passe du 21/08 remet le compteur à zéro ; le débit,
lui, continue tant que les négociateurs saisissent dans Hektor. D'où **deux** passes, et pas une :

| | Quand | Pourquoi |
|---|---|---|
| **19-R1** | **21/08** — lancée à la main | solde les ~270 accumulées depuis mai |
| **19-R2** | **la veille de la bascule (19bis)** | ⚠️ **dernière occasion.** Tout ce qui aura été saisi dans Hektor entre les deux passes n'existe que là |

Entre les deux, si le délai s'allonge, relancer la même commande de temps en temps — elle est
idempotente et reprenable (chaque lot est indépendant, un lot en échec n'arrête pas le run).

---

## LES TROIS DÉPENDANCES RÉELLES À HEKTOR

| | Ce que Hektor fournit | Comment s'en passer | Délai |
|---|---|---|---|
| **1** | Le numéro de mandat | registre en propre | du code |
| **2** | La signature (ImmoSign) | Yousign | un contrat |
| **3** | **La diffusion portails** | contrats directs ou diffuseur | **contrat + migration commerciale** |

> **Arbitrage Frédéric (20/08) : les contrats démarrent à la fin** (chantier 5), pour préparer la
> coupure. Conséquence assumée : la date sera fixée par leur délai, qui ne commencera à courir
> qu'après le développement. La reprise des 350 annonces en ligne est le seul délai non maîtrisé.

---

## CHANTIER 1 — Maintenant, sans dépendance

| | Quoi | Pourquoi maintenant |
|---|---|---|
| **R1** | **Rebrancher ce qui est irremplaçable** — propositions, relances, retours acquéreur, envois, notifications — par *(contact + search_index)* | **URGENT** : une proposition sur deux a déjà perdu son lien, et rien ne peut la reconstruire |
| **R2** | **Nettoyer le recalculable** — 1 373 rapprochements + 11 966 lignes d'historique | sans risque, **mais seulement après R1** |
| **1.1** | ~~Un échec de worker prévient l'utilisateur et le monitoring~~ **FAIT le 20/08** (`48e475a`) | **indispensable** : un envoi raté laisse une annonce en ligne au mauvais prix |
| **1.2** | **Les recherches acquéreur sont enregistrées** dans l'app | seul endroit où une saisie se perd |
| **1.3** | Le numéro Hektor d'**annonce** a le droit d'être vide | ouvre la création app-first d'annonce |
| **1.4** | ~~**Identité des transactions**~~ **FAIT le 20/08** — 28 980 affaires renumérotées, `app_affaire_id` + `app_dossier_id` posés, clé basculée sur le numéro de l'app, triplet Hektor gardé en clé de réconciliation partielle | **le plus sûr des trois**, vérifié : 0 point d'appel ambigu. ⚠️ **`hektor_affaire_id` n'est unique que dans son type** — 7 541 numéros portés par deux types, 0 partageant l'annonce : Hektor tient trois compteurs qui se télescopent. Le numéro de l'app est **une seule série** pour les trois. Débloque la modale de statut (tâche 13) |
| **1.5** | **Identité des contacts** — renommage préalable, ajouter la case, renuméroter ≈ 186 500 lignes, **puis la case Hektor a le droit d'être vide** | débloque la modale d'ajout : contact + recherche + mandant écrits d'un coup. **Demande une demi-journée de relecture avant** |
| **1.6** | ~~Reprendre `numero_dossier`~~ **-> reporte au jour J** : comprendre la règle de numérotation Hektor et la continuer | référence métier lisible dans 11 tables — **personne ne la fabrique après la coupure** |
| **1.7** | ~~Annuaire négociateurs~~ **-> reporte au jour J** : le worker a besoin de l'`idUser` Hektor pour s'impersonner — 40 + 19, présents dans 14 tables | l'affectation doit survivre sans Hektor |

---

## CHANTIER 2 — Le cœur : Hektor confirme, il n'écrase plus

| | Quoi |
|---|---|
| **2.1** | Écrire la règle : les trois cas d'écart *(envoi pas parti / envoi raté / modifié dans Hektor)* |
| **2.2** | La tolérance de comparaison — la traduction des valeurs existe déjà (`resolveHektorSelectValue`) |
| **2.3** | Brancher au retour du worker *(`push_single_annonce_to_supabase.py:573`)* |
| **2.4** | Même règle sur l'import de nuit |

> **Le garde-fou existe déjà**, côté annonce et côté contact (`base_snapshot` + comparaison
> `date_maj`). Aujourd'hui, en cas d'écart, **Hektor gagne**. La règle 2 **inverse le verdict** :
> l'app garde sa valeur et signale. C'est une modification, pas une construction.

**Puis, dans la foulée :**

| | |
|---|---|
| **2.5** | **Le calque d'annonce disparaît** — il n'existe qu'à un seul endroit : l'édition de champs |
| **2.6** | La barrière : un travail sans numéro Hektor **attend** au lieu d'échouer |

---

## CHANTIER 3 — Appliquer le principe aux 16 workers

**Écrire chez soi d'abord, envoyer ensuite, confirmer au retour.**

| Ordre | Workers |
|---|---|
| **3.1** | Les 3 recherches *(ajouter / modifier / supprimer)* |
| **3.2** | **Statut + affaire** *(offre, compromis, vente)* — le geste le plus riche |
| **3.3** | Archiver / désarchiver / supprimer |
| **3.4** | **Créer un contact, créer un mandant, rattacher** *(après 1.3)* |
| **3.5** | **Affectation du négociateur — en DERNIER** (impersonation du worker) |

**Correctifs à glisser dedans :**

- **3.6** — **Clé propre au registre des affaires** *(28 980 lignes, clé 100 % Hektor)*
- **3.7** — **Fiabiliser le mandat des transactions** : l'app doit toujours le fournir ; aujourd'hui
  le worker le devine dans le HTML de Hektor si elle ne le fait pas
- **3.8** — **La clé de recherche** : aujourd'hui un hachage du contenu, elle change à chaque
  édition — **1 270 rapprochements déjà orphelins**. C'est la seule clé structurellement fausse.
- **3.9** — **Ménage** : `app_contact_override` (vide, non écrite), `app_console_create_update_contact_job`
  (remplacée par l'optimiste), tables `_v1` vides

---

## CHANTIER 3bis — Les recherches deviennent tiennes

**Quatre portes à fermer** — et c'est l'étape qui rend le problème de clé **sans objet** :

| | Porte | Fréquence |
|---|---|---|
| 1 | Run dédié `sync_active_searches` | 03:00 |
| 2 | Run quotidien — `push_contacts` **supprime puis réécrit** | 05:30 |
| 3 | **Read-through** — le MÊME code, avec `--contact-id` | à chaque ouverture de fiche |
| 4 | Les 3 travaux sortants `*_hektor_contact_search` | à l'édition |

**Deux préalables obligatoires :**

| | |
|---|---|
| **R3** | **Corriger le modèle « au moins »** — la modale n'expose que des minimums, le worker sait envoyer 20 critères. Aujourd'hui le run de nuit rattrape ; après la coupure, ce qui n'est pas stocké est **perdu** |
| **R4** | **Mesurer** combien de recherches Hektor portent des critères invisibles dans la modale |

> **Une fois les quatre portes fermées, plus personne ne recalcule le hachage : la clé cesse de
> bouger toute seule.** Le défaut identifié trois fois depuis juin disparaît **sans avoir été
> corrigé** — c'est la solution la plus économique du dossier.

---

## CHANTIER 4 — La création part de l'app

| | Quoi | Dépend de |
|---|---|---|
| **4.1** | **L'annonce** : la création écrit la vraie fiche | 1.4 · 2.3 · 2.6 |
| **4.2** | **Le contact et le mandant** : idem | 1.3 · 2.3 |
| **4.3** | **La modale d'ajout de contact** écrit ses trois objets d'un coup : contact + recherche + relation mandant | 4.2 |
| **4.4** | Les workers deviennent invisibles | **quand l'avertissement d'échec aura fait ses preuves** |

---

## CHANTIER 4bis — Rapatrier les binaires *(à terminer AVANT la coupure)*

| | Quoi | Volume |
|---|---|---|
| **4bis.1** | **Les documents** — `hektor_document_id` pointe vers le stockage de Hektor | **40 493** |
| **4bis.2** | **Les photos** — `hektor_photo_id`, idem | **1 397** |

> Ce ne sont pas des identifiants métier, ce sont **des adresses**. Tant qu'ils pointent vers
> Hektor, ils pointent vers un serveur qui va s'éteindre. **Irréversible : ce qui n'est pas
> descendu avant est perdu.**

---

## CHANTIER 5 — Préparer la coupure : les trois contrats

| | Quoi | Nature |
|---|---|---|
| **5.1** | **Sortie des portails** : combien, chez qui, à quel prix, et **comment reprendre les 350 annonces en ligne sans trou de visibilité** | contrat + migration |
| **5.2** | **Yousign** — l'app ne sait pas *lancer* une signature | contrat + code court |
| **5.3** | **Registre de mandats en propre** — obligation légale, libère `numero_mandat` | code |

---

## CHANTIER 6 — Le jour J, une journée

| | |
|---|---|
| **6.1** | Le distributeur démarre à **100 000**, dans le couloir vide 25 000 → 1 000 000 |
| **6.2** | Le serveur remplit **les deux cases** : les 24 tables qui portent le numéro Hektor continuent sans le savoir |
| **6.3** | Le numéro est **imposé**, pas laissé au compteur local (à 5,25 millions) |
| **6.4** | On éteint l'aspirateur : pipeline, workers, Playwright, file de travaux |
| **6.5** | Les 3 PDF et les 4 workers internes **continuent tels quels** |

---

## LA RÈGLE DES IDENTIFIANTS

> **Pour chaque identifiant que Hektor fabrique, trois questions avant la coupure :**
> **1.** Qui le fabriquera après ? · **2.** Que deviennent les valeurs déjà émises ? · **3.** Qu'est-ce
> qui casse s'il est vide ?
>
> Annonces : répondu. Contacts et affaires : chantier 1. **`numero_dossier`, annuaire, binaires :
> nouvellement identifiés.** Détail : `AUDIT_TOUS_LES_IDENTIFIANTS_2026-08-20.md`.

---

## LES CINQ RÈGLES

1. **Un numéro ne se perd jamais.** *(fait)*
2. **Hektor confirme, il n'écrase pas.**
3. **Une action a toujours une fin visible** — surtout quand elle rate.
4. **Tant que la diffusion passe par Hektor, Hektor doit rester à jour.**
5. **Le miroir se met à jour, il ne se remplace pas.** *(posée le 21/08, tâche 0.2)*

### La règle 5, en clair

`data/hektor.sqlite` — 3,89 Go, 464 952 réponses — est **l'archive de tout ce que Hektor a
jamais dit**. C'est encore lui qui fabrique chaque nuit les 56 890 annonces et les 355 641
contacts, en 37 secondes.

| | |
|---|---|
| **Les mises à jour n'ont pas besoin de suppression** | elles écrasent **en place** : `INSERT ... ON CONFLICT(endpoint_name, object_type, object_id_key, page_key) DO UPDATE SET`. Le miroir grossit et se corrige, il ne se vide jamais pour se remplir |
| **Les suppressions CIBLÉES restent permises** | une annonce (`delete_local_annonce.py`), un contact (`delete_local_contact.py`), les mandats d'une annonce reversés en entier à chaque run (`normalize_source.py`, `refresh_single_annonce.py`), une page de listing réécrite (`sync_raw.py`) |
| **Ce qui est INTERDIT** | supprimer le fichier, le déplacer, vider une table en masse, ou « faire de la place » sur les 3,89 Go |
| **Après la coupure il gèle — il ne devient pas inutile** | il reste la source des annonces jusqu'à C.7, et l'archive ensuite |

> C'est une règle de **conservation**, pas de gel. Elle n'empêche rien de ce qui tourne.

---

## CE QUI RESTE NON MESURÉ

- **La lenteur du front** — la mesure F12 n'a jamais été faite.
- **Les 176 champs du grand bloc** — affichables et modifiables, non filtrables dans les listes.
- **La clé de recherche** — hachage du contenu, elle change à chaque édition : **1 270 rapprochements
  déjà orphelins**.
- ~~**Le coût réel de l'identifiant contact**~~ — **MESURÉ le 23/09** : 28 tables Supabase,
  35 fonctions et vues, 52 tables locales. Voir `notice/AUDIT_COMPLET_AVANT_BASCULE_2026-09-23.md`.

---

## 23/09/2026 — AUDIT COMPLET AVANT LA BASCULE (`L4-c ⑤`)

**« Comment as-tu pu rater cela ? »** — parce que mes audits lisaient du **code** et ne
comptaient jamais la **donnée**, et parce que je mesurais **une famille à la fois**. La
bascule ne casse pas une famille : elle casse **la couture** entre une table reconstruite
chaque nuit et une table qui ne l'est jamais. Et cette couture ne meurt jamais avec une
erreur — elle rend zéro ligne.

Quatre balayages, une seule question : *qu'est-ce qui casse le jour où la VALEUR de
`hektor_contact_id` change ?*

> **LE LISTING COMPLET : `notice/AUDIT_COMPLET_AVANT_BASCULE_2026-09-23.md`**
> 13 corrections bloquantes (C-1 → C-13), 19 gênantes (G-1 → G-19), ce qui est protégé,
> ce qui reste non mesuré, et l'ordre des dix gestes.

**Les trois mesures qui changent la forme du chantier :**

| mesure | conséquence |
|---|---|
| `app_search_registry` : **77 083 / 77 088** lignes ont déjà leur doublure | **les 456 000 lignes qui pendent sous `contact_search_key` ne bougeront pas.** La plus grosse dépendance du projet est **déjà protégée**. Il reste **5** lignes à combler |
| **0** travail en file, **0** `app_contact_pending`, **0** `app_search_pending` | tout le chapitre « travail créé avant, consommé après » **disparaît si l'on bascule file vide**. C'est une règle de procédure, pas un développement |
| **35** fonctions et vues cousent reconstruit ↔ figé *(je disais 11 RPC)* | la traduction des tables figées (**C-13**) règle à elle seule dix des treize bloquants |

**Le premier de tous les défauts** : la **porte** du worker
(`console_job_worker.js:1886-1892`) lève pour tout numéro ≥ 10 M **avant** d'avoir lu la
cible. Après la bascule, tous les contacts sont ≥ 10 M — **plus aucun travail ne part vers
Hektor**. La porte que j'ai écrite pour protéger la bascule est ce qui l'empêche.

**Le plus silencieux** : `app_contact_enqueue_due_pushes`
(`patch_5b_barriere_attente_2026-09-21.sql:62-66`) fait `continue` quand la jointure échoue.
**Aucune édition ne repart**, sans erreur, sans trace — et **la sonde censée le voir joint de
la même façon**, donc la panne est invisible.

### 23/09 — où en est la pile des correctifs

| | état | déployé ? |
|---|---|---|
| **C-1** la porte lit la cible **avant** de refuser | ✅ `d26ad2e` | ✅ **oui** — 4 services redémarrés à 09:48, fichier de 08:56 |
| **C-2** la sonde d'attente voit et **nomme** les deux causes | ✅ `e1ff6fa` | ✅ **oui** — c'est une vue, rien à redémarrer |
| C-3 la table de traduction se refuse elle-même | → en cours | |
| C-4 C-5 C-6 C-9 C-12 | à faire, **dormants** | |

**Deux leçons de ces deux-là, et elles valent pour la suite :**

① **Un contrôle doit être éprouvé contre le défaut qu'il prétend voir.** L'ancienne
assertion de la porte cherchait la **présence** d'une comparaison — que les deux versions
contiennent. Ce n'était pas sa présence qui comptait, **c'était sa place**. Les deux
assertions ajoutées ont été passées sur la version d'avant : **elles y échouent**.

② **L'audit déclasse autant qu'il classe.** C-2 n'était **pas** un bloquant de bascule —
je l'avais écrit trop grave le matin même. Mais en regardant de près, il cachait un défaut
d'**aujourd'hui** : le périmètre éligible ne compte que **61 984** contacts sur 356 000 et
**rétrécit chaque nuit**, si bien qu'une saisie dont le contact en sort est **abandonnée en
silence**. La note a été corrigée : **un plan qui garde une gravité fausse ment deux fois.**

### 23/09, fin de matinée — les sept bloquants du code sont posés

| | commit | déployé |
|---|---|---|
| **C-1** la porte lit la cible avant de refuser | `d26ad2e` | ✅ 10:22 |
| **C-2** la sonde d'attente voit et nomme les causes | `e1ff6fa` | ✅ *(vue)* |
| **C-3** la correspondance arrive entière, ou le build s'arrête | `80b9ae8` | ⏳ run de nuit |
| **C-4** le garde-fou de suppression est branché | `f01217b` | ⏳ run de nuit |
| **C-6** le miroir reste une copie de Hektor | `3b9b086` | ⏳ run de nuit |
| **C-9** notaires et mandants passent la porte | `fced315` | ✅ 10:22 |
| **C-12** les deux photos se lisent avec l'identité | `ff1d67a` | ✅ 10:22 |

**C-5** reste, mais ce n'est pas du code dormant : c'est un **geste de la fenêtre**
*(traduire les 356 156 lignes de `app_contact` en même temps que le patch SQL)*.

**CE QUE CETTE MATINÉE A APPRIS, et qui vaut pour la suite :**

① **Un contrôle doit être passé sur le défaut qu'il prétend voir.** Chaque correctif porte
désormais sa preuve : les assertions ajoutées sont rejouées sur la version d'avant et
**doivent y échouer**. Trois contrôles écrits faux cette semaine, dont un ce matin.

② **L'audit déclasse autant qu'il classe.** C-2 n'était pas un bloquant de bascule — mais il
cachait un défaut d'aujourd'hui. C-4 n'était pas dans le run de nuit mais dans le
rafraîchissement ciblé. **Trois gravités corrigées dans la note le jour même.**

③ **Corriger crée des défauts.** C-6 a changé le contrat de `refresh_contact_inproc.py` ;
**ses deux appelants n'ont pas bougé**, et c'est C-12 qui l'a rattrapé une heure plus tard.
*Un contrat qui change sans ses appelants, c'est une panne qui attend son jour.*

④ **Un nom qui ment finit par tromper quelqu'un.** `fetchFreshContactSearchSnapshot(contactId)`
lisait NOTRE table : le paramètre a été renommé plutôt que de ruser avec une expression
régulière.

### 23/09, fin de journée — le run, la descente, et trois restes

**Le run quotidien et la descente ont été rejoués en plein jour**, exprès, pour éprouver les
onze correctifs serveur avant d'aller plus loin. **45/45 étapes, puis 3/3, zéro erreur.**
La donnée n'a fait que croître.

| ce que le run a prouvé | |
|---|---|
| **G-11** | `annuaire avant 59 222 → a faire entrer 2 763`. **Sans le correctif du matin, 2 763 personnes sortaient de l'annuaire cette nuit** — et ce n'était pas 1 738 comme l'ancienne note le disait |
| **un défaut de mon propre correctif** | la case cible était posée **avant** l'insertion des contacts neufs : les 10 nés cette nuit sont repartis sans elle. Il ne se voyait **qu'en tournant sur des contacts réellement neufs** |
| **le verrou fantôme** | `magasin_annonce_app` est l'**étape 3 de la descente elle-même**. Le correctif a été éprouvé là où il pouvait tout bloquer — et l'étape a travaillé |

**Et une cinquième leçon, qui prolonge les quatre du matin :**

⑤ **Un garde-fou qu'on n'a pas vu se déclencher n'est pas un garde-fou.** Trois trouvés morts
en une journée — `delete_contacts_except_dirty` (C-4), `phase2/.descente.lock`, et l'alerte
manquante sur `GTI Recherches Actives`. Les trois étaient écrits, lisibles, convaincants.
Désormais chaque protection posée est **éprouvée dans les deux sens** : elle doit passer au
vert quand tout va bien **et** crier quand ça va mal. La sonde `data.travaux_en_erreur` a été
la première à subir ce traitement le jour même de sa naissance.

## 24/09/2026 — la première nuit après la bascule, puis l'audit de `C.9`

**Le run de 05:00 a doublé 294 179 identités** dans `app_contact` *(356 166 → 650 353)*, sans
une erreur ni une alerte. Trouvé à la lecture du run, réparé le matin même, cause fermée et
contrôle branché — voir le journal ci-dessus. **Supabase n'a jamais été touché.**

**Vérification complète avant d'ouvrir C.9**, à la demande de Frédéric *(« que ma data est
similaire à il y a 4 jours sauf les mises à jour normales »)* : sauvegarde du 20/09 contre
aujourd'hui, 18 tables, **toutes ont grossi ou tenu** ; 0 orphelin côté Supabase ; santé
**0 critique** ; l'app en réel, **zéro erreur console**. La descente de 07:30 a fini à 07:55,
exit 0 ; elle a levé une alarme *(« critères différents : 1 »)* qui était **un écart du 25/08
devenu visible**, pas une saisie perdue.

**`C.9` est ouvert.** L'audit, fait deux fois dans la journée, a trouvé que presque tout est
déjà posé *(numéro Hektor nullable, clé primaire à nous, distributeur, barrière, recensement)*
— et **trois défauts que la première passe n'avait pas vus**, dont un qui commande l'ordre :
dans le cas normal, **le bootstrap de nuit donnerait un second numéro** à une annonce née dans
l'app, parce qu'il ne la reconnaît que par son numéro Hektor et tourne avant toute adoption.
➡ `notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md` *(§4 : ce que la seconde passe a réfuté
de la première ; §5 : l'ordre C.9-a → C.9-f et le feu vert de chacun)*.

~~**Aucune ligne de code C.9 n'est écrite.**~~ *(vrai le matin ; dépassé le jour même)*

**Dans la journée** : C.9-a (le serveur adopte avant le bootstrap), C.9-b (la sonde « une annonce,
un numéro »), C.9-c (le push n'efface plus une annonce que le serveur ignore), puis C.9-e en trois
pièces après la découverte de **D8** — e1 le rafraîchissement adopte, e2 le worker pose le numéro
Hektor avant de rafraîchir, e3 la création donne le numéro (interrupteur en base, éteint).
**L'essai réel a réussi** : 10 000 000 ↔ 63147, un seul numéro. Le run de jour (12 h 35) et la
descente doivent en donner la preuve de nuit. **Reste C.9-d (dans le build) puis C.9-f.**

**Le soir, C.9-d** : le build tient désormais **le carnet des liens** (`app_relation_registry`) —
pour chaque lien écrit, son identifiant et **la recette exacte qui l'a fabriqué**, prise dans
`add_relation` avant que le rôle soit réécrit *(71 799 liens sur 167 486 le sont : sans le
carnet, C.9-f n'aurait pas pu les figer)*. Doublure : **personne ne le lit** avant C.9-f.
Répété sur copie avec le vrai build : **100 % des recettes refabriquent leur identifiant**,
0 conflit, vraie base intacte. **D6 fait dans la foulée** *(« Vas y »)* : le recensement « connu de
l'app seule » **marque enfin ses départs** (il levait la marque, ne la posait jamais), après une
relecture complète et pleine seulement. Répété : 0 objet « app seule » ce jour, les 26 lignes du
registre étaient des restes de la bascule. **Reste C.9-f**, après une nuit du carnet.
Chaque pièce a son contrôle, éprouvé dans les deux sens ; le détail est dans le bloc C.9 de la liste.
