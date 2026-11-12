"""GED morceau 4 (12/11/2026) — l'IA propose le type d'un document avant son envoi.

Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_ged_classer.py
Aucun appel reseau : requests.get / requests.post sont remplaces par des faux.
Verifie : la garde RIB (memes exemples que test_ged_classement_ia.cjs), le refus AVANT tout appel,
store:false et la basse definition, le plafond du jour, l'interrupteur, la reponse nettoyee.
"""
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import HTTPException

from app.routers.ged import autorise
from app.services import openai_ged_classement_service as svc
from app.services.ged_garde_rib import iban_valide, nom_dit_rib, texte_porte_un_rib

ok = 0


def voir(vrai, libelle):
    global ok
    assert vrai, libelle
    ok += 1
    print("  VERT  " + libelle)


print("1) la garde RIB")
voir(iban_valide("FR7630006000011234567890189"), "un IBAN francais valide est reconnu")
voir(texte_porte_un_rib("Titulaire : X\nIBAN : FR76 3000 6000 0112 3456 7890 189\nBIC : AGRIFRPP"), "un IBAN en blocs, suivi du BIC")
voir(texte_porte_un_rib("compte FR7630006000011234567890189 ouvert"), "un IBAN colle")
voir(texte_porte_un_rib("RELEVÉ D’IDENTITÉ BANCAIRE"), "la phrase « relevé d'identité bancaire », accents et apostrophe courbe")
voir(not texte_porte_un_rib("FR76 3000 6000 0112 3456 7890 188"), "TÉMOIN : une clé de contrôle fausse n'est pas un IBAN")
voir(not texte_porte_un_rib("Diagnostic de performance énergétique, réf. DP12345678901234, classe D"), "TÉMOIN : un DPE n'est pas un RIB")
voir(not texte_porte_un_rib(None) and not texte_porte_un_rib(""), "TÉMOIN : pas de texte, pas de RIB")
voir(nom_dit_rib("RIB vendeur.pdf") and nom_dit_rib("rib_dupont.jpg") and nom_dit_rib("IBAN.png"), "un nom qui dit RIB ou IBAN")
voir(nom_dit_rib("Relevé d'identité bancaire.pdf"), "un nom qui dit « identité bancaire »")
voir(not nom_dit_rib("Attribution.pdf") and not nom_dit_rib("Ribeiro compromis.pdf") and not nom_dit_rib("DPE.pdf"), "TÉMOIN : « Attribution », « Ribeiro », « DPE » ne disent pas RIB")

print("2) l'interrupteur")
voir(autorise("admin", "admin", True) and not autorise("admin", "commercial", True), "cran admin : l'admin oui, le négociateur non")
voir(autorise("on", "commercial", True) and not autorise("on", "commercial", False), "cran on : tout actif, jamais un inactif")
voir(not autorise("off", "admin", True), "éteint : personne")


class Faux:
    def __init__(self, ok=True, data=None):
        self.ok, self._data, self.text = ok, data, ""

    def json(self):
        return self._data


class Settings:
    supabase_url = "https://x.supabase.co"
    supabase_service_role_key = "cle"
    openai_api_key = "sk-test"
    openai_vision_model = "gpt-4.1-mini"


TYPES = [{"code": "diag.dpe", "libelle": "DPE"}, {"code": "diag.erp", "libelle": "État des risques"},
         {"code": "transaction.avant_contrat", "libelle": "Compromis"}, {"code": "justif.rib", "libelle": "RIB"}]
envoyes = []
depense = [0.0]


def faux_get(url, headers=None, params=None, timeout=None):
    if url.endswith("/app_ged_type"):
        return Faux(data=TYPES)
    if url.endswith("/app_agent_run"):
        return Faux(data=[{"cost_usd": depense[0]}])
    if url.endswith("/app_agent_prompt"):
        return Faux(data=[])
    if url.endswith("/app_setting"):
        return Faux(data=[{"value": "admin"}])
    raise AssertionError(url)


reponse_ia = {"type_code": "diag.dpe", "confiance": "haute", "nom_propose": "DPE 2024", "pieces": [],
              "sensible": False, "lisible": True, "remarque": ""}


