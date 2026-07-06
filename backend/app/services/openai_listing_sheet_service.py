from __future__ import annotations

import base64
import json
import re
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 12 * 1024 * 1024


FIELD_KEYS = [
    "title",
    "propertyType",
    "agency",
    "negotiatorName",
    "address",
    "postalCode",
    "city",
    "price",
    "netSellerPrice",
    "surface",
    "carrezSurface",
    "livingSurface",
    "roomCount",
    "bedroomCount",
    "levelCount",
    "bathroomCount",
    "showerRoomCount",
    "wcCount",
    "kitchen",
    "exposure",
    "view",
    "interiorState",
    "exteriorState",
    "landSurface",
    "garden",
    "pool",
    "terraceCount",
    "garageCount",
    "garageSurface",
    "parkingInsideCount",
    "parkingOutsideCount",
    "constructionYear",
    "dpeValue",
    "gesValue",
    "coproLots",
    "coproCharges",
    "coproQuotePart",
    "coproWorksFund",
    # Localisation (optionnel)
    "immeuble",
    "transport",
    "proximity",
    "environment",
    # Interieur
    "kitchenEquipment",
    "particularities",
    # Exterieur detaille
    "terrace",
    "terraceSurface",
    "balcony",
    "balconyCount",
    "balconySurface",
    "cellar",
    "cellarSurface",
    "floor",
    "topFloor",
    "floorsCount",
    "partyWalls",
    "residence",
    "residenceType",
    # Equipements
    "heatingFormat",
    "heatingType",
    "heatingEnergy",
    "water",
    "sanitation",
    "waterDistribution",
    "waterEnergy",
    "elevator",
    "disabledAccess",
    "airConditioning",
    "fireplace",
    "electricShutters",
    "doubleGlazing",
    "tripleGlazing",
    "fiber",
    "armoredDoor",
    "intercom",
    "videophone",
    "alarm",
    "digicode",
    "smokeDetector",
    "caretaker",
    # Diagnostics / energie (optionnel)
    "dpeDate",
    "finalEnergy",
    "energyCostMin",
    "energyCostMax",
    # Copropriete / disponibilite
    "coproperty",
    "coproLot",
    "safeguardPlan",
    "available",
    "releaseDate",
    "availabilityDate",
    "keys",
    # Estimation (uniquement si le bien est une estimation)
    "estimationAmount",
    "estimationDate",
    # Charges / fiscalite (info annonce, pas le mandat)
    "propertyTax",
    "housingTax",
    # Avis de valeur (modale estimation) - saisis a la main par le commercial
    "estimationLow",        # fourchette basse
    "estimationHigh",       # fourchette haute
    "stateNote",            # note d'etat globale 1-5
    "stateLabel",           # libelle d'etat (ex. "bon etat general")
    "stateAppreciation",    # appreciation redigee de l'etat
    "strongPoints",         # points forts (un par ligne)
    "watchPoints",          # points de vigilance (un par ligne)
    "priceArgument",        # argumentaire de prix
    "advisorOpinion",       # avis du conseiller
    "chargeEnergy",         # charges energie EUR/an
    "chargeWater",          # charges eau EUR/an
    "chargeInsurance",      # charges assurance EUR/an
    "description",
    "note",
    "mandantCivility",
    "mandantLastName",
    "mandantFirstName",
    "mandantEmail",
    "mandantPhone",
    "mandantAddress",
    "mandantPostalCode",
    "mandantCity",
    # 2e mandant (indivision) — extraction prete ; rattachement a la creation a cabler
    "mandant2Civility",
    "mandant2LastName",
    "mandant2FirstName",
    "mandant2Email",
    "mandant2Phone",
    "mandant2Address",
    "mandant2PostalCode",
    "mandant2City",
]


def _field_schema() -> dict[str, Any]:
    # Sortie allegee : plus de rawText (inutilise cote front) -> ~1/3 de tokens de
    # sortie en moins => plus rapide. _normalize_extraction remet rawText=None pour
    # garder la forme de reponse stable.
    return {
        "type": "object",
        "properties": {
            "value": {"type": ["string", "null"]},
            "confidence": {"type": ["number", "null"]},
        },
        "required": ["value", "confidence"],
        "additionalProperties": False,
    }


# Composition = liste variable de pieces (chambre, cuisine, sejour...) avec type,
# detail, etage, surface et une note. Chaque piece = un objet ; nombre variable.
PIECE_KEYS = ["type", "detail", "etage", "surface", "note"]


