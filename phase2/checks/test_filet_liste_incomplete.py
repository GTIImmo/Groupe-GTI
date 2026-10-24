#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE FILET DES LISTES INCOMPLETES ET LE TRI DES COMPROMIS.   24/10/2026

Audit : notice/AUDIT_ALERTES_MONITORING_2026-10-24.md §2 ter.

CE QU'IL EPROUVE
----------------
  ⓵ LE FILET sur une liste FABRIQUEE qui reproduit le defaut prouve chez Hektor : page 0 = page 1,
     deux compromis du meme bien (7) a cheval sur deux pages -> D1 lu deux fois, D2 jamais ; et un
     FANTOME de mars (F) qu'il faut continuer a retirer. Six cas :
        complete (temoin inverse) · sautes expliques · journal seul · inexplique · deux nuits · sans total
  ⓶ LE TRI : configure_generic_resources rend dateStart interrupteur eteint, id/DESC allume.
  ⓷ (option --nuit-reelle) LE REJEU DE LA DERNIERE NUIT : les listes brutes de data/hektor.sqlite
     (ouvert en LECTURE SEULE) sont recopiees dans une base temporaire, on y reconstruit un miroir
     (liste fraiche + instantane, comme l'upsert) et on joue le VRAI aligner_miroir_sur_hektor, filet
     allume. On rend, par type, ce qui aurait ete garde et retire.

⚠ IL N'ECRIT RIEN DE VRAI : bases en memoire ou dans un dossier temporaire efface a la fin.
   0 appel chez Hektor.

    python -I phase2/checks/test_filet_liste_incomplete.py [--nuit-reelle]
    sortie 0 = vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import normalize_source as ns  # noqa: E402
import sync_raw  # noqa: E402

ECHECS: list[str] = []


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK   ' if ok else 'ECHEC'} {nom}{' -- ' + detail if detail else ''}")
    if not ok:
        ECHECS.append(nom)


def base_fabriquee(pages: list[tuple[int, int, list[tuple[str, str]]]], total: int | None,
                   miroir: list[tuple[str, str]]) -> sqlite3.Connection:
    """pages : (run_id, page, [(id, annonce)]) ; miroir : [(id, annonce)]."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE raw_api_response (id INTEGER PRIMARY KEY, run_id INTEGER,
                    endpoint_name TEXT, object_type TEXT, object_id_key TEXT, page INTEGER,
                    page_key TEXT, payload_json TEXT)""")
    conn.execute("CREATE TABLE hektor_compromis (hektor_compromis_id TEXT, hektor_annonce_id TEXT)")
    for run_id, page, items in pages:
        payload = {"data": [{"id": i, "annonce": {"id": a}} for i, a in items],
                   "metadata": {"total": total} if total is not None else {}}
        conn.execute("""INSERT INTO raw_api_response (run_id, endpoint_name, object_type, object_id_key,
                        page, page_key, payload_json) VALUES (?, 'list_compromis_update', 'compromis', '',
                        ?, ?, ?)""", (run_id, page, str(page), json.dumps(payload)))
    conn.executemany("INSERT INTO hektor_compromis VALUES (?, ?)", miroir)
    return conn


def jouer(conn: sqlite3.Connection, actif: bool) -> tuple[set[str], str]:
    os.environ["APP_MIROIR_FILET_LISTE"] = "1" if actif else "0"
    sortie = io.StringIO()
    with contextlib.redirect_stdout(sortie):
        ns.aligner_miroir_sur_hektor(conn, table="hektor_compromis", id_col="hektor_compromis_id",
                                     endpoint_frais="list_compromis_update", libelle="compromis",
                                     genre="compromis")
    restants = {r[0] for r in conn.execute("SELECT hektor_compromis_id FROM hektor_compromis")}
    return restants, sortie.getvalue()


# La liste qui saute D2 : page 0 = page 1, D1 (bien 7) en fin de page 2 ET en debut de page 3.
SAUTANTE = [(9, 0, [("A", "10"), ("B", "9")]), (9, 1, [("A", "10"), ("B", "9")]),
            (9, 2, [("C", "8"), ("D1", "7")]), (9, 3, [("D1", "7"), ("E", "6")])]
