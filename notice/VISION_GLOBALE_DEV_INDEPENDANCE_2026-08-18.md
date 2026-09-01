# Vision globale du développement — de la surcouche au logiciel autonome

**Date : 2026-08-18 — version 2.** Remplace la v1 du même jour.
**VISION — aucun code écrit.** Document maître de ce chantier.

Cible et ordre des travaux **arbitrés par Frédéric le 18/08**, au fil d'une séance d'analyse.
Tous les chiffres ont été mesurés en base ou lus dans le code le même jour.

---

## Pourquoi ce document existe, et pourquoi il a été refait

La v1 décrivait des **étapes**, pas une **cible**. En cours de rédaction j'ai affirmé deux fois
qu'on ne pouvait pas supprimer le calque optimiste parce que 137 champs n'auraient nulle part où
aller. **Vérification faite en base : c'était faux.** Chaque champ a sa case.

Frédéric : *« C'est une vision globale que je veux du dev, et sans cela le dev ne part pas sur de
bonnes bases, non ? »* — exactement. On pose la cible d'abord.

> **Principe directeur, repris de `NOTE_CONCEPTION_PHASE1_APP_AUTORITAIRE_2026-08-17.md` :**
> *« construire l'état FINAL, pas un échafaudage. »*

---

# 1. LA CIBLE

## 1.1 La règle, formulée par Frédéric

> ### On n'attend Hektor que si on a besoin de ce que Hektor produit.
> Tout le reste part en arrière-plan, et l'utilisateur ne le voit jamais.

Hektor ne produit que **trois** choses que l'app n'a pas :

| Ce que Hektor produit | Remplacé plus tard par |
|---|---|
| Le **numéro de mandat** | le registre de mandats en propre |
| La **signature** | Yousign en direct |
| La **publication sur les portails** | passerelles en direct, ou diffuseur |

**Tout le reste** — créer un bien, un contact, un mandant, le rattacher, modifier n'importe quel
champ, changer un statut, archiver, restaurer, supprimer, réaffecter, envoyer un document ou une
photo — ne dépend d'**aucun** retour de Hektor. L'app le fait chez elle et prévient Hektor après.

## 1.2 Les quatre propriétés de la cible

**① Écrire, c'est écrire.**
Le champ modifié va dans sa case définitive. Pas de calque, pas de valeur provisoire, pas de
priorité de lecture. Une seule valeur par champ, un seul endroit où la lire.

**② L'identité appartient à l'app.**
Chaque fiche reçoit son identifiant à sa création. Les identifiants Hektor deviennent des **cases
qui se remplissent en arrière-plan**, et qui disparaissent à la coupure.

**③ Aucun job n'est attendu.**
L'utilisateur agit, c'est enregistré, c'est affiché. L'ouvrier travaille derrière. Les seules
attentes visibles sont les trois du tableau ci-dessus — et elles sont légitimes.

**④ Le run de nuit reste, jusqu'à la coupure.**
Il rapporte ce que Hektor produit, et pendant la transition il rapporte aussi ce que les
négociateurs y saisissent encore. Il ne s'éteint qu'avec l'envoi, le même jour.

## 1.3 La règle de sécurité qui accompagne le run de nuit

> **Ce que l'app a écrit doit être arrivé chez Hektor AVANT que le run relise.**

Sinon le run rapporte l'ancienne valeur et écrase. Aujourd'hui c'est garanti sans rien faire : les
envois partent dans les 10 minutes. Avec le convoi, il suffit qu'il tourne **avant** le run —
d'où le créneau 05:15, quinze minutes avant 05:30.

C'est ce qui rend inutile tout contrat d'autorité champ par champ : **Hektor confirme au lieu
d'écraser.** *(Point « ordre journalier push/pull » de la note du 17/08 — tranché : push puis pull.)*

## 1.4 Le système à la fin

