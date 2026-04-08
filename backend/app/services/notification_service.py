from __future__ import annotations

import base64
import smtplib
from email.message import EmailMessage
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings


class NotificationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _has_google_oauth(self) -> bool:
        return bool(
            self.settings.google_client_id
            and self.settings.google_client_secret
            and self.settings.google_refresh_token
            and self.settings.google_sender_email
        )

    def _assert_smtp_configured(self) -> None:
        if not self.settings.smtp_host or not self.settings.smtp_user or not self.settings.smtp_pass:
            raise HTTPException(
                status_code=500,
                detail="SMTP non configuré. Variables requises : SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS",
            )

    def _build_message(self, payload: dict[str, Any]) -> EmailMessage:
        to = str(payload.get("to") or "").strip()
        subject = str(payload.get("subject") or "").strip()
        body_text = str(payload.get("bodyText") or "").strip()
        body_html = str(payload.get("bodyHtml") or "").strip() or None
        from_email = str(payload.get("fromEmail") or "").strip() or None
        from_name = str(payload.get("fromName") or "").strip() or "Application diffusion"
        reply_to = str(payload.get("replyTo") or "").strip() or None

        if not to or not subject or not body_text:
            raise HTTPException(status_code=400, detail="Missing to, subject or bodyText")

        effective_sender_email = (
            self.settings.google_sender_email
            if self._has_google_oauth()
            else (from_email if (self.settings.smtp_allow_user_from and from_email) else (self.settings.smtp_from or self.settings.smtp_user or ""))
        )
        if not effective_sender_email:
            raise HTTPException(status_code=500, detail="Adresse d'expéditeur introuvable")

        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message["From"] = f'"{from_name.replace("\"", "\'")}" <{effective_sender_email}>'
        if reply_to or from_email:
            message["Reply-To"] = reply_to or from_email or ""
        message.set_content(body_text)
        if body_html:
            message.add_alternative(body_html, subtype="html")
        return message

    def _send_with_gmail_api(self, message: EmailMessage) -> dict[str, Any]:
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "refresh_token": self.settings.google_refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        if not token_response.ok:
            try:
                payload = token_response.json()
                detail = payload.get("error_description") or payload.get("error") or token_response.text
            except Exception:
                detail = token_response.text.strip() or "Unable to refresh Google access token"
            raise HTTPException(status_code=500, detail=str(detail))

        access_token = str(token_response.json().get("access_token") or "").strip()
        if not access_token:
            raise HTTPException(status_code=500, detail="Access token Gmail manquant")

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8").rstrip("=")
        send_response = requests.post(
            f"https://gmail.googleapis.com/gmail/v1/users/{self.settings.google_sender_email}/messages/send",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw_message},
            timeout=30,
        )
        if not send_response.ok:
            try:
                payload = send_response.json()
                error_payload = payload.get("error") or {}
                detail = error_payload.get("message") or payload
            except Exception:
                detail = send_response.text.strip() or "Unable to send Gmail API message"
            raise HTTPException(status_code=500, detail=str(detail))

        payload = send_response.json() or {}
        return {"ok": True, "messageId": payload.get("id") or message.get("Message-Id")}

    def _send_with_smtp(self, message: EmailMessage) -> dict[str, Any]:
        self._assert_smtp_configured()
        smtp_from = self.settings.smtp_from or self.settings.smtp_user or ""
        if not smtp_from:
            raise HTTPException(status_code=500, detail="SMTP_FROM ou SMTP_USER manquant pour définir l'expéditeur")

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

    def send_diffusion_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = self._build_message(payload)
        if self._has_google_oauth():
            return self._send_with_gmail_api(message)
        return self._send_with_smtp(message)
