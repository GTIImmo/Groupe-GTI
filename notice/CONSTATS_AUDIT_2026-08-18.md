# Constats d'audit — 18 août 2026

**Ce document ne contient AUCUN plan.** Uniquement les faits établis et vérifiés, pour ne pas
avoir à les redécouvrir. Chaque point indique où il a été constaté.

---

## 1. Deux dépendances qui ne se remplacent pas par du code

### La signature électronique appartient à Hektor

Toutes les opérations passent par une adresse Hektor (`mode=ImmoSign-downloadProcedureZip`,
`ImmoSign-remindProcedureSignatories`, annulation) — `Console/console_job_worker.js`.

Surtout : le jeton d'accès au prestataire est **extrait d'une iframe à l'intérieur de Hektor**
(`issueToken=` dans l'URL de l'iframe `mylegitech|immo-sign`, cf. `Console/immosign_*.js`).
Les appels directs à `api.immo-sign.com` ne marchent qu'avec ce jeton emprunté.

→ **L'abonnement est celui de Hektor.** Aucune continuité possible avec le même prestataire sans
contrat en propre. À contrôler un jour : valeur juridique / conservation de la preuve des mandats
déjà signés, et **présence des PDF signés dans le lot rapatrié** (jamais vérifiée).

### La diffusion portails aussi

`backend/app/services/hektor_bridge.py` ne fait que poser un drapeau `diffusable` sur l'annonce.
La syndication vers Le Bon Coin & co. est faite par Hektor via **ses** abonnements portails.

---

## 2. Les fichiers

- **Quatre index d'annonces**, pas seulement les actives : 13 212 actives, 34 450 archivées,
  8 802 historiques, 403 brouillons = **56 867**.
- **Documents des annonces actives : rapatriement TERMINÉ** — 21 136 fichiers, 33 Go sur le
  serveur, 772 Go libres. (Estimation initiale 25 Go : réel 33 Go, donc **mesurer un échantillon**
  avant de lancer les 34 450 archivées.)
- **Photos : 1 355 seulement.** Et pour la plupart des biens **l'inventaire des photos n'existe
  pas encore** : c'est **deux opérations** (inventorier, puis télécharger), pas une.
- Incidents documents : 61 jobs en erreur sur 58 annonces, mais **57 annonces ont malgré tout tous
  leurs documents** ; une seule est vide. Causes : 223 fichiers refusés par le cloud (types MIME —
  **ils sont sur le serveur**, seule la copie distante échoue) et 29 sessions Hektor expirées
  (se rejouent).

---

## 3. Réactivité — mesures réelles

Durées des jobs réussis, du dépôt à la fin :

| Geste | médiane | 90e centile | pire cas |
|---|---:|---:|---:|
| **Créer une annonce** | **57 s** | 146 s | **861 s (14 min)** |
| Changer le statut | 39 s | 151 s | 407 s |
| Envoyer un document | 17 s | 32 s | 66 s |
| Modifier des champs *(optimiste, non ressenti)* | 13 s | 41 s | 109 s |

- **Quatre gestes sont déjà instantanés** : modifier un bien, un contact, une recherche
  (`app_edit_*_optimistic`).
- **La création ne l'est PAS**, malgré `PROVISIONAL_CREATION_ENABLED = true` : la ligne provisoire
  apparaît dans le listing mais **n'est pas ouvrable** — `App.tsx:20202` et `:20209` :
  `if (item.is_provisional) return`. C'est un repère visuel, pas une annonce utilisable.
- **Verrou par annonce** (`App.tsx:11727`) : tant qu'un job `delete`/`archive`/`restore`/
  `change_status` tourne sur un bien, les trois autres sont refusés. Invisible aujourd'hui
  (quelques secondes) — **mais incompatible avec un envoi groupé 2×/jour**, où il durerait 12 h.
  Tout regroupement suppose de le remplacer d'abord par une file ordonnée.
- **Fiabilité en nette amélioration** : taux d'échec des actions utilisateur **15 % sur tout
  l'historique → 3,9 % depuis le 1er juillet** (254 actions, 10 échecs). Dernier échec de
  modification de bien : 30/06.
- Le login Hektor à froid coûte ~30 s, **payées à chaque action** aujourd'hui.

---

## 4. Recherches acquéreur — défaut réel, dormant, à ne PAS corriger tel quel

- L'app ne reçoit que les recherches **actives** (`push_contacts_to_supabase.py:533`,
  `WHERE is_active = 1`), mais `search_index` compte le tableau **complet**, archivées comprises
  (`build_contacts_layer.py:820`). Résultat : **6 contacts** ont leur unique recherche active à
  l'index 1 ou 2.
- **L'API Hektor ne fournit aucun identifiant de recherche** (vérifié sur 256 recherches : seules
  les clés `archive/criteres/offre/particularites/quartiers/types/villes` existent).
- Le seul `idCritere` vient du grattage HTML de la console, dont **l'énumération est fausse** :
  le motif `rel=["'](\d{3,9})` ramasse tout nombre de la page — **11 « recherches » comptées pour
  un contact qui n'en a qu'une**. Cet `idCritere` n'est donc pas une base fiable.
