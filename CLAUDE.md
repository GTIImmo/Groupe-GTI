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
> *(l'état du 07/10, audit complet et 46 chapitres, y est descendu le 08/10)*.

**Réécrit le 08/10/2026, après l'AUDIT PAR OBJET** —
`notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md` *(9 objets × 8 critères, vert / orange / rouge,
lecture seule, contre le code ET l'historique)*. L'audit du 07/10 mélangeait les étapes et se
trompait sur plusieurs objets : il porte désormais un avertissement en tête.

### Les deux étapes — *définies par Frédéric le 08/10*

```
ETAPE 2   l'app fait tout le travail quotidien ; Hektor vit, il FOURNIT LES NUMEROS
          (y compris le n° de mandat via PROTEXA), les workers lui ENVOIENT les mises a jour
ETAPE 3   notre registre electronique des mandats (nos numeros) -> la signature -> la pub ;
          « tant que les 3 ne sont pas chez nous, impossible de couper Hektor » ;
          plus site web, DNS, e-mail
```

### Le verdict de l'audit par objet

```
LE SOCLE TIENT : annonce, recherche, transaction naissent chez nous, s'affichent sans
Hektor, et ce qui redescend n'ecrase pas une saisie de l'app.
LES TROUS : les DROITS du negociateur · des gestes encore « Hektor d'abord » · des ECHECS
SILENCIEUX · des BUGS precis (desarchiver impossible depuis le 30/08...) · et 6 fonctions
ouvertes a un visiteur non connecte.
```

### Le chantier : 8 chantiers, un par un *(plan, section « 🧭 LES CHANTIERS DE L'ÉTAPE 2 »)*

**La méthode, à chaque chantier** *(Frédéric, 08/10)* : **audit du sujet** (revérifier) →
**explication des correctifs proposés** → « vas-y » → code → **contrôle du résultat** → plan,
liste et cette page à jour. Le **tableau de suivi** est dans le plan : on le met à jour à
chaque étape.

| # | chantier | état |
|---|---|---|
| ① | sécurité : 136 fonctions et 15 vues ouvertes à la clé publique *(`notice/CHANTIER_1_SECURITE_2026-10-08.md`)* | 🧪 patch APPLIQUÉ le 08/10 08:22, contrôlé (0 ouverture publique, app connectée OK) ; `hektor-diffusion` v15 déployée ; reste : la nuit du 09/10 |
| ② | les droits du négociateur — **attend la décision de Frédéric** *(`notice/CHANTIER_2_DROITS_NEGOCIATEUR_2026-10-09.md`)* | 🔎 **09/10 audit fait, CONFIRMÉ** : il n'y a que **5 portes**, et la 1re (`app_console_can_request_job`) commande **16 RPC + la règle RLS d'écriture** des travaux · la **lecture est déjà cloisonnée**, le trou est à l'écriture · **43** négociateurs portent le parc, **4** ont un compte · **0 travail demandé par un commercial, jamais** · le circuit de demande dort (9 demandes, toutes d'un admin) · 💬 **attend 3 réponses** : que fait un négociateur seul · le rôle manager · pilote ou 39 comptes |
| ③ | Hektor d'abord → chez nous d'abord (statuts, clôture, fichiers) | ⬜ |
| ④ | aucun échec silencieux — **9 points, 4a → 4i** *(`notice/CHANTIER_4_ECHECS_SILENCIEUX_2026-10-09.md`)* | 🔧 **09/10 : 4a audité (CONFIRMÉ comme structure, éteint comme panne)** — 79 créations **toutes « done »**, 4 échecs cachés, et **toute la fiche (167 champs) perdue** à chaque fois ; **aucun dégât réel** (annonces d'essai ; le mandant du 28/08 était un **faux négatif**) ; ⭐ **les 4 causes sont déjà bouchées** (09/06, 10/07, 31/08) → **le trou est LE SILENCE** · **« option A » de Frédéric** : on n'ajoute **que la parole**, sans faire tomber le travail (l'annonce existe chez Hektor) — ① avertissement au négociateur (`creation_suite_incomplete`, interrupteur `CONSOLE_ALERTE_SUITE_CREATION`, +123 lignes, 0 suppression, **épreuve 19/19**) ② branche `UNION ALL` dans `app_en_attente_humain` → la sentinelle `geste_abandonne` voit seule (**4 lignes au total, 0 sur 30 jours → verte**) · ✅ **répétition exacte (13 mesures) puis patch APPLIQUÉ le 09/10**, contrôlé : empreinte `e2c015e1…` conforme, 7 colonnes, **0 ligne**, droits inchangés (chantier ① intact) · ✅ **4a FINI le 09/10** : 4 workers redémarrés à 17:30:49 (battement `startup` en base), moniteur vert, aucun déploiement · ➡ **le point suivant est 4b** |
| ⑤ | les gestes cassés (5a → 5i) *(`notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md`)* | ✅ **FINI le 08/10, les 9 points** · 6 prouvés en réel (désarchiver, modifier un mandant, le filet du rattachement, rattacher après un retrait, supprimer un contact, ouvrir une archive sans Hektor) · sentinelle 5h verte · **5i prouvé en réel le 08/10 au soir**, après redémarrage des 4 workers (bien 62963 : « c'est NOTRE geste d'état, la saisie part » — Hektor écrit, 0 conflit) · **reste** : le run du 09/10 (5c, 5e-B) |
| ⑥ | ce qui ne redescend pas de Hektor (G.1-b, G.2 → G.6, photos, agenda) *(liste : `D.0`, l. 970 · photos, section **10bis**, l. 1170)* | ⬜ |
| ⑦ | les gestes qui manquent | ⬜ |
| ⑧ | gardé chez nous en entier | ⬜ |

**Ordre DÉCIDÉ par Frédéric le 08/10 : ① puis ⑤ → ④ → ② → ③ → ⑥ → ⑦ → ⑧** (tous seront faits). ① et ⑤ sont **faits** → **le prochain chantier est ④ (aucun échec silencieux)**. Le prompt de reprise est prêt : `notice/PROMPT_CHANTIER_ETAPE2.md` (une seule ligne à changer).
Un périmètre, une taille, un ordre ou un report ne se décident jamais sans lui.

### ✅ LE RUN DU 09/10 EST PASSÉ — *détail : `notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md`*

```
Run 05:00:02 -> 07:34:16 « finished successfully », 50 etapes, 4 sautees, 0 plantage.
5c   OK  l'etape neuve « doublure du registre des mandats » : 19 s, 26 847 lignes,
         juste AVANT celle du registre, qui finit sans erreur
5e-B OK  app_relation_id 1000008 : retire_le NULL, present_in_hektor vrai,
         revu par le run a 05:05 -- le retrait n'a PAS ete repose
5a   OK  le bien 78 (VA2380) est dans l'index des VENDUS/CLOS, pas au parc vivant :
         son statut est « Clos », et le parc vivant ne prend que Actif / Sous offre /
         Sous compromis / Estimation. MON CONTROLE ETAIT FAUX, pas le code.
5h   OK  sentinelle contacts_sans_hektor verte, comme annonce_conflit / partielle /
         push_bloque (0) et mandat_disparu (0 manquant)
```

**Les suites** — ✅ **① et ② faits le 09/10** *(commit `allocateur`)* : le compte
`retraits_leves` s'affiche enfin, et le contrôle de l'allocateur ne compte plus que les
numéros que le run a **inventés** dans la plage de l'app — corrigé aux **quatre** endroits
(les deux registres et leurs deux sentinelles), 12 épreuves vertes hors ligne.
✅ **③ fait le 09/10** : le rattrapage des documents a fini les **35 317 archives** et est
entré dans les **vendus/clos**, qui portent **8,60 documents par annonce au lieu de 2,45**
(21,9 s par annonce au lieu de 10,2) — le lot de 2 500 demandait ~16 h et a bloqué **TROIS**
étapes du run (chauffage delta, entretien compromis, entretien ventes). **Rien n'est perdu** :
les trois se rattrapent seules (chauffage à 30 jours, entretien « ce qui manque »). **Le lot
passe à 1 000** *(décision de Frédéric)* : ~6 h, file vide avant le run — **à remettre à
2 500 quand les vendus/clos seront finis**.
⏳ **Reste** : ④ « GTI Descente » finit avec le **code 1** — le **08/10 ET le 09/10**.

### ⏸ EN PAUSE — LE STATUT DES ARCHIVES *(note complète : `notice/STATUT_DES_ARCHIVES_2026-10-09.md`)*

Signalé le 09/10 : « plus que 201 annonces dans l'index archivé ». **La base n'a rien perdu**
(35 317) — c'était le filtre STATUT resté sur « Actif / offre / compromis ». Mais la vérification
a trouvé **deux vrais défauts, mesurés, non corrigés** :

```
785 archives SANS STATUT -> invisibles quoi qu'on fasse : l'ecran exclut toujours
    « Estimation », et en SQL « different de » rejette aussi les cases VIDES.
5 246 fiches detail d'archive a rattraper (3 241 absentes + ~2 005 perimees) :
    le statut ne vit QUE dans la fiche detail, et les variantes « archived » du
    balayage ne la telechargent JAMAIS (sync_details: False, decision du 24/08).
    -> une archive modifiee chez Hektor n'est jamais actualisee chez nous.
L'OUTIL EXISTE DEJA et fait les deux : sync_archived_annonce_details.py,
    branche NULLE PART. Cout du maintien : ~2 appels par nuit (mesure).
Le trou est LIMITE AUX ARCHIVES : parc vivant 0, vendus/clos 0 (ils portent
    archive=0, donc les variantes « active » lisent bien leur detail).
```

✅ **09/10 : l'outil est BRANCHÉ DANS LE RUN** (option A) — étape optionnelle entre
`sync_raw` et `normalize_source`, limite 50 (convention du projet), ~2 appels/nuit ; une
archive modifiée chez Hektor redeviendra à jour dès la nuit suivante. ⏰ à contrôler au
run du 10/10.
✅ **09/10 : LE RATTRAPAGE EST FINI** — 5 196 fiches lues à 2 293 lectures/h (12:40 → 15:05).
**Archives sans fiche détail : 3 241 → 0.** `app_view_generale`, archives sans statut :
**3 241 → 0**. Les 37 773 archives portent un statut (Clos 34 780, Mandat clos 2 456,
Vendu 425, Actif 83, Estimation 29).
⏳ **Reste le PUSH vers Supabase** pour que l'index de l'app le reçoive — le run de nuit
le fait seul. ✅ Le filet côté écran est **codé** (`933286a`) mais **pas déployé** ; il n'est
plus ce qui débloque, puisque les statuts ne seront plus vides.

### ⛔ Ce qui attend Frédéric

```
① DECIDER les droits du negociateur -- AUDIT FAIT le 09/10, 3 questions precises :
   que fait un negociateur seul sur SES biens (tout sauf supprimer / le quotidien plus
   une demande pour les gestes graves / rien de plus qu'aujourd'hui) · garde-t-on le
   role « manager » (0 compte) · un pilote de 2-3 negociateurs ou les 39 comptes ?
② QUESTIONS DE FAIT   les negociateurs saisissent-ils encore leurs visites dans Hektor ?
                      pourquoi 62 000 contacts seulement au cloud sur 356 000 ?
③ HORS CODE (etape 3, mais a ne pas oublier) : A.4 zone DNS (La Boite Immo -> OVH, garder
   www) · A.5 les leads · l'export PROTEXA · contrats A.1 et A.2
④ C.9-couple          creer un menage d'essai (la sonde est prete)
⑤ POUSSER             git push origin main -- ⚠ pousser = DEPLOYER (Render et Vercel)
```

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *à finir tant que Hektor vit*

```
G.1-b    les 515 brouillons (mesure du 09/10) -- AVANT que le rattrapage les atteigne :
         la NUIT DU 15 AU 16/10 avec le lot ramene a 1 000 (c'etait le 11/10 a 2 500)
G.2      rebalayer le PARC VIVANT, fige depuis le 20/08 (apres le rattrapage ; perimetre =
         toutes les vivantes, estimations comprises -- decision de Frederic)
C.9-couple · C.13-c · E.1 (recherches, visites, documents, signatures) · A.3 · A.4
```

### Ce qui reste vrai de l'exploitation

- **Le rattrapage des documents** tourne à 21 h, lots de 2 500 (décision de Frédéric) : nuit du
  07/10, 1 250 archives, 0 erreur ; ensuite les ventes, puis les historiques, puis les brouillons.
- **Le run de nuit** : 54 étapes. Reprise : `.\scheduled\run_quotidien.ps1 -StartAtLabel
  "<étiquette exacte>"`, puis lire le journal (`REPRISE a partir de`, `SAUTEE (reprise)`).
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
