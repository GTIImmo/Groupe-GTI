"""Génération de l'email de rapprochement « type Tinder » (Lot A).

Périmètre Lot A :
- Template HTML production-ready (mobile-first, tables, CSS inline + media queries,
  boutons bulletproof MSO/VML, dark mode, preheader, < 100 Ko).
- Pile de cartes-biens (système 1 multi-biens) : chaque carte a ses propres
  boutons ❤️/✕ trackés et un CTA « Réserver une visite » (flux RDV Google
  Workspace existant via `appointment_public_url`).
- Version texte brut (multipart/alternative).
- Mode preview : rendu sans envoi.

Hors périmètre Lot A (notés comme évolutions / Lots suivants) :
- Bouton « Voir le bien » et pastille/vignette DPE-GES → Lot D (décision H1).
- Persistance des événements de tracking et table d'envoi → Lot B.
- Filtrage opt-out + en-têtes List-Unsubscribe à l'envoi réel → Lot B/D.

Charte : couleurs reprises des tokens `design-system.css` (--ds-brand-500, --ds-ink…)
résolues ici en hex car les clients mail n'héritent pas des variables CSS externes.
Aucune couleur « inventée » : ce sont les valeurs réelles du design system.
"""

from __future__ import annotations

import html
import json
import re
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings
from . import email_tokens

# --- Charte (valeurs réelles de design-system.css) ----------------------------
BRAND = {
    "magenta": "#c5005f",         # --ds-brand-500 (Pantone 226C)
    "magenta_strong": "#8c0044",  # --ds-brand-strong
    "magenta_soft": "#fdf0f6",    # --ds-brand-soft / --ds-brand-50
    "ink": "#222323",             # --ds-ink (Pantone 432C)
    "ink_soft": "#3b4143",        # --ds-ink-soft
    "ink_mute": "#5c6163",        # --ds-ink-mute
    "neutral_line": "#e4e4e6",    # bordures claires
    "neutral_400": "#a1a4a4",     # --ds-neutral-400 (Pantone 421C)
    "bg": "#f6f7f8",              # --ds-bg
    "surface": "#ffffff",         # --ds-surface
    "on_brand": "#ffffff",        # --ds-on-brand
    # Palette éditoriale chaude (rendu « magazine immobilier »)
    "paper": "#f6f1ea",           # ivoire chaud (fond)
    "ink_warm": "#1f1c1a",        # encre chaude (titres)
    "line_warm": "#e7e0d5",       # filets chauds
    "muted_warm": "#8c8478",      # texte secondaire chaud
}

# Polices : serif éditoriale pour les titres (fallback Georgia, universel en mail),
# sans-serif raffinée pour le corps. Pas d'Arial brut partout.
FONT_DISPLAY = "'Playfair Display', Georgia, 'Times New Roman', serif"
FONT_BODY = "'Helvetica Neue', Helvetica, Arial, sans-serif"

LOGO_URL = "https://www.gti-immobilier.fr/images/logoSite.png"

# Mentions légales reprises de mandat-template.html (agence GROUPE GTI).
LEGAL_LINE = (
    "GROUPE GTI, SAS au capital de 309 968 € — Siège : 22 rue Jean Jaurès, 42700 Firminy — "
    "RCS Saint-Étienne 502 811 144 — Carte professionnelle CPI 42022019 000 043 878 "
    "(CCI Lyon St Étienne Roanne)."
)

_WS_RE = re.compile(r"\s+")


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _clean_text(value: Any) -> str:
    return _WS_RE.sub(" ", html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))).strip()


def _to_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _fmt_eur(value: Any) -> str:
    num = _to_number(value)
    if num is None:
        return "—"
    return f"{round(num):,}".replace(",", " ") + " €"


def _fmt_int(value: Any) -> str | None:
    num = _to_number(value)
    return str(round(num)) if num is not None else None