- **Aucun dégât à ce jour** : 2 suppressions et 27 modifications, toutes sur l'index 0.
- ⚠ **Ne pas poser de garde-fou strict** : pour ces 6 contacts, le repli `|| list[0]` tombe
  peut-être juste ; un `throw` casserait un cas légitime. *(Garde-fou écrit puis annulé le 18/08.)*
- Le défaut disparaît de lui-même le jour où l'app cesse d'envoyer les recherches à Hektor.

---

## 5. Pièges à ne pas rejouer

### L'adresse privée : ne PAS la persister

`app_edit_annonce_optimistic` n'a **aucune** entrée pour `adresse`/`villeprivee`/`codeprive`.
Ce n'est **pas un oubli** : Hektor **compose** l'adresse privée (rue + `ADRESSE_COMPL`) —
cf. `App.tsx:1344` et `:21829`. La saisie entre sous `adresse`, la lecture sort sous
`adresse_privee_listing` / `adresse_detail`. Écrire la saisie dans le composé créerait une
divergence permanente. *(Un correctif avait été écrit sur cette base puis supprimé.)*

À la coupure seulement : rendre `ADRESSE_COMPL` saisissable, persister les composants, concaténer.
Aucune API tierce.

> **Signal général** : quand un champ est SAISI sous une clé et LU sous d'autres, c'est qu'une
> transformation existe entre les deux. L'absence de mappage direct n'est pas une lacune.

### Le blob annonce : ~55 clés sur ~130 sont de l'état Hektor VIVANT

Diffusion, offres, compromis, ventes, mandats, notes, photos. Les figer arrêterait la vie
commerciale des biens. *(Une décision « blob entièrement app-owned » avait été recommandée puis
retirée.)*

### Les éditions de l'app sont déjà protégées en pratique

Une modification faite dans l'app part chez Hektor en quelques minutes (calque optimiste) ; le run
de nuit rapporte ensuite **la même valeur** — il la confirme, il ne l'écrase pas. Constat
empirique : **25 modifications de contact depuis l'origine, aucun incident**.
Il existe par ailleurs une arbitrage par date à plusieurs niveaux (ingestion `sync_raw.py:1001`,
refetch détail, anti-régression normalize, garde-fou de push `base_snapshot._date_maj`).

→ Une mécanique de « propriété par champ » n'est pas nécessaire : **envoi et import se coupent
ensemble**.

---

## 6. Supervision et sauvegarde — deux trous

### La supervision ignore ce qui n'a JAMAIS émis

`monitoring/check_gti_health.py:683` : un automate sans `last_success_at` est rangé dans une liste
`never` puis `continue`. **Seul le retard (`stale`) fait monter la sévérité.** Un automate inscrit
mais jamais branché reste donc invisible **pour toujours**.

**Quatre automates actifs sont dans ce cas** : `backend.fastapi` (criticité *high*, seuil 3 h —
aucun code de heartbeat dans `backend/app`, alors qu'il **expose déjà `/health`**, `main.py:57`),
`console.worker.sync_full`, `contacts.detail_backfill.wrapper`, `console.worker.matterport`.

### La sauvegarde n'a jamais été restaurée

Elle tourne chaque nuit depuis le 17/08 (`phase2/sync/backup_critical.py`, 13 tables critiques).
Tant qu'une restauration n'a pas été faite pour de vrai, **on ne sait pas qu'elle fonctionne**.

---

## 7. État du système (relevé le 18/08)

| | |
|---|---|
| Code | ~148 000 lignes (front 51k, Console 64k, phase2 18k, backend 14k) |
| Base | 107 tables/vues, 91 procédures |
| Automates | 35 suivis, dont 9 critiques |
| Run de nuit | 22 étapes, 04:01 → 04:28 (27 min), réussi le 18/08 |
| Contacts | 57 525 |
| Mandats au registre | 23 836 |
| Rapprochements | 46 450 |
| Ledger d'affaires | 28 979 |
| Ventes DVF | 83 942 |
| Agences / négociateurs | 19 / 152 dont **30 actifs** |

**Indépendant de Hektor déjà** : rapprochement, avis de valeur, ledger d'affaires, espace client,
agenda, relances, Matterport, Google Workspace, IA, données publiques (DVF/IGN/Géorisques) — et
les fichiers déjà rapatriés.

**Dépend encore de Hektor** : signature, diffusion portails, photos non rapatriées, numéros de
mandat, référentiels (agences/négociateurs/nomenclatures), fiche publique et logo du site
partenaire.

---

## 8. Code modifié pendant cette période (traçabilité)

- `310ee99` (08/08) — `App.tsx`, 6 lignes : fiche contact V2 rafraîchie quand ouverte par-dessus
  une annonce *(demandé)*.
- `d4bff42` (17/08) — `run_full_pipeline.ps1` : Matterport non bloquant (retry + heartbeat)
  *(demandé)*.
- `70b2b09` (17/08) — sauvegarde des données locales irremplaçables.
- `4cc7936` (18/08) — téléchargement des photos + accès aux 4 index.

Écrit puis **entièrement annulé** le 18/08 (empreintes vérifiées identiques au commit) :
provenance par champ des contacts + soustraction dans `push_contacts_to_supabase.py`, et garde-fou
de ciblage des recherches dans `console_job_worker.js`.
