# Audit — le rattrapage des documents : où il s'est arrêté, ce qu'il reste, ce qu'il coûte

*25/09/2026 — demandé par Frédéric, qui a relevé que ma mesure précédente ne portait
que sur le périmètre des annonces vivantes.*

> **Ma mesure du 25/09 au matin était fausse par omission.** J'avais écrit
> « l'empreinte est posée à 97,3 %, le rattrapage n'est pas à refaire ». C'était vrai
> **pour `daily-cloud` seul** — 13 437 annonces sur **58 140**. Sur tout le parc,
> l'empreinte est à **29,5 %**. Frédéric : *« je crois que tu es juste sur le périmètre
> des annonces de l'app et pas les archives etc. »* Il avait raison.
> **Même classe d'erreur que la mesure L5 du 25/09 : une liste partielle prise pour la
> liste entière.** La parade est écrite en §0 de CLAUDE.md : dresser le tableau complet,
> même vide, avant de conclure.

---

## 1. L'état réel du parc

| périmètre | annonces | empreinte OK | lue, sans empreinte | **jamais lue** |
|---|---:|---:|---:|---:|
| archive | 35 299 | 4 055 | 4 531 | **26 713** |
| courant | 13 437 | 13 068 | 17 | **352** |
| historique | 8 920 | 26 | 0 | **8 894** |
| brouillon | 484 | 0 | 0 | **484** |
| **total** | **58 140** | **17 149** | **4 548** | **36 443** |

**36 443 annonces n'ont jamais été regardées** pour leurs documents — **63 % du parc**.

⚠ « sans empreinte » ≠ « jamais lue ». L'écriture de l'empreinte n'existe que depuis le
**19/08 11 h 31** ; les 4 548 lues avant cette date ont bien leurs documents mais aucune
empreinte. Elles seront relues (1 lecture de page chacune), et **rien ne sera
re-téléchargé** : `upsertConsoleDocuments` conserve `storage_path`, `file_size`, `sha256`
de la ligne existante.

## 2. Où il s'est arrêté, et pourquoi

Le journal de `app_console_job` (`job_type = sync_console_documents`) :

| scope | jobs | du | au |
|---|---:|---|---|
| `rattrapage` | 13 968 | 19/08 | 20/08 |
| `daily-cloud` | 13 488 | 19/05 | 18/08 |
| `all-local` | 13 158 | 17/08 | 17/08 |
| `archive` | **10 786** | 18/08 | **23/08** |
| divers essais | 146 | 18/08 | 19/08 |

**Tous en `done`. Zéro en `error`.** Le rattrapage de l'archive s'est arrêté à
**10 786 sur 35 299**, soit moins d'un tiers — il n'a pas échoué, il a été **stoppé**.
Le 20/08 à 10 h 08, `7143a1a` posait le frein de débit : *« notre IP a été bannie »*.

## 3. Ce que ça coûte — débit mesuré, pas estimé

Débit observé sur les heures réellement actives du 17 au 23/08 :

| | heures actives | jobs | **par heure** | meilleure heure |
|---|---:|---:|---:|---:|
| avant le frein | 50 | 43 845 | 877 | 2 040 |
| **APRÈS le frein** | 13 | 7 723 | **594** | 1 042 |

**Le frein coûte un tiers du débit. C'est le prix de ne pas être banni.**

```
36 443 annonces ÷ 594 par heure  ≈  61 heures de traitement effectif
```

Soit **~10 nuits de 6 h**, ou un week-end en continu. La cadence est dans le worker :
1 s entre deux requêtes · +60 s toutes les 100 · +300 s toutes les 2 000.

## 4. L'outil existe déjà — et ce n'est pas celui que j'avais dit

