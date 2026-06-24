"""Données de marché DVF (Demandes de Valeurs Foncières — open data data.gouv).

Récupère les ventes d'un département (fichier geo-dvf `.csv.gz`, ~1 Mo compressé),
les met en cache, et calcule des **comparables** géolocalisés autour d'un bien :
filtrage par distance (haversine), type (Maison/Appartement), surface (±tol) et
période (mois). Sert la page Marché de l'avis de valeur et la section comparables.

Source : https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/departements/{dept}.csv.gz
"""

from __future__ import annotations

import csv
import gzip
import io
import math
import time
from datetime import datetime, timedelta
from typing import Any

import requests

_GEO_DVF_BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv"
_CACHE: dict[tuple[str, int], list[dict[str, Any]]] = {}
_CACHE_TS: dict[tuple[str, int], float] = {}
_CACHE_TTL = 86400  # 24 h


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _load_department(dept: str, year: int) -> list[dict[str, Any]]:
    """Charge (et met en cache) les ventes Maison/Appartement d'un département/an."""
    key = (dept, year)
    if key in _CACHE and (time.time() - _CACHE_TS.get(key, 0)) < _CACHE_TTL:
        return _CACHE[key]
    url = f"{_GEO_DVF_BASE}/{year}/departements/{dept}.csv.gz"
    rows: list[dict[str, Any]] = []
    try:
        resp = requests.get(url, timeout=120)
        if not resp.ok:
            _CACHE[key] = []
            _CACHE_TS[key] = time.time()
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
            rows.append({
                "date": row.get("date_mutation") or "",
                "type": type_local,
                "valeur": valeur,
                "surface": surface,
                "pieces": row.get("nombre_pieces_principales") or None,
                "terrain": (float(row["surface_terrain"]) if row.get("surface_terrain") else None),
                "commune": row.get("nom_commune") or "",
                "code_postal": row.get("code_postal") or "",
                "lat": lat,
                "lon": lon,
                "prix_m2": round(valeur / surface) if surface else None,
            })
    except Exception:
        rows = []
    _CACHE[key] = rows
    _CACHE_TS[key] = time.time()
    return rows


def comparables(
    *,
    lat: float,
    lon: float,
    dept: str,
    type_local: str = "Maison",
    surface: float | None = None,
    radius_km: float = 12.0,
    months: int = 24,
    surface_tol: float = 0.30,
    limit: int = 5,
) -> dict[str, Any]:
    """Comparables DVF autour d'un point. Décisions user : commune + voisines (rayon),
    24 mois, même type, surface ±30 %."""
    if not lat or not lon or not dept:
        return {"ok": False, "reason": "missing_geo", "count": 0, "comparables": []}
    now = datetime.now()
    years = [now.year, now.year - 1, now.year - 2]
    rows: list[dict[str, Any]] = []
    for y in years:
        rows += _load_department(dept, y)
    cutoff = (now - timedelta(days=months * 31)).strftime("%Y-%m-%d")
    smin = surface * (1 - surface_tol) if surface else None
    smax = surface * (1 + surface_tol) if surface else None

    matched: list[dict[str, Any]] = []
    for r in rows:
        if r["type"] != type_local:
            continue
        if r["date"] < cutoff:
            continue
        if smin is not None and not (smin <= r["surface"] <= smax):
            continue
        dist = _haversine_km(lat, lon, r["lat"], r["lon"])
        if dist > radius_km:
            continue
        item = dict(r)
        item["distance_km"] = round(dist, 1)
        matched.append(item)

    prix_m2 = sorted(r["prix_m2"] for r in matched if r["prix_m2"])
    avg = round(sum(prix_m2) / len(prix_m2)) if prix_m2 else None
    median = prix_m2[len(prix_m2) // 2] if prix_m2 else None

    # Évolution : prix/m² moyen par année (sur tous les biens du type dans le rayon, sans filtre surface).
    by_year: dict[str, list[float]] = {}
    for r in rows:
        if r["type"] != type_local or not r["prix_m2"]:
            continue
        if _haversine_km(lat, lon, r["lat"], r["lon"]) > radius_km:
            continue
        by_year.setdefault(r["date"][:4], []).append(r["prix_m2"])
    evolution = [
        {"annee": yr, "prix_m2": round(sum(v) / len(v)), "n": len(v)}
        for yr, v in sorted(by_year.items()) if v
    ]

    # Top comparables : surface la plus proche puis vente la plus récente.
    comps = sorted(matched, key=lambda r: (abs(r["surface"] - surface) if surface else 0, r["date"]), reverse=False)
    if surface:
        comps = sorted(matched, key=lambda r: (abs(r["surface"] - surface), ))
    comps = sorted(comps, key=lambda r: r["date"], reverse=True)[:limit] if not surface else comps[:limit]

    return {
        "ok": True,
        "count": len(matched),
        "avg_prix_m2": avg,
        "median_prix_m2": median,
        "radius_km": radius_km,
        "months": months,
        "type": type_local,
        "evolution": evolution,
        "comparables": [
            {
                "commune": c["commune"], "type": c["type"], "surface": int(c["surface"]),
                "pieces": c["pieces"], "terrain": int(c["terrain"]) if c["terrain"] else None,
                "valeur": int(c["valeur"]), "prix_m2": c["prix_m2"], "date": c["date"],
                "distance_km": c["distance_km"],
            }
            for c in comps
        ],
    }
