from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_authenticated_user, require_request_user
from ..models import EstimationRedactionPayload, RedacteurAnnoncePayload, RedacteurDecisionPayload, ScanAnnonceSheetPayload
from ..services.openai_listing_sheet_service import OpenAIListingSheetService
from ..services.openai_listing_writer_service import OpenAIListingWriterService
from ..services.supabase_admin import SupabaseAdminService
from ..settings import Settings, get_settings


router = APIRouter(prefix="/annonces", tags=["annonces"])

# Tarifs gpt-4.1-mini (USD / 1M tokens), pour l'estimation de cout du run.
_REDACTEUR_PRICE_IN = 0.40 / 1_000_000
_REDACTEUR_PRICE_OUT = 1.60 / 1_000_000


def get_admin_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


def get_listing_sheet_service(settings: Settings = Depends(get_settings)) -> OpenAIListingSheetService:
    return OpenAIListingSheetService(settings)


def get_listing_writer_service(settings: Settings = Depends(get_settings)) -> OpenAIListingWriterService:
    return OpenAIListingWriterService(settings)


def _estimate_cost_usd(usage: dict) -> float | None:
    in_tok = usage.get("input_tokens")
    out_tok = usage.get("output_tokens")
    if not isinstance(in_tok, (int, float)) or not isinstance(out_tok, (int, float)):
        return None
    return round(in_tok * _REDACTEUR_PRICE_IN + out_tok * _REDACTEUR_PRICE_OUT, 5)


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


@router.post("/redacteur")
def redacteur_generate(
    payload: RedacteurAnnoncePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    writer_service: OpenAIListingWriterService = Depends(get_listing_writer_service),
):
    # Agent "Redacteur d'annonce" (propose-only) : genere une proposition de titre,
    # description et points forts. N'ecrit RIEN sur l'annonce : l'humain valide.
    user = get_authenticated_user(settings, authorization)
    profile = admin_service.load_profile(user)
    role = str(profile.get("role") or "")
    if role not in {"admin", "manager", "commercial"} or profile.get("is_active") is not True:
        raise HTTPException(status_code=403, detail="Acces redacteur refuse")

    proposal = writer_service.generate(
        payload.propertyData or {},
        photo_urls=payload.photoUrls or [],
        custom_intro=payload.customIntro,
    )
    usage = proposal.get("usage") or {}
    run_id = admin_service.insert_agent_run(
        {
            "agent_key": "redacteur",
            "app_dossier_id": payload.appDossierId,
            "hektor_annonce_id": payload.hektorAnnonceId,
            "negociateur_email": (user.email or "").strip().lower() or None,
            "status": "proposed",
            "model": proposal.get("model"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "cost_usd": _estimate_cost_usd(usage),
            "proposal_json": {
                "title": proposal.get("title"),
                "accroche": proposal.get("accroche"),
                "description": proposal.get("description"),
                "highlights": proposal.get("highlights"),
            },
        }
    )
    return {
        "ok": True,
        "runId": run_id,
        "title": proposal.get("title"),
        "accroche": proposal.get("accroche"),
        "description": proposal.get("description"),
        "highlights": proposal.get("highlights"),
        "model": proposal.get("model"),
        "usage": usage,
        "costUsd": _estimate_cost_usd(usage),
    }


@router.post("/redacteur/decision")
def redacteur_decision(
    payload: RedacteurDecisionPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
):
    # Trace la decision humaine (accepte / rejete) sur une proposition. Analytics
    # uniquement : ne declenche AUCUNE ecriture sur l'annonce (propose-only).
    user = get_authenticated_user(settings, authorization)
    profile = admin_service.load_profile(user)
    role = str(profile.get("role") or "")
    if role not in {"admin", "manager", "commercial"} or profile.get("is_active") is not True:
        raise HTTPException(status_code=403, detail="Acces redacteur refuse")

    patch: dict = {
        "status": payload.status,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    if payload.status == "accepted":
        patch["outcome_json"] = {
            "title": payload.finalTitle,
            "description": payload.finalDescription,
        }
    recorded = admin_service.update_agent_run_decision(payload.runId, patch)
    # Ne jamais renvoyer ok:false (le client HTTP leve sur ok:false) : la trace
    # est best-effort, son echec ne doit pas casser le flux UI.
    return {"ok": True, "recorded": recorded}


@router.post("/estimation-redaction")
def estimation_redaction(
    payload: EstimationRedactionPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    writer_service: OpenAIListingWriterService = Depends(get_listing_writer_service),
):
    # Agent "Avis de valeur" (propose-only) : ameliore les textes d'estimation issus
    # de la fiche manuscrite. N'ecrit RIEN : renvoie des propositions, l'humain valide.
    user = get_authenticated_user(settings, authorization)
    profile = admin_service.load_profile(user)
    role = str(profile.get("role") or "")
    if role not in {"admin", "manager", "commercial"} or profile.get("is_active") is not True:
        raise HTTPException(status_code=403, detail="Acces redacteur refuse")

    result = writer_service.polish_estimation(payload.texts or {}, payload.propertyData or {})
    usage = result.get("usage") or {}
    run_id = admin_service.insert_agent_run(
        {
            "agent_key": "avis_valeur",
            "app_dossier_id": payload.appDossierId,
            "hektor_annonce_id": payload.hektorAnnonceId,
            "negociateur_email": (user.email or "").strip().lower() or None,
            "status": "proposed",
            "model": result.get("model"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "cost_usd": _estimate_cost_usd(usage),
            "proposal_json": {
                "appreciationEtat": result.get("appreciationEtat"),
                "pointsForts": result.get("pointsForts"),
                "pointsVigilance": result.get("pointsVigilance"),
                "argumentairePrix": result.get("argumentairePrix"),
                "avisConseiller": result.get("avisConseiller"),
            },
        }
    )
    return {
        "ok": True,
        "runId": run_id,
        "appreciationEtat": result.get("appreciationEtat"),
        "pointsForts": result.get("pointsForts"),
        "pointsVigilance": result.get("pointsVigilance"),
        "argumentairePrix": result.get("argumentairePrix"),
        "avisConseiller": result.get("avisConseiller"),
        "model": result.get("model"),
        "usage": usage,
        "costUsd": _estimate_cost_usd(usage),
    }
