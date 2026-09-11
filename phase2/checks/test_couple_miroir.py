#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE RUN ECRIT-IL LE LIEN DE MENAGE ?  Sur base JETABLE.        11/09/2026

⚠ NE TOUCHE NI AU MIROIR NI A HEKTOR. Une base temporaire, le vrai schema, la
  vraie fonction d'insertion du run. On verifie trois choses, et pas seulement
  que « ca marche » :

    1. le lien arrive          -- le listing porte `refCouple`, il est ecrit
    2. le lien tient           -- une source qui ne le porte PAS ne l'efface pas
    3. « 0 » ne vaut pas lien  -- Hektor ecrit « 0 » pour dire « aucun menage »

  Le point 2 est le seul qui compte vraiment : c'est celui qui, s'il tombait,
  retirerait d'un coup le nom de 96 877 fiches.

    python phase2/checks/test_couple_miroir.py
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from hektor_pipeline.common import init_db  # noqa: E402
from normalize_source import upsert_contact_from_sources  # noqa: E402


def lien(conn: sqlite3.Connection, contact_id: str):
    ligne = conn.execute(
        "SELECT hektor_couple_contact_id FROM hektor_contact WHERE hektor_contact_id = ?",
        (contact_id,),
    ).fetchone()
    return ligne[0] if ligne else "(absent)"


def main() -> int:
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "jetable.sqlite"
        conn = sqlite3.connect(str(chemin))
        conn.row_factory = sqlite3.Row
        init_db(conn)

        attendus = []

        # 1. UN MENAGE ARRIVE PAR LE LISTING.
        upsert_contact_from_sources(conn, {
            "id": "111", "nom": "", "prenom": "", "civilite": "Mr./Mme", "refCouple": "110",
        })
        attendus.append(("le lien arrive du listing", lien(conn, "111") == "110"))

        # 2. LA MEME FICHE REVIENT SANS LE LIEN  -- le cas qui fait peur.
        #    Une source partielle ne doit RIEN effacer.
        upsert_contact_from_sources(conn, {
            "id": "111", "nom": "", "prenom": "", "civilite": "Mr./Mme",
        })
        attendus.append(("une source sans lien ne l'efface pas", lien(conn, "111") == "110"))

        # 3. « 0 » VEUT DIRE « AUCUN MENAGE », pas « menage numero zero ».
        upsert_contact_from_sources(conn, {
            "id": "222", "nom": "SEUL", "prenom": "Jean", "refCouple": "0",
        })
        attendus.append(("« 0 » ne vaut pas un lien", lien(conn, "222") is None))

        # 4. LE DETAIL L'EMPORTE QUAND IL PORTE LE LIEN, comme pour tout le reste.
        upsert_contact_from_sources(
            conn,
            {"id": "333", "nom": "", "prenom": ""},
            detail_source={"id": "333", "nom": "", "prenom": "", "refCouple": "300"},
        )
        attendus.append(("le detail pose le lien", lien(conn, "333") == "300"))

        # 5. UN VRAI CHANGEMENT DE MENAGE PASSE. Le lien n'est pas fige.
        upsert_contact_from_sources(conn, {
            "id": "111", "nom": "", "prenom": "", "refCouple": "999",
        })
        attendus.append(("un lien different remplace l'ancien", lien(conn, "111") == "999"))

        ok = True
        for libelle, verdict in attendus:
            if not verdict:
                ok = False
            print("   %s %s" % ("OK    " if verdict else "ECHEC ", libelle))
        print("\n   >>> %s" % ("TOUT PASSE" if ok else "IL Y A UN ECHEC"))
        conn.close()
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
