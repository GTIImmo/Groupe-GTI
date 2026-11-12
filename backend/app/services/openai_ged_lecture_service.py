from __future__ import annotations

import json
import re
from typing import Any

import requests
from fastapi import HTTPException

from ..settings import Settings
from . import agent_registry
from .ged_garde_rib import nom_dit_rib, texte_porte_un_rib
from .openai_ged_classement_service import OpenAIGedClassementService, cout_usd
from .openai_listing_sheet_service import _extract_output_text

# ---------------------------------------------------------------------------
# GED (12/11/2026, morceau 6) -- LES FICHES DE LECTURE : l'IA LIT des valeurs dans un document déjà déposé et classé.
# L'IA EXTRAIT ; notre code comparera (morceau 7). Rien ne s'écrit sur le bien. Chaque valeur : {v, page, etat} avec
# etat lu / incertain / non_vu (« non_vu » = pas dans ce qu'on lui a montré, JAMAIS « absent du document »).
# Schéma STRICT : le modèle ne peut rendre QUE les champs de la fiche (ni date de naissance, ni numéro de pièce, ni IBAN).
# Lot 1 : l'état des risques, le DPE, le dossier de diagnostics (catalogue : E_synthese_catalogue.md §5, fiches 1 à 3).
# ---------------------------------------------------------------------------

AGENT_KEY = "ged_lecture"
MAX_PAGES_HD = 6
MAX_IMAGE_HD_OCTETS = 1_600_000
MAX_TEXTE = 20000

_ETAT = {"type": "string", "enum": ["lu", "incertain", "non_vu"]}


def _champ(sorte: str, enum: list[str] | None = None) -> dict[str, Any]:
    v: dict[str, Any] = {"type": ["number", "null"]} if sorte == "num" else {"type": ["string", "null"]}
    if enum:
        v = {"type": ["string", "null"], "enum": [*enum, None]}
    if sorte == "date":
        v["description"] = "AAAA-MM-JJ"
    return {"type": "object", "additionalProperties": False, "required": ["v", "page", "etat"],
            "properties": {"v": v, "page": {"type": ["integer", "null"]}, "etat": _ETAT}}


CLASSES = ["A", "B", "C", "D", "E", "F", "G"]
DIAGNOSTICS = ["dpe", "erp", "amiante", "plomb", "termites", "electricite", "gaz", "surface", "assainissement",
               "merule", "audit", "autre"]

# Une fiche : version (dans le nom enregistré), consigne propre, champs simples, et au plus une liste.
FICHES: dict[str, dict[str, Any]] = {
    "diag.erp": {
        "version": 1,
        "consigne": "C'est un état des risques et pollutions (ERP). date_etablissement : la date à laquelle CET état a "
                    "été établi ou signé par le vendeur ou son mandataire — PAS la date de l'arrêté préfectoral cité "
                    "dedans. commune et code_insee : ceux du bien.",
        "champs": {"date_etablissement": ("date", None), "commune": ("txt", None), "code_insee": ("txt", None)},
    },
    "diag.dpe": {
        "version": 1,
        "consigne": "C'est un diagnostic de performance énergétique (DPE). modele : « 2021 » s'il porte un numéro ADEME "
                    "de 13 caractères et deux étiquettes énergie et climat, sinon « ancien ». conso_ep : la "
                    "consommation d'énergie PRIMAIRE en kWh/m²/an ; conso_ef : l'énergie FINALE si elle est imprimée ; "
                    "emissions : kg CO2/m²/an. date_validite : telle qu'imprimée. diagnostiqueur_societe : la société, "
                    "pas la personne.",
        "champs": {"modele": ("txt", ["2021", "ancien", "inconnu"]), "numero_ademe": ("txt", None),
                   "date_etablissement": ("date", None), "date_validite": ("date", None),
                   "classe_energie": ("txt", CLASSES), "classe_ges": ("txt", CLASSES), "conso_ep": ("num", None),
                   "emissions": ("num", None), "conso_ef": ("num", None), "surface_reference": ("num", None),
                   "methode": ("txt", None), "diagnostiqueur_societe": ("txt", None), "commune": ("txt", None)},
    },
    "diag.dossier": {
        "version": 1,
        "consigne": "C'est un dossier de diagnostic technique (plusieurs diagnostics réunis). Lis la synthèse ou le "
                    "sommaire : pour CHAQUE diagnostic présent, son nom (dans la liste donnée), la date de son "
                    "rapport, sa conclusion en quelques mots (par exemple « présence d'amiante », « anomalies », "
                    "« classe D ») et la page où il commence. Si la page du DPE est lisible, remplis aussi les champs "
                    "dpe_*. commune : celle du bien.",
        "champs": {"commune": ("txt", None), "dpe_classe_energie": ("txt", CLASSES), "dpe_classe_ges": ("txt", CLASSES),
                   "dpe_conso_ep": ("num", None), "dpe_emissions": ("num", None), "dpe_date": ("date", None)},
        "liste": ("diagnostics", {"diagnostic": ("txt", DIAGNOSTICS), "date_rapport": ("date", None),
                                  "conclusion": ("txt", None)}),
    },
}

