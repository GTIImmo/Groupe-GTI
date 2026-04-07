from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_authenticated_user, require_request_user
from ..models import AcceptDiffusionPayload, ApplyDiffusionPayload
from ..services.hektor_bridge import HektorBridgeService
from ..services.supabase_admin import SupabaseAdminService
from ..settings import Settings, get_settings


router = APIRouter(prefix="/hektor-diffusion", tags=["hektor-diffusion"])


def get_bridge(settings: Settings = Depends(get_settings)) -> HektorBridgeService:
    return HektorBridgeService(settings)


def get_admin_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


@router.post("/apply")
def apply_diffusion(
    payload: ApplyDiffusionPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    bridge: HektorBridgeService = Depends(get_bridge),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return {"ok": True, "payload": bridge.apply(payload.appDossierId, payload.dryRun, payload.ensureDiffusable)}


@router.post("/accept")
def accept_diffusion(
    payload: AcceptDiffusionPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    bridge: HektorBridgeService = Depends(get_bridge),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return {"ok": True, "payload": bridge.accept(payload.appDossierId, payload.dryRun)}
