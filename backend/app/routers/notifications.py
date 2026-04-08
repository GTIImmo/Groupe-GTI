from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_authenticated_user, require_request_user
from ..models import DiffusionDecisionEmailPayload
from ..services.notification_service import NotificationService
from ..services.supabase_admin import SupabaseAdminService
from ..settings import Settings, get_settings


router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_service(settings: Settings = Depends(get_settings)) -> NotificationService:
    return NotificationService(settings)


def get_admin_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


@router.post("/diffusion-decision")
def send_diffusion_decision(
    payload: DiffusionDecisionEmailPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    notification_service: NotificationService = Depends(get_notification_service),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return notification_service.send_diffusion_decision(payload.model_dump())
