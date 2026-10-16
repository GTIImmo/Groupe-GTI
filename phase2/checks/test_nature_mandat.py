# -*- coding: utf-8 -*-
"""EPREUVE : _nature() ne devine plus un mandat de recherche dans la NOTE.
                                                                    15/10/2026

POURQUOI CETTE EPREUVE EXISTE
─────────────────────────────────────────────────────────────────────────────
Le piege est revenu DEUX FOIS (7133 le 14/10, puis les 63 lignes du 15/10) :
la note d'un mandat est du TEXTE LIBRE, et le negociateur y ecrit l'ANTECEDENT
du compromis -- « Objet mandat : mandat de recherche 13654 » sur un mandat de
VENTE veut dire « c'est le mandat de recherche n 13654 qui a amene l'acquereur ».

Sans epreuve, un futur correctif remettra le test sur la note en croyant bien
faire. Les cas ci-dessous sont tous REELS, releves en base le 15/10.

LECTURE SEULE : aucune base ouverte, aucun reseau. Elle tourne partout.

    python phase2/checks/test_nature_mandat.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from phase2.sync.mandat_ledger import _nature  # noqa: E402

# (titre, type, note, offre_type, nature attendue)
CAS = [
    # ─── CE QUE LE TYPE DIT FAIT FOI ────────────────────────────────────────
    ("18937 : le type nomme la recherche",
     "Mandat de recherche d'un terrain", None, "0", "RECHERCHE"),
    ("18938 : idem, autre libelle",
     "Mandat de recherche exclusif en cas de demarchage", None, "0", "RECHERCHE"),
    ("un mandat d'acheter est un mandat de recherche",
     "Mandat d'acheter", None, "0", "RECHERCHE"),
    ("18919 : une vente recente, libelle complet",
     "Mandat de vente exclusif sans demarchage", None, "0", "VENTE"),

    # ─── ⭐ LE COEUR : LA NOTE NE NOMME PLUS UNE RECHERCHE ───────────────────
    ("13655 : la note RENVOIE au mandat 13654, le type est vide -> INCONNUE",
     "", "Numéro : 13655 Objet mandat : mandat de recherche 13654 Durée initial mandat : 3",
     "0", "INCONNUE"),
    ("16786 : renvoi colle (« recherche_16782_ »), mandants DIFFERENTS -> INCONNUE",
     None, "Objet mandat : mandat de recherche_16782_ Lesault Thibault et Aurélie",
     "0", "INCONNUE"),
    ("13060 : note « mandat de recherche » SANS numero, mais type SIMPLE -> VENTE",
     "SIMPLE", "Numéro : 13060 Objet mandat : mandat de recherche Durée initial mandat : 3",
     "0", "VENTE"),
    ("3732 : « mandat de recherche car MDV résilié », type SIMPLE -> VENTE",
     "SIMPLE", "Objet mandat : mandat de recherche car MDV résilié", "0", "VENTE"),
    ("7133 : le piege du 14/10 -- « mandat d'acheter » dans un commentaire confidentiel",
     "SIMPLE", "Commentaire confidentiel mandat : ... mandat d'acheter ...", "0", "VENTE"),

    # ─── ⚠ LA NEGATION (13273), exposee par le retrait ci-dessus ────────────
    ("13273 : « pas de mandat de vente » est une NEGATION -> INCONNUE",
     None, "Numéro : 13273 Objet mandat : mandat de recherche 4068 - pas de mandat de vente",
     "0", "INCONNUE"),
    ("et une vraie mention « mandat de vente » dans la note reste une VENTE",
     None, "Objet mandat : mandat de vente", "0", "VENTE"),

    # ─── ⛔ LA FAMILLE GESTION N'A PAS BOUGE (17 vraies gestions en dependent) ─
    ("3298 : la note nomme la gestion, et elle est CONSERVEE",
     "SIMPLE", "Objet mandat : MANDAT DE GESTION 966 Durée initial mandat : 3", "0", "GESTION"),
    ("672 : gestion par la note, sans type",
     None, "Objet mandat : Mandat de gestion 698", "0", "GESTION"),
    ("le type peut aussi nommer la gestion",
     "Mandat de gestion locative", None, "0", "GESTION"),

    # ─── LES AUTRES CHEMINS, INCHANGES ──────────────────────────────────────
    ("un type d'offre de location l'emporte quand rien d'autre ne parle",
     None, "", "2", "LOCATION"),
    ("la note peut encore nommer une location",
     None, "Objet mandat : mandat de location", "0", "LOCATION"),
    ("sans type ni note : on ne devine pas",
     None, None, "0", "INCONNUE"),
]


def main() -> int:
    echecs = []
    print("EPREUVE _nature() — la note ne nomme plus un mandat de recherche\n")
    for titre, type_mandat, note, offre, attendu in CAS:
        obtenu = _nature(type_mandat, note, offre)
        ok = obtenu == attendu
        if not ok:
            echecs.append((titre, attendu, obtenu))
        print(f"  {'ok   ' if ok else 'ECHEC'}  {titre}")
        if not ok:
            print(f"         attendu {attendu}, obtenu {obtenu}")

    # ─── TEMOIN INVERSE : la version d'AVANT doit ECHOUER sur les cas du coeur.
    #     Sans cela, l'epreuve pourrait passer sans que le correctif existe.
    def avant(t_, n_, o):
        n = (n_ or "").upper()
        t = (t_ or "").strip().upper()
        if "MANDAT DE GESTION" in n or "MANDAT DE GERANCE" in n or "GESTION" in t or "GERANCE" in t:
            return "GESTION"
        if "MANDAT DE RECHERCHE" in n or "RECHERCHE" in t or "ACHETER" in t:
            return "RECHERCHE"
        if t in ("SIMPLE", "EXCLUSIF", "ACCORD") or "VENTE" in t:
            return "VENTE"
        if "MANDAT DE LOCATION" in n:
            return "LOCATION"
        if "MANDAT DE VENTE" in n:
            return "VENTE"
        return "INCONNUE"

    # ⚠ 7133 N'EST PAS UN CAS DU COEUR, ET LE TEMOIN ME L'A APPRIS.
    #   Il etait DEJA juste avant le 15/10 : le correctif du 14/10 n'avait ajoute
    #   que des tests sur le TYPE, jamais « acheter » dans la note. 7133 est donc
    #   un garde-fou de NON-REGRESSION (il doit rester VENTE dans les deux
    #   versions), pas une preuve que ce correctif-ci porte quelque chose.
    #   Le mettre dans le coeur rendait le temoin FAUX, pas le code.
    coeur = [c for c in CAS if c[0].startswith(("13655", "16786", "13060", "3732", "13273"))]
    rattrapes = [c[0] for c in coeur if avant(c[1], c[2], c[3]) == c[4]]
    print(f"\n  TEMOIN INVERSE : la version d'AVANT se trompe sur "
          f"{len(coeur) - len(rattrapes)} des {len(coeur)} cas du coeur")
    if rattrapes:
        echecs.append(("temoin inverse creux", "l'avant doit echouer", str(rattrapes)))
        print(f"         ⛔ elle en reussit : {rattrapes}")
    else:
        print("         ✅ aucun n'etait juste avant : le correctif porte bien quelque chose")

    print()
    if echecs:
        print(f">>> {len(echecs)} ECHEC(S)")
        return 1
    print(f"Les {len(CAS)} controles passent, et le temoin inverse est plein.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
