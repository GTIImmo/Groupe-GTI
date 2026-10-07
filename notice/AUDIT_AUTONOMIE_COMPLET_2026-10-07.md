# AUDIT COMPLET — L'AUTONOMIE VIS-À-VIS DE HEKTOR, CONFRONTÉE AU CODE

**Mercredi 07/10/2026.** Audit demandé par Frédéric : *« vérifie que mon projet et mes codes
actuels correspondent au plan d'autonomie — identité, contenu, lecture, worker, data… Travail
d'expert, ne code rien, lecture seule, rapport détaillé mais explicatif. »*

> **Comment cet audit a été fait.** Dix auditeurs ont travaillé en parallèle, un par dimension :
> identité · contenu · flux entrant · flux sortant (worker) · front · backend / vitrine / RDV ·
> fichiers · les 3 exceptions · exploitation · plan contre code. **Chaque constat grave a ensuite
> été remesuré par un contradicteur indépendant**, chargé de le réfuter. Les chiffres de ce
> rapport sont **ceux qui ont survécu à cette seconde mesure** : quand le contradicteur a corrigé
> un chiffre ou une gravité, c'est sa version qui est retenue ici.
>
> **Strictement en lecture seule.** Aucune écriture en base, aucun appel à Hektor, aucun script
> du projet exécuté, rien de redémarré, aucun commit. Supabase n'a reçu que des `SELECT`
> légers ; les bases locales ont été ouvertes en `mode=ro`.
>
> **Sources mesurées** : le code du dépôt (`C:\Hektor\Projet`), Supabase (projet
> `dwaqxfrinihnychuoptk`), `phase2/phase2.sqlite`, `data/hektor.sqlite`, les journaux du run de
> nuit, les tâches et services Windows, le paquet du front réellement en ligne sur Vercel, le
> `/health` du backend Render et la zone DNS publique de `gti-immobilier.fr`. Ce qui n'a pas pu
> être mesuré est dit au §12.

---

## 0. LA RÉPONSE EN UNE PAGE

### Votre thèse

> *« L'étape 2 est terminée. L'app et le serveur sont complètement autonomes de Hektor : ils ne
> font que récupérer et envoyer des mises à jour. Il ne reste avant la coupure que la fin du
> rattrapage des documents et les 3 points historiques : le numéro de mandat (registre
> électronique perso), la signature électronique, les passerelles publicitaires. »*

### Le verdict

```
LA FONDATION EST BONNE              ████████████████████  vraie
   nos numéros, nos registres, notre mémoire, la chaîne « l'app écrit d'abord »

« L'ÉTAPE 2 EST TERMINÉE »          ██████░░░░░░░░░░░░░░  fausse
   votre propre tableau dit L4 🟡 et L5 à L9 ouverts — le code le confirme

« IL NE RESTE QUE 4 POINTS »        ████░░░░░░░░░░░░░░░░  fausse
   les 4 points sont réels, mais ~20 autres dépendances bloqueraient la coupure
   (dont 5 familles trouvées par le contrôle de complétude : voir §13)

« ON NE FAIT QUE RÉCUPÉRER          ████████░░░░░░░░░░░░  vraie pour l'app le jour,
   ET ENVOYER DES MAJ »                                     fausse pour le serveur la nuit
```

**Trois phrases pour tout résumer :**

1. **La mémoire est à vous.** Si Hektor s'éteignait ce soir, les annonces, contacts,
   recherches, liens, affaires, mandats et photos existants seraient conservés, sous vos
   numéros. C'est le gros du travail, et il est fait.

2. **La capacité d'agir sans Hektor, elle, n'est qu'à moitié construite.** Elle est bonne pour
   *modifier* ce qui existe. Elle ne l'est pas pour *créer* : une annonce créée après la coupure
   n'aurait ni mandant, ni mandat, ni photo, ni document, ni lien RDV, ni vitrine. Ajouter une
   pièce ou une photo passe encore par Hektor d'abord. Une recherche créée dans l'app s'efface
   au bout de 24 h si Hektor ne la confirme pas.

3. **Personne n'utilise encore l'app pour saisir.** Depuis le 15/09, **aucun travail n'a été
   demandé par un négociateur**. Les commerciaux n'ont d'ailleurs **pas le droit** de faire la
   plupart des gestes dans l'app. Les chemins « autonomes » ont été prouvés par des essais, pas
   par l'usage : le premier jour sans Hektor serait leur premier jour réel.

**Et quatre surprises hors code, à traiter avant tout préavis :**

