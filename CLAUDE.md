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
| documents de travail | `notice/` — 123 notes |

---

## 2. Où on en est — *une page, pas une archive*

> ⚠ **Cette section porte LE PRÉSENT, et rien d'autre.** Elle avait grossi à **467 lignes
> sur 609**, avec quatre états datés dont trois marqués *« ne jamais relire comme un ordre
> du jour »*. L'historique est parti dans **`notice/JOURNAL_DE_BORD.md`** le 26/09 : on
> l'ouvre pour comprendre **un pourquoi**, jamais pour savoir quoi faire.
>
> **Règle : en fin de session, on RÉÉCRIT cette section. On ne l'empile pas.**

**Mis à jour le 26/09/2026 (après-midi).**

### L'étape, en une ligne

```
ETAPE 2 = l'app fait TOUT, sauf trois choses qui restent a Hektor :
          le numero de mandat (L9) · la signature (A.2) · les portails (A.1)

L0 ✅   L1 ✅   L2 ✅   L3 ✅   L4 🟡   puis  L5  L6  L7  L8  L9
```

### Les trois fronts ouverts — *ils avancent séparément*

| front | où c'en est | ce qui reste |
|---|---|---|
| **① L'IDENTITÉ** *(`L4` / `C.9`)* | la bascule contact est faite *(23/09)*, une annonce **naît dans l'app** depuis le 25/09 *(`e3` allumé)*, `C.9-f` en service la nuit du 26/09 | contrôler la ligne `[numero de bien dans la cle]` du run · surveiller la **1re annonce réelle** d'un négociateur · supprimer les annonces d'essai **63146** et **63147** |
| **② LES DOCUMENTS** *(`D.0`, l. 935 · `G.1`→`G.6`)* | 4 défauts fermés *(mandat/annexe, empreinte, frein, ajout autonome dormant)*. Le **rattrapage tourne seul** : tâche « GTI Rattrapage Documents » à 23 h, lots de 3 000 | **40 987 annonces**, ~14 nuits. Puis `G.2` `--detect` plafonné · `G.3` le ménage des 3 Go · `G.4` l'état doit suivre · `G.5` la RPC d'ajout |
| **③ LES PHOTOS** *(section **10bis**, l. 1135)* | **4 cases cochées le 26/09**, tout **dormant** : le coffre, le calibrage, l'adresse qui ne disparaît plus, le générateur | `G.13` générer les dérivés *(~18 Go, ~3 h)* · `G.14` le logo · `G.15` rebrancher les **48 points** avec repli · `G.16` les restes |

**Le détail des trois fronts est dans la liste, par numéro de ligne. Pas ici.**

### Ce que les photos ont appris le 26/09 — *les deux pièges qui ne crient pas*

> ⚠⚠ **La durée de cache doit valoir EXACTEMENT `max-age=N`.** Supabase parse cette forme
> et refabrique l'en-tête ; une forme plus riche *(`public, max-age=N, immutable`)* est
> ignorée **en silence** et le fichier ressort en `no-cache` — chaque affichage par un
> portail ou un email repasserait en **egress facturé**. Aucune erreur, rien dans les logs.
>
> ⚠⚠ **`upsertConsolePhotos` effaçait.** `if (rows.length)` gardait l'ajout mais **pas** la
> suppression : une liste vide rendue par Hektor emportait **toutes les photos de
> l'annonce**. Or l'`id` de cette ligne porte le chemin du fichier sur le serveur **et**
> l'adresse publique de ses dérivés. Corrigé en **delete-never**. *(Le plan parlait d'un
> `app_photo_id` : cette colonne n'existe pas.)*
>
> ➡ mémoire `photos-coffre-public-et-derives` · `photos-ligne-ne-disparait-jamais`

### ⛔ Ce qui attend Frédéric — *rien de tout ça ne se fait sans lui*

```
① REDEMARRER LES 4 SERVICES              <- rend G.10bis actif. Tant qu'il n'est pas
   HektorConsoleWorker Actions/Admin/        fait, le worker CONTINUE DE SUPPRIMER.
   Documents/SyncLight                       ⚠ EN JOURNEE 06 h - 22 h, JAMAIS 23 h - 05 h
                                             (un job laisse « running » 30 min passe en
                                             erreur, et les erreurs sont ECARTEES A VIE
                                             du rattrapage)
② POUSSER                                <- deploie le filtre du front (commite, pas pousse)
③ npm install sharp dans Console/        <- avant d'allumer G.11
④ allumer -EnqueueConsoleDocuments       <- ⛔ SEULEMENT APRES LE RATTRAPAGE (sinon on
   dans run_quotidien.ps1                   double la consommation du quota Hektor)
⑤ relancer le rattrapage si la tache     <- enqueue_empreinte_lot.js, lots de 3 000
   de 23 h decroche                          ⚠ NE JAMAIS REJOUER une annonce en erreur
```

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *pas seulement une priorité*

```
L9            le registre des mandats se remplit DEPUIS LE MIROIR -- impossible apres
C.9-couple    seul moment ou l'on peut comparer NOTRE paire a celle de Hektor (c'est
              HEKTOR qui cree la 2e fiche du couple ; apres, personne ne le fera)
vitrine +     les liens PUBLICS deja diffuses (QR, imprimes) portent le n° Hektor ->
liens RDV     servir l'ancienne ET la nouvelle forme EN PARALLELE. Recouvrement, pas
              remplacement. (section 11bis)
G.15          les 48 points d'affichage lisent les photos CHEZ HEKTOR. Le jour de la
              coupure elles disparaissent TOUTES de l'ecran en meme temps -- meme avec
              les 169 Go rapatries sur le serveur. Rapatrier remplit le coffre ; ca n'a
              jamais suffi a AFFICHER.
```

**Les quatre doivent être finis AVANT la coupure, pas pendant.**

## 3. Avant de coder — la liste de relecture *(plan, l. 378)*

Elle existe *« parce que le 20/08 j'ai oublié trois fois un point déjà documenté »*.

1. La **section du plan** qui concerne la tâche — et ses voisines, les pièges y sont.
2. Les **notes citées** par cette section : elles portent les décisions déjà prises.
3. `notice/*.md` **et la racine**, par mot-clé — 123 notes, dont 111 ne sont citées nulle part.
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
  question posée — pas montrer que « ça marche ». *(plan, l. 27)*
- **Ne rien écraser.** Additif et chirurgical, jamais de remplacement massif.
- **Pas de code sans « go » explicite.** Un message court, en cadrage, est une **question**.
- **Stager fichier par fichier.** Jamais `git add .` : 73 fichiers non suivis traînent
  dans le dépôt.
- **Les 5 règles du projet** et **la règle des identifiants** : plan, lignes 2236 à 2270.
  *(un numéro ne se perd jamais · Hektor confirme, il n'écrase pas · une action a une fin
  visible · Hektor reste à jour tant qu'il diffuse · le miroir se met à jour, il ne se
  remplace pas)*

---

## 5. Les adresses

| | |
|---|---|
| le **pourquoi** | `notice/PLAN_DEV_ACTUALISE_2026-08-20.md` (2 278 l.) |
| le **quoi**, item par item | `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (6 500 l. — lire la page de tête, l. 1-44) |
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
