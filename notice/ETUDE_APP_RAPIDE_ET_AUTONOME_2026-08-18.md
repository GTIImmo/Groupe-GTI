# Étude — Rendre l'app rapide et autonome (Temps 1)

**Date : 2026-08-18 — version 2 (remplace la v1 du même jour, périmètre élargi par Frédéric).**
**ÉTUDE — aucun code écrit, aucun fichier de production modifié.**

> 🔴 **DOCUMENT LARGEMENT PÉRIMÉ — lire `VISION_GLOBALE_DEV_INDEPENDANCE_2026-08-18.md` (v2).**
>
> Le plan en 5 retraits décrit ici a été remplacé le 18/08 par l'ordre **A → B → C → D**.
> Ce qui a changé : l'étape 1 (purge de saisie) est **abandonnée**, l'étape 2 (read-through) est
> **repoussée à la bascule**, et le convoi **descend en C** — l'utilisateur n'attend plus après B.
>
> **Ce qui reste utile ici** : les références de code vérifiées (§1, §2), la chaîne de la lenteur,
> la méthode de test (§7), et le trou sur la mise à la signature (§5).
>
> ⚠️ **Correction du 18/08 (§3 de cette note est périmé)** : il y est écrit que 137 champs n'ont pas
> de domicile hors du calque. **C'est faux, vérifié en base.** Chaque champ a sa case
> (`detail_raw_json → <groupe> → props → <CHAMP> → value`). Le calque existe parce que la fonction
> d'enregistrement n'y écrit pas, pas parce que la place manque. Le retrait du calque devient donc
> le **Temps 2** de la vision, et non un « rangement à froid ». Voir §2 (E2) de la vision.

Prolonge et **simplifie** `ETUDE_FAISABILITE_DECOUPLAGE_HEKTOR_APP_FIRST_2026-08-08.md`
et `NOTE_CONCEPTION_PHASE1_APP_AUTORITAIRE_2026-08-17.md`.
Toutes les références de ligne ont été vérifiées dans le code le 18/08/2026.

---

## 0. Le cadrage

**Aujourd'hui** : les négociateurs travaillent dans Hektor. Le run de nuit alimente l'app.
Frédéric est le **seul utilisateur** de l'app (bêta).

**Ce qu'il veut** : présenter l'app aux négociateurs, qu'ils l'adoptent et quittent Hektor.
Pendant **quelques semaines**, l'app continue d'alimenter Hektor, le temps de monter ses propres
remplaçants : registre de mandats en propre, Yousign en direct, passerelles en direct. Puis on coupe.

**Le blocage** : l'app est trop lente pour être présentée.

**Le principe posé par Frédéric le 18/08** :
> *« Je souhaite que mon app gère les données en temps réel entre elle et le serveur.
> Vers Hektor, une fois par nuit — sauf numéro de mandat, signature, publicité. »*

Soit : **temps réel entre l'app et sa propre base ; différé vers Hektor.**

### Le contrat de synchronisation

| Rythme | Contenu |
|---|---|
| **Immédiat, app ↔ base** | **Tout.** C'est le principe. |
| **Immédiat, vers Hektor** | Numéro de mandat · Signature · Publicité/diffusion · **Créations** *(cf. §5)* |
| **Convoi de nuit** | Toutes les **modifications** : prix, statut, description, contacts, recherches, mandants |
| **Jamais envoyé** | Estimations, rapprochements, espace client, agenda, relances, ledger — données app-only |

> **Règle mémorisable : le convoi transporte les corrections. Tout ce qui crée quelque chose ou
> déclenche un service reste immédiat.**

**Décision du 18/08 : la publicité passe en convoi de nuit.** Le bouton « Envoyer maintenant »
(§2, R4) sert de porte de sortie quand une baisse de prix doit atteindre les portails tout de suite.
Cela évite d'avoir à sortir le prix et le statut du convoi, et rend caduque la question du rythme de
republication de Hektor vers les portails.

---

## 1. Pourquoi l'app est lente — la chaîne complète

