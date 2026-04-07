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

CREATE TABLE IF NOT EXISTS app_diffusion_target (
    app_dossier_id INTEGER NOT NULL,
    hektor_annonce_id INTEGER NOT NULL,
    hektor_broadcast_id TEXT NOT NULL,
    portal_key TEXT,
    target_state TEXT NOT NULL DEFAULT 'enabled'
        CHECK (target_state IN ('enabled', 'disabled')),
    source_ref TEXT,
    note TEXT,
    requested_by_role TEXT,
    requested_by_name TEXT,
    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_applied_at TEXT,
    last_apply_status TEXT,
    last_apply_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (app_dossier_id, hektor_broadcast_id),
    FOREIGN KEY (app_dossier_id) REFERENCES app_dossier(id)
);

CREATE TABLE IF NOT EXISTS app_diffusion_agency_target (
    agence_nom TEXT NOT NULL,
    portal_key TEXT NOT NULL,
    hektor_broadcast_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agence_nom, portal_key)
);

CREATE TABLE IF NOT EXISTS app_diffusion_refusal_reason (
    code TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    default_refusal_message TEXT NOT NULL,
    default_reminder_message TEXT NOT NULL,
    default_manager_message TEXT NOT NULL,
    first_reminder_delay_days INTEGER NOT NULL DEFAULT 2,
    reminder_interval_days INTEGER NOT NULL DEFAULT 3,
    manager_escalation_delay_days INTEGER NOT NULL DEFAULT 7,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 100,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_diffusion_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_dossier_id INTEGER NOT NULL,
    hektor_annonce_id INTEGER,
    hektor_mandat_id INTEGER,
    requested_by_user_id TEXT,
    requested_by_name TEXT,
    requested_by_role TEXT NOT NULL DEFAULT 'negociateur',
    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    request_comment TEXT,
    status TEXT NOT NULL DEFAULT 'en_cours' CHECK (status IN ('en_cours', 'accepte', 'refuse')),
    decision_by_user_id TEXT,
    decision_by_name TEXT,
    decision_at TEXT,
    decision_comment TEXT,
    accepted_set_diffusable INTEGER NOT NULL DEFAULT 0,
    accepted_default_portals_json TEXT,
    accepted_email_sent_at TEXT,
    refusal_reason_code TEXT,
    refusal_reason_label TEXT,
    refusal_message TEXT,
    correction_required INTEGER NOT NULL DEFAULT 0,
    corrected_at TEXT,
    corrected_by_user_id TEXT,
    corrected_by_name TEXT,
    refused_email_sent_at TEXT,
    last_reminder_at TEXT,
    next_reminder_at TEXT,
    reminder_count INTEGER NOT NULL DEFAULT 0,
    manager_notified_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_dossier_id) REFERENCES app_dossier(id),
    FOREIGN KEY (refusal_reason_code) REFERENCES app_diffusion_refusal_reason(code),
    CHECK (
        status <> 'accepte'
        OR accepted_default_portals_json IS NOT NULL
    ),
    CHECK (
        status <> 'refuse'
        OR refusal_reason_code IS NOT NULL
    ),
    CHECK (
        status = 'en_cours'
        OR decision_at IS NOT NULL
    )
);

CREATE TABLE IF NOT EXISTS app_diffusion_request_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diffusion_request_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_label TEXT NOT NULL,
    event_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actor_user_id TEXT,
    actor_name TEXT,
    actor_role TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (diffusion_request_id) REFERENCES app_diffusion_request(id)
);

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

CREATE INDEX IF NOT EXISTS idx_app_diffusion_target_annonce
ON app_diffusion_target(hektor_annonce_id, target_state);

CREATE INDEX IF NOT EXISTS idx_app_diffusion_target_portal
ON app_diffusion_target(hektor_broadcast_id, target_state);

