#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4-c ⓪ — LA DOUBLURE MONTE DANS LA PLAGE DE L'APP.            22/09/2026

LE PROBLEME, MESURE LE 22/09. Les deux series de numeros de contact se
recouvrent :

    numeros de Hektor        1  ->  605 461
    doublure app_contact_id  3  ->  356 136      <- entierement dedans

    NUMEROS PRESENTS DANS LES DEUX SERIES      194 687
       dont les deux numeros du MEME contact         4
       donc AMBIGUS : un numero, DEUX contacts  194 683

Un numero tout seul ne dit pas d'ou il vient. Rien n'est casse aujourd'hui --
chaque lecteur NOMME sa colonne, et `app_contact_id` n'apparait ni dans le
worker ni dans le front. Mais la bascule (L4-c) consiste justement a faire lire
l'autre colonne a des centaines d'endroits : UN SEUL lecteur tolerant rendrait
la mauvaise fiche 194 683 fois, sans erreur et sans trace.

⚠ J'ETAIS A UNE LIGNE DE L'ECRIRE, ce lecteur tolerant, le 22/09 au matin.
  C'est une mesure faite avant de coder qui l'a arrete. La discipline (« chaque
  lecteur nomme sa colonne ») nous protege aujourd'hui et ne survivra pas six
  mois. Le decalage, lui, rend la faute IMPOSSIBLE au lieu d'interdite.

CE QUE FAIT CE SCRIPT : app_contact_id += 10 000 000, partout. Apres quoi

    < 10 000 000   c'est un numero de Hektor
    >= 10 000 000  c'est le notre

et un numero dit enfin d'ou il vient.

⚠ IL NE COUTERA JAMAIS MOINS CHER QU'AUJOURD'HUI : rien ne lit encore la
  doublure (0 occurrence dans le worker, 0 dans le front). C'est un decalage
  arithmetique sur une colonne morte. Le jour ou elle sera vivante, ce sera une
  tout autre operation.

CE QU'IL NE TOUCHE PAS :
  - les tables de SAUVEGARDE (`*_avant_*`) : une sauvegarde garde l'etat qu'elle
    a sauve, sinon elle ne sauve plus rien ;
  - les valeurs DEJA >= 10 000 000 : ce sont les contacts nes dans l'app, qui
    ont deja leur numero. C'est aussi ce qui rend le script IDEMPOTENT.

⛔ GARDE-FOU DE COLLISION, et c'est le plus important. Avant d'ecrire, il
  verifie qu'aucune valeur decalee ne tomberait sur une valeur deja presente
  dans la plage. Exemple reel : le contact n°1 deviendrait 10 000 001 -- numero
  deja pris par un contact d'essai. Le script REFUSE et les nomme.

RETOUR ARRIERE : `--annuler` soustrait les memes 10 000 000, aux memes lignes.

    python phase2/identite/decaler_doublure_contacts.py              # montre
    python phase2/identite/decaler_doublure_contacts.py --appliquer
    python phase2/identite/decaler_doublure_contacts.py --annuler --appliquer
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"

DECALAGE = 10_000_000

# Une sauvegarde doit rester ce qu'elle etait le jour ou on l'a prise.
MOTIFS_EXCLUS = ("_avant_", "_backup", "_bak", "_old")