```
        AUJOURD'HUI                              LA CIBLE

  Hektor (loué)                            ┌──────────────┐
      │ 21 étapes, 1 h/nuit                │   LE FRONT   │
      ▼                                    └──────┬───────┘
  hektor.sqlite  3,9 Go                           │ écrire = écrire
      ▼                                           ▼
  phase2.sqlite  2 Go                      ┌──────────────┐
      ▼                                    │   SUPABASE   │  ← seule source
  Supabase ──► Front                       └──────┬───────┘
      ▲                                           │
      │ 4 workers, Playwright,             ┌──────┴──────────────────┐
      │ sessions, 2FA, file de jobs        │ Yousign · Portails ·    │
      ▼                                    │ Google · DVF/cadastre   │
  Hektor (écriture)                        └─────────────────────────┘
```

**Disparaît à la coupure** : le pipeline de nuit et ses 21 étapes, les deux bases SQLite locales
(5,9 Go), les 4 services worker, Playwright, le login 2FA, la file de jobs, le calque,
`base_snapshot`, le drapeau `conflict`, les cases `hektor_*_id`.

**Reste** : le front, Supabase, le backend, et les services contractés en propre.

**Tout le poids d'aujourd'hui est le prix de la cohabitation, pas celui du métier.**

---

# 2. CE QUE LA MESURE A ÉTABLI *(18/08)*

## 2.1 Le coût réel des workers — 30 jours

Frédéric : *« le gros problème est la lenteur des workers et leurs impacts. »* Confirmé, et localisé.

| Action | Attente | Exécution | **Total** |
|---|---|---|---|
| **Créer une annonce** | 3 s | **488 s** | **8 min** *(max 30 min ; 1 échec sur 4)* |
| Changer le statut | 3 s | 33 s | 36 s |
| Supprimer une annonce | 5 s | 27 s | 32 s |
| Réaffecter le négociateur | 2 s | 27 s | 30 s |
| Envoyer une photo | 7 s | 20 s | 26 s |
| **Générer le numéro de mandat** | 5 s | 21 s | 26 s |
| Rafraîchir un contact | 12 s | 12 s | 24 s |
| Générer le PDF d'estimation | 5 s | 17 s | 21 s |
| Envoyer un document | 3 s | 14 s | 17 s |
| Modifier des champs | 4 s | 10 s | 14 s |

**Trois lectures :**

1. **La création d'annonce est le point noir** : 8 minutes d'exécution, 1 échec sur 4.
   *(Réserve : 4 créations sur 30 jours, échantillon faible.)* Le convoi ne la réglera pas —
   c'est un chantier à part.
2. **Le reste coûte 15 à 35 s, et ce n'est PAS le login.**
   ⚠️ *Correction du 18/08 — une première lecture attribuait ce temps à la connexion Hektor.
   C'est faux.* Un **keep-alive** ([`console_job_worker.js:354`](../Console/console_job_worker.js:354))
   maintient la session chaude en permanence : toutes les 7 minutes d'inactivité, une lecture légère
   de 0,5 s rafraîchit le TTL **sans re-login**. Commentaire du code : *« le prochain job ne paie pas
   le login à froid (prep ~35s → ~19s, mesure validée) ».*
   Ces 10 à 35 s sont donc le **vrai travail** : charger les formulaires Hektor, résoudre les listes
   déroulantes, reposter. **Aucun regroupement ne les supprime.**
3. **La file saturée n'est pas celle de l'utilisateur.** `sync_console_documents` : 21 982 jobs en
   30 jours, **4 h d'attente moyenne, jusqu'à 11 h**. C'est le rapatriement, sur le worker
   `documents`, une voie séparée. Les actions utilisateur passent par `actions`/`admin` et
   n'attendent que 3 secondes.

## 2.2 Le calque — ce qu'il fait vraiment

La fonction d'enregistrement (`app_edit_annonce_optimistic`) écrit à trois endroits :

| Destination | Champs |
|---|---|
| Colonnes de `app_dossier_current` | **4** — `prix`, `ville`, `code_postal`, `numero_mandat` |
| Clés de `detail_payload_json` *(via `json_map`)* | **9** — surface, pièces, chambres, terrain, lat, lon, garage |
| Clé `app_optimistic_overlay` *(le calque)* | **tous** |

