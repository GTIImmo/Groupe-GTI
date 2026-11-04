#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE METIER DES PARTENAIRES, TIRE DE NETTY (l'ancien logiciel).          04/11/2026

Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §67 et §70 ;
       notice/AUDIT_INDEX_GLOBAL_CONTACTS_2026-11-04.md §14 et §16.

POURQUOI. Chez Hektor, un partenaire n'a qu'une typologie « partenaire », sans metier : le
formulaire en a un (hektorPartnerJobOptions, App.tsx), mais l'API ne le rend pas. Et cette
typologie est surtout la case par defaut de la migration (65 % des « partenaires » n'avaient
AUCUN type dans Netty). Le seul endroit ou le metier existe, c'est le classeur exporte de Netty
le 27/02/2026 (`contacts_extraits.xlsx`, champ `contact_type` ; codes : `notice modelo.txt`).

CE QUE FAIT CE SCRIPT. Il apparie chaque fiche PROFESSIONNELLE du classeur a la couche des
contacts par (nom, prenom, jour de creation) -- Hektor a recopie la date, methode des
appariements c3 du 01/11 -- et range, pour les seules paires SANS AMBIGUITE, le numero de la
fiche et ses codes dans la table locale `contact_metier_netty`. Aucun nom n'y est ecrit.

⛔ DONNEES PERSONNELLES : le classeur reste a la racine du depot, ignore par git, et ne part
   jamais chez Supabase. La table ne garde que des numeros et des codes.
⚠ PAR DEFAUT A BLANC : rien n'est ecrit sans --ecrire. Rejouable : la table est remplacee.

    python phase2/contacts/metier_netty.py            (compte, n'ecrit rien)
    python phase2/contacts/metier_netty.py --ecrire   (remplace la table)
Sortie : 0 = fait · 1 = echec (classeur absent ou illisible).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
CLASSEUR = RACINE / "contacts_extraits.xlsx"
TABLE = "contact_metier_netty"

# Les codes PROFESSIONNELS de Netty (contact_type, « notice modelo »). Exclus : les clients
# (1, 2, 6, 17, 24, 29), Autre (7), Collaborateur (23, nos salaries), Newsletter (35), et les
# venus du site (80-83, 85 Candidat, 87).
METIERS_PROS = {
    3: "maintenance", 4: "administration", 5: "technicien", 8: "marchand_de_biens",
    9: "apporteur", 10: "fournisseur", 11: "huissier", 12: "avocat", 13: "notaire",
    14: "banque", 15: "partenaire", 16: "agent_immobilier", 22: "mandataire",
    25: "investisseur", 26: "gestionnaire", 27: "promoteur", 34: "diagnostiqueur",
    36: "societe", 37: "lotisseur", 84: "courtier", 86: "parrain",
}


def norm(valeur) -> str:
    texte = unicodedata.normalize("NFKD", str(valeur or "")).encode("ascii", "ignore").decode().upper()
    return " ".join(texte.split())


def fiches_pros(classeur: Path):
    """(cle d'appariement, codes pros) de chaque fiche professionnelle non supprimee."""
    import openpyxl  # lecture seule, comme les audits du 01/11
    wb = openpyxl.load_workbook(classeur, read_only=True)
    ws = wb.worksheets[0]
    lignes = ws.iter_rows(values_only=True)
    entete = next(lignes)
    i = {nom: k for k, nom in enumerate(entete)}
    for r in lignes:
        if r[i["deleted"]]:
            continue
        try:
            codes = json.loads(r[i["contact_type"]] or "[]")
        except (TypeError, ValueError):
            continue
        pros = sorted({c for c in codes if c in METIERS_PROS}) if isinstance(codes, list) else []
        if pros:
            yield (norm(r[i["last_name"]]), norm(r[i["first_name"]]), str(r[i["time_created"]])[:10]), pros


def apparier(conn: sqlite3.Connection, fiches) -> tuple[dict[str, list[int]], Counter]:
    index = defaultdict(list)
    for cid, nom, prenom, jour in conn.execute(
            "SELECT hektor_contact_id, nom, prenom, substr(date_enregistrement,1,10) FROM app_contact_current"):
        index[(norm(nom), norm(prenom), jour)].append(str(cid))
    trouves: dict[str, list[int]] = {}
    bilan = Counter()
    for cle, codes in fiches:
        bilan["fiches pros"] += 1
        candidats = index.get(cle, [])
        if len(candidats) != 1:
            bilan["non appariees" if not candidats else "ambigues"] += 1
            continue
        cid = candidats[0]
        if cid in trouves:  # deux fiches Netty sur la meme fiche : on garde l'union des codes
            trouves[cid] = sorted(set(trouves[cid]) | set(codes))
            bilan["deux fiches Netty sur une fiche"] += 1
        else:
            trouves[cid] = codes
    bilan["fiches de la couche retenues"] = len(trouves)
    return trouves, bilan


def ecrire(conn: sqlite3.Connection, trouves: dict[str, list[int]]) -> None:
    maintenant = datetime.now().isoformat(timespec="seconds")
    with conn:
        conn.execute(f"DROP TABLE IF EXISTS {TABLE}")
        conn.execute(f"""CREATE TABLE {TABLE} (
            hektor_contact_id TEXT PRIMARY KEY,
            codes_json TEXT NOT NULL,
            metiers_json TEXT NOT NULL,
            apparie_le TEXT NOT NULL)""")
        conn.executemany(f"INSERT INTO {TABLE} VALUES (?, ?, ?, ?)", [
            (cid, json.dumps(codes), json.dumps([METIERS_PROS[c] for c in codes]), maintenant)
            for cid, codes in sorted(trouves.items())])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phase2-db", type=Path, default=BASE)
    ap.add_argument("--classeur", type=Path, default=CLASSEUR)
    ap.add_argument("--ecrire", action="store_true", help="remplace la table (sinon : a blanc)")
    args = ap.parse_args()
    if not args.classeur.exists():
        print(f"[metier netty] classeur absent : {args.classeur} -- rien n'est fait", file=sys.stderr)
        return 1
    conn = sqlite3.connect(args.phase2_db, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        trouves, bilan = apparier(conn, fiches_pros(args.classeur))
        par_metier = Counter(m for codes in trouves.values() for m in (METIERS_PROS[c] for c in codes))
        print("[metier netty] " + " · ".join(f"{k} {v}" for k, v in bilan.items()))
        print("[metier netty] par metier : " + ", ".join(f"{k} {v}" for k, v in par_metier.most_common()))
        if not args.ecrire:
            print("[metier netty] A BLANC : rien n'est ecrit (--ecrire pour remplacer la table)")
            return 0
        ecrire(conn, trouves)
        print(f"[metier netty] table {TABLE} remplie : {len(trouves)} fiche(s)")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
