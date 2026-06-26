"""Commodités à proximité (OpenStreetMap / Overpass) — proxy serveur.

Overpass refuse les requêtes navigateur (pas de CORS + blocage selon User-Agent).
On l'interroge donc côté serveur (UA correct), pour la page « Cadre de vie » de
l'avis de valeur. Authentifié (interne).
"""

from __future__ import annotations

import math

import requests
from fastapi import APIRouter, Depends, Query

from ..auth import get_authenticated_user, require_request_user
from ..settings import Settings, get_settings

router = APIRouter(tags=["geo"])

_UA = {"User-Agent": "GTI-Immobilier-Estimation/1.0 (contact@gti-immobilier.fr)"}
_OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r, d = 6371.0, math.pi / 180
    a = (math.sin((lat2 - lat1) * d / 2) ** 2
         + math.cos(lat1 * d) * math.cos(lat2 * d) * math.sin((lon2 - lon1) * d / 2) ** 2)
    return r * 2 * math.asin(math.sqrt(a))


@router.get("/geo/commodites")
def commodites(
    lat: float = Query(...),
    lon: float = Query(...),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Compte les commodités OSM autour du bien : écoles (<1,5 km), commerces
    (<1 km), santé (<1,5 km), + gare la plus proche (<8 km)."""
    get_authenticated_user(settings, authorization)
    q = (
        "[out:json][timeout:25];("
        f"nwr[amenity=school](around:1500,{lat},{lon});"
        f"nwr[shop](around:1000,{lat},{lon});"
        f'nwr[amenity~"pharmacy|doctors|hospital|clinic"](around:1500,{lat},{lon});'
        f"nwr[railway=station](around:8000,{lat},{lon});"
        ");out center tags 250;"
    )
    data = None
    for host in _OVERPASS:
        try:
            r = requests.post(host, data={"data": q}, headers=_UA, timeout=30)
            if r.ok:
                data = r.json()
                break
        except Exception:  # noqa: BLE001
            continue
    if not data:
        return {"ok": False, "ecoles": 0, "commerces": 0, "sante": 0, "gareNom": None, "gareKm": None}

    ecoles = commerces = sante = 0
    gare_nom: str | None = None
    gare_km: float | None = None
    for el in data.get("elements", []):
        t = el.get("tags", {})
        if t.get("amenity") == "school":
            ecoles += 1
        elif t.get("shop"):
            commerces += 1
        elif t.get("amenity") in ("pharmacy", "doctors", "hospital", "clinic"):
            sante += 1
        elif t.get("railway") == "station":
            elat = el.get("lat") or (el.get("center") or {}).get("lat")
            elon = el.get("lon") or (el.get("center") or {}).get("lon")
            if elat and elon:
                km = round(_km(lat, lon, elat, elon), 1)
                if gare_km is None or km < gare_km:
                    gare_km, gare_nom = km, (t.get("name") or "Gare")
    return {"ok": True, "ecoles": ecoles, "commerces": commerces, "sante": sante,
            "gareNom": gare_nom, "gareKm": gare_km}
