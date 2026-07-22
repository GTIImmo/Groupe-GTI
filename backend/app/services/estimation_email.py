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
    FONT_DISPLAY,
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
    nego_email = _clean_text(negociateur.get("email"))

    # ── Carte « bien estimé » : contexte (type · ville) SANS révéler le prix. ──
    bien_type = (_clean_text(bien.get("type")) or "Bien").strip()
    bien_label = " · ".join(p for p in (bien_type, ville) if p) or bien_type
    bien_card = (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:{BRAND["paper"]};border:1px solid {BRAND["line_warm"]};border-radius:14px;margin:18px 0 4px">'
        f'<tr>'
        f'<td width="60" align="center" valign="middle" style="padding:14px 0 14px 14px">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td width="44" height="44" align="center" valign="middle" bgcolor="{BRAND["surface"]}" '
        f'style="background:{BRAND["surface"]};border:1px solid {BRAND["line_warm"]};border-radius:11px;font-size:20px">🏡</td>'
        f'</tr></table></td>'
        f'<td valign="middle" style="padding:14px 16px">'
        f'<div style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:10.5px;letter-spacing:1.8px;text-transform:uppercase;font-weight:bold">Le bien estimé</div>'
        f'<div style="color:{BRAND["ink_warm"]};font-family:{FONT_DISPLAY};font-size:16px;margin-top:2px">{_esc(bien_label)}</div>'
        f'</td></tr></table>'
    )

    # ── Encart confidentialité : le montant n'apparaît que dans le PDF. ──
    lock_card = (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:{BRAND["magenta_soft"]};border:1px solid #f6d9e6;border-radius:13px;margin:16px 0 2px">'
        f'<tr>'
        f'<td width="34" valign="top" style="padding:14px 0 14px 16px;font-size:16px">🔒</td>'
        f'<td valign="middle" style="padding:14px 16px 14px 6px">'
        f'<span style="color:{BRAND["ink_soft"]};font-family:{FONT_BODY};font-size:13.5px;line-height:1.6">'
        f'Pour des raisons de confidentialité, <strong style="color:{BRAND["magenta_strong"]}">la valeur détaillée '
        f'figure uniquement dans votre document.</strong> Découvrez-la en un clic ci-dessous.'
        f'</span></td></tr></table>'
    )

    # ── Signature premium : pastille initiales + coordonnées. ──
    initials = ("".join(w[0] for w in nego_nom.split()[:2] if w).upper() or "GTI")[:2]
    sig_card = (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border-top:1px solid {BRAND["line_warm"]}"><tr><td style="padding-top:20px">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td width="46" height="46" align="center" valign="middle" bgcolor="{BRAND["magenta"]}" '
        f'style="background:{BRAND["magenta"]};border-radius:50%;color:#ffffff;font-family:{FONT_DISPLAY};font-size:17px;font-weight:600">{_esc(initials)}</td>'
        f'<td valign="middle" style="padding-left:13px">'
        f'<div style="color:{BRAND["ink_warm"]};font-family:{FONT_BODY};font-size:15px;font-weight:bold">{_esc(nego_nom)}</div>'
        f'<div style="color:{BRAND["ink_mute"]};font-family:{FONT_BODY};font-size:13px;margin-top:1px">{_esc(nego_agence)}</div>'
        + (f'<div style="font-family:{FONT_BODY};font-size:13px;margin-top:3px">'
           f'<a href="mailto:{_esc(nego_email)}" style="color:{BRAND["magenta"]};text-decoration:none;font-weight:bold">{_esc(nego_email)}</a></div>' if nego_email else '')
        + f'</td></tr></table></td></tr></table>'
    )
    sig_q = (
        f'<div style="color:{BRAND["ink_mute"]};font-family:{FONT_BODY};font-size:13.5px;line-height:1.6;'
        f'font-style:italic;margin-top:16px">Une question sur cette estimation ? Répondez simplement à cet '
        f'email, je vous rappelle.</div>'
    )
    reassurance = (
        f'<div style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:12px;letter-spacing:.2px">'
        f'🔒&nbsp; Document PDF sécurisé · lien valable 60 jours</div>'
    )

    greeting_html = f'<strong style="color:{BRAND["ink_warm"]}">{_esc(greeting)}</strong><br>{_esc(intro)}'

    inner = (
        f'<tr><td class="gti-pad" style="padding:6px 6px 0">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="gti-card" '
        f'style="background:{BRAND["surface"]};border:1px solid {BRAND["line_warm"]};border-radius:16px">'
        f'<tr><td class="gti-pad" style="padding:30px 30px 4px">'
        f'{email_eyebrow("Votre estimation")}'
        f'{email_title(subject)}'
        f'{bien_card}'
        f'{email_lead(greeting_html)}'
        f'{lock_card}'
        f'</td></tr>'
        f'<tr><td align="center" style="padding:22px 30px 6px">'
        f'{_button(download_url, "Découvrir mon estimation", bg=BRAND["magenta"], fg=BRAND["on_brand"], arrow=True, mso_width=230)}'
        f'</td></tr>'
        f'<tr><td align="center" style="padding:0 30px 10px">{reassurance}</td></tr>'
        f'<tr><td class="gti-pad" style="padding:8px 30px 28px">{sig_card}{sig_q}</td></tr>'
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
        f"{nego_nom} — {nego_agence}" + (f" — {nego_email}" if nego_email else ""),
        "",
        LEGAL_LINE,
    ]
    return {"subject": subject, "html": html, "text": "\n".join(text_lines)}
