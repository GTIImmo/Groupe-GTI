"""Ledger d'affaires app-owned (offre / compromis / vente) — NIVEAU B.

Objectif : indépendance vis-à-vis de Hektor. On accumule chaque affaire vue dans une table
app-owned, en **UPSERT sur l'id stable** (les changements d'état — ex. compromis active -> cancelled —
sont reflétés) mais **jamais supprimée** : si Hektor retire une affaire, on la conserve avec
`present_in_hektor = false`. Le registre continue de lire Hektor comme aujourd'hui (le branchement
lecture = étape B+ séparée) ; ici on ne fait que **sécuriser la donnée**.

Table locale : phase2/phase2.sqlite -> app_affaire_ledger.
Table Supabase : public.app_affaire_ledger (même schéma).
NON touchée par delete_local_annonce (delete-never) : exemption par simple absence de la table
de sa liste de nettoyage.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"

sys.path.insert(0, str(ROOT / "phase2" / "sync"))
from export_app_payload import _compact_party, normalize_text  # noqa: E402
from push_upgrade_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_files,
)

import os  # noqa: E402

LEDGER_TABLE = "app_affaire_ledger"

# Identite (20/08/2026) : l'affaire porte d'abord le numero de l'app.
#   app_affaire_id -- UNE serie pour les trois types. Hektor, lui, tient trois compteurs
#     separes dont les numeros se telescopent : 7 541 numeros sont portes par deux types
#     differents, sur des annonces et des acquereurs differents. Le numero de Hektor n'est
#     donc unique QUE dans son type -- d'ou l'index unique sur le triplet, et pas sur l'id.
#   app_dossier_id -- le numero d'annonce de l'app, a cote de celui de Hektor.
# Les deux colonnes Hektor deviennent facultatives : une affaire saisie dans l'app existe
# avant que Hektor ne la numerote, et parfois sans que Hektor la numerote jamais.
DDL_SQLITE = f"""
CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
    app_affaire_id      INTEGER PRIMARY KEY,
    app_dossier_id      INTEGER,
    hektor_annonce_id   INTEGER,
    kind                TEXT NOT NULL,
    hektor_affaire_id   TEXT,
    hektor_mandat_id    TEXT,
    numero_mandat       TEXT,
    hektor_acquereur_id TEXT,
    acquereur_json      TEXT,
    state               TEXT,
    montant             TEXT,
    date                TEXT,
    date_acte           TEXT,
    sequestre           TEXT,
    payload_json        TEXT,
    first_seen_at       TEXT,
    last_seen_at        TEXT,
    present_in_hektor   INTEGER NOT NULL DEFAULT 1
);
-- Cle de reconciliation : c'est par ce triplet qu'on reconnait, au retour de Hektor, une
-- affaire deja connue. Partiel, car une affaire nee dans l'app n'a pas encore de numero
-- Hektor et ne doit pas entrer en collision avec les autres.
CREATE UNIQUE INDEX IF NOT EXISTS idx_affaire_ledger_hektor
    ON {LEDGER_TABLE}(hektor_annonce_id, kind, hektor_affaire_id)
    WHERE hektor_affaire_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_affaire_ledger_annonce ON {LEDGER_TABLE}(hektor_annonce_id);
CREATE INDEX IF NOT EXISTS idx_affaire_ledger_dossier ON {LEDGER_TABLE}(app_dossier_id);
CREATE INDEX IF NOT EXISTS idx_affaire_ledger_acq ON {LEDGER_TABLE}(hektor_acquereur_id);
"""

# Toutes les affaires, offres INCLUSES (pas de filtre mandat : 98% des offres ont mandat_id=0).
LEDGER_SQL = """
SELECT hektor_annonce_id, hektor_mandat_id, 'offre' AS kind, hektor_offre_id AS affaire_id,
       hektor_acquereur_id AS acq_id, acquereur_json AS acq_json, offre_state AS state,
       raw_montant AS montant, COALESCE(offre_event_date, raw_date, synced_at) AS dt,
       NULL AS date_acte, NULL AS sequestre, raw_json
FROM hektor.hektor_offre WHERE hektor_annonce_id IS NOT NULL
UNION ALL
SELECT hektor_annonce_id, hektor_mandat_id, 'compromis', hektor_compromis_id,
       NULL, acquereurs_json, compromis_state,
       COALESCE(prix_publique, prix_net_vendeur), COALESCE(date_start, synced_at),
       date_signature_acte, sequestre, raw_json
FROM hektor.hektor_compromis WHERE hektor_annonce_id IS NOT NULL
UNION ALL
SELECT hektor_annonce_id, hektor_mandat_id, 'vente', hektor_vente_id,
       NULL, acquereurs_json, NULL,
       prix, COALESCE(date_vente, synced_at),
       NULL, NULL, raw_json
FROM hektor.hektor_vente WHERE hektor_annonce_id IS NOT NULL
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _open_local() -> sqlite3.Connection:
    con = sqlite3.connect(PHASE2_DB)
    con.row_factory = sqlite3.Row
    con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
    return con


def _mandat_numero(con: sqlite3.Connection) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for row in con.execute("SELECT hektor_annonce_id, hektor_mandat_id, numero FROM hektor.hektor_mandat"):
        a, m, n = normalize_text(row[0]), normalize_text(row[1]), normalize_text(row[2])
        if a and m and n:
            out[(a, m)] = n
    return out


