#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""26bis-TRANSACTIONS -- L'ESSAI SUR LES VRAIES DONNEES, SANS RIEN TOUCHER.

    python -X utf8 phase2/checks/essai_reel_sur_copie_26bis.py

⭐ POURQUOI CET ESSAI EXISTE, alors que l'epreuve hors ligne est a 39/39. Elle
  monte ses propres lignes : elle prouve que le mecanisme est juste, pas qu'il est
  juste SUR NOTRE BASE. Ici les lignes sont les vraies, lues dans phase2.sqlite --
  mais dans une base NEUVE, batie avec le VRAI DDL (contraintes comprises) et
  remplie depuis la base reelle ouverte EN LECTURE SEULE. Meme patron que
  test_r2_attente (qui recopie phase2.sqlite dans un dossier temporaire).

⛔ IL N'ECRIT RIEN DE VRAI : la base reelle est ouverte en `mode=ro` + `query_only`,
  et tout se passe dans un fichier temporaire efface a la fin.

LE CRITERE EST ECRIT AVANT D'AVOIR LE RESULTAT -- sinon on juge apres coup :

    PASSAGE 1  l'etat d'AUJOURD'HUI (ni le local ni la doublure n'ont la colonne)
               -> 1 recopiee (l'essai A2, 1001424), 0 ecartee, et le code DIT que
                  la colonne manque au lieu de tomber
    PASSAGE 2  l'etat de LA NUIT PROCHAINE (refresh a cree la colonne en local, la
               descente l'a apportee dans la doublure)
               -> 1 recopiee, et la MARQUE suit si la doublure en porte une
    PASSAGE 3  LA NUIT D'APRES, rien n'a change
               -> 0 recopiee (le geste ne se repete pas)
    ET DANS LES TROIS : les 340 lignes de la plage AVEC numero et les 30 817 du
    hors-plage ne bougent PAS d'une ligne.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

import affaire_ledger as al                                          # noqa: E402

REELLE = RACINE / "phase2" / "phase2.sqlite"
TABLE = "app_affaire_ledger"
DOUBLURE = TABLE + "__sb"
PLAGE = al.PLAGE_RESERVEE_APP

VERTS = 0
ROUGES: list[str] = []


def juger(nom, attendu, obtenu):
    global VERTS
    if attendu == obtenu:
        VERTS += 1
        print("  OK    %s" % nom)
    else:
        ROUGES.append(nom)
        print("  ROUGE %s\n        attendu %r\n        obtenu %r" % (nom, attendu, obtenu))


def fabriquer(dossier: Path, avec_colonne: bool) -> Path:
    """Une base NEUVE, vrai DDL, remplie depuis la base reelle en lecture seule."""
    copie = dossier / ("avec_colonne.sqlite" if avec_colonne else "aujourd_hui.sqlite")
    src = sqlite3.connect(f"file:{REELLE.as_posix()}?mode=ro", uri=True)
    src.execute("pragma query_only = 1")
    ddl_table = src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                            (TABLE,)).fetchone()[0]
    index = [r[0] for r in src.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL",
        (TABLE,))]
    cols_table = [r[1] for r in src.execute(f"PRAGMA table_info({TABLE})")]
    cols_doublure = [r[1] for r in src.execute(f"PRAGMA table_info({DOUBLURE})")]
    src.close()

    # uri=True est OBLIGATOIRE ici : sans lui, ATTACH refuse l'adresse « file:...?mode=ro »
    # et on perdrait la garantie de lecture seule sur la base reelle.
    con = sqlite3.connect(copie, uri=True)
    con.execute(ddl_table)
    for sql in index:
        con.execute(sql)
    # la doublure, comme pull_from_supabase la recree : sans contraintes
    con.execute('CREATE TABLE "%s" (%s)' % (DOUBLURE, ", ".join('"%s"' % c
                                                                for c in cols_doublure)))
    if avec_colonne:
        # l'etat de la nuit prochaine : refresh l'ajoute en local, la descente
        # l'apporte dans la doublure (elle est RECREEE d'apres Supabase).
        con.execute(f"ALTER TABLE {TABLE} ADD COLUMN transaction_origine TEXT")
        con.execute(f'ALTER TABLE "{DOUBLURE}" ADD COLUMN transaction_origine TEXT')
    con.commit()
    con.execute("ATTACH DATABASE ? AS reel", (f"file:{REELLE.as_posix()}?mode=ro",))
    con.execute(f"INSERT INTO {TABLE} ({', '.join(cols_table)}) "
                f"SELECT {', '.join(cols_table)} FROM reel.{TABLE}")
    con.execute(f'INSERT INTO "{DOUBLURE}" ({", ".join(cols_doublure)}) '
                f'SELECT {", ".join(cols_doublure)} FROM reel."{DOUBLURE}"')
    con.commit()
    con.execute("DETACH DATABASE reel")
    con.close()
    return copie


