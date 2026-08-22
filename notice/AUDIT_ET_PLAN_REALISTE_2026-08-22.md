# Audit du projet et plan réaliste — 22/08/2026

Demandé par Frédéric : *« fais un audit de mon projet actuel et réaliste le plan en détail,
ensuite fais une analyse des deux et donne-moi ton avis. »*

**Tout ce qui suit est mesuré aujourd'hui, pas rappelé de mémoire.** Là où je n'ai pas mesuré,
c'est écrit.

Circonstance : **Hektor est en panne depuis ~15:00** — injoignable depuis deux réseaux sans
rapport, ce n'est pas nous. C'est une occasion qu'on n'aura pas deux fois : au lieu de supposer
ce qui casserait sans lui, **on le voit**.

---

# PARTIE 1 — L'AUDIT

## 1.1 Les cinq pièces, mesurées

| | | Taille réelle |
|---|---|---|
| **Hektor** *(loué)* | le meuble à dossiers | **en panne** |
| **Le miroir** `data/hektor.sqlite` | l'archive de tout ce que Hektor a dit | **3,89 Go** · 33 tables · 464 952 réponses |
| **Le serveur** `phase2/phase2.sqlite` | le coffre et l'usine | **4,32 Go** · 26 tables natives + **120 descendues** · 1 521 386 lignes |
| **Supabase** | le bureau où travaille l'équipe | 91 tables · 29 vues · **124 fonctions** · 10 tâches cron · 104 politiques RLS |
| **Le front** *(Vercel)* | la fenêtre | 19 fichiers · **51 097 lignes** *(dont `App.tsx` : 37 204)* |

Et autour :

```
   le backend (Render)     12 routeurs
   le worker (Windows)     13 196 lignes, ~35 types de travaux
   le serveur              61 scripts phase2, 9 lanceurs, 6 taches planifiees (toutes S4U)
   les binaires            46 359 fichiers, 65,6 Go sur le disque
   la surveillance         21 sondes, dont 2 locales
```

## 1.2 Ce que la panne révèle — l'essai grandeur nature

**Ce qui est tombé :** tout ce qui **écrit** chez Hektor. Le worker, les créations, la signature,
les runs de 03:00 et 05:30 de cette nuit si ce n'est pas rétabli.

**Ce qui tient, mesuré pendant la panne :**

```
   le front Vercel               HTTP 200 en 0,06 s
   Supabase                      repond normalement
   les rapprochements            calcules par pg_cron, dans Supabase -- Hektor n'y est pour rien
   la Descente de 07:30          elle lit Supabase, la panne ne la concerne pas
   travaux en attente            0
   travaux en erreur (24 h)      0
   editions en attente           0
   travaux reussis (24 h)        1 697
```

> **L'app est déjà consultable sans Hektor.** Ce qui casse, ce n'est pas la lecture — c'est
> **l'écriture vers lui** et la **fraîcheur** des données.

C'est la meilleure nouvelle de cet audit, et elle n'était pas acquise avant hier : jusqu'à
mardi, tout ce que l'app avait inventé n'existait qu'en ligne.

## 1.3 Les écarts entre le plan et la réalité

**Trois découvertes, toutes dans le sens du soulagement.**

### ① Le rapatriement des documents est largement fait

Le plan annonce *« 27 — Rapatrier les documents, 40 493, ⚠ irréversible »*. La mesure :

```
   44 512 documents indexes
      22 491   local_only        deja sur le disque, jamais montes au cloud
      22 021   cloud_available   dans le cloud

   46 359 fichiers sur le disque, 65,6 Go
```

Il y a **plus de fichiers sur le disque que de documents `local_only`** — donc une part des
`cloud_available` est déjà là aussi. **La tâche est beaucoup plus petite qu'annoncée**, mais son
périmètre exact reste à établir : *combien de `cloud_available` n'ont pas de fichier local ?*
C'est une mesure d'une heure, pas un chantier.

### ② Le serveur détient déjà les annonces *(corrigé le 21/08)*

`app_view_generale` : 56 893 lignes, 130 colonnes, refaite chaque nuit en 37 secondes. Le plan
affirmait le contraire.

### ③ Le bloc B n'existait pas, et il est fait

Le plan supposait acquis que le serveur apprenait de l'app. **C'était faux : rien ne remontait.**
Construit et vérifié les 21 et 22/08.

## 1.4 Deux défauts trouvés aujourd'hui, non corrigés

| | |
|---|---|
| **`app_search_count_high_water` (9 612 lignes) n'a pas de RLS** | table que j'ai créée le 21/08 pour la sentinelle 4sexies, sans politique. Sensibilité faible *(des identifiants de contact et des compteurs)*, mais c'est un trou, et il est de moi |
| **`tmp_etape12_avant`** | table temporaire d'une migration, restée en place, vide. À supprimer |

