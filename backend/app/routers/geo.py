"""Commodités à proximité (OpenStreetMap / Overpass) + cadastre (IGN apicarto) —
proxy serveur.

Overpass refuse les requêtes navigateur (pas de CORS + blocage selon User-Agent).
apicarto.ign.fr est interrogé côté serveur pour éviter les soucis CORS. Les deux
servent la page « Cadre de vie » / « Éléments cadastraux » de l'avis de valeur.
Authentifié (interne).
"""

from __future__ import annotations

import json
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


_APICARTO = "https://apicarto.ign.fr/api"


def _apicarto_geom(path: str, geom: dict) -> list[dict]:
    """Interroge un module apicarto avec une géométrie GeoJSON ; renvoie les features."""
    r = requests.get(f"{_APICARTO}{path}", params={"geom": json.dumps(geom)}, headers=_UA, timeout=20)
    r.raise_for_status()
    return (r.json() or {}).get("features", []) or []


def _apicarto_point(path: str, lat: float, lon: float) -> list[dict]:
    return _apicarto_geom(path, {"type": "Point", "coordinates": [lon, lat]})


def _geom_centroid(geom: dict | None) -> tuple[float, float] | None:
    """Centroïde approximatif (moyenne des sommets) d'un Polygon/MultiPolygon → (lat, lon)."""
    if not geom:
        return None
    pts: list[list[float]] = []

    def walk(a):
        if not a:
            return
        if isinstance(a[0], (int, float)):
            pts.append(a)
        else:
            for x in a:
                walk(x)

    walk(geom.get("coordinates") or [])
    if not pts:
        return None
    n = len(pts)
    return (sum(p[1] for p in pts) / n, sum(p[0] for p in pts) / n)


def _bearing_fr(lat0: float, lon0: float, lat1: float, lon1: float) -> str:
    dlon = math.radians(lon1 - lon0)
    y = math.sin(dlon) * math.cos(math.radians(lat1))
    x = (math.cos(math.radians(lat0)) * math.sin(math.radians(lat1))
         - math.sin(math.radians(lat0)) * math.cos(math.radians(lat1)) * math.cos(dlon))
    brng = (math.degrees(math.atan2(y, x)) + 360) % 360
    dirs = ["Nord", "Nord-Est", "Est", "Sud-Est", "Sud", "Sud-Ouest", "Ouest", "Nord-Ouest"]
    return dirs[round(brng / 45) % 8]


def _parcelle_from_props(p: dict) -> dict:
    section = p.get("section")
    numero = p.get("numero")
    contenance = p.get("contenance")
    try:
        contenance = int(contenance) if contenance is not None else None
    except (TypeError, ValueError):
        contenance = None
    return {
        "reference": " ".join(x for x in (section, numero) if x).strip() or None,
        "section": section,
        "numero": numero,
        "contenance": contenance,
        "commune": p.get("nom_com"),
        "code_insee": p.get("code_insee"),
        "idu": p.get("idu"),
    }


def _square_polygon(lat: float, lon: float, meters: float) -> dict:
    dlat = meters / 111000.0
    dlon = meters / (111000.0 * max(0.1, math.cos(math.radians(lat))))
    return {"type": "Polygon", "coordinates": [[
        [lon - dlon, lat - dlat], [lon + dlon, lat - dlat],
        [lon + dlon, lat + dlat], [lon - dlon, lat + dlat], [lon - dlon, lat - dlat],
    ]]}


@router.get("/geo/cadastre")
def cadastre(
    lat: float = Query(...),
    lon: float = Query(...),
    candidates: int = Query(0, description="1 = renvoyer aussi les parcelles voisines (sélecteur)"),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Éléments cadastraux du bien : parcelle(s) sous le point (référence,
    section, numéro, contenance) + zonage PLU (API GPU). Si le point ne tombe sur
    aucune parcelle (ex. sur la voie), renvoie aussi les parcelles VOISINES
    (distance/direction/centroïde) pour laisser l'utilisateur choisir. Données IGN
    publiques, gratuites, sans clé. Pas de donnée nominative (propriétaire indispo)."""
    get_authenticated_user(settings, authorization)

    parcelles: list[dict] = []
    contenance_totale = 0
    seen_idu: set[str] = set()
    try:
        for f in _apicarto_point("/cadastre/parcelle", lat, lon):
            item = _parcelle_from_props(f.get("properties", {}) or {})
            if item.get("contenance"):
                contenance_totale += item["contenance"]
            if item.get("idu"):
                seen_idu.add(item["idu"])
            parcelles.append(item)
    except Exception:  # noqa: BLE001
        pass

    # Parcelles voisines : quand rien au point (point sur la voie) ou sur demande.
    nearby: list[dict] = []
    if not parcelles or candidates:
        try:
            feats = _apicarto_geom("/cadastre/parcelle", _square_polygon(lat, lon, 60))
            for f in feats:
                item = _parcelle_from_props(f.get("properties", {}) or {})
                if item.get("idu") and item["idu"] in seen_idu:
                    continue
                c = _geom_centroid(f.get("geometry"))
                if c:
                    item["centroid_lat"], item["centroid_lon"] = round(c[0], 8), round(c[1], 8)
                    item["distance_m"] = round(_km(lat, lon, c[0], c[1]) * 1000)
                    item["direction"] = _bearing_fr(lat, lon, c[0], c[1])
                nearby.append(item)
            nearby.sort(key=lambda x: x.get("distance_m") if x.get("distance_m") is not None else 1e9)
            nearby = nearby[:8]
        except Exception:  # noqa: BLE001
            pass

    plu = None
    try:
        feats = _apicarto_point("/gpu/zone-urba", lat, lon)
        if feats:
            p = feats[0].get("properties", {}) or {}
            plu = {"zone": p.get("libelle"), "libelle": p.get("libelong"), "type": p.get("typezone")}
    except Exception:  # noqa: BLE001
        pass

    # ok = True : l'appel a RÉUSSI (même sans parcelle au point). Le front distingue
    # « parcelle trouvée » via parcelles.length. Ne PAS renvoyer ok:false ici : le client
    # HTTP (invokeBackendApi) interprète ok:false comme une erreur et jette la réponse
    # (donc les parcelles voisines seraient perdues → « pas de cadastre » à tort).
    return {
        "ok": True,
        "found": bool(parcelles),
        "lat": lat,
        "lon": lon,
        "parcelles": parcelles,
        "contenance_totale": contenance_totale or None,
        "candidates": nearby,
        "plu": plu,
    }
