"""05/11/2026 -- L'OFFRE OUBLIEE REGULARISEE : accepter suffit-il a la rattacher a son compromis la nuit ?

Note : notice/AUDIT_REFONTE_MODALE_STATUT_2026-11-05.md §14 (option 1).
On EXECUTE la vraie regle de nuit (`recalculer_les_chaines`) sur une base SQLite EN MEMOIRE -- aucune base
reelle n'est ouverte -- avec les interrupteurs tels qu'ils sont allumes en production (.env, lu par le module).

Le cas : une offre faite le 01/09 au nom de Monsieur (A1), restee « proposee » ; un compromis du 12/10 au nom de
Madame (B1). Noms differents : le § 2.8 ne les relie pas. L'ecran rend alors « Accepter » a l'offre
(offreARegulariser). On verifie que, l'offre une fois ACCEPTEE, la nuit met le compromis dans SON dossier.

TEMOIN INVERSE : la meme offre datee APRES le compromis, acceptee, ne doit PAS l'attirer -- c'est pourquoi l'ecran
exige la date. Et l'offre laissee « proposee » ne doit rien attirer non plus (le probleme de depart).

    python phase2/sync/test_chainage_offre_regularisee.py
    sortie 0 = tout vert · 1 = un controle en echec
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import affaire_ledger as al  # noqa: E402

echecs = 0


def ok(cond: bool, libelle: str) -> None:
    global echecs
    print(("  OK  " if cond else "  ⛔  ") + libelle)
    if not cond:
        echecs += 1


def base(lignes: list[tuple]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute(f"""CREATE TABLE {al.LEDGER_TABLE} (
        app_affaire_id INTEGER PRIMARY KEY, hektor_annonce_id TEXT, kind TEXT, state TEXT, date TEXT,
        acquereurs_json TEXT, propositions_json TEXT, hektor_affaire_id TEXT, present_in_hektor TEXT,
        app_chaine_id INTEGER)""")
    for (ident, kind, state, jour, acq) in lignes:
        props = json.dumps([{"type": "proposition", "date": jour + " 10:00:00"}]) if kind == "offre" else None
        con.execute(f"INSERT INTO {al.LEDGER_TABLE} VALUES (?,?,?,?,?,?,?,?,?,NULL)",
                    (ident, "59132", kind, state, jour, json.dumps([{"id": acq}]), props, str(ident), "1"))
    return con


def chaines(lignes: list[tuple]) -> dict[int, int]:
    con = base(lignes)
    al.recalculer_les_chaines(con)
    return dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {al.LEDGER_TABLE}"))


print("interrupteurs lus par le module :",
      "V2" if al.chainage_v2_actif() else "-", "| 2.8" if al.chainage_offre_proposee_actif() else "| -")

print("Le probleme de depart — l'offre reste « proposee »")
c = chaines([(101, "offre", "proposed", "2026-09-01", "A1"), (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] != c[110], f"offre et compromis dans deux dossiers (offre {c[101]}, compromis {c[110]})")

print("La regularisation — l'offre ACCEPTEE")
c = chaines([(101, "offre", "accepted", "2026-09-01", "A1"), (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] == c[110], f"le compromis rejoint le dossier de l'offre (les deux en {c[110]})")
ok(c[110] == 101, "le dossier porte le numero de l'offre (le plus petit), comme la regle le dit")

print("Meme jour")
c = chaines([(101, "offre", "accepted", "2026-10-12", "A1"), (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] == c[110], "offre et compromis le meme jour : rattaches (l'offre est rangee d'abord)")

print("TEMOIN INVERSE — l'offre datee APRES le compromis, acceptee")
c = chaines([(101, "offre", "accepted", "2026-10-20", "A1"), (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] != c[110], "elle ne l'attire pas : c'est pourquoi l'ecran exige la date")

print("Deja relie par le § 2.8 (meme acquereur), l'offre restee « proposee »")
c = chaines([(101, "offre", "proposed", "2026-09-01", "A1"), (110, "compromis", "active", "2026-10-12", "A1")])
ok(c[101] == c[110] if al.chainage_offre_proposee_actif() else True,
   "meme acquereur : deja dans le meme dossier (aucune regularisation necessaire)")

print("TOUT VERT" if not echecs else f"⛔ {echecs} controle(s) en echec")
sys.exit(1 if echecs else 0)
