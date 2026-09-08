# Porte d'entrée du projet

> Ce fichier ne contient **aucune connaissance**. Il contient des **adresses**.
> Le savoir est dans le plan, la liste, les notes et le code. En cas de désaccord,
> **c'est le code qui gagne, puis le plan, puis cette page.**
> Il se lit en trois minutes. Il ne remplace rien.

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

## 2. Où on en est — *à mettre à jour en fin de session*

**Chantier : `C.19-d` — LE REGISTRE DES TRANSACTIONS.**
Cinq phases, dans `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` à partir de la **ligne 1321**.

```
PHASE 0  mesurer, bloquante        l. 1861   0.1 EN COURS  ·  0.2 0.3 0.4 faites
PHASE 1  le registre, invisible    l. 2099   terminee
PHASE 2  l'ecran                   l. 2674   reste 2.4 (l. 3104), 2.7 (l. 3274),
                                             26bis-TRANSACTIONS (l. 2677)
PHASE 3  l'ecriture part chez Hektor  l. 3353   EN COURS
PHASE 4  menage                    l. 4089   reste 4.1 (l. 4092), 4.2  ·  4.3 faite le 07/09
```

**Au 08/09/2026 : `3.2` est faite POUR LE COMPROMIS, et prouvée sur l'écran.**
Quatre modifications réelles sur le compromis 50078 (165 000 → 175 000), un seul compromis,
rien de perdu. Le détail des **sept obstacles levés** est en tête de `3.2`, ligne 3362.

**La tâche ouverte est `3.2d` — ligne 3604.** Son **lot 1 est fait** (la commission de
l'agence est visible, et la modale vérifie `prix = net + honoraires`). Restent les lots 2, 3
et 4 — le lot 4 vient du relevé du 08/09 : le **partage de la commission** et la
**rétrocession**, absents de toute l'app.

Ensuite : `3.2b` (l. 3509 — la vente, puis l'offre), `3.3`, `3.1`.

> ⭐ **`0.1` n'est plus bloquée.** Sa phrase *« l'assistant refuse d'avancer sous
> automatisation »* était fausse : il refuse un formulaire qu'on ne lui rend pas fidèlement.
> Les trois étapes manquantes sont relevées (l. 1868) avec
> `node Console/releve_assistant_etapes.js` — **qui n'enregistre jamais**.
> Reste le même relevé pour la **vente**.
>
> ⚠ **Un risque ouvert et NON MESURÉ** (l. 1868) : l'enregistrement repose les conditions
> suspensives **sans leur `id_condition`**. Sur un compromis qui en porte, une modification
> pourrait les abîmer — c'est juridique. À éprouver avant d'ouvrir « Modifier » à un vrai
> compromis.
>
> ⚠ **Il existe deux tâches nommées `0.1`** — celle de la phase 0 (l. 1868) et une autre,
> sans rapport, l. 289.

---

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
| le **quoi**, item par item | `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (4 695 l.) |
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

---

## 7. En fin de session — deux gestes, deux minutes

1. **Mettre à jour le §2** de cette page : la tâche ouverte et son numéro de ligne.
2. **Réécrire la mémoire de reprise** (`reprise-…` dans le dossier mémoire), toujours la même,
   jamais une nouvelle par date. *Elle datait du 02/09 alors que 68 commits avaient suivi.*