## 1.5 La dépendance réelle à Hektor, en trois lignes

```
   LES DONNEES     resolu. Le serveur detient tout, y compris ce que l'app a invente
   L'ECRITURE      un robot Playwright qui remplit le formulaire web. Fragile par nature,
                   et ca ne se corrigera pas -- ca disparaitra avec Hektor
   LES PORTAILS
   ET LA SIGNATURE IRREMPLACABLES sans contrat en propre. C'est le seul vrai verrou.
```

---

# PARTIE 2 — LE PLAN RÉALISTE

**Ce qui change par rapport au plan du 21/08 :** des durées, et la distinction entre *ce que je
peux faire* et *ce qui dépend de toi ou d'un tiers*.

⚠ **Sur les durées.** Je me suis trompé deux fois cette semaine en donnant un chiffre précis là
où la donnée ne portait qu'un ordre de grandeur *(les « ~270 recherches », les comptes `pg_stat`)*.
Ce qui suit est donné en **fourchettes**, et chaque fourchette dit sur quoi elle repose.

## 2.1 Ce qui est fait

```
   0.1  les deux registres dans la sauvegarde de nuit
   0.2  la regle du miroir
   B.1  la descente                     110 tables, 1 337 162 lignes
   B.2  les doublures                   10 tables
   B.4  le journal et son alarme
   B.5  la tache planifiee de 07:30
   1 a 4sexies   tout le bloc identite/recherches des 20 et 21/08
```

## 2.2 Ce qui ne dépend pas de moi — **et qui commande le calendrier**

| | Tâche | Durée | Dépend de |
|---|---|---|---|
| **A.1** | **Portails en nom propre** + reprise des ~350 annonces en ligne | **inconnue — semaines à mois** | négociation commerciale |
| **A.2** | **Contrat de signature** en propre | **inconnue — semaines** | négociation commerciale |
| **A.3** | **Registre de mandats** en propre | dépend de A.1/A.2 | obligation légale |
| **19bis** | **Bascule des négociateurs sur l'app** | décision | organisation |

> **Rien de ce qui suit ne permet de couper Hektor tant que A.1 et A.2 ne sont pas faits.**
> C'est le seul chemin critique du projet, et il n'a pas commencé.

## 2.3 Ce que je peux faire sans Hektor

| | Tâche | Durée estimée | Sur quoi repose l'estimation |
|---|---|---|---|
| **C.6** | La table « ce que l'app détient » pour l'annonce + les 36 champs calculés à l'export | **1 à 2 jours** | le patron `app_search_registry` est éprouvé ; les 132 autres champs sont déjà des colonnes locales |
| **C.2a** | **Identité des contacts — la relecture** *(pas le code)* | **une demi-journée** | ~530 points de code recensés le 20/08 |
| **D.1a** | **Mesurer** le périmètre réel du rapatriement des documents | **1 heure** | il suffit de croiser 22 021 `cloud_available` avec le disque |
| — | Fermer les deux trous du 1.4 *(RLS, table résiduelle)* | **1 heure** | deux migrations d'une ligne |

## 2.4 Ce qui exige Hektor vivant

| | Tâche | Durée estimée | Réserve |
|---|---|---|---|
| **C.1** | La règle de comparaison — *Hektor confirme, il n'écrase plus* | **3 à 5 jours** | le garde-fou existe déjà ; c'est le **verdict** qu'on inverse. Mais il faut l'éprouver sur les 3 objets |
| **C.3** | L'exception recherches — fermer la porte sortante, marquer, faire descendre | **1 à 2 jours** | la moitié est déjà là *(la doublure existe)* |
| **C.2b** | Identité des contacts — **le code** | **1 à 2 semaines** | 186 500 lignes, ~530 points de code. **C'est la plus grosse tâche du projet** |
| **C.4** | Les workers, un par un | **2 à 3 semaines** | 35 types de travaux ; l'affectation du négociateur en dernier |
| **C.7** | Le serveur lit sa base, plus le miroir | **2 à 3 jours** | collée à C.1 |
| **C.9** | La création part de l'app | **1 à 2 semaines** | après C.7 |
| **D.1** | Rapatrier ce qui reste des documents | **inconnue** — voir D.1a | ⚠ le débit a déjà fait bannir notre IP |

## 2.5 L'ordre, et ce qui bloque quoi

