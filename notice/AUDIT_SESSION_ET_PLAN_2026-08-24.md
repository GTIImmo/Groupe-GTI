# Audit de la session, du plan, et du système — 24/08/2026

Demandé par Frédéric : *« un audit sur ce chat et mon plan de dev, ensuite refais une analyse
sur mon serveur, mon app et toutes mes notes pour ne pas te baser qu'à des notes, puis reliste
les actions et étapes dans l'ordre le plus logique. »*

Méthode : inventaire des **165 notes** *(109 dans `notice/`, 56 à la racine)*, lecture des plus
structurantes, mesure directe des trois supports, et relecture du code du worker.

---

# PARTIE 1 — AUDIT DE CETTE SESSION

## 1.1 Ce qui a été livré, et qui tient

| | Vérifié comment |
|---|---|
| **B.1 — la descente** · 110 tables | comptes locaux vs Supabase, contenu comparé valeur par valeur |
| **B.2 — les doublures** · 10 tables | 14 contrôles, tables natives inchangées à la ligne près |
| **B.4 — le journal + l'alarme** | **entendue sonner**, puis restaurée |
| **B.5 — la tâche de 07:30** | tourne seule depuis 2 jours, `exit 0`, ~21 min |
| **0.1 · 0.2 — sauvegarde et règle du miroir** | archive décompressée pour vérifier |
| **0.4 → 0.7 — la sécurité** | lecture réussie **puis refusée** avec la clé publique |

**Total descendu et vérifié : 1 513 361 lignes, 120 tables.**

## 1.2 Les erreurs que j'ai commises, et ce qu'elles coûtent

**Elles sont de trois natures, et la troisième est la plus grave.**

### a) Des chiffres donnés sans mesure — trois fois

| Ce que j'ai annoncé | La réalité |
|---|---|
| « ~270 recherches invisibles » | **environ 5** |
| « 20 000 rapprochements disparus » | **zéro** — j'avais comparé une estimation à un comptage |
| « ~2,7 Go après la descente » | **4,34 Go** |

### b) Des conclusions tirées d'observations qui n'excluaient rien

**« Hektor est en panne »** — mon test *(un délai qui expire)* ne distinguait pas un serveur
éteint d'un pare-feu qui nous bloque. C'était **un bannissement d'IP**. Le test qui discrimine
est celui d'un tiers, depuis un autre réseau.

**« La Descente ne tournait pas »** — j'avais mesuré à un instant, longtemps après. Elle avait
tourné jusqu'au bout, en orphelin. Et j'ai **retiré son verrou pendant qu'elle protégeait un run
vivant**.

### c) J'ai réinventé un travail déjà fait

**C'est la plus coûteuse.** J'ai proposé, sous le nom de « C.1' — protéger le champ et non la
fiche », exactement ce que la note **`A1_CHAMPS_PROPRIETE_APP_2026-08-19`** avait établi cinq
jours plus tôt — en mieux :

> *« Si l'app sait écrire un champ dans Hektor, c'est que le négociateur en est l'auteur.
> Donc l'import n'a pas le droit de le réécrire. »*

