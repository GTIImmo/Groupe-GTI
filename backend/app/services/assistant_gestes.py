from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from typing import Any, Callable

import requests

from .assistant_contexte import TOUS_LES_ROLES, ContexteAssistant, Fonction, LectureRefusee, Refus

# ---------------------------------------------------------------------------
# Assistant IA (13/11/2026, étape 3, lot 1) -- LES GESTES, PAR CARTE DE VALIDATION.
# Notes : notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md, notice/ETAPE3_CATALOGUE_COMPLET_DES_ACTIONS_2026-11-13.md.
#
# ⛔ LE MODÈLE NE FAIT JAMAIS UN GESTE. Il appelle « proposer_… » : ce module VÉRIFIE (droits lus avec le jeton,
#   conditions de l'écran), range une CARTE dans app_assistant_action et rend au modèle « carte proposée ».
#   Le geste ne s'exécute qu'au CLIC de la personne (route /assistant/actions/{id}/valider), une seule fois,
#   avec SON jeton, par la même écriture que l'écran.
# ⛔ Chaque geste re-vérifie ses conditions AU CLIC : entre la carte et le clic, le monde a pu changer.
# ⛔ Les fonctions de la base SANS contrôle de l'appelant (app_create_relance_for_contact, app_relance_set_status)
#   ne sont appelées qu'APRÈS une lecture de l'objet avec le jeton (règle du 29/10), et l'e-mail du négociateur
#   est posé par NOTRE serveur, jamais par le modèle.
#
# Lot 1 : les demandes à la direction (diffusion, baisse de prix, annulation de mandat) et les relances.
# ⚠ « Corriger une demande renvoyée » n'est PAS offert : la règle d'écriture de app_diffusion_request réserve la
#   mise à jour à la direction (is_app_manager_or_admin) -- un négociateur ne peut pas corriger, même à l'écran
#   (trouvé le 13/11, noté dans la note de l'étape 3).
# ---------------------------------------------------------------------------

EN_COURS = ("pending", "in_progress", "waiting_commercial")
TYPES_DEMANDE = {
    "diffusion": ("demande_diffusion", "Demande envoyee", "Demander la validation et la mise en diffusion"),
    "baisse_prix": ("demande_baisse_prix", "Demande de baisse de prix envoyee", "Demander une baisse de prix"),
    "annulation_mandat": ("demande_annulation_mandat", "Demande d annulation de mandat envoyee",
                          "Demander l'annulation du mandat"),
}


# ── lecture et écriture avec le jeton de la personne (comme l'écran) ──────────
def _entetes(ctx: ContexteAssistant) -> dict[str, str]:
    return {"apikey": ctx.settings.supabase_anon_key, "Authorization": f"Bearer {ctx.jeton}"}


