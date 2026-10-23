#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑧ défaut 6 — RENDRE LEUR NUMÉRO AUX 3 CONTACTS NÉS DANS L'APP.          23/10/2026

Avant l'adoption (registre_contacts.py, 23/10), le registre local a donné un SECOND numéro
aux trois contacts d'essai nés dans l'app, et jeté leur numéro de Hektor :

    10650777  '20000007'  cible vide      ->  20000007  '20000007'  605925
    10650807  '20000008'  cible vide      ->  20000008  '20000008'  605946
    10650808  '20000009'  cible vide      ->  20000009  '20000009'  605947

et la recherche 77235 (contact 20000008) porte 10650807 -> 20000008.

POURQUOI UN GESTE EXPRÈS : le registre ne répare jamais une identité de lui-même (« un
numéro ne se perd jamais » : changer un numéro est une décision). Mesuré le 23/10 : les
numéros 10650777 / 10650807 / 10650808 ne sont utilisés NULLE PART ailleurs (ni en local, ni
chez Supabase), sauf 10650777 recopié sur 20000007 chez Supabase par pousser_numeros_contact
le 22/10 -- la nuit suivant la réparation, ce même script y renverra 20000007.

CE QU'IL VÉRIFIE AVANT D'ÉCRIRE, ligne par ligne (sinon ARRÊT, rien n'est écrit) :
    la ligne parasite existe telle quelle · le vrai numéro est libre · la cible n'est portée
    par aucune autre ligne · la couche porte bien cette identité avec cette cible.
SAUVEGARDE DATÉE avant d'écrire : app_contact_avant_reparation_20261023 et
    app_search_registry_avant_reparation_20261023 (les seules lignes touchées).
RETOUR ARRIÈRE : --inverse (repose les lignes de la sauvegarde).

    python -I phase2/identite/reparer_contacts_nes_dans_app_2026-10-23.py            -> mesure seule
    python -I phase2/identite/reparer_contacts_nes_dans_app_2026-10-23.py --ecrire   -> répare
    python -I ... --inverse                                                           -> défait
    --base <chemin> : une autre base (répétition sur copie)
    sortie 0 = fait ou rien à faire · 3 = une vérification refuse · 2 = base illisible
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parents[2] / "phase2" / "phase2.sqlite"
SAUVE_CONTACT = "app_contact_avant_reparation_20261023"
SAUVE_RECHERCHE = "app_search_registry_avant_reparation_20261023"
LIGNES = [  # (numéro parasite, identité, numéro de Hektor)
    (10650777, 20000007, "605925"),
    (10650807, 20000008, "605946"),
    (10650808, 20000009, "605947"),
]


def existe(conn, nom):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nom,)).fetchone() is not None


