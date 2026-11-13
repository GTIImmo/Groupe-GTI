"""GED morceau 6, lots 1 à 4 (12-13/11/2026) — les fiches de lecture et la route /ged/lire.

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
voir(set(lec.FICHES) == {"diag.erp", "diag.dpe", "diag.dossier", "justif.taxe", "justif.titre", "copro.carnet", "copro.appel_fonds", "copro.arrete_charges",
                         "transaction.offre", "transaction.avant_contrat", "copro.pv_ag",
                         "mandat.vente", "mandat.avenant", "mandat.fin", "transaction.acte", "transaction.annulation",
                         "facture.honoraires", "diag.electricite", "diag.gaz", "diag.amiante", "diag.plomb", "diag.termites",
                         "diag.assainissement", "diag.surface", "copro.reglement"},
     "lots 1 à 4 : diagnostics, taxe, titre, copro, offre, compromis, PV d'AG, mandat, avenant, fin, acte, annulation, facture, petits diagnostics, surfaces, règlement")
voir(all(strict_partout(lec.schema(f)) for f in lec.FICHES.values()), "schéma STRICT partout : tous les champs obligatoires, aucun champ en plus")
interdits = ("naissance", "iban", "fiscal", "identite", "secu", "nom_", "prenom", "adresse_perso", "civil", "profession")
voir(not any(i in c for f in lec.FICHES.values() for c in lec.schema(f)["properties"] for i in interdits), "aucun champ de la fiche ne demande une donnée de personne")
lot1 = ("diag.erp", "diag.dpe", "diag.dossier")
voir(not any("personnes" in lec.schema(lec.FICHES[c])["properties"] for c in lot1), "TÉMOIN : le lot 1 ne lit toujours aucun nom")
avec_noms = {c for c, f in lec.FICHES.items() if "personnes" in lec.schema(f)["properties"]}
voir(avec_noms == {"justif.taxe", "justif.titre", "transaction.offre", "transaction.avant_contrat", "mandat.vente", "mandat.avenant",
                   "mandat.fin", "transaction.acte", "transaction.annulation"},
     "les noms : taxe, titre, offre, compromis, mandat, avenant, fin de mandat, acte, annulation — jamais le PV, les diagnostics, la facture, le règlement")
voir("aucune" not in lec.FICHES["copro.pv_ag"]["champs"]["procedure"][1], "PV d'AG : « aucune procédure » ne peut pas se lire (un PV ne prouve pas l'absence)")
voir("feuille de présence" in lec.FICHES["copro.pv_ag"]["consigne"] and "personnes" not in lec.schema(lec.FICHES["copro.pv_ag"])["properties"], "PV d'AG : aucune personne, la feuille de présence interdite")
for c in ("transaction.offre", "transaction.avant_contrat", "transaction.annulation"):
    voir("JAMAIS le montant d'un prêt" in lec.FICHES[c]["consigne"] and not any(k for k in lec.FICHES[c]["champs"] if "banque" in k or "apport" in k or k.startswith("montant_pret")), f"{c} : jamais le prêt (montant, banque, apport)")
voir("JAMAIS le prêt" in lec.FICHES["transaction.acte"]["consigne"] and not any("pret" in k for k in lec.FICHES["transaction.acte"]["champs"]), "transaction.acte : jamais le prêt")
voir(lec.FICHES["transaction.avant_contrat"]["texte_max"] == 80000 and lec.FIN_EN_IMAGE == {"transaction.avant_contrat": 2, "transaction.offre": 1, "mandat.vente": 2, "mandat.avenant": 1, "mandat.fin": 1},
     "compromis et mandat : 2 dernières pages en image ; offre, avenant, fin de mandat : la dernière")
for c in avec_noms:
    item = lec.schema(lec.FICHES[c])["properties"]["personnes"]["items"]["properties"]
    voir(set(item) <= {"nom", "prenoms", "qualite", "droits", "quote_part", "page"}, f"{c} : une personne = nom, prénoms, qualité (droits) — rien d'autre")
    voir("EXCEPTION" in lec.FICHES[c]["consigne"] and "ni date ou lieu de naissance" in lec.FICHES[c]["consigne"], f"{c} : la consigne lève l'interdit des noms ICI seulement")
voir("JAMAIS le nom" in lec.FICHES["copro.appel_fonds"]["consigne"] and lec.FICHES["copro.appel_fonds"] is lec.FICHES["copro.arrete_charges"], "charges : une seule fiche, jamais le copropriétaire destinataire")
voir("JAMAIS les vendeurs" in lec.FICHES["justif.titre"]["consigne"], "titre : les NOUVEAUX propriétaires, jamais les anciens")
voir("sauf" in lec._CONSIGNE_COMMUNE and "jamais un nom de personne" in lec._CONSIGNE_COMMUNE, "la consigne commune garde l'interdit, avec sa seule exception")
voir("PAS la date de l'arrêté" in lec.FICHES["diag.erp"]["consigne"], "état des risques : la date de l'état, pas celle de l'arrêté")

print("1 bis) le lot 4")
voir("mandant" in lec.QUALITES, "la qualité « mandant » existe")
for c in ("mandat.vente", "mandat.avenant", "mandat.fin"):
    voir("qualité mandant" in lec.FICHES[c]["consigne"] and "jamais le négociateur" in lec.FICHES[c]["consigne"], f"{c} : les MANDANTS seulement, jamais le négociateur")
voir("raison personnelle" in lec.FICHES["mandat.fin"]["consigne"] and set(lec.FICHES["mandat.fin"]["champs"]["motif"][1]) == {"vendu_ailleurs", "retrait_vente", "autre_agence", "autre"},
     "fin de mandat : un motif dans une liste fermée, jamais une raison personnelle recopiée")
voir("raison personnelle" in lec.FICHES["transaction.annulation"]["consigne"], "annulation : jamais une raison personnelle recopiée")
voir("PAS la date d'envoi" in lec.FICHES["transaction.acte"]["consigne"], "acte : la date de la VENTE, pas celle de l'attestation")
sans_nom = ("diag.electricite", "diag.gaz", "diag.amiante", "diag.plomb", "diag.termites", "diag.assainissement", "diag.surface")
for c in sans_nom:
    voir("JAMAIS le nom ni l'adresse du propriétaire" in lec.FICHES[c]["consigne"] and "personnes" not in lec.schema(lec.FICHES[c])["properties"], f"{c} : aucun nom, jamais le propriétaire")
voir(lec.FICHES["diag.electricite"]["champs"]["resultat"][1] == ["sans_anomalie", "anomalies", "danger_grave"] and lec.FICHES["diag.amiante"]["champs"]["resultat"][1] == ["absence", "presence"],
     "petits diagnostics : un résultat dans une liste fermée (pour les validités du morceau 7)")
fac = lec.FICHES["facture.honoraires"]
voir("ce_type : faux si c'est la facture d'un fournisseur" in fac["consigne"] and fac["champs"]["payeur"][1] == ["vendeur", "acquereur", "autre"] and "personnes" not in lec.schema(fac)["properties"],
     "facture : une facture d'énergie ou de travaux est dite « pas ce type » ; le payeur = une QUALITÉ, jamais un nom")
voir("JAMAIS le nom d'un copropriétaire" in lec.FICHES["copro.reglement"]["consigne"] and lec.PAGES_HD.get("copro.reglement") == 6 and lec.FICHES["copro.reglement"]["texte_max"] == lec.MAX_TEXTE_LONG,
     "règlement : aucun copropriétaire, 6 pages ou 40 000 caractères")
voir(lec.PAGES_HD.get("mandat.vente") == 6 and lec.PAGES_HD.get("transaction.acte") == 6 and lec.PAGES_HD.get("mandat.avenant") is None, "mandat et acte : 6 pages ; avenant : 4 (une page en médiane)")

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

print("2 bis) les noms et les numéros (lot 2)")
L = lambda v, etat="lu", page=1: {"v": v, "page": page, "etat": etat}
taxe = lec.FICHES["justif.taxe"]
brut = {"ce_type": True, **{c: L(None, "non_vu", None) for c in taxe["champs"]}}
brut.update({"montant_total": L(1234.5), "commune": L("Saint-Étienne"), "adresse_biens": L("12 rue des Lilas 42000"),
             "personnes": [{"nom": L("MARTIN"), "prenoms": L("Claire Anne"), "qualite": L("redevable"), "page": 1},
                           {"nom": L("DURAND 12/03/1960"), "prenoms": L("Paul"), "qualite": L("usufruitier"), "page": 1},
                           {"nom": L("claire@exemple.fr"), "prenoms": L(None, "non_vu"), "qualite": L("pdg"), "page": 1}]})
_, vals = lec.normaliser(brut, taxe, 2)
p = {(x["cle"], x["rang"]): x for x in vals}
voir(p[("personnes.nom", 0)]["valeur"] == "MARTIN" and p[("personnes.prenoms", 0)]["valeur"] == "Claire Anne", "un nom et des prénoms sont gardés tels qu'imprimés")
voir(p[("personnes.nom", 1)]["etat"] == "non_vu" and p[("personnes.nom", 1)]["valeur"] is None, "un « nom » avec une date dedans est jeté")
voir(p[("personnes.nom", 2)]["valeur"] is None and p[("personnes.qualite", 2)]["valeur"] is None, "une adresse e-mail en guise de nom, une qualité inventée : jetées")
voir(p[("adresse_biens", 0)]["valeur"] == "12 rue des Lilas 42000" and p[("montant_total", 0)]["valeur_num"] == 1234.5, "l'adresse DES BIENS et le montant sont gardés")
brut["commune"] = L("1 23 45 678 901 234")
brut["adresse_biens"] = L("Réf. 4212345678901")
_, vals = lec.normaliser(brut, taxe, 2)
p = {(x["cle"], x["rang"]): x for x in vals}
voir(p[("commune", 0)]["valeur"] is None and p[("adresse_biens", 0)]["valeur"] is None, "⛔ un long numéro (fiscal, de rôle) n'est gardé dans AUCUN champ, même espacé")
brut["personnes"] = [{"nom": L("NOM"), "prenoms": L("A"), "qualite": L("redevable"), "page": 1} for i in range(20)]
_, vals = lec.normaliser(brut, taxe, 2)
voir(max(x["rang"] for x in vals if x["cle"] == "personnes.nom") == lec.MAX_PERSONNES - 1, f"au plus {lec.MAX_PERSONNES} personnes")
titre = lec.FICHES["justif.titre"]
brut = {"ce_type": True, **{c: L(None, "non_vu", None) for c in titre["champs"]}, "personnes": [], "lots": [{"numero": L("12"), "tantiemes": L("125/10000"), "page": 3}]}
_, vals = lec.normaliser(brut, titre, 40)
voir(any(x["cle"] == "lots.tantiemes" and x["valeur"] == "125/10000" for x in vals), "titre : les lots et leurs tantièmes (une fraction n'est pas un numéro)")
voir(titre.get("texte_max") == lec.MAX_TEXTE_LONG and lec.PAGES_HD.get("justif.titre") == lec.MAX_PAGES_HD, "titre : texte plus long, 6 pages en image")
voir(lec.FICHES["diag.erp"].get("texte_max") is None, "TÉMOIN : le lot 1 garde son texte de 20 000 caractères")


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

print("2 ter) ce qui part vraiment vers l'IA (appel simulé)")
parti = {}


class Reponse:
    ok = True

    def json(self):
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": '{"ce_type": true}'}]}], "usage": {}}


def capter(url, headers=None, json=None, timeout=None):
    parti.update(json)
    return Reponse()


class PortierTypes:
    def types(self):
        return [{"code": c, "sensible": False} for c in lec.FICHES]

    def depense_du_jour(self):
        return 0.0


lec.requests.post = capter
s0 = lec.OpenAIGedLectureService(Settings())
s0.portier = PortierTypes()
long_texte = "mot " * 15000
lec.agent_registry.load_spec = lambda settings, key: lec.agent_registry.DEFAULT_SPECS[key]
s0.lire({"type_code": "justif.titre"}, {"texte": long_texte, "nbPages": 30})
voir(len(parti["input"][0]["content"][0]["text"]) > 30000 and parti["store"] is False, "titre : le texte long part (au-delà de 20 000), et rien n'est gardé chez le fournisseur")
voir("EXCEPTION" in parti["instructions"] and "personnes" in parti["text"]["format"]["schema"]["properties"], "titre : consigne et schéma avec la liste des personnes")
s0.lire({"type_code": "diag.erp"}, {"texte": long_texte, "nbPages": 30})
voir(len(parti["input"][0]["content"][0]["text"]) < 20200 and "EXCEPTION" not in parti["instructions"], "TÉMOIN : l'état des risques garde 20 000 caractères et aucune exception aux noms")
img = "data:image/jpeg;base64," + "A" * 40
r = s0.lire({"type_code": "transaction.avant_contrat"}, {"texte": long_texte * 2, "nbPages": 40, "pages": [{"numero": 39, "image": img}, {"numero": 40, "image": img}]})
contenu = parti["input"][0]["content"]
voir(len(contenu[0]["text"]) > 70000 and sum(1 for c in contenu if c["type"] == "input_image") == 2 and r["parTexte"] is True and r["pagesLues"] == [39, 40],
     "compromis : le TEXTE (80 000) ET les 2 dernières pages en image partent ensemble ; la lecture le dit")
r = s0.lire({"type_code": "mandat.vente"}, {"texte": long_texte, "nbPages": 12, "pages": [{"numero": 11, "image": img}, {"numero": 12, "image": img}]})
voir(30000 < len(parti["input"][0]["content"][0]["text"]) < 40200 and r["pagesLues"] == [11, 12] and "qualité mandant" in parti["instructions"],
     "mandat : 40 000 caractères + les 2 pages des signatures, et la consigne des mandants")
s0.lire({"type_code": "diag.amiante"}, {"texte": long_texte, "nbPages": 21})
voir(len(parti["input"][0]["content"][0]["text"]) < 20200 and "EXCEPTION" not in parti["instructions"] and "personnes" not in parti["text"]["format"]["schema"]["properties"],
     "amiante : 20 000 caractères, aucune exception aux noms")
lec.requests.post = appel_interdit

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
