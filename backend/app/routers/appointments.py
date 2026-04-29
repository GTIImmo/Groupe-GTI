from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_authenticated_user, require_request_user
from ..models import AppointmentRequestCreatePayload
from ..services.appointment_service import AppointmentService
from ..settings import Settings, get_settings


router = APIRouter(prefix="/public/appointments", tags=["appointments"])


def get_appointment_service(settings: Settings = Depends(get_settings)) -> AppointmentService:
    return AppointmentService(settings)


@router.get("/annonce/{ref}")
def get_public_annonce_context(
    ref: str,
    service: AppointmentService = Depends(get_appointment_service),
):
    return service.get_public_annonce_context(ref)


@router.get("/annonce/{ref}/bootstrap")
def get_public_annonce_bootstrap(
    ref: str,
    service: AppointmentService = Depends(get_appointment_service),
):
    return service.get_public_annonce_bootstrap(ref)


@router.get("/annonce/{ref}/slots")
def get_public_annonce_slots(
    ref: str,
    service: AppointmentService = Depends(get_appointment_service),
):
    return service.get_public_annonce_slots(ref)


@router.post("/annonce/{ref}/request")
def create_public_annonce_request(
    ref: str,
    payload: AppointmentRequestCreatePayload,
    service: AppointmentService = Depends(get_appointment_service),
):
    return service.create_public_annonce_request(ref, payload)


@router.get("/annonce/{annonce_id}/summary")
def get_internal_annonce_summary(
    annonce_id: int,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    service: AppointmentService = Depends(get_appointment_service),
):
    get_authenticated_user(settings, authorization)
    return service.get_internal_annonce_summary(annonce_id)
