"""Ingestion « Potentiel locatif » -> table Supabase `app_commune_loyers` (~1×/an).

Patron « bulk / pré-téléchargé » (comme ingest_dvf.py) : télécharge les CSV
data.gouv de la « Carte des loyers » (ANIL/DHUP : loyer €/m²/mois d'annonce,
maison & appartement, par commune) + la « Liste des communes selon le zonage ABC »,
fusionne par code INSEE, et remplace le contenu de `app_commune_loyers`
(DELETE + COPY en une transaction). Le front lit ensuite par INSEE.

Mise à jour : la Carte des loyers est publiée ~1×/an par l'ANIL. Pour rafraîchir :
bumper MILLESIME + les URLs (le chemin data.gouv contient l'année + un horodatage).

Usage :
  python backend/scripts/ingest_loyers.py            # ingestion réelle
  python backend/scripts/ingest_loyers.py --dry-run  # télécharge + parse, n'écrit pas
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]

MILLESIME = 2025
_BASE = "https://static.data.gouv.fr/resources"
# Carte des loyers 2025 (ANIL/DHUP) — loyer d'annonce €/m²/mois charges comprises.
URL_MAISON = f"{_BASE}/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/20251211-145039/pred-mai-mef-dhup.csv"
URL_APPART = f"{_BASE}/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/20251211-145010/pred-app-mef-dhup.csv"
# Zonage ABC en vigueur (tension du marché du logement) — data.gouv.
URL_ZONAGE = f"{_BASE}/liste-des-communes-selon-le-zonage-abc/20260626-082324/liste-ensemble-des-communes-zonage-abc-en-vigueur-25-juin-2026.csv"

TABLE = "app_commune_loyers"
COLS = ["insee", "libgeo", "dep", "loyer_maison", "loyer_appart", "zone_abc", "millesime"]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _num(v: str) -> float | None:
    """Loyer : décimale à la VIRGULE dans les CSV (ex. '8,50358')."""
    s = (v or "").strip().replace(",", ".")
    try:
        return round(float(s), 2) if s else None
    except ValueError:
        return None


def _fetch_csv(url: str) -> list[list[str]]:
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    text = r.content.decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(text), delimiter=";"))


def _parse_loyers(rows: list[list[str]]) -> dict[str, dict[str, Any]]:
    """CSV loyers : id_zone;INSEE_C;LIBGEO;EPCI;DEP;REG;loypredm2;... -> {insee: {loyer, libgeo, dep}}."""
    out: dict[str, dict[str, Any]] = {}
    for r in rows[1:]:
        if len(r) < 7:
            continue
        insee = (r[1] or "").strip().strip('"')
        if not insee:
            continue
        out[insee] = {"loyer": _num(r[6]), "libgeo": (r[2] or "").strip().strip('"'), "dep": (r[4] or "").strip().strip('"')}
    return out


def _parse_zonage(rows: list[list[str]]) -> dict[str, str]:
    """CSV zonage : CODGEO;DEP;LIBGEO;Zonage ABC... -> {insee: zone}."""
    out: dict[str, str] = {}
    for r in rows[1:]:
        if len(r) < 4:
            continue
        insee = (r[0] or "").strip().strip('"')
        zone = (r[3] or "").strip().strip('"')
        if insee and zone:
            out[insee] = zone
    return out


def build() -> list[dict[str, Any]]:
    print("Téléchargement Carte des loyers (maison + appartement) + zonage ABC…")
    maison = _parse_loyers(_fetch_csv(URL_MAISON))
    appart = _parse_loyers(_fetch_csv(URL_APPART))
    zonage = _parse_zonage(_fetch_csv(URL_ZONAGE))
    insees = set(maison) | set(appart) | set(zonage)
    rows: list[dict[str, Any]] = []
    for insee in insees:
        m = maison.get(insee, {})
        a = appart.get(insee, {})
        rows.append({
            "insee": insee,
            "libgeo": m.get("libgeo") or a.get("libgeo") or "",
            "dep": m.get("dep") or a.get("dep") or "",
            "loyer_maison": m.get("loyer"),
            "loyer_appart": a.get("loyer"),
            "zone_abc": zonage.get(insee),
            "millesime": MILLESIME,
        })
    print(f"  maison={len(maison)} · appart={len(appart)} · zonage={len(zonage)} -> {len(rows)} communes fusionnées")
    return rows


def _pooler_dsn() -> str:
    from urllib.parse import quote, urlparse

    override = os.environ.get("DATABASE_POOLER_URL")
    if override:
        return override
    direct = os.environ.get("DATABASE_URL")
    if not direct:
        sys.exit("DATABASE_URL absent (root .env).")
    u = urlparse(direct)
    ref = (u.hostname or "").split(".")[1] if u.hostname and "." in u.hostname else ""
    host = os.environ.get("SUPABASE_POOLER_HOST", "aws-1-eu-west-2.pooler.supabase.com")
    return f"postgresql://postgres.{ref}:{quote(u.password or '')}@{host}:5432/postgres"


def write_rows(rows: list[dict[str, Any]]) -> None:
    import psycopg2

    buf = io.StringIO()
    w = csv.writer(buf)
    for r in rows:
        w.writerow([
            r["insee"], r["libgeo"], r["dep"],
            "" if r["loyer_maison"] is None else r["loyer_maison"],
            "" if r["loyer_appart"] is None else r["loyer_appart"],
            "" if r["zone_abc"] is None else r["zone_abc"],
            r["millesime"],
        ])
    buf.seek(0)

    conn = psycopg2.connect(_pooler_dsn())
    try:
        with conn, conn.cursor() as cur:
            cur.execute(f"DELETE FROM public.{TABLE};")
            cur.copy_expert(
                f"COPY public.{TABLE} ({', '.join(COLS)}) FROM STDIN WITH (FORMAT csv, NULL '')",
                buf,
            )
            cur.execute(f"SELECT count(*), count(loyer_maison), count(loyer_appart), count(zone_abc) FROM public.{TABLE};")
            n, nm, na, nz = cur.fetchone()
        print(f"OK : {n} communes en base · loyer maison {nm} · loyer appart {na} · zone {nz}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion Potentiel locatif -> app_commune_loyers")
    parser.add_argument("--dry-run", action="store_true", help="télécharge + parse sans écrire")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    t0 = time.time()
    rows = build()
    if not rows:
        sys.exit("Aucune commune — abandon (table inchangée).")
    if args.dry_run:
        sample = next((r for r in rows if r["insee"] == "43157"), rows[0])
        print(f"DRY-RUN — exemple {sample['insee']} {sample['libgeo']}: maison={sample['loyer_maison']} appart={sample['loyer_appart']} zone={sample['zone_abc']}")
        print(f"({len(rows)} communes en {time.time() - t0:.1f}s)")
        return
    write_rows(rows)
    print(f"Terminé en {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()

# =============================================================================
# PLANIFICATION (machine GTI, ~1×/an) — Planificateur de tâches Windows.
#   schtasks /Create /TN "Hektor-IngestLoyers" /SC MONTHLY /MO 1 /M JAN /D 15 /ST 04:00 ^
#     /TR "cmd /c cd /d C:\Hektor\Projet && python backend\scripts\ingest_loyers.py >> logs\ingest_loyers.log 2>&1"
# (La Carte des loyers est publiée annuellement ; bumper MILLESIME + URLs à la sortie.)
# =============================================================================
