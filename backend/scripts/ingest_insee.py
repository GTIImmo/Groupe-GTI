"""Ingestion INSEE (profil commune) -> table Supabase `app_commune_insee` (1×/an).

Pour chaque commune des 4 départements GTI (42/43/63/07), récupère via l'API INSEE
Melodi (open data, sans clé) : population + évolution (DS_POPULATIONS_HISTORIQUES)
et revenu médian / niveau de vie (DS_FILOSOFI_CC, mesure MED_SL). L'avis de valeur
lit ensuite la table — aucune dépendance INSEE à la génération. Regroupé avec la
tâche DVF + risques (annuel).

v2 (à enrichir) : % propriétaires, % maisons, CSP, chômage (cubes RP plus complexes).

Usage :
  python backend/scripts/ingest_insee.py            # ingestion réelle
  python backend/scripts/ingest_insee.py --dry-run
  python backend/scripts/ingest_insee.py --limit 20
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
DEPTS = ["42", "43", "63", "07"]
TABLE = "app_commune_insee"
COLS = ["code_insee", "commune", "dept", "population", "population_annee",
        "pop_evolution", "pop_tendance", "revenu_median", "pop_series"]
_MELODI = "https://api.insee.fr/melodi/data"
_H = {"Accept": "application/json"}


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
    out: list[dict[str, Any]] = []
    for dept in DEPTS:
        try:
            r = requests.get(f"https://geo.api.gouv.fr/departements/{dept}/communes",
                             params={"fields": "code,nom", "format": "json"}, timeout=30)
            for c in r.json():
                out.append({"insee": c["code"], "nom": c.get("nom") or "", "dept": dept})
        except Exception as exc:  # noqa: BLE001
            print(f"  ! communes {dept}: {exc}")
    return out


def _melodi(ds: str, insee: str, extra: dict[str, str] | None = None) -> list[dict[str, Any]]:
    params = {"GEO": f"COM-{insee}", "maxResult": 120}
    if extra:
        params.update(extra)
    for attempt in range(6):  # Melodi renvoie des 504 ponctuels -> retries patients
        try:
            r = requests.get(f"{_MELODI}/{ds}", params=params, headers=_H, timeout=60)
            if r.ok:
                return r.json().get("observations", []) or []
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (attempt + 1))
                continue
            return []
        except Exception:  # noqa: BLE001
            time.sleep(1.5 * (attempt + 1))
    return []


def _val(o: dict[str, Any]) -> float | None:
    v = (o.get("measures") or {}).get("OBS_VALUE_NIVEAU", {}).get("value")
    return v if isinstance(v, (int, float)) else None


def commune_insee(c: dict[str, Any]) -> dict[str, Any]:
    insee = c["insee"]
    population = population_annee = pop_evolution = None
    pop_tendance = None
    # population par année -> dernier millésime + évolution sur ~15 ans
    years: dict[int, float] = {}
    for o in _melodi("DS_POPULATIONS_HISTORIQUES", insee):
        try:
            y = int(o["dimensions"].get("TIME_PERIOD"))
        except (TypeError, ValueError):
            continue
        v = _val(o)
        if v and v > 0:
            years[y] = v
    if years:
        latest = max(years)
        population, population_annee = int(round(years[latest])), latest
        past = [y for y in years if y <= latest - 13]
        ref = max(past) if past else min(years)
        if years.get(ref):
            pop_evolution = round((years[latest] - years[ref]) / years[ref] * 100, 1)
            pop_tendance = ("Croissance" if pop_evolution >= 4
                            else "Déclin" if pop_evolution <= -4 else "Stable")
    # revenu médian (niveau de vie)
    revenu_median = None
    for o in _melodi("DS_FILOSOFI_CC", insee, {"FILOSOFI_MEASURE": "MED_SL"}):
        v = _val(o)
        if v and v > 1000:
            revenu_median = int(round(v))
            break
    # Série complète (année -> population) pour la courbe d'évolution riche du PDF.
    pop_series = (json.dumps({str(y): int(round(years[y])) for y in sorted(years)},
                             separators=(",", ":")) if years else None)
    return {"code_insee": insee, "commune": c["nom"], "dept": c["dept"],
            "population": population, "population_annee": population_annee,
            "pop_evolution": pop_evolution, "pop_tendance": pop_tendance,
            "revenu_median": revenu_median, "pop_series": pop_series}


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


def existing_filled() -> set[str]:
    """Communes déjà renseignées (population non nulle) -> à ne pas re-tenter."""
    import psycopg2
    conn = psycopg2.connect(_pooler_dsn())
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT code_insee FROM public.{TABLE} WHERE population IS NOT NULL;")
            return {r[0] for r in cur.fetchall()}
    finally:
        conn.close()


def write_rows(rows: list[dict[str, Any]]) -> None:
    # Upsert reprenable : on n'écrit que les communes effectivement récupérées
    # (population non nulle) pour ne JAMAIS écraser une bonne ligne avec du vide.
    import psycopg2
    rows = [r for r in rows if r.get("population") is not None]
    if not rows:
        print("Aucune donnée nouvelle à écrire (toutes les réponses étaient vides).")
        return
    buf = io.StringIO()
    w = csv.writer(buf)
    for r in rows:
        w.writerow(["" if r[c] is None else r[c] for c in COLS])
    buf.seek(0)
    conn = psycopg2.connect(_pooler_dsn())
    try:
        with conn, conn.cursor() as cur:
            cur.execute(f"CREATE TEMP TABLE _ins_stage (LIKE public.{TABLE} INCLUDING DEFAULTS) ON COMMIT DROP;")
            cur.copy_expert(f"COPY _ins_stage ({', '.join(COLS)}) FROM STDIN WITH (FORMAT csv, NULL '')", buf)
            cur.execute(f"""
                INSERT INTO public.{TABLE} ({', '.join(COLS)}, updated_at)
                SELECT {', '.join(COLS)}, now() FROM _ins_stage
                ON CONFLICT (code_insee) DO UPDATE SET
                  commune = excluded.commune, dept = excluded.dept,
                  population = excluded.population, population_annee = excluded.population_annee,
                  pop_evolution = excluded.pop_evolution, pop_tendance = excluded.pop_tendance,
                  revenu_median = excluded.revenu_median, pop_series = excluded.pop_series,
                  updated_at = now();
            """)
            cur.execute(f"SELECT count(*), count(population), count(revenu_median) FROM public.{TABLE};")
            n, npop, nr = cur.fetchone()
        print(f"OK : {n} communes en base ({npop} avec population, {nr} avec revenu médian)")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion INSEE -> app_commune_insee")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--fill-missing", action="store_true",
                        help="ne (re)tente que les communes sans population en base")
    args = parser.parse_args()
    load_env_file(ROOT / ".env")

    communes = list_communes()
    if args.fill_missing and not args.dry_run:
        filled = existing_filled()
        before = len(communes)
        communes = [c for c in communes if c["insee"] not in filled]
        print(f"fill-missing : {len(filled)} déjà OK, {len(communes)}/{before} à (re)tenter")
    if args.limit:
        communes = communes[: args.limit]
    print(f"{len(communes)} communes (départements {DEPTS}) — interrogation INSEE Melodi…")
    t0 = time.time()
    rows: list[dict[str, Any]] = []
    done = 0
    with ThreadPoolExecutor(max_workers=3) as ex:  # Melodi : concurrence prudente (anti-504)
        for r in ex.map(commune_insee, communes):
            rows.append(r)
            done += 1
            if done % 100 == 0:
                print(f"  ...{done}/{len(communes)}")
    nr = sum(1 for r in rows if r["revenu_median"])
    print(f"{len(rows)} communes en {time.time() - t0:.0f}s (revenu médian : {nr})")
    if args.dry_run:
        for r in rows[:10]:
            line = (f"   {r['commune']} -> pop {r['population']} ({r['population_annee']}) "
                    f"évol {r['pop_evolution']}% [{r['pop_tendance']}] | revenu médian {r['revenu_median']} €/an")
            sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
        return
    write_rows(rows)


if __name__ == "__main__":
    main()

# =============================================================================
# PLANIFICATION — regroupée avec DVF + risques (tâche « Hektor-IngestDVF », 2×/an).
# Enchaîner les 3 scripts :
#   ...&& python backend\scripts\ingest_dvf.py >> logs\ingest_dvf.log 2>&1 ^
#      && python backend\scripts\ingest_georisques.py >> logs\ingest_georisques.log 2>&1 ^
#      && python backend\scripts\ingest_insee.py >> logs\ingest_insee.log 2>&1
# =============================================================================
