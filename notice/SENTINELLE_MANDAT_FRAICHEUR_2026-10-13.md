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

> ✅ **TRANCHÉ : OPTION 1 — on ne touche à rien** *(Frédéric, 13/10)*. Le code gère le cas,
> quelle que soit la durée de la descente. **Aucune tâche planifiée n'a été modifiée, et il n'y
> a rien à faire plus tard** : la question est fermée, pas reportée.
>
> ✅ Le **3ᵉ cas** a été confié ensuite et traité — **option B** — voir la section 11.

---

## 11. LE 3ᵉ CAS — *la mesure a renversé le diagnostic : il y avait DEUX défauts*

J'avais signalé « un faux vert à 01:48 ». En mesurant, j'ai trouvé que ce n'était pas le plus
grave.

### Ce que 10 nuits de journaux du moniteur disent *(`monitoring/logs/`, 120 fichiers lus)*

| passage | `data.doublure_journal` | juste ? |
|---|---|---|
| **01:48** | **« à jour » — 10 fois sur 10** | ❌ **faux** : le relevé est de la veille |
| 03:48 | avertissement — 10/10 | techniquement vrai… |
| 05:48 | avertissement — 10/10 | …mais |
| 07:48 | avertissement — 10/10 | **c'est l'état normal** |
| 09:48 → 23:48 | « à jour » | ✅ |

⭐ **La preuve du défaut d'horloge tient en une ligne** : 01:48 et 03:48 lisent **exactement les
mêmes données** et disent l'inverse. Seul le changement de date **UTC** à 02:00 l'explique —
`releve_le` est écrit en date **locale** *(`comparer_doublures.py` l. 224, `time.strftime`)* et
était comparé à `datetime.now(timezone.utc)`.

⭐⭐ **Mais le second défaut est le vrai.** J'ai trouvé **qui écrit ce relevé** :
`scheduled/run_descente.ps1`, étape **2 sur 3**, donc **juste après la Descente** — entre
**08:03 et 08:49**. Demander « le relevé est-il d'aujourd'hui ? » avant 08:30 **ne peut jamais
être vrai** : la sonde posait **3 avertissements par nuit sur un état parfaitement normal**.
**Le même mal que les deux autres sentinelles**, corrigées le même jour.

*Et un fait écrit dans le fichier lui-même (l. 66-68) : **seuls les rouges envoient un e-mail**.
Ces avertissements n'ont jamais réveillé personne — ils remplissaient la ligne « 8 warning »,
dont celle de l'e-mail du 13/10 au matin.*

### Le remède choisi — **option B**, et c'est le même patron que les deux autres

**On ne devine pas avec une heure écrite en dur : on lit la fraîcheur réelle.**

> • relevé **du jour** → « à jour »
> • relevé de la veille **et la Descente du jour n'a pas encore tourné** → « **NORMAL** », on se tait
> • la **Descente a tourné** mais le relevé n'a pas suivi → **avertissement** ← *la vraie panne*
> • fraîcheur inconnue *(pas de `sb_pull_state`)* → on ne devine pas, on avertit comme avant

**La panne est détectée le jour même, au passage de 09:48**, et **aucune heure n'est écrite en
dur** : même le jour où la Descente durera trois heures, la sonde restera juste.

⚠ **Et ce n'est pas un angle mort** : si la **Descente elle-même** ne tourne pas,
`TASK_CRITICALITY["GTI Descente"] = "critical"` le dit déjà, **en rouge**. Vérifié avant de
rendre la main.

### Éprouvé — 6 cas de plus, **horloge figée**

Le cas de 01:48 n'arrive **qu'une fois par nuit**, et on ne change pas l'heure de la machine :
l'épreuve **fige l'heure que la sonde croit être** *(`_horloge_figee`)*. Les 6 cas : 09:48 normal ·
01:48 relevé de la veille · 07:48 idem · **la vraie panne** · relevé d'avant-hier · fraîcheur
inconnue. **14 épreuves au total dans ce fichier, 14 vertes.**

⭐ **TÉMOIN INVERSE, et il était indispensable** : à 01:48 le nouveau code rend **le même
statut** que l'ancien *(`ok`)* — un test naif n'aurait donc **rien prouvé**. J'ai exécuté
**l'ancien code pris dans le commit précédent** *(`git show HEAD:`)* et comparé :

