from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

import requests
from fastapi import HTTPException

from ..auth import AuthenticatedUser
from .assistant_contexte import TOUS_LES_ROLES, ContexteAssistant, Fonction, LectureRefusee, Refus
from .google_calendar_event_link_service import GoogleCalendarEventLinkService
from .google_workspace_service import GoogleWorkspaceService
from .rapprochement_email import RapprochementEmailService
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
    email = _mon_agenda(ctx)  # re-vérifié AU CLIC
    genre = str(p.get("type") or "")
    if genre not in TYPES_RDV:
        raise Refus("type de rendez-vous inconnu")
    debut, fin = datetime.fromisoformat(p["debut"]), datetime.fromisoformat(p["fin"])
    if debut < datetime.now(timezone.utc):
        raise Refus("ce créneau est passé entre-temps")
    bien, contact, recherche = _liens_rdv(ctx, p)
    r = _google(lambda: GoogleWorkspaceService(ctx.settings).create_calendar_event(
        subject_email=email, summary=p["titre"], start_at=debut.isoformat(), end_at=fin.isoformat(),
        description=p.get("note") or None, location=p.get("lieu") or None, attendees=[], send_updates="none",
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
            ends_at=str((evenement.get("end") or {}).get("dateTime") or fin.isoformat()), attendees=[],
            metadata_json={"source": "assistant", "send_updates": "none", "has_description": bool(p.get("note")),
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
            "debut": _quand(debut), "statut_visite": statut_visite}


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
            "a_dire": "C'est un APERÇU : rien n'est envoyé ni enregistré. L'envoi au client ne se fait pas par "
                      "l'assistant ; il se fait depuis l'écran du rapprochement."}


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
                    "(proposer_activer_brouillon).")


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


# Activer un brouillon = handleExitDraftAnnonce (App.tsx:17147) -> createExitHektorDraftAnnonceJob (api.ts:10688).
# Le statut ne bouge pas, « diffusable » non plus ; la base juge (admin, manager, ou le négociateur sur SES biens).
def _brouillon(ctx: ContexteAssistant, hektor_annonce_id: Any) -> dict[str, Any]:
    numero = str(hektor_annonce_id or "").strip()
    if not numero.isdigit():
        raise Refus("Donne le numéro d'annonce du brouillon.")
    lignes = _lire(ctx, "app_brouillon_annonce_index_current", {
        "hektor_annonce_id": f"eq.{numero}", "limit": "1",
        "select": "hektor_annonce_id,app_brouillon_id,numero_dossier,titre_bien,statut_annonce"})
    if not lignes:
        raise Refus(f"L'annonce {numero} n'est pas parmi les brouillons que tu peux voir.")
    return lignes[0]


