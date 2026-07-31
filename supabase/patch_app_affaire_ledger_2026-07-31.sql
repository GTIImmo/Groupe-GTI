-- Niveau B — ledger d'affaires app-owned (independance vis-a-vis de Hektor).
-- Applique en prod via migration Supabase `create_app_affaire_ledger` (2026-07-31).
-- UPSERT sur (annonce, kind, affaire_id) : les changements d'etat (ex. compromis active -> cancelled)
-- sont refletes ; JAMAIS supprime : si Hektor retire une affaire on la conserve avec
-- present_in_hektor=false. Alimente par phase2/sync/affaire_ledger.py (--refresh --push),
-- branche dans run_full_pipeline.ps1. NON touche par delete_local_annonce (delete-never).

CREATE TABLE IF NOT EXISTS public.app_affaire_ledger (
    hektor_annonce_id   bigint NOT NULL,
    kind                text   NOT NULL,
    hektor_affaire_id   text   NOT NULL,
    hektor_mandat_id    text,
    numero_mandat       text,
    hektor_acquereur_id text,
    acquereur_json      jsonb,
    state               text,
    montant             text,
    date                text,
    date_acte           text,
    sequestre           text,
    payload_json        jsonb,
    first_seen_at       timestamptz,
    last_seen_at        timestamptz,
    present_in_hektor   boolean NOT NULL DEFAULT true,
    PRIMARY KEY (hektor_annonce_id, kind, hektor_affaire_id)
);

CREATE INDEX IF NOT EXISTS idx_app_affaire_ledger_annonce ON public.app_affaire_ledger(hektor_annonce_id);
CREATE INDEX IF NOT EXISTS idx_app_affaire_ledger_acq ON public.app_affaire_ledger(hektor_acquereur_id);

ALTER TABLE public.app_affaire_ledger ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS app_affaire_ledger_select_active_users ON public.app_affaire_ledger;
CREATE POLICY app_affaire_ledger_select_active_users
    ON public.app_affaire_ledger FOR SELECT
    TO public
    USING (is_app_user_active());
