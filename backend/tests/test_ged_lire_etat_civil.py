"""GED morceau 9, lot 9d-2 (16/11/2026) — lire une pièce d'ÉTAT CIVIL : sa nature, la date de l'acte, les époux,
partenaires ou le défunt. Une mesure de PROTECTION : sa nature SEULE.

Lancer depuis backend/ :  PYTHONIOENCODING=utf-8 ../.venv/Scripts/python.exe tests/test_ged_lire_etat_civil.py
Aucun appel réseau. Vérifie : la fiche à part (dans FICHES_PERSONNES), le schéma STRICT et ce qui n'est JAMAIS demandé
(enfants, parents, témoins, adresse, profession, cause de décès, motif, santé), la PREMIÈRE PAGE SEULE, et la garde du
serveur qui JETTE tout sauf la nature d'une mesure de protection, même si l'IA a rendu des noms ou des dates.
"""
import json, os, sys
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
fiche = lec.FICHES_PERSONNES.get("justif.etat_civil")
voir(fiche is not None and "justif.etat_civil" not in lec.FICHES, "l'état civil a sa fiche, À PART (avec les pièces des personnes)")
voir(strict_partout(lec.schema(fiche)), "schéma STRICT : tous les champs obligatoires, aucun en plus")
sch = lec.schema(fiche)["properties"]
voir(set(sch) == {"ce_type", "nature", "date_acte", "personnes"}, "trois choses seulement : la nature, la date de l'acte, les personnes")
voir(set(sch["personnes"]["items"]["properties"]) == {"qualite", "nom", "nom_usage", "prenoms", "page"}, "d'une personne : sa qualité et son nom, rien d'autre")
qualites = sch["personnes"]["items"]["properties"]["qualite"]["properties"]["v"]
voir("enfant" not in json.dumps(qualites) and "representant" not in json.dumps(qualites) and "protege" not in json.dumps(qualites),
     "TÉMOIN : ni enfant, ni personne protégée, ni représentant parmi les qualités")
tout = " ".join(list(sch) + list(sch["personnes"]["items"]["properties"]))
voir(not any(j in tout for j in ("enfant", "parent", "temoin", "adresse", "profession", "cause", "motif", "sante", "medecin", "mesure")),
     "TÉMOIN : jamais enfants, parents, témoins, adresse, profession, cause de décès, motif, santé, détail de la mesure")
voir(fiche.get("premiere_page_seule") is True and fiche.get("texte_max", 99999) <= 6000 and fiche.get("nature_seule") == ["protection"],
     "la première page seule, 6 000 caractères au plus, et la protection : sa nature seule")
voir(all(m in fiche["consigne"] for m in ("PREMIÈRE", "PROTECTION", "RIEN d'autre", "enfants", "santé")), "la consigne le dit aussi")
_, vals = lec.normaliser({"ce_type": True, "nature": L("acte_mariage"), "date_acte": L("1958-06-21"), "personnes": []}, fiche, 1)
voir(next(v for v in vals if v["cle"] == "date_acte")["valeur_date"] == "1958-06-21", "un mariage de 1958 est gardé (date dès 1900)")

print("2) la lecture, sans réseau")


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


parti = {}
reponse_ia = {}


class Reponse:
    ok = True

    def json(self):
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(reponse_ia)}]}], "usage": {}}


def capter(url, headers=None, json=None, timeout=None):
    parti.clear()
    parti.update(json)
    return Reponse()


lec.agent_registry.load_spec = lambda settings, key: lec.agent_registry.DEFAULT_SPECS[key]
s = lec.OpenAIGedLectureService(Settings())
s.portier = Portier()
EC = {"type_code": "justif.etat_civil"}
lec.requests.post = capter
DUPONT = {"qualite": L("epoux"), "nom": L("DUPONT"), "nom_usage": L(None, "non_vu"), "prenoms": L("Paul"), "page": 1}
MARTIN = {"qualite": L("epoux"), "nom": L("MARTIN"), "nom_usage": L("DUPONT"), "prenoms": L("Marie"), "page": 1}

reponse_ia.clear(); reponse_ia.update({"ce_type": True, "nature": L("acte_mariage"), "date_acte": L("1987-06-20"), "personnes": [DUPONT, MARTIN]})
r = s.lire(EC, {"texte": "--- page 1 ---\nACTE DE MARIAGE\n--- page 2 ---\nEnfants : Lucas DUPONT", "nbPages": 2}, personnes=True)
envoye = parti["input"][0]["content"][0]["text"]
voir("ACTE DE MARIAGE" in envoye and "Lucas" not in envoye, "la 1re page seule part (les enfants de la page 2 ne partent pas)")
cles = {v["cle"] for v in r["valeurs"]}
voir({"nature", "date_acte", "personnes.nom", "personnes.prenoms", "personnes.qualite"} <= cles and r["etat"] == "lu", "un mariage : la nature, la date, les deux époux")

reponse_ia.clear(); reponse_ia.update({"ce_type": True, "nature": L("protection"), "date_acte": L("2024-03-12"),
                                       "personnes": [{"qualite": L("autre"), "nom": L("PROTEGE"), "nom_usage": L(None, "non_vu"), "prenoms": L("Jean"), "page": 1}]})
r = s.lire(EC, {"texte": "--- page 1 ---\nJUGEMENT DE MISE SOUS TUTELLE", "nbPages": 1}, personnes=True)
voir([v["cle"] for v in r["valeurs"]] == ["nature"] and r["valeurs"][0]["valeur"] == "protection",
     "une PROTECTION : le serveur ne garde QUE la nature, même si l'IA a rendu un nom et une date")
voir(r["etat"] == "lu" and not r["prives"], "la lecture est « lue », et rien ne part au registre à part")

reponse_ia.clear(); reponse_ia.update({"ce_type": True, "nature": L("protection", "incertain"), "date_acte": L("2024-03-12"), "personnes": [DUPONT]})
r = s.lire(EC, {"texte": "--- page 1 ---\nORDONNANCE", "nbPages": 1}, personnes=True)
voir([v["cle"] for v in r["valeurs"]] == ["nature"], "TÉMOIN : même une protection lue AVEC DOUTE ne garde que sa nature")

reponse_ia.clear(); reponse_ia.update({"ce_type": True, "nature": L("acte_deces"), "date_acte": L("2026-10-30"),
                                       "personnes": [{**DUPONT, "qualite": L("defunt")}]})
r = s.lire(EC, {"texte": "--- page 1 ---\nACTE DE DECES", "nbPages": 1}, personnes=True)
voir(any(v["cle"] == "personnes.nom" and v["valeur"] == "DUPONT" for v in r["valeurs"]), "TÉMOIN : un décès garde le défunt (seule la protection est réduite)")

lec.requests.post = lambda *a, **k: (_ for _ in ()).throw(AssertionError("aucun appel"))
try:
    s.lire(EC, {"texte": "x"})
    voir(False, "porte")
except HTTPException as e:
    voir(e.status_code == 422 and "fermée" in str(e.detail), "SANS l'interrupteur des personnes : refusé avant tout appel")

print(f"\nTOUT EST VERT ({ok})")