def tables_concernees(conn: sqlite3.Connection) -> list[str]:
    noms = []
    for (t,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        if any(motif in t for motif in MOTIFS_EXCLUS):
            continue
        colonnes = {r[1] for r in conn.execute(f'PRAGMA table_info("{t}")')}
        if "app_contact_id" in colonnes:
            noms.append(t)
    return sorted(noms)


def collisions(conn: sqlite3.Connection, tables: list[str], sens: int) -> list[tuple[int, int]]:
    """Valeurs qui, une fois deplacees, tomberaient sur une valeur deja prise.

    ⚠ LE CONTROLE EST GLOBAL, PAS PAR TABLE -- et la premiere version de ce
      script se trompait la-dessus. Un numero de contact designe la MEME
      personne dans toutes les tables : l'espace des numeros est commun. La
      repetition du 22/09 l'a montre en vrai : le contact n°1 vit dans
      `app_contact`, et `10 000 001` est deja pris par un contact d'essai dans
      `app_contact_current__sb`. Table par table, aucune collision ; en verite,
      deux personnes auraient partage un numero.
    """
    occupes: set[int] = set()
    a_bouger: set[int] = set()
    for table in tables:
        if sens > 0:
            occupes |= {r[0] for r in conn.execute(
                f'SELECT DISTINCT app_contact_id FROM "{table}" WHERE app_contact_id >= ?', (DECALAGE,))}
            a_bouger |= {r[0] for r in conn.execute(
                f'SELECT DISTINCT app_contact_id FROM "{table}" '
                f'WHERE app_contact_id IS NOT NULL AND app_contact_id < ?', (DECALAGE,))}
        else:
            occupes |= {r[0] for r in conn.execute(
                f'SELECT DISTINCT app_contact_id FROM "{table}" '
                f'WHERE app_contact_id IS NOT NULL AND app_contact_id < ?', (DECALAGE,))}
            a_bouger |= {r[0] for r in conn.execute(
                f'SELECT DISTINCT app_contact_id FROM "{table}" WHERE app_contact_id >= ?', (DECALAGE,))}
    return sorted((v, v + sens * DECALAGE) for v in a_bouger if (v + sens * DECALAGE) in occupes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deplace la doublure des contacts dans la plage de l'app.")
    parser.add_argument("--appliquer", action="store_true", help="Ecrit vraiment. Sans lui, on montre.")
    parser.add_argument("--annuler", action="store_true", help="Soustrait au lieu d'ajouter (retour arriere).")
    parser.add_argument("--base", type=Path, default=BASE, help="Base a traiter (une COPIE, pour repeter).")
    args = parser.parse_args()

    sens = -1 if args.annuler else 1
    verbe = "REDESCEND" if args.annuler else "MONTE"

    conn = sqlite3.connect(str(args.base), timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    try:
        tables = tables_concernees(conn)
        if not tables:
            print("Aucune table ne porte app_contact_id.")
            return 0

        # ── 1. LE GARDE-FOU DE COLLISION, AVANT TOUT, ET GLOBAL ──
        bloquants = collisions(conn, tables, sens)
        if bloquants:
            print(f"REFUS : {len(bloquants)} numero(s) tomberaient sur un numero deja pris.\n")
            for avant, apres in bloquants[:10]:
                print(f"  {avant} -> {apres}   (deja attribue)")
            if len(bloquants) > 10:
                print(f"  ... et {len(bloquants) - 10} autre(s)")
            print("\nCe sont les numeros des contacts NES DANS L'APP. Les liberer d'abord.")
            return 3

        # ── 2. LE COMPTE, PUIS L'ECRITURE ──
        total = 0
        details = []
        for t in tables:
            if sens > 0:
                n, = conn.execute(
                    f'SELECT COUNT(*) FROM "{t}" WHERE app_contact_id IS NOT NULL AND app_contact_id < ?',
                    (DECALAGE,)).fetchone()
            else:
                n, = conn.execute(
                    f'SELECT COUNT(*) FROM "{t}" WHERE app_contact_id >= ?', (DECALAGE,)).fetchone()
            details.append((t, n))
            total += n

        for t, n in details:
            if n:
                print(f"  {t:40s} {n:>7} ligne(s)")
        print(f"  {'TOTAL':40s} {total:>7} ligne(s) {verbe} de {DECALAGE:,}".replace(",", " "))

        if not args.appliquer:
            print("\nDRY-RUN : rien n'a ete ecrit. Ajouter --appliquer.")
            return 0

        for t, n in details:
            if not n:
                continue
            if sens > 0:
                conn.execute(
                    f'UPDATE "{t}" SET app_contact_id = app_contact_id + ? '
                    f'WHERE app_contact_id IS NOT NULL AND app_contact_id < ?', (DECALAGE, DECALAGE))
            else:
                conn.execute(
                    f'UPDATE "{t}" SET app_contact_id = app_contact_id - ? '
                    f'WHERE app_contact_id >= ?', (DECALAGE, DECALAGE))
        conn.commit()

        # ── 3. LE CONTROLE D'APRES : plus rien sous la plage ──
        restes = 0
        for t in tables:
            if sens > 0:
                r, = conn.execute(
                    f'SELECT COUNT(*) FROM "{t}" WHERE app_contact_id IS NOT NULL AND app_contact_id < ?',
                    (DECALAGE,)).fetchone()
            else:
                r, = conn.execute(f'SELECT COUNT(*) FROM "{t}" WHERE app_contact_id >= ?', (DECALAGE,)).fetchone()
            restes += r
        print(f"\n{total} ligne(s) deplacee(s). Restant du mauvais cote : {restes} (attendu 0).")
        return 0 if restes == 0 else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
