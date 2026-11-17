from __future__ import annotations

import json
import re
import unicodedata
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

import requests
from fastapi import HTTPException

from ..auth import AuthenticatedUser
from .assistant_contexte import TOUS_LES_ROLES, ContexteAssistant, Fonction, LectureRefusee, Refus
from .email_tracking import EmailTrackingService
from .google_calendar_event_link_service import GoogleCalendarEventLinkService
from .google_workspace_service import GoogleWorkspaceService
from .rapprochement_email import RapprochementEmailService
from .rapprochement_sender import RapprochementSender
from .supabase_admin import SupabaseAdminService

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


# ── LOT 2a (13/11/2026) : chez nous seulement ────────────────────────────────
DIRECTION = frozenset({"admin", "manager"})


def _recherche(ctx: ContexteAssistant, cle: Any) -> dict[str, Any]:
    cle = str(cle or "").strip()
    if not cle:
        raise Refus("Donne la clé de la recherche (contact_search_key, objet recherches).")
    lignes = _lire(ctx, "app_contact_searches_current", {"contact_search_key": f"eq.{cle}", "limit": "1",
                                                         "select": "contact_search_key,hektor_contact_id,search_index,archive,is_active"})
    if not lignes:
        raise Refus(f"La recherche {cle} n'est pas parmi celles que tu peux voir.")
    return lignes[0]


def _acquereur(ctx: ContexteAssistant, recherche: dict[str, Any]) -> str:
    try:
        return str(_contact(ctx, recherche["hektor_contact_id"]).get("display_name") or recherche["hektor_contact_id"])
    except Refus:
        return str(recherche["hektor_contact_id"])


