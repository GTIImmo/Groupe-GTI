from __future__ import annotations

import base64
import json
import re
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings
from . import agent_registry


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
    # Terrain (bloc) — surtout type Terrain, mais aussi maisons avec parcelle
    "landConstructible",       # terrain_constructible (oui/non)
    "constructibleSurface",    # terrain_surface_constructible (m2)
    "shon",                    # SHON (m2)
    "landServiced",            # terrain_viabilise (oui/non)
    "waterConnection",         # terrain_raccordement_eau (oui/non)
    "gasConnection",           # terrain_raccordement_gaz (oui/non)
    "electricityConnection",   # terrain_raccordement_electricite (oui/non)
    "phoneConnection",         # terrain_raccordement_telephone (oui/non)
    "landWooded",              # terrain_arbore (oui/non)
    "landPoolable",            # terrain_piscinable (oui/non)
    "garden",
    "gardenSurface",           # SURFACE_JARDIN (m2) — le scan n'avait que jardin oui/non
    "pool",
    # Piscine (sous-bloc revele si pool=oui) — surtout maisons
    "poolType",        # PISCINE_TYPE (enterree, hors-sol...)
    "poolNature",      # PISCINE_NATURE (beton, coque...)
    "poolDetails",     # PISCINE_DETAILS (texte libre)
    "poolDimensions",  # PISCINE_DIMENSIONS (texte, ex. 8x4)
    "poolTreatment",   # PISCINE_TRAITEMENT (sel, chlore...)
    "poolHouse",       # POOL_HOUSE (oui/non)
    "poolHeated",      # PISCINE_CHAUFFEE (oui/non)
    "poolCovered",     # PISCINE_COUVERTE (oui/non)
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
    "coproSyndicateStatus",   # copropriete_statut_syndicat (procedure d'alerte/redressement/en cours/aucune)
    # Construction recente (bien neuf/recent) — groupe Hektor construction_recente
    "tenYearWarranty",        # garantie_decennale (oui/non)
    "damageInsurance",        # assurance_dommages_ouvrage (oui/non)
    "conformityCertificate",  # certificat_conformite (oui/non)
    "completionDeclaration",  # declaration_achevement_travaux (oui/non)
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
    "works",         # travaux a prevoir (texte) -> champ Hektor TRAVAUX
    "chargesDetail",  # detail des charges (texte) -> champ Hektor CHARGES_DETAIL
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


# Descriptions au niveau du champ (schema). Nudge le modele vision a TOUJOURS emettre
# certains champs qu'il saute sinon, meme avec une instruction dans le prompt. Mesure
# reelle sur propertyType "Longere" (type atypique) : 1/3 sans description -> 4/4 avec.
# Etendre ce dico aux autres champs recalcitrants au besoin (eau/assainissement/cuisine).
FIELD_DESCRIPTIONS: dict[str, str] = {
    "propertyType": (
        "OBLIGATOIRE : le type de bien inscrit dans le champ 'Type de bien' en haut de la "
        "fiche, recopie EXACTEMENT meme atypique ou hors liste (maison, longere, mas, corps "
        "de ferme, bastide, gite, terrain, appartement, studio...). Ne jamais laisser null "
        "si un type est ecrit sur la fiche."
    ),
}


def _field_schema(description: str | None = None) -> dict[str, Any]:
    # Sortie allegee : plus de rawText (inutilise cote front) -> ~1/3 de tokens de
    # sortie en moins => plus rapide. _normalize_extraction remet rawText=None pour
    # garder la forme de reponse stable.
    value_schema: dict[str, Any] = {"type": ["string", "null"]}
    if description:
        value_schema["description"] = description
    return {
        "type": "object",
        "properties": {
            "value": value_schema,
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
                "properties": {key: _field_schema(FIELD_DESCRIPTIONS.get(key)) for key in FIELD_KEYS},
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
        # Modele + prompt pilotes par le registre d'agents (repli sur le defaut en code
        # = comportement actuel si la table manque). Le schema JSON reste ci-dessous.
        spec = agent_registry.load_spec(self.settings, "scan_fiche")
        model = spec.model or self.settings.openai_vision_model
        prompt = agent_registry.render(spec.instructions, {})
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
                    # NON-strict : en strict, le modele DOIT emettre les 124 champs (meme
                    # vides) -> ~2000 tokens de sortie -> ~60s/page. En non-strict il n'emet
                    # que les champs trouves -> ~2,5x plus rapide et moins cher. Le front
                    # (_normalize_extraction) complete les champs absents a null.
                    "strict": False,
                    "schema": _schema(),
                }
            },
            "max_output_tokens": spec.max_output_tokens,
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