COMPLETE = [(9, 0, [("A", "10"), ("B", "9")]), (9, 1, [("A", "10"), ("B", "9")]),
            (9, 2, [("C", "8"), ("D1", "7")]), (9, 3, [("D2", "7"), ("E", "6")])]
# Le miroir : tout ce que Hektor porte (D2 compris) + F, fantome de mars VRAIMENT supprime.
MIROIR = [("A", "10"), ("B", "9"), ("C", "8"), ("D1", "7"), ("D2", "7"), ("E", "6"), ("F", "5")]


def etape_filet() -> None:
    print("⓵ le filet, sur une liste fabriquee")
    restants, sortie = jouer(base_fabriquee(COMPLETE, 6, MIROIR), actif=True)
    controle("complete : F (fantome) retire, rien d'autre", restants == {"A", "B", "C", "D1", "D2", "E"},
             str(sorted(restants)))
    controle("complete : verdict COMPLETE", "-> COMPLETE" in sortie)

    restants, sortie = jouer(base_fabriquee(SAUTANTE, 6, MIROIR), actif=True)
    controle("sautante, filet ALLUME : D2 garde, F retire", restants == {"A", "B", "C", "D1", "D2", "E"},
             str(sorted(restants)))
    controle("sautante : verdict SAUTES EXPLIQUES", "-> SAUTES EXPLIQUES" in sortie)

    restants, sortie = jouer(base_fabriquee(SAUTANTE, 6, MIROIR), actif=False)
    controle("sautante, JOURNAL SEUL : comportement d'avant (D2 ET F retires)",
             restants == {"A", "B", "C", "D1", "E"}, str(sorted(restants)))
    controle("journal seul : la ligne dit ce qu'il AURAIT garde (D2)",
             "(JOURNAL SEUL)" in sortie and "AURAIT garde 1 : D2" in sortie, sortie.strip()[-160:])

    restants, sortie = jouer(base_fabriquee(SAUTANTE, 7, MIROIR), actif=True)
    controle("inexplique (total 7) : TOUT garde", restants == {r[0] for r in MIROIR}, str(sorted(restants)))
    controle("inexplique : verdict REFUS", "-> REFUS (1 manquant(s) inexplique(s))" in sortie)

    deux_nuits = COMPLETE + [(8, 4, [("Z", "1")])]
    restants, sortie = jouer(base_fabriquee(deux_nuits, 6, MIROIR + [("Z", "1")]), actif=True)
    controle("deux nuits melangees : TOUT garde", restants == {r[0] for r in MIROIR} | {"Z"},
             str(sorted(restants)))
    controle("deux nuits : verdict REFUS", "-> REFUS (liste melangeant deux nuits" in sortie)

    restants, sortie = jouer(base_fabriquee(SAUTANTE, None, MIROIR), actif=True)
    controle("sans total : comportement d'avant", restants == {"A", "B", "C", "D1", "E"}, str(sorted(restants)))
    controle("sans total : verdict SANS TOTAL", "-> SANS TOTAL" in sortie)


def etape_tri() -> None:
    print("⓶ le tri des compromis")
    args = argparse.Namespace(with_offer_status=False, with_compromis_status=False, mandat_date_start=None,
                              mandat_date_end=None, vente_date_start="2000-01-01", vente_date_end="2030-12-31",
                              mode="update", vente_lookback_months=12)
    os.environ.pop("APP_COMPROMIS_TRI_ID", None)
    p = sync_raw.configure_generic_resources(args, bootstrap=False)["compromis"]["extra_params"]
    controle("eteint : dateStart / DESC (comme avant)", (p.get("sort"), p.get("way")) == ("dateStart", "DESC"),
             str(p))
    os.environ["APP_COMPROMIS_TRI_ID"] = "1"
    p = sync_raw.configure_generic_resources(args, bootstrap=False)["compromis"]["extra_params"]
    controle("allume : id / DESC", (p.get("sort"), p.get("way")) == ("id", "DESC"), str(p))
    controle("allume : withCompromisStatus garde a false", p.get("withCompromisStatus") == "false", str(p))
    o = sync_raw.configure_generic_resources(args, bootstrap=False)["offres"]["extra_params"]
    controle("allume : les offres ne bougent pas", (o.get("sort"), o.get("way")) == ("date", "DESC"), str(o))
    os.environ.pop("APP_COMPROMIS_TRI_ID", None)


