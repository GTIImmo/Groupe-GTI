#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4-b — LE SERVEUR ADOPTE LE NUMERO QUE L'APP A DONNE.        21/09/2026

LA REGLE DU PLAN, mot pour mot : « le serveur remplit LES DEUX CASES ».

    l'objet arrive avec un numero d'app   ->  ON L'ADOPTE
    l'objet arrive sans                   ->  le compteur du serveur en fabrique un

CE QU'IL SE PASSERAIT SANS CE GESTE. Le serveur inscrit une annonce avec
`INSERT INTO app_dossier (hektor_annonce_id, ...)` et laisse son compteur choisir
l'identifiant. Une annonce nee dans l'app porterait donc DEUX numeros : celui que
l'app lui a donne (10 000 001) et celui que le serveur aurait fabrique
(7 589 099). Tout ce qui pend dessous se couperait en deux -- et rien ne le
signalerait, puisque les deux lignes seraient parfaitement valides.

⚠ FREDERIC, 21/09 : « donc avec le A le serveur ne genere plus puisque les
  annonces arrivent avec un numero ? » -- PRESQUE, et la nuance commande ce
  script : pendant toute la migration LES DEUX CAS COEXISTENT. Ce qui vient de
  Hektor n'a pas de numero d'app et le serveur le fabrique, comme aujourd'hui.
  Ce qui nait dans l'app en a un, et il faut l'adopter. Les deux compteurs
  tournent en meme temps -- d'ou les plages qui ne se croisent pas (L4-a).

CE QU'IL ADOPTE : l'IDENTITE seulement -- le numero et sa case Hektor vide. Pas
le contenu : celui-la se decide champ par champ, et ce n'est pas ce lot.

IL LIT LES RECENSEMENTS, pas Supabase : app_annonce_app_seule (26/08),
app_contact_app_seul et app_recherche_app_seule (21/09). Ce sont eux qui savent
deja ce que l'app detient et que le miroir ignore.

⚠ LES RELATIONS N'ONT RIEN A ADOPTER : leur cle n'est pas un numero tire d'un
  compteur, c'est une EMPREINTE calculee sur ce qu'elles relient (Frederic,
  21/09 : « il n'y a pas besoin de distributeur pour le registre des
  relations »). Ce qu'il leur faut, c'est que l'empreinte soit calculee sur les
  numeros de l'app -- pas une adoption.

AUJOURD'HUI : ZERO ligne dans les trois recensements. Ce script est INERTE, et
c'est voulu : il est pose AVANT que la creation app-first existe, pas apres.

IDEMPOTENT : rejouer n'ecrit rien et affiche 0.
RETOUR ARRIERE : les lignes adoptees portent un numero >= a la plage de l'app,
donc elles se retirent par un DELETE cible sur cette plage.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"

# Les plages reservees a l'app (L4-a). Une valeur en dessous serait un numero
# venu de Hektor : on ne l'adopte pas, ce serait ecraser une identite existante.
PLAGE_ANNONCE = 10000000
PLAGE_CONTACT = 10000000
PLAGE_RECHERCHE = 1000000


def connecte() -> sqlite3.Connection:
    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nom,)).fetchone() is not None


def adopter_annonces(conn, dry: bool) -> int:
    if not table_existe(conn, "app_annonce_app_seule"):
        return 0
    lignes = conn.execute(
        "SELECT app_dossier_id, hektor_annonce_id FROM app_annonce_app_seule "
        "WHERE app_dossier_id >= ?", (PLAGE_ANNONCE,)).fetchall()
    n = 0
    for app_id, hektor_id in lignes:
        if conn.execute("SELECT 1 FROM app_dossier WHERE id = ?", (app_id,)).fetchone():
            continue
        if dry:
            n += 1
            continue
        conn.execute(
            "INSERT INTO app_dossier (id, hektor_annonce_id) VALUES (?, ?)",
            (int(app_id), hektor_id or None))
        n += 1
    return n


def adopter_contacts(conn, dry: bool) -> int:
    if not table_existe(conn, "app_contact_app_seul"):
        return 0
    lignes = conn.execute(
        "SELECT hektor_contact_id, app_contact_id, donnees_json FROM app_contact_app_seul").fetchall()
    n = 0
    for identite, app_id, brut in lignes:
        # L'identite d'un contact ne dans l'app EST son numero (option B du 21/09).
        try:
            numero = int(app_id) if app_id else int(str(identite))
        except (TypeError, ValueError):
            continue
        if numero < PLAGE_CONTACT:
            continue
        if conn.execute("SELECT 1 FROM app_contact WHERE app_contact_id = ?", (numero,)).fetchone():
            continue
        if dry:
            n += 1
            continue
        # hektor_contact_id reste VIDE : Hektor ne connait pas encore ce contact.
        conn.execute(
            "INSERT INTO app_contact (app_contact_id, hektor_contact_id) VALUES (?, NULL)", (numero,))
        n += 1
    return n


def adopter_recherches(conn, dry: bool) -> int:
    if not table_existe(conn, "app_recherche_app_seule"):
        return 0
    lignes = conn.execute(
        "SELECT contact_search_key, hektor_contact_id, app_contact_id, donnees_json "
        "FROM app_recherche_app_seule").fetchall()
    n = 0
    for cle, hektor_contact, app_contact, brut in lignes:
        try:
            donnees = json.loads(brut) if brut else {}
        except json.JSONDecodeError:
            donnees = {}
        numero = donnees.get("app_search_id")
        index = donnees.get("search_index")
        if numero is None or int(numero) < PLAGE_RECHERCHE:
            continue
        if conn.execute("SELECT 1 FROM app_search_registry WHERE app_search_id = ?", (int(numero),)).fetchone():
            continue
        if dry:
            n += 1
            continue
        conn.execute(
            "INSERT INTO app_search_registry (app_search_id, hektor_contact_id, app_contact_id, "
            "search_index, contact_search_key) VALUES (?, ?, ?, ?, ?)",
            (int(numero), hektor_contact or None, app_contact, int(index or 0), cle))
        n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description="Le serveur adopte les numeros attribues par l'app.")
    parser.add_argument("--dry-run", action="store_true", help="Compter sans ecrire.")
    args = parser.parse_args()

    conn = connecte()
    try:
        a = adopter_annonces(conn, args.dry_run)
        c = adopter_contacts(conn, args.dry_run)
        r = adopter_recherches(conn, args.dry_run)
        if not args.dry_run:
            conn.commit()
    finally:
        conn.close()

    suffixe = " (dry-run)" if args.dry_run else ""
    print(f"[adoption] annonces={a} contacts={c} recherches={r}{suffixe}")
    if a == c == r == 0:
        print("[adoption] rien a adopter : aucun objet n'est encore ne dans l'app.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
