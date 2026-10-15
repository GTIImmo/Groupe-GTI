# Porte d'entrée du projet

> Ce fichier ne contient **aucune connaissance**. Il contient des **adresses**.
> Le savoir est dans le plan, la liste, les notes et le code. En cas de désaccord,
> **c'est le code qui gagne, puis le plan, puis cette page.**
> Il se lit en trois minutes. Il ne remplace rien.

---

## 0. LA METHODE — *posee par Frederic le 20/09/2026, elle ne s'oublie jamais*

> **A chaque chapitre du plan, dans cet ordre, sans qu'il ait a le redemander :**
>
> 1. **AUDITER** le sujet — le code et la base d'abord, les notes ensuite. En cas de
>    desaccord, le code gagne.
> 2. **EXPLIQUER** clairement et simplement : ce que j'ai trouve, ce que je vais faire,
>    ce que ca touche, comment on revient en arriere, comment on verifiera.
>    ⚠ **Et TOUJOURS « ce que ca pourrait casser ailleurs »** *(Frederic, 08/10)* : avant de
>    corriger, controler que le correctif n'ecrase pas un RAISONNEMENT GLOBAL de l'app --
>    tous les appelants, les chemins de secours, les usages publics, les decisions ecrites.
> 3. **CODER**, en additif, derriere un interrupteur quand c'est possible.
> 4. **CONTROLER** : essais hors ligne, puis preuve en reel si necessaire. Dire aussi
>    ce qui a rate.
> 5. **METTRE A JOUR LE PLAN** : la case cochee AVEC sa mesure, la page de tete, le
>    journal des decisions, le commit qui porte l'identifiant de la tache.
> 6. **PASSER A L'ETAPE SUIVANTE** et recommencer.
>
> **LE FEU VERT, au cas par cas selon le risque** *(arbitrage du 20/09)* :
>
> | | |
> |---|---|
> | **J'enchaine sans attendre** | tache additive et reversible : code neuf dormant, lecture, mesure, audit, mise a jour des documents |
> | **J'attends le « vas-y »** | modification de code existant, du run de nuit, des workers |
> | **Accord OBLIGATOIRE, toujours** | ecriture en base de production · ecriture chez Hektor (creer / modifier / supprimer) · lancer un run ou un rattrapage · redemarrer un service · deployer · tout geste irreversible |
>
> ⚠ **UN AUDIT BALAIE LES OBJETS *ET* LES GESTES — regle posee par Frederic le 21/09**,
> apres un audit qui n'avait mesure QUE la modification d'une annonce et avait manque les
> 167 champs de la CREATION. « Tu vas trop vite dans tes audits, il faut les rendre plus
> approfondis. »
>
> **Avant de conclure quoi que ce soit, dresser le tableau, meme s'il est vide :**
>
> |  | creer | modifier | supprimer / archiver | lire / remonter |
> |---|---|---|---|---|
> | **annonce** | | | | |
> | **contact** | | | | |
> | **recherche** | | | | |
> | **relation** (mandant, proprietaire, acquereur) | | | | |
> | **transaction** (offre, compromis, vente) | | | | |
> | **mandat** | | | | |
> | **document / photo** | | | | |
> | **RDV / visite** | | | | |
>
> Une case qu'on ne sait pas remplir se DIT (« non mesure »), elle ne se saute pas. Et si
> l'audit ne porte que sur un objet, l'ecrire en tete : « audit limite a X, les autres ne
> sont pas mesures ».
>
> **Une seule tache en code a la fois.** Les audits peuvent tourner en parallele.
> **Chaque message de travail commence par une ligne de position** : `L0 · C.1' · 2 sur 4`.
> **Rien n'est fini tant que ce n'est pas ecrit dans les documents** : cette conversation
> sera resumee, les fichiers survivent.

---

## 1. Où tu es

Le dépôt est **`C:\Hektor\Projet`**. `C:\Hektor` n'est pas un dépôt git : si une commande
git répond *« not a git repository »*, tu es au mauvais endroit.

| | |
|---|---|
| front | `apps/hektor-v1/` — valider avec `npm run build`, **jamais** `tsc --noEmit` |
| worker | `Console/console_job_worker.js` |
| synchro | `phase2/` |
| API | `backend/` |
| tâches planifiées | `scheduled/` |
| documents de travail | `notice/` — 160 notes *(compté le 07/10)* |

---

## 2. Où on en est — *une page, pas une archive*

> ⚠ **Cette section porte LE PRÉSENT, et rien d'autre.** Règle : en fin de session, on la
> **RÉÉCRIT**, on ne l'empile pas ; ce qui en sort descend dans **`notice/JOURNAL_DE_BORD.md`**
> *(l'état du 11/10 et toute la journée du 12/10 y sont descendus le 12/10 — le §2 était
> reparti à **234 lignes**, dont 40 pour la seule ligne du chantier ②)*.

**Réécrit le 12/10/2026, à la clôture du chantier ②.**

### Les deux étapes — *définies par Frédéric le 08/10*

```
ETAPE 2   l'app fait tout le travail quotidien ; Hektor vit, il FOURNIT LES NUMEROS
          (y compris le n° de mandat via PROTEXA), les workers lui ENVOIENT les mises a jour
ETAPE 3   notre registre electronique des mandats (nos numeros) -> la signature -> la pub ;
          « tant que les 3 ne sont pas chez nous, impossible de couper Hektor » ;
          plus site web, DNS, e-mail
```

### Les 8 chantiers *(plan, section « 🧭 LES CHANTIERS DE L'ÉTAPE 2 »)*

**La méthode, à chaque chantier** : **audit du sujet** (revérifier) → **explication des
correctifs**, avec « ce que ça pourrait casser ailleurs » → « vas-y » → code → **contrôle du
résultat** → plan, liste et cette page à jour. Prompt de reprise :
**`notice/PROMPT_CHANTIER_ETAPE2.md`** (une ligne à changer, et un § 6 « déjà appris »).

