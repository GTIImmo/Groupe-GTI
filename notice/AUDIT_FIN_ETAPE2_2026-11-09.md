# AUDIT — L'ÉTAPE 2 EST-ELLE FINIE ? — 09/11/2026

*Frédéric (09/11) : « l'étape 2 est finie ? J'ai besoin d'un audit. » Lecture seule : le plan maître, les notes des huit chantiers,
`notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md`, la mémoire du projet, et trois mesures dans Supabase (travaux du worker et comptes).*

> ⚠ **Audit limité** : la grille objet × geste du 08/10 n'est **pas remesurée case par case**. Ses cases rouges étaient le périmètre des
> chantiers ① à ⑦, tous clos ; ce qui n'a pas été remesuré aujourd'hui est dit « non remesuré ». Rien n'est codé, rien n'est écrit en base.

---

## 1. LE VERDICT EN TROIS PHRASES

- **Le travail de CODE prévu pour l'étape 2 est fait.** Les huit chantiers posés le 08/10 sont clos (① à ⑦) ou ne portent plus que des
  décisions (⑧, ligne du plan remise à jour le 09/11).
- **L'étape 2 n'est PAS finie pour autant** : sa définition est « l'app fait tout le travail quotidien », et **aucun commercial ne
  travaille dans l'app** (§2). Le critère de fin du lot L8 — « les négociateurs travaillent dans l'app » — n'est pas rempli.
- **Ce qui reste est d'une autre nature** : la mise en service auprès des négociateurs (des décisions de Frédéric), une liste de
  décisions de ⑧, et quelques défauts ouverts (§4).

---

## 2. LA MESURE QUI DÉCIDE — QUI TRAVAILLE DANS L'APP *(Supabase, 09/11, lecture seule)*

- **Comptes** (`app_user_profile` × `auth.users`) : 5 admins (2 connectés sur 30 jours, 1 sur 7 jours) ; **2 commerciaux, 0 connexion en
  30 jours**.
- **Travaux demandés depuis l'app sur 30 jours** (`app_console_job`, `requested_by` renseigné) : **1 196 travaux, tous par 4 comptes
  admin** (336 sur les 7 derniers jours, 40 types de gestes). **0 travail demandé par un commercial.**
- L'audit du 07/10 disait déjà : « 0 travail demandé par un commercial en 120 jours ». **C'est toujours vrai un mois plus tard.**
- Les gestes, eux, servent et réussissent : statut d'annonce 41 sur 44, création de contact 29 sur 29, photos 23 sur 23, brouillons
  13 sur 15, offres 14 sur 14, documents 9 sur 9.

---

## 3. LES HUIT CHANTIERS *(plan, « 🧭 LES CHANTIERS DE L'ÉTAPE 2 »)*

- ① sécurité — ✅ fini le 08/10.
- ② droits du négociateur — ✅ fini le 12/10 ; **restes reportés par Frédéric** : ce que doit voir exactement un agent commercial, un
  essai réel d'un geste chez Hektor par un négociateur.
- ③ chez nous d'abord — ✅ fini le 14/10 (`CHAMPS_APP_ANNONCE` reste éteint, décision du 13/10 : c'est la coupure qui le rendra utile).
- ④ aucun échec silencieux — ✅ fini le 11/10.
- ⑤ gestes cassés — ✅ fini le 09/10.
- ⑥ ce qui ne redescend pas — ✅ traité les 14-16/10.
- ⑦ gestes qui manquent — ✅ clos le 21/10 (« les deux portes » sorties en chantier à part).
- ⑧ gardé chez nous — 🔧 8a à 8f traités (8e rangé à l'étape 3), 8g devenu le chantier des couples ; **il ne reste que des décisions**.

---

## 4. CE QUI RESTE POUR FINIR L'ÉTAPE 2

**A. La mise en service — des décisions de Frédéric, pas du code**
- Qui utilise l'app, et quand : les 2 comptes commerciaux ne se connectent pas ; les autres négociateurs n'ont pas de compte.
- ② reporté : ce que doit voir un agent commercial ; un essai réel d'un geste par un négociateur.
- Les questions du plan (« Les questions à Frédéric », 07/10) qui concernent l'étape 2 : que peut faire un négociateur seul ; par où
  arrivent les leads ; les négociateurs utilisent-ils les SMS, tâches et envois de fiches de Hektor.

**B. Les décisions de ⑧** *(ligne ⑧ du plan)*
- 9 388 personnes seules à deuxième place vide · 680 coquilles · les doublons (T6) · le RGPD de l'index global · les 633 fiches jamais
  migrées · les 121 241 fiches du compte « accueil » (question à Hektor) · 36 vendeurs + 20 acquéreurs sans notre numéro · les acheteurs
  d'avant le 17/07 (A / B / C) · les 4 mandants à localité perdue.

**C. Des défauts ouverts, trouvés ou relevés aujourd'hui**
- ⚠ **Modifier un mandant : 3 échecs sur 3 le 05/11** (19:40-19:44 UTC), « Formulaire édition contact Hektor introuvable » pour deux
  fiches (115527, 140142). Les 5 précédents (mai → 08/10) avaient réussi. **Cause non cherchée** ; à croiser avec la règle D-5 de la
  session partenaires et la pièce P3 de la session Youtrust, chargées le 09/11 à 12:37.
- Le journal du run perd les sorties Python des dernières étapes depuis le 05/11 (synthèse couples §76, §78).
- 4 bancs d'essai du front en échec, signalés par la session partenaires le 09/11 (ajout d'un conjoint (40)(41), petits défauts point 6
  n° 1, textes bienvu, gênants du front) — **non mesurés sur la version d'avant**.
- La réserve 3 des documents (25/09) : le balayage des documents n'a ni cadence ni arrêt sur un refus 403 — **état actuel non remesuré**.
- Un mandat saisi chez Hektor après coup n'arrivait pas au carnet (le run ne relit le détail que si la date change) — correctif écrit le
  02/11, **sa mise en service n'est pas remesurée ici**.

**D. Les chantiers ouverts à côté, dans leurs propres sessions** *(non audités ici)*
- L'annuaire des partenaires (lots 4 à 7 allumés ; la suite attend Frédéric).
- Le classeur et le suivi d'affaire (spécification de l'annulation, 09/11).
- Le registre des négociateurs (restent la répartition et les droits).
- Hors code : la licence Matterport verrouillée depuis le 03/11.

---

## 5. CE QUI EST ÉTAPE 3, ET NE COMPTE PAS ICI

Le registre électronique des mandats (nos numéros, série), la signature en propre, les passerelles, le site, le DNS, l'e-mail, le bon de
visite fait dans l'app (8e), R5 (l'état d'une transaction chez nous), l'auto-archivage RGPD des recherches (reporté par Frédéric).

---

## 6. NON MESURÉ AUJOURD'HUI

- La grille objet × geste du 08/10, case par case.
- Le volume de travail fait **directement dans Hektor** par les négociateurs (il dirait ce que l'app devrait encore absorber).
- La page de tête `CLAUDE.md` §2 « Ce qui attend Frédéric » date du 19/10 et n'a pas été relue point par point.