# Écran : RapprochementMandat.tsx:365 (« propose ») -- seul le canal TÉLÉPHONE enregistre directement ; l'e-mail
# s'enregistre APRÈS l'envoi et la visite APRÈS le rendez-vous (lot 3).
def preparer_proposition(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    recherche = _recherche(ctx, p.get("contact_search_key"))
    bien = _bien(ctx, p.get("hektor_annonce_id"))
    note = str(p.get("note") or "").strip()[:500]
    resume = f"Noter que l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » a été proposée par TÉLÉPHONE à " \
             f"{_acquereur(ctx, recherche)} (le bien passe « proposé » pour cette recherche, une relance de suivi est posée)"
    if note:
        resume += f". Note : {note}"
    return resume, {"contact_search_key": recherche["contact_search_key"], "hektor_annonce_id": int(bien["hektor_annonce_id"]),
                    "note": note}


def executer_proposition(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    recherche = _recherche(ctx, p.get("contact_search_key"))  # re-vérifié AU CLIC (fonction de la base sans contrôle)
    bien = _bien(ctx, p.get("hektor_annonce_id"))
    _ecrire(ctx, "POST", "rpc/app_record_proposition", {
        "p_search_key": recherche["contact_search_key"], "p_dossier_id": bien["app_dossier_id"], "p_channel": "telephone",
        "p_note": p.get("note") or None, "p_nego": ctx.email, "p_gmail_message_id": None, "p_gmail_thread_id": None})
    return {"contact_search_key": recherche["contact_search_key"], "app_dossier_id": bien["app_dossier_id"], "canal": "telephone"}


# Écran : RapprochementMandat.tsx:374 / 381 -- écarter, ou rétablir (« jamais_vu » efface le statut).
def preparer_statut_bien(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    statut = str(p.get("statut") or "").strip()
    if statut not in {"ecarte", "retabli"}:
        raise Refus("Statut : ecarte, ou retabli (le bien redevient « jamais vu » pour cette recherche).")
    recherche = _recherche(ctx, p.get("contact_search_key"))
    bien = _bien(ctx, p.get("hektor_annonce_id"))
    motif = str(p.get("motif") or "").strip()[:300]
    verbe = "Écarter" if statut == "ecarte" else "Rétablir"
    resume = f"{verbe} l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » pour la recherche de " \
             f"{_acquereur(ctx, recherche)}"
    if motif and statut == "ecarte":
        resume += f". Motif : {motif}"
    return resume, {"contact_search_key": recherche["contact_search_key"], "hektor_annonce_id": int(bien["hektor_annonce_id"]),
                    "statut": statut, "motif": motif}


def executer_statut_bien(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    recherche = _recherche(ctx, p.get("contact_search_key"))  # re-vérifié AU CLIC (fonction de la base sans contrôle)
    bien = _bien(ctx, p.get("hektor_annonce_id"))
    statut_base = "ecarte" if p.get("statut") == "ecarte" else "jamais_vu"
    _ecrire(ctx, "POST", "rpc/app_set_bien_statut", {
        "p_search_key": recherche["contact_search_key"], "p_dossier_id": bien["app_dossier_id"], "p_status": statut_base,
        "p_reason": (p.get("motif") or None) if statut_base == "ecarte" else None, "p_nego": ctx.email})
    return {"contact_search_key": recherche["contact_search_key"], "app_dossier_id": bien["app_dossier_id"], "statut": statut_base}


# Notifications : la fonction de la base (app_mark_notification_read) marque n'importe laquelle -- l'assistant ne
# marque que celles de la PERSONNE (même filtre que l'écran, App.tsx:26315), relues avec le jeton.
MAX_NOTIFICATIONS = 500


def _mes_notifications(ctx: ContexteAssistant, ids: list[int], genre: str) -> list[dict[str, Any]]:
    params = {"negociateur_email": f"eq.{ctx.email}", "read_at": "is.null", "select": "id,type,title",
              "order": "id.asc", "limit": str(MAX_NOTIFICATIONS)}
    if ids:
        params["id"] = f"in.({','.join(str(i) for i in ids)})"
    if genre:
        params["type"] = f"eq.{genre}"
    return _lire(ctx, "app_notification", params)


def preparer_notifications(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    morceaux = [x.strip() for x in str(p.get("notification_ids") or "").split("|") if x.strip()]
    if any(not x.isdigit() for x in morceaux):
        raise Refus("Les numéros de notification sont des nombres séparés par | (ou laisse vide).")
    ids = [int(x) for x in morceaux][:MAX_NOTIFICATIONS]
    genre = str(p.get("type") or "").strip()
    lignes = _mes_notifications(ctx, ids, genre)
    if not lignes:
        raise Refus("Aucune notification non lue à toi ne correspond.")
    quoi = f"« {genre} »" if genre else ("choisies" if ids else "non lues")
    return f"Marquer comme lues {len(lignes)} de tes notifications {quoi}", \
        {"notification_ids": [int(x["id"]) for x in lignes]}


def executer_notifications(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    ids = [int(x) for x in (p.get("notification_ids") or [])][:MAX_NOTIFICATIONS]
    miennes = _mes_notifications(ctx, ids, "") if ids else []  # re-vérifié AU CLIC : seulement les siennes, encore non lues
    for ligne in miennes:
        _ecrire(ctx, "POST", "rpc/app_mark_notification_read", {"p_id": int(ligne["id"])})
    return {"marquees": len(miennes), "deja_lues_ou_absentes": len(ids) - len(miennes)}


# Note de transaction : la fonction de la base contrôle (direction + accès au dossier) et REMPLACE la note.
def _note_actuelle(ctx: ContexteAssistant, affaire_id: int) -> str | None:
    if not _lire(ctx, "app_affaire_ledger", {"app_affaire_id": f"eq.{affaire_id}", "select": "app_affaire_id", "limit": "1"}):
        raise Refus(f"La transaction {affaire_id} n'est pas parmi celles que tu peux voir.")
    # ⚠ app_affaire_note est lisible par tous : lue SEULEMENT après la transaction (règle de l'étape 2)
    notes = _lire(ctx, "app_affaire_note", {"app_affaire_id": f"eq.{affaire_id}", "select": "texte", "limit": "1"})
    return (notes[0].get("texte") if notes else None) or None


def preparer_note(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    try:
        affaire = int(p.get("app_affaire_id"))
    except (TypeError, ValueError):
        raise Refus("Donne l'app_affaire_id de la transaction (objet transactions).") from None
    texte = str(p.get("texte") or "").strip()[:4000]
    if not texte:
        raise Refus("Donne le texte de la note.")
    avant = _note_actuelle(ctx, affaire)
    resume = f"Écrire la note de la transaction {affaire} : « {texte} »"
    resume += f" — ⚠ elle REMPLACE la note actuelle : « {avant[:300]} »" if avant else " (pas de note aujourd'hui)"
    return resume, {"app_affaire_id": affaire, "texte": texte}


def executer_note(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    _note_actuelle(ctx, int(p["app_affaire_id"]))
    r = _ecrire(ctx, "POST", "rpc/app_affaire_note_ecrire", {"target_affaire_id": int(p["app_affaire_id"]), "texte": p["texte"]})
    if not (r or {}).get("ok"):
        raise Refus("la note n'a pas été écrite (la base n'a pas confirmé)")
    return {"app_affaire_id": int(p["app_affaire_id"])}


# ── VAGUE C (16/11/2026) : les gestes de la DIRECTION sur une transaction ─────────
# Note : notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md §29 bis-30. Décision « Oui sans » (sans les suppressions).
# ⛔ La MÊME fonction de la base que l'écran (handleGesteHektor, App.tsx:20021 → app_geste_affaire_optimistic) : elle
#   porte TOUTES les règles (direction seulement, accès au dossier, geste qui va avec le type, offre verrouillée par son
#   compromis, compromis verrouillé par sa vente, numéro Hektor exigé, cascade de l'annulation). Pas de deuxième porte.
# ⛔ DROITS : direction seulement (admin, manager), comme l'écran et la base ; un négociateur n'a pas la fonction.
# ⛔ Les suppressions (compromis, vente) ne sont PAS ouvertes : irréversibles, réservées aux essais et corrections.
# Les verrous sont relus ici AVANT la carte pour dire pourquoi ; la base les rejuge au clic.
GESTES_TRANSACTION = {"accepter": ("accepte", "offre", "Accepter l'offre"),
                      "refuser": ("refus", "offre", "Refuser l'offre"),
                      "annuler": ("annuler", "compromis", "Annuler le compromis")}
_VIVANTE = "present_in_hektor"


def _affaire(ctx: ContexteAssistant, numero: Any) -> dict[str, Any]:
    try:
        affaire = int(numero)
    except (TypeError, ValueError):
        raise Refus("Donne l'app_affaire_id de la transaction (objet transactions ou dossiers).") from None
    lignes = _lire(ctx, "app_affaire_ledger", {"app_affaire_id": f"eq.{affaire}", "limit": "1",
                                               "select": "app_affaire_id,kind,state,hektor_affaire_id,hektor_annonce_id,"
                                                         "app_dossier_id,app_chaine_id,montant,date," + _VIVANTE})
    if not lignes:
        raise Refus(f"La transaction {affaire} n'est pas parmi celles que tu peux voir.")
    return lignes[0]


def _morte(ligne: dict[str, Any]) -> bool:  # = « supprimée chez Hektor » dans la fonction de la base
    return bool(str(ligne.get("hektor_affaire_id") or "").strip()) and ligne.get(_VIVANTE) is False


def _verrou(ctx: ContexteAssistant, a: dict[str, Any]) -> str | None:
    if not a.get("app_chaine_id"):
        return None
    autres = [l for l in _lire(ctx, "app_affaire_ledger", {
        "app_chaine_id": f"eq.{a['app_chaine_id']}", "app_affaire_id": f"neq.{a['app_affaire_id']}",
        "select": "kind,state,hektor_affaire_id," + _VIVANTE}) if not _morte(l)]
    if a["kind"] == "offre":
        for l in sorted(autres, key=lambda x: 0 if x.get("kind") == "vente" else 1):
            if l.get("kind") == "vente" or (l.get("kind") == "compromis"
                                            and str(l.get("state") or "").lower() not in ("cancelled", "annule")):
                quoi = "une vente" if l["kind"] == "vente" else "un compromis en cours"
                return f"ce dossier porte {quoi} (n° {l.get('hektor_affaire_id') or '?'}) : lève-le d'abord avant de revenir " \
                       "sur l'offre (règle de la base)."
    if a["kind"] == "compromis":
        vente = next((l for l in autres if l.get("kind") == "vente"), None)
        if vente:
            return f"ce dossier porte une vente (n° {vente.get('hektor_affaire_id') or '?'}) : après la vente tout est " \
                   "verrouillé ; il faut d'abord supprimer la vente, depuis l'écran."
    return None


def preparer_transaction(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    choix = str(p.get("geste") or "").strip()
    if choix not in GESTES_TRANSACTION:
        raise Refus("Geste : accepter ou refuser (une offre), annuler (un compromis). Les suppressions se font à l'écran.")
    geste, genre, libelle = GESTES_TRANSACTION[choix]
    a = _affaire(ctx, p.get("app_affaire_id"))
    if a.get("kind") != genre:
        raise Refus(f"« {choix} » va avec {('une ' if genre == 'offre' else 'un ')}{genre}, et la transaction "
                    f"{a['app_affaire_id']} est {('une ' if a.get('kind') in ('offre', 'vente') else 'un ')}{a.get('kind')}.")
    if _morte(a):
        raise Refus("Cette transaction a été supprimée chez Hektor.")
    if not str(a.get("hektor_affaire_id") or "").strip():
        raise Refus("Cette transaction n'a pas encore de numéro Hektor : le geste ne peut pas partir (comme à l'écran).")
    cible = {"accepte": "accepted", "refus": "refused", "annuler": "cancelled"}[geste]
    if str(a.get("state") or "") == cible:
        raise Refus("Cette transaction est déjà dans cet état : rien à faire.")
    verrou = _verrou(ctx, a)
    if verrou:
        raise Refus(verrou[0].upper() + verrou[1:])
    montant = f", {_euros(a['montant'])}" if a.get("montant") else ""
    resume = f"{libelle} n° {a['hektor_affaire_id']} (annonce {a.get('hektor_annonce_id')}{montant}) — écrit chez nous tout de " \
             "suite, puis chez Hektor ; si Hektor refuse, l'état d'avant est remis."
    if geste == "annuler":
        resume += " ⚠ L'offre acceptée de ce même dossier peut être refusée avec lui (cascade de la base)."
    return resume, {"app_affaire_id": int(a["app_affaire_id"]), "geste": choix}


def executer_transaction(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    choix = str(p.get("geste") or "")
    if choix not in GESTES_TRANSACTION:
        raise Refus("geste inconnu")
    a = _affaire(ctx, p.get("app_affaire_id"))  # re-lue AU CLIC ; la base rejuge droits et verrous
    r = _ecrire(ctx, "POST", "rpc/app_geste_affaire_optimistic",
                {"target_affaire_id": int(a["app_affaire_id"]), "geste": GESTES_TRANSACTION[choix][0], "job_priority": 7}) or {}
    if r.get("deja_dans_cet_etat"):
        raise Refus("la transaction était déjà dans cet état : rien n'a été envoyé")
    if not r.get("ok"):
        raise Refus("la base n'a pas confirmé le geste")
    return {"app_affaire_id": int(a["app_affaire_id"]), "etat_avant": r.get("etat_avant"), "etat_apres": r.get("etat_apres"),
            "travail": r.get("job_id"), "offres_refusees_en_cascade": r.get("offres_refusees_en_cascade")}


# ── LOT 2b (13/11/2026) : vers Hektor (la base écrit chez nous à l'instant, le worker recopie chez Hektor) ──
# Modifier un contact : app_edit_contact_optimistic contrôle l'appelant et accepte une modification PARTIELLE.
# ⚠ L'écran envoie toujours la fiche complète ; l'assistant n'envoie QUE les champs changés (téléphone, e-mail,
#   commentaire) -- chemin à éprouver en réel sur un contact d'essai avant de s'en servir (note étape 3 §7).
# ⛔ Pas l'adresse ni la ville : leur envoi à Hektor dépend des identifiants de commune (leçon du 22/10).
_CHAMPS_CONTACT = (("telephone", "phone", "phone_primary", "téléphone"), ("email", "email", "email", "e-mail"),
                   ("commentaire", "comments", "commentaires", "commentaire"))


def _fiche_contact(ctx: ContexteAssistant, numero: Any) -> dict[str, Any]:
    numero = str(numero or "").strip()
    if not numero.isdigit():
        raise Refus("Donne le numéro du contact (hektor_contact_id, objet contacts).")
    lignes = _lire(ctx, "app_contacts_current", {"hektor_contact_id": f"eq.{numero}", "limit": "1",
                                                 "select": "hektor_contact_id,display_name,nom,phone_primary,email,commentaires,"
                                                           "archive,active_search_count"})
    if not lignes:
        raise Refus(f"Le contact {numero} n'est pas parmi ceux que tu peux voir.")
    return lignes[0]


def preparer_modif_contact(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    fiche = _fiche_contact(ctx, p.get("hektor_contact_id"))
    changements: dict[str, str] = {}
    lignes = []
    for cle, champ, colonne, libelle in _CHAMPS_CONTACT:
        nouveau = str(p.get(cle) or "").strip()
        if nouveau and nouveau != str(fiche.get(colonne) or "").strip():
            if cle == "email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", nouveau):
                raise Refus(f"« {nouveau} » n'est pas une adresse e-mail.")
            changements[champ] = nouveau[:2000]
            lignes.append(f"{libelle} : « {fiche.get(colonne) or 'vide'} » → « {nouveau[:200]} »")
    if not changements:
        raise Refus("Rien ne change : donne au moins un téléphone, un e-mail ou un commentaire différent de la fiche.")
    return f"Modifier {fiche.get('display_name') or fiche['hektor_contact_id']} — " + " ; ".join(lignes) + \
        " (écrit chez nous tout de suite, recopié chez Hektor ensuite)", \
        {"hektor_contact_id": fiche["hektor_contact_id"], "champs": changements}


def executer_modif_contact(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    fiche = _fiche_contact(ctx, p.get("hektor_contact_id"))
    champs = {k: v for k, v in dict(p.get("champs") or {}).items() if k in {c[1] for c in _CHAMPS_CONTACT}}
    if not champs:
        raise Refus("aucun champ à modifier")
    # ⚠ Prouvé en réel le 13/11 (travail 7f12ad3a, « Nom contact requis ») : le worker EXIGE le nom à chaque
    #   modification, même inchangé (normalizeHektorContactPayload requireName). Il relit la fiche Hektor et ne
    #   change que les champs reçus : renvoyer le nom ACTUEL ne modifie rien. Sans nom connu : on ne lance rien.
    nom = str(fiche.get("nom") or "").strip()
    if not nom:
        raise Refus("ce contact n'a pas de nom chez nous : Hektor refuserait la modification")
    champs = {"last_name": nom, **champs}
    r = _ecrire(ctx, "POST", "rpc/app_edit_contact_optimistic",
                {"target_contact_id": p["hektor_contact_id"], "edit_fields": champs, "debounce_seconds": 600})
    return {"hektor_contact_id": p["hektor_contact_id"], "champs": sorted(champs), "reponse": r}


def preparer_archivage_contact(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    fiche = _fiche_contact(ctx, p.get("hektor_contact_id"))
    archiver = bool(p.get("archiver"))
    if bool(fiche.get("archive")) == archiver:
        raise Refus("Ce contact est déjà archivé." if archiver else "Ce contact n'est pas archivé.")
    nom = fiche.get("display_name") or fiche["hektor_contact_id"]
    if archiver:
        n = int(fiche.get("active_search_count") or 0)
        resume = f"Archiver {nom}" + (f" — ⚠ ses {n} recherche(s) active(s) seront archivées aussi (règle de Hektor)" if n else "")
    else:
        resume = f"Réactiver {nom} — ⚠ ses recherches archivées ne reviennent PAS d'elles-mêmes"
    return resume, {"hektor_contact_id": fiche["hektor_contact_id"], "archiver": archiver}


def executer_archivage_contact(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    _ecrire(ctx, "POST", "rpc/app_console_archiver_contact_optimistic",
            {"p_hektor_contact_id": p["hektor_contact_id"], "p_archive": bool(p["archiver"])})
    return {"hektor_contact_id": p["hektor_contact_id"], "archive": bool(p["archiver"])}


def preparer_archivage_recherche(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    recherche = _recherche(ctx, p.get("contact_search_key"))
    if recherche.get("archive") is True:
        raise Refus("Cette recherche est déjà archivée.")
    if recherche.get("search_index") is None:
        raise Refus("Cette recherche n'a pas de rang chez Hektor : l'écran ne peut pas l'archiver non plus.")
    return f"Archiver la recherche de {_acquereur(ctx, recherche)} (recherche n° {int(recherche['search_index']) + 1})", \
        {"contact_search_key": recherche["contact_search_key"]}


def executer_archivage_recherche(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    recherche = _recherche(ctx, p.get("contact_search_key"))  # le rang est RELU au clic (il peut bouger)
    if recherche.get("archive") is True:
        raise Refus("cette recherche a été archivée entre-temps")
    _ecrire(ctx, "POST", "rpc/app_console_create_delete_contact_search_job", {
        "target_contact_id": recherche["hektor_contact_id"], "search_index": int(recherche["search_index"]),
        "target_critere_id": None, "job_priority": 14})
    return {"contact_search_key": recherche["contact_search_key"]}


# ── LOT 3a (13/11/2026) : l'agenda Google DE LA PERSONNE, sans invitation ──────
# Note : notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md §10-11.
# ⛔ Toujours SON agenda (jamais celui d'un collègue, même pour la direction) ; la garde est celle de l'écran
#   (assert_calendar_subject_allowed : compte Google relié).
# ⛔ Jamais d'invité ni de notification (sendUpdates « none ») : l'écran, lui, envoie TOUJOURS de vraies invitations
#   Google à tous les invités (App.tsx:39262) -- l'envoi vers un client est le lot 3c, pas ouvert.
# ⛔ Déplacer ou supprimer : seulement un RDV posé par l'app (il a sa ligne dans app_google_calendar_event_link,
#   comme à l'écran) ET sans aucun invité -- le changer en silence toucherait l'agenda de quelqu'un d'autre.
# ⚠ Supprimer un RDV de visite ne remet PAS le bien à « jamais vu » (l'écran le fait, App.tsx:25347, et efface ainsi
#   un « proposé » d'avant : défaut n° 3 de l'audit) -- la carte le dit.
TYPES_RDV = {"visite": "Visite", "estimation": "Estimation", "mandat": "Mandat", "compromis": "Compromis",
             "relance": "Relance", "agence": "Agence", "autre": "Rendez-vous"}
PARIS = ZoneInfo("Europe/Paris")
_JOURS = ("lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim.")
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
MAX_JOURS_AGENDA = 31


def _personne(ctx: ContexteAssistant) -> tuple[str, AuthenticatedUser]:
    email = (ctx.email or "").strip().lower()
    if not email:
        raise Refus("Ton compte n'a pas d'adresse : pas d'agenda ni de boîte Google.")
    return email, AuthenticatedUser(id=ctx.user_id, email=email)


def _mon_agenda(ctx: ContexteAssistant) -> str:
    email, user = _personne(ctx)
    try:
        SupabaseAdminService(ctx.settings).assert_calendar_subject_allowed(user, email)
    except HTTPException as exc:
        raise Refus(f"Ton agenda Google n'est pas ouvert à l'application ({exc.detail}).") from None
    return email


def _google(appel: Callable[[], dict[str, Any]], quoi: str) -> dict[str, Any]:
    # Google répond ok / pas ok ; une erreur de saisie (ValueError) ou de jeton (RuntimeError) devient une phrase
    try:
        r = appel()
    except ValueError as exc:
        raise Refus(f"{quoi} : {exc}") from None
    except RuntimeError:
        raise Refus(f"{quoi} : Google n'a pas pu être joint.") from None
    if not r.get("ok"):
        raise Refus(f"{quoi} : Google a refusé ({r.get('statusCode')}).")
    return r


def _quand(instant: datetime) -> str:
    local = instant.astimezone(PARIS)
    return f"{_JOURS[local.weekday()]} {local.strftime('%d/%m/%Y %H:%M')}"


def _instant(texte: Any) -> datetime:
    brut = str(texte or "").strip().replace(" ", "T")
    if len(brut) < 16:
        raise Refus("Donne la date ET l'heure, au format AAAA-MM-JJTHH:MM (heure de Paris).")
    try:
        valeur = datetime.fromisoformat(brut)
    except ValueError:
        raise Refus("Donne la date ET l'heure, au format AAAA-MM-JJTHH:MM (heure de Paris).") from None
    return valeur if valeur.tzinfo else valeur.replace(tzinfo=PARIS)


def _jour(texte: Any, defaut: datetime) -> tuple[datetime, bool]:
    brut = str(texte or "").strip().replace(" ", "T")
    if not brut:
        return defaut, False
    try:
        valeur = datetime.fromisoformat(brut)
    except ValueError:
        raise Refus("Une date s'écrit AAAA-MM-JJ, ou AAAA-MM-JJTHH:MM.") from None
    return (valeur if valeur.tzinfo else valeur.replace(tzinfo=PARIS)), len(brut) <= 10


def lire_mon_agenda(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    email = _mon_agenda(ctx)
    aujourdhui = datetime.now(PARIS).replace(hour=0, minute=0, second=0, microsecond=0)
    debut, _ = _jour(p.get("debut"), aujourdhui)
    fin, jour_seul = _jour(p.get("fin"), debut + timedelta(days=1))
    if jour_seul:
        fin += timedelta(days=1)  # « jusqu'au 20/11 » = le 20/11 compris
    if fin <= debut:
        raise Refus("La fin doit venir après le début.")
    if fin - debut > timedelta(days=MAX_JOURS_AGENDA):
        raise Refus(f"Au plus {MAX_JOURS_AGENDA} jours à la fois.")
    r = _google(lambda: GoogleWorkspaceService(ctx.settings).list_calendar_events(
        subject_email=email, time_min=debut.isoformat(), time_max=fin.isoformat(), max_results=50), "Lecture de ton agenda")
    evenements = [e for e in r.get("events") or [] if isinstance(e, dict) and e.get("status") != "cancelled"]
    ids = [str(e.get("id")) for e in evenements if e.get("id")]
    liens: dict[str, dict[str, Any]] = {}
    if ids:
        for ligne in _lire(ctx, "app_google_calendar_event_link", {
                "google_calendar_email": f"eq.{email}", "status": "eq.active",
                "google_event_id": "in.(" + ",".join('"' + i.replace('"', "") + '"' for i in ids) + ")",
                "select": "id,google_event_id,event_type,hektor_annonce_id,hektor_contact_id"}):
            liens[str(ligne.get("google_event_id"))] = ligne
    domaine = "@" + ctx.settings.google_workspace_domain
    rdv = []
    for e in evenements:
        debut_e, fin_e = e.get("start") or {}, e.get("end") or {}
        journee = "dateTime" not in debut_e
        invites = [a for a in e.get("attendees") or [] if isinstance(a, dict) and not a.get("self")]
        lien = liens.get(str(e.get("id"))) or {}
        ligne = {
            "debut": _quand(datetime.fromisoformat(debut_e["dateTime"])) if not journee else f"{debut_e.get('date')} (journée)",
            "fin": datetime.fromisoformat(fin_e["dateTime"]).astimezone(PARIS).strftime("%H:%M") if not journee else None,
            "titre": str(e.get("summary") or "(sans titre)")[:200],
            "lieu": str(e.get("location") or "")[:200] or None,
            # ⛔ jamais les adresses des invités ni de l'organisateur : seulement combien
            "invites": len(invites),
            "invites_exterieurs": sum(1 for a in invites if not str(a.get("email") or "").lower().endswith(domaine)),
            "rdv_app": lien.get("id"),
        }
        if lien:
            ligne.update({"type": lien.get("event_type"), "hektor_annonce_id": lien.get("hektor_annonce_id"),
                          "hektor_contact_id": lien.get("hektor_contact_id")})
        rdv.append(ligne)
    return {"periode": f"du {_quand(debut)} au {_quand(fin)}", "nombre": len(rdv), "rendez_vous": rdv,
            "suite_non_lue": bool(r.get("hasMore")),
            "a_savoir": "rdv_app = numéro du RDV posé par l'application : seuls ceux-là, et sans invités, peuvent être "
                        "déplacés ou supprimés par l'assistant."}


def _liens_rdv(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict | None, dict | None, dict | None]:
    annonce = str(p.get("hektor_annonce_id") or "").strip()
    bien = _bien(ctx, annonce) if annonce and annonce != "0" else None
    numero = str(p.get("hektor_contact_id") or "").strip()
    contact = _contact(ctx, numero) if numero else None
    cle = str(p.get("contact_search_key") or "").strip()
    recherche = _recherche(ctx, cle) if cle else None
    if recherche:
        if contact and str(contact["hektor_contact_id"]) != str(recherche["hektor_contact_id"]):
            raise Refus("Cette recherche n'est pas celle de ce contact.")
        contact = contact or _contact(ctx, recherche["hektor_contact_id"])
    return bien, contact, recherche


def _duree(valeur: Any) -> timedelta:
    try:
        minutes = int(valeur)
    except (TypeError, ValueError):
        minutes = 0
    if not 5 <= minutes <= 600:
        raise Refus("Donne la durée en minutes (entre 5 et 600).")
    return timedelta(minutes=minutes)


def preparer_rdv(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    email = _mon_agenda(ctx)
    genre = str(p.get("type") or "").strip()
    if genre not in TYPES_RDV:
        raise Refus("Type : " + ", ".join(TYPES_RDV) + ".")
    titre = str(p.get("titre") or "").strip()[:240]
    if not titre:
        raise Refus("Donne le titre du rendez-vous.")
    debut = _instant(p.get("debut"))
    if debut < datetime.now(timezone.utc):
        raise Refus("Ce créneau est déjà passé.")
    fin = debut + _duree(p.get("duree_minutes"))
    bien, contact, recherche = _liens_rdv(ctx, p)
    if genre == "visite" and recherche and not bien:
        raise Refus("Pour une visite liée à une recherche, donne aussi le numéro d'annonce du bien visité.")
    lieu = str(p.get("lieu") or "").strip()[:500]
    note = str(p.get("note") or "").strip()[:2000]
    resume = f"Créer dans TON agenda : {TYPES_RDV[genre]} « {titre} » — {_quand(debut)} → {fin.astimezone(PARIS):%H:%M}"
    if lieu:
        resume += f", {lieu}"
    if bien:
        resume += f" ; bien : annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} »"
    if contact:
        resume += f" ; contact : {contact.get('display_name') or contact['hektor_contact_id']}"
    resume += ". Aucune invitation n'est envoyée : personne d'autre n'est prévenu."
    if genre == "visite" and recherche and bien:
        resume += " Le bien passe « visite » pour cette recherche (comme l'écran)."
    try:
        dispo = GoogleWorkspaceService(ctx.settings).check_calendar_availability(
            subject_email=email, start_at=debut.isoformat(), end_at=fin.isoformat(),
            requested_by=ctx.user_id, requested_by_email=email)
        if dispo.get("ok") and int(dispo.get("busyCount") or 0):
            resume += f" ⚠ Tu es déjà pris sur ce créneau ({dispo['busyCount']} occupation(s))."
    except Exception:  # noqa: BLE001 -- la disponibilité n'est qu'une indication
        resume += " (Disponibilité non vérifiée.)"
    return resume, {"type": genre, "titre": titre, "debut": debut.isoformat(), "fin": fin.isoformat(), "lieu": lieu,
                    "note": note, "hektor_annonce_id": int(bien["hektor_annonce_id"]) if bien else None,
                    "hektor_contact_id": str(contact["hektor_contact_id"]) if contact else None,
                    "contact_search_key": recherche["contact_search_key"] if recherche else None}


def executer_rdv(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    return _poser_rdv(ctx, p, invites=[])


def _poser_rdv(ctx: ContexteAssistant, p: dict[str, Any], invites: list[str]) -> dict[str, Any]:
    # invites vide = SON agenda seulement (lot 3a) ; sinon = l'adresse du client, relue au clic (lot 3c)
    email = _mon_agenda(ctx)  # re-vérifié AU CLIC
    genre = str(p.get("type") or "")
    if genre not in TYPES_RDV:
        raise Refus("type de rendez-vous inconnu")
    debut, fin = datetime.fromisoformat(p["debut"]), datetime.fromisoformat(p["fin"])
    if debut < datetime.now(timezone.utc):
        raise Refus("ce créneau est passé entre-temps")
    bien, contact, recherche = _liens_rdv(ctx, p)
    prevenir = "all" if invites else "none"
    r = _google(lambda: GoogleWorkspaceService(ctx.settings).create_calendar_event(
        subject_email=email, summary=p["titre"], start_at=debut.isoformat(), end_at=fin.isoformat(),
        description=p.get("note") or None, location=p.get("lieu") or None, attendees=invites, send_updates=prevenir,
        dry_run=False, requested_by=ctx.user_id, requested_by_email=email), "Création du rendez-vous")
    evenement = r.get("event") if isinstance(r.get("event"), dict) else {}
    try:
        lien = GoogleCalendarEventLinkService(ctx.settings).create_link(
            event_type=genre, related_entity_type="annonce" if bien else ("contact" if contact else "other"),
            related_entity_id=str(bien["hektor_annonce_id"]) if bien else (str(contact["hektor_contact_id"]) if contact else None),
            app_dossier_id=bien["app_dossier_id"] if bien else None,
            hektor_annonce_id=int(bien["hektor_annonce_id"]) if bien else None,
            hektor_contact_id=str(contact["hektor_contact_id"]) if contact else None,
            calendar_email=email, google_event_id=str(r.get("eventId") or ""), google_html_link=r.get("htmlLink"),
            summary=p["titre"], location=p.get("lieu") or None,
            starts_at=str((evenement.get("start") or {}).get("dateTime") or debut.isoformat()),
            ends_at=str((evenement.get("end") or {}).get("dateTime") or fin.isoformat()), attendees=invites,
            metadata_json={"source": "assistant", "send_updates": prevenir, "has_description": bool(p.get("note")),
                           **({"contact_search_key": recherche["contact_search_key"]} if recherche else {})},
            created_by=ctx.user_id, created_by_email=email)
    except Exception:  # noqa: BLE001 -- le RDV EXISTE chez Google : on le dit, on ne prétend pas l'inverse
        lien = None
    statut_visite = None
    if genre == "visite" and recherche and bien:
        try:  # = onCreated de l'écran (App.tsx:25538), au mieux comme lui
            _ecrire(ctx, "POST", "rpc/app_set_bien_statut", {
                "p_search_key": recherche["contact_search_key"], "p_dossier_id": bien["app_dossier_id"],
                "p_status": "visite", "p_reason": None, "p_nego": email})
            statut_visite = True
        except Refus:
            statut_visite = False
    return {"rdv_app": (lien or {}).get("id"), "dans_google": True, "relie_a_l_app": bool(lien),
            "debut": _quand(debut), "statut_visite": statut_visite, "invitation_envoyee": bool(invites)}


def _mon_rdv(ctx: ContexteAssistant, rdv_id: Any) -> tuple[str, dict[str, Any]]:
    email = _mon_agenda(ctx)
    numero = str(rdv_id or "").strip()
    if not _UUID.fullmatch(numero):
        raise Refus("Donne le numéro du rendez-vous (rdv_app, rendu par la lecture de l'agenda).")
    lignes = _lire(ctx, "app_google_calendar_event_link", {
        "id": f"eq.{numero}", "limit": "1",
        "select": "id,google_calendar_email,google_event_id,event_type,summary,location,starts_at,ends_at,attendees_json,"
                  "status,metadata_json"})
    if not lignes:
        raise Refus("Ce rendez-vous n'est pas parmi ceux que tu peux voir.")
    rdv = lignes[0]
    if rdv.get("status") != "active":
        raise Refus("Ce rendez-vous a déjà été supprimé.")
    if str(rdv.get("google_calendar_email") or "").lower() != email:
        raise Refus("Ce rendez-vous est dans l'agenda d'un collègue : l'assistant ne touche qu'à TON agenda.")
    if [a for a in rdv.get("attendees_json") or [] if str(a or "").strip()]:
        raise Refus("Ce rendez-vous a des invités : le changer les toucherait sans les prévenir. Fais-le depuis l'écran.")
    return email, rdv


def preparer_deplacer_rdv(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    _, rdv = _mon_rdv(ctx, p.get("rdv_id"))
    avant_debut, avant_fin = datetime.fromisoformat(rdv["starts_at"]), datetime.fromisoformat(rdv["ends_at"])
    debut = _instant(p.get("debut")) if str(p.get("debut") or "").strip() else avant_debut
    fin = debut + (_duree(p.get("duree_minutes")) if int(p.get("duree_minutes") or 0) else avant_fin - avant_debut)
    titre = str(p.get("titre") or "").strip()[:240] or str(rdv.get("summary") or "")
    lieu = str(p.get("lieu") or "").strip()[:500] or str(rdv.get("location") or "")
    if (debut, fin, titre, lieu) == (avant_debut, avant_fin, rdv.get("summary") or "", rdv.get("location") or ""):
        raise Refus("Rien ne change : donne un nouvel horaire, une durée, un titre ou un lieu.")
    if debut < datetime.now(timezone.utc):
        raise Refus("Ce créneau est déjà passé.")
    morceaux = []
    if (debut, fin) != (avant_debut, avant_fin):
        morceaux.append(f"{_quand(avant_debut)} → {_quand(debut)}–{fin.astimezone(PARIS):%H:%M}")
    if titre != (rdv.get("summary") or ""):
        morceaux.append(f"titre « {titre} »")
    if lieu != (rdv.get("location") or ""):
        morceaux.append(f"lieu « {lieu} »")
    return f"Modifier dans TON agenda « {rdv.get('summary') or ''} » : " + " ; ".join(morceaux) + \
        ". Personne n'est prévenu (pas d'invité).", \
        {"rdv_id": rdv["id"], "debut": debut.isoformat(), "fin": fin.isoformat(), "titre": titre, "lieu": lieu}


def executer_deplacer_rdv(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    email, rdv = _mon_rdv(ctx, p.get("rdv_id"))  # re-vérifié AU CLIC (un invité a pu être ajouté depuis l'écran)
    debut, fin = datetime.fromisoformat(p["debut"]), datetime.fromisoformat(p["fin"])
    _google(lambda: GoogleWorkspaceService(ctx.settings).update_calendar_event(
        subject_email=email, event_id=str(rdv["google_event_id"]), summary=p.get("titre") or None,
        start_at=debut.isoformat(), end_at=fin.isoformat(), description=None, location=p.get("lieu") or None,
        attendees=None, send_updates="none", dry_run=False, requested_by=ctx.user_id, requested_by_email=email),
        "Modification du rendez-vous")
    try:
        GoogleCalendarEventLinkService(ctx.settings).update_link(
            link_id=rdv["id"], updated_by=ctx.user_id, updated_by_email=email, summary=p.get("titre") or None,
            location=p.get("lieu") or None, starts_at=debut.isoformat(), ends_at=fin.isoformat(),
            metadata_patch={**(rdv.get("metadata_json") or {}), "last_send_updates": "none", "modifie_par": "assistant"})
        relie = True
    except Exception:  # noqa: BLE001 -- Google est à jour ; seule notre copie est en retard : on le dit
        relie = False
    return {"rdv_app": rdv["id"], "debut": _quand(debut), "copie_app_a_jour": relie}


def preparer_supprimer_rdv(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    _, rdv = _mon_rdv(ctx, p.get("rdv_id"))
    resume = f"Supprimer de TON agenda « {rdv.get('summary') or ''} » du {_quand(datetime.fromisoformat(rdv['starts_at']))}. " \
             "Personne n'est prévenu (pas d'invité)."
    if rdv.get("event_type") == "visite" and (rdv.get("metadata_json") or {}).get("contact_search_key"):
        resume += " ⚠ Le bien reste « visite » pour la recherche : l'assistant ne le remet pas à « jamais vu » " \
                  "(l'écran le fait, et efface ainsi un « proposé » d'avant). Rétablis ou écarte le bien si besoin."
    return resume, {"rdv_id": rdv["id"]}


def executer_supprimer_rdv(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    email, rdv = _mon_rdv(ctx, p.get("rdv_id"))  # re-vérifié AU CLIC
    _google(lambda: GoogleWorkspaceService(ctx.settings).delete_calendar_event(
        subject_email=email, event_id=str(rdv["google_event_id"]), send_updates="none",
        requested_by=ctx.user_id, requested_by_email=email), "Suppression du rendez-vous")
    try:
        GoogleCalendarEventLinkService(ctx.settings).mark_deleted(link_id=rdv["id"], updated_by=ctx.user_id,
                                                                  updated_by_email=email)
        relie = True
    except Exception:  # noqa: BLE001
        relie = False
    return {"rdv_app": rdv["id"], "supprime_de_google": True, "copie_app_a_jour": relie}


# ── LOT 3b (13/11/2026) : les e-mails, EN INTERNE seulement ───────────────────
# ⛔ L'e-mail libre de l'écran part en réel hors de tout interrupteur (route /google-workspace/gmail/send, dryRun
#   False par défaut) : l'assistant, lui, n'envoie QU'À DES ADRESSES DU DOMAINE (vérifié à la carte ET au clic),
#   sans pièce jointe, depuis la boîte de la personne (même garde que l'écran : assert_gmail_subject_allowed).
# ⛔ Le rapprochement n'est qu'un APERÇU (une lecture) : rien ne part, rien n'est enregistré.
MAX_DESTINATAIRES = 10
MAX_TEXTE_EMAIL = 3000
_ADRESSE = re.compile(r"[^@\s|,;]+@[^@\s|,;]+\.[^@\s|,;]+")
_LIEN = re.compile(r"https?://[^\s)\]>\"']+")


def _ma_boite(ctx: ContexteAssistant) -> str:
    email, user = _personne(ctx)
    try:
        SupabaseAdminService(ctx.settings).assert_gmail_subject_allowed(user, email)
    except HTTPException as exc:
        raise Refus(f"Ta boîte Gmail n'est pas ouverte à l'application ({exc.detail}).") from None
    return email


MOI = "moi"  # = la personne elle-même ; son adresse est posée par le SERVEUR, au clic (règle de l'étape 1)


def _destinataires_internes(ctx: ContexteAssistant, brut: Any) -> list[str]:
    domaine = "@" + ctx.settings.google_workspace_domain
    morceaux = [x.strip().lower() for x in re.split(r"[|,;\s]+", str(brut or "")) if x.strip()]
    if not morceaux:
        raise Refus("Donne au moins un destinataire.")
    for adresse in morceaux:
        if adresse == MOI:
            continue
        if not _ADRESSE.fullmatch(adresse):
            raise Refus(f"« {adresse} » n'est pas une adresse e-mail.")
        if not adresse.endswith(domaine):
            raise Refus(f"L'assistant n'envoie qu'EN INTERNE : « {adresse} » n'est pas une adresse {domaine}.")
    uniques = list(dict.fromkeys(morceaux))
    if len(uniques) > MAX_DESTINATAIRES:
        raise Refus(f"Au plus {MAX_DESTINATAIRES} destinataires.")
    return uniques


def _contenu_email(p: dict[str, Any]) -> tuple[str, str]:
    objet = str(p.get("objet") or "").strip()
    texte = str(p.get("texte") or "").strip()
    if not objet or len(objet) > 240:
        raise Refus("Donne un objet (240 caractères au plus).")
    if not texte or len(texte) > MAX_TEXTE_EMAIL:
        raise Refus(f"Donne le texte ({MAX_TEXTE_EMAIL} caractères au plus : la carte le montre EN ENTIER).")
    return objet, texte


def preparer_email_interne(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    _ma_boite(ctx)
    dest = _destinataires_internes(ctx, p.get("destinataires"))
    objet, texte = _contenu_email(p)
    qui = ", ".join("toi" if d == MOI else d for d in dest)
    return f"Envoyer depuis TA boîte un e-mail interne à {qui} — objet « {objet} » — texte :\n{texte}", \
        {"destinataires": dest, "objet": objet, "texte": texte}


def executer_email_interne(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    email = _ma_boite(ctx)  # re-vérifié AU CLIC
    dest = list(dict.fromkeys(email if d == MOI else d
                              for d in _destinataires_internes(ctx, "|".join(p.get("destinataires") or []))))
    objet, texte = _contenu_email(p)
    r = _google(lambda: GoogleWorkspaceService(ctx.settings).send_gmail_message(
        subject_email=email, to=dest, subject=objet, body_text=texte, from_name=ctx.nom or "GTI Immobilier",
        attachments=None, dry_run=False, requested_by=ctx.user_id, requested_by_email=email,
        related_entity_type="assistant", related_entity_id=ctx.conversation_id), "Envoi de l'e-mail")
    return {"envoye": True, "destinataires": len(dest), "message_id": r.get("messageId")}


MAX_BIENS_APERCU = 10


def apercu_rapprochement(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    recherche = _recherche(ctx, p.get("contact_search_key"))
    morceaux = [x.strip() for x in re.split(r"[|,;\s]+", str(p.get("annonces") or "")) if x.strip()]
    if not morceaux or any(not x.isdigit() for x in morceaux):
        raise Refus("Donne les numéros d'annonce, séparés par |.")
    if len(morceaux) > MAX_BIENS_APERCU:
        raise Refus(f"Au plus {MAX_BIENS_APERCU} biens dans un aperçu.")
    biens = [_bien(ctx, x) for x in dict.fromkeys(morceaux)]  # chaque bien lu avec le jeton AVANT le rendu
    fiche = (_lire(ctx, "app_contacts_current", {"hektor_contact_id": f"eq.{recherche['hektor_contact_id']}", "limit": "1",
                                                 "select": "display_name,prenom,civilite,email"}) or [{}])[0]
    try:
        rendu = RapprochementEmailService(ctx.settings).render_preview(
            annonce_ids=[int(b["hektor_annonce_id"]) for b in biens], variante="pull", prenom=fiche.get("prenom"),
            civilite=fiche.get("civilite"), criteres=None, custom_intro=str(p.get("mot") or "").strip()[:1500] or None,
            hektor_contact_id=str(recherche["hektor_contact_id"]))
    except HTTPException as exc:
        raise Refus(f"Aperçu impossible ({exc.detail}).") from None

    def masque(texte: Any) -> str:
        # ⛔ aucune adresse e-mail ne part au modèle (ni celle de la personne, ni celle du client)
        # ⛔ ni aucun LIEN : « Voir ce bien », « Affiner », « Se désinscrire » portent une clé d'accès à l'espace du
        #   client (/espace/<jeton>, sans connexion) -- trouvé en réel le 13/11 sur l'aperçu de 10354488
        return _ADRESSE.sub("[adresse]", _LIEN.sub("[lien]", str(texte or "")))

    return {"apercu": True, "rien_n_est_parti": True, "destinataire": fiche.get("display_name"),
            "client_a_une_adresse": bool(str(fiche.get("email") or "").strip()), "objet": masque(rendu.get("subject")),
            "texte": masque(rendu.get("text"))[:5000],
            "a_dire": "C'est un APERÇU : rien n'est envoyé ni enregistré. Pour l'envoyer pour de vrai, propose la carte "
                      "envoyer_rapprochement avec les mêmes biens."}


# ── LOT 3c (16/11/2026) : VERS LE CLIENT -- e-mail, rapprochement réel, invitation ──
# Note : notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md §26-27. Décision « Oui, vas-y » du 16/11 (A, B, C ; pas
#   l'espace client ; le bon de visite viendra avec l'écran).
# ⛔ Le destinataire est TOUJOURS l'adresse de la fiche d'un contact que la personne voit, relue AU CLIC par le serveur :
#   jamais une adresse donnée par le modèle. Et l'adresse du client ne part JAMAIS au modèle (ni dans la carte qu'il
#   relit) : la carte dit « l'adresse de sa fiche ».
# ⛔ Un contact désinscrit (app_contact_consent, opt_out) ne reçoit rien : refusé à la carte ET au clic.
# ⛔ Le rapprochement réel passe par LE MÊME point que l'écran côté acquéreur (RapprochementSender.send_grouped,
#   RechercheAcquereur.tsx:670) : biens jamais proposés seulement, 1 e-mail par négociateur du mandat depuis sa boîte,
#   plafond du jour, désinscription en 1 clic, suivi ; puis les biens envoyés passent « proposé » par e-mail (comme
#   l'écran). L'expéditeur de repli est posé par le SERVEUR (l'écran le prend du navigateur : défaut n° 1 du §10).
# ⛔ Un rendez-vous avec invité envoie une VRAIE invitation Google ; l'assistant ne pourra plus le déplacer ni le
#   supprimer ensuite (garde de _mon_rdv : un RDV avec invités se change depuis l'écran).
def _client(ctx: ContexteAssistant, numero: Any) -> dict[str, Any]:
    numero = str(numero or "").strip()
    if not numero.isdigit():
        raise Refus("Donne le numéro du contact (hektor_contact_id, objet contacts).")
    lignes = _lire(ctx, "app_contacts_current", {"hektor_contact_id": f"eq.{numero}", "limit": "1",
                                                 "select": "hektor_contact_id,display_name,prenom,civilite,email,archive"})
    if not lignes:
        raise Refus(f"Le contact {numero} n'est pas parmi ceux que tu peux voir.")
    fiche = lignes[0]
    if fiche.get("archive"):
        raise Refus("Ce contact est archivé : on n'écrit pas à un contact archivé.")
    adresse = str(fiche.get("email") or "").strip()
    if not _ADRESSE.fullmatch(adresse):
        raise Refus("Ce contact n'a pas d'adresse e-mail valable sur sa fiche : ajoute-la d'abord (carte modifier_contact).")
    if EmailTrackingService(ctx.settings).is_opted_out(adresse):
        raise Refus("Ce contact s'est DÉSINSCRIT des e-mails : rien ne lui sera envoyé.")
    return fiche


def _nom_client(fiche: dict[str, Any]) -> str:
    return str(fiche.get("display_name") or fiche["hektor_contact_id"])


def preparer_email_client(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    _ma_boite(ctx)
    fiche = _client(ctx, p.get("hektor_contact_id"))
    objet, texte = _contenu_email(p)
    return f"Envoyer depuis TA boîte un e-mail à {_nom_client(fiche)} (à l'adresse de sa fiche) — objet « {objet} » — " \
           f"texte :\n{texte}\n⚠ Il part VRAIMENT chez le client.", \
        {"hektor_contact_id": str(fiche["hektor_contact_id"]), "objet": objet, "texte": texte}


def executer_email_client(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    email = _ma_boite(ctx)  # re-vérifié AU CLIC
    fiche = _client(ctx, p.get("hektor_contact_id"))  # adresse, archive et désinscription RELUES au clic
    objet, texte = _contenu_email(p)
    r = _google(lambda: GoogleWorkspaceService(ctx.settings).send_gmail_message(
        subject_email=email, to=[str(fiche["email"]).strip()], subject=objet, body_text=texte,
        from_name=ctx.nom or "GTI Immobilier", attachments=None, dry_run=False, requested_by=ctx.user_id,
        requested_by_email=email, related_entity_type="contact", related_entity_id=str(fiche["hektor_contact_id"])),
        "Envoi de l'e-mail")
    return {"envoye": True, "hektor_contact_id": str(fiche["hektor_contact_id"]), "message_id": r.get("messageId")}


def _biens_frais(ctx: ContexteAssistant, recherche: dict[str, Any], annonces: Any) -> tuple[list[dict], list[dict]]:
    morceaux = [x.strip() for x in re.split(r"[|,;\s]+", str(annonces or "")) if x.strip()]
    if not morceaux or any(not x.isdigit() for x in morceaux):
        raise Refus("Donne les numéros d'annonce, séparés par |.")
    if len(morceaux) > MAX_BIENS_APERCU:
        raise Refus(f"Au plus {MAX_BIENS_APERCU} biens dans un envoi.")
    biens = [_bien(ctx, x) for x in dict.fromkeys(morceaux)]  # chaque bien lu avec le jeton
    frais = RapprochementSender(ctx.settings)._fresh_filter(
        [{"annonce_id": int(b["hektor_annonce_id"]), "dossier_id": int(b["app_dossier_id"])} for b in biens],
        str(recherche["hektor_contact_id"]))
    gardes = {f["annonce_id"] for f in frais}
    return [b for b in biens if int(b["hektor_annonce_id"]) in gardes], \
        [b for b in biens if int(b["hektor_annonce_id"]) not in gardes]


def preparer_envoyer_rapprochement(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    recherche = _recherche(ctx, p.get("contact_search_key"))
    if recherche.get("archive") is True:
        raise Refus("Cette recherche est archivée.")
    fiche = _client(ctx, recherche["hektor_contact_id"])
    frais, deja = _biens_frais(ctx, recherche, p.get("annonces"))
    if not frais:
        raise Refus("Tous ces biens ont déjà été proposés, visités ou écartés pour cet acquéreur : rien de neuf à envoyer.")
    tracking = EmailTrackingService(ctx.settings)
    if not ctx.settings.email_real_send_enabled:
        raise Refus("L'envoi réel des e-mails est coupé sur le serveur : rien ne peut partir.")
    if tracking.count_real_sends_today() >= int(ctx.settings.email_daily_send_cap):
        raise Refus("Le plafond d'envois du jour est atteint : réessaie demain.")
    mot = str(p.get("mot") or "").strip()[:1500]
    liste = " ; ".join(f"annonce {b['hektor_annonce_id']} « {b.get('titre_bien') or ''} »" for b in frais)
    resume = f"Envoyer VRAIMENT à {_nom_client(fiche)} (à l'adresse de sa fiche) l'e-mail de rapprochement avec : {liste}. " \
             "Il part depuis la boîte du négociateur de chaque bien (un e-mail par négociateur), avec le lien de " \
             "désinscription ; ces biens passeront « proposé » par e-mail."
    if mot:
        resume += f" Ton mot en tête : « {mot} »."
    if deja:
        resume += " Laissés de côté, déjà vus par lui : " + ", ".join(str(b["hektor_annonce_id"]) for b in deja) + "."
    return resume, {"contact_search_key": recherche["contact_search_key"],
                    "annonces": [int(b["hektor_annonce_id"]) for b in frais], "mot": mot}


def executer_envoyer_rapprochement(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    recherche = _recherche(ctx, p.get("contact_search_key"))  # re-vérifiée AU CLIC
    fiche = _client(ctx, recherche["hektor_contact_id"])
    biens = {int(b["hektor_annonce_id"]): b for b in (_bien(ctx, a) for a in p.get("annonces") or [])}
    r = RapprochementSender(ctx.settings).send_grouped(
        recipient_email=str(fiche["email"]).strip(), annonce_ids=list(biens), variante="pull",
        contact_search_key=recherche["contact_search_key"], hektor_contact_id=str(recherche["hektor_contact_id"]),
        prenom=fiche.get("prenom"), civilite=fiche.get("civilite"), criteres=None, custom_intro=p.get("mot") or None,
        dry_run=False, created_by=ctx.user_id,
        fallback_sender_email=ctx.email)  # ⛔ le repli = la personne, posé par le serveur
    raison = r.get("skipped") or next((g.get("skipped") for g in r.get("groups") or [] if g.get("skipped")), None)
    if not r.get("ok"):
        raise Refus({"opt_out": "le contact s'est désinscrit", "daily_cap": "plafond d'envois du jour atteint",
                     "no_fresh_bien": "ces biens ont été proposés entre-temps"}.get(str(raison), "l'envoi n'est pas parti"))
    if r.get("dryRun"):
        raise Refus("le serveur a envoyé en MODE TEST (envoi réel coupé) : rien n'est parti chez le client")
    marques = 0
    for groupe in r.get("groups") or []:
        if not groupe.get("ok"):
            continue
        for annonce in groupe.get("annonceIds") or []:
            try:  # = propose(sentRefs, 'email') de l'écran : succès seulement
                _ecrire(ctx, "POST", "rpc/app_record_proposition", {
                    "p_search_key": recherche["contact_search_key"], "p_dossier_id": biens[int(annonce)]["app_dossier_id"],
                    "p_channel": "email", "p_note": None, "p_nego": ctx.email,
                    "p_gmail_message_id": groupe.get("messageId"), "p_gmail_thread_id": None})
                marques += 1
            except Refus:
                pass
    return {"envoye": True, "emails": r.get("sentCount"), "biens_envoyes": r.get("sentAnnonceIds"),
            "biens_marques_proposes": marques}


def preparer_rdv_client(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not str(p.get("hektor_contact_id") or "").strip() and not str(p.get("contact_search_key") or "").strip():
        raise Refus("Donne le contact à inviter (son numéro, ou la clé de sa recherche).")
    resume, params = preparer_rdv(ctx, p)
    fiche = _client(ctx, params["hektor_contact_id"])
    resume = resume.replace("Aucune invitation n'est envoyée : personne d'autre n'est prévenu.",
                            f"⚠ Une VRAIE invitation Google part à {_nom_client(fiche)} (à l'adresse de sa fiche) : il la "
                            "reçoit par e-mail. Ensuite, ce rendez-vous se déplace ou s'annule depuis l'écran.")
    return resume, params


def executer_rdv_client(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    fiche = _client(ctx, p.get("hektor_contact_id"))  # adresse, archive, désinscription RELUES au clic
    return _poser_rdv(ctx, p, invites=[str(fiche["email"]).strip()])


# ── LOT 4a (14/11/2026) : le bien -- champs, rédacteur, photos, brouillon ──────
# Note : notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md §13 et §15. Décision de Frédéric : « 4a et 4b ».
# ⛔ Toujours le geste de l'écran, avec le jeton de la personne : la base juge les droits (app_console_can_request_job).
# ⛔ Liste FERMÉE de champs : jamais le prix (demande de baisse, lot 1), le prix net vendeur, les honoraires, l'adresse,
#   la commune, le code postal, le numéro de mandat ; ni les champs à liste de choix de Hektor (cuisine, exposition,
#   vue, états), dont l'assistant ne connaît pas les codes.
# ⛔ Un brouillon n'est jamais modifié (décision ⑦-10 ③ : on l'ACTIVE) -- il n'est pas dans app_dossiers_current.
CHAMPS_BIEN = {  # nom de l'écran (traduit par app_edit_annonce_optimistic) -> (libellé, genre)
    "title": ("titre", "texte"), "description": ("texte de l'annonce", "texte"),
    "surface": ("surface habitable (m²)", "nombre"), "carrezSurface": ("surface Carrez (m²)", "nombre"),
    "landSurface": ("terrain (m²)", "nombre"), "roomCount": ("pièces", "entier"), "bedroomCount": ("chambres", "entier"),
    "levelCount": ("niveaux", "entier"), "bathroomCount": ("salles de bain", "entier"),
    "showerRoomCount": ("salles d'eau", "entier"), "wcCount": ("WC", "entier"), "garageCount": ("garages / box", "entier"),
    "garageSurface": ("surface du garage (m²)", "nombre"), "parkingInsideCount": ("parkings intérieurs", "entier"),
    "parkingOutsideCount": ("parkings extérieurs", "entier"), "terraceCount": ("terrasses", "entier"),
    "constructionYear": ("année de construction", "annee"), "dpeValue": ("DPE, consommation (kWh/m².an)", "nombre"),
    "gesValue": ("GES, émissions (kg CO2/m².an)", "nombre"), "coproLots": ("lots de copropriété", "entier"),
    "coproCharges": ("charges de copropriété (€/an)", "nombre"), "coproQuotePart": ("quote-part de copropriété", "nombre"),
    "coproWorksFund": ("fonds de travaux (€)", "nombre"),
}
# la valeur actuelle, pour l'« avant » de la carte : le calque de l'app d'abord (nom Hektor), puis la fiche
_AVANT_BIEN = {"title": ("titre", "texte_principal_titre"), "description": ("corps", "texte_principal_html"),
               "surface": ("surfappart", "surface_habitable_detail", "surface"), "roomCount": ("nbpieces", "nb_pieces"),
               "bedroomCount": ("NB_CHAMBRES", "nb_chambres"), "landSurface": ("surfterrain", "surface_terrain_detail"),
               "garageCount": ("GARAGE_BOX", "garage_box_detail")}
MAX_TITRE, MAX_TEXTE_ANNONCE = 120, 6000
_NOMBRE = re.compile(r"\d+([.,]\d+)?")
_BALISE = re.compile(r"<[^>]+>")


def _hors_catalogue(ctx: ContexteAssistant, numero: str) -> None:
    # un brouillon n'est pas dans app_dossiers_current : le dire, plutôt que « introuvable »
    if _lire(ctx, "app_brouillon_annonce_index_current", {"hektor_annonce_id": f"eq.{numero}", "limit": "1",
                                                          "select": "hektor_annonce_id"}):
        raise Refus(f"L'annonce {numero} est un BROUILLON : elle ne se modifie pas tant qu'elle n'est pas activée "
                    "(l'activer se fait depuis sa fiche dans l'application, pas par l'assistant).")


def _bien_vivant(ctx: ContexteAssistant, hektor_annonce_id: Any) -> dict[str, Any]:
    numero = str(hektor_annonce_id or "").strip()
    try:
        return _bien(ctx, numero)
    except Refus:
        if numero.isdigit():
            _hors_catalogue(ctx, numero)
        raise


def _valeur_champ(cle: str, brut: Any) -> str | None:
    texte = str(brut or "").strip()
    if not texte:
        return None
    libelle, genre = CHAMPS_BIEN[cle]
    if genre == "texte":
        plafond = MAX_TITRE if cle == "title" else MAX_TEXTE_ANNONCE
        if len(texte) > plafond:
            raise Refus(f"Le {libelle} dépasse {plafond} caractères.")
        return texte
    texte = texte.replace(" ", "").replace(" ", "")
    if genre == "entier" and not texte.isdigit():
        raise Refus(f"{libelle} : un nombre entier, pas « {brut} ».")
    if genre == "annee" and not (texte.isdigit() and 1500 <= int(texte) <= datetime.now(PARIS).year + 2):
        raise Refus(f"{libelle} : une année sur 4 chiffres, pas « {brut} ».")
    if genre == "nombre" and not _NOMBRE.fullmatch(texte):
        raise Refus(f"{libelle} : un nombre, pas « {brut} ».")
    return texte.replace(",", ".")


def _valeurs_actuelles(ctx: ContexteAssistant, app_dossier_id: Any) -> dict[str, str]:
    try:
        lignes = _lire(ctx, "app_dossier_detail_current", {"app_dossier_id": f"eq.{app_dossier_id}", "limit": "1",
                                                           "select": "detail_payload_json"})
        fiche = json.loads((lignes or [{}])[0].get("detail_payload_json") or "{}")
    except (LectureRefusee, ValueError, TypeError):
        return {}  # l'« avant » n'est qu'un confort : sans lui, la carte montre la nouvelle valeur seule
    calque = fiche.get("app_optimistic_overlay") or {}
    actuelles = {}
    for cle, (nom_hektor, *cles_fiche) in _AVANT_BIEN.items():
        for v in (calque.get(nom_hektor), *(fiche.get(c) for c in cles_fiche)):
            if str(v or "").strip():
                actuelles[cle] = _BALISE.sub(" ", str(v)).strip()
                break
    return actuelles


def _court(texte: str, n: int = 80) -> str:
    texte = re.sub(r"\s+", " ", texte)
    return texte if len(texte) <= n else texte[: n - 1] + "…"


def preparer_modifier_bien(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    champs = {cle: v for cle in CHAMPS_BIEN if (v := _valeur_champ(cle, p.get(cle))) is not None}
    if not champs:
        raise Refus("Rien à modifier : donne au moins un champ (le prix ne se modifie pas ici : demande de baisse).")
    avant = _valeurs_actuelles(ctx, bien["app_dossier_id"])
    lignes = [f"{CHAMPS_BIEN[c][0]} : " + (f"« {_court(avant[c])} » → " if c in avant else "") + f"« {_court(v)} »"
              for c, v in champs.items()]
    return (f"Modifier l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » — " + " ; ".join(lignes) +
            " (chez nous tout de suite, recopié chez Hektor environ 10 minutes après)",
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "champs": champs})


def executer_modifier_bien(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))  # re-vérifié AU CLIC (vendu, clos, droits)
    champs = {c: v for c, v in dict(p.get("champs") or {}).items() if c in CHAMPS_BIEN and str(v or "").strip()}
    if not champs:
        raise Refus("aucun champ à modifier")
    r = _ecrire(ctx, "POST", "rpc/app_edit_annonce_optimistic",
                {"target_dossier_id": bien["app_dossier_id"], "edit_fields": champs, "debounce_seconds": 600})
    return {"app_dossier_id": bien["app_dossier_id"], "champs": sorted(champs), "reponse": r}


# 17/11 (note étape 4 §37-38) : CHANGER LE PRIX, la DIRECTION seulement. La base le refuse au négociateur
# (`prix_sur_demande`, décision B1 du 12/10 : il passe par la demande de baisse) et l'accepte de la direction, par la même
# fonction que l'écran (champ `price` d'app_edit_annonce_optimistic). Double verrou : la carte n'est montrée qu'à la
# direction, la base refuse au clic. ⚠ Accepter une demande de baisse NE change PAS le prix (l'écran vérifie que Hektor
# porte déjà le prix demandé) : la carte signale une baisse demandée en cours, à accepter ensuite dans Suivi.
ECART_PRIX_A_SIGNALER = 0.3


def _prix_voulu(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], int, dict[str, Any] | None]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    brut = re.sub(r"\s+", "", str(p.get("prix") or "")).replace("€", "")
    if not re.fullmatch(r"\d+([.,]\d+)?", brut) or float(brut.replace(",", ".")) < 1:
        raise Refus("Le prix est un montant en euros (ex. 185000).")
    prix = round(float(brut.replace(",", ".")))
    if isinstance(bien.get("prix"), (int, float)) and round(bien["prix"]) == prix:
        raise Refus(f"L'annonce {bien['hektor_annonce_id']} est déjà à {_euros(prix)}.")
    demande = (_lire(ctx, "app_diffusion_requests_current", {
        "app_dossier_id": f"eq.{bien['app_dossier_id']}", "request_type": "eq.demande_baisse_prix",
        "request_status": f"in.({','.join(EN_COURS)})", "select": "id", "limit": "1"}) or [None])[0]
    return bien, prix, demande


def preparer_changer_prix(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien, prix, demande = _prix_voulu(ctx, p)
    ancien = bien.get("prix") if isinstance(bien.get("prix"), (int, float)) and bien["prix"] > 0 else None
    resume = (f"Changer le prix de l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » : "
              + (f"{_euros(ancien)} → " if ancien else "") + f"{_euros(prix)}")
    if ancien and abs(prix - ancien) / ancien > ECART_PRIX_A_SIGNALER:
        resume += f" (⚠ écart de {round(abs(prix - ancien) / ancien * 100)} % : vérifie le montant)"
    resume += " — chez nous tout de suite, recopié chez Hektor environ 10 minutes après ; les rapprochements se recalculent"
    if demande:
        resume += ". Une demande de baisse est en cours sur ce bien : l'accepter ensuite dans Suivi (ce geste ne la traite pas)"
    return resume, {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "prix": str(prix)}


def executer_changer_prix(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    if ctx.role not in DIRECTION:  # 3e verrou, après la route (geste.roles) et avant la base (prix_sur_demande)
        raise Refus("le prix se change par la direction ; un négociateur passe par la demande de baisse")
    bien, prix, _demande = _prix_voulu(ctx, p)  # re-vérifié AU CLIC (vendu, clos, droits, déjà à ce prix)
    r = _ecrire(ctx, "POST", "rpc/app_edit_annonce_optimistic",
                {"target_dossier_id": bien["app_dossier_id"], "edit_fields": {"price": str(prix)}, "debounce_seconds": 600})
    return {"app_dossier_id": bien["app_dossier_id"], "champs": ["price"], "reponse": r}


# Le rédacteur maison (le même service que le bouton « Générer avec l'IA » de la création) : il PROPOSE, n'écrit rien.
def _faits_du_bien(ctx: ContexteAssistant, bien: dict[str, Any]) -> dict[str, Any]:
    lignes = _lire(ctx, "app_dossier_detail_current", {"app_dossier_id": f"eq.{bien['app_dossier_id']}", "limit": "1",
                                                       "select": "detail_payload_json"})
    try:
        fiche = json.loads((lignes or [{}])[0].get("detail_payload_json") or "{}")
    except (ValueError, TypeError):
        fiche = {}
    tete = (_lire(ctx, "app_dossiers_current", {"app_dossier_id": f"eq.{bien['app_dossier_id']}", "limit": "1",
                                               "select": "type_bien,ville"}) or [{}])[0]
    return {"type_bien": tete.get("type_bien"), "ville": tete.get("ville") or fiche.get("ville_publique_detail"),
            "prix": bien.get("prix"), "surface": fiche.get("surface_habitable_detail") or fiche.get("surface"),
            "surface_terrain": fiche.get("surface_terrain_detail"), "pieces": fiche.get("nb_pieces"),
            "chambres": fiche.get("nb_chambres"), "etage": fiche.get("etage_detail")}


def rediger_annonce(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    from .openai_listing_writer_service import OpenAIListingWriterService  # tard : le service charge le client OpenAI
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    consigne = str(p.get("consigne") or "").strip()[:500] or None
    try:
        r = OpenAIListingWriterService(ctx.settings).generate(_faits_du_bien(ctx, bien), photo_urls=[], custom_intro=consigne)
    except HTTPException as exc:
        raise Refus(f"Le rédacteur n'a pas pu écrire ({exc.detail}).") from None
    morceaux = [str(r.get("accroche") or "").strip(), str(r.get("description") or "").strip()]
    points = [str(h).strip() for h in (r.get("highlights") or []) if str(h).strip()]
    if points:
        morceaux.append("Points forts :\n" + "\n".join(f"- {h}" for h in points))
    usage = r.get("usage") or {}
    try:  # même trace que l'écran (app_agent_run), sans jamais casser la réponse
        SupabaseAdminService(ctx.settings).insert_agent_run({
            "agent_key": "redacteur", "app_dossier_id": bien["app_dossier_id"],
            "hektor_annonce_id": int(bien["hektor_annonce_id"]), "negociateur_email": (ctx.email or "").lower() or None,
            "status": "proposed", "model": r.get("model"), "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"), "total_tokens": usage.get("total_tokens"),
            "proposal_json": {"title": r.get("title"), "accroche": r.get("accroche"), "description": r.get("description"),
                              "highlights": r.get("highlights"), "source": "assistant"}})
    except Exception:  # noqa: BLE001
        pass
    return {"proposition": True, "rien_n_est_ecrit": True, "titre": str(r.get("title") or "").strip()[:MAX_TITRE],
            "texte": "\n\n".join(m for m in morceaux if m)[:MAX_TEXTE_ANNONCE],
            "a_dire": "C'est une PROPOSITION : montre-la. Si la personne la veut, prépare proposer_modifier_bien avec "
                      "title et description (rien d'autre)."}


# Photos : les trois fonctions de l'écran (galerie de la fiche) ; elles jugent les droits et rendent ok / erreur.
_ERREURS_PHOTO = {"droits_insuffisants": "tu n'as pas les droits sur ce bien",
                  "photo_introuvable_ou_masquee": "cette photo n'est pas visible chez Hektor",
                  "photo_introuvable_chez_hektor": "cette photo n'est plus chez Hektor",
                  "ordre_incomplet": "l'ordre des photos a changé entre-temps",
                  "ordre_avec_photos_inconnues": "l'ordre des photos a changé entre-temps"}


def _photos(ctx: ContexteAssistant, bien: dict[str, Any]) -> list[dict[str, Any]]:
    # = loadConsolePhotos (api.ts:9088) : présentes chez Hektor, visibles d'abord, dans leur ordre
    return _lire(ctx, "app_console_photo", {"app_dossier_id": f"eq.{bien['app_dossier_id']}", "present_in_hektor": "is.true",
                                            "select": "hektor_photo_id,visible,legend,sort_order",
                                            "order": "visible.desc,sort_order.asc,id.asc", "limit": "500"})


def _photo(photos: list[dict[str, Any]], photo: Any) -> dict[str, Any]:
    numero = str(photo or "").strip()
    for ligne in photos:
        if str(ligne.get("hektor_photo_id")) == numero:
            return ligne
    raise Refus(f"La photo {numero} n'est pas sur cette annonce (lire_photos_bien donne les numéros).")


def _rpc_photo(ctx: ContexteAssistant, fonction: str, corps: dict[str, Any]) -> dict[str, Any]:
    r = _ecrire(ctx, "POST", f"rpc/{fonction}", corps) or {}
    if r.get("ok") is not True:
        erreur = str(r.get("erreur") or "refus inconnu")
        raise Refus(f"refusé : {_ERREURS_PHOTO.get(erreur, erreur)}")
    return r


def lire_photos_bien(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    photos = _photos(ctx, bien)
    visibles = [x for x in photos if x.get("visible") is True]
    return {"annonce": bien["hektor_annonce_id"], "visibles": len(visibles), "masquees": len(photos) - len(visibles),
            "photos": [{"photo": str(x["hektor_photo_id"]), "rang": (visibles.index(x) + 1) if x in visibles else None,
                        "visible": x.get("visible") is True, "couverture": bool(visibles) and x is visibles[0],
                        "legende": x.get("legend") or ""} for x in photos],
            "a_dire": "La couverture est la 1re photo visible. Une photo masquée n'a pas de rang."}


def preparer_couverture(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    photos = _photos(ctx, bien)
    photo = _photo(photos, p.get("photo"))
    if photo.get("visible") is not True:
        raise Refus("Cette photo est masquée : il faut d'abord l'afficher.")
    if photo is photos[0]:
        raise Refus("Cette photo est déjà la couverture.")
    return (f"Mettre la photo {photo['hektor_photo_id']} en COUVERTURE de l'annonce {bien['hektor_annonce_id']} "
            f"« {bien.get('titre_bien') or ''} » (vitrine et portails suivent)",
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "photo": str(photo["hektor_photo_id"])})


def executer_couverture(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    r = _rpc_photo(ctx, "app_console_photo_couverture_optimistic", {
        "p_app_dossier_id": bien["app_dossier_id"], "p_hektor_annonce_id": str(bien["hektor_annonce_id"]),
        "p_hektor_photo_id": p["photo"]})
    return {"app_dossier_id": bien["app_dossier_id"], "photo": p["photo"], "job_id": r.get("job_id")}


def preparer_visibilite_photo(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    photos = _photos(ctx, bien)
    photo = _photo(photos, p.get("photo"))
    visible = bool(p.get("visible"))
    if (photo.get("visible") is True) == visible:
        raise Refus("Cette photo est déjà visible." if visible else "Cette photo est déjà masquée.")
    if not visible and sum(1 for x in photos if x.get("visible") is True) <= 1:
        raise Refus("C'est la dernière photo visible : l'annonce n'en aurait plus aucune.")
    verbe = "Afficher" if visible else "Masquer"
    return (f"{verbe} la photo {photo['hektor_photo_id']} de l'annonce {bien['hektor_annonce_id']} "
            f"« {bien.get('titre_bien') or ''} »" + ("" if visible else " (elle sort de la vitrine et des portails)"),
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "photo": str(photo["hektor_photo_id"]), "visible": visible})


def executer_visibilite_photo(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    photos = _photos(ctx, bien)  # la dernière visible est RE-COMPTÉE au clic
    if not p["visible"] and sum(1 for x in photos if x.get("visible") is True) <= 1:
        raise Refus("c'est devenu la dernière photo visible")
    r = _rpc_photo(ctx, "app_console_photo_visibilite_optimistic", {
        "p_app_dossier_id": bien["app_dossier_id"], "p_hektor_annonce_id": str(bien["hektor_annonce_id"]),
        "p_hektor_photo_id": p["photo"], "p_visible": bool(p["visible"])})
    return {"app_dossier_id": bien["app_dossier_id"], "photo": p["photo"], "visible": bool(p["visible"]),
            "job_id": r.get("job_id")}


def _ordre_avec(visibles: list[str], photo: str, rang: int) -> list[str]:
    ordre = [x for x in visibles if x != photo]
    ordre.insert(rang - 1, photo)
    return ordre


def preparer_deplacer_photo(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    photos = _photos(ctx, bien)
    photo = _photo(photos, p.get("photo"))
    visibles = [str(x["hektor_photo_id"]) for x in photos if x.get("visible") is True]
    if photo.get("visible") is not True:
        raise Refus("Une photo masquée n'a pas de place : il faut d'abord l'afficher.")
    rang = int(p.get("rang") or 0)
    if not 1 <= rang <= len(visibles):
        raise Refus(f"Rang entre 1 et {len(visibles)}.")
    if visibles.index(str(photo["hektor_photo_id"])) + 1 == rang:
        raise Refus("La photo est déjà à cette place.")
    return (f"Déplacer la photo {photo['hektor_photo_id']} au rang {rang} sur {len(visibles)} (annonce "
            f"{bien['hektor_annonce_id']})" + (" — elle devient la COUVERTURE" if rang == 1 else ""),
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "photo": str(photo["hektor_photo_id"]), "rang": rang})


def executer_deplacer_photo(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    visibles = [str(x["hektor_photo_id"]) for x in _photos(ctx, bien) if x.get("visible") is True]  # l'ordre RELU au clic
    if p["photo"] not in visibles or not 1 <= int(p["rang"]) <= len(visibles):
        raise Refus("les photos ont changé entre-temps : relis-les")
    r = _rpc_photo(ctx, "app_console_photos_reordonner_optimistic", {
        "p_app_dossier_id": bien["app_dossier_id"], "p_hektor_annonce_id": str(bien["hektor_annonce_id"]),
        "p_ordre": _ordre_avec(visibles, p["photo"], int(p["rang"]))})
    return {"app_dossier_id": bien["app_dossier_id"], "photo": p["photo"], "rang": int(p["rang"]), "job_id": r.get("job_id")}


# ⛔ Activer un brouillon : RETIRÉ de l'assistant le 15/11/2026 (décision de Frédéric, « B » : « geste du brouillon
#   pas nécessaire »). Le geste reste à l'écran (handleExitDraftAnnonce, App.tsx:17147). Note ETAPE3 §22.


# ── LOT 4b (14/11/2026) : un portail, sur un bien DIFFUSABLE ───────────────────
# = basculerPortail de la vue Publicité (App.tsx:28233) : UNE SEULE cible enregistrée, puis /hektor-diffusion/apply
#   -> un seul ordre part chez Hektor, les autres portails ne sont pas touchés ; puis le résumé est reporté.
# ⛔ Jamais « diffusable » (direction) : ensure_diffusable reste False, comme pour le négociateur à l'écran.
# ⚠ Biens vivants seulement (app_dossiers_current) : les vendus encore diffusés restent à l'écran.
PORTAILS = {"leboncoinDirect": "Leboncoin", "bienicidirect": "Bien'ici", "paper": "Paper", "etreproprio": "Etreproprio",
            "superimmo": "Superimmo"}  # = PORTAILS_PUB (AnnoncesListeV2.tsx:511)
PORTAIL_ID_COMMUN = {"etreproprio": "19", "paper": "20", "superimmo": "21"}  # = AnnoncesListeV2.tsx:522


def _en_ligne(resume: Any) -> list[str]:
    return list(dict.fromkeys(x.strip() for x in str(resume or "").split(",") if x.strip()))


def _bien_diffusion(ctx: ContexteAssistant, hektor_annonce_id: Any) -> dict[str, Any]:
    bien = _bien_vivant(ctx, hektor_annonce_id)
    tete = (_lire(ctx, "app_dossiers_current", {"app_dossier_id": f"eq.{bien['app_dossier_id']}", "limit": "1",
                                               "select": "agence_nom,diffusable,portails_resume,nb_portails_actifs"}) or [{}])[0]
    return {**bien, **tete}


def lire_portails_bien(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien = _bien_diffusion(ctx, p.get("hektor_annonce_id"))
    en_ligne = _en_ligne(bien.get("portails_resume"))
    return {"annonce": bien["hektor_annonce_id"], "diffusable": str(bien.get("diffusable") or "") == "1",
            "valide": _valide(bien.get("validation_diffusion_state")),
            "portails": [{"portail": k, "nom": n, "en_ligne": k in en_ligne} for k, n in PORTAILS.items()],
            "a_dire": "Publier ou retirer des portails n'est possible que sur un bien DÉJÀ diffusable (la direction le rend "
                      "diffusable par le Pilotage ; le négociateur : demande_direction type diffusion)."}


# 17/11 (note étape 4 §44-45) : la carte prend une LISTE (« à publier », « à retirer ») = la fenêtre « Diffusion » de
# l'écran, en n'enregistrant que les portails NOMMÉS (les autres ne bougent pas, comme la case de la vue Publicité).
# ⛔ Seulement sur un bien DÉJÀ diffusable, pour TOUT LE MONDE (règle de Frédéric du 17/11) : la direction le rend
#   diffusable par la carte Pilotage ; la carte ne passe jamais ensure_diffusable.
def _portails_nommes(texte: Any, quoi: str) -> list[str]:
    cles: list[str] = []
    for morceau in str(texte or "").split("|"):
        nom = _simple(morceau).replace(" ", "")  # « Bien'ici », « bienici », « le bon coin »
        if not nom:
            continue
        cle = next((k for k, n in PORTAILS.items() if nom in {_simple(k).replace(" ", ""), _simple(n).replace(" ", "")}),
                   None)
        if not cle:
            raise Refus(f"{quoi} : « {morceau.strip()} » n'est pas un portail ({', '.join(PORTAILS.values())}).")
        if cle not in cles:
            cles.append(cle)
    return cles


def _choix_portails(p: dict[str, Any]) -> dict[str, bool]:
    if "choix" in p:  # la carte préparée
        choix = {str(k): bool(v) for k, v in dict(p.get("choix") or {}).items()}
    elif "portail" in p:  # la forme d'avant le 17/11 (un seul portail) : une carte déjà proposée reste valable
        choix = {str(p.get("portail") or "").strip(): bool(p.get("publier"))}
    else:
        a_publier = _portails_nommes(p.get("publier"), "À publier")
        a_retirer = _portails_nommes(p.get("retirer"), "À retirer")
        if set(a_publier) & set(a_retirer):
            raise Refus("Un même portail ne peut pas être à publier ET à retirer.")
        choix = {**{k: True for k in a_publier}, **{k: False for k in a_retirer}}
    if not choix:
        raise Refus("Nomme au moins un portail à publier ou à retirer (" + ", ".join(PORTAILS.values()) + ").")
    if any(k not in PORTAILS for k in choix):
        raise Refus("Portail : " + ", ".join(PORTAILS) + ".")
    return choix


def _bien_diffusable(ctx: ContexteAssistant, hektor_annonce_id: Any) -> dict[str, Any]:
    bien = _bien_diffusion(ctx, hektor_annonce_id)
    if str(bien.get("diffusable") or "") != "1":
        raise Refus("Ce bien n'est pas encore diffusable : la direction le rend diffusable (carte Pilotage) ; un "
                    "négociateur passe par la demande de validation (demande_direction, type diffusion).")
    return bien


def _noms_portails(cles: list[str]) -> str:
    return ", ".join(PORTAILS.get(k, k) for k in cles) or "aucun"


def preparer_portail(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    choix = _choix_portails(p)
    bien = _bien_diffusable(ctx, p.get("hektor_annonce_id"))
    en_ligne = _en_ligne(bien.get("portails_resume"))
    deja = [k for k, v in choix.items() if (k in en_ligne) == v]
    choix = {k: v for k, v in choix.items() if k not in deja}
    if not choix:
        raise Refus(f"Rien ne change : le bien est déjà {'en ligne sur' if all(k in en_ligne for k in deja) else 'absent de'} "
                    f"{_noms_portails(deja)}.")
    apres = [k for k in en_ligne if choix.get(k, True)] + [k for k, v in choix.items() if v and k not in en_ligne]
    morceaux = [f"PUBLIER sur {_noms_portails([k for k, v in choix.items() if v])}" if any(choix.values()) else "",
                f"RETIRER de {_noms_portails([k for k, v in choix.items() if not v])}" if not all(choix.values()) else ""]
    resume = (f"Diffusion de l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » : "
              + " ; ".join(m for m in morceaux if m)
              + f" — en ligne : {_noms_portails(en_ligne)} → {_noms_portails(apres)} ; les autres portails ne bougent pas")
    if deja:
        resume += f" (déjà dans l'état voulu : {_noms_portails(deja)})"
    return resume, {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "choix": choix}


def executer_portail(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    from .hektor_bridge import HektorBridgeService
    choix = _choix_portails(p)
    bien = _bien_diffusable(ctx, p.get("hektor_annonce_id"))  # re-vérifié AU CLIC, pour tous les rôles (règle du 17/11)
    _email, user = _personne(ctx)
    try:  # la garde de la route /apply : négociateur = bien diffusable ET le sien (jugé avec SON jeton)
        SupabaseAdminService(ctx.settings).assert_can_apply_portals(user, f"Bearer {ctx.jeton}", bien["app_dossier_id"])
    except HTTPException as exc:
        raise Refus(f"refusé : {exc.detail}") from None
    pont = HektorBridgeService(ctx.settings)
    agence: list[dict[str, Any]] | None = None
    numeros: dict[str, str] = {}
    for portail in choix:
        numero = PORTAIL_ID_COMMUN.get(portail)
        if not numero:
            if agence is None:
                agence = pont._load_agency_targets(bien.get("agence_nom"))  # noqa: SLF001
            numero = next((str(t["hektor_broadcast_id"]) for t in agence if t.get("portal_key") == portail), None)
        if not numero:
            raise Refus(f"numéro de passerelle {PORTAILS[portail]} introuvable pour l'agence {bien.get('agence_nom') or ''}")
        numeros[portail] = numero
    # = saveDiffusionTargets (api.ts:8504) avec les SEULS portails nommés : on efface les choix du bien, on écrit ceux-ci
    maintenant = datetime.now(timezone.utc).isoformat()
    _ecrire(ctx, "DELETE", "app_diffusion_target", None, {"app_dossier_id": f"eq.{bien['app_dossier_id']}"})
    _ecrire(ctx, "POST", "app_diffusion_target", [{
        "app_dossier_id": bien["app_dossier_id"], "hektor_annonce_id": int(bien["hektor_annonce_id"]),
        "hektor_broadcast_id": numeros[portail], "portal_key": portail, "target_state": "enabled" if publier else "disabled",
        "source_ref": "console_diffusion", "note": "assistant", "requested_by_role": ctx.role,
        "requested_by_name": ctx.nom or ctx.email, "requested_at": maintenant} for portail, publier in choix.items()])
    try:
        r = pont.apply(bien["app_dossier_id"], False, False, ctx.email or ctx.user_id)
    except HTTPException as exc:
        raise Refus(f"Hektor n'a pas pu être joint ({exc.detail})") from None
    refus = [f for f in r.get("failed") or [] if f.get("action") in {"add", "remove"}]
    if refus:  # rien n'est reporté : la relecture de la nuit remettra l'app d'accord avec ce que Hektor a vraiment fait
        raise Refus("Hektor a refusé : " + " ; ".join(
            f"{PORTAILS.get(str(f.get('portal_key') or ''), f.get('portal_key') or 'un portail')} "
            f"({str(f.get('error') or '')[:120]})" for f in refus))
    avant = _en_ligne(bien.get("portails_resume"))
    apres = [k for k in avant if choix.get(k, True)] + [k for k, v in choix.items() if v and k not in avant]
    try:  # Hektor a CONFIRMÉ ; si le report rate, la relecture de la nuit remettra l'app d'accord (comme l'écran)
        pont.persist_state(bien["app_dossier_id"], portails_resume=", ".join(apres), nb_portails_actifs=len(apres))
        reporte = True
    except Exception:  # noqa: BLE001
        reporte = False
    return {"app_dossier_id": bien["app_dossier_id"], "choix": choix, "en_ligne_apres": apres, "resume_reporte": reporte}


# ── 17/11 (note étape 4 §41-42) : le PILOTAGE de la fiche — cocher Validation, cocher Diffusable [direction] ──────
# = handleSetSelectedDossierValidation / …Diffusable (App.tsx ~21481) : les routes /hektor-diffusion/validation et
# /diffusable (garde `assert_admin` = admin ou manager actif), qui écrivent DIRECTEMENT chez Hektor et relisent, puis
# /persist-state, qui recopie chez nous ce que Hektor MONTRE. Le même pont, ici, avec la même garde jugée avec le jeton.
# ⛔ La carte EXIGE que Hektor confirme les deux cases (l'écran ne vérifie pas la validation) et dit ce qu'il montre
#   sinon. Diffusable sans validation : rare (3 biens sur 13 556 le 17/11), pas refusé, la carte prévient.
CHOIX_PILOTAGE = {"oui": True, "non": False, "": None, "inchange": None}


def _choix_pilotage(valeur: Any, quoi: str) -> bool | None:
    cle = _simple(valeur).replace("inchangee", "inchange")
    if cle not in CHOIX_PILOTAGE:
        raise Refus(f"{quoi} : oui, non, ou vide pour ne pas y toucher.")
    return CHOIX_PILOTAGE[cle]


def _controler_pilotage(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], bool | None, bool | None]:
    bien = _bien_diffusion(ctx, p.get("hektor_annonce_id"))
    validation = _choix_pilotage(p.get("validation"), "Validation")
    diffusable = _choix_pilotage(p.get("diffusable"), "Diffusable")
    if validation is None and diffusable is None:
        raise Refus("Rien à changer : dis Validation oui / non, ou Diffusable oui / non.")
    if (validation is None or validation == _valide(bien.get("validation_diffusion_state"))) and \
            (diffusable is None or diffusable == (str(bien.get("diffusable") or "") == "1")):
        raise Refus(f"Rien ne change : l'annonce {bien['hektor_annonce_id']} est déjà dans cet état.")
    return bien, validation, diffusable


def _oui_non(valeur: bool) -> str:
    return "OUI" if valeur else "NON"


def preparer_pilotage(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien, validation, diffusable = _controler_pilotage(ctx, p)
    valide, diffuse = _valide(bien.get("validation_diffusion_state")), str(bien.get("diffusable") or "") == "1"
    lignes = []
    if validation is not None and validation != valide:
        lignes.append(f"Validation {_oui_non(valide)} → {_oui_non(validation)}")
    if diffusable is not None and diffusable != diffuse:
        lignes.append(f"Diffusable {_oui_non(diffuse)} → {_oui_non(diffusable)}")
    resume = (f"Pilotage de l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » : " + " ; ".join(lignes)
              + ". Écrit DIRECTEMENT chez Hektor au clic, puis relu")
    if diffusable is True and not diffuse:
        resume += ". ⚠ Diffusable OUI : le bien peut repartir sur les portails déjà cochés"
        if not (validation if validation is not None else valide):
            resume += " ; ⚠ sans validation, c'est rare et Hektor peut ne pas l'appliquer"
    if diffusable is False and diffuse:
        resume += ". ⚠ Diffusable NON : le bien sort de tous les portails"
    if validation is False and valide:
        resume += ". ⚠ Invalider peut aussi couper la diffusion chez Hektor"
    if _lire(ctx, "app_diffusion_requests_current", {
            "app_dossier_id": f"eq.{bien['app_dossier_id']}", "request_type": "eq.demande_diffusion",
            "request_status": f"in.({','.join(EN_COURS)})", "select": "id", "limit": "1"}):
        resume += ". Une demande de validation est en cours sur ce bien : elle reste à traiter dans Suivi"
    return resume, {"hektor_annonce_id": int(bien["hektor_annonce_id"]),
                    "validation": "" if validation is None else ("oui" if validation else "non"),
                    "diffusable": "" if diffusable is None else ("oui" if diffusable else "non")}


def executer_pilotage(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    from .hektor_bridge import HektorBridgeService
    if ctx.role not in DIRECTION:  # 3e verrou, après la route (geste.roles) et avant la garde du pont
        raise Refus("le Pilotage est réservé à la direction ; un négociateur passe par la demande de validation")
    bien, validation, diffusable = _controler_pilotage(ctx, p)  # re-vérifié AU CLIC (vendu, clos, déjà dans cet état)
    _email, user = _personne(ctx)
    try:  # = la garde des routes /validation et /diffusable
        SupabaseAdminService(ctx.settings).assert_admin(user)
    except HTTPException as exc:
        raise Refus(f"refusé : {exc.detail}") from None
    pont = HektorBridgeService(ctx.settings)
    vue_validation: str | None = None
    vue_diffusable = "1" if str(bien.get("diffusable") or "") == "1" else "0"
    fait: list[str] = []
    try:
        if validation is not None and validation != _valide(bien.get("validation_diffusion_state")):
            r = pont.set_validation(bien["app_dossier_id"], 1 if validation else 0, False)
            vue_validation = str(r.get("observed_validation") or "").strip().lower() or None
            vue_diffusable = r.get("observed_diffusable") if r.get("observed_diffusable") in {"0", "1"} else vue_diffusable
            if r.get("error"):
                raise Refus(f"Hektor a refusé la validation : {str(r['error'])[:200]}")
            fait.append("validation")
        if diffusable is not None and diffusable != (vue_diffusable == "1"):
            r = pont.set_diffusable(bien["app_dossier_id"], diffusable, False)
            vue_diffusable = r.get("observed_diffusable") if r.get("observed_diffusable") in {"0", "1"} else vue_diffusable
            fait.append("diffusable")
    except HTTPException as exc:
        raise Refus(f"Hektor n'a pas pu être joint ({exc.detail})" + (f" ; déjà fait : {', '.join(fait)}" if fait else "")) from None
    try:  # recopier chez nous ce que Hektor MONTRE (comme l'écran), même si la confirmation manque
        pont.persist_state(bien["app_dossier_id"],
                           validation_diffusion_state=vue_validation if vue_validation in {"oui", "non"} else None,
                           diffusable=vue_diffusable == "1")
        reporte = True
    except Exception:  # noqa: BLE001
        reporte = False
    if "validation" in fait and vue_validation is None:  # une relecture ratée n'est jamais un vert
        raise Refus("la validation est partie chez Hektor mais sa fiche n'a pas pu être relue : vérifie-la sur Hektor")
    if "validation" in fait and vue_validation != ("oui" if validation else "non"):
        raise Refus(f"Hektor n'a pas confirmé la validation : il montre « {vue_validation} »")
    if diffusable is not None and vue_diffusable != ("1" if diffusable else "0"):
        raise Refus(f"Hektor n'a pas confirmé Diffusable : il montre {_oui_non(vue_diffusable == '1')}")
    return {"app_dossier_id": bien["app_dossier_id"], "fait": fait, "validation_vue": vue_validation,
            "diffusable_vu": vue_diffusable, "etat_reporte": reporte}


# ── LOT 2c (17/11/2026) : créer un contact, ajouter une recherche, modifier une recherche ──
# Note : notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md §23-24. Les MÊMES fonctions de la base que l'écran :
#   app_create_contact_optimistic (modale « Nouveau contact », App.tsx:43554 → api.ts:11774), qui contrôle l'appelant ;
#   app_create_search_optimistic (ContactSearchModal.tsx:91 → api.ts:11077) ; app_edit_search_optimistic
#   (ContactSearchModal.tsx:71 → api.ts:11145).
# ⛔ LA COMMUNE : sans commune reconnue, Hektor perd la ville et le code postal (leçon du 22/10). On exige un code
#   postal et une ville qui en fait partie, vérifiée au service de l'écran (geo.api.gouv.fr, fetchCommunesForPostalCode,
#   api.ts:5010). Service en panne : on ne bloque pas (l'écran non plus) et la carte le dit.
# ⛔ UN DOUBLON NE SE CRÉE PAS EN SILENCE : même recherche que l'écran (findContactDuplicateCandidates, api.ts:11927 :
#   même e-mail ou même téléphone) ; s'il en trouve, il faut redemander avec doublon_accepte (le « Continuer malgré
#   doublon » de l'écran), et la carte le dit.
# ⛔ Le contact naît au nom de la personne qui parle (son e-mail, posé par le serveur ; prouvé le 03/11 : travail
#   8809f207 créé chez Hektor avec ce seul e-mail). Pas de société ni de partenaire (le catalogue des métiers, décision
#   du 06/11), pas de rattachement à un bien (geste de l'annonce).
# ⚠ Une recherche créée n'entre dans les rapprochements qu'après Hektor et la descente de nuit (mémoire du 16/10).
TYPES_RECHERCHE = {
    "1": "Maison", "2": "Appartement", "4": "Studio", "18": "Duplex", "39": "Maison de village", "25": "Villa",
    "5": "Terrain", "21": "Immeuble", "43": "Terrain à bâtir", "44": "Terrain agricole", "45": "Terrain de loisir",
    "22": "Propriété", "10": "Mas", "11": "Bastide", "30": "Ferme", "28": "Château", "17": "Chalet", "31": "Loft",
    "41": "Triplex", "27": "Rez-de-villa", "26": "Rez-de-jardin", "16": "Parking", "15": "Garage", "29": "Cave",
    "24": "Cabanon", "20": "Autre",
}  # = TYPE_MAIN + TYPE_MORE de ContactSearchFields.tsx
OFFRES_RECHERCHE = {"achat": "0", "location": "2"}  # DEFAULT_OFFER_OPTIONS de l'écran (vente / location)
CIVILITES = {"": None, "m.": "M.", "mme": "Mme."}   # les deux formes qu'envoie l'écran
GENRES_CONTACT = {"acquereur": "acquéreur", "proprietaire": "propriétaire"}
# critères relus pour qu'une modification ne perde rien de ce que l'écran garde (contactSearchValueFromSearch)
EQUIPEMENTS_RECHERCHE = {
    "garage_parking": "ITEM_GARAGE_PARKING", "terrasse": "ITEM_TERRASSE", "balcon": "ITEM_BALCON",
    "piscine": "ITEM_PISCINE", "ascenseur": "ITEM_ASCENSEUR", "cheminee": "ITEM_CHEMINEE", "cave": "ITEM_CAVE",
    "double_vitrage": "ITEM_DOUBLE_VITRAGE", "plain_pied": "ITEM_PLAIN_PIED", "grenier_comble": "ITEM_GRENIER_COMBLE",
    "acces_handi": "ITEM_ACCES_HANDI", "terrain_constructible": "ITEM_TERRAIN_CONSTRUCTIBLE",
    "terrain_arbore": "ITEM_TERRAIN_ARBORE", "terrain_piscinable": "ITEM_TERRAIN_PISCINABLE",
    "terrain_viabilise": "ITEM_TERRAIN_VIABILISE",
}
_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _simple(texte: Any) -> str:
    sans = unicodedata.normalize("NFKD", str(texte or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[-'’]", " ", sans)).strip().lower()


def _communes_du_code_postal(cp: str) -> list[str] | None:
    """Les communes d'un code postal (le service de l'écran). None = service injoignable."""
    try:
        r = requests.get("https://geo.api.gouv.fr/communes", params={"codePostal": cp, "fields": "nom", "format": "json"},
                         timeout=6)
        if not r.ok:
            return None
        return [str(ligne.get("nom") or "").strip() for ligne in (r.json() or []) if ligne.get("nom")]
    except (requests.RequestException, ValueError):
        return None


def _commune(cp: Any, ville: Any) -> list[Any]:
    """[code postal, ville telle que Hektor la connaît, vérifiée ?]"""
    cp = re.sub(r"\s", "", str(cp or ""))
    ville = str(ville or "").strip()
    if not re.fullmatch(r"\d{5}", cp) or not ville:
        raise Refus("Donne le code postal (5 chiffres) ET la ville : sans les deux, Hektor perd la ville.")
    noms = _communes_du_code_postal(cp)
    if noms is None:
        return [cp, ville, False]
    if not noms:
        raise Refus(f"Le code postal {cp} ne correspond à aucune commune.")
    for nom in noms:
        if _simple(nom) == _simple(ville):
            return [cp, nom, True]
    raise Refus(f"{ville} n'est pas une commune du {cp} (communes du {cp} : {', '.join(noms[:12])}). "
                "Hektor perdrait la ville : redemande avec la bonne.")


def _communes(texte: Any) -> list[list[Any]]:
    morceaux = [m.strip() for m in str(texte or "").split("|") if m.strip()]
    if not morceaux:
        raise Refus("Donne au moins une commune, « code postal ville », séparées par | (ex. 42700 Firminy).")
    if len(morceaux) > 10:
        raise Refus("10 communes au plus.")
    lieux: list[list[Any]] = []
    for morceau in morceaux:
        cp = re.search(r"\d{5}", morceau)
        if not cp:
            raise Refus(f"« {morceau} » : il manque le code postal.")
        lieux.append(_commune(cp.group(0), (morceau[:cp.start()] + " " + morceau[cp.end():]).replace(",", " ")))
    return lieux


def _types(texte: Any) -> list[str]:
    par_libelle = {_simple(libelle): code for code, libelle in TYPES_RECHERCHE.items()}
    codes: list[str] = []
    for morceau in (m.strip() for m in str(texte or "").split("|")):
        if not morceau:
            continue
        code = morceau if morceau in TYPES_RECHERCHE else par_libelle.get(_simple(morceau))
        if not code:
            raise Refus(f"Type de bien inconnu : « {morceau} ». Possibles : {', '.join(TYPES_RECHERCHE.values())}.")
        if code not in codes:
            codes.append(code)
    if not codes:
        raise Refus("Donne au moins un type de bien (ex. Maison|Appartement).")
    return codes


def _entier(valeur: Any, quoi: str, maxi: int = 100_000_000) -> int | None:
    texte = re.sub(r"[\s €]", "", str(valeur or ""))
    if not texte:
        return None
    if not texte.isdigit():
        raise Refus(f"{quoi} : un nombre entier, sans texte (reçu « {valeur} »).")
    nombre = int(texte)
    if nombre > maxi:
        raise Refus(f"{quoi} : {nombre} paraît faux.")
    return nombre or None


def _criteres(p: dict[str, Any]) -> dict[str, Any]:
    """Les critères d'une NOUVELLE recherche, avec les garde-fous de l'écran (un type, une commune, un budget max)."""
    offre = OFFRES_RECHERCHE.get(str(p.get("offre") or "achat").strip().lower())
    if offre is None:
        raise Refus("Offre : achat ou location.")
    budget_min, budget_max = _entier(p.get("budget_min"), "Budget minimum"), _entier(p.get("budget_max"), "Budget maximum")
    if not budget_max:
        raise Refus("Donne le budget maximum : l'écran l'exige aussi.")
    if budget_min and budget_min > budget_max:
        raise Refus("Le budget minimum dépasse le maximum.")
    return {"offre": offre, "types": _types(p.get("types")), "lieux": _communes(p.get("communes")),
            "budget_min": budget_min, "budget_max": budget_max,
            "surface_min": _entier(p.get("surface_min"), "Surface minimum", 100_000),
            "terrain_min": _entier(p.get("terrain_min"), "Terrain minimum", 10_000_000),
            "pieces_min": _entier(p.get("pieces_min"), "Pièces minimum", 50),
            "chambres_min": _entier(p.get("chambres_min"), "Chambres minimum", 50),
            "salles_de_bain_min": None, "dpe": None, "marge": None, "equipements": []}


def _recherche_pour_hektor(c: dict[str, Any]) -> dict[str, Any]:
    """La recherche dans la forme de l'écran (contactSearchValueToInput, puis hContactSearchPayload, api.ts:10933)."""
    def texte(nombre: Any) -> str | None:
        return str(nombre) if nombre else None
    return {"kind": "search_criteria", "enabled": True, "offerCode": c["offre"], "propertyTypeIds": list(c["types"]),
            "city": None, "postalCode": None,
            "localities": [{"city": ville, "postalCode": cp} for cp, ville, _ in c["lieux"]],
            "priceMin": str(c.get("budget_min") or 0), "priceMax": str(c["budget_max"]), "priceMargin": c.get("marge") or None,
            "surfaceMin": texte(c.get("surface_min")), "landSurfaceMin": texte(c.get("terrain_min")),
            "roomsMin": texte(c.get("pieces_min")), "bedroomsMin": texte(c.get("chambres_min")),
            "bathroomsMin": texte(c.get("salles_de_bain_min")), "dpeLetter": c.get("dpe") or None,
            "equipments": list(c.get("equipements") or []), "particulariteIds": []}


def _libelles_types(codes: list[str], connus: dict[str, str] | None = None) -> list[str]:
    connus = connus or {}
    return [TYPES_RECHERCHE.get(code) or connus.get(code) or code for code in codes]


def _dire_criteres(c: dict[str, Any], connus: dict[str, str] | None = None) -> str:
    morceaux = [("achat" if c["offre"] == "0" else "location") + " : " + ", ".join(_libelles_types(c["types"], connus)),
                ", ".join(f"{ville} ({cp})" for cp, ville, _ in c["lieux"])]
    budget = f"jusqu'à {_euros(c['budget_max'])}" if c.get("budget_max") else "sans budget"
    if c.get("budget_min"):
        budget += f" (dès {_euros(c['budget_min'])})"
    morceaux.append(budget)
    for cle, unite in (("surface_min", " m² min"), ("terrain_min", " m² de terrain min"), ("pieces_min", " pièces min"),
                       ("chambres_min", " chambres min")):
        if c.get(cle):
            morceaux.append(f"{c[cle]}{unite}")
    if any(not verifiee for _, _, verifiee in c["lieux"]):
        morceaux.append("⚠ commune non vérifiée (service des communes injoignable)")
    return " — ".join(morceaux)


def _telephone(valeur: Any) -> str:
    brut = str(valeur or "").strip()
    chiffres = re.sub(r"[^\d+]", "", brut)
    if brut and len(re.sub(r"\D", "", chiffres)) < 9:
        raise Refus(f"« {brut} » n'est pas un numéro de téléphone.")
    return chiffres


def _filtre(valeur: str) -> str:  # escapePostgrestFilterValue (api.ts)
    return '"' + valeur.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _doublons(ctx: ContexteAssistant, email: str, telephone: str) -> list[dict[str, Any]]:
    filtres = ([f"email.ilike.{_filtre(email)}"] if email else []) + \
        ([f"phone_primary.eq.{_filtre(telephone)}", f"phone_secondary.eq.{_filtre(telephone)}"] if telephone else [])
    if not filtres:
        return []
    return _lire(ctx, "app_contacts_current", {"or": "(" + ",".join(filtres) + ")", "limit": "6",
                                               "select": "hektor_contact_id,display_name,archive",
                                               "order": "archive.asc,linked_annonce_count.desc"})


def _dire_doublons(lignes: list[dict[str, Any]]) -> str:
    return " ; ".join(f"{d.get('display_name') or 'sans nom'} (n° {d['hektor_contact_id']}"
                      f"{', archivé' if d.get('archive') else ''})" for d in lignes)


def preparer_creer_contact(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    genre = str(p.get("genre") or "").strip().lower()
    if genre not in GENRES_CONTACT:
        raise Refus("Genre : acquereur ou proprietaire (les sociétés et les partenaires se créent dans l'application).")
    nom = str(p.get("nom") or "").strip()[:120]
    if not nom:
        raise Refus("Donne le nom du contact.")
    prenom = str(p.get("prenom") or "").strip()[:120]
    civilite_brute = _simple(p.get("civilite")).replace(" ", "")
    if civilite_brute not in CIVILITES:
        raise Refus("Civilité : M., Mme, ou vide.")
    email = str(p.get("email") or "").strip()[:200]
    if email and not _EMAIL.fullmatch(email):
        raise Refus(f"« {email} » n'est pas une adresse e-mail.")
    telephone = _telephone(p.get("telephone"))
    if not email and not telephone:
        raise Refus("Donne un téléphone ou un e-mail : l'écran exige un moyen de joindre le contact.")
    conjoint_nom = str(p.get("conjoint_nom") or "").strip()[:120]
    conjoint_prenom = str(p.get("conjoint_prenom") or "").strip()[:120]
    if conjoint_prenom and not conjoint_nom:
        raise Refus("Donne aussi le nom du conjoint (il peut être le même).")
    lieu = _commune(p.get("code_postal"), p.get("ville")) if (p.get("code_postal") or p.get("ville")) else None
    adresse = str(p.get("adresse") or "").strip()[:300]
    if adresse and not lieu:
        raise Refus("Une adresse sans code postal ni ville serait perdue chez Hektor : donne-les aussi.")
    recherche = None
    if p.get("avec_recherche"):
        if genre != "acquereur":
            raise Refus("Une recherche se pose sur un acquéreur.")
        recherche = _criteres(p)
    candidats = _doublons(ctx, email, telephone)
    if candidats and not p.get("doublon_accepte"):
        raise Refus(f"Fiche(s) déjà présente(s) avec ce téléphone ou cet e-mail : {_dire_doublons(candidats)}. Si c'est bien "
                    "une autre personne, redemande avec doublon_accepte = true ; sinon, sers-toi de la fiche existante.")
    civilite = CIVILITES[civilite_brute]
    qui = " ".join(x for x in (civilite, prenom, nom.upper()) if x)
    lignes = [f"Créer le contact {qui}, {GENRES_CONTACT[genre]}"
              + (f", en couple avec {' '.join(x for x in (conjoint_prenom, conjoint_nom.upper()) if x)}" if conjoint_nom else "")]
    lignes.append(", ".join(x for x in (f"tél. {telephone}" if telephone else "", email) if x))
    if lieu:
        lignes.append(", ".join(x for x in (adresse, f"{lieu[0]} {lieu[1]}") if x)
                      + ("" if lieu[2] else " (⚠ commune non vérifiée)"))
    if recherche:
        lignes.append("avec sa recherche — " + _dire_criteres(recherche))
    lignes.append("à ton nom ; " + ("Hektor enverra au contact l'e-mail de consentement RGPD" if p.get("email_rgpd")
                                    else "sans e-mail RGPD"))
    if candidats:
        lignes.append(f"⚠ doublon possible, accepté : {_dire_doublons(candidats)}")
    lignes.append("écrit chez nous tout de suite avec un numéro de l'app, recopié chez Hektor ensuite")
    contact = {"civilite": civilite, "last_name": nom, "first_name": prenom or None, "company_name": None, "sociale": None,
               "spouse_last_name": conjoint_nom or None, "spouse_first_name": conjoint_prenom or None,
               "email": email or None, "phone": telephone or None, "phone_secondary": None,
               "address": adresse or None, "postal_code": lieu[0] if lieu else None, "city": lieu[1] if lieu else None,
               "contact_kind": genre, "person_type": "couple" if conjoint_nom else "personne_seule",
               "comments": str(p.get("commentaire") or "").strip()[:2000] or None,
               "send_rgpd_email": bool(p.get("email_rgpd")),
               "contact_next_step": _recherche_pour_hektor(recherche) if recherche else None}
    return " — ".join(lignes), {"contact": contact, "doublon_accepte": bool(candidats)}


def executer_creer_contact(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    contact = dict(p.get("contact") or {})
    if not contact.get("last_name") or not (contact.get("email") or contact.get("phone")):
        raise Refus("carte incomplète")
    if not p.get("doublon_accepte"):  # re-vérifié AU CLIC : une fiche a pu naître depuis la carte
        candidats = _doublons(ctx, str(contact.get("email") or ""), str(contact.get("phone") or ""))
        if candidats:
            raise Refus(f"une fiche avec ce téléphone ou cet e-mail est apparue depuis la carte : {_dire_doublons(candidats)}")
    # ⛔ le compte qui porte le contact = la personne qui parle, posé ICI par le serveur
    contact.update({"hektor_user_email": ctx.email, "target_hektor_user_email": ctx.email})
    travail = _ecrire(ctx, "POST", "rpc/app_create_contact_optimistic", {"contact_payload": contact, "job_priority": 18}) or {}
    if isinstance(travail, list):
        travail = travail[0] if travail else {}
    return {"travail": travail.get("id"), "statut": travail.get("status"),
            "avec_recherche": bool(contact.get("contact_next_step"))}


def _fiche_pour_recherche(ctx: ContexteAssistant, numero: Any) -> dict[str, Any]:
    numero = str(numero or "").strip()
    if not numero.isdigit():
        raise Refus("Donne le numéro du contact (hektor_contact_id, objet contacts).")
    lignes = _lire(ctx, "app_contacts_current", {"hektor_contact_id": f"eq.{numero}", "limit": "1",
                                                 "select": "hektor_contact_id,display_name,archive,ville,code_postal"})
    if not lignes:
        raise Refus(f"Le contact {numero} n'est pas parmi ceux que tu peux voir.")
    if lignes[0].get("archive"):
        raise Refus("Ce contact est archivé : réactive-le d'abord (ses recherches ne reviennent pas seules).")
    return lignes[0]


def preparer_ajouter_recherche(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    fiche = _fiche_pour_recherche(ctx, p.get("hektor_contact_id"))
    criteres = _criteres(p)
    return f"Ajouter une recherche à {fiche.get('display_name') or fiche['hektor_contact_id']} — {_dire_criteres(criteres)} " \
           "(créée chez Hektor ; elle entre dans les rapprochements après la nuit)", \
        {"hektor_contact_id": fiche["hektor_contact_id"], "criteres": criteres}


def executer_ajouter_recherche(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    fiche = _fiche_pour_recherche(ctx, p.get("hektor_contact_id"))  # re-vérifié AU CLIC
    c = dict(p.get("criteres") or {})
    recherche = _recherche_pour_hektor(c)

    def texte(nombre: Any) -> str | None:
        return str(nombre) if nombre else None
    # la ligne provisoire, dans les formes de app_contact_search_current (api.ts:11047)
    champs = {"offre": c["offre"], "villes_json": [f"{cp} {ville}" for cp, ville, _ in c["lieux"]],
              "types_json": {libelle: "1" for libelle in _libelles_types(c["types"])}, "criteres_json": [],
              "prix_min": texte(c.get("budget_min")), "prix_max": texte(c.get("budget_max")),
              "surface_min": texte(c.get("surface_min")), "surface_max": None,
              "pieces_min": texte(c.get("pieces_min")), "pieces_max": None,
              "chambre_min": texte(c.get("chambres_min")), "chambre_max": None,
              "surface_terrain_min": texte(c.get("terrain_min")), "surface_terrain_max": None}
    contexte = {k: v for k, v in (("city", fiche.get("ville")), ("postal_code", fiche.get("code_postal"))) if v}
    travail = _ecrire(ctx, "POST", "rpc/app_create_search_optimistic", {
        "p_token": str(uuid.uuid4()), "p_fields": champs, "target_contact_id": str(fiche["hektor_contact_id"]),
        "search_payload": {**contexte, "search": recherche}, "job_priority": 17}) or {}
    if isinstance(travail, list):
        travail = travail[0] if travail else {}
    return {"hektor_contact_id": fiche["hektor_contact_id"], "travail": travail.get("id"), "statut": travail.get("status")}


def _json(valeur: Any) -> Any:
    if isinstance(valeur, str):
        try:
            return json.loads(valeur)
        except ValueError:
            return None
    return valeur


def _recherche_complete(ctx: ContexteAssistant, cle: Any) -> dict[str, Any]:
    cle = str(cle or "").strip()
    if not cle:
        raise Refus("Donne la clé de la recherche (contact_search_key, objet recherches).")
    lignes = _lire(ctx, "app_contact_searches_current", {
        "contact_search_key": f"eq.{cle}", "limit": "1",
        "select": "contact_search_key,hektor_contact_id,search_index,archive,is_active,offre,villes_json,types_json,"
                  "criteres_json,prix_min,prix_max,surface_min,surface_terrain_min,pieces_min,chambre_min"})
    if not lignes:
        raise Refus(f"La recherche {cle} n'est pas parmi celles que tu peux voir.")
    recherche = lignes[0]
    if recherche.get("archive") is True:
        raise Refus("Cette recherche est archivée.")
    if recherche.get("search_index") is None:
        raise Refus("Cette recherche n'a pas encore de rang chez Hektor (créée récemment ?) : l'écran ne peut pas la "
                    "modifier non plus avant la nuit.")
    return recherche


def _criteres_actuels(r: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Les critères tels que l'écran les relit (contactSearchValueFromSearch, ContactSearchFields.tsx:144).
    ⚠ Écart VOULU : l'écran remplace un prix vide par 120 000 / 250 000 ; ici un vide reste vide."""
    criteres = {}
    for item in (_json(r.get("criteres_json")) or []):
        if isinstance(item, dict) and item.get("cle"):
            criteres[str(item["cle"])] = "" if item.get("valeur") is None else str(item["valeur"])
    lieux = []
    for entree in (_json(r.get("villes_json")) or []):
        texte = str(entree or "")
        cp = re.search(r"\d{4,5}", texte)
        ville = re.sub(r"[·,]", "", re.sub(r"\d{4,5}", "", texte)).strip()
        if ville or cp:
            lieux.append([cp.group(0) if cp else "", ville, True])
    types = _json(r.get("types_json"))
    connus = {str(k): str(v) for k, v in types.items()} if isinstance(types, dict) else {}
    codes = list(connus) if connus else [str(t) for t in (types or [])]

    def nombre(valeur: Any) -> int | None:
        chiffres = re.sub(r"[^\d]", "", str(valeur or "").split(".")[0])
        return int(chiffres) if chiffres and int(chiffres) > 0 else None
    return {"offre": str(r.get("offre") or "0"), "types": codes, "lieux": lieux,
            "budget_min": nombre(r.get("prix_min")), "budget_max": nombre(r.get("prix_max")),
            "surface_min": nombre(r.get("surface_min")), "terrain_min": nombre(r.get("surface_terrain_min")),
            "pieces_min": nombre(r.get("pieces_min")), "chambres_min": nombre(r.get("chambre_min")),
            "salles_de_bain_min": nombre(criteres.get("ITEM_SDB_SDE_MIN")), "dpe": criteres.get("ITEM_DPE_CONS_LETTER") or None,
            "marge": criteres.get("ITEM_PRIX_MARGE") or None,
            "equipements": [code for code, item in EQUIPEMENTS_RECHERCHE.items()
                            if re.fullmatch(r"1|oui|true", criteres.get(item, ""), re.I)]}, connus


def preparer_modifier_recherche(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    r = _recherche_complete(ctx, p.get("contact_search_key"))
    avant, connus = _criteres_actuels(r)
    apres = json.loads(json.dumps(avant))
    changements = []
    if str(p.get("types") or "").strip():
        apres["types"] = _types(p.get("types"))
    if str(p.get("communes") or "").strip():
        apres["lieux"] = _communes(p.get("communes"))
    for cle, quoi, maxi in (("budget_min", "Budget minimum", 100_000_000), ("budget_max", "Budget maximum", 100_000_000),
                            ("surface_min", "Surface minimum", 100_000), ("terrain_min", "Terrain minimum", 10_000_000),
                            ("pieces_min", "Pièces minimum", 50), ("chambres_min", "Chambres minimum", 50)):
        if str(p.get(cle) or "").strip():
            apres[cle] = _entier(p.get(cle), quoi, maxi)
    brut_rayon = re.sub(r"\s|km", "", str(p.get("rayon_km") or "").lower())
    rayon = None
    if brut_rayon:
        if not brut_rayon.isdigit() or int(brut_rayon) > 40:
            raise Refus("Rayon : de 0 à 40 km (le curseur de l'écran).")
        rayon = int(brut_rayon)
    if not apres.get("budget_max"):
        raise Refus("Cette recherche n'a pas de budget maximum : donne-le (l'écran l'exige).")
    if apres.get("budget_min") and apres["budget_min"] > apres["budget_max"]:
        raise Refus("Le budget minimum dépasse le maximum.")
    if not apres["types"] or not apres["lieux"]:
        raise Refus("Une recherche garde au moins un type et une commune.")
    if apres["types"] != avant["types"]:
        changements.append(f"types : {', '.join(_libelles_types(avant['types'], connus)) or 'aucun'} → "
                           f"{', '.join(_libelles_types(apres['types'], connus))}")
    if [lieu[:2] for lieu in apres["lieux"]] != [lieu[:2] for lieu in avant["lieux"]]:
        changements.append(f"communes : {', '.join(f'{v} ({c})' for c, v, _ in avant['lieux']) or 'aucune'} → "
                           f"{', '.join(f'{v} ({c})' for c, v, _ in apres['lieux'])}")
    for cle, libelle in (("budget_min", "budget min"), ("budget_max", "budget max"), ("surface_min", "surface min"),
                         ("terrain_min", "terrain min"), ("pieces_min", "pièces min"), ("chambres_min", "chambres min")):
        if apres.get(cle) != avant.get(cle):
            def dire(v: Any, euros: bool = cle.startswith("budget")) -> str:
                return "vide" if not v else (_euros(v) if euros else str(v))
            changements.append(f"{libelle} : {dire(avant.get(cle))} → {dire(apres.get(cle))}")
    if rayon is not None:
        changements.append(f"rayon autour des communes : {rayon} km")
    if not changements:
        raise Refus("Rien ne change : donne au moins un critère différent de la recherche actuelle.")
    nom = _acquereur(ctx, r)
    # ⚠ Prouvé en réel le 16/11 : une recherche MODIFIÉE ne repart plus chez Hektor (décision C.3 du 24/08, « fermer la
    #   porte sortante des recherches » : app_edit_search_optimistic pose push_search = null) -- comme à l'écran.
    return f"Modifier la recherche n° {int(r['search_index']) + 1} de {nom} — " + " ; ".join(changements) + \
        " (écrit chez nous tout de suite, rapprochements recalculés ; une recherche modifiée reste chez nous, elle ne " \
        "repart plus chez Hektor depuis le 24/08, comme à l'écran)", \
        {"contact_search_key": r["contact_search_key"], "avant": avant, "apres": apres, "rayon_km": rayon,
         "libelles": _libelles_types(apres["types"], connus)}


def executer_modifier_recherche(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    r = _recherche_complete(ctx, p.get("contact_search_key"))  # le rang est RELU au clic (il peut bouger)
    actuel, _ = _criteres_actuels(r)
    if json.loads(json.dumps(actuel)) != p.get("avant"):
        raise Refus("la recherche a changé depuis la carte : redemande la modification")
    corps: dict[str, Any] = {"search": _recherche_pour_hektor(p["apres"]), "search_index": int(r["search_index"]),
                             "type_labels": list(p.get("libelles") or [])}
    if p.get("rayon_km") is not None:
        corps["rayon_km"] = str(int(p["rayon_km"]))
    _ecrire(ctx, "POST", "rpc/app_edit_search_optimistic",
            {"target_contact_id": str(r["hektor_contact_id"]), "search_payload": corps, "debounce_seconds": 600})
    return {"contact_search_key": r["contact_search_key"], "search_index": int(r["search_index"])}


# ── Étape 4 (16/11/2026) : GÉNÉRER LE NUMÉRO DE MANDAT (écran : HektorMandatNumberForm, App.tsx ~3920) ──────────
# Le numéro est une RÉSERVATION OFFICIELLE chez Hektor (Protexa) : il ne se défait pas. La fonction de la base
# `app_console_create_mandat_auto_number_job` contrôle les droits de la personne sur le bien
# (`app_console_can_request_job`) ; les autres gardes de l'écran sont refaites ICI, à la carte ET au clic : pas de numéro
# déjà présent (l'écran a un mode « nouveau mandat » à part, NON ouvert ici), au moins un mandant, un négociateur sur le
# bien. Les mandants ne sont pas passés : le worker les retrouve lui-même sur le bien (il le fait déjà quand la liste est
# vide) — la carte les NOMME seulement. Seul le « Mandat de vente » et ses sous-types de l'écran sont ouverts ici.
SOUS_TYPES_MANDAT_VENTE = (
    "Mandat de vente",
    "Mandat de vente exclusif sans demarchage",
    "Mandat de vente exclusif en cas de demarchage",
    "Mandat de vente non exclusif sans demarchage",
    "Mandat de vente non exclusif en cas de demarchage",
    "Vente par lots",
    "Vente de terrain",
    "Vente en etat futur d'achevement (VEFA)",
    "Cession de Parts Sociales de SARL ou SCI",
    "Vente de fonds de commerce",
    "Vente de murs et fonds de commerce",
    "Mandat de vente semi-exclusif",
)


def _bien_pour_mandat(ctx: ContexteAssistant, hektor_annonce_id: Any) -> tuple[dict[str, Any], list[str], str | None]:
    bien = _bien_vivant(ctx, hektor_annonce_id)
    if str(bien.get("numero_mandat") or "").strip():
        raise Refus(f"L'annonce {bien['hektor_annonce_id']} a déjà le mandat {bien['numero_mandat']} : un NOUVEAU mandat "
                    "sur un bien qui en a déjà un se fait depuis sa fiche (« Ajouter un nouveau mandat »).")
    tete = (_lire(ctx, "app_dossiers_current", {"app_dossier_id": f"eq.{bien['app_dossier_id']}", "limit": "1",
                                               "select": "negociateur_email,commercial_id"}) or [{}])[0]
    if not str(tete.get("negociateur_email") or "").strip() and not str(tete.get("commercial_id") or "").strip():
        raise Refus(f"L'annonce {bien['hektor_annonce_id']} n'a pas de négociateur : choisis-le sur sa fiche avant le numéro.")
    relations = _lire(ctx, "app_contact_relations_current", {
        # ⚠ sur un bien SANS numéro, les vendeurs portent le rôle « proprietaire » (« mandant » n'existe qu'une fois le
        # mandat numéroté — mesuré le 08/10) : les deux comptent, comme ROLES_MANDANT du push (export_app_payload.py)
        "hektor_annonce_id": f"eq.{bien['hektor_annonce_id']}", "role_contact": "in.(mandant,proprietaire)",
        "select": "hektor_contact_id", "limit": "20"})
    ids = sorted({str(r.get("hektor_contact_id") or "").strip() for r in relations} - {""})
    if not ids:
        raise Refus(f"L'annonce {bien['hektor_annonce_id']} n'a aucun mandant : ajoute-le sur sa fiche avant de générer le "
                    "numéro (comme à l'écran).")
    fiches = _lire(ctx, "app_contacts_current", {"hektor_contact_id": f"in.({','.join(ids)})", "select": "display_name",
                                                 "limit": "20"})
    noms = [str(f.get("display_name") or "").strip() for f in fiches if str(f.get("display_name") or "").strip()]
    return bien, noms or [f"contact {i}" for i in ids], str(tete.get("negociateur_email") or "").strip() or None


def _date_debut(brute: Any) -> date:
    texte = str(brute or "").strip()
    if not texte:
        return datetime.now(PARIS).date()
    try:
        jour = date.fromisoformat(texte)
    except ValueError:
        raise Refus("La date de début s'écrit AAAA-MM-JJ (ex. 2026-11-16).")
    if abs((jour - datetime.now(PARIS).date()).days) > 366:
        raise Refus("La date de début doit être à moins d'un an d'aujourd'hui.")
    return jour


def preparer_numero_mandat(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien, noms, _nego = _bien_pour_mandat(ctx, p.get("hektor_annonce_id"))
    sous_type = str(p.get("sous_type") or "").strip() or "Mandat de vente"
    if sous_type not in SOUS_TYPES_MANDAT_VENTE:
        raise Refus("Sous-type de mandat inconnu. Au choix : " + " ; ".join(SOUS_TYPES_MANDAT_VENTE) + ".")
    debut = _date_debut(p.get("date_debut"))
    duree = str(p.get("duree_mois") or "").strip() or "12"
    if not duree.isdigit() or not 1 <= int(duree) <= 120:
        raise Refus("La durée est un nombre de mois, de 1 à 120.")
    tacite = str(p.get("tacite_reconduction") or "oui").strip().lower() not in {"non", "0", "false", "no"}
    resume = (f"Générer le NUMÉRO DE MANDAT officiel de l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » "
              f"— {sous_type}, à partir du {debut.strftime('%d/%m/%Y')}, {duree} mois, "
              f"{'avec' if tacite else 'sans'} tacite reconduction ; mandant(s) : {', '.join(noms)}. "
              "⚠ Hektor réserve le prochain numéro et une ligne est créée au registre des mandats : cela NE SE DÉFAIT PAS.")
    return resume, {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "sous_type": sous_type,
                    "date_debut": debut.isoformat(), "duree_mois": duree, "tacite": tacite}


def executer_numero_mandat(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien, _noms, negociateur = _bien_pour_mandat(ctx, p.get("hektor_annonce_id"))  # re-vérifié AU CLIC : toujours sans numéro, etc.
    sous_type = str(p.get("sous_type") or "Mandat de vente")
    if sous_type not in SOUS_TYPES_MANDAT_VENTE:
        raise Refus("sous-type de mandat inconnu")
    debut = date.fromisoformat(str(p.get("date_debut")))
    travail = _ecrire(ctx, "POST", "rpc/app_console_create_mandat_auto_number_job", {
        "target_app_dossier_id": bien["app_dossier_id"],
        "target_hektor_annonce_id": str(bien["hektor_annonce_id"]),
        # la même charge que l'écran (createHektorMandatAutoNumberJob, lib/api.ts ~12272), mandants laissés au worker
        "mandat_payload": {"type_mandat": "Mandat de vente", "sub_type_mandat": sous_type,
                           "date_debut": debut.strftime("%d/%m/%Y"), "duree_mandat": str(p.get("duree_mois") or "12"),
                           "tacite_reconduction": "1" if p.get("tacite", True) else "0", "mandant_contact_ids": [],
                           "hektor_user_email": negociateur},
        "job_priority": 12})
    travail = travail or {}
    return {"app_dossier_id": bien["app_dossier_id"], "travail": travail.get("id"), "statut": travail.get("status")}


# ── Étape 4 (16/11/2026) : RELANCER UN SIGNATAIRE et ANNULER LA SIGNATURE (Youtrust) ─────────────────────────────
# Écran : SuiviSignatairesYoutrust.tsx + lib/suiviSignataires.ts (les règles de Youtrust, pour ne poser AUCUN travail
# qu'il refuserait) : relancer = demande `ongoing` ET signataire `notified` ; annuler = demande `ongoing` ou `approval`.
# Les gestes n'existent que si l'interrupteur `signature_youtrust` le permet (`on` = tous ; `admin` = les admins) — le
# worker le revérifie (exigerInterrupteurYoutrust). Le travail est celui de l'écran (`poserTravailYoutrust`,
# lib/api.ts ~10478), posé avec le jeton de la personne. ⛔ L'e-mail d'un signataire ne figure JAMAIS dans la carte : le
# résumé repart au modèle. ImmoSign (l'ancien prestataire) n'est pas ouvert ici. L'ENVOI passe par la fenêtre de l'écran.
DEMANDE_SIGNATURE_EN_COURS = ("ongoing", "approval")


def _youtrust_ouvert(ctx: ContexteAssistant) -> None:
    lignes = _lire(ctx, "app_setting", {"key": "eq.signature_youtrust", "select": "value", "limit": "1"})
    cran = str((lignes or [{}])[0].get("value") or "").strip().lower()
    if cran in {"on", "true", "1", "yes"} or (cran == "admin" and ctx.role == "admin"):
        return
    raise Refus("La signature Youtrust n'est pas ouverte à ton compte : relance et annulation se font depuis la fiche du bien.")


def _nom_signataire(s: dict[str, Any]) -> str:
    return " ".join(str(s.get(c) or "").strip() for c in ("prenom", "nom") if str(s.get(c) or "").strip()) or "le signataire"


def _signatures_en_cours(ctx: ContexteAssistant, hektor_annonce_id: Any, document: Any = "") -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """(document, demande) des signatures Youtrust EN COURS du bien ; `document` (un morceau de son nom) départage."""
    _youtrust_ouvert(ctx)
    bien = _bien_vivant(ctx, hektor_annonce_id)
    documents = _lire(ctx, "app_console_document", {"app_dossier_id": f"eq.{bien['app_dossier_id']}",
                                                    "select": "id,app_dossier_id,hektor_annonce_id,document_name,metadata_json",
                                                    "limit": "200"})
    trouves: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for d in documents:
        sig = ((d.get("metadata_json") or {}) if isinstance(d.get("metadata_json"), dict) else {}).get("signature") or {}
        if sig.get("provider") != "youtrust" or not sig.get("signature_request_id"):
            continue
        demande = (_lire(ctx, "app_signature_request", {"id": f"eq.{sig['signature_request_id']}", "limit": "1",
                                                         "select": "id,status,signers"}) or [None])[0]
        if demande and str(demande.get("status") or "") in DEMANDE_SIGNATURE_EN_COURS:
            trouves.append((d, demande))
    filtre = str(document or "").strip().lower()
    if filtre:
        trouves = [(d, dm) for d, dm in trouves if filtre in str(d.get("document_name") or "").lower()]
    if not trouves:
        raise Refus(f"Aucune signature Youtrust en cours sur l'annonce {bien['hektor_annonce_id']}"
                    + (f" pour « {document} »" if filtre else "") + ".")
    if len(trouves) > 1:
        raise Refus("Plusieurs signatures sont en cours sur ce bien : précise le document ("
                    + " ; ".join(str(d.get("document_name") or "") for d, _ in trouves) + ").")
    return trouves


def _signataire_a_relancer(demande: dict[str, Any], qui: Any) -> dict[str, Any]:
    signers = demande.get("signers") if isinstance(demande.get("signers"), list) else []
    relancables = [s for s in signers if str(demande.get("status") or "") == "ongoing"
                   and s.get("status") == "notified" and s.get("provider_signer_id")]
    filtre = str(qui or "").strip().lower()
    if filtre:
        relancables = [s for s in relancables if filtre in _nom_signataire(s).lower()]
    if not relancables:
        raise Refus("Personne à relancer : Youtrust ne relance qu'un signataire invité qui n'a pas encore signé, dans une "
                    "signature en cours" + (f" (aucun ne correspond à « {qui} »)" if filtre else "") + ".")
    if len(relancables) > 1:
        raise Refus("Plusieurs signataires attendent : précise lequel (" + ", ".join(_nom_signataire(s) for s in relancables) + ").")
    return relancables[0]


def _poser_travail_youtrust(ctx: ContexteAssistant, type_travail: str, document: dict[str, Any], demande_id: str,
                            signataire_id: str | None = None) -> dict[str, Any]:
    corps = {"job_type": type_travail, "app_dossier_id": document["app_dossier_id"],
             "hektor_annonce_id": str(document["hektor_annonce_id"]), "priority": 24, "requested_by": ctx.user_id,
             "payload_json": {"signature_request_id": demande_id, "app_console_document_id": document["id"],
                              "document_name": document.get("document_name"),
                              **({"provider_signer_id": signataire_id} if signataire_id else {})}}
    r = _ecrire(ctx, "POST", "app_console_job", corps)
    travail = (r or [{}])[0] if isinstance(r, list) else (r or {})
    return {"travail": travail.get("id"), "statut": travail.get("status")}


def preparer_relance_signature(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    document, demande = _signatures_en_cours(ctx, p.get("hektor_annonce_id"), p.get("document"))[0]
    s = _signataire_a_relancer(demande, p.get("signataire"))
    return (f"Relancer la signature de « {document.get('document_name')} » (annonce {document['hektor_annonce_id']}) : "
            f"Youtrust renvoie le lien de signature à {_nom_signataire(s)} (un e-mail part chez lui).",
            {"hektor_annonce_id": int(document["hektor_annonce_id"]), "document_id": document["id"],
             "signature_request_id": demande["id"], "provider_signer_id": s["provider_signer_id"]})


def executer_relance_signature(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    # re-vérifié AU CLIC : interrupteur, demande toujours en cours, le MÊME signataire toujours à relancer
    trouves = [(d, dm) for d, dm in _signatures_en_cours(ctx, p.get("hektor_annonce_id"))
               if d["id"] == p.get("document_id") and dm["id"] == p.get("signature_request_id")]
    if not trouves:
        raise Refus("cette signature n'est plus en cours")
    document, demande = trouves[0]
    if not any(s.get("provider_signer_id") == p.get("provider_signer_id") and s.get("status") == "notified"
               for s in (demande.get("signers") or [])) or demande.get("status") != "ongoing":
        raise Refus("ce signataire n'est plus à relancer (il a signé, ou la signature a changé)")
    return {"document_id": document["id"], **_poser_travail_youtrust(ctx, "youtrust_remind_signer", document,
                                                                    demande["id"], str(p["provider_signer_id"]))}


def preparer_annulation_signature(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    document, demande = _signatures_en_cours(ctx, p.get("hektor_annonce_id"), p.get("document"))[0]
    signers = demande.get("signers") if isinstance(demande.get("signers"), list) else []
    signes = sum(1 for s in signers if s.get("status") == "signed")
    return (f"Annuler la signature électronique en cours de « {document.get('document_name')} » (annonce "
            f"{document['hektor_annonce_id']}, {signes} signature{'s' if signes > 1 else ''} sur {len(signers)}) : les "
            "signataires ne pourront plus signer ce lien ; le document redevient « à signer » (à renvoyer, ou à signer à la main).",
            {"hektor_annonce_id": int(document["hektor_annonce_id"]), "document_id": document["id"],
             "signature_request_id": demande["id"]})


def executer_annulation_signature(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    trouves = [(d, dm) for d, dm in _signatures_en_cours(ctx, p.get("hektor_annonce_id"))
               if d["id"] == p.get("document_id") and dm["id"] == p.get("signature_request_id")]
    if not trouves:
        raise Refus("cette signature n'est plus en cours (déjà signée, annulée ou expirée)")
    document, demande = trouves[0]
    return {"document_id": document["id"], **_poser_travail_youtrust(ctx, "youtrust_cancel_signature", document, demande["id"])}


# ── Étape 4 (16/11/2026, audit §35) : CARTES DIRECTES — mandants, contacts, annonce ──────────────────────────────
# Note : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §35-36. Chaque carte appelle LA fonction de la base de
# l'écran (définitions relues en base le 16/11), avec le jeton de la personne : c'est la base qui tranche les droits
# (app_console_can_request_job / _contact_job). Les gardes de l'écran sont refaites ICI, à la carte ET au clic.
# ⛔ Deux numéros de contact (mémoire « detailcontact sourceId ») : NOTRE numéro pour l'app, le numéro HEKTOR
#   (hektor_target_id) pour ce qui part chez Hektor. Retirer un mandant exige le numéro Hektor (degroupproprio) ;
#   rattacher prend le nôtre, comme le sélecteur de l'écran (le worker traduit, cibleHektorContact).
# ⛔ Seulement les biens VIVANTS (app_dossiers_current) pour le négociateur, l'archivage et le statut ; un vendu ou un
#   clos passe par sa fiche. Désarchiver lit l'index des archives.
# ⛔ Créer un mandant / modifier son e-mail ou portable : PAS ICI tant que leurs deux fonctions ne contrôlent pas
#   l'appelant (patch de la base préparé, à son accord).
TYPES_GESTE_ANNONCE = ("delete_hektor_annonce", "archive_hektor_annonce", "restore_hektor_annonce",
                       "change_hektor_annonce_status")  # = activeAdminAnnonceJobIds de l'écran (App.tsx ~15450)
CAUSES_ARCHIVAGE = {  # la modale « Archiver l'annonce » (App.tsx ~23330) : cause -> (motif principal, libellé)
    "agence": ("choiceVendu", "Vendu par l'agence"),
    "confrere": ("choiceVendu", "Vendu par un confrère"),
    "proprietaire": ("choiceVendu", "Vendu par le propriétaire"),
    "concurence": ("choiceAutre", "Parti à la concurrence"),
    "vendre_seule": ("choiceAutre", "Le propriétaire vend seul"),
    "annuler_vente": ("choiceAutre", "Vente annulée"),
    "non_renouvele": ("choiceAutre", "Mandat non renouvelé"),
    "mandat_non_obtenu": ("choiceAutre", "Mandat non obtenu"),
    "autre": ("choiceAutre", "Autre"),
}
RAISONS_CONJOINT = {  # = raisonAjoutConjoint (lib/coupleAffichage.ts)
    "cran_ferme": "ce geste n'est pas encore ouvert",
    "meme_fiche": "on ne peut pas choisir la même fiche comme conjoint",
    "conjoint_introuvable": "la fiche choisie est introuvable",
    "personne_archivee": "cette fiche est archivée : réactive-la d'abord",
    "conjoint_archive": "la fiche choisie est archivée",
    "notaire": "une fiche notaire n'est jamais un couple",
    "personne_pas_seule": "cette fiche n'est pas une personne seule",
    "conjoint_pas_seul": "la fiche choisie n'est pas une personne seule (case vide, conjoint d'un autre…)",
    "personne_deja_en_couple": "cette personne a déjà un conjoint",
    "conjoint_deja_en_couple": "la fiche choisie a déjà un conjoint",
    "personne_sans_numero_hektor": "cette fiche n'est pas encore créée chez Hektor : réessaie dans une minute",
    "conjoint_sans_numero_hektor": "la fiche choisie n'est pas connue de Hektor",
    "deja_en_cours": "un ajout de conjoint est déjà en cours pour ces fiches",
}
_PAS_SEULE = ("case_conjoint_vide", "case_vide_orpheline", "conjoint", "conjoint_sans_prenom")


def _ecrire_traduit(ctx: ContexteAssistant, chemin: str, corps: Any, traductions: tuple[tuple[str, str], ...]) -> Any:
    """La base refuse avec un code (« mandat_numerote_18912 ») : on le dit en clair, comme l'écran, jamais on ne le tait."""
    try:
        return _ecrire(ctx, "POST", chemin, corps)
    except Refus as refus:
        for motif, phrase in traductions:
            trouve = re.search(motif, str(refus))
            if trouve:
                raise Refus(phrase.format(*trouve.groups())) from refus
        raise


def _contact_choisi(ctx: ContexteAssistant, numero: Any) -> dict[str, Any]:
    numero = str(numero or "").strip()
    if not numero.isdigit():
        raise Refus("Donne le numéro du contact (hektor_contact_id, objet contacts).")
    lignes = _lire(ctx, "app_contacts_current", {
        "hektor_contact_id": f"eq.{numero}", "limit": "1",
        "select": "hektor_contact_id,hektor_target_id,display_name,nom,archive,negociateur_email,commercial_nom,couple_role,"
                  "nature_fiche,couple_json,hektor_couple_contact_id,relation_roles_json,adresse,code_postal,ville"})
    if not lignes:
        raise Refus(f"Le contact {numero} n'est pas parmi ceux que tu peux voir.")
    return lignes[0]


def _nom_contact(fiche: dict[str, Any]) -> str:
    return str(fiche.get("display_name") or "").strip() or f"contact {fiche['hektor_contact_id']}"


def _tete_bien(ctx: ContexteAssistant, bien: dict[str, Any], colonnes: str) -> dict[str, Any]:
    return (_lire(ctx, "app_dossiers_current", {"app_dossier_id": f"eq.{bien['app_dossier_id']}", "limit": "1",
                                               "select": colonnes}) or [{}])[0]


def _exiger_negociateur(ctx: ContexteAssistant, bien: dict[str, Any]) -> dict[str, Any]:
    # = hasHektorNegotiator de l'écran : sans négociateur, le worker ne saurait pas sous quelle identité écrire
    tete = _tete_bien(ctx, bien, "negociateur_email,commercial_id,commercial_nom,statut_annonce,archive,diffusable,"
                                 "numero_dossier,numero_mandat,offre_id,offre_state,compromis_id,compromis_state,vente_id,"
                                 "titre_bien")
    if not str(tete.get("negociateur_email") or "").strip() and not str(tete.get("commercial_id") or "").strip():
        raise Refus(f"L'annonce {bien['hektor_annonce_id']} n'a pas de négociateur : il faut d'abord en affecter un.")
    return tete


def _aucune_action_en_cours(ctx: ContexteAssistant, hektor_annonce_id: Any) -> None:
    if _lire(ctx, "app_console_job", {"hektor_annonce_id": f"eq.{hektor_annonce_id}", "status": "in.(pending,running)",
                                      "job_type": f"in.({','.join(TYPES_GESTE_ANNONCE)})", "select": "id", "limit": "1"}):
        raise Refus(f"Une action Hektor est déjà en cours sur l'annonce {hektor_annonce_id} : attends la fin du traitement.")


def _mandants_du_bien(ctx: ContexteAssistant, bien: dict[str, Any]) -> set[str]:
    relations = _lire(ctx, "app_contact_relations_current", {
        "hektor_annonce_id": f"eq.{bien['hektor_annonce_id']}", "role_contact": "in.(mandant,proprietaire)",
        "select": "hektor_contact_id", "limit": "50"})
    return {str(r.get("hektor_contact_id") or "").strip() for r in relations} - {""}


# — rattacher un contact EXISTANT comme mandant (écran : handleLink, App.tsx ~3376 ; app_link_mandant_optimistic) —
def _controler_rattachement(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    tete = _exiger_negociateur(ctx, bien)
    fiche = _contact_choisi(ctx, p.get("hektor_contact_id"))
    if str(fiche.get("archive") or "").strip().lower() in {"1", "true"}:
        raise Refus(f"La fiche de {_nom_contact(fiche)} est archivée : l'écran ne propose que des contacts actifs.")
    if fiche.get("couple_role") == "menage_resolu":
        raise Refus("C'est la fiche du MÉNAGE : rattache l'une des deux personnes (une personne, une ligne).")
    nego_bien = str(tete.get("negociateur_email") or "").strip().lower()
    if nego_bien and str(fiche.get("negociateur_email") or "").strip().lower() != nego_bien:
        raise Refus(f"Comme à l'écran, seuls les contacts du négociateur du bien ({tete.get('commercial_nom') or 'son négociateur'})"
                    f" se rattachent : la fiche de {_nom_contact(fiche)} est suivie par "
                    f"{fiche.get('commercial_nom') or 'un autre négociateur'}.")
    if str(fiche["hektor_contact_id"]) in _mandants_du_bien(ctx, bien):
        raise Refus(f"{_nom_contact(fiche)} est déjà mandant (ou propriétaire) de l'annonce {bien['hektor_annonce_id']}.")
    return bien, fiche


def preparer_rattacher_mandant(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien, fiche = _controler_rattachement(ctx, p)
    return (f"Rattacher {_nom_contact(fiche)} comme MANDANT de l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} »"
            " (chez nous tout de suite, recopié chez Hektor ensuite). ⚠ Une fois le mandat numéroté, un mandant ne se retire plus.",
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "hektor_contact_id": str(fiche["hektor_contact_id"])})


def executer_rattacher_mandant(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien, fiche = _controler_rattachement(ctx, p)  # re-vérifié AU CLIC
    travail = _ecrire_traduit(ctx, "rpc/app_link_mandant_optimistic", {
        "target_app_dossier_id": bien["app_dossier_id"], "target_hektor_annonce_id": str(bien["hektor_annonce_id"]),
        "target_contact_id": str(fiche["hektor_contact_id"]), "contact_label": _nom_contact(fiche), "job_priority": 18},
        (("forbidden_link_mandant", "Tu n'as pas les droits sur ce bien chez Hektor."),)) or {}
    return {"app_dossier_id": bien["app_dossier_id"], "travail": travail.get("id"), "statut": travail.get("status")}


# — retirer un mandant (écran : bouton « Retirer » du bloc des mandants, App.tsx ~3686 ; app_unlink_mandant_optimistic) —
TRADUCTIONS_RETRAIT = (
    (r"mandat_numerote_(\S+?)\)?$", "Retrait impossible : le mandat n° {0} a été généré pour ce bien. Un mandant ne peut plus "
                                    "être retiré une fois le mandat numéroté."),
    (r"forbidden_unlink", "Retrait impossible : tu n'as pas les droits sur ce bien chez Hektor."),
    (r"lien_introuvable_ou_deja_retire", "Ce mandant est déjà retiré, ou le lien n'existe pas."),
    (r"contact_introuvable", "Ce contact n'a pas été retrouvé dans l'application."),
)


def _controler_retrait(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    if str(bien.get("numero_mandat") or "").strip():
        raise Refus(f"Retrait impossible : le mandat n° {bien['numero_mandat']} a été généré pour ce bien. Un mandant ne peut "
                    "plus être retiré une fois le mandat numéroté.")
    fiche = _contact_choisi(ctx, p.get("hektor_contact_id"))
    if str(fiche["hektor_contact_id"]) not in _mandants_du_bien(ctx, bien):
        raise Refus(f"{_nom_contact(fiche)} n'est pas mandant de l'annonce {bien['hektor_annonce_id']}.")
    if not str(fiche.get("hektor_target_id") or "").strip().isdigit():
        raise Refus(f"{_nom_contact(fiche)} n'a pas encore de numéro chez Hektor : le retrait ne peut pas lui être envoyé.")
    return bien, fiche


def preparer_retirer_mandant(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien, fiche = _controler_retrait(ctx, p)
    return (f"Retirer {_nom_contact(fiche)} des mandants de l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} »"
            " (le lien disparaît tout de suite ; Hektor est prévenu, et s'il refuse, le lien réapparaît).",
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "hektor_contact_id": str(fiche["hektor_contact_id"])})


def executer_retirer_mandant(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien, fiche = _controler_retrait(ctx, p)
    travail = _ecrire_traduit(ctx, "rpc/app_unlink_mandant_optimistic", {
        "target_app_dossier_id": bien["app_dossier_id"], "target_hektor_annonce_id": str(bien["hektor_annonce_id"]),
        # ⛔ le numéro HEKTOR : c'est lui que degroupproprio exige (la base traduit vers le nôtre pour app_relation)
        "target_contact_id": str(fiche["hektor_target_id"]).strip(), "job_priority": 18}, TRADUCTIONS_RETRAIT) or {}
    return {"app_dossier_id": bien["app_dossier_id"], "travail": travail.get("id"), "statut": travail.get("status")}


# — l'adresse d'un contact (app_edit_contact_optimistic ; la ville VÉRIFIÉE dans les communes du code postal, sinon Hektor
#   ne la garde pas : le worker la traduit en identifiants, applyContactLocalityIds, et une ville mal écrite part en
#   texte seul et se perd — leçon du 22/10) —
def _adresse_voulue(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str], list[str], bool]:
    fiche = _contact_choisi(ctx, p.get("hektor_contact_id"))
    if not str(fiche.get("nom") or "").strip():
        raise Refus("Ce contact n'a pas de nom chez nous : Hektor refuserait la modification.")
    cp, ville, verifiee = _commune(p.get("code_postal"), p.get("ville"))
    rue = str(p.get("adresse") or "").strip()
    if len(rue) > 300:
        raise Refus("L'adresse dépasse 300 caractères.")
    champs = {"postal_code": cp, "city": ville}
    if rue:
        champs["address"] = rue
    actuel = {"address": str(fiche.get("adresse") or "").strip(), "postal_code": str(fiche.get("code_postal") or "").strip(),
              "city": str(fiche.get("ville") or "").strip()}
    if all(actuel[k] == v for k, v in champs.items()):
        raise Refus("Rien ne change : c'est déjà l'adresse de la fiche.")
    avant = ", ".join(x for x in (actuel["address"], f"{actuel['postal_code']} {actuel['city']}".strip()) if x) or "vide"
    apres = ", ".join(x for x in (champs.get("address", actuel["address"]), f"{cp} {ville}") if x)
    return fiche, champs, [avant, apres], verifiee


def preparer_adresse_contact(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    fiche, champs, (avant, apres), verifiee = _adresse_voulue(ctx, p)
    return (f"Changer l'adresse de {_nom_contact(fiche)} : « {avant} » → « {apres} »"
            + ("" if verifiee else " (⚠ commune non vérifiée : service des communes injoignable)")
            + " (chez nous tout de suite, recopiée chez Hektor environ 10 minutes après)",
            {"hektor_contact_id": str(fiche["hektor_contact_id"]), "adresse": champs.get("address", ""),
             "code_postal": champs["postal_code"], "ville": champs["city"]})


def executer_adresse_contact(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    fiche, champs, _textes, _verifiee = _adresse_voulue(ctx, p)
    # le nom ACTUEL avec, comme la carte « modifier un contact » (le worker l'exige à chaque modification)
    champs = {"last_name": str(fiche["nom"]).strip(), **champs}
    r = _ecrire(ctx, "POST", "rpc/app_edit_contact_optimistic",
                {"target_contact_id": str(fiche["hektor_contact_id"]), "edit_fields": champs, "debounce_seconds": 600})
    return {"hektor_contact_id": str(fiche["hektor_contact_id"]), "champs": sorted(champs), "reponse": r}


# — rattacher un CONJOINT existant à une personne seule (écran : « Ajouter un conjoint », App.tsx ~44750 ;
#   app_ajouter_conjoint_optimistic, qui refait toutes ces gardes et refuse SANS lever : ok = false + raison) —
def _seule(fiche: dict[str, Any]) -> bool:
    couple = fiche.get("couple_json") if isinstance(fiche.get("couple_json"), dict) else {}
    paire = str(fiche.get("hektor_couple_contact_id") or "").strip()
    return (str(couple.get("etat") or "aucun") == "aucun" and paire in {"", str(fiche["hektor_contact_id"])}
            and fiche.get("nature_fiche") not in _PAS_SEULE)


def _controler_conjoint(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    cran = _lire(ctx, "app_setting", {"key": "eq.contacts_couples_ajout", "select": "value", "limit": "1"})
    valeur = str((cran or [{}])[0].get("value") or "off").strip().lower()
    if valeur not in {"on", "true", "1", "yes", "admin"} or (valeur == "admin" and ctx.role != "admin"):
        raise Refus("L'ajout d'un conjoint n'est pas encore ouvert.")
    personne = _contact_choisi(ctx, p.get("hektor_contact_id"))
    conjoint = _contact_choisi(ctx, p.get("conjoint_contact_id"))
    if personne["hektor_contact_id"] == conjoint["hektor_contact_id"]:
        raise Refus("On ne peut pas choisir la même fiche comme conjoint.")
    for fiche, qui in ((personne, "personne"), (conjoint, "conjoint")):
        if str(fiche.get("archive") or "").strip().lower() in {"1", "true"}:
            raise Refus(f"La fiche de {_nom_contact(fiche)} est archivée.")
        if fiche.get("nature_fiche") == "notaire" or "notaire_" in str(fiche.get("relation_roles_json") or ""):
            raise Refus("Une fiche notaire n'est jamais un couple.")
        if not _seule(fiche):
            raise Refus(f"{_nom_contact(fiche)} n'est pas une personne seule (déjà en couple, ou case de conjoint) : "
                        "les couples existants se travaillent sur la fiche.")
    return personne, conjoint


def preparer_ajouter_conjoint(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    personne, conjoint = _controler_conjoint(ctx, p)
    return (f"Faire de {_nom_contact(conjoint)} le CONJOINT de {_nom_contact(personne)} : les deux fiches forment un couple "
            f"chez nous tout de suite, Hektor les relie ensuite ; {_nom_contact(conjoint)} rejoint aussi les biens dont "
            f"{_nom_contact(personne)} est propriétaire (là où tu as les droits). ⚠ Le défaire se fait sur la fiche, pas ici.",
            {"hektor_contact_id": str(personne["hektor_contact_id"]), "conjoint_contact_id": str(conjoint["hektor_contact_id"])})


def executer_ajouter_conjoint(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    personne, conjoint = _controler_conjoint(ctx, p)
    r = _ecrire_traduit(ctx, "rpc/app_ajouter_conjoint_optimistic", {
        "target_contact_id": str(personne["hektor_contact_id"]), "conjoint_contact_id": str(conjoint["hektor_contact_id"])},
        ((r"forbidden_link_conjoint", "Tu n'as pas les droits sur l'une de ces deux fiches."),)) or {}
    if not r.get("ok"):
        raison = str(r.get("raison") or "")
        raise Refus(RAISONS_CONJOINT.get(raison, f"refusé ({raison or 'sans raison'})"))
    return {"hektor_contact_id": str(personne["hektor_contact_id"]), "travail": r.get("job_id"), "biens": r.get("biens")}


# — réaffecter le négociateur d'un bien [direction] (écran : handleAssignHektorNegotiator, App.tsx ~19153 ; les
#   négociateurs du menu = le REGISTRE, fiches actives chez Hektor, loadHektorNegotiatorOptions, lib/api.ts ~6625) —
def _negociateur_choisi(ctx: ContexteAssistant, nom: Any, agence: Any = "", numero: Any = "") -> dict[str, Any]:
    fiches = [f for f in _lire(ctx, "app_negociateur_fiche", {
        "sorte": "eq.fiche_negociateur", "actif_chez_hektor": "is.true", "limit": "1000",
        "select": "hektor_negociateur_id,hektor_user_id,hektor_agence_id,agence_id_user,agence_nom,nom_vu,email_vu"})
        if str(f.get("hektor_user_id") or "").strip().isdigit()]
    if str(numero or "").strip():
        trouves = [f for f in fiches if str(f.get("hektor_negociateur_id") or "") == str(numero).strip()]
        if not trouves:
            raise Refus("ce négociateur n'est plus actif chez Hektor")
        return trouves[0]
    cherche, lieu = _simple(nom), _simple(agence)
    if not cherche:
        raise Refus("Donne le nom du négociateur à qui confier le bien.")
    trouves = [f for f in fiches if cherche in _simple(f.get("nom_vu")) and (not lieu or lieu in _simple(f.get("agence_nom")))]
    if not trouves:
        raise Refus(f"Aucun négociateur ACTIF chez Hektor ne correspond à « {nom} »" + (f" à l'agence « {agence} »" if lieu else "")
                    + ".")
    if len(trouves) > 1:
        raise Refus("Plusieurs fiches correspondent : " + " ; ".join(f"{f.get('nom_vu')} ({f.get('agence_nom') or 'sans agence'})"
                                                                     for f in trouves[:10])
                    + ". Redemande avec le nom complet et l'agence.")
    return trouves[0]


def _controler_negociateur(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    nego = _negociateur_choisi(ctx, p.get("negociateur"), p.get("agence"), p.get("hektor_negociateur_id"))
    tete = _tete_bien(ctx, bien, "negociateur_email,commercial_nom")
    if str(nego.get("email_vu") or "").strip().lower() and \
            str(nego.get("email_vu") or "").strip().lower() == str(tete.get("negociateur_email") or "").strip().lower():
        raise Refus(f"L'annonce {bien['hektor_annonce_id']} est déjà confiée à {nego.get('nom_vu')}.")
    return bien, nego, tete


def preparer_reaffecter_negociateur(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien, nego, tete = _controler_negociateur(ctx, {**p, "hektor_negociateur_id": ""})
    return (f"Confier l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » à {nego.get('nom_vu')} "
            f"({nego.get('agence_nom') or 'sans agence'}) — aujourd'hui : {tete.get('commercial_nom') or 'aucun négociateur'}. "
            "Le bien change de portefeuille chez nous tout de suite (ce que chacun voit), Hektor suit ensuite.",
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "hektor_negociateur_id": str(nego["hektor_negociateur_id"])})


def executer_reaffecter_negociateur(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien, nego, _tete = _controler_negociateur(ctx, p)  # le négociateur est RELU par son numéro : toujours actif ?
    r = _ecrire(ctx, "POST", "rpc/app_assign_negotiator_optimistic", {
        "target_dossier_id": bien["app_dossier_id"], "target_user_id": str(nego["hektor_user_id"]).strip(),
        # la même charge que l'écran (createAssignHektorAnnonceNegotiatorJob, lib/api.ts ~12725)
        "job_payload": {"target_hektor_user_label": nego.get("nom_vu"), "target_hektor_user_email": nego.get("email_vu"),
                        "target_hektor_negociateur_id": nego.get("hektor_negociateur_id"),
                        "target_hektor_agence_id": nego.get("hektor_agence_id"),
                        "target_agency_id_user": nego.get("agence_id_user"), "target_agency_label": nego.get("agence_nom")},
        "job_priority": 9}) or {}
    return {"app_dossier_id": bien["app_dossier_id"], "travail": r.get("job_id")}


# — archiver [direction] / désarchiver un bien (écran : handleArchiveHektorAnnonce, App.tsx ~18714 ; désarchiver :
#   app_restore_annonce_optimistic, ouvert au négociateur sur SES biens) —
def _controler_archivage(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str], str]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    cause = str(p.get("cause") or "").strip()
    if cause not in CAUSES_ARCHIVAGE:
        raise Refus("Donne la cause de l'archivage : " + " ; ".join(f"{k} ({v[1]})" for k, v in CAUSES_ARCHIVAGE.items()) + ".")
    principal, libelle = CAUSES_ARCHIVAGE[cause]
    precision = str(p.get("precision") or "").strip()[:500]
    if cause == "autre" and not precision:
        raise Refus("Avec la cause « autre », la précision est obligatoire (elle part chez Hektor).")
    vendu = principal == "choiceVendu"
    prix = re.sub(r"\s", "", str(p.get("prix") or "")) if vendu else ""
    if prix and not prix.isdigit():
        raise Refus("Le prix de vente est un nombre entier d'euros, ou vide.")
    confrere = str(p.get("confrere") or "").strip()[:200] if vendu else ""
    tete = _tete_bien(ctx, bien, "archive")
    if str(tete.get("archive") or "").strip() == "1":
        raise Refus(f"L'annonce {bien['hektor_annonce_id']} est déjà en cours d'archivage.")
    _aucune_action_en_cours(ctx, bien["hektor_annonce_id"])
    motif = " — ".join(x for x in ("Vendu" if vendu else "Autre motif", libelle, precision,
                                    f"prix {_euros(prix)}" if prix else "", f"confrère {confrere}" if confrere else "") if x)
    return bien, {"archive_main_choice": principal, "archive_sub_choice": cause, "archive_other_text": precision or None,
                  "archive_price": prix or None, "archive_confrere": confrere or None}, motif


def preparer_archiver_annonce(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien, charge, motif = _controler_archivage(ctx, p)
    return (f"ARCHIVER l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » — motif : {motif}. Hektor "
            "archive le bien et COUPE SA DIFFUSION ; il sort des biens vivants (il se désarchive ensuite).",
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "cause": charge["archive_sub_choice"],
             "precision": charge["archive_other_text"] or "", "prix": charge["archive_price"] or "",
             "confrere": charge["archive_confrere"] or ""})


def executer_archiver_annonce(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien, charge, _motif = _controler_archivage(ctx, p)
    r = _ecrire_traduit(ctx, "rpc/app_archive_annonce_optimistic",
                        {"target_dossier_id": bien["app_dossier_id"], "job_payload": charge, "job_priority": 8},
                        (("forbidden_archive", "Archiver un bien est réservé à la direction."),
                         ("annonce_deja_archivee", "Cette annonce est déjà archivée."))) or {}
    return {"app_dossier_id": bien["app_dossier_id"], "travail": r.get("job_id")}


def _archive(ctx: ContexteAssistant, hektor_annonce_id: Any) -> dict[str, Any]:
    numero = str(hektor_annonce_id or "").strip()
    if not numero.isdigit():
        raise Refus("Donne le numéro d'annonce du bien (ex. 63289).")
    lignes = _lire(ctx, "app_archive_annonce_index_current", {"hektor_annonce_id": f"eq.{numero}", "limit": "1",
                                                               "select": "app_archive_id,hektor_annonce_id,titre_bien"})
    if not lignes:
        if _lire(ctx, "app_dossiers_current", {"hektor_annonce_id": f"eq.{numero}", "select": "app_dossier_id", "limit": "1"}):
            raise Refus(f"L'annonce {numero} n'est pas archivée.")
        raise Refus(f"L'annonce {numero} n'est pas parmi les biens archivés que tu peux voir.")
    _aucune_action_en_cours(ctx, numero)
    return lignes[0]


def preparer_desarchiver_annonce(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    archive = _archive(ctx, p.get("hektor_annonce_id"))
    return (f"DÉSARCHIVER l'annonce {archive['hektor_annonce_id']} « {archive.get('titre_bien') or ''} » : Hektor la remet "
            "en vie, et elle revient parmi les biens vivants à la relecture (quelques minutes).",
            {"hektor_annonce_id": int(archive["hektor_annonce_id"])})


def executer_desarchiver_annonce(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    archive = _archive(ctx, p.get("hektor_annonce_id"))
    r = _ecrire_traduit(ctx, "rpc/app_restore_annonce_optimistic",
                        {"target_dossier_id": archive["app_archive_id"], "job_payload": {}, "job_priority": 8},
                        (("forbidden_restore", "Tu n'as pas les droits sur ce bien chez Hektor."),)) or {}
    return {"app_dossier_id": archive["app_archive_id"], "travail": r.get("job_id")}


# — passer une ESTIMATION en ACTIF [direction] (la modale « Faire évoluer le statut », cible 'active' ; App.tsx ~20191).
#   ⚠ Hektor remet « diffusable » à 1 (mémoire « Le geste Actif remet diffusable à 1 ») : la carte le DIT.
#   Seul ce passage est ouvert : il n'existe AUCUNE cible « Estimation » (ni ici ni à l'écran), Clos relève des « deux
#   portes », offre / compromis / vente passent par la fenêtre de l'écran. —
def _controler_activation(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    bien = _bien_vivant(ctx, p.get("hektor_annonce_id"))
    tete = _exiger_negociateur(ctx, bien)
    if "estimation" not in str(tete.get("statut_annonce") or "").lower():
        raise Refus(f"L'annonce {bien['hektor_annonce_id']} est « {tete.get('statut_annonce') or 'sans statut'} » : seul le passage "
                    "Estimation → Actif se fait ici (offre, compromis, vente : la fenêtre de statut de l'écran).")
    _aucune_action_en_cours(ctx, bien["hektor_annonce_id"])
    return bien, tete


def preparer_activer_estimation(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    bien, _tete = _controler_activation(ctx, p)
    return (f"Passer l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » d'ESTIMATION à ACTIF. ⚠ Hektor la "
            "rend DIFFUSABLE en même temps (elle peut partir sur les portails). Le retour en Estimation n'existe pas, ni ici ni "
            "à l'écran.", {"hektor_annonce_id": int(bien["hektor_annonce_id"])})


def executer_activer_estimation(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    bien, tete = _controler_activation(ctx, p)
    # la charge de l'écran (createChangeHektorAnnonceStatusJob, lib/api.ts ~12590) pour la cible « Actif » : le dossier,
    # la date du jour (la modale la pose à l'ouverture), tout le reste vide
    charge: dict[str, Any] = {cle: tete.get(cle) for cle in ("numero_dossier", "numero_mandat", "offre_id", "offre_state",
                                                             "compromis_id", "compromis_state", "vente_id", "titre_bien",
                                                             "negociateur_email")}
    charge.update({"target_status": "active", "transaction_date": datetime.now(PARIS).date().isoformat(),
                   "apres_vente": "actif"})
    for cle in ("amount", "sale_price", "signature_date", "validity_days", "retraction_days", "selected_mandat",
                "buyer_contact_id", "buyer_contact_ids", "buyer_notary_id", "acquereurs_affirmes", "mandant_contact_ids",
                "seller_notary_id", "buyer_notary_nom", "seller_notary_nom", "notaires_affirmes", "buyer_fees",
                "buyer_fees_rate", "seller_fees", "net_seller_price", "sequestration", "close_reason", "close_state",
                "close_etat", "close_raison", "close_date", "close_mandat_on_sale", "close_price", "reprendre_transaction",
                "champs_touches"):
        charge[cle] = None
    r = _ecrire_traduit(ctx, "rpc/app_change_annonce_status_optimistic",
                        {"target_dossier_id": bien["app_dossier_id"], "target_status": "active", "job_payload": charge,
                         "job_priority": 7},
                        (("forbidden_change_status", "Changer le statut d'un bien est réservé à la direction."),)) or {}
    return {"app_dossier_id": bien["app_dossier_id"], "travail": r.get("job_id")}


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
          "l'écran ; une seule demande en cours par type. C'est le chemin du NÉGOCIATEUR : la direction ne s'adresse pas "
          "une demande, elle fait le geste (le prix : changer_prix).",
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
    # lot 2a
    Geste("bien_propose",
          "Prépare l'enregistrement d'un bien PROPOSÉ PAR TÉLÉPHONE à un acquéreur (une recherche) : le bien passe « proposé » "
          "et une relance de suivi est posée. (L'e-mail et la visite ne sont pas encore ouverts.)",
          TOUS_LES_ROLES,
          _schema({"contact_search_key": {"type": "string", "description": "clé de la recherche (recherches, rapprochements)"},
                   "hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   "note": {"type": "string", "description": "ce qui a été dit, ou vide"}}),
          preparer_proposition, executer_proposition),
    Geste("statut_bien",
          "Prépare : ÉCARTER un bien pour la recherche d'un acquéreur (avec un motif), ou le RÉTABLIR.",
          TOUS_LES_ROLES,
          _schema({"contact_search_key": {"type": "string", "description": "clé de la recherche"},
                   "hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   "statut": {"type": "string", "enum": ["ecarte", "retabli"]},
                   "motif": {"type": "string", "description": "pourquoi il est écarté, ou vide"}}),
          preparer_statut_bien, executer_statut_bien),
    Geste("notifications_lues",
          "Prépare : marquer comme lues des notifications DE LA PERSONNE (des numéros, ou toutes celles d'un type, ou toutes).",
          TOUS_LES_ROLES,
          _schema({"notification_ids": {"type": "string", "description": "numéros séparés par |, ou vide"},
                   "type": {"type": "string", "description": "un type de notification, ou vide"}}),
          preparer_notifications, executer_notifications),
    Geste("note_transaction",
          "Prépare la NOTE d'une transaction (direction seulement, comme l'écran). ⚠ Elle REMPLACE la note existante.",
          DIRECTION,
          _schema({"app_affaire_id": {"type": "integer", "description": "identifiant de la transaction (transactions)"},
                   "texte": {"type": "string", "description": "le texte complet de la note"}}),
          preparer_note, executer_note),
    # vague C (direction)
    Geste("transaction",
          "Prépare un geste de la DIRECTION sur une transaction : accepter ou refuser une OFFRE, annuler un COMPROMIS. Les "
          "règles de l'écran s'appliquent (offre verrouillée par son compromis, compromis verrouillé par sa vente). Pas de "
          "suppression : elle se fait à l'écran.",
          DIRECTION,
          _schema({"app_affaire_id": {"type": "integer", "description": "identifiant de la transaction (transactions)"},
                   "geste": {"type": "string", "enum": list(GESTES_TRANSACTION)}}),
          preparer_transaction, executer_transaction),
    # lot 2b
    Geste("modifier_contact",
          "Prépare la modification d'un contact : téléphone, e-mail, commentaire (vide = inchangé). Pas l'adresse.",
          TOUS_LES_ROLES,
          _schema({"hektor_contact_id": {"type": "string", "description": "numéro du contact"},
                   "telephone": {"type": "string", "description": "nouveau téléphone, ou vide"},
                   "email": {"type": "string", "description": "nouvel e-mail, ou vide"},
                   "commentaire": {"type": "string", "description": "nouveau commentaire COMPLET, ou vide"}}),
          preparer_modif_contact, executer_modif_contact),
    Geste("archiver_contact",
          "Prépare l'ARCHIVAGE d'un contact (archiver = true) ou sa RÉACTIVATION (archiver = false).",
          TOUS_LES_ROLES,
          _schema({"hektor_contact_id": {"type": "string", "description": "numéro du contact"},
                   "archiver": {"type": "boolean"}}),
          preparer_archivage_contact, executer_archivage_contact),
    Geste("archiver_recherche",
          "Prépare l'ARCHIVAGE d'une recherche d'acquéreur (ce que l'écran appelle « supprimer »).",
          TOUS_LES_ROLES,
          _schema({"contact_search_key": {"type": "string", "description": "clé de la recherche"}}),
          preparer_archivage_recherche, executer_archivage_recherche),
    # lot 3a
    Geste("creer_rdv",
          "Prépare un RENDEZ-VOUS dans l'agenda Google DE LA PERSONNE (jamais celui d'un collègue), SANS invité ni "
          "invitation, relié si possible à un bien, un contact, une recherche. Une visite liée à une recherche met le bien "
          "« visite » (comme l'écran).",
          TOUS_LES_ROLES,
          _schema({"type": {"type": "string", "enum": list(TYPES_RDV)},
                   "titre": {"type": "string", "description": "ex. « Visite T3 Firminy — M. DURAND »"},
                   "debut": {"type": "string", "description": "AAAA-MM-JJTHH:MM, heure de Paris"},
                   "duree_minutes": {"type": "integer", "description": "entre 5 et 600"},
                   "lieu": {"type": "string", "description": "adresse, ou vide"},
                   "hektor_annonce_id": {"type": "string", "description": "numéro d'annonce lié, ou vide"},
                   "hektor_contact_id": {"type": "string", "description": "numéro du contact lié, ou vide"},
                   "contact_search_key": {"type": "string", "description": "clé de la recherche (visite), ou vide"},
                   "note": {"type": "string", "description": "description du rendez-vous, ou vide"}}),
          preparer_rdv, executer_rdv),
    Geste("deplacer_rdv",
          "Prépare la modification d'un rendez-vous POSÉ PAR L'APPLICATION dans l'agenda de la personne (rdv_app rendu par "
          "lire_mon_agenda) et SANS invité : nouvel horaire, durée, titre ou lieu (vide / 0 = inchangé).",
          TOUS_LES_ROLES,
          _schema({"rdv_id": {"type": "string", "description": "rdv_app"},
                   "debut": {"type": "string", "description": "AAAA-MM-JJTHH:MM, ou vide"},
                   "duree_minutes": {"type": "integer", "description": "0 = durée inchangée"},
                   "titre": {"type": "string", "description": "nouveau titre, ou vide"},
                   "lieu": {"type": "string", "description": "nouveau lieu, ou vide"}}),
          preparer_deplacer_rdv, executer_deplacer_rdv),
    Geste("supprimer_rdv",
          "Prépare la suppression d'un rendez-vous POSÉ PAR L'APPLICATION dans l'agenda de la personne, SANS invité.",
          TOUS_LES_ROLES,
          _schema({"rdv_id": {"type": "string", "description": "rdv_app"}}),
          preparer_supprimer_rdv, executer_supprimer_rdv),
    # lot 3b
    Geste("email_interne",
          "Prépare un E-MAIL INTERNE envoyé depuis la boîte de la personne, SEULEMENT à des adresses @gti-immobilier.fr "
          "(collègues), sans pièce jointe. Jamais à un client.",
          TOUS_LES_ROLES,
          _schema({"destinataires": {"type": "string", "description": "adresses @gti-immobilier.fr séparées par | ; "
                                                                      "« moi » = la personne elle-même"},
                   "objet": {"type": "string"},
                   "texte": {"type": "string", "description": "le texte COMPLET (3000 caractères au plus)"}}),
          preparer_email_interne, executer_email_interne),
    # lot 3c : vers le client
    Geste("email_client",
          "Prépare un E-MAIL À UN CLIENT (un contact de la base), envoyé depuis la boîte de la personne, à l'adresse de sa "
          "fiche (jamais une autre), sans pièce jointe. Refusé si le contact s'est désinscrit. Il part VRAIMENT.",
          TOUS_LES_ROLES,
          _schema({"hektor_contact_id": {"type": "string", "description": "numéro du contact"},
                   "objet": {"type": "string"},
                   "texte": {"type": "string", "description": "le texte COMPLET (3000 caractères au plus)"}}),
          preparer_email_client, executer_email_client),
    Geste("envoyer_rapprochement",
          "Prépare l'ENVOI RÉEL à un acquéreur de l'e-mail de rapprochement (le même que l'écran) avec des biens : seuls "
          "ceux jamais proposés partent, depuis la boîte du négociateur de chaque bien ; ils passent ensuite « proposé ». "
          "Montre d'abord l'aperçu (apercu_rapprochement).",
          TOUS_LES_ROLES,
          _schema({"contact_search_key": {"type": "string", "description": "clé de la recherche de l'acquéreur"},
                   "annonces": {"type": "string", "description": "numéros d'annonce séparés par | (10 au plus)"},
                   "mot": {"type": "string", "description": "mot personnel en tête, ou vide"}}),
          preparer_envoyer_rapprochement, executer_envoyer_rapprochement),
    Geste("rdv_client",
          "Prépare un RENDEZ-VOUS dans l'agenda de la personne AVEC LE CLIENT INVITÉ : une vraie invitation Google part à "
          "l'adresse de sa fiche. Une visite liée à une recherche met le bien « visite » (comme l'écran).",
          TOUS_LES_ROLES,
          _schema({"type": {"type": "string", "enum": list(TYPES_RDV)},
                   "titre": {"type": "string", "description": "ex. « Visite T3 Firminy — M. DURAND »"},
                   "debut": {"type": "string", "description": "AAAA-MM-JJTHH:MM, heure de Paris"},
                   "duree_minutes": {"type": "integer", "description": "entre 5 et 600"},
                   "lieu": {"type": "string", "description": "adresse, ou vide"},
                   "hektor_annonce_id": {"type": "string", "description": "numéro d'annonce lié, ou vide"},
                   "hektor_contact_id": {"type": "string", "description": "numéro du contact INVITÉ"},
                   "contact_search_key": {"type": "string", "description": "clé de sa recherche (visite), ou vide"},
                   "note": {"type": "string", "description": "description, visible du client, ou vide"}}),
          preparer_rdv_client, executer_rdv_client),
    # lot 4a
    Geste("modifier_bien",
          "Prépare la modification de champs d'une annonce VIVANTE (vide = inchangé) : titre, texte, surfaces, pièces, "
          "chambres, niveaux, salles d'eau, WC, garages, parkings, terrasses, année, DPE / GES, copropriété. Pas le prix "
          "(direction : changer_prix ; négociateur : demande_direction baisse_prix), ni l'adresse, ni les honoraires, "
          "ni le mandat. Écrit chez nous tout de suite, "
          "chez Hektor 10 minutes après.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   **{cle: {"type": "string", "description": f"{libelle} ; vide = inchangé"}
                      for cle, (libelle, _genre) in CHAMPS_BIEN.items()}}),
          preparer_modifier_bien, executer_modifier_bien),
    # étape 4 (16/11) : le numéro de mandat, réservation OFFICIELLE et irréversible chez Hektor
    # 17/11 (§38) : le prix, la DIRECTION seulement (le négociateur : demande de baisse)
    Geste("changer_prix",
          "Prépare le CHANGEMENT DU PRIX d'une annonce vivante (hausse ou baisse), par la direction elle-même. Écrit chez nous "
          "tout de suite, chez Hektor 10 minutes après. Ne traite pas une demande de baisse en cours (elle s'accepte ensuite "
          "dans Suivi). Réservé à la direction.",
          DIRECTION,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "prix": {"type": "string", "description": "nouveau prix en euros (ex. 185000)"}}),
          preparer_changer_prix, executer_changer_prix),
    Geste("numero_mandat",
          "Prépare la GÉNÉRATION DU NUMÉRO DE MANDAT officiel d'une annonce vivante qui n'en a pas encore, avec au moins un "
          "mandant et un négociateur (mêmes conditions que l'écran). Mandat de vente seulement. IRRÉVERSIBLE : Hektor réserve "
          "le prochain numéro. N'édite PAS le document de mandat et n'envoie rien en signature.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "sous_type": {"type": "string", "description": "sous-type de mandat de vente (vide = « Mandat de vente »)"},
                   "date_debut": {"type": "string", "description": "AAAA-MM-JJ, vide = aujourd'hui"},
                   "duree_mois": {"type": "string", "description": "1 à 120, vide = 12"},
                   "tacite_reconduction": {"type": "string", "description": "oui ou non, vide = oui"}}),
          preparer_numero_mandat, executer_numero_mandat),
    # étape 4 (16/11) : la signature Youtrust en cours (l'ENVOI passe par la fenêtre de l'écran)
    Geste("relance_signature",
          "Prépare la RELANCE d'un signataire d'une signature Youtrust EN COURS sur un bien : Youtrust lui renvoie le lien "
          "(un e-mail part). Seulement un signataire invité qui n'a pas encore signé. Si l'interrupteur Youtrust le permet.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "document": {"type": "string", "description": "un morceau du nom du document, vide = le seul en cours"},
                   "signataire": {"type": "string", "description": "un morceau de son nom, vide = le seul à relancer"}}),
          preparer_relance_signature, executer_relance_signature),
    Geste("annulation_signature",
          "Prépare l'ANNULATION d'une signature Youtrust EN COURS sur un bien : les signataires ne pourront plus signer ce "
          "lien, le document redevient « à signer ». Si l'interrupteur Youtrust le permet.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "document": {"type": "string", "description": "un morceau du nom du document, vide = le seul en cours"}}),
          preparer_annulation_signature, executer_annulation_signature),
    # étape 4 (16/11, audit §35) : les cartes directes — mandants, contacts, annonce
    Geste("rattacher_mandant",
          "Prépare le RATTACHEMENT d'un contact EXISTANT comme mandant d'une annonce vivante (un contact actif du "
          "négociateur du bien, comme le sélecteur de l'écran). Créer un NOUVEAU mandant n'est pas offert ici.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "hektor_contact_id": {"type": "string", "description": "numéro du contact (objet contacts)"}}),
          preparer_rattacher_mandant, executer_rattacher_mandant),
    Geste("retirer_mandant",
          "Prépare le RETRAIT d'un mandant d'une annonce vivante. Impossible si le numéro de mandat a été généré.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "hektor_contact_id": {"type": "string", "description": "numéro du contact (objet contacts)"}}),
          preparer_retirer_mandant, executer_retirer_mandant),
    Geste("adresse_contact",
          "Prépare le changement d'ADRESSE d'un contact existant : code postal ET ville obligatoires (la ville est vérifiée "
          "dans les communes du code postal), rue facultative (vide = rue inchangée).",
          TOUS_LES_ROLES,
          _schema({"hektor_contact_id": {"type": "string", "description": "numéro du contact"},
                   "adresse": {"type": "string", "description": "rue, ou vide"},
                   "code_postal": {"type": "string", "description": "5 chiffres"},
                   "ville": {"type": "string", "description": "commune de ce code postal"}}),
          preparer_adresse_contact, executer_adresse_contact),
    Geste("ajouter_conjoint",
          "Prépare : faire d'une fiche EXISTANTE le conjoint d'une personne seule (deux personnes seules, non archivées). "
          "Créer le conjoint, modifier ou défaire un couple ne se fait pas ici.",
          TOUS_LES_ROLES,
          _schema({"hektor_contact_id": {"type": "string", "description": "numéro de la personne"},
                   "conjoint_contact_id": {"type": "string", "description": "numéro de la fiche du conjoint"}}),
          preparer_ajouter_conjoint, executer_ajouter_conjoint),
    Geste("reaffecter_negociateur",
          "Prépare la RÉAFFECTATION d'une annonce vivante à un autre négociateur (actif chez Hektor) : le bien change de "
          "portefeuille. Réservé à la direction.",
          DIRECTION,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "negociateur": {"type": "string", "description": "nom (ou morceau du nom) du négociateur"},
                   "agence": {"type": "string", "description": "son agence s'il a plusieurs fiches, sinon vide"}}),
          preparer_reaffecter_negociateur, executer_reaffecter_negociateur),
    Geste("archiver_annonce",
          "Prépare l'ARCHIVAGE d'une annonce vivante, avec sa cause (comme la modale de l'écran) : Hektor coupe sa diffusion. "
          "Réservé à la direction.",
          DIRECTION,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "cause": {"type": "string", "enum": list(CAUSES_ARCHIVAGE)},
                   "precision": {"type": "string", "description": "obligatoire si cause = autre, sinon vide"},
                   "prix": {"type": "string", "description": "vendu seulement : prix en euros si connu, sinon vide"},
                   "confrere": {"type": "string", "description": "vendu par un confrère : son nom si connu, sinon vide"}}),
          preparer_archiver_annonce, executer_archiver_annonce),
    Geste("desarchiver_annonce",
          "Prépare le DÉSARCHIVAGE d'une annonce archivée : elle revient parmi les biens vivants.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"}}),
          preparer_desarchiver_annonce, executer_desarchiver_annonce),
    Geste("activer_estimation",
          "Prépare le passage d'une annonce en ESTIMATION au statut ACTIF (Hektor la rend diffusable en même temps). Seul ce "
          "changement de statut est offert ici. Réservé à la direction.",
          DIRECTION,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"}}),
          preparer_activer_estimation, executer_activer_estimation),
    Geste("couverture_photo",
          "Prépare : mettre une photo VISIBLE en couverture d'une annonce (numéros donnés par lire_photos_bien).",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   "photo": {"type": "string", "description": "numéro de la photo"}}),
          preparer_couverture, executer_couverture),
    Geste("visibilite_photo",
          "Prépare : MASQUER (visible = false) ou AFFICHER (visible = true) une photo d'une annonce. Jamais la dernière "
          "photo visible. (Supprimer une photo n'est pas offert.)",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   "photo": {"type": "string", "description": "numéro de la photo"},
                   "visible": {"type": "boolean"}}),
          preparer_visibilite_photo, executer_visibilite_photo),
    Geste("deplacer_photo",
          "Prépare : placer une photo VISIBLE à un rang (1 = couverture) ; les autres glissent d'un cran.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   "photo": {"type": "string", "description": "numéro de la photo"},
                   "rang": {"type": "integer", "description": "nouvelle place, à partir de 1"}}),
          preparer_deplacer_photo, executer_deplacer_photo),
    # lot 4b
    Geste("portail",
          "Prépare la DIFFUSION d'une annonce DÉJÀ DIFFUSABLE : la PUBLIER et / ou la RETIRER sur un ou plusieurs portails "
          "(Leboncoin, Bien'ici, Paper, Etreproprio, Superimmo) en une fois ; les portails non nommés ne bougent pas. Un "
          "bien pas encore diffusable : la direction le rend diffusable par le Pilotage, le négociateur fait une demande "
          "de validation.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   "publier": {"type": "string", "description": "portails à publier séparés par |, ou vide"},
                   "retirer": {"type": "string", "description": "portails à retirer séparés par |, ou vide"}}),
          preparer_portail, executer_portail),
    # 17/11 (§41-42) : le Pilotage de la fiche, la DIRECTION seulement (le négociateur : demande de validation)
    Geste("pilotage",
          "Prépare le PILOTAGE d'une annonce vivante : cocher ou décocher Validation et / ou Diffusable chez Hektor (oui, non, "
          "ou vide pour ne pas y toucher). Écrit DIRECTEMENT chez Hektor au clic, puis relu. Réservé à la direction.",
          DIRECTION,
          _schema({"hektor_annonce_id": {"type": "string", "description": "numéro d'annonce"},
                   "validation": {"type": "string", "description": "oui, non, ou vide (inchangé)"},
                   "diffusable": {"type": "string", "description": "oui, non, ou vide (inchangé)"}}),
          preparer_pilotage, executer_pilotage),
    # lot 2c
    Geste("creer_contact",
          "Prépare la CRÉATION d'un contact (personne seule ou couple), acquéreur ou propriétaire, au nom de la personne qui "
          "parle ; avec, pour un acquéreur, sa première recherche si avec_recherche. Pas de société ni de partenaire. Les "
          "doublons (même téléphone ou e-mail) sont cherchés avant : s'il y en a, montre-les et ne redemande avec "
          "doublon_accepte = true que si la personne confirme que c'est quelqu'un d'autre.",
          TOUS_LES_ROLES,
          _schema({"genre": {"type": "string", "enum": list(GENRES_CONTACT)},
                   "civilite": {"type": "string", "enum": ["", "M.", "Mme"]},
                   "nom": {"type": "string"}, "prenom": {"type": "string", "description": "ou vide"},
                   "telephone": {"type": "string", "description": "ou vide (téléphone OU e-mail obligatoire)"},
                   "email": {"type": "string", "description": "ou vide"},
                   "conjoint_nom": {"type": "string", "description": "couple seulement, sinon vide"},
                   "conjoint_prenom": {"type": "string", "description": "couple seulement, sinon vide"},
                   "adresse": {"type": "string", "description": "rue, ou vide"},
                   "code_postal": {"type": "string", "description": "5 chiffres, ou vide"},
                   "ville": {"type": "string", "description": "commune de ce code postal, ou vide"},
                   "commentaire": {"type": "string", "description": "ou vide"},
                   "email_rgpd": {"type": "boolean",
                                  "description": "true = Hektor envoie au contact l'e-mail de consentement RGPD (choix par "
                                                 "défaut de l'écran) ; demande-le à la personne si elle ne l'a pas dit"},
                   "doublon_accepte": {"type": "boolean", "description": "false, sauf confirmation de la personne"},
                   "avec_recherche": {"type": "boolean", "description": "acquéreur : poser aussi sa recherche"},
                   "offre": {"type": "string", "description": "recherche : achat (défaut) ou location ; sinon vide"},
                   "types": {"type": "string", "description": "recherche : types séparés par | (Maison|Appartement)"},
                   "communes": {"type": "string", "description": "recherche : « code postal ville » séparés par |"},
                   "budget_min": {"type": "string", "description": "recherche : euros, ou vide"},
                   "budget_max": {"type": "string", "description": "recherche : euros (obligatoire si recherche)"},
                   "surface_min": {"type": "string", "description": "m², ou vide"},
                   "terrain_min": {"type": "string", "description": "m², ou vide"},
                   "pieces_min": {"type": "string", "description": "ou vide"},
                   "chambres_min": {"type": "string", "description": "ou vide"}}),
          preparer_creer_contact, executer_creer_contact),
    Geste("ajouter_recherche",
          "Prépare l'AJOUT d'une recherche d'acquéreur à un contact existant : au moins un type, une commune, un budget "
          "maximum (comme l'écran). Elle n'entre dans les rapprochements qu'après la nuit.",
          TOUS_LES_ROLES,
          _schema({"hektor_contact_id": {"type": "string", "description": "numéro du contact"},
                   "offre": {"type": "string", "description": "achat (défaut) ou location"},
                   "types": {"type": "string", "description": "types séparés par | (Maison|Appartement)"},
                   "communes": {"type": "string", "description": "« code postal ville » séparés par | (42700 Firminy)"},
                   "budget_min": {"type": "string", "description": "euros, ou vide"},
                   "budget_max": {"type": "string", "description": "euros"},
                   "surface_min": {"type": "string", "description": "m², ou vide"},
                   "terrain_min": {"type": "string", "description": "m², ou vide"},
                   "pieces_min": {"type": "string", "description": "ou vide"},
                   "chambres_min": {"type": "string", "description": "ou vide"}}),
          preparer_ajouter_recherche, executer_ajouter_recherche),
    Geste("modifier_recherche",
          "Prépare la MODIFICATION d'une recherche active : seuls les critères donnés changent (vide = inchangé). Communes "
          "et types : la liste COMPLÈTE voulue. Écrit tout de suite, rapprochements recalculés.",
          TOUS_LES_ROLES,
          _schema({"contact_search_key": {"type": "string", "description": "clé de la recherche"},
                   "types": {"type": "string", "description": "liste complète séparée par |, ou vide"},
                   "communes": {"type": "string", "description": "liste complète « code postal ville » séparée par |, ou vide"},
                   "budget_min": {"type": "string", "description": "euros, ou vide"},
                   "budget_max": {"type": "string", "description": "euros, ou vide"},
                   "surface_min": {"type": "string", "description": "m², ou vide"},
                   "terrain_min": {"type": "string", "description": "m², ou vide"},
                   "pieces_min": {"type": "string", "description": "ou vide"},
                   "chambres_min": {"type": "string", "description": "ou vide"},
                   "rayon_km": {"type": "string", "description": "0 à 40, ou vide"}}),
          preparer_modifier_recherche, executer_modifier_recherche),
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
    carte = {"id": ligne["id"], "geste": geste.nom, "resume": resume, "expire_le": ligne.get("expire_le"),
             "cibles": cibles_carte(parametres, geste.nom)}
    ctx.cartes.append(carte)
    return carte


# Étape 4, lot 3 (16/11/2026) : sur quoi porte la carte, pour le lien « Ouvrir la fiche » de l'écran. Lu dans les
# paramètres que le SERVEUR a préparés (jamais dans le texte du modèle), et rien d'autre ne sort (ni le texte d'un e-mail,
# ni des critères). Le contact d'abord (une relance, un rendez-vous client portent sur la personne), puis le bien : par
# son numéro d'annonce s'il en a un, sinon par son app_dossier_id.
# Lot 3b : + la transaction (app_affaire_id), la recherche (sa clé, quand le contact n'est pas déjà là), le rendez-vous
# (le JOUR de son début, pour l'agenda) et la demande à la direction (par le numéro d'annonce du bien).
def cibles_carte(parametres: dict[str, Any] | None, geste: str | None = None) -> list[dict[str, str]]:
    p = parametres or {}
    cibles: list[dict[str, str]] = []
    contact = str(p.get("hektor_contact_id") or "").strip()
    if contact:
        cibles.append({"type": "contact", "id": contact})
    cle = str(p.get("contact_search_key") or "").strip()
    if cle and not contact:
        cibles.append({"type": "recherche", "cle": cle})
    annonce = str(p.get("hektor_annonce_id") or "").strip()
    if annonce and annonce != "0":
        cibles.append({"type": "annonce", "numero": annonce})
    elif str(p.get("app_dossier_id") or "").strip():
        cibles.append({"type": "bien", "id": str(p["app_dossier_id"]).strip()})
    if geste == "demande_direction" and annonce and annonce != "0":
        cibles.append({"type": "demande", "numero": annonce})
    affaire = str(p.get("app_affaire_id") or "").strip()
    if affaire:
        cibles.append({"type": "transaction", "id": affaire})
    jour = re.match(r"\d{4}-\d{2}-\d{2}", str(p.get("debut") or ""))
    if jour:
        cibles.append({"type": "rdv", "date": jour.group(0)})
    return cibles


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


# ── lot 3 : les LECTURES (pas de carte : rien n'est écrit) ─────────────────────
FONCTIONS_LECTURE_LOT3: tuple[Fonction, ...] = (
    Fonction("lire_mon_agenda",
             "Lit les rendez-vous de l'agenda Google DE LA PERSONNE entre deux dates (31 jours au plus) : heure, titre, lieu, "
             "nombre d'invités, et rdv_app pour ceux posés par l'application.",
             TOUS_LES_ROLES,
             _schema({"debut": {"type": "string", "description": "AAAA-MM-JJ ou AAAA-MM-JJTHH:MM ; vide = aujourd'hui"},
                      "fin": {"type": "string", "description": "AAAA-MM-JJ (jour compris) ; vide = 24 h après le début"}}),
             lire_mon_agenda),
    Fonction("apercu_rapprochement",
             "Montre le texte de l'e-mail de rapprochement qui partirait à un acquéreur pour des biens : un APERÇU, rien "
             "n'est envoyé.",
             TOUS_LES_ROLES,
             _schema({"contact_search_key": {"type": "string", "description": "clé de la recherche de l'acquéreur"},
                      "annonces": {"type": "string", "description": "numéros d'annonce séparés par |"},
                      "mot": {"type": "string", "description": "mot personnel du négociateur en intro, ou vide"}}),
             apercu_rapprochement),
)


# ── lot 4 : les LECTURES (pas de carte : rien n'est écrit chez Hektor) ──────────
FONCTIONS_LECTURE_LOT4: tuple[Fonction, ...] = (
    Fonction("lire_photos_bien",
             "Liste les photos d'une annonce vivante : numéro, rang, visible ou masquée, couverture, légende.",
             TOUS_LES_ROLES,
             _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"}}),
             lire_photos_bien),
    Fonction("lire_portails_bien",
             "Dit si une annonce vivante est diffusable, et sur quels portails elle est en ligne.",
             TOUS_LES_ROLES,
             _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"}}),
             lire_portails_bien),
    Fonction("rediger_annonce",
             "Le rédacteur de l'agence PROPOSE un titre et un texte d'annonce à partir des données du bien. Rien n'est "
             "écrit : pour les reporter, préparer ensuite proposer_modifier_bien.",
             TOUS_LES_ROLES,
             _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                      "consigne": {"type": "string", "description": "ce que la personne veut mettre en avant, ou vide"}}),
             rediger_annonce),
)