> **Correction du 25/09.** J'avais recommandé `enqueue_console_sync_jobs.js --detect
> --cap 3000`. C'est le mauvais outil. **Le bon est `Console/enqueue_empreinte_lot.js`**,
> écrit le 21/08 exactement pour ça — Frédéric s'en souvenait (« des lots de 3000 »),
> pas moi. Son journal le confirme : `lot: empreinte`, scope `archive`, **3 141 jobs**
> du 21 au 23/08.

```
node Console/enqueue_empreinte_lot.js --scope archive --dry-run
node Console/enqueue_empreinte_lot.js --scope archive --limit 3000
```

Scopes : `archive` · `historical` · `brouillon`. Lot de 3 000 par défaut, priorité 200.

**Ses trois exclusions, dans l'ordre — c'est ce qui le rend sûr :**

1. **empreinte déjà posée** → déjà rattrapée ;
2. **job en erreur sur cette annonce** → **NE JAMAIS REJOUER** *(les 403 répétés ont fait
   bannir l'IP le 20/08)* ;
3. **job `pending`/`running`** → déjà dans la file.

Et il pagine systématiquement : sans ça PostgREST plafonne à 1 000 lignes et on croirait
à tort que les annonces non rendues sont « à faire » — on les rejouerait indéfiniment.

✅ **La reprise se fait par identifiant**, jamais par position. Conforme à la règle posée
après l'incident de reprise par `--start-at`.

⚠ **Ne pas utiliser `enqueue_console_sync_jobs.js` sans `--detect` pour un rattrapage** :
il ne saute que les jobs `pending`/`running`, jamais les `done`. Relancé, il ré-empilerait
les 3 000 premières par ordre d'identifiant — celles déjà faites.

L'enfilage ne touche pas Hektor : il ne lit que Supabase. Toute la charge est dans le
worker, qui porte le frein (1 s · +60 s/100 · +300 s/2 000).

## 5. Les réserves, à traiter AVANT de relancer

1. ✅ **CORRIGÉ LE 25/09 — `app_console_document_fingerprint` n'avait aucun numéro de l'app.**
   *(patch `supabase/patch_empreinte_numero_app_2026-09-25.sql` + worker + `REPOINT_TABLES`,
   garde-fou `Console/test_empreinte_numero_app.js`. La clé de conflit reste
   `hektor_annonce_id` : les workers en ont besoin pour désigner la fiche chez Hektor.)*
   L'énoncé d'origine : Sa clé primaire
   *est* `hektor_annonce_id`, et elle **n'est pas dans `REPOINT_TABLES`**. Même défaut que
   les 13 tables satellites réparées pour les contacts le 25/09. Aujourd'hui 0 orpheline,
   mais **4 081 empreintes sont déjà hors de l'index courant**. Si une annonce change de
   numéro Hektor, son empreinte reste sur l'ancien → elle est vue « jamais lue » et
   re-synchronisée. À la coupure, la table devient illisible.
   **C'est le carnet du rattrapage : le perdre, c'est recommencer 61 heures.**
2. ⚠ **La clé d'unicité d'un document est `(hektor_annonce_id, source,
   hektor_document_id)`** — pas la nôtre. Un changement de numéro Hektor recrée les
   documents en double au lieu de les reconnaître.
3. ⛔ **La détection n'a ni cadence ni arrêt sur 403** (`fetch` nu, pas `hektorFetch` ;
   `lectures_ko` puis `continue`, l. 316). Sans effet tant que le retard dure — le mode
   détection ne lit alors rien — mais **le jour où le retard est résorbé, le balayage
   quotidien lit 13 068 pages à pleine vitesse.**
4. ⚠ **L'étape du pipeline est bloquante** (`throw`) alors que ses voisines fragiles sont
   en `Invoke-OptionalStepWithRetry` : une session Hektor morte tuerait Matterport, les
   liens publics de RDV, la vitrine et l'export Android.

## 6. Ce qui est sain — vérifié

| étape | n° app | n° Hektor | |
|---|---|---|---|
| enfilage | posé depuis les 4 index | posé | ✅ |
| `app_console_job` | rempli | rempli | ✅ repointé |
| résolution du bien | cherché **d'abord** | filet | ✅ |
| action chez Hektor | — | `hektor_annonce_id` | ✅ correct |
| `app_console_document` | **44 516 / 44 516** | rempli | ✅ repointé |
| `app_console_photo` | **1 397 / 1 397** | rempli | ✅ repointé |
| lecture par l'app | `eq('app_dossier_id', …)` | **pas utilisé** | ✅ |
| **l'empreinte** | **aucune colonne** | clé primaire | ⛔ (§5.1) |

Et un soupçon levé par la mesure : les bornes des 4 séries se chevauchent
(courant 118→10 000 000, archive 15 633→7 344 118, historique 284→5 941 337,
brouillon 1 386 845→7 589 138), mais **0 collision sur 58 140 numéros**. C'est **une
seule série** répartie sur quatre tables : `app_dossier_id` n'est jamais ambigu.

Petit défaut relevé au passage : **53 documents sur 4 annonces** (49540, 33151, 61654,
35884) portent un `app_dossier_id` absent des quatre index.

## 7. L'ordre proposé

| | | |
|---|---|---|
| **1** | donner son numéro d'app à l'empreinte + l'ajouter au repointage | *le carnet du rattrapage* |
| **2** | cadence + arrêt net au 403 dans la détection | *avant qu'elle ne serve* |
| **3** | un test hors ligne qui prouve 1 et 2 | |
| **4** | **relancer le rattrapage** : `enqueue_empreinte_lot.js`, lots de 3 000, archive → historique → brouillon | **~61 h** |
| **5** | `--detect` + plafond dans le pipeline, étape non bloquante avec sonde | |
| **6** | **Frédéric** : allumer `-EnqueueConsoleDocuments` | *le run quotidien ne fait plus que les MAJ* |

Le point **4** est le gros morceau et il est indépendant des autres : il peut tourner
pendant qu'on code le reste, **à condition que 1 soit fait avant** — sinon une
ré-indexation d'annonce pendant le rattrapage effacerait une partie du travail.
