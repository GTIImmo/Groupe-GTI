#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA COLONNE AF S'APPELLE « Prix » -- MAIS EST-CE UN PRIX ?        17/11/2026

⛔ LECTURE SEULE.

⛔⛔ CE QUI A DECLENCHE CETTE MESURE : les trois valeurs les plus frequentes de la
  colonne « Prix » sont **43 (437 fois), 42 (308) et 63 (245)**. Ce ne sont pas des
  prix : ce sont les numeros des departements de la Loire, de la Haute-Loire et du
  Puy-de-Dome -- le secteur de l'agence. Et 66 lignes disent « NON TROUVÉ ».
  ➡ ON NE DECIDE RIEN sur une colonne dont on ne sait pas ce qu'elle contient.

⭐ LA METHODE : on ne demande pas « est-ce un prix ? » mais on RANGE les valeurs par
  ORDRE DE GRANDEUR. Un prix de maison et un numero de departement ne vivent pas
  dans le meme intervalle -- le tri suffit a trancher, sans supposer.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
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
    """Rend le nombre d'une case, ou None. Tolere les espaces et les virgules."""
    t = re.sub(r"[\s ]", "", (v or "").strip()).replace("€", "")
    t = t.replace(",", ".")
    if not re.fullmatch(r"\d+(\.\d+)?", t):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== LA COLONNE « Prix » CONTIENT-ELLE DES PRIX ? (lecture seule) ===")
    print()
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(lignes))
        return 2

    #: ⚠ ON NE SE FIE PAS A LA LETTRE SEULE : on cherche AUSSI la colonne par son
    #:   entete, et on DIT si les deux ne tombent pas au meme endroit.
    i_lettre = index_de("AF")
    i_nom = entetes.index("Prix") if "Prix" in entetes else None
    print("la lettre AF pointe la colonne %d : %r"
          % (i_lettre + 1, entetes[i_lettre] if i_lettre < len(entetes) else "(hors liste)"))
    print("l'entete « Prix » est a la colonne %s"
          % (i_nom + 1 if i_nom is not None else "(introuvable)"))
    if i_nom is not None and i_nom != i_lettre:
        print("⛔⛔ LES DEUX NE TOMBENT PAS AU MEME ENDROIT -- la lettre du plan est")
        print("   peut-etre fausse. On mesure LES DEUX.")
    print()

    for titre, i in [("AF (par la lettre)", i_lettre)] + (
            [("« Prix » (par l'entete)", i_nom)] if i_nom is not None and i_nom != i_lettre else []):
        if i is None or i >= len(entetes):
            continue
        valeurs = [str(l[i] if i < len(l) else "").strip() for _r, l in lignes]
        pleins = [v for v in valeurs if v]
        nombres = [n for n in (nombre(v) for v in pleins) if n is not None]
        textes = [v for v in pleins if nombre(v) is None]
        print("=== %s -- entete %r ===" % (titre, entetes[i]))
        print("   remplie %d . des NOMBRES %d . du TEXTE %d"
              % (len(pleins), len(nombres), len(textes)))
        print()
        print("   ⭐ PAR ORDRE DE GRANDEUR -- c'est ca qui tranche :")
        tranches = [
            ("moins de 100      (un DEPARTEMENT ?)", lambda x: x < 100),
            ("100 a 999", lambda x: 100 <= x < 1000),
            ("1 000 a 9 999", lambda x: 1000 <= x < 10000),
            ("10 000 a 99 999   (un PRIX possible)", lambda x: 10000 <= x < 100000),
            ("100 000 a 999 999 (un PRIX probable)", lambda x: 100000 <= x < 1000000),
            ("1 million et plus", lambda x: x >= 1000000),
        ]
        for libelle, test in tranches:
            c = sum(1 for x in nombres if test(x))
            print("      %-38s %5d  %5.1f %%"
                  % (libelle, c, 100.0 * c / len(nombres) if nombres else 0))
        print()
        if textes:
            print("   LE TEXTE (non numerique) :")
            for v, c in Counter(textes).most_common(5):
                print("      %5d x  %s" % (c, re.sub(r"\s+", " ", v)[:60]))
            print()
        #: ⭐ LE TEMOIN : si c'est un departement, les valeurs < 100 doivent etre
        #:   des departements REELS du secteur, pas n'importe quoi.
        petits = Counter(int(x) for x in nombres if x < 100)
        if petits:
            print("   LES VALEURS SOUS 100, par frequence :")
            for v, c in petits.most_common(10):
                print("      %5d x  %s" % (c, v))
            print("      -> %d valeurs distinctes sous 100" % len(petits))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
