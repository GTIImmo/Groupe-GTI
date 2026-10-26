# -*- coding: utf-8 -*-
"""Essai du chantier 2 -- c (⑧ types, 26/10/2026) sur une COPIE de phase2.sqlite :
la nuit pose NOTRE numero de mandat (`app_mandat_id`) sur chaque transaction, par la cle
« bien + numero de mandat » du registre des mandats.

    python phase2/checks/test_mandat_notre_numero_sur_copie.py --base <copie.sqlite>

⛔ JAMAIS sur phase2/phase2.sqlite (le script joue la nuit et ECRIT dans la base donnee).
   data/hektor.sqlite en LECTURE SEULE ; aucun push, aucun appel a Hektor.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync import affaire_ledger as A  # noqa: E402

ECHECS: list[str] = []


def ok(cond: bool, nom: str) -> None:
    print(("  ok   " if cond else "  ECHEC ") + nom)
    if not cond:
        ECHECS.append(nom)


def interrupteur(allume: bool) -> None:
    os.environ["APP_AFFAIRE_MANDAT_NOTRE_NUMERO"] = "1" if allume else "0"


def la_regle_du_upsert() -> None:
    """Le CASE de l'UPSERT, joue a part (base en memoire) : trouve / meme numero / numero change."""
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE L (k TEXT PRIMARY KEY, numero_mandat TEXT, app_mandat_id INTEGER)")
    c.execute("INSERT INTO L VALUES ('a', '100', 7), ('b', '100', 7), ('c', '100', 7)")
    sql = ("INSERT INTO L VALUES (?, ?, ?) ON CONFLICT(k) DO UPDATE SET "
           "app_mandat_id = CASE WHEN excluded.app_mandat_id IS NOT NULL THEN excluded.app_mandat_id "
           "WHEN excluded.numero_mandat IS L.numero_mandat THEN L.app_mandat_id ELSE NULL END, "
           "numero_mandat = excluded.numero_mandat")
    c.execute(sql, ("a", "100", 9))
    c.execute(sql, ("b", "100", None))
    c.execute(sql, ("c", "200", None))
    v = dict(c.execute("SELECT k, app_mandat_id FROM L"))
    ok(v == {"a": 9, "b": 7, "c": None}, f"retrouve -> pose ; meme numero -> garde ; numero change -> vide ({v})")
    src = Path(A.__file__).read_text(encoding="utf-8")
    ok("WHEN excluded.numero_mandat IS {LEDGER_TABLE}.numero_mandat THEN {LEDGER_TABLE}.app_mandat_id" in src,
       "c'est bien cette regle que porte affaire_ledger.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    args = ap.parse_args()
    base = Path(args.base).resolve()
    if base == (ROOT / "phase2" / "phase2.sqlite").resolve():
        print("REFUS : c'est la base de production. Donner une COPIE.")
        return 2

    print("0. la regle de l'UPSERT")
    la_regle_du_upsert()

    con = sqlite3.connect(f"file:{base}", uri=True, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("ATTACH DATABASE ? AS hektor", (f"file:{A.HEKTOR_DB}?mode=ro",))
    A._ENV_DEJA_CHARGE = True
    os.environ["APP_AFFAIRE_PERSONNES_DEUX_NUMEROS"] = "1"
    os.environ["APP_AFFAIRE_VENDEURS_DEUX_NUMEROS"] = "1"

    print("1. la nuit, interrupteur ETEINT")
    interrupteur(False)
    A.refresh_ledger(con, full=True)
    n = con.execute("SELECT COUNT(*) FROM app_affaire_ledger WHERE app_mandat_id IS NOT NULL").fetchone()[0]
    ok(n == 0, f"aucune transaction ne porte app_mandat_id ({n})")
    ok(all("app_mandat_id" not in d for d in A.ledger_rows_for_push(con)[:2000]),
       "le push n'envoie PAS la colonne (Supabase ne l'a peut-etre pas encore)")

    print("2. la nuit, interrupteur ALLUME")
    interrupteur(True)
    A.refresh_ledger(con, full=True)
    vivantes = con.execute("SELECT COUNT(*) FROM app_affaire_ledger WHERE present_in_hektor = 1"
                           " AND NULLIF(TRIM(numero_mandat), '') IS NOT NULL").fetchone()[0]
    poses = con.execute("SELECT COUNT(*) FROM app_affaire_ledger WHERE present_in_hektor = 1"
                        " AND app_mandat_id IS NOT NULL").fetchone()[0]
    ok(poses == vivantes and poses > 20_000, f"transactions vivantes a numero rattachees : {poses} sur {vivantes} (~23 336)")
    faux = con.execute(
        "SELECT COUNT(*) FROM app_affaire_ledger l JOIN app_mandat m ON m.app_mandat_id = l.app_mandat_id"
        " WHERE CAST(m.hektor_annonce_id AS TEXT) <> CAST(l.hektor_annonce_id AS TEXT)"
        "    OR m.numero_mandat <> l.numero_mandat").fetchone()[0]
    ok(faux == 0, f"chaque app_mandat_id designe le mandat de la MEME cle bien + numero ({faux} faux)")
    sans = con.execute("SELECT COUNT(*) FROM app_affaire_ledger WHERE NULLIF(TRIM(numero_mandat), '') IS NULL"
                       " AND app_mandat_id IS NOT NULL").fetchone()[0]
    ok(sans == 0, f"une transaction sans numero ne recoit rien ({sans})")
    lignes = A.ledger_rows_for_push(con)
    ok(any(d.get("app_mandat_id") for d in lignes), "le push envoie la colonne, interrupteur allume")

    print("3. un mandat qui manque au registre (il arrivera la nuit d'apres) : on garde, on n'efface pas")
    cible = con.execute("SELECT l.app_mandat_id, l.hektor_annonce_id, l.numero_mandat FROM app_affaire_ledger l"
                        " WHERE l.app_mandat_id IS NOT NULL LIMIT 1").fetchone()
    con.execute("UPDATE app_mandat SET numero_mandat = numero_mandat || '_cache' WHERE app_mandat_id = ?", (cible[0],))
    A.refresh_ledger(con, full=True)
    garde = con.execute("SELECT app_mandat_id FROM app_affaire_ledger WHERE hektor_annonce_id = ? AND numero_mandat = ?"
                        " LIMIT 1", (cible[1], cible[2])).fetchone()[0]
    ok(garde == cible[0], f"meme numero, mandat introuvable ce soir : le numero d'hier est garde ({garde})")
    con.execute("UPDATE app_mandat SET numero_mandat = REPLACE(numero_mandat, '_cache', '') WHERE app_mandat_id = ?", (cible[0],))

    con.rollback()
    con.close()
    print()
    print("ECHECS :", len(ECHECS))
    return 1 if ECHECS else 0


if __name__ == "__main__":
    raise SystemExit(main())
