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
| ③ | **Hektor d'abord → chez nous d'abord** *(`notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md`)* | 🔧 **en cours** — **5 patchs, 0 déploiement, 0 redémarrage**, tous éprouvés en réel. ✅ **3a** : « Actif » et « Mandat clos » écrivent le **statut et le diffusable chez nous d'abord** *(73 s gagnées)* · ✅ **un bien VENDU/CLOS est de nouveau manipulable** — **8 941** annonces bloquées depuis le 25/08 *(les 35 318 **archives** restent en lecture seule, règle de Frédéric)* · ✅ **défaut 5a** : le désarchivage porte enfin **notre vrai numéro** · ✅ **3b** : **archiver** et **changer de négociateur** écrivent la **fiche**, et ⭐ **le MOTIF d'archivage est gardé chez nous pour la première fois**. ⚠ **Reste** : **3c** la clôture de mandat *(la chaîne existe et son interrupteur est allumé — l'applicateur écrit juste au mauvais grain)* · **3d/3e** documents et photos |
| ④ | aucun échec silencieux — 9 points *(`notice/CHANTIER_4_ECHECS_SILENCIEUX_2026-10-09.md`)* | ✅ **FINI le 11/10** |
| ⑤ | les gestes cassés *(`notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md`)* | ✅ **FINI le 09/10** |
| ⑥ | ce qui ne redescend pas de Hektor (G.1-b, G.2 → G.6, photos, agenda) *(liste : `D.0`, l. 970 · photos, section **10bis**, l. 1170)* | ⬜ |
| ⑦ | les gestes qui manquent | ⬜ |
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

### ⛔ Ce qui attend Frédéric

```
① CHANTIER ③ EN COURS -- 3a, le repli vendu/clos, 5a et 3b sont FAITS.
   La suite : 3c (la cloture de mandat), 3d / 3e (documents et photos)
①-bis NE SE DECIDENT PAS SANS LUI, sortis du chantier ③ les 12 et 13/10 :
     - MODIFIER LES CHAMPS d'un bien vendu/clos : ce n'est PAS un repli, c'est un autre
       chantier (la file d'attente de 10 min a le n° de dossier pour cle primaire), et
       l'ecran l'interdit deliberement (« Lecture seule jusqu'a desarchivage »)
     - REACTIVER UN BIEN CLOS marche maintenant ; l'ecran promet encore « desarchiver »
       a un bien qui n'est pas archive (bandeau de l'index leger) -> chantier ⑦
     - L'INTERRUPTEUR DU CONTRAT D'ANNONCE (CHAMPS_APP_ANNONCE) : NE PAS L'ALLUMER tant
       que appliquer_contrat.py n'a pas la regle « vide ne gagne pas » -- il pose la
       valeur de Supabase SANS filtre, et n'importe meme pas la constante (ses freres
       mandat et affaire, eux, l'appliquent)
     - LA MODALE « REAFFECTER LE NEGOCIATEUR » ne propose QU'UN SEUL nom (Emmanuelle
       PEREIRA), et changer d'agence ne change pas la liste -> essai reel impossible a
       defaire, donc NON FAIT. Defaut a part, a trancher.
     - LE MOTIF du statut CLOS ne va nulle part (ni Hektor -- formulaire validerClos
       eteint depuis le 28/08 -- ni chez nous). Celui de l'ARCHIVAGE est gardé depuis
       le 13/10. A decider pour le Clos : carnet, ou circuit des demandes ?
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
   temoin inverse. C'etait la DERNIERE de la famille (mesure).
⑧ ⛔ LE DECALAGE DU MONITEUR NE MARCHE PAS -- mesure du 13/10, consigne NON EXECUTEE.
   La descente a dure de 18 a 64 MINUTES sur les 12 derniers jours : partie a 07:45,
   elle finit entre 08:03 et 08:49. « Apres 08:05 » ne suffit donc pas (11 jours sur 12).
   Et la fenetre dangereuse (run ~06:49 -> copie prete) fait 1 h 14 a 2 h, alors que le
   moniteur a UN SEUL declencheur repete TOUTES LES 2 H (depart 17:48:54) : quel que soit
   le decalage, un passage tombe dedans, et les 12 passages bougeraient.
   Le code gere deja le cas. Si Frederic veut fermer la cause a la source :
     1 ne rien toucher (recommande)   2 descendre les 2 doublures EN PREMIER (touche
     au run, go necessaire)           3 moniteur toutes les 3 h
   ⚠ ET UN TROISIEME CAS DE LA MEME CONFUSION UTC/LOCALE, NON CORRIGE (son appel) :
   l. ~2184, releve_le est une date LOCALE comparee a datetime.now(timezone.utc) ->
   entre minuit et 2 h, le passage de 01:48 peut dire « a jour » sur le releve de la
   VEILLE. Faux vert, deux heures par nuit.
```

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *à finir tant que Hektor vit*

```
G.1-b    les 515 brouillons -- AVANT que le rattrapage les atteigne : la NUIT DU 15 AU 16/10
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

## 3. Avant de coder — la liste de relecture *(plan, l. 1037 « ⛔ AVANT DE COMMENCER UN CHANTIER »)*

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
  question posée — pas montrer que « ça marche ». *(plan, l. 686 « ⚖ LA RÈGLE DU FAIT »)*
- **Ne rien écraser.** Additif et chirurgical, jamais de remplacement massif.
- **Pas de code sans « go » explicite.** Un message court, en cadrage, est une **question**.
- **Stager fichier par fichier.** Jamais `git add .` : 73 fichiers non suivis traînent
  dans le dépôt.
- **Les 5 règles du projet** et **la règle des identifiants** : plan, sections « LA RÈGLE DES
  IDENTIFIANTS » (l. 2746) et « LES CINQ RÈGLES » (l. 2757).
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
