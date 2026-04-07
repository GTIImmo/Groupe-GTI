from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_authenticated_user, require_request_user
from ..models import CreateUserPayload, SendResetPayload, UpdateUserPayload
from ..services.supabase_admin import SupabaseAdminService
from ..settings import Settings, get_settings


router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def get_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


@router.get("/list")
def list_users(
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    service: SupabaseAdminService = Depends(get_service),
):
    user = get_authenticated_user(settings, authorization)
    service.assert_admin(user)
    return {"ok": True, "users": service.list_users()}


@router.post("/create")
def create_user(
    payload: CreateUserPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    service: SupabaseAdminService = Depends(get_service),
):
    user = get_authenticated_user(settings, authorization)
    service.assert_admin(user)
    return service.create_user(payload.model_dump())


@router.post("/update")
def update_user(
    payload: UpdateUserPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    service: SupabaseAdminService = Depends(get_service),
):
    user = get_authenticated_user(settings, authorization)
    service.assert_admin(user)
    return service.update_user(payload.model_dump())


@router.post("/send-reset")
def send_reset(
    payload: SendResetPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    service: SupabaseAdminService = Depends(get_service),
):
    user = get_authenticated_user(settings, authorization)
    service.assert_admin(user)
    return service.send_reset(payload.email)
