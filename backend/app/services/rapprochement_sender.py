"""Chokepoint unique d'envoi de l'email de rapprochement (Lot C).

Utilisé par l'envoi manuel (POST /emails/rapprochement/send) ET par le worker de
relance. Centralise TOUS les garde-fous au même endroit :
- filtrage opt-out AVANT tout envoi (RGPD) ;
- plafond de volume quotidien (anti-spam, indépendant du DNS) + seuil d'alerte ;
- envoi réel uniquement si EMAIL_REAL_SEND_ENABLED ; sinon dry-run forcé ;
- en-têtes List-Unsubscribe + List-Unsubscribe-Post ;
- persistance de l'envoi et des identifiants Gmail.

Aucun envoi réel n'a lieu tant que `email_real_send_enabled` est faux : on log un
dry-run via le service Google Workspace existant (réutilisé, non dupliqué).
"""

from __future__ import annotations

from typing import Any

from ..settings import Settings
from .email_tracking import EmailTrackingService
from .google_workspace_service import GoogleWorkspaceService
from .rapprochement_email import RapprochementEmailService


class RapprochementSender:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.tracking = EmailTrackingService(settings)
        self.renderer = RapprochementEmailService(settings)
        self.workspace = GoogleWorkspaceService(settings)

    def send(
        self,
        *,
        recipient_email: str,
        sender_email: str,
        annonce_ids: list[int],
        variante: str = "push",
        contact_search_key: str | None = None,
        hektor_contact_id: str | None = None,
        prenom: str | None = None,
        civilite: str | None = None,
        criteres: str | None = None,
        custom_intro: str | None = None,
        dry_run: bool = True,
        relance_type: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        recipient = (recipient_email or "").strip()
        if not recipient:
            return {"ok": False, "skipped": "no_recipient"}

        # 1) Opt-out (RGPD) : jamais d'envoi à un désinscrit.
        if self.tracking.is_opted_out(recipient):
            return {"ok": False, "skipped": "opt_out", "recipient": recipient}

        # 2) Mode d'envoi : réel uniquement si activé en conf ET demandé.
        real = bool(self.settings.email_real_send_enabled) and not dry_run
        effective_dry_run = not real

        # 3) Plafond quotidien (uniquement pour les envois réels).
        daily_count = 0
        cap_alert = False
        if real:
            daily_count = self.tracking.count_real_sends_today()
            if daily_count >= int(self.settings.email_daily_send_cap):
                return {"ok": False, "skipped": "daily_cap",
                        "dailyCount": daily_count, "cap": self.settings.email_daily_send_cap}
            cap_alert = daily_count >= int(self.settings.email_daily_send_alert)

        # 4) Création de l'envoi (statut dépend du mode).
        envoi = self.tracking.create_envoi(
            contact_search_key=contact_search_key, hektor_contact_id=hektor_contact_id,
            recipient_email=recipient, sender_email=sender_email, variante=variante,
            subject="", dossier_ids=annonce_ids, dry_run=effective_dry_run, created_by=created_by,
        )
        envoi_id = envoi["id"]

        # 5) Rendu du template avec l'id d'envoi réel (liens trackés) + variation relance.
        rendered = self.renderer.render_preview(
            annonce_ids=annonce_ids, variante=variante, prenom=prenom, civilite=civilite,
            criteres=criteres, envoi_id=envoi_id, relance_type=relance_type, custom_intro=custom_intro,
        )

        # 6) En-têtes de désinscription 1-clic.
        headers = self.tracking.list_unsubscribe_headers(envoi_id)

        # 7) Envoi via Google Workspace (réel ou dry-run loggé).
        result = self.workspace.send_gmail_message(
            subject_email=sender_email, to=[recipient], subject=rendered["subject"],
            body_text=rendered["text"], body_html=rendered["html"], reply_to=sender_email,
            extra_headers=headers, dry_run=effective_dry_run,
            related_entity_type="contact", related_entity_id=hektor_contact_id,
        )

        if real and result.get("ok"):
            self.tracking.mark_sent(envoi_id, gmail_message_id=result.get("messageId"),
                                    gmail_thread_id=result.get("threadId"))

        return {
            "ok": bool(result.get("ok")), "dryRun": effective_dry_run, "envoiId": envoi_id,
            "subject": rendered["subject"], "listUnsubscribe": headers.get("List-Unsubscribe"),
            "dailyCount": daily_count + (1 if real and result.get("ok") else 0),
            "dailyCap": self.settings.email_daily_send_cap, "capAlert": cap_alert,
            "messageId": result.get("messageId"), "relanceType": relance_type,
        }
