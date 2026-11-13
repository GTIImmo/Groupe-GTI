#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA LISTE EXACTE DU RE-GEL -- a relire AVANT toute ecriture.   13/11/2026

Plan : notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md, section 1.7 (A, B, C).
Source : notice/RAPPORT_V2_CONTRE_GEL_2026-11-13.csv -- la sortie REELLE de
l'apparieur v2, pas le texte du rapport A19 (qui annoncait 348 la ou le fichier
en contient 341 : c'est le fichier qui fait foi).

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il produit un CSV que Frederic relit, et il
   affiche les comptes. Le geste d'ecriture est un patch separe, qui ne sera
   pose qu'apres cette relecture.

LES TROIS LOTS :
  A  CORRIGER   3 liens faux du gel (etage « 1 mandat seul »)
                ⚠ SEUL lot qui RETOUCHE des liens existants
  B  RETIRER    2 liens poses sur une ligne DOUBLON du classeur
  C  AJOUTER    les liens « v2 seul » a >= 3 familles DONT LA TRANSACTION EST LIBRE
                (les 48 dont la transaction est deja prise par une AUTRE ligne
                 sont ECARTES : une transaction ne peut pas appartenir a deux
                 lignes du classeur)
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
RAPPORT = RACINE / "notice" / "RAPPORT_V2_CONTRE_GEL_2026-11-13.csv"
SORTIE = RACINE / "notice" / "REGEL_ADDITIF_A_RELIRE_2026-11-13.csv"

# ── A : les 3 liens faux, juges un par un et CONTRE-AUDITES depuis le classeur
#   (ligne, id_unique, bien du gel, bien de v2)
A_CORRIGER = [
    (3229, "0FFZI3NF", 38358, 51140, "LOTI SUD EST / DESSAGNE : 2 noms + 3 dates AU JOUR"),
    (3370, "HFXW07KA", 45946, 43179, "JOAQUIM / REYNEBEAU : 2 noms + 3 dates AU JOUR"),
    (3390, "A6H4MA4O", 31561, 29784, "SCAFIDI / ROUGERON CHERBUT : 2 noms + 3 dates AU JOUR"),
]

# ── LES 48 A ECARTER DU LOT C : leur transaction appartient DEJA a une autre
#   ligne du classeur. Les geler ferait appartenir une meme transaction a DEUX
#   affaires -- exactement le faux qui devient invisible une fois dans le Sheet.
#   ⭐ Releve en base le 13/11 (app_classeur_lien), avec temoin inverse.
DEJA_PRISES = {
    "1101": "3959/compromis", "1232": "2414/vente", "1876": "3540/offre",
    "3678": "4252/offre", "4480": "3785/compromis", "4496": "3938/compromis",
    "4546": "1379/vente", "4747": "3988/offre", "6340": "380/compromis",
    "6341": "380/offre", "6342": "380/vente", "7651": "488/vente",
    "7780": "3962/offre", "11415": "3958/offre", "11958": "4113/offre",
    "11960": "2388/vente", "14008": "21/offre", "14813": "3689/compromis",
    "15914": "3493/compromis", "16342": "3996/compromis", "17026": "3731/offre",
    "17387": "3842/compromis", "20073": "3887/compromis", "21551": "227/compromis",
    "21552": "227/offre", "23050": "4005/compromis", "23475": "3899/compromis",
    "23802": "4670/offre", "23995": "3518/offre", "23997": "457/vente",
    "24125": "845/vente", "24291": "1758/offre", "24410": "1103/vente",
    "24415": "1951/vente", "24447": "2118/vente", "24450": "3817/compromis",
    "24588": "4114/compromis", "24593": "4064/compromis", "24594": "4064/offre",
    "25710": "4666/offre", "26075": "1024/vente", "27134": "3605/compromis",
    "27183": "793/compromis", "27186": "793/vente", "27195": "4668/compromis",
    "27445": "3985/compromis", "29024": "4735/offre", "1000003": "4675/compromis",
}

# ── B : les 2 liens poses sur une ligne doublon (les 4 autres groupes : RIEN)
B_RETIRER = [
    (3818, "doublon de la ligne 1397 (ROMEO CLEMENT, mandat 13695) ; le gel le met sur le bien 45081, sa jumelle sur 9705"),
    (4100, "doublon de la ligne 2346 (BASSET BASTET, mandat 3968) ; le gel le met sur le bien 21037, sa jumelle sur 48145"),
]


