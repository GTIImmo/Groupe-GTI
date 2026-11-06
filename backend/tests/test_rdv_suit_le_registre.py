"""La page publique de RDV lit le REGISTRE, et le lien le suit à chaque ouverture (05/11/2026, audit §48).

Hors ligne : les tables sont des listes en mémoire (agences et coordonnées du 05/11 : Tence porte le mail d'Yssingeaux
chez Hektor). Rien n'est lu ni écrit en production.
Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_rdv_suit_le_registre.py   (sortie 0 = tout vert)
"""
from __future__ import annotations

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.appointment_service import AppointmentService

ANNUAIRE_AGENCES = [  # app_agence_directory (extrait du 05/11)
    {"nom": "Groupe GTI Tence", "tel": "0471560236", "mail": "yssingeaux@gti-immobilier.fr"},
    {"nom": "Groupe GTI Firminy", "tel": "04 77 06 20 20", "mail": "firminy@gti-immobilier.fr"},
]
FICHES = [  # app_negociateur_fiche (extrait)
    {"app_fiche_id": 1, "app_personne_id": 1000035, "sorte": "fiche_negociateur", "hektor_negociateur_id": "26",
     "telephone": "04 77 00 00 26", "portable": "06 00 00 00 26", "email_vu": "pereira@gti-immobilier.fr",
     "nom_vu": "Emmanuelle PEREIRA", "actif_chez_hektor": True},
]
TEXTE_ANNONCE = {"texte_principal_html": "Contact : 06 99 99 99 99 ou annonce@exemple.fr", "corps_listing_html": ""}


def correspond(valeur, filtre: str) -> bool:
    op, _, attendu = filtre.partition(".")
    texte = "" if valeur is None else str(valeur).lower() if isinstance(valeur, bool) else str(valeur)
    if op == "eq":
        return texte == attendu
    if op == "ilike":
        return texte.lower() == attendu.lower()
    raise AssertionError(f"filtre non prévu : {filtre}")


class Faux(AppointmentService):
    def __init__(self, tables: dict[str, list[dict]], pannes: set[str] | None = None):  # pas de Settings : rien ne sort
        self.tables = tables
        self.pannes = pannes or set()
        self.lus: list[str] = []
        self.ecrits: list[dict] = []

    def _rest_get(self, path, *, params):
        self.lus.append(path)
        if path in self.pannes:
            raise RuntimeError(f"panne {path}")
        lignes = self.tables.get(path, [])
        for cle, filtre in params.items():
            if cle in ("select", "limit", "order"):
                continue
            lignes = [l for l in lignes if correspond(l.get(cle), filtre)]
        return copy.deepcopy(lignes)

    def _rest_patch(self, path, *, payload, params):
        self.ecrits.append(payload)
        return []

    def _read_detail_payload_by_annonce(self, annonce_id):
        self.lus.append("texte_annonce")
        return dict(TEXTE_ANNONCE)


def tables(agences=None, alias=None, personnes=None, carnet=None):
    return {
        "app_registre_champ_app": carnet or [],
        "app_agence_directory": ANNUAIRE_AGENCES,
        "app_negociateur_fiche": FICHES,
        "app_registre_agence": agences or [],
        "app_registre_agence_alias": alias or [],
        "app_negociateur_personne": personnes or [],
    }


DOSSIER_TENCE = {"hektor_annonce_id": 60001, "commercial_id": "26", "negociateur_email": "pereira@gti-immobilier.fr",
                 "agence_nom": "Groupe GTI Tence"}
LIEN_FIGE = {"id": "lien-1", "negociateur_phone": "04 77 00 00 26", "negociateur_mobile": "06 00 00 00 26",
             "agence_phone": "0471560236", "agence_email": "yssingeaux@gti-immobilier.fr"}
# Le registre porte une correction (saisie au carnet : la colonne en garde la valeur, §50).
REGISTRE_TENCE = [{"app_agence_id": 2000009, "telephone": "04 71 56 02 36", "email": "tence@gti-immobilier.fr"}]
ALIAS_TENCE = [{"cle": "TENCE", "app_agence_id": 2000009, "ecriture": "Groupe GTI Tence"}]

resultats: list[tuple[str, bool]] = []


def essai(nom, condition):
    resultats.append((nom, bool(condition)))


# 1. TÉMOIN INVERSE -- registre vide (l'état d'avant la 1re nuit) : rien ne change, rien n'est réécrit, l'annonce n'est pas relue.
s = Faux(tables())
lien = s._maybe_enrich_link_contacts(dict(LIEN_FIGE), DOSSIER_TENCE)
essai("1. registre vide : le lien figé reste tel quel", lien.get("agence_email") == "yssingeaux@gti-immobilier.fr")
essai("1. registre vide : aucune réécriture", s.ecrits == [])
essai("1. registre vide : le texte de l'annonce n'est pas relu", "texte_annonce" not in s.lus)

# 2. Le registre porte la correction : le lien déjà envoyé la SUIT.
s = Faux(tables(REGISTRE_TENCE, ALIAS_TENCE))
lien = s._maybe_enrich_link_contacts(dict(LIEN_FIGE), DOSSIER_TENCE)
essai("2. correction au registre : le lien figé est réécrit", len(s.ecrits) == 1 and s.ecrits[0]["agence_email"] == "tence@gti-immobilier.fr")
essai("2. ... avec le tél du registre", s.ecrits and s.ecrits[0]["agence_phone"] == "04 71 56 02 36")
essai("2. ... et le négociateur inchangé", s.ecrits and s.ecrits[0]["negociateur_mobile"] == "06 00 00 00 26")

