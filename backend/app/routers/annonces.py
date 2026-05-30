from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_authenticated_user, require_request_user
from ..models import ScanAnnonceSheetPayload
from ..services.openai_listing_sheet_service import OpenAIListingSheetService
from ..services.supabase_admin import SupabaseAdminService
from ..settings import Settings, get_settings


router = APIRouter(prefix="/annonces", tags=["annonces"])


def get_admin_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


def get_listing_sheet_service(settings: Settings = Depends(get_settings)) -> OpenAIListingSheetService:
    return OpenAIListingSheetService(settings)


@router.post("/scan-fiche")
def scan_annonce_sheet(
    payload: ScanAnnonceSheetPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    listing_sheet_service: OpenAIListingSheetService = Depends(get_listing_sheet_service),
):
    user = get_authenticated_user(settings, authorization)
    profile = admin_service.load_profile(user)
    role = str(profile.get("role") or "")
    if role not in {"admin", "manager", "commercial"} or profile.get("is_active") is not True:
        raise HTTPException(status_code=403, detail="Acces scan fiche refuse")
    return {"ok": True, "payload": listing_sheet_service.extract(payload.model_dump())}