| | avant | après | |
|---|---|---|---|
| **01:48**, relevé de la veille | « à jour » | « de la veille — **NORMAL** » | ✅ **bascule** |
| **07:48**, relevé de la veille | avertissement | « NORMAL » | ✅ **bascule** |
| **09:48**, Descente faite, relevé non | avertissement | avertissement | ✅ **identique, et c'est voulu** |

### Contrôle sur le vrai état, en lecture seule

```
[ok] data.doublure_journal   Releve des doublures a jour : 10 doublures, 49 app seule
     dernier_releve             '2026-10-13'
     descente_la_plus_recente   '2026-10-13T07:45:03'
     descente_du_jour           True
```

### Ce que ça change pour toi

- **4 bruits de moins par nuit** *(1 faux vert + 3 avertissements inutiles)*.
- **Un avertissement de moins** dans le résumé de l'e-mail du matin.
- Une panne du relevé est maintenant **dite le jour même**, alors qu'avant elle se **noyait**
  dans trois avertissements quotidiens identiques.


---

# ⚠ LA **QUATRIÈME** DE LA FAMILLE — `data.relation_disparue` (14/10, 05:51)

**L'alerte reçue par Frédéric :**
> `[data.relation_disparue]` **Liens de la couche absents du registre : 1 sur 132 769 (seuil 0)
> — l'étape de nuit ne passe plus** · 2026-10-14T03:51:11 UTC

## C'EST UNE FAUSSE ALERTE, ET POUR LA MÊME RAISON QUE LES TROIS AUTRES

| | heure (UTC) | heure locale |
|---|---|---|
| **l'alerte** | **03:51:11** | **05:51** |
| l'étape « registre des liens (app_relation) » *(journal du run)* | **04:52:49 → 04:53:30** | **06:52:49 → 06:53:30** |

➡ **Le moniteur a mesuré 1 h 01 AVANT que l'étape ne reconstruise le registre.** Il comparait
une couche **déjà rafraîchie cette nuit** à un registre **de la veille**.
⚠ Et le message est le plus trompeur de la famille : *« l'étape de nuit ne passe plus »* —
alors qu'elle passait **une heure plus tard, et avec succès** *(`DONE`, 41 s)*.

## LA PREUVE, MESURÉE APRÈS LE PASSAGE DE L'ÉTAPE
La même formule, rejouée à 07:20 en lecture seule *(`phase2/checks/relation_disparue.py`)* :

