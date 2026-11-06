"""La page publique d'estimation : rotation sur les négociateurs ACTIFS du registre, page sans agence = Firminy, coordonnées
d'agence du registre d'abord (06/11/2026, audit §52).

Hors ligne : les tables sont des listes en mémoire (extraits du 06/11 : à Firminy, 7 personnes « tournaient », une seule
active). Rien n'est lu ni écrit en production.
Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_estimation_registre.py   (sortie 0 = tout vert)
"""
from __future__ import annotations

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.appointment_service import AppointmentService

ANNUAIRE_AGENCES = [  # app_agence_directory (extrait, n° en TEXTE comme en base)
    {"id_agence": "1", "nom": "Compte formation", "tel": "06.58.77.08.93", "mail": "frederic.gerphagnon@gti-immobilier.fr"},
    {"id_agence": "10", "nom": "Groupe GTI ANNONAY", "tel": "09 73 31 48 18", "mail": "annonay@gti-immobilier.fr"},
    {"id_agence": "12", "nom": "Groupe GTI Firminy", "tel": "04 77 06 20 20", "mail": "firminy@gti-immobilier.fr"},
    {"id_agence": "16", "nom": "Groupe GTI Ambert   ", "tel": "04 73 82 95 61", "mail": "ambert@gti-immobilier.fr"},
]
FICHES = [  # app_negociateur_fiche (extrait)
    {"app_personne_id": 1000035, "sorte": "fiche_negociateur", "hektor_negociateur_id": "26", "hektor_agence_id": "12",
     "actif_chez_hektor": True, "nom_vu": "Emmanuelle PEREIRA", "email_vu": "pereira@gti-immobilier.fr"},
    {"app_personne_id": 1000036, "sorte": "fiche_negociateur", "hektor_negociateur_id": "19", "hektor_agence_id": "12",
     "actif_chez_hektor": False, "nom_vu": "Franck GERPHAGNON", "email_vu": "franck.gerphagnon@gmail.com"},
    {"app_personne_id": 1000099, "sorte": "fiche_negociateur", "hektor_negociateur_id": "77", "hektor_agence_id": "12",
     "actif_chez_hektor": True, "nom_vu": "Ancien CHEZNOUS", "email_vu": "ancien@gti-immobilier.fr"},
    {"app_personne_id": 1000010, "sorte": "fiche_negociateur", "hektor_negociateur_id": "8", "hektor_agence_id": "16",
     "actif_chez_hektor": True, "nom_vu": "Alice RONDEAU", "email_vu": "rondeau@gti-immobilier.fr"},
]
PERSONNES = [
    {"app_personne_id": 1000035, "actif": True}, {"app_personne_id": 1000036, "actif": True},
    {"app_personne_id": 1000099, "actif": False}, {"app_personne_id": 1000010, "actif": True},
]
BIENS_FIRMINY = [  # app_dossiers_current : l'ANCIEN chemin (toute personne ayant un bien)
    {"commercial_id": "26", "commercial_nom": "Emmanuelle PEREIRA", "negociateur_email": "pereira@gti-immobilier.fr", "agence_nom": "Groupe GTI Firminy"},
    {"commercial_id": "19", "commercial_nom": "Franck GERPHAGNON", "negociateur_email": "franck.gerphagnon@gmail.com", "agence_nom": "Groupe GTI Firminy"},
]


def correspond(valeur, filtre: str) -> bool:
    op, _, attendu = filtre.partition(".")
    texte = "" if valeur is None else str(valeur).lower() if isinstance(valeur, bool) else str(valeur)
    if op == "eq":
        return texte == attendu
    if op == "ilike":
        return texte.lower() == attendu.lower()
    if op == "in":
        return texte in attendu.strip("()").split(",")
    raise AssertionError(f"filtre non prévu : {filtre}")


class Faux(AppointmentService):
    def __init__(self, tables, pannes=None):  # pas de Settings : rien ne sort
        self.tables = tables
        self.pannes = pannes or set()

    def _rest_get(self, path, *, params):
        if path in self.pannes:
            raise RuntimeError(f"panne {path}")
        lignes = self.tables.get(path, [])
        for cle, filtre in params.items():
            if cle in ("select", "limit", "order"):
                continue
            lignes = [l for l in lignes if correspond(l.get(cle), filtre)]
        return copy.deepcopy(lignes)


