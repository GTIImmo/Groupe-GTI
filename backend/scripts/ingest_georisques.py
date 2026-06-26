"""Ingestion Géorisques -> table Supabase `app_commune_risques` (1×/an).

Pour chaque commune des 4 départements GTI (42/43/63/07), récupère le profil de
risques (Géorisques) et le stocke. L'avis de valeur lit ensuite la table — aucune
dépendance Géorisques au moment de la génération. Regroupé avec la tâche DVF
(actualisation annuelle) — voir README en bas + ingest_dvf.py.

Sources Géorisques (API publique, sans clé) :
  - gaspar/risques (par INSEE) : inventaire des risques de la commune
  - radon (par INSEE) : potentiel radon
  - zonage_sismique (par lat/lon) : zone de sismicité
  - rga (par lat/lon) : exposition retrait-gonflement des argiles
Liste des communes + centroïdes : geo.api.gouv.fr.

Usage :
  python backend/scripts/ingest_georisques.py            # ingestion réelle
  python backend/scripts/ingest_georisques.py --dry-run  # récupère sans écrire
  python backend/scripts/ingest_georisques.py --limit 20 # test sur N communes
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
DEPTS = ["42", "43", "63", "07"]
TABLE = "app_commune_risques"
COLS = ["code_insee", "commune", "dept", "risques", "radon", "sismicite", "argiles"]

_RADON = {"1": "Faible", "2": "Moyen", "3": "Élevé"}
# Libellés Géorisques (souvent verbeux) -> risque « principal » court pour l'affichage.
_RISK_KEYS = ["Inondation", "Mouvement de terrain", "Séisme", "Radon", "Industriel",
              "Rupture de barrage", "Feu de forêt", "Nucléaire", "Transport de marchandises",
              "Engins de guerre", "Cavité", "Avalanche"]
_GR = "https://georisques.gouv.fr/api/v1"


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


def list_communes() -> list[dict[str, Any]]:
    """Toutes les communes des départements GTI avec leur centroïde (geo.api.gouv)."""
    out: list[dict[str, Any]] = []
    for dept in DEPTS:
        try:
            r = requests.get(f"https://geo.api.gouv.fr/departements/{dept}/communes",
                             params={"fields": "code,nom,centre", "format": "json"}, timeout=30)
            for c in r.json():
                centre = (c.get("centre") or {}).get("coordinates") or [None, None]
                out.append({"insee": c["code"], "nom": c.get("nom") or "", "dept": dept,
                            "lon": centre[0], "lat": centre[1]})
        except Exception as exc:  # noqa: BLE001
            print(f"  ! communes {dept}: {exc}")
    return out


def _get(url: str, params: dict[str, str]) -> dict[str, Any] | None:
    try:
        r = requests.get(url, params=params, timeout=20,
                         headers={"User-Agent": "GTI-Immobilier-Estimation/1.0"})
        return r.json() if r.ok else None
    except Exception:  # noqa: BLE001
        return None


def commune_risques(c: dict[str, Any]) -> dict[str, Any]:
    insee, lat, lon = c["insee"], c["lat"], c["lon"]
    risques: list[str] = []
    g = _get(f"{_GR}/gaspar/risques", {"code_insee": insee})
    if g and g.get("data"):
        for x in g["data"][0].get("risques_detail", []):
            lib = (x.get("libelle_risque_long") or "")
            for key in _RISK_KEYS:
                if key.lower() in lib.lower() and key not in risques:
                    risques.append(key)
    radon = ""
    rd = _get(f"{_GR}/radon", {"code_insee": insee})
    if rd and rd.get("data"):
        radon = _RADON.get(str(rd["data"][0].get("classe_potentiel", "")), "")
    sismicite = ""
    if lat and lon:
        z = _get(f"{_GR}/zonage_sismique", {"latlon": f"{lon},{lat}"})
        if z and z.get("data"):
            sismicite = (z["data"][0].get("zone_sismicite") or "").title()
    argiles = ""
    if lat and lon:
        a = _get(f"{_GR}/rga", {"latlon": f"{lon},{lat}"})
        if a:
            argiles = (a.get("exposition") or "").replace("Exposition", "").strip().capitalize()
    return {"code_insee": insee, "commune": c["nom"], "dept": c["dept"],
            "risques": risques, "radon": radon, "sismicite": sismicite, "argiles": argiles}


def _pg_array(values: list[str]) -> str:
    # Littéral array Postgres pour COPY : {"a","b"}
    esc = [v.replace("\\", "\\\\").replace('"', '\\"') for v in values]
    return "{" + ",".join(f'"{v}"' for v in esc) + "}"


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
        w.writerow([r["code_insee"], r["commune"], r["dept"], _pg_array(r["risques"]),
                    r["radon"], r["sismicite"], r["argiles"]])
    buf.seek(0)
    conn = psycopg2.connect(_pooler_dsn())
    try:
        with conn, conn.cursor() as cur:
            cur.execute(f"DELETE FROM public.{TABLE};")
            cur.copy_expert(f"COPY public.{TABLE} ({', '.join(COLS)}) FROM STDIN WITH (FORMAT csv, NULL '')", buf)
            cur.execute(f"SELECT count(*) FROM public.{TABLE};")
            n = cur.fetchone()[0]
        print(f"OK : {n} communes en base")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion Géorisques -> app_commune_risques")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="limiter à N communes (test)")
    args = parser.parse_args()
    load_env_file(ROOT / ".env")

    communes = list_communes()
    if args.limit:
        communes = communes[: args.limit]
    print(f"{len(communes)} communes (départements {DEPTS}) — interrogation Géorisques…")
    t0 = time.time()
    rows: list[dict[str, Any]] = []
    done = 0
    with ThreadPoolExecutor(max_workers=5) as ex:  # Géorisques : concurrence modérée
        for r in ex.map(commune_risques, communes):
            rows.append(r)
            done += 1
            if done % 100 == 0:
                print(f"  ...{done}/{len(communes)}")
    print(f"{len(rows)} communes récupérées en {time.time() - t0:.0f}s "
          f"(avec risques : {sum(1 for r in rows if r['risques'])})")
    if args.dry_run:
        for r in rows[:8]:
            line = f"   {r['commune']} -> {r['risques']} | radon {r['radon']} | seisme {r['sismicite']} | argiles {r['argiles']}"
            sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
        return
    write_rows(rows)


if __name__ == "__main__":
    main()

# =============================================================================
# PLANIFICATION — regroupée avec la DVF (tâche Windows existante « Hektor-IngestDVF »).
# Mettre à jour la tâche pour enchaîner les deux scripts (la DVF tourne 2×/an,
# les risques en profitent — l'upsert est idempotent) :
#
#   schtasks /Create /TN "Hektor-IngestDVF" /SC MONTHLY /MO 1 /M AVR,OCT /D 28 /ST 03:00 /F ^
#     /TR "cmd /c cd /d C:\Hektor\Projet && python backend\scripts\ingest_dvf.py >> logs\ingest_dvf.log 2>&1 && python backend\scripts\ingest_georisques.py >> logs\ingest_georisques.log 2>&1"
# =============================================================================
