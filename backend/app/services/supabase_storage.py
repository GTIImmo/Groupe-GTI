"""Accès Supabase Storage côté backend (service_role) pour l'avis de valeur.

Sert à retrouver le PDF d'un dossier dans ``app_console_document`` (écrit par le
worker au Lot 1) et à produire une URL signée temporaire — utilisée par la route
de téléchargement trackée du mail d'estimation.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from ..settings import Settings

CONSOLE_DOCS_BUCKET = "hektor-console-documents"


def _headers(settings: Settings) -> dict[str, str]:
    key = settings.supabase_service_role_key
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def find_estimation_pdf(settings: Settings, app_dossier_id: int) -> dict[str, Any] | None:
    """Avis de valeur (PDF) le plus récent d'un dossier, disponible dans le cloud."""
    r = requests.get(
        f"{settings.supabase_url}/rest/v1/app_console_document",
        headers=_headers(settings),
        params={
            "select": "storage_bucket,storage_path,storage_status,document_name,mime_type,created_at",
            "app_dossier_id": f"eq.{app_dossier_id}",
            "document_name": "ilike.Avis de valeur%",
            "storage_status": "eq.cloud_available",
            "order": "created_at.desc",
            "limit": "1",
        },
        timeout=30,
    )
    r.raise_for_status()
    rows = r.json() or []
    return rows[0] if rows else None


def create_signed_url(settings: Settings, bucket: str, path: str, expires_in: int = 900) -> str:
    """URL signée temporaire d'un objet du bucket (POST /storage/v1/object/sign)."""
    encoded_path = quote(path, safe="/")
    r = requests.post(
        f"{settings.supabase_url}/storage/v1/object/sign/{bucket}/{encoded_path}",
        headers=_headers(settings),
        json={"expiresIn": expires_in},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json() or {}
    signed = data.get("signedURL") or data.get("signedUrl")
    if not signed:
        raise RuntimeError("Supabase Storage: signedURL absent")
    return f"{settings.supabase_url}/storage/v1{signed}" if signed.startswith("/") else signed


def signed_url_for_estimation_pdf(settings: Settings, app_dossier_id: int, expires_in: int = 900) -> str | None:
    """Retrouve l'avis de valeur du dossier et renvoie son URL signée (ou None si absent)."""
    doc = find_estimation_pdf(settings, app_dossier_id)
    if not doc or not doc.get("storage_path"):
        return None
    bucket = doc.get("storage_bucket") or CONSOLE_DOCS_BUCKET
    return create_signed_url(settings, bucket, str(doc["storage_path"]), expires_in)
