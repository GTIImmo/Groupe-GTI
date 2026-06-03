from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings


class GoogleCalendarEventLinkService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }

    def _raise_for_response(self, response: requests.Response, fallback: str) -> None:
        if response.ok:
            return
        try:
            payload = response.json()
            message = payload.get("msg") or payload.get("message") or payload.get("error_description") or payload.get("error")
        except Exception:
            message = response.text.strip() or fallback
        raise HTTPException(status_code=response.status_code if response.status_code >= 400 else 500, detail=str(message))

    def _rest_get(self, params: dict[str, str]) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_google_calendar_event_link",
            headers=self._headers(),
            params=params,
            timeout=30,
        )
        self._raise_for_response(response, "Unable to read Google calendar event link")
        return response.json() or []

    def _rest_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/app_google_calendar_event_link",
            headers={**self._headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "google_calendar_email,google_event_id"},
            json=[payload],
            timeout=30,
        )
        self._raise_for_response(response, "Unable to create Google calendar event link")
        rows = response.json() or []
        if not rows:
            raise HTTPException(status_code=500, detail="Lien evenement Google non cree")
        return rows[0]

    def _rest_patch(self, link_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.patch(
            f"{self.settings.supabase_url}/rest/v1/app_google_calendar_event_link",
            headers={**self._headers(), "Prefer": "return=representation"},
            params={"id": f"eq.{link_id}"},
            json=payload,
            timeout=30,
        )
        self._raise_for_response(response, "Unable to update Google calendar event link")
        rows = response.json() or []
        if not rows:
            raise HTTPException(status_code=404, detail="Lien evenement Google introuvable")
        return rows[0]

    def get_link(self, link_id: str) -> dict[str, Any]:
        rows = self._rest_get({"select": "*", "id": f"eq.{link_id}", "limit": "1"})
        if not rows:
            raise HTTPException(status_code=404, detail="Lien evenement Google introuvable")
        return rows[0]

    def list_links(
        self,
        *,
        app_dossier_id: int | None = None,
        hektor_annonce_id: int | None = None,
        hektor_contact_id: str | None = None,
        calendar_email: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        clean_limit = max(1, min(limit, 100))
        params = {
            "select": "*",
            "order": "starts_at.desc",
            "limit": str(clean_limit),
        }
        if app_dossier_id is not None:
            params["app_dossier_id"] = f"eq.{app_dossier_id}"
        if hektor_annonce_id is not None:
            params["hektor_annonce_id"] = f"eq.{hektor_annonce_id}"
        if calendar_email:
            params["google_calendar_email"] = f"ilike.{calendar_email}"
        if hektor_contact_id:
            direct_params = {**params, "hektor_contact_id": f"eq.{hektor_contact_id}"}
            attendee_params = {
                **params,
                "metadata_json->attendee_contacts": f"cs.{json.dumps([{'hektor_contact_id': hektor_contact_id}], separators=(',', ':'))}",
            }
            rows_by_id: dict[str, dict[str, Any]] = {}
            rows = self._rest_get(direct_params)
            try:
                rows.extend(self._rest_get(attendee_params))
            except HTTPException:
                pass
            for row in rows:
                row_id = str(row.get("id") or "")
                if row_id:
                    rows_by_id[row_id] = row
            return sorted(
                rows_by_id.values(),
                key=lambda row: str(row.get("starts_at") or ""),
                reverse=True,
            )[:clean_limit]
        return self._rest_get(params)

    def create_link(
        self,
        *,
        event_type: str,
        related_entity_type: str,
        related_entity_id: str | None,
        app_dossier_id: int | None,
        hektor_annonce_id: int | None,
        hektor_contact_id: str | None,
        calendar_email: str,
        google_event_id: str,
        google_html_link: str | None,
        summary: str,
        location: str | None,
        starts_at: str,
        ends_at: str,
        attendees: list[str],
        metadata_json: dict[str, Any] | None,
        created_by: str,
        created_by_email: str | None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return self._rest_post({
            "event_type": event_type,
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
            "app_dossier_id": app_dossier_id,
            "hektor_annonce_id": hektor_annonce_id,
            "hektor_contact_id": hektor_contact_id,
            "google_calendar_email": calendar_email,
            "google_event_id": google_event_id,
            "google_html_link": google_html_link,
            "summary": summary,
            "location": location,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "attendees_json": attendees,
            "status": "active",
            "metadata_json": metadata_json or {},
            "created_by": created_by,
            "created_by_email": created_by_email,
            "updated_by": created_by,
            "updated_by_email": created_by_email,
            "updated_at": now,
        })

    def update_link(
        self,
        *,
        link_id: str,
        updated_by: str,
        updated_by_email: str | None,
        summary: str | None = None,
        location: str | None = None,
        starts_at: str | None = None,
        ends_at: str | None = None,
        attendees: list[str] | None = None,
        google_html_link: str | None = None,
        metadata_patch: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "updated_by": updated_by,
            "updated_by_email": updated_by_email,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if summary is not None:
            payload["summary"] = summary
        if location is not None:
            payload["location"] = location
        if starts_at is not None:
            payload["starts_at"] = starts_at
        if ends_at is not None:
            payload["ends_at"] = ends_at
        if attendees is not None:
            payload["attendees_json"] = attendees
        if google_html_link is not None:
            payload["google_html_link"] = google_html_link
        if metadata_patch is not None:
            payload["metadata_json"] = metadata_patch
        return self._rest_patch(link_id, payload)

    def mark_deleted(self, *, link_id: str, updated_by: str, updated_by_email: str | None) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return self._rest_patch(link_id, {
            "status": "deleted",
            "cancelled_at": now,
            "updated_by": updated_by,
            "updated_by_email": updated_by_email,
            "updated_at": now,
        })
