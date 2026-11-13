from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..auth import get_authenticated_user, require_request_user
from ..services.assistant_catalogue import ContexteAssistant, Refus
from ..services.assistant_gestes import GESTES
from ..services.assistant_service import AGENT_KEY, MAX_QUESTION_CARACTERES, AssistantService
from ..services.supabase_admin import SupabaseAdminService
from ..settings import Settings, get_settings
from .ged import autorise

# Assistant IA (12/11/2026, étape 1) : poser une question et recevoir la réponse EN FLUX (une ligne JSON par
# événement), lister ses conversations, en relire une. Derrière l'interrupteur `assistant_ia` (off / admin / on),
# relu à CHAQUE question. Tout ce qui peut refuser se joue AVANT le flux (vrai code HTTP) ; la question est écrite
# avant l'appel à l'IA : une saisie ne se perd jamais. Note : notice/ETAPE1_SOCLE_ASSISTANT_IA_2026-11-12.md.

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantMessagePayload(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CARACTERES)
    conversationId: str | None = Field(default=None, min_length=36, max_length=36)


def get_admin_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


def get_assistant_service(settings: Settings = Depends(get_settings)) -> AssistantService:
    return AssistantService(settings)


def _jeton(authorization: str | None) -> str:
    return str(authorization or "").split(" ", 1)[-1].strip()


def _ouvrir(settings: Settings, authorization: str | None, admin_service: SupabaseAdminService,
            service: AssistantService) -> tuple[Any, dict[str, Any]]:
    user = get_authenticated_user(settings, authorization)
    profile = admin_service.load_profile(user)
    if not autorise(service.interrupteur(), str(profile.get("role") or ""), profile.get("is_active") is True):
        raise HTTPException(status_code=403, detail="Assistant IA éteint pour ce compte")
    return user, profile


