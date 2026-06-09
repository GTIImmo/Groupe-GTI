from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from ..auth import get_authenticated_user, require_request_user
from ..services.google_calendar_event_link_service import GoogleCalendarEventLinkService
from ..services.google_workspace_service import GoogleWorkspaceService
from ..services.supabase_admin import SupabaseAdminService
from ..settings import Settings, get_settings


router = APIRouter(prefix="/google-workspace", tags=["google-workspace"])


class GoogleCalendarFreeBusyTestPayload(BaseModel):
    subjectEmail: EmailStr
    timeMin: str | None = None
    timeMax: str | None = None
    calendarIds: list[str] = Field(default_factory=list)


class GoogleCalendarEventTestPayload(BaseModel):
    subjectEmail: EmailStr
    summary: str = Field(min_length=1, max_length=240)
    startAt: str = Field(min_length=10)
    endAt: str = Field(min_length=10)
    description: str | None = None
    location: str | None = None
    attendees: list[EmailStr] = Field(default_factory=list)
    sendUpdates: Literal["all", "externalOnly", "none"] = "none"
    dryRun: bool = True


class GoogleGmailSendTestPayload(BaseModel):
    subjectEmail: EmailStr
    to: list[EmailStr] = Field(default_factory=list)
    subject: str = Field(min_length=1, max_length=240)
    bodyText: str = Field(min_length=1, max_length=5000)
    bodyHtml: str | None = Field(default=None, max_length=20000)
    fromName: str = Field(default="GTI Immobilier", min_length=1, max_length=120)
    replyTo: EmailStr | None = None
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    dryRun: bool = True
    relatedEntityType: str | None = Field(default=None, max_length=80)
    relatedEntityId: str | None = Field(default=None, max_length=120)


class GoogleGmailSendPayload(BaseModel):
    subjectEmail: EmailStr
    to: list[EmailStr] = Field(default_factory=list)
    subject: str = Field(min_length=1, max_length=240)
    bodyText: str = Field(min_length=1, max_length=8000)
    bodyHtml: str | None = Field(default=None, max_length=30000)
    fromName: str = Field(default="GTI Immobilier", min_length=1, max_length=120)
    replyTo: EmailStr | None = None
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    dryRun: bool = False
    relatedEntityType: str | None = Field(default=None, max_length=80)
    relatedEntityId: str | None = Field(default=None, max_length=120)


class GoogleCalendarEventDeletePayload(BaseModel):
    subjectEmail: EmailStr
    eventId: str = Field(min_length=1, max_length=256)
    sendUpdates: Literal["all", "externalOnly", "none"] = "none"


class GoogleCalendarEventUpdatePayload(BaseModel):
    subjectEmail: EmailStr
    eventId: str = Field(min_length=1, max_length=256)
    summary: str | None = Field(default=None, min_length=1, max_length=240)
    startAt: str | None = None
    endAt: str | None = None
    description: str | None = None
    location: str | None = None
    attendees: list[EmailStr] | None = None
    sendUpdates: Literal["all", "externalOnly", "none"] = "none"
    dryRun: bool = True


class GoogleCalendarEventCreatePayload(BaseModel):
    subjectEmail: EmailStr
    eventType: Literal["visite", "estimation", "mandat", "compromis", "relance", "agence", "autre"] = "visite"
    relatedEntityType: Literal["annonce", "contact", "affaire", "visite", "relance", "other"] = "annonce"
    relatedEntityId: str | None = Field(default=None, max_length=120)
    appDossierId: int | None = Field(default=None, gt=0)
    hektorAnnonceId: int | None = Field(default=None, gt=0)
    hektorContactId: str | None = Field(default=None, max_length=80)
    summary: str = Field(min_length=1, max_length=240)
    startAt: str = Field(min_length=10)
    endAt: str = Field(min_length=10)
    description: str | None = Field(default=None, max_length=12000)
    location: str | None = Field(default=None, max_length=500)
    attendees: list[EmailStr] = Field(default_factory=list)
    sendUpdates: Literal["all", "externalOnly", "none"] = "all"
    dryRun: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


class GoogleCalendarAvailabilityPayload(BaseModel):
    subjectEmail: EmailStr
    startAt: str = Field(min_length=10)
    endAt: str = Field(min_length=10)