Sur ~150 champs éditables, **13 ont une écriture propre**. Le reste ne va que sur le calque.

**Mais la place existe.** Structure réelle, relevée sur un bien :

```
detail_payload_json → detail_raw_json → <groupe> → props → <CHAMP> → value

  ag_exterieur        17 champs        equipements      selon le bien
  diagnostiques       13 champs        copropriete      selon le bien
  mandat_infofi       11 champs        secteur          selon le bien
  ag_interieur        10 champs        organiser_visite selon le bien
  mandat_mandatdispo   4 champs        terrain           1 champ
```

Le calque n'existe pas par manque de place : **c'est un raccourci pris à l'époque où Hektor
réécrivait tout la nuit suivante.** Il ne valait pas le coup d'écrire proprement.

**Conséquence non évidente** : une valeur posée sur le calque est **invisible** aux filtres, aux
tris et au moteur de rapprochement. Corriger cela rend ~137 champs exploitables.

## 2.3 Autres mesures utiles

- **Poids d'une fiche** : 28,3 Ko en moyenne, **141 Ko au maximum**.
- **Read-through à l'ouverture** : 33 déclenchements en 7 jours, 10,7 s en moyenne. Il ne part
  **pas** à chaque ouverture — déduplication + délai de 30 min par bien. Ce n'est donc **pas** la
  cause de la lenteur perçue aujourd'hui.
- **Front** : `App.tsx` 37 200 lignes, dont un composant de 8 035 lignes et 224 variables d'état.
  Recalculé à chaque rechargement de liste. **Non mesuré côté navigateur — mesure F12 à faire.**

---

# 2bis. L'AUDIT DE FAISABILITÉ DU 18/08 — ce qu'il a corrigé

Trois analyses en lecture seule (mapping des champs · identité · risque de régression).
**Elles ont corrigé trois affirmations de ce document. Les corrections priment.**

## ① La double identité des annonces existe déjà — depuis mars 2026

C'était l'inquiétude de Frédéric : *« ajouter une colonne d'identifiant m'inquiète pour les
fonctions déjà en place. »* **Il n'y a rien à ajouter.**

```
app_dossier_current : 13 212 lignes
  app_dossier_id     13 212 remplis, tous distincts,  plage 118 → 5 132 231
  hektor_annonce_id  13 212 remplis, tous distincts,  plage 6 → 62 899
  lignes où les deux sont égaux : 0
```

Exemples : `app 118 ↔ hektor 102`, `app 142 ↔ hektor 10238`. **Deux numérotations indépendantes.**

Origine : `SQL_V1_SURCOUCHE_METIER_2026-03-23.md` (23/03/2026) — `app_dossier` a son propre `id` et
toutes les tables filles pointent sur `app_dossier_id`. **C'est la conception d'origine de la
surcouche.** Elle tourne depuis cinq mois sans avoir jamais fait parler d'elle.

Confirmations complémentaires : `app_dossier_id` est **déjà la clé primaire** de
`app_dossier_current` ; **aucune clé étrangère** dans tout Supabase sur ces identifiants ; la RLS
tolère déjà un identifiant Hektor absent ; `app_edit_annonce_optimistic` **fonctionne déjà en
`app_dossier_id` seul** — le patron cible existe et tourne en production.

⇒ **B ne crée aucune colonne pour les annonces. Elle relâche une contrainte.** Aucune signature de
fonction ne change. Seule décision : attribuer les `app_dossier_id` app dans une plage réservée
au-dessus de 5,1 M pour ne pas percuter le compteur de la base locale.

## ② La création d'annonce n'est pas à 8 minutes

Le chiffre de 8 min venait de 4 jobs. Sur **92 créations** :

| | |
|---|---|
| Médiane | **57 s** |
| p90 / p95 | 231 s / 423 s |
| > 10 min | 4 cas sur 92 |
| Taux d'échec | 27 % (mai) → **4,5 % (juillet)** |