- **la zone DNS de `gti-immobilier.fr`** (et donc la messagerie Google de toute l'agence) est
  servie par les serveurs de **La Boîte Immo** ;
- **les leads des portails** ne passent plus par Hektor depuis le **01/02/2026**, et personne ne
  sait par où ils arrivent ;
- **le site www.gti-immobilier.fr** est hébergé chez l'éditeur de Hektor ;
- **le rattrapage des documents** n'est pas « à une nuit » : il en reste au moins 6, et les
  documents des **biens en vente** ne sont plus relus depuis le **20/08**.

---

## 1. CE QUI EST VRAI — la fondation, à ne pas abîmer

Avant les défauts, ce qui tient. Un audit qui ne voit que les manques ment par omission.

| sujet | ce qui est en place, mesuré le 07/10 |
|---|---|
| **identité du contact** | 356 397 contacts côté serveur, 62 154 dans le cloud, **100 % sous notre numéro** (plage 10–20 M). Le numéro Hektor n'est plus qu'une *cible* (`hektor_target_id`), **0 contact sans cible**. Les sentinelles d'identité sont vertes. |
| **identité de l'annonce** | `app_dossier_id` est la clé partout, en **une seule série** pour les annonces vivantes, archivées, historiques et brouillons : **0 collision** sur 58 225. `annonce_un_numero` : 0 écart sur 13 463. |
| **registres durables** | `app_relation` 132 709 liens, `app_affaire_ledger` 31 047 affaires, `app_mandat` 26 842 mandats : **rien n'y est jamais effacé**. Les retraits de mandant sont datés et nominatifs. |
| **chaîne « l'app écrit d'abord »** | Pour **modifier** une annonce ou un contact, pour les **transactions** et pour **rattacher ou retirer un mandant** : une ligne durable est écrite chez nous, puis le worker livre. Ensuite : 5 essais, puis un conflit visible, puis une relance toutes les 6 h, et **jamais de purge**. Les deux cartes de réclamation (JS et SQL) sont identiques : **42 genres de travaux**, aucun orphelin. |
| **le front** | Il ne lit **que** Supabase et le backend : **0 appel direct à Hektor**. Il appelle 73 RPC, et toutes existent en base. Le code en ligne (Vercel `0487dfc`) est exactement `origin/main`. |
| **photos** | Les **74 992 photos du parc vivant** ont leurs dérivés dans notre coffre public. **13 463 vignettes sur 13 463** pointent chez nous. Les ajouts faits dans Hektor remontent chaque nuit, hors quota. |
| **documents déjà descendus** | 104 477 documents (154 Go) : 21 857 dans le cloud, 82 620 sur le serveur, tous **lisibles sans Hektor**. Les blocs ImmoSign et « Mes documents » sont indexés depuis le 18/08. **300 mandats signés** ont été rapatriés avec leur dossier de preuves. |
| **run de nuit** | Le 07/10 : **54 étapes sur 54**, de 05:00 à 07:20, code 0. Une seule nuit ratée sur 31 (le 19/09, Hektor injoignable). |
| **les deux correctifs du 03/10** | `busy_timeout` sur la descente (`a86a800`), attente de la fin du quotidien (`5cfd576`) : **faits et poussés**. CLAUDE.md les donne encore « à faire ». |
| **sauvegarde** | Veeam / OVH copie la machine entière chaque nuit (succès du 27/09 au 06/10). Un fichier a été restauré pour de vrai depuis le coffre le 19/08. *(L'audit du 01/10 disait « aucune restauration » : c'était faux.)* |
| **gestes de Frédéric du 03/10** | Pousser, `busy_timeout`, garde d'ordonnancement, essai `degroupproprio` : **4 sur 4 faits**. |

➡ **Votre diagnostic sur l'architecture est juste** : l'app écrit chez elle, le worker livre,
le run de nuit rapporte. Le problème n'est pas la direction prise. C'est que la route n'est pas
finie, et que la carte qui dit « terminé » est en avance sur le terrain.

---

## 2. « L'ÉTAPE 2 EST TERMINÉE » — ce que dit votre propre plan

Votre charte du 20/09 définit l'étape 2 : *« mon logiciel assure toutes ses fonctions actuelles
sans Hektor, sauf trois »*. Elle la découpe en **dix lots**, chacun avec un critère
*« Fini quand »*. Voici chaque critère confronté au code.

| lot | « Fini quand » (le plan) | ce que dit le code | verdict |
|---|---|---|---|
| **L0** ne plus rien perdre | aucune saisie ne disparaît sans trace | Vrai pour les **modifications**. Faux pour les **créations** : une ligne provisoire (recherche, lien, contact, annonce) est effacée 24 h après un échec (`app_sweep_stale_provisionals`, chaque minute). | 🟡 |
| **L1** les numéros à la naissance | un contact, **une recherche**, un bien naissent dans l'app avec leur numéro | Contact ✅, annonce ✅. **Recherche ⛔** : son distributeur `app_search_id_app_seq` n'a **jamais servi** (`last_value = NULL`). | 🟡 coché à tort |
| **L2** les corps chez l'app | le serveur tient un objet que le miroir ignore | Vrai pour le contact (recensement) et le lien. **Faux pour l'annonce** (corps refait chaque nuit depuis le miroir, N.4/26bis-3 ouvert) et pour la transaction (26bis-TRANSACTIONS ouvert). | 🟡 coché à tort |
| **L3** la récence par champ | le run confirme, il n'écrase plus | En réalité **« écraser puis reposer »** : le push réécrit depuis Hektor, puis les saisies en attente sont reposées une seconde plus tard. Aucune saisie n'est perdue, mais l'énoncé n'est pas celui du code. | ✅ avec réserve |
| **L4-b′ / L4-c** fermer la porte, une personne un numéro | — | Faits et vérifiés. | ✅ |
| **L4** la création part de l'app | on crée sans attendre Hektor | Le mécanisme existe, mais **0 création réelle depuis le 25/09**. C.9-couple, 26bis-TRANSACTIONS et 4.3 sont ouverts. | 🟡 (le plan le dit) |
| **L5** les gestes manquants | **plus aucun écran ne renvoie vers Hektor** | **Pas commencé.** Il reste **16 points d'entrée « Ouvrir Hektor » vivants**. Le contrôle de baisse de prix lit Hektor. Ne savent pas se faire dans l'app : modifier un mandat existant, gérer les photos, fusionner des doublons, reprendre un brouillon. | ⛔ |
| **L6** ce que Hektor fait remonter | les trois exceptions remontent proprement, le reste ne remonte plus | Partiel. Les documents des biens en vente ne remontent plus depuis le 20/08. Le critère « le reste ne remonte plus » **contredit** la décision du 21/09 (« les commerciaux saisissent encore dans Hektor »). | ⛔ |
| **L7** les fichiers chez l'app | afficher un document ou une photo ne dépend plus de Hektor | **Afficher** ✅. **Ajouter** ⛔ : Hektor d'abord (G.5 dormant). | 🟡 |
| **L8** exploitation et bascule | **les négociateurs travaillent dans l'app** | **Pas commencé.** 8 comptes, 7 profils, 0 négociateur actif, 0 travail demandé par un commercial. | ⛔ |
| **L9** registre des mandats | un mandat neuf s'enregistre sans Hektor | La phase 1 (la donnée) est faite. La série légale, l'inaltérabilité, C.13-c et l'export manquent. | 🟡 (cité par vous) |

**Conclusion du §2.** Votre page d'accueil le dit elle-même, `CLAUDE.md` ligne 142 :
`L0 ✅ L1 ✅ L2 ✅ L3 ✅ L4 🟡 puis L5 L6 L7 L8 L9`. **L'étape 2 n'est pas terminée selon votre
propre définition.** Et deux des lots cochés ✅ (L1, L2) ne couvrent pas leur énoncé, ce qui
enfreint la règle de CLAUDE.md §4 : *« une tâche n'est cochée que si son ÉNONCÉ est couvert »*.

---

## 3. LA GRILLE OBJETS × GESTES — l'état réel, toutes dimensions confondues

> ✅ = l'app écrit **chez elle d'abord**, Hektor suit · 🟡 = marche aujourd'hui, mais dépend de
> Hektor pour exister ou se compléter · ⛔ = le geste n'existe pas, ou ne survivrait pas à la
> coupure · ⚙ = décision écrite

| | créer | modifier | supprimer / archiver | lire / remonter |
|---|---|---|---|---|
| **annonce** | 🟡 notre numéro, mais **une façade de 11 champs** ; le corps (≈ 180 champs) ne vit que dans le travail envoyé à Hektor ; **0 création réelle depuis le 25/09** | ✅ calque + file d'attente · ⚠ réservé admin/manager | ⚙🟡 suppression : Hektor d'abord (30/08) · ⛔ **archiver / restaurer / changer le négociateur** : l'intention va dans un carnet **que personne n'applique** | ✅ l'écran lit Supabase · 🟡 le corps serveur est refait chaque nuit depuis le miroir |
| **contact** | ✅ ligne durable ≥ 20 M · 0 en réel | ✅ | ⚙🟡 Hektor d'abord | ✅ |
| **recherche** | ⛔ **ligne provisoire seule**, effacée 24 h après un échec, jamais rapprochée | ✅ propriété de l'app (C.3) | ⚙ archivage envoyé sans retour (20/09) | ✅ |
| **relation (mandant)** | ✅ ligne durable · ⛔ **refusée sur une annonce sans numéro Hektor** · ⛔ les mandants saisis **à la création d'une annonce** ne passent que par Hektor | — | ✅ retrait daté, prouvé le 03/10 | ✅ registre · 🟡 les droits de voir un contact lisent encore l'ancienne table refaite chaque nuit |
| **transaction** | ✅ au cloud · 🟡 le corps (offre, compromis, vente) est fabriqué **chez Hektor** ; le serveur ne la tient qu'une fois revue de Hektor | ✅ | ✅ | ✅ · 🟡 le chaînage offre → compromis → vente se fait sur les numéros Hektor |
| **mandat** | ⛔ numéro PROTEXA via Hektor (cité par vous) · le chemin app n'a servi **que 3 fois**, la dernière le 28/08 | ⛔ aucun geste (l'avenant ne change que le prix) | 🟡 clôture chez nous, mais 2 usages seulement | ✅ registre `app_mandat` · 🟡 lui-même refait depuis le miroir |
| **document** | ⛔ **Hektor d'abord**, y compris pour les 3 PDF que nous générons (avis de valeur, mandat, cadastre) | — | 🟡 Hektor d'abord, et notre copie est effacée | 🟡 archives à 96 %, ventes à 0,5 %, **biens en vente figés depuis le 20/08** |
| **photo** | ⛔ Hektor d'abord (robot navigateur) | ⛔ réordonner, photo principale : n'existent pas | ⛔ n'existe pas | ✅ parc vivant à 100 % chez nous · 🟡 c'est Hektor qui décide quelles photos « existent » |
| **RDV / visite** | ✅ Google Agenda sans Hektor · 🟡 lien public créé **seulement** si l'annonce a un numéro Hektor | non mesuré | non mesuré | ⛔ fiche visite PDF fabriquée **par Hektor** · ⛔ l'agenda des visites Hektor n'est importé nulle part |
| **diffusion** | ⛔ API Hektor (cité par vous) | ⛔ idem | ⛔ idem | ✅ état remonté chaque nuit (réparé le 30/09) |
| **signature** | ⛔ s'ouvre **dans Hektor** (cité par vous) | ⛔ relance via ImmoSign/Hektor | ⛔ annulation via ImmoSign/Hektor | ✅ suivi d'état, PDF signé et preuves rapatriés |

**Ce que la grille dit, et qu'aucun total ne dirait.** Les trois piliers (annonce, contact,
recherche) sont solides **en modification**. Les **créations**, les **fichiers** et les gestes
**de fin de vie** (archiver, supprimer, clôturer) dépendent encore de Hektor, soit pour exister,
soit pour s'afficher. Une coupure demain figerait le stock proprement, mais empêcherait de faire
**naître** un objet complet.

---

## 4. LES 4 POINTS QUE VOUS AVEZ CITÉS — leur état réel

### 4.1 (a) « La fin du rattrapage des documents » — c'est bien plus qu'une fin

`CLAUDE.md` §2 dit *« ~2 500 restantes → UNE nuit »*. **C'est une erreur de lecture** : le
journal affiche un **curseur** (« balayées / déjà marquées »), pas un total.

```
CE QUI RESTE À SCANNER (Supabase, croisement index × empreintes, 07/10 au matin)
   archives            1 250 / 35 317   (dont 784 archives « pro », jamais scannées)
   historique (VENTES) 8 895 /  8 937   ← les biens VENDUS : compromis, actes, mandats soldés
   brouillons            508 /    508
   ------------------------------------------------------------
   ≈ 10 650 annonces    rythme : 2 500 par nuit, UN seul périmètre par nuit
```

**Cinq choses que le compte « une nuit » ne disait pas :**

1. **Au moins 6 nuits, probablement jusqu'à fin octobre.** Le mode `--scope auto` ne prend
   qu'un périmètre par nuit (`enqueue_empreinte_lot.js:153-158`). Ce soir, seulement 1 250
   archives. Ensuite, les ventes portent en moyenne **24,3 documents par annonce** (contre 2,7
   pour les archives). Un lot de 2 500 ventes coûterait 40 000 à 70 000 requêtes, soit **20 à
   36 h** : il ne tient pas dans une nuit. *(Estimation, sur un échantillon de 42 ventes
   récentes.)* Prévoir aussi **+137 à +273 Go** de disque.

2. **Les 508 brouillons échoueront tous.** `loadDossier` (`console_job_worker.js:1877-1929`) ne
   sait pas chercher dans l'index des brouillons. Le lot lèvera 508 fois « Dossier
   introuvable ». La nuit suivante, la tâche refusera de tourner (≥ 20 erreurs). Puis la règle
   « ne jamais rejouer » les exclura pour toujours, et le contrôle dira « rien à faire ».
   **Ce défaut n'est écrit nulle part.**

