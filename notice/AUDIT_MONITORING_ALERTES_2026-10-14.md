# AUDIT GLOBAL DU MONITORING — LES ALERTES — 14/10/2026

*Demandé par Frédéric : « il y a aussi le monitoring, fais un audit global à ce sujet, les
alertes de mon monitoring actuel ».*

**Lecture seule.** Source : les **361 journaux** du moniteur *(`monitoring/logs/`)*, du **14/09
au 14/10** — un mois — plus le code et la base.

---

## 0. ⛔ D'ABORD : J'ANNULE L'OPTION « A » QUE TU VIENS DE CHOISIR

Tu as répondu **« a »** à : *« le moniteur lit ton clic « Résolu » et n'envoie plus d'e-mail pour
cette alerte »*. **En mesurant pour le coder, j'ai trouvé que ça n'enlèverait AUCUN e-mail.**
Je ne l'ai donc pas codé, et voici la démonstration.

L'e-mail ne part **que** sur une **bascule** *(`check_gti_health.py`, l. 3157)* :

```python
newly_critical = [r for r in criticals if previous_status.get(r.status_key) != "critical"]
```

> Traduit : **un e-mail part seulement quand une alerte PASSE au rouge**, pas tant qu'elle y reste.

Donc une alerte que tu as marquée « Résolu » et qui **reste** rouge **ne t'écrit déjà plus**.
Et si elle repasse au **vert** puis au rouge, c'est **un nouveau problème** — ton ancien clic est
périmé, et il serait **dangereux** de s'en servir pour se taire.

➡ **Il n'y a aucun cas où « A » aurait supprimé un e-mail sans cacher une vraie reprise.**

*C'est l'audit qui a sauvé la mise : j'avais proposé « A » avant d'avoir mesuré la mécanique
d'envoi.*

---

## 1. COMBIEN D'E-MAILS, ET POUR QUOI

**33 bascules en un mois**, soit **environ 1 par jour**.

| cause | bascules | part |
|---|---|---|
| **les TÂCHES PLANIFIÉES** *(`scheduledtasks` + ses 3 déclinaisons)* | **16** | **48 %** |
| **`monitor.summary`** — ⚠ *le **résumé**, compté comme une alerte* | **7** | **21 %** |
| les **4 sentinelles de la famille** *(mandat_un_numero ×2, mandat_disparu, …)* | 3 | 9 % |
| `data.travaux_en_erreur` | 2 | 6 % |
| contacts *(conflit, push bloqué)* | 2 | 6 % |
| workers, wal_size, divers | 3 | 9 % |

⭐ **Deux causes font 69 % de tes e-mails : les tâches planifiées, et un résumé qui se compte
lui-même.**

---

## 2. LES TÂCHES PLANIFIÉES — *la moitié des e-mails, et ça va mieux*

Le message est toujours le même : **« dernier résultat 1 »** — la tâche Windows a rendu un code
d'échec. **Ce ne sont donc PAS de fausses alertes.** Jour par jour :

| tâche | jours en échec *(sur 31)* | derniers échecs |
|---|---|---|
| **GTI Descente** | **8** | 15/09 · 28-29/09 · 01-02/10 · **08-09-10/10** |
| GTI Recherches Actives | 4 | 19-20/09 · 26-27/09 |
| GTI Quotidien | 4 | 17-18-19/09 · 03/10 |
| GTI Relances Email | 2 | 22/09 · 12/10 |

✅ **Et la tendance est bonne : plus aucun échec de tâche planifiée depuis le 12/10.**

⭐ **Le remède était déjà écrit dans le projet, et il a été posé.** Le commentaire de
`TASK_CRITICALITY` dit, depuis le 08/09 : *« si le bruit devient gênant, le remède n'est PAS de
repasser en warning — c'est un réessai par table dans `pull_from_supabase.py` »*. Ce réessai
existe, et il a été **renforcé deux fois** *(15/09 pour les coupures 520-524, 01/10 pour les
réponses tronquées qui se déguisent en succès)*.
**Il n'y a donc rien à faire ici : on voit le résultat d'un correctif qui marche.**

---

## 3. ⚠ `monitor.summary` DOUBLE CHAQUE E-MAIL

C'est le **résumé** du passage : *« GTI monitor summary: 1 critical, 8 warning »*.
Il est **compté comme une alerte à part entière**, donc il bascule **avec** les autres :
**7 e-mails sur 33 (21 %)**.

