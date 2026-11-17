from __future__ import annotations

import re
import unicodedata
import uuid
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

import requests

from ..settings import Settings
from .supabase_storage import CONSOLE_DOCS_BUCKET, _headers

# ---------------------------------------------------------------------------
# Assistant IA (17/11/2026, note étape 4 §51-52) -- LE TROMBONE : déposer des fichiers de l'ordinateur dans la conversation.
#
# ⛔ La règle du coffre (`hektor_console_documents_temp_upload`) ne laisse une personne déposer QUE dans le dossier d'un
#   travail d'envoi qu'elle vient de créer : un dépôt libre avec son jeton serait REFUSÉ. Ici, c'est NOTRE SERVEUR qui
#   vérifie qui dépose, le type et la taille, puis fabrique une ADRESSE D'ENVOI SIGNÉE pour UN fichier à UN endroit :
#   `temp/assistant/<la personne>/<numéro>/<nom>`. L'écran y envoie le fichier directement (il ne transite pas par
#   Render) ; le serveur RELIT ensuite ce qui a été déposé (taille, type réels) et le SUPPRIME s'il sort des règles.
# ⛔ Le modèle ne voit JAMAIS le contenu : seulement le nom, le type et la taille (`decrire_pour_le_modele`).
# ⛔ La personne ne touche qu'à SES fichiers : le chemin porte son identifiant, pris dans son jeton, jamais fourni.
# Les types et la taille sont ceux du coffre (`storage.buckets`, lus le 17/11) : un type refusé l'est tout de suite,
# avec sa raison (un .odt était refusé EN SILENCE par le coffre : mémoire « coffre-refus-de-type »).
# Les dépôts non utilisés sont purgés après 2 jours (Console/nettoyer_temporaires_orphelins.js, préfixe temp/assistant).
# ---------------------------------------------------------------------------

PREFIXE = "temp/assistant"
TAILLE_MAX = 50 * 1024 * 1024  # = la limite du coffre hektor-console-documents
MAX_FICHIERS = 10  # par question, comme les pièces jointes d'un e-mail
TYPES_ACCEPTES = {  # = storage.buckets.allowed_mime_types de hektor-console-documents (17/11) -> libellé lisible
    "application/pdf": "PDF",
    "image/jpeg": "photo JPEG",
    "image/png": "image PNG",
    "image/webp": "image WebP",
    "application/msword": "Word",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
    "application/vnd.ms-excel": "Excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel",
    "text/plain": "texte",
    "application/zip": "archive ZIP",
}
TYPES_REFUSES_EXPLIQUES = {
    "application/vnd.oasis.opendocument.text": "un fichier LibreOffice (.odt) n'est pas accepté par le coffre : "
                                               "enregistre-le en PDF ou en Word (.docx)",
    "application/vnd.oasis.opendocument.spreadsheet": "un tableur LibreOffice (.ods) n'est pas accepté : "
                                                      "enregistre-le en Excel (.xlsx) ou en PDF",
    "image/heic": "une photo HEIC (iPhone) n'est pas acceptée : envoie-la en JPEG",
    "image/heif": "une photo HEIF (iPhone) n'est pas acceptée : envoie-la en JPEG",
}
_NUMERO = re.compile(r"[0-9a-f]{32}")


class RefusFichier(Exception):
    """Un dépôt refusé : le message part tel quel à l'écran."""


def _nom_sur(nom: str) -> str:
    """Le nom au coffre : sans accents ni caractères spéciaux (comme safeStorageObjectFilename de l'écran)."""
    sans = unicodedata.normalize("NFKD", str(nom or "")).encode("ascii", "ignore").decode()
    sans = re.sub(r"[^A-Za-z0-9._-]+", "_", sans).strip("._") or "fichier"
    if "." in sans:
        base, ext = sans.rsplit(".", 1)
        return f"{base[:100]}.{ext[:10]}"
    return sans[:110]


def _taille_lisible(octets: int) -> str:
    if octets >= 1024 * 1024:
        return f"{octets / (1024 * 1024):.1f} Mo".replace(".", ",")
    return f"{max(1, round(octets / 1024))} Ko"


