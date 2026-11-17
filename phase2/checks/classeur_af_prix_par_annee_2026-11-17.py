#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""POURQUOI 1 008 DEPARTEMENTS DANS LA COLONNE « Prix » ?           17/11/2026

⛔ LECTURE SEULE. On croise la NATURE de la valeur avec l'ANNEE de l'affaire :
  si les departements sont les lignes ANCIENNES, la colonne a change d'usage en
  cours de route, et la decision devient simple (on ne reprend que la periode
  ou elle porte un prix).
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import apparier_classeur as ap                                      # noqa: E402


def index_de(lettre: str) -> int:
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def nombre(v: str):
    t = re.sub(r"[\s ]", "", (v or "").strip()).replace("€", "").replace(",", ".")
    if not re.fullmatch(r"\d+(\.\d+)?", t):
        return None
    return float(t)


def annee(v: str):
    """L'annee d'une date du classeur -- les DEUX formats (lecon du 14/11)."""
    t = (v or "").strip()
    m = re.search(r"(?:^|\D)(\d{4})(?:\D|$)", t)
    if m:
        a = int(m.group(1))
        if 1990 <= a <= 2040:
            return a
    m = re.search(r"(\d{2})\s*$", t)
    if m:
        a = 2000 + int(m.group(1))
        if 2000 <= a <= 2040:
            return a
    return None


def nature(v: str) -> str:
    n = nombre(v)
    if n is None:
        return "TEXTE (« NON TROUVÉ »)"
    if n < 100:
        return "DEPARTEMENT (< 100)"
    if n < 10000:
        return "douteux (100 a 9 999)"
    return "un PRIX (>= 10 000)"


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== LA COLONNE « Prix » : SA NATURE, PAR ANNEE (lecture seule) ===")
    print()
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(lignes))
        return 2
    i_prix = entetes.index("Prix")
    #: ⭐ l'annee vient de « Vente Réglée » en premier (la plus sure), puis de
    #:   « Compromis », puis de « Offre Achat » -- on prend la PREMIERE connue.
    sources = [c for c in ("Vente Réglée", "Compromis", "Offre Achat") if c in entetes]
    idx = [entetes.index(c) for c in sources]
    print("colonne du prix : %d . sources d'annee : %s" % (i_prix + 1, " > ".join(sources)))
    print()

    par_annee = defaultdict(Counter)
    sans_annee = Counter()
    for _r, l in lignes:
        v = str(l[i_prix] if i_prix < len(l) else "").strip()
        if not v:
            continue
        a = None
        for i in idx:
            a = annee(str(l[i] if i < len(l) else ""))
            if a:
                break
        if a is None:
            sans_annee[nature(v)] += 1
        else:
            par_annee[a][nature(v)] += 1

    cles = ("un PRIX (>= 10 000)", "DEPARTEMENT (< 100)",
            "douteux (100 a 9 999)", "TEXTE (« NON TROUVÉ »)")
    print("   annee      PRIX   DEPT  douteux  texte    total   %% de DEPT")
    for a in sorted(par_annee):
        c = par_annee[a]
        tot = sum(c.values())
        print("   %-8s %6d %6d %7d %6d %8d %9.1f %%"
              % (a, c[cles[0]], c[cles[1]], c[cles[2]], c[cles[3]], tot,
                 100.0 * c[cles[1]] / tot if tot else 0))
    if sans_annee:
        tot = sum(sans_annee.values())
        print("   %-8s %6d %6d %7d %6d %8d %9.1f %%"
              % ("(sans)", sans_annee[cles[0]], sans_annee[cles[1]],
                 sans_annee[cles[2]], sans_annee[cles[3]], tot,
                 100.0 * sans_annee[cles[1]] / tot if tot else 0))
    print()
    #: ⭐⭐ LE VERDICT : y a-t-il une ANNEE DE BASCULE ?
    #: ⛔⛔ MON PREMIER TEST A CONCLU FAUX, et un script qui conclut faux est pire
    #:   qu'un script muet. Il rangeait 2017 dans « le prix domine » sur **2
    #:   lignes** (1 prix, 1 texte), ce qui cassait l'ordre et faisait dire
    #:   « pas de bascule nette » alors qu'elle saute aux yeux :
    #:      2018 82 % dept . 2019 94 % . 2020 61 % || 2021 2,4 % . 2022 0,6 %
    #:   ➡ UNE ANNEE A DEUX LIGNES NE TEMOIGNE DE RIEN : on exige un plancher.
    PLANCHER = 30
    annees = [a for a in sorted(par_annee) if sum(par_annee[a].values()) >= PLANCHER]
    maigres = [a for a in sorted(par_annee) if sum(par_annee[a].values()) < PLANCHER]
    if maigres:
        print("   ⚠ annees ECARTEES du verdict (moins de %d lignes) : %s"
              % (PLANCHER, ", ".join(map(str, maigres))))
    avant = [a for a in annees
             if par_annee[a][cles[1]] > par_annee[a][cles[0]]]
    apres = [a for a in annees
             if par_annee[a][cles[0]] > par_annee[a][cles[1]]]
    print("   annees ou le DEPARTEMENT domine : %s"
          % (", ".join(map(str, avant)) or "aucune"))
    print("   annees ou le PRIX domine        : %s"
          % (", ".join(map(str, apres)) or "aucune"))
    if avant and apres and max(avant) < min(apres):
        print("   ⭐⭐⭐ IL Y A UNE BASCULE NETTE : departement jusqu'en %d, prix a"
              " partir de %d." % (max(avant), min(apres)))
        print("     ➡ LA COLONNE A CHANGE D'USAGE en cours de route.")
    else:
        print("   ⚠ PAS DE BASCULE NETTE : les deux natures se melangent dans les")
        print("     memes annees.")
    print()
    #: ⭐⭐ ET LA BONNE REGLE N'EST PAS L'ANNEE, C'EST LA VALEUR. Trier par annee
    #:   perdrait les 232 vrais prix de 2020 (une annee de transition : 61 % de
    #:   departements MAIS 232 prix). L'ordre de grandeur, lui, ne se trompe pas :
    #:   un departement est sous 100, un prix immobilier depasse 10 000.
    tot_prix = sum(par_annee[a][cles[0]] for a in par_annee) + sans_annee[cles[0]]
    tot_dept = sum(par_annee[a][cles[1]] for a in par_annee) + sans_annee[cles[1]]
    tot_dout = sum(par_annee[a][cles[2]] for a in par_annee) + sans_annee[cles[2]]
    print("   ⭐⭐ LA REGLE QUI NE SE TROMPE PAS N'EST PAS L'ANNEE, C'EST LA VALEUR :")
    print("      un PRIX (>= 10 000)          %5d  <- reprenables" % tot_prix)
    print("      un DEPARTEMENT (< 100)       %5d  <- a ECARTER" % tot_dept)
    print("      douteux (100 a 9 999)        %5d  <- a REGARDER un par un" % tot_dout)
    print("   ⚠ Trier par ANNEE perdrait les %d vrais prix de 2020, une annee de"
          % par_annee.get(2020, Counter())[cles[0]])
    print("     transition. Trier par la VALEUR les garde tous.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
