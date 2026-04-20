from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_authenticated_user, require_request_user
from ..models import AcceptDiffusionPayload, ApplyDiffusionPayload, PersistHektorStatePayload, SetDiffusablePayload, SetValidationPayload
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
    result = bridge.apply(payload.appDossierId, payload.dryRun, payload.ensureDiffusable, user.email or user.id)
    if not payload.dryRun and result.get("hektor_annonce_id"):
        result["refresh_queue"] = admin_service.enqueue_annonce_refresh(
            app_dossier_id=payload.appDossierId,
            hektor_annonce_id=str(result.get("hektor_annonce_id") or ""),
            reason="apply_diffusion_targets",
            requested_by=user.email or user.id,
            payload={"ensure_diffusable": payload.ensureDiffusable},
        )
    return {"ok": True, "payload": result}


@router.post("/diffusable")
def set_diffusable(
    payload: SetDiffusablePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    bridge: HektorBridgeService = Depends(get_bridge),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    result = bridge.set_diffusable(payload.appDossierId, payload.diffusable, payload.dryRun)
    if not payload.dryRun and result.get("hektor_annonce_id"):
        result["refresh_queue"] = admin_service.enqueue_annonce_refresh(
            app_dossier_id=payload.appDossierId,
            hektor_annonce_id=str(result.get("hektor_annonce_id") or ""),
            reason="set_diffusable",
            requested_by=user.email or user.id,
            payload={"requested_diffusable": payload.diffusable},
        )
    return {"ok": True, "payload": result}


@router.post("/validation")
def set_validation(
    payload: SetValidationPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    bridge: HektorBridgeService = Depends(get_bridge),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    result = bridge.set_validation(payload.appDossierId, payload.state, payload.dryRun)
    if not payload.dryRun and result.get("hektor_annonce_id"):
        result["refresh_queue"] = admin_service.enqueue_annonce_refresh(
            app_dossier_id=payload.appDossierId,
            hektor_annonce_id=str(result.get("hektor_annonce_id") or ""),
            reason="set_validation",
            requested_by=user.email or user.id,
            payload={"requested_state": payload.state},
        )
    return {"ok": True, "payload": result}


@router.post("/persist-state")
def persist_hektor_state(
    payload: PersistHektorStatePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    bridge: HektorBridgeService = Depends(get_bridge),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return {
        "ok": True,
        "payload": bridge.persist_state(
            payload.appDossierId,
            validation_diffusion_state=payload.validationDiffusionState,
            diffusable=payload.diffusable,
        ),
    }


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
    result = bridge.accept(payload.appDossierId, payload.dryRun, user.email or user.id)
    if not payload.dryRun and result.get("hektor_annonce_id"):
        result["refresh_queue"] = admin_service.enqueue_annonce_refresh(
            app_dossier_id=payload.appDossierId,
            hektor_annonce_id=str(result.get("hektor_annonce_id") or ""),
            reason="accept_validation_request",
            requested_by=user.email or user.id,
        )
    return {"ok": True, "payload": result}
