from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_authenticated_user, require_request_user
from ..services.openai_ged_classement_service import AGENT_KEY, MAX_PAGES, OpenAIGedClassementService
from ..services.openai_ged_lecture_service import AGENT_KEY as AGENT_LECTURE, MAX_PAGES_HD, OpenAIGedLectureService
from ..services.supabase_admin import SupabaseAdminService
from ..settings import Settings, get_settings

# GED (12/11/2026, morceau 4) : la fenetre de depot demande a l'IA le type d'un fichier AVANT
# son envoi. Propose seulement : n'ecrit RIEN sur le bien ni sur le document. Derriere
# l'interrupteur `ged_lecture_ia` (off / admin / on), relu a CHAQUE appel.

router = APIRouter(prefix="/ged", tags=["ged"])


class GedPage(BaseModel):
    numero: int = Field(ge=1)
    image: str


class GedClasserPayload(BaseModel):
    nomFichier: str | None = None
    hektorAnnonceId: str | None = None
    nbPages: int | None = Field(default=None, ge=0)
    pages: list[GedPage] = Field(default_factory=list, max_length=MAX_PAGES)
    texte: str | None = None


class GedLirePayload(BaseModel):
    jobId: str = Field(min_length=36, max_length=36)
    nomFichier: str | None = None
    nbPages: int | None = Field(default=None, ge=0)
    pages: list[GedPage] = Field(default_factory=list, max_length=MAX_PAGES_HD)
    texte: str | None = None


def get_admin_service(settings: Settings = Depends(get_settings)) -> SupabaseAdminService:
    return SupabaseAdminService(settings)


def get_classement_service(settings: Settings = Depends(get_settings)) -> OpenAIGedClassementService:
    return OpenAIGedClassementService(settings)


def get_lecture_service(settings: Settings = Depends(get_settings)) -> OpenAIGedLectureService:
    return OpenAIGedLectureService(settings)


def autorise(cran: str, role: str, actif: bool) -> bool:
    if not actif:
        return False
    if cran == "on":
        return role in {"admin", "manager", "commercial"}
    if cran == "admin":
        return role == "admin"
    return False


def _hektor_annonce_id(valeur: str | None) -> int | None:
    try:
        return int(str(valeur or "").strip())
    except ValueError:
        return None


@router.post("/classer")
def ged_classer(
    payload: GedClasserPayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: OpenAIGedClassementService = Depends(get_classement_service),
):
    user = get_authenticated_user(settings, authorization)
    profile = admin_service.load_profile(user)
    cran = service.interrupteur()
    if not autorise(cran, str(profile.get("role") or ""), profile.get("is_active") is True):
        raise HTTPException(status_code=403, detail="Classement par l'IA eteint pour ce compte")

    email = (user.email or "").strip().lower() or None
    annonce = _hektor_annonce_id(payload.hektorAnnonceId)
    try:
        resultat = service.classer(payload.model_dump())
    except HTTPException as exc:
        # Les refus d'avant l'appel (RIB, plafond, vignette) ne coutent rien : on ne trace que les echecs de l'IA.
        if exc.status_code == 502:
            _tracer(admin_service, {"agent_key": AGENT_KEY, "hektor_annonce_id": annonce, "negociateur_email": email,
                                    "status": "error", "error_text": str(exc.detail)[:2000]})
        raise
    usage = resultat.get("usage") or {}
    # Le journal ne garde ni le nom propose ni la remarque : le type, la confiance et le cout suffisent.
    _tracer(admin_service, {
        "agent_key": AGENT_KEY,
        "hektor_annonce_id": annonce,
        "negociateur_email": email,
        "status": "proposed",
        "model": resultat.get("model"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cost_usd": resultat.get("costUsd"),
        "proposal_json": {
            "type_code": resultat.get("typeCode"),
            "confiance": resultat.get("confiance"),
            "pieces": [p.get("typeCode") for p in resultat.get("pieces") or []],
            "sensible": resultat.get("sensible"),
            "pages_envoyees": len(payload.pages),
            "nb_pages": payload.nbPages,
            "texte_caracteres": len(payload.texte or ""),
        },
    })
    return {"ok": True, **{k: v for k, v in resultat.items() if k != "usage"}}


# GED (12/11/2026, morceau 6) : l'IA LIT les valeurs d'un document qui vient d'être déposé et classé. Le serveur
# vérifie que le classement est celui de l'utilisateur (decide_par), lit, puis ÉCRIT la lecture et ses valeurs (clé de
# service : l'écran ne peut pas écrire ces tables). Rien ne s'écrit sur le bien.
@router.post("/lire")
def ged_lire(
    payload: GedLirePayload,
    authorization: str | None = Depends(require_request_user),
    settings: Settings = Depends(get_settings),
    admin_service: SupabaseAdminService = Depends(get_admin_service),
    service: OpenAIGedLectureService = Depends(get_lecture_service),
):
    user = get_authenticated_user(settings, authorization)
    profile = admin_service.load_profile(user)
    if not autorise(service.portier.interrupteur(), str(profile.get("role") or ""), profile.get("is_active") is True):
        raise HTTPException(status_code=403, detail="Lecture par l'IA eteinte pour ce compte")
    classement = service.classement_du_travail(payload.jobId)
    if not classement:
        raise HTTPException(status_code=404, detail="Classement introuvable pour ce dépôt")
    if str(classement.get("decide_par") or "") != str(user.id):
        raise HTTPException(status_code=403, detail="Ce document a été classé par quelqu'un d'autre")
    email = (user.email or "").strip().lower() or None
    annonce = _hektor_annonce_id(classement.get("hektor_annonce_id"))
    try:
        resultat = service.lire(classement, payload.model_dump())
    except HTTPException as exc:
        if exc.status_code == 502:
            _tracer(admin_service, {"agent_key": AGENT_LECTURE, "hektor_annonce_id": annonce, "negociateur_email": email,
                                    "status": "error", "error_text": str(exc.detail)[:2000]})
        raise
    usage = resultat.get("usage") or {}
    # le journal des agents compte le coût (plafond du jour) ; les valeurs vont dans app_ged_valeur, pas ici
    _tracer(admin_service, {
        "agent_key": AGENT_LECTURE, "hektor_annonce_id": annonce, "negociateur_email": email, "status": "proposed",
        "model": resultat.get("model"), "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"), "cost_usd": resultat.get("costUsd"),
        "proposal_json": {"fiche": resultat.get("fiche"), "etat": resultat.get("etat"), "pages_lues": resultat.get("pagesLues"),
                          "par_texte": resultat.get("parTexte"), "valeurs_lues": sum(1 for v in resultat["valeurs"] if v["etat"] != "non_vu")},
    })
    lecture_id = service.enregistrer(classement, resultat, str(user.id))
    return {"ok": True, "lectureId": lecture_id, "fiche": resultat["fiche"], "etat": resultat["etat"], "valeurs": resultat["valeurs"],
            "costUsd": resultat.get("costUsd")}


def _tracer(admin_service: SupabaseAdminService, ligne: dict) -> None:
    # Best-effort : une trace ratee ne doit jamais faire perdre la proposition a l'ecran.
    try:
        admin_service.insert_agent_run(ligne)
    except Exception:
        pass