def faux_post(url, headers=None, json=None, timeout=None):
    import json as j
    envoyes.append(json)
    return Faux(data={"output_text": j.dumps(reponse_ia), "usage": {"input_tokens": 1000, "output_tokens": 100}})


svc.requests.get = faux_get
svc.requests.post = faux_post
svc.agent_registry.requests.get = faux_get
vignette = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8" + b"0" * 2000).decode()
service = svc.OpenAIGedClassementService(Settings())

print("3) le refus AVANT tout appel")
for nom, texte, libelle in [("RIB.pdf", None, "nom RIB"), ("scan.pdf", "IBAN FR76 3000 6000 0112 3456 7890 189", "IBAN dans le texte")]:
    try:
        service.classer({"nomFichier": nom, "texte": texte, "pages": [{"numero": 1, "image": vignette}], "nbPages": 1})
        voir(False, libelle)
    except HTTPException as e:
        voir(e.status_code == 422 and not envoyes, f"{libelle} : refusé (422), rien n'est parti chez OpenAI")
try:
    service.classer({"nomFichier": "x.pdf", "pages": [{"numero": 1, "image": "data:image/jpeg;base64," + base64.b64encode(b"0" * 500_000).decode()}]})
    voir(False, "vignette lourde")
except HTTPException as e:
    voir(e.status_code == 413 and not envoyes, "une image en haute définition est refusée (413), rien n'est parti")
depense[0] = 2.5
try:
    service.classer({"nomFichier": "x.pdf", "pages": [{"numero": 1, "image": vignette}], "nbPages": 1})
    voir(False, "plafond")
except HTTPException as e:
    voir(e.status_code == 429 and not envoyes, "plafond du jour atteint : refusé (429), rien n'est parti")
depense[0] = 0.0

print("4) l'appel")
r = service.classer({"nomFichier": "IMG_2041.jpg", "hektorAnnonceId": "62774", "pages": [{"numero": 1, "image": vignette}], "nbPages": 1})
req = envoyes[-1]
voir(req["store"] is False, "store: false")
voir(all(c.get("detail") == "low" for c in req["input"][0]["content"] if c["type"] == "input_image"), "les images partent en basse définition")
voir(req["text"]["format"]["strict"] is True and req["text"]["format"]["schema"]["properties"]["type_code"]["enum"] == [t["code"] for t in TYPES], "schéma strict, le type ne sort que de la liste")
voir("62774" not in str(req), "le numéro du bien ne part pas chez OpenAI")
voir(req["reasoning"] == {"effort": "none"} and req["model"] == "gpt-6-luna", "gpt-6-luna, sans raisonnement")
voir(r["typeCode"] == "diag.dpe" and r["nomPropose"] == "DPE 2024" and r["costUsd"] == round(1000 * 0.1e-6 + 100 * 0.5e-6, 6), "réponse rendue avec son coût")

print("5) la réponse nettoyée")
n = svc.normaliser({**reponse_ia, "type_code": "justif.rib", "nom_propose": "RIB Dupont"}, [t["code"] for t in TYPES], 1)
voir(n["typeCode"] == "justif.rib" and n["nomPropose"] is None and n["pieces"] == [], "l'IA voit un RIB : seul le type est gardé")
n = svc.normaliser({**reponse_ia, "nom_propose": "CNI 123456789012"}, [t["code"] for t in TYPES], 1)
voir(n["nomPropose"] is None, "un nom proposé qui porte un long numéro est jeté")
pieces = [{"type_code": "transaction.avant_contrat", "page_debut": 1, "page_fin": 8}, {"type_code": "diag.dpe", "page_debut": 9, "page_fin": 12}]
voir(len(svc.normaliser({**reponse_ia, "pieces": pieces}, [t["code"] for t in TYPES], 12)["pieces"]) == 2, "deux pièces dans le fichier : rendues")
voir(svc.normaliser({**reponse_ia, "pieces": pieces}, [t["code"] for t in TYPES], 10)["pieces"] == [], "une page hors du fichier : pièce écartée, et une seule restante ne se sépare pas")
try:
    svc.normaliser({**reponse_ia, "type_code": "inconnu"}, [t["code"] for t in TYPES], 1)
    voir(False, "type inconnu")
except HTTPException as e:
    voir(e.status_code == 502, "un type hors liste est refusé")

print(f"\nTOUT EST VERT ({ok})")
