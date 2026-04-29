from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
from fastapi import HTTPException

from ..models import AppointmentRequestCreatePayload
from ..services.hektor_bridge import HektorBridgeService
from ..services.notification_service import NotificationService
from ..settings import Settings


PARIS_TZ = ZoneInfo("Europe/Paris")
FRENCH_WEEKDAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
FRENCH_MONTHS = [
    "",
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
]


class AppointmentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.notification_service = NotificationService(settings)
        self.hektor_bridge = HektorBridgeService(settings)

    def _rest_headers(self) -> dict[str, str]:
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
            message = payload.get("message") or payload.get("error_description") or payload.get("error") or payload.get("msg")
        except Exception:
            message = response.text.strip() or fallback
        raise HTTPException(status_code=response.status_code if response.status_code >= 400 else 500, detail=str(message))

    def _rest_get(self, path: str, *, params: dict[str, str]) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.settings.supabase_url}/rest/v1/{path}",
            headers=self._rest_headers(),
            params=params,
            timeout=30,
        )
        self._raise_for_response(response, f"Unable to read {path}")
        return response.json() or []

    def _rest_post(self, path: str, *, payload: list[dict[str, Any]] | dict[str, Any], on_conflict: str | None = None) -> list[dict[str, Any]]:
        params = {"on_conflict": on_conflict} if on_conflict else None
        response = requests.post(
            f"{self.settings.supabase_url}/rest/v1/{path}",
            headers={**self._rest_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params=params,
            json=payload,
            timeout=30,
        )
        self._raise_for_response(response, f"Unable to write {path}")
        return response.json() or []

    def _rest_patch(self, path: str, *, payload: dict[str, Any], params: dict[str, str]) -> list[dict[str, Any]]:
        response = requests.patch(
            f"{self.settings.supabase_url}/rest/v1/{path}",
            headers={**self._rest_headers(), "Prefer": "return=representation"},
            params=params,
            json=payload,
            timeout=30,
        )
        self._raise_for_response(response, f"Unable to update {path}")
        return response.json() or []

    def _read_dossier_by_annonce(self, annonce_id: int) -> dict[str, Any]:
        rows = self._rest_get(
            "app_dossier_current",
            params={
                "select": "app_dossier_id,hektor_annonce_id,titre_bien,numero_dossier,numero_mandat,ville,prix,type_bien,commercial_id,commercial_nom,negociateur_email,agence_nom,photo_url_listing,adresse_detail,adresse_privee_listing",
                "hektor_annonce_id": f"eq.{annonce_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Annonce {annonce_id} introuvable dans app_dossier_current")
        return rows[0]

    def _read_link_by_token(self, token: str) -> dict[str, Any] | None:
        rows = self._rest_get(
            "app_appointment_public_link",
            params={
                "select": "*",
                "token": f"eq.{token}",
                "is_active": "eq.true",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def _read_link_by_annonce(self, annonce_id: int) -> dict[str, Any] | None:
        rows = self._rest_get(
            "app_appointment_public_link",
            params={
                "select": "*",
                "hektor_annonce_id": f"eq.{annonce_id}",
                "is_active": "eq.true",
                "order": "created_at.desc",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def _ensure_link_for_annonce(self, annonce_id: int) -> dict[str, Any]:
        existing = self._read_link_by_annonce(annonce_id)
        if existing:
            return existing
        dossier = self._read_dossier_by_annonce(annonce_id)
        payload = {
            "link_type": "annonce",
            "token": secrets.token_urlsafe(12),
            "hektor_annonce_id": annonce_id,
            "app_dossier_id": dossier.get("app_dossier_id"),
            "commercial_id": dossier.get("commercial_id"),
            "commercial_nom": dossier.get("commercial_nom"),
            "negociateur_email": dossier.get("negociateur_email"),
            "agence_nom": dossier.get("agence_nom"),
            "ville": dossier.get("ville"),
            "type_bien": dossier.get("type_bien"),
            "prix": dossier.get("prix"),
            "photo_url": dossier.get("photo_url_listing"),
            "last_generated_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        rows = self._rest_post("app_appointment_public_link", payload=[payload])
        if not rows:
            raise HTTPException(status_code=500, detail="Lien public RDV non cree")
        return rows[0]

    def _resolve_link(self, ref: str) -> tuple[dict[str, Any], dict[str, Any]]:
        token = ref.strip()
        if token and not token.isdigit():
            link = self._read_link_by_token(token)
            if not link:
                raise HTTPException(status_code=404, detail="Lien RDV introuvable")
            dossier = self._read_dossier_by_annonce(int(link["hektor_annonce_id"]))
            return link, dossier
        try:
            annonce_id = int(token)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Reference annonce invalide") from exc
        link = self._ensure_link_for_annonce(annonce_id)
        dossier = self._read_dossier_by_annonce(annonce_id)
        return link, dossier

    def _read_slot_rule(self, link: dict[str, Any]) -> dict[str, Any]:
        commercial_id = str(link.get("commercial_id") or "").strip()
        if commercial_id:
            rows = self._rest_get(
                "app_appointment_slot_rule",
                params={
                    "select": "*",
                    "scope_type": "eq.negociateur",
                    "scope_key": f"eq.{commercial_id}",
                    "is_active": "eq.true",
                    "limit": "1",
                },
            )
            if rows:
                return rows[0]
        rows = self._rest_get(
            "app_appointment_slot_rule",
            params={
                "select": "*",
                "scope_type": "eq.global",
                "is_active": "eq.true",
                "limit": "1",
            },
        )
        if rows:
            return rows[0]
        return {
            "min_delay_hours": 36,
            "days_ahead": 21,
            "slot_minutes": 30,
            "day_start_hour": 9,
            "day_end_hour": 18,
            "lunch_break_start": "12:30",
            "lunch_break_end": "14:00",
            "fake_busy_ratio": 0.35,
            "allow_saturday": True,
            "allow_sunday": False,
        }

    def _compose_public_url(self, token: str) -> str | None:
        base = (self.settings.app_base_url or "").rstrip("/")
        if not base:
            return None
        return f"{base}/rdv/annonce/{token}"

    def _context_payload(self, link: dict[str, Any], dossier: dict[str, Any]) -> dict[str, Any]:
        return {
            "token": link.get("token"),
            "publicUrl": self._compose_public_url(str(link.get("token") or "")),
            "hektorAnnonceId": dossier.get("hektor_annonce_id"),
            "appDossierId": dossier.get("app_dossier_id"),
            "title": dossier.get("titre_bien"),
            "ville": link.get("ville") or dossier.get("ville"),
            "typeBien": link.get("type_bien") or dossier.get("type_bien"),
            "price": link.get("prix") if link.get("prix") is not None else dossier.get("prix"),
            "photoUrl": link.get("photo_url") or dossier.get("photo_url_listing"),
            "commercialId": link.get("commercial_id") or dossier.get("commercial_id"),
            "commercialName": link.get("commercial_nom") or dossier.get("commercial_nom"),
            "negociateurEmail": link.get("negociateur_email") or dossier.get("negociateur_email"),
            "agenceNom": link.get("agence_nom") or dossier.get("agence_nom"),
            "negociateurPhone": link.get("negociateur_phone"),
            "negociateurMobile": link.get("negociateur_mobile"),
            "agencePhone": link.get("agence_phone"),
            "agenceEmail": link.get("agence_email"),
        }

    def _load_contact_details(self, dossier: dict[str, Any]) -> dict[str, Any]:
        details = {
            "negociateurPhone": None,
            "negociateurMobile": None,
            "agencePhone": None,
            "agenceEmail": None,
        }
        if not (
            self.settings.hektor_api_base_url
            and self.settings.hektor_client_id
            and self.settings.hektor_client_secret
        ):
            return details

        commercial_id = str(dossier.get("commercial_id") or "").strip()
        agence_nom = str(dossier.get("agence_nom") or "").strip()

        try:
            if commercial_id:
                nego = self._fetch_hektor_negociateur(commercial_id)
                details["negociateurPhone"] = nego.get("telephone") or None
                details["negociateurMobile"] = nego.get("portable") or None
                agence_nom = str(nego.get("agence_nom") or agence_nom).strip()
        except Exception:
            pass

        try:
            if agence_nom:
                agence = self._fetch_hektor_agence(agence_nom)
                details["agencePhone"] = agence.get("tel") or None
                details["agenceEmail"] = agence.get("mail") or None
        except Exception:
            pass

        return details

    def _maybe_enrich_link_contacts(self, link: dict[str, Any], dossier: dict[str, Any]) -> dict[str, Any]:
        if any(
            str(link.get(key) or "").strip()
            for key in ("negociateur_phone", "negociateur_mobile", "agence_phone", "agence_email")
        ):
            return link

        details = self._load_contact_details(dossier)
        payload = {
            "negociateur_phone": details.get("negociateurPhone"),
            "negociateur_mobile": details.get("negociateurMobile"),
            "agence_phone": details.get("agencePhone"),
            "agence_email": details.get("agenceEmail"),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        rows = self._rest_patch(
            "app_appointment_public_link",
            payload=payload,
            params={"id": f"eq.{link['id']}"},
        )
        if rows:
            return rows[0]
        link.update(payload)
        return link

    def _fetch_hektor_negociateur(self, negotiateur_id: str) -> dict[str, Any]:
        parsed, _ = self.hektor_bridge._call_hektor(
            f"/Api/Negociateur/NegoById/?id={requests.utils.quote(negotiateur_id, safe='')}&version={self.settings.hektor_api_version}",
            method="GET",
        )
        if not isinstance(parsed, dict):
            return {}
        data = parsed.get("data") if isinstance(parsed.get("data"), dict) else parsed
        if not isinstance(data, dict):
            return {}
        return {
            "telephone": self._coalesce_text(data.get("telephone"), data.get("tel")),
            "portable": self._coalesce_text(data.get("portable"), data.get("mobile")),
            "agence_nom": self._coalesce_text(data.get("agence"), data.get("agence_nom")),
        }

    def _fetch_hektor_agence(self, agence_nom: str) -> dict[str, Any]:
        parsed, _ = self.hektor_bridge._call_hektor(
            f"/Api/Agence/ListAgences/?version={self.settings.hektor_api_version}",
            method="GET",
        )
        rows = []
        if isinstance(parsed, dict):
            if isinstance(parsed.get("data"), list):
                rows = parsed.get("data") or []
            elif isinstance(parsed.get("liste"), list):
                rows = parsed.get("liste") or []
        elif isinstance(parsed, list):
            rows = parsed

        target = self._normalize_text(agence_nom)
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_name = self._coalesce_text(row.get("nom"), row.get("agence"), row.get("name"))
            if self._normalize_text(row_name) == target:
                coord = row.get("coordonnees") if isinstance(row.get("coordonnees"), dict) else {}
                return {
                    "tel": self._coalesce_text(coord.get("tel"), row.get("tel")),
                    "mail": self._coalesce_text(coord.get("mail"), row.get("mail"), row.get("email")),
                }
        return {}

    def _normalize_text(self, value: Any) -> str:
        return " ".join(str(value or "").strip().lower().split())

    def _coalesce_text(self, *values: Any) -> str | None:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return None

    def get_public_annonce_context(self, ref: str) -> dict[str, Any]:
        link, dossier = self._resolve_link(ref)
        return self._context_payload(link, dossier)

    def get_public_annonce_bootstrap(self, ref: str) -> dict[str, Any]:
        link, dossier = self._resolve_link(ref)
        rule = self._read_slot_rule(link)
        slots = self._generate_slots(link, rule)
        return {
            "context": self._context_payload(link, dossier),
            "rule": {
                "minDelayHours": int(rule.get("min_delay_hours") or 36),
                "daysAhead": int(rule.get("days_ahead") or 21),
                "slotMinutes": int(rule.get("slot_minutes") or 30),
            },
            "slots": slots,
        }

    def get_public_annonce_slots(self, ref: str) -> dict[str, Any]:
        link, _ = self._resolve_link(ref)
        rule = self._read_slot_rule(link)
        slots = self._generate_slots(link, rule)
        return {
            "rule": {
                "minDelayHours": int(rule.get("min_delay_hours") or 36),
                "daysAhead": int(rule.get("days_ahead") or 21),
                "slotMinutes": int(rule.get("slot_minutes") or 30),
            },
            "slots": slots,
        }

    def get_internal_annonce_summary(self, annonce_id: int) -> dict[str, Any]:
        link = self._ensure_link_for_annonce(annonce_id)
        dossier = self._read_dossier_by_annonce(annonce_id)
        link = self._maybe_enrich_link_contacts(link, dossier)
        requests = self._read_requests_for_annonce(annonce_id)
        events = self._read_events_for_request_ids([str(item.get("id") or "").strip() for item in requests])
        return {
            "ok": True,
            "context": self._context_payload(link, dossier),
            "requests": requests,
            "events": events,
        }

    def _generate_slots(self, link: dict[str, Any], rule: dict[str, Any]) -> list[dict[str, Any]]:
        now = datetime.now(PARIS_TZ)
        min_delay = int(rule.get("min_delay_hours") or 36)
        days_ahead = int(rule.get("days_ahead") or 21)
        slot_minutes = int(rule.get("slot_minutes") or 30)
        day_start_hour = int(rule.get("day_start_hour") or 9)
        day_end_hour = int(rule.get("day_end_hour") or 18)
        busy_ratio = float(rule.get("fake_busy_ratio") or 0.35)
        lunch_start = self._parse_hhmm(str(rule.get("lunch_break_start") or "12:30"))
        lunch_end = self._parse_hhmm(str(rule.get("lunch_break_end") or "14:00"))
        allow_saturday = bool(rule.get("allow_saturday", True))
        allow_sunday = bool(rule.get("allow_sunday", False))
        earliest = now + timedelta(hours=min_delay)
        seed = str(link.get("token") or link.get("hektor_annonce_id") or "")
        slots: list[dict[str, Any]] = []

        for offset in range(days_ahead + 1):
            day = (earliest + timedelta(days=offset)).date()
            weekday = day.weekday()
            if weekday == 5 and not allow_saturday:
                continue
            if weekday == 6 and not allow_sunday:
                continue
            if self._is_french_public_holiday(day):
                continue
            cursor = datetime.combine(day, time(hour=day_start_hour), tzinfo=PARIS_TZ)
            end_of_day = datetime.combine(day, time(hour=day_end_hour), tzinfo=PARIS_TZ)
            while cursor < end_of_day:
                next_cursor = cursor + timedelta(minutes=slot_minutes)
                if cursor < earliest:
                    cursor = next_cursor
                    continue
                if lunch_start and lunch_end:
                    lunch_start_dt = datetime.combine(day, lunch_start, tzinfo=PARIS_TZ)
                    lunch_end_dt = datetime.combine(day, lunch_end, tzinfo=PARIS_TZ)
                    if cursor < lunch_end_dt and next_cursor > lunch_start_dt:
                        cursor = next_cursor
                        continue
                slots.append(
                    {
                        "startAt": cursor.astimezone(UTC).isoformat(),
                        "endAt": next_cursor.astimezone(UTC).isoformat(),
                        "dateKey": day.isoformat(),
                        "dayNumber": day.day,
                        "monthLabel": FRENCH_MONTHS[day.month],
                        "weekdayLabel": FRENCH_WEEKDAYS[day.weekday()],
                        "displayDate": cursor.strftime("%d/%m/%Y"),
                        "displayDateLabel": self._format_public_date(day),
                        "displayTime": cursor.strftime("%H:%M"),
                        "endDisplayTime": f"jusqu'a {next_cursor.strftime('%H:%M')}",
                        "periodLabel": self._period_label(cursor),
                        "available": not self._is_fake_busy(seed, cursor, busy_ratio),
                    }
                )
                cursor = next_cursor
        return slots[:80]

    def _period_label(self, value: datetime) -> str:
        return "Matin" if value.hour < 12 else "Apres-midi"

    def _format_public_date(self, value: date) -> str:
        weekday = FRENCH_WEEKDAYS[value.weekday()]
        month = FRENCH_MONTHS[value.month]
        return f"{weekday} {value.day} {month}"

    def _is_french_public_holiday(self, value: date) -> bool:
        easter = self._easter_sunday(value.year)
        fixed_days = {
            date(value.year, 1, 1),
            date(value.year, 5, 1),
            date(value.year, 5, 8),
            date(value.year, 7, 14),
            date(value.year, 8, 15),
            date(value.year, 11, 1),
            date(value.year, 11, 11),
            date(value.year, 12, 25),
        }
        moving_days = {
            easter + timedelta(days=1),
            easter + timedelta(days=39),
            easter + timedelta(days=50),
        }
        return value in fixed_days or value in moving_days

    def _easter_sunday(self, year: int) -> date:
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    def _parse_hhmm(self, value: str) -> time | None:
        text = value.strip()
        if not text or ":" not in text:
            return None
        hour, minute = text.split(":", 1)
        return time(hour=int(hour), minute=int(minute))

    def _read_requests_for_annonce(self, annonce_id: int) -> list[dict[str, Any]]:
        rows = self._rest_get(
            "app_appointment_request",
            params={
                "select": "id,request_status,client_nom,client_email,client_telephone,requested_start_at,requested_end_at,client_message,created_at",
                "hektor_annonce_id": f"eq.{annonce_id}",
                "order": "created_at.desc",
                "limit": "50",
            },
        )
        return [
            {
                "id": row.get("id"),
                "status": row.get("request_status"),
                "client_nom": row.get("client_nom"),
                "client_email": row.get("client_email"),
                "client_telephone": row.get("client_telephone"),
                "requested_start_at": row.get("requested_start_at"),
                "requested_end_at": row.get("requested_end_at"),
                "message": row.get("client_message"),
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]

    def _read_events_for_request_ids(self, request_ids: list[str]) -> list[dict[str, Any]]:
        cleaned = [item for item in request_ids if item]
        if not cleaned:
            return []
        rows = self._rest_get(
            "app_appointment_request_event",
            params={
                "select": "id,appointment_request_id,event_type,event_label,actor_name,payload_json,created_at",
                "appointment_request_id": f"in.({','.join(cleaned)})",
                "order": "created_at.desc",
                "limit": "200",
            },
        )
        return [
            {
                "id": row.get("id"),
                "appointment_request_id": row.get("appointment_request_id"),
                "event_type": row.get("event_type"),
                "event_label": row.get("event_label"),
                "actor_name": row.get("actor_name"),
                "payload_json": self._stringify_payload_json(row.get("payload_json")),
                "created_at": row.get("created_at"),
            }
            for row in rows
        ]

    def _stringify_payload_json(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)

    def _is_fake_busy(self, seed: str, start_at: datetime, busy_ratio: float) -> bool:
        digest = hashlib.sha1(f"{seed}|{start_at.date().isoformat()}|{start_at.strftime('%H:%M')}".encode("utf-8")).hexdigest()
        value = int(digest[:8], 16) / 0xFFFFFFFF
        return value < busy_ratio

    def create_public_annonce_request(self, ref: str, payload: AppointmentRequestCreatePayload) -> dict[str, Any]:
        link, dossier = self._resolve_link(ref)
        nego_email = str(dossier.get("negociateur_email") or "").strip()
        if not nego_email:
            raise HTTPException(status_code=400, detail="Aucun email negociateur disponible pour cette annonce")
        requested_start = self._parse_client_datetime(payload.requestedStartAt)
        requested_end = self._parse_client_datetime(payload.requestedEndAt) if payload.requestedEndAt else None
        valid_slots = {
            slot["startAt"]: slot
            for slot in self._generate_slots(link, self._read_slot_rule(link))
            if slot.get("available")
        }
        start_key = requested_start.astimezone(UTC).isoformat()
        if start_key not in valid_slots:
            raise HTTPException(status_code=400, detail="Le creneau demande n'est plus disponible")
        if requested_end is None:
            requested_end = self._parse_client_datetime(valid_slots[start_key]["endAt"])

        request_row = {
            "public_link_id": link["id"],
            "app_dossier_id": dossier.get("app_dossier_id"),
            "hektor_annonce_id": dossier.get("hektor_annonce_id"),
            "commercial_id": dossier.get("commercial_id"),
            "commercial_nom": dossier.get("commercial_nom"),
            "negociateur_email": nego_email,
            "agence_nom": dossier.get("agence_nom"),
            "client_nom": payload.clientName,
            "client_email": payload.clientEmail,
            "client_telephone": payload.clientPhone,
            "requested_start_at": requested_start.astimezone(UTC).isoformat(),
            "requested_end_at": requested_end.astimezone(UTC).isoformat(),
            "client_message": payload.message,
            "request_status": "pending",
        }
        rows = self._rest_post("app_appointment_request", payload=[request_row])
        if not rows:
            raise HTTPException(status_code=500, detail="Demande de rendez-vous non creee")
        created = rows[0]

        self._rest_post(
            "app_appointment_request_event",
            payload=[
                {
                    "appointment_request_id": created["id"],
                    "event_type": "request_created",
                    "event_label": "Demande client creee",
                    "actor_name": payload.clientName,
                    "payload_json": {
                        "client_email": payload.clientEmail,
                        "client_telephone": payload.clientPhone,
                        "requested_start_at": request_row["requested_start_at"],
                    },
                }
            ],
        )

        self._send_notification_email(dossier=dossier, request_row=request_row)

        self._rest_post(
            "app_appointment_request_event",
            payload=[
                {
                    "appointment_request_id": created["id"],
                    "event_type": "mail_sent",
                    "event_label": "Notification envoyee au negociateur",
                    "actor_name": "Systeme",
                    "payload_json": {"to": nego_email},
                }
            ],
        )

        return {
            "ok": True,
            "requestId": created["id"],
            "status": created["request_status"],
        }

    def _parse_client_datetime(self, value: str) -> datetime:
        text = value.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Date de rendez-vous manquante")
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Format de date invalide") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed

    def _send_notification_email(self, *, dossier: dict[str, Any], request_row: dict[str, Any]) -> None:
        to = str(request_row.get("negociateur_email") or "").strip()
        if not to:
            raise HTTPException(status_code=400, detail="Email negociateur manquant")
        start_local = self._parse_client_datetime(str(request_row["requested_start_at"])).astimezone(PARIS_TZ)
        title = str(dossier.get("titre_bien") or "").strip() or f"Annonce {dossier.get('hektor_annonce_id') or '-'}"
        subject = f"Nouvelle demande de rendez-vous - {title}"
        lines = [
            "Une nouvelle demande de rendez-vous a ete envoyee depuis un QR annonce vitrine.",
            "",
            f"Bien : {dossier.get('titre_bien') or '-'}",
            f"Annonce : {dossier.get('hektor_annonce_id') or '-'}",
            f"Dossier : {dossier.get('numero_dossier') or '-'}",
            f"Client : {request_row.get('client_nom') or '-'}",
            f"Telephone : {request_row.get('client_telephone') or '-'}",
            f"Email : {request_row.get('client_email') or '-'}",
            f"Creneau souhaite : {start_local.strftime('%d/%m/%Y %H:%M')}",
            f"Message : {request_row.get('client_message') or 'Sans message'}",
        ]
        email_payload = {
            "to": to,
            "subject": subject,
            "bodyText": "\n".join(lines),
            "fromName": "GTI Rendez-vous",
        }
        self.notification_service.send_diffusion_decision(email_payload)
