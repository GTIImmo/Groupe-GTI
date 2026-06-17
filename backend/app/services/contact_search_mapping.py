"""Mapping recherche contact → format job Hektor (Étape 2 espace client).

PORT FIDÈLE des fonctions du front (apps/hektor-v1/src/ContactSearchFields.tsx) :
- contactSearchValueFromSearch : recherche stockée -> valeur de formulaire
- contactSearchValueToInput     : valeur -> HektorContactSearchInput
- hContactSearchPayload (api.ts): input -> objet 'search' du job

But : reproduire EXACTEMENT ce que fait l'édition d'une recherche par le négociateur,
pour que la modif depuis l'espace client ait le même comportement (mêmes champs
conservés/simplifiés). On ne réinvente rien : on rejoue le chemin éprouvé.
"""

from __future__ import annotations

import json
import re
from typing import Any

# Équipements (code interface -> clé ITEM_ Hektor), identique au front.
EQUIP_ITEM_BY_CODE: dict[str, str] = {
    "garage_parking": "ITEM_GARAGE_PARKING", "terrasse": "ITEM_TERRASSE", "balcon": "ITEM_BALCON",
    "piscine": "ITEM_PISCINE", "ascenseur": "ITEM_ASCENSEUR", "cheminee": "ITEM_CHEMINEE",
    "cave": "ITEM_CAVE", "double_vitrage": "ITEM_DOUBLE_VITRAGE", "plain_pied": "ITEM_PLAIN_PIED",
    "grenier_comble": "ITEM_GRENIER_COMBLE", "acces_handi": "ITEM_ACCES_HANDI",
    "terrain_constructible": "ITEM_TERRAIN_CONSTRUCTIBLE", "terrain_arbore": "ITEM_TERRAIN_ARBORE",
    "terrain_piscinable": "ITEM_TERRAIN_PISCINABLE", "terrain_viabilise": "ITEM_TERRAIN_VIABILISE",
}

_NUM_RE = re.compile(r"[^0-9.]")
_CP_RE = re.compile(r"(\d{4,5})")


def _parse_json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return None


def _critere_map(raw: Any) -> dict[str, str]:
    parsed = _parse_json_safe(raw)
    items = parsed if isinstance(parsed, list) else (list(parsed.values()) if isinstance(parsed, dict) else [])
    out: dict[str, str] = {}
    for it in items:
        if isinstance(it, dict) and "cle" in it:
            k = str(it.get("cle") or "")
            v = it.get("valeur")
            if k:
                out[k] = "" if v is None else str(v)
    return out


def _num(value: Any, fallback: int) -> int:
    try:
        n = float(_NUM_RE.sub("", str(value if value is not None else "")))
    except ValueError:
        return fallback
    return int(n) if (n == n and n > 0) else fallback  # n==n écarte NaN


def _clean(value: Any) -> str | None:
    s = str(value).strip() if value is not None else ""
    return s or None


def search_to_value(src: dict[str, Any]) -> dict[str, Any]:
    """app_contact_search_current (1 ligne) -> valeur de formulaire (port de contactSearchValueFromSearch)."""
    crit = _critere_map(src.get("criteres_json"))
    villes = _parse_json_safe(src.get("villes_json"))
    localities: list[dict[str, str]] = []
    for entry in (villes if isinstance(villes, list) else []):
        s = str(entry or "")
        m = _CP_RE.search(s)
        city = _CP_RE.sub("", s).replace("·", "").replace(",", "").strip()
        postal = m.group(1) if m else ""
        if city or postal:
            localities.append({"city": city, "postalCode": postal})
    types_parsed = _parse_json_safe(src.get("types_json"))
    if isinstance(types_parsed, list):
        type_ids = [str(v) for v in types_parsed]
    elif isinstance(types_parsed, dict):
        type_ids = list(types_parsed.keys())
    else:
        type_ids = []
    equipments = [code for code, item in EQUIP_ITEM_BY_CODE.items()
                  if re.match(r"^(1|oui|true)$", str(crit.get(item, "")), re.I)]
    return {
        "offerCode": str(src.get("offre")) if src.get("offre") else "0",
        "typeIds": type_ids or ["1"],
        "localities": localities,
        "priceMin": _num(src.get("prix_min"), 120000),
        "priceMax": _num(src.get("prix_max"), 250000),
        "priceMargin": crit.get("ITEM_PRIX_MARGE", ""),
        "surfaceMin": _num(src.get("surface_min"), 0),
        "landSurfaceMin": _num(src.get("surface_terrain_min"), 0),
        "rooms": _num(src.get("pieces_min"), 0),
        "bedrooms": _num(src.get("chambre_min"), 0),
        "bathrooms": _num(crit.get("ITEM_SDB_SDE_MIN"), 0),
        "equipments": equipments,
        "dpeLetter": crit.get("ITEM_DPE_CONS_LETTER", ""),
    }