⇒ **B ne se justifie plus par la lenteur**, mais par les cas extrêmes et surtout parce qu'elle rend
la coupure indolore. Argument plus faible — à assumer comme tel.

## ③ Le périmètre de A est plus petit, mais son intérêt plus grand

Sur **170 champs éditables** :

| Famille | Nb | Situation |
|---|---|---|
| **Case Hektor existante** | **110** | écrire dans `<groupe>.props.<CHAMP>.value` suffit |
| **Donnée présente sous une autre forme** | **22** | adresse → `localite` ; honoraires → `honoraires_detail_console_json` ; chauffage → `chauffage_console_json` ; titre/description → `texte_principal_*`. Rien n'est perdu, l'écriture passe ailleurs. |
| **Absents partout** | **28** | vérifié : 0 occurrence sur 2 000 fiches |

**Les 28 sont déjà aveugles aujourd'hui** — et `AUDIT_CHAMPS_HEKTOR_MANQUANTS_2026-07-07.md` le
disait déjà (section « Manquants PARTOUT »). Ajoutés à l'app en juillet, ils partent vers Hektor
mais **l'API ne les renvoie jamais** : l'app les affiche vides au rechargement.

> **Ce n'est donc pas une limite d'A, c'est une réparation.** Puisque Hektor ne les rend jamais,
> ces 28 champs appartiennent à l'app **par nature**. Leur donner une case chez elle est le bon
> modèle, pas un contournement.

**Deux contraintes fermes découvertes** :
- **Le calque ne peut pas être entièrement supprimé** : `composition_pieces` y transite sous forme
  de diff structuré, et les pièces vivent dans un groupe sans `props`. `resolveDisplayAddress`
  (`App.tsx:3813`) en dépend aussi. A est donc un **retrait ciblé, champ par champ**, jamais global.
- **8 champs auraient une case mais resteraient invisibles** (`surfappart`, `surfterrain`,
  `nbpieces`, `NB_CHAMBRES`, `dateenr`, `NO_DOSSIER`, `prix`, `PRIXNETVENDEUR`) : le dictionnaire
  `mapped` (`App.tsx:2530-2559`) court-circuite la lecture des groupes. Correctif distinct, à risque
  de régression — il touche cockpit, modale et en-tête.

Point rassurant : le calque est **vide sur les 13 212 fiches**, et le cockpit affiche pourtant tout
correctement. **La lecture par les cases fonctionne déjà en production.**

## ④ L'état du dépôt est le vrai risque — pas le code à venir

| | Constat vérifié |
|---|---|
| 🔴 | **314 lignes tournent en production sans être sur GitHub.** `console_job_worker.js` est au commit `0a06fdd` sur disque, `origin/main` est à `4cc7936`. Les 4 services ont démarré à 10:06, après. Une restauration depuis GitHub **régresse le worker en silence**. Risque **déjà réalisé**. |
| 🔴 | **Aucun retour arrière SQL.** Pas de rollback, pas de sauvegarde du code des fonctions. Sur 12 fonctions critiques testées, **3 n'ont aucun fichier source local**. 6 patchs SQL appliqués en prod ne sont dans aucun commit. |
| 🔴 | **Une régression d'édition n'alerterait personne.** Les 3 sentinelles qui la couvrent (`annonce_conflit`, `annonce_partielle`, `annonce_push_bloque`) sont bien placées mais plafonnent en `warning`, alors que l'alerte ne part qu'en `critical`. |
| 🟠 | **Rien n'interdit deux fiches pour la même annonce** : `hektor_annonce_id` est `NOT NULL` mais **sans index unique**. 708 fiches ont des identifiants dispersés (trace de suppression/réinsertion), 1 135 rapprochements sont orphelins. |
| 🟢 | `npm run build` **passe** (37 s, 0 erreur). Rollback Vercel **instantané**. Files `*_pending` **vides**. Taux d'erreur des jobs **0,4 %**. |

⚠️ Un test du dépôt est **cassé** : `backend/tests/test_rapprochement_email.py:68`.

