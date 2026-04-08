from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from fastapi import HTTPException

from ..settings import Settings


class NotificationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _assert_smtp_configured(self) -> None:
        if not self.settings.smtp_host or not self.settings.smtp_user or not self.settings.smtp_pass:
            raise HTTPException(
                status_code=500,
                detail="SMTP non configuré. Variables requises : SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS",
            )

    def send_diffusion_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._assert_smtp_configured()

        to = str(payload.get("to") or "").strip()
        subject = str(payload.get("subject") or "").strip()
        body_text = str(payload.get("bodyText") or "").strip()
        body_html = str(payload.get("bodyHtml") or "").strip() or None
        from_email = str(payload.get("fromEmail") or "").strip() or None
        from_name = str(payload.get("fromName") or "").strip() or "Application diffusion"
        reply_to = str(payload.get("replyTo") or "").strip() or None

        if not to or not subject or not body_text:
            raise HTTPException(status_code=400, detail="Missing to, subject or bodyText")

        smtp_from = self.settings.smtp_from or self.settings.smtp_user or ""
        effective_sender_email = from_email if (self.settings.smtp_allow_user_from and from_email) else smtp_from
        if not effective_sender_email:
            raise HTTPException(status_code=500, detail="SMTP_FROM ou SMTP_USER manquant pour définir l'expéditeur")

        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message["From"] = f'"{from_name.replace("\"", "\'")}" <{effective_sender_email}>'
        if reply_to or from_email:
            message["Reply-To"] = reply_to or from_email or ""
        message.set_content(body_text)
        if body_html:
            message.add_alternative(body_html, subtype="html")

        try:
            if self.settings.smtp_secure:
                with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
                    server.login(self.settings.smtp_user, self.settings.smtp_pass)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.settings.smtp_user, self.settings.smtp_pass)
                    server.send_message(message)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return {"ok": True, "messageId": message.get("Message-Id")}
