"""Demande de visite interactive (Lot 1).

Cycle : le client envoie une demande (depuis l'espace) -> le négociateur du mandat reçoit
un email ACTIONNABLE + une cloche -> il choisit un créneau et confirme -> on crée le VRAI
évènement Google Calendar dans son agenda (DWD) + on prévient le client par email, et la
visite apparaît dans « Mes rendez-vous » de l'espace.

N'utilise JAMAIS la vitrine simulée. Le créneau confirmé est un vrai RDV Google (pour les
négociateurs @gti-immobilier.fr). Si le négociateur n'a pas de boîte Workspace (gmail), on
confirme quand même côté client/statut (best-effort) sans créer l'évènement Google.
"""

from __future__ import annotations

import html as _html
import re
from datetime import datetime, timedelta
from typing import Any

from ..settings import Settings
from . import email_tokens
from .email_tracking import EmailTrackingService
from .google_calendar_event_link_service import GoogleCalendarEventLinkService
from .google_workspace_service import GoogleWorkspaceService
from .rapprochement_email import (
    BRAND, FONT_BODY, FONT_DISPLAY, LOGO_URL, RapprochementEmailService,
    _button, _esc, email_eyebrow, email_lead, email_shell, email_title,
)

GTI_DOMAIN = "gti-immobilier.fr"
_MONTHS = {"jan": 1, "fév": 2, "fev": 2, "mar": 3, "avr": 4, "mai": 5, "juin": 6,
           "juil": 7, "août": 8, "aout": 8, "sep": 9, "oct": 10, "nov": 11, "déc": 12, "dec": 12}
_PERIOD_HOURS = {"Matin": [9, 10, 11], "Après-midi": [14, 15, 16], "Fin de journée": [17, 18]}


