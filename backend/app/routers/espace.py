"""Router de l'espace client (Étape 1).

- GET  /espace/{token}           : page publique (lien magique) affichant le(s) bien(s).
- POST /espace/{token}/feedback  : enregistre ❤️/✕ depuis la page (relié au tracking).

Aucun login. Le token (action 'espace') autorise l'accès à l'envoi correspondant.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ..services import email_tokens
from ..services.email_tracking import EmailTrackingService, is_real_envoi_id
from ..services.espace_client import EspaceClientService
from ..settings import Settings, get_settings

router = APIRouter(tags=["espace"])


def _secret(settings: Settings) -> str:
    return getattr(settings, "email_tracking_secret", None) or settings.supabase_service_role_key


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("/espace/{token}", response_class=HTMLResponse)
def espace_page(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    svc = EspaceClientService(settings)
    if not payload or payload.get("a") != email_tokens.ACTION_ESPACE:
        return HTMLResponse(svc._page_message("Lien expiré", "Ce lien n'est plus valide. Contactez votre conseiller."),
                            status_code=410)
    envoi_id = str(payload.get("e") or "")
    # Ouvrir l'espace = signal d'engagement fort -> on l'enregistre comme une ouverture.
    try:
        EmailTrackingService(settings).record_event(
            envoi_id=envoi_id, action=email_tokens.ACTION_OPEN,
            ip=_client_ip(request), user_agent=request.headers.get("user-agent"))
    except Exception:
        pass
    return HTMLResponse(svc.render_page(envoi_id=envoi_id, token=token))


@router.post("/espace/{token}/feedback")
async def espace_feedback(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") != email_tokens.ACTION_ESPACE:
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    envoi_id = str(payload.get("e") or "")
    try:
        body = await request.json()
    except Exception:
        body = {}
    action = str(body.get("action") or "")
    bien_id = body.get("bien_id")
    reason = body.get("reason")
    if action not in (email_tokens.ACTION_LIKE, email_tokens.ACTION_PASS):
        return JSONResponse({"ok": False, "error": "bad_action"}, status_code=400)

    tracking = EmailTrackingService(settings)
    # Vérifie que le bien fait bien partie de cet envoi (cloisonnement).
    if is_real_envoi_id(envoi_id) and bien_id is not None:
        owned = tracking._get("app_email_envoi_bien",
                              {"select": "app_dossier_id", "envoi_id": f"eq.{envoi_id}",
                               "app_dossier_id": f"eq.{bien_id}", "limit": "1"})
        if not owned:
            return JSONResponse({"ok": False, "error": "not_owned"}, status_code=403)
    try:
        tracking.record_event(envoi_id=envoi_id, action=action, bien_id=bien_id, ip=_client_ip(request),
                              reason=str(reason)[:60] if reason else None)
    except Exception:
        pass
    return JSONResponse({"ok": True})


@router.post("/espace/{token}/message")
async def espace_message(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") != email_tokens.ACTION_ESPACE:
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    envoi_id = str(payload.get("e") or "")
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = str((body or {}).get("text") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    try:
        res = EspaceClientService(settings).submit_message(envoi_id=envoi_id, message=text, bien_id=(body or {}).get("bien_id"))
    except Exception:
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    return JSONResponse(res)


@router.post("/espace/{token}/recherche")
async def espace_recherche(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") != email_tokens.ACTION_ESPACE:
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    envoi_id = str(payload.get("e") or "")
    try:
        edits = await request.json()
    except Exception:
        edits = {}
    if not isinstance(edits, dict):
        edits = {}
    try:
        res = EspaceClientService(settings).submit_search_update(envoi_id=envoi_id, edits=edits)
    except Exception:
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    return JSONResponse(res)
