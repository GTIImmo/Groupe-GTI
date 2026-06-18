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
import re
from typing import Any

import requests

from ..settings import Settings
from . import contact_search_mapping as CSM
from .email_tracking import EmailTrackingService
from .rapprochement_email import BRAND, FONT_BODY, FONT_DISPLAY, build_bien_view, _clean_text, _esc, _specs_line
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
                       "photo_url_listing,images_preview_json,statut_annonce,mandat_type",
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
                # Lien Matterport : niché dans une valeur du payload -> extraction directe du brut.
                m = re.search(r'https?://[^"\\\s]*matterport[^"\\\s]*', raw)
                if m:
                    detail["_matterport"] = m.group(0)
        return dossier, detail

    @staticmethod
    def _photos(dossier: dict[str, Any]) -> list[str]:
        """Galerie : liste d'URLs https tirée de images_preview_json (ordonnée), repli sur la photo unique."""
        photos: list[str] = []
        raw = dossier.get("images_preview_json")
        items: Any = raw
        if isinstance(raw, str):
            try:
                items = json.loads(raw)
            except Exception:
                items = None
        if isinstance(items, list):
            ordered: list[tuple[int, str]] = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                url = str(it.get("full") or it.get("url") or "").strip()
                if url.startswith("https://") and "no_pic" not in url:
                    try:
                        order = int(it.get("order"))
                    except Exception:
                        order = 999
                    ordered.append((order, url))
            ordered.sort(key=lambda x: x[0])
            seen: set[str] = set()
            for _, url in ordered:
                if url not in seen:
                    seen.add(url)
                    photos.append(url)
        if not photos:
            p = str(dossier.get("photo_url_listing") or "").strip()
            if p.startswith("https://") and "no_pic" not in p:
                photos = [p]
        return photos[:12]

    def _view_from_dossier(self, dossier_id: int) -> dict[str, Any] | None:
        dossier, detail = self._load_dossier_by_id(dossier_id)
        if not dossier:
            return None
        view = build_bien_view(dossier, detail)
        view["photos"] = self._photos(dossier)
        view["rdv_url"] = self.renderer._appointment_url(dossier.get("hektor_annonce_id"))
        # Règle réseau : l'interlocuteur d'un bien = le négociateur du MANDAT (pas le commercial du contact).
        view["nego"] = {
            "nom": (dossier.get("commercial_nom") or "Votre conseiller Groupe GTI"),
            "agence": (dossier.get("agence_nom") or "Groupe GTI"),
            "email": dossier.get("negociateur_email") or None,
        }
        return view

    # Libellés + ordre d'affichage de l'historique (du plus engageant au moins).
    _HISTORY_LABELS = {"visite": ("Visite organisée", 1), "propose": ("Déjà proposé", 2),
                       "ecarte": ("Écarté", 3), "ecarté": ("Écarté", 3),
                       "refuse": ("Pas pour vous", 4), "refusé": ("Pas pour vous", 4)}

    def _load_history(self, envoi: dict[str, Any], *, active_ids: set[int],
                      refused_ids: set[int]) -> list[dict[str, Any]]:
        """Biens déjà vus ensemble : proposés / visités / écartés (table statut, à l'échelle du
        contact) + refusés par le client dans cet envoi. Dédupliqués, hors biens encore actifs."""
        info: dict[int, tuple[str, int]] = {}
        cid = str(envoi.get("hektor_contact_id") or "").strip()
        if cid:
            try:
                rows = self.renderer._rest_get(
                    "app_bien_acquereur_statut",
                    {"select": "app_dossier_id,status", "hektor_contact_id": f"eq.{cid}"})
            except Exception:
                rows = []
            for r in rows:
                did = r.get("app_dossier_id")
                if did is None:
                    continue
                lbl = self._HISTORY_LABELS.get(str(r.get("status") or "").strip().lower())
                if lbl:
                    info[int(did)] = lbl
        for did in refused_ids:
            info.setdefault(int(did), self._HISTORY_LABELS["refuse"])

        out: list[dict[str, Any]] = []
        for did, (label, rank) in info.items():
            if did in active_ids:
                continue
            view = self._view_from_dossier(did)
            if not view:
                continue
            view["status_label"] = label
            view["_rank"] = rank
            out.append(view)
        out.sort(key=lambda v: v["_rank"])
        return out[:24]

    def build_context(self, envoi_id: str) -> dict[str, Any] | None:
        envoi = self.tracking._envoi(envoi_id)
        if not envoi:
            return None
        bien_rows = self.tracking._get(
            "app_email_envoi_bien",
            {"select": "app_dossier_id,feedback", "envoi_id": f"eq.{envoi_id}"},
        )
        biens: list[dict[str, Any]] = []
        refused_ids: set[int] = set()
        for row in bien_rows:
            did = row.get("app_dossier_id")
            if did is None:
                continue
            # Masquer les biens refusés de la vue principale : ils basculent dans l'historique.
            if str(row.get("feedback") or "").strip().lower() in ("refuse", "refusé"):
                refused_ids.add(int(did))
                continue
            view = self._view_from_dossier(int(did))
            if not view:
                continue
            view["feedback"] = row.get("feedback")
            biens.append(view)
        history = self._load_history(envoi, active_ids={int(v["dossier_id"]) for v in biens},
                                     refused_ids=refused_ids)
        search_row = self._load_search_for_envoi(envoi)
        search_value = CSM.search_to_value(search_row) if search_row else None
        return {"envoi": envoi, "biens": biens, "history": history,
                "search_row": search_row, "search_value": search_value}

    def _contact_envois(self, contact_id: str) -> list[dict[str, Any]]:
        """Tous les envois d'un contact, le plus récent d'abord (pour l'espace unifié)."""
        return self.tracking._get(
            "app_email_envoi",
            {"select": "id,sender_email,search_index,contact_search_key,created_at",
             "hektor_contact_id": f"eq.{contact_id}", "order": "created_at.desc", "limit": "80"})

    def latest_envoi_id_for_contact(self, contact_id: str) -> str | None:
        envois = self._contact_envois(str(contact_id or "").strip())
        return envois[0]["id"] if envois else None

    def envoi_for_contact_bien(self, contact_id: str, bien_id: Any) -> str | None:
        """Retrouve l'envoi (le plus récent) ayant proposé ce bien à ce contact — pour tracer le clic."""
        cid = str(contact_id or "").strip()
        if not cid or bien_id is None:
            return None
        envois = self._contact_envois(cid)
        if not envois:
            return None
        ids = ",".join(e["id"] for e in envois)
        rows = self.tracking._get(
            "app_email_envoi_bien",
            {"select": "envoi_id", "app_dossier_id": f"eq.{bien_id}", "envoi_id": f"in.({ids})"})
        owned = {r.get("envoi_id") for r in rows}
        for e in envois:  # envois est trié récent->ancien : on prend le plus récent qui contient ce bien
            if e["id"] in owned:
                return e["id"]
        return None

    def build_context_for_contact(self, hektor_contact_id: str) -> dict[str, Any] | None:
        """Espace UNIFIÉ : agrège les biens proposés au contact par TOUS les négociateurs.

        - actifs : tout ce qui a été proposé et n'est ni refusé (client) ni écarté (négo) ;
        - historique : refusés / écartés, à l'échelle du contact ;
        chaque bien actif porte l'envoi le plus récent qui l'a proposé (pour le tracking)."""
        contact_id = str(hektor_contact_id or "").strip()
        if not contact_id:
            return None
        envois = self._contact_envois(contact_id)
        env_at = {e["id"]: (e.get("created_at") or "") for e in envois}

        # État par bien : envoi représentant (le plus récent) + feedback éventuel.
        state: dict[int, dict[str, Any]] = {}
        if envois:
            ids = ",".join(e["id"] for e in envois)
            rows = self.tracking._get(
                "app_email_envoi_bien",
                {"select": "app_dossier_id,feedback,envoi_id", "envoi_id": f"in.({ids})"})
            for r in rows:
                did = r.get("app_dossier_id")
                if did is None:
                    continue
                did = int(did)
                at = env_at.get(r.get("envoi_id"), "")
                cur = state.get(did)
                if cur is None or at > cur["at"]:
                    state[did] = {"envoi_id": r.get("envoi_id"), "at": at, "feedback": cur["feedback"] if cur else None}
                fb = str(r.get("feedback") or "").strip().lower()
                if fb:
                    state[did]["feedback"] = fb
                    if fb in ("refuse", "refusé"):
                        state[did]["refused"] = True

        # Statut négociateur (écarté / proposé / visité), à l'échelle du contact.
        statut: dict[int, str] = {}
        try:
            srows = self.renderer._rest_get(
                "app_bien_acquereur_statut",
                {"select": "app_dossier_id,status", "hektor_contact_id": f"eq.{contact_id}"})
        except Exception:
            srows = []
        for r in srows:
            did = r.get("app_dossier_id")
            if did is not None:
                statut[int(did)] = str(r.get("status") or "").strip().lower()

        active: list[dict[str, Any]] = []
        history: list[dict[str, Any]] = []
        for did, st in state.items():
            s = statut.get(did, "")
            refused = bool(st.get("refused")) or s in ("refuse", "refusé")
            ecarte = s in ("ecarte", "ecarté")
            view = self._view_from_dossier(did)
            if not view:
                continue
            view["envoi_id"] = st.get("envoi_id")
            if refused or ecarte:
                view["status_label"] = "Pas pour vous" if refused else "Écarté"
                view["_rank"] = 4 if refused else 3
                history.append(view)
            else:
                view["feedback"] = st.get("feedback")
                view["_at"] = st.get("at") or ""
                active.append(view)
        active.sort(key=lambda v: v.get("_at") or "", reverse=True)
        history.sort(key=lambda v: v["_rank"])

        search_row = self._load_search_for_envoi(envois[0]) if envois else None
        search_value = CSM.search_to_value(search_row) if search_row else None
        return {"contact_id": contact_id, "biens": active, "history": history[:24],
                "search_row": search_row, "search_value": search_value,
                "primary_envoi_id": (envois[0]["id"] if envois else None)}

    # ── PORTAIL (refonte design) : vues riches + contexte + rendu ──────────────
    @staticmethod
    def _to_int(v: Any) -> int | None:
        try:
            return int(float(str(v).replace(" ", "").replace(",", ".")))
        except Exception:
            return None

    def _portal_specs(self, detail: dict[str, Any]) -> list[list[str]]:
        out: list[list[str]] = []
        surf = self._to_int(detail.get("surface"))
        if surf:
            out.append([f"{surf} m²", "Habitable"])
        p = self._to_int(detail.get("nb_pieces"))
        if p:
            out.append([str(p), "Pièces"])
        c = self._to_int(detail.get("nb_chambres"))
        if c:
            out.append([str(c), "Chambres"])
        t = self._to_int(detail.get("surface_terrain_detail"))
        if t and t > 0:
            out.append([f"{t} m²", "Terrain"])
        return out

    @staticmethod
    def _portal_feats(detail: dict[str, Any]) -> list[str]:
        raw = detail.get("equipements_json")
        data = raw
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except Exception:
                return []
        sections = data if isinstance(data, list) else [data]
        feats: list[str] = []
        for sec in sections:
            props = sec.get("props") if isinstance(sec, dict) else None
            if not isinstance(props, dict):
                continue
            for p in props.values():
                if isinstance(p, dict) and str(p.get("value", "")).strip().upper() in ("OUI", "YES", "1", "TRUE"):
                    lbl = str(p.get("label") or "").strip()
                    if lbl:
                        feats.append(lbl)
        return feats[:12]

    def _portal_details(self, dossier: dict[str, Any], detail: dict[str, Any]) -> list[list[str]]:
        out: list[list[str]] = []
        t = _clean_text(dossier.get("type_bien"))
        if t:
            out.append(["Type", t])
        ter = self._to_int(detail.get("surface_terrain_detail"))
        if ter and ter > 0:
            out.append(["Terrain", f"{ter} m²"])
        et = _clean_text(detail.get("etage_detail"))
        if et:
            out.append(["Étage", et])
        gar = self._to_int(detail.get("garage_box_detail"))
        if gar and gar > 0:
            out.append(["Garage", str(gar)])
        asc = _clean_text(detail.get("ascenseur_detail"))
        if asc and asc.lower() not in ("non", "0", "false"):
            out.append(["Ascenseur", "Oui"])
        ter2 = _clean_text(detail.get("terrasse_detail"))
        if ter2 and ter2.lower() not in ("non", "0", "false"):
            out.append(["Terrasse", "Oui"])
        return out

    @staticmethod
    def _portal_desc(detail: dict[str, Any]) -> str:
        txt = detail.get("texte_principal_html") or ""
        txt = re.sub(r"<[^>]+>", " ", str(txt))
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt[:700]

    def _portal_pourquoi(self, dossier: dict[str, Any], detail: dict[str, Any],
                         sv: dict[str, Any] | None) -> list[str]:
        if not sv:
            return []
        out: list[str] = []
        prix = self._to_int(dossier.get("prix"))
        pmin, pmax = self._to_int(sv.get("priceMin")), self._to_int(sv.get("priceMax"))
        if prix and pmax and prix <= pmax and (not pmin or prix >= pmin * 0.9):
            out.append("Budget")
        # Secteur : ville/CP du bien dans les localités de la recherche
        cp = str(dossier.get("code_postal") or "").strip()
        ville = str(dossier.get("ville") or "").strip().lower()
        for loc in (sv.get("localities") or []):
            if (cp and cp == str(loc.get("postalCode") or "").strip()) or \
               (ville and ville == str(loc.get("city") or "").strip().lower()):
                out.append("Secteur")
                break
        surf, smin = self._to_int(detail.get("surface")), self._to_int(sv.get("surfaceMin"))
        if surf and smin and surf >= smin:
            out.append("Surface")
        pieces, rmin = self._to_int(detail.get("nb_pieces")), self._to_int(sv.get("rooms"))
        if pieces and rmin and pieces >= rmin:
            out.append("Pièces")
        ch, bmin = self._to_int(detail.get("nb_chambres")), self._to_int(sv.get("bedrooms"))
        if ch and bmin and ch >= bmin:
            out.append("Chambres")
        return out

    @staticmethod
    def _initials(name: str | None) -> str:
        parts = [p for p in re.split(r"[\s.-]+", str(name or "").strip()) if p]
        return ("".join(p[0] for p in parts[:2]) or "?").upper()

    def _portal_view(self, dossier: dict[str, Any], detail: dict[str, Any], *, envoi_id: Any,
                     sv: dict[str, Any] | None, feedback: Any = None, feedback_reason: Any = None,
                     badge: str | None = None) -> dict[str, Any]:
        base = build_bien_view(dossier, detail)
        did = dossier.get("app_dossier_id")
        annonce = dossier.get("hektor_annonce_id")
        hono = base["honoraires"]
        prix = self._to_int(dossier.get("prix"))
        surf = self._to_int(detail.get("surface"))
        ppm = f"{round(prix / surf):,} €/m²".replace(",", " ") if (prix and surf) else ""
        mandat = str(dossier.get("mandat_type") or "").lower()
        statut = "Exclusif" if "xclusif" in mandat else (_clean_text(dossier.get("statut_annonce")) or "Disponible")
        nego = {
            "initials": self._initials(dossier.get("commercial_nom")),
            "name": _clean_text(dossier.get("commercial_nom")) or "Votre conseiller Groupe GTI",
            "agence": _clean_text(dossier.get("agence_nom")) or "Groupe GTI",
            "tel": None,
            "email": dossier.get("negociateur_email") or None,
        }
        fin = [["Prix de vente", hono["price_main"]]]
        if hono.get("sub"):
            fin.append(["Honoraires", hono["sub"]])
        if hono.get("net"):
            fin.append(["Net vendeur", hono["net"].replace("Net vendeur", "").strip() or hono["net"]])
        return {
            "key": str(did), "dossier_id": int(did) if did is not None else None, "envoi_id": envoi_id,
            "ref": base["ref"], "statut": statut, "loc": base["secteur"],  # ville + CP (jamais la rue)
            "title": base["titre"], "price": hono["price_main"], "ppm": ppm,
            "specs": self._portal_specs(detail), "photos": self._photos(dossier),
            "nego": nego, "matterport": detail.get("_matterport"),
            "dpe_img": _clean_text(detail.get("dpe_image_url")), "ges_img": _clean_text(detail.get("ges_image_url")),
            "desc": self._portal_desc(detail), "details": self._portal_details(dossier, detail),
            "feats": self._portal_feats(detail), "honos": hono.get("sub") or "Honoraires à la charge du vendeur",
            "fin": fin, "pourquoi": self._portal_pourquoi(dossier, detail, sv),
            "rdv_url": self.renderer._appointment_url(annonce) if annonce else None,
            "feedback": feedback, "feedback_reason": feedback_reason, "badge": badge,
        }

    _MONTHS_FR = ["", "jan", "fév", "mar", "avr", "mai", "juin", "juil", "août", "sep", "oct", "nov", "déc"]

    def _portal_visites(self, dossier_ids: list[int], titles: dict[int, str]) -> list[dict[str, Any]]:
        if not dossier_ids:
            return []
        ids = ",".join(str(d) for d in dossier_ids)
        try:
            rows = self.renderer._rest_get(
                "app_google_calendar_event_link",
                {"select": "starts_at,status,metadata_json,app_dossier_id",
                 "app_dossier_id": f"in.({ids})", "event_type": "eq.visite",
                 "order": "starts_at.asc"})
        except Exception:
            return []
        out: list[dict[str, Any]] = []
        for r in rows:
            if str(r.get("status") or "active") == "deleted":
                continue
            sa = str(r.get("starts_at") or "")
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})", sa)
            if not m:
                continue
            _, mo, dd, hh, mi = m.groups()
            cancelled = str(r.get("status") or "") == "cancelled"
            meta = r.get("metadata_json") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            did = r.get("app_dossier_id")
            out.append({
                "d": str(int(dd)), "m": self._MONTHS_FR[int(mo)] if 1 <= int(mo) <= 12 else mo,
                "title": meta.get("titre_bien") or titles.get(int(did) if did is not None else -1) or "Visite",
                "loc": meta.get("secteur") or "",
                "when": f"{hh}h{mi}",
                "status": "wait" if cancelled else "ok",
                "status_label": "Annulée" if cancelled else "Confirmée",
            })
        return out

    def build_portal_context(self, hektor_contact_id: str, featured_dossier_id: int | None = None) -> dict[str, Any] | None:
        contact_id = str(hektor_contact_id or "").strip()
        if not contact_id:
            return None
        envois = self._contact_envois(contact_id)
        env_at = {e["id"]: (e.get("created_at") or "") for e in envois}
        state: dict[int, dict[str, Any]] = {}
        if envois:
            ids = ",".join(e["id"] for e in envois)
            rows = self.tracking._get(
                "app_email_envoi_bien",
                {"select": "app_dossier_id,feedback,feedback_reason,envoi_id", "envoi_id": f"in.({ids})"})
            for r in rows:
                did = r.get("app_dossier_id")
                if did is None:
                    continue
                did = int(did)
                at = env_at.get(r.get("envoi_id"), "")
                cur = state.get(did)
                if cur is None or at > cur["at"]:
                    state[did] = {"envoi_id": r.get("envoi_id"), "at": at,
                                  "feedback": cur["feedback"] if cur else None,
                                  "reason": cur.get("reason") if cur else None}
                fb = str(r.get("feedback") or "").strip().lower()
                if fb:
                    state[did]["feedback"] = fb
                    if r.get("feedback_reason"):
                        state[did]["reason"] = r.get("feedback_reason")
                    if fb in ("refuse", "refusé"):
                        state[did]["refused"] = True
        statut: dict[int, str] = {}
        try:
            srows = self.renderer._rest_get(
                "app_bien_acquereur_statut",
                {"select": "app_dossier_id,status", "hektor_contact_id": f"eq.{contact_id}"})
        except Exception:
            srows = []
        for r in srows:
            d = r.get("app_dossier_id")
            if d is not None:
                statut[int(d)] = str(r.get("status") or "").strip().lower()

        search_row = self._load_search_for_envoi(envois[0]) if envois else None
        sv = CSM.search_to_value(search_row) if search_row else None

        active: list[tuple[str, dict[str, Any]]] = []
        ecartes: list[dict[str, Any]] = []
        titles: dict[int, str] = {}
        for did, st in state.items():
            s = statut.get(did, "")
            refused = bool(st.get("refused")) or s in ("refuse", "refusé")
            ecarte = s in ("ecarte", "ecarté")
            dossier, detail = self._load_dossier_by_id(did)
            if not dossier:
                continue  # bien vendu / archivé : sort de app_dossier_current -> non affiché
            view = self._portal_view(dossier, detail, envoi_id=st.get("envoi_id"), sv=sv,
                                     feedback=st.get("feedback"), feedback_reason=st.get("reason"))
            titles[did] = view["title"]
            if refused or ecarte:
                view["feedback"] = "refuse"
                ecartes.append(view)
            else:
                active.append((st.get("at") or "", view))
        active.sort(key=lambda t: t[0], reverse=True)
        actives = [v for _, v in active]

        featured = None
        if featured_dossier_id is not None:
            featured = next((v for v in actives if v.get("dossier_id") == int(featured_dossier_id)), None)
        if featured:
            actives = [v for v in actives if v is not featured]
        elif actives:
            featured = actives.pop(0)
        if featured and not featured.get("badge"):
            featured["badge"] = None
        # Marque « Nouveau » le 1er de la sélection (le plus récent)
        if actives:
            actives[0]["badge"] = actives[0].get("badge") or "Nouveau"

        visites = self._portal_visites(list(titles.keys()), titles)

        # Contact (client)
        crow = self.renderer._rest_get(
            "app_contacts_current",
            {"select": "display_name,email", "hektor_contact_id": f"eq.{contact_id}", "limit": "1"})
        cname = (crow[0].get("display_name") if crow else None) or "Votre espace"
        cmail = (crow[0].get("email") if crow else None) or ""

        # Chips + champs depuis la recherche
        chips: list[tuple[str, str]] = []
        fields: dict[str, Any] = {}
        if sv:
            pmin, pmax = self._to_int(sv.get("priceMin")), self._to_int(sv.get("priceMax"))
            if pmin or pmax:
                chips.append(("Budget", f"{(pmin or 0)//1000}–{(pmax or 0)//1000} k€"))
            locs = [l.get("city") for l in (sv.get("localities") or []) if l.get("city")]
            if locs:
                chips.append(("Secteur", ", ".join(locs[:2])))
            smin = self._to_int(sv.get("surfaceMin"))
            if smin:
                chips.append(("Surface", f"≥ {smin} m²"))
            bmin = self._to_int(sv.get("bedrooms"))
            if bmin:
                chips.append(("Chambres", f"{bmin}+"))
            fields = {"priceMin": pmin, "priceMax": pmax, "surfaceMin": smin,
                      "rooms": self._to_int(sv.get("rooms")), "bedrooms": bmin}

        n_fav = sum(1 for v in ([featured] if featured else []) + actives if v.get("feedback") == "interesse")
        stats = {"proposes": len(actives) + (1 if featured else 0) + len(ecartes),
                 "favoris": n_fav, "visites": len(visites), "ecartes": len(ecartes)}

        return {
            "client": {"name": cname, "email": cmail, "initials": self._initials(cname)},
            "search_chips": chips, "search_fields": fields,
            "featured": featured, "selection": actives, "ecartes": ecartes[:24],
            "visites": visites, "stats": stats,
        }

    def render_contact_portal(self, *, hektor_contact_id: str, token: str,
                              featured_dossier_id: int | None = None, from_email: bool = False) -> str:
        from . import espace_portal
        ctx = self.build_portal_context(hektor_contact_id, featured_dossier_id)
        if ctx is None:
            return self._page_message("Espace introuvable",
                                      "Cet espace n'est plus disponible. Contactez votre conseiller.")
        base = (getattr(self.settings, "email_tracking_base_url", None) or self.settings.app_base_url or "").rstrip("/")
        return espace_portal.render_portal(ctx, token=token, base=base, from_email=from_email)

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

    def _bien_nego_email(self, dossier_id: Any) -> str | None:
        """Négociateur du MANDAT d'un bien (destinataire des questions sur ce bien)."""
        if dossier_id is None:
            return None
        rows = self.renderer._rest_get(
            "app_dossier_current",
            {"select": "negociateur_email", "app_dossier_id": f"eq.{dossier_id}", "limit": "1"})
        return (rows[0].get("negociateur_email") if rows else None) or None

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
        # Règle réseau : la question est rattachée à un bien → elle part au négociateur du MANDAT.
        nego = self._bien_nego_email(bien_id) or envoi.get("sender_email") or self._negociateur_email(cid)
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

    # Requalification GUIDÉE (sûre) : la raison du ✕ -> piste pour le négociateur (pas d'écriture CRM auto).
    _REQUALIF_SUGGESTION = {
        "trop_cher": "Budget ressenti trop élevé — proposer moins cher ou ajuster le budget.",
        "secteur": "Secteur non souhaité — revoir les communes de la recherche.",
        "trop_petit": "Surface jugée insuffisante — augmenter surface / nombre de pièces.",
        "autre": "Bien écarté (autre raison).",
    }

    def record_requalif_hint(self, *, envoi: dict[str, Any], bien_id: Any, reason: str) -> None:
        sugg = self._REQUALIF_SUGGESTION.get(reason)
        if not sugg:
            return
        nego = envoi.get("sender_email") or self._bien_nego_email(bien_id)
        if not nego:
            return
        try:
            self.tracking._insert("app_notification", {
                "negociateur_email": nego, "type": "requalification_hint",
                "title": "Piste de requalification", "body": sugg,
                "contact_search_key": envoi.get("contact_search_key"),
                "app_dossier_id": int(bien_id) if str(bien_id or "").isdigit() else None,
                "payload": {"source": "espace_client", "reason": reason},
            }, prefer="return=minimal")
        except Exception:
            pass

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

    @staticmethod
    def _gallery(v: dict[str, Any]) -> str:
        photos = [p for p in (v.get("photos") or ([v.get("photo")] if v.get("photo") else [])) if p]
        if not photos:
            return '<div class="gal ph-empty">Photos bientôt disponibles</div>'
        slides = "".join(
            f'<div class="slide"><img src="{_esc(p)}" alt="{_esc(v["titre"])}" loading="lazy"></div>'
            for p in photos)
        nav = ""
        n = len(photos)
        if n > 1:
            dots = "".join(f'<span class="dot{" on" if i == 0 else ""}"></span>' for i in range(n))
            nav = ('<button class="gnav prev" type="button" aria-label="Photo précédente">‹</button>'
                   '<button class="gnav next" type="button" aria-label="Photo suivante">›</button>'
                   f'<div class="gcount"><span class="gcur">1</span> / {n}</div>'
                   f'<div class="dots">{dots}</div>')
        return f'<div class="gal" data-n="{n}"><div class="gal-track">{slides}</div>{nav}</div>'

    def _bien_block(self, v: dict[str, Any]) -> str:
        hono = v["honoraires"]
        sub = f'<div class="sub">{_esc(hono["sub"])}</div>' if hono.get("sub") else ""
        net = f'<div class="sub">{_esc(hono["net"])}</div>' if hono.get("net") else ""
        rdv = (f'<a class="btn ghost" href="{_esc(v["rdv_url"])}">Organiser une visite</a>'
               if v.get("rdv_url") else "")
        did = _esc(v["dossier_id"])
        nego_nom = _esc(v.get('nego', {}).get('nom') or 'votre conseiller Groupe GTI')
        chosen = v.get("feedback")  # état initial selon le feedback déjà enregistré
        # Espace unifié (contact) : le bien porte l'envoi qui l'a proposé, pour tracer le clic.
        envoi_attr = f' data-envoi="{_esc(v["envoi_id"])}"' if v.get("envoi_id") else ""
        return f"""
      <article class="card" data-bien="{did}"{envoi_attr}>
        {self._gallery(v)}
        <div class="body">
          <div class="loc">{_esc((v['secteur'] or v['ref']))}</div>
          <h2 class="title">{_esc(v['titre'])}</h2>
          <div class="price">{_esc(hono['price_main'])}</div>
          {sub}{net}
          <div class="specs">{_specs_line(v['specs'])}</div>
          <div class="actions">
            <button class="btn like {'on' if chosen=='interesse' else ''}" data-action="like">❤ Coup de cœur</button>
            <button class="btn pass {'on' if chosen=='refuse' else ''}" data-action="pass">Pas pour moi</button>
          </div>
          <div class="reasons" hidden>
            <div class="reasons-h">Pour mieux cibler la prochaine fois — qu'est-ce qui ne va pas&nbsp;?</div>
            <button class="rchip" data-reason="trop_cher">Trop cher</button>
            <button class="rchip" data-reason="secteur">Mauvais secteur</button>
            <button class="rchip" data-reason="trop_petit">Trop petit</button>
            <button class="rchip" data-reason="autre">Autre</button>
          </div>
          <div class="ack" hidden></div>
          {rdv}
          <div class="qbox">
            <div class="qinter">Une question sur ce bien&nbsp;? <b>{nego_nom}</b> vous répond directement.</div>
            <textarea class="qtext" placeholder="Votre question…"></textarea>
            <button class="btn qsend">Poser ma question</button>
            <div class="ack qack" hidden></div>
          </div>
        </div>
      </article>"""

    def _history_block(self, history: list[dict[str, Any]]) -> str:
        if not history:
            return ""
        rows = []
        for v in history:
            photos = v.get("photos") or ([v.get("photo")] if v.get("photo") else [])
            thumb = (f'<div class="hthumb"><img src="{_esc(photos[0])}" alt="" loading="lazy"></div>'
                     if photos else '<div class="hthumb hthumb-empty"></div>')
            specs = " · ".join(v.get("specs") or [])
            meta = _esc(" · ".join(p for p in (v.get("secteur"), specs) if p))
            rows.append(
                f'<div class="hrow">{thumb}'
                f'<div class="hmeta"><div class="htitle">{_esc(v["titre"])}</div>'
                f'<div class="hloc">{meta}</div></div>'
                f'<span class="hbadge">{_esc(v.get("status_label") or "")}</span></div>')
        return (
            '<details class="hist">'
            f'<summary>Déjà vus ensemble<span class="hist-n">{len(history)}</span>'
            '<span class="chev" aria-hidden="true">⌄</span></summary>'
            f'<div class="hist-list">{"".join(rows)}</div>'
            '</details>')

    @staticmethod
    def _search_block(sv: dict[str, Any] | None) -> str:
        if not sv:
            return ""
        def _fld(lbl: str, fid: str, val: Any) -> str:
            v = int(val) if val else ""
            return f'<label class="fld"><span>{lbl}</span><input type="number" min="0" id="{fid}" value="{v}"></label>'
        fields = (_fld("Budget min (€)", "f-priceMin", sv["priceMin"]) + _fld("Budget max (€)", "f-priceMax", sv["priceMax"])
                  + _fld("Surface min (m²)", "f-surfaceMin", sv["surfaceMin"]) + _fld("Pièces min", "f-rooms", sv["rooms"])
                  + _fld("Chambres min", "f-bedrooms", sv["bedrooms"]))
        return (
            '<div class="rech"><div class="rech-h">Affiner ma recherche</div>'
            '<p class="rech-sub">Ajustez vos critères : vos prochaines propositions collent mieux à votre projet, '
            'et votre conseiller est prévenu aussitôt.</p>'
            f'<div class="fields">{fields}</div>'
            '<button class="btn like" id="rech-save">Mettre à jour</button>'
            '<div class="ack" id="rech-ack" hidden></div></div>'
        )

    def _grouped_cards(self, biens: list[dict[str, Any]]) -> str:
        """Cartes regroupées par négociateur du mandat (en-tête léger si plusieurs négos)."""
        groups: dict[str, list[dict[str, Any]]] = {}
        order: list[str] = []
        for v in biens:
            nom = (v.get("nego") or {}).get("nom") or "Votre conseiller Groupe GTI"
            if nom not in groups:
                groups[nom] = []
                order.append(nom)
            groups[nom].append(v)
        single = len(order) <= 1
        out: list[str] = []
        for nom in order:
            if not single:
                out.append(f'<div class="negohdr"><span class="negohdr-k">Proposé par</span> {_esc(nom)}</div>')
            out.extend(self._bien_block(v) for v in groups[nom])
        return "".join(out)

    def _render(self, ctx: dict[str, Any], token: str) -> str:
        """Espace lié à un envoi (compat) : les biens de cet email."""
        has_active = bool(ctx["biens"])
        lead_h1 = "Une sélection rien que pour vous" if has_active else "Votre espace personnel"
        lead_p = ("Quelques biens repérés pour votre projet. Faites défiler les photos, gardez ceux qui vous "
                  "parlent — on s'occupe du reste." if has_active else
                  "Vous avez parcouru tous les biens du moment. Affinez votre recherche ci-dessous : vos "
                  "prochaines pépites arrivent vite.")
        return self._shell(token=token, cards="".join(self._bien_block(v) for v in ctx["biens"]),
                           search_block=self._search_block(ctx.get("search_value")),
                           history_block=self._history_block(ctx.get("history") or []),
                           lead_h1=lead_h1, lead_p=lead_p)

    def render_contact_page(self, *, hektor_contact_id: str, token: str) -> str:
        """Espace UNIFIÉ d'un contact : tous les biens, regroupés par négociateur."""
        ctx = self.build_context_for_contact(hektor_contact_id)
        if ctx is None:
            return self._page_message("Espace introuvable",
                                      "Cet espace n'est plus disponible. Contactez votre conseiller.")
        has_active = bool(ctx["biens"])
        lead_h1 = "Tous vos biens, au même endroit" if has_active else "Votre espace personnel"
        lead_p = ("Voici tout ce que votre agence a sélectionné pour vous. Gardez ce qui vous plaît — chaque bien "
                  "vous met en lien avec le bon conseiller." if has_active else
                  "Vous avez parcouru tous les biens du moment. Affinez votre recherche ci-dessous : vos "
                  "prochaines pépites arrivent vite.")
        return self._shell(token=token, cards=self._grouped_cards(ctx["biens"]),
                           search_block=self._search_block(ctx.get("search_value")),
                           history_block=self._history_block(ctx.get("history") or []),
                           lead_h1=lead_h1, lead_p=lead_p)

    def _shell(self, *, token: str, cards: str, search_block: str, history_block: str,
               lead_h1: str, lead_p: str) -> str:
        base = (getattr(self.settings, "email_tracking_base_url", None) or self.settings.app_base_url or "").rstrip("/")
        post_url = f"{base}/espace/{html.escape(token)}/feedback"
        search_post = f"{base}/espace/{html.escape(token)}/recherche"
        msg_post = f"{base}/espace/{html.escape(token)}/message"
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
  .negohdr{{margin:26px 6px 2px;font-family:{FONT_BODY};font-size:13px;color:{BRAND['ink_warm']};font-weight:600}}
  .negohdr-k{{color:{BRAND['magenta']};font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-right:6px}}
  .card{{background:#fff;border:1px solid {BRAND['line_warm']};border-radius:16px;overflow:hidden;margin:20px 0;box-shadow:0 1px 2px rgba(31,28,26,.04),0 12px 30px -18px rgba(31,28,26,.25)}}
  /* Galerie : bande horizontale scroll-snap, flèches + pastilles, badge compteur */
  .gal{{position:relative;background:#efe9e0;line-height:0}}
  .gal-track{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;-webkit-overflow-scrolling:touch;scrollbar-width:none}}
  .gal-track::-webkit-scrollbar{{display:none}}
  .slide{{flex:0 0 100%;scroll-snap-align:center}}
  .slide img{{display:block;width:100%;height:310px;object-fit:cover}}
  .gnav{{position:absolute;top:50%;transform:translateY(-50%);width:38px;height:38px;border-radius:50%;border:none;background:rgba(31,28,26,.42);color:#fff;font-size:22px;line-height:36px;text-align:center;cursor:pointer;padding:0;opacity:.92;transition:opacity .15s}}
  .gnav:hover{{opacity:1}} .gnav.prev{{left:10px}} .gnav.next{{right:10px}}
  .gcount{{position:absolute;top:12px;right:12px;background:rgba(31,28,26,.55);color:#fff;font-size:12px;line-height:1;padding:5px 10px;border-radius:20px;letter-spacing:.4px}}
  .dots{{position:absolute;bottom:12px;left:0;right:0;display:flex;gap:6px;justify-content:center;line-height:0}}
  .dot{{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.55);transition:width .2s,background .2s}}
  .dot.on{{background:#fff;width:18px;border-radius:4px}}
  .ph-empty{{height:200px;display:flex;align-items:center;justify-content:center;color:{BRAND['muted_warm']};background:#efe9e0;font-size:14px}}
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
  .qbox{{margin-top:14px;border-top:1px solid {BRAND['line_warm']};padding-top:14px}}
  .qinter{{font-size:13px;color:{BRAND['muted_warm']};margin-bottom:8px}}
  .qtext{{width:100%;min-height:62px;padding:10px;border:1px solid {BRAND['line_warm']};border-radius:8px;font-size:14px;color:{BRAND['ink_warm']};font-family:inherit;resize:vertical}}
  .qsend{{margin-top:8px}}
  .foot{{color:{BRAND['muted_warm']};font-size:11px;line-height:1.6;margin-top:22px}}
  /* Historique : section repliable, biens déjà vus (proposés / visités / écartés / refusés) */
  .hist{{background:#fff;border:1px solid {BRAND['line_warm']};border-radius:14px;margin:20px 0;overflow:hidden}}
  .hist>summary{{list-style:none;cursor:pointer;padding:16px 20px;font-family:{FONT_DISPLAY};font-size:18px;font-weight:600;display:flex;align-items:center}}
  .hist>summary::-webkit-details-marker{{display:none}}
  .hist-n{{background:{BRAND['magenta_soft']};color:{BRAND['magenta_strong']};font-family:{FONT_BODY};font-size:12px;font-weight:700;padding:2px 9px;border-radius:20px;margin-left:10px}}
  .chev{{margin-left:auto;color:{BRAND['muted_warm']};font-size:18px;transition:transform .2s}}
  .hist[open] .chev{{transform:rotate(180deg)}}
  .hist-list{{padding:0 14px 8px}}
  .hrow{{display:flex;align-items:center;gap:12px;padding:11px 6px;border-top:1px solid {BRAND['line_warm']}}}
  .hthumb{{width:66px;height:50px;border-radius:9px;overflow:hidden;flex:none;background:#efe9e0}}
  .hthumb img{{width:100%;height:100%;object-fit:cover;display:block}}
  .hmeta{{flex:1;min-width:0}}
  .htitle{{font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .hloc{{color:{BRAND['muted_warm']};font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}}
  .hbadge{{flex:none;font-size:11px;font-weight:600;padding:4px 10px;border-radius:20px;background:#efe9e0;color:{BRAND['ink_soft']};white-space:nowrap}}
  @media (prefers-color-scheme:dark){{body{{background:#15130f;color:#f5efe6}}
    .card,.rech,.hist{{background:#211e19;border-color:#322d25}}.lead p{{color:#c2b9aa}}
    .hrow{{border-color:#322d25}}.hthumb,.ph-empty,.gal{{background:#2a261f}}.hbadge{{background:#2a261f;color:#cabfae}}
    .fld input,.qtext{{background:#1b1813;border-color:#322d25;color:#f5efe6}}}}
</style>
</head>
<body>
  <div class="top"><span class="name">Votre espace</span><span class="tag">groupe gti</span></div>
  <div class="wrap">
    <div class="lead">
      <h1>{_esc(lead_h1)}</h1>
      <p>{_esc(lead_p)}</p>
    </div>
    {cards}
    {search_block}
    {history_block}
    <div class="foot">Espace personnel sécurisé. Vos choix ne sont visibles que par votre agence.
      GROUPE GTI · RCS Saint-Étienne 502 811 144 · CPI 42022019 000 043 878.</div>
  </div>
<script>
const POST={json.dumps(post_url)};
const MSG={json.dumps(msg_post)};
async function post(b){{try{{await fetch(POST,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(b)}});}}catch(e){{}}}}
// Galerie photos : flèches, pastilles et compteur synchronisés au défilement.
document.querySelectorAll('.gal[data-n]').forEach(g=>{{
  const track=g.querySelector('.gal-track'); if(!track) return;
  const n=parseInt(g.getAttribute('data-n'))||1; if(n<2) return;
  const cur=g.querySelector('.gcur'); const dots=[].slice.call(g.querySelectorAll('.dot'));
  const idx=()=>Math.round(track.scrollLeft/track.clientWidth);
  const sync=()=>{{const i=idx(); if(cur)cur.textContent=(i+1); dots.forEach((d,k)=>d.classList.toggle('on',k===i));}};
  track.addEventListener('scroll',()=>window.requestAnimationFrame(sync),{{passive:true}});
  const go=d=>track.scrollTo({{left:Math.max(0,Math.min(n-1,idx()+d))*track.clientWidth,behavior:'smooth'}});
  const p=g.querySelector('.prev'),nx=g.querySelector('.next');
  if(p)p.addEventListener('click',()=>go(-1)); if(nx)nx.addEventListener('click',()=>go(1));
  dots.forEach((d,k)=>d.addEventListener('click',()=>track.scrollTo({{left:k*track.clientWidth,behavior:'smooth'}})));
}});
document.querySelectorAll('.card').forEach(card=>{{
  const bien=card.getAttribute('data-bien');
  const env=card.getAttribute('data-envoi');  // espace unifié : envoi qui a proposé ce bien
  const ack=card.querySelector('.ack');
  const reasons=card.querySelector('.reasons');
  card.querySelectorAll('button[data-action]').forEach(btn=>{{
    btn.addEventListener('click',()=>{{
      const action=btn.getAttribute('data-action');
      card.querySelectorAll('button[data-action]').forEach(b=>{{b.disabled=true;b.classList.remove('on')}});
      btn.classList.add('on'); ack.hidden=false;
      if(action==='like'){{ack.textContent='Avec plaisir ! Votre conseiller revient vers vous très vite.';}}
      else{{ack.textContent='C\\'est noté, merci.'; if(reasons) reasons.hidden=false;}}
      post({{bien_id:bien,action,envoi_id:env}});
    }});
  }});
  if(reasons){{reasons.querySelectorAll('.rchip').forEach(ch=>{{
    ch.addEventListener('click',()=>{{
      reasons.querySelectorAll('.rchip').forEach(x=>x.classList.remove('on')); ch.classList.add('on');
      ack.textContent='Merci, ça nous aide à affiner nos propositions.';
      post({{bien_id:bien,action:'pass',reason:ch.getAttribute('data-reason'),envoi_id:env}});
    }});
  }});}}
  const qs=card.querySelector('.qsend');
  if(qs){{qs.addEventListener('click',async()=>{{
    const ta=card.querySelector('.qtext'); const t=ta.value.trim(); if(!t)return;
    qs.disabled=true; const qa=card.querySelector('.qack'); qa.hidden=false; qa.textContent='Message envoyé à votre conseiller. Il vous répond directement.';
    try{{await fetch(MSG,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{bien_id:bien,text:t,envoi_id:env}})}});}}catch(e){{}}
  }});}}
}});
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
