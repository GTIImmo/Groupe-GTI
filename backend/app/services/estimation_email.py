"""Email « votre estimation est disponible » (Lot 2).

Réutilise INTÉGRALEMENT le système de design email partagé du rapprochement
(coquille premium, en-tête logo GTI, pied légal, dark-mode, boutons MSO) — voir
``rapprochement_email``. Spécifique ici : un email simple (1 bien) qui présente la
valeur estimée + fourchette et un **bouton de téléchargement du PDF tracké**
(``/r/download/{token}`` → log du clic → redirection vers l'URL signée du PDF).
Pixel d'ouverture + lien désinscription identiques au rapprochement.
"""

from __future__ import annotations

from typing import Any

from ..settings import Settings
from . import email_tokens
from .rapprochement_email import (
    BRAND,
    FONT_BODY,
    LEGAL_LINE,
    _button,
    _clean_text,
    _esc,
    _fmt_eur,
    email_eyebrow,
    email_lead,
    email_shell,
    email_title,
)


def _track_base(settings: Settings) -> str | None:
    base = (getattr(settings, "email_tracking_base_url", None) or getattr(settings, "app_base_url", None) or "").strip()
    return base.rstrip("/") if base else None


def _value_block(val_basse: str, val_estimee: str, val_haute: str) -> str:
    """Bloc de valeur : fourchette basse / valeur estimée (magenta) / fourchette haute."""
    cell = (
        '<td width="33%" align="center" valign="bottom" style="padding:6px 4px">'
        '<div style="font-family:{font};font-size:10px;font-weight:bold;letter-spacing:1.2px;'
        'text-transform:uppercase;color:{mute}">{k}</div>'
        '<div style="font-family:{font};font-size:{size};font-weight:bold;color:{color};margin-top:5px">{v}</div></td>'
    )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'class="gti-card" style="background:{BRAND["magenta_soft"]};border:1px solid {BRAND["line_warm"]};'
        f'border-radius:12px"><tr>'
        + cell.format(font=FONT_BODY, mute=BRAND["muted_warm"], k="Fourchette basse", size="16px", color=BRAND["ink_warm"], v=_esc(val_basse))
        + cell.format(font=FONT_BODY, mute=BRAND["muted_warm"], k="Valeur estimée", size="27px", color=BRAND["magenta"], v=_esc(val_estimee))
        + cell.format(font=FONT_BODY, mute=BRAND["muted_warm"], k="Fourchette haute", size="16px", color=BRAND["ink_warm"], v=_esc(val_haute))
        + '</tr></table>'
    )


def render_estimation_email(
    *,
    settings: Settings,
    envoi_id: str,
    app_dossier_id: int,
    bien: dict[str, Any],
    valeurs: dict[str, Any],
    proprietaire_nom: str | None = None,
    negociateur: dict[str, Any] | None = None,
    prenom: str | None = None,
    civilite: str | None = None,
    custom_intro: str | None = None,
) -> dict[str, str]:
    """Rend l'email estimation. envoi_id = 'preview' en aperçu, uuid réel à l'envoi."""
    negociateur = negociateur or {}
    secret = getattr(settings, "email_tracking_secret", None) or settings.supabase_service_role_key
    base = _track_base(settings)

    download_url = (
        f"{base}/r/download/{email_tokens.make_estimation_token(envoi_id=envoi_id, app_dossier_id=app_dossier_id, secret=secret)}"
        if base else "#download"
    )
    pixel = (
        f'<img src="{base}/r/o/{email_tokens.make_open_token(envoi_id=envoi_id, secret=secret)}.png" '
        f'width="1" height="1" alt="" style="display:block;border:0;opacity:0">'
        if base else ""
    )
    unsub_url = f"{base}/r/u/{email_tokens.make_unsub_token(envoi_id=envoi_id, secret=secret)}" if base else None

    name = " ".join(p for p in (civilite, prenom) if p).strip() or _clean_text(proprietaire_nom)
    greeting = f"Bonjour {name}," if name else "Bonjour,"
    subject = "Votre estimation est disponible"
    preheader = "Le détail de la valeur de votre bien, à consulter en un clic."

    titre_bien = _clean_text(bien.get("titre")) or "votre bien"
    localite = " ".join(p for p in (str(bien.get("code_postal") or "").strip(), _clean_text(bien.get("ville"))) if p).strip()
    intro = (custom_intro or "").strip() or (
        f"J'ai le plaisir de vous transmettre l'estimation de « {titre_bien} »"
        + (f" à {localite}" if localite else "")
        + ". Vous trouverez ci-dessous une synthèse, et le document complet en téléchargement."
    )

    nego_nom = _clean_text(negociateur.get("nom")) or "Votre conseiller Groupe GTI"
    nego_agence = _clean_text(negociateur.get("agence")) or "Groupe GTI"
    nego_contact = " · ".join(p for p in (_clean_text(negociateur.get("tel")), _clean_text(negociateur.get("email"))) if p)

    val_estimee = _fmt_eur(valeurs.get("estimee"))
    val_basse = _fmt_eur(valeurs.get("basse"))
    val_haute = _fmt_eur(valeurs.get("haute"))

    sign_html = (
        f"Une question sur cette estimation ? Répondez simplement à cet email, je vous rappelle.<br>"
        f"<strong>{_esc(nego_nom)}</strong> — {_esc(nego_agence)}"
        + (f"<br>{_esc(nego_contact)}" if nego_contact else "")
    )

    inner = (
        f'<tr><td class="gti-pad" style="padding:6px 6px 0">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="gti-card" '
        f'style="background:{BRAND["surface"]};border:1px solid {BRAND["line_warm"]};border-radius:14px">'
        f'<tr><td style="padding:26px 26px 4px">'
        f'{email_eyebrow("Votre estimation")}'
        f'{email_title(subject)}'
        f'{email_lead(_esc(greeting) + "<br>" + _esc(intro))}'
        f'</td></tr>'
        f'<tr><td style="padding:16px 26px 4px">{_value_block(val_basse, val_estimee, val_haute)}</td></tr>'
        f'<tr><td align="center" style="padding:20px 26px 6px">'
        f'{_button(download_url, "Télécharger mon estimation (PDF)", bg=BRAND["magenta"], fg=BRAND["on_brand"])}'
        f'</td></tr>'
        f'<tr><td style="padding:6px 26px 26px">{email_lead(sign_html)}</td></tr>'
        f'</table></td></tr>'
        + (f'<tr><td style="font-size:0;line-height:0">{pixel}</td></tr>' if pixel else "")
    )

    html = email_shell(title=subject, preheader=preheader, inner_rows=inner, tag="Estimation", unsub_url=unsub_url)

    text_lines = [
        greeting,
        "",
        intro,
        "",
        f"Fourchette basse : {val_basse}",
        f"Valeur estimée : {val_estimee}",
        f"Fourchette haute : {val_haute}",
        "",
        f"Télécharger mon estimation (PDF) : {download_url}",
        "",
        f"{nego_nom} — {nego_agence}" + (f" — {nego_contact}" if nego_contact else ""),
        "",
        LEGAL_LINE,
    ]
    return {"subject": subject, "html": html, "text": "\n".join(text_lines)}