def verifier(conn) -> tuple[list, list[str]]:
    a_faire, refus = [], []
    for parasite, ident, cible in LIGNES:
        deja = conn.execute("SELECT app_contact_id, hektor_contact_id, hektor_target_id FROM app_contact "
                            "WHERE app_contact_id = ?", (ident,)).fetchone()
        if deja == (ident, str(ident), cible):
            print(f"  {ident} : déjà réparé")
            continue
        ligne = conn.execute("SELECT app_contact_id, hektor_contact_id, hektor_target_id FROM app_contact "
                             "WHERE app_contact_id = ?", (parasite,)).fetchone()
        if ligne != (parasite, str(ident), None):
            refus.append(f"{ident} : la ligne parasite n'est pas celle mesurée ({ligne})")
            continue
        if deja is not None:
            refus.append(f"{ident} : le numéro {ident} est déjà pris par {deja}")
            continue
        autre = conn.execute("SELECT app_contact_id FROM app_contact WHERE hektor_target_id = ?", (cible,)).fetchone()
        if autre is not None:
            refus.append(f"{ident} : la cible {cible} est déjà portée par {autre[0]}")
            continue
        couche = conn.execute("SELECT hektor_target_id FROM app_contact_current WHERE hektor_contact_id = ?",
                              (str(ident),)).fetchone()
        if couche is None or couche[0] != cible:
            refus.append(f"{ident} : la couche ne porte pas {ident} / {cible} ({couche})")
            continue
        a_faire.append((parasite, ident, cible))
        print(f"  {ident} : {parasite} -> {ident}, cible {cible}")
    return a_faire, refus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ecrire", action="store_true")
    ap.add_argument("--inverse", action="store_true")
    ap.add_argument("--base", type=Path, default=BASE)
    args = ap.parse_args()
    try:
        conn = sqlite3.connect(str(args.base), timeout=60)
        conn.execute("PRAGMA busy_timeout = 30000")
    except sqlite3.Error as e:
        print(f"base illisible : {e}")
        return 2
    try:
        if args.inverse:
            if not existe(conn, SAUVE_CONTACT):
                print("rien à défaire : pas de sauvegarde.")
                return 0
            for parasite, ident, cible in LIGNES:
                conn.execute("DELETE FROM app_contact WHERE app_contact_id = ? AND hektor_contact_id = ?",
                             (ident, str(ident)))
            conn.execute(f"INSERT INTO app_contact SELECT * FROM {SAUVE_CONTACT}")
            if existe(conn, SAUVE_RECHERCHE):
                for (sid, cid) in conn.execute(f"SELECT app_search_id, app_contact_id FROM {SAUVE_RECHERCHE}").fetchall():
                    conn.execute("UPDATE app_search_registry SET app_contact_id = ? WHERE app_search_id = ?", (cid, sid))
            conn.commit()
            print("défait : les lignes de la sauvegarde sont reposées.")
            return 0

        print("mesure :")
        a_faire, refus = verifier(conn)
        rech = conn.execute("SELECT app_search_id, app_contact_id FROM app_search_registry "
                            "WHERE app_contact_id IN (%s)" % ",".join("?" * len(LIGNES)),
                            [p for p, _, _ in LIGNES]).fetchall()
        print(f"  recherches au numéro parasite : {rech}")
        if refus:
            print("REFUS -- rien n'est écrit :")
            for r in refus:
                print("   ", r)
            return 3
        if not a_faire and not rech:
            print("rien à faire.")
            return 0
        if not args.ecrire:
            print("\nmesure seule : relancer avec --ecrire pour réparer.")
            return 0

        parasites = [p for p, _, _ in a_faire]
        trous = ",".join("?" * len(parasites))
        if not existe(conn, SAUVE_CONTACT):
            conn.execute(f"CREATE TABLE {SAUVE_CONTACT} AS SELECT * FROM app_contact WHERE app_contact_id IN ({trous})", parasites)
        if not existe(conn, SAUVE_RECHERCHE):
            conn.execute(f"CREATE TABLE {SAUVE_RECHERCHE} AS SELECT * FROM app_search_registry "
                         f"WHERE app_contact_id IN ({','.join('?' * len(LIGNES))})", [p for p, _, _ in LIGNES])
        for parasite, ident, cible in a_faire:
            conn.execute("UPDATE app_contact SET app_contact_id = ?, hektor_target_id = ?, "
                         "updated_at = CURRENT_TIMESTAMP WHERE app_contact_id = ? AND hektor_contact_id = ?",
                         (ident, cible, parasite, str(ident)))
        for parasite, ident, _ in LIGNES:
            conn.execute("UPDATE app_search_registry SET app_contact_id = ? WHERE app_contact_id = ?", (ident, parasite))
        # Contrôle avant d'enregistrer : plus aucun contact né dans l'app à deux numéros.
        reste = conn.execute("SELECT count(*) FROM app_contact WHERE CAST(hektor_contact_id AS INTEGER) >= 20000000 "
                             "AND app_contact_id <> CAST(hektor_contact_id AS INTEGER)").fetchone()[0]
        if reste:
            conn.rollback()
            print(f"ARRÊT : il resterait {reste} contact(s) à deux numéros. Rien n'est écrit.")
            return 3
        conn.commit()
        print(f"\nréparé : {len(a_faire)} contact(s), recherches recâblées. Sauvegarde : {SAUVE_CONTACT}, {SAUVE_RECHERCHE}.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