def _piece_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {key: {"type": ["string", "null"]} for key in PIECE_KEYS},
        "required": PIECE_KEYS,
        "additionalProperties": False,
    }


# Bareme d'etat par poste (avis de valeur) : 8 postes fixes, chacun avec un niveau
# (neuf/bon/correct/a prevoir) et une precision libre.
STATE_POST_KEYS = ["poste", "level", "note"]


def _state_post_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {key: {"type": ["string", "null"]} for key in STATE_POST_KEYS},
        "required": STATE_POST_KEYS,
        "additionalProperties": False,
    }


def _schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "summaryConfidence": {"type": ["number", "null"]},
            "fields": {
                "type": "object",
                "properties": {key: _field_schema() for key in FIELD_KEYS},
                "required": FIELD_KEYS,
                "additionalProperties": False,
            },
            "pieces": {"type": "array", "items": _piece_schema()},
            "statePosts": {"type": "array", "items": _state_post_schema()},
            "warnings": {"type": "array", "items": {"type": "string"}},
            "missingFields": {"type": "array", "items": {"type": "string"}},
            "rawNotes": {"type": ["string", "null"]},
        },
        "required": ["summaryConfidence", "fields", "pieces", "statePosts", "warnings", "missingFields", "rawNotes"],
        "additionalProperties": False,
    }


def _extract_data_url(value: str, mime_type: str | None) -> tuple[str, str]:
    raw = value.strip()
    detected_mime = (mime_type or "").strip().lower()
    match = re.match(r"^data:(?P<mime>[-\w.+/]+);base64,(?P<data>.+)$", raw, re.IGNORECASE | re.DOTALL)
    if match:
        detected_mime = match.group("mime").lower()
        raw = match.group("data").strip()
    if detected_mime == "image/jpg":
        detected_mime = "image/jpeg"
    if detected_mime not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Format image refuse. Utilise JPG, PNG ou WebP.")
    try:
        decoded = base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Image base64 invalide") from exc
    if len(decoded) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image trop lourde pour le scan OCR")
    return detected_mime, base64.b64encode(decoded).decode("ascii")


def _extract_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    for output in payload.get("output") or []:
        if not isinstance(output, dict):
            continue
        for content in output.get("content") or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str) and content["text"].strip():
                return content["text"].strip()
    raise HTTPException(status_code=502, detail="OpenAI n'a pas retourne de texte exploitable")


