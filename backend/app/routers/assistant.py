from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..auth import get_authenticated_user, require_request_user
from ..services import assistant_fichiers as fichiers_service
from ..services import assistant_parcours as parcours_moteur
from ..services import parcours_phrases, parcours_publics
from ..services.agent_tarifs import cout_usd
from ..services.openai_listing_sheet_service import OpenAIListingSheetService
from ..services.assistant_catalogue import ContexteAssistant, Refus
from ..services.assistant_gestes import GESTES, lire_fiche_du_parcours
from ..services.assistant_service import AGENT_KEY, AGENT_PHRASE, MAX_QUESTION_CARACTERES, PLAFOND_JOUR_USD, AssistantService
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
    # 17/11 (le trombone) : les numéros des fichiers déposés pour CETTE question ; vide = comme avant
    fichiers: list[str] = Field(default_factory=list, max_length=fichiers_service.MAX_FICHIERS)


class DepotFichierPayload(BaseModel):
    nom: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=120)
    taille: int = Field(gt=0)


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
    # 17/11 (le trombone) : chaque fichier joint est RELU au coffre (le sien, encore là, dans les règles) ; le modèle
    # n'en reçoit que le nom, le type et la taille, à la suite de la question (gardés dans l'historique).
    question_modele = question
    if payload.fichiers:
        _trombone_ouvert(service, profile)
        try:
            joints = [fichiers_service.decrire(settings, str(user.id), n) for n in dict.fromkeys(payload.fichiers)]
        except fichiers_service.RefusFichier as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from None
        question_modele = question + fichiers_service.decrire_pour_le_modele(joints)
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
    service.ajouter_message(conversation_id, "user", question_modele)

    ctx = ContexteAssistant(settings=settings, user_id=str(user.id), email=email,
                            role=str(profile.get("role") or ""), jeton=_jeton(authorization),
                            conversation_id=conversation_id, nom=profile.get("display_name") or None)
    durees = {"preparation": round((time.monotonic() - t0) * 1000)}
    return StreamingResponse(_flux(service, admin_service, ctx, spec, conversation_id, historique, question_modele, t0,
                                   durees),
                             media_type="application/x-ndjson")


# ── 17/11 : LE TROMBONE (note étape 4 §51-52) — déposer des fichiers de l'ordinateur dans la conversation ──────────
INTERRUPTEUR_FICHIERS = "assistant_fichiers"  # off / admin / on ; absent = éteint


def _trombone_ouvert(service: AssistantService, profile: dict[str, Any]) -> None:
    if not autorise(service.interrupteur(INTERRUPTEUR_FICHIERS), str(profile.get("role") or ""),
                    profile.get("is_active") is True):
        raise HTTPException(status_code=403, detail="Joindre des fichiers n'est pas encore ouvert pour ce compte")