class VisiteRequestService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.tracking = EmailTrackingService(settings)
        self.renderer = RapprochementEmailService(settings)
        self.ws = GoogleWorkspaceService(settings)
        self.links = GoogleCalendarEventLinkService(settings)

    def _secret(self) -> str:
        return getattr(self.settings, "email_tracking_secret", None) or self.settings.supabase_service_role_key

    def _base(self) -> str:
        return (getattr(self.settings, "email_tracking_base_url", None) or self.settings.app_base_url or "").rstrip("/")

    def get(self, request_id: str) -> dict[str, Any] | None:
        rows = self.renderer._rest_get("app_espace_visite_request",
                                       {"select": "*", "id": f"eq.{request_id}", "limit": "1"})
        return rows[0] if rows else None

    # ── Créneaux : à partir des jours+moments demandés -> horaires précis ──────
    def _parse_day(self, label: str) -> datetime | None:
        m = re.search(r"(\d{1,2})\s+([a-zA-Zàâäéèêëîïôöùûüç]+)", str(label or ""))
        if not m:
            return None
        day = int(m.group(1))
        mon = _MONTHS.get(m.group(2).lower()[:4]) or _MONTHS.get(m.group(2).lower()[:3])
        if not mon:
            return None
        today = datetime.now()
        year = today.year
        try:
            d = datetime(year, mon, day)
        except ValueError:
            return None
        if d.date() < today.date():
            try:
                d = datetime(year + 1, mon, day)
            except ValueError:
                return None
        return d

    def slot_options(self, req: dict[str, Any]) -> list[dict[str, Any]]:
        days = req.get("requested_days") or []
        periods = req.get("requested_periods") or ["Matin", "Après-midi"]
        out: list[dict[str, Any]] = []
        for dl in days[:15]:
            d = self._parse_day(dl)
            if not d:
                continue
            hours: list[dict[str, str]] = []
            for p in periods:
                for h in _PERIOD_HOURS.get(p, [10, 14]):
                    start = d.replace(hour=h, minute=0, second=0, microsecond=0)
                    end = start + timedelta(hours=1)
                    hours.append({"start": start.isoformat(), "end": end.isoformat(), "label": f"{h}h"})
            out.append({"day": str(dl), "hours": hours})
        return out

    # ── Création de la demande (depuis l'espace) ──────────────────────────────
    def create_request(self, *, envoi: dict[str, Any], bien_id: Any, nego: str | None,
                        title: str, days: list, periods: list, phone: str, message: str) -> dict[str, Any]:
        client = envoi.get("recipient_email") or ""
        rows = self.tracking._insert("app_espace_visite_request", {
            "hektor_contact_id": envoi.get("hektor_contact_id"), "contact_email": client,
            "contact_search_key": envoi.get("contact_search_key"),
            "envoi_id": envoi.get("id") if str(envoi.get("id") or "").count("-") == 4 else None,
            "app_dossier_id": int(bien_id) if str(bien_id or "").isdigit() else None,
            "hektor_annonce_id": (int(envoi.get("hektor_annonce_id"))
                                  if str(envoi.get("hektor_annonce_id") or "").isdigit() else None),
            "bien_title": title, "negociateur_email": nego, "status": "demandee",
            "requested_days": days, "requested_periods": periods, "phone": phone, "message": message,
        }, prefer="return=representation")
        req = rows[0] if isinstance(rows, list) and rows else (rows or {})
        rid = req.get("id")
        # Email actionnable au négociateur + cloche + email de confirmation au client.
        if nego and rid:
            try:
                self._email_nego(req)
            except Exception:
                pass
            try:
                self._cloche_nego(req)
            except Exception:
                pass
        if client and rid:
            try:
                self._email_client_recue(req)
            except Exception:
                pass
        return {"ok": True, "requestId": rid}

    def _cloche_nego(self, req: dict[str, Any]) -> None:
        base = self._base()
        tok = email_tokens.make_visite_request_token(request_id=str(req["id"]), role="nego", secret=self._secret())
        url = f"{base}/visite/{tok}"
        dispo = self._dispo_text(req)
        self.tracking._insert("app_notification", {
            "negociateur_email": req.get("negociateur_email"), "type": "demande_visite",
            "title": "Demande de visite", "app_dossier_id": req.get("app_dossier_id"),
            "body": f"{req.get('contact_email') or 'Un client'} souhaite visiter « {req.get('bien_title')} ». {dispo}",
            "contact_search_key": req.get("contact_search_key"),
            "payload": {"source": "espace_client", "action_url": url, "request_id": str(req["id"]),
                        "phone": req.get("phone")},
        }, prefer="return=minimal")

    @staticmethod
    def _dispo_text(req: dict[str, Any]) -> str:
        days = req.get("requested_days") or []
        periods = req.get("requested_periods") or []
        s = " · ".join(days) + ((" — " + ", ".join(periods)) if periods else "")
        return f"Dispos : {s}." if s else "Dispos : à convenir."

    # ── Confirmation par le négociateur -> vrai évènement Google + email client ─
    def confirm(self, *, request_id: str, start_iso: str, end_iso: str) -> dict[str, Any]:
        req = self.get(request_id)
        if not req:
            return {"ok": False, "error": "not_found"}
        if req.get("status") == "confirmee":
            return {"ok": True, "already": True}
        nego = req.get("negociateur_email") or ""
        client = req.get("contact_email") or ""
        title = req.get("bien_title") or "le bien"
        gev_id, gev_link = None, None
        # Vrai évènement Google uniquement si le négo a une boîte Workspace @gti.
        if nego.lower().endswith("@" + GTI_DOMAIN):
            try:
                ev = self.ws.create_calendar_event(
                    subject_email=nego, summary=f"Visite — {title}",
                    start_at=start_iso, end_at=end_iso,
                    description=f"Visite demandée depuis l'espace client.\nClient : {client}"
                                + (f"\nTél : {req.get('phone')}" if req.get("phone") else ""),
                    attendees=[client] if client else None, send_updates="all",
                    dry_run=not self.settings.email_real_send_enabled)
                if ev.get("ok"):
                    gev_id, gev_link = ev.get("eventId"), ev.get("htmlLink")
                    try:
                        self.links.create_link(
                            event_type="visite", related_entity_type="contact",
                            related_entity_id=req.get("hektor_contact_id"),
                            app_dossier_id=req.get("app_dossier_id"),
                            hektor_annonce_id=req.get("hektor_annonce_id"),
                            hektor_contact_id=req.get("hektor_contact_id"),
                            calendar_email=nego, google_event_id=gev_id, google_html_link=gev_link,
                            summary=f"Visite — {title}", location=None,
                            starts_at=start_iso, ends_at=end_iso,
                            attendees=[client] if client else [],
                            metadata_json={"source": "espace_visite", "titre_bien": title,
                                           "contact_search_key": req.get("contact_search_key")},
                            created_by="espace_visite", created_by_email=client or None)
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            self.tracking._patch("app_espace_visite_request", {"id": f"eq.{request_id}"}, {
                "status": "confirmee", "confirmed_start": start_iso, "confirmed_end": end_iso,
                "google_event_id": gev_id, "google_html_link": gev_link,
                "updated_at": datetime.now().isoformat()})
        except Exception:
            pass
        if client:
            try:
                self._email_client_confirmee(req, start_iso)
            except Exception:
                pass
        return {"ok": True, "googleEvent": bool(gev_id)}

    # ── Niveau 2 : le négociateur PROPOSE des créneaux, le client en choisit un ─
    def propose(self, *, request_id: str, slots: list) -> dict[str, Any]:
        req = self.get(request_id)
        if not req:
            return {"ok": False, "error": "not_found"}
        if req.get("status") == "confirmee":
            return {"ok": True, "already": True}
        clean: list[dict[str, str]] = []
        for s in (slots or [])[:6]:
            st = str((s or {}).get("start") or "").strip()
            en = str((s or {}).get("end") or "").strip()
            if not st or not en:
                continue
            clean.append({"start": st, "end": en,
                          "label": str((s or {}).get("label") or self._fr_datetime(st))[:60]})
        if not clean:
            return {"ok": False, "error": "no_slots"}
        try:
            self.tracking._patch("app_espace_visite_request", {"id": f"eq.{request_id}"}, {
                "status": "proposee", "proposed_slots": clean,
                "updated_at": datetime.now().isoformat()})
        except Exception:
            pass
        if req.get("contact_email"):
            try:
                self._email_client_proposee({**req, "proposed_slots": clean})
            except Exception:
                pass
        return {"ok": True, "proposed": len(clean)}

    def accept(self, *, request_id: str, start_iso: str, end_iso: str) -> dict[str, Any]:
        """Le client accepte un créneau proposé : crée le vrai RDV (via confirm) et prévient le négo."""
        res = self.confirm(request_id=request_id, start_iso=start_iso, end_iso=end_iso)
        if res.get("ok") and not res.get("already"):
            req = self.get(request_id)
            if req:
                try:
                    self._notify_nego_confirmed(req, start_iso)
                except Exception:
                    pass
        return res

    @staticmethod
    def _fr_datetime(iso: str) -> str:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})", str(iso or ""))
        if not m:
            return str(iso)
        y, mo, d, h, mi = m.groups()
        mon = ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
        return f"{int(d)} {mon[int(mo)]} à {h}h{mi if mi != '00' else ''}"

    # ── Emails : coquille premium PARTAGÉE (en-tête/pied/dark-mode/preheader) ──
    def _shell(self, *, title: str, body_html: str, preheader: str = "", tag: str | None = None) -> str:
        return email_shell(title=title, preheader=preheader or title, inner_rows=body_html, tag=tag)

    def _btn(self, href: str, label: str, *, bg: str = None, fg: str = "#ffffff") -> str:
        return _button(href, label, bg=bg or BRAND["magenta"], fg=fg)

    def _email_nego(self, req: dict[str, Any]) -> None:
        base = self._base()
        tok = email_tokens.make_visite_request_token(request_id=str(req["id"]), role="nego", secret=self._secret())
        url = f"{base}/visite/{tok}"
        client = req.get("contact_email") or "Un client"
        phone = req.get("phone")
        rows = (f'<tr><td style="padding:6px 0;color:{BRAND["muted_warm"]};font-size:13px;width:120px">Bien</td>'
                f'<td style="padding:6px 0;color:{BRAND["ink_warm"]};font-size:14px;font-weight:bold">{_esc(req.get("bien_title"))}</td></tr>'
                f'<tr><td style="padding:6px 0;color:{BRAND["muted_warm"]};font-size:13px">Client</td>'
                f'<td style="padding:6px 0;font-size:14px"><a href="mailto:{_esc(client)}" style="color:{BRAND["magenta"]};text-decoration:none">{_esc(client)}</a></td></tr>'
                + (f'<tr><td style="padding:6px 0;color:{BRAND["muted_warm"]};font-size:13px">Téléphone</td>'
                   f'<td style="padding:6px 0;font-size:14px"><a href="tel:{_esc(phone)}" style="color:{BRAND["magenta"]};text-decoration:none">{_esc(phone)}</a></td></tr>' if phone else "")
                + f'<tr><td style="padding:6px 0;color:{BRAND["muted_warm"]};font-size:13px">Disponibilités</td>'
                f'<td style="padding:6px 0;color:{BRAND["ink_warm"]};font-size:14px">{_esc(self._dispo_text(req).replace("Dispos : ", ""))}</td></tr>'
                + (f'<tr><td style="padding:6px 0;color:{BRAND["muted_warm"]};font-size:13px">Message</td>'
                   f'<td style="padding:6px 0;color:{BRAND["ink_warm"]};font-size:14px">{_esc(req.get("message"))}</td></tr>' if req.get("message") else ""))
        body = (f'<tr><td class="gti-pad" style="padding:8px 6px 18px">{email_eyebrow("Demande de visite")}'
                f'{email_title("Un client souhaite visiter ce bien")}</td></tr>'
                f'<tr><td class="gti-pad" style="padding:0 6px"><table role="presentation" width="100%" class="gti-card" style="background:{BRAND["surface"]};border:1px solid {BRAND["line_warm"]};border-radius:12px"><tr><td style="padding:16px 22px"><table role="presentation" width="100%">{rows}</table></td></tr></table></td></tr>'
                f'<tr><td align="center" class="gti-pad" style="padding:24px 6px 6px">{self._btn(url, "Voir et confirmer un créneau")}</td></tr>'
                f'<tr><td align="center" class="gti-pad" style="padding:4px 6px 8px"><div class="gti-mute" style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:12px;line-height:1.5">Vous choisissez l\'horaire&nbsp;: la visite est ajoutée à votre agenda et le client est prévenu.</div></td></tr>')
        html = self._shell(title="Demande de visite", body_html=body, tag="Espace négociateur",
                           preheader=f"{client} souhaite visiter {req.get('bien_title')}")
        self.ws.send_gmail_message(
            subject_email=(self.settings.google_workspace_subject_email or f"accueil@{GTI_DOMAIN}"),
            to=[req.get("negociateur_email")], subject=f"Demande de visite — {req.get('bien_title')}",
            body_html=html, body_text=f"Demande de visite pour {req.get('bien_title')}. {self._dispo_text(req)} Confirmez : {url}",
            reply_to=req.get("contact_email") or None, dry_run=not self.settings.email_real_send_enabled,
            related_entity_type="contact", related_entity_id=req.get("hektor_contact_id"))

    def _email_client_recue(self, req: dict[str, Any]) -> None:
        body = (f'<tr><td class="gti-pad" style="padding:8px 6px 6px">{email_eyebrow("Demande envoyée")}'
                f'{email_title("Votre demande de visite est partie !")}'
                f'{email_lead("Votre conseiller a bien reçu votre demande de visite pour <b>" + _esc(req.get("bien_title")) + "</b>.<br>" + _esc(self._dispo_text(req)) + "<br>Il vous recontacte très vite pour fixer le créneau exact.")}</td></tr>')
        self.ws.send_gmail_message(
            subject_email=(self.settings.google_workspace_subject_email or f"accueil@{GTI_DOMAIN}"),
            to=[req.get("contact_email")], subject="Votre demande de visite est bien enregistrée",
            body_html=self._shell(title="Demande envoyée", body_html=body, tag="Votre projet",
                                  preheader=f"Demande reçue pour {req.get('bien_title')} — votre conseiller revient vers vous."),
            body_text=f"Votre demande de visite pour {req.get('bien_title')} est enregistrée. Votre conseiller vous recontacte.",
            reply_to=req.get("negociateur_email") or None, dry_run=not self.settings.email_real_send_enabled,
            related_entity_type="contact", related_entity_id=req.get("hektor_contact_id"))

    def _email_client_confirmee(self, req: dict[str, Any], start_iso: str) -> None:
        when = self._fr_datetime(start_iso)
        body = (f'<tr><td class="gti-pad" style="padding:8px 6px 6px">{email_eyebrow("Visite confirmée", color="#1f8a5b")}'
                f'{email_title("C\'est confirmé : " + when)}'
                f'{email_lead("Votre visite de <b>" + _esc(req.get("bien_title")) + "</b> est fixée au <b>" + _esc(when) + "</b>.<br>Votre conseiller vous attend. À très bientôt&nbsp;!")}</td></tr>')
        self.ws.send_gmail_message(
            subject_email=(self.settings.google_workspace_subject_email or f"accueil@{GTI_DOMAIN}"),
            to=[req.get("contact_email")], subject=f"Visite confirmée — {req.get('bien_title')}",
            body_html=self._shell(title="Visite confirmée", body_html=body, tag="Votre projet",
                                  preheader=f"Visite confirmée le {when} — {req.get('bien_title')}"),
            body_text=f"Votre visite de {req.get('bien_title')} est confirmée le {when}.",
            reply_to=req.get("negociateur_email") or None, dry_run=not self.settings.email_real_send_enabled,
            related_entity_type="contact", related_entity_id=req.get("hektor_contact_id"))

    def _email_client_proposee(self, req: dict[str, Any]) -> None:
        base = self._base()
        tok = email_tokens.make_visite_request_token(request_id=str(req["id"]), role="client", secret=self._secret())
        url = f"{base}/visite/{tok}"
        slots = req.get("proposed_slots") or []
        lis = "".join(
            f'<tr><td style="padding:7px 0"><span style="display:inline-block;background:{BRAND["surface"]};'
            f'border:1px solid {BRAND["line_warm"]};border-radius:10px;padding:9px 16px;color:{BRAND["ink_warm"]};'
            f'font-size:14px;font-weight:bold">{_esc(self._fr_datetime(s.get("start")) if not s.get("label") else s.get("label"))}</span></td></tr>'
            for s in slots)
        body = (f'<tr><td class="gti-pad" style="padding:8px 6px 6px">{email_eyebrow("Créneaux proposés")}'
                f'{email_title("Votre conseiller vous propose ces horaires")}'
                f'{email_lead("Pour visiter <b>" + _esc(req.get("bien_title")) + "</b>, choisissez le créneau qui vous arrange&nbsp;:")}</td></tr>'
                f'<tr><td class="gti-pad" style="padding:10px 6px 0"><table role="presentation">{lis}</table></td></tr>'
                f'<tr><td align="center" class="gti-pad" style="padding:22px 6px 6px">{self._btn(url, "Choisir mon créneau")}</td></tr>'
                f'<tr><td align="center" class="gti-pad" style="padding:4px 6px 8px"><div class="gti-mute" style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:12px">Un clic suffit&nbsp;: votre visite sera confirmée immédiatement.</div></td></tr>')
        self.ws.send_gmail_message(
            subject_email=(self.settings.google_workspace_subject_email or f"accueil@{GTI_DOMAIN}"),
            to=[req.get("contact_email")], subject=f"Choisissez votre créneau de visite — {req.get('bien_title')}",
            body_html=self._shell(title="Créneaux proposés", body_html=body, tag="Votre projet",
                                  preheader=f"Choisissez votre créneau pour visiter {req.get('bien_title')}"),
            body_text=f"Votre conseiller vous propose des créneaux pour visiter {req.get('bien_title')}. Choisissez le vôtre : {url}",
            reply_to=req.get("negociateur_email") or None, dry_run=not self.settings.email_real_send_enabled,
            related_entity_type="contact", related_entity_id=req.get("hektor_contact_id"))

    def _notify_nego_confirmed(self, req: dict[str, Any], start_iso: str) -> None:
        when = self._fr_datetime(start_iso)
        # Cloche : le client a choisi son créneau.
        try:
            self.tracking._insert("app_notification", {
                "negociateur_email": req.get("negociateur_email"), "type": "visite_confirmee",
                "title": "Visite confirmée par le client", "app_dossier_id": req.get("app_dossier_id"),
                "body": f"{req.get('contact_email') or 'Le client'} a confirmé la visite de « {req.get('bien_title')} » : {when}.",
                "contact_search_key": req.get("contact_search_key"),
                "payload": {"source": "espace_visite", "request_id": str(req["id"])},
            }, prefer="return=minimal")
        except Exception:
            pass
        body = (f'<tr><td class="gti-pad" style="padding:8px 6px 6px">{email_eyebrow("Visite confirmée", color="#1f8a5b")}'
                f'{email_title("Le client a choisi son créneau")}'
                f'{email_lead("<b>" + _esc(req.get("contact_email")) + "</b> a confirmé la visite de <b>" + _esc(req.get("bien_title")) + "</b> le <b>" + _esc(when) + "</b>.<br>L\'évènement a été ajouté à votre agenda.")}</td></tr>')
        self.ws.send_gmail_message(
            subject_email=(self.settings.google_workspace_subject_email or f"accueil@{GTI_DOMAIN}"),
            to=[req.get("negociateur_email")], subject=f"Visite confirmée par le client — {req.get('bien_title')}",
            body_html=self._shell(title="Visite confirmée", body_html=body, tag="Espace négociateur",
                                  preheader=f"{req.get('contact_email')} a confirmé la visite — {when}"),
            body_text=f"{req.get('contact_email')} a confirmé la visite de {req.get('bien_title')} le {when}.",
            reply_to=req.get("contact_email") or None, dry_run=not self.settings.email_real_send_enabled,
            related_entity_type="contact", related_entity_id=req.get("hektor_contact_id"))

    # ── Page d'action du négociateur (sans login, via jeton) ──────────────────
    def render_nego_page(self, *, req: dict[str, Any], token: str) -> str:
        base = self._base()
        confirmed = req.get("status") == "confirmee"
        opts = self.slot_options(req)
        chips = ""
        for o in opts:
            btns = "".join(
                f'<button class="h" data-start="{_html.escape(h["start"])}" data-end="{_html.escape(h["end"])}">{_html.escape(h["label"])}</button>'
                for h in o["hours"])
            chips += f'<div class="day"><div class="dl">{_html.escape(o["day"])}</div><div class="hs">{btns}</div></div>'
        if not opts:
            chips = '<div class="muted">Aucune disponibilité précisée — appelez le client pour convenir d\'un créneau.</div>'
        phone = req.get("phone")
        done = ('<div class="done">✓ Visite confirmée'
                + (f' · {_html.escape(self._fr_datetime(req.get("confirmed_start")))}' if req.get("confirmed_start") else '')
                + '<br><span>Le client a été prévenu et l\'évènement est dans votre agenda.</span></div>') if confirmed else ''
        return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<title>Demande de visite · Groupe GTI</title>