Ce n'est pas une accumulation de petites lenteurs. C'est **une seule chaîne**, alimentée par deux
déclencheurs : ouvrir une fiche, et modifier un champ.

```
DÉCLENCHEUR A — tu ouvres un bien
   App.tsx:12403-12410  →  requestAnnonceRefresh   (contact : :12391-12399)
   api.ts:7176          →  RPC app_console_request_annonce_refresh (TTL 1800 s)
                        →  job « refresh_console_data »
                        →  worker sync_light (console_job_worker.js:3231)
                        →  login Hektor 19-35 s + AnnonceById + ListPasserelles
                        →  rejeu phase2 + push ciblé

DÉCLENCHEUR B — tu modifies un champ
   RPC app_edit_annonce_optimistic → app_annonce_pending, push_after = now + 600 s
   pg_cron (1×/min)     →  job « update_hektor_annonce_fields » 10 minutes plus tard
                        →  même worker, même login Hektor

LES DEUX ABOUTISSENT AU MÊME ENDROIT
   App.tsx:~12042  setInterval(refreshHektorActionJobs, 5000)   ← 2 requêtes toutes les 5 s
   App.tsx:12026   à la fin du job → setDataReloadKey(+1), 600 ms après
                        ↓
   rechargement complet des listes
                        ↓
   selectedDossier recréé   (App.tsx:12494-12506, 12512-12546)
                        ↓
   detail change d'identité (App.tsx:15335)
                        ↓
   CockpitDetail purge son brouillon (App.tsx:22374 : setEdited({}))
                        ↓
   ⚠️ SAISIE NON ENREGISTRÉE PERDUE
```

**Point clé découvert le 18/08** : le déclencheur B compte autant que le A. Chaque correction
revient dans la figure de l'utilisateur un quart d'heure plus tard sous forme de rechargement
complet. **Retirer le read-through sans déplacer l'envoi ne suffirait donc pas** — l'app resterait
agitée toute la journée.

### Pourquoi ce mécanisme existe

Il n'est pas absurde : il date du temps où **Hektor était le patron**. Le calque, le `base_snapshot`,
le flag `conflict` et le read-through forment une **armure** dont la seule fonction est de protéger
les saisies de l'app contre un Hektor qui pouvait les écraser.

> Le jour où l'app devient le patron, cette armure ne protège plus rien.
> **La retirer n'est pas construire : c'est soustraire.**

---

## 2. Le Temps 1 — cinq retraits

Aucun ne change **ce qui** part vers Hektor. R4 change **quand**. Tous sont réversibles.

### R1 — Le rafraîchissement automatique à l'ouverture d'une fiche

**Fichiers** : `App.tsx:12391-12399` (contact) et `:12403-12410` (annonce). Deux `useEffect`.

**Ce qui change** : la fiche s'ouvre **instantanément**, avec les données de la dernière nuit.
Plus de job, plus d'ouvrier, plus de login Hektor.

**Remplacement — bouton n°1, sur la fiche annonce uniquement** *(tranché par Frédéric le 18/08 ;
pas de bouton sur la fiche contact)* :

> **« Actualiser depuis Hektor »** — appelle `requestAnnonceRefresh`, la fonction existante.
> Récupère ce qui a bougé chez Hektor : numéro de mandat, état de diffusion, état de signature,
> affaires. La capacité est conservée, elle n'est plus payée à chaque ouverture.

**Régression temporaire assumée** : tant que les négociateurs saisissent dans Hektor, une fiche
affiche l'état de la nuit et non celui de l'instant. **Cette régression s'inverse à la bascule** :
quand plus personne n'écrit dans Hektor, il n'y a plus rien à aller y chercher.

### R2 — Le sondage permanent des jobs

**Fichier** : `App.tsx:~12042` — `setInterval(refreshHektorActionJobs, 5000)`.

Après R1 et R4, presque plus aucun job n'est créé dans la journée : le sondage tourne à vide.
**Proposition** : ne sonder que s'il existe au moins un job suivi non terminé.
Zéro requête au repos, réactivité inchangée quand un job tourne.