Et il est **rouge ou orange aux 318 passages sur 318** — **jamais vert en un mois**.

---

## 4. ⚠ TROIS SONDES N'ONT JAMAIS ÉTÉ VERTES EN UN MOIS

*(mesure fiable : ces trois-là s'écrivent à **chaque** passage)*

| sonde | état | valeur | seuil |
|---|---|---|---|
| `data.notif_non_lues` | **318/318 en alerte** | **1 601** | 300 |
| `data.notif_orphelines` | **318/318 en alerte** | **166** | 20 |
| `monitor.summary` | **318/318 en alerte** | *(résumé)* | — |
| `data.ecart_statut_regle` | 309/318 *(97 %)* | 6 | 4 |

> **Une sonde qui n'est jamais verte n'est pas une alerte : c'est un réglage, ou un problème
> jamais traité.** Elles ne t'envoient **aucun** e-mail *(elles ne basculent pas, elles sont déjà
> rouges)* — mais elles **remplissent ta ligne de résumé en permanence**, et c'est ce qui donne
> l'impression que « tout sonne ».

---

## 5. LE BRUIT DE FOND D'AUJOURD'HUI *(passage de 09:48, 71 sondes)*

**61 vertes.** 2 rouges · 8 orange — et tu les connais toutes :

| | |
|---|---|
| 🔴 `data.travaux_en_erreur` | **2** · les deux sont sans conséquence *(voir la note de la sentinelle)* |
| 🔴 `monitor.summary` | le résumé lui-même |
| 🟠 8 avertissements | notifications, orphelins de recherche, écarts de statut, gestes abandonnés |

---

## 6. ⚠ LES AUTRES TROUS, MESURÉS

1. ⚠ **43 journaux sur 361 sont illisibles** *(`JSONDecodeError`, répartis du 15/09 au 14/10)*.
   **Mon audit a donc un trou de 12 %** — je le dis plutôt que de conclure dessus. *C'est
   d'ailleurs pour ça que j'ai manqué la bascule de `relation_disparue` ce matin à 05:48.*
   **Cause probable** : l'en-tête est écrit en UTF-16 et la sortie de Python est recopiée dedans
   — un encodage mixte, déjà signalé dans `run_gti_health.ps1` le 27/08. **Non diagnostiqué.**
2. ⚠ **UN SEUL CANAL** : `WHATSAPP_ALERT_WEBHOOK` n'a **jamais** été posé *(mesuré : « whatsapp
   ignoré » à chaque envoi)*. Et le **repli SMTP est mort** *(« Connection unexpectedly
   closed », 09 et 10/10)* — tout passe par la clé Workspace depuis le 10/10.
   **Si cette clé tombe, tu ne reçois plus rien.**
3. ⚠ **Le bouton « Résolu » de l'écran Santé ne sert à rien** pour le moniteur : mesuré,
   `app_alert_state` apparaît **0 fois** dans `check_gti_health.py`. Tu cliques dessus depuis le
   **24/08** — `notif_orphelines`, `notif_non_lues`, `console.jobs.errors`, `geste_abandonne`,
   et `travaux_en_erreur` ce matin à 08:37 — **et toutes sont revenues**.
   ⭐ La table a même une colonne **`snoozed_until`** *(« se taire jusqu'au… »)* : **vide
   partout**, et le moniteur ne la lit pas non plus.

---

## 7. CE QUE JE RECOMMANDE — *dans cet ordre, et rien n'est décidé*

| | ce que ça change | effort |
|---|---|---|
| **1** ⭐⭐ | **`monitor.summary` cesse d'être une alerte** *(c'est un résumé)* → **−21 % d'e-mails**, et **rien n'est caché** : les vraies alertes partent toujours | ≈ 30 min |
| **2** ⭐ | **Dire la vérité dans l'écran Santé** : soit brancher `snoozed_until` *(« Résolu » = silence 7 jours)*, soit renommer le bouton en **« Masquer de cet écran »**. Aujourd'hui il ment. | ≈ 1 h |
| **3** | **Les 3 sondes jamais vertes** : décider, pour chacune, si c'est **un seuil à corriger** ou **un travail à faire** *(1 601 notifications non lues, 166 sans destinataire)*. **Ce sont tes chiffres, pas les miens** — je ne peux pas trancher. | à discuter |
| **4** | **Les 43 journaux illisibles** : diagnostiquer l'encodage, pour que le monitoring soit mesurable | ≈ 1 h |
| **5** | **Le second canal** *(WhatsApp)*, pour ne pas dépendre d'une seule clé | à décider |

