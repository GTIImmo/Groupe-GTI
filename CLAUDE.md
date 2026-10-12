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
> *(l'état du 08/10 et la journée du 09/10 y sont descendus le 09/10 — elle avait fait passer
> cette page de 60 à 160 lignes)*.

**Réécrit le 09/10/2026, à la clôture du chantier ⑤.**

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
résultat** → plan, liste et cette page à jour. Le prompt de reprise est prêt :
**`notice/PROMPT_CHANTIER_ETAPE2.md`** (une seule ligne à changer, et un § 6 « déjà appris »).

| # | chantier | état |
|---|---|---|
| ① | sécurité : 136 fonctions ouvertes à la clé publique *(`notice/CHANTIER_1_SECURITE_2026-10-08.md`)* | ✅ **FINI** — patch appliqué le 08/10, et la nuit du 09/10 est passée sans refus de droits |
| ② | **les droits du négociateur** — 2a → 2i *(`notice/CHANTIER_2_DROITS_NEGOCIATEUR_2026-10-09.md`)* | 🔧 **2a FINI le 12/10 : la décision est prise** — audit refait et élargi *(Frédéric : « normalement tout existe déjà », « cela ne doit surtout pas changer les worker », « tu n'as pas audité les consultations ? »)*. ⭐ **l'option B était DÉJÀ codée de bout en bout** pour 3 gestes, et `request_type` n'a **aucune contrainte** : ajouter un type ne demande **aucun patch SQL** · ✅ **worker intact, prouvé** : 0 occurrence du circuit dans `Console/`, `backend/`, `scheduled/` ; et l'écriture chez Hektor part bien **sous le nom du négociateur en charge du bien** *(bascule `mode=autologin`, arrêt avant écriture si l'identité ne se vérifie pas)* · 🔴 **point 2i NEUF** : mon « la lecture est déjà cloisonnée » était **FAUX** — 24 vues sans `security_invoker`, et le filtre « ses biens » est posé par **le navigateur**, pas par la base ; 4 tables sans aucune limite *(archives, vendus, mandats, **affaires et commissions**)*. **Pas public** *(`anon` = non partout)* · ⭐ **R2** : le rôle « agent commercial » se fait par une **case « périmètre » sur le compte**, pas par une 5ᵉ valeur de `app_role` *(irréversible en PostgreSQL)* · **L4 (cloisonner) d'abord**, puis L2, L5, L6, L7, L1 ; **L3 supprimé** · pilote : **2 comptes existants, 2 agences** · ➡ **suivant : L4, audit des 24 vues** |
| ③ | Hektor d'abord → chez nous d'abord (statuts, clôture, fichiers) | ⬜ |
| ④ | **aucun échec silencieux** — 9 points 4a → 4i *(`notice/CHANTIER_4_ECHECS_SILENCIEUX_2026-10-09.md`)* | ✅ **FINI le 11/10** — **6 corrigés** (4a la suite d'une création, 4b cinq messages qui mentaient, 4c le marqueur d'erreur, 4d la recherche effacée, 4e les photos + le multiple, 4i le no-op du run) · **1 clos sans correctif** après mesure (4f) · **2 notés** car jamais survenus ou auto-réparants (4g, 4h) · ⭐ **les leçons** : *chercher l'œil qui existe avant d'en poser un neuf* (3 fois sur 9) · *trancher sur l'état du travail, jamais sur l'horloge* · *ne jamais faire d'un maximum une généralité* · *chercher un mot n'est pas mesurer un comportement* · ⏳ **les restes sont listés dans la note**, chacun avec sa raison |
| ⑤ | les gestes cassés (5a → 5i) *(`notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md`)* | ✅ **FINI le 09/10** — 9 points, **7 prouvés en réel**, et le run du 09/10 a validé les 3 derniers |
| ⑥ | ce qui ne redescend pas de Hektor (G.1-b, G.2 → G.6, photos, agenda) *(liste : `D.0`, l. 970 · photos, section **10bis**, l. 1170)* | ⬜ |
| ⑦ | les gestes qui manquent | ⬜ |
| ⑧ | gardé chez nous en entier | ⬜ |

**Ordre décidé par Frédéric : ① ⑤ puis ④ → ② → ③ → ⑥ → ⑦ ⑧.** Un périmètre, une taille,
un ordre ou un report ne se décident jamais sans lui.

### Ce que la journée du 09/10 a laissé — *trois notes, à lire au chantier ④*

```
notice/STATUT_DES_ARCHIVES_2026-10-09.md
   785 archives sans statut etaient INVISIBLES (« <> Estimation » rejette le vide) -> filet
   code, PAS deploye. 5 196 fiches detail rattrapees, 0 archive sans statut. L'outil est
   branche dans le run (~2 appels/nuit). Le defaut de l'interrupteur brouillon est INVERSE.

notice/ALERTES_MUETTES_2026-10-09.md
   AUCUNE alerte n'etait partie depuis au moins un mois (19 tentatives, 0 succes). La
   surveillance passe desormais par la cle de service Workspace, comme le backend.
   ⚠ RESTE : un seul canal -- WHATSAPP_ALERT_WEBHOOK n'a jamais ete pose.

le contact fantome (audit du 09/10, pas de note dediee)
   Un geste a echoue 5 fois cet apres-midi : le contact 145561 n'existe PLUS chez Hektor,
   alors que nous le croyons present. Le contact est le SEUL objet sans filet d'absence,
   et c'est structurel : son balayage est un delta, jamais complet (23 760 pages sinon).
   3 pistes mesurees : A ne pas envoyer de geste quand RIEN n'a change (le plus rentable,
   7 champs identiques ce jour-la) · C ne pas rejouer 5 fois l'irreparable · D1 marquer le
   contact absent quand un 404 l'apprend. Frederic : « je prefere voir plus tard ».
```

### ✅ LE RUN DU 10/10 — tout ce qu'on a posé le 09/10 tient

```
05:00:02 -> 07:18:40, 55 etapes (50 la veille), 2 sautees (4 la veille)
l'etape neuve « fiches detail des archives » : 2 secondes, bien placee
les 3 etapes bloquees la veille ont TOUTES tourne (lot des documents a 1 000)
retraits_leves enfin imprime · plus aucune alarme « L'ALLOCATEUR EST FAUX »
sentinelle relation_disparue VERTE · archives 35 318, 0 sans statut
parc vivant 13 475, 0 brouillon dedans · registre des mandats 0 manquant
```

❌ **Mon correctif des alertes ne marchait pas** : la tâche ne voit pas le site-packages de
l'utilisateur, donc ni `requests` ni `google.auth`. Corrigé le 10/10 — le lanceur préfère
le **venv du projet**, et un email d'essai est **parti depuis l'environnement exact de la
tâche**. ⏰ La vraie preuve sera la prochaine bascule vers critical.
⚠ **Un refus de garde-fou** (`contacts connus de l'app seule`, code 4). ❌ **J'avais écrit
« décalage d'horaire » : c'EST FAUX.** Le vrai motif est dans le journal — *« 85 074 lignes
sur 85 256 inconnues de la couche locale […] les deux côtés ne parlent probablement pas la
même série de numéros (bascule en cours ?) »*. **Il y avait bel et bien une bascule** : celle
des étiquettes de liens (voir le bloc suivant). ⭐ **Ce garde-fou a bien fait son travail** —
il a refusé de recenser un parc entier comme « né dans l'app ». Mesuré depuis : la doublure
et la couche s'accordent à nouveau (0 étiquette inconnue), **ça passera cette nuit**.
✅ Et les **3 mandats du serveur absents de Supabase** sont résorbés : 26 851 = 26 851, 0 absent.

### 🔴 LE CARNET DES LIENS — la nuit du 09→10, et le tri du 10/10 au soir

**Mon rattrapage de 5 196 fiches d'archives a fait changer de rôle 6 259 liens.** Le rôle entre
dans la recette du badge → 6 308 badges menacés → **le garde-fou de C.9-f s'est déclenché, et
son repli était CASSÉ** : `substituer=False` met `_CLES_FIGEES = {}`, et le test de la l. 1166
était `is not None` — **qu'un dict vide passe**. Le repli a donc écrit NOTRE numéro au lieu de
celui de Hektor : **167 483 badges refaits en une nuit**, la bascule même qu'il devait empêcher
*(la mesure du 25/09 en redoutait 167 487)*. ✅ **Aucune donnée perdue** — 34 liens d'écart sur
167 703, et le compte des relations identique avant/après le push.

**Conséquence qui restait** : deux badges par ancre → `charger_cles_figees` ne reprend RIEN pour
une ancre ambiguë → **le filet ne protégeait plus que 3,9 % du parc**.

✅ **TRIÉ LE 10/10 à 19:05, accord de Frédéric** — le patron du projet *(sauvegarder dans une
table datée, puis nettoyer)*, appliqué cinq fois avant :

```
app_relation_registry_avant_tri_20261010   335 249 lignes  = LE CARNET ENTIER, intact
supprimees du carnet de travail            161 204 badges REMPLACES
                                           (proprietaire 126 084 · acquereurs 34 905 · mandant 215)
gardees                                      6 376 barrees sans equivalent vivant
                                           (6 284 roles bascules + 92 vraies disparitions)
AVANT  ambigues 161 204  ->  proteges   6 456 (  3,9 %)
APRES  ambigues       0  ->  proteges 167 660 (100,0 %)
charger_cles_figees() : 174 036 ancres, 0 ambigue, 174 036 FIGENT un numero
```

**AUCUN changement de code.** Script + retour arrière : `phase2/identite/trier_carnet_des_liens_2026-10-10.py`.

⚠ **LA CAUSE RACINE RESTE OUVERTE** : `app_relation_registry` a pour clé primaire **le badge
lui-même** → un nouveau badge est forcément une nouvelle ligne, **ce carnet est construit pour
doubler**. Le carnet des recherches, lui, a pour clé `app_search_id` (un numéro **frappé**) et
garde sa clé calculée dans une COLONNE : il ne peut pas doubler. ➡ C'est le **point ⑥.1** du
chantier « le registre des relations devient autonome » — *« un numéro de lien FRAPPÉ, jamais
calculé »*.

⭐ **Et le numéro frappé EXISTE DÉJÀ** : `app_relation.app_relation_id`, 132 727 lignes, deux
distributeurs, deux plages — comme `app_dossier.id`, `app_contact_id`, `app_affaire_id`,
`app_mandat_id`, `app_search_id`. **Il n'est simplement pas utilisé là où ça compte** : ce sont
`app_contact_relation_current` *(ce que l'app lit et ce qui monte au cloud)* et
`app_relation_registry` qui ont pour clé `relation_key`. **La réparation serait d'inverser les
deux** : identifier le lien par son numéro, et laisser le badge calculé comme simple colonne.

⬜ **NOTÉ ET REPORTÉ** — *Frédéric, 10/10 : « note-le mais on le corrigera plus tard si
nécessaire »*. **Ne pas le relancer de soi-même.** Le filet trié tient en attendant ; ce qu'il
faut surveiller, c'est qu'une ancre ambiguë ne réapparaisse *(journal du run : « 0 ambigues »)*.

⬜ **Et le repli lui-même n'est pas corrigé.** Frédéric a choisi l'**option 3** : un garde-fou qui
se déclenche doit **s'arrêter et crier**, pas réécrire le parc avec une autre règle. ⚠ Mais
« crier » n'a **aucune destination** aujourd'hui : cette nuit, **2 étapes ont échoué et le run a
conclu « Pipeline finished successfully », exit 0** — la sonde n'a donc rien vu. **➡ À porter au
chantier ④ « aucun échec silencieux ».**

### ✅ 11/10 — LA SURVEILLANCE ÉTAIT MUETTE PARCE QU'ELLE N'AVAIT RIEN À DIRE

**Frédéric : *« j'ai pas eu de mail pour me dire que tout est revenu à la normale »*.** Il avait
raison : la sonde voyait **3 critical** et n'envoyait rien. ⭐ **Et ce n'était pas une panne** —
la règle (`check_gti_health.py:2843`) n'envoie que sur **bascule** vers critical, et un
« retour à la normale » exige **ZÉRO** critical. Les 3 l'étant depuis des jours, elle était
**coincée : rien à annoncer, et pas le droit d'annoncer le retour.**

**Les 3 critical, 2 causes, toutes deux déjà connues :**

```
data.travaux_en_erreur      24 travaux  -> 12 TypeError DEJA CORRIGES le 06/10 (3607d29)
                                         + 6 du contact fantome (reporte le 09/10)
                                         + 3 « database is locked » (note le 06/10)
                                         + 1 timeout 90 s · 1 document · 1 unlink non prouve
data.contact_conflit         1 ligne  ┐  LA MEME : 10076643 MARTIN Mickael,
data.contact_push_bloque     1 ligne  ┘  cible Hektor 145561 qui N'EXISTE PLUS
```

**Deux patchs, appliqués par Frédéric depuis son téléphone le 11/10** *(mes écritures Supabase
restent refusées par le garde-fou de session — « Production Deploy »)* :

```
07:42:38  patch_purge_erreurs_infra_2026-10-11.sql       24 -> 0, 14 lignes archivees
          (motif ENTIER archive, pas 150 car. ; 179 lignes de journal parties en CASCADE)
~07:5x    patch_saisie_en_attente_contact_fantome_2026-10-11.sql    1 -> 0
RESULTAT  les 3 alarmes a ZERO · saisie intacte : « M. Mickael MARTIN »
```

⭐ **Un garde-fou NEUF dans chaque patch** : le premier refuse si une saisie en attente
**repartirait** *(la barrière du 5b relance tant que `conflict = false`)* ; le second refuse si
la saisie **n'est pas déjà appliquée chez nous** — c'est ce qui protège C.1'.

✅⭐ **LA PREUVE EST TOMBÉE, ET FRÉDÉRIC A REÇU LE MAIL** — sonde de **09:48:55 → 09:52:18, code 0** :

```
71 controles : 65 ok · 6 warning · 0 CRITICAL
une seule ligne [alert] : « whatsapp ignore: WHATSAPP_ALERT_WEBHOOK absent »
   -> AUCUNE ligne « email echoue »   (le 10/10 : « Connection unexpectedly closed »)
interpreteur : C:\Hektor\Projet\.venv\Scripts\python.exe
```

➡ La chaîne entière est prouvée **par une vraie bascule**, et plus par un essai manuel :
le lanceur prend le venv → `requests` et `google.auth` sont là → la clé de service
Workspace signe → le mail part → **il arrive**. **Après au moins un mois de silence.**

⚠ **ET LE SEUL CANAL RESTE LE SEUL CANAL** : `WHATSAPP_ALERT_WEBHOOK` est toujours absent —
c'est littéralement la ligne que la sonde imprime à chaque envoi, et c'est la cause du mois
de silence. **On a réparé le canal, pas le fait qu'il soit unique.**

⚠ **Et la cause de fond reste** : `database is locked` avait **déjà** été purgé le 01/10
*(2 cas)* et est revenu *(3 cas)* — le `busy_timeout` manquant est noté depuis le 06/10. Et le
contact fantôme peut revenir : les pistes A / C / D1 du 09/10 sont au « je préfère voir plus
tard » de Frédéric.

### ⛔ Ce qui attend Frédéric

```
① DECIDER les droits du negociateur (chantier ②)
② QUESTIONS DE FAIT   les negociateurs saisissent-ils encore leurs visites dans Hektor ?
                      pourquoi 62 000 contacts seulement au cloud sur 356 000 ?
③ HORS CODE (etape 3) : A.4 zone DNS (La Boite Immo -> OVH, garder www) · A.5 les leads ·
   l'export PROTEXA · contrats A.1 et A.2
④ C.9-couple          creer un menage d'essai (la sonde est prete)
⑤ POUSSER             git push origin main -- ⚠ pousser = DEPLOYER (Render et Vercel).
                      Le filet « statut vide » attend ce push ; le reste est deja actif.
```

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *à finir tant que Hektor vit*

```
G.1-b    les 515 brouillons -- AVANT que le rattrapage les atteigne : la NUIT DU 15 AU 16/10
         (lot ramene a 1 000 le 09/10 ; c'etait le 11/10 a 2 500)
G.2      rebalayer le PARC VIVANT, fige depuis le 20/08 (apres le rattrapage ; perimetre =
         toutes les vivantes, estimations comprises -- decision de Frederic)
C.9-couple · C.13-c · E.1 (recherches, visites, documents, signatures) · A.3 · A.4
```

### Ce qui reste vrai de l'exploitation

- **Le rattrapage des documents** tourne à 21 h, **lots de 1 000** *(ramené de 2 500 le 09/10 :
  les vendus/clos portent 8,6 documents par annonce au lieu de 2,45)*. Reste ~6 900 annonces,
  fin vers le **16-17/10**. ⚠ **À remettre à 2 500** quand les vendus/clos seront finis.
- **Le run de nuit** : 55 étapes, ~2 h 35 (05:00 → 07:35). Reprise :
  `.\scheduled\run_quotidien.ps1 -StartAtLabel "<étiquette exacte>"`.
- ⏰ **LA MATINÉE A CHANGÉ LE 12/10** : `03:00` recherches actives · `05:00` le run *(fin 07:18-07:34)* ·
  **`07:45` la descente** *(était 08:15 ; fin attendue 08:18-08:49 ; elle attend le run jusqu'à 45 min)* ·
  `08:00` les relances e-mail · **`09:00` la sauvegarde** *(était 08:00)*. **Pourquoi** : la descente
  **saturait la passerelle de Supabase** et **l'app en souffrait** *(146 appels du front refusés sur
  une fenêtre de 12 min le 12/10)*. ⚠ **C'est un pansement, pas la cause.** Et la mesure a trouvé
  mieux : **152 tables descendues, 0 dans la sauvegarde quotidienne** — option C en attente de Frédéric.
- **Render et Vercel se déploient seuls** sur un push vers `main` : `/health` rend le commit.
- **Une autre session** travaille parfois en parallèle : relire `git log` avant d'écrire.

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
