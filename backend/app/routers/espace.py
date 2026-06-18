"""Router de l'espace client.

Deux formes de lien magique (sans login) :
- ESPACE (lié à un envoi)    : GET /espace/{token} → les biens de cet email.
- ESPACE_CONTACT (unifié)    : GET /espace/{token} → TOUS les biens du contact, tous négos.

Les POST (feedback ❤️/✕, message, recherche) sont communs : pour un token contact, on
résout l'envoi concerné (celui qui a proposé le bien, ou le plus récent) afin de tracer
exactement comme avant. Aucun changement de schéma : modèle additif.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ..services import email_tokens
from ..services.email_tracking import EmailTrackingService, is_real_envoi_id
from ..services.espace_client import EspaceClientService
from ..settings import Settings, get_settings

router = APIRouter(tags=["espace"])

_ESPACE_ACTIONS = (email_tokens.ACTION_ESPACE, email_tokens.ACTION_ESPACE_CONTACT)


def _secret(settings: Settings) -> str:
    return getattr(settings, "email_tracking_secret", None) or settings.supabase_service_role_key


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _resolve_envoi_id(svc: EspaceClientService, payload: dict, *, bien_id=None) -> str | None:
    """Identifie l'envoi à tracer selon le type de token.

    - token envoi   → l'envoi du token.
    - token contact → l'envoi (le plus récent) ayant proposé ce bien ; à défaut, le plus récent.
    """
    if payload.get("a") == email_tokens.ACTION_ESPACE_CONTACT:
        cid = str(payload.get("c") or "")
        if bien_id is not None:
            eid = svc.envoi_for_contact_bien(cid, bien_id)
            if eid:
                return eid
        return svc.latest_envoi_id_for_contact(cid)
    return str(payload.get("e") or "") or None


@router.get("/espace/{token}", response_class=HTMLResponse)
def espace_page(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    svc = EspaceClientService(settings)
    if not payload or payload.get("a") not in _ESPACE_ACTIONS:
        return HTMLResponse(svc._page_message("Lien expiré", "Ce lien n'est plus valide. Contactez votre conseiller."),
                            status_code=410)
    # Ouvrir l'espace = signal d'engagement fort → on l'enregistre comme une ouverture.
    open_envoi = _resolve_envoi_id(svc, payload)
    if open_envoi:
        try:
            EmailTrackingService(settings).record_event(
                envoi_id=open_envoi, action=email_tokens.ACTION_OPEN,
                ip=_client_ip(request), user_agent=request.headers.get("user-agent"))
        except Exception:
            pass
    if payload.get("a") == email_tokens.ACTION_ESPACE_CONTACT:
        featured = payload.get("f")
        from_email = (request.query_params.get("from") or "").lower() == "email"
        return HTMLResponse(svc.render_contact_portal(
            hektor_contact_id=str(payload.get("c") or ""), token=token,
            featured_dossier_id=int(featured) if str(featured or "").isdigit() else None,
            from_email=from_email))
    return HTMLResponse(svc.render_page(envoi_id=str(payload.get("e") or ""), token=token))


@router.post("/espace/{token}/feedback")
async def espace_feedback(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") not in _ESPACE_ACTIONS:
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    try:
        body = await request.json()
    except Exception:
        body = {}
    action = str(body.get("action") or "")
    bien_id = body.get("bien_id")
    reason = body.get("reason")
    if action not in (email_tokens.ACTION_LIKE, email_tokens.ACTION_PASS):
        return JSONResponse({"ok": False, "error": "bad_action"}, status_code=400)

    svc = EspaceClientService(settings)
    tracking = EmailTrackingService(settings)
    envoi_id = _resolve_envoi_id(svc, payload, bien_id=bien_id)
    if not envoi_id:
        return JSONResponse({"ok": False, "error": "not_owned"}, status_code=403)
    # Vérifie que le bien fait bien partie de cet envoi (cloisonnement).
    if is_real_envoi_id(envoi_id) and bien_id is not None:
        owned = tracking._get("app_email_envoi_bien",
                              {"select": "app_dossier_id", "envoi_id": f"eq.{envoi_id}",
                               "app_dossier_id": f"eq.{bien_id}", "limit": "1"})
        if not owned:
            return JSONResponse({"ok": False, "error": "not_owned"}, status_code=403)
    clean_reason = str(reason)[:60] if reason else None
    try:
        tracking.record_event(envoi_id=envoi_id, action=action, bien_id=bien_id, ip=_client_ip(request),
                              reason=clean_reason)
    except Exception:
        pass
    # Requalification guidée : raison du ✕ → piste pour le négociateur (sûr, pas d'écriture CRM).
    if action == email_tokens.ACTION_PASS and clean_reason:
        try:
            envoi = tracking._envoi(envoi_id)
            if envoi:
                svc.record_requalif_hint(envoi=envoi, bien_id=bien_id, reason=clean_reason)
        except Exception:
            pass
    return JSONResponse({"ok": True})


@router.post("/espace/{token}/message")
async def espace_message(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") not in _ESPACE_ACTIONS:
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = str((body or {}).get("text") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    svc = EspaceClientService(settings)
    bien_id = (body or {}).get("bien_id")
    envoi_id = _resolve_envoi_id(svc, payload, bien_id=bien_id)
    if not envoi_id:
        return JSONResponse({"ok": False, "error": "no_envoi"}, status_code=403)
    try:
        res = svc.submit_message(envoi_id=envoi_id, message=text, bien_id=bien_id)
    except Exception:
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    return JSONResponse(res)


@router.post("/espace/{token}/visite")
async def espace_visite(token: str, request: Request, settings: Settings = Depends(get_settings)):
    """Demande de visite (option A) : notifie le négociateur du mandat (cloche app + email).
    Ne touche pas l'agenda Google, n'utilise pas la vitrine simulée."""
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") not in _ESPACE_ACTIONS:
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    try:
        body = await request.json()
    except Exception:
        body = {}
    bien_id = (body or {}).get("bien_id")
    svc = EspaceClientService(settings)
    envoi_id = _resolve_envoi_id(svc, payload, bien_id=bien_id)
    if not envoi_id:
        return JSONResponse({"ok": False, "error": "no_envoi"}, status_code=403)
    try:
        res = svc.submit_visite_request(
            envoi_id=envoi_id, bien_id=bien_id,
            days=(body or {}).get("days"), periods=(body or {}).get("periods"),
            message=(body or {}).get("message"), phone=(body or {}).get("phone"))
    except Exception:
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    return JSONResponse(res)


@router.post("/espace/{token}/recherche")
async def espace_recherche(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") not in _ESPACE_ACTIONS:
        return JSONResponse({"ok": False, "error": "invalid_token"}, status_code=410)
    try:
        edits = await request.json()
    except Exception:
        edits = {}
    if not isinstance(edits, dict):
        edits = {}
    svc = EspaceClientService(settings)
    envoi_id = _resolve_envoi_id(svc, payload)  # recherche = niveau contact → envoi le plus récent
    if not envoi_id:
        return JSONResponse({"ok": False, "error": "no_envoi"}, status_code=403)
    try:
        res = svc.submit_search_update(envoi_id=envoi_id, edits=edits)
    except Exception:
        return JSONResponse({"ok": False, "error": "server"}, status_code=500)
    return JSONResponse(res)