### ⛔ Ce que je ne recommande PAS

- **Baisser les seuils ou passer des rouges en orange** pour faire taire. Le projet a déjà
  tranché deux fois contre *(commentaires de `TASK_CRITICALITY`)*, et la mesure lui donne
  raison : **les alertes des tâches planifiées étaient vraies**, et elles ont cessé quand le
  défaut a été réparé.
- **L'option « A »** — voir la section 0.

---

## 8. CE QUI EST DÉJÀ FAIT CES DEUX DERNIERS JOURS

| | |
|---|---|
| **4 sentinelles de la famille** *(elles criaient sur une copie en retard)* | ✅ corrigées les 13 et 14/10 — **26 épreuves** |
| **`data.travaux_en_erreur` écoute le bandeau du bien** | ✅ 14/10 — **mais pas le bouton de l'écran Santé**, qui est celui que Frédéric utilise |
| **les tâches planifiées** | ✅ réessai par table posé *(15/09, 01/10)* — **plus aucun échec depuis le 12/10** |

---

## 9. ⚠⚠ CORRECTION DE MON PROPRE AUDIT — *« 33 e-mails » était faux : il y en a **14***

En codant le point 1, j'ai **rejoué tout le mois** à travers l'ancien et le nouveau code
*(318 journaux lisibles)*. Résultat :

| | |
|---|---|
| e-mails partis **avant** le correctif | **14** |
| e-mails qui partiraient **après** | **14** |
| **gain** | **ZÉRO** |

### Mon erreur

J'ai compté **33 bascules** vers le rouge et j'en ai déduit **33 e-mails**, puis **7 bascules de
`monitor.summary`** → **« −21 % »**. C'est faux : `dispatch(newly_critical)` envoie **UNE**
liste, donc **toutes les bascules d'un même passage partent dans un seul e-mail**.

Et le résumé **n'a jamais basculé seul** : aux 7 passages concernés, il accompagnait une vraie
alerte *(une tâche planifiée, `wal_size`, `travaux_en_erreur`…)*. **L'e-mail partait de toute
façon.**

### Ce que le correctif apporte réellement

**Pas moins d'e-mails — des e-mails plus propres.** Sur 7 des 14 envois du mois, la liste
contenait une ligne qui ne disait rien de neuf :

```
AVANT : scheduledtasks:gti_descente, scheduledtasks, monitor.summary
APRES : scheduledtasks:gti_descente, scheduledtasks
```

**Je le garde** : c'est juste *(un résumé n'est pas une alerte)*, c'est éprouvé **8 fois sur 8**,
et le témoin inverse montre qu'**aucune vraie alerte n'est perdue** — y compris le message de
rétablissement, qui reste identique. **Mais le bénéfice est de lisibilité, pas de volume, et
j'avais annoncé l'inverse.**

### ⭐ Et ça change l'ordre des priorités

**14 e-mails en un mois, soit un tous les deux jours.** Ce n'est pas un monitoring qui hurle.
➡ **Le vrai problème n'est donc pas le NOMBRE d'e-mails, c'est que CHAQUE e-mail est illisible** :
il porte *« 1 critical, 8 warning »*, dont **3 avertissements qui n'ont jamais été verts en un
mois**.

**Nouvel ordre recommandé :**

| | | pourquoi |
|---|---|---|
| **1** ⭐⭐ | **les 3 sondes jamais vertes** *(§ 4)* | c'est **elles** qui rendent chaque e-mail illisible. Pour chacune : seuil à corriger **ou** travail à faire. **Ce sont les chiffres de Frédéric — 1 601 notifications non lues — je ne peux pas trancher** |
| **2** ⭐ | **l'écran Santé dit la vérité** *(§ 6-3)* | le bouton « Résolu » mentait depuis le 24/08 |
| **3** | les 43 journaux illisibles | le monitoring doit être mesurable — **ce trou m'a déjà fait manquer une alerte et sous-estimer un chiffre** |
| **4** | le second canal | une seule clé tient tout |
| ~~0~~ | ~~le résumé~~ | **fait**, mais gain **0 e-mail** — seulement 7 e-mails plus propres |

