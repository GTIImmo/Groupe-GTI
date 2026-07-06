from __future__ import annotations

import json
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings
from . import agent_registry

# Agent "Redacteur d'annonce" (Phase 3, premier agent IA, propose-only).
# Genere un titre + description + points forts a partir des donnees FACTUELLES
# d'un bien et de ses photos. Ne fait AUCUNE ecriture : il propose, l'humain valide.
# Mirroir du pattern OpenAIListingSheetService (API Responses, sortie JSON strict).

MAX_PHOTOS = 4


def _writer_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "accroche": {"type": "string"},
            "description": {"type": "string"},
            "highlights": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["title", "accroche", "description", "highlights"],
        "additionalProperties": False,
    }


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


def _format_facts(property_data: dict[str, Any]) -> str:
    # Ordre lisible ; on ne garde que les valeurs renseignees (pas d'invention en aval).
    labels = [
        ("type_bien", "Type de bien"),
        ("ville", "Ville"),
        ("code_postal", "Code postal"),
        ("prix", "Prix (EUR)"),
        ("surface", "Surface habitable (m2)"),
        ("surface_terrain", "Surface terrain (m2)"),
        ("pieces", "Nombre de pieces"),
        ("chambres", "Chambres"),
        ("sdb", "Salles de bain"),
        ("etage", "Etage"),
        ("exposition", "Exposition"),
        ("etat", "Etat general"),
        ("chauffage", "Chauffage"),
        ("dpe", "DPE"),
        ("ges", "GES"),
        ("annee_construction", "Annee de construction"),
        ("equipements", "Equipements"),
        ("secteur", "Secteur / environnement"),
        ("composition", "Composition (pieces)"),
        ("atouts", "Atouts / points forts"),
    ]
    lines: list[str] = []
    for key, label in labels:
        value = property_data.get(key)
        if value is None:
            continue
        text = ", ".join(str(v).strip() for v in value if str(v).strip()) if isinstance(value, (list, tuple)) else str(value).strip()
        if text:
            lines.append(f"- {label} : {text}")
    return "\n".join(lines) if lines else "- (aucune donnee factuelle fournie)"


def _estimation_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "appreciationEtat": {"type": "string"},
            "pointsForts": {"type": "array", "items": {"type": "string"}},
            "pointsVigilance": {"type": "array", "items": {"type": "string"}},
            "argumentairePrix": {"type": "string"},
            "avisConseiller": {"type": "string"},
        },
        "required": ["appreciationEtat", "pointsForts", "pointsVigilance", "argumentairePrix", "avisConseiller"],
        "additionalProperties": False,
    }


def _format_estimation_texts(texts: dict[str, Any]) -> str:
    labels = [
        ("appreciationEtat", "Appreciation de l'etat"),
        ("pointsForts", "Points forts"),
        ("pointsVigilance", "Points de vigilance"),
        ("argumentairePrix", "Argumentaire de prix"),
        ("avisConseiller", "Avis du conseiller"),
    ]
    lines: list[str] = []
    for key, label in labels:
        value = texts.get(key)
        if value is None:
            continue
        text = ", ".join(str(v).strip() for v in value if str(v).strip()) if isinstance(value, (list, tuple)) else str(value).strip()
        if text:
            lines.append(f"- {label} : {text}")
    return "\n".join(lines) if lines else "- (aucune note fournie)"


class OpenAIListingWriterService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _run_json_agent(
        self,
        agent_key: str,
        variables: dict[str, Any],
        schema: dict[str, Any],
        schema_name: str,
        extra_content: list[dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], str]:
        # Point d'appel unique : lit la fiche de l'agent (registre Supabase + repli
        # code), rend le prompt, appelle OpenAI, parse le JSON strict. HTTP + erreurs
        # + parse mutualises pour tous les agents. Le schema reste fourni par l'appelant
        # (couple au parsing en aval).
        if not self.settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY non configure sur le backend")

        spec = agent_registry.load_spec(self.settings, agent_key)
        model = spec.model or self.settings.openai_vision_model
        prompt = agent_registry.render(spec.instructions, variables)

        content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
        if extra_content:
            content.extend(extra_content)

        request_payload = {
            "model": model,
            "input": [{"role": "user", "content": content}],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
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
            raise HTTPException(status_code=502, detail=message or f"Erreur OpenAI ({agent_key})")

        data = response.json()
        parsed = json.loads(_extract_output_text(data))
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=502, detail=f"Reponse OpenAI inattendue ({agent_key})")
        usage_raw = data.get("usage") or {}
        usage = {
            "input_tokens": usage_raw.get("input_tokens"),
            "output_tokens": usage_raw.get("output_tokens"),
            "total_tokens": usage_raw.get("total_tokens"),
        }
        return parsed, usage, model

    def generate(
        self,
        property_data: dict[str, Any],
        photo_urls: list[str] | None = None,
        custom_intro: str | None = None,
    ) -> dict[str, Any]:
        has_photos = any(str(u).strip() for u in (photo_urls or []))
        variables = {
            "facts": _format_facts(property_data),
            "photo_line": (
                "- Les photos servent a decrire l'ambiance et les volumes, jamais a deduire un chiffre.\n"
                if has_photos else ""
            ),
            "custom_intro_line": (
                f"- Consigne du negociateur : {custom_intro.strip()}\n"
                if (custom_intro and custom_intro.strip()) else ""
            ),
        }
        extra_content: list[dict[str, Any]] = []
        for url in (photo_urls or [])[:MAX_PHOTOS]:
            clean = str(url).strip()
            if clean:
                extra_content.append({"type": "input_image", "image_url": clean})

        parsed, usage, model = self._run_json_agent(
            "redacteur", variables, _writer_schema(), "hektor_listing_description",
            extra_content=extra_content,
        )
        return {
            "title": str(parsed.get("title") or "").strip(),
            "accroche": str(parsed.get("accroche") or "").strip(),
            "description": str(parsed.get("description") or "").strip(),
            "highlights": [str(item).strip() for item in parsed.get("highlights", []) if str(item).strip()],
            "model": model,
            "usage": usage,
        }

    def polish_estimation(
        self,
        texts: dict[str, Any],
        property_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Ameliore les textes d'un AVIS DE VALEUR (issus d'une fiche manuscrite scannee) :
        # reformule en francais professionnel SANS inventer de fait ni de chiffre.
        variables = {
            "raw": _format_estimation_texts(texts or {}),
            "facts": _format_facts(property_data or {}),
        }
        parsed, usage, model = self._run_json_agent(
            "avis_valeur", variables, _estimation_schema(), "hektor_estimation_redaction",
        )
        return {
            "appreciationEtat": str(parsed.get("appreciationEtat") or "").strip(),
            "pointsForts": [str(item).strip() for item in parsed.get("pointsForts", []) if str(item).strip()],
            "pointsVigilance": [str(item).strip() for item in parsed.get("pointsVigilance", []) if str(item).strip()],
            "argumentairePrix": str(parsed.get("argumentairePrix") or "").strip(),
            "avisConseiller": str(parsed.get("avisConseiller") or "").strip(),
            "model": model,
            "usage": usage,
        }