## Étape 0 — avant la première ligne de code *(~2 h)*

1. **Pousser `main`** (les 314 lignes de worker) et désamorcer l'index git (12 suppressions stagées).
2. **Exporter les 122 fonctions SQL** dans un fichier versionné — unique moyen de revenir en arrière.
3. **Passer les 3 sentinelles d'édition en `critical`.**
4. **Poser l'index unique partiel** sur `hektor_annonce_id` — ferme une faille **déjà ouverte**,
   utile indépendamment de B.
5. Écrire le point de retour sur une page (sha de référence, id du déploiement Vercel, commande de
   restart des 4 services).

---

# 3. LE CHEMIN — A, B, D

Arbitré le 18/08. **Trois étapes, pas quatre** : le convoi (ex-C) a été abandonné, voir plus bas.
Le principe : **ce qui rend l'app instantanée passe avant tout le reste — et le reste s'avère inutile.**

## A — Écrire dans la vraie case, et enregistrer au fil de la frappe

**But** : supprimer le calque, supprimer le brouillon, et rendre les ~137 champs exploitables.

**Décision du 18/08 : enregistrement au fil de la frappe.** Plus de bouton « Enregistrer », plus de
barre, plus de brouillon — donc **plus rien à perdre**, et le bug de purge de saisie disparaît par
construction.

Quatre précautions vérifiées le 18/08 :

| | Précaution |
|---|---|
| **1** | **Temporiser côté écran** : enregistrer en sortie de champ, ou ~1 s après la dernière frappe. Pas un enregistrement par touche (« 250000 » ne doit pas en faire six). |
| **2** | **Le recalcul du rapprochement coûte 32 ms** *(mesuré)*. Ce n'est pas un obstacle : enregistrer au fil de la frappe ne le sature pas. |
| **3** | **L'adresse est un cas à part** : elle déclenche un re-géocodage. Enregistrer champ par champ géocoderait trois fois (rue seule, puis + CP, puis + ville) dont deux faux. Attendre que l'adresse soit stable. **Seul endroit où le regroupement garde une raison d'être.** |
| **4** | **Délai worker inchangé à 10 minutes.** Il se réarme à chaque modification, donc rien ne part tant qu'on travaille sur le bien. |

- La fonction d'enregistrement écrit dans `<groupe> → props → <CHAMP> → value`
- Pour un champ jamais rempli par Hektor : savoir dans quel groupe créer la case
  *(le découpage par rubrique du front devrait correspondre — à confirmer)*
- **Filet** : les champs sans case identifiée restent sur le calque, qui se vide de lui-même
- Le front cesse de lire le calque en premier

**Le worker ne change pas.** La ligne d'attente (`push_fields`) est indépendante de l'endroit où
la valeur est rangée pour l'affichage.

**Décision à prendre dans A** : voir D6 — garde-t-on un brouillon et un bouton « Enregistrer »,
ou enregistre-t-on au fil de la saisie ?

## B — L'identité passe à l'app *(le cœur du chantier)*

**But** : plus aucun job n'est attendu.

- L'app attribue l'identifiant à la création
- `hektor_annonce_id` / `hektor_contact_id` deviennent des **cases vides qui se remplissent**
  quand l'ouvrier a fini
- Idem pour ce que Hektor fabrique et qu'on n'a pas à la création *(numéro de dossier, etc.)*
- On retire la table des fiches provisoires, la réconciliation et le balayage automatique

**Ce qui devient instantané** : créer un bien, un contact, un mandant, le rattacher, modifier
n'importe quel champ, changer un statut, archiver, restaurer, supprimer, réaffecter, envoyer un
document ou une photo.

**Ce qui reste une attente légitime** : « générer le numéro de mandat ». Et si le bien vient
d'être créé, il faut que l'arrière-plan ait rattrapé — 8 minutes aujourd'hui. La différence :
pendant ce temps on peut **remplir la fiche, ajouter les photos, saisir le mandant**, au lieu
d'être bloqué.