```
   A.1 + A.2  --------------------------------------------------->  la coupure
   (semaines a mois, ne depend pas de moi)                              |
                                                                       |
   C.6 -> C.1 -> C.7 -> C.9                                             |
            \                                                           |
             -> C.2a -> C.2b -> C.4 ------------------------------------+
                        (la plus longue)                                |
                                                                        |
   D.1a -> D.1 --------------------------------------------------------+
```

**Le chemin le plus long côté technique** : `C.2a → C.2b → C.4`, soit **4 à 6 semaines** de
travail effectif.

**Le chemin le plus long tout court** : `A.1`, dont je ne connais pas la durée.

---

# PARTIE 3 — ANALYSE, ET MON AVIS

## 3.1 Ce que l'audit dit du projet

**Le projet est en bien meilleur état que le plan ne le laissait croire.** Trois tâches
inscrites comme lourdes se révèlent faites ou beaucoup plus petites : les annonces sur le
serveur, le rapatriement des documents, et la moitié du bloc B qu'on vient de construire.

**Et la panne d'aujourd'hui est un bon signal.** Le front répond, Supabase répond, les
rapprochements se calculent, la file de travaux est vide. **L'app tient debout sans Hektor** —
en lecture. C'est plus que ce qu'on pouvait dire lundi.

## 3.2 Ce qui m'inquiète vraiment

**① Le bloc A n'a pas commencé, et c'est le seul qui compte.**

Tout le travail technique du monde ne coupera pas Hektor tant que tes annonces passent par son
abonnement portails et que tes mandats se signent avec **son** contrat. Ces deux dossiers ont un
délai que personne ici ne maîtrise, et **ils sont à zéro**.

Si A.1 prend quatre mois et qu'il commence en novembre, la coupure est en mars. S'il commence
cette semaine, elle peut être en décembre. **C'est le seul arbitrage qui change vraiment la
date**, et il ne demande pas une ligne de code.

**② `App.tsx` fait 37 204 lignes.**

Un seul fichier porte les trois quarts du front. Ce n'est pas un problème aujourd'hui — ça
marche — mais chaque écran ajouté le rend plus difficile à modifier sans rien casser, et le
chantier C va beaucoup y toucher *(la création part de l'app, C.9)*. Je ne propose pas de le
découper maintenant : ce serait un chantier en soi, sans valeur métier. Je le signale parce que
c'est le genre de dette qui se paie au pire moment.

**③ La qualité de mes propres estimations.**

Trois fois cette semaine j'ai donné un chiffre précis sur une donnée qui n'en portait pas :
« ~270 recherches invisibles » *(réalité : environ 5)*, « 20 000 rapprochements disparus »
*(réalité : zéro, j'avais comparé une estimation à un comptage)*, « ~2,7 Go après la descente »
*(réalité : 4,32)*. Aucune n'a causé de dégât, mais toutes ont coûté du temps.

**La règle que j'applique désormais** : un chiffre qui entre dans une décision se mesure par un
comptage, pas par une estimation ni par un échantillon d'une seule occurrence.

## 3.3 Mon avis, en trois phrases

**Ouvre le bloc A cette semaine.** C'est le seul chemin critique, il ne demande rien de moi, et
chaque semaine de retard s'ajoute intégralement à la date de coupure.

**Ne lance pas C.2b — l'identité des contacts — avant d'avoir fait C.2a**, la demi-journée de
relecture. C'est la plus grosse tâche du projet, elle touche 186 500 lignes et ~530 points de
code, et c'est exactement le genre de chantier où une heure de lecture économise une semaine.

**Et ne cherche pas à finir le rattrapage des recherches.** La mesure d'aujourd'hui — 1 recherche
découverte sur 26 700 fiches relues, dans les tranches les plus riches — dit que le gain est de
quelques unités. *(Ce sujet appartient à l'autre session ; je ne le documente ici que parce qu'il
change une priorité.)*

## 3.4 Ce que je ferais demain matin, à ta place

```
   1.  appeler les portails et Yousign            A.1, A.2 -- rien a coder
   2.  me faire dire ce que dit le journal        la premiere Descente automatique, 07:30
   3.  me faire mesurer D.1a                      1 heure, et ca dedouble peut-etre une tache
   4.  me faire faire C.6                         1 a 2 jours, local, sans Hektor
```

Le reste attend que Hektor revienne — et ce n'est pas grave, parce que **rien de ce qui attend
n'est sur le chemin critique.**

---

*Sources : mesures directes du 22/08/2026 sur les cinq supports ; `sb_pull_state` ;
`app_doublure_journal` ; `app_console_job` ; `app_worker_registry` ; `pg_stat_user_tables` et
`information_schema` côté Supabase ; inventaire du disque `C:\Hektor\HektorConsoleDocuments` ;
`notice/AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md` pour l'audit de la veille.*
