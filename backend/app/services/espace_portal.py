"""Portail espace client (refonte design 2026-06) — rendu fidèle à la maquette validée.

ADDITIF : ce module ne remplace pas `espace_client._render` tant qu'on ne l'a pas branché.
Il produit le HTML du portail (nav + onglets + bien vedette + sélection + écartés + recherche
+ visites + overlay détail + modale de refus), avec NOS vraies fonctions :
- ❤️ coup de cœur / ✕ écarter + raison  -> POST /espace/{token}/feedback (tracking existant)
- Affiner ma recherche                   -> POST /espace/{token}/recherche (écriture Hektor)
- Visite                                 -> VRAI lien RDV Google Workspace (jamais de faux calendrier)
- Matterport 360°                        -> lien réel du payload, masqué si absent
- DPE/GES                                -> vignettes images (dpe_image_url / ges_image_url)
- Espace unifié par contact, bien vedette = bien de l'email ouvert.
Pas de messagerie (retirée), pas d'anneau de score (remplacé par pastilles « Pourquoi ce bien »).
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

_CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "espace_portal.css"


def _css() -> str:
    try:
        return _CSS_PATH.read_text(encoding="utf-8")
    except Exception:
        return ""


def _e(v: Any) -> str:
    return html.escape("" if v is None else str(v))


# ── Icônes (reprises de la maquette) ─────────────────────────────────────────
IC = {
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.2-3.2"></path></svg>',
    "grid": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1.5"></rect><rect x="14" y="3" width="7" height="7" rx="1.5"></rect><rect x="3" y="14" width="7" height="7" rx="1.5"></rect><rect x="14" y="14" width="7" height="7" rx="1.5"></rect></svg>',
    "heart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M19 14c1.5-1.5 3-3.3 3-5.5A4.5 4.5 0 0 0 12 6 4.5 4.5 0 0 0 2 8.5C2 12 5 14 12 21c2.6-2.6 4.7-4.6 6-6z"></path></svg>',
    "cal": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"></rect><path d="M16 2v4M8 2v4M3 10h18"></path></svg>',
    "x": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M18 6 6 18M6 6l12 12" stroke-linecap="round"></path></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>',
    "chev": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="m9 6 6 6-6 6" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
    "prev": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="m15 6-6 6 6 6" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
    "next": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="m9 6 6 6-6 6" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
    "cam": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><path d="m21 15-5-5L5 21"></path></svg>',
    "visite": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="4" width="18" height="18" rx="2.5"></rect><path d="M3 9h18M8 2v4M16 2v4" stroke-linecap="round"></path></svg>',
    "nope": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M17 2v11M22 11V4a1 1 0 0 0-1-1h-4v10h4a1 1 0 0 0 1-1z"></path><path d="M17 13l-4.5 8.5a2 2 0 0 1-2.8-2.6L11 13H5.5a2 2 0 0 1-2-2.4l1.4-7A2 2 0 0 1 7 3h10" stroke-linejoin="round"></path></svg>',
    "globe": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M12 2a10 10 0 1 0 0 20"></path><path d="M12 2c-3 3-4.5 6-4.5 10s1.5 7 4.5 10M12 2c3 3 4.5 6 4.5 10S15 19 12 22M2.5 9h19M2.5 15h19"></path></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" style="width:13px;height:13px"><path d="M5 12.5 10 17 19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
    "edit": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>',
    "restore": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4" stroke-linecap="round" stroke-linejoin="round"></path></svg>',
    "tel": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07A19.5 19.5 0 0 1 2.1 9.82 2 2 0 0 1 4.11 7.6h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 15.16a16 16 0 0 0 5.93 5.93l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="2" y="5" width="20" height="14" rx="2"></rect><path d="m2 8 10 6 10-6"></path></svg>',
}


def _feat_gallery(v: dict[str, Any]) -> str:
    photos = [p for p in (v.get("photos") or []) if p][:8] or [""]
    n = len(photos)
    slides = "".join(f'<div class="gal-slide"><img src="{_e(p)}" alt="{_e(v.get("title"))}" loading="lazy"></div>' for p in photos)
    dots = "".join(f'<span class="gd{" on" if i == 0 else ""}"></span>' for i in range(n))
    nav = (f'<button class="gal-nav prev" type="button" aria-label="Précédente">{IC["prev"]}</button>'
           f'<button class="gal-nav next" type="button" aria-label="Suivante">{IC["next"]}</button>'
           f'<span class="gal-count">{IC["cam"]}<span class="gc-cur">1</span>/{n}</span>'
           f'<div class="gal-dots">{dots}</div>') if n > 1 else ""
    return f'<div class="gal"><div class="gal-track">{slides}</div>{nav}</div>'


def _pc_gallery(v: dict[str, Any]) -> str:
    photos = [p for p in (v.get("photos") or []) if p][:6] or [""]
    n = len(photos)
    slides = "".join(f'<div class="pcg-s"><img src="{_e(p)}" alt="" loading="lazy"></div>' for p in photos)
    dots = "".join(f'<span class="pcgd{" on" if i == 0 else ""}"></span>' for i in range(n)) if n > 1 else ""
    return f'<div class="pcg"><div class="pcg-track">{slides}</div><div class="pcg-dots">{dots}</div></div>'


def _pourquoi(v: dict[str, Any]) -> str:
    """Pastilles « Pourquoi ce bien » (remplace l'anneau de score) : critères respectés."""
    items = v.get("pourquoi") or []
    if not items:
        return ""
    chips = "".join(f'<span class="pq">{IC["check"]}{_e(t)}</span>' for t in items)
    return f'<div class="pqwrap">{chips}</div>'


def _specs_html(v: dict[str, Any]) -> str:
    spi = {
        "Habitable": '<path d="M4 20h16M6 20V10l6-4.5 6 4.5v10"></path>',
        "Pièces": '<rect x="3" y="9" width="18" height="11" rx="1"></rect><path d="M3 13h18M7 9V6h10v3"></path>',
        "Chambres": '<path d="M3 18v-5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v5M3 18h18"></path>',
        "Terrain": '<path d="M12 2 4 7v13h16V7z"></path>',
        "Terrasse": '<path d="M3 20h18M5 20v-8h14v8M5 12l7-5 7 5"></path>',
    }
    out = []
    for val, lbl in (v.get("specs") or []):
        ic = spi.get(lbl, spi["Habitable"])
        out.append(f'<span class="spec"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">{ic}</svg>{_e(val)}</span>')
    return "".join(out)


def _featured(v: dict[str, Any]) -> str:
    if not v:
        return ""
    nego = v.get("nego") or {}
    mport = (f'<div class="feat-en"><a class="ep-360" data-360="{_e(v.get("matterport"))}" target="_blank" '
             f'href="{_e(v.get("matterport"))}"><span class="e360-ic">{IC["globe"]}</span>Visite virtuelle 360°'
             f'<svg class="e360-arr" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">'
             f'<path d="m9 6 6 6-6 6" stroke-linecap="round" stroke-linejoin="round"></path></svg></a></div>'
             ) if v.get("matterport") else ""
    k = _e(v.get("key"))
    label = _match_label(v.get("pourquoi"))
    score = (f'<div class="feat-score"><span class="st"><small>Correspondance</small>'
             f'<span>{_e(label)}</span></span></div>') if label else ""
    return f"""
    <article class="feat" data-card="{k}" data-envoi="{_e(v.get('envoi_id'))}">
      <div class="feat-media">
        {score}
        <button class="feat-fav" data-fav="{k}" aria-label="Coup de cœur">♡</button>
        {_feat_gallery(v)}
      </div>
      <div class="feat-body">
        <div class="feat-loc">{IC['pin']}{_e(v.get('loc'))}</div>
        <div class="feat-title disp">{_e(v.get('title'))}</div>
        <div class="feat-priceline"><span class="feat-price">{_e(v.get('price'))}</span><span class="feat-fai">FAI</span></div>
        <div class="feat-specs">{_specs_html(v)}</div>
        {mport}
        <div class="feat-adv"><span class="fa-av">{_e(nego.get('initials'))}</span><div class="fa-i"><div class="fa-n">{_e(nego.get('name'))}</div><div class="fa-g">Votre conseiller · {_e(nego.get('agence'))}</div></div></div>
        <div class="pc-actions feat-actions">
          <button class="pca cta" data-detail="{k}">+ Détail</button>
          <button class="pca-ic" data-visite="{k}" title="Planifier une visite">{IC['visite']}</button>
          <button class="pca-ic fav" data-cfav="{k}" title="Coup de cœur">{IC['heart']}</button>
          <button class="pca-ic nope" data-nope="{k}" title="Pas pour moi">{IC['nope']}</button>
        </div>
      </div>
    </article>"""


def _card(v: dict[str, Any]) -> str:
    nego = v.get("nego") or {}
    k = _e(v.get("key"))
    badge = f'<span class="pc-badge">{_e(v.get("badge"))}</span>' if v.get("badge") else ""
    specs = '<span>·</span>'.join(f'<span>{_e(s[0])}</span>' for s in (v.get("specs") or [])[:3])
    return f"""
      <article class="pc" data-card="{k}" data-envoi="{_e(v.get('envoi_id'))}">
        <div class="pc-media">{badge}<button class="pc-fav" data-fav="{k}" aria-label="Coup de cœur">♡</button>
          <button class="pc-nope" data-nope="{k}" title="Pas pour moi">{IC['x']}</button>{_pc_gallery(v)}</div>
        <div class="pc-body">
          <div class="pc-loc">{_e(v.get('loc'))}</div>
          <div class="pc-title">{_e(v.get('title'))}</div>
          <div class="pc-specs">{specs}</div>
          <div class="pc-adv"><span class="pca-av">{_e(nego.get('initials'))}</span><span class="pca-n">{_e(nego.get('name'))}</span></div>
          <div class="pc-foot"><div class="pc-price">{_e(v.get('price'))}</div></div>
          <div class="pc-actions"><button class="pca cta" data-detail="{k}">+ Détail</button>
            <button class="pca-ic" data-visite="{k}" title="Visiter">{IC['visite']}</button>
            <button class="pca-ic fav" data-cfav="{k}" title="Coup de cœur">{IC['heart']}</button>
            <button class="pca-ic nope" data-nope="{k}" title="Pas pour moi">{IC['nope']}</button></div>
        </div>
      </article>"""


def _stats(s: dict[str, Any]) -> str:
    cells = [("proposes", "biens proposés", False), ("favoris", "coups de cœur", True),
             ("visites", "visites", False), ("ecartes", "écartés", False)]
    out = []
    for key, lbl, dark in cells:
        out.append(f'<div class="stat{" dark" if dark else ""}"><div class="v">{_e(s.get(key, 0))}</div><div class="l">{lbl}</div></div>')
    return f'<div class="stats">{"".join(out)}</div>'


def _match_label(pourquoi: list) -> str:
    n = len(pourquoi or [])
    if n >= 4:
        return "Coup de cœur probable"
    if n >= 2:
        return "Belle correspondance"
    if n >= 1:
        return "Correspond à votre recherche"
    return ""


def _ecartes_teaser(n: int) -> str:
    if n:
        title = f"{n} bien{'s' if n > 1 else ''} écarté{'s' if n > 1 else ''}"
        txt = "Vous les avez retirés de votre sélection. Consultez-les ou restaurez-les à tout moment."
    else:
        title = "Aucun bien écarté"
        txt = "Quand un bien ne vous convient pas, dites-le-nous : il rejoint vos écartés et affine nos propositions."
    return (f'<article class="invite" id="ecTeaser"><span class="ic">{IC["x"]}</span>'
            f'<h3 class="disp" id="ecTeaserTitle">{title}</h3>'
            f'<p id="ecTeaserTxt">{txt}</p>'
            '<button data-goto="ecartes">Voir mes écartés</button></article>')


# Image marketing du bloc estimation (photo réelle GTI, charge bien). Surchargée si besoin.
ESTIMATION_IMG = ("https://groupe-gti-immobilier.staticlbi.com/original/images/biens/16/"
                  "cbce175a4551d953a821702103579263/ee28aa8451ea7d0c6c35f278760f3fbd.jpg")


def _estimation_block(img: str | None = None) -> str:
    pts = "".join(f'<li>{IC["check"]}{t}</li>' for t in
                  ["Rapport détaillé sous 48 h", "Prix de marché actualisé", "Accompagnement de A à Z"])
    return (
        '<div class="adslot">'
        f'<div class="adslot-media"><img src="{_e(img or ESTIMATION_IMG)}" alt="" '
        'style="width:100%;height:100%;object-fit:cover;display:block"><div class="adslot-shade"></div></div>'
        '<div class="adslot-body">'
        f'<span class="adslot-tag">{IC["check"]}100% gratuit · sans engagement</span>'
        '<h3 class="disp">Connaissez la vraie valeur de votre bien</h3>'
        '<p>Votre conseiller GTI réalise une estimation <b>gratuite et sans engagement</b>, '
        'fondée sur les ventes réelles de votre secteur.</p>'
        f'<ul class="adslot-pts">{pts}</ul>'
        '<div class="adslot-cta"><a class="adslot-btn" href="mailto:accueil@gti-immobilier.fr?subject=Estimation%20de%20mon%20bien">'
        'Estimer mon bien gratuitement</a></div></div></div>'
    )


def _search_chips(chips: list) -> str:
    out = ['<span class="cb-lead">Ma recherche</span>']
    for label, val in chips:
        out.append(f'<span class="sd-chip">{_e(label)} <b>{_e(val)}</b></span>')
    return "".join(out)


def _search_form(f: dict[str, Any]) -> str:
    def num(lbl, fid, val):
        return f'<label class="sdf">{lbl}<input type="number" id="{fid}" value="{_e(val) if val else ""}"></label>'
    return (
        '<div class="sdf-grid">'
        + num("Budget min (€)", "f-pmin", f.get("priceMin"))
        + num("Budget max (€)", "f-pmax", f.get("priceMax"))
        + num("Surface min (m²)", "f-surf", f.get("surfaceMin"))
        + num("Pièces min", "f-rooms", f.get("rooms"))
        + num("Chambres min", "f-bed", f.get("bedrooms"))
        + '</div>'
        '<div class="sdf-row"><button class="sdf-save" id="dockSave">Mettre à jour</button>'
        '<button class="sdf-cancel" id="dockCancel">Annuler</button>'
        f'<span class="sdf-ack" id="dockAck">{IC["check"]}Recherche mise à jour · conseiller informé</span></div>'
    )


def _visites(visites: list) -> str:
    if not visites:
        return '<div class="ec-empty">Aucune visite planifiée pour le moment. Sur un bien qui vous plaît, cliquez « Visiter ».</div>'
    rows = []
    for vi in visites:
        st = vi.get("status") or "wait"
        rows.append(
            f'<div class="vrow"><div class="vdate"><div class="d">{_e(vi.get("d"))}</div><div class="m">{_e(vi.get("m"))}</div></div>'
            f'<div class="vmeta"><div class="t">{_e(vi.get("title"))}</div><div class="s">{IC["pin"]}{_e(vi.get("loc"))} · {_e(vi.get("when"))}</div></div>'
            f'<span class="vstatus {"ok" if st == "ok" else "wait"}">{_e(vi.get("status_label"))}</span></div>')
    return f'<div class="card">{"".join(rows)}</div>'


def _bien_data(v: dict[str, Any]) -> dict[str, Any]:
    """Données pour l'overlay détail (consommées côté JS)."""
    nego = v.get("nego") or {}
    return {
        "ref": v.get("ref"), "statut": v.get("statut") or "Disponible", "loc": v.get("loc"),
        "title": v.get("title"), "price": v.get("price"), "ppm": v.get("ppm") or "",
        "photos": [p for p in (v.get("photos") or []) if p][:8],
        "specs": v.get("specs") or [], "honos": v.get("honos") or "",
        "matterport": v.get("matterport") or "", "dpe_img": v.get("dpe_img") or "", "ges_img": v.get("ges_img") or "",
        "desc": v.get("desc") or "", "details": v.get("details") or [], "feats": v.get("feats") or [],
        "fin": v.get("fin") or [], "rdv": v.get("rdv_url") or "", "pourquoi": v.get("pourquoi") or [],
        "nego": {"i": nego.get("initials"), "n": nego.get("name"), "a": nego.get("agence"),
                 "tel": nego.get("tel") or "", "mail": nego.get("email") or ""},
    }


def render_portal(ctx: dict[str, Any], *, token: str, base: str, from_email: bool = False) -> str:
    base = (base or "").rstrip("/")
    tok = html.escape(token)
    post_fb = f"{base}/espace/{tok}/feedback"
    post_re = f"{base}/espace/{tok}/recherche"
    post_vi = f"{base}/espace/{tok}/visite"

    client = ctx.get("client") or {}
    featured = ctx.get("featured")
    selection = ctx.get("selection") or []
    ecartes = ctx.get("ecartes") or []
    visites = ctx.get("visites") or []
    stats = ctx.get("stats") or {}

    # Compteurs nav
    n_sel = (1 if featured else 0) + len(selection)
    n_fav = sum(1 for v in [featured, *selection] if v and v.get("feedback") == "interesse")

    selection_html = "".join(_card(v) for v in selection) or \
        '<div class="ec-empty">Aucun autre bien pour le moment — votre conseiller vous en envoie dès qu\'il en trouve.</div>'

    # Données overlay : tous les biens (vedette + sélection + écartés)
    data_map = {}
    favs = []
    for v in [featured, *selection, *ecartes]:
        if v and v.get("key") is not None:
            data_map[str(v["key"])] = _bien_data(v)
            if v.get("feedback") == "interesse":
                favs.append(str(v["key"]))

    nav = f"""
  <nav class="nav">
    <div class="logo"><span class="mk"><img src="{base}/assets/gti-brand-mark.png" alt="GTI" style="width:22px;height:22px;object-fit:contain;filter:brightness(0) invert(1)"></span></div>
    <div class="nlinks">
      <a class="nlink" data-tab="recherche">{IC['search']}Mon projet</a>
      <a class="nlink active" data-tab="biens">{IC['grid']}Ma sélection<span class="ct">{n_sel}</span></a>
      <a class="nlink" data-tab="favoris">{IC['heart']}Coups de cœur<span class="ct">{n_fav}</span></a>
      <a class="nlink" data-tab="visites">{IC['cal']}Mes rendez-vous<span class="ct">{len(visites)}</span></a>
      <a class="nlink" data-tab="ecartes">{IC['x']}Écartés<span class="ct" id="ecCount">{len(ecartes)}</span></a>
    </div>
    <div class="nspace"></div>
    <div class="nav-prof"><div class="np-i"><div class="np-n">{_e(client.get('name'))}</div><div class="np-r">{_e(client.get('email'))}</div></div><span class="nav-av">{_e(client.get('initials'))}</span></div>
  </nav>"""

    panel_biens = f"""
    <section class="panel active" data-panel="biens">
      <div class="pagetop"></div>
      <div class="clientbar" id="dock">
        <div class="cb-head">
          <div class="cb-crit">{_search_chips(ctx.get('search_chips') or [])}</div>
          <button class="sd-btn" id="dockEdit">{IC['edit']}Affiner ma recherche</button>
        </div>
        <div class="sd-form" id="dockForm">{_search_form(ctx.get('search_fields') or {})}</div>
      </div>
      <div class="sectitle"><div><h2 class="disp">Votre bien à la une</h2></div></div>
      {_featured(featured)}
      <div class="sectitle"><div><h2 class="disp">Aussi pour vous</h2></div><a class="link" data-goto="recherche">Voir mes critères{IC['chev']}</a></div>
      <div class="grid">{selection_html}{_ecartes_teaser(len(ecartes))}</div>
      <div class="promos">{_estimation_block()}</div>
    </section>"""

    panel_favoris = f"""
    <section class="panel" data-panel="favoris">
      <div class="sectitle"><div><div class="eyebrow">Vos coups de cœur ❤</div><h2 class="disp">Les biens qui vous plaisent</h2></div></div>
      <div class="grid" id="favGrid"></div>
      <div class="ec-empty" id="favEmpty">Cliquez sur le ❤ d'un bien : il apparaîtra ici, et votre conseiller est prévenu.</div>
    </section>"""

    panel_visites = f"""
    <section class="panel" data-panel="visites">
      <div class="sectitle"><div><div class="eyebrow">Vos rendez-vous</div><h2 class="disp">Mes visites</h2></div></div>
      {_visites(visites)}
    </section>"""

    panel_ecartes = f"""
    <section class="panel" data-panel="ecartes">
      <div class="sectitle"><div><div class="eyebrow">Déjà vus ensemble</div><h2 class="disp" id="ecTeaserTitle">Vos biens écartés</h2><div class="sub" id="ecTeaserTxt">Vous les avez retirés de votre sélection. Restaurez-les à tout moment.</div></div></div>
      <div class="grid" id="ecGrid">{"".join(_ecarte_row(v) for v in ecartes)}</div>
      <div class="ec-empty" id="ecEmpty" style="{'display:none' if ecartes else ''}">Aucun bien écarté.</div>
    </section>"""

    panel_recherche = f"""
    <section class="panel" data-panel="recherche" id="affiner">
      <div class="sectitle"><div><div class="eyebrow">Votre projet</div><h2 class="disp">Ma recherche</h2><div class="sub">Ajustez vos critères — vos prochaines propositions collent mieux, et votre conseiller est prévenu.</div></div></div>
      <div class="rech">
        {_search_form(ctx.get('search_fields') or {}).replace('dockSave', 'rechSave').replace('dockCancel', 'rechCancel').replace('dockAck', 'rechAck').replace('sdf-grid', 'fields').replace('class="sdf"', 'class="fld"')}
      </div>
    </section>"""

    body = f"""{nav}
  <div class="wrap">
    {panel_biens}
    {panel_recherche}
    {panel_favoris}
    {panel_visites}
    {panel_ecartes}
  </div>
  <div class="ov" id="ov"><div class="ov-bg" data-close></div><div class="ov-sheet" id="ovSheet"></div></div>
  <div class="rm" id="rm"><div class="rm-bg" data-rmclose></div>
    <div class="rm-card"><h3>Qu'est-ce qui ne va pas&nbsp;?</h3><p>Dites-le-nous : ce bien rejoint vos écartés et on affine les prochains.</p>
      <div class="rm-opts">
        <button class="rm-opt" data-reason="trop_cher">{IC['nope']}Trop cher</button>
        <button class="rm-opt" data-reason="secteur">{IC['pin']}Mauvais secteur</button>
        <button class="rm-opt" data-reason="trop_petit">{IC['grid']}Trop petit</button>
        <button class="rm-opt" data-reason="autre">{IC['x']}Autre raison</button>
      </div>
      <button class="rm-cancel" data-rmclose>Annuler</button>
    </div>
  </div>
  <div class="rm vm" id="vm"><div class="rm-bg" data-vmclose></div>
    <div class="rm-card vm-card">
      <button class="vm-x" data-vmclose aria-label="Fermer">✕</button>
      <div class="vm-eyebrow">{IC['cal']}<span>Demande de visite</span></div>
      <h3 id="vm-bien">Organiser une visite</h3>
      <p class="vm-loc" id="vm-loc"></p>
      <div class="vm-lbl">Quels jours vous arrangent&nbsp;?</div>
      <div class="vm-days" id="vm-days"></div>
      <div class="vm-lbl">À quel moment&nbsp;?</div>
      <div class="vm-chips">
        <button class="vm-chip" data-period="Matin">Matin</button>
        <button class="vm-chip" data-period="Après-midi">Après-midi</button>
        <button class="vm-chip" data-period="Fin de journée">Fin de journée</button>
      </div>
      <input class="vm-phone" id="vm-phone" type="tel" inputmode="tel" placeholder="Votre téléphone (pour être rappelé)">
      <textarea class="vm-msg" id="vm-msg" placeholder="Un mot pour votre conseiller (facultatif)…"></textarea>
      <button class="vm-send" id="vm-send">Envoyer ma demande de visite</button>
      <div class="vm-ack" id="vm-ack" hidden></div>
    </div>
  </div>
  <nav class="mobnav">
    <a data-tab="biens" class="active">{IC['grid']}<span>Sélection</span></a>
    <a data-tab="favoris">{IC['heart']}<span>Cœur</span></a>
    <a data-tab="visites">{IC['cal']}<span>RDV</span></a>
    <a data-tab="recherche">{IC['search']}<span>Projet</span></a>
  </nav>"""

    js = _PORTAL_JS.replace("__POST_FB__", json.dumps(post_fb)) \
                   .replace("__POST_RE__", json.dumps(post_re)) \
                   .replace("__POST_VI__", json.dumps(post_vi)) \
                   .replace("__DATA__", json.dumps(data_map, ensure_ascii=False)) \
                   .replace("__FAVS__", json.dumps(favs)) \
                   .replace("__FROM_EMAIL__", "true" if from_email else "false")

    return f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mon espace acquéreur · Groupe GTI</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
{_css()}
/* ── Ajouts refonte : pastilles « Pourquoi ce bien » + vignettes DPE ── */
.pqwrap{{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}}
.pq{{display:inline-flex;align-items:center;gap:5px;background:#e8f6ef;color:var(--green);border-radius:9px;padding:5px 10px;font-size:12px;font-weight:700}}
.pq svg{{color:var(--green)}}
.ov-dpe{{display:flex;gap:12px;flex-wrap:wrap}} .ov-dpe a{{display:block;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fff}} .ov-dpe img{{height:120px;width:auto;display:block}}
.eyebrow{{font-size:11.5px;font-weight:800;letter-spacing:.4px;color:var(--accent-d);margin-bottom:6px;text-transform:uppercase}}
/* ── Modale demande de visite ── */
.vm .rm-card{{max-width:460px;text-align:left}}
.vm-x{{position:absolute;top:14px;right:14px;width:32px;height:32px;border-radius:50%;border:1px solid var(--line);background:var(--surface);color:var(--mute);font-size:14px}}
.vm-eyebrow{{display:inline-flex;align-items:center;gap:7px;background:var(--accent-soft);color:var(--accent-d);font-size:11px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;padding:6px 11px;border-radius:20px;margin-bottom:12px}}
.vm-eyebrow svg{{width:15px;height:15px}}
.vm-card h3{{font-family:'Fraunces',serif;font-weight:600;font-size:21px;line-height:1.2}}
.vm-loc{{font-size:13px;color:var(--mute);margin:4px 0 6px}}
.vm-lbl{{font-size:12.5px;font-weight:700;color:var(--ink);margin:16px 0 8px}}
.vm-days{{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;scrollbar-width:none}} .vm-days::-webkit-scrollbar{{display:none}}
.vm-day{{flex:none;min-width:58px;border:1.5px solid var(--line);border-radius:13px;padding:9px 6px;text-align:center;cursor:pointer;transition:.13s;background:var(--surface)}}
.vm-day:hover{{border-color:var(--accent)}} .vm-day.on{{background:var(--accent);border-color:var(--accent);color:#fff}}
.vm-day .dd{{font-size:10.5px;font-weight:700;text-transform:uppercase;opacity:.75}} .vm-day .dn{{font-size:18px;font-weight:800;margin-top:1px}} .vm-day .dm{{font-size:10px;opacity:.75}}
.vm-chips{{display:flex;gap:8px;flex-wrap:wrap}}
.vm-chip{{border:1.5px solid var(--line);background:var(--surface);color:var(--ink);border-radius:11px;padding:9px 15px;font-size:13.5px;font-weight:600;cursor:pointer;transition:.13s}}
.vm-chip:hover{{border-color:var(--accent)}} .vm-chip.on{{background:var(--accent);border-color:var(--accent);color:#fff}}
.vm-phone,.vm-msg{{width:100%;margin-top:14px;padding:12px 14px;border:1.5px solid var(--line);border-radius:12px;font-size:14.5px;font-family:inherit;color:var(--ink);background:var(--surface)}}
.vm-phone:focus,.vm-msg:focus{{outline:none;border-color:var(--accent)}} .vm-msg{{min-height:70px;resize:vertical}}
.vm-send{{width:100%;margin-top:16px;background:var(--accent);color:#fff;border-radius:13px;padding:14px;font-size:14.5px;font-weight:700;box-shadow:0 10px 24px -12px rgba(197,0,95,.8)}}
.vm-send:hover{{background:var(--accent-d)}} .vm-send:disabled{{opacity:.6}}
.vm-ack{{margin-top:14px;font-size:14px;color:var(--green);font-weight:700;text-align:center;line-height:1.5}}
</style>
</head>
<body>
{body}
<script>
{js}
</script>
</body></html>"""


def _ecarte_row(v: dict[str, Any]) -> str:
    k = _e(v.get("key"))
    photos = [p for p in (v.get("photos") or []) if p]
    img = f'<img src="{_e(photos[0])}" alt="" style="filter:grayscale(.4) brightness(.96)">' if photos else ""
    specs = " · ".join(_e(s[0]) for s in (v.get("specs") or [])[:3])
    reason = v.get("feedback_reason") or "écarté"
    return (f'<article class="pc" data-ecarte="{k}"><div class="pc-media"><span class="pc-badge">Écarté · {_e(reason)}</span>{img}</div>'
            f'<div class="pc-body"><div class="pc-loc">{_e(v.get("loc"))}</div><div class="pc-title">{_e(v.get("title"))}</div>'
            f'<div class="pc-specs">{specs}</div><div class="pc-foot"><div class="pc-price">{_e(v.get("price"))}</div>'
            f'<button class="pc-cta" data-restore="{k}" data-envoi="{_e(v.get("envoi_id"))}">{IC["restore"]}Restaurer</button></div></div></article>')


_PORTAL_JS = r"""
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
const POST_FB=__POST_FB__, POST_RE=__POST_RE__, POST_VI=__POST_VI__, DATA=__DATA__;
async function postFb(b){try{await fetch(POST_FB,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});}catch(e){}}

/* ── Onglets ── */
function show(t){
  $$('.panel').forEach(p=>p.classList.toggle('active',p.dataset.panel===t));
  $$('.nlink').forEach(l=>l.classList.toggle('active',l.dataset.tab===t));
  $$('.mobnav a').forEach(l=>l.classList.toggle('active',l.dataset.tab===t));
  if(t==='favoris')renderFav();
  window.scrollTo({top:0,behavior:'smooth'});
}
document.addEventListener('click',e=>{const t=e.target.closest('[data-tab],[data-goto]');if(t&&(t.dataset.tab||t.dataset.goto)){e.preventDefault();show(t.dataset.tab||t.dataset.goto);}});

/* ── Galeries scroll-snap (feat / cartes / overlay) ── */
function bindGal(root,trackSel,dotSel,curSel){
  root.querySelectorAll(trackSel).forEach(tr=>{
    const wrap=tr.closest('.gal,.pcg,.ovg'); if(!wrap)return;
    const dots=wrap.querySelectorAll(dotSel), cur=curSel?wrap.querySelector(curSel):null;
    const ix=()=>Math.round(tr.scrollLeft/tr.clientWidth);
    const sy=()=>{const i=ix();if(cur)cur.textContent=i+1;dots.forEach((d,k)=>d.classList.toggle('on',k===i));};
    tr.addEventListener('scroll',()=>requestAnimationFrame(sy),{passive:true});
    const go=d=>tr.scrollTo({left:Math.max(0,Math.min(tr.children.length-1,ix()+d))*tr.clientWidth,behavior:'smooth'});
    const p=wrap.querySelector('.prev'),nx=wrap.querySelector('.next');
    if(p)p.addEventListener('click',ev=>{ev.stopPropagation();go(-1);});
    if(nx)nx.addEventListener('click',ev=>{ev.stopPropagation();go(1);});
    dots.forEach((d,k)=>d.addEventListener('click',()=>tr.scrollTo({left:k*tr.clientWidth,behavior:'smooth'})));
  });
}
function initGals(root){bindGal(root,'.gal-track','.gd','.gc-cur');bindGal(root,'.pcg-track','.pcgd',null);bindGal(root,'.ovg-track','.ovgd','.ovgc');}
initGals(document);

/* ── Affiner ma recherche ── */
function wireSave(saveId,ackId){const s=document.getElementById(saveId);if(!s)return;s.addEventListener('click',async()=>{
  const g=id=>{const el=document.getElementById(id);return el?el.value:'';};
  const body={priceMin:g('f-pmin'),priceMax:g('f-pmax'),surfaceMin:g('f-surf'),rooms:g('f-rooms'),bedrooms:g('f-bed')};
  const a=document.getElementById(ackId);if(a)a.classList.add('show');
  try{await fetch(POST_RE,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});}catch(e){}});}
const de=$('#dockEdit'); if(de)de.addEventListener('click',()=>$('#dockForm').classList.toggle('open'));
const dc=$('#dockCancel'); if(dc)dc.addEventListener('click',()=>$('#dockForm').classList.remove('open'));
wireSave('dockSave','dockAck'); wireSave('rechSave','rechAck');

/* ── Coups de cœur (= like) ── */
const favs=new Set(__FAVS__);
function envoiOf(el){const c=el.closest('[data-card]');return c?c.dataset.envoi:'';}
function syncFav(){
  $$('[data-fav],[data-cfav],[data-ovfav]').forEach(el=>{
    const k=el.dataset.fav||el.dataset.cfav||el.dataset.ovfav;const on=favs.has(k);
    el.classList.toggle('on',on);
    if(el.classList.contains('pc-fav')||el.classList.contains('feat-fav'))el.textContent=on?'♥':'♡';
  });
  const b=$('[data-tab="favoris"] .ct');if(b)b.textContent=favs.size;
}
function toggleFav(k,envoi){if(favs.has(k)){favs.delete(k);}else{favs.add(k);postFb({action:'like',bien_id:k,envoi_id:envoi});}syncFav();}
document.addEventListener('click',e=>{const f=e.target.closest('[data-fav],[data-cfav]');if(f){toggleFav(f.dataset.fav||f.dataset.cfav,envoiOf(f));}});
function favCard(k){
  const b=DATA[k];if(!b)return'';const ph=(b.photos&&b.photos[0])||'';
  return `<article class="pc" data-card="${k}"><div class="pc-media">`
    +`<button class="pc-fav on" data-fav="${k}" aria-label="Coup de cœur">♥</button>`
    +`<button class="pc-nope" data-nope="${k}" title="Pas pour moi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M18 6 6 18M6 6l12 12" stroke-linecap="round"/></svg></button>`
    +(ph?`<img src="${ph}" alt="" style="height:190px;width:100%;object-fit:cover">`:'')
    +`</div><div class="pc-body"><div class="pc-loc">${b.loc}</div><div class="pc-title">${b.title}</div>`
    +`<div class="pc-specs">${b.specs.map(s=>s[0]).join(' · ')}</div>`
    +`<div class="pc-foot"><div class="pc-price">${b.price}</div></div>`
    +`<div class="pc-actions"><button class="pca cta" data-detail="${k}">+ Détail</button></div></div></article>`;
}
function renderFav(){
  const grid=$('#favGrid'),empty=$('#favEmpty');if(!grid)return;
  grid.innerHTML=[...favs].map(favCard).join('');
  if(empty)empty.style.display=favs.size?'none':'';
}
syncFav();

/* ── Écarter (✕ -> modale raison -> pass) ── */
const rm=$('#rm');let pend=null,pendEnvoi=null;
document.addEventListener('click',e=>{const n=e.target.closest('[data-nope]');if(n){pend=n.dataset.nope;pendEnvoi=envoiOf(n);rm.classList.add('open');}});
if(rm)rm.addEventListener('click',e=>{
  if(e.target.closest('[data-rmclose]')){rm.classList.remove('open');pend=null;return;}
  const o=e.target.closest('[data-reason]');
  if(o&&pend){rejectBien(pend,o.dataset.reason,pendEnvoi);rm.classList.remove('open');pend=null;}
});
function rejectBien(k,reason,envoi){
  document.querySelectorAll('[data-card="'+k+'"]').forEach(c=>{if(c.classList.contains('feat'))c.style.display='none';else c.classList.add('gone');});
  postFb({action:'pass',bien_id:k,reason:reason,envoi_id:envoi});
  const c=$('#ecCount');if(c)c.textContent=(parseInt(c.textContent||'0')+1);
  closeDetail();
}
document.addEventListener('click',e=>{const r=e.target.closest('[data-restore]');if(r){const k=r.dataset.restore;const card=r.closest('[data-ecarte]');if(card)card.remove();const c=$('#ecCount');if(c)c.textContent=Math.max(0,parseInt(c.textContent||'1')-1);}});

/* ── Overlay détail ── */
const ov=$('#ov'),ovSheet=$('#ovSheet');
const SPI={'Habitable':'<path d="M4 20h16M6 20V10l6-4.5 6 4.5v10"/>','Pièces':'<rect x="3" y="9" width="18" height="11" rx="1"/><path d="M3 13h18M7 9V6h10v3"/>','Chambres':'<path d="M3 18v-5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v5M3 18h18"/>','Terrain':'<path d="M12 2 4 7v13h16V7z"/>','Terrasse':'<path d="M3 20h18M5 20v-8h14v8M5 12l7-5 7 5"/>'};
function openDetail(k){
  const b=DATA[k];if(!b)return;
  const ph=b.photos.length?b.photos:[''];
  const mport=b.matterport?`<a class="ov-360" href="${b.matterport}" target="_blank"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 2a10 10 0 1 0 0 20"/><path d="M12 2c-3 3-4.5 6-4.5 10s1.5 7 4.5 10M12 2c3 3 4.5 6 4.5 10S15 19 12 22M2.5 9h19M2.5 15h19"/></svg><span><b>Visite virtuelle 360°</b><small>Explorez chaque pièce en immersion</small></span></a>`:'';
  const dpe=(b.dpe_img||b.ges_img)?`<div class="ov-sec"><div class="ov-sl">Performance énergétique</div><div class="ov-dpe">${b.dpe_img?`<a href="${b.dpe_img}" target="_blank"><img src="${b.dpe_img}" alt="DPE"></a>`:''}${b.ges_img?`<a href="${b.ges_img}" target="_blank"><img src="${b.ges_img}" alt="GES"></a>`:''}</div></div>`:'';
  const det=b.details.length?`<div class="ov-sec"><div class="ov-sl">Caractéristiques</div><div class="ov-grid">${b.details.map(d=>`<div class="ov-gi"><span class="k">${d[0]}</span><span class="v">${d[1]}</span></div>`).join('')}</div></div>`:'';
  const feats=b.feats.length?`<div class="ov-sec"><div class="ov-sl">Équipements</div><div class="ov-feats">${b.feats.map(f=>`<span class="f">${f}</span>`).join('')}</div></div>`:'';
  const fin=b.fin.length?`<div class="ov-sec"><div class="ov-sl">Informations financières</div><div class="ov-grid">${b.fin.map(d=>`<div class="ov-gi"><span class="k">${d[0]}</span><span class="v">${d[1]}</span></div>`).join('')}</div></div>`:'';
  const visiteBtn=`<button class="ov-cic-btn visite" data-ovvisite="${k}" title="Planifier une visite"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="4" width="18" height="18" rx="2.5"/><path d="M3 9h18M8 2v4M16 2v4" stroke-linecap="round"/></svg><span class="ov-lbl">Visiter</span></button>`;
  const pq=(b.pourquoi&&b.pourquoi.length)?`<div class="ov-sec"><div class="ov-sl">Pourquoi ce bien</div><div style="display:flex;flex-wrap:wrap;gap:7px">${b.pourquoi.map(t=>`<span class="pq"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" style="width:13px;height:13px"><path d="M5 12.5 10 17 19 7" stroke-linecap="round" stroke-linejoin="round"/></svg>${t}</span>`).join('')}</div></div>`:'';
  ovSheet.innerHTML=`<button class="ov-close" data-close>✕</button>
    <div class="ov-hero"><div class="ovg"><div class="ovg-track">${ph.map(p=>`<div class="ovg-s"><img src="${p}" alt=""></div>`).join('')}</div>${ph.length>1?`<button class="ovg-nav prev">‹</button><button class="ovg-nav next">›</button><span class="ovg-count"><span class="ovgc">1</span>/${ph.length}</span><div class="ovg-dots">${ph.map((_,i)=>`<span class="ovgd${i?'':' on'}"></span>`).join('')}</div>`:''}</div><div class="grad"></div>
      <span class="ov-ref">Réf. ${b.ref} · ${b.statut}</span>
      <div class="ov-cap"><div class="loc">${b.loc}</div><div class="ti disp">${b.title}</div><div class="pr">${b.price} <span class="ov-ppm">${b.ppm}</span></div></div></div>
    <div class="ov-body">
      <div class="ov-specs">${b.specs.map(s=>`<span class="s"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">${SPI[s[1]]||SPI['Habitable']}</svg><b>${s[0]}</b>${s[1]}</span>`).join('')}</div>
      <div class="ov-honos">${b.honos}</div>
      ${mport}
      ${pq}
      ${b.desc?`<div class="ov-sec"><div class="ov-sl">Description</div><div class="ov-desc">${b.desc}</div></div>`:''}
      ${det}${feats}${dpe}${fin}
      <div class="ov-adv"><span class="a">${b.nego.i}</span><div class="ov-adv-i"><div class="nm">${b.nego.n}</div><div class="ag">Votre conseiller · ${b.nego.a}</div></div><div class="ov-adv-acts">${b.nego.tel?`<a class="ov-cic" href="tel:${b.nego.tel}" title="Appeler"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07A19.5 19.5 0 0 1 2.1 9.82 2 2 0 0 1 4.11 7.6h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 15.16a16 16 0 0 0 5.93 5.93l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg></a>`:''}${b.nego.mail?`<a class="ov-cic" href="mailto:${b.nego.mail}" title="Écrire"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="m2 8 10 6 10-6"/></svg></a>`:''}</div></div>
      <div class="ov-act">${visiteBtn}
        <button class="ov-cic-btn fav" data-ovfav="${k}" title="Coup de cœur"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M19 14c1.5-1.5 3-3.3 3-5.5A4.5 4.5 0 0 0 12 6 4.5 4.5 0 0 0 2 8.5C2 12 5 14 12 21c2.6-2.6 4.7-4.6 6-6z"/></svg><span class="ov-lbl">Coup de cœur</span></button>
        <button class="ov-cic-btn nope" data-ovnope="${k}" title="Pas pour moi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M17 2v11M22 11V4a1 1 0 0 0-1-1h-4v10h4a1 1 0 0 0 1-1z"/><path d="M17 13l-4.5 8.5a2 2 0 0 1-2.8-2.6L11 13H5.5a2 2 0 0 1-2-2.4l1.4-7A2 2 0 0 1 7 3h10" stroke-linejoin="round"/></svg><span class="ov-lbl">Pas pour moi</span></button>
      </div>
    </div>`;
  ov.classList.add('open');document.body.style.overflow='hidden';initGals(ovSheet);syncFav();
}
function closeDetail(){if(ov){ov.classList.remove('open');document.body.style.overflow='';}}
document.addEventListener('click',e=>{const d=e.target.closest('[data-detail]');if(d)openDetail(d.dataset.detail);});
if(ov)ov.addEventListener('click',e=>{
  if(e.target.closest('[data-close]')||e.target.classList.contains('ov-bg'))closeDetail();
  const f=e.target.closest('[data-ovfav]');if(f)toggleFav(f.dataset.ovfav,'');
  const n=e.target.closest('[data-ovnope]');if(n){pend=n.dataset.ovnope;pendEnvoi='';closeDetail();rm.classList.add('open');}
  const vv=e.target.closest('[data-ovvisite]');if(vv){closeDetail();openVisite(vv.dataset.ovvisite);}
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeDetail();if(rm)rm.classList.remove('open');if(vm)vm.classList.remove('open');}});

/* ── Demande de visite : modale moderne -> POST /visite (cloche + email au négo, JAMAIS la vitrine simulée) ── */
const vm=$('#vm'); let vmKey=null, vmEnvoi=null;
const VM_DJ=['Dim','Lun','Mar','Mer','Jeu','Ven','Sam'], VM_DM=['jan','fév','mar','avr','mai','juin','juil','août','sep','oct','nov','déc'];
function openVisite(k){
  if(!vm)return; vmKey=k; const card=document.querySelector('[data-card="'+k+'"]'); vmEnvoi=card?card.dataset.envoi:'';
  const b=DATA[k]||{};
  const bn=$('#vm-bien'), lo=$('#vm-loc'); if(bn)bn.textContent=b.title||'Organiser une visite'; if(lo)lo.textContent=b.loc||'';
  // Génère les 15 prochains jours (hors aujourd'hui)
  const days=$('#vm-days'); if(days){days.innerHTML='';
    for(let i=1;i<=15;i++){const d=new Date();d.setDate(d.getDate()+i);
      const lab=VM_DJ[d.getDay()]+' '+d.getDate()+' '+VM_DM[d.getMonth()];
      const el=document.createElement('button');el.className='vm-day';el.dataset.day=lab;
      el.innerHTML='<div class="dd">'+VM_DJ[d.getDay()]+'</div><div class="dn">'+d.getDate()+'</div><div class="dm">'+VM_DM[d.getMonth()]+'</div>';
      days.appendChild(el);}}
  vm.querySelectorAll('.vm-chip,.vm-day').forEach(x=>x.classList.remove('on'));
  const ph=$('#vm-phone'),ms=$('#vm-msg'),ak=$('#vm-ack'),sd=$('#vm-send');
  if(ph)ph.value='';if(ms)ms.value='';if(ak){ak.hidden=true;ak.textContent='';}if(sd){sd.disabled=false;sd.textContent='Envoyer ma demande de visite';}
  vm.classList.add('open');
}
if(vm)vm.addEventListener('click',e=>{
  if(e.target.closest('[data-vmclose]')){vm.classList.remove('open');return;}
  const d=e.target.closest('.vm-day'); if(d)d.classList.toggle('on');
  const c=e.target.closest('.vm-chip'); if(c)c.classList.toggle('on');
});
const vmSend=$('#vm-send');
if(vmSend)vmSend.addEventListener('click',async()=>{
  const days=[...vm.querySelectorAll('.vm-day.on')].map(x=>x.dataset.day);
  const periods=[...vm.querySelectorAll('.vm-chip.on')].map(x=>x.dataset.period);
  const phone=($('#vm-phone')||{}).value||'', message=($('#vm-msg')||{}).value||'';
  vmSend.disabled=true; vmSend.textContent='Envoi…';
  try{await fetch(POST_VI,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bien_id:vmKey,envoi_id:vmEnvoi,days,periods,phone,message})});}catch(e){}
  const ak=$('#vm-ack'); if(ak){ak.hidden=false;ak.innerHTML='✓ Demande envoyée&nbsp;! Votre conseiller vous recontacte vite pour fixer le créneau.';}
  vmSend.textContent='Demande envoyée';
  setTimeout(()=>vm.classList.remove('open'),2600);
});
document.addEventListener('click',e=>{const v=e.target.closest('[data-visite]');if(v)openVisite(v.dataset.visite);});

/* ── Arrivée depuis l'email (#affiner) : ouvrir le formulaire + surbrillance ── */
if(__FROM_EMAIL__||location.hash==='#affiner'){
  const f=$('#dockForm');if(f)f.classList.add('open');
  const d=$('#dock');if(d){setTimeout(()=>{d.scrollIntoView({behavior:'smooth',block:'center'});d.style.boxShadow='0 0 0 3px var(--accent)';setTimeout(()=>d.style.boxShadow='',2400);},300);}
}
"""