# 3. Une 2e ouverture, déjà à jour : aucune réécriture.
deja = {**LIEN_FIGE, "agence_phone": "04 71 56 02 36", "agence_email": "tence@gti-immobilier.fr"}
s = Faux(tables(REGISTRE_TENCE, ALIAS_TENCE))
s._maybe_enrich_link_contacts(dict(deja), DOSSIER_TENCE)
essai("3. lien déjà à jour : aucune réécriture", s.ecrits == [])

# 4. Le registre a le tél mais pas le mail : le mail vient de l'annuaire (repli champ par champ).
s = Faux(tables([{"app_agence_id": 2000009, "telephone": "04 71 56 02 36", "email": None}], ALIAS_TENCE))
d = s._load_contact_details(DOSSIER_TENCE)
essai("4. tél du registre", d["agencePhone"] == "04 71 56 02 36")
essai("4. mail en repli sur l'annuaire", d["agenceEmail"] == "yssingeaux@gti-immobilier.fr")

# 5. Le portable À NOUS de la personne passe devant sa fiche Hektor.
s = Faux(tables(personnes=[{"app_personne_id": 1000035, "telephone": None, "portable": "07 11 11 11 11"}]))
d = s._load_contact_details(DOSSIER_TENCE)
essai("5. portable à nous", d["negociateurMobile"] == "07 11 11 11 11")
essai("5. fixe vide chez nous : celui de la fiche", d["negociateurPhone"] == "04 77 00 00 26")

# 6. Tout tombe en panne (registre ET annuaire) : le lien garde sa copie, et l'annonce n'est pas relue.
s = Faux(tables(REGISTRE_TENCE, ALIAS_TENCE), pannes={"app_registre_agence_alias", "app_agence_directory", "app_negociateur_fiche"})
lien = s._maybe_enrich_link_contacts(dict(LIEN_FIGE), DOSSIER_TENCE)
essai("6. pannes : copie gardée", lien.get("agence_email") == "yssingeaux@gti-immobilier.fr" and s.ecrits == [])
essai("6. pannes : le texte de l'annonce n'est pas relu", "texte_annonce" not in s.lus)

# 7. Lien incomplet et rien ailleurs : le texte de l'annonce, comme avant.
s = Faux(tables(), pannes={"app_agence_directory", "app_negociateur_fiche"})
d = s._load_contact_details(DOSSIER_TENCE, {"negociateur_phone": None, "negociateur_mobile": None, "agence_phone": None, "agence_email": None})
essai("7. rien ailleurs : le texte de l'annonce est relu", "texte_annonce" in s.lus and d["negociateurMobile"] == "06 99 99 99 99")

# 8. Deux agences sous la même clé : on ne choisit pas au hasard, on prend l'annuaire.
s = Faux(tables(REGISTRE_TENCE + [{"app_agence_id": 2000099, "telephone": "x", "email": "autre@x.fr"}],
                [{"cle": "TENCE", "app_agence_id": 2000009, "ecriture": "A"}, {"cle": "TENCE", "app_agence_id": 2000099, "ecriture": "B"}]))
d = s._load_contact_details(DOSSIER_TENCE)
essai("8. clé ambiguë : repli sur l'annuaire", d["agenceEmail"] == "yssingeaux@gti-immobilier.fr")

# 9. L'écriture EXACTE départage une clé ambiguë.
s = Faux(tables(REGISTRE_TENCE + [{"app_agence_id": 2000099, "telephone": "x", "email": "autre@x.fr"}],
                [{"cle": "TENCE", "app_agence_id": 2000009, "ecriture": "Groupe GTI Tence"}, {"cle": "TENCE", "app_agence_id": 2000099, "ecriture": "B"}]))
d = s._load_contact_details(DOSSIER_TENCE)
essai("9. écriture exacte : la bonne agence", d["agenceEmail"] == "tence@gti-immobilier.fr")

# 11. L'agence existe au registre mais ses deux champs sont vides : l'annuaire, et le lien n'est PAS réécrit.
s = Faux(tables([{"app_agence_id": 2000009, "telephone": None, "email": None}], ALIAS_TENCE))
s._maybe_enrich_link_contacts(dict(LIEN_FIGE), DOSSIER_TENCE)
essai("11. registre vide pour l'agence : aucune réécriture", s.ecrits == [])
d = s._load_contact_details(DOSSIER_TENCE)
essai("11. registre vide pour l'agence : l'annuaire", d["agenceEmail"] == "yssingeaux@gti-immobilier.fr")

# 10. La clé Python = la clé SQL sur les écritures difficiles.
essai("10. clé : espaces de fin", AppointmentService._cle_agence("Groupe GTI Ambert    ") == "AMBERT")
essai("10. clé : accents", AppointmentService._cle_agence("Groupe GTI Saint-Bonnet-le-Château") == "SAINT-BONNET-LE-CHATEAU")
essai("10. clé : « Gti » et espaces", AppointmentService._cle_agence("Groupe Gti Le Puy en Velay") == "LE-PUY-EN-VELAY")
essai("10. clé : sans préfixe", AppointmentService._cle_agence("Agences supprimée") == "AGENCES-SUPPRIMEE")

for nom, ok in resultats:
    print(("OK   " if ok else "ROUGE") + "  " + nom)
rouges = [n for n, ok in resultats if not ok]
print(f"\n{len(resultats) - len(rouges)}/{len(resultats)} verts")
sys.exit(1 if rouges else 0)
