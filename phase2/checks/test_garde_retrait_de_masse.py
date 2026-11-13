#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE GARDE-FOU DU RETRAIT DE MASSE (mandats et relations).    13/11/2026

Audit : notice/AUDIT_SUPPRESSION_HEKTOR_TOUTES_FAMILLES_2026-11-13.md

CE QU'IL EPROUVE
  (1) LE TEMOIN INVERSE, EN PREMIER : les rythmes REELS mesures sur 34 nuits de
      journaux doivent PASSER. Un garde-fou qui crie chaque nuit n'en est plus un.
  (2) LE REFUS au-dela du plafond, avec un message qui dit la famille, les deux
      nombres, et que RIEN n'a ete ecrit.
  (3) L'INTERRUPTEUR APP_RETRAIT_DE_MASSE_AUTORISE.
  (4) L'ORDRE : dans les DEUX registres, le garde-fou est appele AVANT la
      premiere ecriture. C'est le vrai controle -- un arret a moitie serait pire
      que pas d'arret.
  (5) ⛔ LE PIEGE DES MANDATS : le compte ne doit porter QUE sur les vraies
      disparitions (`hektor_mandat_id IS NOT NULL`). Sans cela, l'import du
      registre legal du 28/10 (567 mandats, nes hors Hektor) aurait ete REFUSE.

! IL N'ECRIT RIEN, N'OUVRE AUCUNE BASE ET NE FAIT AUCUN APPEL RESEAU.

    python -I phase2/checks/test_garde_retrait_de_masse.py
    sortie 0 = vert . 1 = un controle en echec . 2 = n'a pas pu mesurer
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

ECHECS: list[str] = []


def controle(libelle: str, ok: bool, detail: str = "") -> None:
    print(("  OK    " if ok else "  ECHEC ") + libelle + (("  -- " + detail) if detail and not ok else ""))
    if not ok:
        ECHECS.append(libelle)


def main() -> int:
    try:
        from phase2.sync import garde_retrait_de_masse as g
    except Exception as exc:                                        # noqa: BLE001
        print("N'A PAS PU MESURER : import impossible (%s)" % type(exc).__name__)
        return 2

    os.environ.pop("APP_RETRAIT_DE_MASSE_AUTORISE", None)

    def leve(famille: str, combien: int, total: int | None = None) -> str | None:
        try:
            g.verifier(famille, combien, total_vivants=total)
        except g.RetraitDeMasseRefuse as exc:
            return str(exc)
        return None

    print()
    print("(1) LE TEMOIN INVERSE -- les rythmes REELS doivent PASSER")
    controle("relations : 17 (la plus forte nuit observee) passe", leve("relations", 17, 132937) is None)
    controle("relations : 0 passe", leve("relations", 0, 132937) is None)
    controle("mandats : 1 (la seule vraie disparition) passe", leve("mandats", 1, 26921) is None)
    controle("mandats : 0 passe", leve("mandats", 0, 26921) is None)
    controle("une famille inconnue n'est jamais bloquee", leve("photos", 999999) is None)

    print()
    print("(2) LE REFUS -- au-dela du plafond")
    for famille, plafond in sorted(g.PLAFONDS.items()):
        msg = leve(famille, plafond + 1, 100000)
        controle("%s : %d leve" % (famille, plafond + 1), msg is not None)
        if msg:
            controle("   le message nomme la famille", famille in msg, msg[:140])
            controle("   le message donne les deux nombres",
                     str(plafond + 1) in msg and str(plafond) in msg, msg[:140])
            controle("   le message dit que RIEN n'a ete touche", "AUCUNE" in msg, msg[:140])
        controle("%s : %d (le plafond exact) NE leve PAS" % (famille, plafond),
                 leve(famille, plafond, 100000) is None)

    print()
    print("(3) L'INTERRUPTEUR")
    os.environ["APP_RETRAIT_DE_MASSE_AUTORISE"] = "1"
    controle("allume : 100 000 passent", leve("relations", 100000, 132937) is None)
    os.environ["APP_RETRAIT_DE_MASSE_AUTORISE"] = "0"
    controle("eteint : les memes 100 000 levent", leve("relations", 100000, 132937) is not None)
    os.environ.pop("APP_RETRAIT_DE_MASSE_AUTORISE", None)
    controle("absent : les memes 100 000 levent", leve("relations", 100000, 132937) is not None)

    print()
    print("(4) L'ORDRE -- le garde-fou precede la premiere ecriture, DANS LES DEUX REGISTRES")
    for nom, chemin, ecriture in (
        ("relations", RACINE / "phase2" / "sync" / "relation_ledger.py",
         "UPDATE app_relation SET present_in_hektor = 0"),
        ("mandats", RACINE / "phase2" / "sync" / "mandat_ledger.py",
         "UPDATE app_mandat SET present_in_hektor = 0"),
    ):
        try:
            texte = io.open(chemin, encoding="utf-8", errors="replace").read()
        except Exception as exc:                                    # noqa: BLE001
            print("N'A PAS PU MESURER : %s illisible (%s)" % (chemin.name, type(exc).__name__))
            return 2
        garde = texte.find("garde_retrait_de_masse.verifier(")
        ecrit = texte.find(ecriture)
        controle("%s : le garde-fou est appele" % nom, garde > 0)
        controle("%s : l'ecriture existe bien (temoin)" % nom, ecrit > 0, ecriture)
        if garde > 0 and ecrit > 0:
            controle("%s : le garde-fou est AVANT l'ecriture" % nom, garde < ecrit,
                     "garde=%d ecriture=%d" % (garde, ecrit))

    print()
    print("(5) LE PIEGE DES MANDATS -- ne compter que les VRAIES disparitions")
    texte = io.open(RACINE / "phase2" / "sync" / "mandat_ledger.py",
                    encoding="utf-8", errors="replace").read()
    debut = texte.find("_a_retirer = con.execute(")
    fin = texte.find("garde_retrait_de_masse.verifier(", debut)
    extrait = texte[debut:fin] if debut > 0 and fin > debut else ""
    controle("le compte des mandats existe", debut > 0)
    controle("il exclut les mandats NES HORS HEKTOR (hektor_mandat_id IS NOT NULL)",
             "hektor_mandat_id IS NOT NULL" in extrait, extrait[:160])
    controle("il garde la meme clause que l'UPDATE (NOT EXISTS sur _vus)",
             "NOT EXISTS" in extrait and "_vus" in extrait)
    # le registre des relations, lui, n'a pas ce piege aujourd'hui : on verifie
    # qu'il compte bien TOUTE la liste (62 sur 62 portent un numero Hektor).
    controle("les relations comptent bien toute la liste (len(a_marquer))",
             "verifier(\n            \"relations\", len(a_marquer)" in
             io.open(RACINE / "phase2" / "sync" / "relation_ledger.py",
                     encoding="utf-8", errors="replace").read().replace("\r\n", "\n"))

    print()
    if ECHECS:
        print("ECHEC : %d controle(s) en echec" % len(ECHECS))
        for e in ECHECS:
            print("   . " + e)
        return 1
    print("VERT : tous les controles passent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
