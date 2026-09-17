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
⚬ **LA PAGE DE TÊTE DE LA LISTE REMPLACE SA LECTURE** : `notice/LISTE_TACHES_A_COCHER_2026-08-29.md`,
les **57 premières lignes**. Elle porte la tâche en cours, les trois suivantes, ce qui attend
Frédéric, et les renvois par numéro de ligne. Le reste du document est une **archive** : on
l’ouvre à la ligne indiquée, jamais en entier (6 500 lignes).

Cinq phases, à partir de la **ligne 1372**.

```
PHASE 0  mesurer, bloquante        l. 1912   0.1 quasi finie  ·  0.2 0.3 0.4 faites
PHASE 1  le registre, invisible    l. 2328   terminee
PHASE 2  l'ecran                   l. 2903   reste 2.4 (l. 3333), 2.6, 2.7 COTE ECRAN (l. 3556), 26bis-TRANSACTIONS (l. 2906)
PHASE 3  l'ecriture part chez Hektor  l. 3635   EN COURS
PHASE 4  menage                    l. 5290   reste 4.1 (l. 5293), 4.2 (l. 5297)  ·  4.3 faite le 07/09
```

**Au 08/09/2026 — LES TROIS GENRES SONT MODIFIABLES, ET PROUVÉS EN RÉEL.**

```
compromis  50078   165 000 → 175 000, quatre fois · aucun doublon · fiche vérifiée
vente      23301   créée, modifiée 175 000 → 176 500, supprimée · annonce rendue intacte
offre      33050   165 000 → 167 000  ·  33048 REFUSÉE re-acceptée puis re-refusée
```

**Au 10/09/2026 — CE QUE L'API CACHE, LE WORKER LE LIT MAINTENANT.**

Le registre a gagné quatre colonnes tirées de `payload_json` (`mandants_json`,
`notaires_json`, `propositions_json`, `commission_agence`) et le worker ne jette
plus le formulaire de Hektor : à chaque écriture il en tire ce que l'API ne rend
jamais, **sans une requête de plus**, dans `app_affaire_console`.

```
notairesAcquereur[] · notairesMandant[]     0 sur 10 586 par l'API
unitesEntreePercent / unitesSortiePercent   le partage de la commission
conditions suspensives : retenues + CATALOGUE de l'agence
montantHonoraireEntree / tauxHonoraireEntree   le TAUX VENDEUR (manque n°1 de 0.1)
```

Prouvé trois fois en réel sur le compromis 50078, et rejouable hors ligne :
`node Console/test_lecture_console.js` — onze assertions sur du HTML capturé.

⭐ **`2.6` A CHANGÉ DE NATURE.** La piste « la typologie du contact filtre » venait
de quatre mesures ; **le parc la dément à 39 %** — sur 12 446 acquéreurs réels de
compromis, 4 886 ne portent PAS la typologie et sont pourtant attachés. Et la
comparaison console/API sur 649 compromis donne **zéro écart** : l'API ne cache
rien, le défaut est bien à l'ÉCRITURE. L'instrumentation que le dossier réclamait
depuis le 06/09 est posée (ce qui part vraiment, ce que le formulaire garde, ce
que `findProspect` rend). ⚠ Reste l'essai avec deux contacts, jamais fait.

⚠ **LES TROIS ESSAIS « DEUX ACQUÉREURS » (02, 06 et 07/09) UTILISAIENT LE MÊME
  COUPLE**, dont un contact que Hektor n'a jamais attaché. Ils ne prouvent donc
  pas que Hektor n'en garde qu'un.

### Les outils du 10/09

```
Console/lecture_assistant.js                  le lecteur, PARTAGE (extrait du worker)
Console/test_lecture_console.js               11 assertions, N'APPELLE PAS HEKTOR
Console/extract_hektor_compromis_console.js   le rattrapage, LECTURE SEULE
phase2/sync/sync_hektor_compromis_console.py  son pilote, cadence de reference
```

⚠ **LA CADENCE N'EST PAS NEGOCIABLE** : 1 requête par compromis, 0,5 s entre deux,
lots de 100 avec 60 s, vagues de 2 000 avec 300 s. C'est la méthode de
`notice/NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09.md`, la seule qui n'ait jamais
rien déclenché (56 926 lectures). La coquille est écartée pour lire — mesuré le
10/09 : le formulaire arrive identique sans elle, ce qui divise le flux par deux.