TYPES = (("compromis", "hektor_compromis", "hektor_compromis_id", "list_compromis_update", "list_compromis"),
         ("ventes", "hektor_vente", "hektor_vente_id", "list_ventes_update", "list_ventes"),
         ("offres", "hektor_offre", "hektor_offre_id", "list_offres_update", "list_offres"))


def etape_nuit_reelle() -> int:
    print("⓷ le rejeu de la derniere nuit (data/hektor.sqlite en lecture seule)")
    source = ROOT / "data" / "hektor.sqlite"
    if not source.exists():
        print("  pas de miroir local -- impossible de mesurer")
        return 2
    dossier = Path(tempfile.mkdtemp(prefix="filet_"))
    try:
        src = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True, timeout=30)
        conn = sqlite3.connect(str(dossier / "essai.sqlite"))
        conn.row_factory = sqlite3.Row
        conn.execute("""CREATE TABLE raw_api_response (id INTEGER PRIMARY KEY, run_id INTEGER,
                        endpoint_name TEXT, object_type TEXT, object_id_key TEXT, page INTEGER,
                        page_key TEXT, payload_json TEXT)""")
        for _, table, id_col, frais, instantane in TYPES:
            for ep in (frais, instantane):
                for row in src.execute("""SELECT id, run_id, endpoint_name, object_type, object_id_key, page,
                                          page_key, payload_json FROM raw_api_response WHERE endpoint_name = ?""",
                                       (ep,)):
                    conn.execute("INSERT INTO raw_api_response VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tuple(row))
            conn.execute(f"CREATE TABLE {table} ({id_col} TEXT PRIMARY KEY, hektor_annonce_id TEXT)")
            # Le miroir tel que l'upsert le reconstruit chaque nuit : liste fraiche + instantane.
            for item in ns.iter_listing_items(ns.fetch_latest_raw_payloads(conn, frais)):
                a = item.get("annonce") if isinstance(item.get("annonce"), dict) else {}
                conn.execute(f"INSERT OR IGNORE INTO {table} VALUES (?, ?)",
                             (str(item.get("id")), str(a.get("id") or item.get("id_annonce") or "")))
            for item in ns.iter_listing_items(ns.fetch_latest_raw_payloads(conn, instantane)):
                a = item.get("annonce") if isinstance(item.get("annonce"), dict) else {}
                conn.execute(f"INSERT OR IGNORE INTO {table} VALUES (?, ?)",
                             (str(item.get("id")), str(a.get("id") or item.get("id_annonce") or "")))
        src.close()
        os.environ["APP_MIROIR_FILET_LISTE"] = "1"
        for libelle, table, id_col, frais, _ in TYPES:
            avant = {r[0] for r in conn.execute(f"SELECT {id_col} FROM {table}")}
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie):
                ns.aligner_miroir_sur_hektor(conn, table=table, id_col=id_col, endpoint_frais=frais,
                                             libelle=libelle, genre=None)
            apres = {r[0] for r in conn.execute(f"SELECT {id_col} FROM {table}")}
            for ligne in sortie.getvalue().strip().splitlines():
                print("   ", ligne)
            print(f"    -> {libelle} : {len(avant - apres)} retire(s)")
        conn.close()
        return 0
    finally:
        os.environ.pop("APP_MIROIR_FILET_LISTE", None)
        shutil.rmtree(dossier, ignore_errors=True)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--nuit-reelle", action="store_true")
    args = ap.parse_args()
    try:
        etape_filet()
        etape_tri()
        code_reel = etape_nuit_reelle() if args.nuit_reelle else 0
    finally:
        os.environ.pop("APP_MIROIR_FILET_LISTE", None)
        os.environ.pop("APP_COMPROMIS_TRI_ID", None)
    if ECHECS:
        print(f"ECHEC : {len(ECHECS)} controle(s) -- {', '.join(ECHECS)}")
        return 1
    if code_reel == 2:
        return 2
    print("VERT : tous les controles passent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
