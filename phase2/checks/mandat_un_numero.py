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

# ⚠ LA MESURE SE FAIT EN MEMOIRE, PAS EN SQL, ET C'EST UN CORRECTIF DU 30/09.
# La premiere version comparait les deux tables en SQL, avec un CAST des deux
# cotes de la jointure. Un CAST sur une colonne de jointure ecarte TOUT index :
# la sonde a tourne plus de deux minutes sur 26 826 lignes, et une sonde de sante
# qui met deux minutes ne tourne pas -- elle finit par etre coupee.
# 26 826 lignes tiennent dans un dictionnaire sans peine. On lit une fois chaque
# table, on compare des ensembles, et la mesure prend moins d'une seconde.


def _lire(conn: sqlite3.Connection, table: str) -> dict:
    """{(annonce, numero): numero d'app} -- les deux colonnes ramenees au texte."""
    sortie = {}
    for app_id, annonce, numero in conn.execute(
        f"SELECT app_mandat_id, hektor_annonce_id, numero_mandat FROM {table}"
    ):
        a = str(annonce or "").strip()
        n = str(numero or "").strip()
        if a and n:
            sortie[(a, n)] = int(app_id) if app_id is not None else None
    return sortie


def _table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (nom,)).fetchone() is not None


def mesurer(conn: sqlite3.Connection) -> dict | None:
    """Rend les comptes, et `graves` leur somme.

    None si une des deux tables manque -- ce n'est PAS un zero.
    """
    if not _table_existe(conn, "app_mandat") or not _table_existe(conn, "app_mandat__sb"):
        return None
    serveur = _lire(conn, "app_mandat")
    cloud = _lire(conn, "app_mandat__sb")

    # ① LE COUPLE PORTE-T-IL LE MEME NUMERO DES DEUX COTES ?
    deux_numeros = sum(1 for cle, ident in cloud.items()
                       if cle in serveur and serveur[cle] != ident)

    # ② UN NUMERO VISE-T-IL DEUX COUPLES ? On retourne les deux tables : si un
    #    meme numero d'app pointe ici et la-bas sur des couples differents,
    #    l'identite du mandat est rompue.
    par_id_serveur = {}
    for cle, ident in serveur.items():
        if ident is not None:
            par_id_serveur[ident] = cle
    croisements = sum(1 for cle, ident in cloud.items()
                      if ident in par_id_serveur and par_id_serveur[ident] != cle)

    # ③ LE PUSH EST-IL PASSE ?
    absents_du_cloud = sum(1 for cle in serveur if cle not in cloud)

    # ④ CE QUE SEUL LE CLOUD PORTE, dans la plage de l'app : un mandat NE DANS
    #    L'APP que le miroir n'a pas encore ramene. Normal, compte a part.
    en_attente = sum(1 for cle, ident in cloud.items()
                     if cle not in serveur and (ident or 0) >= PLAGE)

    comptes = {
        "deux_numeros": deux_numeros,
        "croisements": croisements,
        "absents_du_cloud": absents_du_cloud,
        "en_attente": en_attente,
    }
    # Le run ne distribue que SOUS la plage. Un numero au-dessus, cote serveur,
    # veut dire que l'allocateur a regarde le MAX global -- le defaut d'aout.
    comptes["plage_envahie"] = sum(1 for ident in serveur.values()
                                   if (ident or 0) >= PLAGE)
    comptes["graves"] = sum(comptes[c] for c in GRAVES)
    comptes["serveur"] = len(serveur)
    comptes["supabase"] = len(cloud)
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
