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
    "bathroomCount",
    "showerRoomCount",
    "wcCount",
    "kitchen",
    "exposure",
    "view",
    "interiorState",
    "exteriorState",
    "landSurface",
    "terraceCount",
    "garageCount",
    "parkingInsideCount",
    "parkingOutsideCount",
    "constructionYear",
    "dpeValue",
    "gesValue",
    "coproLots",
    "coproCharges",
    "coproQuotePart",
    "coproWorksFund",
    "description",
    "note",
    "mandantCivility",
    "mandantLastName",
    "mandantFirstName",
    "mandantEmail",
    "mandantPhone",
]


def _field_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "value": {"type": ["string", "null"]},
            "confidence": {"type": ["number", "null"]},
            "rawText": {"type": ["string", "null"]},
        },
        "required": ["value", "confidence", "rawText"],
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
            "warnings": {"type": "array", "items": {"type": "string"}},
            "missingFields": {"type": "array", "items": {"type": "string"}},
            "rawNotes": {"type": ["string", "null"]},
        },
        "required": ["summaryConfidence", "fields", "warnings", "missingFields", "rawNotes"],
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
    return {
        "model": model,
        "summaryConfidence": _normalize_confidence(parsed.get("summaryConfidence")),
        "fields": normalized_fields,
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
            "Les champs mandant concernent le proprietaire/vendeur, pas le negociateur."
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
            "max_output_tokens": 3500,
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