| # | chantier | état |
|---|---|---|
| ① | sécurité : 136 fonctions ouvertes à la clé publique | ✅ **FINI le 08/10** |
| ② | **les droits du négociateur** *(`notice/CHANTIER_2_DROITS_NEGOCIATEUR_2026-10-09.md`)* | ✅ **FINI le 12/10** — **8 patchs** et **1 déploiement**, tous contrôlés. Le négociateur a **21 gestes** sur ses biens · les **commissions** des collègues sont cachées · les **photos** du réseau sont visibles · le **registre** est réservé · le **manager = admin** *(sauf l'écran Santé)* · la **case « périmètre »** est à l'écran, **éprouvée par un pilote**. Restes **reportés par Frédéric**, pas oubliés *(voir « ce qui attend »)* |
| ③ | **Hektor d'abord → chez nous d'abord** *(`notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md`)* | 🔧 **en cours** — **6 patchs, 0 déploiement, 0 redémarrage, 0 ligne de front**, tous éprouvés en réel. ✅ **3a** statut + diffusable chez nous d'abord *(73 s gagnées)* · ✅ **8 941 biens vendus/clos redeviennent manipulables** *(bloqués depuis le 25/08 ; les 35 318 **archives** restent en lecture seule)* · ✅ **défaut 5a** : le désarchivage porte notre vrai numéro · ✅ **3b** archiver et négociateur écrivent la **fiche**, et ⭐ **les 3 motifs que l'app connaît sont gardés chez nous** *(archivage, désarchivage, clôture)* · ✅ **« vide ne gagne pas »** posé dans le contrat d'annonce. ⛔ **L'interrupteur reste ÉTEINT** *(voir « ce qui attend »)*. ✅ **3c (5/5 codées)** la clôture de mandat a sa **propre colonne** `mandat_date_cloture_app` — forme trouvée par Frédéric, **patron des photos recopié** — + le RPC de saisie *(carnet **et** vitrine en une transaction)* + l'alerte « Mandat échu » qui suit + ⭐ **la re-pose après le push, sur les DEUX chemins qui effacent** *(le run **et** le chemin immédiat du worker)*, **sans aucun redémarrage**. ⏰ **À prouver par le run du 14/10.** ⚠ **Restent 2 pièces de 3c** : le **champ à l'écran** *(3 points d'entrée)* et le **worker** *(4 services)*, + le sort de `appliquer_contrat_mandat.py`. ✅ **3e** le **journal des suppressions** *(qui/quoi/quand)* : le patron existait **deux fois** dans le projet, recopié — **mais avec une divergence : si la trace ne s'écrit pas, ON NE DÉTRUIT PAS** *(ses deux aînées, elles, avalent l'erreur — mesurable)* · + la **mention « supprimé chez Hektor »** sur les documents · + ⭐⭐ **le garde-fou de LISTE VIDE, qui manquait aussi aux photos** · + le `confirm` qui dit la vérité. ⛔ **Reste pour 3e** : 4 services, le push, l'écran du journal, et le **geste « supprimer une photo »** — ⚠ **la commande Hektor est INCONNUE** *(audit du 25/09 : « les trouver d'abord »)*, un relevé en lecture seule est à faire. ✅ **3d (2 pièces sur 4)** un document et une photo **existent chez nous avant que Hektor réponde** — le lot était en plan depuis le 25/09, et j'ai trouvé **pourquoi il ne pouvait pas marcher** : le rangement calcule `storage_path || <place définitive>`, donc il gardait le chemin **temporaire** comme domicile du document *(mesuré contre la version d'avant : 2 contrôles rouges)*. ⭐ **Deux gardes, pas une** — et celle des droits faisait **déjà** ce que Frédéric demandait. **Répétition 15/15.** ⭐⭐ **Et la fuite de la salle d'attente est nettoyée ET bouchée** : **109 fichiers, 196 Mo** dormaient sous `temp/` depuis le 14/05, dont **93 venant des générateurs de PDF**, pas des documents. ✅ **3d-③ le front** : un seul point d'appel pour les deux objets, et ⭐⭐ **une photo déposée ne disparaît plus** — l'écran faisait `if (!url) return null`, donc elle n'était **pas affichée du tout** *(une absence est pire qu'une erreur : elle ne se remarque pas)*. ✅ **3d-④ le repreneur** a son script — ⛔ **mais aucune tâche Windows ne l'appelle : il ne tourne pas, c'est à enregistrer**. ⭐ **Les 4 épreuves rouges sont réparées** *(dont 2 qui exigeaient le défaut ou accusaient la bonne réponse)* : **294 contrôles verts, 0 échec** — une première depuis le 27/09. ⭐⭐ **14/10, la fin** : ✅ **la pièce 4 de 3c est PROUVÉE par le vrai chemin** *(`posees 1` sur 62774)* · ✅ **option B** : les 2 étapes du contrat de mandat quittent le run *(elles n'atteignaient plus rien depuis le 30/09)* · ✅ **bloc 2 : supprimer une photo** — la commande Hektor est **trouvée** par un relevé en lecture seule *(`mode=delete_img` + `mode=ordonne_photos`)*, le geste, la base et l'écran sont écrits, **324 contrôles verts**. ➡ **Bloc 3 reporté au chantier ⑦** (décision de Frédéric). ✅ **Tout est collé, déployé et éprouvé en réel le 14/10** : une photo ajoutée puis supprimée sur 62774, le repreneur a tourné. ⚠ L'essai a trouvé un **3ᵉ verrou** (la distribution des travaux), corrigé |
| ④ | aucun échec silencieux — **10 points** *(`notice/CHANTIER_4_ECHECS_SILENCIEUX_2026-10-09.md`)* | ✅ **FINI le 11/10** · ⭐ **4j ajouté et fait le 13/10** *(trouvé par la session du chantier ③)* : **23 battements du run partaient dans le vide** — une clé non enregistrée reçoit **0 ligne modifiée** et le code compte **un succès**. **6 nuits sur 46** portaient un échec dont personne n'a rien su. 23 lignes de registre + 14 `-WorkerKey` au run ; il ne reste que **3 étapes sans clé**, celles qui **tuent déjà le run**. ⏳ **1ᵉʳ contrôle le 14/10 au matin** |
| ⑤ | les gestes cassés *(`notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md`)* | ✅ **FINI le 09/10** |
| ⑥ | ce qui ne redescend pas de Hektor (G.1-b, G.2 → G.6, photos, agenda) *(`notice/CHANTIER_6_REDESCENTE_HEKTOR_2026-10-14.md` · liste : `D.0`, l. 974 · photos, section **10bis**, l. 1174)* | 🔧 **en cours — 9 points listés** · ✅ **6a FINI le 14/10** : les **527 brouillons** sortent du rattrapage des documents — ⭐ **pas par un correctif, par une décision** *(Frédéric : « il n'y a pas de documents dans les brouillons, il faut juste le savoir »)*. Le défaut était réel *(0 des 527 dans les 3 index que `loadDossier` connaît → 527 échecs, exclusion définitive, rouge 30 j, la nuit du **16→17/10**)*. ⭐ **Et un brouillon est un MONDE À PART** : il entre par la **GraphQL** (`sync_hektor_drafts.py`), pas par le run REST ; il est **sorti du parc vivant exprès** (301 le 22/06) ; il est **en lecture seule par décision** (`App.tsx:411`, bouton « Reprendre la saisie » qui ouvre Hektor) ; **aucune modification n'a jamais été tentée** (8 rafraîchissements, 0 autre travail, depuis juin). ⭐ **Les 956 photos de 168 brouillons sont déjà sur le serveur — sans jamais appeler Hektor** (miroir local + CDN) ; **les documents, eux, n'ont aucune source locale**. ⚠ **Le piège évité** : retirer le périmètre sans le **déclarer** faisait crier « PÉRIMÈTRE OUBLIÉ » puis « LOT MAIGRE » en **code 1** → un e-mail rouge par nuit *(prouvé par témoin inverse)*. **3 épreuves vertes, 0 écriture, 0 redémarrage.** ✅ **6a-bis FINI le 14/10, SANS AUCUN PATCH** *(Frédéric : « A »)* — j'avais annoncé « un négociateur ne voit ni la fiche ni les photos de ses brouillons » : **vrai des fonctions, faux de l'écran**. Il voit déjà la liste *(RLS `is_app_user_active()`)*, la **vignette** *(510/527, servie par notre serveur)* et la fiche légère ; et le **panneau photos n'est pas affiché** sur une fiche légère → `loadConsolePhotos()` n'est **jamais appelé**, la RLS n'est **jamais testée**. ⚠⚠ **Et l'ouvrir aurait été dangereux** : `app_console_can_access_dossier` est la porte de **12 fonctions, dont 10 d'ÉCRITURE** *(créer un document, créer une photo, les 3 gestes d'affaire…)* **+ `app_console_can_request_job`** — on aurait ouvert dix gestes d'écriture sur une saisie en cours, contre la décision du 23/06. ⭐ **Et le système se répare seul** : sur les 73 brouillons finalisés, **66** sont revenus au parc vivant et sur leurs 638 photos **602 pointent le bon numéro, 0 est mal pointée**. ⛔ **Question en attente** : `app_brouillon_annonce_detail_cache` est **vide et rien ne la remplit** *(pas de type `prepare_brouillon_annonce_detail`)* → ce serait un **nouveau type de travail (3 verrous)**, donc **chantier ⑦**, et seulement si tu en as l'usage. · 🔧 **6b en cours (G.2 ✅ codé, dormant)** : **depuis le 20/08 personne ne va voir s'il y a du nouveau** — la récupération d'août **était complète**, la photo a 8 semaines. ⭐ **Preuve métier sans appeler Hektor** : mandats signés **avant** le 20/08 → 399 documents sur 472 ; **après** → **4 sur 97**. ➡ **93 mandats n'existent que chez Hektor**, +12/semaine *(71 annonces neuves + 22 déjà lues)*. ⭐ **Le mécanisme existait à moitié** : l'empreinte est posée (54 896), **la comparaison `--detect` jamais allumée**. ⚠ **Et la date ne peut pas servir** *(22/22 : un mandat du 12/10 sur une annonce « modifiée » le 13/02/2025)* — **pour les photos c'est l'inverse**, ne pas confondre. ✅ **Codé dormant** : budget de lectures *(le `--cap` ne plafonnait que les travaux : la boucle lisait 13 484 pages ≈ 6 h 23)*, périmètre `vente` *(727)*, étape du run en **2 lignes, non bloquante et surveillée** par une clé qui existait déjà *(0 écriture en base)*. ⚠⚠ **2 défauts trouvés et corrigés** : la **pagination sans tri** *(31 signatures vues sur 58 → 58/58 ; même défaut qu'en septembre, laissé dans ce fichier)* et **6 tâches suivies sur 8** *(« GTI Rattrapage Documents » jamais dans la liste du moniteur — 5ᵉ fois le même trou, à moitié rebouché le 26/09)* → **8/8**. ➡ **Plan arrêté** : ① **15/10 ~10:00** la passe à la main *(456 sans empreinte pour 1 requête + 727 biens en vente relus)* ; ② **allumage SEULEMENT après la fin du rattrapage** *(nuit du 16→17, signal « rien à faire »)* — un seul worker, une seule file |
| ⑦ | les gestes qui manquent *(`notice/CHANTIER_7_GESTES_QUI_MANQUENT.md`)* | ⬜ — ➕ **14/10 : ARCHIVER / DÉSARCHIVER UN CONTACT** *(audité : l'app ne sait **que supprimer** ; la commande Hektor de la fiche est **inconnue**, relevé en lecture seule d'abord)* · ➕ **le cas Gladys DURIEUX** *(mandante d'une annonce active, fiche archivée — à régler en même temps)* — ➡ **reçoit du chantier ③ (14/10, décision de Frédéric)** : le **crayon** de la date de clôture dans la rubrique Mandat *(`setMandatClotureApp` n'a qu'un appelant, la modale de statut)* et l'**écran du journal des suppressions** *(admins ; aucun écran ne le lit)*. ⭐ Et **réordonner / choisir la photo principale** : `mode=ordonne_photos` est désormais **connu** (relevé du 14/10) |
| ⑧ | gardé chez nous en entier | ⬜ |

**Ordre de Frédéric : ① ⑤ ④ ② puis ③ → ⑥ → ⑦ ⑧.** Un périmètre, une taille, un ordre ou un
report ne se décident jamais sans lui.

### ⭐ Les leçons qui servent au chantier suivant

1. ⭐ **Mesurer LE GESTE DE L'ÉCRAN, pas un geste plausible.** Trois fois le 12/10 j'ai cru à
   une avarie grave en comptant des lignes que l'app ne compte jamais *(l'écran lit les
   affaires et les photos **par annonce**, compte les contacts en **estimé** et les annonces en
   **exact**)*. **Lire comment l'écran lit, avant de crier.**
2. ⭐ **Une répétition vérifie les DEUX SENS** : que la nouvelle phrase **apparaît** *et* que
   l'ancienne **disparaît** ; et qu'un patch **a changé quelque chose**, pas seulement que
   l'inverse revient. *(Mémoire : « répétition : le témoin inverse ».)*
3. ⭐ **Modifier une fonction sans rien écraser** : le patch ne **recopie** pas la fonction, il
   la **lit dans la base**, vérifie son empreinte *(sans les retours chariot)*, contrôle que
   **l'ancre est unique**, insère après elle, réexécute.
4. ⭐ **Contrôler un droit sans mot de passe**, en empruntant l'identité, en lecture seule :
   `BEGIN; SET LOCAL ROLE authenticated; SET LOCAL request.jwt.claims = …'{"sub":"<uuid>"}'…;`
   puis des lectures, puis `ROLLBACK;`
5. ⭐ **Une règle de lecture doit sortir ses parties constantes** : `(select f())` est évalué
   **une fois**, `f()` **une fois par ligne** — 8,15 s contre 0,076 s pour un déplacement de
   parenthèses.
6. ⭐ **`service_role` porte `rolbypassrls`** → **aucune règle RLS ne peut casser** les
   workers, le backend, `phase2`, le run ni les crons. À ressortir chaque fois que la question
   se pose.
7. ⭐ **Un remplacement en masse ne se relit qu'en le faisant IMPRIMER** : lignes changées
   **et** lignes gardées avec leur raison. C'est ainsi que 3 défauts sont sortis.
8. ⚠ **Ne jamais conclure « le déploiement est cassé » juste après un push** : sonder en
   boucle, puis parler. *(Render `/health` rend le commit ; pour Vercel, chercher une chaîne
   neuve dans `/assets/index-*.js`.)*
9. ⭐⭐ **UNE CAUSE STRUCTURELLE SE BALAIE DANS TOUTE SA FAMILLE** *(12/10)*. Le 08/10, 5a a
   réparé « désarchiver » pour les archives — **une case sur huit**, alors que les 7 autres
   partageaient la même supposition *(« le bien est dans `app_dossier_current` »)*, fausse
   depuis le 20/05 pour **44 259 biens**. **Ce que Frédéric signale est un symptôme, jamais
   le périmètre.**
10. ⭐ **LE NOM D'UNE COLONNE MENT — et une mesure peut être une tautologie.** `app_archive_id`
   / `app_historical_id` **sont** `app_dossier_id`, renommés. J'avais conclu l'inverse d'un
   « 0 archive n'existe comme `app_dossier_id` » qui ne disait que *« aucune archive n'est
   dans la table des vivants »* — **la définition d'une archive**. Vérifier par un **second
   chemin** *(ici : les anciens travaux du même bien)*.
11. ⚠ **L'ÉCRAN PEUT PORTER UNE RÈGLE QUE LA BASE IGNORE.** L'écran a trois états
   *(vivant · index sans détail · index avec détail)*, les RPC n'en connaissaient qu'un :
   le bouton restait affiché et échouait en jargon. **Avant de corriger une fonction, lire
   ce que l'écran promet.**
12. ⚠ **Deux règles PostgreSQL** : deux règles « permissive » se combinent en **OU** *(ajouter
   une règle stricte à côté d'une large ne cloisonne rien — il faut remplacer)* · et une **vue**
   n'applique les règles des tables qu'avec `security_invoker`.
13. ⭐⭐ **UNE SENTINELLE QUI CRIE AU LOUP N'EST PLUS UNE SENTINELLE** *(13/10)*. « le push
   n'est pas passé » revenait **chaque matin depuis le 08/10** et repartait seul deux heures
   plus tard : le moniteur passe à 07:48, entre le push *(06:56)* et la descente de la doublure
   *(~07:58)* — il comparait **le registre du matin à la copie de la veille**. **Quand on ne
   peut pas savoir, on dit « non concluant », on ne crie pas** — et le vrai rouge reste intact.
   ⚠ Et **un rouge quotidien n'est pas forcément de mon fait** : l'historique des alertes le
   datait d'avant mon travail. *(`notice/SENTINELLE_MANDAT_FRAICHEUR_2026-10-13.md`.)*
14. ⚠ **DEUX DATES NE SE COMPARENT PAS COMME DEUX TEXTES.** `app_mandat.last_seen_at` est en
   **UTC**, `sb_pull_state.derniere_descente` est **locale sans fuseau écrit** : comparer les
   chaînes rendait l'**inverse** de la vérité, à **deux heures** près.
15. ⭐⭐ **CHERCHER SI LE PROJET A DÉJÀ TRANCHÉ — avant de proposer une forme.** Le 13/10,
   Frédéric a demandé « une colonne supplémentaire » : ce patron tournait **déjà dans la vue
   que je venais de lire** *(photos : `COALESCE(x_app, x)` + les deux colonnes nues + une
   **re-pose après le push**, 24 497 lignes sur 24 505)*. J'avais proposé une jointure — que
   la **RLS à 0 politique** rendait impossible. **Il avait la bonne forme avant moi.**
16. ⚠⚠ **NE PAS RELIRE SA PROPRE ÉCRITURE COMME SI ELLE FAISAIT AUTORITÉ.** Le worker écrivait
   notre date dans **la colonne de Hektor** *(« confort d'affichage, sans autorité »)*, et le
   magasin relisait **ce même registre** comme « ce que dit l'app ». **La boucle était fermée** :
   4 fausses « décisions de l'app », et **deux de mes comptages faux** *(« 0 sur 2 » puis
   « 4 sur 7 » — le vrai était 0 sur 3)*. ➡ **Toujours demander : qui a ÉCRIT cette valeur ?**
   Une colonne « ce que dit l'app » qui est aussi écrite par l'app ne prouve rien.
17. ⚠ **UN TÉMOIN NE DOIT PAS DÉPENDRE D'UNE TABLE QUE L'ÉPREUVE MODIFIE.** Mon témoin inverse
   a rendu `117 / 117 / 118` : l'épreuve d'effacement supprimait la ligne de carnet qui servait
   à **exclure** ce couple du décompte. Le patch était sain ; **la mesure était mal bâtie**.
   ➡ **Figer la liste des exclus AVANT les épreuves.**
18. ⭐ **AVANT DE CRIER À LA PERTE, REGARDER SI LA LIGNE EST UN BIEN D'ESSAI.** Le 13/10 j'ai
   bâti une alerte complète *(« une ligne du coffre a disparu, rien ne l'explique, sentinelle à
   poser »)* sur la clôture de **62774** — **le bac à sable du projet**, dont les traces sont
   **retirées exprès** *(« Bac a sable 62774 : propre »)*. **Les 2 clôtures réelles sur 2
   étaient intactes.** Les biens d'essai sont listés dans la mémoire de reprise : **62963,
   62774, 284/107, 15633/49544, contact 10355757**. **Les écarter d'abord.**
19. ⚠⚠ **UN HEARTBEAT NON ENREGISTRÉ PART DANS LE VIDE *ET COMPTE POUR UN SUCCÈS*.**
   `monitoring/heartbeat.py` écrit en **`PATCH` FILTRÉ** sur `app_worker_registry` : une clé
   **sans ligne** touche **0 ligne**, reçoit **204**, et `200 <= status < 300` compte un succès.
   Et `check_gti_health` **énumère la table** — donc il ne la regarde jamais. ⚠ **9 des 40 clés
   du run sont dans ce cas**, dont **`phase2.adresses_photos`**, alors que le commentaire du run
   promet le contraire depuis le 27/09 *(→ chantier ④)*. **Poser une étape avec `-WorkerKey`
   n'est PAS la faire surveiller : il faut la ligne de registre.**
21. ⚠⚠ **UN JOURNAL QUI AVALE SON ERREUR NE PROUVE RIEN.** `insertDeletedAnnonceLog` et son
   jumeau contacts journalisent l'échec d'écriture **et laissent la suppression continuer** :
   résultat mesurable, **une de leurs lignes a un `before_json` vide et aucun demandeur** — on a
   détruit sans savoir quoi. ➡ **Pour une trace de geste irréversible, l'écriture de la trace
   est une CONDITION, pas un effet de bord** : elle s'écrit **avant**, et si elle rate, on ne
   détruit pas.
22. ⚠ **UNE COLONNE POSÉE EN BASE NE REMONTE PAS TOUTE SEULE À L'ÉCRAN.** Deux fois le 13/10 :
   la clôture de mandat *(le cockpit lisait la fiche, qui n'a pas la colonne)* et la mention
   « supprimé chez Hektor » *(le `select` du front **nomme** ses colonnes)*. **Après avoir ajouté
   une colonne, chercher le `select` qui doit la porter** — sinon le silence est total.
26. ⚠⚠ **UN SEUIL ABSOLU SUR UN COMPTEUR QUI CROIT EST UNE ALARME A RETARDEMENT**
   *(14/10)*. Frédéric a demandé « monte le seuil » pour deux sondes jamais vertes. Mesure :
   elles montent de **+15,8** et **+2,7 par jour** — un seuil à 2 000 serait franchi dans
   **25 jours**. ➡ **Sur un compteur cumulatif, surveiller l'EMBALLEMENT** *(`rule: "growth"`,
   déjà dans le fichier)*, **pas le total** — et **régler les paramètres sur la vitesse
   mesurée**, jamais sur un chiffre rond. ⚠ Le prix à dire : une dérive **lente** ne sonnera
   plus jamais.
27. ⚠⚠ **UN SEUIL QUI PORTE UN RAISONNEMENT NE SE MONTE PAS « POUR FAIRE TAIRE »** *(14/10)*.
   Le seuil 4 de `ecart_statut_regle` tolérait **quatre REMONTÉES** nommées, et le commentaire
   disait : *« un cinquième écart veut dire que quelque chose a bougé »*. Les 2 nouveaux sont
   des **REDESCENTES** — autre famille — et l'un n'a **aucun numéro de dossier**.
   ➡ **Lire ce qu'un seuil PROTÈGE avant de le déplacer** ; proposer de changer **la règle**
   plutöt que le chiffre.
25. ⚠⚠ **UN POURCENTAGE ANNONCE SE MESURE SUR LE GESTE FINAL** *(14/10)*. J'ai promis
   « −21 % d'e-mails » en comptant **7 bascules** de `monitor.summary` sur 33. Rejeu du mois
   entier : **14 e-mails avant, 14 après — gain ZERO**. `dispatch` envoie **une** liste, donc
   toutes les bascules d'un même passage partent dans **un seul** e-mail, et le résumé n'a
   jamais basculé seul. ➡ **Mesurer sur ce qui PART, pas sur l'intermédiaire qui lui
   ressemble.** Même famille que la leçon 1. *(Le correctif reste : 7 e-mails plus propres.)*
23. ⭐⭐ **UNE ALERTE DOIT ÉCOUTER LA RÉPONSE DE L'HUMAIN** *(14/10)*. L'écran offrait deux
   boutons pour trancher un geste abandonné, et le rouge ne les regardait pas : Frédéric
   recevait un e-mail **chaque matin pour un problème qu'il avait déjà traité**. ➡ Quand on
   ajoute un bouton « j'ai traité », **chercher toutes les sondes qui comptent la même
   chose** — ici le bandeau et `geste_abandonne` écoutaient, le rouge non.
   ⚠ Et dans le même geste : **ne jamais soustraire des NOMBRES, croiser des IDENTIFIANTS**
   *(les 2 gestes tranchés n'existaient plus : « 2 − 2 = 0 » aurait effacé une vraie alerte)*.
24. ⚠ **UNE COLONNE « dernière exécution » PORTE SOUVENT LE DÉPART, PAS LA FIN**
   *(14/10)*. `sb_pull_state.derniere_descente` **et** `derniere_complete` valent toutes
   deux l'heure de **départ** *(149 lignes sur 154 identiques)*. Mon correctif de la veille
   en a déduit « la Descente a fini » et a gardé un faux avertissement.
   ➡ **Avant de conclure « c'est fini », vérifier que la colonne mesure une FIN.**
28. ⭐⭐ **DEUX ÉCRITURES DE LA MÊME TRANSACTION SE RECONNAISSENT À LA MICROSECONDE**
   *(15/10)*. Il fallait savoir quelles lignes du carnet appartenaient à *ce* travail et
   pas à un geste plus récent qui avait réussi. `now()` est **figé** pendant une
   transaction, et les deux colonnes l'ont pour défaut : donc
   `app_annonce_champ_app.ecrit_le = app_console_job.requested_at` **exactement**.
   Mesure : **un seul couple à 0,000 s** sur 21, les autres à 44 s, 124 s, 8 006 s,
   473 236 s. ➡ **Un horodatage de transaction est un IDENTIFIANT** — même famille que
   « on croise sur les identifiants, jamais sur les nombres » (leçon 23). ⚠ Et il n'était
   pas décoratif : les 2 lignes visées avaient été écrites **plus tard** (+2 h 14, +2 min)
   par le geste que Frédéric avait refait à la main. Sans lui, on effaçait du vrai.
29. ⚠⚠ **UNE RÈGLE ÉLARGIE DANS UNE VUE NE L'EST PAS DANS LES FONCTIONS QUI LA DOUBLENT**
   *(15/10)*. Le 14/10 j'ai élargi `app_en_attente_humain` à « 5 tentatives **OU** plus de
   3 h » et j'ai écrit « le travail devient visible ». **Faux à moitié** : `app_action_status`
   (le bandeau) et `app_action_resolve` (le clic) portent **leur propre copie** du `>= 5`.
   Résultat mesuré : 47824 sonne, apparaît dans le moniteur, et **n'a aucun bouton** — le
   clic était refusé **en silence**, parce que le front **jetait** le `{"resolved": false}`
   que la RPC rendait depuis toujours. ➡ **Après avoir changé un seuil, chercher qui
   d'autre porte le même seuil** ; et **un front qui jette le compte-rendu d'une RPC
   fabrique un bouton menteur**.
31. ⭐⭐ **UN RETOUR ARRIÈRE NE JUGE QUE SA PROPRE PART** *(15/10)*. Deux patchs du même jour
   touchaient **la même fonction**. L'inverse du premier exigeait l'empreinte d'**avant les
   deux** : les deux posés, il **défaisait correctement sa part, puis refusait** —
   `STOP : on ne retombe PAS sur l'empreinte d'origine (2315de8f…)`, et `2315de8f` **est**
   l'empreinte « second patch seul ». Le travail était bon, **le juge trop strict**. Il
   refusait sans rien casser *(l'exception annule tout)*, mais il **bloquait**.
   ➡ **Un inverse vérifie d'abord qu'il ne reste AUCUNE TRACE de ce qu'il devait retirer** ;
   l'empreinte globale ne s'exige que si l'autre patch n'est pas là — sinon il **dit**
   pourquoi elle diffère et **nomme l'autre inverse à jouer**. ⚠ Et ça ne se voit qu'en
   **éprouvant la chaîne complète dans l'ordre réel**, pas chaque patch isolément.
30. ⚠⚠⚠ **TROISIÈME FOIS : MES ÉPREUVES NE TRAVERSENT PAS LE COPIER-COLLER** *(15/10)*.
   Frédéric colle `patch_aligner_seuil_trancher` → `STOP : l'ancre du repli apparait 0 fois`.
   J'avais protégé l'**empreinte** avec `replace(…, chr(13), '')` et laissé les **ancres**
   nues : collé depuis Windows, le fichier arrive en **CRLF**, et une ancre **multi-lignes**
   ne se retrouve plus dans un corps stocké en LF. Une seule de mes trois ancres était
   multi-lignes — **c'est la seule qui a cassé**. Reproduit et guéri en lecture seule :
   la même ancre donne **1** en LF, **0** collée, **1** quand on nettoie **les deux côtés**.
   ⚠ **La leçon était déjà écrite, deux fois** *(mémoire « empreinte md5 faussée par les
   fins de ligne Windows », élargie le 12/10 : « ça touche TOUTE ANCRE MULTILIGNE »)*.
   ➡ **Règle mécanique : dans un patch destiné à être COLLÉ, envelopper
   `replace(…, chr(13), '')` autour de CHAQUE ancre, de CHAQUE texte inséré** *(sinon le CRLF
   entre dans `prosrc` et c'est l'INVERSE qui ne retrouvera plus rien)* **et du
   `pg_get_functiondef`/`pg_get_viewdef` lu. Puis COMPTER les ancres multi-lignes avant
   d'envoyer.**
   ⚠⚠ **Et la cause profonde : mon épreuve ne reproduisait pas LE TRANSPORT.** Trois épreuves
   vertes n'ont rien vu parce qu'elles passent par l'outil SQL, jamais par un copier-coller.
   **Le remède est d'éprouver le transport lui-même** : exécuter le patch via
   `EXECUTE replace(texte, chr(10), chr(13)||chr(10))` — ce qui a reproduit l'erreur exacte,
   puis prouvé la guérison (aller **et** retour, empreinte d'origine retrouvée).
20. ⚠ **UN `revoke ... from public` N'ENLÈVE PAS UN DROIT PAR DÉFAUT.** Supabase pose
   `GRANT EXECUTE ... TO authenticated` sur **toute nouvelle fonction** ; ce n'est pas PUBLIC,
   donc le `revoke` le laisse. **Relire `proacl` après avoir créé une fonction** — mon patch
   annonçait « `service_role` seulement » et la base disait autre chose.

### ⛔ Ce qui attend Frédéric

```
① ✅✅ LA FIN DU CHANTIER ③ -- 14/10, FAIT ET EPROUVE EN REEL :
   · option B collee : les 2 etapes du contrat de mandat sont hors du run ET en `legacy`
     (verifie en base, note corrigee) ;
   · bloc 2 colle -- ET UN TROISIEME VERROU TROUVE PAR L'ESSAI : app_console_claim_next_job
     a sa PROPRE liste de types par service. ⚠ NOUVEAU TYPE DE TRAVAIL = 3 verrous en base
     (contrainte, droits, DISTRIBUTION) + 5 endroits worker + ConsoleJobType + 8 fonctions ecran ;
   · la tache « GTI Reprise Envois Hektor » enregistree, et elle a TOURNE a 12:30 (0, sortie 0) ;
   · 4 services redemarres (12:29), pousse (front du bloc 2 en ligne, mesure) ;
   · ⭐⭐ L'ESSAI REEL SUR 62774 : une photo AJOUTEE chez nous avant Hektor (28 s, rangee a sa
     place definitive, temporaire efface, une seule ligne) puis SUPPRIMEE chez Hektor et chez nous
     (6 s, renumerotation, 0 autre photo emportee, les 4 d'origine intactes, 1 ligne au journal) ;
   · la piece 4 de 3c PROUVEE par le vrai chemin (posees 1).
   ⚠ RESTE, SANS URGENCE : redemarrer les 4 services un jour (les 2 messages du worker
     promettent desormais la reprise, mais ce texte n'est pas encore dans les processus) ;
     le dossier serveur VIDE de la photo d'essai (le geste efface le fichier, pas le dossier --
     comme celui du document).
   ➡ BLOC 3 REPORTE AU CHANTIER ⑦ : le crayon de cloture, l'ecran du journal.
①-avant CHANTIER ③ EN COURS -- 3a, le repli vendu/clos, 5a, 3b et 3c(3/5) sont FAITS.
   3c EN 5 PIECES, ordre valide par Frederic le 13/10 :
     [1+2 FAITES] la colonne mandat_date_cloture_app + la vue + l'alerte + le RPC
       de saisie app_set_mandat_cloture_optimistic (authenticated : VOULU).
     [4 FAITE]    la re-pose : RPC app_reposer_cloture_mandat_app (service_role
       seulement) + une etape NON BLOQUANTE dans le run (l. 1515-1539, apres le push)
       + un appel CIBLE dans push_single_annonce_to_supabase.py.
       ⚠ IL Y AVAIT DEUX CHEMINS QUI EFFACENT, PAS UN : le run ET le chemin immediat
         du worker (delete_target_remote efface toujours les lignes de registre de
         l'annonce) -- donc ~1 min apres n'importe quel geste.
       ⭐ AUCUN REDEMARRAGE : le worker lance ce .py en sous-processus (mesure).
   ⏰ A VERIFIER EN PREMIER LE 14/10 AU MATIN : les 2 dates d'essai (62966 = 2026-08-28,
     24933 = 2026-09-18) doivent ETRE ENCORE LA apres le run de 05:00. Regarder aussi
     le heartbeat `phase2.repose_cloture_mandat` et la ligne « phase2 re-pose cloture
     mandat » du journal du run. C'est la seule preuve par le VRAI chemin.
   ⚠ LA SUITE :
     [3 FAITE, SAUF LE CRAYON] l'ecran. ⭐ La logique existait DEJA et lisait la
       mauvaise source ; la bonne valeur etait DEJA CHARGEE dans ckCycleAff
       (loadRegisterCycleAffaires lit le registre PAR CYCLE). Une seule
       superposition (`ckClotureDe`) corrige SIX consommateurs : la frontiere des
       cycles, la pastille du cycle, le parcours du cockpit (son test lisait LA
       FICHE, qui n'a pas la colonne -> vide depuis toujours), l'historique V3, et
       « Jours restants » AUX DEUX ENDROITS + la jauge. `mandatClos` pose une fois :
       Clos avant Echu avant restant. ➕ la SAISIE : champ date dans la modale
       « Clos » -> app_set_mandat_cloture_optimistic (un echec n'empeche pas le
       changement de statut). ➕ le texte « Motif transmis a Hektor », FAUX depuis
       le 28/08, corrige. tsc -b vert.
       ⚠ NON FAIT, A DIRE : (a) le CRAYON dans la rubrique Mandat (saisie hors
         modale) -- il demande une verification a l'oeil, impossible sans session ;
         (b) la rubrique « Mandat SOURCE » laissee sur la version de Hektor,
         VOLONTAIREMENT (c'est son nom) -- a confirmer ;
         (c) PERSONNE N'A VU L'ECRAN. ⚠ VERCEL SE DEPLOIE SEUL AU PUSH : c'est
         FREDERIC qui pousse, pas moi.
     [5 FAITE, INERTE] le worker : son PATCH ecrit mandat_date_cloture_app (la
       notre) -- une ligne -- et le refus « aucun numero de mandat » passe de `error`
       a `done` (4 fausses alertes sur 5 ; la VRAIE erreur reste une erreur).
       L'ecriture du carnet est INCHANGEE. ⭐ Ca ferme la boucle qui m'a coute deux
       comptages faux. ⚠ LA MESURE A ECARTE l'appel au RPC : il refuse un couple
       absent du registre, et 4 clotures du journal etaient dans ce cas -- il les
       aurait PERDUES.
       ⛔⛔ INERTE JUSQU'AU REDEMARRAGE DES 4 SERVICES. ACCORD NON DONNE le 13/10 :
         JE N'AI RIEN REDEMARRE. A controler par l'HEURE DES PROCESSUS, pas par la
         croyance (le 08/10 : lances 1 h 24 APRES la modification du fichier).
     - appliquer_contrat_mandat.py : INUTILE depuis le 28/08 (il ecrit
       app_view_generale.mandat_date_cloture, une colonne qui ne monte NULLE PART --
       mesure : elle n'existe que dans app_mandat_register_current). Trois options
       presentees le 13/10 (A le retirer du run / B le redresser / C le commenter),
       RECOMMANDE A, Frederic n'a pas encore tranche.
   3d : LOT 2c, LE 14/10 -- 2 PIECES SUR 4.
     [1 FAITE, A COLLER] patch_chantier3_3d_lot2c_creer_document_2026-10-14.sql :
       app_console_creer_document_optimistic + sa jumelle photo. Elles creent la
       ligne chez nous ET posent app_document_id dans la charge du travail, dans
       la MEME transaction -- c'est ca qui allume le chemin differe du worker.
       REPETITION 15/15, 0 echec (collee par Frederic), dont le refus d'un depot
       sur le bien d'un AUTRE joue avec la vraie identite d'un commercial.
       ⭐ La garde des droits (app_console_can_access_dossier) faisait DEJA ce que
         Frederic demandait au point 3 : il n'y avait rien a ajouter.
       ⭐ REPLI NATUREL : sans la RPC, le travail part sans app_document_id et le
         worker reprend l'ancien chemin (121 envois sur 121 depuis mai).
     [2 FAITE, INERTE] le worker. ⛔ LES 4 SERVICES N'ONT PAS ETE REDEMARRES.
       ⚠⚠ LE DEFAUT QUI BLOQUAIT LE LOT DEPUIS LE 25/09 : le rangement calcule
         `document.storage_path || <place definitive>`, et la RPC pose le chemin
         TEMPORAIRE dedans -- donc le « || » ne se declenche JAMAIS. Le document
         aurait vecu dans temp/ pour toujours, marque « cloud_available ».
         Remede : le marqueur storage_status='pending_upload' (PAS le nom du
         chemin) remet storage_path a blanc avant le rangement.
     [1 et 2 EN PRODUCTION] patch colle, 4 services redemarres -- VERIFIE, pas cru :
       les deux RPC sont en base (authenticated oui, anon NON), et les 4 processus
       sont nes a 10:21:5x alors que le fichier a ete modifie a 10:10:24.
       ⚠ Get-Process StartTime est REFUSE (autre compte) : passer par
         Get-CimInstance Win32_Process.
     [3 FAITE] le front. Un SEUL point d'appel pour les deux objets
       (poserNotreLigneAvantHektor) -- deux copies divergeraient.
       ⚠ L'ORDRE EST IMPOSE PAR LA POLITIQUE DE STORAGE : le travail, PUIS le
         fichier, PUIS la ligne. La relecture du travail vient APRES l'appel, c'est
         elle qui rapporte la charge enrichie de app_document_id.
       ⭐⭐ ET J'AVAIS DIT FAUX A FREDERIC : ce n'etait pas « une tuile cassee en fin
         de galerie ». L'ecran faisait `if (!url) return null` -- la photo n'etait
         PAS AFFICHEE DU TOUT. Une absence est pire qu'une erreur : elle ne se
         remarque pas. Le negociateur deposait, ne voyait rien, recommencait.
         -> une TUILE D'ATTENTE remplace l'absence.
       ⚠ hektor_photo_id etait declare NON NUL et il mentait (3 usages, aucun ne le
         lit). Et sourcePhotos avait besoin d'un type explicite : sans lui, l'objet
         de secours formait une UNION et TypeScript refusait storage_status.
     [4 FAITE, MAIS ELLE NE TOURNE PAS] scheduled/run_reprise_envois_hektor.ps1,
       12:30, lot de 50 (le creux : run fini ~07:30, descente jusqu'a 08:49,
       rattrapage a 21:00 ; 50 envois = ~17 min de worker).
       ⛔⛔ MESURE DU 14/10 : 7 TACHES « GTI », AUCUNE N'APPELLE LE REPRENEUR.
         UN .ps1 DANS scheduled/ NE TOURNE PAS. A ENREGISTRER PAR FREDERIC.
       ⭐ Mesure : ZERO ligne en a_envoyer/echec aujourd'hui -- normal, le chemin
         etait dormant. C'est un FILET, utile a partir de la piece 3.
       ⚠ Pas de battement -WorkerKey (lecon du 13/10) : la surveillance passe par le
         resultat de la tache Windows.
   ⭐ LES 4 EPREUVES ROUGES SONT REPAREES -- 294 controles verts, 0 echec, 17 epreuves
     (une premiere depuis le 27/09) :
     - test_photo_ajout_gardee : la doublure de fabriquerDerivesApresRangement
       manquait (bf3afb9). +4 controles, dont « archivee : les derives SONT fabriques
       quand meme, sans le cloud ».
     - test_porte_contacts : ⚠ LE CODE EST JUSTE, LES EXPRESSIONS ETAIENT PERIMEES.
       L'une accusait la bonne reponse (`let contactId` avant le try, pour le catch) ;
       son propre commentaire previenait « au bout de trois fois » -- c'etait la
       TROISIEME. On guette le VRAI danger par une reference arriere \1 (une variable
       passee comme SA PROPRE SOURCE), sur le code SANS LES COMMENTAIRES -- sinon le
       commentaire qui raconte l'ancien defaut le declenche lui-meme.
     - test_reprendre_envois : (n) exigeait « offset= », la technique ABANDONNEE
       EXPRES. Le curseur est un PROGRES (l'offset saute des lignes quand l'ensemble
       bouge, et le script pose des travaux pendant qu'il lit). +controle (o).
     - test_aucune_fausse_promesse : ⭐⭐ elle est passee au rouge PARCE QUE j'ai ecrit
       le .ps1, et elle avait RAISON de crier. Mais elle mesurait un FICHIER : la
       suivre aurait cree la fausse promesse qu'elle interdit. Elle mesure maintenant
       LA TACHE WINDOWS, dans les DEUX SENS (pas de tache -> le message prudent est
       EXIGE ; une tache -> la promesse est EXIGEE). Les deux branches sont prouvees.
       ➡ LES 2 MESSAGES DU WORKER N'ONT DONC PAS BOUGE : ils disent encore la verite.
   ⭐⭐ LA FUITE DE LA SALLE D'ATTENTE : NETTOYEE ET BOUCHEE LE 14/10.
     109 fichiers, 196 Mo dormaient sous temp/ du coffre documents depuis le 14/05.
     ⚠ ILS NE VENAIENT PAS D'OU JE CROYAIS : 93 sortaient des TROIS GENERATEURS DE
       PDF (estimation 137 Mo, cadastre 19 Mo, mandat 2,3 Mo), 11 seulement de
       l'ajout de documents, 5 sans aucun travail (tous des essais).
     ⭐ Les 104 travaux etaient tous « done » et AUCUNE LIGNE VIVANTE N'Y POINTAIT
       (0 sur 162 544 documents, 0 sur 441 199 photos) : rien en vol, zero perte.
     SUPPRIMES : 109, verifie PAR DEUX CHEMINS -- le script recompte a la source, et
       storage.objects passe de 22 973 a 22 864 (exactement 109 de moins).
     Trace : logs/temporaires_avant_nettoyage_2026-10-14T08-07-17.tsv
     Outil : Console/nettoyer_temporaires_orphelins.js -- QUATRE gardes refaites a
       chaque passage, et il ne supprime rien sans --supprimer.
     LE BOUCHON TENAIT EN UN SEUL ENDROIT : handleUploadDocumentToHektor, par ou
       passent les quatre types. On y recopie la regle des photos ET sa prudence :
       on ne supprime que si la copie serveur a reussi, sinon on garde et on le DIT.
   ⚠ DEUX EPREUVES ETAIENT DEJA ROUGES AVANT (verifie contre HEAD), NON REPAREES --
     HORS PERIMETRE, Frederic n'a rien dit :
     - test_photo_ajout_gardee est tombee le 27/09 quand fabriquerDerivesApres-
       Rangement est entre dans persistProvidedPhotoFile (bf3afb9, G.17) : ses
       doublures n'ont jamais suivi -> ReferenceError. 17 JOURS ROUGE SANS QUE
       PERSONNE LE VOIE.
     - test_porte_contacts : 11 verts, 2 rouges sur « L4-c ② l'ecrasement de
       l'identite par la cible », depuis le chantier contacts du 23/09.
   Puis : 3e (le reste : 4 services, le push, l'ecran du journal, la photo)
①-ter ⭐⭐ LES TROIS CLOTURES DE MANDAT « DE L'APP » ETAIENT DES ESSAIS (etabli le 13/10).
   62966 = L'ANNONCE D'ESSAI, designee explicitement pour eprouver la cloture
     (CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md, 3 fois : « Essai sur l'annonce
      62966 (mandat 660) » -- exactement notre ligne, n° 18842)
   62774 = LE BAC A SABLE (« Bac a sable 62774 : propre »)
   24933 = le bien d'essai des taches 3.2 / 3.4 (4 fichiers SUPPRESSION_ESSAIS*)
   ➡ AUCUN UTILISATEUR REEL N'A JAMAIS CLOS UN MANDAT DANS L'APP. Colle a Frederic :
     « CE SERA mon app qui va le gerer » -- au futur. Le defaut etait reel (la date
     ne tenait pas), mais il n'a JAMAIS perdu une donnee de production.
   ➡ FAUSSE ALERTE REFERMEE : la ligne « disparue » de 62774 etait une trace d'essai,
     retiree comme les autres. PAS DE SENTINELLE A POSER.
   ⭐ Les 2 dates reposees sont des donnees d'ESSAI, LAISSEES EXPRES : ce sont les
     TEMOINS DE LA PIECE 4 -- si elles survivent a la nuit, la re-pose marche.
     A retirer quand la piece 4 sera prouvee.
①-bis NE SE DECIDENT PAS SANS LUI, sortis du chantier ③ les 12 et 13/10 :
     - MODIFIER LES CHAMPS d'un bien vendu/clos : ce n'est PAS un repli, c'est un autre
       chantier (la file d'attente de 10 min a le n° de dossier pour cle primaire), et
       l'ecran l'interdit deliberement (« Lecture seule jusqu'a desarchivage »)
     - REACTIVER UN BIEN CLOS marche maintenant ; l'ecran promet encore « desarchiver »
       a un bien qui n'est pas archive (bandeau de l'index leger) -> chantier ⑦
     - ⛔ L'INTERRUPTEUR CHAMPS_APP_ANNONCE RESTE ETEINT (tranche le 13/10, « sommes-nous
       prets ? » -> NON). La regle « vide ne gagne pas » est posee (13/10, inerte, prouve),
       mais le CRITERE DU PROJET n'est pas rempli : on n'allume qu'un champ que l'APP CREE
       et que HEKTOR N'ENTRETIENT PAS (contrat_autorite.py le dit deux fois). Or nos 4
       champs sont tous entretenus par Hektor, et la valeur qu'on ecrit est PROVISOIRE
       ~70 s sans marque « confirmee ». C'est LA COUPURE qui nous rendra prets.
     - 📜 LES NEGOCIATEURS INACTIFS : 1 522 biens vivants (11 %) sont a leur nom, 4 227
       (31 %) n'ont aucun negociateur -- mais seulement 12 actifs et 2 diffuses.
       DECISION DE FREDERIC LE 13/10 : ON NE TOUCHE A RIEN. Ne pas relancer.
       (La modale « reaffecter » n'est PAS cassee : elle montre les 30 actifs de l'agence
        choisie ; Firminy n'en a qu'un. GONZALEZ est inactif, d'ou l'essai non fait.)
② REPORTE PAR LUI, chantier ② (noter, NE PAS relancer de soi-meme) :
     - ce que doit voir exactement un AGENT COMMERCIAL. L'essai du 12/10 a prouve
       que tout abaisser casse le rapprochement (93 % de lignes mortes) : les
       annonces doivent rester au reseau. Trois sorties possibles dans la note.
     - la fonction de SECOURS admin-users, a deployer A PART chez Supabase :
         npx supabase functions deploy admin-users --project-ref dwaqxfrinihnychuoptk
       (inutile tant que Render repond)
     - le refus du prix n'a JAMAIS ETE EXECUTE (ma session ne peut pas ecrire)
     - un essai REEL d'un geste chez Hektor par un negociateur
③ QUESTIONS DE FAIT   les negociateurs saisissent-ils encore leurs visites dans Hektor ?
                      pourquoi 62 000 contacts seulement au cloud sur 356 000 ?
④ HORS CODE (etape 3) : A.4 zone DNS (La Boite Immo -> OVH, garder www) · A.5 les leads ·
   l'export PROTEXA · contrats A.1 et A.2
⑤ C.9-couple          creer un menage d'essai (la sonde est prete)
⑥ LE CARNET DES LIENS : cause racine NOTEE ET REPORTEE le 10/10 (un lien s'identifie
   par un badge CALCULE alors que son numero existe). Ne pas la relancer.
⑦ LA SENTINELLE DU REGISTRE (13/10) : elle ne crie plus au loup, mais la CAUSE reste --
   la doublure app_mandat__sb descend une heure APRES le push (table 97 sur 110).
   A TRANCHER PAR LUI, je n'ai rien choisi :
     A descendre app_mandat__sb en PREMIER      B decaler le moniteur apres 08:05
   Controle a faire : l'e-mail de demain 07:48 doit porter un WARNING « NON CONCLUANT »
   au lieu du rouge, et 0 ecart a 09:48.
⑦-bis SA SOEUR EST CORRIGEE AUSSI (13/10, go « A maintenant ») : data.recherche_
   divergente lit desormais la fraicheur REELLE (max(refreshed_at) du natif contre
   sb_pull_state.derniere_descente) au lieu de l'indice propose le 29/08. 8 epreuves,
   temoin inverse.
   ⚠⚠ MAIS J'AI EU TORT DE DIRE « c'etait la DERNIERE de la famille » : il y en avait
   une 4e, data.relation_disparue, corrigee le 14/10 par l'autre session (a4ab4d9) --
   Frederic a recu son faux rouge le 14/10 a 05:51. DEUX ERREURS DE METHODE : (1) j'ai
   cru un DOCSTRING au lieu de lire le code (c'est la regle n° 4 de cette page) ;
   (2) j'ai grepe « __sb » DANS LE MONITEUR, alors que la formule vit dans
   phase2/checks/ -- un balayage de famille se fait LA OU VIVENT LES MEMBRES.
   Balayage refait le 14/10 : le moniteur importe QUATRE formules. mandat_un_numero et
   relation_disparue ont leur garde ; annonce_un_numero et mandat_disparu n'en ont AUCUN,
   mais mesure sur 104 passages : annonce_un_numero n'a JAMAIS crie, et les 7 rouges de
   mandat_disparu sont DISPERSES sur la journee (01:48 a 23:48), donc ca ne ressemble pas
   au faux cri du matin. JE NE CONCLUS PAS : 3 options en section 14 de la note,
   RECOMMANDE « mesurer d'abord d'ou viennent ces 7 rouges ». A trancher par Frederic.
⑧ ⛔ LE DECALAGE DU MONITEUR NE MARCHE PAS -- mesure du 13/10, consigne NON EXECUTEE.
   La descente a dure de 18 a 64 MINUTES sur les 12 derniers jours : partie a 07:45,
   elle finit entre 08:03 et 08:49. « Apres 08:05 » ne suffit donc pas (11 jours sur 12).
   Et la fenetre dangereuse (run ~06:49 -> copie prete) fait 1 h 14 a 2 h, alors que le
   moniteur a UN SEUL declencheur repete TOUTES LES 2 H (depart 17:48:54) : quel que soit
   le decalage, un passage tombe dedans, et les 12 passages bougeraient.
   TRANCHE LE 13/10 : OPTION 1, ON NE TOUCHE A RIEN -- le code gere le cas quelle que
   soit la duree de la descente. Rien a faire plus tard : la question est FERMEE, pas
   reportee. Aucune tache planifiee n'a ete modifiee.
   ✅ LES TROIS SENTINELLES SONT CORRIGEES (13/10) : data.doublure_journal avait DEUX
   defauts, et la mesure a renverse le diagnostic. (1) l'horloge : releve_le est une
   date LOCALE comparee a une date UTC -- 10 nuits de journaux montrent 01:48 « a jour »
   10 fois sur 10 quand 03:48, MEMES DONNEES, avertit 10 fois sur 10. (2) le vrai
   defaut : ce releve est ecrit par la DESCENTE (run_descente.ps1 etape 2/3, vers
   08:03-08:49), donc « est-il d'aujourd'hui ? » est FAUX chaque nuit -> 3 avertissements
   par nuit sur un etat NORMAL. Remede (option B) : on lit la fraicheur reelle, pas une
   heure en dur -- tant que la Descente du jour n'a pas tourne, la veille est normale ;
   des qu'elle a tourne, le releve doit avoir suivi (panne dite a 09:48, le jour meme).
   Pas d'angle mort : « GTI Descente » est deja surveillee en critical.
   Gain : 4 bruits de moins par nuit, 1 avertissement de moins dans l'e-mail du matin.
   ⚠ MESURE DU 14/10 : 3 BRUITS SUR 4, PAS 4. derniere_descente porte l'heure de DEPART
   (toutes ses lignes valent 07:45:03, et derniere_complete AUSSI -- 149 sur 154
   identiques) : AUCUNE colonne ne dit « la Descente est finie ». A 07:48 la sonde la
   croyait terminee alors que le releve est son etape 2 sur 3. Corrige le 14/10 par un
   DELAI MESURE (DELAI_DESCENTE_MINUTES = 120 ; la descente dure 18 a 64 min, et le
   passage de 09:48 juge quand meme -> une vraie panne sort le jour meme).
⑨ ✅ LE CLIC DE L'HUMAIN ETEINT ENFIN L'ALERTE (14/10, go « oui »).
   QUESTION DE FREDERIC : « la plupart des erreurs sont connues, comment arreter de les
   faire sonner ». REPONSE MESUREE : IL N'Y A QU'UNE CHOSE QUI SONNE. Les 8 warnings de
   son e-mail n'envoient RIEN (l. 66-68 : seuls les critical declenchent un envoi) ;
   le seul rouge est data.travaux_en_erreur.
   LE DEFAUT : le bandeau de l'ecran a deux boutons, et app_action_resolve fait UN SEUL
   geste -- un INSERT dans app_pending_resolution. Il ne touche PAS au travail, qui
   reste `error` pour toujours. Donc le bandeau se taisait, data.geste_abandonne se
   taisait, ET LE ROUGE CONTINUAIT : un e-mail chaque matin pour un probleme deja traite.
   REMEDE : champ OPTIONNEL "exclure_resolus" sur CETTE sentinelle seulement (les 39
   autres ne bougent pas). Le rouge ne compte plus ce qu'un humain a tranche, ni les
   travaux de plus de 30 jours (la vue du bandeau s'arrete a 30 jours : au-dela personne
   ne peut plus cliquer). Rien n'est masque en silence, le message les compte a part.
   ⭐⭐ LE PIEGE EVITE PAR LA MESURE : « brut moins nombre de resolutions » aurait efface
   une vraie alerte -- les 2 gestes deja tranches N'EXISTENT PLUS dans app_console_job.
   ON CROISE SUR LES IDENTIFIANTS, JAMAIS SUR LES NOMBRES.
   Garde-fou chiffre : au-dela de 200 travaux on ne filtre pas (max jamais atteint sur
   220 passages : 24, moyenne 5,8). Idem si une lecture echoue, si une liste peut etre
   tronquee, ou si la forme est inconnue : EN CAS DE DOUTE ON CRIE COMME AVANT.
   10 epreuves + temoin inverse SUR LA BOUCLE (un correctif branche nulle part passe
   toutes les epreuves unitaires) + controle contre la PRODUCTION (non_filtre_cause =
   None, donc les 2 lectures PostgREST marchent -- sans ce controle le correctif serait
   mort en silence).
   ⬜ RESTE A FREDERIC : (a) CLIQUER « J'ai refait » sur les 2 gestes -- aucun risque,
   61672 a abouti chez Hektor (le bien EST « Sous offre ») et 62963 est un bien d'essai
   de l'autre session ; le rouge doit passer au vert et l'e-mail ne plus partir.
   (b) LES 8 WARNINGS : autre sujet, ILS NE SONNENT PAS, chacun a un seuil pose pour une
   raison. A reprendre un par un S'IL LE DEMANDE -- rien n'a ete decide.
⑩ ✅ « ABANDONNER CE GESTE » DEFAIT ENFIN L'ECRITURE DE L'APP (15/10, go « oui fais A »).
   QUESTION DE FREDERIC : « comment annuler le changement dans l'apps, remettre le montant
   comme hektor ». REPONSE : ca n'existait pas. Les DEUX boutons du bandeau faisaient la
   meme chose -- faire taire l'alerte -- et la valeur ecrite chez nous restait en place
   alors que Hektor n'avait jamais recu le geste.
   REMEDE : « Abandonner » = « ce geste n'a pas eu lieu ». La fiche reprend l'etat d'avant
   (DEJA pose dans la charge du travail par les RPC optimistes), et la ligne de carnet est
   EFFACEE -- une ligne absente veut dire « l'app n'a rien a dire », donc Hektor gagne
   (contrat d'autorite). « J'ai refait » n'est PAS touche.
   GARDE-FOU : ecrit_le = requested_at a la microseconde (lecon 28). Les 4 gestes d'AFFAIRE
   sont hors de portee EXPRES : le worker les restaure deja (restaurerEtatAffaire).
   11 controles verts sur la vraie base en transaction annulee + TEMOIN INVERSE.
   Detail : notice/ABANDON_DEFAIT_LE_GESTE_2026-10-15.md
   ✅ (d) ALIGNE LE 15/10, go « OUI ALIGNE LES 2 » :
   patch_aligner_seuil_trancher_2026-10-15.sql -- app_action_status ET app_action_resolve
   prennent la regle de la vue (« 5 tentatives OU plus de 3 h »).
   ⚠ LE PRIX, DIT : un travail de 4 h a 2 tentatives devient tranchable alors que le filet
     pourrait encore le reprendre (fenetre 24 h). ⭐ Mais le filet ne couvre que 9 types
     IDEMPOTENTS, et les 2 travaux du jour n'en sont pas : rien a rejouer, rien a perdre.
   ⚠⚠ ET UN TROISIEME MUR, TROUVE PAR LA MESURE : aligner les seuils N'AURAIT PAS SUFFI.
     app_action_status leve 'dossier_not_found' si le bien n'est pas dans
     app_dossier_current -- et 47824 est VENDU (« Maison de village a renover », VM8012),
     donc dans l'index des vendus/clos depuis le 20/05. Le front avalait l'erreur (EXPRES)
     et LE BANDEAU NE S'AFFICHAIT JAMAIS. ⭐ Meme supposition fausse que le defaut 5a du
     08/10, fausse pour 44 259 biens : balayee ici dans sa DERNIERE case (lecon 9).
     Les ARCHIVES sont incluses expres : trancher une alerte ne modifie pas le bien.
   11 controles avant/apres sur les VRAIS travaux (ERREUR dossier_not_found -> abandonnes=1 ;
   61439 a 1 h 30 reste « rien_a_trancher » : la regle des 3 h n'ouvre pas tout).
   LES DEUX RETOURS ARRIERE RETOMBENT A L'OCTET PRES (empreintes mesurees aux 3 etapes).
   OU SONT LES BOUTONS (question de Frederic) : PAS dans l'ecran Sante -- sur LA FICHE DU
   BIEN. Cockpit onglet « Le Bien » (App.tsx:28785, masque si lecture seule) et au-dessus
   de la barre d'onglets de la fiche classique (App.tsx:30394, toujours). Chemin court :
   Sante -> cliquer le bien cite par l'alerte (le lien de ⑦-5 A).
   ✅ (a) LES DEUX PATCHS SONT COLLES -- controle du 15/10 : les 5 morceaux sont en base,
   0 retour chariot, empreintes ad573c70 (resolve) et 9d68752a (status, exactement celle que
   l'epreuve avait predite). Le bandeau du bien VENDU 47824 rend « 1 geste » (avant : erreur,
   bandeau invisible) ; 61672 et 62963 : 1 chacun ; 61439 (1 h 48) : 0, a partir de 12:02.
   Sur les QUATRE, lignes_a_defaire = 0 -- rien a remettre.
   ⚠ LA VERSION 1 DES PATCHS A ECHOUE AU COLLAGE (CRLF, lecon 30) : rien n'avait ete ecrit.
   ⚠⚠ ET LE CONTROLE A TROUVE UN DEFAUT DANS LE RETOUR ARRIERE, corrige (lecon 31) : les deux
     patchs touchent la MEME fonction, et l'inverse du premier exigeait l'empreinte d'avant
     LES DEUX -- il defaisait sa part puis refusait. 6 controles de la chaine complete.
   ⬜ RESTE A FREDERIC : (b) pousser le front (sans lui, le bandeau ne DIT pas ce que le clic
   a fait, et il cache encore une ligne qu'il n'a pas tranchee) ; (c) « J'ai refait » sur
   61672 et 62963 ; (d) « Abandonner » sur 47824 ; (e) 61439 a partir de 12:02.
```

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *à finir tant que Hektor vit*

```
G.1-b    ✅ PLUS DE PEREMPTION -- CLOS LE 14/10 PAR UNE DECISION (chantier 6, point 6a) :
         « il n'y a pas de documents dans les brouillons » (Frederic). Les 527 sont HORS
         rattrapage (HORS_AUTO, enqueue_empreinte_lot.js), le worker n'est pas touche.
G.2      rebalayer le PARC VIVANT, fige depuis le 20/08 (apres le rattrapage ; perimetre =
         toutes les vivantes, estimations comprises -- decision de Frederic)
C.9-couple · C.13-c · E.1 (recherches, visites, documents, signatures) · A.3 · A.4
```

### Ce qui reste vrai de l'exploitation

- **Le rattrapage des documents** tourne à 21 h, **lots de 1 000**. Reste ~6 900 annonces, fin
  vers le **16-17/10**. ⚠ **À remettre à 2 500** quand les vendus/clos seront finis.
- ⏰ **La matinée, depuis le 12/10** : `03:00` recherches actives · `05:00` le run *(55 étapes,
  fin 07:18-07:34)* · **`07:45` la descente** *(elle attend le run jusqu'à 45 min)* · `08:00`
  les relances e-mail · **`09:00` la sauvegarde**. ⚠ C'est un **pansement** : la descente
  saturait la passerelle Supabase. Reprise du run :
  `.\scheduled\run_quotidien.ps1 -StartAtLabel "<étiquette exacte>"`.
- **Render et Vercel se déploient seuls** sur un push vers `main` : `/health` rend le commit.
  ⚠ **La fonction Supabase `admin-users` NE se déploie PAS par un push.**
- ⚠ **Une autre session travaille en parallèle** : relire `git log` avant d'écrire, et stager
  **fichier par fichier**.
- ⚠ **Les alertes n'ont qu'UN seul canal** : `WHATSAPP_ALERT_WEBHOOK` n'a jamais été posé.

---

## 3. Avant de coder — la liste de relecture *(plan, l. 1110 « ⛔ AVANT DE COMMENCER UN CHANTIER »)*

Elle existe *« parce que le 20/08 j'ai oublié trois fois un point déjà documenté »*.

1. La **section du plan** qui concerne la tâche — et ses voisines, les pièges y sont.
2. Les **notes citées** par cette section : elles portent les décisions déjà prises.
3. `notice/*.md` **et la racine**, par mot-clé — 160 notes au 07/10, la plupart citées nulle part.
4. `git log --all --diff-filter=D -- 'notice/*'` — 12 notes supprimées le 19/08 portent
   encore de la doctrine active. **À lancer depuis `C:\Hektor\Projet`.**
5. La **mémoire projet** : `C:\Users\admin\.claude\projects\C--Hektor\memory\`.

**Les trois questions, avant de dire qu'une chose est cassée :**
**Est-ce documenté ?** (ici, ce qui ressemble à une négligence est presque toujours une
décision écrite) · **Est-ce mesuré ?** (mesurer, *puis* conclure) · **Qu'est-ce que j'oublie ?**
(les cas voisins : la recherche supprimée, les contacts, les affaires…)

---

## 4. Ce qui ne se discute pas

- **Lire le CODE, pas les notes**, pour établir un état. *L'inventaire de `C.4` a été faux
  quatre fois parce que la liste ne suivait pas le code — c'est de là que vient l'impression
  de refaire les mêmes choses.*
- **Une mesure approximative vaut une mesure fausse.**
- **Une tâche n'est cochée que si son ÉNONCÉ est couvert**, et la mesure doit répondre à la
  question posée — pas montrer que « ça marche ». *(plan, l. 759 « ⚖ LA RÈGLE DU FAIT »)*
- **Ne rien écraser.** Additif et chirurgical, jamais de remplacement massif.
- **Pas de code sans « go » explicite.** Un message court, en cadrage, est une **question**.
- **Stager fichier par fichier.** Jamais `git add .` : 73 fichiers non suivis traînent
  dans le dépôt.
- **Les 5 règles du projet** et **la règle des identifiants** : plan, sections « LA RÈGLE DES
  IDENTIFIANTS » (l. 2970) et « LES CINQ RÈGLES » (l. 2981).
  *(un numéro ne se perd jamais · Hektor confirme, il n'écrase pas · une action a une fin
  visible · Hektor reste à jour tant qu'il diffuse · le miroir se met à jour, il ne se
  remplace pas)*

---

## 5. Les adresses

| | |
|---|---|
| le **pourquoi** | `notice/PLAN_DEV_ACTUALISE_2026-08-20.md` (3 092 l. au 08/10) |
| le **quoi**, item par item | `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (9 469 l. au 08/10 — lire la page de tête, l. 1-75) |
| le **dernier audit** | `notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md` — l'étape 2, objet par objet *(celui du 07/10, `AUDIT_AUTONOMIE_COMPLET_2026-10-07.md`, reste utile pour l'étape 3)* |
| l'**historique** de la page de tête | `notice/JOURNAL_DE_BORD.md` — *un pourquoi, jamais un ordre du jour* |
| le protocole de test en cours | `notice/PROTOCOLE_TEST_STATUTS_TRANSACTIONS_2026-09-01.md` |
| les pièges déjà payés | la mémoire projet (voir §3.5) |

> Ces deux documents pèsent 116 k tokens. **Ne jamais les lire en entier** : ouvrir la
> section concernée par son numéro de ligne, comme ci-dessus.

---

## 6. Pièges d'outillage

- **4 services worker** partagent `console_job_worker.js` : redémarrer **un seul ne suffit
  pas**. Un correctif non redémarré n'est pas actif — plusieurs essais ont été perdus comme ça.
- Le front se valide par `npm run build` dans `apps/hektor-v1` (c'est ce que fait Vercel).
- Vérifier un écran qui « plante » : **la console du déployé d'abord**, la base ensuite.
- **Les renvois `l. N` se décalent en silence** dès qu'on insère ailleurs dans la liste.
  Un renvoi ne se *calcule* pas, il se *trouve* — le 26/09, quatre étaient faux, dont
  trois depuis des jours *(`C.9-couple` pointait la section `C.4`)*. Après toute édition
  de la liste ou de cette page :

  ```bash
  python phase2/checks/verifier_renvois_liste.py --reparer
  ```

  Puis **relancer sans `--reparer`** : une correction change la taille du texte, donc
  peut décaler les suivants.

---

## 7. En fin de session — deux gestes, deux minutes

1. **RÉÉCRIRE le §2** de cette page — *réécrire, pas ajouter un bloc en haut.* C'est
   l'empilement qui l'avait porté à 467 lignes sur 609, avec trois états datés marqués
   *« ne jamais relire comme un ordre du jour »* : un document qui se contredit ne tient
   plus le fil. Ce qui sort du présent descend dans `notice/JOURNAL_DE_BORD.md`.
2. **Réécrire la mémoire de reprise** (`reprise-…` dans le dossier mémoire), toujours la même,
   jamais une nouvelle par date. *Elle datait du 02/09 alors que 68 commits avaient suivi.*
