"""Router email de rapprochement (Lot A + Lot B).

- GET  /emails/rapprochement/preview : rendu du template sans envoi (interne, authentifié).
- POST /emails/rapprochement/send    : envoi DRY-RUN (filtre opt-out + crée l'envoi +
                                       en-têtes List-Unsubscribe). Jamais d'envoi réel ici.
- Landing publique des boutons trackés, désormais persistée (Lot B) :
    GET /r/feedback/{token}  (❤️/✕)  -> app_email_event + feedback bien + statut + score
    GET /r/o/{token}.png     (pixel) -> événement d'ouverture (signal faible)
    GET /r/u/{token}         (unsub) -> opt-out app_contact_consent

Les tokens « preview » (id non-uuid) ne déclenchent aucune écriture : preview/dry-run sûr.
"""

from __future__ import annotations

import base64
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, Field

from ..auth import get_authenticated_user, require_request_user
from ..services import email_tokens
from ..services.email_tracking import EmailTrackingService
from ..services.estimation_email import render_estimation_email
from ..services.estimation_sender import EstimationSender
from ..services.rapprochement_email import BRAND, RapprochementEmailService
from ..services.rapprochement_sender import RapprochementSender
from ..services.supabase_storage import signed_url_for_estimation_pdf
from ..settings import Settings, get_settings

router = APIRouter(tags=["emails"])


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None

# GIF transparent 1x1 (pixel d'ouverture).
_PIXEL_GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


def _secret(settings: Settings) -> str:
    return getattr(settings, "email_tracking_secret", None) or settings.supabase_service_role_key


def _page(title: str, message: str, *, accent: str = BRAND["magenta"]) -> str:
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title></head>
<body style="margin:0;background:{BRAND['bg']};font-family:Arial,Helvetica,sans-serif">
<table role="presentation" width="100%" height="100%" cellpadding="0" cellspacing="0"><tr>
<td align="center" valign="middle" style="padding:40px 16px">
  <table role="presentation" width="440" style="max-width:440px;background:#fff;border-radius:14px;padding:32px 28px;text-align:center">
    <tr><td>
      <img src="https://www.gti-immobilier.fr/images/logoSite.png" width="120" alt="Groupe GTI" style="display:inline-block;border:0;height:auto">
      <div style="height:4px;width:48px;background:{accent};border-radius:2px;margin:18px auto"></div>
      <h1 style="color:{BRAND['ink']};font-size:20px;margin:0 0 10px">{title}</h1>
      <p style="color:{BRAND['ink_mute']};font-size:15px;line-height:1.55;margin:0">{message}</p>
    </td></tr>
  </table>
</td></tr></table></body></html>"""


@router.get("/emails/rapprochement/preview", response_class=HTMLResponse)
def preview_rapprochement_email(
    annonce_ids: str = Query(..., description="Liste d'IDs d'annonce Hektor séparés par des virgules"),
    variante: str = Query("push", pattern="^(push|pull)$"),
    prenom: str | None = None,
    civilite: str | None = None,
    criteres: str | None = Query(None, description="Texte d'accroche critères, ex. 'votre recherche maison · Firminy · 80 000 €'"),
    custom_intro: str | None = Query(None, description="Mot personnel du négociateur, inséré en intro (mode hybride)"),
    format: str = Query("html", pattern="^(html|text)$"),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    get_authenticated_user(settings, authorization)  # 401 si non authentifié (preview = interne)
    ids = [int(x) for x in (annonce_ids or "").replace(" ", "").split(",") if x.strip().isdigit()]
    result = RapprochementEmailService(settings).render_preview(
        annonce_ids=ids, variante=variante, prenom=prenom, civilite=civilite, criteres=criteres,
        custom_intro=custom_intro,
    )
    if format == "text":
        return Response(content=result["text"], media_type="text/plain; charset=utf-8")
    return HTMLResponse(content=result["html"])


_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


@router.get("/assets/gti-mark.png")
def gti_mark():
    """Sert le cube GTI (logo email), public, mis en cache 30 jours."""
    return FileResponse(_ASSETS_DIR / "gti-mark.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=2592000"})


@router.get("/assets/gti-brand-mark.png")
def gti_brand_mark():
    """Marque GTI (cube magenta, logo officiel) servie pour l'espace client."""
    return FileResponse(_ASSETS_DIR / "gti-brand-mark.png", media_type="image/png",
                        headers={"Cache-Control": "public, max-age=2592000"})