def value_to_input(value: dict[str, Any]) -> dict[str, Any]:
    """Valeur de formulaire -> HektorContactSearchInput (port de contactSearchValueToInput)."""
    return {
        "kind": "search_criteria", "enabled": True,
        "offerCode": value["offerCode"],
        "propertyTypeIds": value["typeIds"],
        "localities": [{"city": l["city"], "postalCode": l["postalCode"]} for l in value["localities"]],
        "priceMin": str(value["priceMin"]),
        "priceMax": str(value["priceMax"]),
        "priceMargin": value.get("priceMargin") or None,
        "surfaceMin": str(value["surfaceMin"]) if value.get("surfaceMin") else None,
        "landSurfaceMin": str(value["landSurfaceMin"]) if value.get("landSurfaceMin") else None,
        "roomsMin": str(value["rooms"]) if value.get("rooms") else None,
        "bedroomsMin": str(value["bedrooms"]) if value.get("bedrooms") else None,
        "bathroomsMin": str(value["bathrooms"]) if value.get("bathrooms") else None,
        "dpeLetter": value.get("dpeLetter") or None,
        "equipments": value["equipments"],
    }


def to_hektor_search(inp: dict[str, Any]) -> dict[str, Any]:
    """HektorContactSearchInput -> objet 'search' du job (port de hContactSearchPayload)."""
    g = inp.get
    return {
        "kind": "search_criteria",
        "enabled": inp.get("enabled", True) is not False,
        "offerCode": _clean(g("offerCode")),
        "propertyTypeIds": g("propertyTypeIds") if isinstance(g("propertyTypeIds"), list) else [],
        "city": _clean(g("city")),
        "postalCode": _clean(g("postalCode")),
        "localities": g("localities") if isinstance(g("localities"), list) else None,
        "priceMin": _clean(g("priceMin")), "priceMax": _clean(g("priceMax")), "priceMargin": _clean(g("priceMargin")),
        "surfaceMin": _clean(g("surfaceMin")), "surfaceMax": _clean(g("surfaceMax")),
        "landSurfaceMin": _clean(g("landSurfaceMin")), "landSurfaceMax": _clean(g("landSurfaceMax")),
        "livingRoomSurfaceMin": _clean(g("livingRoomSurfaceMin")), "livingRoomSurfaceMax": _clean(g("livingRoomSurfaceMax")),
        "roomsMin": _clean(g("roomsMin")), "roomsMax": _clean(g("roomsMax")),
        "bedroomsMin": _clean(g("bedroomsMin")), "bedroomsMax": _clean(g("bedroomsMax")),
        "bathroomsMin": _clean(g("bathroomsMin")), "bathroomsMax": _clean(g("bathroomsMax")),
        "floorsMin": _clean(g("floorsMin")), "floorsMax": _clean(g("floorsMax")),
        "levelsMin": _clean(g("levelsMin")), "levelsMax": _clean(g("levelsMax")),
        "dpeLetter": _clean(g("dpeLetter")), "heatingType": _clean(g("heatingType")),
        "heatingEnergy": _clean(g("heatingEnergy")), "kitchenType": _clean(g("kitchenType")),
        "occupation": _clean(g("occupation")),
        "equipments": g("equipments") if isinstance(g("equipments"), list) else [],
        "particulariteIds": g("particulariteIds") if isinstance(g("particulariteIds"), list) else [],
    }


# Champs simples éditables depuis l'espace client (Étape 2).
EDITABLE_FIELDS = {"priceMin", "priceMax", "surfaceMin", "rooms", "bedrooms"}


def apply_client_edits(value: dict[str, Any], edits: dict[str, Any]) -> dict[str, Any]:
    """Applique uniquement les champs autorisés (budget, surface, pièces, chambres)."""
    out = dict(value)
    for k in EDITABLE_FIELDS:
        if k in edits and edits[k] is not None:
            try:
                out[k] = int(float(str(edits[k]).replace(" ", "")))
            except (TypeError, ValueError):
                pass
    return out


def build_job_search_payload(src: dict[str, Any], edits: dict[str, Any], *, search_index: int) -> dict[str, Any]:
    """Construit le `search_payload` du RPC app_console_create_update_contact_search_job."""
    value = apply_client_edits(search_to_value(src), edits)
    search = to_hektor_search(value_to_input(value))
    return {"search": search, "search_index": search_index}