### ⭐ La leçon, et c'est la troisième de la journée

**J'ai présenté un gain chiffré AVANT de l'avoir mesuré.** Le chiffre semblait solide — il venait
d'un comptage réel — mais il comptait **la mauvaise unité** : des *bascules* au lieu des *envois*.
➡ **Un pourcentage annoncé doit être mesuré SUR LE GESTE FINAL** *(ici : l'e-mail qui part)*,
jamais sur un intermédiaire qui lui ressemble. C'est la même famille que « mesurer le geste de
l'écran, pas un geste plausible » *(leçon 1)*.

---

## 10. LES TROIS SONDES JAMAIS VERTES — *décisions de Frédéric : « 1a, 2a, 3a »*

### ① et ② — FAIT, mais **pas** avec un seuil

Sa consigne : *« c'est normal, personne ne les lit, monte le seuil »*. **La mesure a dit qu'un
seuil ne tiendrait pas.**

| sonde | il y a un mois | aujourd'hui | vitesse |
|---|---|---|---|
| `data.notif_non_lues` | **1 110** | **1 601** | **+15,8 / jour** |
| `data.notif_orphelines` | **81** | **166** | **+2,7 / jour** |

> ⚠ **Un seuil absolu sur un compteur qui ne fait que croître est une alarme à retardement.**
> À +15,8 par jour, un seuil posé à 2 000 serait franchi **dans 25 jours**, et on y reviendrait.

**La bonne forme existait déjà dans le fichier** : `rule: "growth"`. On ne surveille plus le
**total** *(que Frédéric assume)* mais **l'emballement** — « est-ce que ça double d'un coup ? ».
C'est ce qui dirait qu'un robot s'est mis à fabriquer des notifications.

**Réglages calés sur la mesure, pas choisis au hasard :**

| | croissance normale | il faut, pour sonner |
|---|---|---|
| non lues | ~ **+1,3** par passage *(2 h)* sur 1 601 | **+10 % ET +100** d'un coup |
| sans destinataire | ~ **+0,23** par passage sur 166 | **+15 % ET +20** d'un coup |

*`growth_abs` évite qu'un petit nombre sonne sur un pourcentage : de 2 à 3, c'est +50 %, et ça
ne veut rien dire.*

⚠ **LE PRIX, ASSUMÉ ET DIT** : une dérive **lente** ne sonnera plus jamais — le point de
comparaison avance avec elle. **Le total reste visible dans l'écran Santé**, et c'est là qu'il
faudra le regarder.

**Éprouvé 10 fois sur 10** *(`monitoring/test_notifications_emballement.py`)*, dont les deux
chiffres d'aujourd'hui → **vert**, l'emballement → **sonne**, la baisse → vert, et le garde-fou
du petit nombre. **Témoin inverse** : les mêmes chiffres avec l'ancien réglage → `warning` ;
avec le nouveau → `ok`. **Les deux basculent.**

---

### ③ — ⛔ JE N'AI PAS MONTÉ LE SEUIL, ET VOICI POURQUOI

Sa consigne était *« 3a »* = monter le seuil de `data.ecart_statut_regle` de 4 à 6.
**Le projet avait déjà tranché contre, et il avait écrit pourquoi** *(`check_gti_health.py`,
l. 407-412)* :

> *« SEUIL 4, ET NON 0. Au 01/09 il y a exactement quatre écarts, et les quatre sont des
> **REMONTÉES** que la borne 2 bloque — ce sont de vraies incohérences du côté Hektor […].
> **Un CINQUIÈME écart, lui, veut dire que quelque chose a bougé : c'est celui-là qu'on veut
> voir.** »*

**Il y en a six.** Et j'ai regardé lesquels :

| n° de dossier | Hektor dit | la règle dit | sens |
|---|---|---|---|
| 18594 | Actif | Sous offre | remontée |
| 18865 | Actif | Sous offre | remontée |
| VM66700 | Actif | Sous compromis | remontée |
| VS046 | Sous offre | Sous compromis | remontée |
| **VT9437** | Sous offre | **Actif** | **redescente** |
| **⚠ *(vide)*** | Sous offre | **Actif** | **redescente** |

⭐⭐ **Les quatre écarts tolérés en septembre étaient des REMONTÉES. Les deux nouveaux sont des
REDESCENTES** — une **autre famille**, que le seuil 4 ne couvrait pas. C'est **exactement** le
« cinquième écart » que la sonde devait signaler.

⚠⚠ **Et le sixième n'a PAS de numéro de dossier.** *« Un numéro ne se perd jamais »* est l'une
des **cinq règles du projet**, et c'était déjà la cause du **défaut 5a** du chantier ③ *(les
désarchivages posaient `app_dossier_id = NULL` alors que le vrai numéro existait)*.

