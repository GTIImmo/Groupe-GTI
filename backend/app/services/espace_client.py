"""Espace client — Étape 1 (squelette).

Page web publique (sans login), ouverte par un lien magique depuis l'email.
Affiche le(s) bien(s) proposé(s) avec :
- ❤️ « Ça m'intéresse » / ✕ « Pas pour moi » (reliés au tracking existant),
- « Réserver une visite » → le VRAI flux RDV Google Workspace (jamais la vitrine Android),
- le bloc conseiller.

Rendu côté backend (comme les pages de landing), donc isolé : aucun lien avec le
front négociateur ni avec l'export des écrans Android.
Étapes suivantes (non incluses ici) : modifier sa recherche, raison du ✕, messages, swipe.
"""

from __future__ import annotations

import html
import json
from typing import Any

import requests

from ..settings import Settings
from . import contact_search_mapping as CSM
from .email_tracking import EmailTrackingService
from .rapprochement_email import BRAND, FONT_BODY, FONT_DISPLAY, build_bien_view, _esc, _specs_line
from .rapprochement_email import RapprochementEmailService


class EspaceClientService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.tracking = EmailTrackingService(settings)
        self.renderer = RapprochementEmailService(settings)

    def _load_dossier_by_id(self, dossier_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
        rows = self.renderer._rest_get(
            "app_dossier_current",
            {"select": "app_dossier_id,hektor_annonce_id,titre_bien,numero_dossier,numero_mandat,"
                       "ville,code_postal,prix,type_bien,commercial_nom,negociateur_email,agence_nom,"
                       "photo_url_listing,statut_annonce",
             "app_dossier_id": f"eq.{dossier_id}", "limit": "1"},
        )
        if not rows:
            return {}, {}
        dossier = rows[0]
        det = self.renderer._rest_get(
            "app_dossier_detail_current",
            {"select": "detail_payload_json", "app_dossier_id": f"eq.{dossier_id}", "limit": "1"},
        )
        detail: dict[str, Any] = {}
        if det:
            raw = str(det[0].get("detail_payload_json") or "").strip()
            if raw:
                try:
                    parsed = json.loads(raw)
                    detail = parsed if isinstance(parsed, dict) else {}
                except Exception:
                    detail = {}
        return dossier, detail

    def build_context(self, envoi_id: str) -> dict[str, Any] | None:
        envoi = self.tracking._envoi(envoi_id)
        if not envoi:
            return None
        bien_rows = self.tracking._get(
            "app_email_envoi_bien",
            {"select": "app_dossier_id,feedback", "envoi_id": f"eq.{envoi_id}"},
        )
        biens: list[dict[str, Any]] = []
        conseiller = {"nom": "Votre conseiller Groupe GTI", "agence": "Groupe GTI", "email": None}
        for row in bien_rows:
            did = row.get("app_dossier_id")
            if did is None:
                continue
            dossier, detail = self._load_dossier_by_id(int(did))
            if not dossier:
                continue
            view = build_bien_view(dossier, detail)
            view["feedback"] = row.get("feedback")
            view["rdv_url"] = self.renderer._appointment_url(dossier.get("hektor_annonce_id"))
            biens.append(view)
            if conseiller["email"] is None:
                conseiller = {
                    "nom": (dossier.get("commercial_nom") or "Votre conseiller Groupe GTI"),
                    "agence": (dossier.get("agence_nom") or "Groupe GTI"),
                    "email": dossier.get("negociateur_email") or None,
                }
        search_row = self._load_search_for_envoi(envoi)
        search_value = CSM.search_to_value(search_row) if search_row else None
        return {"envoi": envoi, "biens": biens, "conseiller": conseiller,
                "search_row": search_row, "search_value": search_value}

    def _load_search_for_envoi(self, envoi: dict[str, Any]) -> dict[str, Any] | None:
        """Identifie la recherche par (contact + index) STABLE ; repli sur la clé (ancien envoi)."""
        cid = str(envoi.get("hektor_contact_id") or "").strip()
        idx = envoi.get("search_index")
        if cid and idx is not None:
            rows = self.renderer._rest_get(
                "app_contact_search_current",
                {"select": "*", "hektor_contact_id": f"eq.{cid}", "search_index": f"eq.{int(idx)}", "limit": "1"})
            if rows:
                return rows[0]
        key = envoi.get("contact_search_key")
        if key:
            rows = self.renderer._rest_get(
                "app_contact_search_current", {"select": "*", "contact_search_key": f"eq.{key}", "limit": "1"})
            return rows[0] if rows else None
        return None

    def _negociateur_email(self, hektor_contact_id: str | None) -> str | None:
        if not hektor_contact_id:
            return None
        rows = self.renderer._rest_get(
            "app_contacts_current",
            {"select": "negociateur_email", "hektor_contact_id": f"eq.{hektor_contact_id}", "limit": "1"},
        )
        return (rows[0].get("negociateur_email") if rows else None) or None

    def _rpc(self, name: str, body: dict[str, Any]) -> Any:
        r = requests.post(
            f"{self.settings.supabase_url}/rest/v1/rpc/{name}",
            headers={"apikey": self.settings.supabase_service_role_key,
                     "Authorization": f"Bearer {self.settings.supabase_service_role_key}",
                     "Content-Type": "application/json"},
            json=body, timeout=30,
        )
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return None

    def submit_search_update(self, *, envoi_id: str, edits: dict[str, Any]) -> dict[str, Any]:
        """Au « Enregistrer » de l'espace : crée le job de mise à jour Hektor (si activé) + notifie le négociateur."""
        envoi = self.tracking._envoi(envoi_id)
        if not envoi:
            return {"ok": False, "error": "no_envoi"}
        search_row = self._load_search_for_envoi(envoi)
        if not search_row:
            return {"ok": False, "error": "search_not_found"}
        contact_id = str(search_row.get("hektor_contact_id") or "").strip()
        search_index = int(search_row.get("search_index") or 0)
        payload = CSM.build_job_search_payload(search_row, edits, search_index=search_index)

        job_created = False
        if self.settings.espace_search_write_enabled and contact_id.isdigit():
            # Même job que l'édition négociateur, via la fonction jumelle autorisée par le token espace.
            self._rpc("app_espace_create_search_update_job", {
                "target_contact_id": contact_id, "search_payload": payload, "job_priority": 16,
            })
            job_created = True

        # Notification négociateur (cloche dans l'app).
        nego = self._negociateur_email(contact_id) or envoi.get("sender_email")
        if nego:
            s = payload["search"]
            resume = f"budget {s.get('priceMin') or '?'}–{s.get('priceMax') or '?'} €"
            try:
                self.tracking._insert("app_notification", {
                    "negociateur_email": nego, "type": "recherche_modifiee_client",
                    "title": "Un client a modifié sa recherche",
                    "body": f"Nouvelle recherche : {resume}." + ("" if job_created else " (en attente d'activation)"),
                    "contact_search_key": envoi.get("contact_search_key"),
                    "payload": {"source": "espace_client", "edits": edits},
                }, prefer="return=minimal")
            except Exception:
                pass
        return {"ok": True, "jobCreated": job_created}

    def submit_message(self, *, envoi_id: str, message: str, bien_id: Any = None) -> dict[str, Any]:
        """Question/message d'un client : stocke + notifie le négociateur (cloche) + email interne."""
        envoi = self.tracking._envoi(envoi_id)
        if not envoi:
            return {"ok": False, "error": "no_envoi"}
        cid = envoi.get("hektor_contact_id")
        nego = self._negociateur_email(cid) or envoi.get("sender_email")
        msg = (message or "").strip()[:2000]
        try:
            self.tracking._insert("app_espace_message", {
                "envoi_id": envoi_id, "hektor_contact_id": cid, "contact_search_key": envoi.get("contact_search_key"),
                "app_dossier_id": int(bien_id) if str(bien_id or "").isdigit() else None,
                "negociateur_email": nego, "message": msg,
            }, prefer="return=minimal")
        except Exception:
            pass
        if nego:
            try:
                self.tracking._insert("app_notification", {
                    "negociateur_email": nego, "type": "message_client_espace",
                    "title": "Question d'un client", "body": msg[:200],
                    "contact_search_key": envoi.get("contact_search_key"),
                    "payload": {"source": "espace_client"},
                }, prefer="return=minimal")
            except Exception:
                pass
        email_sent = False
        if nego:
            try:
                from .google_workspace_service import GoogleWorkspaceService
                res = GoogleWorkspaceService(self.settings).send_gmail_message(
                    subject_email=(self.settings.google_workspace_subject_email or "accueil@gti-immobilier.fr"),
                    to=[nego], subject="Un client vous a écrit depuis son espace",
                    body_text=f"Message reçu depuis l'espace client (contact Hektor {cid}) :\n\n{msg}",
                    reply_to=envoi.get("recipient_email"),
                    dry_run=not self.settings.email_real_send_enabled,
                    related_entity_type="contact", related_entity_id=cid)
                email_sent = bool(res.get("ok")) and not res.get("dryRun")
            except Exception:
                pass
        return {"ok": True, "emailSent": email_sent}

    def render_page(self, *, envoi_id: str, token: str) -> str:
        ctx = self.build_context(envoi_id)
        if ctx is None:
            return self._page_message("Lien introuvable", "Cet espace n'est plus disponible. Contactez votre conseiller.")
        return self._render(ctx, token)

    # --- Rendu HTML -----------------------------------------------------------
    def _page_message(self, title: str, msg: str) -> str:
        return (f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
                f"<meta name=viewport content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>"
                f"<style>body{{margin:0;font-family:{FONT_BODY};background:{BRAND['paper']};color:{BRAND['ink_warm']};"
                f"display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center;padding:24px}}</style>"
                f"</head><body><div><h1 style='font-family:{FONT_DISPLAY}'>{html.escape(title)}</h1>"
                f"<p style='color:{BRAND['muted_warm']}'>{html.escape(msg)}</p></div></body></html>")

    def _bien_block(self, v: dict[str, Any]) -> str:
        hono = v["honoraires"]
        photo = (f'<div class="ph"><img src="{_esc(v["photo"])}" alt="{_esc(v["titre"])}"></div>'
                 if v["photo"] else '<div class="ph ph-empty">Photos sur demande</div>')
        sub = f'<div class="sub">{_esc(hono["sub"])}</div>' if hono.get("sub") else ""
        net = f'<div class="sub">{_esc(hono["net"])}</div>' if hono.get("net") else ""
        rdv = (f'<a class="btn ghost" href="{_esc(v["rdv_url"])}">Réserver une visite</a>'
               if v.get("rdv_url") else "")
        did = _esc(v["dossier_id"])
        # État initial selon le feedback déjà enregistré
        chosen = v.get("feedback")
        return f"""
      <article class="card" data-bien="{did}">
        {photo}
        <div class="body">
          <div class="loc">{_esc((v['secteur'] or v['ref']))}</div>
          <h2 class="title">{_esc(v['titre'])}</h2>
          <div class="price">{_esc(hono['price_main'])}</div>
          {sub}{net}
          <div class="specs">{_specs_line(v['specs'])}</div>
          <div class="actions">
            <button class="btn like {'on' if chosen=='interesse' else ''}" data-action="like">❤ Ça m'intéresse</button>
            <button class="btn pass {'on' if chosen=='refuse' else ''}" data-action="pass">Pas pour moi</button>
          </div>
          <div class="reasons" hidden>
            <div class="reasons-h">Pourquoi ? (facultatif)</div>
            <button class="rchip" data-reason="trop_cher">Trop cher</button>
            <button class="rchip" data-reason="secteur">Mauvais secteur</button>
            <button class="rchip" data-reason="trop_petit">Trop petit</button>
            <button class="rchip" data-reason="autre">Autre</button>
          </div>
          <div class="ack" hidden></div>
          {rdv}
        </div>
      </article>"""

    def _render(self, ctx: dict[str, Any], token: str) -> str:
        cards = "".join(self._bien_block(v) for v in ctx["biens"])
        c = ctx["conseiller"]
        base = (getattr(self.settings, "email_tracking_base_url", None) or self.settings.app_base_url or "").rstrip("/")
        post_url = f"{base}/espace/{html.escape(token)}/feedback"
        search_post = f"{base}/espace/{html.escape(token)}/recherche"
        msg_post = f"{base}/espace/{html.escape(token)}/message"
        conseiller_mail = (f'<a href="mailto:{_esc(c["email"])}">{_esc(c["email"])}</a>' if c.get("email") else "")

        sv = ctx.get("search_value")
        search_block = ""
        if sv:
            def _fld(lbl: str, fid: str, val: Any) -> str:
                v = int(val) if val else ""
                return f'<label class="fld"><span>{lbl}</span><input type="number" min="0" id="{fid}" value="{v}"></label>'
            fields = (_fld("Budget min (€)", "f-priceMin", sv["priceMin"]) + _fld("Budget max (€)", "f-priceMax", sv["priceMax"])
                      + _fld("Surface min (m²)", "f-surfaceMin", sv["surfaceMin"]) + _fld("Pièces min", "f-rooms", sv["rooms"])
                      + _fld("Chambres min", "f-bedrooms", sv["bedrooms"]))
            search_block = (
                '<div class="rech"><div class="rech-h">Ma recherche</div>'
                '<p class="rech-sub">Ajustez vos critères : votre conseiller en est informé, et vos prochains biens s\'affinent.</p>'
                f'<div class="fields">{fields}</div>'
                '<button class="btn like" id="rech-save">Enregistrer ma recherche</button>'
                '<div class="ack" id="rech-ack" hidden></div></div>'
            )
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Votre espace · Groupe GTI</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;background:{BRAND['paper']};color:{BRAND['ink_warm']};font-family:{FONT_BODY};-webkit-font-smoothing:antialiased}}
  .wrap{{max-width:640px;margin:0 auto;padding:0 14px 40px}}
  .top{{background:{BRAND['ink_warm']};border-radius:0 0 12px 12px;padding:16px 20px;display:flex;align-items:center;justify-content:space-between}}
  .top .name{{color:#fff;font-size:16px;font-weight:600}} .top .tag{{color:#cfc8bd;font-size:11px;letter-spacing:2px;text-transform:uppercase}}
  .lead{{padding:22px 6px 10px}} .lead h1{{font-family:{FONT_DISPLAY};font-size:24px;margin:0 0 6px}} .lead p{{color:{BRAND['ink_soft']};margin:0;line-height:1.6}}
  .card{{background:#fff;border:1px solid {BRAND['line_warm']};border-radius:14px;overflow:hidden;margin:18px 0}}
  .ph img{{display:block;width:100%;height:auto}} .ph-empty{{height:180px;display:flex;align-items:center;justify-content:center;color:{BRAND['muted_warm']};background:#efe9e0}}
  .body{{padding:18px 20px}}
  .loc{{color:{BRAND['magenta']};font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase}}
  .title{{font-family:{FONT_DISPLAY};font-size:22px;line-height:1.25;margin:8px 0 6px;font-weight:600}}
  .price{{font-family:{FONT_DISPLAY};font-size:24px}} .sub{{color:{BRAND['muted_warm']};font-size:13px;margin-top:3px}}
  .specs{{margin:10px 0 4px}}
  .actions{{display:flex;gap:10px;margin-top:16px}}
  .btn{{flex:1;border-radius:26px;padding:13px 10px;font-size:15px;font-weight:600;text-align:center;cursor:pointer;border:1px solid {BRAND['line_warm']};background:#fff;color:{BRAND['ink_soft']};text-decoration:none;display:block}}
  .btn.like{{background:{BRAND['magenta']};border-color:{BRAND['magenta']};color:#fff}}
  .btn.ghost{{flex:none;margin-top:12px;background:{BRAND['ink_warm']};border-color:{BRAND['ink_warm']};color:#fff}}
  .btn.on{{opacity:.55}} .btn:disabled{{cursor:default}}
  .ack{{margin-top:12px;font-size:14px;color:{BRAND['magenta_strong']};font-weight:600}}
  .adv{{background:#fff;border:1px solid {BRAND['line_warm']};border-radius:14px;padding:16px 20px;display:flex;align-items:center;gap:14px;margin-top:8px}}
  .adv .av{{width:46px;height:46px;border-radius:50%;background:{BRAND['magenta_soft']};color:{BRAND['magenta_strong']};display:flex;align-items:center;justify-content:center;font-weight:700}}
  .adv .nm{{font-weight:600}} .adv .ag{{color:{BRAND['muted_warm']};font-size:13px}}
  .rech{{background:#fff;border:1px solid {BRAND['line_warm']};border-radius:14px;padding:18px 20px;margin:18px 0}}
  .rech-h{{font-family:{FONT_DISPLAY};font-size:19px;font-weight:600}}
  .rech-sub{{color:{BRAND['muted_warm']};font-size:13px;margin:4px 0 14px;line-height:1.5}}
  .fields{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}}
  .fld{{display:flex;flex-direction:column;font-size:12px;color:{BRAND['muted_warm']}}}
  .fld input{{margin-top:5px;padding:11px;border:1px solid {BRAND['line_warm']};border-radius:8px;font-size:15px;color:{BRAND['ink_warm']};background:#fff;width:100%}}
  .reasons{{margin-top:12px}} .reasons-h{{font-size:12px;color:{BRAND['muted_warm']};margin-bottom:8px}}
  .rchip{{border:1px solid {BRAND['line_warm']};background:#fff;color:{BRAND['ink_soft']};border-radius:16px;padding:7px 13px;font-size:13px;margin:0 6px 6px 0;cursor:pointer}}
  .rchip.on{{background:{BRAND['magenta_soft']};border-color:{BRAND['magenta']};color:{BRAND['magenta_strong']}}}
  .msg{{background:#fff;border:1px solid {BRAND['line_warm']};border-radius:14px;padding:18px 20px;margin:18px 0}}
  .msg textarea{{width:100%;min-height:80px;padding:11px;border:1px solid {BRAND['line_warm']};border-radius:8px;font-size:15px;color:{BRAND['ink_warm']};font-family:inherit;resize:vertical}}
  .foot{{color:{BRAND['muted_warm']};font-size:11px;line-height:1.6;margin-top:22px}}
  @media (prefers-color-scheme:dark){{body{{background:#15130f;color:#f5efe6}}.card,.adv{{background:#211e19;border-color:#322d25}}.lead p{{color:#c2b9aa}}}}
</style>
</head>
<body>
  <div class="top"><span class="name">Votre espace</span><span class="tag">groupe gti</span></div>
  <div class="wrap">
    <div class="lead">
      <h1>Les biens sélectionnés pour vous</h1>
      <p>Dites-nous ce qui vous plaît. Votre conseiller en est informé aussitôt.</p>
    </div>
    {cards}
    {search_block}
    <div class="msg"><div class="rech-h">Une question ?</div>
      <p class="rech-sub">Écrivez à votre conseiller, il vous répond directement.</p>
      <textarea id="msg-text" placeholder="Votre message…"></textarea>
      <button class="btn like" id="msg-send" style="margin-top:12px">Envoyer à mon conseiller</button>
      <div class="ack" id="msg-ack" hidden></div>
    </div>
    <div class="adv">
      <div class="av">{_esc((c['nom'][:1] or 'G')).upper()}</div>
      <div style="flex:1"><div class="nm">{_esc(c['nom'])}</div><div class="ag">{_esc(c['agence'])} · {conseiller_mail}</div></div>
    </div>
    <div class="foot">Espace personnel sécurisé. Vos choix ne sont visibles que par votre agence.
      GROUPE GTI · RCS Saint-Étienne 502 811 144 · CPI 42022019 000 043 878.</div>
  </div>
<script>
const POST={json.dumps(post_url)};
async function post(b){{try{{await fetch(POST,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(b)}});}}catch(e){{}}}}
document.querySelectorAll('.card').forEach(card=>{{
  const bien=card.getAttribute('data-bien');
  const ack=card.querySelector('.ack');
  const reasons=card.querySelector('.reasons');
  card.querySelectorAll('button[data-action]').forEach(btn=>{{
    btn.addEventListener('click',()=>{{
      const action=btn.getAttribute('data-action');
      card.querySelectorAll('button[data-action]').forEach(b=>{{b.disabled=true;b.classList.remove('on')}});
      btn.classList.add('on'); ack.hidden=false;
      if(action==='like'){{ack.textContent='Merci ! Votre conseiller vous recontacte très vite.';}}
      else{{ack.textContent='C\\'est noté.'; if(reasons) reasons.hidden=false;}}
      post({{bien_id:bien,action}});
    }});
  }});
  if(reasons){{reasons.querySelectorAll('.rchip').forEach(ch=>{{
    ch.addEventListener('click',()=>{{
      reasons.querySelectorAll('.rchip').forEach(x=>x.classList.remove('on')); ch.classList.add('on');
      ack.textContent='Merci, ça nous aide à affiner nos propositions.';
      post({{bien_id:bien,action:'pass',reason:ch.getAttribute('data-reason')}});
    }});
  }});}}
}});
const MSG={json.dumps(msg_post)};
const ms=document.getElementById('msg-send');
if(ms){{ms.addEventListener('click',async()=>{{
  const t=document.getElementById('msg-text').value.trim(); if(!t)return;
  ms.disabled=true; const a=document.getElementById('msg-ack'); a.hidden=false; a.textContent='Message envoyé à votre conseiller. Il vous répond vite.';
  try{{await fetch(MSG,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{text:t}})}});}}catch(e){{}}
}});}}
const RECH={json.dumps(search_post)};
const rs=document.getElementById('rech-save');
if(rs){{rs.addEventListener('click',async()=>{{
  const g=id=>document.getElementById(id).value;
  const body={{priceMin:g('f-priceMin'),priceMax:g('f-priceMax'),surfaceMin:g('f-surfaceMin'),rooms:g('f-rooms'),bedrooms:g('f-bedrooms')}};
  rs.disabled=true; const a=document.getElementById('rech-ack'); a.hidden=false; a.textContent='Recherche mise à jour. Votre conseiller est informé.';
  try{{await fetch(RECH,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(body)}});}}catch(e){{}}
}});}}
</script>
</body>
</html>"""