def _lire(ctx: ContexteAssistant, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
    r = requests.get(f"{ctx.settings.supabase_url}/rest/v1/{table}", headers=_entetes(ctx), params=params, timeout=15)
    if not r.ok:
        raise LectureRefusee(f"lecture de {table} impossible ({r.status_code})")
    return r.json() or []


def _ecrire(ctx: ContexteAssistant, methode: str, chemin: str, corps: Any, params: dict[str, str] | None = None) -> Any:
    r = requests.request(methode, f"{ctx.settings.supabase_url}/rest/v1/{chemin}",
                         headers={**_entetes(ctx), "Prefer": "return=representation"}, json=corps, params=params, timeout=15)
    if not r.ok:
        # la base a refusé : on le dit avec son message (droits, contrainte), jamais un succès inventé
        try:
            message = (r.json() or {}).get("message")
        except ValueError:
            message = None
        raise Refus(f"la base a refusé l'écriture ({r.status_code}{' : ' + str(message)[:200] if message else ''})")
    return r.json() if r.text else None


def _bien(ctx: ContexteAssistant, hektor_annonce_id: Any) -> dict[str, Any]:
    numero = str(hektor_annonce_id or "").strip()
    if not numero.isdigit():
        raise Refus("Donne le numéro d'annonce du bien (ex. 63289).")
    lignes = _lire(ctx, "app_dossiers_current", {
        "hektor_annonce_id": f"eq.{numero}", "limit": "1",
        "select": "app_dossier_id,hektor_annonce_id,numero_dossier,numero_mandat,titre_bien,commercial_nom,"
                  "validation_diffusion_state,statut_annonce,prix"})
    if not lignes:
        raise Refus(f"L'annonce {numero} n'est pas parmi les biens vivants que tu peux voir.")
    return lignes[0]


def _valide(etat: Any) -> bool:
    # = isValidationApproved de l'écran (App.tsx:8046)
    return re.sub(r"\s+", " ", str(etat or "").strip().lower()) in {"1", "true", "oui", "valide", "validee", "validation ok",
                                                                     "validation_ok", "ok"}


def _euros(montant: Any) -> str:
    return f"{int(round(float(montant))):,}".replace(",", " ") + " €"


# ── 1. les demandes à la direction (écran : handleCreateDiffusionRequest, App.tsx:20375 ; api.ts:8062) ──
def _controler_demande(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], str, str | None]:
    genre = str(p.get("type") or "").strip()
    if genre not in TYPES_DEMANDE:
        raise Refus("Type de demande : diffusion, baisse_prix ou annulation_mandat.")
    type_base = TYPES_DEMANDE[genre][0]
    bien = _bien(ctx, p.get("hektor_annonce_id"))
    if not str(bien.get("numero_mandat") or "").strip():
        raise Refus("Ce bien n'a pas de numéro de mandat : l'écran n'ouvre pas de demande « sans mandat ».")
    valide = _valide(bien.get("validation_diffusion_state"))
    if genre in {"baisse_prix", "annulation_mandat"} and not valide:
        raise Refus("Impossible : le mandat doit être sous validation = oui (règle de l'écran). Une demande de "
                    "validation (diffusion) vient d'abord.")
    if genre == "diffusion" and valide:
        raise Refus("Ce mandat est déjà validé : il n'y a plus de demande de validation à faire ; c'est le choix des "
                    "portails (pas encore ouvert à l'assistant).")
    deja = _lire(ctx, "app_diffusion_requests_current", {
        "app_dossier_id": f"eq.{bien['app_dossier_id']}", "request_type": f"eq.{type_base}",
        "request_status": f"in.({','.join(EN_COURS)})", "select": "id,request_status", "limit": "1"})
    if deja:
        raise Refus("Une demande de ce type est déjà en cours pour ce bien (une seule à la fois, comme à l'écran).")
    prix = None
    if genre == "baisse_prix":
        brut = re.sub(r"\s+", "", str(p.get("nouveau_prix") or "")).replace(",", ".").replace("€", "")
        try:
            valeur = float(brut)
        except ValueError:
            valeur = 0.0
        if valeur <= 0:
            raise Refus("Le nouveau prix demandé doit être un montant (ex. 185000).")
        prix = str(round(valeur))  # = normalizeRequestedPriceInput (App.tsx:7446)
    return bien, type_base, prix


def _commentaire_demande(genre: str, prix: str | None, commentaire: str) -> str:
    # le MÊME texte que l'écran (App.tsx:20399), que Pauline et extractRequestedPriceFromRequest relisent
    if genre == "baisse_prix":
        return "\n".join(x for x in ["Demande de baisse de prix", f"Nouveau prix demande : {prix}" if prix else None,
                                      f"Commentaire : {commentaire}" if commentaire else None] if x)
    if genre == "annulation_mandat":
        return "\n".join(x for x in ["Demande d annulation de mandat",
                                      f"Motif / contexte : {commentaire}" if commentaire else None] if x)
    return commentaire