> ⚠️ **Point de réconciliation à traiter dès la conception.** Pendant le trou où la case Hektor est
> vide, si le run de nuit passe, il verra arriver le bien depuis Hektor **sans reconnaître** que
> c'est le même — la correspondance se fait justement sur cette case. Risque : **deux fiches pour
> le même bien.** Ce n'est pas bloquant, c'est une règle à écrire.

## ~~C — Le convoi de nuit~~ — **ABANDONNÉ (Frédéric, 18/08)**

> *« Le convoi me fait un peu peur, car les workers fonctionnent bien actuellement. »*

**Décision : on n'y touche pas.** Le rythme d'envoi reste **10 minutes**, inchangé.

**Pourquoi l'abandon est justifié** — le gain avait été surestimé :

- Le convoi devait supprimer « le login payé à chaque geste ». **Ce login n'existe pas** : le
  keep-alive le supprime déjà (§2.1, lecture n°2). Les 10 à 35 s sont du vrai travail sur les
  formulaires Hektor, que le regroupement ne supprime pas.
- Il ne resterait donc que l'enrobage — prise de job, logs, changements d'identité : **20 à 30 %**,
  sur un temps que **plus personne n'attend après B**.
- En face, le coût est réel : remplacer le verrou par bien (repéré par la revue externe du 17/08 —
  dans un convoi, le job « tourne » pendant tout le passage et bloquerait les actions sur tous les
  biens concernés), gérer les échecs partiels, réadapter les seuils de surveillance, et perdre la
  finesse du « quelle modification a échoué ».
- Charge réelle projetée : **300 actions/jour ≈ 75 min de travail réparties sur 3 ouvriers**, sur
  une journée de dix heures. Rien ne sature.

> **La conclusion qui simplifie le plan : il n'y a rien à optimiser côté ouvriers, parce
> qu'après B personne ne les attend.** Qu'un job prenne 10 s ou 5 s n'a plus d'importance.
> Le seul problème était l'attente — et c'est B qui la supprime, pas le convoi.

**Précaution optionnelle, non urgente** : le délai se remet à zéro à chaque modification, sans
plafond. Avec 10 minutes le scénario est peu probable, mais quelqu'un qui retouche un bien toutes
les 9 minutes ne pousserait jamais. Un plafond — jamais plus de 2 h après la première modification
— coûterait trois lignes.

## D — La coupure

Le même jour : on arrête d'envoyer **et** d'importer.
On éteint le pipeline de nuit, les 4 services worker, Playwright, la file de jobs, le convoi.
On archive les deux bases SQLite. On retire les cases `hektor_*_id`.

---

# 4. EN PARALLÈLE — ce qui ne dépend pas du développement

| Chantier | Nature | Remarque |
|---|---|---|
| **Yousign** | contrat + intégration | **En premier des trois.** Le worker ne sait pas *lancer* une signature — seulement relancer, annuler, télécharger. Tant que Yousign n'est pas là, les négociateurs doivent rouvrir Hektor pour ce geste. |
| **Registre de mandats** | développement | Obligation légale. 23 836 mandats numérotés ; l'app reprend la série. |
| **Portails** | décision commerciale | Direct, diffuseur, ou garder Hektor pour cela seul — option légitime qui repousse la coupure sans bloquer le reste. |
| **Photos** | temps machine | **Irréversible.** Inventorier, puis télécharger. 1 355 rapatriées à ce jour. Seule fenêtre qui se ferme. |
| **Création d'annonce à 8 min** | analyse | Pourquoi 488 s, pourquoi 1 échec sur 4. Reste immédiate même après C. |

## Traité dans des sessions séparées *(Frédéric, 18/08)*

Sauvegarde hors site et test de restauration · inventaire et rapatriement des photos ·
versionnement des notes. **Ne conditionnent aucune étape de ce chantier.**

---

# 5. LES DÉCISIONS

## Prises le 18/08

