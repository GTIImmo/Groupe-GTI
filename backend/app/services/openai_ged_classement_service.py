from __future__ import annotations

import base64
import json
import re
import time
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings
from . import agent_registry
from .ged_garde_rib import nom_dit_rib, texte_porte_un_rib
from .openai_listing_sheet_service import _extract_output_text

# ---------------------------------------------------------------------------
# GED (12/11/2026, morceau 4) -- L'IA PROPOSE LE TYPE D'UN DOCUMENT AVANT SON ENVOI.
#
# Ce qui part : des vignettes BASSE definition (detail « low ») de quelques pages, un extrait
# du texte du PDF s'il en a un, et le nom du fichier. ⛔ Ni la fiche du bien, ni le nom du
# mandant : l'IA ne voit que le document (minimisation, pas de biais de confirmation).
# Ce qui revient : un type parmi les codes de app_ged_type, une confiance, un nom court SANS
# nom de personne, les pieces si le fichier en porte plusieurs. Rien n'est lu en valeurs ici
# (c'est le morceau 6) et RIEN ne s'ecrit sur le bien : l'ecran propose, l'humain choisit.
# `store: false` sur chaque appel. Un RIB n'est jamais envoye (ged_garde_rib, 2e verrou).
# ---------------------------------------------------------------------------

AGENT_KEY = "ged_classement"
INTERRUPTEUR = "ged_lecture_ia"
MAX_PAGES = 12
MAX_VIGNETTE_OCTETS = 400 * 1024
MAX_TEXTE_CARACTERES = 6000
PLAFOND_JOUR_USD = 2.0
_TYPES_TTL_SECONDES = 300.0

# Tarifs (USD par jeton, entree / sortie), pour le cout de chaque appel et le plafond du jour.
_TARIFS = {
    "gpt-6-luna": (0.10 / 1_000_000, 0.50 / 1_000_000),
    "gpt-5.6-luna": (0.20 / 1_000_000, 1.20 / 1_000_000),
    "gpt-4.1-mini": (0.40 / 1_000_000, 1.60 / 1_000_000),
}

_types_cache: tuple[float, list[dict[str, Any]]] | None = None


def cout_usd(model: str | None, usage: dict[str, Any]) -> float | None:
    tarif = _TARIFS.get(str(model or ""))
    entree, sortie = usage.get("input_tokens"), usage.get("output_tokens")
    if not tarif or not isinstance(entree, (int, float)) or not isinstance(sortie, (int, float)):
        return None
    return round(entree * tarif[0] + sortie * tarif[1], 6)


def schema(codes: list[str]) -> dict[str, Any]:
    # STRICT : petit schema, tous les champs obligatoires. Le type ne peut sortir que de la liste.
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["type_code", "confiance", "nom_propose", "pieces", "sensible", "lisible", "remarque"],
        "properties": {
            "type_code": {"type": "string", "enum": codes},
            "confiance": {"type": "string", "enum": ["haute", "moyenne", "basse"]},
            "nom_propose": {"type": "string"},
            "pieces": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["type_code", "page_debut", "page_fin"],
                    "properties": {
                        "type_code": {"type": "string", "enum": codes},
                        "page_debut": {"type": "integer"},
                        "page_fin": {"type": "integer"},
                    },
                },
            },
            "sensible": {"type": "boolean"},
            "lisible": {"type": "boolean"},
            "remarque": {"type": "string"},
        },
    }


_INSTRUCTIONS = (
    "Tu ranges les documents d'une agence immobiliere francaise (transaction : vente de biens). "
    "On te montre un document en vignettes basse definition (avec le numero de chaque page), parfois un extrait "
    "de son texte, et le nom du fichier. Dis de quel type il est, parmi cette liste et elle seule :\n"
    "{{types}}\n"
    "Regles :\n"
    "- type_code : le type du document entier ; s'il en contient plusieurs, celui de la premiere piece.\n"
    "- confiance : haute si le document le dit clairement (titre, en-tete, formulaire reconnaissable), moyenne si "
    "tu deduis, basse si tu devines.\n"
    "- nom_propose : un nom court (60 caracteres au plus) pour le classer, par exemple « DPE 2024 », « Compromis "
    "signe », « Taxe fonciere 2025 ». JAMAIS de nom de personne, d'adresse, de numero de piece, de compte ou de "
    "telephone.\n"
    "- pieces : remplis-la seulement si le fichier reunit PLUSIEURS documents distincts (par exemple un compromis "
    "puis un DPE puis un etat des risques) : une entree par document, avec ses pages de debut et de fin dans la "
    "numerotation donnee. Sinon, liste vide. Un dossier de diagnostics (DDT) reste UNE piece de type diag.dossier.\n"
    "- sensible : vrai pour une piece d'identite, un etat civil ou une decision de justice sur une personne, un "
    "financement, une fiche de renseignements personnels ou un releve d'identite bancaire.\n"
    "- lisible : faux si les vignettes ne permettent pas de reconnaitre le document.\n"
    "- remarque : une phrase au plus, sans donnee personnelle ; vide sinon.\n"
    "Ne recopie AUCUNE valeur du document (nom, date de naissance, numero, montant) : tu ranges, tu ne lis pas."
)

