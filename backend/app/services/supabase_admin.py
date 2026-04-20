from __future__ import annotations

from typing import Any

import requests
from fastapi import HTTPException

from ..auth import AuthenticatedUser
from ..settings import Settings


class SupabaseAdminService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _admin_headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }

    def _rest_headers(self) -> dict[str, str]:
        return self._admin_headers()

    def _raise_for_response(self, response: requests.Response, fallback: str) -> None:
        if response.ok:
            return
        try:
            payload = response.json()
            message = payload.get("msg") or payload.get("message") or payload.get("error_description") or payload.get("error")
        except Exception:
            message = response.text.strip() or fallback
        raise HTTPException(status_code=response.status_code if response.status_code >= 400 else 500, detail=str(message))

    def load_profile(self, user: AuthenticatedUser) -> dict[str, Any]:
        params = {
            "select": "id,email,role,is_active,display_name,first_name,last_name",
            "or": f"(id.eq.{user.id},email.ilike.{user.email or ''})",
        }
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params=params,
            timeout=30,
        )
        self._raise_for_response(response, "Unable to load app_user_profile")
        rows = response.json() or []
        for row in rows:
            if str(row.get("id") or "") == user.id:
                return row
        return rows[0] if rows else {}

    def assert_admin(self, user: AuthenticatedUser) -> dict[str, Any]:
        profile = self.load_profile(user)
        if not profile:
            raise HTTPException(status_code=403, detail=f"Profil admin introuvable pour {user.email or user.id}")
        role = str(profile.get("role") or "")
        is_active = profile.get("is_active")
        if role not in {"admin", "manager"} or is_active is not True:
            raise HTTPException(status_code=403, detail="Acces admin refuse")
        return profile

    def list_users(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params={"select": "*", "order": "is_active.desc,display_name.asc"},
            timeout=30,
        )
        self._raise_for_response(response, "Unable to list users")
        return response.json() or []

    def _load_profile_by_id(self, user_id: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params={"select": "*", "id": f"eq.{user_id}", "limit": 1},
            timeout=30,
        )
        self._raise_for_response(response, "Unable to read user profile by id")
        rows = response.json() or []
        return rows[0] if rows else {}

    def _upsert_profile(self, profile_payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers={**self._rest_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "id"},
            json=[profile_payload],
            timeout=30,
        )
        self._raise_for_response(response, "Unable to upsert user profile")
        rows = response.json() or []
        if rows:
            return rows[0]
        profile = self._load_profile_by_id(str(profile_payload["id"]))
        if not profile:
            raise HTTPException(status_code=500, detail="Profil utilisateur non cree dans app_user_profile")
        return profile

    def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        display_name = payload.get("displayName") or " ".join(filter(None, [payload.get("firstName"), payload.get("lastName")])).strip() or payload["email"]
        auth_response = requests.post(
            f"{self.settings.supabase_url}/auth/v1/admin/users",
            headers=self._admin_headers(),
            json={
                "email": payload["email"],
                "password": payload["password"],
                "email_confirm": True,
                "user_metadata": {
                    "first_name": payload.get("firstName") or None,
                    "last_name": payload.get("lastName") or None,
                    "display_name": display_name,
                },
            },
            timeout=30,
        )
        self._raise_for_response(auth_response, "Unable to create auth user")
        auth_payload = auth_response.json()
        auth_user = auth_payload.get("user") or auth_payload
        user_id = auth_user.get("id")
        if not user_id:
            lookup_response = requests.get(
                f"{self.settings.supabase_url}/auth/v1/admin/users",
                headers=self._admin_headers(),
                params={"page": 1, "per_page": 1000},
                timeout=30,
            )
            self._raise_for_response(lookup_response, "Unable to read auth users after create")
            users = lookup_response.json().get("users") or []
            matched = next((item for item in users if str(item.get("email") or "").strip().lower() == payload["email"].strip().lower()), None)
            user_id = matched.get("id") if matched else None
        if not user_id:
            raise HTTPException(status_code=500, detail="Supabase auth user id missing")

        profile_payload = {
            "id": user_id,
            "email": payload["email"],
            "role": payload["role"],
            "first_name": payload.get("firstName") or None,
            "last_name": payload.get("lastName") or None,
            "display_name": display_name,
            "is_active": payload.get("isActive", True),
        }
        profile = self._upsert_profile(profile_payload)
        if str(profile.get("id") or "") != str(user_id):
            raise HTTPException(status_code=500, detail="Profil utilisateur incoherent apres creation")
        return {"ok": True, "userId": user_id, "email": payload["email"]}

    def update_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        display_name = payload.get("displayName") or " ".join(filter(None, [payload.get("firstName"), payload.get("lastName")])).strip() or payload["email"]
        response = requests.patch(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params={"id": f"eq.{payload['id']}"},
            json={
                "email": payload["email"],
                "role": payload["role"],
                "first_name": payload.get("firstName") or None,
                "last_name": payload.get("lastName") or None,
                "display_name": display_name,
                "is_active": payload.get("isActive", True),
            },
            timeout=30,
        )
        self._raise_for_response(response, "Unable to update user profile")
        return {"ok": True}

    def send_reset(self, email: str) -> dict[str, Any]:
        body: dict[str, Any] = {"email": email}
        if self.settings.app_base_url:
            body["redirect_to"] = self.settings.app_base_url
        response = requests.post(
            f"{self.settings.supabase_url}/auth/v1/recover",
            headers=self._admin_headers(),
            json=body,
            timeout=30,
        )
        self._raise_for_response(response, "Unable to send reset email")
        return {"ok": True}
