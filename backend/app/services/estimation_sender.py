"""Chokepoint d'envoi de l'email « votre estimation est disponible » (Lot 2).

Mêmes garde-fous que le rapprochement (opt-out RGPD, plafond quotidien, dry-run par
défaut, persistance de l'envoi + tracking), mais pour 1 seul dossier d'estimation et
un email qui pointe vers le téléchargement du PDF (route trackée /r/download).
Aucun envoi réel tant que ``email_real_send_enabled`` est faux.
"""

from __future__ import annotations

from typing import Any

from ..settings import Settings
from .email_tracking import EmailTrackingService
from .estimation_email import render_estimation_email
from .google_workspace_service import GoogleWorkspaceService


class EstimationSender:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.tracking = EmailTrackingService(settings)
        self.workspace = GoogleWorkspaceService(settings)

    def send(
        self,
        *,
        recipient_email: str,
        sender_email: str,
        app_dossier_id: int,
        bien: dict[str, Any],
        valeurs: dict[str, Any],
        proprietaire_nom: str | None = None,
        negociateur: dict[str, Any] | None = None,
        prenom: str | None = None,
        civilite: str | None = None,
        custom_intro: str | None = None,
        intro_variante: str | None = None,
        hektor_contact_id: str | None = None,
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        recipient = (recipient_email or "").strip()
        if not recipient:
            return {"ok": False, "skipped": "no_recipient"}

        # 1) Opt-out (RGPD).
        if self.tracking.is_opted_out(recipient):
            return {"ok": False, "skipped": "opt_out", "recipient": recipient}

        # 2) Mode d'envoi : réel uniquement si activé ET demandé.
        real = bool(self.settings.email_real_send_enabled) and not dry_run
        effective_dry_run = not real

        # Expéditeur : Google Workspace ne peut envoyer QU'au nom d'un compte du domaine
        # (impersonation). Si le négociateur a une adresse hors domaine (ex. @gmail.com),
        # on envoie depuis un compte du domaine et on garde son adresse en reply-to —
        # sinon l'envoi échoue silencieusement (cas Franck @gmail.com).
        domain = "@" + str(self.settings.google_workspace_domain or "gti-immobilier.fr").lstrip("@").lower()
        fallback_sender = self.settings.google_workspace_subject_email or ("accueil" + domain)
        raw_sender = (sender_email or "").strip()
        send_as = raw_sender if raw_sender.lower().endswith(domain) else fallback_sender
        reply_to = raw_sender or send_as

        # 3) Plafond quotidien (envois réels seulement).
        daily_count = 0
        cap_alert = False
        if real:
            daily_count = self.tracking.count_real_sends_today()
            if daily_count >= int(self.settings.email_daily_send_cap):
                return {"ok": False, "skipped": "daily_cap", "dailyCount": daily_count, "cap": self.settings.email_daily_send_cap}
            cap_alert = daily_count >= int(self.settings.email_daily_send_alert)

        # 4) Création de l'envoi (variante non-push/pull -> stockée NULL).
        envoi = self.tracking.create_envoi(
            contact_search_key=None, hektor_contact_id=hektor_contact_id,
            recipient_email=recipient, sender_email=send_as, variante="estimation",
            subject="Votre estimation est disponible", dossier_ids=[int(app_dossier_id)],
            dry_run=effective_dry_run, created_by=created_by,
        )
        envoi_id = envoi["id"]

        # 5) Rendu de l'email avec l'envoi réel (liens trackés : pixel + download).
        rendered = render_estimation_email(
            settings=self.settings, envoi_id=envoi_id, app_dossier_id=int(app_dossier_id),
            bien=bien, valeurs=valeurs, proprietaire_nom=proprietaire_nom,
            negociateur=negociateur, prenom=prenom, civilite=civilite, custom_intro=custom_intro,
            variante=intro_variante,
        )

        # 6) En-têtes de désinscription 1-clic.
        headers = self.tracking.list_unsubscribe_headers(envoi_id)

        # 7) Envoi via Google Workspace (réel ou dry-run loggé).
        result = self.workspace.send_gmail_message(
            subject_email=send_as, to=[recipient], subject=rendered["subject"],
            body_text=rendered["text"], body_html=rendered["html"], reply_to=reply_to,
            extra_headers=headers, dry_run=effective_dry_run,
            related_entity_type="contact", related_entity_id=hektor_contact_id,
        )

        if real and result.get("ok"):
            self.tracking.mark_sent(envoi_id, gmail_message_id=result.get("messageId"), gmail_thread_id=result.get("threadId"))

        return {
            "ok": bool(result.get("ok")), "dryRun": effective_dry_run, "envoiId": envoi_id,
            "subject": rendered["subject"], "listUnsubscribe": headers.get("List-Unsubscribe"),
            "dailyCount": daily_count + (1 if real and result.get("ok") else 0),
            "dailyCap": self.settings.email_daily_send_cap, "capAlert": cap_alert,
            "messageId": result.get("messageId"),
        }
