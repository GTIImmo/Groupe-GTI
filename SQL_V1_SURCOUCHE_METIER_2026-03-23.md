# SQL V1 surcouche metier

Date: 23/03/2026

## Objet

Cette note propose un schema SQL concret pour la V1 de la surcouche metier au-dessus de la base principale Hektor.

Le principe retenu :

- ne pas modifier les tables Hektor synchronisees
- ajouter des tables locales dediees a l'outil metier
- garder une separation nette entre :
  - donnees source Hektor
  - donnees internes
  - actions API

## Perimetre V1

Le schema ci-dessous couvre en priorite :

- demandes mandat / diffusion
- diffusion passerelles
- fiche dossier

Et il prepare aussi :

- suivi transaction
- pilotage global

## Tables locales recommandees

### 1. app_dossier

Table pivot locale par dossier / annonce.

```sql
CREATE TABLE IF NOT EXISTS app_dossier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hektor_annonce_id INTEGER,
    hektor_mandat_id INTEGER,
    numero_dossier TEXT,
    numero_mandat TEXT,
    commercial_id TEXT,
    commercial_nom TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hektor_annonce_id)
);
```

But :

- fournir un identifiant local stable
- servir d'ancrage a toutes les donnees internes

### 2. app_work_item

File de travail unifiee.

Une ligne = un sujet detecte ou cree a traiter.

```sql
CREATE TABLE IF NOT EXISTS app_work_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_dossier_id INTEGER NOT NULL,
    workflow_type TEXT NOT NULL,
    event_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    assigned_role TEXT,
    assigned_user TEXT,
    priority TEXT NOT NULL DEFAULT 'normal',
    detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_at TEXT,
    closed_at TEXT,
    reason TEXT,
    details_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_dossier_id) REFERENCES app_dossier(id)
);
```

Valeurs conseillees :

- `workflow_type`
  - `mandat_diffusion`
  - `diffusion_passerelle`
  - `transaction`
  - `manager_alert`

- `event_type`
  - `demande_diffusion`
  - `baisse_prix`
  - `annulation_mandat`
  - `mandat_non_diffuse`
  - `bien_non_visible`
  - `offre_recue`
  - `compromis_signe`
  - `offre_sans_compromis_delai_depasse`
  - `vente_delai_long`
  - `dossier_bloque`
  - `erreur_diffusion`

- `status`
  - `new`
  - `pending`
  - `in_progress`
  - `done`
  - `refused`
  - `cancelled`

### 3. app_note

Commentaires libres.

```sql
CREATE TABLE IF NOT EXISTS app_note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_dossier_id INTEGER NOT NULL,
    author_role TEXT,
    author_name TEXT,
    note_type TEXT NOT NULL DEFAULT 'general',
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_dossier_id) REFERENCES app_dossier(id)
);
```

Valeurs conseillees :

- `note_type`
  - `general`
  - `admin`
  - `diffusion`
  - `transaction`
  - `manager`

### 4. app_internal_status

Statut metier interne et prochaine action.

```sql
CREATE TABLE IF NOT EXISTS app_internal_status (
    app_dossier_id INTEGER PRIMARY KEY,
    internal_status TEXT,
    priority TEXT NOT NULL DEFAULT 'normal',
    next_action TEXT,
    last_action_note TEXT,
    updated_by TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_dossier_id) REFERENCES app_dossier(id)
);
```

Valeurs conseillees :

- `internal_status`
  - `a_controler`
  - `en_attente_commercial`
  - `pret_diffusion`
  - `a_relancer`
  - `bloque`
  - `suivi_manager`

- `priority`
  - `low`
  - `normal`
  - `high`
  - `urgent`

### 5. app_followup

Relances et actions planifiees.

```sql
CREATE TABLE IF NOT EXISTS app_followup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_dossier_id INTEGER NOT NULL,
    followup_type TEXT NOT NULL,
    target_role TEXT,
    target_user TEXT,
    planned_for TEXT,
    done_at TEXT,
    result_status TEXT,
    result_note TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_dossier_id) REFERENCES app_dossier(id)
);
```

Valeurs conseillees :

- `followup_type`
  - `relance_commercial`
  - `relance_admin`
  - `relance_transaction`
  - `relance_manager`

- `result_status`
  - `pending`
  - `done`
  - `no_answer`
  - `blocked`

### 6. app_blocker

Blocages identifies.

```sql
CREATE TABLE IF NOT EXISTS app_blocker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_dossier_id INTEGER NOT NULL,
    blocker_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,
    comment TEXT,
    FOREIGN KEY (app_dossier_id) REFERENCES app_dossier(id)
);
```