# --- Honoraires (mapping validé H2, règles loi Hoguet) ------------------------
def format_honoraires(prix: Any, honoraires_raw: Any) -> dict[str, Any]:
    """Construit l'affichage du prix honoraires inclus + qui les paie.

    Règles validées sur biens réels :
    - `prix` public = prix FAI (honoraires inclus).
    - dans honoraires_json, `taux` est un MONTANT en € (pas un %), dédupliqué.
    - `charge` ∈ {vendeur, acquéreur} (casse variable, parfois 2 lignes).
      Défaut en cas d'ambiguïté : on privilégie la ligne « acquéreur ».
    - net vendeur dérivé = FAI − honoraires (prix_net_vendeur est NULL en base).
    - % TTC = honoraires / net vendeur (base loi Hoguet).
    """
    prix_fai = _to_number(prix)
    entries: list[dict[str, Any]] = []
    raw = honoraires_raw
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = None
    if isinstance(raw, list):
        seen: set[tuple[str, str]] = set()
        for item in raw:
            if not isinstance(item, dict):
                continue
            montant = _to_number(item.get("taux"))
            charge = str(item.get("charge") or "").strip().lower()
            if montant is None:
                continue
            charge_norm = "acquereur" if charge.startswith(("acqu", "achet")) else ("vendeur" if charge else "")
            key = (f"{montant:.2f}", charge_norm)
            if key in seen:
                continue
            seen.add(key)
            entries.append({"montant": montant, "charge": charge_norm})

    # Sélection : on privilégie la charge acquéreur si présente.
    chosen = next((e for e in entries if e["charge"] == "acquereur"), None) or (entries[0] if entries else None)

    if prix_fai is None:
        return {"price_main": "—", "sub": None, "charge": None}

    if not chosen or not chosen["charge"]:
        return {"price_main": _fmt_eur(prix_fai), "sub": "Honoraires inclus", "charge": None}

    if chosen["charge"] == "vendeur":
        return {
            "price_main": _fmt_eur(prix_fai),
            "sub": "Honoraires à la charge du vendeur",
            "charge": "vendeur",
        }

    # charge acquéreur → FAI + % TTC + net vendeur (loi Hoguet)
    montant = chosen["montant"]
    net = prix_fai - montant
    pct_txt = None
    if net and net > 0:
        pct = montant / net * 100
        pct_txt = f"{pct:.1f}".replace(".", ",") + " %"
    sub = "dont {pct} TTC d'honoraires à la charge de l'acquéreur".format(pct=pct_txt) if pct_txt else \
        "Honoraires à la charge de l'acquéreur"
    return {
        "price_main": f"{_fmt_eur(prix_fai)} FAI",
        "sub": sub,
        "net": f"Prix hors honoraires : {_fmt_eur(net)}",
        "charge": "acquereur",
    }


