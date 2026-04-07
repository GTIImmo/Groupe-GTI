from __future__ import annotations

from dataclasses import dataclass

import requests
from fastapi import Header, HTTPException

from .settings import Settings


@dataclass
class AuthenticatedUser:
    id: str
    email: str | None
    role: str | None = None
    is_active: bool | None = None


def _supabase_headers(settings: Settings, bearer_token: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    return headers


def get_authenticated_user(
    settings: Settings,
    authorization: str | None,
) -> AuthenticatedUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization bearer manquant")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="JWT vide")

    user_response = requests.get(
        f"{settings.supabase_url}/auth/v1/user",
        headers=_supabase_headers(settings, token),
        timeout=30,
    )
    if user_response.status_code != 200:
        raise HTTPException(status_code=401, detail="JWT Supabase invalide")

    user_payload = user_response.json()
    user_id = str(user_payload.get("id") or "").strip()
    if not user_id:
        raise HTTPException(status_code=401, detail="Utilisateur Supabase introuvable")

    return AuthenticatedUser(
        id=user_id,
        email=(user_payload.get("email") or None),
    )


def require_request_user(authorization: str | None = Header(default=None)) -> str | None:
    return authorization