3. **Les documents des BIENS EN VENTE ne sont plus relus depuis le 19-20/08.** C'est le point
   le plus grave de tout le chapitre fichiers. 13 036 des 13 037 empreintes du parc vivant
   datent d'août. **13 documents sur 19 874** ont été synchronisés en 30 jours. Le rattrapage
   ne regarde que les archives, les ventes et les brouillons, jamais le parc vivant. Ce qui
   manque donc chez nous :
   - tout mandat, compromis, avenant ou diagnostic déposé dans Hektor depuis le 20/08 sur un
     bien en vente ;
   - **132 biens en vente jamais lus, dont 97 créés après le 20/08** : chaque nouveau mandat
     arrive sans aucun document chez nous (environ 2 par jour).

   **Finir le rattrapage ne rattrape pas cela.**

4. **Le relais ne peut pas être « simplement allumé ».** Le geste ⑤ de CLAUDE.md
   (`-EnqueueConsoleDocuments`) empilerait, tel quel, **les 13 463 annonces vivantes chaque
   nuit**, soit plus de 27 h de travail par nuit. La file ne se viderait jamais. La tâche G.2
   (une détection limitée aux ~724 biens en vente) doit être écrite **avant**.

5. ~~**3 136 annonces de location ne sont dans aucun périmètre**~~ — **corrigé par le contrôle
   de complétude (§13)** : une fois les chiffres dépliés, 673 des 675 locations « actives » sont
   rangées dans l'agence « Agences supprimée » au statut « Mandat clos ». C'est une ancienne
   activité de gestion, morte depuis 2020-2022. Il ne reste que **2 vraies locations vivantes**
   (62309 et 62504). Leur sort, et celui d'une éventuelle carte G, reste **à trancher**.

Et deux restes plus petits :
- **230 documents** sont indexés **sans fichier**. La plupart sont des synchros tuées par le
  bannissement d'IP du 20/08. Seul Hektor les a encore, dont des mandats et un avenant
  « AVT 87 000 € ».
- **111 annonces** ont été lues en août quand elles étaient vivantes, puis vendues : leurs
  pièces de fin de vie (compromis, acte) ne seront **jamais** relues par le rattrapage.

### 4.2 (b) Le numéro de mandat et le registre — confirmé, et plus large que « un registre »

**Confirmé.** Le numéro sort de l'étape PROTEXA `valideStep1`, rejouée chez Hektor
(`console_job_worker.js:15470-15478`). L'app ne sait pas en fabriquer.

**Mais un « registre électronique perso » ne suffira pas.** Voici ce qui manque, mesuré :

| il faut | état aujourd'hui |
|---|---|
| **une série légale** continue, sans trou | ⛔ n'existe pas. La seule séquence (`app_mandat_id`) est un identifiant interne. Elle a **déjà 2 numéros brûlés** sans ligne : elle ne peut pas servir de numéro légal. |
| **l'inaltérabilité** (journal, horodatage tiers) | ⛔ aucun déclencheur, aucun journal. La clé de service peut tout réécrire, et **le run réécrit chaque nuit** type, dates et mandants depuis le miroir (`mandat_ledger.py:546-566`). |
| **un export / une impression** pour un contrôle | ⛔ l'écran du registre n'a ni export, ni CSV, ni impression. |
| **détacher le registre du miroir** | ⛔ il est construit `FROM hektor.hektor_annonce` (`export_app_payload.py:747`). `app_mandat` exige le numéro Hektor de l'annonce (`NOT NULL`, clé unique `(hektor_annonce_id, numero_mandat)`). Un mandat posé sur une annonce née après la coupure **ne trouverait pas sa place**. |
| **le contenu complet dès la création** | ⛔ le worker n'écrit que 5 champs, avec ce commentaire : *« C'EST LE RUN QUI COMPLETE »*. |
| **les avenants et les mandats de recherche** | ⛔ **ils prennent leur numéro dans LA MÊME série PROTEXA** : 18500 est un avenant, 18267 et 18747 sont des mandats de recherche. L'app n'a aucun chemin pour eux. Un distributeur qui ne connaîtrait que les mandats de vente ferait des trous dès le premier jour. |
| **expliquer les trous de 2026** | 28 numéros manquent entre 18264 et 18924 ; 3 sont expliqués par nos données ; **25 restent inexpliqués**. Seul l'export complet de PROTEXA le permettra, **et il faut l'obtenir avant la coupure**. |
| **le montant** | Il a été retiré de `app_mandat` le 06/10 ; le registre affiche le **prix de l'annonce** sous l'intitulé « Montant ». Acceptable pour un outil de travail, pas pour un registre légal : à faire valider par le juriste. |
| **les dates de clôture** (C.13-c) | 118 sur 24 494 lignes. |
| **la décision « continuer la série PROTEXA ou repartir de 0 »** | Deux positions contradictoires coexistent (mémoire du 28/09, plan l.172). **Aucune n'est écrite au journal des décisions.** |

