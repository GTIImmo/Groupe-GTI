# LA SENTINELLE DU REGISTRE CRIAIT AU LOUP CHAQUE MATIN — 13/10/2026

*Hors chantier ③. Né de l'alerte que Frédéric a reçue le 13/10 au matin :*
`[data.mandat_un_numero] Mandats du serveur absents de Supabase : 4 sur 26855 (seuil 0) -- le push n'est pas passe`

> ⚠ La note du chantier ③ n'est **pas** touchée : une autre session l'avait ouverte avec des
> modifications non commitées au moment où j'ai écrit ceci.

---

## 1. CE QUE LE MESSAGE DISAIT — ET CE QUI ÉTAIT VRAI

| | |
|---|---|
| Le message | « le push n'est pas passé » |
| La vérité | **le push est passé** : le journal du run, ligne 1219, dit `PUSH app_mandat -> Supabase : 26855 lignes`, étape **DONE** |
| Et aussi | Supabase, le serveur **et** la doublure portent tous **26 855** lignes |
| Ma part | **aucune.** L'historique `app_monitor_event` montre ce rouge **chaque jour depuis le 08/10** (5, 1, 3, 4 absents), c'est-à-dire **avant** mon travail |

## 2. LA CAUSE — UNE QUESTION D'HORLOGE, PAS DE DONNÉE

La sentinelle compare **le registre du serveur** à **sa doublure** `app_mandat__sb`, l'image de
Supabase redescendue chez nous. Or les deux ne sont pas remplies au même moment :

| heure | ce qui se passe |
|---|---|
| **06:56** | le run **écrit** le registre et le **pousse** vers Supabase ✅ |
| **07:45** | la descente démarre — `app_mandat__sb` est la table **97 sur 110** |
| **07:48** | **le moniteur passe** *(il passe toutes les 2 h, à …:48)* |
| **~07:58** | la doublure est enfin rafraîchie |

À **07:48**, elle comparait donc **le registre de ce matin** à **une copie de la veille**.
Deux heures plus tard, à 09:49, elle redevenait verte **toute seule**.
**Un rouge qui revient chaque matin et repart seul n'est plus un rouge** : il apprend à ne plus
être lu, et il enterre les vrais.

*Le warning `data.doublure_journal` du même e-mail a exactement la même cause.*

## 3. CE QUI A ÉTÉ FAIT — « ne crie pas ce que tu ne peux pas savoir »

