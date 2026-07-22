"""Persistance du suivi de l'email de rapprochement (Lot B).

Couvre :
- Consentement / opt-out (filtrage des désinscrits AVANT chaque envoi).
- Création d'un envoi + ses biens, génération des en-têtes List-Unsubscribe.
- Enregistrement des événements (ouverture, ❤️/✕, visite, désinscription) déclenchés
  par les endpoints de tracking du Lot A.
- Scoring chaud/tiède/froid : clics (❤️/RDV) en signal fort, ouverture en signal faible.

Écrit en base via Supabase REST (service_role), même convention que le reste du backend.
Les envois `preview` (id non-uuid) ne sont jamais persistés : preview/dry-run sûr.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

import requests

from ..settings import Settings
from . import email_tokens

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def is_real_envoi_id(envoi_id: Any) -> bool:
    """Un vrai envoi a un id uuid ; 'preview' (et autres) ne sont pas persistés."""
    return bool(envoi_id) and bool(_UUID_RE.match(str(envoi_id)))


def hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:32]


# Mapping action token (Lot A) -> type d'événement / feedback bien.
_ACTION_TO_EVENT = {
    email_tokens.ACTION_LIKE: "like",
    email_tokens.ACTION_PASS: "pass",
    email_tokens.ACTION_VISITE: "visite",
    email_tokens.ACTION_OPEN: "open",
    email_tokens.ACTION_UNSUB: "unsub",
    email_tokens.ACTION_ESTIMATION: "download",  # téléchargement de l'avis de valeur (signal fort)
}
_ACTION_TO_FEEDBACK = {email_tokens.ACTION_LIKE: "interesse", email_tokens.ACTION_PASS: "refuse"}


class EmailTrackingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # --- REST helpers (service_role) ------------------------------------------
    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        return {
            "apikey": self.settings.supabase_service_role_key,
            "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "Content-Type": "application/json",
            **(extra or {}),
        }

    def _get(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        r = requests.get(f"{self.settings.supabase_url}/rest/v1/{path}", headers=self._headers(), params=params, timeout=30)
        r.raise_for_status()
        return r.json() or []

    def _insert(self, path: str, payload: dict[str, Any] | list[dict[str, Any]], *, on_conflict: str | None = None,
                prefer: str = "return=representation") -> list[dict[str, Any]]:
        params = {"on_conflict": on_conflict} if on_conflict else None
        r = requests.post(f"{self.settings.supabase_url}/rest/v1/{path}",
                          headers=self._headers({"Prefer": prefer}), params=params, json=payload, timeout=30)
        r.raise_for_status()
        return (r.json() or []) if "return=representation" in prefer else []

    def _patch(self, path: str, params: dict[str, str], payload: dict[str, Any]) -> list[dict[str, Any]]:
        r = requests.patch(f"{self.settings.supabase_url}/rest/v1/{path}",
                           headers=self._headers({"Prefer": "return=representation"}), params=params, json=payload, timeout=30)
        r.raise_for_status()
        return r.json() or []

    # --- Consentement / opt-out -----------------------------------------------
    def is_opted_out(self, email: str | None) -> bool:
        if not email or not email.strip():
            return False
        rows = self._get("app_contact_consent", {
            "select": "status", "channel": "eq.email",
            "email": f"eq.{email.strip().lower()}", "status": "eq.opt_out", "limit": "1",
        })
        return bool(rows)

    def filter_opted_out(self, emails: list[str]) -> dict[str, list[str]]:
        """Sépare destinataires autorisés / bloqués. À appeler AVANT tout envoi."""
        allowed, blocked = [], []
        for e in emails:
            (blocked if self.is_opted_out(e) else allowed).append(e)
        return {"allowed": allowed, "blocked": blocked}

    def record_opt_out(self, *, email: str | None, hektor_contact_id: str | None, source: str, ip: str | None = None) -> None:
        if not email:
            return
        now = datetime.now(UTC).isoformat()
        self._insert("app_contact_consent", {
            "email": email.strip().lower(), "hektor_contact_id": hektor_contact_id, "channel": "email",
            "status": "opt_out", "source": source, "opt_out_at": now, "ip_hash": hash_ip(ip), "updated_at": now,
        }, on_conflict="email,channel", prefer="resolution=merge-duplicates,return=minimal")

    # --- Envoi ----------------------------------------------------------------
    def create_envoi(self, *, contact_search_key: str | None, hektor_contact_id: str | None, recipient_email: str,
                     sender_email: str, variante: str, subject: str, dossier_ids: list[int],
                     dry_run: bool = True, created_by: str | None = None, search_index: int | None = None) -> dict[str, Any]:
        rows = self._insert("app_email_envoi", {
            "contact_search_key": contact_search_key, "hektor_contact_id": hektor_contact_id,
            "recipient_email": recipient_email, "sender_email": sender_email,
            "variante": variante if variante in ("push", "pull") else None,
            "subject": subject, "statut": "brouillon" if dry_run else "envoye",
            "sent_at": None if dry_run else datetime.now(UTC).isoformat(),
            "dry_run": dry_run, "created_by": created_by, "search_index": search_index,
        })
        envoi = rows[0]
        biens = [{"envoi_id": envoi["id"], "app_dossier_id": d} for d in dossier_ids if d is not None]
        if biens:
            self._insert("app_email_envoi_bien", biens, on_conflict="envoi_id,app_dossier_id",
                         prefer="resolution=merge-duplicates,return=minimal")
        return envoi

    def list_unsubscribe_headers(self, envoi_id: str) -> dict[str, str]:
        """En-têtes List-Unsubscribe + List-Unsubscribe-Post (Gmail/Yahoo 1-clic)."""
        secret = getattr(self.settings, "email_tracking_secret", None) or self.settings.supabase_service_role_key
        base = (getattr(self.settings, "email_tracking_base_url", None) or self.settings.app_base_url or "").rstrip("/")
        mailto = "postmaster@gti-immobilier.fr"
        parts = [f"<mailto:{mailto}?subject=unsubscribe>"]
        headers = {}
        if base:
            token = email_tokens.make_unsub_token(envoi_id=envoi_id, secret=secret)
            parts.insert(0, f"<{base}/r/u/{token}>")
            headers["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
        headers["List-Unsubscribe"] = ", ".join(parts)
        return headers

    # --- Événements (déclenchés par les endpoints Lot A) ----------------------
    def record_event(self, *, envoi_id: str, action: str, ip: str | None = None, user_agent: str | None = None,
                     bien_id: Any = None, reason: str | None = None) -> None:
        if not is_real_envoi_id(envoi_id):
            return  # preview/dry-run : on ne persiste rien
        evt_type = _ACTION_TO_EVENT.get(action)
        if not evt_type:
            return
        now = datetime.now(UTC).isoformat()
        self._insert("app_email_event", {
            "envoi_id": envoi_id, "app_dossier_id": bien_id, "type": evt_type,
            "user_agent": (user_agent or "")[:300] or None, "ip_hash": hash_ip(ip),
        }, prefer="return=minimal")

        if evt_type == "open":
            self._touch_open(envoi_id, now)
        elif evt_type in ("like", "pass", "visite"):
            self._touch_click(envoi_id, now, action, bien_id, reason=reason)
        elif evt_type == "download":
            self._touch_download(envoi_id, now)
            self._notify_nego_estimation(envoi_id, bien_id)
        elif evt_type == "unsub":
            self._touch_unsub(envoi_id, now, ip)
        self._recompute_score(envoi_id)

    def _envoi(self, envoi_id: str) -> dict[str, Any] | None:
        rows = self._get("app_email_envoi", {"select": "*", "id": f"eq.{envoi_id}", "limit": "1"})
        return rows[0] if rows else None

    def _touch_open(self, envoi_id: str, now: str) -> None:
        env = self._envoi(envoi_id) or {}
        patch: dict[str, Any] = {"open_count": int(env.get("open_count") or 0) + 1}
        if not env.get("opened_at"):
            patch["opened_at"] = now
        if env.get("statut") in (None, "brouillon", "envoye"):
            patch["statut"] = "ouvert"
        self._patch("app_email_envoi", {"id": f"eq.{envoi_id}"}, patch)

    def _touch_click(self, envoi_id: str, now: str, action: str, bien_id: Any, reason: str | None = None) -> None:
        env = self._envoi(envoi_id) or {}
        patch: dict[str, Any] = {"click_count": int(env.get("click_count") or 0) + 1}
        if not env.get("first_clicked_at"):
            patch["first_clicked_at"] = now
        # Statut : un ❤️ ou une visite prime ; un ✕ ne dégrade pas un statut positif.
        if action == email_tokens.ACTION_VISITE:
            patch["statut"], patch["rdv_at"] = "rdv", now
        elif action == email_tokens.ACTION_LIKE:
            if env.get("statut") != "rdv":
                patch["statut"] = "interesse"
        elif action == email_tokens.ACTION_PASS:
            if env.get("statut") in (None, "brouillon", "envoye", "ouvert", "clique"):
                patch["statut"] = "refuse"
        self._patch("app_email_envoi", {"id": f"eq.{envoi_id}"}, patch)

        feedback = _ACTION_TO_FEEDBACK.get(action)
        if feedback and bien_id is not None:
            row = {"envoi_id": envoi_id, "app_dossier_id": bien_id, "feedback": feedback, "feedback_at": now}
            if reason:
                row["feedback_reason"] = reason[:60]
            self._insert("app_email_envoi_bien", row,
                         on_conflict="envoi_id,app_dossier_id", prefer="resolution=merge-duplicates,return=minimal")

    def _touch_download(self, envoi_id: str, now: str) -> None:
        """Téléchargement de l'avis de valeur : signal fort (le propriétaire a récupéré son
        estimation). Compté comme un clic, statut « cliqué » si pas déjà plus avancé."""
        env = self._envoi(envoi_id) or {}
        patch: dict[str, Any] = {"click_count": int(env.get("click_count") or 0) + 1}
        if not env.get("first_clicked_at"):
            patch["first_clicked_at"] = now
        if env.get("statut") in (None, "brouillon", "envoye", "ouvert"):
            patch["statut"] = "clique"
        self._patch("app_email_envoi", {"id": f"eq.{envoi_id}"}, patch)

    def _notify_nego_estimation(self, envoi_id: str, app_dossier_id: Any) -> None:
        """Cloche du négociateur : le propriétaire a consulté son avis de valeur (clic sur
        le lien PDF de l'email). In-app UNIQUEMENT (pas d'email — non nécessaire).

        Même mécanisme que « demande de visite » (espace_visite._cloche_nego) : on écrit
        une ligne app_notification pour le négociateur en charge du dossier ; la cloche du
        front l'affiche telle quelle. Le fil d'activité du cockpit, lui, montre déjà
        « Avis de valeur ouvert par le propriétaire » via app_email_event (type=download).

        Best-effort : n'échoue JAMAIS le tracking (le clic doit toujours rediriger vers le
        PDF). L'anti-doublon repose sur l'index unique partiel
        (negociateur_email, app_dossier_id, type) WHERE read_at IS NULL : tant que le
        négociateur n'a pas lu la notification, un nouveau clic n'en recrée pas (l'INSERT
        en conflit lève, et l'exception est absorbée ici).
        """
        if not app_dossier_id:
            return
        try:
            rows = self._get("app_dossiers_current", {
                "select": "negociateur_email,titre_bien",
                "app_dossier_id": f"eq.{app_dossier_id}", "limit": "1"})
            dossier = rows[0] if rows else {}
            nego = (dossier.get("negociateur_email") or "").strip()
            if not nego:
                return  # dossier sans négociateur résolu : rien à notifier
            titre = (dossier.get("titre_bien") or "votre bien").strip()
            self._insert("app_notification", {
                "negociateur_email": nego,
                "type": "estimation_consultee",
                "title": "Avis de valeur consulté",
                "app_dossier_id": app_dossier_id,
                "body": f"Le propriétaire a ouvert son estimation « {titre} ».",
                "payload": {"source": "estimation", "envoi_id": envoi_id},
            }, prefer="return=minimal")
        except Exception:
            pass  # doublon (index partiel), négo introuvable, réseau… : jamais bloquant

    def _touch_unsub(self, envoi_id: str, now: str, ip: str | None) -> None:
        env = self._envoi(envoi_id) or {}
        self._patch("app_email_envoi", {"id": f"eq.{envoi_id}"}, {"statut": "desinscrit", "unsubscribed_at": now})
        self.record_opt_out(email=env.get("recipient_email"), hektor_contact_id=env.get("hektor_contact_id"),
                            source="email_unsubscribe", ip=ip)

    # --- Scoring chaud / tiède / froid ----------------------------------------
    def score_from_events(self, events: list[dict[str, Any]]) -> str:
        """Clics (like/visite) = signal fort ; ouverture = signal faible.
        chaud  : au moins un ❤️ ou une demande de visite/RDV.
        tiède  : ouverture (signal faible) ou seulement des ✕ (engagement sans intérêt).
        froid  : aucun événement.
        """
        types = {e.get("type") for e in events}
        # « download » (récupération de l'avis de valeur) = intention forte du propriétaire.
        if "like" in types or "visite" in types or "download" in types:
            return "chaud"
        if "open" in types or "pass" in types:
            return "tiede"
        return "froid"

    def _recompute_score(self, envoi_id: str) -> None:
        events = self._get("app_email_event", {"select": "type", "envoi_id": f"eq.{envoi_id}", "limit": "200"})
        self._patch("app_email_envoi", {"id": f"eq.{envoi_id}"}, {"score": self.score_from_events(events)})

    # --- Volume / cap quotidien (garde-fou anti-spam) -------------------------
    def count_real_sends_today(self) -> int:
        """Nombre d'envois RÉELS (non dry-run) émis depuis le début du jour (UTC)."""
        start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        rows = self._get("app_email_envoi", {
            "select": "id", "dry_run": "eq.false", "sent_at": f"gte.{start}", "limit": "1000",
        })
        return len(rows)

    # --- Maj après envoi réel -------------------------------------------------
    def mark_sent(self, envoi_id: str, *, gmail_message_id: str | None, gmail_thread_id: str | None) -> None:
        self._patch("app_email_envoi", {"id": f"eq.{envoi_id}"}, {
            "statut": "envoye", "dry_run": False, "sent_at": datetime.now(UTC).isoformat(),
            "gmail_message_id": gmail_message_id, "gmail_thread_id": gmail_thread_id,
        })

    def bump_relances_count(self, envoi_id: str) -> None:
        env = self._envoi(envoi_id) or {}
        self._patch("app_email_envoi", {"id": f"eq.{envoi_id}"},
                    {"relances_count": int(env.get("relances_count") or 0) + 1})

    # --- Réconciliation avec la file de rappel humaine (app_relance_rapprochement) ---
    def reconcile_human_relances(self, *, contact_search_key: str | None, app_dossier_ids: list[int] | None,
                                 status: str, note: str) -> None:
        """Marque les rappels humains J+5 correspondants (évite tout doublon avec l'auto-relance)."""
        if not contact_search_key:
            return
        params = {"contact_search_key": f"eq.{contact_search_key}", "status": "eq.a_faire"}
        if app_dossier_ids:
            ids = ",".join(str(d) for d in app_dossier_ids if d is not None)
            if ids:
                params["app_dossier_id"] = f"in.({ids})"
        try:
            self._patch("app_relance_rapprochement", params,
                        {"status": status, "sub": note, "updated_at": datetime.now(UTC).isoformat()})
        except Exception:
            pass  # la réconciliation ne doit jamais bloquer un envoi
