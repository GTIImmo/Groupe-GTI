"""Router des pages d'action « demande de visite » (sans login, via jeton signé).

- GET  /visite/{token}            → page d'action du négociateur (choisir un créneau).
- POST /visite/{token}/confirmer  → confirme le créneau : crée le VRAI évènement Google
  dans l'agenda du négociateur (DWD), passe la demande en « confirmee » et prévient le
  client par email.

Le jeton porte l'id de la demande et le rôle ('nego'). Aucune donnée personnelle dans l'URL.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ..services import email_tokens
from ..services.espace_visite import VisiteRequestService
from ..settings import Settings, get_settings

router = APIRouter(tags=["visite"])


def _secret(settings: Settings) -> str:
    return getattr(settings, "email_tracking_secret", None) or settings.supabase_service_role_key


def _verify(token: str, settings: Settings) -> dict | None:
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") != email_tokens.ACTION_VISITE_REQ:
        return None
    return payload


@router.get("/visite/{token}", response_class=HTMLResponse)
def visite_page(token: str, settings: Settings = Depends(get_settings)):
    payload = _verify(token, settings)
    svc = VisiteRequestService(settings)
    if not payload:
        return HTMLResponse(_expired(), status_code=410)
    req = svc.get(str(payload.get("r") or ""))
    if not req:
        return HTMLResponse(_expired(), status_code=410)
    # role client → page d'acceptation d'un créneau proposé ; sinon page d'action du négo.
    if payload.get("role") == "client":
        return HTMLResponse(svc.render_client_page(req=req, token=token))
    return HTMLResponse(svc.render_nego_page(req=req, token=token))


@router.post("/visite/{token}/confirmer")
async def visite_confirmer(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = _verify(token, settings)
    if not payload or payload.get("role") != "nego":
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    try:
        body = await request.json()
    except Exception:
        body = {}
    start_iso = str((body or {}).get("start") or "").strip()
    end_iso = str((body or {}).get("end") or "").strip()
    if not start_iso or not end_iso:
        return JSONResponse({"ok": False, "error": "missing_slot"}, status_code=400)
    svc = VisiteRequestService(settings)
    try:
        res = svc.confirm(request_id=str(payload.get("r") or ""), start_iso=start_iso, end_iso=end_iso)
    except Exception:
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    return JSONResponse(res)


@router.post("/visite/{token}/proposer")
async def visite_proposer(token: str, request: Request, settings: Settings = Depends(get_settings)):
    """Le négociateur propose un ou plusieurs créneaux au client (statut proposee + email client)."""
    payload = _verify(token, settings)
    if not payload or payload.get("role") != "nego":
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    try:
        body = await request.json()
    except Exception:
        body = {}
    slots = (body or {}).get("slots")
    if not isinstance(slots, list) or not slots:
        return JSONResponse({"ok": False, "error": "missing_slots"}, status_code=400)
    svc = VisiteRequestService(settings)
    try:
        res = svc.propose(request_id=str(payload.get("r") or ""), slots=slots)
    except Exception:
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    return JSONResponse(res)


@router.post("/visite/{token}/accepter")
async def visite_accepter(token: str, request: Request, settings: Settings = Depends(get_settings)):
    """Le client accepte un créneau proposé : crée le vrai RDV Google et prévient le négociateur."""
    payload = _verify(token, settings)
    if not payload or payload.get("role") != "client":
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    try:
        body = await request.json()
    except Exception:
        body = {}
    start_iso = str((body or {}).get("start") or "").strip()
    end_iso = str((body or {}).get("end") or "").strip()
    if not start_iso or not end_iso:
        return JSONResponse({"ok": False, "error": "missing_slot"}, status_code=400)
    svc = VisiteRequestService(settings)
    try:
        res = svc.accept(request_id=str(payload.get("r") or ""), start_iso=start_iso, end_iso=end_iso)
    except Exception:
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    return JSONResponse(res)


def _expired() -> str:
    return ("<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Lien expiré</title></head><body style='margin:0;background:#f4f3f0;"
            "font-family:system-ui,sans-serif;color:#181a1c'>"
            "<div style='max-width:460px;margin:60px auto;padding:0 20px;text-align:center'>"
            "<div style='font-size:40px'>⏳</div>"
            "<h1 style='font-size:22px'>Ce lien n'est plus valide</h1>"
            "<p style='color:#8b9197'>La demande a peut-être déjà été traitée. "
            "Retrouvez-la dans votre application Hektor.</p></div></body></html>")
