#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA COUCHE CONTACTS SAIT-ELLE LIRE UN MENAGE ?  Base JETABLE.   11/09/2026

⚠ NE TOUCHE NI A phase2.sqlite NI A HEKTOR. Une base temporaire, le vrai
  `load_contacts`, et quatre cas dont un seul est vraiment difficile.

LE CAS DIFFICILE, ET POURQUOI IL EXISTE : `load_contacts` accepte une liste
d'identifiants -- c'est ce que fait refresh_contact_inproc.py pour rafraichir UN
contact. La porteuse n'est alors pas dans le lot charge. Resoudre le nom depuis
la memoire du lot donnerait « Contact 457053 » a une fiche dont le nom existe,
et personne ne le verrait avant des semaines.

    python phase2/checks/test_couple_couche.py
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from phase2.contacts.build_contacts_layer import load_contacts  # noqa: E402

SCHEMA = """
CREATE TABLE hektor_contact (
    hektor_contact_id TEXT PRIMARY KEY,
    hektor_agence_id TEXT, hektor_negociateur_id TEXT,
    civilite TEXT, nom TEXT, prenom TEXT, archive TEXT,
    date_enregistrement TEXT, date_maj TEXT, email TEXT, portable TEXT, fixe TEXT,
    ville TEXT, code_postal TEXT, adresse TEXT, typologie_json TEXT,
    raw_json TEXT, synced_at TEXT, hektor_couple_contact_id TEXT
);
"""

# nom, prenom, civilite, lien de menage
FICHES = {
    # la porteuse et sa fiche de menage : le cas courant, 93 873 fois au parc
    "141053": ("SELL AND SIGNE", "Test", "", "141053"),
    "485955": ("", "", "Mr./Mme", "141053"),
    # une fiche de menage dont la porteuse a disparu de Hektor : 14 080 au parc
    "595529": ("", "", "Mr./Mme", "586326"),
    # un contact ordinaire, qui ne doit surtout pas bouger
    "605030": ("TEST MANDANT 25-08", "Sophie", "", None),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as dossier:
        conn = sqlite3.connect(str(Path(dossier) / "jetable.sqlite"))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        for cid, (nom, prenom, civ, lien) in FICHES.items():
            conn.execute(
                "INSERT INTO hektor_contact(hektor_contact_id, civilite, nom, prenom, archive,"
                " typologie_json, raw_json, synced_at, hektor_couple_contact_id)"
                " VALUES (?, ?, ?, ?, '0', '[\"mandant\"]', '{}', '2026-09-11', ?)",
                (cid, civ, nom, prenom, lien),
            )
        conn.commit()

        par_id = {c.hektor_contact_id: c for c in load_contacts(conn)}
        attendus = [
            ("la fiche de menage emprunte l'identite de sa porteuse",
             par_id["485955"].display_name == "Mr./Mme Test SELL AND SIGNE"),
            ("et elle est marquee a masquer",
             par_id["485955"].couple_role == "menage_resolu"),
            ("porteuse disparue : le numero, pas « Mr./Mme »",
             par_id["595529"].display_name == "Contact 595529"),
            ("et elle est marquee a garder",
             par_id["595529"].couple_role == "menage_orphelin"),
            ("la porteuse elle-meme n'est PAS une fiche de menage",
             par_id["141053"].couple_role is None
             and par_id["141053"].display_name == "Test SELL AND SIGNE"),
            ("un contact ordinaire ne bouge pas",
             par_id["605030"].couple_role is None
             and par_id["605030"].display_name == "Sophie TEST MANDANT 25-08"),
        ]

        # ── LE CAS DIFFICILE : on ne charge QUE la fiche de menage.
        seule = load_contacts(conn, contact_ids=["485955"])
        attendus.append((
            "LOT PARTIEL : la porteuse est cherchee en base, pas dans le lot",
            len(seule) == 1 and seule[0].display_name == "Mr./Mme Test SELL AND SIGNE"))

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
