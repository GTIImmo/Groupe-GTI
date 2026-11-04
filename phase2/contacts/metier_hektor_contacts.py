#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE METIER DES PARTENAIRES CREES CHEZ HEKTOR DEPUIS LA MIGRATION.            04/11/2026

Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §16 (lot 1, mini-chantier A9).

POURQUOI. Netty (contact_metier_netty) ne connait que les fiches d'AVANT la migration (01/03/2026), et
les deux listes de l'annonce (hektor_diag_contacts_choix) ne montrent que les syndics et les
diagnostiqueurs. Les partenaires crees depuis dans Hektor (numeros >= 601 900, 266 au 04/11) ont un
metier que l'API ne rend pas : il se lit dans leur formulaire, UNE requete par fiche
(Console/extract_hektor_metier_contacts.js, lecture seule).

CE QUE FAIT CE SCRIPT. Il range ce metier dans la table locale `hektor_contact_metier`
(data/hektor.sqlite) : numero Hektor, code et libelle du metier, date de lecture. Mise a jour, jamais
videe. Deux facons :
    python phase2/contacts/metier_hektor_contacts.py --importer <compte-rendu.json>
        (range un compte rendu deja produit par l'extracteur -- aucune requete chez Hektor)
    python phase2/contacts/metier_hektor_contacts.py --lire [--limit N]
        (lit chez Hektor les partenaires >= 601 900 jamais lus, puis range ; 1 requete/s)
Sortie : 0 = fait · 1 = echec · 3 = Hektor a refuse (403).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE_PHASE2 = RACINE / "phase2" / "phase2.sqlite"
BASE_HEKTOR = RACINE / "data" / "hektor.sqlite"
EXTRACTEUR = RACINE / "Console" / "extract_hektor_metier_contacts.js"
PREMIER_NUMERO_APRES_MIGRATION = 601900


def assurer_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS hektor_contact_metier (
            hektor_contact_id TEXT PRIMARY KEY,
            metier_code TEXT,
            metier_libelle TEXT,
            statut TEXT NOT NULL,
            erreur TEXT,
            lu_le TEXT NOT NULL
        )
        """
    )
    con.commit()


def ranger(resultats: list[dict]) -> dict[str, int]:
    con = sqlite3.connect(BASE_HEKTOR, timeout=30)
    try:
        assurer_table(con)
        comptes = {"done": 0, "erreur": 0}
        for r in resultats:
            numero = str(r.get("hektor_contact_id") or "").strip()
            if not numero.isdigit():
                continue
            metier = r.get("metier") or {}
            statut = str(r.get("status") or "error")
            con.execute(
                """
                INSERT INTO hektor_contact_metier (hektor_contact_id, metier_code, metier_libelle, statut, erreur, lu_le)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(hektor_contact_id) DO UPDATE SET
                    metier_code = CASE WHEN excluded.statut = 'done' THEN excluded.metier_code ELSE hektor_contact_metier.metier_code END,
                    metier_libelle = CASE WHEN excluded.statut = 'done' THEN excluded.metier_libelle ELSE hektor_contact_metier.metier_libelle END,
                    statut = excluded.statut, erreur = excluded.erreur, lu_le = excluded.lu_le
                """,
                (numero, metier.get("value"), metier.get("label"), statut, r.get("error"),
                 str(r.get("extracted_at") or datetime.now(timezone.utc).isoformat())),
            )
            comptes["done" if statut == "done" else "erreur"] += 1
        con.commit()
        return comptes
    finally:
        con.close()


def candidats(limite: int) -> list[str]:
    p2 = sqlite3.connect(f"file:{BASE_PHASE2.as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        numeros = [str(r[0]) for r in p2.execute(
            "SELECT CAST(hektor_target_id AS TEXT) FROM app_contact_current "
            "WHERE typologies_json LIKE '%partenaire%' AND CAST(hektor_target_id AS INTEGER) >= ?",
            (PREMIER_NUMERO_APRES_MIGRATION,))]
    finally:
        p2.close()
    deja: set[str] = set()
    if BASE_HEKTOR.exists():
        hk = sqlite3.connect(f"file:{BASE_HEKTOR.as_posix()}?mode=ro", uri=True, timeout=30)
        try:
            if hk.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='hektor_contact_metier'").fetchone():
                deja = {str(r[0]) for r in hk.execute("SELECT hektor_contact_id FROM hektor_contact_metier WHERE statut = 'done'")}
        finally:
            hk.close()
    reste = [n for n in sorted(numeros) if n not in deja]
    return reste[:limite] if limite > 0 else reste


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--importer", type=Path, help="compte rendu JSON de l'extracteur a ranger")
    ap.add_argument("--lire", action="store_true", help="lire chez Hektor les partenaires jamais lus")
    ap.add_argument("--limit", type=int, default=300)
    args = ap.parse_args()
    if args.importer:
        donnees = json.loads(args.importer.read_text(encoding="utf-8").strip().splitlines()[-1])
        comptes = ranger(donnees.get("results") or [])
        print(json.dumps({"statut": donnees.get("status"), **comptes}, ensure_ascii=False))
        return 3 if donnees.get("status") == "stopped_on_403" else 0
    if args.lire:
        numeros = candidats(args.limit)
        if not numeros:
            print(json.dumps({"statut": "rien_a_lire"}, ensure_ascii=False))
            return 0
        fini = subprocess.run(["node", str(EXTRACTEUR), "--contact-ids", ",".join(numeros), "--delay-ms", "1100"],
                              cwd=str(RACINE / "Console"), capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=120 * len(numeros) + 60)
        donnees = json.loads(fini.stdout.strip().splitlines()[-1]) if fini.stdout.strip() else {}
        comptes = ranger(donnees.get("results") or [])
        print(json.dumps({"statut": donnees.get("status"), "lus": len(numeros), **comptes}, ensure_ascii=False))
        return 3 if donnees.get("status") == "stopped_on_403" else (0 if fini.returncode == 0 else 1)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