def _normalize_confidence(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    confidence = float(value)
    if confidence > 1 and confidence <= 100:
        confidence = confidence / 100
    return min(1, max(0, confidence))


def _normalize_extraction(parsed: dict[str, Any], model: str) -> dict[str, Any]:
    fields = parsed.get("fields") if isinstance(parsed.get("fields"), dict) else {}
    normalized_fields: dict[str, dict[str, Any]] = {}
    for key in FIELD_KEYS:
        item = fields.get(key) if isinstance(fields, dict) else None
        if not isinstance(item, dict):
            item = {}
        value = item.get("value")
        raw_text = item.get("rawText")
        normalized_fields[key] = {
            "value": str(value).strip() if value is not None and str(value).strip() else None,
            "confidence": _normalize_confidence(item.get("confidence")),
            "rawText": str(raw_text).strip() if raw_text is not None and str(raw_text).strip() else None,
        }
    normalized_pieces: list[dict[str, Any]] = []
    raw_pieces = parsed.get("pieces")
    if isinstance(raw_pieces, list):
        for piece in raw_pieces:
            if not isinstance(piece, dict):
                continue
            cleaned = {key: (str(piece.get(key)).strip() if piece.get(key) is not None and str(piece.get(key)).strip() else None) for key in PIECE_KEYS}
            if any(cleaned.values()):
                normalized_pieces.append(cleaned)
    normalized_posts: list[dict[str, Any]] = []
    raw_posts = parsed.get("statePosts")
    if isinstance(raw_posts, list):
        for post in raw_posts:
            if not isinstance(post, dict):
                continue
            cleaned = {key: (str(post.get(key)).strip() if post.get(key) is not None and str(post.get(key)).strip() else None) for key in STATE_POST_KEYS}
            if any(cleaned.values()):
                normalized_posts.append(cleaned)
    return {
        "model": model,
        "summaryConfidence": _normalize_confidence(parsed.get("summaryConfidence")),
        "fields": normalized_fields,
        "pieces": normalized_pieces,
        "statePosts": normalized_posts,
        "warnings": [str(item).strip() for item in parsed.get("warnings", []) if str(item).strip()] if isinstance(parsed.get("warnings"), list) else [],
        "missingFields": [str(item).strip() for item in parsed.get("missingFields", []) if str(item).strip()] if isinstance(parsed.get("missingFields"), list) else [],
        "rawNotes": str(parsed.get("rawNotes")).strip() if parsed.get("rawNotes") else None,
    }


class OpenAIListingSheetService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def extract(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY non configure sur le backend")

        mime_type, image_base64 = _extract_data_url(str(payload.get("imageBase64") or ""), payload.get("mimeType"))
        model = self.settings.openai_vision_model
        prompt = (
            "Tu lis une fiche papier d'annonce immobiliere francaise, souvent remplie a la main par un commercial. "
            "Retourne uniquement les donnees visibles. N'invente jamais une valeur absente ou illisible. "
            "Les montants et surfaces doivent etre retournes en chiffres simples, sans unite, espace ou symbole euro. "
            "Si une valeur est incertaine, baisse confidence. Si elle est illisible, value doit etre null. "
            "Les champs garden (jardin) et pool (piscine) valent 'oui' ou 'non' selon leur presence. "
            "garageSurface est une surface de garage en m2 (chiffres simples). "
            "levelCount est le nombre de niveaux/etages du bien. "
            "Les champs de presence (terrace, balcony, cellar, elevator, disabledAccess, airConditioning, "
            "fireplace, electricShutters, doubleGlazing, tripleGlazing, fiber, armoredDoor, intercom, "
            "videophone, alarm, digicode, smokeDetector, caretaker, coproperty, safeguardPlan, available, "
            "topFloor) valent 'oui' ou 'non'. "
            "heatingFormat/heatingType/heatingEnergy = format, type et energie du chauffage en clair "
            "(ex: individuel, gaz de ville, electrique). water=type d'eau, sanitation=assainissement. "
            "estimationAmount = valeur estimee du bien (chiffres), uniquement s'il s'agit d'une estimation. "
            "estimationDate = la date inscrite en haut de la fiche (libelle 'Date estimation'), format tel qu'ecrit. "
            "propertyTax=taxe fonciere, housingTax=taxe d'habitation (chiffres). "
            "Les champs mandant (dont mandantAddress/mandantPostalCode/mandantCity) concernent "
            "le proprietaire/vendeur, pas le negociateur. Les champs mandant2* concernent un SECOND "
            "proprietaire (indivision) si la fiche en mentionne un, sinon null. "
            "N'extrais AUCUN numero ni donnee de mandat (type, duree, honoraires) : hors perimetre. "
            "Le tableau 'pieces' liste la COMPOSITION du logement : une entree par piece decrite "
            "(type ex. Chambre/Cuisine/Sejour/Salle de bains/WC/Entree/Bureau/Dressing/Buanderie, "
            "detail ex. 'suite parentale', etage, surface en m2, note libre). Nombre de pieces variable ; "
            "liste vide si la fiche n'en decrit aucune. "
            "Les champs d'avis de valeur (estimationLow/estimationHigh/estimee via estimationAmount, "
            "stateNote 1-5, stateLabel, stateAppreciation, strongPoints, watchPoints, priceArgument, "
            "advisorOpinion, chargeEnergy/chargeWater/chargeInsurance) sont saisis a la main par le "
            "commercial pour l'estimation. Le tableau 'statePosts' est le bareme d'etat : une entree "
            "par poste evalue (poste ex. 'Toiture', level = neuf/bon/correct/a prevoir, note = precision "
            "ex. 'refaite 2019') ; liste vide si non rempli."
        )
        request_payload = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:{mime_type};base64,{image_base64}"},
                    ],
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "hektor_listing_sheet_extraction",
                    "strict": True,
                    "schema": _schema(),
                }
            },
            "max_output_tokens": 6500,
        }
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=request_payload,
            timeout=120,
        )
        if not response.ok:
            try:
                error_payload = response.json()
                message = error_payload.get("error", {}).get("message") or error_payload.get("message")
            except Exception:
                message = response.text.strip()
            raise HTTPException(status_code=502, detail=message or "Erreur OpenAI Vision")

        output_text = _extract_output_text(response.json())
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Reponse OpenAI non JSON") from exc
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=502, detail="Reponse OpenAI inattendue")
        return _normalize_extraction(parsed, model)