_CONSIGNE_COMMUNE = (
    "Tu lis un document d'une agence immobilière française pour en relever quelques valeurs. Rends UNIQUEMENT les champs "
    "demandés. Pour chaque champ : v = la valeur (dates en AAAA-MM-JJ, nombres sans unité avec un point décimal), "
    "page = la page où tu l'as lue, etat = « lu » si tu l'as lue nettement, « incertain » si tu hésites (écriture, "
    "scan pâle, jour et mois ambigus), « non_vu » si elle n'est pas dans ce qu'on te montre (v = null). N'invente rien. "
    "ce_type : faux si ce document n'est manifestement pas du type annoncé. Ne recopie jamais un nom de personne, une "
    "date de naissance, une adresse personnelle, un numéro fiscal ou bancaire.\n"
)

agent_registry.DEFAULT_SPECS.setdefault(AGENT_KEY, agent_registry.AgentSpec(AGENT_KEY, _CONSIGNE_COMMUNE, "gpt-6-luna", 1800))


def schema(fiche: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {"ce_type": {"type": "boolean"}}
    for cle, (sorte, enum) in fiche["champs"].items():
        props[cle] = _champ(sorte, enum)
    if fiche.get("liste"):
        nom, champs = fiche["liste"]
        props[nom] = {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": [*champs.keys(), "page"],
            "properties": {**{c: _champ(s, e) for c, (s, e) in champs.items()}, "page": {"type": ["integer", "null"]}},
        }}
    return {"type": "object", "additionalProperties": False, "required": list(props.keys()), "properties": props}


def _valeur(sorte: str, enum: list[str] | None, brut: Any) -> tuple[str | None, float | None, str | None]:
    # (texte, nombre, date) normalisés ; une valeur qui ne tient pas sa forme est jetée (None)
    if brut is None or brut == "":
        return None, None, None
    if sorte == "num":
        try:
            x = float(brut)
            return None, x, None
        except (TypeError, ValueError):
            return None, None, None
    texte = re.sub(r"\s+", " ", str(brut)).strip()[:200]
    if sorte == "date":
        return (None, None, texte) if re.fullmatch(r"(19[5-9]\d|20\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])", texte) else (None, None, None)
    if enum and texte not in enum:
        return None, None, None
    return texte or None, None, None


def normaliser(brut: Any, fiche: dict[str, Any], nb_pages: int) -> tuple[bool, list[dict[str, Any]]]:
    if not isinstance(brut, dict):
        raise HTTPException(status_code=502, detail="Réponse de lecture inattendue")
    valeurs: list[dict[str, Any]] = []

    def ajouter(cle: str, rang: int, sorte: str, enum: list[str] | None, champ: Any) -> None:
        champ = champ if isinstance(champ, dict) else {}
        etat = champ.get("etat") if champ.get("etat") in {"lu", "incertain", "non_vu"} else "non_vu"
        texte, nombre, date = _valeur(sorte, enum, champ.get("v"))
        if texte is None and nombre is None and date is None:
            etat = "non_vu"
        page = champ.get("page") if isinstance(champ.get("page"), int) and 1 <= champ["page"] <= max(nb_pages, 1) else None
        valeurs.append({"cle": cle, "rang": rang, "valeur": texte, "valeur_num": nombre, "valeur_date": date, "page": page, "etat": etat})

    for cle, (sorte, enum) in fiche["champs"].items():
        ajouter(cle, 0, sorte, enum, brut.get(cle))
    if fiche.get("liste"):
        nom, champs = fiche["liste"]
        for rang, item in enumerate((brut.get(nom) or [])[:30]):
            if isinstance(item, dict):
                for c, (s, e) in champs.items():
                    ajouter(f"{nom}.{c}", rang, s, e, item.get(c))
    return bool(brut.get("ce_type", True)), valeurs


def verifier_image_hd(data_url: str) -> str:
    # même forme que la vignette, plafond plus haut (une page lisible)
    m = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)", data_url.strip())
    if not m or len(m.group(2)) * 3 // 4 > MAX_IMAGE_HD_OCTETS:
        raise HTTPException(status_code=413, detail="Page trop lourde ou invalide")
    return data_url.strip()