# --- Vue normalisée d'un bien pour le template --------------------------------
def build_bien_view(dossier: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    ref = (
        str(dossier.get("numero_mandat") or dossier.get("numero_dossier") or "").strip()
        or (f"V{dossier.get('hektor_annonce_id')}" if dossier.get("hektor_annonce_id") else "")
    )
    ville = str(dossier.get("ville") or detail.get("ville_publique_listing") or "").strip()
    cp = str(dossier.get("code_postal") or detail.get("code_postal") or "").strip()
    secteur = " ".join(p for p in (cp, ville) if p).strip()

    specs: list[str] = []
    surface = _fmt_int(detail.get("surface"))
    pieces = _fmt_int(detail.get("nb_pieces"))
    chambres = _fmt_int(detail.get("nb_chambres"))
    if surface:
        specs.append(f"{surface} m²")
    if pieces:
        specs.append(f"{pieces} pièces")
    if chambres:
        specs.append(f"{chambres} ch.")

    titre = _clean_text(dossier.get("titre_bien") or detail.get("texte_principal_titre")) or "Bien à découvrir"
    photo = str(dossier.get("photo_url_listing") or detail.get("photo_url_listing") or "").strip()

    return {
        "dossier_id": dossier.get("app_dossier_id"),
        "annonce_id": dossier.get("hektor_annonce_id"),
        "ref": ref,
        "titre": titre,
        "secteur": secteur,
        "specs": specs,
        "photo": photo if photo.startswith("https://") and "no_pic" not in photo else "",
        "honoraires": format_honoraires(dossier.get("prix"), detail.get("honoraires_json")),
    }


# --- Boutons bulletproof (MSO/VML + a) ----------------------------------------
def _button(href: str, label: str, *, bg: str, fg: str, border: str | None = None) -> str:
    border = border or bg
    href_e = _esc(href)
    return f"""<!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{href_e}" style="height:46px;v-text-anchor:middle;width:210px;" arcsize="50%" strokecolor="{border}" fillcolor="{bg}">
<w:anchorlock/><center style="color:{fg};font-family:Georgia,serif;font-size:14px;font-weight:bold;">{_esc(label)}</center>
</v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
<a href="{href_e}" style="background:{bg};border:1px solid {border};border-radius:26px;color:{fg};display:inline-block;font-family:{FONT_BODY};font-size:14px;font-weight:bold;letter-spacing:.3px;line-height:44px;text-align:center;text-decoration:none;width:210px;-webkit-text-size-adjust:none;mso-hide:all;">{_esc(label)}</a>
<!--<![endif]-->"""


# ─────────────────────────────────────────────────────────────────────────────
# Système de design email PARTAGÉ (en-tête / pied / coquille premium)
# Réutilisé par TOUS les emails (rapprochement + transactionnels visite/message)
# pour une identité unique : papier ivoire, encre chaude, filet magenta signature,
# logo réel GTI + lockup domaine, titres Playfair, pied avec marque + mentions.
# Bulletproof : tables + styles inline, dark-mode, preheader, MSO.
# ─────────────────────────────────────────────────────────────────────────────
EMAIL_TAGLINE = "GTI-IMMOBILIER.FR"

# <head> commun (polices serif éditoriales, dark-mode, MSO) — classes gti-* pour le mode sombre.
EMAIL_HEAD = (
    '<meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    '<meta http-equiv="X-UA-Compatible" content="IE=edge">'
    '<meta name="color-scheme" content="light dark">'
    '<meta name="supported-color-schemes" content="light dark">'
    '<!--[if !mso]><!-- --><link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&display=swap" rel="stylesheet"><!--<![endif]-->'
    '<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->'
    '<style>'
    f'body{{margin:0;padding:0;background:{BRAND["paper"]};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}'
    'img{-ms-interpolation-mode:bicubic}a{text-decoration:none}'
    '@media only screen and (max-width:600px){.gti-container{width:100%!important}.gti-pad{padding-left:18px!important;padding-right:18px!important}}'
    '@media (prefers-color-scheme:dark){'
    'body,.gti-bg{background:#15130f!important}'
    '.gti-card{background:#211e19!important;border-color:#322d25!important}'
    '.gti-ink{color:#f5efe6!important}.gti-mute{color:#c2b9aa!important}}'
    '</style>'
)


def email_header(*, tag: str | None = None) -> str:
    """En-tête premium : filet magenta signature + logo réel sur encre chaude + lockup domaine."""
    tag_cell = (
        f'<td align="right" style="vertical-align:middle;padding:18px 24px;white-space:nowrap">'
        f'<span style="color:#cfc8bd;font-family:{FONT_BODY};font-size:10px;'
        f'letter-spacing:2.5px;text-transform:uppercase">{_esc(tag)}</span></td>'
    ) if tag else ''
    return (
        f'<tr><td class="gti-pad" style="padding:2px 6px 20px">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'bgcolor="{BRAND["ink_warm"]}" style="background:{BRAND["ink_warm"]};border-radius:12px;overflow:hidden">'
        f'<tr><td colspan="2" style="font-size:0;line-height:0;height:3px;background:{BRAND["magenta"]}">&nbsp;</td></tr>'
        f'<tr><td align="left" style="vertical-align:middle;padding:20px 24px">'
        f'<img src="{LOGO_URL}" height="46" alt="Groupe GTI" style="display:block;border:0;height:46px;width:auto">'
        f'<div style="color:#8f877b;font-family:{FONT_BODY};font-size:9.5px;letter-spacing:3px;margin-top:9px">{EMAIL_TAGLINE}</div>'
        f'</td>{tag_cell}</tr></table></td></tr>'
    )


def email_footer(*, unsub_url: str | None = None) -> str:
    """Pied premium : marque (carré magenta + « Groupe GTI » Playfair) + mentions légales."""
    unsub = (
        f'<div class="gti-mute" style="margin-top:10px;font-family:{FONT_BODY};font-size:11px;'
        f'color:{BRAND["muted_warm"]}">Vous recevez cet email car vous êtes en relation avec notre agence. '
        f'<a href="{_esc(unsub_url)}" style="color:{BRAND["ink_soft"]};text-decoration:underline">Se désinscrire</a>.</div>'
    ) if unsub_url else ''
    return (
        f'<tr><td class="gti-pad" style="padding:26px 6px 28px">'
        f'<div style="border-top:1px solid {BRAND["line_warm"]};margin-bottom:16px;font-size:0;line-height:0">&nbsp;</div>'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td style="vertical-align:middle;padding-right:9px"><table role="presentation" cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td width="10" height="10" bgcolor="{BRAND["magenta"]}" style="font-size:0;line-height:0;background:{BRAND["magenta"]}">&nbsp;</td></tr></table></td>'
        f'<td style="vertical-align:middle"><span class="gti-ink" style="font-family:{FONT_DISPLAY};color:{BRAND["ink_warm"]};font-size:15px;letter-spacing:.5px">Groupe GTI</span></td>'
        f'</tr></table>'
        f'<div class="gti-mute" style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:11px;line-height:1.6;margin-top:10px">{_esc(LEGAL_LINE)}</div>'
        f'{unsub}</td></tr>'
    )


def email_eyebrow(text: str, *, color: str | None = None) -> str:
    """Suréclat : petit tiret magenta + libellé capitales espacées."""
    color = color or BRAND["magenta"]
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td style="vertical-align:middle;padding-right:8px"><div style="width:22px;height:2px;background:{color};font-size:0;line-height:0">&nbsp;</div></td>'
        f'<td style="vertical-align:middle"><span style="color:{color};font-family:{FONT_BODY};font-size:11px;font-weight:bold;letter-spacing:2.5px;text-transform:uppercase">{_esc(text)}</span></td>'
        f'</tr></table>'
    )


