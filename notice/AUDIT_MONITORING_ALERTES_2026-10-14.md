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
