"""Endpoint données de marché DVF (comparables) — interne, authentifié."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..auth import get_authenticated_user, require_request_user
from ..services import dvf_service
from ..settings import Settings, get_settings

router = APIRouter(tags=["dvf"])


@router.get("/dvf/comparables")
def dvf_comparables(
    lat: float = Query(...),
    lon: float = Query(...),
    dept: str = Query(..., description="Code département (ex. 42, 2A)"),
    type: str = Query("Maison", pattern="^(Maison|Appartement)$"),
    surface: float | None = Query(None),
    radius_km: float = Query(12.0, ge=1, le=50),
    months: int = Query(24, ge=6, le=60),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Comparables DVF géolocalisés autour d'un bien (commune + voisines, 24 mois,
    même type, surface ±30 %). Source open data geo-dvf, mise en cache 24 h."""
    get_authenticated_user(settings, authorization)
    return dvf_service.comparables(
        lat=lat, lon=lon, dept=str(dept).strip(), type_local=type,
        surface=surface, radius_km=radius_km, months=months,
    )