def tables(registre_agences=None, alias=None, fiches=FICHES):
    return {"app_agence_directory": ANNUAIRE_AGENCES, "app_negociateur_fiche": fiches, "app_negociateur_personne": PERSONNES,
            "app_dossiers_current": BIENS_FIRMINY, "app_registre_agence": registre_agences or [],
            "app_registre_agence_alias": alias or []}


resultats: list[tuple[str, bool]] = []


def essai(nom, condition):
    resultats.append((nom, bool(condition)))


FIRMINY = {"id_agence": "12", "nom": "Groupe GTI Firminy"}

# 1. La rotation ne prend que les ACTIFS : fiche active chez Hektor ET personne non passée « ancien ».
s = Faux(tables())
r = s._read_dynamic_agency_negotiators(FIRMINY)
essai("1. Firminy : seule Emmanuelle PEREIRA tourne", [x["user_id"] for x in r] == ["26"])
essai("1. ... avec son e-mail", r and r[0]["negotiator_email"] == "pereira@gti-immobilier.fr")

# 2. Ambert, écrit avec des espaces : trouvée par son n° d'agence (l'ancien `ilike` sur le nom la ratait).
r = s._read_dynamic_agency_negotiators({"id_agence": "16", "nom": "Groupe GTI Ambert   "})
essai("2. Ambert (espaces) : Alice RONDEAU tourne", [x["user_id"] for x in r] == ["8"])

# 3. Le registre répond mais l'agence n'a aucun actif : liste vide (la demande ira sur le mail de l'agence).
r = s._read_dynamic_agency_negotiators({"id_agence": "10", "nom": "Groupe GTI ANNONAY"})
essai("3. agence sans actif : personne ne tourne", r == [])

# 4. Le registre ne répond pas : l'ancien chemin, inchangé.
s = Faux(tables(), pannes={"app_negociateur_fiche"})
r = s._read_dynamic_agency_negotiators(FIRMINY)
essai("4. registre en panne : ancien chemin (biens)", sorted(x["user_id"] for x in r) == ["19", "26"])

# 5. La page sans agence : Firminy, plus Annonay.
s = Faux(tables())
a = s._read_default_agency_row()
essai("5. page sans agence : Firminy", a.get("nom") == "Groupe GTI Firminy")
essai("5. ... ses coordonnées (annuaire, registre vide)", a.get("mail") == "firminy@gti-immobilier.fr")

# 6. Les coordonnées de l'agence viennent du registre d'abord.
s = Faux(tables([{"app_agence_id": 2000007, "telephone": "04 77 00 00 07", "email": "contact.firminy@gti-immobilier.fr"}],
                [{"cle": "FIRMINY", "app_agence_id": 2000007, "ecriture": "Groupe GTI Firminy"}]))
a = s._read_agency_by_key("firminy")
essai("6. par la clé : mail du registre", a.get("mail") == "contact.firminy@gti-immobilier.fr")
essai("6. par la clé : tél du registre", a.get("tel") == "04 77 00 00 07")
essai("6. le n° d'agence reste celui de Hektor (rotation)", a.get("id_agence") == "12")
a = s._read_default_agency_row()
essai("6. page sans agence : mail du registre", a.get("mail") == "contact.firminy@gti-immobilier.fr")

# 7. Le registre a le tél mais pas le mail : le mail de l'annuaire.
s = Faux(tables([{"app_agence_id": 2000007, "telephone": "04 77 00 00 07", "email": None}],
                [{"cle": "FIRMINY", "app_agence_id": 2000007, "ecriture": "Groupe GTI Firminy"}]))
a = s._read_agency_by_key("firminy")
essai("7. repli champ par champ", a.get("mail") == "firminy@gti-immobilier.fr" and a.get("tel") == "04 77 00 00 07")

for nom, ok in resultats:
    print(("OK   " if ok else "ROUGE") + "  " + nom)
rouges = [n for n, ok in resultats if not ok]
print(f"\n{len(resultats) - len(rouges)}/{len(resultats)} verts")
sys.exit(1 if rouges else 0)