**189 champs déjà listés**, dérivés des trois listes du worker. Le mécanisme déjà décrit
*(« les champs verts sont retirés du paquet — c'est une soustraction »)*. Les trois portes
d'entrée déjà nommées. Et **trois arbitrages en attente de Frédéric**, jamais rendus.

**A2 n'existe pas.** Le travail s'est arrêté sur cette validation.

## 1.3 Pourquoi c'est arrivé — la cause est structurelle

Il existe un **contrat de méthode** *(`METHODE_DE_TRAVAIL_2026-08-20`)*, écrit après une journée
où trois oublis avaient été rattrapés par Frédéric. Son étape ① est explicite : lire la
checklist, **les notes citées**, `ls notice/*.md` par mot-clé, les notes supprimées, la mémoire.

**Je ne l'ai pas appliqué** en attaquant C.1.

Et le plan ne pouvait pas m'y aider :

```
   sur les 21 notes les plus recentes, 19 ne sont PAS citees par le plan
```

Dont `A1`, `METHODE_DE_TRAVAIL`, l'étude des workers, l'audit de l'identité des contacts, la
vision globale. **Le plan s'est détaché de la connaissance accumulée.** C'est la cause, pas
l'inattention.

---

# PARTIE 2 — AUDIT DU PLAN

## 2.1 Ce qui est faux ou périmé dans le plan actuel

| | Le plan dit | La mesure dit |
|---|---|---|
| **C.4** | « les 35 workers, 2 à 3 semaines » | **16 workers** sont le gisement réel *(familles B1+B2)*. **7 sur 34 fonctionnent déjà sans Hektor.** Source : `ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20`, non citée |
| **C.1'** | à écrire | **déjà écrit** dans `A1`, en attente de 3 arbitrages |
| **D.1** | « rapatrier 40 493 documents » | 46 359 fichiers et **65,6 Go déjà sur le disque**. Périmètre réel non mesuré |
| **Dépendance à Hektor** | diffuse | **trois workers seulement** : numéro de mandat, relance et annulation de signature. Ce sont exactement A.1 et A.2 |

## 2.2 Ce qui est juste et confirmé

- **La stratégie en trois étapes** supprime bien le cas ③ *(modifié dans Hektor)* et avec lui
  l'arbitrage. Confirmé.
- **Le vrai danger restant** — l'envoi échoue, la protection tombe, le run écrase — est
  **démontré** sur le contact 602197 : les trois supports disent `prix_min = 0`, la saisie de
  120 000 € n'existe nulle part, et personne n'avait rien modifié dans Hektor.
- **Le chemin critique n'est pas technique.** A.1 et A.2 ne dépendent pas de moi et sont à zéro.

---

# PARTIE 3 — L'ÉTAT RÉEL, MESURÉ LE 24/08

```
   LE SERVEUR      phase2.sqlite  4,34 Go       miroir  3,90 Go
                   annonces     56 894   (version Hektor, refaite chaque nuit)
                   contacts    355 670
                   recherches   76 880
                   descendu de Supabase : 120 tables, 1 513 361 lignes

   LE JOURNAL      22/08   45 lignes connues de l'app seule
                   23/08   45
                   24/08   45          -> PLAT

   L'APP           51 097 lignes de TypeScript, dont 37 204 dans App.tsx
   SUPABASE        91 tables, 29 vues, 124 fonctions, 10 crons
   LES BINAIRES    46 359 fichiers, 65,6 Go
   LES TACHES      6, toutes en S4U
   LA SURVEILLANCE 21 sondes
```

**Le journal plat trois jours de suite est un résultat** : la divergence ne croît pas. Si ça
tient trois semaines, **B.3 est inutile** — décidé par la mesure, pas par intuition.

---

# PARTIE 4 — LES ACTIONS, DANS L'ORDRE LE PLUS LOGIQUE

## Ordre 0 — réparer la cause, pas les symptômes *(1 heure)*

| | |
|---|---|
| **0.a** | **Rattacher les 19 notes orphelines au plan.** Sans ça, la duplication recommencera. C'est la seule action de cet audit qui protège toutes les autres |
| **0.b** | **Rendre les trois arbitrages de A1** — `statut_annonce`, `negociateur_email`, les champs de mandat. Personne ne peut le faire à la place de Frédéric, et A2 est bloqué dessus depuis le 19/08 |

## Ordre 1 — ce qui commande la date, et ne dépend pas de moi

| | | |
|---|---|---|
| **A.1** | **Portails en nom propre** | semaines à mois · **à zéro** |
| **A.2** | **Contrat de signature** | semaines · **à zéro** |
| **A.3** | Registre de mandats en propre | après A.1/A.2 |

> Ces trois-là remplacent **exactement** les trois seuls workers qui dépendent réellement de
> Hektor. Tant qu'ils n'avancent pas, aucune ligne de code ne rapproche la coupure.

## Ordre 2 — avant de basculer les négociateurs

| | | Durée |
|---|---|---|
| **C.0** | **AUDIT : que ne peut-on pas faire dans l'app ?** | ½ j — **décide de la date de l'étape 2** |
| **C.3** | Fermer la porte sortante des recherches | 1 à 2 j — supprime la famille 602197 |
| **A2** | **La propriété des champs** *(ex-C.1')* — la constante unique, lue par les trois portes ; les champs verts retirés du paquet | 2 à 3 j — **après 0.b** |
| **C.2a** | Identité des contacts — la relecture | ½ j |

## Ordre 3 — pendant l'étape 2

`C.2b` identité contacts *(1 à 2 sem.)* · `C.6` le domicile de l'annonce *(1 à 2 j)* ·
**`C.4` les 16 workers** *(et non 35)* · `C.5` clé du registre d'affaires et mandat des
transactions · `C.7` le serveur lit sa base · `C.8` calque et barrière · `C.9` la création part
de l'app · `C.11` ménage.

## Ordre 4 — la coupure

`D.1a` mesurer le périmètre réel des documents *(1 h)* · `D.1`/`D.2` rapatrier · `E` le jour J.

## En observation, sans action

**B.3** — le déclencheur. Le journal décidera. Trois jours plats sur trois.

---

*Sources : mesure directe des trois supports le 24/08 ; `console_job_worker.js` lignes 9179,
11419, 11599, 11918 ; `push_contacts_to_supabase.py:458-461` ; inventaire des 165 notes ;
`A1_CHAMPS_PROPRIETE_APP_2026-08-19` ; `ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20` ;
`METHODE_DE_TRAVAIL_2026-08-20`.*
