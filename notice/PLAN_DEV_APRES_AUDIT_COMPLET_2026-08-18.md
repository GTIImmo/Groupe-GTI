# Plan de développement — après audit complet (18 août 2026)

**Remplace `NOTE_PLAN_DEV_PHASES_2026-08-17.md` et `NOTE_PLAN_DEV_PHASES_2026-08-18.md`.**
Artefact : *Plan de développement — Indépendance Hektor*.
Tous les chiffres relevés en base le 18/08 ; dépendances vérifiées dans le code.

---

## Erreur de méthode corrigée

Les plans précédents empilaient les chantiers de développement.
**Le chemin critique n'est pas le développement** : ce sont deux dépendances **contractuelles**
qu'aucune ligne de code ne remplace. Elles fixent la date de coupure.
**Décision du 18/08 : elles seront traitées après la voie B.**

---

## Les trois constats qui déplacent le plan

### 1. La signature électronique appartient à Hektor *(majeur, nouveau)*

Toutes les opérations observées dans `Console/console_job_worker.js` passent par une adresse
Hektor : `mode=ImmoSign-downloadProcedureZip` (récupération du PDF signé),
`mode=ImmoSign-remindProcedureSignatories` (relance), annulation idem.

Et surtout : les scripts d'exploration (`Console/immosign_*.js`) montrent que le jeton d'accès
au prestataire est **extrait d'une iframe à l'intérieur de Hektor** (`issueToken=` dans l'URL de
l'iframe `mylegitech|immo-sign`). **L'abonnement au service de signature est celui de Hektor,
pas celui de GTI.**

→ À la coupure, la signature s'arrête net. Il faut un **contrat en propre**, puis l'intégration.
C'est le délai le plus long du chantier, et il n'apparaissait dans aucun plan précédent.

### 2. La diffusion portails est un contrat, pas un branchement

`backend/app/services/hektor_bridge.py` ne fait que poser un drapeau `diffusable` sur l'annonce.
La syndication vers Le Bon Coin & co. est faite par Hektor via **ses** abonnements portails.

→ Reprendre la diffusion = signer avec les portails (ou un diffuseur), puis produire les flux.
Décision commerciale d'abord.

### 3. La réactivité est plus avancée que je ne le disais *(bonne nouvelle)*

`PROVISIONAL_CREATION_ENABLED = true` (`api.ts:4703`) : **la création d'annonce est déjà
optimiste**, contrairement à ce que disait la note mémoire. Quatre gestes sont donc déjà
instantanés : modifier un bien, un contact, une recherche, et créer une annonce.

Fiabilité : taux d'échec des actions utilisateur **15 % sur tout l'historique → 3,9 % depuis le
1er juillet** (254 actions, 10 échecs). Dernier échec de modification de bien : 30/06.

---

## État vérifié le 18/08

| | |
|---|---|
| Code | ~148 000 lignes (front 51k, Console 64k, phase2 18k, backend 14k) |
| Base | 107 tables/vues, 91 procédures |
| Automates | 35 suivis, dont 9 critiques |
| Run de nuit | 22 étapes, 04:01 → 04:28 (27 min), réussi le 18/08 |

| Donnée | Volume |
|---|---:|
| Contacts | 57 525 |
| Annonces (4 index) | 56 867 |
| Mandats au registre | 23 836 |
| Rapprochements | 46 450 |
| Ledger d'affaires | 28 979 |
| Ventes DVF | 83 942 |
| Documents rapatriés | 21 136 (33 Go, 100 % des actives) |
| Photos rapatriées | 1 355 |
| Agences / négociateurs | 19 / 152 dont **30 actifs** |

**Survit à la coupure** : rapprochement, avis de valeur, ledger, espace client, agenda, relances,
Matterport, Google Workspace, IA, DVF — et les fichiers déjà rapatriés.

**S'arrête avec Hektor** : signature, diffusion portails, photos non rapatriées, numéros de
mandat, référentiels, fiche publique + logo.

---

## Trois voies en parallèle

### Voie A — APRÈS la voie B (décision Frédéric du 18/08)

> **Conséquence assumée** : la voie A est le seul délai extérieur. La traiter après la voie B
> additionne les durées au lieu de les recouvrir — la date de coupure recule d'autant.
> Contrepartie : on n'ouvre pas de contrat pendant qu'on paie encore Hektor.
>
> **Une exception en sort et rejoint la voie C** : vérifier que les **PDF signés sont bien
> rapatriés**. Ce n'est pas un contrat, c'est une preuve juridique hébergée chez Hektor —
> elle disparaît à la coupure et ne peut donc pas attendre.

- **A1 — Signature en propre.** Choisir le prestataire et contracter. Vérifier la valeur
  juridique des mandats déjà signés via Hektor et la conservation de la preuve.
  **Contrôler que les PDF signés sont bien dans le lot rapatrié** (jamais vérifié).
- **A2 — Diffusion portails.** Trancher : direct / diffuseur / **garder Hektor pour cela seul**
  (option légitime qui repousse la coupure sans bloquer le reste). Établir la liste exacte des
  données exigées — elle définit aussi le contenu minimal du convoi.

### Voie B — le développement

1. **Réactivité + convoi 2×/jour** — *en premier, sans elle personne ne bascule.*
   - terminer l'inventaire : restent documents, photos, statut, archivage, affectation
     négociateur, contacts mandants ;
   - basculer ce qui peut l'être (patron déjà éprouvé) ;
   - construire le convoi : contrainte d'**ordre** (créer → affecter → publier) et d'**identité**
     (jusqu'à **30 changements d'identité** par passage). Variante A (1 passage) puis B (2) ;
   - **restent immédiats** : mandats, diffusion, signature.
   - *Gain* : le login Hektor à froid (~30 s) est payé à chaque action aujourd'hui ; un convoi ne
     le paie qu'une fois par passage.
2. **Référentiels** — l'annuaire existe (216 lignes) mais est recopié de Hektor chaque nuit ;
   en faire une donnée que l'app administre. Figer les nomenclatures, réconcilier les listes
   divergentes de types de bien.
3. **Numérotation des mandats** — obligation légale, 23 836 mandats déjà numérotés ; l'app
   reprend la suite de la série.
4. **Fiche publique + logo** — court, sans dépendance extérieure.
5. **Composition de l'adresse** — le jour J. Voir `NOTE_ADRESSE_PRIVEE_NE_PAS_PERSISTER_2026-08-17.md`.

### Voie C — temps machine

Documents : actives ✅ terminé (21 136 / 33 Go). Restent archivées (34 450), historiques (8 802),
brouillons (403). **Mesurer un échantillon avant de lancer** (33 Go réels vs 25 estimés).
Photos : **deux opérations** — inventorier, puis télécharger. L'inventaire n'existe presque pas.

---

## Hors développement — les interrupteurs

Protéger les saisies de l'app **ne demande aucun code**. Envoi et import sont les deux bouts du
même tuyau : une modification faite dans l'app part chez Hektor en quelques minutes, et le run de
nuit rapporte la même valeur — il la confirme. Le jour où l'on arrête de pousser, **on arrête
d'importer**. Pendant la phase de test, il est même souhaitable que Hektor garde la main.

- **À la bascule** : couper l'import de nuit ; réduire le convoi au nécessaire.
- **Règle permanente** : ne rien retirer dont un automate se sert pour viser Hektor
  (`hektor_annonce_id`, `hektor_contact_id`, `idUser`, `search_index`, `base_snapshot`).

---

## Angles morts trouvés par l'audit

| Sévérité | Point |
|---|---|
| 🔴 | **La sauvegarde n'a jamais été restaurée.** Elle tourne depuis le 17/08 ; tant qu'un essai de restauration n'a pas été fait, on ne sait pas qu'elle fonctionne. |
| 🔴 | **Angle mort de la supervision : ce qui n'a JAMAIS émis n'alerte pas.** `check_gti_health.py:683` range ces automates dans une liste `never` puis `continue` ; seul le retard (`stale`) fait monter la sévérité. Un automate inscrit mais jamais branché reste donc invisible **pour toujours**. |
| 🔴 | **`backend.fastapi` (criticité *high*, seuil 3 h) n'émet aucun battement** — aucun code de heartbeat dans `backend/app`. Si l'API tombe (hébergée sur Render), personne n'est prévenu. Elle expose pourtant `/health` (`main.py:57`) : une sonde externe suffit — c'est le « reste sondes externes » déjà noté au palier 1 du monitoring. |
| 🟠 | **4 automates actifs n'ont jamais émis** : `backend.fastapi`, `console.worker.sync_full`, `contacts.detail_backfill.wrapper` (high), `console.worker.matterport` (medium). À brancher ou à retirer du registre. |
| ⚪ | Ciblage des recherches acquéreur — dormant, aucun dégât, disparaît à la bascule. Voir mémoire `recherches-index-actives-vs-complet`. |
| ⚪ | 223 documents refusés par le cloud (types MIME) ; présents sur le serveur. |
| ⚪ | 29 sessions Hektor expirées sur 21 136 documents ; se rejoue. |

---

## Ce qui a été codé pendant l'étude (traçabilité)

- `310ee99` (08/08) — App.tsx, 6 lignes : correctif fiche contact V2 *(demandé)*.
- `d4bff42` (17/08) — `run_full_pipeline.ps1` : Matterport non bloquant *(demandé, « GO OPTION A »)*.
- `e161020` (17/08) — documentation seule.
- `70b2b09` (17/08) — sauvegarde des données locales irremplaçables.
- `4cc7936` (18/08) — téléchargement des photos + accès aux 4 index.

Écrit puis **entièrement annulé** le 18/08 (empreintes vérifiées identiques au commit) :
provenance par champ des contacts, soustraction dans `push_contacts_to_supabase.py`, garde-fou de
ciblage des recherches dans `console_job_worker.js`.
