from __future__ import annotations

from datetime import datetime, timezone
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

    def _normalize_email(self, email: str | None) -> str:
        return str(email or "").strip().lower()

    def _is_workspace_email(self, email: str | None) -> bool:
        normalized = self._normalize_email(email)
        domain = self.settings.google_workspace_domain
        return bool(normalized and normalized.endswith(f"@{domain}"))

    def _rest_rows(self, table: str, params: dict[str, Any], fallback: str) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/{table}",
            headers=self._rest_headers(),
            params=params,
            timeout=30,
        )
        self._raise_for_response(response, fallback)
        return response.json() or []

    def _resolve_hektor_google_identity(self, email: str, role: str) -> dict[str, Any]:
        normalized = self._normalize_email(email)
        user_rows = [
            row for row in self._rest_rows(
                "app_user_directory",
                {
                    "select": "id_user,user_type,display_name,email",
                    "email": f"ilike.{normalized}",
                    "user_type": "eq.NEGO",
                    "limit": 10,
                },
                "Unable to resolve Hektor user directory",
            )
            if self._normalize_email(row.get("email")) == normalized and str(row.get("user_type") or "").upper() == "NEGO"
        ]
        agency_rows = [
            row for row in self._rest_rows(
                "app_hektor_negotiator_agency_directory",
                {
                    "select": "hektor_negociateur_id,hektor_user_id,hektor_agence_id,agence_id_user,agence_nom,display_name,email,is_active",
                    "email": f"ilike.{normalized}",
                    "is_active": "eq.true",
                    "limit": 20,
                },
                "Unable to resolve Hektor negotiator agency directory",
            )
            if self._normalize_email(row.get("email")) == normalized and row.get("is_active") is True
        ]
        metadata: dict[str, Any] = {
            "match_source": "auto_create_user",
            "user_directory_count": len(user_rows),
            "active_agency_directory_count": len(agency_rows),
        }

        conflict_reason: str | None = None
        selected_user = user_rows[0] if len(user_rows) == 1 else None
        selected_agency: dict[str, Any] | None = None

        if len(user_rows) > 1:
            conflict_reason = "multiple_active_hektor_users_for_email"
        elif selected_user:
            user_id = str(selected_user.get("id_user") or "").strip()
            matching_agencies = [row for row in agency_rows if str(row.get("hektor_user_id") or "").strip() == user_id]
            if len(matching_agencies) == 1:
                selected_agency = matching_agencies[0]
            elif len(matching_agencies) > 1:
                conflict_reason = "multiple_active_agencies_for_hektor_user"
            elif len(agency_rows) == 1:
                conflict_reason = "hektor_user_and_agency_directory_mismatch"
        elif len(agency_rows) == 1:
            selected_agency = agency_rows[0]
        elif len(agency_rows) > 1:
            conflict_reason = "multiple_active_agencies_for_email"

        if conflict_reason:
            metadata["conflict_reason"] = conflict_reason
            return {
                "link_status": "conflict",
                "hektor_user_id": None,
                "hektor_negociateur_id": None,
                "negociateur_email": None,
                "metadata_json": metadata,
            }

        if selected_agency:
            metadata["match_source"] = "app_hektor_negotiator_agency_directory"
            metadata["agence_nom"] = selected_agency.get("agence_nom")
            return {
                "link_status": "linked",
                "hektor_user_id": str(selected_agency.get("hektor_user_id") or "").strip() or None,
                "hektor_negociateur_id": str(selected_agency.get("hektor_negociateur_id") or "").strip() or None,
                "negociateur_email": self._normalize_email(selected_agency.get("email")) or normalized,
                "metadata_json": metadata,
            }

        if selected_user:
            metadata["match_source"] = "app_user_directory"
            return {
                "link_status": "linked",
                "hektor_user_id": str(selected_user.get("id_user") or "").strip() or None,
                "hektor_negociateur_id": None,
                "negociateur_email": self._normalize_email(selected_user.get("email")) or normalized,
                "metadata_json": metadata,
            }

        metadata["match_source"] = "workspace_only"
        if role == "commercial":
            metadata["conflict_reason"] = "commercial_without_hektor_match"
            return {
                "link_status": "pending",
                "hektor_user_id": None,
                "hektor_negociateur_id": None,
                "negociateur_email": None,
                "metadata_json": metadata,
            }

        return {
            "link_status": "linked",
            "hektor_user_id": None,
            "hektor_negociateur_id": None,
            "negociateur_email": None,
            "metadata_json": metadata,
        }

    def _sync_google_workspace_identity(self, *, user_id: str, email: str, role: str, is_active: bool) -> dict[str, Any] | None:
        normalized = self._normalize_email(email)
        if not self._is_workspace_email(normalized):
            if is_active:
                raise HTTPException(status_code=400, detail=f"Utilisateur actif hors domaine {self.settings.google_workspace_domain} refuse")
            return None

        resolved = self._resolve_hektor_google_identity(normalized, role) if is_active else {
            "link_status": "disabled",
            "hektor_user_id": None,
            "hektor_negociateur_id": None,
            "negociateur_email": None,
            "metadata_json": {"match_source": "disabled_profile"},
        }
        now = datetime.now(timezone.utc).isoformat()
        identity_payload = {
            "app_user_id": user_id,
            "google_email": normalized,
            "workspace_domain": self.settings.google_workspace_domain,
            "hektor_user_id": resolved["hektor_user_id"],
            "hektor_negociateur_id": resolved["hektor_negociateur_id"],
            "negociateur_email": resolved["negociateur_email"],
            "link_status": resolved["link_status"],
            "is_active": bool(is_active),
            "last_checked_at": now,
            "metadata_json": resolved["metadata_json"],
            "updated_at": now,
        }
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/app_google_workspace_identity",
            headers={**self._rest_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "app_user_id"},
            json=[identity_payload],
            timeout=30,
        )
        self._raise_for_response(response, "Unable to upsert app_google_workspace_identity")
        rows = response.json() or []
        return rows[0] if rows else identity_payload

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

    def assert_active_profile(self, user: AuthenticatedUser) -> dict[str, Any]:
        profile = self.load_profile(user)
        if not profile:
            raise HTTPException(status_code=403, detail=f"Profil utilisateur introuvable pour {user.email or user.id}")
        if profile.get("is_active") is not True:
            raise HTTPException(status_code=403, detail="Compte utilisateur inactif")
        return profile

    def _assert_workspace_subject_allowed(
        self,
        user: AuthenticatedUser,
        subject_email: str,
        *,
        account_label: str,
        action_label: str,
        forbidden_label: str,
    ) -> dict[str, Any]:
        profile = self.assert_active_profile(user)
        normalized_subject = self._normalize_email(subject_email)
        if not self._is_workspace_email(normalized_subject):
            raise HTTPException(status_code=400, detail=f"Compte {account_label} hors domaine {self.settings.google_workspace_domain}")

        role = str(profile.get("role") or "")
        if role in {"admin", "manager"}:
            return profile
        if role != "commercial":
            raise HTTPException(status_code=403, detail=f"Role non autorise pour {action_label}")

        identity_rows = self._rest_rows(
            "app_google_workspace_identity",
            {
                "select": "google_email,negociateur_email,link_status,is_active",
                "app_user_id": f"eq.{user.id}",
                "is_active": "eq.true",
                "limit": 1,
            },
            "Unable to read Google Workspace identity",
        )
        identity = identity_rows[0] if identity_rows else {}
        allowed_emails = {
            self._normalize_email(user.email),
            self._normalize_email(profile.get("email")),
            self._normalize_email(identity.get("google_email")),
            self._normalize_email(identity.get("negociateur_email")),
        }
        allowed_emails.discard("")
        if normalized_subject not in allowed_emails or identity.get("link_status") != "linked":
            raise HTTPException(status_code=403, detail=forbidden_label)
        return profile

    def assert_calendar_subject_allowed(self, user: AuthenticatedUser, subject_email: str) -> dict[str, Any]:
        return self._assert_workspace_subject_allowed(
            user,
            subject_email,
            account_label="Agenda",
            action_label="modifier Google Agenda",
            forbidden_label="Agenda Google non autorise pour cet utilisateur",
        )

    def assert_gmail_subject_allowed(self, user: AuthenticatedUser, subject_email: str) -> dict[str, Any]:
        return self._assert_workspace_subject_allowed(
            user,
            subject_email,
            account_label="Gmail",
            action_label="envoyer un email",
            forbidden_label="Gmail non autorise pour cet utilisateur",
        )

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
        email = self._normalize_email(payload["email"])
        if not self._is_workspace_email(email):
            raise HTTPException(status_code=400, detail=f"Creation utilisateur reservee aux comptes @{self.settings.google_workspace_domain}")
        display_name = payload.get("displayName") or " ".join(filter(None, [payload.get("firstName"), payload.get("lastName")])).strip() or payload["email"]
        auth_response = requests.post(
            f"{self.settings.supabase_url}/auth/v1/admin/users",
            headers=self._admin_headers(),
            json={
                "email": email,
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
            matched = next((item for item in users if self._normalize_email(item.get("email")) == email), None)
            user_id = matched.get("id") if matched else None
        if not user_id:
            raise HTTPException(status_code=500, detail="Supabase auth user id missing")

        profile_payload = {
            "id": user_id,
            "email": email,
            "role": payload["role"],
            "first_name": payload.get("firstName") or None,
            "last_name": payload.get("lastName") or None,
            "display_name": display_name,
            "is_active": payload.get("isActive", True),
        }
        profile = self._upsert_profile(profile_payload)
        if str(profile.get("id") or "") != str(user_id):
            raise HTTPException(status_code=500, detail="Profil utilisateur incoherent apres creation")
        identity = self._sync_google_workspace_identity(
            user_id=user_id,
            email=email,
            role=payload["role"],
            is_active=payload.get("isActive", True),
        )
        return {
            "ok": True,
            "userId": user_id,
            "email": email,
            "googleWorkspaceIdentity": {
                "linkStatus": identity.get("link_status") if identity else None,
                "hektorUserId": identity.get("hektor_user_id") if identity else None,
                "hektorNegociateurId": identity.get("hektor_negociateur_id") if identity else None,
            },
        }

    def update_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        email = self._normalize_email(payload["email"])
        is_active = payload.get("isActive", True)
        if is_active and not self._is_workspace_email(email):
            raise HTTPException(status_code=400, detail=f"Utilisateur actif hors domaine @{self.settings.google_workspace_domain} refuse")
        display_name = payload.get("displayName") or " ".join(filter(None, [payload.get("firstName"), payload.get("lastName")])).strip() or email
        response = requests.patch(
            f"{self.settings.supabase_url}/rest/v1/app_user_profile",
            headers=self._rest_headers(),
            params={"id": f"eq.{payload['id']}"},
            json={
                "email": email,
                "role": payload["role"],
                "first_name": payload.get("firstName") or None,
                "last_name": payload.get("lastName") or None,
                "display_name": display_name,
                "is_active": is_active,
            },
            timeout=30,
        )
        self._raise_for_response(response, "Unable to update user profile")
        identity = self._sync_google_workspace_identity(
            user_id=payload["id"],
            email=email,
            role=payload["role"],
            is_active=is_active,
        )
        return {
            "ok": True,
            "googleWorkspaceIdentity": {
                "linkStatus": identity.get("link_status") if identity else None,
                "hektorUserId": identity.get("hektor_user_id") if identity else None,
                "hektorNegociateurId": identity.get("hektor_negociateur_id") if identity else None,
            },
        }

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

    # ---- Suivi des runs d'agent IA (Phase 3, propose-only) --------------------
    # Best-effort : la tracabilite ne doit jamais faire echouer la generation.

    def insert_agent_run(self, row: dict[str, Any]) -> int | None:
        try:
            response = requests.post(
                f"{self.settings.supabase_url}/rest/v1/app_agent_run",
                headers={**self._rest_headers(), "Prefer": "return=representation"},
                json=[row],
                timeout=20,
            )
            if not response.ok:
                return None
            rows = response.json() or []
            return int(rows[0]["id"]) if rows and rows[0].get("id") is not None else None
        except Exception:
            return None

    def update_agent_run_decision(self, run_id: int, patch: dict[str, Any]) -> bool:
        try:
            response = requests.patch(
                f"{self.settings.supabase_url}/rest/v1/app_agent_run",
                headers=self._rest_headers(),
                params={"id": f"eq.{run_id}"},
                json=patch,
                timeout=20,
            )
            return response.ok
        except Exception:
            return False