agent_registry.DEFAULT_SPECS.setdefault(
    AGENT_KEY, agent_registry.AgentSpec(AGENT_KEY, _INSTRUCTIONS, "gpt-6-luna", 700)
)


class OpenAIGedClassementService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # ── base (cle de service) ────────────────────────────────────────────────
    def _headers(self) -> dict[str, str]:
        key = self.settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}"}

    def interrupteur(self) -> str:
        # Absent, illisible ou en erreur = eteint (patron des interrupteurs a trois crans).
        try:
            r = requests.get(
                f"{self.settings.supabase_url}/rest/v1/app_setting",
                headers=self._headers(),
                params={"key": f"eq.{INTERRUPTEUR}", "select": "value", "limit": "1"},
                timeout=8,
            )
            rows = r.json() if r.ok else []
            valeur = str((rows[0] or {}).get("value") or "").strip().lower() if rows else ""
        except Exception:
            valeur = ""
        return valeur if valeur in {"on", "admin"} else "off"

    def types(self) -> list[dict[str, Any]]:
        global _types_cache
        maintenant = time.monotonic()
        if _types_cache and maintenant - _types_cache[0] < _TYPES_TTL_SECONDES:
            return _types_cache[1]
        r = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_ged_type",
            headers=self._headers(),
            params={"actif": "eq.true", "select": "code,libelle,famille,lecture,sensible", "order": "ordre.asc"},
            timeout=10,
        )
        if not r.ok:
            raise HTTPException(status_code=503, detail="Liste des types de documents illisible")
        rows = [row for row in (r.json() or []) if row.get("code")]
        if not rows:
            raise HTTPException(status_code=503, detail="Liste des types de documents vide")
        _types_cache = (maintenant, rows)
        return rows

    def depense_du_jour(self) -> float:
        debut = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
        r = requests.get(
            f"{self.settings.supabase_url}/rest/v1/app_agent_run",
            headers=self._headers(),
            params={"agent_key": f"eq.{AGENT_KEY}", "created_at": f"gte.{debut}", "select": "cost_usd"},
            timeout=10,
        )
        if not r.ok:
            # Une lecture ratee n'est jamais un vert : sans le compte, on n'appelle pas.
            raise HTTPException(status_code=503, detail="Depense du jour illisible : pas d'appel a l'IA")
        return float(sum(float(row.get("cost_usd") or 0) for row in (r.json() or [])))

    # ── l'appel ──────────────────────────────────────────────────────────────
    def classer(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY non configure sur le backend")
        nom = str(payload.get("nomFichier") or "").strip()
        texte = str(payload.get("texte") or "")[:MAX_TEXTE_CARACTERES]
        pages = payload.get("pages") or []
        nb_pages = int(payload.get("nbPages") or len(pages) or 0)

        # ⛔ 2e verrou RIB, AVANT tout appel.
        if nom_dit_rib(nom) or texte_porte_un_rib(texte):
            raise HTTPException(status_code=422, detail="Releve d'identite bancaire : jamais envoye a l'IA")
        if not pages and not texte.strip():
            raise HTTPException(status_code=400, detail="Rien a lire : ni page ni texte")
        if len(pages) > MAX_PAGES:
            raise HTTPException(status_code=413, detail=f"{MAX_PAGES} pages au plus")

        contenu: list[dict[str, Any]] = []
        for page in pages:
            numero = int(page.get("numero") or 0)
            image = verifier_vignette(str(page.get("image") or ""))
            contenu.append({"type": "input_text", "text": f"Page {numero} sur {nb_pages}"})
            contenu.append({"type": "input_image", "image_url": image, "detail": "low"})

        types = self.types()
        codes = [str(t["code"]) for t in types]
        if self.depense_du_jour() >= PLAFOND_JOUR_USD:
            raise HTTPException(status_code=429, detail="Plafond de depense du jour atteint : classement par l'IA en pause")

        spec = agent_registry.load_spec(self.settings, AGENT_KEY)
        model = spec.model or "gpt-6-luna"
        liste = "\n".join(f"- {t['code']} : {t.get('libelle') or ''}" for t in types)
        consigne = agent_registry.render(spec.instructions, {"types": liste})
        entete = f"Nom du fichier : {nom or '(sans nom)'}\nNombre de pages : {nb_pages}"
        if texte.strip():
            entete += f"\nExtrait du texte :\n{texte}"
        requete: dict[str, Any] = {
            "model": model,
            "store": False,
            "instructions": consigne,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": entete}, *contenu]}],
            "text": {"format": {"type": "json_schema", "name": "ged_classement", "strict": True, "schema": schema(codes)}},
            "max_output_tokens": spec.max_output_tokens,
        }
        if not model.startswith("gpt-4"):
            requete["reasoning"] = {"effort": "none"}
        reponse = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.settings.openai_api_key}", "Content-Type": "application/json"},
            json=requete,
            timeout=60,
        )
        if not reponse.ok:
            try:
                message = reponse.json().get("error", {}).get("message")
            except Exception:
                message = reponse.text.strip()[:300]
            raise HTTPException(status_code=502, detail=message or "Erreur OpenAI")
        corps = reponse.json()
        try:
            brut = json.loads(_extract_output_text(corps))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Reponse de l'IA non JSON") from exc
        resultat = normaliser(brut, codes, nb_pages)
        resultat["model"] = model
        resultat["usage"] = corps.get("usage") or {}
        resultat["costUsd"] = cout_usd(model, resultat["usage"])
        return resultat