class GoogleCalendarEventBusinessUpdatePayload(BaseModel):
    eventType: Literal["visite", "estimation", "mandat", "compromis", "relance", "agence", "autre"] | None = None
    relatedEntityType: Literal["annonce", "contact", "affaire", "visite", "relance", "other"] | None = None
    relatedEntityId: str | None = Field(default=None, max_length=120)
    appDossierId: int | None = Field(default=None, gt=0)
    hektorAnnonceId: int | None = Field(default=None, gt=0)
    hektorContactId: str | None = Field(default=None, max_length=80)
    summary: str | None = Field(default=None, min_length=1, max_length=240)
    startAt: str | None = None
    endAt: str | None = None
    description: str | None = Field(default=None, max_length=12000)
    location: str | None = Field(default=None, max_length=500)
    attendees: list[EmailStr] | None = None
    metadata: dict[str, object] | None = None
    sendUpdates: Literal["all", "externalOnly", "none"] = "all"
    dryRun: bool = False


class GoogleCalendarEventBusinessDeletePayload(BaseModel):
    sendUpdates: Literal["all", "externalOnly", "none"] = "all"


def get_google_workspace_service(settings: Settings = Depends(get_settings)) -> GoogleWorkspaceService:
    return GoogleWorkspaceService(settings)


def get_admin_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


def get_calendar_link_service(settings: Settings = Depends(get_settings)) -> GoogleCalendarEventLinkService:
    return GoogleCalendarEventLinkService(settings)


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _metadata_hektor_contact_id(metadata: dict[str, object] | None) -> str | None:
    if not isinstance(metadata, dict):
        return None
    direct_contact_id = _clean_optional_text(metadata.get("contact_id")) or _clean_optional_text(metadata.get("hektor_contact_id"))
    if direct_contact_id:
        return direct_contact_id
    attendee_contacts = metadata.get("attendee_contacts")
    if not isinstance(attendee_contacts, list):
        return None
    for item in attendee_contacts:
        if not isinstance(item, dict):
            continue
        contact_id = (
            _clean_optional_text(item.get("hektor_contact_id"))
            or _clean_optional_text(item.get("hektorContactId"))
            or _clean_optional_text(item.get("contact_id"))
        )
        if contact_id:
            return contact_id
    return None