def familles(ligne: dict) -> int:
    try:
        return int((ligne.get("familles v2") or "0").strip())
    except ValueError:
        return 0


def main() -> int:
    if not RAPPORT.exists():
        print("N'A PAS PU MESURER : %s introuvable" % RAPPORT.name)
        return 2

    lignes = list(csv.DictReader(io.open(RAPPORT, encoding="utf-8-sig"), delimiter=";"))
    seuls = [x for x in lignes if "MOI SEUL" in (x.get("cas") or "").upper()]
    gros = [x for x in seuls if familles(x) >= 3]

    print()
    print("  LE RE-GEL ADDITIF -- LISTE A RELIRE")
    print("  " + "=" * 74)
    print("  source : %s  (%d lignes)" % (RAPPORT.name, len(lignes)))
    print()
    print("  A  CORRIGER  %3d liens  -- le gel se trompe de bien" % (len(A_CORRIGER) * 3))
    print("  B  RETIRER   %3d liens  -- poses sur une ligne doublon" % len(B_RETIRER))
    print("  C  AJOUTER   %3d liens  -- « v2 seul », >= 3 familles" % len(gros))
    print("     dont il faudra ECARTER ceux dont la transaction est deja prise")
    print("  " + "-" * 74)
    print("  « v2 seul » au total : %d   . a 1-2 familles (laisses) : %d"
          % (len(seuls), len(seuls) - len(gros)))
    print()

    with io.open(SORTIE, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["LOT", "geste", "ligne du classeur", "ID Unique", "role",
                    "transaction ACTUELLE (gel)", "transaction NOUVELLE (v2)",
                    "bien du gel", "bien de v2", "nb familles", "quelles familles",
                    "POURQUOI", "DECISION (a remplir)"])
        for ligne, idu, bien_gel, bien_v2, pourquoi in A_CORRIGER:
            for x in lignes:
                if (x.get("ligne") or "").strip() == str(ligne):
                    w.writerow(["A", "CORRIGER", ligne, idu, x.get("role", ""),
                                x.get("transaction GEL", ""), x.get("transaction v2", ""),
                                bien_gel, bien_v2, x.get("familles v2", ""),
                                x.get("quelles familles", ""), pourquoi, ""])
        for ligne, pourquoi in B_RETIRER:
            w.writerow(["B", "RETIRER", ligne, "", "(tous les roles de la ligne)",
                        "", "", "", "", "", "", pourquoi, ""])
        for x in gros:
            tx = (x.get("transaction v2") or "").strip()
            prise = DEJA_PRISES.get(tx)
            w.writerow(["C", "ECARTER (conflit)" if prise else "AJOUTER",
                        x.get("ligne", ""), x.get("ID Unique", ""),
                        x.get("role", ""), "", tx,
                        "", x.get("bien de la v2", ""), x.get("familles v2", ""),
                        x.get("quelles familles", ""),
                        ("⛔ transaction DEJA prise par la ligne %s" % prise) if prise
                        else (x.get("comment v2 a choisi", "")), ""])

    a_ajouter = sum(1 for x in gros if (x.get("transaction v2") or "").strip() not in DEJA_PRISES)
    ecartes = len(gros) - a_ajouter
    print("  LOT C, detail apres le controle des conflits :")
    print("     A AJOUTER (transaction libre)  : %3d" % a_ajouter)
    print("     ECARTES (transaction deja prise): %3d" % ecartes)
    print()
    if ecartes != len(DEJA_PRISES):
        print("  ⚠ ATTENTION : %d ecartes pour %d transactions connues en conflit."
              % (ecartes, len(DEJA_PRISES)))
        print("    (normal si une meme transaction revient sur plusieurs lignes)")
    print("  TOTAL DES GESTES : %d  (A %d + B %d + C %d)"
          % (len(A_CORRIGER) * 3 + len(B_RETIRER) + a_ajouter,
             len(A_CORRIGER) * 3, len(B_RETIRER), a_ajouter))
    print()
    print("  ecrit : %s" % SORTIE)
    print()
    print("  ⛔ RIEN N'A ETE ECRIT EN BASE. Le patch viendra apres ta relecture,")
    print("     et il ecartera les transactions deja prises (controle en base).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
