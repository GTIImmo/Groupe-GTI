"""GED morceau 6, lot 1 (12/11/2026) — les fiches de lecture et la route /ged/lire.

Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_ged_lire.py
Aucun appel réseau. Vérifie : le schéma STRICT (rien d'autre que les champs de la fiche), la normalisation (une valeur
qui ne tient pas sa forme est jetée), les refus AVANT tout appel (pièce des personnes, RIB, type sans fiche), et que la
route refuse le classement d'un autre.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import HTTPException

from app.routers import ged as route
from app.services import openai_ged_lecture_service as lec

ok = 0


def voir(vrai, libelle):
    global ok
    assert vrai, libelle
    ok += 1
    print("  VERT  " + libelle)


def strict_partout(s):
    if s.get("type") == "object" or "properties" in s:
        if s.get("additionalProperties") is not False or set(s.get("required", [])) != set(s.get("properties", {})):
            return False
        return all(strict_partout(v) for v in s["properties"].values())
    if s.get("type") == "array":
        return strict_partout(s["items"])
    return True


print("1) les fiches")
voir(set(lec.FICHES) == {"diag.erp", "diag.dpe", "diag.dossier"}, "lot 1 : état des risques, DPE, dossier de diagnostics")
voir(all(strict_partout(lec.schema(f)) for f in lec.FICHES.values()), "schéma STRICT partout : tous les champs obligatoires, aucun champ en plus")
interdits = ("naissance", "iban", "fiscal", "identite", "secu", "nom_", "prenom")
voir(not any(i in c for f in lec.FICHES.values() for c in lec.schema(f)["properties"] for i in interdits), "aucune fiche ne demande une donnée de personne")
voir("PAS la date de l'arrêté" in lec.FICHES["diag.erp"]["consigne"], "état des risques : la date de l'état, pas celle de l'arrêté")

print("2) la normalisation")
fiche = lec.FICHES["diag.dpe"]
brut = {"ce_type": True, **{c: {"v": None, "page": None, "etat": "non_vu"} for c in fiche["champs"]}}
brut.update({"date_etablissement": {"v": "15/01/2025", "page": 1, "etat": "lu"}, "classe_energie": {"v": "H", "page": 1, "etat": "lu"},
             "conso_ep": {"v": 214, "page": 9, "etat": "lu"}, "date_validite": {"v": "2035-01-14", "page": 1, "etat": "incertain"}})
ce_type, vals = lec.normaliser(brut, fiche, 2)
v = {x["cle"]: x for x in vals}
voir(v["date_etablissement"]["etat"] == "non_vu" and v["date_etablissement"]["valeur_date"] is None, "une date hors forme AAAA-MM-JJ est jetée (non_vu)")
voir(v["classe_energie"]["etat"] == "non_vu", "une classe hors A-G est jetée")
voir(v["conso_ep"]["valeur_num"] == 214 and v["conso_ep"]["page"] is None, "une page hors du document est effacée, la valeur gardée")
voir(v["date_validite"]["valeur_date"] == "2035-01-14" and v["date_validite"]["etat"] == "incertain", "« incertain » est gardé tel quel")
voir(ce_type is True and len(vals) == len(fiche["champs"]), "une ligne par champ, même non vu")
_, vals = lec.normaliser({"ce_type": False, "commune": {"v": "X", "page": 1, "etat": "lu"}, "diagnostics": [{"diagnostic": {"v": "amiante", "page": 4, "etat": "lu"}, "date_rapport": {"v": "2026-02-10", "page": 4, "etat": "lu"}, "conclusion": {"v": "absence", "page": 4, "etat": "lu"}, "page": 4}]}, lec.FICHES["diag.dossier"], 30)
voir(any(x["cle"] == "diagnostics.diagnostic" and x["rang"] == 0 and x["valeur"] == "amiante" for x in vals), "la liste du dossier : une ligne par champ et par rang")


class Settings:
    supabase_url = "https://x.supabase.co"
    supabase_service_role_key = "cle"
    openai_api_key = "sk-test"
    openai_vision_model = "gpt-4.1-mini"


class Portier:
    def types(self):
        return [{"code": "diag.erp", "sensible": False}, {"code": "transaction.financement", "sensible": True}]

    def depense_du_jour(self):
        return 0.0

    def interrupteur(self):
        return "admin"


def appel_interdit(*a, **k):
    raise AssertionError("aucun appel à OpenAI ne devait partir")


lec.requests.post = appel_interdit
s = lec.OpenAIGedLectureService(Settings())
s.portier = Portier()

print("3) les refus AVANT tout appel")
for classement, charge, attendu, libelle in [
    ({"type_code": "transaction.financement"}, {"texte": "offre de prêt"}, 422, "type sans fiche (et pièce des personnes) : refusé"),
    ({"type_code": "diag.erp", "document_name": "RIB.pdf"}, {"texte": "x"}, 422, "nom RIB : refusé"),
    ({"type_code": "diag.erp"}, {"texte": "IBAN FR76 3000 6000 0112 3456 7890 189"}, 422, "IBAN dans le texte : refusé"),
    ({"type_code": "diag.erp"}, {}, 400, "rien à lire : refusé"),
]:
    try:
        s.lire(classement, charge)
        voir(False, libelle)
    except HTTPException as e:
        voir(e.status_code == attendu, f"{libelle} ({e.status_code})")
lec.FICHES["transaction.financement"] = lec.FICHES["diag.erp"]
try:
    s.lire({"type_code": "transaction.financement"}, {"texte": "x"})
    voir(False, "sensible")
except HTTPException as e:
    voir(e.status_code == 422 and "personnes" in str(e.detail), "une pièce des personnes, même avec une fiche, attend le morceau 9")
del lec.FICHES["transaction.financement"]

print("4) la route")


class User:
    id = "u-1"
    email = "frederic@exemple.fr"


class Admin:
    def load_profile(self, user):
        return {"role": "admin", "is_active": True}

    def insert_agent_run(self, row):
        return 1


class Service:
    portier = Portier()

    def __init__(self, decide_par):
        self.decide_par = decide_par

    def classement_du_travail(self, job_id):
        return {"id": "c-1", "hektor_annonce_id": "62774", "type_code": "diag.erp", "decide_par": self.decide_par}

    def lire(self, *a):
        raise AssertionError("ne devait pas lire")


route.get_authenticated_user = lambda settings, authorization: User()
charge = route.GedLirePayload(jobId="0" * 36, texte="x")
try:
    route.ged_lire(charge, "jeton", Settings(), Admin(), Service("quelqu-un-d-autre"))
    voir(False, "autre")
except HTTPException as e:
    voir(e.status_code == 403, "le classement d'un autre : refusé (403), rien n'est lu")
Portier.interrupteur = lambda self: "off"
try:
    route.ged_lire(charge, "jeton", Settings(), Admin(), Service("u-1"))
    voir(False, "eteint")
except HTTPException as e:
    voir(e.status_code == 403, "interrupteur éteint : refusé (403)")

print(f"\nTOUT EST VERT ({ok})")