@router.get("/fichiers/etat")
def fichiers_etat(
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    _user, profile = _ouvrir(settings, authorization, admin_service, service)
    try:
        _trombone_ouvert(service, profile)
        ouvert = True
    except HTTPException:
        ouvert = False
    return {"ouvert": ouvert, "types": sorted(fichiers_service.TYPES_ACCEPTES), "tailleMax": fichiers_service.TAILLE_MAX,
            "maxFichiers": fichiers_service.MAX_FICHIERS}


@router.post("/fichiers/preparer")
def fichiers_preparer(
    payload: DepotFichierPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _trombone_ouvert(service, profile)
    try:
        return fichiers_service.preparer_depot(settings, str(user.id), payload.nom, payload.type, payload.taille)
    except fichiers_service.RefusFichier as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@router.post("/fichiers/{numero}/confirmer")
def fichiers_confirmer(
    numero: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _trombone_ouvert(service, profile)
    try:
        f = fichiers_service.decrire(settings, str(user.id), numero)
    except fichiers_service.RefusFichier as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return {"id": f["id"], "nom": f["nom"], "type": f["type"], "libelle": f["libelle"], "taille": f["taille"]}


@router.delete("/fichiers/{numero}")
def fichiers_retirer(
    numero: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    user, _profile = _ouvrir(settings, authorization, admin_service, service)
    try:
        return {"retires": fichiers_service.retirer(settings, str(user.id), numero)}
    except fichiers_service.RefusFichier as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


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


# ── 18/11 (note étape 4 §66, marche 6a) : la carte « créer » APRÈS son clic ───────────────────────────────────────
# ROUVRIR : la fenêtre a été fermée sans créer. Le serveur re-vérifie TOUT comme au premier clic (le même `executer`, qui
#   n'écrit rien) et rend des liens frais pour les photos de la fiche ; la carte ne change pas d'état.
# SUITE : la fenêtre a créé la fiche -> la carte le garde (« Estimation créée »), pour un rechargement. Rien d'autre.
GESTE_CREATION = "ouvrir_creation_annonce"
GESTES_QUI_OUVRENT = (GESTE_CREATION, "ouvrir_avis_de_valeur")  # « Rouvrir » : la fenêtre de création, l'avis de valeur


def _carte_creation_validee(service: AssistantService, action_id: str, user_id: str,
                            gestes: tuple[str, ...] = (GESTE_CREATION,)) -> dict[str, Any]:
    carte = _carte_a_moi(service, action_id, user_id)
    if carte.get("geste") not in gestes or carte.get("etat") != "executee":
        raise HTTPException(status_code=409, detail="Cette carte ne rouvre pas de fenêtre de création.")
    return carte


@router.post("/actions/{action_id}/rouvrir")
def assistant_rouvrir(
    action_id: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    carte = _carte_creation_validee(service, action_id, str(user.id), GESTES_QUI_OUVRENT)
    geste = GESTES[str(carte["geste"])]
    role = str(profile.get("role") or "")
    if role not in geste.roles:
        raise HTTPException(status_code=403, detail="Ce geste n'est pas ouvert à ton rôle")
    ctx = ContexteAssistant(settings=settings, user_id=str(user.id), email=(user.email or "").strip().lower(), role=role,
                            jeton=_jeton(authorization), conversation_id=carte.get("conversation_id"),
                            nom=profile.get("display_name") or None)
    try:
        return {"ok": True, "resultat": geste.executer(ctx, dict(carte.get("parametres") or {}))}
    except Refus as exc:
        return {"ok": False, "detail": f"Non rouverte : {exc}"}


class SuiteCreationPayload(BaseModel):
    app_dossier_id: int | None = Field(default=None, ge=1)
    genre: str = Field(pattern="^(estimation|annonce)$")


@router.post("/actions/{action_id}/suite")
def assistant_suite(
    action_id: str,
    payload: SuiteCreationPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
):
    user, _profile = _ouvrir(settings, authorization, admin_service, service)
    carte = _carte_creation_validee(service, action_id, str(user.id))
    # les liens des photos ont expiré : on ne les garde pas ; le reste du résultat (ce qui a été pré-rempli) reste
    resultat = {k: v for k, v in dict(carte.get("resultat") or {}).items() if k != "photos"}
    resultat["cree"] = {"app_dossier_id": payload.app_dossier_id, "genre": payload.genre, "le": datetime.now(timezone.utc).isoformat()}
    if not service.noter_suite(action_id, str(user.id), resultat):
        raise HTTPException(status_code=409, detail="Cette carte ne rouvre pas de fenêtre de création.")
    return {"ok": True, "resultat": resultat}


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


# ── 19/11 (étape 4 chap. 6, P1) : LE PARCOURS GUIDÉ — les questions sans modèle ─────────────────────────────────────
# Un clic n'appelle PAS le modèle : le serveur enregistre la réponse dans app_assistant_parcours (P3) et rend la question
# suivante (assistant_parcours.py, les 19 questions en données). Derrière l'interrupteur `assistant_parcours`
# (off / admin / on ; absent = éteint), EN PLUS de celui de l'assistant. Note étape 4 §93.
# ⛔ Les coordonnées d'un nouveau mandant ne passent pas par ces routes (l'écran les dépose dans le schéma privé).
INTERRUPTEUR_PARCOURS = "assistant_parcours"


class ParcoursDepartPayload(BaseModel):
    genre: str = Field(pattern="^(creation_estimation|creation_annonce)$")
    conversationId: str | None = Field(default=None, min_length=36, max_length=36)


class ParcoursReponsePayload(BaseModel):
    question: str = Field(min_length=1, max_length=40)
    geste: str = Field(pattern="^(repondre|passer|nsp)$")
    valeurs: dict[str, Any] = Field(default_factory=dict)


def get_parcours_store(settings: Settings = Depends(get_settings)) -> parcours_moteur.ParcoursStore:
    return parcours_moteur.ParcoursStore(settings)


def _parcours_ouvert(service: AssistantService, profile: dict[str, Any]) -> None:
    if not autorise(service.interrupteur(INTERRUPTEUR_PARCOURS), str(profile.get("role") or ""),
                    profile.get("is_active") is True):
        raise HTTPException(status_code=403, detail="Le parcours guidé n'est pas encore ouvert pour ce compte")


@router.post("/parcours")
def parcours_commencer(
    payload: ParcoursDepartPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    conversation_id = None
    if payload.conversationId:
        conv = service.conversation(payload.conversationId)
        if not conv or str(conv.get("user_id") or "") != str(user.id):
            raise HTTPException(status_code=404, detail="Conversation introuvable")
        conversation_id = str(conv["id"])
    premiere = parcours_moteur.suivante({}, parcours_moteur.annee_a_paris())
    ligne = store.creer(str(user.id), conversation_id, payload.genre, premiere["id"] if premiere else None)
    return {"ok": True, "parcours": parcours_moteur.vue(ligne)}


@router.get("/parcours/{parcours_id}")
def parcours_relire(
    parcours_id: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    _user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    if len(parcours_id) != 36:
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    # avec SON jeton : la règle de lecture de la base (auteur avant la création, négociateur, admin) décide
    ligne = store.lire_avec_jeton(_jeton(authorization), parcours_id)
    if not ligne:
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    return {"ok": True, "parcours": parcours_moteur.vue(ligne)}


@router.post("/parcours/{parcours_id}/reponse")
def parcours_repondre(
    parcours_id: str,
    payload: ParcoursReponsePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    if len(parcours_id) != 36:
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    ligne = store.lire_service(parcours_id)
    # même l'admin, qui relit les parcours des autres, ne répond pas à leur place
    if not ligne or str(ligne.get("user_id") or "") != str(user.id):
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    if ligne.get("etat") != "en_cours" or ligne.get("app_dossier_id") is not None:
        raise HTTPException(status_code=409, detail="Ce parcours est terminé : la fiche est créée.")
    annee = parcours_moteur.annee_a_paris()
    if payload.question not in {q["id"] for q in parcours_moteur.questions_posees(dict(ligne.get("reponses") or {}), annee)}:
        raise HTTPException(status_code=400, detail="Cette question n'est pas posée pour ce bien.")
    try:
        reponses = parcours_moteur.enregistrer(dict(ligne.get("reponses") or {}), payload.question, payload.valeurs,
                                               payload.geste)
    except parcours_moteur.RefusParcours as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    prochaine = parcours_moteur.suivante(reponses, annee)
    ecrite = store.ecrire_reponses(ligne, reponses, prochaine["id"] if prochaine else None)
    if not ecrite:
        # P4-c (20/11) : si SEULE la lecture des services publics (arrière-plan) a écrit entre-temps, la réponse se rejoue
        #   sur la ligne fraîche -- rien n'est écrasé. Tout autre changement (un second onglet) reste refusé.
        fraiche = store.lire_service(parcours_id)
        if fraiche and fraiche.get("etat") == "en_cours" and fraiche.get("app_dossier_id") is None \
                and parcours_moteur.seul_publics_a_bouge(ligne.get("reponses") or {}, fraiche.get("reponses") or {}):
            reponses = parcours_moteur.enregistrer(dict(fraiche.get("reponses") or {}), payload.question,
                                                   payload.valeurs, payload.geste)
            prochaine = parcours_moteur.suivante(reponses, annee)
            ecrite = store.ecrire_reponses(fraiche, reponses, prochaine["id"] if prochaine else None)
    if not ecrite:
        raise HTTPException(status_code=409, detail="Le parcours a bougé ailleurs (un autre onglet ?) : recharge-le.")
    return {"ok": True, "parcours": parcours_moteur.vue(ecrite, annee)}


@router.get("/parcours")
def parcours_de_la_conversation(
    conversationId: str = Query(min_length=36, max_length=36),
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    # P2 (19/11) : une conversation rouverte retrouve ses parcours, relus avec SON jeton (la règle de lecture décide)
    _user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    annee = parcours_moteur.annee_a_paris()
    lignes = store.lister_conversation_avec_jeton(_jeton(authorization), conversationId)
    return {"ok": True, "parcours": [parcours_moteur.vue(ligne, annee) for ligne in lignes]}


class ParcoursFichePayload(BaseModel):
    fichiers: str = Field(min_length=1, max_length=400)


@router.post("/parcours/{parcours_id}/fiche")
def parcours_lire_fiche(
    parcours_id: str,
    payload: ParcoursFichePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    # P4-b (19/11) : la fiche papier jointe PENDANT le parcours (trombone) est lue par le scan de la fenêtre ; ce qui est
    # déjà répondu n'est pas remplacé ; les coordonnées du mandant vont au coffre privé
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    if len(parcours_id) != 36:
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    ligne = store.lire_service(parcours_id)
    if not ligne or str(ligne.get("user_id") or "") != str(user.id):
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    if ligne.get("etat") != "en_cours" or ligne.get("app_dossier_id") is not None:
        raise HTTPException(status_code=409, detail="Ce parcours est terminé : la fiche est créée.")
    ctx = ContexteAssistant(settings=settings, user_id=str(user.id), email=(user.email or "").strip().lower(),
                            role=str(profile.get("role") or ""), jeton=_jeton(authorization),
                            conversation_id=ligne.get("conversation_id"), nom=profile.get("display_name") or None)
    try:
        ecrite = lire_fiche_du_parcours(ctx, ligne, payload.fichiers)
    except Refus as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    if not ecrite:
        raise HTTPException(status_code=409, detail="Le parcours a bougé ailleurs (un autre onglet ?) : recharge-le.")
    return {"ok": True, "parcours": parcours_moteur.vue(ecrite)}


@router.post("/parcours/{parcours_id}/publics")
def parcours_services_publics(
    parcours_id: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    # P4-c (20/11) : l'adresse est dite -> le DPE (ADEME), l'année (BDNB), la parcelle (cadastre), la copropriété (RNIC),
    #   lus par les routes de l'éditeur d'avis avec le jeton de la personne. ⛔ Gardés comme PROPOSITIONS (`_publics`) :
    #   aucune case n'est posée ; la question concernée demande « C'est bien ça ? » (parcours_publics.py).
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    if len(parcours_id) != 36:
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    ligne = store.lire_service(parcours_id)
    if not ligne or str(ligne.get("user_id") or "") != str(user.id):
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    if ligne.get("etat") != "en_cours" or ligne.get("app_dossier_id") is not None:
        raise HTTPException(status_code=409, detail="Ce parcours est terminé : la fiche est créée.")
    annee = parcours_moteur.annee_a_paris()
    reponses = dict(ligne.get("reponses") or {})
    cle = parcours_moteur.cle_publics(reponses)
    if cle is None:
        raise HTTPException(status_code=400, detail="L'adresse du bien n'est pas encore dite.")
    deja = reponses.get(parcours_moteur.CLE_PUBLICS)
    if isinstance(deja, dict) and deja.get("cle") == cle:
        return {"ok": True, "parcours": parcours_moteur.vue(ligne, annee)}  # déjà lu pour cette adresse : rien à refaire
    garde = parcours_publics.lire(reponses, authorization or "", settings, annee)
    # Pendant la lecture (quelques secondes) la personne a pu répondre : on relit, on ne pose QUE `_publics`, et on
    # recommence si quelqu'un écrit entre les deux (jamais une réponse écrasée).
    for _ in range(3):
        fraiche = store.lire_service(parcours_id)
        if not fraiche or fraiche.get("etat") != "en_cours" or fraiche.get("app_dossier_id") is not None:
            raise HTTPException(status_code=409, detail="Ce parcours est terminé : la fiche est créée.")
        nouvelles = {**dict(fraiche.get("reponses") or {}), parcours_moteur.CLE_PUBLICS: garde}
        ecrite = store.ecrire_reponses(fraiche, nouvelles, fraiche.get("etape"))
        if ecrite:
            return {"ok": True, "parcours": parcours_moteur.vue(ecrite, annee)}
    raise HTTPException(status_code=409, detail="Le parcours a bougé ailleurs (un autre onglet ?) : recharge-le.")


TYPES_PHOTOS_DU_BIEN = {"image/jpeg", "image/png", "image/webp"}  # = l'étape Photos de la fenêtre


@router.get("/parcours/{parcours_id}/photos")
def parcours_photos_du_bien(
    parcours_id: str,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    # P6 (20/11) : les PHOTOS DU BIEN du parcours, relues au coffre dans le dossier de SON AUTEUR, avec un lien de lecture
    #   court : les vignettes de la question, et l'étape 2 « Photos » de la fenêtre à son ouverture. ⛔ Jamais lues par
    #   personne (ni scan ni modèle). Une photo purgée du coffre (dépôts gardés 2 jours) est comptée, jamais inventée.
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    if len(parcours_id) != 36:
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    ligne = store.lire_service(parcours_id)
    if not ligne or str(ligne.get("user_id") or "") != str(user.id):
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    rendues, absentes = [], 0
    for p in (ligne.get("reponses") or {}).get("photos") or []:
        numero = str(p.get("id") if isinstance(p, dict) else p)
        try:
            f = fichiers_service.decrire(settings, str(user.id), numero)
            if f["type"] not in TYPES_PHOTOS_DU_BIEN:
                absentes += 1
                continue
            rendues.append({"id": numero, "nom": f["nom"], "type": f["type"], "taille": f["taille"],
                            "url": fichiers_service.lien_lecture(settings, f["chemin"]),
                            "visible": not (isinstance(p, dict) and p.get("visible") is False)})
        except fichiers_service.RefusFichier:
            absentes += 1
    return {"ok": True, "photos": rendues, "absentes": absentes}


class ParcoursPhrasePayload(BaseModel):
    question: str = Field(min_length=1, max_length=60)
    texte: str = Field(min_length=1, max_length=4000)


@router.post("/parcours/{parcours_id}/phrase")
def parcours_phrase_libre(
    parcours_id: str,
    payload: ParcoursPhrasePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    # P4-d (20/11) : une PHRASE LIBRE tapée dans la zone du bas pendant qu'une question est ouverte, lue TOUT DE SUITE par
    #   le petit lecteur (le format du scan). ⛔ Téléphones et e-mails retirés AVANT le modèle ; la question ouverte reçoit
    #   ses cases dans la CARTE (la personne valide) ; les autres sont pré-remplies « dit », jamais à la place d'une réponse.
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    if len(parcours_id) != 36:
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    ligne = store.lire_service(parcours_id)
    if not ligne or str(ligne.get("user_id") or "") != str(user.id):
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    if ligne.get("etat") != "en_cours" or ligne.get("app_dossier_id") is not None:
        raise HTTPException(status_code=409, detail="Ce parcours est terminé : la fiche est créée.")
    annee = parcours_moteur.annee_a_paris()
    question = next((q for q in parcours_moteur.questions_posees(dict(ligne.get("reponses") or {}), annee)
                     if q["id"] == payload.question), None)
    if not question:
        raise HTTPException(status_code=400, detail="Cette question n'est pas posée pour ce bien.")
    try:
        texte, retires = parcours_phrases.retirer_coordonnees(parcours_phrases.nettoyer(payload.texte))
    except parcours_moteur.RefusParcours as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    if service.depense_du_jour() >= PLAFOND_JOUR_USD:
        raise HTTPException(status_code=429, detail="Plafond de dépense du jour atteint : la phrase n'est pas lue")
    try:
        lu = parcours_phrases.lire(texte, question["titre"], OpenAIListingSheetService(settings).extract_texte)
    except HTTPException:
        raise HTTPException(status_code=502, detail="La phrase n'a pas pu être lue : réessaie, ou réponds avec les boutons.") from None
    cout = cout_usd(lu.get("model"), lu.get("usage") or {}) if isinstance(lu.get("usage"), dict) else None
    usage = lu.get("usage") or {}
    try:  # même compteur que l'assistant (app_agent_run), jamais le texte
        admin_service.insert_agent_run({
            "agent_key": AGENT_PHRASE, "negociateur_email": (user.email or "").strip().lower() or None, "status": "proposed",
            "model": lu.get("model"), "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"), "cost_usd": cout,
            "proposal_json": {"parcours_id": parcours_id, "question": payload.question, "caracteres": len(texte),
                              "retires": retires}})
    except Exception:  # noqa: BLE001
        pass
    # Pendant la lecture la personne a pu répondre : on relit et on applique sur la ligne fraîche (l'application ne
    # remplace jamais une réponse), trois essais au plus.
    for _ in range(3):
        fraiche = store.lire_service(parcours_id)
        if not fraiche or fraiche.get("etat") != "en_cours" or fraiche.get("app_dossier_id") is not None:
            raise HTTPException(status_code=409, detail="Ce parcours est terminé : la fiche est créée.")
        try:
            nouvelles, carte, dire = parcours_phrases.appliquer(dict(fraiche.get("reponses") or {}), payload.question, texte,
                                                                lu["lecture"], annee, cout)
        except parcours_moteur.RefusParcours as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from None
        ecrite = store.ecrire_reponses(fraiche, nouvelles, fraiche.get("etape"))
        if ecrite:
            return {"ok": True, "parcours": parcours_moteur.vue(ecrite, annee), "carte": carte,
                    "dire": {**dire, "retires": retires}}
    raise HTTPException(status_code=409, detail="Le parcours a bougé ailleurs (un autre onglet ?) : recharge-le.")


class ParcoursCreePayload(BaseModel):
    app_dossier_id: int | None = Field(default=None, ge=1)


@router.post("/parcours/{parcours_id}/cree")
def parcours_cree(
    parcours_id: str,
    payload: ParcoursCreePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: AssistantService = Depends(get_assistant_service),
    store: parcours_moteur.ParcoursStore = Depends(get_parcours_store),
):
    # P2 (19/11) : la fenêtre remplie par le parcours a créé la fiche -> le parcours est terminé (une seule fois)
    user, profile = _ouvrir(settings, authorization, admin_service, service)
    _parcours_ouvert(service, profile)
    if len(parcours_id) != 36:
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    ligne = store.lire_service(parcours_id)
    if not ligne or str(ligne.get("user_id") or "") != str(user.id):
        raise HTTPException(status_code=404, detail="Parcours introuvable")
    if ligne.get("etat") != "en_cours" or ligne.get("app_dossier_id") is not None:
        raise HTTPException(status_code=409, detail="Ce parcours est déjà terminé.")
    ecrite = store.terminer(ligne, payload.app_dossier_id)
    if not ecrite:
        raise HTTPException(status_code=409, detail="Ce parcours est déjà terminé.")
    return {"ok": True, "parcours": parcours_moteur.vue(ecrite)}
