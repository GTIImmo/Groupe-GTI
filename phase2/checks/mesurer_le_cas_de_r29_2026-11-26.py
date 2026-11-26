#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""R29 : LE CAS QU'ELLE DEVAIT COUVRIR, ET POURQUOI IL NE SE PRESENTE PLUS -- LECTURE SEULE (images du protocole, socle en ro).

    python -X utf8 -u phase2\checks\mesurer_le_cas_de_r29_2026-11-26.py

SON MOT (26/11) : « R29 ne touche aucune ligne au 82. Zero, apres zero au rejeu sur copie. Avant de la laisser dans le juge,
nomme-moi le cas qu'elle devait couvrir et dis-moi pourquoi il ne se presente pas : soit il existe et le juge ne le voit
pas, soit il n'existe pas et on retire la regle. »

LA MESURE SE FAIT DANS LE JUGE (memoire : « une regle se mesure dans le juge, avec ses gardes ») : on appelle SA fonction
r29_candidat sur chaque ligne que R29 regarde (les lignes NON tranchees du passage, moins celles que r29_apres_les_verdicts
ecarte d'emblee), et on deroule A COTE l'entonnoir de ses conditions avec SES fonctions (noms, premiere proposition, ventes
du mandat, honoraires), pour voir ou chaque ligne s'arrete.
TEMOIN POSITIF : l'image du 81 (avant ses cases) DOIT rendre 9Q0FHAKK -- sinon la mesure est aveugle et ne prouve rien.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

CAS = [("image du 81 (avant ses cases) -- TEMOIN POSITIF, passage 81", "2026-11-25_072625", 81),
       ("image du 26/11 (ses cases corrigees), passage 82", "2026-11-26_094931", 82)]


def entonnoir(I, i: str, tenues: set) -> str:
    """Ou la ligne s'arrete dans les conditions de R29 (meme ordre que r29_candidat, memes fonctions)."""
    D = I.D
    nm = P.noms_texte(D.case(i, "Acquéreur"))
    jo = P.K.d_sheet(D.case(i, "Offre Achat"))
    if not nm or not jo:
        return "1 pas de nom d'acquereur ou pas de date d'offre"
    if P.nombre_case(D.case(i, "Commission TTC")) is None:
        return "2 pas de Commission TTC"
    offres = [(a, p) for a, p in sorted(I.pieces.items()) if p.get("kind") == "offre" and I.nature[a] == P.PC.VRAIE
              and (P.noms_acquereurs_hektor(p) & nm) and P.premiere_proposition(p) == jo]
    if not offres:
        return "3 aucune offre a son nom proposee le jour de sa case"
    return "4+ une offre a son nom ce jour-la, arretee plus loin (mandat a plusieurs ventes, honoraires, acquereur, tenue)"


def main() -> int:
    socle = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
    for titre, image, pid in CAS:
        I = P.Image(P.IMAGES / image)
        rangs = [{"id_unique": r[0], "verdict": r[1], "pieces": json.loads(r[2]) if r[2] else [], "motif": r[3],
                  "motif_texte": r[4]} for r in socle.execute(
            "select id_unique, verdict, pieces, motif, motif_texte from verdict where passage=?", (pid,))]
        tenues = {a for x in rangs for a in x["pieces"]} | set(P.PIECE_DONNEE_PAR_DECISION)
        decisions = set(P.RIEN_A_ETIQUETER_PAR_DECISION) | set(P.DOUBLON_PAR_DECISION) | set(P.LIGNE_SUR_LE_BIEN_PAR_DECISION)
        regardees = [x["id_unique"] for x in rangs if not (
            x["verdict"] == "TRANCHEE" or x["id_unique"].startswith("#") or x["id_unique"] in decisions
            or x["motif"] in ("ID_EN_DOUBLE", "A_SA_DECISION")
            or (x["motif"] == "RIEN_A_ETIQUETER" and str(x["motif_texte"] or "").startswith("REGLE R27")))]
        cand = {}
        for i in regardees:
            r = P.r29_candidat(I, i, tenues)
            if r:
                cand[i] = r
        print("\n== %s" % titre)
        print("   lignes non tranchees que R29 regarde : %d" % len(regardees))
        print("   l'entonnoir (ou chacune s'arrete) : %s" % dict(sorted(Counter(entonnoir(I, i, tenues) for i in regardees).items())))
        print("   CANDIDATES de r29_candidat (avant sa garde) : %d %s" % (len(cand), sorted(cand)))
        for i, (v, b, preuve) in cand.items():
            print("      %s -> vente %s, bien %s : %s" % (i, v, b, preuve[:230]))
        sys.stdout.flush()
    socle.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
