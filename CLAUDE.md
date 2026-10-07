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
| documents de travail | `notice/` — 160 notes *(compté le 07/10)* |

---

## 2. Où on en est — *une page, pas une archive*

> ⚠ **Cette section porte LE PRÉSENT, et rien d'autre.** Règle : en fin de session, on la
> **RÉÉCRIT**, on ne l'empile pas ; ce qui en sort descend dans **`notice/JOURNAL_DE_BORD.md`**
> *(l'état du 03/10 au 06/10 y est descendu le 07/10 : run réparé, retirer un mandant, L9…)*.

**Réécrit le 07/10/2026, après l'audit complet** —
`notice/AUDIT_AUTONOMIE_COMPLET_2026-10-07.md` *(10 dimensions, chaque constat grave remesuré
par un contradicteur, puis un contrôle de complétude ; lecture seule)*.

### Le verdict, en quatre lignes

```
L0 ✅  L1 🟡  L2 🟡  L3 ✅  L4 🟡  L5 ⛔  L6 ⛔  L7 🟡  L8 ⛔  L9 🟡  L10 ⬜
L'ETAPE 2 N'EST PAS TERMINEE. La memoire est a nous, et MODIFIER marche sans Hektor.
CREER, mettre sous mandat, ajouter un fichier, valider pour la diffusion : encore Hektor.
Personne ne saisit dans l'app : 0 travail demande par un commercial en 120 jours.
```

### Le chantier : l'audit est DANS le plan, pas à côté *(décision du 07/10)*

| où | quoi |
|---|---|
| plan, section « 🔎 L'AUDIT COMPLET DU 07/10 » | où va chaque point · **les 8 questions à Frédéric** · **🧭 LES 46 CHAPITRES**, la liste que le dev suit *(proposée le 07/10, à valider)* |
| `notice/CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md` | le détail de chaque chapitre (ordre interne, prérequis, feu vert, critère de fin) |
| plan, lots | **L1 et L2 rouverts** · lot **`L10` « Préparer la coupure »** créé |
| liste, section 13 | les 16 tâches de `L10` |
| liste, section 12 | hors code : A.1 → A.5 *(A.4 DNS et site, A.5 leads : neufs)* |
| liste, cases existantes | G.1→G.6, 26bis-3, C.9-couple, C.13-c, E.0-bis, E.1, E.2, F.1, 11bis ①, A.3 : annotées « ↳ 07/10 » |

### Les fronts

| front | où c'en est | ce qui reste |
|---|---|---|
| **① IDENTITÉ / NAISSANCE** *(L4 · L10-1 · L10-2)* | le stock est 100 % sous nos numéros ; contact et annonce savent naître (e3 allumé) | n° Hektor de l'annonce `NOT NULL` dans 16 tables ; recherche seulement provisoire ; C.9-couple : sonde prête, geste humain |
| **② LES DOCUMENTS** *(`D.0`, l. 963 · G.1→G.6)* | rattrapage à 21 h, lots de 2 500, 0 erreur | ≈ 10 650 annonces (≥ 6 nuits) ; **G.1-b les brouillons échoueront** ; parc vivant figé depuis le 20/08 (G.2 puis G.6) ; G.5 devenu bloquant |
| **③ LES PHOTOS** *(section **10bis**, l. 1163)* | affichage 100 % chez nous (74 992 photos du parc vivant) | ajouter / retirer / réordonner chez nous (G.5, E.0-bis) ; 350 retraits faits dans Hektor non remontés |
| **④ LE REGISTRE DES MANDATS** *(L9, liste section 9)* | phase 1 faite ; mandants et prix chez nous depuis le 06/10 | série légale, inaltérabilité, export, avenants et mandats de recherche, export PROTEXA, 2 défauts dormants de l'étape D |
| **⑤ LA COUPURE** *(L10, liste section 13)* | ouvert le 07/10 | 16 tâches ; ordre proposé dans le plan, **pas décidé** |

### ⛔ Ce qui attend Frédéric

```
⓪ AVANT LE 08/10 A 21:00     fixer la taille du lot des VENTES (proposition 400) et
                             dire « vas-y » pour G.1-e (ch.1) -- sinon un lot de 2 500
                             ventes (20 a 36 h) fait refuser le run du matin
① HORS CODE, sans attendre   A.4 la zone DNS de gti-immobilier.fr est servie par
                             La Boite Immo (MX Google de toute l'agence) : export
                             de la zone, puis OVH -- GARDER l'adresse de www
                             (l'admin Hektor et le worker passent par elle)
                             A.5 ou arrivent les leads depuis le 01/02 ?
                             l'export PROTEXA · les contrats A.1 et A.2 · le juriste
② LES 8 QUESTIONS            plan, section « 🔎 L'AUDIT COMPLET DU 07/10 »
③ C.9-couple                 creer un menage d'essai sur une cible choisie (sonde prete)
④ POUSSER                    git push origin main -- ⚠ pousser = DEPLOYER (Render et
                             Vercel se deploient seuls, ~1 min)
⑤ G.6                        NE PAS allumer -EnqueueConsoleDocuments tel quel : G.2 d'abord
```

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *à finir tant que Hektor vit*

```
G.1-b    les 508 brouillons du rattrapage -- AVANT qu'il les atteigne
G.2      rebalayer le PARC VIVANT, fige depuis le 20/08
L10-8    les planchers « Hektor repond vide » (l'index des archives peut tomber sur
         un simple hoquet : ils protegent DES MAINTENANT)
C.9-couple · C.13-c · N.4 (26bis-3) · E.1 (recherches, visites, documents, signatures)
A.3      l'export PROTEXA     ·     A.4 la zone DNS, AVANT tout preavis
```

### Ce qui reste vrai de l'exploitation

- **Le run de nuit** a été réparé le 03/10 (l'étape des liens : 79 min → 46 s). Le
  `busy_timeout` de la descente (`a86a800`) et la garde d'ordonnancement (`5cfd576`) sont
  **faits et poussés**. Nuit du 07/10 : 54 étapes sur 54, 05:00 → 07:20.
- **Reprise** : `.\scheduled\run_quotidien.ps1 -StartAtLabel "<étiquette exacte>"`. Lire le
  journal dans les 30 s : chercher `REPRISE a partir de`, compter les `SAUTEE (reprise)`.
- **Render et Vercel se déploient seuls** sur un push vers `main` : `/health` rend le commit
  qui tourne.
- **Une autre session** travaille parfois en parallèle sur le même dépôt (07/10 : la sonde
  C.9-couple). Relire `git log` avant d'écrire dans les documents.

## 3. Avant de coder — la liste de relecture *(plan, l. 886 « ⛔ AVANT DE COMMENCER UN CHANTIER »)*

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
  question posée — pas montrer que « ça marche ». *(plan, l. 535 « ⚖ LA RÈGLE DU FAIT »)*
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
| le **pourquoi** | `notice/PLAN_DEV_ACTUALISE_2026-08-20.md` (2 941 l. au 07/10) |
| le **quoi**, item par item | `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (9 440 l. au 07/10 — lire la page de tête, l. 1-75) |
| le **dernier audit** | `notice/AUDIT_AUTONOMIE_COMPLET_2026-10-07.md` — la carte de ce qui reste avant la coupure |
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
