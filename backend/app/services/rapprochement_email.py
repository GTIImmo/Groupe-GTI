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
}

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
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{href_e}" style="height:44px;v-text-anchor:middle;width:200px;" arcsize="14%" strokecolor="{border}" fillcolor="{bg}">
<w:anchorlock/><center style="color:{fg};font-family:Arial,sans-serif;font-size:15px;font-weight:bold;">{_esc(label)}</center>
</v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
<a href="{href_e}" style="background:{bg};border:1px solid {border};border-radius:8px;color:{fg};display:inline-block;font-family:Arial,Helvetica,sans-serif;font-size:15px;font-weight:bold;line-height:42px;text-align:center;text-decoration:none;width:200px;-webkit-text-size-adjust:none;mso-hide:all;">{_esc(label)}</a>
<!--<![endif]-->"""


def build_property_card_html(view: dict[str, Any], links: dict[str, str]) -> str:
    hono = view["honoraires"]
    photo_cell = ""
    if view["photo"]:
        photo_cell = (
            f'<tr><td style="padding:0;font-size:0;line-height:0">'
            f'<img src="{_esc(view["photo"])}" width="600" alt="{_esc(view["titre"])}" '
            f'style="display:block;width:100%;max-width:600px;height:auto;border:0;border-radius:12px 12px 0 0"></td></tr>'
        )
    sub = f'<div style="color:{BRAND["ink_mute"]};font-size:13px;margin-top:2px">{_esc(hono["sub"])}</div>' if hono.get("sub") else ""
    net = f'<div style="color:{BRAND["ink_mute"]};font-size:12px;margin-top:1px">{_esc(hono["net"])}</div>' if hono.get("net") else ""
    specs = _esc(" · ".join(view["specs"])) if view["specs"] else ""
    secteur = _esc(view["secteur"])

    like = _button(links["like"], "❤️ Ça m'intéresse", bg=BRAND["magenta"], fg=BRAND["on_brand"])
    passb = _button(links["pass"], "✕ Pas pour moi", bg=BRAND["surface"], fg=BRAND["ink_soft"], border=BRAND["neutral_line"])
    visite = _button(links["visite"], "Réserver une visite", bg=BRAND["ink"], fg=BRAND["on_brand"]) if links.get("visite") else ""
    visite_row = (
        f'<tr><td align="center" style="padding:4px 20px 18px">{visite}</td></tr>' if visite else ""
    )

    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
      style="background:{BRAND['surface']};border:1px solid {BRAND['neutral_line']};border-radius:12px;margin:0 0 20px;overflow:hidden">
      {photo_cell}
      <tr><td style="padding:16px 20px 4px;font-family:Arial,Helvetica,sans-serif">
        <div style="color:{BRAND['neutral_400']};font-size:12px;letter-spacing:.3px">{_esc(view['ref'])}{(' · ' + secteur) if secteur else ''}</div>
        <div style="color:{BRAND['ink']};font-size:18px;font-weight:bold;line-height:1.3;margin:4px 0">{_esc(view['titre'])}</div>
        <div style="color:{BRAND['magenta']};font-size:20px;font-weight:bold;margin-top:6px">{_esc(hono['price_main'])}</div>
        {sub}{net}
        <div style="color:{BRAND['ink_soft']};font-size:14px;margin-top:8px">{specs}</div>
      </td></tr>
      <tr><td style="padding:14px 20px 6px">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
          <td align="center" style="padding:0 5px 0 0;width:50%">{like}</td>
          <td align="center" style="padding:0 0 0 5px;width:50%">{passb}</td>
        </tr></table>
      </td></tr>
      {visite_row}
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
        f'<div style="color:{BRAND["ink"]};font-size:14px;font-weight:bold">{_esc(signature["nom"])}</div>'
        + (f'<div style="color:{BRAND["ink_mute"]};font-size:13px">{_esc(signature["agence"])}</div>' if signature.get("agence") else "")
        + (f'<div style="color:{BRAND["ink_mute"]};font-size:13px">{_esc(signature["tel"])}</div>' if signature.get("tel") else "")
        + (f'<div style="font-size:13px"><a href="mailto:{_esc(signature["email"])}" style="color:{BRAND["magenta"]};text-decoration:none">{_esc(signature["email"])}</a></div>' if signature.get("email") else "")
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
<!--[if mso]><noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript><![endif]-->
<style>
  body{{margin:0;padding:0;background:{BRAND['bg']};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}
  img{{-ms-interpolation-mode:bicubic}}
  a{{text-decoration:none}}
  @media only screen and (max-width:600px){{
    .gti-container{{width:100%!important}}
    .gti-pad{{padding-left:16px!important;padding-right:16px!important}}
  }}
  @media (prefers-color-scheme:dark){{
    body,.gti-bg{{background:#111111!important}}
    .gti-card,.gti-shell{{background:#1c1c1d!important}}
    .gti-ink{{color:#f3f3f3!important}}
    .gti-mute{{color:#b9bbbb!important}}
  }}
</style>
</head>
<body class="gti-bg">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all">{preheader}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="gti-bg" style="background:{BRAND['bg']}">
  <tr><td align="center" style="padding:24px 12px">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" class="gti-container gti-shell" style="width:600px;max-width:600px;background:{BRAND['bg']}">
      <!-- En-tête -->
      <tr><td class="gti-pad" style="padding:4px 8px 18px" align="left">
        <img src="{LOGO_URL}" width="120" alt="Groupe GTI" style="display:block;border:0;height:auto;max-width:120px">
      </td></tr>
      <!-- Accroche -->
      <tr><td class="gti-pad gti-card" style="background:{BRAND['surface']};border-radius:12px 12px 0 0;padding:22px 24px 8px;font-family:Arial,Helvetica,sans-serif">
        <div class="gti-ink" style="color:{BRAND['ink']};font-size:16px">{greeting}</div>
        {intro_html}
        <div class="gti-mute" style="color:{BRAND['ink_soft']};font-size:15px;line-height:1.55;margin-top:6px">{accroche}</div>
      </td></tr>
      <tr><td class="gti-pad gti-card" style="background:{BRAND['surface']};border-radius:0 0 12px 12px;padding:8px 16px 20px;margin-bottom:8px">
        {cards}
      </td></tr>
      <!-- Signature -->
      <tr><td class="gti-pad" style="padding:18px 24px 6px;font-family:Arial,Helvetica,sans-serif">{sig_html}</td></tr>
      <!-- Pied légal -->
      <tr><td class="gti-pad" style="padding:14px 24px 24px;font-family:Arial,Helvetica,sans-serif">
        <div class="gti-mute" style="color:{BRAND['neutral_400']};font-size:11px;line-height:1.5">{_esc(LEGAL_LINE)}</div>
        <div style="margin-top:8px;font-size:11px;color:{BRAND['neutral_400']}">
          Vous recevez cet email car vous êtes en relation avec notre agence.
          <a href="{unsub}" style="color:{BRAND['ink_mute']};text-decoration:underline">Se désinscrire</a>.
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
        lines.append(f"  Ça m'intéresse : {v['_links']['like']}")
        lines.append(f"  Pas pour moi : {v['_links']['pass']}")
        if v["_links"].get("visite"):
            lines.append(f"  Réserver une visite : {v['_links']['visite']}")
        lines.append("")
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

    def _links_for_bien(self, envoi_id: str, bien_id: Any, annonce_id: int) -> dict[str, str]:
        secret = getattr(self.settings, "email_tracking_secret", None) or self.settings.supabase_service_role_key
        base = self._track_base()
        like = email_tokens.make_feedback_token(envoi_id=envoi_id, bien_id=bien_id, action=email_tokens.ACTION_LIKE, secret=secret)
        passt = email_tokens.make_feedback_token(envoi_id=envoi_id, bien_id=bien_id, action=email_tokens.ACTION_PASS, secret=secret)
        links = {
            "like": f"{base}/r/feedback/{like}" if base else f"#like-{bien_id}",
            "pass": f"{base}/r/feedback/{passt}" if base else f"#pass-{bien_id}",
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
            view["_links"] = self._links_for_bien(envoi_id, view["dossier_id"], aid)
            biens.append(view)
            # Signature dérivée du premier bien (négociateur du dossier).
            if signature["tel"] is None:
                signature = {
                    "nom": _clean_text(dossier.get("commercial_nom")) or "Votre conseiller Groupe GTI",
                    "agence": _clean_text(dossier.get("agence_nom")) or "Groupe GTI",
                    "tel": None,
                    "email": _clean_text(dossier.get("negociateur_email")) or None,
                }

        crit = criteres or "votre recherche"
        if variante == "push":
            accroche = f"Un bien vient de rentrer et correspond à {crit}. Découvrez-le ci-dessous et dites-nous s'il vous plaît :"
            subject = "Un nouveau bien correspond à votre recherche"
        else:
            accroche = f"Voici une sélection de biens pour {crit}. Indiquez-nous ceux qui vous plaisent :"
            subject = "Une sélection de biens pour votre recherche"
        if len(biens) > 1:
            subject = f"{len(biens)} biens pour votre recherche" if variante == "pull" else subject

        # Relances : objet différent (no_open) ou angle plus doux (soft) — chaque relance apporte qqch.
        if relance_type == "no_open":
            subject = "Toujours à la recherche d'un bien ? Une proposition pour vous"
            accroche = f"Nous pensons à {crit} : voici (à nouveau) un bien qui pourrait vous plaire."
        elif relance_type == "soft":
            subject = "Ce bien est toujours disponible — un mot de votre conseiller"
            accroche = f"Petit rappel concernant {crit}. Ce bien est toujours disponible ; dites-nous ce que vous en pensez :"

        greeting_name = " ".join(p for p in (civilite, prenom) if p) or "Bonjour"
        greeting = f"Bonjour {prenom}," if (prenom and not civilite) else (f"{greeting_name}," if greeting_name != "Bonjour" else "Bonjour,")

        secret = getattr(self.settings, "email_tracking_secret", None) or self.settings.supabase_service_role_key
        base = self._track_base()
        ctx = {
            "subject": subject,
            "preheader": accroche,
            "greeting": greeting,
            "intro": (custom_intro or "").strip() or None,  # mot libre du négociateur (hybride)
            "accroche": accroche,
            "biens": biens,
            "signature": signature,
            "pixel_url": f"{base}/r/o/{email_tokens.make_open_token(envoi_id=envoi_id, secret=secret)}.png" if base else None,
            "unsubscribe_url": f"{base}/r/u/{email_tokens.make_unsub_token(envoi_id=envoi_id, secret=secret)}" if base else None,
        }
        return {"subject": subject, "html": build_email_html(ctx), "text": build_email_text(ctx)}
