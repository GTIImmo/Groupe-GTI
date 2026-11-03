from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_authenticated_user, require_request_user
from ..models import AcceptDiffusionPayload, ApplyDiffusionPayload, PersistHektorStatePayload, SetDiffusablePayload, SetValidationPayload, VerifyPriceDropPayload
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
    # Lot 4 (03/11/2026) : ouvert au negociateur sur SES annonces deja diffusables ; il ne peut
    # jamais rendre une annonce diffusable (ensureDiffusable force a False pour lui).
    _profile, privilegie = admin_service.assert_can_apply_portals(user, authorization, payload.appDossierId)
    ensure_diffusable = payload.ensureDiffusable if privilegie else False
    return {"ok": True, "payload": bridge.apply(payload.appDossierId, payload.dryRun, ensure_diffusable, user.email or user.id)}


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
    return {"ok": True, "payload": bridge.set_diffusable(payload.appDossierId, payload.diffusable, payload.dryRun)}


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
    return {"ok": True, "payload": bridge.set_validation(payload.appDossierId, payload.state, payload.dryRun)}


@router.post("/persist-state")
def persist_hektor_state(
    payload: PersistHektorStatePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    bridge: HektorBridgeService = Depends(get_bridge),
):
    user = get_authenticated_user(settings, authorization)
    # Lot 4 (03/11/2026) : le negociateur peut reporter l'etat de SES portails (resume, nombre),
    # jamais la validation ni « diffusable » -- ces deux champs sont ignores pour lui.
    _profile, privilegie = admin_service.assert_can_apply_portals(user, authorization, payload.appDossierId)
    return {
        "ok": True,
        "payload": bridge.persist_state(
            payload.appDossierId,
            validation_diffusion_state=payload.validationDiffusionState if privilegie else None,
            diffusable=payload.diffusable if privilegie else None,
            portails_resume=payload.portailsResume,
            nb_portails_actifs=payload.nbPortailsActifs,
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
    return {"ok": True, "payload": bridge.accept(payload.appDossierId, payload.dryRun, user.email or user.id)}


@router.post("/price-drop-check")
def verify_price_drop(
    payload: VerifyPriceDropPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    bridge: HektorBridgeService = Depends(get_bridge),
):
    user = get_authenticated_user(settings, authorization)
    admin_service.assert_admin(user)
    return {"ok": True, "payload": bridge.verify_price_drop(payload.appDossierId, payload.requestedPrice, payload.requestText)}
