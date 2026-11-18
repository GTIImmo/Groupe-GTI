#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CE QU'IL A TRANCHE DANS L'ARBITRAGE, LIGNE PAR LIGNE.           18/11/2026

    .venv\Scripts\python.exe -X utf8 phase2\checks\arbitrage_ce_qu_il_a_tranche_2026-11-18.py

⛔ LECTURE SEULE. Il croise SES decisions (relevees dans la base de la page
  d'arbitrage) avec le dossier qui etait affiche, et rend DEUX listes :
    . CE QU'IL FAUT POSER  (« le classeur a raison »)
    . CE QU'IL A ECARTE    (« rien » -- dont les appariements qu'il juge FAUX)

⭐⭐ POURQUOI UN SCRIPT ET PAS UNE LECTURE A L'OEIL : 41 decisions, et chacune doit
  etre reliee a SA famille et a SA valeur. Une decision « classeur » ne dit pas
  QUOI poser : c'est le dossier qui le dit.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ECRAN = RACINE / "notice" / "LIGNES_A_TRANCHER_ECRAN_2026-11-18.json"
DECISIONS = Path(sys.argv[1]) if len(sys.argv) > 1 else None


def main() -> int:
    if DECISIONS is None or not DECISIONS.exists():
        print("⛔ donner en argument le fichier de ses decisions (JSON)")
        return 2
    dossier = {x["id"]: x for x in json.loads(ECRAN.read_text(encoding="utf-8"))}
    dec = json.loads(DECISIONS.read_text(encoding="utf-8"))
    print("=== LE DOSSIER AFFICHE : %d lignes . SES DECISIONS : %d ==="
          % (len(dossier), len(dec)))
    inconnues = [k for k in dec if k not in dossier]
    if inconnues:
        print("⛔ %d decisions ne correspondent a AUCUNE ligne du dossier : %s"
              % (len(inconnues), " ".join(inconnues)))
    sans = [k for k in dossier if k not in dec]
    print("lignes du dossier SANS decision : %d%s"
          % (len(sans), ("  -> " + " ".join(sans)) if sans else ""))
    print()

    poser, ecarte = [], []
    for ident, (choix, note) in sorted(dec.items()):
        x = dossier.get(ident)
        if not x:
            continue
        (poser if choix == "classeur" else ecarte).append((ident, x, note))

    print("=== ① CE QU'IL FAUT POSER -- « le classeur a raison » : %d ===" % len(poser))
    for fam, n in Counter(x["famille"] for _, x, _ in poser).most_common():
        print("   %-26s %3d" % (fam, n))
    print()
    for ident, x, _ in poser:
        print("   %-9s %-16s ligne %-6s  classeur %-14s  nous %-14s  %s"
              % (ident, x["famille"][:16], x["ligne"], str(x["classeur"])[:14],
                 str(x["nous"])[:14], str(x["ville"])[:28]))
    print()
    print("=== ② CE QU'IL A ECARTE -- « rien » : %d ===" % len(ecarte))
    for ident, x, note in ecarte:
        print()
        print("   ⛔ %s -- %s, ligne %s du Sheet" % (ident, x["famille"], x["ligne"]))
        print("      classeur %s   nous %s   ecart %s"
              % (x["classeur"], x["nous"], x["ecart"]))
        print("      %s . %s" % (str(x["ville"])[:40], str(x["vendeur"])[:34]))
        if note:
            print("      ⭐ SA NOTE : %s" % note)
        print("      ses dates au Sheet : offre %s . compromis %s . vente %s"
              % (x["sheet"].get("offre"), x["sheet"].get("compromis"),
                 x["sheet"].get("vente")))
        for t in x["app"]:
            print("      chez nous : %-10s %-10s %s%s"
                  % (t["k"], t["s"], t["d"],
                     ("   ⚑ " + t["alerte"]) if t.get("alerte") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
