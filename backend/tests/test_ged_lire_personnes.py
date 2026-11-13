"""GED morceau 9, lot 9a (13/11/2026) — lire la pièce d'identité et la fiche de renseignements.

Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_ged_lire_personnes.py
Aucun appel réseau. Vérifie : les deux fiches à part (FICHES inchangé), le schéma STRICT et ce qui n'est jamais demandé,
le numéro de la pièce gardé à part (jamais dans app_ged_valeur ni dans la réponse), la porte fermée sans l'interrupteur,
l'état civil et le financement toujours fermés, la garde RIB, et la route qui décide l'interrupteur par compte.
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


def L(v, etat="lu", page=1):
    return {"v": v, "page": page, "etat": etat}


print("1) les fiches")
voir(set(lec.FICHES_PERSONNES) == {"justif.identite", "transaction.renseignements"}, "deux fiches : la pièce d'identité et la fiche de renseignements")
voir(not set(lec.FICHES_PERSONNES) & set(lec.FICHES), "elles vivent À PART de FICHES (les 25 types lus ne bougent pas)")
voir(not {"justif.etat_civil", "transaction.financement", "justif.rib"} & (set(lec.FICHES) | set(lec.FICHES_PERSONNES)),
     "l'état civil et le financement restent fermés (9d) ; le RIB n'a aucune fiche")
voir(all(strict_partout(lec.schema(f)) for f in lec.FICHES_PERSONNES.values()), "schéma STRICT : tous les champs obligatoires, aucun en plus")
piece = lec.schema(lec.FICHES_PERSONNES["justif.identite"])["properties"]["pieces"]["items"]["properties"]
jamais = ("adresse", "nationalite", "sexe", "taille", "mrz", "signature", "photo", "telephone", "email", "profession")
voir(not any(j in c for c in piece for j in jamais), "pièce d'identité : jamais l'adresse, la nationalité, le sexe, la taille, la ligne codée, la signature")
pers = lec.schema(lec.FICHES_PERSONNES["transaction.renseignements"])["properties"]["personnes"]["items"]["properties"]
jamais_r = ("telephone", "email", "profession", "nationalite", "revenu", "banque", "iban", "compte", "fiscal", "secu", "enfant", "sante")
voir(not any(j in c for c in pers for j in jamais_r), "fiche de renseignements : jamais téléphone, e-mail, profession, revenus, banque, enfants, santé")
voir(lec.PRIVES == {"pieces.numero", "pieces.date_delivrance", "pieces.autorite_delivrance"}, "le registre : numéro, date et autorité de délivrance")
voir("EXCEPTION" in lec.FICHES_PERSONNES["justif.identite"]["consigne"] and "MRZ" in lec.FICHES_PERSONNES["justif.identite"]["consigne"],
     "la consigne dit l'exception, et interdit la ligne codée")

print("2) la normalisation")
fiche = lec.FICHES_PERSONNES["justif.identite"]
brut = {"ce_type": True, "pieces": [{
    "nature": L("cni_ancien_modele"), "nom": L("SPECIMEN"), "nom_usage": L(None, "non_vu"), "prenoms": L("Jeanne, Marie"),
    "date_naissance": L("1938-04-02"), "lieu_naissance": L("SAINT-ÉTIENNE (42)"), "numero": L("0612 42 3001 75"),
    "date_delivrance": L("2012-06-14"), "autorite_delivrance": L("Préfecture de la Loire"), "date_fin_validite": L("2022-06-13"),
    "page": 1}]}
_, vals = lec.normaliser(brut, fiche, 1)
par = {v["cle"]: v for v in vals}
voir(par["pieces.date_naissance"]["valeur_date"] == "1938-04-02", "une date de naissance d'avant 1950 est gardée")
voir(par["pieces.numero"]["valeur"] == "061242300175", "le numéro de la pièce est gardé (espaces retirés), malgré la règle des longs numéros")
voir(par["pieces.lieu_naissance"]["valeur"] == "SAINT-ÉTIENNE (42)", "le lieu de naissance, avec son département")
_, vals = lec.normaliser({**brut, "pieces": [{**brut["pieces"][0], "numero": L("06-12/42@"), "lieu_naissance": L("123456789012")}]}, fiche, 1)
par = {v["cle"]: v for v in vals}
voir(par["pieces.numero"]["etat"] == "non_vu" and par["pieces.lieu_naissance"]["etat"] == "non_vu",
     "TÉMOIN : un numéro mal formé est jeté, et un long numéro ailleurs que dans « numero » aussi")
_, vals = lec.normaliser({"ce_type": True, "date_document": L("1938-04-02"), "personnes": []}, lec.FICHES_PERSONNES["transaction.renseignements"], 1)
voir(next(v for v in vals if v["cle"] == "date_document")["etat"] == "non_vu", "TÉMOIN : une date de 1938 n'est gardée QUE comme date de naissance")
_, vals = lec.normaliser({"ce_type": True, "pieces": [brut["pieces"][0]] * 20}, fiche, 1)
voir(max(v["rang"] for v in vals) == lec.MAX_PERSONNES - 1, "12 pièces au plus")


class Settings:
    supabase_url = "https://x.supabase.co"
    supabase_service_role_key = "cle"
    openai_api_key = "sk-test"
    openai_vision_model = "gpt-4.1-mini"


class Portier:
    cran = "admin"

    def types(self):
        return [{"code": c, "sensible": True} for c in ("justif.identite", "transaction.renseignements", "transaction.financement", "justif.etat_civil")] + \
               [{"code": c, "sensible": False} for c in lec.FICHES]

    def depense_du_jour(self):
        return 0.0

    def interrupteur(self, cle="ged_lecture_ia"):
        return self.cran if cle == "ged_lecture_personnes" else "on"


def appel_interdit(*a, **k):
    raise AssertionError("aucun appel ne devait partir")


parti = {}
reponse_ia = {}


class Reponse:
    ok = True

    def json(self):
        import json
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(reponse_ia)}]}], "usage": {}}


def capter(url, headers=None, json=None, timeout=None):
    parti.clear()
    parti.update(json)
    return Reponse()


lec.agent_registry.load_spec = lambda settings, key: lec.agent_registry.DEFAULT_SPECS[key]
s = lec.OpenAIGedLectureService(Settings())
s.portier = Portier()
img = "data:image/jpeg;base64," + "A" * 40

print("3) la porte")
lec.requests.post = appel_interdit
for code, charge, libelle in [
    ("justif.identite", {"pages": [{"numero": 1, "image": img}], "nbPages": 1}, "pièce d'identité SANS l'interrupteur : refusée avant tout appel"),
    ("transaction.renseignements", {"texte": "x"}, "fiche de renseignements SANS l'interrupteur : refusée"),
]:
    try:
        s.lire({"type_code": code}, charge)
        voir(False, libelle)
    except HTTPException as e:
        voir(e.status_code == 422 and "fermée" in str(e.detail), libelle)
for code, libelle in [("transaction.financement", "le financement reste fermé MÊME avec l'interrupteur"),
                      ("justif.etat_civil", "l'état civil reste fermé MÊME avec l'interrupteur")]:
    try:
        s.lire({"type_code": code}, {"texte": "x"}, personnes=True)
        voir(False, libelle)
    except HTTPException as e:
        voir(e.status_code == 422, libelle)
try:
    s.lire({"type_code": "transaction.renseignements"}, {"texte": "Vendeur DUPONT IBAN FR76 3000 6000 0112 3456 7890 189"}, personnes=True)
    voir(False, "rib")
except HTTPException as e:
    voir(e.status_code == 422 and "bancaire" in str(e.detail), "un IBAN dans une fiche de renseignements : jamais envoyé (garde RIB inchangée)")
lec.FICHES["transaction.financement"] = lec.FICHES["diag.erp"]
try:
    s.lire({"type_code": "transaction.financement"}, {"texte": "x"}, personnes=True)
    voir(False, "sensible")
except HTTPException as e:
    voir(e.status_code == 422 and "morceau 9" in str(e.detail), "TÉMOIN : un type sensible hors des deux fiches reste refusé, même avec une fiche")
del lec.FICHES["transaction.financement"]

print("4) ce qui part, ce qui revient")
lec.requests.post = capter
reponse_ia.clear()
reponse_ia.update(brut)
r = s.lire({"type_code": "justif.identite"}, {"pages": [{"numero": 1, "image": img}], "nbPages": 1}, personnes=True)
voir(parti["store"] is False and "EXCEPTION" in parti["instructions"] and "pieces" in parti["text"]["format"]["schema"]["properties"],
     "la pièce part avec sa consigne et son schéma, et rien n'est gardé chez le fournisseur")
voir(not any(v["cle"] in lec.PRIVES for v in r["valeurs"]), "⛔ la réponse (et donc l'écran) ne porte NI le numéro NI la délivrance")
voir({v["cle"] for v in r["prives"]} == lec.PRIVES, "les trois valeurs privées sont mises à part")
voir(any(v["cle"] == "pieces.date_fin_validite" for v in r["valeurs"]) and r["etat"] == "lu", "la fin de validité et la date de naissance restent dans les valeurs lues")
reponse_ia.clear()
reponse_ia.update({**brut, "ce_type": False})
r = s.lire({"type_code": "justif.identite"}, {"pages": [{"numero": 1, "image": img}], "nbPages": 1}, personnes=True)
voir(r["etat"] == "pas_ce_type" and r["prives"] == [], "« pas ce type » : rien n'est gardé au registre")

print("5) l'enregistrement")
appels = []


class Rep:
    def __init__(self, ok=True, corps=None):
        self.ok = ok
        self.corps = corps

    def json(self):
        return self.corps


def poste(url, headers=None, json=None, timeout=None, echec_rpc=False):
    appels.append((url.rsplit("/", 1)[-1], json))
    if url.endswith("app_ged_lecture"):
        return Rep(True, [{"id": "lec-1"}])
    if url.endswith("app_ged_piece_privee_ecrire"):
        return Rep(not poste.echec_rpc, None)
    return Rep(True, None)


poste.echec_rpc = False
lec.requests.post = poste
reponse_ia.clear()
reponse_ia.update(brut)
lec.requests.post = capter
r = s.lire({"type_code": "justif.identite"}, {"pages": [{"numero": 1, "image": img}], "nbPages": 1}, personnes=True)
lec.requests.post = poste
r["usage"] = {}
s.enregistrer({"id": "c-1", "hektor_annonce_id": "63331", "type_code": "justif.identite"}, r, "u-1")
noms = [a[0] for a in appels]
voir(noms == ["app_ged_lecture", "app_ged_piece_privee_ecrire", "app_ged_valeur"], "ordre : la lecture, le registre, puis les valeurs")
voir({l["cle"] for l in appels[1][1]["p_lignes"]} == lec.PRIVES and appels[1][1]["p_lecture_id"] == "lec-1", "le registre reçoit les 3 valeurs privées, rattachées à la lecture")
voir(not any(l["cle"] in lec.PRIVES for l in appels[2][1]), "⛔ app_ged_valeur ne reçoit AUCUNE valeur privée")
appels.clear()
poste.echec_rpc = True
try:
    s.enregistrer({"id": "c-1", "hektor_annonce_id": "63331", "type_code": "justif.identite"}, r, "u-1")
    voir(False, "echec")
except HTTPException as e:
    voir(e.status_code == 503 and [a[0] for a in appels] == ["app_ged_lecture", "app_ged_piece_privee_ecrire"],
         "le registre refuse : erreur 503, et les valeurs ne partent pas")
appels.clear()
s.enregistrer({"id": "c-2", "hektor_annonce_id": "63331", "type_code": "diag.erp"},
              {"fiche": "diag.erp/1", "model": "m", "etat": "lu", "pagesLues": [], "parTexte": True, "usage": {}, "costUsd": 0,
               "valeurs": [{"cle": "commune", "rang": 0, "valeur": "Firminy", "valeur_num": None, "valeur_date": None, "page": 1, "etat": "lu"}]}, "u-1")
voir([a[0] for a in appels] == ["app_ged_lecture", "app_ged_valeur"], "TÉMOIN : un document du bien (sans « prives ») ne touche jamais le registre")
lec.requests.post = appel_interdit

print("6) la route décide l'interrupteur, compte par compte")


class User:
    id = "u-1"
    email = "frederic@exemple.fr"


class Admin:
    role = "admin"

    def load_profile(self, user):
        return {"role": self.role, "is_active": True}

    def insert_agent_run(self, row):
        return 1


class Service:
    def __init__(self, code, cran):
        self.portier = Portier()
        self.portier.cran = cran
        self.code = code
        self.recu = None

    def classement_du_travail(self, job_id):
        return {"id": "c-1", "hektor_annonce_id": "63331", "type_code": self.code, "decide_par": "u-1"}

    def lire(self, classement, payload, personnes=False):
        self.recu = personnes
        return {"fiche": "x/1", "model": "m", "etat": "lu", "valeurs": [], "prives": [], "usage": {}, "costUsd": 0,
                "pagesLues": [], "parTexte": True}

    def enregistrer(self, classement, resultat, user_id):
        return "lec-1"


route.get_authenticated_user = lambda settings, authorization: User()
charge = route.GedLirePayload(jobId="0" * 36, texte="x")
for code, cran, role, attendu, libelle in [
    ("justif.identite", "off", "admin", False, "interrupteur éteint : la pièce n'est pas ouverte, même pour un admin"),
    ("justif.identite", "admin", "admin", True, "cran admin + admin : ouverte"),
    ("justif.identite", "admin", "commercial", False, "cran admin + négociateur : fermée"),
    ("justif.identite", "on", "commercial", True, "cran on : ouverte au négociateur"),
    ("diag.erp", "on", "admin", False, "TÉMOIN : un document du bien ne demande jamais l'interrupteur des personnes"),
]:
    a = Admin()
    a.role = role
    sv = Service(code, cran)
    rep = route.ged_lire(charge, "jeton", Settings(), a, sv)
    voir(sv.recu is attendu and "prives" not in rep, libelle)

print(f"\nTOUT EST VERT ({ok})")
