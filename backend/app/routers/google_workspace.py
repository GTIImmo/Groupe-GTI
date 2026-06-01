from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from ..auth import get_authenticated_user, require_request_user
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


def get_google_workspace_service(settings: Settings = Depends(get_settings)) -> GoogleWorkspaceService:
    return GoogleWorkspaceService(settings)


def get_admin_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


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