> **Monter le seuil à 6 avalerait ces deux lignes sans que personne ne les regarde jamais.**

#### ❓ Trois sorties — à trancher

| | |
|---|---|
| **A** | monter quand même le seuil à 6 *(ou 7)* — **les 2 redescentes disparaissent du radar** |
| **B** ⭐ | **regarder les 2 redescentes** *(c'est 2 lignes, ~15 min)*, corriger, et le seuil 4 redevient juste |
| **C** ⭐ | **changer la règle plutôt que le seuil** : tolérer les **remontées** *(la famille jugée acceptable en septembre)* et sonner sur **toute redescente**. Plus durable que n'importe quel chiffre |

**Je recommande C, et B tout de suite** *(la ligne sans numéro mérite un regard dans tous les
cas)*. **Je n'ai rien décidé.**

---

## 11. ⚠ CORRECTION : « le bouton Résolu ne sert à rien » ÉTAIT TROP FORT

*Question de Frédéric après le déploiement : « maintenant le bouton Corrigé fonctionne ? »*
**Réponse mesurée : il fonctionnait DÉJÀ — pour l'écran. Et il a un autre défaut, plus grave.**

### Ce qu'il fait vraiment

`alerts_governed`, la vue que l'écran Santé lit, contient en ce moment :

| | nombre |
|---|---|
| `new` / **info** | **1 601** ← *une ligne par notification non lue* |
| `new` / warning | **8** ← *les 8 avertissements affichés* |
| **`resolved`** / warning | **4** |
| **`resolved`** / critical | **2** ← *ses deux clics du 14/10 à 08:37* |

Et l'écran filtre : `alertsToTreat` ne garde que `warning` **et** `critical`, en excluant
`resolved`, `ignored` et `snoozed` *(`SanteSystemeScreen.tsx`, l. 160-168)*.

➡ **Ses deux clics de ce matin ont marché** : les deux alertes rouges ont bien disparu de
« Alertes à traiter ». **J'avais tort de dire que le bouton ne servait à rien.**

**Ce qu'il ne fait pas** *(et c'est délibéré, cf. § 0)* : il n'enlève **aucun e-mail**, puisque
l'e-mail ne part que sur une bascule.

### ⚠⚠ MAIS LE VRAI DÉFAUT EST AILLEURS : « Résolu » EST DÉFINITIF

`app_alert_state` garde `resolved` **pour toujours**, par `alert_key`. Donc :

| cliqué « Résolu » le | n'apparaîtra **plus jamais** dans « Alertes à traiter » |
|---|---|
| 24/08 | `scheduledtasks`, `scheduledtasks:gti_recherches_actives`, `workers.heartbeat:console.worker.documents` |
| 01/09 | `data.geste_abandonne` |
| 03/09 | `data.notif_non_lues`, `data.notif_orphelines`, `console.jobs.errors` |
| **14/10** | `data.travaux_en_erreur`, `monitor.summary` |

> **Même si l'une d'elles empire, elle ne reviendra pas dans la liste.** Un clic vaut
> extinction définitive sur cet écran.

⭐ **Et c'est exactement pour ça que la colonne `snoozed_until` existe** — *« se taire
jusqu'au… »*. Elle est **vide partout**, et le bouton ne l'utilise pas. Le mécanisme sûr a été
prévu puis jamais branché.

### ⭐ Un défaut de poids, trouvé en passant

L'écran Santé charge **1 615 lignes, soit ~285 Ko**, à chaque ouverture — parce que **chacune
des 1 601 notifications non lues est une ligne d'alerte** dans `alerts_governed`. Elles ne sont
même pas affichées *(elles sont seulement comptées)*. **Non corrigé, pas demandé.**

### ❓ La suite, à trancher

