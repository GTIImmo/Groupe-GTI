"""Essai hors ligne de contact_seconde_fiche_from_api.py (couples · piece B, 31/10/2026).

Un FAUX Hektor rejoue les cas mesures : la seconde fiche est la suivante (379 fois
sur 393), deux plus loin (1 fois), introuvable dans les 3 suivantes, une fiche
d'un autre couple au milieu, un refus 429 (arret net), un 404 (on continue).

    python -I phase2/sync/test_contact_seconde_fiche.py
    sortie 0 = tout vert · 1 = un controle en echec
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "phase2" / "sync"))

from hektor_pipeline.common import HektorNonRetryableError  # noqa: E402
import contact_seconde_fiche_from_api as m  # noqa: E402


class FauxHektor:
    """fiches : {numero: refCouple} ; refus : {numero: texte d'erreur}."""

    def __init__(self, fiches=None, refus=None, panne=None):
        self.fiches = fiches or {}
        self.refus = refus or {}
        self.panne = panne or set()
        self.lus: list[str] = []

    def get_json(self, path, params=None):
        cid = params["id"]
        self.lus.append(cid)
        if cid in self.panne:
            raise RuntimeError("GET failed after 4 attempts: 503")
        if cid in self.refus:
            raise HektorNonRetryableError(self.refus[cid])
        if cid not in self.fiches:
            raise HektorNonRetryableError(f"404 Client Error: Not Found for url: /Api/Contact/ContactById?id={cid}")
        return {"data": {"contact": {"id": cid, "refCouple": self.fiches[cid], "nom": "X"}}}


echecs = []


def controle(nom, ok, detail=""):
    print(f"{'  OK  ' if ok else 'ECHEC '} {nom}{'' if ok else ' -- ' + str(detail)}")
    if not ok:
        echecs.append(nom)


P = "606071"

# 1. la suivante designe la premiere -> trouvee en UNE lecture
h = FauxHektor({"606072": P})
r = m.chercher(h, P, 3, "v2")
controle("1 la suivante : trouvee", r["seconde"] == "606072", r)
controle("1 une seule lecture", h.lus == ["606072"], h.lus)

# 2. deux plus loin, avec une fiche d'un AUTRE couple au milieu
h = FauxHektor({"606072": "600000", "606073": P})
r = m.chercher(h, P, 3, "v2")
controle("2 deux plus loin : trouvee", r["seconde"] == "606073", r)
controle("2 la fiche du milieu est dite « autre »", r["lus"][0]["issue"] == "autre", r["lus"])

# 3. une personne SEULE juste apres (refCouple = elle-meme) n'est pas la seconde
h = FauxHektor({"606072": "606072", "606073": "606073", "606074": "606074"})
r = m.chercher(h, P, 3, "v2")
controle("3 trois fiches seules : rien", r["seconde"] is None, r)
controle("3 au plus 3 lectures", len(h.lus) == 3, h.lus)

# 4. 404 au milieu : on continue
h = FauxHektor({"606073": P})
r = m.chercher(h, P, 3, "v2")
controle("4 un 404 n'arrete pas", r["seconde"] == "606073" and r["lus"][0]["issue"] == "absente", r)

# 5. refus 429 : ARRET NET, rien de plus n'est lu
h = FauxHektor({"606073": P}, refus={"606072": "429 Client Error: Too Many Requests"})
r = m.chercher(h, P, 3, "v2")
controle("5 refus : arret net", r["seconde"] is None and "refus" in (r.get("arret") or "") and h.lus == ["606072"], (r, h.lus))

# 6. Hektor en panne (5xx apres les essais du client) : arret net
h = FauxHektor({"606073": P}, panne={"606072"})
r = m.chercher(h, P, 3, "v2")
controle("6 panne : arret net", r["seconde"] is None and h.lus == ["606072"], (r, h.lus))

# 7. la premiere ne peut pas etre sa propre seconde (refCouple = elle-meme)
controle("7 la premiere n'est jamais la seconde",
         m.issue_de_la_lecture({"data": {"contact": {"id": P, "refCouple": P}}}, P, P) == "autre")

# 8. reponse sans fiche (200 vide) = absente
controle("8 reponse vide = absente", m.issue_de_la_lecture({"data": {}}, P, "606072") == "absente")

# 9. reponse NON emballee dans « contact » (meme deballage que la nuit)
controle("9 detail non emballe", m.issue_de_la_lecture({"data": {"id": "606072", "refCouple": P}}, P, "606072") == "seconde")

# 10. une fiche qui repond sous un AUTRE numero que celui demande n'est pas prise
controle("10 numero rendu different", m.issue_de_la_lecture({"data": {"contact": {"id": "999", "refCouple": P}}}, P, "606072") == "autre")

print("TOUT VERT" if not echecs else f"{len(echecs)} ECHEC(S)")
sys.exit(1 if echecs else 0)