CREATE INDEX IF NOT EXISTS idx_app_diffusion_agency_target_portal
ON app_diffusion_agency_target(portal_key, hektor_broadcast_id, is_active);

INSERT OR IGNORE INTO app_diffusion_agency_target (agence_nom, portal_key, hektor_broadcast_id, note) VALUES
('Groupe GTI Ambert', 'bienicidirect', '2', 'Flux par agence'),
('Groupe GTI Ambert', 'leboncoinDirect', '35', 'Flux par agence'),
('Groupe GTI ANNONAY', 'bienicidirect', '3', 'Flux par agence'),
('Groupe GTI ANNONAY', 'leboncoinDirect', '36', 'Flux par agence'),
('Groupe GTI BRIOUDE', 'bienicidirect', '4', 'Flux par agence'),
('Groupe GTI BRIOUDE', 'leboncoinDirect', '41', 'Flux par agence'),
('Groupe GTI Craponne-sur-Arzon', 'bienicidirect', '5', 'Flux par agence'),
('Groupe GTI Craponne-sur-Arzon', 'leboncoinDirect', '42', 'Flux par agence'),
('Groupe GTI Yssingeaux', 'bienicidirect', '6', 'Flux par agence'),
('Groupe GTI Yssingeaux', 'leboncoinDirect', '38', 'Flux par agence'),
('Groupe GTI Montbrison', 'bienicidirect', '7', 'Flux par agence'),
('Groupe GTI Montbrison', 'leboncoinDirect', '37', 'Flux par agence'),
('Groupe GTI Saint-Just-Saint-Rambert', 'bienicidirect', '8', 'Flux par agence'),
('Groupe GTI Saint-Just-Saint-Rambert', 'leboncoinDirect', '37', 'Flux par agence'),
('Groupe GTI Issoire', 'bienicidirect', '9', 'Flux par agence'),
('Groupe GTI Issoire', 'leboncoinDirect', '41', 'Flux par agence'),
('Groupe GTI Saint-Bonnet-le-Château', 'bienicidirect', '10', 'Flux par agence'),
('Groupe GTI Saint-Bonnet-le-Château', 'leboncoinDirect', '42', 'Flux par agence'),
('Groupe GTI COURPIERE', 'bienicidirect', '11', 'Flux par agence'),
('Groupe GTI COURPIERE', 'leboncoinDirect', '35', 'Flux par agence'),
('Groupe GTI Monistrol sur Loire', 'bienicidirect', '13', 'Flux par agence'),
('Groupe GTI Monistrol sur Loire', 'leboncoinDirect', '40', 'Flux par agence'),
('Groupe GTI Saint-Didier-en-Velay', 'bienicidirect', '14', 'Flux par agence'),
('Groupe GTI Saint-Didier-en-Velay', 'leboncoinDirect', '40', 'Flux par agence'),
('Groupe GTI Firminy', 'bienicidirect', '15', 'Flux par agence'),
('Groupe GTI Firminy', 'leboncoinDirect', '39', 'Flux par agence'),
('Groupe GTI Saint-Etienne', 'bienicidirect', '16', 'Flux par agence'),
('Groupe GTI Saint-Etienne', 'leboncoinDirect', '39', 'Flux par agence'),
('Groupe GTI Dunières', 'bienicidirect', '17', 'Flux par agence'),
('Groupe GTI Dunières', 'leboncoinDirect', '43', 'Flux par agence'),
('Groupe GTI Tence', 'bienicidirect', '22', 'Flux par agence'),
('Groupe GTI Tence', 'leboncoinDirect', '43', 'Flux par agence'),
('Groupe Gti Le Puy en Velay', 'bienicidirect', '23', 'Flux par agence'),
('Groupe Gti Le Puy en Velay', 'leboncoinDirect', '38', 'Flux par agence');

CREATE INDEX IF NOT EXISTS idx_app_diffusion_request_dossier
ON app_diffusion_request(app_dossier_id);

