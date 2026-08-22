#!/usr/bin/env python3
"""LE JOURNAL DES DOUBLURES — le serveur dit-il la meme chose que l'app ? (tache B.4)

POURQUOI
--------
Depuis B.2 (22/08/2026), chaque fiche existe en DEUX exemplaires sur le serveur :

    app_contact_search_current       76 845   la version HEKTOR, refaite chaque nuit
    app_contact_search_current__sb   10 750   la version de l'APP, descendue de Supabase

Personne ne tranche entre les deux -- c'est le principe de la doublure, et l'arbitrage est
le chantier C. En attendant, il faut REGARDER : la divergence est-elle rare, stable, ou en
train de croitre ? Sans mesure, la bascule se deciderait a l'intuition. C'est exactement
ce qui a laisse app_dossier_id deriver de mars a juin sans que personne le voie.

POURQUOI UN JOURNAL ET PAS UNE ALARME
-------------------------------------
Une alarme sur « les deux ne disent pas la meme chose » sonnerait en permanence, pour rien :
Supabase ne porte qu'un SOUS-ENSEMBLE (57 519 contacts sur 355 668), et
app_diffusion_request__sb porte 9 lignes face a un natif vide. Ces ecarts sont legitimes.
Une sentinelle qui sonne toujours ne protege de rien -- voir les 855 notifications non lues
que plus personne ne regarde.

D'ou : un JOURNAL (une photo par jour, jamais effacee) + UNE alarme etroite, celle qui a
vraiment un sens -- les recherches dont les CRITERES different alors que la ligne existe
des deux cotes. Mesure le 22/08 : 0 sur 10 750.

CE QU'IL NE FAIT PAS
--------------------
Aucun appel reseau : les deux tables sont sur le meme disque. Il ne modifie aucune donnee,
il n'ecrit que dans son propre journal. Retour arriere : DROP TABLE app_doublure_journal.

USAGE
-----
  python phase2/checks/comparer_doublures.py            # releve et ecrit le journal
  python phase2/checks/comparer_doublures.py --dry-run  # affiche sans ecrire
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
JOURNAL = "app_doublure_journal"

JOURNAL_DDL = f"""
CREATE TABLE IF NOT EXISTS {JOURNAL} (
    releve_le      TEXT NOT NULL,
    doublure       TEXT NOT NULL,
    cle            TEXT NOT NULL,
    accord         INTEGER NOT NULL,
    hektor_seul    INTEGER NOT NULL,
    app_seule      INTEGER NOT NULL,
    PRIMARY KEY (releve_le, doublure)
)
"""

# La cle d'appariement de chaque doublure. Sans elle on ne peut rien comparer : il faut
# savoir quelle ligne d'un cote correspond a quelle ligne de l'autre.
CLES: dict[str, tuple[str, ...]] = {
    "app_contact_current__sb": ("hektor_contact_id",),
    "app_contact_search_current__sb": ("hektor_contact_id", "search_index"),
    # Cles relevees le 22/08 en lisant les tables, pas en les devinant : mes trois premiers
    # choix (row_key, group_key) n'existaient dans aucune des deux.
    "app_contact_relation_current__sb": ("relation_key",),
    "app_contact_duplicate_group_current__sb": ("duplicate_group_id",),
    "app_contact_duplicate_member_current__sb": ("duplicate_group_id", "hektor_contact_id"),
    "app_affaire_ledger__sb": ("app_affaire_id",),
    "app_diffusion_target__sb": ("app_dossier_id", "portal_key"),
    "app_diffusion_agency_target__sb": ("agence_nom", "portal_key"),
    "app_diffusion_request__sb": ("id",),
    "app_diffusion_request_event__sb": ("id",),
}

# L'ALARME, volontairement etroite : les criteres qu'un negociateur peut affiner dans la
# modale de recherche. Une difference ici = une saisie que Hektor n'a pas recue.
CRITERES_RECHERCHE = ("prix_min", "prix_max", "surface_min", "pieces_min", "chambre_min")


def colonnes(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute('PRAGMA table_info("%s")' % table)}


def existe(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table,)).fetchone()[0] > 0


def poser_index(conn: sqlite3.Connection, table: str, cle: tuple[str, ...]) -> None:
    """Un index sur la cle d'appariement, sans quoi la comparaison est inutilisable.

    Trouve le 22/08 : la premiere version tournait encore au bout de dix minutes. Les
    tables descendues sont creees sans AUCUN index -- comparer 355 668 lignes a 57 519
    sans index, c'est 20 milliards de comparaisons. Avec l'index : quelques secondes.

    L'index est pose une fois et reste : il ne coute que du disque, et la descente qui
    remplace la table le supprimera avec elle (on le repose au releve suivant).
    """
    nom = "idx_doublure_" + table.replace("__", "_")[:48]
    cols = ", ".join('"%s"' % c for c in cle)
    conn.execute('CREATE INDEX IF NOT EXISTS "%s" ON "%s" (%s)' % (nom, table, cols))
    conn.commit()


def comparer(conn: sqlite3.Connection, doublure: str, cle: tuple[str, ...]) -> dict | None:
    """Trois chiffres : d'accord, Hektor seul, l'app seule."""
    natif = doublure[:-4]
    if not existe(conn, natif) or not existe(conn, doublure):
        return None
    dispo = colonnes(conn, natif) & colonnes(conn, doublure)
    cle_utile = tuple(c for c in cle if c in dispo)
    if not cle_utile:
        return None
    poser_index(conn, doublure, cle_utile)
    poser_index(conn, natif, cle_utile)
    jointure = " AND ".join('h."%s" = s."%s"' % (c, c) for c in cle_utile)
    accord = conn.execute(
        'SELECT count(*) FROM "%s" s JOIN "%s" h ON %s' % (doublure, natif, jointure)
    ).fetchone()[0]
    app_seule = conn.execute(
        'SELECT count(*) FROM "%s" s WHERE NOT EXISTS '
        '(SELECT 1 FROM "%s" h WHERE %s)' % (doublure, natif, jointure)
    ).fetchone()[0]
    hektor_seul = conn.execute(
        'SELECT count(*) FROM "%s" h WHERE NOT EXISTS '
        '(SELECT 1 FROM "%s" s WHERE %s)' % (natif, doublure, jointure)
    ).fetchone()[0]
    return {"cle": "+".join(cle_utile), "accord": accord,
            "hektor_seul": hektor_seul, "app_seule": app_seule}


def recherches_divergentes(conn: sqlite3.Connection) -> int | None:
    """L'ALARME : recherches presentes des deux cotes dont les criteres different."""
    natif, doublure = "app_contact_search_current", "app_contact_search_current__sb"
    if not existe(conn, natif) or not existe(conn, doublure):
        return None
    dispo = colonnes(conn, natif) & colonnes(conn, doublure)
    champs = [c for c in CRITERES_RECHERCHE if c in dispo]
    if not champs:
        return None
    ecart = " OR ".join(
        'COALESCE(h."%s",\'\') <> COALESCE(s."%s",\'\')' % (c, c) for c in champs)
    return conn.execute(
        'SELECT count(*) FROM "%s" s JOIN "%s" h '
        'ON h.hektor_contact_id = s.hektor_contact_id AND h.search_index = s.search_index '
        'WHERE %s' % (doublure, natif, ecart)
    ).fetchone()[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare chaque doublure a sa table native et tient le journal (B.4).")
    parser.add_argument("--dry-run", action="store_true", help="Affiche sans rien ecrire.")
    parser.add_argument("--phase2-db", type=Path, default=PHASE2_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(str(args.phase2_db))
    conn.execute(JOURNAL_DDL)
    conn.commit()
    jour = time.strftime("%Y-%m-%d")

    print(f"{'DOUBLURE':<44} {'ACCORD':>9} {'HEKTOR SEUL':>12} {'APP SEULE':>10}")
    print("-" * 80)
    releves = []
    for doublure, cle in sorted(CLES.items()):
        r = comparer(conn, doublure, cle)
        if r is None:
            print(f"{doublure:<44}   (non comparable : cle ou table absente)")
            continue
        releves.append((doublure, r))
        print(f"{doublure:<44} {r['accord']:>9} {r['hektor_seul']:>12} {r['app_seule']:>10}")

    divergentes = recherches_divergentes(conn)
    print()
    print(f"ALARME  recherches dont les CRITERES different : "
          f"{divergentes if divergentes is not None else 'non mesurable'}")
    print("        (0 attendu : toute autre valeur = une saisie que Hektor n'a pas recue)")

    if args.dry_run:
        print("\n[dry-run] le journal n'a pas ete ecrit")
        return 0

    for doublure, r in releves:
        conn.execute(
            f"INSERT INTO {JOURNAL}(releve_le, doublure, cle, accord, hektor_seul, app_seule) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(releve_le, doublure) DO UPDATE SET "
            "cle=excluded.cle, accord=excluded.accord, hektor_seul=excluded.hektor_seul, "
            "app_seule=excluded.app_seule",
            (jour, doublure, r["cle"], r["accord"], r["hektor_seul"], r["app_seule"]))
    conn.commit()
    jours = conn.execute(f"SELECT count(DISTINCT releve_le) FROM {JOURNAL}").fetchone()[0]
    print(f"\njournal ecrit : {len(releves)} doublures pour le {jour} "
          f"({jours} jour(s) d'historique)")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