**LA TÂCHE OUVERTE est `3.5` — L'ESSAI RÉEL DE LA SUPPRESSION** (liste, l. 5163).

Les cinq pièces sont codées depuis le 07/09 et le journal a été ajouté le 16/09 —
mais il n'avait **jamais été lu** (`request` au lieu de `_request`, corrigé le 17/09
par `bcb05fe`). Sans ce correctif, une suppression ordonnée par l'app **revenait au
run suivant**. Il ne reste que la preuve de bout en bout. ⚠ **Elle écrit chez Hektor
et demande un go explicite.**

**Les deux suivantes** : les **mandants depuis l'app** (lot 3, l. 4018), puis
**2.7 côté écran** (l. 3556) et **2.6** (l. 3412).

⛔ **CE QUE FRÉDÉRIC A MIS DE CÔTÉ**, et qu'on cesse de remonter à chaque tour : les
**2 dettes** (la surveillance qui crie depuis juillet · le numéro de contact qui ne
voyage pas avec sa fiche).

### `3.2e` — la répartition de commission *(détail : liste, section 3.2e)*

⛔ **RIEN NE PART CHEZ HEKTOR** (Frédéric, 14/09, 06bd38b) : leur modèle ne sait pas
exprimer un quart des répartitions réelles — l'acquéreur est suivi par une AUTRE agence
dans 26,6 % des cas. *« Mieux vaut un champ absent qu'un champ menteur. »*
La table existe et elle est remplie ; le reste est **garé**. ✅ Le point 1 — lever
`VenteDateStart` à 2000 — est fait (993dcc5). ⛔ L'étape de conversion reste
**désactivée dans le run** (8456e9f).

**Au 17/09 — LA JOURNÉE QUI A TOUT ÉPROUVÉ D'UN COUP.** `2.7` (couverture mandat
48 % → 74,9 %), `3.3` (le contrat d'autorité vidé), `3.1` (le verdict du carnet), le
chaînage (12 670 chaînes, les 4 copies de la règle d'accord, test ⑤ à 0 écart) et la
note libre d'une transaction. ⚠ **Et un bannissement d'IP à 06:34** : le balayage du
miroir fabriquait un client neuf par pièce, donc 17 logins OAuth en 22 s. Corrigé
(`c524f7e`), **pas encore éprouvé en réel** — le run de 5 h est son juge.

> ⭐ **`0.1` est quasi finie.** Sa phrase *« l'assistant refuse d'avancer sous
> automatisation »* était **fausse** : il refuse un formulaire qu'on ne lui rend pas
> fidèlement. **23 champs de données classés sur 24** ; le dernier,
> `agenceReseauSelected` (la rétrocession), est **hors périmètre par décision de Frédéric**,
> pas par oubli. Reste le relevé de l'offre.
>
> ⚠ **« C » NE VEUT PAS DIRE « il refuse l'écriture ».** Hektor *calcule* le net vendeur et
> la commission si on n'envoie rien — mais **il garde ce qu'on lui envoie, sans vérifier**.
> Il a accepté une fiche à *« 177 345 € »* pour un prix public de 175 000 sans broncher.
> **Rien ne rattrape une incohérence : l'alerte de la modale est le seul filet.**
>
> ⚠ Le risque des **conditions suspensives est LEVÉ** (mesuré le 08/09) : une modification
> les préserve. Le principe *« on repose ce que Hektor a rendu »* les protège sans code.

### Les outils du 08/09 — tous rejouables

```
Console/releve_assistant_etapes.js      l'inventaire des étapes    N'ÉCRIT JAMAIS
Console/mesure_reprise_compromis.js     le formulaire pré-rempli ? N'ÉCRIT JAMAIS
Console/mesure_reprise_panier.js        le panier retient-il l'id ? N'ÉCRIT JAMAIS
Console/campagne_champs_compromis.js    ⚠ LE SEUL QUI ÉCRIT CHEZ HEKTOR
phase2/checks/verifier_regle_chainage.py       les 3 copies de la règle, confrontées
phase2/checks/test_chainage_vente_ferme.py     le correctif du run, sur registre jetable
```

> ⚠ **Il existe deux tâches nommées `0.1`** — celle de la phase 0 (l. 1919) et une autre,
> sans rapport, l. 340.

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
| le **quoi**, item par item | `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (6 500 l. — lire la page de tête, l. 1-44) |
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