def preparer_demande(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    genre = str(p.get("type") or "").strip()
    bien, _, prix = _controler_demande(ctx, p)
    commentaire = str(p.get("commentaire") or "").strip()[:1000]
    resume = f"{TYPES_DEMANDE[genre][2]} — annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} »"
    if prix:
        ancien = f" (aujourd'hui {_euros(bien['prix'])})" if isinstance(bien.get("prix"), (int, float)) else ""
        resume += f", nouveau prix {_euros(prix)}{ancien}"
    if commentaire:
        resume += f". Commentaire : {commentaire}"
    return resume, {"type": genre, "hektor_annonce_id": int(bien["hektor_annonce_id"]), "nouveau_prix": prix,
                    "commentaire": commentaire}


def executer_demande(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    genre = str(p.get("type") or "")
    bien, type_base, prix = _controler_demande(ctx, p)  # re-vérifié AU CLIC
    texte = _commentaire_demande(genre, prix, str(p.get("commentaire") or "").strip()) or None
    libelle = ctx.nom or ctx.email
    cree = _ecrire(ctx, "POST", "app_diffusion_request", {
        "app_dossier_id": bien["app_dossier_id"], "hektor_annonce_id": bien["hektor_annonce_id"],
        "numero_dossier": bien.get("numero_dossier"), "numero_mandat": bien.get("numero_mandat"),
        "titre_bien": bien.get("titre_bien"), "commercial_nom": bien.get("commercial_nom"),
        "request_type": type_base, "requested_by": ctx.user_id, "requested_by_label": libelle,
        "request_comment": texte, "request_reason": texte, "follow_up_needed": False, "relaunch_count": 0})
    demande = (cree or [{}])[0]
    if not demande.get("id"):
        raise Refus("la demande n'a pas été créée (la base n'a rien rendu)")
    maintenant = datetime.now(timezone.utc).isoformat()
    try:
        _ecrire(ctx, "POST", "app_diffusion_request_event", {
            "diffusion_request_id": demande["id"], "event_type": "request_created", "event_label": TYPES_DEMANDE[genre][1],
            "event_at": maintenant, "actor_user_id": ctx.user_id, "actor_name": libelle, "actor_role": "nego",
            "payload_json": json.dumps({"message": texte}, ensure_ascii=False) if texte else None})
        evenement = True
    except Refus:
        evenement = False  # la demande existe ; seul l'historique manque -- on le dit, on ne l'efface pas
    return {"demande_id": demande["id"], "type": type_base, "historique_ecrit": evenement}


# ── 2. les relances (écran : createRelanceForContact api.ts:4316, setRelanceStatus api.ts:4523) ──
def _contact(ctx: ContexteAssistant, hektor_contact_id: Any) -> dict[str, Any]:
    numero = str(hektor_contact_id or "").strip()
    if not numero:
        raise Refus("Donne le numéro du contact (hektor_contact_id, colonne de contacts).")
    lignes = _lire(ctx, "app_contacts_current", {"hektor_contact_id": f"eq.{numero}", "select": "hektor_contact_id,display_name",
                                                 "limit": "1"})
    if not lignes:
        raise Refus(f"Le contact {numero} n'est pas parmi ceux que tu peux voir.")
    return lignes[0]


def _date(texte: Any) -> date:
    try:
        return date.fromisoformat(str(texte or "").strip()[:10])
    except ValueError:
        raise Refus("Donne la date d'échéance au format AAAA-MM-JJ.") from None


def preparer_relance(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    contact = _contact(ctx, p.get("hektor_contact_id"))
    libelle = str(p.get("libelle") or "").strip()[:200]
    if not libelle:
        raise Refus("Donne l'intitulé de la relance (ex. « Rappeler pour la visite »).")
    echeance = _date(p.get("echeance"))
    annonce = str(p.get("hektor_annonce_id") or "").strip()
    bien = _bien(ctx, annonce) if annonce and annonce != "0" else None
    detail = str(p.get("detail") or "").strip()[:500]
    resume = f"Créer une relance pour {contact.get('display_name') or contact['hektor_contact_id']} le " \
             f"{echeance.strftime('%d/%m/%Y')} : {libelle}"
    if bien:
        resume += f" (annonce {bien['hektor_annonce_id']})"
    return resume, {"hektor_contact_id": contact["hektor_contact_id"], "libelle": libelle, "echeance": echeance.isoformat(),
                    "detail": detail, "app_dossier_id": bien["app_dossier_id"] if bien else None}


def executer_relance(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    _contact(ctx, p.get("hektor_contact_id"))  # re-vérifié AU CLIC (la fonction de la base ne contrôle pas l'appelant)
    lignes = _ecrire(ctx, "POST", "rpc/app_create_relance_for_contact", {
        "p_hektor_contact_id": p["hektor_contact_id"], "p_label": p["libelle"], "p_due_date": p["echeance"],
        "p_negociateur_email": ctx.email,  # ⛔ posé par le serveur, jamais par le modèle
        "p_sub": p.get("detail") or None, "p_contact_search_key": None, "p_app_dossier_id": p.get("app_dossier_id")})
    relance = (lignes or [{}])[0]
    return {"relance_id": relance.get("id"), "echeance": relance.get("due_date")}


def _relance(ctx: ContexteAssistant, relance_id: Any) -> dict[str, Any]:
    numero = str(relance_id or "").strip()
    if not numero.isdigit():
        raise Refus("Donne le numéro de la relance (colonne id de relances).")
    lignes = _lire(ctx, "app_relance_rapprochement", {"id": f"eq.{numero}", "select": "id,label,due_date,status", "limit": "1"})
    if not lignes:
        raise Refus(f"La relance {numero} n'est pas parmi celles que tu peux voir.")
    return lignes[0]


def preparer_statut_relance(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    statut = str(p.get("statut") or "").strip()
    if statut not in {"fait", "reporte"}:
        raise Refus("Statut : fait ou reporte (reporter décale l'échéance de 3 jours, comme l'écran).")
    relance = _relance(ctx, p.get("relance_id"))
    if relance.get("status") == "fait":
        raise Refus("Cette relance est déjà faite.")
    verbe = "Marquer comme faite" if statut == "fait" else "Reporter de 3 jours"
    return f"{verbe} la relance « {relance.get('label') or ''} » (échéance {relance.get('due_date') or 'sans date'})", \
        {"relance_id": int(relance["id"]), "statut": statut}


def executer_statut_relance(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    relance = _relance(ctx, p.get("relance_id"))  # re-vérifié AU CLIC
    if relance.get("status") == "fait":
        raise Refus("cette relance a été faite entre-temps")
    _ecrire(ctx, "POST", "rpc/app_relance_set_status", {"p_relance_id": int(relance["id"]), "p_status": p["statut"]})
    apres = _relance(ctx, relance["id"])
    if apres.get("status") != p["statut"]:
        raise Refus("la relance n'a pas changé d'état (relu après l'écriture)")
    return {"relance_id": apres["id"], "statut": apres.get("status"), "echeance": apres.get("due_date")}


# ── le catalogue des gestes ───────────────────────────────────────────────────
class Geste:
    def __init__(self, nom: str, description: str, roles: frozenset[str], parametres: dict[str, Any],
                 preparer: Callable[[ContexteAssistant, dict[str, Any]], tuple[str, dict[str, Any]]],
                 executer: Callable[[ContexteAssistant, dict[str, Any]], dict[str, Any]]) -> None:
        self.nom, self.description, self.roles, self.parametres = nom, description, roles, parametres
        self.preparer, self.executer = preparer, executer


def _schema(proprietes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": proprietes, "required": list(proprietes), "additionalProperties": False}


GESTES: dict[str, Geste] = {g.nom: g for g in (
    Geste("demande_direction",
          "Prépare une DEMANDE À LA DIRECTION sur un bien : diffusion (validation et mise en ligne d'un mandat pas encore "
          "validé), baisse_prix (nouveau prix, mandat validé), annulation_mandat (mandat validé). Mêmes conditions que "
          "l'écran ; une seule demande en cours par type.",
          TOUS_LES_ROLES,
          _schema({"type": {"type": "string", "enum": list(TYPES_DEMANDE)},
                   "hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   "nouveau_prix": {"type": "string", "description": "baisse_prix seulement, en euros ; sinon vide"},
                   "commentaire": {"type": "string", "description": "le motif ou le contexte, pour la direction"}}),
          preparer_demande, executer_demande),
    Geste("creer_relance",
          "Prépare une RELANCE à faire pour un contact, à une date (elle revient à la personne qui parle).",
          TOUS_LES_ROLES,
          _schema({"hektor_contact_id": {"type": "string", "description": "numéro du contact (contacts)"},
                   "libelle": {"type": "string", "description": "intitulé court"},
                   "echeance": {"type": "string", "description": "AAAA-MM-JJ"},
                   "detail": {"type": "string", "description": "précision, ou vide"},
                   "hektor_annonce_id": {"type": "string", "description": "numéro d'annonce lié, ou vide"}}),
          preparer_relance, executer_relance),
    Geste("statut_relance",
          "Prépare le changement d'une relance : fait, ou reporte (+3 jours, comme l'écran).",
          TOUS_LES_ROLES,
          _schema({"relance_id": {"type": "integer", "description": "colonne id de relances"},
                   "statut": {"type": "string", "enum": ["fait", "reporte"]}}),
          preparer_statut_relance, executer_statut_relance),
)}


# ── la carte : ranger la proposition (clé de service, la table n'est écrite que par le serveur) ──
def _service(ctx: ContexteAssistant) -> dict[str, str]:
    cle = ctx.settings.supabase_service_role_key
    return {"apikey": cle, "Authorization": f"Bearer {cle}"}


def ranger_carte(ctx: ContexteAssistant, geste: Geste, resume: str, parametres: dict[str, Any]) -> dict[str, Any]:
    r = requests.post(f"{ctx.settings.supabase_url}/rest/v1/app_assistant_action",
                      headers={**_service(ctx), "Prefer": "return=representation"},
                      json=[{"conversation_id": ctx.conversation_id, "user_id": ctx.user_id, "user_email": ctx.email,
                             "geste": geste.nom, "parametres": parametres, "resume": resume}], timeout=15)
    if not r.ok or not (r.json() or []):
        raise LectureRefusee(f"carte non rangée ({r.status_code})")
    ligne = r.json()[0]
    carte = {"id": ligne["id"], "geste": geste.nom, "resume": resume, "expire_le": ligne.get("expire_le")}
    ctx.cartes.append(carte)
    return carte


def _proposer(geste: Geste) -> Callable[[ContexteAssistant, dict[str, Any]], dict[str, Any]]:
    def proposer(ctx: ContexteAssistant, params: dict[str, Any]) -> dict[str, Any]:
        resume, parametres = geste.preparer(ctx, params)
        carte = ranger_carte(ctx, geste, resume, parametres)
        return {"carte_proposee": True, "carte_id": carte["id"], "resume": resume,
                "a_dire": "Une carte est affichée à la personne : RIEN n'est fait tant qu'elle n'a pas cliqué « Valider ». "
                          "Ne dis jamais que c'est fait ; dis que tu as préparé la carte."}
    return proposer


FONCTIONS_GESTES: tuple[Fonction, ...] = tuple(
    Fonction(f"proposer_{g.nom}", g.description + " Rien n'est fait : une carte est proposée, la personne valide d'un clic.",
             g.roles, g.parametres, _proposer(g))
    for g in GESTES.values()
)
