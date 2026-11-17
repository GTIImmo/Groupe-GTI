#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES DECISIONS EN ATTENTE DU CHANTIER CLASSEUR -- de quoi trancher. 17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\classeur_aide_aux_decisions_2026-11-17.py

⛔ LECTURE SEULE, rien n'est ecrit ni genere.

Sa demande du 17/11 : « Aide moi pour les decisions en attente ». Une decision ne se
prend pas sur un nom de colonne : il faut le REMPLISSAGE, des EXEMPLES REELS, et ce
qu'on a DEJA chez nous. C'est ce que ce script sort, colonne par colonne.

LES COLONNES CONCERNEES (lettre du Sheet -> ce que le plan en dit) :
   U  X    « Signe » / « Signee »   -> a quoi servent-ils ? JAMAIS tranche
   AA      N0 de facture            -> deja rapatrie par C8, mais VISIBLE ou NON ?
   AC AE AK                         -> JAMAIS MESUREES
   AF      Prix                     -> « on liste » (C10)
"""
from __future__ import annotations

import re
import sys
import unicodedata
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

#: les lettres a examiner, et ce que le plan en dit
A_EXAMINER = [
    ("U", "« Signe » -- a quoi sert-il ?"),
    ("X", "« Signee » -- a quoi sert-il ?"),
    ("AA", "N0 de facture -- deja rapatrie (C8), VISIBLE ou NON ?"),
    ("AC", "jamais mesuree"),
    ("AE", "jamais mesuree"),
    ("AF", "Prix -- « on liste » (C10)"),
    ("AK", "jamais mesuree"),
]


def index_de(lettre: str) -> int:
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def est_pictogramme(c: str) -> bool:
    if c in " \t ":
        return False
    return unicodedata.category(c).startswith("S") or ord(c) > 0x2000


def forme(v: str) -> str:
    """La FORME d'une valeur, pas sa valeur : pour voir si une colonne est homogene."""
    t = (v or "").strip()
    if not t:
        return "(vide)"
    if all(est_pictogramme(c) or c.isspace() for c in t):
        return "pictogramme seul"
    if re.fullmatch(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", t):
        return "une DATE jj/mm/aaaa"
    if re.fullmatch(r"\d{1,2}\s+[a-zA-Zéûîôàè]+\s*\d{0,4}", t):
        return "une date en TEXTE (« 5 decembre23 »)"
    if re.fullmatch(r"[\d  .,]+\s*(€|EUR)?", t):
        return "un MONTANT"
    if re.fullmatch(r"\d+", t):
        return "un NOMBRE entier"
    if re.fullmatch(r"(?i)(oui|non|o|n|x|v)", t):
        return "un OUI/NON"
    if len(t) <= 3:
        return "un code court (<= 3 car.)"
    return "du TEXTE libre"


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== LES DECISIONS EN ATTENTE -- DE QUOI TRANCHER (lecture seule) ===")
    print()

    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    n = len(lignes)
    i_etat = entetes.index("Etat Actuel")
    print("le classeur : %d lignes, %d colonnes" % (n, len(entetes)))
    print()

    def case(l, i):
        return str(l[i] if i < len(l) else "").strip()

    for lettre, note in A_EXAMINER:
        i = index_de(lettre)
        if i >= len(entetes):
            print("=== %-3s HORS DU CLASSEUR (il n'a que %d colonnes) ==="
                  % (lettre, len(entetes)))
            print()
            continue
        nom = entetes[i] or "(sans entete)"
        valeurs = [case(l, i) for _r, l in lignes]
        pleins = [v for v in valeurs if v]
        print("=== %-3s « %s » ===" % (lettre, nom[:46]))
        print("    le plan dit : %s" % note)
        print("    remplie %d fois sur %d  (%.1f %%)" % (len(pleins), n, 100.0 * len(pleins) / n))
        if not pleins:
            print("    ⛔ TOTALEMENT VIDE -> il n'y a RIEN a decider.")
            print()
            continue
        print("    valeurs DISTINCTES : %d" % len({v for v in pleins}))
        print("    les FORMES rencontrees :")
        for f, c in Counter(forme(v) for v in pleins).most_common(6):
            print("       %-34s %5d  %5.1f %%" % (f, c, 100.0 * c / len(pleins)))
        print("    EXEMPLES REELS (les plus frequents) :")
        for v, c in Counter(pleins).most_common(6):
            #: ⛔ les retours a la ligne d'une adresse font TOMBER la console
            #:   Windows (code -1) : on les aplatit AVANT d'afficher.
            propre = re.sub(r"\s+", " ", v).strip()
            print("       %5d x  %s" % (c, propre[:66]))
        #: ⭐ une colonne qui ne se remplit que sur UN etat dit a quoi elle sert
        par_etat = Counter(case(l, i_etat) or "(vide)"
                           for _r, l in lignes if case(l, i))
        print("    QUAND est-elle remplie ? (etat de l'affaire)")
        for e, c in par_etat.most_common(4):
            print("       %-26s %5d  %5.1f %%" % (e[:26], c, 100.0 * c / len(pleins)))
        print()

    # ─── U x X : LE CROISEMENT, qui dit a quoi ils servent ───────────────────
    #: ⭐ DEUX BOOLEENS A 100 % DE REMPLISSAGE ne se devinent pas par leur nom
    #:   (« Signe » et « Signee » !). On les CROISE avec l'etat de l'affaire :
    #:   une case qui vaut TRUE pour toutes les ventes reglees et FALSE pour les
    #:   annulees dit ce qu'elle signifie, sans qu'on ait a supposer.
    i_u, i_x = index_de("U"), index_de("X")
    if i_u < len(entetes) and i_x < len(entetes):
        print("=== U x X -- LE CROISEMENT QUI DIT A QUOI ILS SERVENT ===")
        croise = Counter()
        par_etat_ux = Counter()
        for _r, l in lignes:
            u, x = case(l, i_u), case(l, i_x)
            e = case(l, i_etat) or "(vide)"
            croise[(u, x)] += 1
            par_etat_ux[(e, u, x)] += 1
        print("    U=%r . X=%r" % (entetes[i_u], entetes[i_x]))
        for (u, x), c in croise.most_common():
            print("       U=%-6s X=%-6s %5d  %5.1f %%" % (u, x, c, 100.0 * c / n))
        print()
        print("    ET PAR ETAT -- c'est ca qui tranche :")
        for (e, u, x), c in par_etat_ux.most_common(10):
            print("       %-24s U=%-6s X=%-6s %5d" % (e[:24], u, x, c))
        print()

    # ─── C6 : LES VENTES EN CONFLIT ──────────────────────────────────────────
    print("=== C6 -- LES 26 VENTES OU NOTRE COMPROMIS PORTE DEJA UNE AUTRE DATE ===")
    print("   ⛔ C'est un CONFLIT, pas un vide : ecraser effacerait une date que")
    print("     NOUS avons, au profit d'une date du Sheet. Sa decision.")
    print("   ⚠ La mesure complete demande le rapport du gel ; on donne ici ce que")
    print("     le classeur seul permet de dire.")
    i_v = index_de("V")
    if i_v < len(entetes):
        print("   la colonne V est « %s », remplie %d fois"
              % (entetes[i_v], sum(1 for _r, l in lignes if case(l, i_v))))
    print()
    print("⭐ CE QUE CE SCRIPT NE DIT PAS, et il ne le pretend pas : si une colonne")
    print("  vaut la peine d'etre rapatriee. Ca, c'est sa decision -- le script")
    print("  donne seulement de quoi la prendre.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
