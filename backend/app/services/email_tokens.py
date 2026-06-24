"""Tokens signés (HMAC) pour les liens trackés de l'email de rapprochement.

Lot A : on génère et on vérifie des tokens autoportants (sans état en base).
Chaque token encode l'identifiant d'envoi, le bien concerné, l'action
(« j'aime » / « passe » / « visite » / « ouverture » / « désinscription ») et une
expiration optionnelle. Aucune donnée personnelle n'est placée dans le token.

La persistance des événements (écriture en base à la réception du clic) arrive au
Lot B ; ici on se contente de produire des URL valides et vérifiables, ce qui
permet de tester le rendu et le round-trip de la landing en preview/dry-run.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any

# Actions reconnues par la landing / le tracking.
ACTION_LIKE = "like"      # ❤️ Ça m'intéresse
ACTION_PASS = "pass"      # ✕ Pas pour moi
ACTION_VISITE = "visite"  # Réserver une visite
ACTION_OPEN = "open"      # pixel d'ouverture
ACTION_UNSUB = "unsub"    # désinscription
ACTION_ESPACE = "espace"  # accès à l'espace client (lien magique, lié à un envoi)
ACTION_ESPACE_CONTACT = "espc"  # espace client UNIFIÉ (lié au contact, tous négos confondus)
ACTION_VISITE_REQ = "vreq"  # demande de visite : page d'action (négo confirme, ou client accepte)
ACTION_ESTIMATION = "estim"  # téléchargement de l'avis de valeur (PDF) d'un dossier d'estimation

VALID_ACTIONS = {ACTION_LIKE, ACTION_PASS, ACTION_VISITE, ACTION_OPEN, ACTION_UNSUB,
                 ACTION_ESPACE, ACTION_ESPACE_CONTACT, ACTION_VISITE_REQ, ACTION_ESTIMATION}


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(payload_b64: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    # 16 octets suffisent largement pour un lien email et gardent l'URL courte.
    return _b64url_encode(digest[:16])


def sign_token(payload: dict[str, Any], secret: str) -> str:
    """Sérialise et signe un payload. Retourne `<payload_b64>.<sig_b64>`."""
    compact = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    payload_b64 = _b64url_encode(compact.encode("utf-8"))
    return f"{payload_b64}.{_sign(payload_b64, secret)}"


def verify_token(token: str, secret: str) -> dict[str, Any] | None:
    """Vérifie la signature et l'expiration. Retourne le payload ou None si invalide."""
    if not token or "." not in token:
        return None
    payload_b64, _, sig = token.partition(".")
    if not hmac.compare_digest(sig, _sign(payload_b64, secret)):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    exp = payload.get("x")
    if exp is not None:
        try:
            if datetime.now(UTC).timestamp() > float(exp):
                return None
        except (TypeError, ValueError):
            return None
    return payload


def _exp_ts(ttl_days: int | None) -> float | None:
    if ttl_days is None:
        return None
    return (datetime.now(UTC) + timedelta(days=ttl_days)).timestamp()


def make_feedback_token(
    *,
    envoi_id: str,
    bien_id: int | str | None,
    action: str,
    secret: str,
    ttl_days: int | None = 30,
) -> str:
    """Token pour les boutons ❤️/✕ d'un bien (H3 : 30 jours par défaut)."""
    if action not in (ACTION_LIKE, ACTION_PASS, ACTION_VISITE):
        raise ValueError(f"Action feedback invalide: {action}")
    return sign_token(
        {"v": 1, "e": str(envoi_id), "b": (None if bien_id is None else str(bien_id)), "a": action, "x": _exp_ts(ttl_days)},
        secret,
    )


def make_open_token(*, envoi_id: str, secret: str, ttl_days: int | None = 60) -> str:
    """Token du pixel d'ouverture (signal faible, cf. consigne scoring)."""
    return sign_token({"v": 1, "e": str(envoi_id), "a": ACTION_OPEN, "x": _exp_ts(ttl_days)}, secret)


def make_unsub_token(*, envoi_id: str, secret: str) -> str:
    """Token de désinscription (H3 : sans expiration)."""
    return sign_token({"v": 1, "e": str(envoi_id), "a": ACTION_UNSUB, "x": None}, secret)


def make_espace_token(*, envoi_id: str, secret: str, ttl_days: int | None = 30) -> str:
    """Lien magique vers l'espace client lié à un envoi (par défaut 30 jours)."""
    return sign_token({"v": 1, "e": str(envoi_id), "a": ACTION_ESPACE, "x": _exp_ts(ttl_days)}, secret)


def make_visite_request_token(*, request_id: str, role: str, secret: str, ttl_days: int | None = 21) -> str:
    """Lien d'action d'une demande de visite (sans login). role = 'nego' (confirme/propose) ou
    'client' (accepte un créneau proposé). Porte l'id de la demande."""
    return sign_token({"v": 1, "r": str(request_id), "role": str(role),
                       "a": ACTION_VISITE_REQ, "x": _exp_ts(ttl_days)}, secret)


def make_estimation_token(*, envoi_id: str, app_dossier_id: int | str, secret: str, ttl_days: int | None = 60) -> str:
    """Lien tracké de téléchargement de l'avis de valeur (PDF) d'un dossier d'estimation.
    Porte l'envoi (pour tracer le clic) + l'app_dossier_id (pour retrouver le PDF). 60 j."""
    return sign_token(
        {"v": 1, "e": str(envoi_id), "d": str(app_dossier_id), "a": ACTION_ESTIMATION, "x": _exp_ts(ttl_days)},
        secret,
    )


def make_espace_contact_token(*, hektor_contact_id: str, secret: str, ttl_days: int | None = 60,
                              featured_dossier_id: int | str | None = None) -> str:
    """Lien magique vers l'espace client UNIFIÉ d'un contact (tous les biens, tous les négos).

    Lié au contact (pas à un envoi) : un seul lien stable, même si plusieurs négociateurs
    envoient des emails. `featured_dossier_id` = bien à mettre EN VEDETTE (celui de cet email)."""
    payload = {"v": 1, "c": str(hektor_contact_id), "a": ACTION_ESPACE_CONTACT, "x": _exp_ts(ttl_days)}
    if featured_dossier_id is not None:
        payload["f"] = str(featured_dossier_id)
    return sign_token(payload, secret)