@router.get("/status")
def get_google_workspace_status(
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return service.status()


@router.post("/calendar/freebusy-test")
def test_google_calendar_freebusy(
    payload: GoogleCalendarFreeBusyTestPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return service.calendar_freebusy(
        subject_email=str(payload.subjectEmail),
        time_min=payload.timeMin,
        time_max=payload.timeMax,
        calendar_ids=payload.calendarIds or None,
        requested_by=user.id,
        requested_by_email=user.email,
    )


@router.post("/gmail/send-test")
def test_google_gmail_send(
    payload: GoogleGmailSendTestPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return service.send_gmail_message(
        subject_email=str(payload.subjectEmail),
        to=[str(email) for email in payload.to],
        subject=payload.subject,
        body_text=payload.bodyText,
        body_html=payload.bodyHtml,
        from_name=payload.fromName,
        reply_to=str(payload.replyTo) if payload.replyTo else None,
        cc=[str(email) for email in payload.cc],
        bcc=[str(email) for email in payload.bcc],
        dry_run=payload.dryRun,
        requested_by=user.id,
        requested_by_email=user.email,
        related_entity_type=payload.relatedEntityType,
        related_entity_id=payload.relatedEntityId,
    )


@router.post("/gmail/send")
def send_google_gmail_message(
    payload: GoogleGmailSendPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_gmail_subject_allowed(user, str(payload.subjectEmail))
    try:
        return service.send_gmail_message(
            subject_email=str(payload.subjectEmail),
            to=[str(email) for email in payload.to],
            subject=payload.subject,
            body_text=payload.bodyText,
            body_html=payload.bodyHtml,
            from_name=payload.fromName,
            reply_to=str(payload.replyTo) if payload.replyTo else None,
            cc=[str(email) for email in payload.cc],
            bcc=[str(email) for email in payload.bcc],
            dry_run=payload.dryRun,
            requested_by=user.id,
            requested_by_email=user.email,
            related_entity_type=payload.relatedEntityType,
            related_entity_id=payload.relatedEntityId,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/calendar/event-test")
def test_google_calendar_event(
    payload: GoogleCalendarEventTestPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return service.create_calendar_event(
        subject_email=str(payload.subjectEmail),
        summary=payload.summary,
        start_at=payload.startAt,
        end_at=payload.endAt,
        description=payload.description,
        location=payload.location,
        attendees=[str(email) for email in payload.attendees],
        send_updates=payload.sendUpdates,
        dry_run=payload.dryRun,
        requested_by=user.id,
        requested_by_email=user.email,
    )


@router.post("/calendar/event-update-test")
def test_google_calendar_event_update(
    payload: GoogleCalendarEventUpdatePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return service.update_calendar_event(
        subject_email=str(payload.subjectEmail),
        event_id=payload.eventId,
        summary=payload.summary,
        start_at=payload.startAt,
        end_at=payload.endAt,
        description=payload.description,
        location=payload.location,
        attendees=[str(email) for email in payload.attendees] if payload.attendees is not None else None,
        send_updates=payload.sendUpdates,
        dry_run=payload.dryRun,
        requested_by=user.id,
        requested_by_email=user.email,
    )


@router.post("/calendar/event-delete-test")
def test_google_calendar_event_delete(
    payload: GoogleCalendarEventDeletePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return service.delete_calendar_event(
        subject_email=str(payload.subjectEmail),
        event_id=payload.eventId,
        send_updates=payload.sendUpdates,
        requested_by=user.id,
        requested_by_email=user.email,
    )


@router.get("/calendar/events")
def list_google_calendar_event_links(
    appDossierId: int | None = Query(default=None, gt=0),
    hektorAnnonceId: int | None = Query(default=None, gt=0),
    hektorContactId: str | None = Query(default=None, max_length=80),
    calendarEmail: EmailStr | None = Query(default=None),
    startAt: str | None = Query(default=None, max_length=40),
    endAt: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=50, ge=1, le=100),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    link_service: GoogleCalendarEventLinkService = Depends(get_calendar_link_service),
):
    user = get_authenticated_user(settings, authorization)
    profile = admin_service.assert_active_profile(user)
    role = str(profile.get("role") or "")
    scoped_calendar_email = str(calendarEmail) if calendarEmail else None
    if role not in {"admin", "manager"}:
        scoped_calendar_email = scoped_calendar_email or str(profile.get("email") or user.email or "")
        admin_service.assert_calendar_subject_allowed(user, scoped_calendar_email)
    elif scoped_calendar_email:
        admin_service.assert_calendar_subject_allowed(user, scoped_calendar_email)
    return {
        "ok": True,
        "events": link_service.list_links(
            app_dossier_id=appDossierId,
            hektor_annonce_id=hektorAnnonceId,
            hektor_contact_id=hektorContactId,
            calendar_email=scoped_calendar_email,
            start_at=startAt,
            end_at=endAt,
            limit=limit,
        ),
    }


@router.post("/calendar/availability")
def check_google_calendar_availability(
    payload: GoogleCalendarAvailabilityPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_calendar_subject_allowed(user, str(payload.subjectEmail))
    try:
        return service.check_calendar_availability(
            subject_email=str(payload.subjectEmail),
            start_at=payload.startAt,
            end_at=payload.endAt,
            requested_by=user.id,
            requested_by_email=user.email,
        )
    except Exception as exc:
        return {
            "ok": False,
            "subjectEmail": str(payload.subjectEmail).lower(),
            "timeMin": payload.startAt,
            "timeMax": payload.endAt,
            "isAvailable": False,
            "busyCount": 0,
            "busy": [],
            "statusCode": 502,
            "error": {
                "message": "Compte Google Agenda non disponible ou non autorise pour cet utilisateur.",
                "providerMessage": str(exc)[:500],
            },
        }


@router.post("/calendar/events")
def create_google_calendar_event(
    payload: GoogleCalendarEventCreatePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
    link_service: GoogleCalendarEventLinkService = Depends(get_calendar_link_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_calendar_subject_allowed(user, str(payload.subjectEmail))
    attendees = [str(email) for email in payload.attendees]
    result = service.create_calendar_event(
        subject_email=str(payload.subjectEmail),
        summary=payload.summary,
        start_at=payload.startAt,
        end_at=payload.endAt,
        description=payload.description,
        location=payload.location,
        attendees=attendees,
        send_updates=payload.sendUpdates,
        dry_run=payload.dryRun,
        requested_by=user.id,
        requested_by_email=user.email,
    )
    if payload.dryRun or not result.get("ok"):
        return {**result, "linkSaved": False}

    event_payload = result.get("event") if isinstance(result.get("event"), dict) else {}
    start_payload = event_payload.get("start") if isinstance(event_payload.get("start"), dict) else {}
    end_payload = event_payload.get("end") if isinstance(event_payload.get("end"), dict) else {}
    metadata_json = {
        **payload.metadata,
        "send_updates": payload.sendUpdates,
        "has_description": bool(payload.description),
    }
    hektor_contact_id = _clean_optional_text(payload.hektorContactId) or _metadata_hektor_contact_id(metadata_json)
    link = link_service.create_link(
        event_type=payload.eventType,
        related_entity_type=payload.relatedEntityType,
        related_entity_id=payload.relatedEntityId,
        app_dossier_id=payload.appDossierId,
        hektor_annonce_id=payload.hektorAnnonceId,
        hektor_contact_id=hektor_contact_id,
        calendar_email=str(payload.subjectEmail).lower(),
        google_event_id=str(result.get("eventId") or ""),
        google_html_link=result.get("htmlLink"),
        summary=payload.summary,
        location=payload.location,
        starts_at=str(start_payload.get("dateTime") or payload.startAt),
        ends_at=str(end_payload.get("dateTime") or payload.endAt),
        attendees=attendees,
        metadata_json=metadata_json,
        created_by=user.id,
        created_by_email=user.email,
    )
    return {**result, "linkSaved": True, "link": link}


@router.patch("/calendar/events/{link_id}")
def update_google_calendar_event(
    link_id: str,
    payload: GoogleCalendarEventBusinessUpdatePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
    link_service: GoogleCalendarEventLinkService = Depends(get_calendar_link_service),
):
    user = get_authenticated_user(settings, authorization)
    link = link_service.get_link(link_id)
    calendar_email = str(link.get("google_calendar_email") or "")
    event_id = str(link.get("google_event_id") or "")
    admin_service.assert_calendar_subject_allowed(user, calendar_email)
    attendees = [str(email) for email in payload.attendees] if payload.attendees is not None else None
    result = service.update_calendar_event(
        subject_email=calendar_email,
        event_id=event_id,
        summary=payload.summary,
        start_at=payload.startAt,
        end_at=payload.endAt,
        description=payload.description,
        location=payload.location,
        attendees=attendees,
        send_updates=payload.sendUpdates,
        dry_run=payload.dryRun,
        requested_by=user.id,
        requested_by_email=user.email,
    )
    if payload.dryRun or not result.get("ok"):
        return {**result, "linkSaved": False, "link": link}

    event_payload = result.get("event") if isinstance(result.get("event"), dict) else {}
    start_payload = event_payload.get("start") if isinstance(event_payload.get("start"), dict) else {}
    end_payload = event_payload.get("end") if isinstance(event_payload.get("end"), dict) else {}
    metadata_patch = {
        **(link.get("metadata_json") if isinstance(link.get("metadata_json"), dict) else {}),
        **(payload.metadata or {}),
        "last_send_updates": payload.sendUpdates,
    }
    hektor_contact_id = _clean_optional_text(payload.hektorContactId) or _metadata_hektor_contact_id(metadata_patch)
    next_link = link_service.update_link(
        link_id=link_id,
        updated_by=user.id,
        updated_by_email=user.email,
        event_type=payload.eventType,
        related_entity_type=payload.relatedEntityType,
        related_entity_id=payload.relatedEntityId,
        app_dossier_id=payload.appDossierId,
        hektor_annonce_id=payload.hektorAnnonceId,
        hektor_contact_id=hektor_contact_id,
        summary=payload.summary,
        location=payload.location,
        starts_at=str(start_payload.get("dateTime") or payload.startAt) if payload.startAt else None,
        ends_at=str(end_payload.get("dateTime") or payload.endAt) if payload.endAt else None,
        attendees=attendees,
        google_html_link=result.get("htmlLink"),
        metadata_patch=metadata_patch,
    )
    return {**result, "linkSaved": True, "link": next_link}


@router.delete("/calendar/events/{link_id}")
def delete_google_calendar_event(
    link_id: str,
    payload: GoogleCalendarEventBusinessDeletePayload | None = None,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: GoogleWorkspaceService = Depends(get_google_workspace_service),
    link_service: GoogleCalendarEventLinkService = Depends(get_calendar_link_service),
):
    user = get_authenticated_user(settings, authorization)
    link = link_service.get_link(link_id)
    calendar_email = str(link.get("google_calendar_email") or "")
    event_id = str(link.get("google_event_id") or "")
    admin_service.assert_calendar_subject_allowed(user, calendar_email)
    send_updates = payload.sendUpdates if payload else "all"
    result = service.delete_calendar_event(
        subject_email=calendar_email,
        event_id=event_id,
        send_updates=send_updates,
        requested_by=user.id,
        requested_by_email=user.email,
    )
    if not result.get("ok"):
        return {**result, "linkSaved": False, "link": link}
    next_link = link_service.mark_deleted(
        link_id=link_id,
        updated_by=user.id,
        updated_by_email=user.email,
    )
    return {**result, "linkSaved": True, "link": next_link}
