# Plan de développement actualisé — 20/08/2026

Remplace le plan du 18/08. Établi après quatre audits mesurés :
identifiants (19/08), workers (20/08), diffusion (20/08), contacts et modales (20/08).

---

## CE QUI EST FAIT

| | | Commit |
|---|---|---|
| Un dossier ne perd jamais son numéro | on marque `absent_depuis`, on ne supprime plus | `dc45c62` |
| Le correctif anti-fantôme couvre 21 tables au lieu de 5 | ~600 annonces abîmées depuis juin | `aa8a374` |
| **Les identifiants d'annonce sont alignés** | 13 215 / 13 215, vérifié après un run complet | `99e262f` |
| Pipeline et surveillance fiabilisés | chauffage non bloquant, sauvegarde surveillée, 4 sentinelles en critique | 5 commits |

---

## ⛔ AVANT DE COMMENCER UN CHANTIER — à relire, sans exception

**Cette liste existe parce que le 20/08 j'ai oublié trois fois un point déjà documenté.**
Un plan ne protège de rien s'il n'est pas relu avant chaque geste.

| | À relire | Pourquoi |
|---|---|---|
| **1** | **Ce document en entier** — pas seulement la tâche visée | les pièges sont dans les sections voisines |
| **2** | Les **notes citées** par le chantier concerné | elles contiennent les décisions déjà prises |
| **3** | `ls notice/*.md` **et la racine**, par mot-clé | ~158 notes ; celles qui comptent ne sont pas toujours dans `notice/` |
| **4** | **L'historique git** : `git log --all --diff-filter=D -- 'notice/*'` | 12 notes supprimées le 19/08 portent encore de la doctrine active |
| **5** | La **mémoire projet** de l'assistant | la réponse y était déjà, deux fois, le 20/08 |

**Trois questions à se poser avant d'affirmer qu'une chose est cassée :**

1. **Est-ce documenté ?** Dans ce projet, ce qui ressemble à une négligence est presque toujours
   une décision écrite quelque part.
2. **Est-ce mesuré ?** Une détection `ILIKE` mal écrite m'a fait affirmer l'inverse de la vérité
   sur `app_edit_search_optimistic`. **Mesurer, puis conclure.**
3. **Qu'est-ce que j'oublie ?** Lister les cas voisins : si on traite « la recherche modifiée »,
   a-t-on traité « la recherche supprimée » ? Si on traite les annonces, et les contacts ?
   les affaires ? les recherches ?

---

## LES TÂCHES, DANS L'ORDRE

*Vue opérationnelle. Le détail, les mesures et les pièges sont dans les chantiers plus bas.*

| | Tâche | |
|---|---|---|
| ✅ | Avertissement d'échec des workers | `48e475a` |
| ✅ **1** | ~~**Rattacher l'irremplaçable**~~ **FAIT** — 15 lignes déplacées, 0 perdue — propositions, relances, retours acquéreur, envois — à la recherche vivante du contact | 15 lignes, **0 ambiguïté** |
| **1bis** | *(cas des recherches SUPPRIMÉES chez Hektor : 31 clés, 681 rapprochements — **rien d'irremplaçable dessous**, donc rien à rattacher)* | traité par la tâche 2 |
| ✅ **2** | ~~**Supprimer le recalculable**~~ **FAIT** — 13 339 lignes — 1 373 rapprochements + 11 966 lignes d'historique, **les deux cas confondus** | après le 1 |
| ✅ **2bis** | ~~**Poser le balayage nocturne**~~ **FAIT** — `app_sweep_search_orphans`, 07:00 — la même réparation, chaque nuit | sinon la fuite reprend dès le lendemain |
| ✅ **2ter** | ~~**Sentinelle**~~ **FAIT** — sur les orphelins NON rattachables *(contact à plusieurs recherches)* | attendu 0 |
| ✅ **3** | ~~Le numéro Hektor d'**annonce** a le droit d'être vide~~ **FAIT** — + sa sentinelle | |
| ✅ **4** | ~~**Identité des transactions**~~ **FAIT le 20/08** — 28 980 affaires numérotées par l'app, clé basculée, numéros Hektor facultatifs, sentinelle posée | 0 point d'appel ambigu, **confirmé par lecture** : le worker envoie `idOffre=""` — il ne sait que créer |
| ✅ **4bis** | ~~MESURER : supprimée ou archivée ?~~ **RÉPONDU le 21/08 — ARCHIVÉE, toujours.** **Hektor ne sait pas supprimer une recherche** : même le bouton « Supprimer » de l'app appelle `archiveHektorContactSearch` → `modifDateArchiveCritere`, qui pose une *date d'archivage* (`console_job_worker.js:11878-11890`, `:11918`) | ⇒ **le rang ne glisse jamais. `(contact + rang)` est STABLE.** Les « 184 contacts à risque » n'existent pas |
| ✅ **4bis-A** | ~~**Les recherches archivées ne sont plus supprimées de Supabase**~~ **FAIT le 21/08** — 6 777 récupérées | **C'ÉTAIT LA FUITE.** Hektor archive au lieu d'effacer ; Supabase supprimait ⇒ clé morte ⇒ orphelins. Règle *delete-never*, comme le registre d'affaires |
| ✅ **4bis-B** | ~~**Le verrou du moteur de rapprochement**~~ **FAIT le 21/08** — il ne score que les actives | **posé AVANT les données** : sans lui, 6 777 clients qui ne cherchent plus auraient reçu des propositions. Sentinelle seuil 0 |
| ✅ **2quater** | ~~**Le balayage tient un carnet**~~ **FAIT le 21/08** — `app_sweep_search_orphans_log` | une réparation qui ne dit pas ce qu'elle répare ne se surveille pas. **Vérifié après un run complet : 0 réparation** |
| ✅ **4ter** | ~~Un numéro propre pour la recherche, en doublure~~ **FAIT le 21/08** — `app_search_id` + registre local `app_search_registry` (table à part, car le run complet **vide** la couche des recherches) ; 76 839 numérotées, 10 744 poussées, 0 doublon | **précédé le même jour par** : les recherches archivées ne sont plus supprimées de Supabase *(la vraie source des orphelins)*, + verrou du moteur de rapprochement |
| ✅ **4quater** | **Observer** la doublure — **close le 21/08** — l'observation n'était plus nécessaire : le seul cas pouvant mettre le numéro en défaut a été provoqué et vérifié en direct : sentinelles `data.recherche_sans_numero` et `data.recherche_numero_double`, seuil 0, + le carnet du balayage `app_sweep_search_orphans_log` | **des semaines**, pas des jours. C'est leur **silence** qui autorise la bascule |
| ✅ **4quinquies** | ~~**FIGER le nom de la recherche**~~ **FAIT le 21/08** — 76 841 noms figés dans `app_search_registry`, 0 doublon, 0 ligne divergente | **L'empreinte n'est PAS touchée.** Prouvé : une sentinelle écrite dans le registre est reprise par la ligne après reconstruction, puis restaurée. ⇒ **les 185 contacts à plusieurs recherches actives cessent d'être un problème** — plus rien ne se détache, donc plus rien à rattacher. Le balayage reste en filet |
| **26bis-①** | **Créer + remplir les tables d'annonces sur le serveur** — 56 888 fiches, **≈ 1 Go** *(mesuré ; 739 Go libres)* | **additif, jetable, personne ne les lit.** Remonté ici le 21/08 : ce n'est PAS irréversible *(contrairement aux documents et photos)*, et l'observation doit commencer tôt |
| **26bis-②** | **Observer** — la base locale dit-elle la même chose que Supabase ? | **après la bascule du numéro de recherche**, pour ne pas avoir deux doublures à surveiller en même temps |
| **5** | **Identité des contacts** — 186 500 lignes, ≈ 530 points de code | **après 4quinquies — PRÉALABLE DUR** : renuméroter les contacts changerait les 3 961 noms d'un coup, et le balayage serait débordé, sinon les 3 961 étiquettes changent d'un coup. **Le renommage `target_contact_id` → `hektor_contact_id` se fait DANS cette tâche**, pas avant *(voir 5a rayée)* |
| ~~5a~~ | ~~Renommer seul les 11 paramètres ambigus~~ **RAYÉE le 20/08** | **pas sans risque** : Postgres refuse le rename (DROP+CREATE), l'appel se fait par NOM, et la compilation ne voit rien. Coût = déploiement coordonné sur 3 machines ; gain = lisibilité seule |
| **6** | Écrire la règle de comparaison — les 3 cas d'écart | |
| **7** | La tolérance de comparaison | |
| **8** | Brancher la comparaison **au retour du worker** | |
| **9** | Même règle sur l'import de nuit | |
| **26bis-③** | **Basculer** — l'envoi vers Supabase ET la consultation des archives lisent **la base locale**, plus le miroir | ⚠️ **collée au contrat, et pas par hasard** : c'est LÀ que l'arbitrage Hektor/app trouve un endroit où s'écrire. Le serveur vient lire dans Supabase ce que l'app a saisi *(comme `fetch_app_owned_contact_fields` le fait déjà pour 3 champs)*. ⇒ le miroir sort du chemin critique |
| **10** | **Le calque disparaît** | |
| **11** | La barrière — un travail sans numéro Hektor attend | |
| **12** | Les 3 recherches *(ajouter / modifier / supprimer)* | |
| **13** | **Statut + affaire** *(offre, compromis, vente)* | le geste le plus riche |
| **14** | Archiver / désarchiver / supprimer | |
| **15** | Créer un contact, créer un mandant, rattacher | |
| **16** | **Affectation du négociateur** | **en dernier** — impersonation |
| **17** | Clé propre du **registre des affaires** | |
| **18** | Fiabiliser le mandat des transactions | ne plus le deviner dans le HTML |
| **19** | Ménage des tables mortes | |
| ✅ **19-R1** | ~~**RATTRAPAGE DES ACQUÉREURS — passe de fond**~~ **lancé le 21/08** — `scheduled/run_rattrapage_acquereurs.ps1`, 71 337 fiches, ≈ 4 h 35 | ferme le trou des **nouvelles** recherches, accumulé depuis mai. Voir *Le trou des NOUVELLES recherches* |
| ⏳ **19-R2** | **RATTRAPAGE — LA VEILLE DE LA BASCULE** — **relancer la même commande** la veille du jour où les négociateurs passent sur l'app | ⚠️ **à ne pas oublier : c'est la DERNIÈRE occasion.** Après la bascule, plus personne ne crée de recherche dans Hektor — ce qui n'aura pas été rapatrié ce jour-là ne le sera jamais |
| **19bis** | **BASCULE DES NÉGOCIATEURS SUR L'APP** | **décision d'organisation** — c'est elle qui débloque tout le bloc recherches |
| **20** | **Corriger le modèle « au moins »** de la modale recherche | après la bascule |
| **21** | **Mesurer** les critères Hektor invisibles dans l'app | |
| **22** | **Fermer les 4 portes des recherches** | **DÉCLASSÉE le 21/08** : elle servait à empêcher qu'on recalcule le nom. Une fois le nom figé (4quinquies), plus personne ne le recalcule — les portes peuvent rester ouvertes. Reste utile pour l'autonomie, plus pour la stabilité |
| **23** | La création d'**annonce** écrit la vraie fiche | **après 26bis-③** — sinon une annonce créée dans l'app n'existerait que dans Supabase, et le serveur ne l'apprendrait que si Hektor la confirme. *Creuser le trou pendant qu'on le rebouche* |
| **24** | La création de **contact** et de **mandant** | |
| **25** | La modale d'ajout écrit ses **trois objets d'un coup** | |
| **26** | Les workers deviennent invisibles | une fois l'avertissement éprouvé |
| **27** | **Rapatrier les documents** — 40 493 | ⚠️ **irréversible** |
| **28** | **Rapatrier les photos** — 1 397 | ⚠️ **irréversible** |
| **29** | **Sortie des portails** + reprise des 350 annonces en ligne | délai non maîtrisé |
| **30** | **Yousign** | |
| **31** | **Registre de mandats en propre** | |
| **32** | Le distributeur démarre à 100 000 | jour J |
| **33** | Le serveur remplit **les deux cases** | jour J |
| **34** | Le numéro est **imposé**, pas laissé au compteur | jour J |
| **35** | On éteint l'aspirateur — pipeline, workers, Playwright, file | jour J |

---

## LE BLOB DE DETAIL — faux obstacle, leve le 21/08

Le contrat d'autorite du 17/08 reclamait *« un inventaire exhaustif des ~130 cles du blob avant
d'ecrire quoi que ce soit dessus »*. **Cet inventaire est sans objet** : la question n'etait pas
« que contient le blob » mais « qui l'ecrit ».

**Une seule fonction ecrit dans le blob** : `app_edit_annonce_optimistic`. Et elle n'y touche
que **7 cles** :

```
   surface . nb_pieces . nb_chambres . surface_terrain_detail
   latitude_detail . longitude_detail . garage_box_detail
```

Elle range en plus ce que le negociateur vient de saisir dans un **compartiment dedie**,
`app_optimistic_overlay`. **Le paquet a deja un tiroir reserve a l'app.**

Les 127 autres cles sont une photocopie de Hektor : l'app les lit, les affiche, s'en sert pour
le rapprochement -- elle n'en ecrit aucune.

> **Ce qui reste a faire est minuscule** : proteger ces 7 cles de la reecriture de nuit, avec le
> mecanisme qui existe deja (celui qui protege naissance / lieu / situation matrimoniale cote
> contact). Ce n'est pas un chantier a part : ca rentre dans « Hektor confirme, il n'ecrase plus ».

**Ce qui reste valide de la mise en garde du 17/08** : ne PAS declarer « tout le descriptif est a
l'app ». Le blob transporte de la diffusion, des affaires, des mandats et des photos bien
vivants -- une regle en bloc les aurait geles.

---

## LE TROU DE STOCKAGE DES ANNONCES — decouvert et tranche le 21/08

**Constat, mesure a l'appui.** Cote annonces, le serveur local **ne detient pas les donnees** :

```
   app_dossier  (local)  =  10 colonnes seulement
      id . hektor_annonce_id . hektor_mandat_id . numero_dossier
      numero_mandat . commercial_id . commercial_nom . dates . absent_depuis
```

Le contenu vit **uniquement dans le miroir de Hektor** (`data/hektor.sqlite`, 34 tables,
464 952 reponses API brutes). `view_generale.py` recompose a la volee **une ligne a plat
d'environ 200 champs**, qui part ensuite vers Supabase, coupee en deux :

| | |
|---|---|
| **59 champs** | colonnes de `app_dossier_current` -- chercher, filtrer, trier |
| **134 champs** | le paquet `app_dossier_detail_current` -- afficher |

Le partage est decide par deux listes explicites dans le code. **Rien n'est opaque** : les
134 cles sont nommees et calculees une par une. *(C'est pourquoi l'« inventaire des 130 cles »
reclame par le contrat d'autorite du 17/08 est sans objet -- voir plus bas.)*

> **Le probleme** : le jour ou Hektor s'eteint, le miroir cesse d'etre alimente. Or c'est lui
> qui fabrique la ligne a plat. **Le serveur local n'aurait plus de quoi la recalculer.**

*(Le contact et la recherche n'ont PAS ce trou : le local a ses propres tables --
355 641 contacts, 76 839 recherches.)*

### La decision (Frederic, 21/08) : option ②

**Le serveur local recoit ses propres tables d'annonces** et reste le maitre, comme pour les
contacts et les recherches. Supabase garde son role : le sous-ensemble utile, en ligne.

**Consequence de calendrier, non negociable** : le remplissage initial doit se faire **pendant
que Hektor vit encore**, puisque c'est le miroir qui alimente. Apres la coupure il serait trop
tard. -> tache **26bis**.

### Les trois gestes, et OU ils sont dans la liste

```
   26bis-(1)  CREER + REMPLIR   juste apres la bascule du numero de recherche
   26bis-(2)  OBSERVER          en parallele, personne ne lit
   ------------------------------------------------------------------
   26bis-(3)  BASCULER          juste apres la tache 9 -- COLLEE au contrat d'autorite
```

**Pourquoi ce n'est plus a la fin (corrige le 21/08).** Je l'avais rangee avec le rapatriement
des documents et des photos, dans la famille « sortir de chez Hektor avant la coupure ».
**Fausse ressemblance** :

- **Ce n'est PAS irreversible.** Documents et photos, oui. Une table locale, on la jette.
- **Elle demande une longue observation.** La poser tard, c'est repousser la coupure d'autant.
- **(3) va avec 6-9.** Les laisser a vingt taches d'ecart, c'est se condamner a faire l'un sans
  l'autre : le contrat aurait un arbitrage sans endroit ou l'ecrire.
- **Et surtout** : la creation app-first (23-25) ecrit dans Supabase. Sans 26bis, une annonce
  creee dans l'app n'existe QUE la, et le serveur ne l'apprend que si Hektor la confirme.
  **Ce serait creuser le trou pendant qu'on le rebouche.**

**Une seule reserve, assumee** : (2) attend la bascule du numero de recherche, pour ne pas avoir
deux doublures a surveiller en meme temps. C'est une affaire de jours. Six chiffres a lire chaque
matin au lieu de trois, ca cesse d'etre une surveillance et ca devient une corvee -- et une
sentinelle qu'on ne lit plus ne protege de rien.

### (3) EXIGE le contrat d'autorite -- trouve par Frederic le 21/08

L'app n'ecrit QUE dans Supabase (aucune porte d'entree vers le serveur, et il ne faut pas en
creer). Donc une table locale alimentee seulement par le miroir **apprendrait les modifications
uniquement par Hektor** -- et seulement si Hektor les a recues. **Une saisie en conflit, ou dont
l'envoi a echoue, n'arriverait JAMAIS dans la base locale.**

Le serveur doit donc **venir lire dans Supabase ce que l'app a ecrit**. Ce mecanisme existe deja,
pour trois champs de contact : `fetch_app_owned_contact_fields` relit dans Supabase ce que Hektor
ne connait pas, et le reinjecte. **Meme geste, a etendre.**

```
   la nuit :
        ce que dit HEKTOR (le miroir)  +  ce que dit L'APP (relu dans Supabase)
              -> arbitre selon le CONTRAT D'AUTORITE du 17/08
              -> ecrit dans LA BASE LOCALE
              -> envoye vers Supabase
```

> **La table locale devient l'endroit ou l'arbitrage a lieu.** Aujourd'hui il n'y a pas d'endroit :
> c'est pour cela que Hektor gagne par defaut -- il est seul dans la piece.

**Consequence sur l'ordre** : les taches **6-9** et **26bis** ne sont plus independantes.
`26bis sans le contrat` = une base qui oublie les saisies.
`le contrat sans 26bis` = un arbitrage sans endroit ou se faire.

### Ce que 26bis debloque en plus

Apres la coupure, une annonce **creee dans l'app** puis archivee n'aura jamais existe dans le
miroir : son detail ne serait nulle part. La consultation des archives doit donc changer de
source -- et 26bis est ce qui le permet.

---

## LE BLOC RECHERCHES — ce que les audits du 20/08 au soir ont changé

**Trois choses que je croyais et qui sont fausses**, vérifiées dans le code, pas déduites :

| Ce qui était écrit | Ce que la lecture montre |
|---|---|
| L'étiquette sert à détecter qu'une recherche a changé chez Hektor | **Non.** La détection vient de la **redemande de la fiche** (run 03:00, sans filtre de date) et de la comparaison de contenu `stable_payload_hash`. L'étiquette n'est que le **nom de rangement** de la ligne |
| Il faut reprendre ≈ 493 000 lignes | **Non.** **Un seul endroit fabrique l'étiquette** : `build_contacts_layer.py:827` |
| Le renommage seul est sans risque | **Non.** Postgres refuse le rename, l'appel se fait par NOM, la compilation ne voit rien |

**La preuve que le numéro suffit est dans le projet lui-même.** Dans le *même* script d'envoi,
deux tables voisines :

| Table | Rangée sous | Quand Hektor modifie |
|---|---|---|
| `app_contact_current` | `hektor_contact_id` — **un numéro** | ligne **mise à jour sur place** ✅ |
| `app_contact_search_current` | l'étiquette — **un haché de contenu** | ligne **supprimée puis recréée** ❌ |

Les modifications de contact faites dans Hektor remontent parfaitement. **Le mécanisme
fonctionne déjà avec un numéro stable — il n'est pas appliqué aux recherches, voilà tout.**

### Le fond, formule par Frederic le 20/08 au soir : **il y a DEJA deux haches**

Preuve dans `phase2.sqlite`, table `app_contact_supabase_push_state` :

```
   UNE RECHERCHE
   nom de la ligne : 001697ad4134b105219d5549       <- un hache (la cle)
   empreinte       : 742548023fb03575338def20...    <- un AUTRE hache

   UN CONTACT
   nom de la ligne : 100030                         <- un NUMERO
   empreinte       : 03dd0f0f5e96c4c031bec5b88...   <- un hache
```

**L'empreinte de contenu existe deja sur les 3 962 recherches.** Elle est calculee et
stockee a chaque run. **Et elle n'est jamais consultee** : le nom ayant change en meme temps
que le contenu, la ligne d'avant est introuvable et l'empreinte connue reste rangee sous un
nom mort.

> **Deux haches sur chaque recherche. Le premier fait mal le travail du second.
> Le second, qui le ferait bien, n'est jamais lu.**

**Ce que le chantier fait, exactement :**

```
   AVANT   nom : 001697ad4134b105219d5549     empreinte : 742548...
   APRES   nom : 412                          empreinte : 742548...
                  ^                                        ^
             on remplace CA                      on ne touche pas a CA
```

Le run de nuit retrouve alors la ligne d'avant, compare les deux empreintes, voit que le
contenu a bouge, **et met a jour au lieu de detruire**.

> **On ne construit rien. On enleve un doublon qui bloque un mecanisme deja present.**

Le detail de la boucle : `push_contacts_to_supabase.py:206-211`
`known_hashes.get(row_key(row)) != stable_payload_hash(row)` -- le nom sert a retrouver ce
qu'on savait, l'empreinte sert a comparer. Deux metiers, une seule ligne de code.

**La méthode retenue est celle de Frédéric (20/08) : la doublure.**

```
   poser le numero A COTE, sans rien lui confier
        -> l'etiquette continue de commander, rien ne casse
   observer pendant des semaines : tombe-t-il toujours juste ?
        -> une sentinelle repond, pas une supposition
   basculer seulement une fois qu'il a fait ses preuves
```

> C'est l'inverse de ce que j'avais proposé — basculer puis vérifier. **Et c'est ce qu'on
> aurait dû faire pour les annonces** : `app_dossier_id` a dérivé de mars à juin sans que
> personne le voie, précisément parce que personne ne l'observait.

**Tâche 4bis — RÉPONDUE le 21/08.** **Hektor ne sait pas supprimer une recherche.**
Le worker, même pour un « Supprimer » demandé depuis l'app, appelle
`archiveHektorContactSearch` → `mode=contacts-contactProfile-modifDateArchiveCritere` avec une
`dateArchive` : il **pose une date**, il n'efface rien (`console_job_worker.js:11878-11890`, `:11918`).

> **Donc le rang ne glisse jamais, et `(contact + rang)` est une poignée stable.**
> Confirmé par les données : 72 872 archivées en local occupant des rangs jusqu'à 15, et
> seulement **9** recherches actives précédées d'une archivée. Capturer l'`idCritere` n'est
> plus un préalable — ça reste un confort.

⚠️ **Mais l'archivage détache quand même**, pour une raison de **périmètre**, pas de rang :
le local garde les archivées, **Supabase ne garde que les actives**. Une recherche archivée
disparaît donc de Supabase, et ce qui pointait sur sa clé devient orphelin. C'est ce rythme
que mesure le carnet du balayage (`app_sweep_search_orphans_log`, posé le 21/08).

*(Correction : les « 31 recherches supprimées chez Hektor » notées le 20/08 étaient selon toute
vraisemblance des recherches **archivées**.)*

---

## LE CHANTIER D'IDENTITÉ — trois objets, un seul dessin

**Le dessin, valable pour les trois :**

```
   case 1 : un numero A TOI        <- la cle, remplie des la creation, jamais remplacee
   case 2 : le numero de Hektor    <- simple reference, vide en attendant son retour
```

**Arbitrage Frédéric (20/08) : pas de solution mixte.** Un objet ne peut pas avoir une case pour
les anciens et deux pour les nouveaux. **Tout le parc bascule d'un coup, ou rien.**

**Deuxième arbitrage : on double ET on bascule dans la foulée.** Jamais de numéro « secondaire »
généré mais inutilisé — c'est ce qui a laissé `app_dossier_id` dériver de mars à juin sans que
personne le voie. *Ce qui est utilisé est ce qui est vérifié.*

### L'ordre, établi par l'audit des points d'appel (20/08)

| Ordre | Objet | Volume | Points d'appel ambigus | Risque |
|---|---|---|---|---|
| **1** | **Transactions** | ≈ 29 100 | **0 sur 12** — jamais envoyés au worker | **le plus faible** |
| — | *Annonces* | *341 394* | *3 sur 56, dont 2 `null`* | *fait le 19/08* |
| **2** | **Contacts** | ≈ 186 500 | **3 réels**, ≈ 10 fonctions à relire | **le plus élevé** |
| **3** | **Recherches** *(3 961)* | ≈ 1 300 rapprochements à rebrancher | clé = **hachage du contenu**, elle bouge seule | **cas à part — voir le dossier ci-dessous** |

> **Pourquoi les contacts sont les plus risqués** : ils n'ont qu'une seule colonne, donc **aucune
> couche n'a jamais eu a faire la distinction**. Mesure du 20/08 :
>
> | | Front | Fonctions de la base | Worker |
> |---|---|---|---|
> | Annonces | 53 explicites / 56 | explicites | lit un champ nomme |
> | **Contacts** | **3 ambigus**, ~10 fonctions | **6 fonctions ambigues** | lit un champ nomme |
> | Transactions | 12 / 12 explicites | jamais envoyees | ne les connait pas |
>
> Les six fonctions concernees : `app_console_create_update_contact_job`,
> `..._delete_contact_job`, `..._contact_search_job`, `..._update_contact_search_job`,
> `..._delete_contact_search_job`, `..._update_mandant_contact_job` — toutes ecrivent
> `hektor_contact_id` a partir de `target_contact_id`.

### La méthode, par objet — jamais deux à la fois

```
   0. AUDIT COMPLET DES POINTS D'APPEL, sur les TROIS couches -- prealable absolu.
      Partout ou un identifiant part vers un worker, il doit etre lu dans la
      colonne NOMMEE, jamais dans "la cle".
        a) le front        : modales, api.ts, App.tsx
        b) les fonctions de la base : les 14 app_console_create_*_job
        c) le worker       : il lit deja un champ nomme -> a confirmer, pas a modifier
      Puis renommer ce qui est ambigu : input.contactId -> input.hektorContactId.
      Aucun effet fonctionnel aujourd'hui, verifie par la compilation.
   1. ajouter la case (Supabase + local, parent et tables enfants)
   2. renumeroter le stock  : table de correspondance conservee, essai a blanc
                              qui annule tout, transaction unique, verification chiffree
   3. basculer la cle DANS LA FOULEE : les jointures lisent la nouvelle case,
      ET LA CASE HEKTOR DEVIENT FACULTATIVE -> c'est CE geste qui autorise
      la creation depuis l'app. Il est impossible avant l'etape 3, puisque
      la case Hektor est encore la cle.
   4. poser la sentinelle   : doublons = 0, orphelins = 0, ecart local/Supabase = 0
   5. le worker NE CHANGE PAS : il lit toujours le champ nomme hektor_*_id
```

**Preuve avant la masse** : basculer un seul objet, le modifier depuis l'app, vérifier que le
worker aboutit et que Hektor a bien reçu. Dix annonces avaient servi de test le 19/08 avant les
12 162 — aucun orphelin créé.

**Garde-fou pendant la transition** : la RPC de création de travail **refuse** de créer un travail
Hektor si la case Hektor est vide — elle le met en attente. Un travail ne peut donc pas partir
avec un mauvais numéro : il ne part pas du tout.

---

## LE DOSSIER RECHERCHES — enquête du 20/08, à lire avant d'y toucher

**Trois facettes distinctes**, identifiées par `RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md` :

| | Facette | État |
|---|---|---|
| **A** | **Clé instable** — `contact_search_key` hache le **contenu éditable** | ❌ jamais corrigée |
| **B** | **Écrasement** — l'édition renvoie TOUTE la recherche depuis une copie peut-être périmée | ❌ jamais corrigée |
| **C** | **Angle mort `date_maj`** — éditer une recherche dans Hektor ne bump pas la date du contact | ✅ **corrigée le 20/06** |

**C a été corrigée par un run dédié** : `scheduled/run_recherches_actives.ps1` ->
`sync_active_searches.py`, **03:00 chaque nuit**, ~3 590 contacts, sans filtre `date_maj`.

> **Le noeud : la correction de C amplifie A.**
> Avant le 20/06, une édition faite dans Hektor était invisible -> la clé ne bougeait pas.
> Depuis, elle est détectée -> **la clé bouge** -> l'historique se détache.
> **Orphelins : 327 le 19/06 -> 1 332 le 20/08. Multiplié par quatre en deux mois.**

**Ce n'est PAS voulu — vérifié le 20/08 :**

- **6 clés du projet sur 7 hachent une identité** (relation, registre, contact, dossier, doublons).
  La recherche est **la seule** à hacher du contenu.
- **Deux consommateurs s'en protègent déjà en production** : `app_email_envoi.search_index`
  (migration du 17/06 : *« la contact_search_key change à l'édition »*) et
  `espace_client._load_search_for_envoi` (3 niveaux, *« on ne s'y fie qu'en tout dernier recours »*).
  **Le contrat de fait est déjà : ne pas se fier à cette clé.**
- **Personne ne dépend de son instabilité.** Le rapprochement est le seul à ne pas se protéger.

**Pourquoi ça n'a jamais été corrigé** : le correctif proposé en juin était `hash(contact_id, index)`.
Il est **mauvais** — l'`index` est la **position**, qui bouge à chaque suppression et n'est pas
alignée entre l'API et le grattage Console. **La bonne réponse est un identifiant propre à l'app.**

**Gravité** : le moteur de rapprochement est **app-only par décision métier**
(`NOTE_MOTEUR_RAPPROCHEMENT_ACQUEREUR_2026-06-14.md`). Ce qui se détache — propositions, retours
acquéreur, relances, emails — **n'existe nulle part ailleurs**. Hektor ne peut rien reconstruire.

**Vérifié en direct le 20/08**, contact 604020 : édition à 14:36 -> clé inchangée, 41
rapprochements recalculés ; retour de Hektor à 14:48:07 -> **nouvelle clé**, les 41 deviennent
orphelins. Et **aucune des 4 fonctions** qui suppriment des rapprochements ne nettoie par absence.

### Ce qui pend sous la clé — mesuré le 20/08, SEPT tables

| Table | Total | Orphelins | Recalculable ? |
|---|---|---|---|
| Historique de score | 450 046 | **11 966** | ✅ oui |
| Rapprochements | 47 547 | **1 373** | ✅ oui |
| **Notifications** | 843 | **13** | ❌ **non** |
| **Propositions** | 11 | **6 — 55 %** | ❌ **non** |
| **Relances** | 10 | **5 — 50 %** | ❌ **non** |
| **Envois d'email** | 82 | **2** | ❌ **non** |
| **Retours acquéreur** | 7 | **2 — 29 %** | ❌ **non** |

> ⛔ **NE PAS « nettoyer les orphelins » d'un bloc.** Plus de la moitié des propositions et des
> relances sont détachées : ce sont des traces d'actions réelles, **app-only**, que Hektor n'a
> jamais eues. Les supprimer les détruirait définitivement.

**Deux gestes distincts, dans cet ordre :**

1. **REBRANCHER l'irremplaçable** — propositions, relances, retours acquéreur, envois,
   notifications — par *(contact + search_index)*, **exactement comme le fait déjà
   `espace_client._load_search_for_envoi`**. ~28 lignes aujourd'hui, mais 50 % des propositions.
2. **NETTOYER le recalculable** — rapprochements et historique de score, 13 339 lignes, sans risque.
3. **CLÉ PROPRE**, pour que ça ne recommence pas.

**Rebrancher AVANT de nettoyer.** Dans l'autre sens, on détruit ce qu'on voulait sauver.

> **L'espace client ne changera pas de comportement** : il ne s'appuie déjà plus sur la clé
> (résolution à 3 niveaux). C'est le seul consommateur déjà immunisé.

### Les recherches deviennent-elles indépendantes en coupant le run de 03:00 ?

**Presque — il y a TROIS portes entrantes, pas une :**

| | Porte | Fréquence |
|---|---|---|
| **1** | Run dédié `sync_active_searches` | 03:00 |
| **2** | Run quotidien — `push_contacts_to_supabase` **supprime puis réécrit** les recherches d'un contact | 05:30 |
| **3** | **Read-through** — `refresh_console_contact_data` appelle le **même code** avec `--contact-id` | à chaque ouverture de fiche |

**Et une porte sortante** : les 3 travaux `*_hektor_contact_search`.

Couper les quatre rend les recherches entièrement app-owned — **et la clé cesse alors de bouger
toute seule, donc le problème A disparaît sans être corrigé**. Mais il faut d'abord :

- **corriger le modèle « au moins »** : la modale n'expose que des minimums, le worker sait envoyer
  20 critères. Ce que l'app ne sait pas exprimer sera perdu (cf. mémoire projet) ;
- **mesurer combien de recherches Hektor portent des critères invisibles dans l'app** ;
- **rebrancher l'irremplaçable** (point 1 ci-dessus) avant de couper quoi que ce soit.

**Ne pas ajouter de garde-fou sur la suppression** — décision Frédéric du 18/08 : il ferait échouer
les cas où le repli `list[0]` tombe juste.

### Le trou des NOUVELLES recherches — mesuré le 21/08

Les trois portes ci-dessus font entrer les **modifications**. Aucune ne fait entrer une
**première** recherche :

```
   les recherches ne sont PAS dans le listing -- uniquement dans ContactById
   creer une recherche ne bouge PAS la date_maj du contact
   le run de 03:00 ne relit que les contacts dont l'app connait deja une recherche active
   -> un contact qui gagne sa PREMIERE recherche n'entre dans aucun run. Jamais.
```

**Combien ?** Sonde du 21/08, **249 fiches tirées au hasard et lues en direct** chez Hektor parmi
les 67 483 contacts de typologie « acquéreur » sans recherche connue : **1 seule** portait une
recherche que l'app ignorait. Soit **≈ 270 recherches invisibles**, pas 67 000. *L'image de l'app
est juste à 99,6 %.*

**Ce que la sonde a écarté** : la typologie « acquéreur » **enveloppe** les recherches (aucune
recherche connue hors d'elle) mais elle est posée à la main sur des contacts qui n'ont jamais
rempli de critères, et elle ne bouge pas quand une recherche est créée. **Inutilisable comme
signal.** Il faut relire les fiches.

**Le remède** — `sync_active_searches.py --scope acquereurs`, c'est-à-dire *le run de 03:00 avec
une autre liste d'entrée* : mêmes quatre étapes, mêmes drapeaux, seule la sélection change
(`acquereur_contact_ids`). 71 337 fiches, **≈ 4 h 35**.

> ⚠️ **La pause de 20 s entre les lots ne doit pas être retirée.** Le run de 03:00 tient
> 6 appels/s pendant 10 minutes ; ici il faudrait les tenir 3 h. C'est exactement la forme qui a
> fait **bannir notre IP** au rattrapage des documents. Avec la pause : 4,2 appels/s en moyenne.

**Ce n'est pas un stock, c'est un débit.** La passe du 21/08 remet le compteur à zéro ; le débit,
lui, continue tant que les négociateurs saisissent dans Hektor. D'où **deux** passes, et pas une :

| | Quand | Pourquoi |
|---|---|---|
| **19-R1** | **21/08** — faite | solde les ~270 accumulées depuis mai |
| **19-R2** | **la veille de la bascule (19bis)** | ⚠️ **dernière occasion.** Tout ce qui aura été saisi dans Hektor entre les deux passes n'existe que là |

Entre les deux, si le délai s'allonge, relancer la même commande de temps en temps — elle est
idempotente et reprenable (chaque lot est indépendant, un lot en échec n'arrête pas le run).

---

## LES TROIS DÉPENDANCES RÉELLES À HEKTOR

| | Ce que Hektor fournit | Comment s'en passer | Délai |
|---|---|---|---|
| **1** | Le numéro de mandat | registre en propre | du code |
| **2** | La signature (ImmoSign) | Yousign | un contrat |
| **3** | **La diffusion portails** | contrats directs ou diffuseur | **contrat + migration commerciale** |

> **Arbitrage Frédéric (20/08) : les contrats démarrent à la fin** (chantier 5), pour préparer la
> coupure. Conséquence assumée : la date sera fixée par leur délai, qui ne commencera à courir
> qu'après le développement. La reprise des 350 annonces en ligne est le seul délai non maîtrisé.

---

## CHANTIER 1 — Maintenant, sans dépendance

| | Quoi | Pourquoi maintenant |
|---|---|---|
| **R1** | **Rebrancher ce qui est irremplaçable** — propositions, relances, retours acquéreur, envois, notifications — par *(contact + search_index)* | **URGENT** : une proposition sur deux a déjà perdu son lien, et rien ne peut la reconstruire |
| **R2** | **Nettoyer le recalculable** — 1 373 rapprochements + 11 966 lignes d'historique | sans risque, **mais seulement après R1** |
| **1.1** | ~~Un échec de worker prévient l'utilisateur et le monitoring~~ **FAIT le 20/08** (`48e475a`) | **indispensable** : un envoi raté laisse une annonce en ligne au mauvais prix |
| **1.2** | **Les recherches acquéreur sont enregistrées** dans l'app | seul endroit où une saisie se perd |
| **1.3** | Le numéro Hektor d'**annonce** a le droit d'être vide | ouvre la création app-first d'annonce |
| **1.4** | ~~**Identité des transactions**~~ **FAIT le 20/08** — 28 980 affaires renumérotées, `app_affaire_id` + `app_dossier_id` posés, clé basculée sur le numéro de l'app, triplet Hektor gardé en clé de réconciliation partielle | **le plus sûr des trois**, vérifié : 0 point d'appel ambigu. ⚠️ **`hektor_affaire_id` n'est unique que dans son type** — 7 541 numéros portés par deux types, 0 partageant l'annonce : Hektor tient trois compteurs qui se télescopent. Le numéro de l'app est **une seule série** pour les trois. Débloque la modale de statut (tâche 13) |
| **1.5** | **Identité des contacts** — renommage préalable, ajouter la case, renuméroter ≈ 186 500 lignes, **puis la case Hektor a le droit d'être vide** | débloque la modale d'ajout : contact + recherche + mandant écrits d'un coup. **Demande une demi-journée de relecture avant** |
| **1.6** | ~~Reprendre `numero_dossier`~~ **-> reporte au jour J** : comprendre la règle de numérotation Hektor et la continuer | référence métier lisible dans 11 tables — **personne ne la fabrique après la coupure** |
| **1.7** | ~~Annuaire négociateurs~~ **-> reporte au jour J** : le worker a besoin de l'`idUser` Hektor pour s'impersonner — 40 + 19, présents dans 14 tables | l'affectation doit survivre sans Hektor |

---

## CHANTIER 2 — Le cœur : Hektor confirme, il n'écrase plus

| | Quoi |
|---|---|
| **2.1** | Écrire la règle : les trois cas d'écart *(envoi pas parti / envoi raté / modifié dans Hektor)* |
| **2.2** | La tolérance de comparaison — la traduction des valeurs existe déjà (`resolveHektorSelectValue`) |
| **2.3** | Brancher au retour du worker *(`push_single_annonce_to_supabase.py:573`)* |
| **2.4** | Même règle sur l'import de nuit |

> **Le garde-fou existe déjà**, côté annonce et côté contact (`base_snapshot` + comparaison
> `date_maj`). Aujourd'hui, en cas d'écart, **Hektor gagne**. La règle 2 **inverse le verdict** :
> l'app garde sa valeur et signale. C'est une modification, pas une construction.

**Puis, dans la foulée :**

| | |
|---|---|
| **2.5** | **Le calque d'annonce disparaît** — il n'existe qu'à un seul endroit : l'édition de champs |
| **2.6** | La barrière : un travail sans numéro Hektor **attend** au lieu d'échouer |

---

## CHANTIER 3 — Appliquer le principe aux 16 workers

**Écrire chez soi d'abord, envoyer ensuite, confirmer au retour.**

| Ordre | Workers |
|---|---|
| **3.1** | Les 3 recherches *(ajouter / modifier / supprimer)* |
| **3.2** | **Statut + affaire** *(offre, compromis, vente)* — le geste le plus riche |
| **3.3** | Archiver / désarchiver / supprimer |
| **3.4** | **Créer un contact, créer un mandant, rattacher** *(après 1.3)* |
| **3.5** | **Affectation du négociateur — en DERNIER** (impersonation du worker) |

**Correctifs à glisser dedans :**

- **3.6** — **Clé propre au registre des affaires** *(28 980 lignes, clé 100 % Hektor)*
- **3.7** — **Fiabiliser le mandat des transactions** : l'app doit toujours le fournir ; aujourd'hui
  le worker le devine dans le HTML de Hektor si elle ne le fait pas
- **3.8** — **La clé de recherche** : aujourd'hui un hachage du contenu, elle change à chaque
  édition — **1 270 rapprochements déjà orphelins**. C'est la seule clé structurellement fausse.
- **3.9** — **Ménage** : `app_contact_override` (vide, non écrite), `app_console_create_update_contact_job`
  (remplacée par l'optimiste), tables `_v1` vides

---

## CHANTIER 3bis — Les recherches deviennent tiennes

**Quatre portes à fermer** — et c'est l'étape qui rend le problème de clé **sans objet** :

| | Porte | Fréquence |
|---|---|---|
| 1 | Run dédié `sync_active_searches` | 03:00 |
| 2 | Run quotidien — `push_contacts` **supprime puis réécrit** | 05:30 |
| 3 | **Read-through** — le MÊME code, avec `--contact-id` | à chaque ouverture de fiche |
| 4 | Les 3 travaux sortants `*_hektor_contact_search` | à l'édition |

**Deux préalables obligatoires :**

| | |
|---|---|
| **R3** | **Corriger le modèle « au moins »** — la modale n'expose que des minimums, le worker sait envoyer 20 critères. Aujourd'hui le run de nuit rattrape ; après la coupure, ce qui n'est pas stocké est **perdu** |
| **R4** | **Mesurer** combien de recherches Hektor portent des critères invisibles dans la modale |

> **Une fois les quatre portes fermées, plus personne ne recalcule le hachage : la clé cesse de
> bouger toute seule.** Le défaut identifié trois fois depuis juin disparaît **sans avoir été
> corrigé** — c'est la solution la plus économique du dossier.

---

## CHANTIER 4 — La création part de l'app

| | Quoi | Dépend de |
|---|---|---|
| **4.1** | **L'annonce** : la création écrit la vraie fiche | 1.4 · 2.3 · 2.6 |
| **4.2** | **Le contact et le mandant** : idem | 1.3 · 2.3 |
| **4.3** | **La modale d'ajout de contact** écrit ses trois objets d'un coup : contact + recherche + relation mandant | 4.2 |
| **4.4** | Les workers deviennent invisibles | **quand l'avertissement d'échec aura fait ses preuves** |

---

## CHANTIER 4bis — Rapatrier les binaires *(à terminer AVANT la coupure)*

| | Quoi | Volume |
|---|---|---|
| **4bis.1** | **Les documents** — `hektor_document_id` pointe vers le stockage de Hektor | **40 493** |
| **4bis.2** | **Les photos** — `hektor_photo_id`, idem | **1 397** |

> Ce ne sont pas des identifiants métier, ce sont **des adresses**. Tant qu'ils pointent vers
> Hektor, ils pointent vers un serveur qui va s'éteindre. **Irréversible : ce qui n'est pas
> descendu avant est perdu.**

---

## CHANTIER 5 — Préparer la coupure : les trois contrats

| | Quoi | Nature |
|---|---|---|
| **5.1** | **Sortie des portails** : combien, chez qui, à quel prix, et **comment reprendre les 350 annonces en ligne sans trou de visibilité** | contrat + migration |
| **5.2** | **Yousign** — l'app ne sait pas *lancer* une signature | contrat + code court |
| **5.3** | **Registre de mandats en propre** — obligation légale, libère `numero_mandat` | code |

---

## CHANTIER 6 — Le jour J, une journée

| | |
|---|---|
| **6.1** | Le distributeur démarre à **100 000**, dans le couloir vide 25 000 → 1 000 000 |
| **6.2** | Le serveur remplit **les deux cases** : les 24 tables qui portent le numéro Hektor continuent sans le savoir |
| **6.3** | Le numéro est **imposé**, pas laissé au compteur local (à 5,25 millions) |
| **6.4** | On éteint l'aspirateur : pipeline, workers, Playwright, file de travaux |
| **6.5** | Les 3 PDF et les 4 workers internes **continuent tels quels** |

---

## LA RÈGLE DES IDENTIFIANTS

> **Pour chaque identifiant que Hektor fabrique, trois questions avant la coupure :**
> **1.** Qui le fabriquera après ? · **2.** Que deviennent les valeurs déjà émises ? · **3.** Qu'est-ce
> qui casse s'il est vide ?
>
> Annonces : répondu. Contacts et affaires : chantier 1. **`numero_dossier`, annuaire, binaires :
> nouvellement identifiés.** Détail : `AUDIT_TOUS_LES_IDENTIFIANTS_2026-08-20.md`.

---

## LES QUATRE RÈGLES

1. **Un numéro ne se perd jamais.** *(fait)*
2. **Hektor confirme, il n'écrase pas.**
3. **Une action a toujours une fin visible** — surtout quand elle rate.
4. **Tant que la diffusion passe par Hektor, Hektor doit rester à jour.**

---

## CE QUI RESTE NON MESURÉ

- **La lenteur du front** — la mesure F12 n'a jamais été faite.
- **Les 176 champs du grand bloc** — affichables et modifiables, non filtrables dans les listes.
- **La clé de recherche** — hachage du contenu, elle change à chaque édition : **1 270 rapprochements
  déjà orphelins**.
- **Le coût réel de l'identifiant contact** — quelles tables parmi les 21 qui portent le numéro Hektor.
