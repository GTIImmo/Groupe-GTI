CREATE TABLE IF NOT EXISTS sync_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    notes TEXT,
    pid INTEGER,
    heartbeat_at TEXT,
    current_step TEXT,
    current_resource TEXT,
    current_endpoint TEXT,
    current_object_id TEXT,
    current_page INTEGER,
    progress_done INTEGER,
    progress_total INTEGER,
    progress_unit TEXT
);

CREATE TABLE IF NOT EXISTS sync_error (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    stage TEXT NOT NULL,
    endpoint_name TEXT,
    object_type TEXT,
    object_id TEXT,
    page INTEGER,
    error_message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES sync_run(id)
);

CREATE TABLE IF NOT EXISTS raw_api_response (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    endpoint_name TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT,
    object_id_key TEXT NOT NULL DEFAULT '',
    page INTEGER,
    page_key INTEGER NOT NULL DEFAULT -1,
    params_json TEXT,
    payload_json TEXT NOT NULL,
    http_status INTEGER,
    fetched_at TEXT NOT NULL,
    UNIQUE(endpoint_name, object_type, object_id_key, page_key),
    FOREIGN KEY (run_id) REFERENCES sync_run(id)
);

CREATE TABLE IF NOT EXISTS hektor_agence (
    hektor_agence_id TEXT PRIMARY KEY,
    nom TEXT,
    type TEXT,
    mail TEXT,
    tel TEXT,
    responsable TEXT,
    parent_id TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_negociateur (
    hektor_negociateur_id TEXT PRIMARY KEY,
    hektor_user_id TEXT,
    hektor_agence_id TEXT,
    nom TEXT,
    prenom TEXT,
    email TEXT,
    telephone TEXT,
    portable TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_annonce (
    hektor_annonce_id TEXT PRIMARY KEY,
    no_dossier TEXT,
    no_mandat TEXT,
    hektor_agence_id TEXT,
    hektor_negociateur_id TEXT,
    date_maj TEXT,
    offre_type TEXT,
    idtype TEXT,
    prix REAL,
    surface TEXT,
    archive TEXT,
    diffusable TEXT,
    valide TEXT,
    partage TEXT,
    titre TEXT,
    ville TEXT,
    code_postal TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_annonce_detail (
    hektor_annonce_id TEXT PRIMARY KEY,
    statut_id TEXT,
    statut_name TEXT,
    localite_json TEXT,
    mandats_json TEXT,
    proprietaires_json TEXT,
    honoraires_json TEXT,
    notes_json TEXT,
    zones_json TEXT,
    particularites_json TEXT,
    pieces_json TEXT,
    images_json TEXT,
    textes_json TEXT,
    terrain_json TEXT,
    copropriete_json TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_mandat (
    hektor_mandat_id TEXT PRIMARY KEY,
    hektor_annonce_id TEXT,
    numero TEXT,
    type TEXT,
    date_enregistrement TEXT,
    date_debut TEXT,
    date_fin TEXT,
    date_cloture TEXT,
    montant TEXT,
    mandants_texte TEXT,
    note TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_contact (
    hektor_contact_id TEXT PRIMARY KEY,
    hektor_agence_id TEXT,
    hektor_negociateur_id TEXT,
    civilite TEXT,
    nom TEXT,
    prenom TEXT,
    archive TEXT,
    date_enregistrement TEXT,
    date_maj TEXT,
    email TEXT,
    portable TEXT,
    fixe TEXT,
    ville TEXT,
    code_postal TEXT,
    typologie_json TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_offre (
    hektor_offre_id TEXT PRIMARY KEY,
    hektor_annonce_id TEXT,
    hektor_mandat_id TEXT,
    hektor_acquereur_id TEXT,
    nom TEXT,
    prenom TEXT,
    raw_status TEXT,
    raw_date TEXT,
    raw_montant TEXT,
    acquereur_json TEXT,
    propositions_json TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_compromis (
    hektor_compromis_id TEXT PRIMARY KEY,
    hektor_annonce_id TEXT,
    hektor_mandat_id TEXT,
    status TEXT,
    date_start TEXT,
    date_end TEXT,
    date_signature_acte TEXT,
    part_admin TEXT,
    sequestre TEXT,
    prix_net_vendeur TEXT,
    prix_publique TEXT,
    mandants_json TEXT,
    acquereurs_json TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_vente (
    hektor_vente_id TEXT PRIMARY KEY,
    hektor_annonce_id TEXT,
    hektor_mandat_id TEXT,
    date_vente TEXT,
    prix TEXT,
    honoraires TEXT,
    part_admin TEXT,
    commission_agence TEXT,
    mandants_json TEXT,
    acquereurs_json TEXT,
    notaires_json TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_broadcast (
    hektor_broadcast_id TEXT PRIMARY KEY,
    nom TEXT,
    count INTEGER,
    listings_json TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_broadcast_listing (
    hektor_broadcast_id TEXT NOT NULL,
    hektor_annonce_id TEXT NOT NULL,
    passerelle TEXT,
    commercial_id TEXT,
    commercial_type TEXT,
    commercial_nom TEXT,
    commercial_prenom TEXT,
    export_status TEXT,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL,
    PRIMARY KEY (hektor_broadcast_id, hektor_annonce_id, commercial_id)
);

CREATE TABLE IF NOT EXISTS hektor_broadcast_portal (
    hektor_broadcast_id TEXT PRIMARY KEY,
    passerelle_key TEXT NOT NULL,
    listing_count INTEGER,
    supports_read INTEGER NOT NULL DEFAULT 1,
    supports_write INTEGER NOT NULL DEFAULT 1,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hektor_annonce_broadcast_state (
    hektor_broadcast_id TEXT NOT NULL,
    hektor_annonce_id TEXT NOT NULL,
    commercial_key TEXT NOT NULL,
    passerelle_key TEXT NOT NULL,
    commercial_id TEXT,
    commercial_type TEXT,
    commercial_nom TEXT,
    commercial_prenom TEXT,
    current_state TEXT NOT NULL,
    export_status TEXT,
    is_success INTEGER NOT NULL DEFAULT 0,
    is_error INTEGER NOT NULL DEFAULT 0,
    raw_json TEXT NOT NULL,
    synced_at TEXT NOT NULL,
    PRIMARY KEY (hektor_broadcast_id, hektor_annonce_id, commercial_key)
);

CREATE TABLE IF NOT EXISTS hektor_annonce_broadcast_target (
    hektor_broadcast_id TEXT NOT NULL,
    hektor_annonce_id TEXT NOT NULL,
    target_state TEXT NOT NULL,
    source_ref TEXT,
    note TEXT,
    updated_at TEXT NOT NULL,
    last_applied_at TEXT,
    last_apply_status TEXT,
    last_apply_error TEXT,
    PRIMARY KEY (hektor_broadcast_id, hektor_annonce_id)
);

CREATE TABLE IF NOT EXISTS case_dossier_source (
    hektor_annonce_id TEXT PRIMARY KEY,
    no_dossier TEXT,
    no_mandat TEXT,
    hektor_agence_id TEXT,
    hektor_negociateur_id TEXT,
    negociateur_nom TEXT,
    negociateur_prenom TEXT,
    negociateur_email TEXT,
    negociateur_telephone TEXT,
    negociateur_portable TEXT,
    statut_name TEXT,
    annonce_source_status TEXT,
    archive TEXT,
    diffusable TEXT,
    valide TEXT,
    prix REAL,
    case_kind TEXT,
    mandat_id TEXT,
    mandat_type TEXT,
    mandat_date_debut TEXT,
    mandat_date_fin TEXT,
    mandat_date_cloture TEXT,
    offre_id TEXT,
    compromis_id TEXT,
    vente_id TEXT,
    vente_date TEXT,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sync_run_status ON sync_run(status, heartbeat_at, started_at);
CREATE INDEX IF NOT EXISTS idx_broadcast_listing_annonce ON hektor_broadcast_listing(hektor_annonce_id);
CREATE INDEX IF NOT EXISTS idx_broadcast_listing_status ON hektor_broadcast_listing(export_status);
CREATE INDEX IF NOT EXISTS idx_broadcast_state_annonce ON hektor_annonce_broadcast_state(hektor_annonce_id);
CREATE INDEX IF NOT EXISTS idx_broadcast_state_portal ON hektor_annonce_broadcast_state(passerelle_key, current_state);
CREATE INDEX IF NOT EXISTS idx_broadcast_target_annonce ON hektor_annonce_broadcast_target(hektor_annonce_id, target_state);