| | Décision |
|---|---|
| **Cible** | On n'attend Hektor que pour ce que Hektor produit |
| **Temps réel** | Numéro de mandat · Signature · Publicité. Rien d'autre. |
| **Run de nuit** | Conservé jusqu'à la coupure, avec la règle « pousser avant de relire » |
| **Ordre** | **A** les cases → **B** l'identité → **D** la coupure. Trois étapes. |
| **Calque** | Supprimé en A, avec filet pour les champs sans case |
| **Modèle d'édition (ex-D6)** | **Au fil de la frappe.** Plus de brouillon, plus de bouton « Enregistrer ». |
| **Rythme d'envoi** | **10 minutes, inchangé.** Pas de passage à 30 min. |
| **Convoi de nuit** | **ABANDONNÉ.** Gain surestimé (le login est déjà amorti par le keep-alive), coût réel, et les workers fonctionnent. |
| **Identité** | Attribuée par l'app (étape B) |
| **Read-through à l'ouverture** | **Conservé tel quel jusqu'à la bascule**, puis remplacé par un bouton « Actualiser depuis Hektor » sur la fiche annonce uniquement. Il ne coûte que ~5 déclenchements/jour et rapatrie les PDF signés. |
| **Correction de la purge de saisie** | **Abandonnée** — elle réparait un mécanisme que D6 va probablement supprimer |
| **Convoi** | En C. Sautable si arbitrage nécessaire. |

## Restant à trancher

**D7 — La règle de réconciliation** *(appartient à B)* — cf. l'avertissement du §3-B.
**C'est la seule décision technique encore ouverte, et elle bloque B.**

**D8 — Yousign en premier ?** Le trou sur la mise à la signature le plaide.

**D9 — Le message aux négociateurs** : ce qu'ils font dans l'app, ce qui reste dans Hektor
(la signature), et pour combien de temps.

---

---

# 5bis. LES CONTACTS — AUDIT EN COURS, AUCUNE DÉCISION

**Différence structurelle avec les annonces** : `hektor_contact_id` **EST la clé primaire** de
`app_contact_current`. Une clé primaire ne peut pas être vide. La solution « on crée avec un
identifiant vide, le worker complète en arrière-plan » — qui marche pour les annonces parce que
`app_dossier_id` est déjà la clé — **ne s'applique pas telle quelle** ici.

Éléments déjà établis (audit du 18/08) :

- **Aucun surrogate `app_contact_id` n'existe** : 0 colonne dans Supabase, 0 occurrence dans le
  code. La décision du 17/08 (`NOTE_CONCEPTION_PHASE1_APP_AUTORITAIRE_2026-08-17.md:40`) a été
  **prise mais jamais codée**.
- **57 525 lignes**, **17 tables** portent `hektor_contact_id`, dont **2 l'ont pour clé primaire**
  (`app_contact_pending`, `app_search_pending`).
- Créer un contact prend **15 s** ; `create_hektor_contact` a été appelé **0 fois en 30 jours**,
  `create_hektor_mandant_contact` 2 fois.
- Les recherches acquéreur sont **déjà largement app-first** (édition optimiste,
  `app_search_pending`, push débouncé) et leur communication avec Hektor est **connue pour être
  incomplète** — mémoires `recherches-index-actives-vs-complet` et `hektor-sync-trou-recherche`.

**Trois chemins possibles, aucun tranché :**

| | Ce que ça implique |
|---|---|
| Ajouter un identifiant app | 57 525 lignes, 17 tables, 2 clés primaires à refaire |
| Valeur temporaire dans la colonne, échangée à l'arrivée du vrai identifiant | Un contact neuf n'est référencé que par 1 à 3 lignes → échange petit |
| Ne rien faire | 15 s d'attente sur un geste rare |

> **Audit approfondi demandé par Frédéric le 18/08.** Périmètre : création et modification d'un
> contact, liaison à une annonce, liaison à une recherche, écriture directe dans les colonnes sans
> calque, worker en arrière-plan. Lecture des notes existantes sur l'identité contact.
> **Conclusions à insérer ici quand l'audit sera rendu. Rien n'est décidé avant.**

---

# 6. CE QUI RESTE VRAI QUOI QU'IL ARRIVE