def email_title(text: str) -> str:
    return (f'<div class="gti-ink" style="color:{BRAND["ink_warm"]};font-family:{FONT_DISPLAY};'
            f'font-size:25px;line-height:1.22;margin-top:13px">{_esc(text)}</div>')


def email_lead(html_text: str) -> str:
    return (f'<div class="gti-mute" style="color:{BRAND["ink_soft"]};font-family:{FONT_BODY};'
            f'font-size:15px;line-height:1.65;margin-top:11px">{html_text}</div>')


def email_shell(*, title: str, preheader: str, inner_rows: str,
                tag: str | None = None, unsub_url: str | None = None) -> str:
    """Coquille email premium partagée : <head> commun + en-tête + corps + pied."""
    return f"""<!DOCTYPE html>
<html lang="fr" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>{EMAIL_HEAD}<title>{_esc(title)}</title></head>
<body class="gti-bg">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all">{_esc(preheader)}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="gti-bg" style="background:{BRAND['paper']}">
  <tr><td align="center" style="padding:28px 14px">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" class="gti-container" style="width:600px;max-width:600px">
      {email_header(tag=tag)}
      {inner_rows}
      {email_footer(unsub_url=unsub_url)}
    </table>
  </td></tr>
</table>
</body>
</html>"""


def _specs_line(specs: list[str]) -> str:
    if not specs:
        return ""
    sep = f'<span style="color:{BRAND["line_warm"]}">&nbsp;&nbsp;|&nbsp;&nbsp;</span>'
    inner = sep.join(f'<span>{_esc(s)}</span>' for s in specs)
    return (f'<div style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:13px;'
            f'letter-spacing:.4px;margin-top:2px">{inner}</div>')


