"""Ingestion DVF -> table Supabase `app_dvf_vente` (à lancer 2×/an).

La DVF (DGFiP/geo-dvf) n'est publiée que ~2×/an (avril : S2 de l'an précédent ;
octobre : S1 de l'année en cours). Ce script télécharge les ventes Maison/Appartement
des départements GTI (42/43/63/07) sur les 3 derniers millésimes, applique le
NETTOYAGE (dans l'ordre), et remplace le contenu de `app_dvf_vente` (DELETE + COPY)
en une transaction. Le front lit ensuite la RPC `app_dvf_comparables`.

NETTOYAGE (ordre important — cf. cahier des charges) :
  1. surface >= 9 m² (lignes valides) ; valeur >= 1000 ; lat/lon présents
  2. EXCLURE l'en-bloc / multi-lots : on regroupe par `id_mutation` et on ne garde
     que les mutations à EXACTEMENT 1 logement bâti (Maison/Appartement). Au-delà,
     `valeur_fonciere` est le prix global de plusieurs biens -> prix/m² faux.
     De plus on borne les lots de copropriété : `nombre_lots <= 2` (maison=0,
     appart seul=1, appart + 1 annexe=2 ; au-delà la valeur est diluée).
  3. prix/m² = valeur / surface, PUIS bornes de bon sens : 300 <= prix/m² <= 8000.
  (Le rognage 5/95 % se fait au moment du calcul, dans la RPC, sur le set local.)

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
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]

GEO_DVF_BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv"
DEPTS = ["42", "43", "63", "07"]            # périmètre GTI (mutuellement limitrophes)
N_MILLESIMES = 5                            # année courante (souvent vide) + 4 précédentes
                                            # => 4 années PLEINES de DVF, pour couvrir la fenêtre
                                            #    d'estimation qui remonte jusqu'à 48 mois (RPC v4).
TABLE = "app_dvf_vente"

# Seuils de nettoyage (cf. cahier des charges) — ajustables.
MIN_SURFACE = 9         # m² — en deçà, prix/m² absurde (cave, box…)
MIN_VALEUR = 1000       # € — vente symbolique / erreur
MAX_NOMBRE_LOTS = 2     # lots de copropriété max (maison=0, appart seul=1, +1 annexe=2)
PRICE_MIN = 300         # €/m² — borne basse de bon sens (Loire)
PRICE_MAX = 8000        # €/m² — borne haute de bon sens (Loire)

COLS = ["id_mutation", "date_mutation", "type_local", "valeur", "surface", "pieces",
        "terrain", "commune", "code_postal", "code_commune", "dept", "lat", "lon",
        "prix_m2", "nombre_lots"]


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
    """Télécharge un (département, millésime) et renvoie TOUTES les lignes bâties
    Vente Maison/Appartement valides (surface/valeur/géo). Le regroupement par
    mutation (exclusion en-bloc) se fait ensuite, globalement."""
    url = f"{GEO_DVF_BASE}/{year}/departements/{dept}.csv.gz"
    rows: list[dict[str, Any]] = []
    try:
        resp = requests.get(url, timeout=180)
        if not resp.ok:
            print(f"  - {dept}/{year}: indisponible ({resp.status_code})")
            return []
        text = gzip.decompress(resp.content).decode("utf-8", errors="replace")
        for row in csv.DictReader(io.StringIO(text)):
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
                nombre_lots = int(float(row.get("nombre_lots") or 0))
            except (TypeError, ValueError):
                continue
            if surface < MIN_SURFACE or valeur < MIN_VALEUR or not lat or not lon:
                continue
            pieces_raw = row.get("nombre_pieces_principales")
            terrain_raw = row.get("surface_terrain")
            rows.append({
                "id_mutation": row.get("id_mutation") or "",
                "date_mutation": row.get("date_mutation") or "",
                "type_local": type_local,
                "valeur": valeur,
                "surface": surface,
                "pieces": int(float(pieces_raw)) if pieces_raw else None,
                "terrain": float(terrain_raw) if terrain_raw else None,
                "commune": row.get("nom_commune") or "",
                "code_postal": row.get("code_postal") or "",
                "code_commune": row.get("code_commune") or "",
                "dept": dept,
                "lat": lat,
                "lon": lon,
                "nombre_lots": nombre_lots,
                "prix_m2": round(valeur / surface) if surface else None,
            })
        print(f"  - {dept}/{year}: {len(rows)} lignes bâties valides")
    except Exception as exc:  # noqa: BLE001
        print(f"  - {dept}/{year}: erreur {exc}")
        return []
    return rows


def clean(raw: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Applique l'exclusion en-bloc + bornes prix. Renvoie (lignes propres, stats)."""
    # 1) regrouper par mutation : compter les logements bâtis par mutation
    by_mut: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in raw:
        by_mut[r["id_mutation"]].append(r)

    n_mut = len(by_mut)
    kept: list[dict[str, Any]] = []
    excl_enbloc = excl_lots = excl_price = 0
    for rows in by_mut.values():
        if len(rows) != 1:          # 2) en-bloc : >1 logement bâti -> rejet
            excl_enbloc += 1
            continue
        r = rows[0]
        if r["nombre_lots"] > MAX_NOMBRE_LOTS:   # trop de lots de copro -> rejet
            excl_lots += 1
            continue
        pm = r["prix_m2"]           # 3) bornes prix/m²
        if pm is None or pm < PRICE_MIN or pm > PRICE_MAX:
            excl_price += 1
            continue
        kept.append(r)
    stats = {
        "lignes_brutes": len(raw), "mutations": n_mut,
        "rejet_enbloc": excl_enbloc, "rejet_nombre_lots": excl_lots,
        "rejet_prix_borne": excl_price, "retenues": len(kept),
    }
    return kept, stats


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

    buf = io.StringIO()
    w = csv.writer(buf)
    for r in rows:
        w.writerow([
            r["id_mutation"], r["date_mutation"], r["type_local"], r["valeur"], r["surface"],
            "" if r["pieces"] is None else r["pieces"],
            "" if r["terrain"] is None else r["terrain"],
            r["commune"], r["code_postal"], r["code_commune"], r["dept"], r["lat"], r["lon"],
            "" if r["prix_m2"] is None else r["prix_m2"], r["nombre_lots"],
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
    parser.add_argument("--dry-run", action="store_true", help="télécharge + nettoie sans écrire")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")

    t0 = time.time()
    raw = download_all()
    rows, stats = clean(raw)
    print(f"Nettoyage : {stats['lignes_brutes']} lignes brutes / {stats['mutations']} mutations "
          f"-> {stats['retenues']} retenues "
          f"(rejets : en-bloc {stats['rejet_enbloc']}, nombre_lots {stats['rejet_nombre_lots']}, "
          f"prix hors bornes {stats['rejet_prix_borne']}) en {time.time() - t0:.1f}s")
    if not rows:
        sys.exit("Aucune vente retenue — abandon (table inchangée).")
    if args.dry_run:
        by_dept: dict[str, int] = defaultdict(int)
        for r in rows:
            by_dept[r["dept"]] += 1
        print("DRY-RUN — répartition par département :", dict(by_dept))
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
