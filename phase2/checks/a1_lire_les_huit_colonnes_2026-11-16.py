#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A1 -- LES HUIT COLONNES QUE LE RAPPORT DU GEL NE COUVRE PAS.      16/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\a1_lire_les_huit_colonnes_2026-11-16.py

SON ENONCE, AU PLAN : « LIRE LE SHEET sur les 8 colonnes que le rapport NE COUVRE
PAS : F G Y AA Z AH AI AJ. Le rapport ne porte que 21 colonnes sur 38 -> pour ces
huit, je n'ai AUCUN ecart mesure, seulement les comptages du 02/11. »

⭐ POURQUOI A1 EST LE BON ENCHAINEMENT LE 16/11. Les 96 offres viennent d'etre
  posees et n'ont pas encore vecu une nuit : poser autre chose avant leur premiere
  epreuve doublerait la surface sans savoir si la premiere moitie tient. A1, lui,
  n'ecrit RIEN -- et il debloque QUATRE taches de la phase C a la fois :

      C3  Z  -> les 896 dates d annulation (et les motifs, via F)
      C4  F et G -> app_affaire_condition et app_affaire_note
      C8  Y et AA -> les deux plus gros postes du chantier, sans aucune case chez nous
      C9  AH AI AJ -> et le numero de mandat

⛔ LECTURE SEULE DE BOUT EN BOUT. Le Sheet est lu, phase2.sqlite n'est pas ouvert,
  rien n'est ecrit en base ni chez Hektor. Un seul fichier produit dans notice/.

⛔⛔ CE QU'ON NE FAIT PAS, ET C'EST LE VERROU V1 DU PROJET : on ne lit PAS les Apps
  Script du classeur -- c'est le geste de Frederic. On lit des COLONNES DE DONNEES,
  ce que l'apparieur fait depuis le 28/10.

⚠ ET LA FENETRE DU SHEET EST CELLE DE A3 : `lire_classeur` lit `A1:AL6000`. Mesure
  du 16/11 : le classeur porte 4 789 lignes, donc 1 211 de marge, et AL est bien la
  derniere colonne (A4bis du 31/10). Rien n'est perdu par le bas aujourd'hui.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

import apparier_classeur as ap                                      # noqa: E402

# ⚠ `lire_classeur` lit GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE dans l'environnement,
#   et apparier_classeur ne charge le `.env` que dans SON main (l. 387). Un script
#   qui importe la fonction doit donc le charger lui-meme -- sinon KeyError.
ap.load_env_file(RACINE / ".env")

SORTIE = RACINE / "notice" / "A1_LES_HUIT_COLONNES_2026-11-16.csv"

# Les huit, par leur LETTRE de colonne -- c'est ainsi que le plan les nomme, et
# c'est la seule facon de ne pas se tromper si un en-tete change de libelle.
LETTRES = ["F", "G", "Y", "Z", "AA", "AH", "AI", "AJ"]


def index_de(lettre: str) -> int:
    """« F » -> 5, « AA » -> 26. Zero-base, comme la liste rendue par le Sheet."""
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def est_une_date(v: str) -> bool:
    return bool(re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", v)
                or re.match(r"^\d{4}-\d{2}-\d{2}", v))


def est_un_nombre(v: str) -> bool:
    return bool(re.match(r"^-?[\d\s ]+([.,]\d+)?\s*(EUR|€)?$", v))


def main() -> int:
    entetes, lignes = ap.lire_classeur()
    print("classeur : %d lignes, %d colonnes lues" % (len(lignes), len(entetes)))
    print()

    print("=== LES HUIT COLONNES, LEUR LIBELLE ET CE QU'ELLES PORTENT ===")
    print()
    detail = []
    for lettre in LETTRES:
        i = index_de(lettre)
        libelle = entetes[i].strip() if i < len(entetes) else "(hors fenetre)"
        valeurs = []
        for _num, l in lignes:
            v = str(l[i]).strip() if i < len(l) else ""
            if v:
                valeurs.append(v)
        n = len(valeurs)
        formes = Counter("date" if est_une_date(v) else
                         "nombre" if est_un_nombre(v) else "texte" for v in valeurs)
        distinctes = len(set(valeurs))
        print("  %-3s %-26s rempli %4d / %d  (%.0f %%)"
              % (lettre, libelle[:26], n, len(lignes), 100.0 * n / max(1, len(lignes))))
        print("      formes : %s" % (dict(formes.most_common()) or "-"))
        print("      valeurs distinctes : %d" % distinctes)
        if distinctes and distinctes <= 12:
            print("      LA LISTE COMPLETE : %s"
                  % " . ".join("%s (%d)" % (v, c)
                               for v, c in Counter(valeurs).most_common()))
        else:
            print("      les 6 plus fréquentes : %s"
                  % " . ".join("%s (%d)" % (v[:30], c)
                               for v, c in Counter(valeurs).most_common(6)))
        print()
        detail.append({"lettre": lettre, "libelle": libelle, "rempli": n,
                       "distinctes": distinctes,
                       "formes": " ".join("%s=%d" % kv for kv in formes.most_common()),
                       "exemples": " | ".join(v[:40] for v, _ in
                                              Counter(valeurs).most_common(5))})

    # ── CE QUE CA DEBLOQUE, colonne par colonne ────────────────────────────────
    print("=== CE QUE CHAQUE COLONNE DEBLOQUE AU PLAN ===")
    for lettre, tache in (("Z", "C3  les 896 dates d annulation -> date_annulation_app"),
                          ("F", "C3/C4  les motifs d annulation, et les conditions"),
                          ("G", "C4  les notes -> app_affaire_note, origine classeur"),
                          ("Y", "C8  l un des deux plus gros postes du chantier"),
                          ("AA", "C8  l autre -- aucune case chez nous aujourd hui"),
                          ("AH", "C9  (et AH/AJ se contredisent sur 229 lignes)"),
                          ("AI", "C9"),
                          ("AJ", "C9")):
        d = next(x for x in detail if x["lettre"] == lettre)
        print("   %-3s %-28s %4d valeurs -> %s"
              % (lettre, d["libelle"][:28], d["rempli"], tache))
    print()

    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0]), delimiter=";")
        w.writeheader()
        w.writerows(detail)
    print("ecrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