def voisines(con):
    avec = con.execute(
        f"SELECT COUNT(*) FROM {TABLE} WHERE CAST(app_affaire_id AS INTEGER) >= {PLAGE}"
        f" AND hektor_affaire_id IS NOT NULL"
        f" AND TRIM(CAST(hektor_affaire_id AS TEXT)) <> ''").fetchone()[0]
    hors = con.execute(
        f"SELECT COUNT(*) FROM {TABLE} "
        f"WHERE CAST(app_affaire_id AS INTEGER) < {PLAGE}").fetchone()[0]
    return avec, hors


def main() -> int:
    if not REELLE.exists():
        print(f"pas de base locale : {REELLE}")
        return 2
    # ignore_cleanup_errors : Windows garde parfois la main sur un fichier SQLite
    # une seconde de trop -- un brouillon qui survit ne doit pas faire echouer un
    # essai qui, lui, a reussi.
    with tempfile.TemporaryDirectory(prefix="essai26bis_",
                                     ignore_cleanup_errors=True) as brouillon:
        dossier = Path(brouillon)

        print("=== PASSAGE 1 : L'ETAT D'AUJOURD'HUI (sans la colonne) ===")
        con = sqlite3.connect(fabriquer(dossier, avec_colonne=False))
        avant = voisines(con)
        print(f"  les voisines avant : {avant[0]} de la plage AVEC numero, "
              f"{avant[1]} hors plage")
        r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
        juger("1  une seule ligne recopiee", 1, r["recopiees"])
        juger("1b et c'est bien l'essai A2", [1001424], r.get("cles"))
        juger("1c aucune ecartee", None, r.get("ecartees_colonne_obligatoire_vide"))
        juger("1d le temoin boucle (0 -> 1)",
              (0, 1), (r["plage_sans_numero_avant"], r["plage_sans_numero_apres"]))
        juger("1e LES VOISINES N'ONT PAS BOUGE", avant, voisines(con))
        juger("1f la ligne est VRAIMENT dans le registre", 1, con.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE app_affaire_id = 1001424").fetchone()[0])
        # ⭐ et son numero n'a pas ete invente : c'est celui du serveur
        juger("1g son genre et son annonce suivent", ("offre", 28351), tuple(con.execute(
            f"SELECT kind, hektor_annonce_id FROM {TABLE} "
            f"WHERE app_affaire_id = 1001424").fetchone()))
        con.close()

        print()
        print("=== PASSAGE 2 : L'ETAT DE LA NUIT PROCHAINE (avec la colonne) ===")
        chemin2 = fabriquer(dossier, avec_colonne=True)
        con = sqlite3.connect(chemin2)
        avant = voisines(con)
        r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
        juger("2  une seule ligne recopiee", 1, r["recopiees"])
        juger("2b la colonne entre dans la recopie", True,
              r.get("colonnes_recopiees", 0) > 49)
        juger("2c les colonnes obligatoires sont les trois attendues",
              ["app_affaire_id", "kind", "present_in_hektor"],
              sorted(r.get("colonnes_obligatoires", [])))
        juger("2d LES VOISINES N'ONT PAS BOUGE", avant, voisines(con))

        print()
        print("=== PASSAGE 3 : LA NUIT D'APRES, rien n'a change ===")
        r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
        juger("3  le geste ne se repete pas", 0, r["recopiees"])
        juger("3b et il n'y a plus de candidate", 0, r["candidates"])
        juger("3c pas de doublon sur 1001424", 1, con.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE app_affaire_id = 1001424").fetchone()[0])
        juger("3d LES VOISINES N'ONT TOUJOURS PAS BOUGE", avant, voisines(con))
        con.close()

    print()
    print("%d/%d verts" % (VERTS, VERTS + len(ROUGES)))
    if ROUGES:
        print("ROUGES : " + " . ".join(ROUGES))
    return 1 if ROUGES else 0


if __name__ == "__main__":
    raise SystemExit(main())