| | |
|---|---|
| **A** ⭐ | **brancher `snoozed_until`** : « Résolu » = silence **7 jours**, puis l'alerte revient si le problème est toujours là. Plus de silence définitif, et le mécanisme existe déjà en base |
| **B** | **ajouter un bouton « Réveiller »** à côté, pour annuler un « Résolu » devenu faux |
| **C** | ne rien changer, en sachant que les 9 alertes ci-dessus sont éteintes **pour de bon** |

**Je recommande A.** Rien n'est décidé.

---

## 12. L'ÉCRAN SANTÉ — *« c'est un sapin de Noël »* (Frédéric, 14/10)

**Je l'ai regardé dans son Chrome**, connecté avec sa session. Il avait raison, et **ce n'est pas
la couleur le problème** :

| ce que l'écran affiche | |
|---|---|
| **71 lignes** à plat, toutes au même niveau visuel | il faut **4 écrans** pour arriver en bas |
| **61 sont vertes** | dont **21 disent littéralement « 0 (seuil 0) »** |
| les **10 qui comptent** | affichées **DEUX FOIS** — en haut dans « Alertes à traiter », puis **à nouveau** dans la liste du bas |

### Trois défauts vus à l'écran

1. ⚠ **Chaque ligne s'appelle « sentinel » ou « absolute »** — en gras, comme un titre. C'est le
   **type de règle**, pas un nom. Le vrai libellé est en dessous, en plus petit. **71 fois.**
2. ⚠ **Deux chiffres se contredisent en haut** : « Alertes à traiter **7** » et
   « À SURVEILLER **8** » — une alerte marquée « Résolu » sort de la liste mais **reste comptée**.
3. ⚠ **« il y a 2 h » partout** : l'écran montrait le relevé de 09:48 à 11:24. Le bouton
   « Rafraîchir » **relit la base**, il ne relance pas le moniteur.

### FAIT — *décision de Frédéric : « A »*

**On ne montre plus que ce qui ne va pas.** Les lignes vertes sont repliées derrière **une seule
ligne** — *« 61 contrôles au vert »* — qui se **déplie d'un clic**.
⭐ **Rien n'est supprimé** : tout reste consultable, c'est du bruit qu'on range, pas de
l'information qu'on cache. `npm run build` **vert**.

➡ **L'écran passe de 71 lignes à 10.** *(Et le mot « sentinel » de 71 occurrences à 10 — le
défaut 1 se résorbe de lui-même sans qu'on y touche.)*

### ⬜ Ce qui reste, non fait et non décidé

Les défauts **2** *(les deux chiffres qui se contredisent)* et **3** *(le libellé « sentinel »,
la date trompeuse)*, et le **doublon haut/bas**. **Frédéric a choisi A, pas C** — je n'ai pas
élargi.

### ✅ CONTROLE EN PRODUCTION, dans son Chrome *(14/10, après son push)*

| | |
|---|---|
| **replié** *(par défaut)* | **10 lignes**, puis une seule ligne : ● **60 contrôles au vert** · *Afficher* |
| **déplié** *(un clic)* | tout revient — rien n'est perdu |

Le groupe **« Infrastructure & workers » a entièrement disparu** : ses 24 contrôles étaient tous
au vert. Restent « Qualité des données » *(8)* et « Métier » *(1)*.

⚠ **ET LE DOUBLON SAUTE MAINTENANT AUX YEUX.** Avec 61 lignes de bruit en moins, on voit que
« Notifications non lues: 1601 » est affiché **deux fois à dix lignes d'écart** — une fois dans
« Alertes à traiter », une fois dans « Qualité des données ». C'était invisible avant, c'est
criant maintenant. **Non corrigé : Frédéric a choisi A, pas C.**

### ⚠ Et la réponse à sa question : « pourquoi tes corrections ne sont pas en ligne ? »

**Ce n'est pas un déploiement.** Le moniteur est un **script sur son serveur**, pas une app en
ligne : le fichier était déjà modifié *(11:13)*, mais **sa dernière exécution datait de 09:48**.
L'écran montrait donc l'ancien résultat. Calculé à l'avance, en lecture seule :

```
CE QUE LE PASSAGE DE 11:48 DIRA
  VERT    Notifications non lues: 1601 (prec. 1601)
  VERT    Notifications sans destinataire: 166 (prec. 166)
  ROUGE   Travaux console en erreur: 2 (seuil 0)
```

➡ **Les deux notifications passent au vert.** Le rouge reste, et c'est normal : il attend le clic
**« J'ai refait » dans la fiche du bien** — pas celui de l'écran Santé.