def preparer_activer_brouillon(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    b = _brouillon(ctx, p.get("hektor_annonce_id"))
    statut = str(b.get("statut_annonce") or "").strip()
    if not statut:
        raise Refus("Ce brouillon n'a aucun statut : il n'y a rien à activer. Il faut terminer la saisie dans Hektor.")
    return (f"ACTIVER le brouillon {b['hektor_annonce_id']} « {b.get('titre_bien') or ''} » : il rejoint le catalogue "
            f"« {statut} », sans être diffusé. ⚠ Pas de retour en arrière depuis l'application.",
            {"hektor_annonce_id": int(b["hektor_annonce_id"])})


def executer_activer_brouillon(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    b = _brouillon(ctx, p.get("hektor_annonce_id"))  # encore un brouillon AU CLIC
    if not str(b.get("statut_annonce") or "").strip():
        raise Refus("ce brouillon n'a plus de statut")
    lignes = _ecrire(ctx, "POST", "app_console_job", {
        "job_type": "exit_hektor_draft_annonce", "app_dossier_id": b["app_brouillon_id"],
        "hektor_annonce_id": str(b["hektor_annonce_id"]),
        "payload_json": {"numero_dossier": b.get("numero_dossier"), "titre_bien": b.get("titre_bien"),
                         "statut_annonce": b.get("statut_annonce"), "source": "assistant"},
        "priority": 20, "requested_by": ctx.user_id})
    return {"hektor_annonce_id": b["hektor_annonce_id"], "job_id": (lignes or [{}])[0].get("id")}


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
            "a_dire": "Ajouter ou retirer un portail n'est possible que sur un bien diffusable (la direction le rend "
                      "diffusable : demande_direction type diffusion)."}


def preparer_portail(ctx: ContexteAssistant, p: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    portail = str(p.get("portail") or "").strip()
    if portail not in PORTAILS:
        raise Refus("Portail : " + ", ".join(PORTAILS) + ".")
    bien = _bien_diffusion(ctx, p.get("hektor_annonce_id"))
    if str(bien.get("diffusable") or "") != "1":
        raise Refus("Ce bien n'est pas encore diffusable : la direction doit le valider et cocher Diffusable "
                    "(demande_direction, type diffusion).")
    publier = bool(p.get("publier"))
    if (portail in _en_ligne(bien.get("portails_resume"))) == publier:
        raise Refus(f"Le bien est déjà {'en ligne' if publier else 'absent'} sur {PORTAILS[portail]}.")
    verbe = "PUBLIER" if publier else "RETIRER"
    return (f"{verbe} l'annonce {bien['hektor_annonce_id']} « {bien.get('titre_bien') or ''} » "
            f"{'sur' if publier else 'de'} {PORTAILS[portail]} — les autres portails ne bougent pas",
            {"hektor_annonce_id": int(bien["hektor_annonce_id"]), "portail": portail, "publier": publier})


def executer_portail(ctx: ContexteAssistant, p: dict[str, Any]) -> dict[str, Any]:
    from .hektor_bridge import HektorBridgeService
    portail, publier = p["portail"], bool(p["publier"])
    bien = _bien_diffusion(ctx, p.get("hektor_annonce_id"))
    _email, user = _personne(ctx)
    try:  # la garde de la route /apply : négociateur = bien diffusable ET le sien (jugé avec SON jeton)
        SupabaseAdminService(ctx.settings).assert_can_apply_portals(user, f"Bearer {ctx.jeton}", bien["app_dossier_id"])
    except HTTPException as exc:
        raise Refus(f"refusé : {exc.detail}") from None
    pont = HektorBridgeService(ctx.settings)
    numero = PORTAIL_ID_COMMUN.get(portail) or next(
        (str(t["hektor_broadcast_id"]) for t in pont._load_agency_targets(bien.get("agence_nom"))  # noqa: SLF001
         if t.get("portal_key") == portail), None)
    if not numero:
        raise Refus(f"numéro de passerelle {PORTAILS[portail]} introuvable pour l'agence {bien.get('agence_nom') or ''}")
    # = saveDiffusionTargets (api.ts:8504) avec UNE cible : on efface les choix du bien, on écrit celui-ci
    _ecrire(ctx, "DELETE", "app_diffusion_target", None, {"app_dossier_id": f"eq.{bien['app_dossier_id']}"})
    _ecrire(ctx, "POST", "app_diffusion_target", [{
        "app_dossier_id": bien["app_dossier_id"], "hektor_annonce_id": int(bien["hektor_annonce_id"]),
        "hektor_broadcast_id": numero, "portal_key": portail, "target_state": "enabled" if publier else "disabled",
        "source_ref": "console_diffusion", "note": "assistant", "requested_by_role": ctx.role,
        "requested_by_name": ctx.nom or ctx.email, "requested_at": datetime.now(timezone.utc).isoformat()}])
    try:
        r = pont.apply(bien["app_dossier_id"], False, False, ctx.email or ctx.user_id)
    except HTTPException as exc:
        raise Refus(f"Hektor n'a pas pu être joint ({exc.detail})") from None
    refus = next((f for f in r.get("failed") or [] if f.get("action") in {"add", "remove"}), None)
    if refus:
        raise Refus(f"Hektor a refusé : {str(refus.get('error') or '')[:200]}")
    avant = _en_ligne(bien.get("portails_resume"))
    apres = [k for k in avant if k != portail] + ([portail] if publier else [])
    try:  # Hektor a CONFIRMÉ ; si le report rate, la relecture de la nuit remettra l'app d'accord (comme l'écran)
        pont.persist_state(bien["app_dossier_id"], portails_resume=", ".join(apres), nb_portails_actifs=len(apres))
        reporte = True
    except Exception:  # noqa: BLE001
        reporte = False
    return {"app_dossier_id": bien["app_dossier_id"], "portail": portail, "publie": publier, "en_ligne_apres": apres,
            "resume_reporte": reporte}


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
    # lot 4a
    Geste("modifier_bien",
          "Prépare la modification de champs d'une annonce VIVANTE (vide = inchangé) : titre, texte, surfaces, pièces, "
          "chambres, niveaux, salles d'eau, WC, garages, parkings, terrasses, année, DPE / GES, copropriété. JAMAIS le prix "
          "(demande_direction baisse_prix), ni l'adresse, ni les honoraires, ni le mandat. Écrit chez nous tout de suite, "
          "chez Hektor 10 minutes après.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   **{cle: {"type": "string", "description": f"{libelle} ; vide = inchangé"}
                      for cle, (libelle, _genre) in CHAMPS_BIEN.items()}}),
          preparer_modifier_bien, executer_modifier_bien),
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
    Geste("activer_brouillon",
          "Prépare l'ACTIVATION d'un brouillon : il rejoint le catalogue de son statut, sans être diffusé. Pas de retour "
          "en arrière depuis l'application.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro d'annonce du brouillon"}}),
          preparer_activer_brouillon, executer_activer_brouillon),
    # lot 4b
    Geste("portail",
          "Prépare : PUBLIER (publier = true) ou RETIRER (publier = false) une annonce DIFFUSABLE sur UN portail. Les autres "
          "portails ne bougent pas. Rendre un bien diffusable reste à la direction.",
          TOUS_LES_ROLES,
          _schema({"hektor_annonce_id": {"type": "integer", "description": "numéro de l'annonce"},
                   "portail": {"type": "string", "enum": list(PORTAILS)},
                   "publier": {"type": "boolean"}}),
          preparer_portail, executer_portail),
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