Valeurs conseillees :

- `blocker_type`
  - `piece_manquante`
  - `validation_refusee`
  - `erreur_diffusion`
  - `compromis_en_retard`
  - `vente_en_retard`
  - `dossier_incomplet`

- `status`
  - `open`
  - `resolved`

### 7. app_broadcast_action

Journal et file d'attente des actions API sur les passerelles.

```sql
CREATE TABLE IF NOT EXISTS app_broadcast_action (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_dossier_id INTEGER NOT NULL,
    hektor_annonce_id INTEGER NOT NULL,
    hektor_broadcast_id INTEGER,
    portal_key TEXT,
    action_type TEXT NOT NULL,
    requested_by TEXT,
    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'queued',
    api_response TEXT,
    error_message TEXT,
    executed_at TEXT,
    FOREIGN KEY (app_dossier_id) REFERENCES app_dossier(id)
);
```

Valeurs conseillees :

- `action_type`
  - `add`
  - `remove`

- `status`
  - `queued`
  - `sent`
  - `success`
  - `error`

## Index recommandes

```sql
CREATE INDEX IF NOT EXISTS idx_app_dossier_annonce
ON app_dossier(hektor_annonce_id);

CREATE INDEX IF NOT EXISTS idx_app_work_item_workflow_status
ON app_work_item(workflow_type, status, priority);

CREATE INDEX IF NOT EXISTS idx_app_work_item_dossier
ON app_work_item(app_dossier_id);

CREATE INDEX IF NOT EXISTS idx_app_note_dossier
ON app_note(app_dossier_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_app_followup_dossier
ON app_followup(app_dossier_id, planned_for);

CREATE INDEX IF NOT EXISTS idx_app_blocker_dossier_status
ON app_blocker(app_dossier_id, status);

CREATE INDEX IF NOT EXISTS idx_app_broadcast_action_status
ON app_broadcast_action(status, requested_at);
```

## Vues SQL recommandees

Les tables ci-dessus ne doivent pas etre affichees brutes dans l'interface.

Il faut leur ajouter des vues de lecture pretes a l'emploi.

### 1. app_view_demandes_mandat_diffusion

Vue pour Pauline.

Source logique :

- `case_dossier_source`
- `app_dossier`
- `app_work_item`
- `app_internal_status`
- dernieres `app_note`
- `app_blocker`

Contenu utile :

- bien
- mandat
- commercial
- type de demande
- statut
- priorite
- blocage
- prochaine action

### 2. app_view_diffusion_passerelles

Vue pour negociateurs.

Source logique :

- `case_dossier_source`
- tables diffusion principales
- `app_dossier`
- `app_internal_status`
- `app_broadcast_action`

Contenu utile :

- bien
- validation diffusion
- diffusable
- etat global diffusion
- etat par portail
- erreurs
- derniere action

### 3. app_view_suivi_transaction

Vue pour Delphine.

Source logique :

- `case_dossier_source`
- `app_dossier`
- `app_work_item`
- `app_followup`
- `app_blocker`

Contenu utile :

- offre
- compromis
- vente
- delais
- blocages
- relances

### 4. app_view_pilotage_global

Vue pour managers.

Source logique :

- aggregation de `case_dossier_source`
- `app_work_item`
- `app_followup`
- `app_blocker`
- `app_internal_status`

Contenu utile :

- volumes
- retards
- alertes
- indicateurs par commercial

### 5. app_view_fiche_dossier

Vue detaillee commune.

Source logique :

- `case_dossier_source`
- details annonce
- diffusion
- transactionnel
- notes
- relances
- blocages
- statut interne

## Ordre de mise en place recommande

### Etape 1

Creer seulement :

- `app_dossier`
- `app_work_item`
- `app_note`
- `app_internal_status`
- `app_broadcast_action`

### Etape 2

Ajouter :

- `app_followup`
- `app_blocker`

### Etape 3

Construire les vues de lecture.

## Recommandation pratique

Pour rester pragmatique en V1 :

- commencer simple
- ne pas surcharger `app_work_item` de logique trop complexe au debut
- utiliser `details_json` pour les cas particuliers
- stabiliser d'abord les files Pauline et diffusion passerelles

## Conclusion

Ce schema permet :

- de garder Hektor comme source synchronisee
- d'ajouter une vraie couche metier locale
- de piloter les files de travail
- de preparer les actions de diffusion
- sans melanger la base Hektor et la logique interne de l'outil
