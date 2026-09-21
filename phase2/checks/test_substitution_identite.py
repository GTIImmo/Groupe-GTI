#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4-b (②) — LA SUBSTITUTION RANGE-T-ELLE SOUS UNE SEULE FICHE ?  21/09/2026

CE QU'IL PROUVE, et il repond a la question posee -- pas « ca marche » :

    ① le contact ne dans l'app se range sous SON IDENTITE (10 000 002),
       PAS sous le numero de Hektor (605 453) ;
    ② sa recherche pend sous la meme identite ;
    ③ la seconde fiche, celle de l'essai casse, N'EXISTE PLUS ;
    ④ un contact ORDINAIRE, lui, ne bouge pas d'un pouce.

    ⚠ ④ est le plus important des quatre. Le defaut qu'on corrige touche 2
      fiches sur 356 002 ; une correction qui deplacerait les 356 000 autres
      serait infiniment pire que le defaut.

IL N'ECRIT JAMAIS DANS LA VRAIE BASE. Il travaille sur une COPIE, faite par
VACUUM INTO -- obligatoire ici : phase2.sqlite est en WAL, une copie de fichier
laisserait les dernieres ecritures dans le journal et mentirait.

Le miroir est ouvert en LECTURE SEULE.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "contacts"))

from build_contacts_layer import refresh_contact_slice  # noqa: E402

BASE = RACINE / "phase2" / "phase2.sqlite"
MIROIR = RACINE / "data" / "hektor.sqlite"

NUMERO_HEKTOR = "605453"      # ce que Hektor a donne au contact d'essai
IDENTITE_APP = "10000002"     # ce que l'app lui avait donne
TEMOIN = None                 # choisi au hasard dans le parc, plus bas


def copier(destination: Path) -> None:
    conn = sqlite3.connect(str(BASE))
    try:
        conn.execute("VACUUM INTO ?", (str(destination),))
    finally:
        conn.close()


def main() -> int:
    if not BASE.exists() or not MIROIR.exists():
        print("REFUS : base ou miroir introuvable.")
        return 2

    with tempfile.TemporaryDirectory() as dossier:
        copie = Path(dossier) / "essai.sqlite"
        copier(copie)

        conn = sqlite3.connect(str(copie))
        temoin = conn.execute(
            "SELECT hektor_contact_id FROM app_contact_current "
            "WHERE CAST(hektor_contact_id AS INTEGER) < 10000000 "
            "  AND active_search_count > 0 LIMIT 1").fetchone()
        temoin = temoin[0] if temoin else None
        avant_temoin = conn.execute(
            "SELECT COUNT(*) FROM app_contact_current WHERE hektor_contact_id = ?",
            (temoin,)).fetchone()[0] if temoin else 0
        conn.close()

        # ── LE GESTE : le worker demande un rafraichissement, avec le numero
        #    de Hektor -- c'est exactement ce qu'il a envoye le 21/09 a 14:35.
        resultat = refresh_contact_slice(
            contact_ids=[NUMERO_HEKTOR], hektor_db=MIROIR, phase2_db=copie)

        conn = sqlite3.connect(str(copie))
        sous_identite = conn.execute(
            "SELECT COUNT(*) FROM app_contact_current WHERE hektor_contact_id = ?",
            (IDENTITE_APP,)).fetchone()[0]
        sous_hektor = conn.execute(
            "SELECT COUNT(*) FROM app_contact_current WHERE hektor_contact_id = ?",
            (NUMERO_HEKTOR,)).fetchone()[0]
        recherches_identite = conn.execute(
            "SELECT COUNT(*) FROM app_contact_search_current WHERE hektor_contact_id = ?",
            (IDENTITE_APP,)).fetchone()[0]
        recherches_hektor = conn.execute(
            "SELECT COUNT(*) FROM app_contact_search_current WHERE hektor_contact_id = ?",
            (NUMERO_HEKTOR,)).fetchone()[0]

        # ④ le temoin : un contact ordinaire, rafraichi lui aussi, doit rester
        #    exactement ou il etait.
        apres_temoin = 0
        if temoin:
            refresh_contact_slice(contact_ids=[temoin], hektor_db=MIROIR, phase2_db=copie)
            apres_temoin = conn.execute(
                "SELECT COUNT(*) FROM app_contact_current WHERE hektor_contact_id = ?",
                (temoin,)).fetchone()[0]
        conn.close()

    print(f"   fiches construites            : {resultat['contacts_total']}")
    print(f"① sous l'identite {IDENTITE_APP}      : {sous_identite}   (attendu 1)")
    print(f"③ sous le numero Hektor {NUMERO_HEKTOR}  : {sous_hektor}   (attendu 0)")
    print(f"② recherches sous l'identite    : {recherches_identite}   (attendu >= 1)")
    print(f"   recherches sous Hektor        : {recherches_hektor}   (attendu 0)")
    print(f"④ temoin {temoin} : {avant_temoin} -> {apres_temoin}   (attendu 1 -> 1)")

    echecs = []
    if sous_identite != 1:
        echecs.append("① la fiche n'est pas rangee sous son identite")
    if sous_hektor != 0:
        echecs.append("③ la seconde fiche survit sous le numero de Hektor")
    if recherches_identite < 1:
        echecs.append("② la recherche ne pend pas sous l'identite")
    if recherches_hektor != 0:
        echecs.append("② une recherche pend encore sous le numero de Hektor")
    if temoin and (avant_temoin != 1 or apres_temoin != 1):
        echecs.append("④ UN CONTACT ORDINAIRE A BOUGE -- arreter tout")

    if echecs:
        print("\nECHEC :")
        for ligne in echecs:
            print(f"  - {ligne}")
        return 1
    print("\nOK : une personne, une fiche -- et le parc n'a pas bouge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
