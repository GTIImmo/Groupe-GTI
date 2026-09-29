# -*- coding: utf-8 -*-
"""A.3-tech (29/09/2026) -- UN MANDAT NE DISPARAIT PAS DU REGISTRE. LOCALE.

CE QU'ELLE SURVEILLE
--------------------
`app_mandat` est la table DURABLE : elle garde tout, et ne perd rien.
`app_mandat_register_current` est la VUE de travail, refaite chaque nuit a
partir des annonces vivantes. Un mandat qui est dans la premiere et pas dans la
seconde a ete PERDU par le registre.

POURQUOI ELLE EXISTE
--------------------
Le mandat etait l'objet le MOINS surveille du projet : UNE sentinelle sur les
24, et elle regardait autre chose (les biens diffuses sans mandat). Pendant ce
temps le registre perdait ses lignes depuis le 31/07 sans que rien ne le dise.
Mesure du 29/09 : 23 091 des 23 840 lignes figees au 31/07, et 635 mandats de
vente absents -- dont 80 qui courent encore.

-- LE FILTRE DES TYPES D'OFFRE N'EST PAS UN DETAIL, C'EST LE COEUR DE LA MESURE.
   La table porte TOUT, locations comprises (« le serveur recoit tous les
   types »). Le registre, lui, n'admet que la vente, la vente immo pro et le
   neuf -- decision de Frederic du 26/08. Compter sans ce filtre annonce
   2 983 pertes la ou il y en a 635 : le reste est ECARTE VOLONTAIREMENT.
   C'est exactement l'erreur commise le 29/09, et corrigee par sa question
   « est-ce que ce ne sont pas des mandats de location ? ».

CE QU'ELLE REND
---------------
`None` si une des deux tables manque -- et la sonde le DIRA : une mesure
impossible n'est PAS un zero.
"""
from __future__ import annotations

import sqlite3
from datetime import date

# Les trois seuls types d'offre que le registre de l'app admet (26/08).
# Les locations (2, 11) et le saisonnier (8) restent au serveur.
TYPES_ADMIS = ("0", "10", "6")


def _table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?", (nom,)
    ).fetchone() is not None


def mesurer(conn: sqlite3.Connection) -> dict | None:
    """Les mandats que la table durable a et que le registre n'a pas.

    None si une des deux tables manque : ce n'est PAS un zero.
    """
    if not _table_existe(conn, "app_mandat"):
        return None
    if not _table_existe(conn, "app_mandat_register_current"):
        return None

    au_registre = {
        (str(a), str(n))
        for a, n in conn.execute(
            "SELECT hektor_annonce_id, numero_mandat FROM app_mandat_register_current"
        )
    }

    aujourd_hui = date.today().isoformat()
    perdus = 0
    en_cours = 0
    ecartes = 0
    sans_type = 0
    exemples: list[str] = []

    for annonce, numero, type_offre, date_fin in conn.execute(
        "SELECT hektor_annonce_id, numero_mandat, offre_type, date_fin FROM app_mandat"
    ):
        if (str(annonce), str(numero)) in au_registre:
            continue
        t = str(type_offre or "")
        if not t:
            # Sans type on ne tranche pas : on le COMPTE A PART plutot que de le
            # ranger d'office du cote des pertes ou des locations.
            sans_type += 1
            continue
        if t not in TYPES_ADMIS:
            ecartes += 1
            continue
        perdus += 1
        if date_fin and str(date_fin) >= aujourd_hui:
            en_cours += 1
            if len(exemples) < 5:
                exemples.append(f"{annonce}/{numero} jusqu'au {date_fin}")

    return {
        "perdus": perdus,
        "en_cours": en_cours,
        "ecartes_locations": ecartes,
        "sans_type": sans_type,
        "au_registre": len(au_registre),
        "exemples": exemples,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    base = Path(__file__).resolve().parents[1] / "phase2.sqlite"
    cx = sqlite3.connect(f"file:{base.as_posix()}?mode=ro", uri=True)
    try:
        m = mesurer(cx)
    finally:
        cx.close()
    if m is None:
        print("NON MESURABLE : une des deux tables manque -- ce n'est pas un zero")
        raise SystemExit(1)
    print("UN MANDAT NE DISPARAIT PAS DU REGISTRE")
    print("   lignes au registre            : %s" % m["au_registre"])
    print("   PERDUS (types admis)          : %s" % m["perdus"])
    print("   dont ENCORE EN COURS          : %s" % m["en_cours"])
    print("   ecartes (locations, voulu)    : %s" % m["ecartes_locations"])
    print("   sans type d'offre connu       : %s" % m["sans_type"])
    for e in m["exemples"]:
        print("      %s" % e)
