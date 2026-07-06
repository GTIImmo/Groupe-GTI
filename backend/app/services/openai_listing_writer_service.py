from __future__ import annotations

import json
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings

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

    def generate(
        self,
        property_data: dict[str, Any],
        photo_urls: list[str] | None = None,
        custom_intro: str | None = None,
    ) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY non configure sur le backend")

        model = self.settings.openai_vision_model
        facts = _format_facts(property_data)
        has_photos = any(str(u).strip() for u in (photo_urls or []))
        prompt = (
            "Tu es redacteur immobilier expert (agence GTI Immobilier). Redige une annonce en francais "
            "a partir des seules DONNEES FACTUELLES fournies.\n"
            "Regles :\n"
            "- N'utilise QUE les faits fournis ; n'invente aucun chiffre ni caracteristique ; n'affirme rien d'incertain.\n"
            "- Style precis et evocateur, sans cliches ('coup de coeur', 'ecrin de verdure', 'prestations de qualite', "
            "'rare a la vente') ni superlatifs vides.\n"
            "- Valorise concretement : volumes, luminosite, exposition, distribution des pieces, atouts techniques "
            "(DPE, chauffage) et environnement.\n"
            "Produis (JSON) :\n"
            "- title : 60-70 caracteres (type + atout majeur + secteur).\n"
            "- accroche : 1 phrase (~140 caracteres) qui capte l'essentiel.\n"
            "- description : 3 courts paragraphes (exterieur/localisation ; interieur/distribution ; technique & "
            "conclusion), 700-1100 caracteres, sans repeter le titre.\n"
            "- highlights : 3 a 5 atouts concrets de 3 a 6 mots.\n"
        )
        if has_photos:
            prompt += "- Les photos servent a decrire l'ambiance et les volumes, jamais a deduire un chiffre.\n"
        if custom_intro and custom_intro.strip():
            prompt += f"- Consigne du negociateur : {custom_intro.strip()}\n"
        prompt += f"\nDONNEES FACTUELLES :\n{facts}"

        content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
        for url in (photo_urls or [])[:MAX_PHOTOS]:
            clean = str(url).strip()
            if clean:
                content.append({"type": "input_image", "image_url": clean})

        request_payload = {
            "model": model,
            "input": [{"role": "user", "content": content}],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "hektor_listing_description",
                    "strict": True,
                    "schema": _writer_schema(),
                }
            },
            "max_output_tokens": 1200,
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
            raise HTTPException(status_code=502, detail=message or "Erreur OpenAI (redacteur)")

        data = response.json()
        parsed = json.loads(_extract_output_text(data))
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=502, detail="Reponse OpenAI inattendue (redacteur)")
        usage = data.get("usage") or {}
        return {
            "title": str(parsed.get("title") or "").strip(),
            "accroche": str(parsed.get("accroche") or "").strip(),
            "description": str(parsed.get("description") or "").strip(),
            "highlights": [str(item).strip() for item in parsed.get("highlights", []) if str(item).strip()],
            "model": model,
            "usage": {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        }

    def polish_estimation(
        self,
        texts: dict[str, Any],
        property_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Ameliore les textes d'un AVIS DE VALEUR (issus d'une fiche manuscrite scannee) :
        # reformule en francais professionnel SANS inventer de fait ni de chiffre.
        if not self.settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY non configure sur le backend")

        model = self.settings.openai_vision_model
        facts = _format_facts(property_data or {})
        raw = _format_estimation_texts(texts or {})
        prompt = (
            "Tu es expert en evaluation immobiliere (agence GTI Immobilier). Reformule des NOTES BRUTES "
            "(issues d'une fiche manuscrite) en textes d'avis de valeur professionnels, a partir des seules "
            "infos fournies.\n"
            "Regles :\n"
            "- N'invente aucun fait ni chiffre ; conserve le sens ; corrige orthographe, grammaire et syntaxe.\n"
            "- Ton d'expert : objectif, sobre, argumente ; aucun langage commercial ni superlatif.\n"
            "- Un champ vide en entree reste vide en sortie (jamais de remplissage invente).\n"
            "Produis (JSON), concis et rediges :\n"
            "- appreciationEtat : etat general en 2 a 4 phrases completes.\n"
            "- pointsForts / pointsVigilance : listes, un element factuel par entree.\n"
            "- argumentairePrix : justification du positionnement (atouts/limites, coherence marche), 2 a 4 phrases.\n"
            "- avisConseiller : synthese et recommandation, 2 a 3 phrases.\n\n"
            f"NOTES BRUTES :\n{raw}\n\nFAITS DU BIEN :\n{facts}"
        )
        request_payload = {
            "model": model,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "hektor_estimation_redaction",
                    "strict": True,
                    "schema": _estimation_schema(),
                }
            },
            "max_output_tokens": 1200,
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
            raise HTTPException(status_code=502, detail=message or "Erreur OpenAI (avis de valeur)")

        data = response.json()
        parsed = json.loads(_extract_output_text(data))
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=502, detail="Reponse OpenAI inattendue (avis de valeur)")
        usage = data.get("usage") or {}
        return {
            "appreciationEtat": str(parsed.get("appreciationEtat") or "").strip(),
            "pointsForts": [str(item).strip() for item in parsed.get("pointsForts", []) if str(item).strip()],
            "pointsVigilance": [str(item).strip() for item in parsed.get("pointsVigilance", []) if str(item).strip()],
            "argumentairePrix": str(parsed.get("argumentairePrix") or "").strip(),
            "avisConseiller": str(parsed.get("avisConseiller") or "").strip(),
            "model": model,
            "usage": {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens"),
            },
        }
