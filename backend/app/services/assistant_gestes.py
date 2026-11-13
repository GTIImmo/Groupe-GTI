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