class OpenAIGedLectureService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.portier = OpenAIGedClassementService(settings)  # interrupteur, plafond du jour

    def _headers(self) -> dict[str, str]:
        key = self.settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}"}

    def classement_du_travail(self, job_id: str) -> dict[str, Any] | None:
        r = requests.get(f"{self.settings.supabase_url}/rest/v1/app_ged_classement", headers=self._headers(),
                         params={"app_console_job_id": f"eq.{job_id}", "select": "id,hektor_annonce_id,type_code,decide_par,document_name", "limit": "1"}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Classement illisible")
        rows = r.json() or []
        return rows[0] if rows else None

    def type_sensible(self, code: str) -> bool:
        return any(t.get("code") == code and t.get("sensible") for t in self.portier.types())

    def lire(self, classement: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY non configure sur le backend")
        code = str(classement.get("type_code") or "")
        fiche = FICHES.get(code)
        if not fiche:
            raise HTTPException(status_code=422, detail="Pas de fiche de lecture pour ce type")
        if self.type_sensible(code):
            raise HTTPException(status_code=422, detail="Pièce des personnes : lue plus tard (morceau 9)")
        nom = str(payload.get("nomFichier") or classement.get("document_name") or "")
        texte = str(payload.get("texte") or "")[:MAX_TEXTE]
        pages = payload.get("pages") or []
        nb_pages = int(payload.get("nbPages") or len(pages) or 1)
        if nom_dit_rib(nom) or texte_porte_un_rib(texte):
            raise HTTPException(status_code=422, detail="Relevé d'identité bancaire : jamais envoyé à l'IA")
        if not pages and not texte.strip():
            raise HTTPException(status_code=400, detail="Rien à lire")
        if len(pages) > MAX_PAGES_HD:
            raise HTTPException(status_code=413, detail=f"{MAX_PAGES_HD} pages au plus")
        contenu: list[dict[str, Any]] = []
        for p in pages:
            contenu.append({"type": "input_text", "text": f"Page {int(p.get('numero') or 0)} sur {nb_pages}"})
            contenu.append({"type": "input_image", "image_url": verifier_image_hd(str(p.get("image") or "")), "detail": "high"})
        if self.portier.depense_du_jour() >= 2.0:
            raise HTTPException(status_code=429, detail="Plafond de dépense du jour atteint : lecture en pause")

        spec = agent_registry.load_spec(self.settings, AGENT_KEY)
        model = spec.model or "gpt-6-luna"
        entete = f"Type annoncé : {code}\nNombre de pages du document : {nb_pages}"
        if texte.strip():
            entete += f"\nTexte du document :\n{texte}"
        requete: dict[str, Any] = {
            "model": model, "store": False,
            "instructions": spec.instructions + fiche["consigne"],
            "input": [{"role": "user", "content": [{"type": "input_text", "text": entete}, *contenu]}],
            "text": {"format": {"type": "json_schema", "name": "ged_lecture", "strict": True, "schema": schema(fiche)}},
            "max_output_tokens": spec.max_output_tokens,
        }
        if not model.startswith("gpt-4"):
            requete["reasoning"] = {"effort": "none"}
        reponse = requests.post("https://api.openai.com/v1/responses",
                                headers={"Authorization": f"Bearer {self.settings.openai_api_key}", "Content-Type": "application/json"},
                                json=requete, timeout=90)
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
            raise HTTPException(status_code=502, detail="Réponse de lecture non JSON") from exc
        ce_type, valeurs = normaliser(brut, fiche, nb_pages)
        usage = corps.get("usage") or {}
        etat = "pas_ce_type" if not ce_type else ("lu" if any(v["etat"] != "non_vu" for v in valeurs) else "incomplet")
        return {"fiche": f"{code}/{fiche['version']}", "model": model, "etat": etat, "valeurs": valeurs, "usage": usage,
                "costUsd": cout_usd(model, usage), "pagesLues": [int(p.get("numero") or 0) for p in pages], "parTexte": not pages}

    def enregistrer(self, classement: dict[str, Any], resultat: dict[str, Any], user_id: str | None) -> str:
        ligne = {"classement_id": classement["id"], "hektor_annonce_id": classement["hektor_annonce_id"],
                 "type_code": classement["type_code"], "fiche": resultat["fiche"], "modele": resultat["model"],
                 "etat": resultat["etat"], "pages_lues": resultat["pagesLues"] or None, "par_texte": resultat["parTexte"],
                 "input_tokens": resultat["usage"].get("input_tokens"), "output_tokens": resultat["usage"].get("output_tokens"),
                 "cout_usd": resultat["costUsd"], "lu_par": user_id}
        r = requests.post(f"{self.settings.supabase_url}/rest/v1/app_ged_lecture",
                          headers={**self._headers(), "Prefer": "return=representation"}, json=[ligne], timeout=15)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Lecture non enregistrée")
        lecture_id = r.json()[0]["id"]
        lignes = [{**v, "lecture_id": lecture_id} for v in resultat["valeurs"]]
        if lignes:
            r = requests.post(f"{self.settings.supabase_url}/rest/v1/app_ged_valeur", headers=self._headers(), json=lignes, timeout=15)
            if not r.ok:
                raise HTTPException(status_code=503, detail="Valeurs lues non enregistrées")
        return lecture_id