**⛔ Deux défauts DORMANTS dans le code déjà écrit (l'étape D du 30/09, jamais exercée en réel).**
- **Le premier vrai mandat créé depuis l'app casserait l'envoi nocturne de `app_mandat`.** La
  copie locale de Supabase n'est pas rafraîchie avant l'étape du registre (la « doublure »
  annoncée n'a jamais été branchée, `run_full_pipeline.ps1:819-824`). Le run attribuerait un
  second identifiant, Supabase refuserait la ligne au nom de la contrainte d'unicité, et **cela
  recommencerait chaque nuit**.
- **Le format de date** : le worker écrit `JJ-MM-AAAA`, alors que les 24 768 lignes existantes
  sont en ISO.

**Usage réel** : 73 numéros PROTEXA en septembre-octobre, **tous faits directement dans
Hektor**. 0 par l'app depuis le 28/08.

**Effort estimé** (à confirmer) : 3 à 5 semaines de développement, plus le juriste,
l'horodatage tiers et l'export PROTEXA.

### 4.3 (b) La signature électronique — confirmée, dépendance totale

Le PDF du mandat est fabriqué chez nous. **Le reste est chez Hektor** :
- le lancement de la signature ouvre un onglet Hektor (*« le négociateur valide + envoie à la
  main »*, `App.tsx:5427-5433`) ;
- la relance et l'annulation passent par ImmoSign via Hektor ;
- le jeton ImmoSign se lit dans une iframe Hektor.

**Il n'existe aucune ligne de code pour un prestataire direct** (Yousign ou autre).

À savoir :
- **le bouton « Signature » vise probablement une adresse morte AUJOURD'HUI.** Le paquet en
  ligne contient 6 fois l'ancien domaine `groupe-gti-immobilier.la-boite-immo.com` (la
  variable `VITE_HEKTOR_BASE_URL` n'est pas posée sur Vercel). Selon la mémoire du projet, ce
  domaine **n'authentifie plus depuis le 11/09**. *(Non vérifié en réel : tout appel à Hektor
  était interdit. Un clic suffit pour le confirmer.)* ;
- les scripts d'exploration ImmoSign (`Console/immosign_*.js`, 16 fichiers) **ne sont pas dans
  git**. Ils lisent le jeton dans l'iframe Hektor, donc ne serviront pas tels quels ;
- **50 procédures sont en cours** (48 mandats, 2 bons de visite). Elles devront être soldées
  avant la coupure. Pour les mandats signés, **299 sur 300 ont leur ZIP de preuves** : c'est
  bon ;
- la voie « signature manuscrite » ne sert pas de repli autonome : elle suppose le dépôt du
  PDF, et ce dépôt passe par Hektor (§5, B3).

**Effort estimé** : 1,5 à 3 semaines une fois le contrat signé.

### 4.4 (b) Les passerelles — confirmées, et ce n'est PAS « seulement commercial »

L'audit du 01/10 écrivait *« ce n'est pas une exception technique, l'API existe déjà »*.
**C'est faux pour l'après-coupure** : l'API en question est **celle de Hektor**, elle disparaît
avec lui.

Ce qui manque :
- **un générateur de flux d'annonces** au format d'un diffuseur : **0 ligne aujourd'hui** ;
- des **références stables** reconnues par les portails (aujourd'hui, Leboncoin affiche la
  référence Hektor) ;
- la **réception des leads** ;
- un **suivi** de ce qui a vraiment été publié.

État actuel : **346 annonces en ligne, 1 523 diffusions sur 5 portails**, toutes pilotées dans
Hektor. Depuis l'app, la dernière demande date du **25/05**.

Corrections à l'audit du 01/10 et à CLAUDE.md :
- l'écran **applique et relit** bien la diffusion (`handleCommitDiffusionTargets`). Le défaut
  « souhait au lieu de confirmation » est **plus étroit** qu'écrit : il n'existe que quand
  Hektor répond mais refuse une partie ;
- la logique d'appel à l'API Hektor existe en **4 exemplaires** : le backend, une fonction
  Supabase, et deux scripts phase2. Les 4 seront à retirer.

**Effort estimé** : 2 à 4 semaines pour le flux et le suivi, plus les leads, plus les contrats.

---

## 5. CE QUE LA THÈSE OUBLIE — les dépendances qui bloqueraient aussi la coupure

> Classées par famille. Pour chacune : **ce qui se passe**, **ce que ça veut dire pour
> l'agence**, **la preuve**. Toutes ont été confirmées ou corrigées par un contradicteur.

### B1 — Une annonce née après la coupure serait orpheline ⛔ BLOQUANT

**Ce qui se passe.** Une annonce créée dans l'app reçoit bien **notre** numéro. Mais tout ce
qui s'y rattache exige encore **le numéro Hektor** de l'annonce :
- **16 tables vivantes** déclarent `hektor_annonce_id NOT NULL` : photos, documents, liens,
  mandats, registre, diffusion, liens et demandes RDV, Matterport ;
- **4 clés d'unicité** reposent dessus (lien, mandat, photo, document) ;
- **8 fonctions** lèvent `missing_hektor_annonce_id` : rattacher, retirer ou créer un mandant,
  modifier un mandant, numéro de mandat, modifier, supprimer, Matterport.

Aujourd'hui, on ne le voit pas, parce que Hektor donne son numéro en moins d'une minute.

**Pour l'agence, après la coupure** : sur une nouvelle annonce, ni mandant, ni mandat, ni
photo, ni document, ni diffusion, ni lien RDV. Ses offres, compromis et ventes ne seraient même
pas chaînés : trois dossiers au lieu d'un.

**⚠ Un défaut probable dès aujourd'hui** (lu dans le code, non exécuté) : le front envoie
`String(dossier.hektor_annonce_id)`, c'est-à-dire le **texte « null »**, qui **passe** le
garde-fou (`api.ts:8122, 9230`). Sur une annonce sans numéro Hektor, un administrateur créerait
alors une ligne de lien dont le numéro de bien vaut « null ». Le cas typique : créer une annonce
et ajouter son mandant dans la foulée.

**Le travail est sur le schéma, pas sur les données** : `app_dossier_id` est déjà rempli à 100 %
dans ces tables. Mais c'est lui qui est facultatif, et la colonne Hektor qui est obligatoire,
**exactement l'inverse de la cible**. Le plan prévoyait « la case Hektor devient facultative »
(chantier d'identité, étape 3) : fait **pour la fiche seulement**.

### B2 — Créer, c'est encore attendre Hektor ⛔ BLOQUANT

| objet | ce que l'app écrit au moment du geste | le reste |
|---|---|---|
| **annonce** | 11 champs métier dans `app_dossier_current`, rien dans la fiche détaillée | les ≈ 180 autres champs ne vivent que dans la charge du travail envoyé à Hektor |
| **recherche** | une ligne **provisoire**, avec une exception qui avale toute erreur | **effacée 24 h après** (même après un succès). Elle n'est **jamais rapprochée**, et pas rejouée si l'envoi échoue. |
| **mandants saisis à la création d'une annonce** | **rien** chez nous | rattachés ou créés **uniquement chez Hektor** (`console_job_worker.js:19761-19862`) |
| **transaction** | la ligne du registre | le corps (offre, compromis, vente) est fabriqué **chez Hektor** par le worker |

**Pour l'agence, après la coupure** : une recherche saisie s'affiche 15 minutes, passe en
« création expirée », puis disparaît. Une annonce n'a qu'un titre, un prix et une ville.
**Aujourd'hui déjà**, il suffit que le worker soit arrêté 15 minutes pour qu'une recherche créée
disparaisse de l'écran le lendemain. **La règle n°1 « une saisie ne se perd jamais » ne couvre
que les modifications, pas les créations.**

### B3 — Ajouter un document ou une photo : Hektor d'abord ⛔ BLOQUANT

Le document ou la photo part chez Hektor. **La ligne n'existe chez nous qu'après sa
confirmation.** Les trois PDF que nous fabriquons nous-mêmes (avis de valeur, mandat, plan
cadastral) suivent le même chemin.

Le chemin « notre serveur d'abord » est **écrit mais dormant** :
- `console_job_worker.js:7832` et `8071` portent la mention « DORMANT » ;
- le front n'a que le droit `SELECT` sur ces deux tables ;
- aucune fonction ne crée la ligne. C'est la tâche **G.5**, non faite.

**Pour l'agence, après la coupure** : plus aucun ajout de pièce, de photo ou de PDF généré. Le
fichier reste dans un dossier temporaire, invisible.

### B4 — Des gestes quotidiens qui n'existent pas, ou qui ne s'appliquent pas ⛔ BLOQUANT

- **Archiver, restaurer, changer le négociateur.** L'intention est notée dans un carnet
  (`app_annonce_champ_app`), mais **rien ne la recopie jamais sur l'annonce** : le contrat
  d'autorité de l'annonce est **vide** (`CHAMPS_APP_ANNONCE = ()`), et l'applicateur « viendra
  ici » selon le commentaire du run. Le plan affirme *« le jour de la coupure, l'app gagne de
  fait »* : **c'est faux pour ces trois champs**. Une annonce archivée depuis l'app resterait
  « active » partout. Le **motif d'archivage** (vendu par un confrère, à quel prix) n'est gardé
  dans aucun champ chez nous.
- **Photos** : supprimer, réordonner, choisir la principale. Le geste n'existe pas, et ce que
  vous faites dans Hektor ne remonte pas non plus : **350 photos retirées dans Hektor sont
  toujours affichées**, et 33 biens en vente ont une autre photo principale chez nous.
- **Modifier un mandat existant** (type, dates) et le **prolonger** : impossible. Les mandants,
  eux, se corrigent bien depuis le 03/10.
- **Fusionner des doublons, reprendre un brouillon** : ces gestes ouvrent Hektor.
- **Supprimer** une annonce, un contact, un document : Hektor d'abord (décision du 30/08),
  **à inverser le jour J**, et c'est impossible pour une annonce sans numéro Hektor.

### B5 — Accepter une baisse de prix demande son avis à Hektor ⛔ BLOQUANT

Le backend lit **le prix chez Hektor** pour valider la demande (`hektor_bridge.py:410-427`,
`475-495`). Si Hektor ne répond pas, il affiche *« Opération refusée : Prix différent Hektor »*,
**un faux motif**. L'écran ne propose alors que « Fermer » ou « Lien Hektor », et ce lien vise
l'ancien domaine.

Ce n'est pas une passerelle : c'est un contrôle de gestion, prévu au lot L5 et non fait. *(Le
circuit dort aujourd'hui : dernière baisse acceptée le 13/05.)*

### B6 — Le run de nuit ne sait pas vivre sans Hektor ⛔ BLOQUANT

**Sa 1re étape (`sync_raw`) est bloquante.** Si Hektor ne répond pas, le run s'arrête en
1 à 2 minutes, et **les 53 autres étapes ne tournent pas**. Le 19/09, toute la nuit a été
perdue ainsi. Une **2e étape bloquante** interroge Hektor : l'annuaire des négociateurs et des
agences. Elle **efface sans plancher** ce que Hektor ne renvoie pas : une réponse vide ou de
forme nouvelle viderait l'annuaire (B11).

Surtout, les étapes « propres à l'app » **lisent le miroir**, pas Supabase :
- **la vitrine publique** est fabriquée depuis `app_view_generale`, refaite depuis le miroir,
  puis croisée avec `hektor.hektor_annonce`, `hektor_agence` et `hektor_negociateur`. Le prix,
  le statut, l'archivage et « diffusable » qu'elle publie viennent **du miroir**. Un prix
  modifié dans l'app n'arrive sur l'écran d'agence qu'après un aller-retour par Hektor ;
- les dérivés photos, les adresses photos et Matterport n'ont pas d'autre déclencheur que ce
  run.

Le plan dit seulement *« 6.4 on éteint l'aspirateur »*, puis *« 6.5 les 3 PDF continuent tels
quels »*. Or ces PDF passent par le même worker, qui refuse tout travail quand l'interrupteur
Hektor est coupé. **Personne n'a écrit le run d'après la coupure.**

### B7 — Le serveur n'est pas maître du corps de l'annonce 🟡 date de péremption

- Le corps de l'annonce côté serveur (`app_view_generale`) est **supprimé puis recréé chaque
  nuit depuis le miroir** (`view_generale.py:35-37`).
- Le contrat d'autorité de l'annonce est **vide** : la nuit, Hektor gagne, puis les saisies en
  attente sont reposées.
- Le « 189/189 champs en local » de CLAUDE.md mesure **une copie du cloud** refaite à chaque
  descente, pas un corps propre au serveur.
- Le serveur **n'adopte un objet né dans l'app que si le miroir le connaît**
  (`descendre_correspondance_annonces.py`).

C'est le **N.4 / 26bis-3** de votre plan, marqué « date de péremption » : son remplissage vient
du miroir. Nuance du contradicteur : la **donnée** n'est pas en danger, puisque le serveur
reçoit chaque matin une copie complète du cloud. Ce qui manque, c'est **le branchement** : faire
de cette copie la source au lieu du miroir.

### B8 — Le côté public est encore indexé sur Hektor 🟡 date de péremption

- **Les liens RDV et la vitrine** sont créés et résolus par le numéro Hektor. Une annonce sans
  numéro Hektor **n'aurait ni QR, ni page RDV, ni place en vitrine**, ne serait proposée dans
  **aucun email de rapprochement** et serait retirée des relances sans un mot
  (`relance_worker.py:49-55`).
- **La fiche visite PDF** de la page RDV est fabriquée **par Hektor** (`pdf.php`).
- **Les vignettes DPE/GES** sont servies par le CDN de Hektor, y compris dans **l'espace client
  envoyé aux acquéreurs**. C'est **notre** code qui fabrique ces adresses
  (`export_app_payload.py:24`).
- Le **logo du PDF de mandat** est chargé sur `www.gti-immobilier.fr` (`mandat-template.html`).
  La case G.14 le croyait réglé : elle n'avait traité que les emails.
- L'**avis de valeur PDF** prend ses photos chez Hektor (`console_job_worker.js:6116-6133`).

**⚠ Une correction importante à la recette prévue (11bis ①).** Passer les QR au **jeton**,
comme prévu, **fabriquerait des QR qui meurent**. Le jeton n'est **pas stable** : quand une
annonce sort de la vitrine une nuit, son lien est désactivé, et à son retour un **nouveau**
jeton est créé ; l'ancien répond 404. **81 annonces ont déjà eu plusieurs jetons** (jusqu'à 9),
et 34 annonces actives ont un jeton mort. Il faut d'abord rendre le jeton stable.
Aujourd'hui, `?ref=<n° Hektor>` est paradoxalement la forme la plus durable. Les QR déjà
imprimés **ne meurent pas seuls** à la coupure : leur numéro est résolu dans **notre** table.

**À relativiser** : la page RDV publique n'a **jamais enregistré une seule demande** depuis le
29/04, et ses créneaux sont en partie fictifs. L'enjeu réel est la **vitrine** et les
**annonces futures**.

### B9 — Le nom de domaine, la messagerie et le site web 🔴 HORS CODE, à traiter avant tout préavis

**La découverte la plus lourde de conséquences de l'audit**, mesurée dans le DNS public :

```
gti-immobilier.fr     titulaire : GTI Immobilier · registraire : OVH · expire le 18/03/2028   ✅
   serveurs DNS       ns1.la-boite-immo.fr · ns2.la-boite-immo.fr                            ⛔
   messagerie (MX)    Google Workspace · SPF « include:la-boite-immo.fr » · DKIM · DMARC
   www                même machine que l'administration Hektor (92.222.237.145)
```

**Le domaine est à vous. Mais l'annuaire du domaine (la zone DNS) est tenu par La Boîte Immo.**
C'est lui qui dit au monde où livrer les mails `@gti-immobilier.fr`. Si l'éditeur cesse de
servir la zone à la résiliation :
- **plus aucun email** n'arrive aux négociateurs ni à `accueil@` ;
- les emails envoyés par l'app (rapprochement, estimation, RDV) ne sont plus délivrés ;
- **le site www tombe**.

**Le remède est entre vos mains**, et il doit précéder le préavis :
1. recréer la zone chez OVH : 7 MX Google, SPF, DKIM, DMARC, les vérifications Google et Apple,
   `mail` ;
2. puis y faire pointer le domaine.

À traiter **en même temps** : où héberger le site public, aujourd'hui sur la machine de Hektor.

Ce sujet **n'apparaît nulle part** dans le plan, la liste ni CLAUDE.md.

### B10 — Les leads des portails : le canal est inconnu depuis février 🔴

Hektor ajoutait les demandes des portails dans le champ « commentaires » du contact :
*« LeBonCoin le JJ-MM-AAAA : Bonjour, ce bien pourrait m'intéresser… »*. 1 563 contacts pour
Leboncoin, 355 pour Bien'ici. **Ces messages s'arrêtent net le 01/02/2026** (362 en janvier, 19
le 1er février, puis 0), alors que le miroir est à jour.

**Depuis février, personne ne sait par où arrivent les leads.** L'app n'a aucune entrée pour
eux. *(Piste trouvée par le contrôle de complétude, §13 : Hektor a un module **Leads**,
« Demandes en attente », avec une API documentée `listLeads` que nous ne lisons pas. Les leads
y arrivent peut-être depuis février. À vérifier en le demandant aux négociateurs.)* Les leads sont hors du périmètre de l'étape 2 (charte), mais **ils se perdraient à la
coupure** si une partie transite encore par Hektor. **À établir avant.**

### B11 — Les négociateurs, les agences et les droits ⛔ BLOQUANT

- **L'annuaire** (qui est négociateur, de quelle agence, son téléphone) est **recopié de
  Hektor chaque nuit**. Les créneaux RDV, la répartition des commissions, le lien avec Google
  Agenda et la vitrine sont rangés sous le **numéro Hektor du négociateur**. Un nouveau
  collaborateur se crée dans Hektor (décision du 19/09). **Après la coupure, un négociateur
  embauché n'existerait nulle part**, et il ne pourrait même pas créer sa première annonce
  (`agency_forbidden`).
- **Les droits de l'app sont écrits en « types de travaux Hektor ».** Un commercial ne peut
  demander que 7 types de travaux (documents, signature). Il **ne peut pas** :
  - modifier une annonce (`forbidden_update_annonce`) ;
  - rattacher un mandant ;
  - ajouter une photo ;
  - générer un mandat PDF ou un avis de valeur ;
  - demander un numéro de mandat.

  Archiver et changer le statut sont réservés à l'admin, pas même au manager.
- **Les négociateurs n'ont pas de compte** : 8 comptes, 7 profils (3 admin et 2 commerciaux
  actifs), contre **39 négociateurs** qui portent des annonces vivantes. Les deux comptes
  commerciaux n'ont **aucune session** en 30 jours.

**Incohérence d'ordre dans le plan** : la liste place **F.1** (utilisateurs, rôles, droits)
**après** la coupure, alors que **E.2** (les négociateurs passent sur l'app) doit la précéder.

### B12 — Le numéro de dossier EM…/VA… 🟡

C'est la référence que l'agence lit partout (mails, documents, vitrine), et c'est Hektor qui la
fabrique. Le plan l'a « reportée au jour J ». Les 2 annonces d'essai n'en ont pas.

Ce n'est pas une seule série : EM 8 841 · EA 2 449 · ET 512 · EI 255 · V7 199 · V3 163 · VM 147…
La reprendre demande de comprendre plusieurs séries.

### B13 — Il n'existe pas d'interrupteur de coupure ⛔

- Le seul levier, `CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS`, est **codé en dur à « true »** dans le
  service Windows (`HektorConsoleWorkerService.cs:209`, recompilation nécessaire).
- Ce levier arrête **aussi** les PDF et le bouton **« Préparer »**, seule porte vers les
  **82 620 documents (79 %) qui ne sont que sur le serveur**. Le geste naturel du jour J
  rendrait donc 79 % des documents illisibles dans l'app.
- Les 4 crons et les RPC continueraient de fabriquer des travaux Hektor. Chaque ouverture de
  fiche en créerait un, voué à l'échec.

### B14 — Les chantiers à date de péremption que la thèse n'a pas listés 🟡

Ils exigent que Hektor vive encore :
- **C.9-couple** : la mesure d'une heure (« une fiche ou deux ? ») n'a **jamais été faite**.
  Aujourd'hui, c'est Hektor qui crée la 2e fiche du couple et pose le lien.
- **Le rattrapage des recherches invisibles** (E.1) : une passe la veille de la coupure, volume
  inconnu (50 à 1 600 selon le plan).
- **L'agenda des visites Hektor** (qui, quand, quel bien) n'est importé nulle part. Les bons de
  visite en PDF le sont, eux, pour les annonces déjà scannées.
- **C.13-c** : les dates de clôture des mandats (118 sur 24 494).
- **N.4** : le corps local de l'annonce (B7).
- **Les documents du parc vivant** (§4.1).
- **L'export PROTEXA** (§4.2).
- **Solder les 50 signatures en cours** (§4.3).
- **Préparer le détail d'une annonce archivée** interroge Hektor **avant** notre base. Si Hektor
  répond mal, il peut même **écraser** le cache console déjà bon
  (`sync_console_missing_fields.py:330-370`).

---

## 6. LA FIABILITÉ — l'infrastructure n'est pas encore prête à porter seule la vérité

> Tant que Hektor vit, il sert de filet : tout ce qui se perd chez nous peut se relire chez lui.
> **Le jour de la coupure, ce filet disparaît.** Ces points deviennent alors vitaux.

### 6.1 Les sauvegardes

| constat | gravité |
|---|---|
| **Le schéma Supabase n'existe nulle part ailleurs que dans Supabase.** **51 fonctions sur 141**, dont **le moteur de rapprochement** (`app_match_score_v2`, `app_process_rapprochement_dirty`), ne sont **pas dans git**, ni ailleurs sur le disque. **6 des 12 tâches cron** n'ont pas leur horaire versionné. Il n'y a ni `pg_dump` ni `psql` sur la machine. Si le projet Supabase était perdu, les données reviendraient par la descente, mais **la logique serait à réécrire de mémoire**. | **IMPORTANT** |
| `app_relation`, `app_mandat` et leurs carnets **ne sont toujours pas** dans la sauvegarde quotidienne (signalé le 01/10). Ils ont d'autres copies (Supabase, la descente, Veeam) : on perd au pire une journée. Le remède tient en quelques noms à ajouter à une liste. | MOYEN |
| **Le miroir `hektor.sqlite` (4,1 Go) n'est sauvegardé que par Veeam** (14 jours, jamais restauré). Après la coupure, il devient **la seule source** du détail des 34 530 archives. | IMPORTANT |
| **La doctrine de sauvegarde s'inverse à la coupure, et rien ne le prévoit.** `backup_critical.py` ne copie que ce qui « ne se reconstruit pas depuis le miroir ». Après la coupure, plus rien ne se reconstruit : **la source devient Supabase**, et sa copie locale (la descente) n'est dans **aucune** sauvegarde quotidienne. De plus, la sauvegarde de 08:00 passe **avant** la descente de 08:15. | IMPORTANT |
| **Restauration** : un seul fichier de 7,7 Mo a été restauré depuis le coffre OVH. Jamais `phase2.sqlite`, jamais le miroir, jamais les documents, jamais la machine, jamais Supabase. | MOYEN |

### 6.2 La surveillance

| constat | gravité |
|---|---|
| **Une alerte critique figée depuis le 01/10 a déjà masqué une vraie panne.** Le 05/10, la relecture immédiate des annonces a été **cassée 9 heures** (TypeError, `export_app_payload.py:1871`), trouvée **à la main**. Le moniteur n'a rien envoyé : la clé était déjà rouge. Il n'envoie que ce qui **devient** critique. Les 15 erreurs ne sont ni soldées ni rejouées : **l'alerte reste aveugle aujourd'hui**. | **IMPORTANT** |
| **La sentinelle des tâches cron répond « ok » quand elle n'arrive pas à mesurer** : c'est arrivé dans **56 % des passages** sur 30 jours (statement timeout sur 801 634 lignes jamais purgées). Les 20 anomalies réellement vues sont sorties en « warning », donc **jamais envoyées**. Ces crons sont le moteur des envois et du rapprochement. | **IMPORTANT** |
| **23 sentinelles sur 35** ne préviennent jamais personne (warning). Elles ne s'affichent que dans l'écran « Santé système ». | MOYEN |
| **0 sentinelle de données** sur les documents, les photos et les RDV, alors que c'est là que le volume est le plus gros. **7 heartbeats partent dans le vide** (dont les 4 étapes photos) : leurs clés n'existent pas dans `app_worker_registry`, donc le PATCH met à jour 0 ligne sans rien dire. | IMPORTANT |
| **Personne ne dirait que le serveur est mort** : le moniteur tourne sur la machine qu'il surveille. Il n'y a aucun témoin extérieur, aucune sonde de place disque, aucune sonde sur Veeam. | IMPORTANT |
| **Les workers plantent tous les 2 à 4 jours** (code `0xC0000409`), puis sont relancés en 10 s par leur enveloppe. Une quinzaine d'arrêts depuis le 17/09, **non surveillés**. | MOYEN |
| `recherche_divergente` **crie toujours faux** au petit matin (30/09, 01/10, 02/10). | MOYEN |

### 6.3 La capacité

- **Disque** : les documents locaux sont passés de **61 Go à 327 Go en 12 jours**. Il reste
  444 Go sur un volume **unique** (Windows, code, bases, fichiers, sauvegardes). Avec les ventes
  du rattrapage : +137 à +273 Go. **Aucune alerte de place.**
- **Supabase** : la base a doublé depuis août (**3,8 Go**) sur la plus petite machine (256 Mo de
  cache). Des sondes simples dépassent déjà le délai. Quand toutes les saisies arriveront
  d'abord dans Supabase, ce sera serré.

### 6.4 Une faille de sécurité vue en passant *(hors plan, mais à ne pas laisser)*

**La fonction Supabase `hektor-diffusion` est déployée et ACTIVE** (version 14). Elle appelle
l'API Hektor pour diffuser, valider ou retirer une annonce. Elle **ne vérifie que la connexion de
l'utilisateur, pas son rôle** (`index.ts:84-88, 420-445`). Un négociateur connecté pourrait
l'appeler directement et **accepter une diffusion sans l'administratrice**, alors que les routes
du backend, elles, exigent le rôle admin.

### 6.5 Petites dettes relevées

- Le paquet de production vise **l'ancien domaine Hektor** (6 occurrences) : les boutons
  « Ouvrir Hektor » et « Signature » ne marchent probablement plus.
- Les **protections « saisie en attente » s'ouvrent** si la lecture Supabase échoue
  (`push_contacts_to_supabase.py:427-506`). Seule exposée aujourd'hui : 1 recherche, mais la
  perte serait **définitive**.
- Il reste **13 ouvertures de base sans attente** (Matterport, écrivains de `hektor.sqlite`).
- **1 commit non poussé** (`38ad468`) et **89 fichiers non suivis**, dont tout le travail
  préparatoire de la signature et du worker Leboncoin. Les horaires de 6 des 7 tâches n'existent
  que dans Windows.
- Les files **Matterport** et `sync_full` n'ont **aucun service** : le front sait créer des
  travaux Matterport qui ne seraient jamais réclamés.

---

## 7. L'USAGE RÉEL — le chiffre qui change la lecture de tout le reste

```
DEPUIS LE 15/09                                     DANS L'APP     DANS HEKTOR
   contacts créés                                        4 (essais)      367
   annonces modifiées                                    1             ≤ 3 066
   annonces créées (depuis le 25/09, e3 allumé)          0                89
   mandats numérotés (septembre-octobre)                 0                73
   transactions nées (depuis le 07/09)                   0         15-21 / semaine

QUI DEMANDE LES TRAVAUX (120 jours)       admin 412 · système 543 · COMMERCIAL 0
COMPTES ACTIFS EN 30 JOURS                2 administrateurs
TRAVAUX D'ÉCRITURE EN OCTOBRE             8
```

C'est **conforme à votre décision du 21/09** : *« pendant toute la migration, les commerciaux
saisissent encore dans Hektor »*. Ce n'est donc pas une faute. **Mais cela change le sens de
« autonome »** :
- les chemins de création et de modification sont **prouvés par 1 à 3 essais**, faits par des
  administrateurs ;
- **aucun n'a tenu une charge réelle** ;
- le flux réel va **de Hektor vers l'app**, pas l'inverse.

**Le jour de la coupure serait le premier jour d'usage réel de l'app par l'agence entière.**
C'est pour cela que le lot **L8** (« les négociateurs travaillent dans l'app ») n'est pas un
détail : c'est **la répétition générale** qui manque.

---

## 8. LES DOCUMENTS DU PROJET SE CONTREDISENT — à corriger pour ne plus se tromper soi-même

Votre méthode le dit : *« une consigne périmée se relit comme un ordre du jour »*. En voici, et
la thèse s'appuie probablement sur certaines d'entre elles.

| où | ce qui est écrit | la réalité mesurée |
|---|---|---|
| CLAUDE.md §2 ⑤ | « ~2 500 restantes → UNE nuit » | ≈ 10 650, au moins 6 nuits, plus le parc vivant figé |
| CLAUDE.md §2 ②③ | `busy_timeout` et garde d'ordonnancement « à faire » | faits le 03/10 (`a86a800`, `5cfd576`) |
| CLAUDE.md §2 ④ | essai `degroupproprio` « JAMAIS EXÉCUTÉ » | exécuté le 03/10 à 18:22 UTC |
| CLAUDE.md l.157 | « corps durable en local 189/189 » | une copie du cloud, refaite à chaque descente |
| CLAUDE.md, A.1 | « correctif = 1 ligne, la bonne version dort à côté » | l'écran applique et relit déjà ; le défaut est plus étroit |
| Plan, L1 ✅ | « une recherche naît dans l'app avec son numéro » | distributeur jamais appelé |
| Plan, L2 ✅ | « le serveur tient un objet que le miroir ignore » | faux pour l'annonce et la transaction (26bis-3, 26bis-TRANSACTIONS ouverts) |
| Plan, L3 ✅ | « le run confirme, il n'écrase plus » | il écrase puis repose |
| Plan, « annonce close, rien ne périme » | — | N.4 porte une « date de péremption » dans le même plan |
| Plan, 6.5 | « les 3 PDF continuent tels quels » | ils passent par le worker que 6.4 éteint, et par un dépôt chez Hektor |
| Plan, l.1187 / 1664 | « 181 des 182 mandats créés depuis juin viennent de l'app » | 3 travaux en tout dans la table |
| Plan, L6 | « le reste ne remonte plus » | contredit la décision du 21/09 |
| Liste, page de tête | « e3 codée, ÉTEINTE » | allumée depuis le 25/09 |
| Liste | F.1 (droits) **après** la coupure | E.2 (négociateurs dans l'app) doit la précéder, et les droits la bloquent |
| Audit du 01/10 | « recherche : créer ✅ » | provisoire seule |
| Audit du 01/10 | « passerelles : pas une exception technique » | l'API est celle de Hektor |
| Audit du 01/10 | « aucune restauration testée » | un fichier restauré le 19/08 |
| Audit du 01/10 | « aucune insertion directe dans `app_console_job` » | 13 insertions directes dans `api.ts` |
| Audit du 01/10 | « 1 saisie de recherche perdue depuis 8 jours » | c'est la protection voulue par C.3, la valeur est intacte dans l'app |
| Mémoire « audit identité contacts » | « aucun `app_contact_id` null » | 14 aujourd'hui |
| Mémoire « bannissement d'IP » | seuil de 13 000 à 17 000 requêtes | ≈ 18 000 par nuit depuis 12 nuits, sans bannissement : la vraie limite est le **temps** |

---

## 9. CE QUI A UNE DATE DE PÉREMPTION — à finir tant que Hektor vit

| chantier | pourquoi ça périme |
|---|---|
| **les documents du parc vivant** + le rattrapage (archives, ventes, brouillons, locations ?) | seul Hektor a ces fichiers |
| **les 230 documents indexés sans fichier** | idem |
| **l'export complet de la série PROTEXA** | seul moyen d'expliquer les 25 trous et de savoir où reprendre |
| **C.13-c** — dates de clôture des mandats | se remplit depuis le miroir |
| **N.4** — corps local de l'annonce | sa méthode de remplissage est le miroir |
| **C.9-couple** — la mesure d'une heure | seul moment où l'on peut comparer notre paire à celle de Hektor |
| **E.1** — rattrapage des recherches invisibles | une passe la veille |
| **l'agenda des visites Hektor** | importé nulle part — décision en attente |
| **les 50 signatures en cours** | une procédure non soldée devient orpheline |
| **les leads** | trouver le canal tant qu'on peut encore comparer |
| **la zone DNS** | doit être déplacée **avant** le préavis |

---

## 10. LA LISTE COMPLÈTE DE CE QUI RESTE — classée

> **A** = bloque la coupure · **B** = date de péremption (à faire pendant que Hektor vit) ·
> **C** = peut se faire après. Les efforts marqués *(est.)* sont des estimations d'auditeur,
> pas des mesures.

### A — BLOQUE LA COUPURE

| # | chantier | les 4 points ? | taille |
|---|---|---|---|
| A1 | **Registre légal des mandats** : série, inaltérabilité, export, détaché du miroir, avenants et mandats de recherche, réparer les 2 défauts dormants de l'étape D | ✅ cité | 3-5 sem. *(est.)* + juriste + horodatage |
| A2 | **Signature** chez un prestataire en propre | ✅ cité | 1,5-3 sem. *(est.)* + contrat |
| A3 | **Diffusion** : flux à nous + contrats au nom de GTI + suivi | ✅ cité | 2-4 sem. *(est.)* + contrats |
| A4 | **Documents** : finir le rattrapage, réparer les brouillons, G.2 puis G.6, rebalayer le parc vivant, trancher les locations | ✅ cité (sous-estimé) | ≥ 6 nuits + quelques jours de code |
| A5 | **Le numéro Hektor de l'annonce devient facultatif partout** (16 tables, 4 clés, 8 fonctions, chaînage des transactions, liens RDV, vitrine) | ⛔ oublié | moyen-gros |
| A6 | **Créer sans Hektor** : corps complet de l'annonce, recherche durable, mandants à la création, transaction sans Hektor | ⛔ oublié | moyen |
| A7 | **G.5** : ajouter un document, une photo ou un PDF généré chez nous d'abord | ⛔ oublié | petit-moyen (socle écrit) |
| A8 | **Les gestes manquants** : appliquer archiver / restaurer / négociateur, gérer les photos, modifier ou prolonger un mandat, fusionner, reprendre un brouillon, inverser les suppressions | ⛔ oublié | moyen (L5 : 6-10 j au plan) |
| A9 | **Baisse de prix** contrôlée sur le prix de l'app | ⛔ oublié | petit |
| A10 | **Le run d'après la coupure** : sortir de la chaîne Hektor ce qui doit vivre (vitrine depuis Supabase, liens RDV, dérivés photos, registres) | ⛔ oublié | moyen |
| A11 | **Un interrupteur de coupure** qui n'arrête ni les PDF ni « Préparer » | ⛔ oublié | petit |
| A12 | **Négociateurs** : annuaire à nous, création d'un collaborateur, **droits réécrits** (F.1 avant E.2), **comptes**, puis **E.2** | ⛔ oublié | moyen + organisation |
| A13 | **Numéro de dossier** EM/VA : qui le fabrique ? | ⛔ oublié | petit-moyen |
| A14 | **Zone DNS** à déplacer chez OVH, **site web** à rehéberger | ⛔ oublié — hors code | quelques heures + décision |
| A15 | **Leads** : trouver le canal actuel, construire l'entrée | ⛔ oublié | inconnu |
| A16 | **Sauvegarde et surveillance de l'après** : schéma Supabase versionné et exporté, doctrine inversée, miroir sauvegardé, témoin extérieur, disque, alerte figée, sentinelle cron honnête | ⛔ oublié | quelques jours |

### B — DATE DE PÉREMPTION (Hektor doit vivre)

C.9-couple (1 h de mesure) · N.4 · C.13-c · E.1 recherches invisibles · export PROTEXA ·
agenda des visites (décision) · 230 documents sans fichier · 50 signatures en cours · 111
documents de fin de vie · rendre le **jeton RDV stable** avant de le publier.

### C — PEUT SE FAIRE APRÈS (ou en parallèle)

Retirer les 16 « Ouvrir Hektor » et corriger l'ancien domaine · vignettes DPE/GES et logo du
mandat chez nous · avis de valeur avec nos photos · fiche visite PDF à nous · 5 biens actifs
« sans photo » · ménage du cloud (G.3/G.4) · trio contrat de la relation · N.2 · fonction
`hektor-diffusion` (rôle admin, puis retrait) · purge de `cron.job_run_details` · mise à jour de
CLAUDE.md et du plan (§8).

---

## 11. L'ORDRE QUE JE RECOMMANDE

> Proposé, pas décidé. Le plan fait foi : ce qui suit se discute avant d'y entrer.

```
0. DÈS MAINTENANT, HORS CODE (aucun risque, gros enjeu)
   · déplacer la zone DNS chez OVH (MX, SPF, DKIM, DMARC) et décider du site web
   · trouver par où arrivent les leads depuis février
   · demander l'export complet de PROTEXA
   · lancer les contrats : signature en propre, diffuseur au nom de GTI
   · trancher : continuer la série PROTEXA ou repartir de 0 ; locations dans le rattrapage ?

1. CE QUI PÉRIME, PENDANT QUE HEKTOR VIT
   · réparer les brouillons du rattrapage AVANT le 12/10 (sinon 508 exclus pour toujours)
   · G.2 puis rebalayer le parc vivant (les biens en vente, figés depuis le 20/08)
   · C.9-couple (1 h) · C.13-c · solder les 50 signatures

2. RENDRE LA NAISSANCE AUTONOME (le cœur technique qui manque)
   · A5 numéro Hektor facultatif · A6 créer sans Hektor · A7 G.5 · A11 interrupteur

3. LA RÉPÉTITION GÉNÉRALE (L8)
   · droits réécrits + comptes négociateurs → quelques négociateurs pilotes
     travaillent DANS L'APP pendant que Hektor vit encore
   · c'est elle qui trouvera les défauts que seul l'usage révèle

4. LES TROIS EXCEPTIONS (registre légal, signature, flux portails)
   en parallèle de 2-3, dès que les contrats et le juriste répondent

5. LE JOUR J PRÉPARÉ : le run d'après, la surveillance d'après, la sauvegarde d'après
```

**Pourquoi cet ordre.** Les points 0 et 1 ne coûtent presque rien et **ne se rattrapent pas**
après. Le point 3 est le seul qui transforme une autonomie **prouvée par des essais** en
autonomie **prouvée par l'usage**. Sans lui, la coupure serait le premier essai grandeur nature.

---

## 12. CE QUE CET AUDIT N'A PAS PU MESURER

*Une case non mesurée se dit, elle ne se saute pas.*

- **Rien n'a été exécuté contre Hektor.** Les points suivants sont donc lus dans le code,
  jamais éprouvés :
  - les liens de l'ancien domaine mènent-ils à une page de connexion ?
  - que fait Hektor quand l'app envoie un couple ?
  - `pdf.php` exige-t-il une session ?
  - par où arrivent les leads côté Hektor ?
- **Le comportement réel des écrans** devant une annonce sans numéro Hektor : le front n'a pas
  été lancé.
- **Le volume** de l'agenda des visites Hektor, des recherches invisibles, et des documents
  rattachés aux contacts ou aux transactions plutôt qu'aux biens (un paramètre
  `isDocUploadPropsect` le suggère).
- **Les contrats** :
  - le site www fait-il partie de l'abonnement La Boîte Immo ?
  - que fera l'éditeur de la zone DNS à la résiliation ?
  - qui possède le CDN des photos neuves ?
- **Les sauvegardes Supabase** (PITR, rétention) et les **alertes Veeam / OVH** côté console :
  non visibles sans leurs consoles.
- **Les mentions légales exactes du registre des mandats** : à confirmer par un juriste.
- **Les efforts en semaines** sont des estimations d'auditeur.

---

## ANNEXE — Méthode et garde-fous de cet audit

- **10 dimensions**, un auditeur chacune, avec la consigne : *le code gagne sur les notes ;
  chaque affirmation porte sa preuve ; dire la source mesurée ; une case non mesurée se dit*.
- **10 contradicteurs**, un par dimension, chargés de **refaire les mesures** des constats
  graves et de les **réfuter**. Sur les quelque 140 constats, une large part a été **nuancée**
  et plusieurs ont été **infirmés**. Exemples :
  - « le RDV est cassé à la coupure » → les QR imprimés survivent ;
  - « passer au jeton est petit » → le jeton n'est pas stable ;
  - « 28 trous inexpliqués » → 25 ;
  - « 2 RDV pris » → 0 par cette voie ;
  - « le run du 22/09 a échoué » → c'était un run de journée.

  Les contradicteurs ont aussi **trouvé des choses que les auditeurs avaient manquées** :
  - la zone DNS ;
  - le canal des leads disparu en février ;
  - les brouillons du rattrapage qui échoueront ;
  - les défauts dormants de l'étape D ;
  - la fonction `hektor-diffusion` sans contrôle de rôle ;
  - le jeton RDV instable ;
  - la panne du 05/10 masquée par l'alerte figée.
- **Lecture seule respectée** : aucun fichier du projet modifié (sauf la création de ce
  rapport), aucune écriture en base, aucun appel à Hektor, aucun redémarrage, aucun commit.

*Rapport à relire avec Frédéric. Il ne modifie ni le plan, ni la liste, ni CLAUDE.md : les
corrections du §8 attendent son accord.*

---

## 13. CE QUE LE CONTRÔLE DE COMPLÉTUDE A AJOUTÉ — *même jour, après la rédaction*

> Un critique a relu les dix dimensions pour chercher **ce qui manquait**. Il a lancé cinq
> enquêtes, toutes en lecture seule. Elles ajoutent **cinq familles de dépendances** que
> personne n'avait vues, et elles corrigent un point du §4.1.

### C1 — Le drapeau « diffusable » commande le rapprochement ⛔ BLOQUANT

- **Ce que dit le code.** Le moteur de rapprochement, une fonction 100 % app, ne retient un
  bien que s'il est « Actif » **et** `diffusable = '1'`. La règle est dans 8 fonctions SQL,
  dans le déclencheur `trg_dossier_dirty` et dans 2 gardes du front.
- **Personne chez nous ne sait poser ce drapeau.**
  - aucune fonction SQL ne l'écrit ;
  - le contrat d'autorité de l'annonce est vide ;
  - les 3 écrivains réels (le run de nuit, la relecture d'une fiche, le geste admin du backend)
    recopient tous une valeur **lue chez Hektor** ;
  - même « passer en Actif » ne rend le bien diffusable que parce que le worker envoie
    `diffusable=1` à Hektor, puis que le miroir le redescend ;
  - une annonce née dans l'app est insérée avec `diffusable = NULL`, une colonne sans valeur
    par défaut.
- **Ce que cela touche.** En 30 jours, 55 biens sont entrés dans le rapprochement et
  **473 alertes** sont parties. Après la coupure, ce flux tombe à **zéro**, et la vitrine comme
  les liens RDV filtrent aussi sur ce drapeau.
- **Ce n'est pas un défaut d'aujourd'hui** : le filtre est voulu. 152 des 248 annonces
  « Actif » non diffusables n'ont même pas de numéro de mandat. **Il manque un propriétaire** :
  le plan ne dit nulle part qui validera un bien pour la diffusion après la coupure. Et changer
  de fournisseur de portails ne donnera pas ce drapeau à l'app.

### C2 — Mettre une estimation sous mandat, ou clore un mandat, passe par Hektor ⛔ BLOQUANT

- **Estimation → Actif** (la mise sous mandat) **n'écrit rien chez nous**. L'app envoie
  l'ordre à Hektor, puis attend la relecture. Dans toute la base, la seule fonction qui écrit
  `statut_annonce` localement est la redescente après la suppression d'une transaction. C'est un
  geste quotidien : environ **60 mandats par mois**, dont 1 seul fait depuis l'app. Il est
  réservé à l'admin.
- **Clore un mandat** : le statut « Mandat clos » est posé **d'abord chez Hektor**
  (`console_job_worker.js:13121-13135`), et la clôture locale ne vient qu'**après**. La case
  `C.13` de la liste (« la clôture ne passe plus par Hektor ») n'est vraie que pour la fiche de
  clôture, pas pour le statut.

### C3 — Les visites et les documents-modèles sont fabriqués par Hektor ⛔ BLOQUANT

- **Le bon de visite**, preuve du droit aux honoraires, est fabriqué par le modèle Hektor
  « Bon de Visite Groupe GTI » : **environ 115 par mois**, 25 négociateurs, environ 16 agences.
- **Le bon de visite de l'app ne fait qu'imprimer** (`App.tsx` 37608-37787). Il n'archive aucun
  PDF et ne crée aucune ligne. Son numéro n'appartient à aucune série. Il ne couvre qu'un seul
  bien. Il exige un RDV créé dans l'app : 19 en tout, le dernier le 19/06, **jamais en
  production**.
- **L'offre d'achat** n'a aucun générateur dans l'app. **L'avenant** de l'app ne change que le
  prix, et il a servi **0 fois**, contre environ 8 avenants par mois faits par le modèle Hektor.
- **La visite n'existe comme objet nulle part** : l'agenda Hektor n'est pas importé, et sur
  619 bons captés, 305 ne portent aucun nom d'acquéreur. La « Génération docs 100 % interne » de
  la note du 01/07 est **contredite**.

### C4 — Hektor rend des services aux clients que l'app ne remplace pas 🟡

- **L'email RGPD / « Espace personnel »** d'un nouveau contact est envoyé **par Hektor**, à la
  demande de l'app (une case cochée par défaut, `_email_rgpd=1`).
- **Les automatismes CRM** (mail de nouveau mandat, mail d'échéance, anniversaire) sont
  pilotés par l'app mais **exécutés par Hektor**. Les relances automatiques de l'app sont, elles,
  volontairement bloquées.
- **Tâches et rappels**, **reporting**, **envoi de fiches** : rien n'a d'équivalent dans l'app,
  ni d'import. L'usage réel n'est pas mesurable sans Hektor.
- **Les leads** : Hektor a un module « Demandes en attente » (API `listLeads`) que nous ne
  lisons pas (voir B10).
- Seulement **proposés**, sans perte : pige, Interkab (0 rétrocession sur 9 252 ventes),
  MyNotary, Meero, Jestimo. **À demander** : SMS, Properstar (un portail international ?),
  « Support de comm' », gestion des clés et des panneaux.

### C5 — Le scénario de fin de contrat : un Hektor qui répond « vide » ⛔ BLOQUANT, et possible dès aujourd'hui

Le run a été audité pour un Hektor qui **se tait** : il s'arrête net, sans dégât. Mais un compte
résilié peut aussi répondre **« 200 OK, 0 annonce »**, ou un objet au lieu d'une liste. Dans ce
cas :
1. `sync_raw` termine **en succès**, après avoir **remplacé la page 1 par le vide et effacé les
   3 064 autres pages** du listing. Ensuite, 3 330 annonces n'ont plus de copie locale.
2. Le plancher de 50 % existe, mais **au mauvais étage** : il protège une table d'état, pas
   les pages brutes.
3. `normalize_source` recalcule le périmètre depuis ces pages vides et **vide 9 tables du
   miroir, plus 24 925 mandats**, sans plancher ni journal (`normalize_source.py:658-726`).
4. Le run continue. Le registre des affaires marque **environ 30 700 affaires** « absentes »,
   et l'écran les cache. Le registre des liens masque une partie des mandants.
5. Le premier vrai arrêt est le frein des 500 dossiers du push. C'est **un plancher par
   accident**.
6. **Si seules les archives reviennent vides** (une page vide en plein balayage suffit), l'index
   des **35 317 archives** de Supabase est effacé sans plancher. **C'est possible dès
   aujourd'hui, sur un simple hoquet de Hektor.**

Le jour J du plan ne dit pas d'**éteindre les tâches et les workers AVANT** la fin de l'accès à
Hektor.

### C6 — Sécurité, vue en passant *(hors plan)*

**9 fonctions d'écriture sont exécutables sans être connecté** : la clé « anon » est publique,
puisqu'elle est dans le paquet du front. Exemples : `app_set_bien_statut`,
`app_record_proposition`, `app_create_relance_for_contact`, les sources d'estimation. Cela
s'ajoute à la fonction `hektor-diffusion` sans contrôle de rôle (§6.4). Enfin, les cibles de
diffusion sont modifiables par **tout compte actif, sur toute annonce**.

### Ce que cela change aux §0 et §10

- La liste de ce que la thèse oublie passe d'**une quinzaine à une vingtaine** de chantiers.
- **À ajouter au §10, catégorie A** :
  - le drapeau « diffusable » devient un champ de l'app (C1) ;
  - la mise sous mandat et la clôture se font chez nous (C2) ;
  - le bon de visite et les documents-modèles sont faits par nous (C3) ;
  - l'email RGPD et les automatismes clients sont repris (C4) ;
  - les planchers « Hektor répond vide » sont posés, et l'ordre d'extinction est écrit (C5).
- **Les droits** sont plus bloquants qu'écrit au B11. Un commercial peut **créer** une annonce,
  mais ensuite il ne peut **ni la modifier, ni changer son statut, ni y ajouter une photo ou un
  mandant**. Avec les droits actuels, E.2 n'est pas jouable.