## L'invariant workers *(consigne Frédéric, 17/08)*

> *« Conserver les règles Hektor (IDs, etc.) pour que les workers fonctionnent toujours,
> jusqu'à la coupure finale. »*

Ne pas retirer avant la coupure : `hektor_annonce_id`, `hektor_contact_id`, `idUser` du
négociateur, `search_index`, `base_snapshot`, `app_console_job` et les files d'envoi.
**Avant de retirer quoi que ce soit : « un worker s'en sert-il pour viser Hektor ? » Si oui, on garde.**

## Ce qui survit à la coupure sans rien faire

Rapprochement acquéreur, avis de valeur, ledger d'affaires, espace client, agenda et prise de
rendez-vous, relances et emails, Matterport, Google Workspace, agents IA, données DVF.
**Déjà la majeure partie de la valeur de l'app.**

---

---

# 6bis. PIÈGE D'EXPLOITATION — le drapeau invisible du pipeline

**Incident du 19/08, à ne pas rejouer.**

Après l'échec du run de 5h30 (arrêt à l'étape 13), les 4 étapes de publication ont été relancées
à la main, avec les commandes et les arguments **copiés du script**. Résultat : **357 brouillons
sont entrés dans le périmètre des annonces actives** (13 220 → 13 577), sans aucune erreur ni
avertissement.

**Cause** : `run_full_pipeline.ps1:191` pose `$env:APP_BROUILLON_BUCKET_ENABLED = "1"`.
`phase2/sync/export_app_payload.py:324` la lit. Sans elle, `brouillon_active_exclusion_sql()`
renvoie une chaîne vide et **les brouillons ne sont plus exclus du périmètre actif**.

> **Règle : reproduire les commandes d'un script ne suffit pas — il faut reproduire son
> environnement.** Toute reprise manuelle d'une étape de publication doit être préfixée par
> `APP_BROUILLON_BUCKET_ENABLED=1`.

**Portée vérifiée** : c'est le **seul** drapeau applicatif de ce type. Un `grep` sur `$env:` dans
`run_full_pipeline.ps1` et `scheduled/*.ps1`, croisé avec les `os.environ.get("APP_…")` des scripts
du pipeline, ne remonte que celui-là. Les deux autres occurrences (`CONSOLE_NODE_EXE`,
`USERPROFILE`) ne concernent que la localisation de Node.

**Correctif de fond suggéré, non fait** : ce drapeau silencieux devrait soit être posé en dur dans
`export_app_payload.py`, soit faire échouer bruyamment le script quand il est absent. En l'état,
son oubli produit une donnée fausse — 357 brouillons présentés comme des annonces actives — sans
la moindre trace dans les journaux.

**Détection** : le symptôme se lit par un chevauchement entre les index, qui doit toujours être nul :

```sql
select count(*) from app_dossier_current d
join app_brouillon_annonce_index_current b on b.hektor_annonce_id = d.hektor_annonce_id;
-- doit valoir 0
```

C'est un bon candidat pour une sentinelle de `check_gti_health.py`.

---

# 7. RÈGLES DE CONDUITE

- **Protocole par étape** *(Frédéric, 18/08)* : vérifier et analyser → expliquer clairement →
  **obtenir la validation** → coder → vérifier son travail → étape suivante.
- **Que du plus.** Ne rien dégrader : ni l'app, ni les workers, ni l'existant.
- On ajoute, on ne remplace jamais. Tout passe derrière un interrupteur.
- Rien n'est déployé sans être vérifié sur un bien de test.
- Stager fichier par fichier, jamais `git add .`.
- ⚠️ **Ne pas faire `git commit -a`** : l'index porte 12 suppressions stagées de notes
  stratégiques, encore récupérables par `git show HEAD:<chemin>`.
- Valider le front avec `npm run build`, jamais `tsc --noEmit`.
- Les 4 services worker partagent `console_job_worker.js` : les redémarrer **tous** après une
  modification.
- Tests de signature : signataire `frederic.gerphagnon@` uniquement — chaque procédure est facturée.