### R3 — La purge de la saisie en cours *(correction de bug)*

**Fichier** : `App.tsx:22374` — `useEffect(() => { setEdited({}); setSaveMsg(null) }, [props.detail])`

L'effet réagit à un changement de **référence** de `props.detail`, pas à un changement de **bien**.
Or `detail` est recréé à chaque rechargement (`App.tsx:15335`), même pour le même bien aux mêmes
valeurs. Le brouillon de saisie (`edited`, alimenté par `onFieldSave` `App.tsx:23745`) est alors vidé
sans avertissement, et la barre « Enregistrer » disparaît.

**Correction** : réagir à l'**identifiant du dossier** au lieu de la référence de l'objet.

⚠️ **Ce n'est pas une seule ligne.** C'est aujourd'hui cette même ligne qui nettoie le brouillon
*après* un enregistrement réussi. Il faut donc ajouter ce nettoyage à l'endroit correct, dans
`doSaveEdits` (`App.tsx:23776`), sur le chemin du succès. **Deux endroits, moins de cinq lignes.**

**C'est un bug : à corriger indépendamment de tout le reste.**

### R4 — Les modifications passent au convoi de nuit

**Aujourd'hui** : `push_after = now() + 600 s` (RPC `app_edit_annonce_optimistic`, et ses jumelles
contact/recherche).
**Demain** : `push_after` = prochain créneau de nuit.

C'est la **variante A** de l'étude du 08/08 : aucun code neuf. Les files `app_*_pending` existent,
les sweeps `app_*_enqueue_due_pushes` tournent déjà toutes les minutes. **L'outbox existant devient
le convoi.**

**Le convoi se place en tête du run de nuit** :

```
05:15   CONVOI       l'app envoie à Hektor tout ce qui a été saisi dans la journée
05:30   RUN DE NUIT  relit Hektor… et y retrouve les valeurs de l'app
```

