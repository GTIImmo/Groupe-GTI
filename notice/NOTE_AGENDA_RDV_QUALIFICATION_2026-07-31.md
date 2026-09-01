# Note de cadrage — Qualification des RDV Google Agenda saisis par les négociateurs

**Date : 2026-07-31 · Statut : cadrage validé, développement NON commencé (en attente du go par lot)**

---

## 1. Objectif

Les négociateurs saisissent d'abord leurs rendez-vous **directement dans Google Agenda**, en texte libre. Aujourd'hui l'app ne voit ces créneaux que comme « occupés » : elle ne sait ni de quel type de RDV il s'agit, ni pour quel contact, ni pour quel bien.

Le but : que l'app **lise ces RDV, les qualifie (type + contact + bien) et les rende exploitables** — jusqu'à **orienter le négociateur vers la bonne action métier** (faire l'estimation, éditer le bon de visite…). Le RDV cesse d'être un simple créneau : il devient le **déclencheur** du travail métier.

## 2. Contrainte absolue — feature 100 % additive

**On ne retire rien et on ne casse rien.** En particulier, restent inchangés :

- la **création de RDV depuis l'app → poussée dans Google Agenda** (flux app→Google actuel) ;
- toutes les fonctions actuelles (cockpit, mandats, estimations, rapprochement, diffusion, mails, workers, prise de RDV publique QR…).

Le projet **ajoute** uniquement le flux inverse Google→app (ingestion + qualification + orientation). Cf. règle projet « ne pas écraser le code existant ».

## 3. Ce qui existe déjà et sera réutilisé (rien à réinventer)

Le socle Google Workspace et **le modèle de qualification sont déjà en base et fonctionnels** :

| Brique existante | Détail |
|---|---|
| **Délégation domaine (DWD)** | `backend/app/services/google_workspace_service.py` + compte de service `secrets/google-workspace-service-account.json`, `.env` configuré, `google-auth` OK. Scopes actifs : `gmail.send`, `calendar.freebusy`, `calendar.events`, `gmail.readonly`. |
| **Table de liaison qualifiée** | `app_google_calendar_event_link` : `event_type` (**`visite\|estimation\|mandat\|compromis\|relance\|agence\|autre`** = le **type/POURQUOI**), `hektor_contact_id` (= **QUI**), `hektor_annonce_id` / `app_dossier_id` (= **QUOI**), `google_event_id`, `attendees_json`, `metadata_json.attendee_contacts`, `status`. |
| **Endpoints** | `routers/google_workspace.py` : `POST /calendar/events` (crée dans Google **+** enregistre le lien qualifié), `PATCH /calendar/events/{id}`, `DELETE`, `GET /calendar/events` (relit les liens, droits admin/manager/négo scopés via `assert_calendar_subject_allowed`). |
| **Service de liaison** | `google_calendar_event_link_service.py` : `create_link` / `update_link` / `list_links` / `mark_deleted`. |
| **Journalisation** | `app_google_workspace_action_log` (audit des appels). |

**Conséquence clé :** les 3 ancres de qualification (type / contact / bien) ont **déjà** leurs colonnes. On écrit dans un modèle prêt.

## 4. Le seul manque réel = l'ingestion des événements « orphelins »

`GET /calendar/events` lit la **table de liens**, pas Google. Donc il ne voit **que les RDV créés par l'app**. Un RDV **tapé à la main dans Google** par le négociateur n'a **aucune ligne de lien** → il est **invisible**.

L'ajour se résume à **une brique d'ingestion** : appeler `events.list` sur l'agenda du négociateur, écarter ce qui est déjà connu, et faire passer le reste dans l'entonnoir de qualification.

### 4.1 Nouvelle méthode à ajouter au service
`GoogleWorkspaceService.list_calendar_events(subject_email, time_min, time_max, page_token=…)` :
- appelle `GET https://www.googleapis.com/calendar/v3/calendars/primary/events` avec `singleEvents=true`, `orderBy=startTime`, pagination, `syncToken` en incrémental (v2) ;
- réutilise `_delegated_access_token(subject_email, [calendar.events])` (déjà présent) ;
- journalise dans `app_google_workspace_action_log` (action `calendar.events.list`).

### 4.2 Traitement à l'ingestion (par origine)
- **Événements déjà liés** : ceux dont le `google_event_id` existe déjà dans `app_google_calendar_event_link` → on ne re-traite pas (RDV créés par l'app).
- **Couche Netty — NE PAS IGNORER (révision 2026-07-31)** : événements `creator.email == netty.fr@gmail.com` (« Visite N° … », `extendedProperties.private = {event_id, nego, username, is_shared}`). Ce sont de **vrais RDV**, poussés par le CRM tiers en cours de remplacement, et **mieux structurés que la saisie manuelle** : ils portent le **type** (Visite) + une **adresse propre** (69/69 avec `location` renseignée). Vérifié : le numéro « Visite N° 17910 » est une **réf. interne Netty**, PAS un `hektor_annonce_id` (id Hektor 6→62819, 17910 absent ; pas de match dossier/mandat) → le **rattachement du bien se fait par l'ADRESSE**, pas par le numéro.
  - **On les ingère comme source complémentaire** : ils donnent bien+type propres, il leur manque le **client** (QUI) → entonnoir pour le contact seulement.
  - **Déduplication avec le jumeau manuel** : double saisie mesurée (33 jours avec RDV Netty **et** RDV manuel le même jour). Fusion → **Netty apporte bien+type, le manuel apporte client+téléphone** = 1 seul RDV qualifié (tue le doublon).
  - **Ancre = l'événement du négociateur** quand un jumeau existe (il **survit** à la coupure Netty) ; un RDV Netty **sans** jumeau → on qualifie l'événement Netty (client manquant → question).
  - **Pont transitoire** : le flux Netty s'éteindra avec le CRM ; on l'exploite pendant la bascule (continuité des RDV dès J1 + adresses propres pour bootstrapper le rapprochement bien), **sans** dépendance permanente.

## 5. L'entonnoir de qualification

Passe **tous** les événements ingérés. À chaque étape : soit l'app tranche, soit elle pose **une question ciblée** au négociateur (bannette « À qualifier »).

```
Événement Google ingéré
   │
   ├─ ① Perso ou pro ?
   │      perso → ignoré · pro → étape ② · doute → question
   │
   ├─ ② Type (POURQUOI/action) : visite / estimation / mandat / compromis / relance / autre
   │      déterminé → étape ③ · doute → question
   │
   ├─ ③ Contact (QUI) — MINIMUM REQUIS
   │      trouvé (tél/nom) → rattaché · absent/inconnu → question
   │
   └─ ④ Bien / annonce (QUOI) — rattaché si présent, NON bloquant
```

**Règle de complétude :** `type + contact` = RDV **valable** (l'action peut être proposée) ; `+ bien` = RDV **complet**.

**Cas estimation en amont (décision arrêtée) :** pas encore de bien/mandat → l'app tente d'abord de **matcher un bien par l'adresse** ; si rien, elle **propose « Créer le dossier d'estimation »** (1 clic, pré-rempli contact+adresse). **Jamais de création silencieuse** (évite les dossiers fantômes sur RDV annulés/no-show). Le RDV devient ainsi le point d'entrée qui enclenche l'objet.

**Défaut de classification (décision arrêtée) :** tout RDV **clairement perso** est ignoré (étape ①) ; tout RDV **ambigu** (ni clairement perso ni clairement pro) va **TOUJOURS en « à qualifier »** — jamais ignoré en silence. Conséquence assumée : volume élevé sur les profils bruités (ex. Gonzalez ~73 % « autre »), maîtrisé par (a) la mémoire libellés+récurrents et (b) des actions groupées dans la bannette (§8). Option de repli si débordement : ne remonter que si signal pro (tél/adresse/contact connu) — non retenue pour l'instant.

## 6. Le parser / classifieur (signaux)

Basé sur les données réelles (4 négociateurs, 12 mois — voir §11) :

- **Type** : mots-clés du libellé (`visite`, `estim(ation)`, `mandat`, `compromis`/`signature`/`acte`, `offre`, `edl`…). Défaut robuste + apprentissage des libellés récurrents.
- **Perso/non-métier** : liste d'exclusion (`permanence`, `pub`/`dipso`, `perso`, `anniv`, `repas`, `banque`, `médecin`, `rdv tél` interne…).
- **Contact (QUI)** : le **téléphone dans le titre est la clé de rapprochement forte** (présent 2–25 % des titres) → match sur le CRM ; sinon le **nom**. L'invité Google est majoritairement un **collègue**, pas le client → ne **pas** s'y fier seul.
- **Bien (QUOI)** : **adresse** dans le titre/lieu → match annonce ; sinon rattachement différé.
- **Confiance** : sous un seuil, on ne devine pas → question. Ne jamais créer un lien à faible confiance (même philosophie que le moteur de rapprochement).

### Mémoire des réponses
- Réponse mémorisée par **libellé** (l'app apprend : « permanence » = perso).
- Sur un **événement récurrent**, la réponse marque **toute la série** → jamais reposée (ex. réel : 236 « permanence » récurrentes chez un négociateur). L'entonnoir se **resserre avec le temps**.

## 7. Google Contacts (People API) — synchronisation BIDIRECTIONNELLE (décidé 2026-07-31)

**Décision** : intégration Google Contacts complète et **bidirectionnelle**, pas seulement pour les RDV. Double but : (a) **remplir la base contacts pro** dans les deux sens → beaucoup moins de RDV non affectés ; (b) confort négociateur (caller-ID, auto-complétion, invitation facile). Même délégation domaine que l'Agenda (le backend impersonne chaque négociateur).

### 7.1 Frontière = le COMPTE PRO (pas de libellé)
Le compte **@gti-immobilier.fr est pro par nature** → **tout son carnet Google Contacts = zone pro partagée** avec le CRM. **Pas de libellé** « GTI ». Les contacts **perso** restent sur le **compte perso** du négociateur (sa responsabilité). *(Hygiène de mise en route : prévenir les négociateurs de garder le perso hors du compte pro ; au 1er sync, tout le carnet pro remonte.)*

### 7.2 Les deux sens
- **App → carnet pro (push) — TEMPS RÉEL** : dès qu'un contact change dans le CRM, écriture immédiate dans le carnet Google pro → **caller-ID** (nom affiché à l'appel), **auto-complétion**, **invitation facile** en RDV (= lien parfait).
- **Carnet pro → App (pull) — QUASI TEMPS RÉEL (60s)** : ⚠️ Google **ne fournit pas de webhook pour les contacts** (contrairement à Gmail/Agenda). Donc lecture **incrémentale toutes les 60s** (`syncToken`, deltas seulement, léger). Un contact saisi sur le tél est dans l'app en ~1 min.

### 7.3 Règle d'entrée au pull — 3 issues
- **Propre** (nom + téléphone valide FR + numéro inconnu du CRM) → ✅ **auto-créé** dans le CRM.
- **Trop pauvre** (pas de tél / numéro invalide / pas de nom exploitable) → 🚫 **EXCLU** (tracé dans un log d'audit, aucune action demandée).
- **Déjà connu** (le tél matche un contact CRM) → 🔗 pas un nouveau → règles de conflit ci-dessous.

### 7.4 Conflits — hybride D + mémoire des valeurs
Clé anti-doublon = **le numéro de téléphone**.
- **Champ vide au CRM** → le carnet le remplit tout seul (auto).
- **Champ déjà rempli ET différent** → **« à valider »** (un clic pour choisir) ; **jamais d'écrasement silencieux**.
- **Mémoire** : toute modification **archive la valeur précédente** (historique : champ, ancienne valeur, nouvelle, source, date). Ex. affiché sur la fiche : *« Tél : 06 99… — précédent : 06 12… (31/07, depuis le tél de Legrand) »*. **Rien n'est jamais détruit.**

### 7.5 Gouvernance / RGPD
Les contacts vivent dans le **compte pro géré par le domaine Workspace** → **l'entreprise contrôle** : au départ d'un négociateur, désactivation du compte = données parties (propre). Nettement plus sain que des données sur un tél perso non maîtrisé. *(Reste à cadrer avant activation : note d'information aux négociateurs + politique appareils.)*

### 7.6 Technique
- Scopes (Lot 0) : **`https://www.googleapis.com/auth/contacts`** (lecture **+** écriture, car bidirectionnel) + activer **People API**.
- Push : `people.createContact` / `updateContact`. Pull : `people.connections.list` + `syncToken` (incrémental 60s).
- **Table de correspondance** `app_google_contact_link` : `crm_contact_id ↔ google_resource_name ↔ negociateur_email ↔ etag/sync_state`.
- **Historique** `app_contact_field_history` (mémoire des valeurs) : `contact, champ, ancienne, nouvelle, source, date`.
- **Worker de sync** (pull 60s) + push déclenché sur changement CRM. DWD par négociateur.

## 8. UI — où le négociateur voit ses RDV

- **Incomplets → bannette « À qualifier »** sur l'écran d'accueil (badge compteur). Chaque ligne indique **précisément l'ancre manquante** et propose l'action : *« Visite machin — il manque le bien. [Compléter] »*. Compléter se fait **dans l'app** (mini-formulaire qui/quoi/pourquoi) ; l'app **réécrit** proprement dans Google (l'app devient la source du lien).
- **Gestion du volume (requis vu « toujours à qualifier »)** : multi-sélection + **actions groupées** (« tout marquer perso », « ignorer la série »), tri par confiance, et **apprentissage** (libellé/série résolu une fois → auto-classé ensuite) pour que la bannette se vide vite.
- **Complets → cockpit du bien/contact**, rubrique **Rendez-vous** + timeline **Activité** (briques maquettes cockpit v28-agenda / v30-ajout-rdv déjà prévues).
- **Manager → reporting de complétude** par négociateur (`completeness_score`, couche `app_alert`/notifications). Reporting périodique plutôt que relance RDV par RDV.

## 9. Orientation → tâche métier (la finalité)

Une fois les 3 ancres réunies, mapping type → action proposée :

| Type | Action proposée |
|---|---|
| Estimation | Créer le dossier d'estimation → faire / éditer l'avis de valeur (PDF) |
| Visite | Générer le **bon de visite** (contact + bien pré-remplis) → compte-rendu |
| Mandat | Éditer le mandat (chaîne PDF + signature existante) |
| Offre | Saisir l'offre → suivi offre/compromis |
| Compromis / signature | Checklist pièces + rappel notaire |

## 10. Relance & reporting

- **Relance douce graduée** : rappel in-app J+0, notification J+1 ; si toujours incomplet, entrée dans le **reporting hebdo manager**.
- **Pas de harcèlement** RDV par RDV ; le manager voit un **tableau de complétude** (ex. profils très hétérogènes : un négociateur ~90 %, un autre ~40 %, un troisième ~5 %).

## 11. Données d'appui (extraction lecture seule, 12 mois)

Profils très hétérogènes → concevoir pour la diversité, pas pour un profil moyen :
- **Teyssonnier** : riche (nom+tél+adresse+prix), 25 % de titres avec téléphone → excellent parsing.
- **Legrand** : riche mais brouillon (minuscules, fautes), 15 % tél.
- **Gonzalez** : très gros volume (~6 800 événements/an), ~73 % de bruit → filtre anti-bruit indispensable.
- **Delavaud** : n'utilise quasiment pas l'agenda (28 RDV/an) → pour lui, le flux inverse (créer depuis l'app) prime.

Champs structurés Google quasi jamais utilisés (lieu 0–7 %, invité 0–1 %) → **le parsing du texte libre est la seule voie ; un add-on à menus déroulants serait ignoré.**

## 12. Découpage en lots proposé (à valider avant chaque lot)

- **Lot 0 — Débloquer + choisir le négo test** : activer People API + scope **`contacts` (lecture+écriture, car sync bidirectionnelle)** (console admin DWD) *(action Frédéric, hors code)* ; **démarrage sur UN SEUL négociateur test** (ex. Legrand) avant tout élargissement.
- **Lot 1 — Ingestion** : `list_calendar_events` + endpoint `POST /calendar/ingest` (pull d'un négo, exclusion des `google_event_id` **déjà liés** uniquement ; **Netty ingéré**, marqué `source=netty`), écriture des événements bruts dans une table de staging. Aucun impact UI.
- **Lot 2 — Classifieur** : parser type + perso/pro + extraction tél/adresse ; score de confiance ; test sur les vrais titres (mesure du taux d'extraction).
- **Lot 3 — Rapprochement + dédup** : contact (tél/nom) + bien (adresse) → écriture dans `app_google_calendar_event_link` ; **déduplication Netty ↔ manuel** (même jour/adresse → 1 RDV, ancre = événement du négociateur) ; mémoire des réponses + récurrents.
- **Lot 4 — UI « À qualifier »** : bannette accueil + mini-formulaire de complétion (réécriture Google) ; rubrique Rendez-vous cockpit.
- **Lot 5 — Orientation** : mapping type → action métier.
- **Lot 6 — Relance + reporting manager**.
- **Lot 7 — Google Contacts (sync bidirectionnelle)** : push CRM→carnet pro (temps réel) + pull carnet→CRM (worker 60s, `syncToken`) ; règle d'entrée 3 issues (auto/exclu/déjà-connu) ; conflits hybride D + `app_contact_field_history` (mémoire des valeurs) ; tables `app_google_contact_link` + historique. *(après note d'info RGPD aux négociateurs — §7.5)*. **Fort effet sur la réduction des RDV non affectés** → peut être remonté plus tôt si prioritaire.

## 13. Décisions (arrêtées le 2026-07-31)

1. **Estimation en amont** — ✅ **ARRÊTÉ** : match adresse d'abord ; sinon **proposer** « Créer le dossier d'estimation » (1 clic, pré-rempli), jamais de création silencieuse.
2. **Complétion** — ✅ **ARRÊTÉ** : **dans l'app** (mini-formulaire) avec réécriture vers Google (l'app = source du lien).
3. **Défaut de classification** — ✅ **ARRÊTÉ** : RDV ambigu → **TOUJOURS « à qualifier »** (jamais ignoré en silence) ; volume maîtrisé par mémoire+actions groupées (§8) ; repli « signal pro » gardé en réserve.
4. **Google Contacts** — ✅ **ARRÊTÉ** : **sync bidirectionnelle**, frontière = le **compte pro** (pas de libellé) ; pull = auto / **exclu** (pauvres) / déjà-connu ; conflits **hybride D + mémoire des valeurs** ; **temps réel** (push instantané, pull 60s). Reste ⏳ **note d'info RGPD** aux négociateurs avant activation (§7.5).
5. **Périmètre** — ✅ **ARRÊTÉ** : démarrage sur **UN SEUL négociateur test** (ex. Legrand) avant élargissement.
