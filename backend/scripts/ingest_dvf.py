"""Ingestion DVF -> table Supabase `app_dvf_vente` (à lancer 2×/an).

La DVF (DGFiP/geo-dvf) n'est publiée que ~2×/an (avril : S2 de l'an précédent ;
octobre : S1 de l'année en cours). Ce script télécharge les ventes Maison/Appartement
des départements GTI (42/43/63/07) sur les 3 derniers millésimes, les filtre comme
l'ancien service Python, et remplace le contenu de `app_dvf_vente` (DELETE + COPY)
en une transaction. Le front lit ensuite la RPC `app_dvf_comparables`.

Planification (machine GTI toujours allumée) — voir README en bas de fichier :
  Tâche planifiée Windows, 2×/an : ~28 avril et ~28 octobre.

Usage :
  python backend/scripts/ingest_dvf.py            # ingestion réelle
  python backend/scripts/ingest_dvf.py --dry-run  # télécharge + filtre, n'écrit pas
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]

GEO_DVF_BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv"
DEPTS = ["42", "43", "63", "07"]            # périmètre GTI (mutuellement limitrophes)
N_MILLESIMES = 3                            # année courante + 2 précédentes
TABLE = "app_dvf_vente"
COLS = ["date_mutation", "type_local", "valeur", "surface", "pieces",
        "terrain", "commune", "code_postal", "dept", "lat", "lon", "prix_m2"]


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


def fetch_dept_year(dept: str, year: int) -> list[dict[str, Any]]:
    """Télécharge et filtre un (département, millésime). [] si 404/erreur."""
    url = f"{GEO_DVF_BASE}/{year}/departements/{dept}.csv.gz"
    rows: list[dict[str, Any]] = []
    try:
        resp = requests.get(url, timeout=180)
        if not resp.ok:
            print(f"  - {dept}/{year}: indisponible ({resp.status_code})")
            return []
        text = gzip.decompress(resp.content).decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            if row.get("nature_mutation") != "Vente":
                continue
            type_local = row.get("type_local")
            if type_local not in ("Maison", "Appartement"):
                continue
            try:
                valeur = float(row.get("valeur_fonciere") or 0)
                surface = float(row.get("surface_reelle_bati") or 0)
                lat = float(row.get("latitude") or 0)
                lon = float(row.get("longitude") or 0)
            except (TypeError, ValueError):
                continue
            if surface < 9 or valeur < 1000 or not lat or not lon:
                continue
            pieces_raw = row.get("nombre_pieces_principales")
            terrain_raw = row.get("surface_terrain")
            rows.append({
                "date_mutation": row.get("date_mutation") or "",
                "type_local": type_local,
                "valeur": valeur,
                "surface": surface,
                "pieces": int(float(pieces_raw)) if pieces_raw else None,
                "terrain": float(terrain_raw) if terrain_raw else None,
                "commune": row.get("nom_commune") or "",
                "code_postal": row.get("code_postal") or "",
                "dept": dept,
                "lat": lat,
                "lon": lon,
                "prix_m2": round(valeur / surface) if surface else None,
            })
        print(f"  - {dept}/{year}: {len(rows)} ventes Maison/Appartement")
    except Exception as exc:  # noqa: BLE001
        print(f"  - {dept}/{year}: erreur {exc}")
        return []
    return rows


def download_all() -> list[dict[str, Any]]:
    year = datetime.now().year
    years = [year - i for i in range(N_MILLESIMES)]
    pairs = [(d, y) for d in DEPTS for y in years]
    print(f"Téléchargement geo-dvf : {DEPTS} × {years} ({len(pairs)} fichiers)…")
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for chunk in ex.map(lambda p: fetch_dept_year(p[0], p[1]), pairs):
            rows += chunk
    return rows


def _pooler_dsn() -> str:
    """DSN de connexion. Le host direct `db.<ref>.supabase.co` n'est plus résolu en
    IPv4 (IPv6-only) -> on passe par le pooler `...pooler.supabase.com` (user
    `postgres.<ref>`, port 5432 session = COPY supporté). Override possible via
    DATABASE_POOLER_URL."""
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
    import psycopg2  # import tardif : seulement pour l'écriture réelle

    dsn = _pooler_dsn()

    # buffer CSV pour COPY (bien plus rapide qu'un INSERT par ligne)
    buf = io.StringIO()
    w = csv.writer(buf)
    for r in rows:
        w.writerow([
            r["date_mutation"], r["type_local"], r["valeur"], r["surface"],
            "" if r["pieces"] is None else r["pieces"],
            "" if r["terrain"] is None else r["terrain"],
            r["commune"], r["code_postal"], r["dept"], r["lat"], r["lon"],
            "" if r["prix_m2"] is None else r["prix_m2"],
        ])
    buf.seek(0)

    conn = psycopg2.connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(f"DELETE FROM public.{TABLE};")
            cur.copy_expert(
                f"COPY public.{TABLE} ({', '.join(COLS)}) FROM STDIN WITH (FORMAT csv, NULL '')",
                buf,
            )
            cur.execute(f"SELECT count(*), max(date_mutation) FROM public.{TABLE};")
            n, through = cur.fetchone()
        print(f"OK : {n} lignes en base · vente la plus récente {through}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion DVF -> app_dvf_vente")
    parser.add_argument("--dry-run", action="store_true", help="télécharge + filtre sans écrire")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")

    t0 = time.time()
    rows = download_all()
    print(f"{len(rows)} ventes filtrées en {time.time() - t0:.1f}s")
    if not rows:
        sys.exit("Aucune vente récupérée — abandon (table inchangée).")
    if args.dry_run:
        by_dept: dict[str, int] = {}
        for r in rows:
            by_dept[r["dept"]] = by_dept.get(r["dept"], 0) + 1
        print("DRY-RUN — répartition par département :", by_dept)
        return
    write_rows(rows)


if __name__ == "__main__":
    main()

# =============================================================================
# PLANIFICATION (machine GTI, 2×/an) — Planificateur de tâches Windows.
# Crée une tâche qui s'exécute fin avril et fin octobre (après publication DVF) :
#
#   schtasks /Create /TN "Hektor-IngestDVF" /SC MONTHLY /MO 1 ^
#     /M AVR,OCT /D 28 /ST 03:00 ^
#     /TR "cmd /c cd /d C:\Hektor\Projet && python backend\scripts\ingest_dvf.py >> logs\ingest_dvf.log 2>&1"
#
# (MONTHLY, jour 28, uniquement avril & octobre, 03:00.)
# =============================================================================
