# -*- coding: utf-8 -*-
"""Rafraichit les 4 tables passerelle depuis le brut `list_broadcasts` deja en base.

POURQUOI CE SCRIPT PLUTOT QUE `python normalize_source.py`
    normalize_source n'a qu'un seul interrupteur (--contact-id) : le lancer
    renormaliserait TOUT le miroir (agences, negos, annonces, details, mandats,
    contacts, offres, compromis, ventes), en pleine journee, pour reparer quatre
    tables. On appelle donc LES MEMES FONCTIONS, et elles seules.

    ⚠ Aucun appel reseau : on relit le brut DEJA descendu par le run de nuit.
      Rien n'est demande a Hektor.

CE QUE CA REPARE (mesure du 30/09/2026)
    Le deballeur rendait ZERO passerelle depuis le 07/07 -- Hektor avait change la
    forme de sa reponse (`data` liste -> `{"platforms": [...]}`) et le code se
    taisait. Les quatre tables etaient figees au 7 juillet, et la lecture a la
    volee RECOPIAIT ce contenu de juillet en y tamponnant la date du jour : aucun
    controle de fraicheur ne pouvait le voir.

USAGE
    python phase2/sync/rafraichir_passerelles.py --a-blanc   # mesure, annule tout
    python phase2/sync/rafraichir_passerelles.py             # ecrit

RETOUR ARRIERE
    Le contenu efface est REFABRICABLE : il vient du brut `raw_api_response`, qui
    n'est jamais purge. Relancer ce script rend exactement le meme etat.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import normalize_source as ns  # noqa: E402
from hektor_pipeline.common import Settings, connect_db  # noqa: E402

TABLES = (
    "hektor_broadcast",
    "hektor_broadcast_portal",
    "hektor_broadcast_listing",
    "hektor_annonce_broadcast_state",
)


class ConnexionSansCommit:
    """Enveloppe qui NEUTRALISE `commit()`.

    ⚠ Sans elle, `--a-blanc` ne prouverait rien : les quatre fonctions de
    normalize_source appellent `conn.commit()` chacune a leur fin, et le ROLLBACK
    final n'aurait plus rien a annuler. On les laisse ecrire dans la transaction,
    et c'est NOUS qui decidons de valider ou d'annuler.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def commit(self) -> None:  # volontairement sans effet
        return None

    def __getattr__(self, nom: str):
        return getattr(self._conn, nom)


def etat(conn) -> dict:
    out = {}
    for table in TABLES:
        out[table] = conn.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]
    out["annonces"] = conn.execute(
        "SELECT COUNT(DISTINCT hektor_annonce_id) FROM hektor_annonce_broadcast_state"
    ).fetchone()[0]
    out["perimees"] = conn.execute(
        "SELECT COUNT(*) FROM hektor_broadcast_listing WHERE substr(synced_at,1,10) < date('now')"
    ).fetchone()[0]
    return out


def affiche(titre: str, valeurs: dict, reference: dict | None = None) -> None:
    print("  %s" % titre)
    for cle, valeur in valeurs.items():
        if reference is None:
            print("      %-34s %6s" % (cle, valeur))
        else:
            print("      %-34s %6s   (%+d)" % (cle, valeur, valeur - reference[cle]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a-blanc", action="store_true",
                        help="Joue tout puis ANNULE : rien n'est ecrit.")
    args = parser.parse_args()

    settings = Settings.from_env()
    conn = connect_db(settings.db_path)
    print("  base : %s" % settings.db_path)
    conn.row_factory = sqlite3.Row

    print("=" * 74)
    print("RAFRAICHISSEMENT DES PASSERELLES%s" % ("  --  A BLANC" if args.a_blanc else ""))
    print("=" * 74)

    avant = etat(conn)
    affiche("[AVANT]", avant)

    muet = ConnexionSansCommit(conn)
    depart = time.time()
    conn.execute("BEGIN")
    try:
        ns.upsert_broadcasts(muet)
        ns.upsert_broadcast_portals(muet)
        ns.upsert_broadcast_listings(muet)
        ns.upsert_broadcast_states(muet)
        apres = etat(conn)
        duree = time.time() - depart
        print()
        affiche("[APRES]", apres, avant)
        print()
        print("  duree du verrou : %.2f s" % duree)

        if args.a_blanc:
            conn.execute("ROLLBACK")
            print("  -> A BLANC : tout est annule, la base n'a pas bouge.")
        else:
            conn.commit()
            print("  -> ECRIT.")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
