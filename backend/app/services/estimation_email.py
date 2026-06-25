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
    LEGAL_LINE,
    _button,
    _clean_text,
    _esc,
    email_eyebrow,
    email_lead,
    email_shell,
    email_title,
)


def _track_base(settings: Settings) -> str | None:
    base = (getattr(settings, "email_tracking_base_url", None) or getattr(settings, "app_base_url", None) or "").strip()
    return base.rstrip("/") if base else None


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
    variante: str | None = None,
) -> dict[str, str]:
    """Rend l'email estimation. envoi_id = 'preview' en aperçu, uuid réel à l'envoi.

    Le montant N'EST PAS affiché dans l'email : la valeur n'est visible qu'après
    clic sur le bouton de téléchargement (le clic = vrai signal d'intérêt).
    `variante` choisit le ton de l'intro : 'vente' (défaut) ou 'succession'.
    `custom_intro` (texte libre du négociateur) prime sur la variante.
    """
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

    # Description naturelle du bien (caractéristiques injectées dans l'intro).
    type_label = (_clean_text(bien.get("type")) or "bien").strip()
    type_label = (type_label[:1].lower() + type_label[1:]) if type_label else "bien"
    ville = _clean_text(bien.get("ville"))
    desc = f"votre {type_label}"
    try:
        surf = int(float(bien.get("surface"))) if bien.get("surface") not in (None, "") else None
    except (TypeError, ValueError):
        surf = None
    try:
        pcs = int(float(bien.get("pieces"))) if bien.get("pieces") not in (None, "") else None
    except (TypeError, ValueError):
        pcs = None
    if surf:
        desc += f" de {surf} m²"
    if pcs:
        desc += f" ({pcs} pièces)"
    if ville:
        desc += f" à {ville}"

    # Deux variantes (toutes deux après visite) — aucune ne révèle le prix.
    if variante == "succession":
        default_intro = (
            "Je vous remercie de m'avoir reçu. Comme convenu, vous trouverez l'avis de valeur de "
            f"{desc}, établi dans le cadre de votre succession. Fondé sur les caractéristiques du "
            "bien et les transactions comparables récentes, ce document constitue une valeur vénale "
            "que vous pourrez transmettre à votre notaire. Vous le découvrirez en détail en le téléchargeant."
        )
    else:  # 'vente' (défaut)
        default_intro = (
            "Je vous remercie de votre accueil lors de notre rendez-vous. Comme convenu, voici "
            f"l'estimation de {desc}. Je l'ai établie d'après ses caractéristiques et les ventes "
            "récentes du secteur ; vous en trouverez le détail complet dans le document à télécharger."
        )
    intro = (custom_intro or "").strip() or default_intro

    nego_nom = _clean_text(negociateur.get("nom")) or "Votre conseiller Groupe GTI"
    nego_agence = _clean_text(negociateur.get("agence")) or "Groupe GTI"
    nego_contact = " · ".join(p for p in (_clean_text(negociateur.get("tel")), _clean_text(negociateur.get("email"))) if p)

    # Le montant n'apparaît PAS : on incite à cliquer pour découvrir la valeur.
    teaser = email_lead(
        "Pour des raisons de confidentialité, le détail de la valeur figure uniquement "
        "dans le document. Cliquez ci-dessous pour le découvrir."
    )

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
        f'{teaser}'
        f'</td></tr>'
        f'<tr><td align="center" style="padding:18px 26px 6px">'
        f'{_button(download_url, "Découvrir la valeur de mon bien (PDF)", bg=BRAND["magenta"], fg=BRAND["on_brand"])}'
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
        "Le détail de la valeur figure dans le document à télécharger :",
        f"Découvrir la valeur de mon bien (PDF) : {download_url}",
        "",
        f"{nego_nom} — {nego_agence}" + (f" — {nego_contact}" if nego_contact else ""),
        "",
        LEGAL_LINE,
    ]
    return {"subject": subject, "html": html, "text": "\n".join(text_lines)}
