# -*- coding: utf-8 -*-
"""C.2b -- Lot 1 : la serie de numeros de contact nait localement.

LE PATRON EST CELUI DE app_dossier, A L'IDENTIQUE :

    app_dossier                          app_contact  (ici)
        id            AUTOINCREMENT          app_contact_id     AUTOINCREMENT
        hektor_annonce_id  NULLABLE          hektor_contact_id  NULLABLE
        absent_depuis                        absent_depuis
        UNIQUE(hektor_annonce_id)            UNIQUE(hektor_contact_id)

POURQUOI NULLABLE : un contact cree dans l'app n'a PAS de numero Hektor. La case
reste vide jusqu'a ce que le worker rapporte le sien. Le patron existe depuis
toujours cote annonce et n'a jamais servi (0 ligne sur 56 894) -- ici il servira.

POURQUOI absent_depuis ET PAS UNE SUPPRESSION : regle du projet, « un dossier ne
perd jamais son numero ». Si Hektor cesse de renvoyer un contact, on le marque,
on ne l'efface pas -- sinon tout ce qui pend dessus devient orphelin.

CE QUE CE SCRIPT NE FAIT PAS : il ne touche a AUCUNE table existante, il n'ecrit
rien dans Supabase, et personne ne lit encore cette table. C'est une doublure.

RETOUR ARRIERE : DROP TABLE app_contact. Rien d'autre n'a change.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

BASE = Path(r"C:\Hektor\Projet\phase2\phase2.sqlite")
SOURCE = "app_contact_current"
REGISTRE = "app_contact"

SCHEMA = f"""
CREATE TABLE {REGISTRE} (
    app_contact_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    hektor_contact_id TEXT,
    created_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    absent_depuis     TEXT,
    UNIQUE(hektor_contact_id)
)
"""


def connecte() -> sqlite3.Connection:
    conn = sqlite3.connect(str(BASE), timeout=60)
    # phase2 est en WAL et plusieurs ecrivains coexistent : sans ce reglage, un
    # autre run (le rattrapage acquereurs) se fait tuer au bout de 5 secondes.
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="mesure et affiche, n'ecrit rien")
    args = ap.parse_args()

    conn = connecte()
    try:
        deja = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
            (REGISTRE,)).fetchone()[0]

        total = conn.execute(f"SELECT count(*) FROM {SOURCE}").fetchone()[0]
        vides = conn.execute(
            f"SELECT count(*) FROM {SOURCE} "
            "WHERE hektor_contact_id IS NULL OR trim(hektor_contact_id) = ''"
        ).fetchone()[0]
        doublons = conn.execute(
            f"SELECT count(*) FROM (SELECT hektor_contact_id FROM {SOURCE} "
            "GROUP BY 1 HAVING count(*) > 1)").fetchone()[0]
        non_num = conn.execute(
            f"SELECT count(*) FROM {SOURCE} "
            "WHERE CAST(hektor_contact_id AS INTEGER) = 0").fetchone()[0]

        print(f"source {SOURCE:26s} {total:8d} contacts")
        print(f"   sans numero Hektor      {vides:8d}")
        print(f"   numeros en double       {doublons:8d}")
        print(f"   numeros non numeriques  {non_num:8d}")
        print(f"   registre deja present   {'OUI' if deja else 'non'}")

        # On refuse de construire une identite sur des donnees douteuses.
        if vides or doublons:
            print("\nREFUS : la source contient des numeros vides ou en double.")
            return 2
        if deja:
            print(f"\nREFUS : {REGISTRE} existe deja -- ce script ne le reconstruit pas.")
            return 3
        if args.dry_run:
            print("\n--dry-run : rien ecrit.")
            return 0

        print(f"\ncreation de {REGISTRE} ...")
        conn.execute(SCHEMA)

        # L'ordre decide de la serie. On suit l'ordre de Hektor : le numero 1 de
        # l'app correspond au plus ancien contact, ce qui rend la table lisible.
        print("remplissage ...")
        conn.execute(
            f"INSERT INTO {REGISTRE} (hektor_contact_id) "
            f"SELECT hektor_contact_id FROM {SOURCE} "
            "ORDER BY CAST(hektor_contact_id AS INTEGER), hektor_contact_id")
        conn.commit()

        # --- verification, apres coup et sur la base reelle
        pose = conn.execute(f"SELECT count(*) FROM {REGISTRE}").fetchone()[0]
        mini, maxi = conn.execute(
            f"SELECT min(app_contact_id), max(app_contact_id) FROM {REGISTRE}").fetchone()
        distincts = conn.execute(
            f"SELECT count(DISTINCT app_contact_id) FROM {REGISTRE}").fetchone()[0]
        orphelins = conn.execute(
            f"SELECT count(*) FROM {SOURCE} s "
            f"WHERE NOT EXISTS (SELECT 1 FROM {REGISTRE} r "
            "WHERE r.hektor_contact_id = s.hektor_contact_id)").fetchone()[0]

        print(f"\n   lignes posees        {pose:8d}   (source {total})")
        print(f"   numeros              {mini} .. {maxi}")
        print(f"   distincts            {distincts:8d}")
        print(f"   contacts sans numero {orphelins:8d}")

        ok = (pose == total and distincts == total and orphelins == 0
              and mini == 1 and maxi == total)
        print("\n" + ("REGISTRE POSE ET VERIFIE." if ok else "ANOMALIE -- a examiner."))
        return 0 if ok else 4
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