CREATE INDEX IF NOT EXISTS idx_app_diffusion_request_status
ON app_diffusion_request(status, requested_at DESC);

CREATE INDEX IF NOT EXISTS idx_app_diffusion_request_next_reminder
ON app_diffusion_request(next_reminder_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_app_diffusion_request_open
ON app_diffusion_request(app_dossier_id)
WHERE status = 'en_cours';

CREATE INDEX IF NOT EXISTS idx_app_diffusion_request_event_request
ON app_diffusion_request_event(diffusion_request_id, event_at DESC);

INSERT OR REPLACE INTO app_diffusion_refusal_reason (
    code, label, default_refusal_message, default_reminder_message, default_manager_message,
    first_reminder_delay_days, reminder_interval_days, manager_escalation_delay_days, sort_order
) VALUES
('elements_manquants', 'Elements manquants',
 'La demande de diffusion ne peut pas etre validee car des elements obligatoires sont manquants.',
 'Relance: la demande reste bloquee car les elements demandes ne sont pas encore corriges.',
 'Escalade manager: la demande reste non corrigee malgre les relances.',
 2, 3, 7, 10),
('mandat_non_valide', 'Mandat non valide',
 'La demande de diffusion ne peut pas etre validee car le mandat n''est pas conforme ou exploitable.',
 'Relance: la demande reste bloquee car le mandat n''a pas encore ete regularise.',
 'Escalade manager: le mandat n''a pas ete regularise malgre les relances.',
 2, 2, 6, 20),
('bien_non_diffusable', 'Bien non diffusable',
 'La demande de diffusion ne peut pas etre validee car le bien n''est pas diffusable en l''etat.',
 'Relance: la demande reste bloquee car le bien n''est toujours pas diffusable.',
 'Escalade manager: le bien reste non diffusable malgre les relances.',
 3, 4, 10, 30),
('photos_non_conformes', 'Photos a corriger',
 'La demande de diffusion ne peut pas etre validee car les photos ne sont pas conformes.',
 'Relance: la demande reste bloquee car les photos n''ont pas encore ete corrigees.',
 'Escalade manager: les photos ne sont toujours pas conformes malgre les relances.',
 3, 4, 10, 40),
('texte_annonce_incomplet', 'Texte annonce a corriger',
 'La demande de diffusion ne peut pas etre validee car le texte annonce est incomplet ou non publiable.',
 'Relance: la demande reste bloquee car le texte annonce n''a pas encore ete corrige.',
 'Escalade manager: le texte annonce reste non conforme malgre les relances.',
 3, 4, 10, 50),
('bareme_honoraire_non_respecte', 'Bareme honoraire non respecte',
 'La demande de diffusion ne peut pas etre validee car le bareme honoraire n''est pas respecte.',
 'Relance: la demande reste bloquee car le bareme honoraire n''a pas encore ete corrige.',
 'Escalade manager: le bareme honoraire reste non conforme malgre les relances.',
 2, 3, 6, 60),
('validation_interne_requise', 'Validation interne requise',
 'La demande de diffusion ne peut pas etre validee sans validation interne prealable.',
 'Relance: la demande reste bloquee en attente de validation interne.',
 'Escalade manager: la validation interne n''a pas ete obtenue malgre les relances.',
 2, 3, 5, 70),
('correction_fiche_bien', 'Correction fiche bien',
 'La demande de diffusion ne peut pas etre validee car la fiche bien doit etre corrigee.',
 'Relance: la demande reste bloquee car la fiche bien n''a pas encore ete corrigee.',
 'Escalade manager: la fiche bien reste a corriger malgre les relances.',
 2, 3, 7, 80),
('autre', 'Autre',
 'La demande de diffusion ne peut pas etre validee en l''etat.',
 'Relance: la demande reste bloquee en attente de correction.',
 'Escalade manager: la demande reste bloquee malgre les relances.',
 3, 4, 10, 90);
