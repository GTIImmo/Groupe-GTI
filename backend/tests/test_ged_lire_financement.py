"""GED morceau 9, lot 9d (16/11/2026) — lire la pièce de FINANCEMENT : sa nature, sa date, ses emprunteurs. Rien d'autre.

Lancer depuis backend/ :  PYTHONIOENCODING=utf-8 ../.venv/Scripts/python.exe tests/test_ged_lire_financement.py
Aucun appel réseau. Vérifie : la fiche à part (dans FICHES_PERSONNES), le schéma STRICT et ce qui n'est JAMAIS demandé
(montant, taux, durée, banque, assurance, revenus, compte), la PREMIÈRE PAGE SEULE redite par le serveur (texte et
images), la garde RIB qui regarde TOUT ce qui arrive, la porte fermée sans l'interrupteur, l'état civil toujours fermé.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import HTTPException

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


print("1) la fiche")
fiche = lec.FICHES_PERSONNES.get("transaction.financement")
voir(fiche is not None and "transaction.financement" not in lec.FICHES, "le financement a sa fiche, À PART (avec les pièces des personnes)")
voir(strict_partout(lec.schema(fiche)), "schéma STRICT : tous les champs obligatoires, aucun en plus")
sch = lec.schema(fiche)["properties"]
voir(set(sch) == {"ce_type", "nature", "date_document", "personnes"}, "trois choses seulement : la nature, la date, les emprunteurs")
voir(set(sch["personnes"]["items"]["properties"]) == {"qualite", "nom", "nom_usage", "prenoms", "page"}, "d'un emprunteur : sa qualité et son nom, rien d'autre")
tout = " ".join(list(sch) + list(sch["personnes"]["items"]["properties"]))
jamais = ("montant", "taux", "duree", "mensualit", "cout", "banque", "courtier", "apport", "revenu", "assurance", "sante",
          "iban", "compte", "numero", "adresse", "naissance")
voir(not any(j in tout for j in jamais), "TÉMOIN : jamais montant, taux, durée, banque, apport, revenus, assurance, compte, adresse")
voir(fiche.get("premiere_page_seule") is True and fiche.get("texte_max", 99999) <= 6000, "la première page seule, 6 000 caractères au plus")
voir(all(m in fiche["consigne"] for m in ("PREMIÈRE", "JAMAIS", "assurance", "santé", "montant", "taux")), "la consigne le dit aussi")
voir("justif.rib" not in lec.FICHES_PERSONNES and "justif.rib" not in lec.FICHES, "TÉMOIN : le RIB n'a toujours aucune fiche")

print("2) la normalisation")
_, vals = lec.normaliser({"ce_type": True, "nature": L("offre_de_pret"), "date_document": L("2026-10-02"),
                          "personnes": [{"qualite": L("emprunteur"), "nom": L("DUPONT"), "nom_usage": L(None, "non_vu"), "prenoms": L("Paul"), "page": 1}]}, fiche, 1)
par = {(v["cle"], v["rang"]): v for v in vals}
voir(par[("nature", 0)]["valeur"] == "offre_de_pret" and par[("date_document", 0)]["valeur_date"] == "2026-10-02", "la nature et la date")
voir(par[("personnes.nom", 0)]["valeur"] == "DUPONT" and par[("personnes.qualite", 0)]["valeur"] == "emprunteur", "l'emprunteur et sa qualité")
_, vals = lec.normaliser({"ce_type": True, "nature": L("pret_relais"), "date_document": L("1938-04-02"), "personnes": []}, fiche, 1)
par = {v["cle"]: v for v in vals}
voir(par["nature"]["etat"] == "non_vu" and par["date_document"]["etat"] == "non_vu",
     "TÉMOIN : une nature hors liste est jetée, une date de 1938 n'est pas la date d'une offre")


class Settings:
    supabase_url = "https://x.supabase.co"
    supabase_service_role_key = "cle"
    openai_api_key = "sk-test"
    openai_vision_model = "gpt-4.1-mini"


class Portier:
    def types(self):
        return [{"code": c, "sensible": True} for c in ("justif.identite", "transaction.renseignements", "transaction.financement", "justif.etat_civil")] + \
               [{"code": c, "sensible": False} for c in lec.FICHES]

    def depense_du_jour(self):
        return 0.0


def appel_interdit(*a, **k):
    raise AssertionError("aucun appel ne devait partir")


parti = {}


class Reponse:
    ok = True

    def json(self):
        import json
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(
            {"ce_type": True, "nature": L("accord_de_principe"), "date_document": L("2026-10-02"), "personnes": []})}]}], "usage": {}}


def capter(url, headers=None, json=None, timeout=None):
    parti.clear()
    parti.update(json)
    return Reponse()


lec.agent_registry.load_spec = lambda settings, key: lec.agent_registry.DEFAULT_SPECS[key]
s = lec.OpenAIGedLectureService(Settings())
s.portier = Portier()
img = "data:image/jpeg;base64," + "A" * 40
FIN = {"type_code": "transaction.financement"}

print("3) la porte")
lec.requests.post = appel_interdit
try:
    s.lire(FIN, {"texte": "x"})
    voir(False, "porte")
except HTTPException as e:
    voir(e.status_code == 422 and "fermée" in str(e.detail), "SANS l'interrupteur des personnes : refusé avant tout appel")
try:
    s.lire(FIN, {"texte": "--- page 1 ---\nOffre de prêt\n--- page 7 ---\nIBAN FR76 3000 6000 0112 3456 7890 189"}, personnes=True)
    voir(False, "rib")
except HTTPException as e:
    voir(e.status_code == 422 and "bancaire" in str(e.detail), "un IBAN en page 7 : refusé -- la garde RIB regarde TOUT ce qui arrive, pas seulement la 1re page")

print("4) la première page seule, redite par le serveur")
lec.requests.post = capter
texte = "--- page 1 ---\nOFFRE DE PRET emise le 02/10/2026 emprunteur DUPONT Paul\n--- page 2 ---\nASSURANCE EMPRUNTEUR questionnaire de sante\n--- page 3 ---\nMONTANT 250000"
r = s.lire(FIN, {"texte": texte, "nbPages": 3, "pages": [{"numero": 1, "image": img}, {"numero": 2, "image": img}, {"numero": 3, "image": img}]}, personnes=True)
envoye = parti["input"][0]["content"][0]["text"]
images = [c for c in parti["input"][0]["content"] if c["type"] == "input_image"]
voir("OFFRE DE PRET" in envoye and "ASSURANCE" not in envoye and "sante" not in envoye and "MONTANT" not in envoye,
     "le texte s'arrête au repère de la page 2 : ni l'assurance, ni la santé, ni le montant ne partent")
voir(len(images) == 1 and r["pagesLues"] == [1], "une seule image part : la page 1 (les pages 2 et 3 sont retirées)")
voir(r["etat"] == "lu" and any(v["cle"] == "nature" and v["valeur"] == "accord_de_principe" for v in r["valeurs"]), "la lecture rend la nature")
s.lire(FIN, {"texte": "", "nbPages": 3, "pages": [{"numero": 1, "image": img}]}, personnes=True)
voir(len([c for c in parti["input"][0]["content"] if c["type"] == "input_image"]) == 1, "un scan : sa page 1 en image")
lec.requests.post = appel_interdit
try:
    s.lire(FIN, {"texte": "", "nbPages": 3, "pages": [{"numero": 3, "image": img}]}, personnes=True)
    voir(False, "page 3")
except HTTPException as e:
    voir(e.status_code == 400, "TÉMOIN : seule la page 3 envoyée -> retirée -> « rien à lire », AUCUN appel")
lec.requests.post = capter
s.lire({"type_code": "transaction.renseignements"}, {"texte": "--- page 1 ---\nVendeur A\n--- page 2 ---\nVendeur B", "nbPages": 2}, personnes=True)
voir("Vendeur B" in parti["input"][0]["content"][0]["text"], "TÉMOIN : les autres types gardent toutes leurs pages (la fiche de renseignements, page 2 comprise)")

print(f"\nTOUT EST VERT ({ok})")