def verifier_vignette(data_url: str) -> str:
    m = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)", data_url.strip())
    if not m:
        raise HTTPException(status_code=400, detail="Vignette invalide (JPEG, PNG ou WebP en base64)")
    try:
        octets = base64.b64decode(m.group(2), validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Vignette invalide") from exc
    if len(octets) > MAX_VIGNETTE_OCTETS:
        raise HTTPException(status_code=413, detail="Vignette trop lourde : la basse definition est obligatoire")
    return data_url.strip()


_NOM_INTERDIT = re.compile(r"\d{5,}|@")


def normaliser(brut: Any, codes: list[str], nb_pages: int) -> dict[str, Any]:
    if not isinstance(brut, dict) or brut.get("type_code") not in codes:
        raise HTTPException(status_code=502, detail="Reponse de l'IA inattendue")
    type_code = str(brut["type_code"])
    confiance = brut.get("confiance") if brut.get("confiance") in {"haute", "moyenne", "basse"} else "basse"
    if type_code == "justif.rib":
        # L'IA a reconnu un RIB malgre les gardes (photo au nom muet) : on ne garde QUE le type.
        return {"typeCode": type_code, "confiance": confiance, "nomPropose": None, "pieces": [], "sensible": True,
                "lisible": bool(brut.get("lisible", True)), "remarque": None}
    nom = re.sub(r"\s+", " ", str(brut.get("nom_propose") or "")).strip()[:60]
    if _NOM_INTERDIT.search(nom):
        nom = ""  # un long nombre ou une adresse e-mail n'a rien a faire dans un nom de document
    pieces = []
    for p in brut.get("pieces") or []:
        if not isinstance(p, dict) or p.get("type_code") not in codes:
            continue
        debut, fin = int(p.get("page_debut") or 0), int(p.get("page_fin") or 0)
        if 1 <= debut <= fin <= max(nb_pages, 1):
            pieces.append({"typeCode": str(p["type_code"]), "pageDebut": debut, "pageFin": fin})
    if len(pieces) < 2:
        pieces = []  # une seule piece = le fichier entier : rien a separer
    remarque = re.sub(r"\s+", " ", str(brut.get("remarque") or "")).strip()[:200] or None
    return {"typeCode": type_code, "confiance": confiance, "nomPropose": nom or None, "pieces": pieces,
            "sensible": bool(brut.get("sensible")), "lisible": bool(brut.get("lisible", True)), "remarque": remarque}
