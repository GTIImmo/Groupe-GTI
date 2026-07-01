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


# =====================================================================
# 1ère vague de sources « bâti/bien » de l'estimation (per-point, gratuites,
# sans clé) : RNB (identifiant bâtiment) -> BDNB (caractéristiques bâti) ;
# DPE ADEME (étiquette réelle). Toutes renvoient ok:True (le front recalcule
# la présence via `found` — ne PAS renvoyer ok:false, cf. invokeBackendApi).
# =====================================================================

_RNB = "https://rnb-api.beta.gouv.fr/api/alpha"
_BDNB = "https://api.bdnb.io/v1/bdnb"
_DPE_DS = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant"


def _rnb_closest(lat: float, lon: float, radius: int = 40) -> dict | None:
    """Bâtiment RNB le plus proche du point (le 1er résultat = le plus proche)."""
    try:
        r = requests.get(f"{_RNB}/buildings/closest/",
                         params={"point": f"{lat},{lon}", "radius": radius},
                         headers=_UA, timeout=20)
        if not r.ok:
            return None
        results = (r.json() or {}).get("results") or []
        return results[0] if results else None
    except Exception:  # noqa: BLE001
        return None


def _rnb_bdnb_bc_id(building: dict | None) -> str | None:
    """Identifiant BDNB (batiment_construction) porté par un bâtiment RNB — pivot vers la BDNB."""
    for e in (building or {}).get("ext_ids") or []:
        if e.get("source") == "bdnb" and e.get("id"):
            return e["id"]
    return None


def _bdnb_rows(path: str, params: dict) -> list | None:
    try:
        r = requests.get(f"{_BDNB}/{path}", params=params, headers=_UA, timeout=25)
        if not r.ok:
            return None
        d = r.json()
        return d if isinstance(d, list) else None
    except Exception:  # noqa: BLE001
        return None


@router.get("/geo/rnb")
def rnb(
    lat: float = Query(...),
    lon: float = Query(...),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Référentiel National des Bâtiments : identifiant `rnb_id` du bâtiment sous le
    point + adresse validée. Sert de clé pivot vers la BDNB. Gratuit, sans clé."""
    get_authenticated_user(settings, authorization)
    b = _rnb_closest(lat, lon)
    if not b:
        return {"ok": True, "found": False, "lat": lat, "lon": lon}
    adr = (b.get("addresses") or [{}])[0] or {}
    parts = [adr.get("street_number"), adr.get("street"), adr.get("city_zipcode"), adr.get("city_name")]
    address = " ".join(str(p) for p in parts if p) or None
    return {
        "ok": True,
        "found": True,
        "lat": lat,
        "lon": lon,
        "rnb_id": b.get("rnb_id"),
        "status": b.get("status"),
        "distance_m": round(b.get("distance") or 0, 1),
        "address": address,
        "bdnb_id": _rnb_bdnb_bc_id(b),
    }


@router.get("/geo/bdnb")
def bdnb(
    lat: float = Query(...),
    lon: float = Query(...),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Base de Données Nationale des Bâtiments : caractéristiques du bâtiment sous le
    point (année, type, matériaux mur/toit, hauteur, niveaux, logements, DPE théorique,
    aléa argile). Chaînage RNB (bâtiment le plus proche) -> BDNB (id construction ->
    groupe -> fiche). Gratuit, offre Open sans clé."""
    get_authenticated_user(settings, authorization)
    building = _rnb_closest(lat, lon)
    rnb_id = (building or {}).get("rnb_id")
    bc = _rnb_bdnb_bc_id(building)
    if not bc:
        return {"ok": True, "found": False, "lat": lat, "lon": lon, "rnb_id": rnb_id}
    rows = _bdnb_rows("donnees/batiment_construction",
                      {"batiment_construction_id": f"eq.{bc}", "select": "batiment_groupe_id", "limit": 1})
    bg = (rows or [{}])[0].get("batiment_groupe_id") if rows else None
    if not bg:
        return {"ok": True, "found": False, "lat": lat, "lon": lon, "rnb_id": rnb_id}
    fields = ("annee_construction,classe_bilan_dpe,conso_5_usages_ep_m2,mat_mur_txt,"
              "mat_toit_txt,hauteur_mean,nb_niveau,nb_log,type_batiment_dpe,alea_argile")
    rows = _bdnb_rows("donnees/batiment_groupe_complet",
                      {"batiment_groupe_id": f"eq.{bg}", "select": fields, "limit": 1})
    d = (rows or [{}])[0] if rows else {}
    conso = d.get("conso_5_usages_ep_m2")
    return {
        "ok": True,
        "found": bool(d),
        "lat": lat,
        "lon": lon,
        "rnb_id": rnb_id,
        "batiment_groupe_id": bg,
        "annee_construction": d.get("annee_construction"),
        "classe_dpe": d.get("classe_bilan_dpe"),
        "conso_ep_m2": round(conso) if isinstance(conso, (int, float)) else None,
        "mat_mur": d.get("mat_mur_txt"),
        "mat_toit": d.get("mat_toit_txt"),
        "hauteur": d.get("hauteur_mean"),
        "nb_niveau": d.get("nb_niveau"),
        "nb_logements": d.get("nb_log"),
        "type_batiment": d.get("type_batiment_dpe"),
        "alea_argile": d.get("alea_argile"),
    }


@router.get("/geo/dpe")
def dpe(
    lat: float = Query(...),
    lon: float = Query(...),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """DPE ADEME (open data) : dernier diagnostic à proximité immédiate du point
    (étiquette DPE + GES réels, conso, date, adresse). Heuristique : rayon serré 90 m,
    le plus RÉCENT. Gratuit, sans clé."""
    get_authenticated_user(settings, authorization)
    results: list = []
    try:
        r = requests.get(f"{_DPE_DS}/lines", headers=_UA, timeout=25, params={
            "geo_distance": f"{lon},{lat},90",
            "sort": "-date_etablissement_dpe",
            "size": 1,
            "select": ("etiquette_dpe,etiquette_ges,date_etablissement_dpe,adresse_ban,"
                       "type_batiment,conso_5_usages_par_m2_ep,surface_habitable_logement"),
        })
        if r.ok:
            results = (r.json() or {}).get("results") or []
    except Exception:  # noqa: BLE001
        results = []
    d = results[0] if results else {}
    return {
        "ok": True,
        "found": bool(d),
        "lat": lat,
        "lon": lon,
        "etiquette_dpe": d.get("etiquette_dpe"),
        "etiquette_ges": d.get("etiquette_ges"),
        "date": d.get("date_etablissement_dpe"),
        "adresse": d.get("adresse_ban"),
        "type_batiment": d.get("type_batiment"),
        "conso_ep_m2": d.get("conso_5_usages_par_m2_ep"),
        "surface": d.get("surface_habitable_logement"),
    }
