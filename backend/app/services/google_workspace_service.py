from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any
from zoneinfo import ZoneInfo

import requests

from ..settings import Settings


GOOGLE_WORKSPACE_SCOPES: tuple[dict[str, str], ...] = (
    {
        "key": "gmail_send",
        "scope": "https://www.googleapis.com/auth/gmail.send",
        "phase": "notifications",
        "purpose": "Envoyer les emails metier depuis accueil@gti-immobilier.fr ou un compte autorise.",
    },
    {
        "key": "calendar_freebusy",
        "scope": "https://www.googleapis.com/auth/calendar.freebusy",
        "phase": "visites",
        "purpose": "Lire les disponibilites sans lire le detail complet des rendez-vous.",
    },
    {
        "key": "calendar_events",
        "scope": "https://www.googleapis.com/auth/calendar.events",
        "phase": "visites",
        "purpose": "Creer et mettre a jour les rendez-vous de visite avec invitations client.",
    },
    {
        "key": "contacts_readonly",
        "scope": "https://www.googleapis.com/auth/contacts.readonly",
        "phase": "crm",
        "purpose": "Lire les contacts Google pour enrichir les fiches CRM.",
    },
    {
        "key": "gmail_metadata",
        "scope": "https://www.googleapis.com/auth/gmail.metadata",
        "phase": "crm_email",
        "purpose": "Retrouver les fils Gmail lies a une fiche sans lire le corps des messages.",
    },
    {
        "key": "gmail_readonly",
        "scope": "https://www.googleapis.com/auth/gmail.readonly",
        "phase": "crm_email_ia",
        "purpose": "Lire les emails pour affichage CRM et futurs agents IA, a activer plus tard.",
    },
)

INITIAL_GOOGLE_WORKSPACE_SCOPES = (
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.freebusy",
    "https://www.googleapis.com/auth/calendar.events",
)

CALENDAR_FREEBUSY_SCOPE = "https://www.googleapis.com/auth/calendar.freebusy"
CALENDAR_EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
DEFAULT_CALENDAR_TIMEZONE = "Europe/Paris"