<style>
 *{{box-sizing:border-box}} body{{margin:0;background:#f4f3f0;color:#181a1c;font-family:Manrope,system-ui,sans-serif}}
 .wrap{{max-width:560px;margin:0 auto;padding:0 16px 50px}}
 .top{{background:#1f1c1a;border-radius:0 0 14px 14px;padding:16px 20px;color:#fff;font-weight:800}}
 .card{{background:#fff;border:1px solid #e7e6e1;border-radius:18px;padding:22px;margin-top:18px;box-shadow:0 14px 34px -26px rgba(24,26,28,.5)}}
 .eyebrow{{font-size:11px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:#8c0044}}
 h1{{font-family:Fraunces,serif;font-size:23px;margin:8px 0 4px}}
 .sub{{color:#8b9197;font-size:14px}} .meta{{margin:14px 0;font-size:14px}} .meta b{{color:#8c0044}}
 .lbl{{font-size:12.5px;font-weight:700;margin:18px 0 8px}}
 .day{{margin-bottom:12px}} .dl{{font-size:13px;font-weight:700;margin-bottom:6px}}
 .hs{{display:flex;flex-wrap:wrap;gap:8px}}
 .h{{border:1.5px solid #e7e6e1;background:#fff;border-radius:11px;padding:10px 16px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit}}
 .h:hover{{border-color:#c5005f}} .h.on{{background:#c5005f;border-color:#c5005f;color:#fff}}
 .call{{display:inline-flex;align-items:center;gap:8px;border:1.5px solid #e7e6e1;border-radius:11px;padding:11px 16px;font-size:14px;font-weight:700;color:#181a1c;text-decoration:none;margin-top:6px}}
 .go{{width:100%;margin-top:12px;background:#c5005f;color:#fff;border:none;border-radius:13px;padding:15px;font-size:15px;font-weight:700;cursor:pointer}}
 .go:disabled{{background:#e7e6e1;color:#8b9197;cursor:default}}
 .go.alt{{background:#fff;color:#c5005f;border:1.5px solid #c5005f}}
 .go.alt:disabled{{background:#fff;color:#cbb8c0;border-color:#ecd9e2}}
 .hint{{color:#8b9197;font-size:13px;margin-top:18px}}
 .muted{{color:#8b9197;font-size:14px}} .ack{{margin-top:14px;color:#1f8a5b;font-weight:700;display:none}}
 .done{{background:#e8f6ef;color:#1f8a5b;border-radius:13px;padding:16px;font-weight:700;font-size:15px}} .done span{{font-weight:500;color:#3b6d11;font-size:13px}}
</style></head>
<body>
 <div class="top">Groupe GTI · Espace négociateur</div>
 <div class="wrap"><div class="card">
   <div class="eyebrow">Demande de visite</div>
   <h1>{_html.escape(req.get("bien_title") or "Bien")}</h1>
   <div class="sub">Demande envoyée par un client depuis son espace.</div>
   <div class="meta">Client : <b>{_html.escape(req.get("contact_email") or "")}</b>{(' · Tél : <b>'+_html.escape(phone)+'</b>') if phone else ''}<br>
     Disponibilités : <b>{_html.escape(self._dispo_text(req).replace("Dispos : ", ""))}</b>
     {('<br>Message : '+_html.escape(req.get("message"))) if req.get("message") else ''}</div>
   {done if confirmed else f'''
   <div class="lbl">Sélectionnez le ou les créneaux</div>
   {chips}
   {('<a class="call" href="tel:'+_html.escape(phone)+'">📞 Appeler le client</a>') if phone else ''}
   <div class="hint" id="hint">Un seul créneau → vous confirmez directement. Plusieurs → vous les proposez, le client choisit.</div>
   <button class="go" id="propose" disabled>Proposer au client</button>
   <button class="go alt" id="confirm" disabled>Confirmer directement</button>
   <div class="ack" id="ack"></div>'''}
 </div></div>
<script>
const BASE="{base}/visite/{_html.escape(token)}";
const sel=new Map();
function refresh(){{
  const n=sel.size, p=document.getElementById('propose'), c=document.getElementById('confirm');
  if(p)p.disabled=n<1; if(c)c.disabled=n!==1;
}}
document.querySelectorAll('.h').forEach(b=>b.addEventListener('click',()=>{{
  const k=b.dataset.start;
  if(sel.has(k)){{sel.delete(k);b.classList.remove('on');}}
  else{{const day=b.closest('.day').querySelector('.dl').textContent;
        sel.set(k,{{start:b.dataset.start,end:b.dataset.end,label:day+' · '+b.textContent.trim()}});b.classList.add('on');}}
  refresh();
}}));
async function send(url,payload,msg){{
  document.querySelectorAll('.go').forEach(x=>{{x.disabled=true;}});
  try{{await fetch(url,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});}}catch(e){{}}
  document.querySelectorAll('.go,.hint').forEach(x=>{{x.style.display='none';}});
  const a=document.getElementById('ack'); if(a){{a.textContent=msg;a.style.display='block';}}
}}
const cf=document.getElementById('confirm');
if(cf)cf.addEventListener('click',()=>{{const s=[...sel.values()][0]; if(!s)return;
  send(BASE+'/confirmer',{{start:s.start,end:s.end}},'✓ Visite confirmée — le client est prévenu et l\\'évènement est dans votre agenda.');}});
const pr=document.getElementById('propose');
if(pr)pr.addEventListener('click',()=>{{const arr=[...sel.values()]; if(!arr.length)return;
  send(BASE+'/proposer',{{slots:arr}},'✓ Créneaux envoyés au client — il choisit, et vous serez prévenu de sa confirmation.');}});
</script>
</body></html>"""

    # ── Page d'acceptation du client (sans login, via jeton role=client) ──────
    def render_client_page(self, *, req: dict[str, Any], token: str) -> str:
        base = self._base()
        confirmed = req.get("status") == "confirmee"
        slots = req.get("proposed_slots") or []
        btns = "".join(
            f'<button class="slot" data-start="{_html.escape(s["start"])}" data-end="{_html.escape(s["end"])}">'
            f'{_html.escape(s.get("label") or self._fr_datetime(s.get("start")))}</button>'
            for s in slots if s.get("start") and s.get("end"))
        if not btns:
            btns = '<div class="muted">Aucun créneau proposé pour l\'instant. Votre conseiller revient vers vous.</div>'
        done = ('<div class="done">✓ Votre visite est confirmée'
                + (f' · {_html.escape(self._fr_datetime(req.get("confirmed_start")))}' if req.get("confirmed_start") else '')
                + '<br><span>Vous recevez la confirmation par email. À très bientôt&nbsp;!</span></div>') if confirmed else ''
        return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<title>Votre visite · Groupe GTI</title>
<style>
 *{{box-sizing:border-box}} body{{margin:0;background:#f4f3f0;color:#181a1c;font-family:Manrope,system-ui,sans-serif}}
 .wrap{{max-width:520px;margin:0 auto;padding:0 16px 50px}}
 .top{{background:#1f1c1a;border-radius:0 0 14px 14px;padding:16px 20px;color:#fff;font-weight:800}}
 .card{{background:#fff;border:1px solid #e7e6e1;border-radius:18px;padding:24px;margin-top:18px;box-shadow:0 14px 34px -26px rgba(24,26,28,.5)}}
 .eyebrow{{font-size:11px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:#8c0044}}
 h1{{font-family:Fraunces,serif;font-size:24px;margin:8px 0 4px}}
 .sub{{color:#8b9197;font-size:14px;line-height:1.5}}
 .lbl{{font-size:12.5px;font-weight:700;margin:20px 0 10px}}
 .slot{{display:block;width:100%;text-align:left;border:1.5px solid #e7e6e1;background:#fff;border-radius:13px;padding:15px 18px;margin-bottom:10px;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit;color:#181a1c}}
 .slot:hover{{border-color:#c5005f}} .slot.on{{background:#c5005f;border-color:#c5005f;color:#fff}}
 .go{{width:100%;margin-top:14px;background:#c5005f;color:#fff;border:none;border-radius:13px;padding:16px;font-size:15px;font-weight:700;cursor:pointer}}
 .go:disabled{{background:#e7e6e1;color:#8b9197;cursor:default}}
 .muted{{color:#8b9197;font-size:14px}} .ack{{margin-top:14px;color:#1f8a5b;font-weight:700;display:none}}
 .done{{background:#e8f6ef;color:#1f8a5b;border-radius:13px;padding:16px;font-weight:700;font-size:15px}} .done span{{font-weight:500;color:#3b6d11;font-size:13px}}
</style></head>
<body>
 <div class="top">Groupe GTI · Votre visite</div>
 <div class="wrap"><div class="card">
   <div class="eyebrow">Choisissez votre créneau</div>
   <h1>{_html.escape(req.get("bien_title") or "Votre visite")}</h1>
   <div class="sub">Votre conseiller vous propose ces horaires. Sélectionnez celui qui vous convient.</div>
   {done if confirmed else f'''
   <div class="lbl">Créneaux disponibles</div>
   {btns}
   <button class="go" id="go" disabled>J'accepte ce créneau</button>
   <div class="ack" id="ack">✓ Visite confirmée — vous recevez la confirmation par email. À très bientôt&nbsp;!</div>'''}
 </div></div>
<script>
const POST="{base}/visite/{_html.escape(token)}/accepter";
let sel=null;
document.querySelectorAll('.slot').forEach(b=>b.addEventListener('click',()=>{{
  document.querySelectorAll('.slot').forEach(x=>x.classList.remove('on'));b.classList.add('on');
  sel={{start:b.dataset.start,end:b.dataset.end}};const g=document.getElementById('go');if(g)g.disabled=false;
}}));
const go=document.getElementById('go');
if(go)go.addEventListener('click',async()=>{{
  if(!sel)return; go.disabled=true; go.textContent='Confirmation…';
  try{{await fetch(POST,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(sel)}});}}catch(e){{}}
  go.style.display='none'; const a=document.getElementById('ack'); if(a)a.style.display='block';
}});
</script>
</body></html>"""