Hektor **confirme** au lieu d'écraser. **C'est l'ordre qui règle le problème, pas le code.**
Cela supprime le préalable le plus lourd du chantier : plus besoin du contrat d'autorité champ par
champ (C6/C7, déjà retirés le 18/08), ni de l'inventaire des ~130 clés du blob exigé par la note du
17/08. *(C'est le point ouvert « ordre journalier push/pull » de cette note — tranché : push puis pull.)*

**Bouton n°2, sur la fiche annonce** :

> **« Envoyer maintenant à Hektor »** — pose `push_after = now()` sur les lignes `app_*_pending` du
> dossier. Aucun mécanisme neuf : c'est le convoi, déclenché à la main pour un bien.
> **C'est lui qui règle la publicité.**

**Fenêtre de risque du convoi** : une saisie faite entre 05:15 et 05:30 ne serait pas encore partie
et serait écrasée par l'import. Quinze minutes, en pleine nuit. Négligeable, mais à documenter.

**Contrepartie à accepter, le temps que les négociateurs basculent** : la fenêtre de conflit passe
de 10 minutes à ~15 heures. Si Frédéric corrige un prix à 14h et qu'un négociateur touche le même
bien dans Hektor à 16h, le convoi trouvera Hektor modifié. Acceptable car (a) Frédéric est seul sur
l'app et édite peu, (b) **tant que les négociateurs sont dans Hektor, ce sont eux qui doivent
gagner**, (c) le bouton « Envoyer maintenant » est la porte de sortie.

### R5 — Le conflit ne bloque plus en silence

**Aujourd'hui** : si la date de modification Hektor a bougé depuis l'édition, le worker **renonce**
et pose le drapeau `conflict`. La valeur de l'app est perdue au prochain import, sans message.

**Demain** : on pousse **et on notifie** (« la valeur Hektor a été remplacée »), ou on renonce **et
on notifie**. Dans les deux cas, l'utilisateur est prévenu.

Le garde-fou lui-même reste — il protège une saisie faite dans Hektor par un négociateur, et ils y
sont encore. **C'est son silence qu'on retire, pas sa fonction.** Il s'éteindra à la bascule.

---

## 3. Le calque optimiste — conservé, mais requalifié

Frédéric, 18/08 : *« Il n'y a plus besoin non plus des calques optimistes ! »*
**Juste sur le principe. Mais une vérification du code impose une nuance.**

### Ce que fait réellement la RPC d'édition

`supabase/patch_annonce_edit_partial_status_2026-07-09.sql:36-124` écrit à trois endroits :

| Destination | Nombre de champs |
|---|---|
| Colonnes de `app_dossier_current` | **4** — `prix`, `ville`, `code_postal`, `numero_mandat` |
| Clés réelles de `detail_payload_json` (via `json_map`) | **9** — surface, pièces, chambres, terrain, lat, lon, garage |
| **Clé `app_optimistic_overlay`** | **tous les champs édités** |

> Sur les **~150 champs éditables** d'une fiche (`CK_LB_SECTIONS`, `App.tsx:21814-21841`),
> **seuls 13 ont un vrai domicile dans la base. Les ~137 autres n'existent QUE dans le calque** —
> description, DPE, chauffage, équipements, honoraires, copropriété, etc.

Le calque a donc **deux métiers** :

1. **Armure** contre un Hektor qui écrase → ce métier disparaît. ✅
2. **Seul lieu de stockage de 137 champs** → le supprimer aujourd'hui ferait disparaître de l'écran
   toute description modifiée. ❌

### Ce qu'on gagne gratuitement

Le commentaire de `App.tsx:2516` est explicite : *« Le read-through efface le calque au retour
Hektor »*. **R1 retire le read-through → plus rien n'efface le calque.** La valeur reste affichée.
Le comportement voulu est obtenu **sans toucher au calque**.

### Décision proposée

**On ne supprime pas le calque, on change son statut.**
Aujourd'hui : *« valeur provisoire en attendant Hektor »*. Demain : *« la valeur de l'app »*, lue en
premier, que rien n'écrase. Même stockage, sens inverse, **zéro travail**.

Le vrai nettoyage — donner une case propre aux 137 champs dans `detail_payload_json` — devient un
**chantier de rangement à faire à froid**, plus tard. Il n'est pas gratuit : le blob est organisé en
groupes (`hektorWizardRawDetailGroups`, lecture via `rawWizardDetailField` `App.tsx:2499`), donc
écrire un champ suppose de savoir dans quel groupe le poser.

**Bénéfice différé de ce rangement, à noter** : une valeur posée sur le calque n'est pas exploitable
par le moteur de rapprochement ni par les filtres — seuls les 13 champs à vrai domicile le sont.
Le rangement rendrait les 137 autres utilisables pour trier, filtrer et scorer.

---

## 4. Les créations — mécanisme allégé

Frédéric, 18/08 : *« Pour les nouveaux, on peut peut-être faire quelque chose de moins lourd que
l'actuel, si c'est juste un retour d'ID à compléter en arrière-plan. »*

**Idée retenue.** Elle rejoint exactement le point H de
`NOTE_REVUE_EXTERNE_CHANTIER_INDEPENDANCE_2026-08-17.md` :

> *« Un contact créé dans l'app possède une identité définitive dès la première seconde. Plus besoin
> de jeton provisoire ni de réconciliation : l'ID Hektor devient une simple référence ajoutée plus
> tard. »*

| | Aujourd'hui | Proposé |
|---|---|---|
| À la création | table `app_annonce_provisional`, ligne provisoire affichée en tête de liste | la fiche réelle, avec **son identité définitive** |
| Retour Hektor | réconciliation, échange de la provisoire contre la vraie | **une colonne vide qui se remplit** |
| Entretien | cron `app_sweep_stale_provisionals` pour les provisoires oubliées | rien |

**Condition, et c'est une vraie décision** : **l'identité doit être attribuée par l'app**, pas par
Hektor ni par la base locale SQLite (`app_dossier.id`, AUTOINCREMENT). C'est le « surrogate » de la
Phase 0 des notes.

**Pourquoi c'est le bon moment** : c'est aussi ce qui rendra la coupure indolore — le jour où Hektor
s'éteint, les fiches ont déjà leur identité définitive, il n'y a rien à migrer.

---

## 5. Ce qui reste immédiat vers Hektor

### Numéro de mandat — fonctionne depuis l'app

`create_hektor_mandat_auto_number` (`console_job_worker.js:9824`), 5 étapes Protexa. Inchangé.
Seul geste où l'attente est **structurelle** : le numéro n'existe pas avant que Hektor le rende.

### ⚠️ Les créations — contrainte, pas choix

**Pour obtenir un numéro de mandat, le bien doit exister dans Hektor.** Si la création attendait la
nuit, le numéro ne pourrait pas être généré le jour même. Même dépendance pour le mandant : pas de
mandat sans mandant rattaché.

Restent donc immédiats : `create_hektor_draft_annonce`, `create_hektor_contact`,
`create_hektor_mandant_contact`, `link_hektor_mandant`. Gestes rares, et déjà optimistes à l'écran.

### ⚠️ Signature — l'app ne sait pas en lancer une

**Vérifié le 18/08** : le worker ne connaît que quatre opérations ImmoSign —
`downloadProcedureZip`, `remindProcedureSignatories`, `deleteProcedure`,
`Documents-printImmoSignDocument`. **Aucune création ni envoi de procédure.**

> **Conséquence pour la bascule** : mettre un mandat à la signature se fait **à la main, dans
> Hektor**. Tant que Yousign n'est pas en place, les négociateurs devront rouvrir Hektor pour ce
> seul geste. Donc :
>
> 1. le message aux négociateurs doit le dire (« tout dans l'app, **sauf** la mise à la signature ») ;
> 2. **Yousign passe en tête des trois remplacements**, pas en dernier.

Rappel : le jeton d'accès au prestataire est extrait d'une iframe **à l'intérieur de Hektor** —
l'abonnement appartient à Hektor, pas à GTI. C'est le délai le plus long du chantier.

### Publicité / passerelles

Passe par le backend (`hektor_bridge.py`), pas par un worker. Inchangé.

### À trancher — les gestes d'administration

`change_hektor_annonce_status`, `archive_hektor_annonce`, `restore_hektor_annonce`,
`delete_hektor_annonce`, `assign_hektor_annonce_negotiator`.

**Proposition : les garder immédiats.** Ils sont rares et on veut en voir l'effet — archiver un bien
qui resterait affiché comme actif pendant quinze heures serait déroutant. Le statut conditionne en
outre la publicité. *(Décision de Frédéric attendue.)*

---

## 6. Ce que ce Temps 1 ne traite pas

- **La vitesse d'affichage pure du front.** `App.tsx` fait 37 200 lignes, dont un composant `App()`
  de 8 035 lignes avec 224 variables d'état. R1 + R2 + R4 supprimant la quasi-totalité des
  rechargements, **mesurer d'abord** avant de décider d'y toucher.
- **Le rangement des 137 champs** (§3) — chantier à froid.
- **Le réveil du backend Render** au premier clic.
- **Les photos** (C9) — prérequis irréversible de la coupure.
- **Le rapatriement** des documents archivés / historiques / brouillons (voie C).
- **La sauvegarde** — `NOTE_BRIEF_SAUVEGARDE_2026-08-18.md`, échéance dimanche 23/08.

---

## 7. Comment tester — méthode du bien témoin

1. **Vitesse** — chronométrer l'ouverture d'une fiche. Attendu : de plusieurs secondes à immédiat.
2. **Saisie protégée (R3)** — saisir sans enregistrer, laisser un job se terminer en parallèle :
   **la saisie est toujours là**. C'est le test du bug.
3. **Silence au repos (R2)** — onglet réseau, fiche ouverte, aucun job : **zéro requête récurrente**.
4. **Le calque tient (R1 + §3)** — modifier une description, enregistrer, rouvrir la fiche :
   **la valeur est toujours affichée**. C'est le test qui valide qu'on peut garder le calque.
5. **Convoi (R4)** — modifier un prix, vérifier que **rien ne part dans la journée**, puis que la
   valeur est bien dans Hektor après 05:15, et **toujours dans l'app après 06:30**.
6. **Bouton « Envoyer maintenant »** — modifier un prix, cliquer, vérifier l'arrivée dans Hektor
   en quelques minutes.
7. **Bouton « Actualiser depuis Hektor »** — modifier le bien dans Hektor, cliquer, la valeur arrive.
8. **Conflit visible (R5)** — modifier des deux côtés, vérifier qu'un **message** apparaît.
9. **Non-régression rapprochement** — une édition de prix ou de surface recalcule les correspondances.

⚠️ **Signature** : tests uniquement avec `frederic.gerphagnon@` comme signataire. Jamais de vrais
mandants — chaque procédure est facturée.

---

## 8. Ordre d'exécution

| # | Action | Risque | Réversible | Quand |
|---|---|---|---|---|
| **1** | **R3** — corriger la purge de saisie | nul | ✅ | tout de suite, c'est un bug |
| **2** | **R1** — retirer le rafraîchissement à l'ouverture + bouton « Actualiser » | faible | ✅ | |
| **3** | **R2** — sonder seulement si un job est en cours | faible | ✅ | avec R1 |
| **4** | **R4** — convoi de nuit + bouton « Envoyer maintenant » | moyen | ✅ | |
| **5** | **R5** — conflit notifié au lieu d'être silencieux | faible | ✅ | avec R4 |
| **6** | Adapter les seuils de surveillance au rythme nocturne | faible | ✅ | **avec R4, pas après** |
| **7** | Requalifier le calque *(documentation + commentaires)* | nul | ✅ | avec R1 |
| **8** | **Mesurer** la vitesse réelle → décider pour le front | — | — | après 1-7 |
| **9** | Créations allégées + identité côté app | moyen | ⚠️ | après décision §4 |
| **10** | Bascule des négociateurs sur l'app | — | — | quand 1-8 sont validés |
| **11** | Registre de mandats, Yousign, passerelles en propre | — | — | les quelques semaines |
| **12** | Couper : arrêter d'envoyer **et** d'importer, le même jour | — | — | fin |

Les points **1 à 3 ne changent rien** à ce qui part vers Hektor : faisables, testables et annulables
indépendamment de toute décision sur le convoi.

**Le point 6 n'est pas optionnel** : un worker qui ne tourne plus qu'une fois par nuit déclenchera
des alertes de fraîcheur calibrées sur un rythme continu. Point J de la revue externe :
*« à traiter en même temps que l'allumage du lot, pas après. »*

---

## 9. Ce qui reste à trancher

1. **Les gestes d'administration** (§5) — immédiats ou en convoi ? *Proposition : immédiats.*
2. **L'identité côté app pour les créations** (§4) — décision structurante, conditionne le point 9
   de l'ordre d'exécution.
3. **Yousign en tête des trois remplacements ?** Le trou de la mise à la signature (§5) le plaide.
4. **Le message aux négociateurs** — ce qu'ils font dans l'app, ce qui reste dans Hektor
   (la signature), et pour combien de temps.

---

## 10. Rappels de conduite

- **Rien n'est codé sans feu vert explicite.** Cette note est une proposition.
- Stager fichier par fichier, jamais `git add .`.
- ⚠️ **Ne pas faire `git commit -a`** : l'index porte 12 suppressions stagées de notes stratégiques,
  encore récupérables par `git show HEAD:<chemin>`.
- Valider le front avec `npm run build` (= ce que fait Vercel), jamais `tsc --noEmit`.
- Vérifier sur un bien de test avant tout déploiement.
- Les 4 services worker partagent `console_job_worker.js` : redémarrer **tous** les services après
  une modification, pas un seul.