class GoogleWorkspaceService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def status(self) -> dict[str, Any]:
        service_account_file = self.settings.google_workspace_service_account_file
        service_account_file_exists = bool(service_account_file and service_account_file.exists())
        service_account_info = self._service_account_info() if service_account_file_exists else None
        configured_scopes = set(self.settings.google_workspace_scopes)
        missing_initial_scopes = [
            scope for scope in INITIAL_GOOGLE_WORKSPACE_SCOPES
            if scope not in configured_scopes
        ]
        service_account_client_id = service_account_info.get("clientId") if service_account_info else None
        client_id_matches_file = bool(
            self.settings.google_workspace_dwd_client_id
            and service_account_client_id
            and self.settings.google_workspace_dwd_client_id == str(service_account_client_id)
        )
        dwd_ready = bool(
            self.settings.google_workspace_auth_mode == "domain_wide_delegation"
            and self.settings.google_workspace_dwd_client_id
            and service_account_file_exists
            and service_account_info
            and client_id_matches_file
            and not missing_initial_scopes
        )

        return {
            "ok": True,
            "workspace": {
                "domain": self.settings.google_workspace_domain,
                "authMode": self.settings.google_workspace_auth_mode,
            },
            "domainWideDelegation": {
                "ready": dwd_ready,
                "clientIdConfigured": bool(self.settings.google_workspace_dwd_client_id),
                "clientIdMatchesServiceAccountFile": client_id_matches_file,
                "serviceAccountFileConfigured": bool(service_account_file),
                "serviceAccountFileExists": service_account_file_exists,
                "serviceAccount": service_account_info,
                "testSubjectEmailConfigured": bool(self.settings.google_workspace_subject_email),
                "testSubjectEmail": self.settings.google_workspace_subject_email,
                "configuredScopes": sorted(configured_scopes),
                "missingInitialScopes": missing_initial_scopes,
            },
            "notificationSender": {
                "gmailApiConfigured": bool(
                    self.settings.google_client_id
                    and self.settings.google_client_secret
                    and self.settings.google_refresh_token
                    and self.settings.google_sender_email
                ),
                "senderEmail": self.settings.google_sender_email,
                "targetSenderEmail": self.settings.google_workspace_subject_email or self.settings.google_sender_email,
            },
            "delegationModel": {
                "calendarSubject": "negociateur_google_email",
                "technicalSenderSubject": self.settings.google_workspace_subject_email or "accueil@gti-immobilier.fr",
                "note": "Domain Wide Delegation permettra d'agir au nom du collaborateur GTI concerne, sans consentement manuel par utilisateur.",
            },
            "recommendedScopes": list(GOOGLE_WORKSPACE_SCOPES),
            "nextSteps": self._next_steps(
                dwd_ready=dwd_ready,
                missing_initial_scopes=missing_initial_scopes,
                service_account_file_exists=service_account_file_exists,
                service_account_info=service_account_info,
                client_id_matches_file=client_id_matches_file,
            ),
        }

    def calendar_freebusy(
        self,
        *,
        subject_email: str,
        time_min: str | None = None,
        time_max: str | None = None,
        calendar_ids: list[str] | None = None,
        requested_by: str | None = None,
        requested_by_email: str | None = None,
    ) -> dict[str, Any]:
        clean_subject = self._validate_workspace_email(subject_email)
        start = self._parse_datetime(time_min) if time_min else datetime.now(timezone.utc)
        end = self._parse_datetime(time_max) if time_max else start + timedelta(hours=8)
        if end <= start:
            raise ValueError("time_max doit etre posterieur a time_min")

        access_token = self._delegated_access_token(
            subject_email=clean_subject,
            scopes=[CALENDAR_FREEBUSY_SCOPE],
        )
        ids = calendar_ids or [clean_subject]
        response = requests.post(
            "https://www.googleapis.com/calendar/v3/freeBusy",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "timeMin": start.isoformat().replace("+00:00", "Z"),
                "timeMax": end.isoformat().replace("+00:00", "Z"),
                "items": [{"id": item} for item in ids],
            },
            timeout=30,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text[:500]}
        if response.status_code >= 400:
            self._log_action(
                action_type="calendar.freebusy",
                subject_email=clean_subject,
                requested_by=requested_by,
                requested_by_email=requested_by_email,
                status="error",
                provider_status_code=response.status_code,
                error_message=self._safe_error_message(payload),
                metadata_json={
                    "time_min": start.isoformat(),
                    "time_max": end.isoformat(),
                    "calendar_count": len(ids),
                },
            )
            return {
                "ok": False,
                "statusCode": response.status_code,
                "subjectEmail": clean_subject,
                "error": payload,
            }
        self._log_action(
            action_type="calendar.freebusy",
            subject_email=clean_subject,
            requested_by=requested_by,
            requested_by_email=requested_by_email,
            status="done",
            metadata_json={
                "time_min": start.isoformat(),
                "time_max": end.isoformat(),
                "calendar_count": len(ids),
            },
        )
        return {
            "ok": True,
            "subjectEmail": clean_subject,
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "calendars": payload.get("calendars", {}),
            "groups": payload.get("groups", {}),
        }

    def send_gmail_message(
        self,
        *,
        subject_email: str,
        to: list[str],
        subject: str,
        body_text: str,
        body_html: str | None = None,
        from_name: str = "GTI Immobilier",
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        dry_run: bool = True,
        requested_by: str | None = None,
        requested_by_email: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
    ) -> dict[str, Any]:
        clean_subject_email = self._validate_workspace_email(subject_email)
        clean_to = self._validate_email_list(to, "Destinataire requis")
        clean_cc = self._validate_email_list(cc or [], "Copie invalide", allow_empty=True)
        clean_bcc = self._validate_email_list(bcc or [], "Copie cachee invalide", allow_empty=True)
        clean_subject = (subject or "").strip()
        clean_body_text = (body_text or "").strip()
        clean_body_html = (body_html or "").strip() or None
        clean_from_name = (from_name or "").strip() or "GTI Immobilier"
        clean_reply_to = self._validate_email(reply_to) if reply_to and reply_to.strip() else None
        if not clean_subject:
            raise ValueError("Objet email requis")
        if not clean_body_text:
            raise ValueError("Corps texte email requis")

        message = EmailMessage()
        message["From"] = formataddr((clean_from_name, clean_subject_email))
        message["To"] = ", ".join(clean_to)
        if clean_cc:
            message["Cc"] = ", ".join(clean_cc)
        message["Subject"] = clean_subject
        if clean_reply_to:
            message["Reply-To"] = clean_reply_to
        message.set_content(clean_body_text)
        if clean_body_html:
            message.add_alternative(clean_body_html, subtype="html")

        metadata = {
            "to_count": len(clean_to),
            "cc_count": len(clean_cc),
            "bcc_count": len(clean_bcc),
            "has_reply_to": bool(clean_reply_to),
            "has_html": bool(clean_body_html),
            "subject_length": len(clean_subject),
            "body_text_length": len(clean_body_text),
        }

        if dry_run:
            self._log_action(
                action_type="gmail.send",
                subject_email=clean_subject_email,
                target_email=clean_to[0],
                requested_by=requested_by,
                requested_by_email=requested_by_email,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                dry_run=True,
                status="done",
                metadata_json=metadata,
            )
            return {
                "ok": True,
                "dryRun": True,
                "subjectEmail": clean_subject_email,
                "toCount": len(clean_to),
                "ccCount": len(clean_cc),
                "bccCount": len(clean_bcc),
                "hasHtml": bool(clean_body_html),
            }

        if clean_bcc:
            message["Bcc"] = ", ".join(clean_bcc)

        access_token = self._delegated_access_token(
            subject_email=clean_subject_email,
            scopes=[GMAIL_SEND_SCOPE],
        )
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8").rstrip("=")
        response = requests.post(
            f"https://gmail.googleapis.com/gmail/v1/users/{clean_subject_email}/messages/send",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw_message},
            timeout=30,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text[:500]}
        if response.status_code >= 400:
            self._log_action(
                action_type="gmail.send",
                subject_email=clean_subject_email,
                target_email=clean_to[0],
                requested_by=requested_by,
                requested_by_email=requested_by_email,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                dry_run=False,
                status="error",
                provider_status_code=response.status_code,
                error_message=self._safe_error_message(payload),
                metadata_json=metadata,
            )
            return {
                "ok": False,
                "statusCode": response.status_code,
                "subjectEmail": clean_subject_email,
                "error": payload,
            }

        metadata["google_message_id"] = payload.get("id")
        metadata["google_thread_id"] = payload.get("threadId")
        self._log_action(
            action_type="gmail.send",
            subject_email=clean_subject_email,
            target_email=clean_to[0],
            requested_by=requested_by,
            requested_by_email=requested_by_email,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            dry_run=False,
            status="done",
            metadata_json=metadata,
        )
        return {
            "ok": True,
            "dryRun": False,
            "subjectEmail": clean_subject_email,
            "messageId": payload.get("id"),
            "threadId": payload.get("threadId"),
        }

    def create_calendar_event(
        self,
        *,
        subject_email: str,
        summary: str,
        start_at: str,
        end_at: str,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        send_updates: str = "none",
        dry_run: bool = True,
        requested_by: str | None = None,
        requested_by_email: str | None = None,
    ) -> dict[str, Any]:
        clean_subject = self._validate_workspace_email(subject_email)
        clean_summary = (summary or "").strip()
        if not clean_summary:
            raise ValueError("Titre du rendez-vous requis")
        start = self._parse_datetime(start_at, default_timezone=ZoneInfo(DEFAULT_CALENDAR_TIMEZONE))
        end = self._parse_datetime(end_at, default_timezone=ZoneInfo(DEFAULT_CALENDAR_TIMEZONE))
        if end <= start:
            raise ValueError("end_at doit etre posterieur a start_at")
        clean_send_updates = send_updates if send_updates in {"all", "externalOnly", "none"} else "none"
        clean_attendees = [
            {"email": self._validate_email(item)}
            for item in (attendees or [])
            if (item or "").strip()
        ]
        event_body: dict[str, Any] = {
            "summary": clean_summary,
            "start": {
                "dateTime": start.isoformat(),
                "timeZone": DEFAULT_CALENDAR_TIMEZONE,
            },
            "end": {
                "dateTime": end.isoformat(),
                "timeZone": DEFAULT_CALENDAR_TIMEZONE,
            },
            "extendedProperties": {
                "private": {
                    "source": "gti-hektor",
                    "created_by": "gti-backend",
                },
            },
        }
        if description:
            event_body["description"] = description.strip()
        if location:
            event_body["location"] = location.strip()
        if clean_attendees:
            event_body["attendees"] = clean_attendees

        if dry_run:
            self._log_action(
                action_type="calendar.event.create",
                subject_email=clean_subject,
                target_email=clean_attendees[0]["email"] if clean_attendees else None,
                requested_by=requested_by,
                requested_by_email=requested_by_email,
                dry_run=True,
                status="done",
                metadata_json={
                    "send_updates": clean_send_updates,
                    "attendee_count": len(clean_attendees),
                    "has_location": bool(location),
                    "has_description": bool(description),
                    "start_at": start.isoformat(),
                    "end_at": end.isoformat(),
                },
            )
            return {
                "ok": True,
                "dryRun": True,
                "subjectEmail": clean_subject,
                "sendUpdates": clean_send_updates,
                "event": event_body,
            }

        access_token = self._delegated_access_token(
            subject_email=clean_subject,
            scopes=[CALENDAR_EVENTS_SCOPE],
        )
        response = requests.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            params={"sendUpdates": clean_send_updates},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=event_body,
            timeout=30,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text[:500]}
        if response.status_code >= 400:
            self._log_action(
                action_type="calendar.event.create",
                subject_email=clean_subject,
                target_email=clean_attendees[0]["email"] if clean_attendees else None,
                requested_by=requested_by,
                requested_by_email=requested_by_email,
                dry_run=False,
                status="error",
                provider_status_code=response.status_code,
                error_message=self._safe_error_message(payload),
                metadata_json={
                    "send_updates": clean_send_updates,
                    "attendee_count": len(clean_attendees),
                    "has_location": bool(location),
                    "has_description": bool(description),
                    "start_at": start.isoformat(),
                    "end_at": end.isoformat(),
                },
            )
            return {
                "ok": False,
                "statusCode": response.status_code,
                "subjectEmail": clean_subject,
                "error": payload,
            }
        self._log_action(
            action_type="calendar.event.create",
            subject_email=clean_subject,
            target_email=clean_attendees[0]["email"] if clean_attendees else None,
            requested_by=requested_by,
            requested_by_email=requested_by_email,
            dry_run=False,
            status="done",
            metadata_json={
                "send_updates": clean_send_updates,
                "attendee_count": len(clean_attendees),
                "has_location": bool(location),
                "has_description": bool(description),
                "start_at": start.isoformat(),
                "end_at": end.isoformat(),
                "google_event_id": payload.get("id"),
            },
        )
        return {
            "ok": True,
            "dryRun": False,
            "subjectEmail": clean_subject,
            "sendUpdates": clean_send_updates,
            "eventId": payload.get("id"),
            "htmlLink": payload.get("htmlLink"),
            "event": payload,
        }

    def update_calendar_event(
        self,
        *,
        subject_email: str,
        event_id: str,
        summary: str | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        send_updates: str = "none",
        dry_run: bool = True,
        requested_by: str | None = None,
        requested_by_email: str | None = None,
    ) -> dict[str, Any]:
        clean_subject = self._validate_workspace_email(subject_email)
        clean_event_id = (event_id or "").strip()
        if not clean_event_id:
            raise ValueError("Identifiant evenement Google requis")
        clean_send_updates = send_updates if send_updates in {"all", "externalOnly", "none"} else "none"

        event_patch: dict[str, Any] = {}
        changed_fields: list[str] = []

        if summary is not None:
            clean_summary = summary.strip()
            if not clean_summary:
                raise ValueError("Titre du rendez-vous requis")
            event_patch["summary"] = clean_summary
            changed_fields.append("summary")

        if (start_at is None) != (end_at is None):
            raise ValueError("start_at et end_at doivent etre fournis ensemble")
        if start_at and end_at:
            start = self._parse_datetime(start_at, default_timezone=ZoneInfo(DEFAULT_CALENDAR_TIMEZONE))
            end = self._parse_datetime(end_at, default_timezone=ZoneInfo(DEFAULT_CALENDAR_TIMEZONE))
            if end <= start:
                raise ValueError("end_at doit etre posterieur a start_at")
            event_patch["start"] = {
                "dateTime": start.isoformat(),
                "timeZone": DEFAULT_CALENDAR_TIMEZONE,
            }
            event_patch["end"] = {
                "dateTime": end.isoformat(),
                "timeZone": DEFAULT_CALENDAR_TIMEZONE,
            }
            changed_fields.extend(["start", "end"])
        else:
            start = None
            end = None

        if description is not None:
            event_patch["description"] = description.strip()
            changed_fields.append("description")
        if location is not None:
            event_patch["location"] = location.strip()
            changed_fields.append("location")

        clean_attendees: list[dict[str, str]] | None = None
        if attendees is not None:
            clean_attendees = [
                {"email": self._validate_email(item)}
                for item in attendees
                if (item or "").strip()
            ]
            event_patch["attendees"] = clean_attendees
            changed_fields.append("attendees")

        if not event_patch:
            raise ValueError("Aucune modification fournie")

        metadata = {
            "send_updates": clean_send_updates,
            "changed_fields": changed_fields,
            "attendee_count": len(clean_attendees) if clean_attendees is not None else None,
            "has_location": location is not None and bool(location.strip()),
            "has_description": description is not None and bool(description.strip()),
            "start_at": start.isoformat() if start else None,
            "end_at": end.isoformat() if end else None,
            "google_event_id": clean_event_id,
        }

        if dry_run:
            self._log_action(
                action_type="calendar.event.update",
                subject_email=clean_subject,
                target_email=clean_attendees[0]["email"] if clean_attendees else None,
                requested_by=requested_by,
                requested_by_email=requested_by_email,
                dry_run=True,
                status="done",
                metadata_json=metadata,
            )
            return {
                "ok": True,
                "dryRun": True,
                "subjectEmail": clean_subject,
                "eventId": clean_event_id,
                "sendUpdates": clean_send_updates,
                "eventPatch": event_patch,
            }

        access_token = self._delegated_access_token(
            subject_email=clean_subject,
            scopes=[CALENDAR_EVENTS_SCOPE],
        )
        response = requests.patch(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{clean_event_id}",
            params={"sendUpdates": clean_send_updates},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=event_patch,
            timeout=30,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text[:500]}
        if response.status_code >= 400:
            self._log_action(
                action_type="calendar.event.update",
                subject_email=clean_subject,
                target_email=clean_attendees[0]["email"] if clean_attendees else None,
                requested_by=requested_by,
                requested_by_email=requested_by_email,
                dry_run=False,
                status="error",
                provider_status_code=response.status_code,
                error_message=self._safe_error_message(payload),
                metadata_json=metadata,
            )
            return {
                "ok": False,
                "statusCode": response.status_code,
                "subjectEmail": clean_subject,
                "eventId": clean_event_id,
                "error": payload,
            }

        self._log_action(
            action_type="calendar.event.update",
            subject_email=clean_subject,
            target_email=clean_attendees[0]["email"] if clean_attendees else None,
            requested_by=requested_by,
            requested_by_email=requested_by_email,
            dry_run=False,
            status="done",
            metadata_json=metadata,
        )
        return {
            "ok": True,
            "dryRun": False,
            "subjectEmail": clean_subject,
            "eventId": payload.get("id"),
            "htmlLink": payload.get("htmlLink"),
            "event": payload,
        }

    def delete_calendar_event(
        self,
        *,
        subject_email: str,
        event_id: str,
        send_updates: str = "none",
        requested_by: str | None = None,
        requested_by_email: str | None = None,
    ) -> dict[str, Any]:
        clean_subject = self._validate_workspace_email(subject_email)
        clean_event_id = (event_id or "").strip()
        if not clean_event_id:
            raise ValueError("Identifiant evenement Google requis")
        clean_send_updates = send_updates if send_updates in {"all", "externalOnly", "none"} else "none"

        access_token = self._delegated_access_token(
            subject_email=clean_subject,
            scopes=[CALENDAR_EVENTS_SCOPE],
        )
        response = requests.delete(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{clean_event_id}",
            params={"sendUpdates": clean_send_updates},
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
        if response.status_code >= 400:
            try:
                payload: Any = response.json()
            except ValueError:
                payload = {"raw": response.text[:500]}
            self._log_action(
                action_type="calendar.event.delete",
                subject_email=clean_subject,
                requested_by=requested_by,
                requested_by_email=requested_by_email,
                status="error",
                provider_status_code=response.status_code,
                error_message=self._safe_error_message(payload),
                metadata_json={
                    "send_updates": clean_send_updates,
                    "google_event_id": clean_event_id,
                },
            )
            return {
                "ok": False,
                "statusCode": response.status_code,
                "subjectEmail": clean_subject,
                "eventId": clean_event_id,
                "error": payload,
            }

        self._log_action(
            action_type="calendar.event.delete",
            subject_email=clean_subject,
            requested_by=requested_by,
            requested_by_email=requested_by_email,
            status="done",
            metadata_json={
                "send_updates": clean_send_updates,
                "google_event_id": clean_event_id,
            },
        )
        return {
            "ok": True,
            "subjectEmail": clean_subject,
            "eventId": clean_event_id,
            "sendUpdates": clean_send_updates,
        }

    def _service_account_info(self) -> dict[str, Any] | None:
        path = self.settings.google_workspace_service_account_file
        if not path:
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return {
            "projectId": payload.get("project_id"),
            "clientEmail": payload.get("client_email"),
            "clientId": payload.get("client_id"),
            "privateKeyIdConfigured": bool(payload.get("private_key_id")),
            "privateKeyConfigured": bool(payload.get("private_key")),
        }

    def _log_action(
        self,
        *,
        action_type: str,
        subject_email: str,
        status: str,
        requested_by: str | None = None,
        requested_by_email: str | None = None,
        target_email: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        dry_run: bool = False,
        provider_status_code: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        try:
            response = requests.post(
                f"{self.settings.supabase_url}/rest/v1/app_google_workspace_action_log",
                headers={
                    "apikey": self.settings.supabase_service_role_key,
                    "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
                    "Content-Type": "application/json",
                },
                json=[{
                    "requested_by": requested_by,
                    "requested_by_email": requested_by_email,
                    "action_type": action_type,
                    "subject_email": subject_email,
                    "target_email": target_email,
                    "related_entity_type": related_entity_type,
                    "related_entity_id": related_entity_id,
                    "dry_run": dry_run,
                    "status": status,
                    "provider_status_code": provider_status_code,
                    "error_code": error_code,
                    "error_message": error_message[:500] if error_message else None,
                    "metadata_json": metadata_json or {},
                }],
                timeout=20,
            )
            response.raise_for_status()
        except Exception:
            return

    def _safe_error_message(self, payload: Any) -> str | None:
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                return str(error.get("message") or error.get("status") or "")[:500] or None
            if error:
                return str(error)[:500]
            if payload.get("raw"):
                return str(payload.get("raw"))[:500]
        return str(payload)[:500] if payload else None

    def _delegated_access_token(self, *, subject_email: str, scopes: list[str]) -> str:
        if not self.settings.google_workspace_service_account_file:
            raise RuntimeError("Fichier compte de service Google non configure")
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account
        except ImportError as exc:
            raise RuntimeError("Dependance google-auth manquante dans l'environnement backend") from exc

        credentials = service_account.Credentials.from_service_account_file(
            str(self.settings.google_workspace_service_account_file),
            scopes=scopes,
        ).with_subject(subject_email)
        credentials.refresh(Request())
        if not credentials.token:
            raise RuntimeError("Token Google Workspace non obtenu")
        return credentials.token

    def _validate_workspace_email(self, email: str) -> str:
        clean = (email or "").strip().lower()
        if not clean or "@" not in clean:
            raise ValueError("Email Google Workspace requis")
        if clean.split("@", 1)[1] != self.settings.google_workspace_domain:
            raise ValueError("Email hors domaine Google Workspace GTI")
        return clean

    def _validate_email(self, email: str) -> str:
        clean = (email or "").strip().lower()
        if not clean or "@" not in clean:
            raise ValueError("Email invite invalide")
        return clean

    def _validate_email_list(self, emails: list[str], error_message: str, *, allow_empty: bool = False) -> list[str]:
        cleaned: list[str] = []
        for item in emails:
            if not (item or "").strip():
                continue
            clean = self._validate_email(item)
            if clean not in cleaned:
                cleaned.append(clean)
        if not cleaned and not allow_empty:
            raise ValueError(error_message)
        return cleaned

    def _parse_datetime(self, value: str, *, default_timezone: timezone | ZoneInfo = timezone.utc) -> datetime:
        clean = (value or "").strip()
        if clean.endswith("Z"):
            clean = clean[:-1] + "+00:00"
        parsed = datetime.fromisoformat(clean)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=default_timezone)
        return parsed.astimezone(timezone.utc)

    def _next_steps(
        self,
        *,
        dwd_ready: bool,
        missing_initial_scopes: list[str],
        service_account_file_exists: bool,
        service_account_info: dict[str, Any] | None,
        client_id_matches_file: bool,
    ) -> list[str]:
        steps: list[str] = []
        if dwd_ready:
            return ["Configuration Google Workspace prete pour brancher les premiers appels backend."]
        if self.settings.google_workspace_auth_mode != "domain_wide_delegation":
            steps.append("Confirmer le mode d'autorisation Google Workspace a utiliser.")
        if not self.settings.google_workspace_dwd_client_id:
            steps.append("Renseigner le Client ID Domain Wide Delegation du compte de service.")
        if not self.settings.google_workspace_service_account_file:
            steps.append("Renseigner le chemin du fichier JSON du compte de service Google.")
        elif not service_account_file_exists:
            steps.append("Verifier que le fichier JSON du compte de service existe au chemin configure.")
        elif not service_account_info:
            steps.append("Verifier que le fichier JSON du compte de service est lisible et valide.")
        elif self.settings.google_workspace_dwd_client_id and not client_id_matches_file:
            steps.append("Verifier que GOOGLE_WORKSPACE_DWD_CLIENT_ID correspond au client_id du fichier JSON.")
        if missing_initial_scopes:
            steps.append("Autoriser les scopes initiaux Gmail send et Agenda dans la console admin Google.")
        if not self.settings.google_workspace_subject_email:
            steps.append("Choisir un compte sujet de test, idealement accueil@gti-immobilier.fr.")
        return steps