def _dossier(user_id: str, numero: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", str(user_id or "")):
        raise RefusFichier("Compte illisible : dépôt impossible.")
    if not _NUMERO.fullmatch(str(numero or "")):
        raise RefusFichier("Numéro de fichier illisible.")
    return f"{PREFIXE}/{user_id}/{numero}"


def controler_annonce(nom: str, type_mime: str, taille: int) -> str:
    """Les règles AVANT l'envoi (ce que l'écran annonce) ; rend le type retenu."""
    nom = str(nom or "").strip()
    if not nom:
        raise RefusFichier("Fichier sans nom.")
    type_mime = str(type_mime or "").strip().lower()
    if type_mime in TYPES_REFUSES_EXPLIQUES:
        raise RefusFichier(f"« {nom} » : {TYPES_REFUSES_EXPLIQUES[type_mime]}.")
    if type_mime not in TYPES_ACCEPTES:
        raise RefusFichier(f"« {nom} » : ce type de fichier n'est pas accepté (PDF, photo JPEG / PNG / WebP, Word, "
                           "Excel, texte ou ZIP).")
    if not isinstance(taille, int) or taille <= 0:
        raise RefusFichier(f"« {nom} » est vide.")
    if taille > TAILLE_MAX:
        raise RefusFichier(f"« {nom} » pèse {_taille_lisible(taille)} : 50 Mo au plus.")
    return type_mime


def preparer_depot(settings: Settings, user_id: str, nom: str, type_mime: str, taille: int) -> dict[str, Any]:
    """Vérifie, puis rend une adresse d'envoi signée pour UN fichier, à UN endroit (le jeton ne sert qu'à lui)."""
    type_mime = controler_annonce(nom, type_mime, taille)
    numero = uuid.uuid4().hex
    chemin = f"{_dossier(user_id, numero)}/{_nom_sur(nom)}"
    r = requests.post(f"{settings.supabase_url}/storage/v1/object/upload/sign/{CONSOLE_DOCS_BUCKET}/{quote(chemin, safe='/')}",
                      headers=_headers(settings), json={}, timeout=20)
    if not r.ok:
        raise RefusFichier(f"Le coffre n'a pas préparé le dépôt ({r.status_code}).")
    adresse = str((r.json() or {}).get("url") or "")
    jeton = (parse_qs(urlparse(adresse).query).get("token") or [""])[0]
    if not jeton:
        raise RefusFichier("Le coffre n'a pas rendu d'adresse d'envoi.")
    return {"id": numero, "bucket": CONSOLE_DOCS_BUCKET, "chemin": chemin, "jeton": jeton, "type": type_mime}


def _objets(settings: Settings, user_id: str, numero: str) -> list[dict[str, Any]]:
    r = requests.post(f"{settings.supabase_url}/storage/v1/object/list/{CONSOLE_DOCS_BUCKET}", headers=_headers(settings),
                      json={"prefix": f"{_dossier(user_id, numero)}/", "limit": 5}, timeout=20)
    if not r.ok:
        raise RefusFichier(f"Le coffre n'a pas pu être relu ({r.status_code}).")
    return [o for o in (r.json() or []) if o.get("name") and o.get("id")]  # les « dossiers » n'ont pas d'id


def retirer(settings: Settings, user_id: str, numero: str) -> int:
    objets = _objets(settings, user_id, numero)
    if not objets:
        return 0
    chemins = [f"{_dossier(user_id, numero)}/{o['name']}" for o in objets]
    r = requests.delete(f"{settings.supabase_url}/storage/v1/object/{CONSOLE_DOCS_BUCKET}", headers=_headers(settings),
                        json={"prefixes": chemins}, timeout=20)
    if not r.ok:
        raise RefusFichier(f"Le coffre n'a pas supprimé le fichier ({r.status_code}).")
    return len(chemins)


def decrire(settings: Settings, user_id: str, numero: str) -> dict[str, Any]:
    """Ce qui est VRAIMENT au coffre (relu), contrôlé à nouveau ; un fichier hors règles est supprimé et refusé."""
    objets = _objets(settings, user_id, numero)
    if len(objets) != 1:
        raise RefusFichier("Ce fichier n'est pas (ou plus) dans la conversation : joins-le à nouveau.")
    objet = objets[0]
    meta = objet.get("metadata") or {}
    taille = int(meta.get("size") or meta.get("contentLength") or 0)
    type_mime = str(meta.get("mimetype") or "").lower()
    try:
        controler_annonce(objet["name"], type_mime, taille)
    except RefusFichier:
        retirer(settings, user_id, numero)
        raise
    return {"id": numero, "nom": objet["name"], "type": type_mime, "libelle": TYPES_ACCEPTES[type_mime], "taille": taille,
            "chemin": f"{_dossier(user_id, numero)}/{objet['name']}"}


def copier(settings: Settings, source: str, destination: str) -> None:
    """Copie AU COFFRE (clé du serveur) un fichier du trombone vers la place d'un travail (ex. temp/photos/<travail>/) :
    le fichier n'est pas renvoyé depuis l'ordinateur. La source doit être sous temp/assistant/ (jamais ailleurs)."""
    if not str(source).startswith(f"{PREFIXE}/") or ".." in str(source) or ".." in str(destination):
        raise RefusFichier("Copie refusée : la source n'est pas un fichier joint à l'assistant.")
    r = requests.post(f"{settings.supabase_url}/storage/v1/object/copy", headers=_headers(settings),
                      json={"bucketId": CONSOLE_DOCS_BUCKET, "sourceKey": source, "destinationKey": destination}, timeout=30)
    if not r.ok:
        raise RefusFichier(f"Le coffre n'a pas copié le fichier ({r.status_code}).")


def decrire_pour_le_modele(fichiers: list[dict[str, Any]]) -> str:
    """Ce que le modèle voit des fichiers joints : nom, type, taille -- jamais le contenu."""
    if not fichiers:
        return ""
    lignes = [f"fichier:{f['id']} « {f['nom']} » ({f['libelle']}, {_taille_lisible(int(f['taille']))})" for f in fichiers]
    return ("\n\n[Fichiers joints par la personne -- tu ne vois que leur nom, leur type et leur taille, JAMAIS leur "
            "contenu : " + " ; ".join(lignes) + "]")
