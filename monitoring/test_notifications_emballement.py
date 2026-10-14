#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPREUVE : les 2 sondes de notifications surveillent l'EMBALLEMENT, plus le total.

LE DEFAUT. Elles etaient en alerte 318 fois sur 318 en un mois -- JAMAIS VERTES.
Mesure : notif_non_lues est passee de 1 110 a 1 601 (+15,8 par jour), et
notif_orphelines de 81 a 166 (+2,7 par jour).

⚠ POURQUOI PAS SIMPLEMENT « MONTER LE SEUIL », CE QUE FREDERIC AVAIT DEMANDE :
  parce qu'un seuil absolu sur un compteur qui ne fait que croitre est une alarme
  A RETARDEMENT. A +15,8 par jour, un seuil a 2 000 serait franchi dans 25 jours.
  On surveille donc ce qui a du sens : le compte DOUBLE-T-IL d'un coup ?

    python monitoring/test_notifications_emballement.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_gti_health as cgh  # noqa: E402

NON_LUES = [s for s in cgh.DATA_SENTINELS if s["key"] == "data.notif_non_lues"][0]
ORPHELINES = [s for s in cgh.DATA_SENTINELS if s["key"] == "data.notif_orphelines"][0]


def juger(sentinelle: dict, compte: int, precedent: int | None):
    """Fait tourner LE vrai `_evaluate_sentinel`, en lui donnant un passage precedent."""
    mon = cgh.Monitor(argparse.Namespace(project_root="."), None)
    mon._previous_sentinel_count = lambda _cle, _v=precedent: _v
    return mon._evaluate_sentinel(sentinelle, compte)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    cas = [
        # --- notifications non lues : 1 601 aujourd'hui, +1,3 par passage ---
        ("1. LE CAS D'AUJOURD'HUI : 1 601 apres 1 600 -> VERT (c'etait rouge avant)",
         NON_LUES, 1601, 1600, "ok"),
        ("2. croissance normale d'une journee : 1 617 apres 1 601 -> vert",
         NON_LUES, 1617, 1601, "ok"),
        ("3. EMBALLEMENT : 1 801 apres 1 601 (+12,5 %, +200) -> CA SONNE",
         NON_LUES, 1801, 1601, "warning"),
        ("4. +11 % mais seulement +11 (petit total) -> vert, growth_abs protege",
         NON_LUES, 111, 100, "ok"),
        ("5. premier passage, aucun precedent -> vert, on pose le repere",
         NON_LUES, 1601, None, "ok"),
        ("6. ca BAISSE (quelqu'un a lu) : 900 apres 1 601 -> vert",
         NON_LUES, 900, 1601, "ok"),
        # --- notifications sans destinataire : 166 aujourd'hui, +0,23 par passage ---
        ("7. LE CAS D'AUJOURD'HUI : 166 apres 165 -> VERT (c'etait rouge avant)",
         ORPHELINES, 166, 165, "ok"),
        ("8. croissance normale d'une semaine : 185 apres 166 -> vert",
         ORPHELINES, 185, 166, "ok"),
        ("9. EMBALLEMENT : 200 apres 166 (+20 %, +34) -> CA SONNE",
         ORPHELINES, 200, 166, "warning"),
        ("10. +20 % mais seulement +4 -> vert, growth_abs protege",
         ORPHELINES, 24, 20, "ok"),
    ]

    rates = 0
    for titre, sentinelle, compte, precedent, voulu in cas:
        statut, message, _ = juger(sentinelle, compte, precedent)
        if statut != voulu:
            rates += 1
            print("  ECHEC  " + titre)
            print("         statut %r, attendu %r" % (statut, voulu))
            print("         message : " + message)
        else:
            print("  ok     %-74s [%s]" % (titre, statut))

    # --- ce que l'ancien reglage disait des memes chiffres -------------------
    print()
    print("-- TEMOIN INVERSE : les memes chiffres avec l'ancien reglage --")
    ancien_nl = dict(NON_LUES, rule="absolute", max=300)
    ancien_or = dict(ORPHELINES, rule="absolute", max=20)
    for nom, s, v in (("notif_non_lues  ", ancien_nl, 1601), ("notif_orphelines", ancien_or, 166)):
        sa, ma, _ = juger(s, v, v - 1)
        sn, mn, _ = juger(NON_LUES if "non_lues" in nom else ORPHELINES, v, v - 1)
        fleche = "BASCULE" if sa != sn else "IDENTIQUE"
        print("  %s  AVANT [%s]  APRES [%s]  -> %s" % (nom, sa, sn, fleche))
        if sa == sn:
            print("         ECHEC : rien n'a change, l'epreuve ne mesure rien")
            rates += 1

    print()
    if rates:
        print("%d epreuve(s) en ECHEC." % rates)
        return 1
    print("Les %d epreuves passent : le total n'alerte plus, l'emballement si." % len(cas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