@router.post("/message")
def assistant_message(
    payload: AssistantMessagePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    t0 = time.monotonic()  # étape 2 : les durées du tour vont au journal (sans texte)
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    email = (user.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=403, detail="Compte sans adresse e-mail : plafond impossible à compter")
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")
    spec = service.preparer(email)

    if payload.conversationId:
        conv = service.conversation(payload.conversationId)
        # même l'admin, qui RELIT les conversations des autres, n'écrit pas dans celles des autres
        if not conv or str(conv.get("user_id") or "") != str(user.id):
            raise HTTPException(status_code=404, detail="Conversation introuvable")
        conversation_id = str(conv["id"])
        historique = service.historique(conversation_id)
    else:
        conversation_id = service.creer_conversation(str(user.id), email, question[:80])
        historique = []
    service.ajouter_message(conversation_id, "user", question)

    ctx = ContexteAssistant(settings=settings, user_id=str(user.id), email=email,
                            role=str(profile.get("role") or ""), jeton=_jeton(authorization),
                            conversation_id=conversation_id, nom=profile.get("display_name") or None)
    durees = {"preparation": round((time.monotonic() - t0) * 1000)}
    return StreamingResponse(_flux(service, admin_service, ctx, spec, conversation_id, historique, question, t0, durees),
                             media_type="application/x-ndjson")


async def _flux(service: AssistantService, admin_service: SupabaseAdminService, ctx: ContexteAssistant, spec: Any,
                conversation_id: str, historique: list[dict[str, Any]], question: str,
                t0: float, durees: dict[str, int]) -> AsyncIterator[str]:
    def ligne(evenement: dict[str, Any]) -> str:
        return json.dumps(evenement, ensure_ascii=False) + "\n"

    yield ligne({"type": "debut", "conversationId": conversation_id})
    fin: dict[str, Any] | None = None
    try:
        async for evenement in service.repondre(ctx, spec, historique, question):
            if evenement["type"] == "_fin":
                fin = evenement
            else:
                if evenement["type"] == "texte" and "premier_mot" not in durees:
                    durees["premier_mot"] = round((time.monotonic() - t0) * 1000)
                yield ligne(evenement)
    except BaseException as exc:  # noqa: BLE001 -- y compris l'onglet fermé en cours de route (annulation)
        nom = type(exc).__name__
        durees["total"] = round((time.monotonic() - t0) * 1000)
        _tracer(admin_service, _ligne_journal(ctx, spec, conversation_id, question, None, durees, status="error",
                                              error_text=nom if nom in {"CancelledError", "GeneratorExit"} else f"{nom}: {exc}"[:2000]))
        if isinstance(exc, (asyncio.CancelledError, GeneratorExit, KeyboardInterrupt, SystemExit)):
            raise
        detail = "Trop d'étapes pour cette question : reformule-la plus simplement" if nom == "MaxTurnsExceeded" \
            else "L'assistant n'a pas pu répondre"
        yield ligne({"type": "erreur", "detail": detail})
        return

    durees["total"] = round((time.monotonic() - t0) * 1000)
    run_id = await asyncio.to_thread(_tracer, admin_service,
                                     _ligne_journal(ctx, spec, conversation_id, question, fin, durees, status="proposed"))
    try:
        message_id = await asyncio.to_thread(service.ajouter_message, conversation_id, "assistant", fin["reponse"],
                                             ctx.appels or None, run_id)
    except HTTPException:
        message_id = None  # la réponse est affichée ; seul l'enregistrement a raté, on le dit
    yield ligne({"type": "fin", "messageId": message_id, "costUsd": fin.get("costUsd"),
                 "enregistre": message_id is not None})


def _ligne_journal(ctx: ContexteAssistant, spec: Any, conversation_id: str, question: str,
                   fin: dict[str, Any] | None, durees: dict[str, int] | None = None, *, status: str,
                   error_text: str | None = None) -> dict[str, Any]:
    # ⛔ JAMAIS le texte : ni la question, ni la réponse, ni les paramètres des fonctions (ils sont dans le fil).
    usage = (fin or {}).get("usage") or {}
    ligne: dict[str, Any] = {
        "agent_key": AGENT_KEY,
        "negociateur_email": ctx.email,
        "status": status,
        "model": getattr(spec, "model", None),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cost_usd": (fin or {}).get("costUsd"),
        "proposal_json": {
            "conversation_id": conversation_id,
            "fonctions": [a.get("nom") for a in ctx.appels],
            "fonctions_en_erreur": [a.get("nom") for a in ctx.appels if a.get("erreur")],
            "etapes": (fin or {}).get("etapes"),
            "question_caracteres": len(question),
            "reponse_caracteres": len((fin or {}).get("reponse") or ""),
            "durees_ms": durees or {},
            "jetons_en_cache": usage.get("cached_tokens"),
        },
    }
    if error_text:
        ligne["error_text"] = error_text
    return ligne


def _tracer(admin_service: SupabaseAdminService, ligne: dict[str, Any]) -> int | None:
    # Best-effort : une trace ratée ne doit jamais faire perdre la réponse à l'écran.
    try:
        return admin_service.insert_agent_run(ligne)
    except Exception:
        return None


@router.get("/conversations")
def assistant_conversations(
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    user, _profile = _ouvrir(settings, authorization, admin_service, service)
    return {"ok": True, "conversations": service.lister(_jeton(authorization), str(user.id))}


@router.get("/conversations/{conversation_id}")
def assistant_conversation(
    conversation_id: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    _ouvrir(settings, authorization, admin_service, service)
    if len(conversation_id) != 36:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    conversation = service.relire(_jeton(authorization), conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return {"ok": True, "conversation": conversation}


# ── étape 3 (13/11/2026) : les cartes de validation ──────────────────────────
# ⛔ Le geste ne s'exécute QU'ICI, au clic de la personne qui l'a demandé, une seule fois, avant expiration, avec
#   SON jeton, par la même écriture que l'écran (assistant_gestes). Notes : notice/ETAPE3_*_2026-11-13.md.
def _carte_a_moi(service: AssistantService, action_id: str, user_id: str) -> dict[str, Any]:
    if len(action_id) != 36:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    carte = service.carte(action_id)
    if not carte or str(carte.get("user_id") or "") != user_id:
        # même l'admin, qui relit les cartes des autres, ne valide pas à leur place
        raise HTTPException(status_code=404, detail="Carte introuvable")
    return carte


def _pourquoi_pas(carte: dict[str, Any]) -> str:
    etat = carte.get("etat")
    if etat == "proposee":
        return "Carte expirée (30 minutes) : redemande-la à l'assistant. Rien n'a été fait."
    return {"executee": "Cette carte a déjà été validée.", "en_cours": "Cette carte est déjà en cours.",
            "refusee": "Cette carte a été refusée.", "echec": "Cette carte a déjà échoué.",
            "expiree": "Carte expirée : redemande-la à l'assistant."}.get(str(etat), "Carte indisponible.")


@router.post("/actions/{action_id}/valider")
def assistant_valider(
    action_id: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    carte = _carte_a_moi(service, action_id, str(user.id))
    geste = GESTES.get(str(carte.get("geste") or ""))
    role = str(profile.get("role") or "")
    if not geste or role not in geste.roles:
        raise HTTPException(status_code=403, detail="Ce geste n'est pas ouvert à ton rôle")
    if not service.prendre_carte(action_id, str(user.id), "en_cours"):
        if carte.get("etat") == "proposee":
            service.terminer_carte(action_id, "expiree", {"raison": "clic après expiration"})
        raise HTTPException(status_code=409, detail=_pourquoi_pas(carte))
    ctx = ContexteAssistant(settings=settings, user_id=str(user.id), email=(user.email or "").strip().lower(), role=role,
                            jeton=_jeton(authorization), conversation_id=carte.get("conversation_id"),
                            nom=profile.get("display_name") or None)
    try:
        resultat = geste.executer(ctx, dict(carte.get("parametres") or {}))
    except Refus as exc:
        service.terminer_carte(action_id, "echec", {"raison": str(exc)})
        return {"ok": False, "etat": "echec", "detail": f"Non fait : {exc}"}
    except Exception as exc:  # noqa: BLE001 -- la personne reçoit une phrase ; le détail va au journal de la carte
        service.terminer_carte(action_id, "echec", {"raison": f"{type(exc).__name__}"})
        return {"ok": False, "etat": "echec", "detail": "Non fait : l'écriture n'a pas abouti."}
    service.terminer_carte(action_id, "executee", resultat)
    return {"ok": True, "etat": "executee", "resultat": resultat}


@router.post("/actions/{action_id}/refuser")
def assistant_refuser(
    action_id: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    user, _profile = _ouvrir(settings, authorization, admin_service, service)
    carte = _carte_a_moi(service, action_id, str(user.id))
    if not service.prendre_carte(action_id, str(user.id), "refusee"):
        raise HTTPException(status_code=409, detail=_pourquoi_pas(carte))
    return {"ok": True, "etat": "refusee"}


@router.get("/conversations/{conversation_id}/actions")
def assistant_cartes(
    conversation_id: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    _ouvrir(settings, authorization, admin_service, service)
    if len(conversation_id) != 36:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return {"ok": True, "actions": service.lister_cartes(_jeton(authorization), conversation_id)}
