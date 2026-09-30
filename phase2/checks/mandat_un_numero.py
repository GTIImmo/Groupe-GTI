#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A.3-tech etape B — UN MANDAT, UN NUMERO : le serveur et Supabase d'accord ?
                                                                  30/09/2026

L'OEIL DU REGISTRE DES MANDATS. Meme role que `annonce_un_numero` (C.9-b) pour
l'annonce, et meme patron -- une seule formule, lue par la sonde de sante ET par
le controle de nuit, parce que deux copies d'une meme regle divergent tot ou tard.

CE QU'ON COMPARE
----------------
    le serveur   app_mandat        la table locale, remplie par le run
    Supabase     app_mandat__sb    sa DOUBLURE, descendue par pull_from_supabase

⚠ LA DOUBLURE NE DEMANDE AUCUN CODE, et c'est verifie le 30/09 : le descendeur
  lit le schema de Supabase et descend TOUT ce qu'il trouve ; quand le nom existe
  deja en local il le range sous `<nom>__sb`. app_mandat -> app_mandat__sb, sans
  rien a declarer. « Pas de liste a tenir, donc aucune table ne passe au travers. »

CE QUI EST GRAVE -- seuil ZERO
-------------------------------
    deux_numeros        un meme couple (annonce, numero) porte DEUX numeros
                        d'app. C'est le defaut que la cle unique doit empecher ;
                        s'il apparait, c'est que les deux distributeurs se sont
                        croises.
    croisements         un meme numero d'app vise DEUX couples differents.
    absents_du_cloud    une ligne du serveur que Supabase n'a pas. Le push n'est
                        pas passe -- et un registre incomplet qui se presente
                        comme a jour est exactement ce qu'on refuse ailleurs.
    plage_envahie       un numero >= 1 000 000 pose par le RUN. C'est le defaut
                        d'aout, celui qui a coute cinq jours de creations
                        impossibles cote affaires.

CE QUI N'EST PAS GRAVE, et se compte a part pour ne pas crier pour rien
-----------------------------------------------------------------------
    en_attente          une ligne que SEUL Supabase porte, avec un numero de la
                        plage de l'app : un mandat NE DANS L'APP que le miroir
                        n'a pas encore ramene. C'est le fonctionnement normal,
                        et cela DOIT retomber a zero apres une descente + un run.

CE QU'ELLE REND
---------------
`None` si une table manque -- une mesure impossible n'est PAS un zero, et la
sonde doit le dire. Tant que la doublure n'a jamais ete descendue, c'est le cas,
et c'est honnete : on ne peut rien affirmer sur un accord qu'on n'a pas lu.

LECTURE SEULE.
    python phase2/checks/mandat_un_numero.py     la mesure, code 1 si grave
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"

# La moitie haute est reservee aux mandats nes dans l'app. Meme valeur que
# l'affaire et le dossier. Le run ne doit JAMAIS y poser un numero.
PLAGE = 1_000_000
GRAVES = ("deux_numeros", "croisements", "absents_du_cloud", "plage_envahie")

# Le CAST est du cote de la DOUBLURE seulement : cote serveur les colonnes
# restent nues, pour que SQLite se serve de la cle primaire et de l'index UNIQUE.
_S_ID = "CAST(s.app_mandat_id AS INTEGER)"
_S_AN = "CAST(s.hektor_annonce_id AS TEXT)"
_S_NU = "CAST(s.numero_mandat AS TEXT)"

REQUETES = {
    "deux_numeros": f"""
        SELECT COUNT(*) FROM app_mandat__sb s
          JOIN app_mandat m ON m.hektor_annonce_id = {_S_AN}
                           AND m.numero_mandat    = {_S_NU}
         WHERE m.app_mandat_id <> {_S_ID}""",
    "croisements": f"""
        SELECT COUNT(*) FROM app_mandat__sb s
          JOIN app_mandat m ON m.app_mandat_id = {_S_ID}
         WHERE m.hektor_annonce_id <> {_S_AN}
            OR m.numero_mandat    <> {_S_NU}""",
    "absents_du_cloud": """
        SELECT COUNT(*) FROM app_mandat m
         WHERE NOT EXISTS (
               SELECT 1 FROM app_mandat__sb s
                WHERE CAST(s.hektor_annonce_id AS TEXT) = m.hektor_annonce_id
                  AND CAST(s.numero_mandat AS TEXT)     = m.numero_mandat)""",
    "en_attente": f"""
        SELECT COUNT(*) FROM app_mandat__sb s
         WHERE {_S_ID} >= {PLAGE}
           AND NOT EXISTS (
               SELECT 1 FROM app_mandat m
                WHERE m.hektor_annonce_id = {_S_AN}
                  AND m.numero_mandat     = {_S_NU})""",
}


def _table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (nom,)).fetchone() is not None


def mesurer(conn: sqlite3.Connection) -> dict | None:
    """Rend les comptes, et `graves` leur somme.

    None si une des deux tables manque -- ce n'est PAS un zero.
    """
    if not _table_existe(conn, "app_mandat") or not _table_existe(conn, "app_mandat__sb"):
        return None
    comptes = {cle: conn.execute(sql).fetchone()[0] for cle, sql in REQUETES.items()}
    # Le run ne distribue que SOUS la plage. Un numero au-dessus, cote serveur,
    # veut dire que l'allocateur a regarde le MAX global -- le defaut d'aout.
    comptes["plage_envahie"] = conn.execute(
        f"SELECT COUNT(*) FROM app_mandat WHERE app_mandat_id >= {PLAGE}").fetchone()[0]
    comptes["graves"] = sum(comptes[c] for c in GRAVES)
    comptes["serveur"] = conn.execute("SELECT COUNT(*) FROM app_mandat").fetchone()[0]
    comptes["supabase"] = conn.execute("SELECT COUNT(*) FROM app_mandat__sb").fetchone()[0]
    return comptes


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    conn = sqlite3.connect(f"file:{BASE.as_posix()}?mode=ro", uri=True)
    try:
        m = mesurer(conn)
    finally:
        conn.close()
    if m is None:
        print("NON MESURABLE : app_mandat ou sa doublure app_mandat__sb manque.")
        print("   (la doublure arrive avec : python phase2/sync/pull_from_supabase.py")
        print("    --table app_mandat -- aucun code a ecrire, le descendeur la prend seul)")
        return 2
    print(f"serveur {m['serveur']} mandats · doublure Supabase {m['supabase']}")
    for cle in GRAVES:
        print(f"  {cle:22} {m[cle]}")
    print(f"  {'en_attente':22} {m['en_attente']}   (normal : ne dans l'app, pas encore chez Hektor)")
    if m["graves"]:
        print(f"GRAVE : {m['graves']} ecart(s) -- un mandat doit avoir UN numero.")
        return 1
    print("Un mandat, un numero : le serveur et Supabase sont d'accord.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