def refresh_ledger(con: sqlite3.Connection, *, full: bool = True) -> dict[str, int]:
    """UPSERT (delete-never) de toutes les affaires courantes dans le ledger local.
    En mode full, les lignes non revues ce run passent present_in_hektor=0 (conservées)."""
    con.executescript(DDL_SQLITE)
    run_ts = now_iso()
    mnum = _mandat_numero(con)

    existing_first: dict[tuple[str, str, str], str] = {}
    for row in con.execute(f"SELECT hektor_annonce_id, kind, hektor_affaire_id, first_seen_at FROM {LEDGER_TABLE}"):
        existing_first[(str(row[0]), str(row[1]), str(row[2]))] = row[3] or run_ts

    # Le numero d'affaire est distribue ici, par le serveur local, comme app_dossier.id.
    # On ne renumerote JAMAIS une ligne connue : l'ON CONFLICT ci-dessous laisse
    # app_affaire_id intact. Seules les affaires nouvelles prennent un numero.
    next_affaire_id = (con.execute(f"SELECT COALESCE(MAX(app_affaire_id), 0) FROM {LEDGER_TABLE}").fetchone()[0]) + 1
    dossier_par_annonce: dict[str, int] = {
        str(a): int(i) for i, a in con.execute(
            "SELECT id, hektor_annonce_id FROM app_dossier WHERE hektor_annonce_id IS NOT NULL"
        )
    }

    seen = 0
    inserted = 0
    for r in con.execute(LEDGER_SQL):
        annonce = normalize_text(r["hektor_annonce_id"])
        affaire_id = normalize_text(r["affaire_id"])
        kind = normalize_text(r["kind"])
        if not (annonce and affaire_id and kind):
            continue
        mid = normalize_text(r["hektor_mandat_id"])
        party = _compact_party(r["acq_json"])
        acq_id = normalize_text(r["acq_id"]) or (normalize_text(party.get("id")) if party else "")
        numero = mnum.get((annonce, mid), "") if mid and mid != "0" else ""
        key = (annonce, kind, affaire_id)
        first_seen = existing_first.get(key, run_ts)
        nouvelle = key not in existing_first
        if nouvelle:
            inserted += 1
        # Numero propose : ignore par SQLite si la ligne existe deja (DO UPDATE ne le touche pas).
        # On n'avance le compteur que pour une affaire reellement nouvelle.
        propose = next_affaire_id
        if nouvelle:
            next_affaire_id += 1
        con.execute(
            f"""
            INSERT INTO {LEDGER_TABLE}(app_affaire_id, app_dossier_id,
                hektor_annonce_id, kind, hektor_affaire_id, hektor_mandat_id,
                numero_mandat, hektor_acquereur_id, acquereur_json, state, montant, date, date_acte,
                sequestre, payload_json, first_seen_at, last_seen_at, present_in_hektor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(hektor_annonce_id, kind, hektor_affaire_id)
              WHERE hektor_affaire_id IS NOT NULL DO UPDATE SET
                app_dossier_id=excluded.app_dossier_id,
                hektor_mandat_id=excluded.hektor_mandat_id,
                numero_mandat=excluded.numero_mandat,
                hektor_acquereur_id=excluded.hektor_acquereur_id,
                acquereur_json=excluded.acquereur_json,
                state=excluded.state, montant=excluded.montant, date=excluded.date,
                date_acte=excluded.date_acte, sequestre=excluded.sequestre,
                payload_json=excluded.payload_json,
                last_seen_at=excluded.last_seen_at, present_in_hektor=1
            """,
            (
                propose, dossier_par_annonce.get(annonce),
                int(annonce), kind, affaire_id, mid or None, numero or None, acq_id or None,
                json.dumps(party, ensure_ascii=True, separators=(",", ":")) if party else None,
                normalize_text(r["state"]) or None, normalize_text(r["montant"]) or None,
                normalize_text(r["dt"]) or None, normalize_text(r["date_acte"]) or None,
                normalize_text(r["sequestre"]) or None, normalize_text(r["raw_json"]) or None,
                first_seen, run_ts,
            ),
        )
        seen += 1

    absent = 0
    if full:
        cur = con.execute(f"UPDATE {LEDGER_TABLE} SET present_in_hektor=0 WHERE last_seen_at <> ?", (run_ts,))
        absent = cur.rowcount or 0
    con.commit()
    total = con.execute(f"SELECT COUNT(*) FROM {LEDGER_TABLE}").fetchone()[0]
    return {"seen": seen, "inserted": inserted, "marked_absent": absent, "ledger_total": total}


def ledger_rows_for_push(con: sqlite3.Connection) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for r in con.execute(f"SELECT * FROM {LEDGER_TABLE}"):
        d = dict(r)
        for jcol in ("acquereur_json", "payload_json"):
            v = d.get(jcol)
            if isinstance(v, str) and v:
                try:
                    d[jcol] = json.loads(v)
                except Exception:
                    d[jcol] = None
        d["present_in_hektor"] = bool(d.get("present_in_hektor"))
        rows.append(d)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh + push du ledger d'affaires (Niveau B).")
    parser.add_argument("--refresh", action="store_true", help="UPSERT local depuis le miroir Hektor.")
    parser.add_argument("--push", action="store_true", help="UPSERT vers Supabase (delete-never).")
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()
    if not (args.refresh or args.push):
        args.refresh = args.push = True  # backfill par défaut

    con = _open_local()
    result: dict[str, object] = {}
    if args.refresh:
        result["refresh"] = refresh_ledger(con, full=True)
    if args.push:
        load_env_files(DEFAULT_ENV_FILES)
        url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not (url and key):
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
        client = SupabaseRestClient(base_url=url, service_role_key=key)
        rows = ledger_rows_for_push(con)
        client.upsert_rows(path=LEDGER_TABLE, rows=rows, batch_size=args.batch_size)
        result["push"] = {"rows_pushed": len(rows)}
    con.close()
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