**Un seul test en plus, et il est DANS LA FORMULE** *(`phase2/checks/mandat_un_numero.py`, la
seule copie — le fichier du moniteur dit lui-même « la formule n'est pas ici »)* :

> si la doublure a été descendue **avant** la dernière écriture du registre,
> ou si la descente est **en cours** → **« NON CONCLUANT »** *(warning)*
> sinon → on juge **comme avant** *(rouge si des mandats manquent)*

**Le vrai rouge est intact** : copie à jour + des mandats qui manquent = `critical`, mot pour
mot comme avant.

| fichier | ce qui change |
|---|---|
| `phase2/checks/mandat_un_numero.py` | `_en_utc()` · `_fraicheur_copie()` · 2 lignes dans `mesurer()` · `main()` rend **2** et dit « NON CONCLUANT » |
| `monitoring/check_gti_health.py` | **une branche insérée avant** la branche rouge *(rien d'écrasé)* + la nuance ajoutée au docstring |
| `phase2/checks/test_mandat_un_numero_fraicheur.py` | **neuf** : l'épreuve, 12 cas |

⚠ **LE PIÈGE DE FUSEAU, qui aurait faussé la mesure de DEUX HEURES.** `app_mandat.last_seen_at`
est en **UTC** *(`+00:00`)*, `sb_pull_state.derniere_descente` est **locale sans fuseau écrit**.
Comparer les deux **textes** aurait rendu l'inverse de la vérité. D'où `_en_utc()`.

## 4. CE QUI A ÉTÉ ÉPROUVÉ — 12 cas, et le témoin inverse

`python phase2/checks/test_mandat_un_numero_fraicheur.py` → **12/12**.
L'épreuve se joue sur une **base en mémoire** : le cas « copie en retard » ne dure que d'environ
06:56 à 07:58, et on n'allait pas attendre demain matin — ni abîmer `phase2.sqlite` en pleine
journée pour le provoquer.

**Côté formule (8 cas)** : copie à jour sans écart · **copie à jour AVEC un écart → on crie
encore** · copie de la veille → on se tait · descente en cours → on se tait · pas de date ·
date illisible · registre sans date *(on ne devine pas)* · **le piège du fuseau**.

**Côté sentinelle (4 cas)**, avec le **vrai** code du moniteur, cette sonde **seule** *(le
moniteur complet envoie des e-mails)* : `critical` quand le push a vraiment échoué · `warning`
copie en retard · `warning` descente en cours · `critical` quand la fraîcheur est inconnue.

⭐ **Témoin inverse.** Un test qui passe ne prouve rien s'il ne sait pas échouer. J'ai **remis la
comparaison naïve** à la place de `_en_utc()` et vérifié que le cas 8 **bascule** :

| | `copie_en_retard` |
|---|---|
| avec la conversion de fuseau | **True** *(la vérité)* |
| comparaison naïve des textes | **False** *(le mensonge)* |

## 5. LE CONTRÔLE SUR LE VRAI ÉTAT

Sonde réelle, base ouverte en **lecture seule**, à 11 h :

```
[ok] data.mandat_un_numero
   Un mandat, un numero : 0 ecart sur 26855 (0 ne(s) dans l'app, pas encore chez Hektor)
   copie_descendue_le   '2026-10-13T07:45:03'      (= 05:45 UTC)
   registre_ecrit_le    '2026-10-13T04:56:43+00:00'
   copie_en_retard      False
```
05:45 UTC **après** 04:56 UTC → la copie est à jour, et la sentinelle juge donc **comme avant**.

## 6. CE QUI POURRAIT CASSER AILLEURS — vérifié

| | |
|---|---|
| `graves` *(le code de sortie de la formule)* | **délibérément pas touché** : `mandat_un_numero.py` en ligne de commande garde le sens de son code 1. Le « non concluant » rend **2**, une valeur neuve |
| les **autres** branches rouges | `deux_numeros`, `croisements`, `plage_envahie` se mesurent **sur le serveur seul** : la fraîcheur de la copie ne les concerne pas, elles restent `critical` **avant** la nouvelle branche |
| les autres sondes | elles n'appellent pas cette formule *(une copie par fichier, c'est la règle du projet)* |
| le run, les workers, la descente | **rien** : la formule est en **lecture seule**, le moniteur n'écrit que dans sa propre liste |
| retour arrière | `git revert` du commit, ou supprimer la branche du moniteur : la formule reprend son rouge |

## 7. CE QUI RESTE À FRÉDÉRIC

- ⬜ **Le vrai contrôle est demain matin à 07:48** : l'e-mail doit porter un **warning
  « NON CONCLUANT »** à la place du `critical`, et **0 écart** à 09:48.
- ⬜ **La cause profonde n'est pas réparée, elle est seulement rendue lisible** : la doublure
  descend **une heure après** le push. Deux pistes *(à trancher, pas par moi)* :
  **A** descendre `app_mandat__sb` **en premier** au lieu de 97<sup>e</sup> ·
  **B** décaler le moniteur du matin après 08:05. **Je n'ai rien choisi.**
- ⚠ **Les 8 warnings de l'e-mail du 13/10 ne viennent d'aucun de mes travaux** — vérifié un par un.

---

## 8. ⭐ LA FAMILLE — *il reste UNE sœur, et son correctif est à un `and` près*

« Une cause structurelle se balaie dans toute sa famille. » J'ai donc cherché **toutes** les
sentinelles qui tirent un **rouge** à partir d'une **doublure `__sb`** :

| sentinelle | état |
|---|---|
| `data.mandat_un_numero` | ✅ **corrigée aujourd'hui** |
| `data.recherche_divergente` *(`check_gti_health.py` **l. 2128**)* | ⛔ **le même défaut, intact** |
| `data.relation_disparue` | ✅ rien à faire — son docstring dit « le retard du cloud est rendu **en information, jamais en alerte** » |
| `data.mandat_disparu` | ✅ rien à faire — elle compare **serveur ↔ miroir**, pas la doublure |

**La sœur était déjà connue**, et son correctif déjà écrit… en mémoire seulement : une note du
**29/08** dit *« correction proposée (PAS codée, en attente de go) : statut non mesurable au lieu
d'un critical sur données périmées »*. **Six semaines plus tard, elle sonne toujours.**

Et le plus frappant : **deux lignes au-dessus du rouge**, le même code calcule déjà
`dernier != aujourdhui` pour écrire le warning `data.doublure_journal` *« relevé des doublures
pas fait aujourd'hui »*. **Elle sait que sa copie est périmée, et tire quand même.**
Le garde-fou est **à un `and` près**.

> ✅ **RÉPONSE DE FRÉDÉRIC : « A, maintenant »** — fait, voir la section 9.

---

## 9. LA SŒUR EST CORRIGÉE — *et mieux que ce que proposait le 29/08*

Le correctif proposé le 29/08 était : *« ne pas évaluer quand le relevé des doublures n'est pas
d'aujourd'hui »*. En mesurant, j'ai trouvé **une meilleure source** : les deux côtés portent
leur propre date, donc on lit la **fraîcheur réelle** au lieu d'un indice indirect.

| ce qu'on compare | sa date, mesurée le 13/10 |
|---|---|
| le **natif** `app_contact_search_current` *(réécrit en entier chaque nuit — 77 178 lignes, toutes la même date)* | `max(refreshed_at)` = **04:49 UTC** *(= 06:49 chez nous)* |
| la **doublure** `app_contact_search_current__sb` | `sb_pull_state.derniere_descente` = **07:45 locale** *(= 05:45 UTC)* |

05:45 UTC **après** 04:49 UTC → la copie est à jour, donc on juge normalement. À 07:48, elle ne
l'était pas.

⭐ **Et j'ai trouvé le piège avant qu'il ne morde.** Le fichier contient **déjà** un lecteur de
dates, `parse_iso`, qui suppose **UTC** quand le fuseau manque. S'en servir ici aurait
**rajeuni la copie de deux heures** — et **dans le pire sens** : une copie périmée serait
passée pour fraîche, donc la sentinelle aurait crié en croyant ses données bonnes.
D'où un **jumeau** `parse_iso_locale_si_sans_fuseau`, dont le nom dit ce qu'il fait.
*(Et `parse_iso` reste juste là où elle sert : les dates de Supabase et des API, toutes en UTC.)*

**Éprouvé : 8 cas sur 8** — `monitoring/test_recherche_divergente_fraicheur.py`, sur une base
d'essai construite dans un dossier temporaire *(jamais la vraie)*, en appelant **la seule sonde**.
Dont **« copie à jour ET un critère qui diverge → on crie encore »**, et les 4 cas où la
fraîcheur est **inconnue** → **on ne devine pas, on juge comme avant**.

**Témoin inverse** : en remplaçant le bon lecteur de dates par `parse_iso`, le cas 8 **bascule**
de `warning` à `critical`. Il mesure donc bien quelque chose.

**Contrôle réel**, base en lecture seule : `[ok] 0 (seuil 0)`, `copie_en_retard = False`.

⚠ **Un défaut voisin, trouvé en passant, PAS corrigé** *(c'est ton appel)* : deux lignes plus
haut, le même code compare `releve_le` — écrit en **date locale** par `comparer_doublures.py` —
à `datetime.now(timezone.utc)`, une **date UTC**. Entre minuit et 2 h du matin les deux ne sont
pas le même jour : le passage de **01:48** peut dire « relévé à jour » en s'appuyant sur celui de
**la veille**. C'est un **faux vert**, deux heures par nuit — **la troisième fois** que la même
confusion UTC / locale apparaît dans ce fichier.

---

## 10. ⛔ DÉCALER LE MONITEUR NE PEUT PAS MARCHER — *la mesure contredit la consigne*

Tu as tranché : **« décaler le moniteur du matin après 08:05 »**. **Je ne l'ai pas fait**, parce
qu'en mesurant la durée réelle de la descente j'ai trouvé que ça **ne résoudrait rien**.

**Ce que j'avais dit** : la copie est prête « vers 07:58 ». **C'était le bon chiffre d'un seul
jour.** Les 12 dernières descentes :

| jour | début | durée | fin |
|---|---|---|---|
| 13/10 | 07:45 | **18 min** | 08:03 |
| 12/10 | 08:15 | **50 min** | 09:04 |
| 11/10 | 08:15 | 33 min | 08:48 |
| 10/10 | 08:15 | 41 min | 08:56 |
| 09/10 | 08:15 | 39 min | 08:53 |
| **08/10** | 08:15 | **64 min** | **09:19** |
| 07 → 03/10 | 08:15 | 30 à 36 min | ≈ 08:45 → 08:50 |

Avec un départ à 07:45, la copie est prête **entre 08:03 et 08:49** selon le jour. **08:05 ne
suffit donc pas** : sur 11 de ces 12 jours la descente tournait encore.

**Et le fond du problème est géométrique.** La fenêtre dangereuse va du moment où le run
réécrit nos tables *(≈ 06:49)* jusqu'au moment où la copie est prête *(08:03 → 08:49)* : elle
fait donc **de 1 h 14 à 2 h**. Or le moniteur a **un seul déclencheur**, qui se **répète toutes
les 2 h** *(départ 17:48:54, donc …:48:54)*.

> **Une cadence de 2 h et une fenêtre de 2 h : quel que soit le décalage, un passage tombe
> dedans.** Le mettre à 08:20 → dedans la plupart des jours. Le mettre à 09:20 → le passage
> **précédent** tombe à 07:20, dedans aussi. **Le décalage déplace le problème, il ne l'enlève
> pas** — et il bougerait les **12** passages de la journée, pas seulement celui du matin.

**Ce qui marche, et qui est fait** : les deux sentinelles **savent maintenant qu'elles ne savent
pas**. C'est vrai à 07:48 comme à 08:20, et même le jour où la descente prendra 90 minutes.

### ❓ Si tu veux quand même fermer la cause à la source — à toi de trancher

| | ce que ça fait | ce que ça coûte |
|---|---|---|
| **1. ne rien toucher** *(ma recommandation)* | le code gère déjà le cas, quelle que soit la durée | rien |
| **2. descendre les 2 doublures EN PREMIER** | `app_mandat__sb` *(97ᵉ sur 110)* et `app_contact_search_current__sb` seraient prêtes vers **07:46**, avant le passage de 07:48 | on touche à **la descente**, donc au run : c'est un geste sérieux, et il faut ton go |
| **3. passer le moniteur à toutes les 3 h** | la cadence ne colle plus à la fenêtre | on perd un tiers des passages, pour un bénéfice que le code apporte déjà |

**Je n'ai rien choisi, et je n'ai touché à aucune tâche planifiée.**