| garde | valeur |
|---|---|
| `source_absents` | **0** |
| `doublons` · `hors_plage_app` · `plage_envahie` | **0** |
| `retraits_perdus` · `doublure_perimee` · `registre_sans_mandant` | **0** |
| **`graves`** | **0** |
| `source_lus` | **132 736** *(contre 132 769 dans l'alerte : la couche bougeait pendant la mesure)* |
| `doublure_du` | **2026-10-14T06:51:46** |

## ⭐ ET LA SENTINELLE A DÉJÀ TOUT CE QU'IL FAUT POUR SE TAIRE

| | UTC |
|---|---|
| **la couche** `app_contact_relation_current.refreshed_at` *(max)* | **04:46:13** |
| **le registre** `app_relation.last_seen_at` *(max)* | **04:52:49** |

**La règle est limpide : le registre doit être AU MOINS aussi frais que la couche.**
À 03:51 il datait de la veille et la couche du jour → **la mesure n'était pas concluante**.
Maintenant le registre est **postérieur** à la couche → elle l'est, et elle dit **0**.

⭐ **C'est exactement le correctif appliqué aux trois autres le 13/10** : *« elle lit maintenant
la fraîcheur réelle des deux côtés »*.

## ⚠ LE PIÈGE À NE PAS REFAIRE
Les deux dates ne s'écrivent **pas** de la même façon :
`refreshed_at` → `2026-10-14T04:46:13+00:00` · `last_seen_at` *(couche)* → `2026-10-14T04:27:59Z`
➡ **comparer les CHAÎNES marcherait par chance** *(`+` < `Z`)*. Il faut **analyser les dates**,
pas les textes — leçon déjà payée le 13/10 *(UTC contre locale, deux heures d'erreur)*.

## CE QUE JE PROPOSE *(non codé, en attente du « vas-y »)*
`source_absents` ne devient **critique** que si le registre est **au moins aussi frais** que la
couche. Sinon : **« NON CONCLUANT »** *(warning)*, comme ses trois sœurs. Le vrai rouge — un
lien perdu alors que le registre est à jour — **reste intact**.

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS
| | |
|---|---|
| **le vrai rouge** | ⛔ **intact** : registre à jour + un lien manquant = toujours `critical` |
| les **7 autres gardes** de cette sentinelle | ⛔ **pas touchées** *(doublons, plages, retraits, doublure périmée, registre sans mandant)* |
| ⚠ **le risque réel du correctif** | **masquer une panne durable** : si l'étape des liens ne tournait **plus du tout**, le registre resterait vieux et la sentinelle dirait « non concluant » **tous les jours**. ➡ il faut donc **un warning qui s'aggrave avec l'âge** *(au-delà de ~26 h sans passage de l'étape, c'est une vraie panne)* — c'est ce que les trois sœurs font déjà |
| le moniteur | ⚠ **une ligne de plus dans `check_gti_health.py`**, aucune autre sonde touchée |
| **décaler le moniteur** | ⛔ **ne marche pas** — déjà tranché le 13/10 : *« la descente dure de 18 à 64 min et la fenêtre fait 2 h, comme la cadence »* |

## ✅ CORRIGÉE (14/10) — ET ELLE VA PLUS LOIN QUE SES TROIS SŒURS

**La nuance est DANS LA FORMULE**, pas dans le moniteur — la règle du 13/10 :
*« si elle vivait dans `check_gti_health.py`, elle serait perdue pour quiconque lance la formule
à la main, et c'est justement ce qu'on fait pour vérifier. »*

| | |
|---|---|
| `phase2/checks/relation_disparue.py` | `_en_utc()` · `_fraicheur_registre()` · le drapeau **`source_non_concluant`** · **`PLAFOND_HEURES = 26`** |
| `monitoring/check_gti_health.py` | **une branche `warning` avant le rouge**, et rien d'autre |

⭐ **CE QU'ELLE FAIT DE PLUS QUE SES SŒURS : LE PLAFOND.** Un registre qui resterait vieux
**plusieurs jours** n'est pas un décalage d'horloge, c'est une panne — et ses sœurs, dans ce cas,
**se tairaient indéfiniment**. Au-delà de **26 h** *(24 h de cycle + 2 h de marge pour un run en
retard)*, on crie, **et le message le dit**. ⚠ **Sans ce plafond, le correctif masquerait
l'avarie qu'il est censé laisser passer.**

⚠ **ET `graves` SUIT.** `main()` rend un code de sortie non nul dès que `graves > 0` : sans
l'ajustement, la sonde serait **rouge en ligne de commande** pendant que le moniteur se tait.
**Deux verdicts différents sur la même mesure, c'est la pire des issues.** Le compte brut reste
lisible dans `source_absents` — on n'efface rien, on refuse seulement de le compter comme
**grave** tant qu'on ne sait pas.

### LES ÉPREUVES — **5 sur 5**, base SQLite **en mémoire**, **la vraie formule** appelée
*(`mesurer()`, celle que le moniteur appelle — aucune écriture sur `phase2.sqlite`)*

| | situation | verdict | attendu |
|---|---|---|---|
| ① | **le cas de ce matin** : registre de la veille *(24 h)* + 1 absent | **NON CONCLUANT** | ✅ |
| ② | **le vrai rouge** : registre à jour + 1 absent | **GRAVE** | ✅ |
| ③ | **la panne durable** : registre vieux de **30 h** + 1 absent | **GRAVE** *(plafond)* | ✅ |
| ④ | rien à signaler : registre à jour, 0 absent | **ok** | ✅ |
| ⑤ | **le piège des fuseaux** : `+00:00`, `Z`, et une date locale | **le même instant** | ✅ |

⚠ **ET LE ④ A ÉCHOUÉ AU PREMIER ESSAI — C'ÉTAIT MON ÉPREUVE, PAS LE CODE.** Je jugeais sur
`graves`, qui **agrège les sept gardes** ; une base en mémoire minimale n'a pas les tables des
autres *(doublure, mandants…)*, donc il portait **du bruit de décor**. On juge désormais sur
**la garde elle-même** — exactement les deux lignes du moniteur.
➡ *Une épreuve qui échoue n'accuse pas toujours le code : il faut d'abord vérifier qu'elle
mesure ce qu'on croit.*

⚠ **`check_gti_health.py` N'A PAS ÉTÉ LANCÉ** : il écrit des alertes et **enverrait un email**.
Les deux fichiers **compilent** *(`py_compile`)*, et la formule a été exécutée seule.

### CE QUI RESTE À VOIR
⏰ **Demain matin à 05:51** : l'email ne doit plus arriver — ou, s'il arrive, dire
**« NON CONCLUANT »** en avertissement, avec les deux dates comparées.