def build_property_card_html(view: dict[str, Any], links: dict[str, str]) -> str:
    hono = view["honoraires"]
    photo_cell = ""
    if view["photo"]:
        photo_cell = (
            f'<tr><td style="padding:0;font-size:0;line-height:0">'
            f'<img src="{_esc(view["photo"])}" width="600" alt="{_esc(view["titre"])}" '
            f'style="display:block;width:100%;max-width:600px;height:auto;border:0"></td></tr>'
        )
    sub = f'<div style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:13px;margin-top:4px">{_esc(hono["sub"])}</div>' if hono.get("sub") else ""
    net = f'<div style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:12px;margin-top:1px">{_esc(hono["net"])}</div>' if hono.get("net") else ""
    overline = _esc(view["secteur"] or view["ref"]).upper()

    # Refonte : MONO-action. Un seul bouton fort « Voir ce bien » qui ouvre l'espace client
    # (galerie, détails, ❤️/✕, RDV). Le refus se fait dans l'espace (avec raison), plus dans l'email.
    cta = _button(links.get("espace") or links["like"], "Voir ce bien", bg=BRAND["magenta"], fg=BRAND["on_brand"])

    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
      style="background:{BRAND['surface']};border:1px solid {BRAND['line_warm']};border-radius:4px;margin:0 0 18px">
      {photo_cell}
      <tr><td style="padding:22px 26px 0">
        <div style="color:{BRAND['magenta']};font-family:{FONT_BODY};font-size:11px;font-weight:bold;letter-spacing:2px">{overline}</div>
        <div style="color:{BRAND['ink_warm']};font-family:{FONT_DISPLAY};font-size:23px;line-height:1.25;margin:8px 0 0">{_esc(view['titre'])}</div>
      </td></tr>
      <tr><td style="padding:14px 26px 0">
        <div style="color:{BRAND['ink_warm']};font-family:{FONT_DISPLAY};font-size:25px;line-height:1.1">{_esc(hono['price_main'])}</div>
        {sub}{net}
      </td></tr>
      <tr><td style="padding:12px 26px 0">
        <div style="border-top:1px solid {BRAND['line_warm']};font-size:0;line-height:0">&nbsp;</div>
      </td></tr>
      <tr><td style="padding:12px 26px 0">{_specs_line(view['specs'])}</td></tr>
      <tr><td align="center" style="padding:22px 26px 22px">{cta}</td></tr>
    </table>"""


# --- Email complet ------------------------------------------------------------
def build_email_html(ctx: dict[str, Any]) -> str:
    cards = "".join(build_property_card_html(v, v["_links"]) for v in ctx["biens"])
    preheader = _esc(ctx["preheader"])
    accroche = _esc(ctx["accroche"])
    greeting = _esc(ctx["greeting"])
    intro_html = (
        f'<div class="gti-mute" style="color:{BRAND["ink_soft"]};font-size:15px;line-height:1.55;margin-top:8px;white-space:pre-line">{_esc(ctx.get("intro"))}</div>'
        if ctx.get("intro") else ""
    )
    signature = ctx["signature"]
    unsub = _esc(ctx.get("unsubscribe_url") or "#")
    pixel = (
        f'<img src="{_esc(ctx["pixel_url"])}" width="1" height="1" alt="" '
        f'style="display:block;width:1px;height:1px;border:0;opacity:0" />'
        if ctx.get("pixel_url") else ""
    )

    sig_html = (
        f'<div style="color:{BRAND["magenta"]};font-family:{FONT_BODY};font-size:10px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px">Votre conseiller</div>'
        f'<div style="color:{BRAND["ink_warm"]};font-family:{FONT_DISPLAY};font-size:18px">{_esc(signature["nom"])}</div>'
        + (f'<div style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:13px;margin-top:2px">{_esc(signature["agence"])}</div>' if signature.get("agence") else "")
        + (f'<div style="color:{BRAND["muted_warm"]};font-family:{FONT_BODY};font-size:13px">{_esc(signature["tel"])}</div>' if signature.get("tel") else "")
        + (f'<div style="font-family:{FONT_BODY};font-size:13px;margin-top:1px"><a href="mailto:{_esc(signature["email"])}" style="color:{BRAND["magenta"]};text-decoration:none">{_esc(signature["email"])}</a></div>' if signature.get("email") else "")
    )

    # Bloc « Affiner ma recherche » : ouvre l'espace ancré sur le formulaire (#affiner).
    affiner_url = _esc(ctx.get("affiner_url") or "#")
    affiner_html = (
        '<tr><td class="gti-pad" style="padding:0 6px 18px">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="gti-card" '
        'style="background:#fdf0f6;border:1px solid #f3cde0;border-radius:14px"><tr>'
        '<td style="vertical-align:middle;padding:18px 14px 18px 22px">'
        f'<div class="gti-ink" style="color:{BRAND["ink_warm"]};font-family:{FONT_DISPLAY};font-size:17px;line-height:1.25">Pas tout à fait ça&nbsp;?</div>'
        '<div style="color:#8c5a72;font-family:' + FONT_BODY + ';font-size:13px;line-height:1.5;margin-top:3px">'
        'Dites-moi ce que vous cherchez vraiment&nbsp;— je vous envoie des biens plus justes.</div></td>'
        '<td width="40" align="center" style="vertical-align:middle;padding:16px 20px 16px 6px">'
        f'<a href="{affiner_url}" style="display:inline-block;width:34px;height:34px;border-radius:50%;'
        f'background:{BRAND["magenta"]};text-align:center;line-height:34px;color:#ffffff;font-family:{FONT_BODY};'
        'font-size:17px;font-weight:bold;text-decoration:none">&rsaquo;</a></td>'
        '</tr></table></td></tr>'
    )

    return f"""<!DOCTYPE html>