@router.get("/r/o/{token}.png")
def track_open(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if payload and payload.get("a") == email_tokens.ACTION_OPEN:
        try:
            EmailTrackingService(settings).record_event(
                envoi_id=str(payload.get("e") or ""), action=email_tokens.ACTION_OPEN,
                ip=_client_ip(request), user_agent=request.headers.get("user-agent"))
        except Exception:
            pass  # le pixel ne doit jamais casser le rendu de l'email
    return Response(content=_PIXEL_GIF, media_type="image/gif",
                    headers={"Cache-Control": "no-store, no-cache, must-revalidate, private"})


@router.get("/r/feedback/{token}", response_class=HTMLResponse)
def track_feedback(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload:
        return HTMLResponse(_page("Lien expiré", "Ce lien n'est plus valide. Contactez votre conseiller Groupe GTI."), status_code=410)
    action = payload.get("a")
    try:
        EmailTrackingService(settings).record_event(
            envoi_id=str(payload.get("e") or ""), action=str(action), bien_id=payload.get("b"),
            ip=_client_ip(request), user_agent=request.headers.get("user-agent"))
    except Exception:
        pass  # on confirme à l'utilisateur même si la persistance échoue
    if action == email_tokens.ACTION_LIKE:
        # Lot D : redirigera (302) vers l'espace client du bien. En attendant, page d'attente honnête.
        return HTMLResponse(_page("Votre espace arrive",
                                  "Nous préparons votre espace personnel : photos, détails complets du bien, "
                                  "prise de rendez-vous et mise à jour de votre recherche. "
                                  "Votre conseiller vous recontacte très vite."))
    if action == email_tokens.ACTION_PASS:
        return HTMLResponse(_page("Merci pour votre retour", "Ce bien ne vous correspond pas : nous affinerons nos prochaines propositions.", accent=BRAND["neutral_400"]))
    return HTMLResponse(_page("Merci", "Votre réponse a bien été prise en compte."))


@router.get("/r/download/{token}")
def download_estimation(token: str, request: Request, settings: Settings = Depends(get_settings)):
    """Téléchargement de l'avis de valeur : log le clic (signal fort) puis redirige (302)
    vers l'URL signée du PDF archivé. Token 'estim' porte l'envoi + l'app_dossier_id."""
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload or payload.get("a") != email_tokens.ACTION_ESTIMATION:
        return HTMLResponse(_page("Lien expiré", "Ce lien de téléchargement n'est plus valide. Contactez votre conseiller Groupe GTI."), status_code=410)
    try:
        EmailTrackingService(settings).record_event(
            envoi_id=str(payload.get("e") or ""), action=email_tokens.ACTION_ESTIMATION,
            ip=_client_ip(request), user_agent=request.headers.get("user-agent"))
    except Exception:
        pass  # le tracking ne doit jamais empêcher le téléchargement
    app_dossier_id = payload.get("d")
    signed = None
    if app_dossier_id:
        try:
            signed = signed_url_for_estimation_pdf(settings, int(app_dossier_id))
        except Exception:
            signed = None
    if signed:
        return RedirectResponse(url=signed, status_code=302)
    return HTMLResponse(_page("Estimation indisponible",
                              "Votre estimation n'est pas encore disponible. Votre conseiller Groupe GTI vous l'envoie très vite."),
                        status_code=404)


@router.get("/r/u/{token}", response_class=HTMLResponse)
def unsubscribe(token: str, request: Request, settings: Settings = Depends(get_settings)):
    payload = email_tokens.verify_token(token, _secret(settings))
    if not payload:
        return HTMLResponse(_page("Lien invalide", "Ce lien de désinscription n'est plus valide."), status_code=410)
    try:
        EmailTrackingService(settings).record_event(
            envoi_id=str(payload.get("e") or ""), action=email_tokens.ACTION_UNSUB, ip=_client_ip(request))
    except Exception:
        pass
    return HTMLResponse(_page("Désinscription enregistrée",
                              "Vous ne recevrez plus d'emails de proposition de biens. "
                              "Cette préférence est désormais enregistrée.",
                              accent=BRAND["neutral_400"]))


# --- Envoi (DRY-RUN strict — aucun envoi réel tant que DKIM/DMARC non confirmés) ----
class RapprochementSendPayload(BaseModel):
    recipient_email: str
    annonce_ids: list[int] = Field(..., min_length=1)
    sender_email: str
    variante: str = "push"
    contact_search_key: str | None = None
    hektor_contact_id: str | None = None
    prenom: str | None = None
    civilite: str | None = None
    criteres: str | None = None
    custom_intro: str | None = None  # mot libre du négociateur (hybride), inséré en intro
    dry_run: bool = True  # réel uniquement si dry_run=false ET EMAIL_REAL_SEND_ENABLED=true
    group_by_nego: bool = False  # True (côté acquéreur) : 1 email par négociateur de mandat


@router.post("/emails/rapprochement/send")
def send_rapprochement_email(
    payload: RapprochementSendPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Chokepoint d'envoi (manuel). Filtre opt-out -> plafond quotidien -> crée l'envoi ->
    template avec id d'envoi réel -> en-têtes List-Unsubscribe -> envoi réel ou dry-run.
    L'envoi réel n'a lieu que si EMAIL_REAL_SEND_ENABLED=true et payload.dry_run=false.

    Si group_by_nego=true : on ne garde que les biens frais, on les regroupe par
    négociateur du mandat, et on envoie 1 email par négociateur depuis SA boîte (send-as)."""
    user = get_authenticated_user(settings, authorization)
    sender = RapprochementSender(settings)
    if payload.group_by_nego:
        return sender.send_grouped(
            recipient_email=payload.recipient_email, annonce_ids=payload.annonce_ids,
            variante=payload.variante, contact_search_key=payload.contact_search_key,
            hektor_contact_id=payload.hektor_contact_id, prenom=payload.prenom,
            civilite=payload.civilite, criteres=payload.criteres,
            custom_intro=payload.custom_intro, dry_run=payload.dry_run, created_by=user.id,
            fallback_sender_email=payload.sender_email,
        )
    return sender.send(
        recipient_email=payload.recipient_email, sender_email=payload.sender_email,
        annonce_ids=payload.annonce_ids, variante=payload.variante,
        contact_search_key=payload.contact_search_key, hektor_contact_id=payload.hektor_contact_id,
        prenom=payload.prenom, civilite=payload.civilite, criteres=payload.criteres,
        custom_intro=payload.custom_intro, dry_run=payload.dry_run, created_by=user.id,
    )


# --- Email estimation (Lot 2) : « votre estimation est disponible » + bouton PDF ----
class EstimationSendPayload(BaseModel):
    recipient_email: str
    app_dossier_id: int
    sender_email: str
    bien: dict = Field(default_factory=dict)
    valeurs: dict = Field(default_factory=dict)
    proprietaire_nom: str | None = None
    negociateur: dict | None = None
    prenom: str | None = None
    civilite: str | None = None
    custom_intro: str | None = None
    intro_variante: str | None = None  # 'vente' | 'succession' (ton de l'intro)
    hektor_contact_id: str | None = None
    dry_run: bool = True  # réel uniquement si dry_run=false ET EMAIL_REAL_SEND_ENABLED=true


@router.get("/emails/estimation/preview", response_class=HTMLResponse)
def preview_estimation_email(
    app_dossier_id: int = Query(...),
    titre: str | None = None,
    type: str | None = None,
    ville: str | None = None,
    code_postal: str | None = None,
    surface: float | None = None,
    pieces: int | None = None,
    proprietaire: str | None = None,
    nego: str | None = None,
    agence: str | None = None,
    variante: str | None = Query(None, description="'vente' | 'succession' (ton de l'intro)"),
    format: str = Query("html", pattern="^(html|text)$"),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    get_authenticated_user(settings, authorization)  # 401 si non authentifié (preview interne)
    result = render_estimation_email(
        settings=settings, envoi_id="preview", app_dossier_id=app_dossier_id,
        bien={"titre": titre, "type": type, "ville": ville, "code_postal": code_postal,
              "surface": surface, "pieces": pieces},
        valeurs={},
        proprietaire_nom=proprietaire, negociateur={"nom": nego, "agence": agence},
        variante=variante,
    )
    if format == "text":
        return Response(content=result["text"], media_type="text/plain; charset=utf-8")
    return HTMLResponse(content=result["html"])


@router.post("/emails/estimation/send")
def send_estimation_email(
    payload: EstimationSendPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Chokepoint d'envoi de l'email estimation (dry-run par défaut). Filtre opt-out ->
    plafond -> crée l'envoi -> rend l'email (liens pixel + download trackés) -> envoi
    réel ou dry-run. Réel seulement si EMAIL_REAL_SEND_ENABLED=true et dry_run=false."""
    user = get_authenticated_user(settings, authorization)
    return EstimationSender(settings).send(
        recipient_email=payload.recipient_email, sender_email=payload.sender_email,
        app_dossier_id=payload.app_dossier_id, bien=payload.bien, valeurs=payload.valeurs,
        proprietaire_nom=payload.proprietaire_nom, negociateur=payload.negociateur,
        prenom=payload.prenom, civilite=payload.civilite, custom_intro=payload.custom_intro,
        intro_variante=payload.intro_variante,
        hektor_contact_id=payload.hektor_contact_id, dry_run=payload.dry_run, created_by=user.id,
    )


@router.get("/emails/rapprochement/tracking")
def get_email_tracking(
    contact_search_key: str | None = None,
    hektor_contact_id: str | None = None,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Expose le suivi (statut + score chaud/tiède/froid + compteurs) pour l'écran de rapprochement."""
    get_authenticated_user(settings, authorization)
    if not contact_search_key and not hektor_contact_id:
        return {"ok": False, "detail": "contact_search_key ou hektor_contact_id requis"}
    tracking = EmailTrackingService(settings)
    params = {"select": "id,recipient_email,variante,statut,score,open_count,click_count,"
                        "sent_at,rdv_at,unsubscribed_at,relances_count,dry_run,created_at",
              "order": "created_at.desc", "limit": "50"}
    if contact_search_key:
        params["contact_search_key"] = f"eq.{contact_search_key}"
    if hektor_contact_id:
        params["hektor_contact_id"] = f"eq.{hektor_contact_id}"
    envois = tracking._get("app_email_envoi", params)
    for e in envois:
        e["biens"] = tracking._get("app_email_envoi_bien",
                                   {"select": "app_dossier_id,feedback,feedback_at", "envoi_id": f"eq.{e['id']}"})
    return {"ok": True, "envois": envois}


@router.get("/emails/rapprochement/stats")
def get_send_stats(
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
):
    """Volume d'envois réels du jour vs plafond/alerte (garde-fou anti-spam)."""
    get_authenticated_user(settings, authorization)
    count = EmailTrackingService(settings).count_real_sends_today()
    return {
        "ok": True, "today": count,
        "alertThreshold": settings.email_daily_send_alert, "cap": settings.email_daily_send_cap,
        "alert": count >= settings.email_daily_send_alert, "capReached": count >= settings.email_daily_send_cap,
        "realSendEnabled": settings.email_real_send_enabled,
    }