<html lang="fr" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>{_esc(ctx['subject'])}</title>
<!--[if !mso]><!-- --><link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&display=swap" rel="stylesheet"><!--<![endif]-->
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
<style>
  body{{margin:0;padding:0;background:{BRAND['paper']};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}
  img{{-ms-interpolation-mode:bicubic}}
  a{{text-decoration:none}}
  @media only screen and (max-width:600px){{
    .gti-container{{width:100%!important}}
    .gti-pad{{padding-left:18px!important;padding-right:18px!important}}
  }}
  @media (prefers-color-scheme:dark){{
    body,.gti-bg{{background:#15130f!important}}
    .gti-card{{background:#211e19!important;border-color:#322d25!important}}
    .gti-ink{{color:#f5efe6!important}}
    .gti-mute{{color:#c2b9aa!important}}
  }}
</style>
</head>
<body class="gti-bg">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all">{preheader}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="gti-bg" style="background:{BRAND['paper']}">
  <tr><td align="center" style="padding:28px 14px">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" class="gti-container" style="width:600px;max-width:600px">
      <!-- En-tête : logo GTI réel sur bandeau foncé (le logo ressort, le « groupe » gris devient lisible) -->
      <tr><td class="gti-pad" style="padding:2px 6px 18px">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{BRAND['ink_warm']}" style="background:{BRAND['ink_warm']};border-radius:10px"><tr>
          <td align="left" style="vertical-align:middle;padding:18px 24px">
            <img src="{LOGO_URL}" height="50" alt="Groupe GTI" style="display:block;border:0;height:50px;width:auto">
          </td>
          <td align="right" style="vertical-align:middle;padding:18px 24px">
            <span style="color:#cfc8bd;font-family:{FONT_BODY};font-size:10px;letter-spacing:2.5px;text-transform:uppercase">Pour votre projet</span>
          </td>
        </tr></table>
      </td></tr>
      <!-- Accroche éditoriale -->
      <tr><td class="gti-pad" style="padding:14px 6px 22px">
        <div style="color:{BRAND['magenta']};font-family:{FONT_BODY};font-size:11px;font-weight:bold;letter-spacing:2.5px;text-transform:uppercase">Rien que pour vous</div>
        <div class="gti-ink" style="color:{BRAND['ink_warm']};font-family:{FONT_DISPLAY};font-size:26px;line-height:1.2;margin-top:12px">{greeting}</div>
        {intro_html}
        <div class="gti-mute" style="color:{BRAND['ink_soft']};font-family:{FONT_BODY};font-size:15px;line-height:1.65;margin-top:10px">{accroche}</div>
      </td></tr>
      <!-- Cartes biens -->
      <tr><td class="gti-pad" style="padding:0 6px">
        {cards}
      </td></tr>
      <!-- Affiner ma recherche -->
      {affiner_html}
      <!-- Signature -->
      <tr><td class="gti-pad" style="padding:8px 6px 6px">{sig_html}</td></tr>
      <!-- Pied légal -->
      <tr><td class="gti-pad" style="padding:22px 6px 26px">
        <div style="border-top:1px solid {BRAND['line_warm']};margin-bottom:14px;font-size:0;line-height:0">&nbsp;</div>
        <div class="gti-mute" style="color:{BRAND['muted_warm']};font-family:{FONT_BODY};font-size:11px;line-height:1.6">{_esc(LEGAL_LINE)}</div>
        <div class="gti-mute" style="margin-top:8px;font-family:{FONT_BODY};font-size:11px;color:{BRAND['muted_warm']}">
          Vous recevez cet email car vous êtes en relation avec notre agence.
          <a href="{unsub}" style="color:{BRAND['ink_soft']};text-decoration:underline">Se désinscrire</a>.
        </div>
      </td></tr>
    </table>
    {pixel}
  </td></tr>
</table>
</body>
</html>"""


def build_email_text(ctx: dict[str, Any]) -> str:
    lines = [ctx["greeting"], ""]
    if ctx.get("intro"):
        lines += [ctx["intro"], ""]
    lines += [ctx["accroche"], ""]
    for v in ctx["biens"]:
        hono = v["honoraires"]
        lines.append(f"• {v['titre']}" + (f" ({v['ref']})" if v["ref"] else ""))
        if v["secteur"]:
            lines.append(f"  Secteur : {v['secteur']}")
        price = hono["price_main"] + (f" — {hono['sub']}" if hono.get("sub") else "")
        lines.append(f"  Prix : {price}")
        if hono.get("net"):
            lines.append(f"  {hono['net']}")
        if v["specs"]:
            lines.append("  " + " · ".join(v["specs"]))
        lines.append(f"  Voir ce bien : {v['_links'].get('espace') or v['_links']['like']}")
        lines.append("")
    if ctx.get("affiner_url"):
        lines += ["Pas tout à fait ça ? Affinez votre recherche :", ctx["affiner_url"], ""]
    sig = ctx["signature"]
    lines.append("—")
    lines += [s for s in (sig.get("nom"), sig.get("agence"), sig.get("tel"), sig.get("email")) if s]
    lines.append("")
    lines.append(LEGAL_LINE)
    if ctx.get("unsubscribe_url"):
        lines.append(f"Se désinscrire : {ctx['unsubscribe_url']}")
    return "\n".join(lines)


# --- Assemblage / preview -----------------------------------------------------
class RapprochementEmailService:
    """Charge les biens réels et assemble le contexte de rendu (Lot A: preview/dry-run)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _rest_get(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        resp = requests.get(
            f"{self.settings.supabase_url}/rest/v1/{path}",
            headers={
                "apikey": self.settings.supabase_service_role_key,
                "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
            },
            params=params,
            timeout=30,
        )
        if not resp.ok:
            raise HTTPException(status_code=502, detail=f"Lecture Supabase échouée ({path}): {resp.text[:200]}")
        return resp.json() or []

    def _load_dossier(self, annonce_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
        rows = self._rest_get(
            "app_dossier_current",
            {
                "select": "app_dossier_id,hektor_annonce_id,titre_bien,numero_dossier,numero_mandat,"
                          "ville,code_postal,prix,type_bien,commercial_nom,negociateur_email,agence_nom,"
                          "photo_url_listing,statut_annonce",
                "hektor_annonce_id": f"eq.{annonce_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"Annonce {annonce_id} introuvable")
        dossier = rows[0]
        detail_rows = self._rest_get(
            "app_dossier_detail_current",
            {"select": "detail_payload_json", "hektor_annonce_id": f"eq.{annonce_id}", "limit": "1"},
        )
        detail: dict[str, Any] = {}
        if detail_rows:
            raw = str(detail_rows[0].get("detail_payload_json") or "").strip()
            if raw:
                try:
                    parsed = json.loads(raw)
                    detail = parsed if isinstance(parsed, dict) else {}
                except Exception:
                    detail = {}
        return dossier, detail

    def _appointment_url(self, annonce_id: int) -> str | None:
        rows = self._rest_get(
            "app_appointment_public_link",
            {"select": "token", "hektor_annonce_id": f"eq.{annonce_id}", "is_active": "eq.true",
             "order": "created_at.desc", "limit": "1"},
        )
        token = rows[0].get("token") if rows else None
        if not token:
            return None
        # IMPÉRATIF : on réutilise STRICTEMENT le vrai flux RDV Google Workspace,
        # identique à AppointmentService._compose_public_url -> {app_base_url}/rdv/annonce/{token}.
        # On ne pointe JAMAIS vers la vitrine GitHub (gtiimmo.github.io/vitrine, calendrier fictif).
        base = (self.settings.app_base_url or "").rstrip("/")
        if not base or "github.io" in base.lower() or "vitrine" in base.lower():
            return None
        return f"{base}/rdv/annonce/{token}"

    def _track_base(self) -> str:
        # H6 : URL publique HTTPS du backend (à fournir). Repli sur app_base_url.
        base = getattr(self.settings, "email_tracking_base_url", None) or self.settings.app_base_url or ""
        return base.rstrip("/")

    def _links_for_bien(self, envoi_id: str, bien_id: Any, annonce_id: int,
                        hektor_contact_id: str | None = None) -> dict[str, str]:
        secret = getattr(self.settings, "email_tracking_secret", None) or self.settings.supabase_service_role_key
        base = self._track_base()
        like = email_tokens.make_feedback_token(envoi_id=envoi_id, bien_id=bien_id, action=email_tokens.ACTION_LIKE, secret=secret)
        passt = email_tokens.make_feedback_token(envoi_id=envoi_id, bien_id=bien_id, action=email_tokens.ACTION_PASS, secret=secret)
        # « Voir ce bien » ouvre l'espace UNIFIÉ du contact (un seul lien stable, tous négos)
        # dès qu'on connaît le contact ; sinon repli sur l'espace lié à l'envoi (compat).
        if hektor_contact_id:
            espace = email_tokens.make_espace_contact_token(
                hektor_contact_id=str(hektor_contact_id), secret=secret, featured_dossier_id=bien_id)
        else:
            espace = email_tokens.make_espace_token(envoi_id=envoi_id, secret=secret)
        links = {
            "like": f"{base}/r/feedback/{like}" if base else f"#like-{bien_id}",
            "pass": f"{base}/r/feedback/{passt}" if base else f"#pass-{bien_id}",
            # « Voir ce bien » ouvre l'espace client (lien magique), pas une simple page de merci.
            "espace": f"{base}/espace/{espace}" if base else f"#espace-{bien_id}",
        }
        visite = self._appointment_url(annonce_id) if annonce_id else None
        if visite:
            links["visite"] = visite
        return links

    def render_preview(
        self,
        *,
        annonce_ids: list[int],
        variante: str = "push",
        prenom: str | None = None,
        civilite: str | None = None,
        criteres: str | None = None,
        envoi_id: str = "preview",
        relance_type: str | None = None,
        custom_intro: str | None = None,
        hektor_contact_id: str | None = None,
    ) -> dict[str, Any]:
        if not annonce_ids:
            raise HTTPException(status_code=400, detail="Au moins un annonce_id est requis")
        variante = variante if variante in ("push", "pull") else "push"
        # envoi_id = "preview" en mode aperçu ; un uuid réel quand l'envoi est persisté (Lot B).

        biens: list[dict[str, Any]] = []
        signature: dict[str, Any] = {"nom": "Groupe GTI", "agence": "Groupe GTI", "tel": None, "email": None}
        for aid in annonce_ids:
            dossier, detail = self._load_dossier(aid)
            view = build_bien_view(dossier, detail)
            view["_links"] = self._links_for_bien(envoi_id, view["dossier_id"], aid, hektor_contact_id)
            biens.append(view)
            # Signature dérivée du premier bien (négociateur du dossier).
            if signature["tel"] is None:
                signature = {
                    "nom": _clean_text(dossier.get("commercial_nom")) or "Votre conseiller Groupe GTI",
                    "agence": _clean_text(dossier.get("agence_nom")) or "Groupe GTI",
                    "tel": None,
                    "email": _clean_text(dossier.get("negociateur_email")) or None,
                }

        # Textes chaleureux, écrits « comme un conseiller qui pense à son client ».
        if variante == "push":
            subject = "Je crois avoir trouvé un bien pour vous"
            accroche = "Un bien vient de rentrer, et je crois qu'il pourrait vraiment vous plaire."
        else:
            subject = "Un bien choisi pour votre projet"
            accroche = "J'ai pensé à vous en le voyant. Dites-moi simplement s'il vous plaît."
        if len(biens) > 1 and variante == "pull":
            subject = f"{len(biens)} biens choisis pour votre projet"
            accroche = "J'en ai retenu quelques-uns en pensant à votre projet. Dites-moi ceux qui vous plaisent."

        # Relances : un autre angle, toujours avec délicatesse (jamais « relance n°2 » mécanique).
        if relance_type == "no_open":
            subject = "Ce bien vous attend toujours"
            accroche = ("Je me permets de revenir vers vous : ce bien est toujours disponible, "
                        "et je crois sincèrement qu'il mérite votre coup d'œil.")
        elif relance_type == "soft":
            subject = "Toujours disponible — et toujours pour vous"
            accroche = ("Un petit mot pour vous redire que ce bien est encore là. "
                        "Si vous avez la moindre question, je reste à votre écoute.")

        name = " ".join(p for p in (civilite, prenom) if p).strip()
        greeting = f"Bonjour {name}," if name else "Bonjour,"

        secret = getattr(self.settings, "email_tracking_secret", None) or self.settings.supabase_service_role_key
        base = self._track_base()
        # « Affiner ma recherche » : lien espace ancré sur le formulaire (#affiner), depuis l'email.
        espace_link = (biens[0].get("_links", {}).get("espace") if biens else None)
        affiner_url = f"{espace_link}?from=email#affiner" if espace_link else None
        ctx = {
            "subject": subject,
            "preheader": accroche,
            "greeting": greeting,
            "intro": (custom_intro or "").strip() or None,  # mot libre du négociateur (hybride)
            "accroche": accroche,
            "biens": biens,
            "signature": signature,
            "affiner_url": affiner_url,
            "pixel_url": f"{base}/r/o/{email_tokens.make_open_token(envoi_id=envoi_id, secret=secret)}.png" if base else None,
            "unsubscribe_url": f"{base}/r/u/{email_tokens.make_unsub_token(envoi_id=envoi_id, secret=secret)}" if base else None,
        }
        return {"subject": subject, "html": build_email_html(ctx), "text": build_email_text(ctx)}
