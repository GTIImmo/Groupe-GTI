# -*- coding: utf-8 -*-
"""A.3-tech (29/09/2026) -- UN MANDAT NE DISPARAIT PAS. LOCALE.

CE QU'ELLE SURVEILLE, ET POURQUOI C'EST CELA
---------------------------------------------
`app_mandat` est le registre : il garde tout, definitivement. La seule question
qui compte pour un registre est donc :

    est-ce qu'il contient toujours TOUT ce qu'on lui a confie ?

-- PREMIERE VERSION, LE MATIN MEME : elle comparait la table au REGISTRE ACTUEL
   (app_mandat_register_current) et classait les absents en « encore en cours »
   ou non. Frederic : « je comprends pas en quoi cela nous importe que le mandat
   soit echu ou non ». DEUX DEFAUTS, et il les a trouves tous les deux.

   1. « ECHU » N'A AUCUN SENS POUR UN REGISTRE. Un mandat de 2019, clos, sur un
      bien vendu, doit y figurer -- la loi demande dix ans de conservation. Un
      mandat echu absent est EXACTEMENT le meme trou qu'un mandat en cours
      absent. Hierarchiser, c'est importer une intuition de metier dans un objet
      dont la nature est de ne rien hierarchiser.

   2. COMPARER A LA VUE, C'EST MESURER UNE DIFFERENCE VOULUE.
      app_mandat_register_current est une vue de travail : elle montre le parc,
      par construction. Qu'elle porte moins que le registre n'est pas un defaut,
      c'est son role. Et cet ecart DISPARAITRA TOUT SEUL le jour ou la vue lira
      cette table. Une sentinelle qui surveille une grandeur transitoire ne
      survit pas a son chantier.

CE QU'ELLE SURVEILLE DONC, ET QUI RESTERA VRAI APRES LA COUPURE
---------------------------------------------------------------
    miroir_absents   un mandat du miroir absent de la table   -> la chaine s'est arretee
    doublons         deux lignes pour un meme couple          -> la cle a cede
    plage_envahie    un id du run dans la plage de l'app      -> le defaut d'aout
                                                                 (cinq jours de
                                                                  creations impossibles)

LE RETARD DE LA VUE EST RENDU EN INFORMATION, JAMAIS EN ALERTE. Il dit « la vue
est en retard sur la table », ce qui est vrai ET VOULU jusqu'au rebranchement.

CE QU'ELLE REND
---------------
`None` si une table manque -- et la sonde le DIRA : une mesure impossible n'est
PAS un zero.
"""
from __future__ import annotations

import sqlite3

# Les trois types d'offre que le registre de l'app admet (decision du 26/08).
# Ils ne servent QU'A l'information sur le retard de la vue : la table, elle,
# porte tout, y compris les locations.
TYPES_ADMIS = ("0", "10", "6")

# La moitie haute est reservee aux mandats nes dans l'app. Le run ne doit JAMAIS
# y poser un numero -- c'est l'invariant de l'allocateur.
PLAGE_RESERVEE_APP = 1_000_000


def _table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?", (nom,)
    ).fetchone() is not None


def mesurer(conn: sqlite3.Connection) -> dict | None:
    """Les trois gardes du registre, plus le retard de la vue en information.

    None si app_mandat manque : ce n'est PAS un zero.
    """
    if not _table_existe(conn, "app_mandat"):
        return None

    lignes = conn.execute("SELECT COUNT(*) FROM app_mandat").fetchone()[0]

    # ① LA CLE A-T-ELLE TENU ?
    doublons = conn.execute(
        "SELECT COUNT(*) FROM (SELECT 1 FROM app_mandat"
        " GROUP BY hektor_annonce_id, numero_mandat HAVING COUNT(*) > 1)"
    ).fetchone()[0]

    # ② L'ALLOCATEUR A-T-IL TENU ? Le run ne doit rien poser dans la plage de
    #    l'app. C'est cet invariant qui a cede en aout, cote affaires.
    plage_envahie = conn.execute(
        "SELECT COUNT(*) FROM app_mandat WHERE app_mandat_id >= ?",
        (PLAGE_RESERVEE_APP,),
    ).fetchone()[0]

    # ③ LA CHAINE A-T-ELLE TOURNE ? Tout mandat du miroir portant une annonce ET
    #    un numero doit etre dans la table. S'il en manque, l'etape de nuit ne
    #    passe plus -- et le registre cesse d'etre complet sans rien dire.
    miroir_absents = None
    miroir_lu = None
    try:
        conn.execute("SELECT 1 FROM hektor.hektor_mandat LIMIT 1")
        connus = {
            (str(a), str(n))
            for a, n in conn.execute(
                "SELECT hektor_annonce_id, numero_mandat FROM app_mandat")
        }
        miroir_absents = 0
        miroir_lu = 0
        for annonce, numero in conn.execute(
            "SELECT hektor_annonce_id, numero FROM hektor.hektor_mandat"
        ):
            a = str(annonce or "").strip()
            n = str(numero or "").strip()
            if not a or not n:
                continue          # 94 lignes sans annonce ni numero : ecartees a raison
            miroir_lu += 1
            if (a, n) not in connus:
                miroir_absents += 1
    except sqlite3.Error:
        # Le miroir n'est pas attache a cette connexion : on ne devine pas.
        miroir_absents = None

    # ④ LE RETARD DE LA VUE -- INFORMATION, JAMAIS UNE ALERTE.
    retard_vue = None
    if _table_existe(conn, "app_mandat_register_current"):
        au_registre = {
            (str(a), str(n))
            for a, n in conn.execute(
                "SELECT hektor_annonce_id, numero_mandat FROM app_mandat_register_current")
        }
        retard_vue = sum(
            1
            for a, n, t in conn.execute(
                "SELECT hektor_annonce_id, numero_mandat, offre_type FROM app_mandat")
            if (str(a), str(n)) not in au_registre and str(t or "") in TYPES_ADMIS
        )

    return {
        "lignes": lignes,
        "doublons": doublons,
        "plage_envahie": plage_envahie,
        "miroir_absents": miroir_absents,
        "miroir_lu": miroir_lu,
        "retard_vue": retard_vue,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    racine = Path(__file__).resolve().parents[2]
    cx = sqlite3.connect(f"file:{(racine / 'phase2' / 'phase2.sqlite').as_posix()}?mode=ro", uri=True)
    try:
        cx.execute("ATTACH DATABASE ? AS hektor", (str(racine / "data" / "hektor.sqlite"),))
    except sqlite3.Error:
        pass
    try:
        m = mesurer(cx)
    finally:
        cx.close()
    if m is None:
        print("NON MESURABLE : app_mandat manque -- ce n'est pas un zero")
        raise SystemExit(1)
    print("UN MANDAT NE DISPARAIT PAS")
    print("   lignes au registre            : %s" % m["lignes"])
    print("   doublons sur la cle           : %s   (doit valoir 0)" % m["doublons"])
    print("   ids dans la plage de l'app    : %s   (doit valoir 0)" % m["plage_envahie"])
    if m["miroir_absents"] is None:
        print("   mandats du miroir absents     : NON MESURE (miroir non attache)")
    else:
        print("   mandats du miroir absents     : %s sur %s   (doit valoir 0)"
              % (m["miroir_absents"], m["miroir_lu"]))
    print("")
    print("   -- information, jamais une alerte --")
    print("   retard de la vue de travail   : %s" % m["retard_vue"])
    print("      (la vue montre le parc ; elle porte moins que le registre,")
    print("       c'est son role, et cet ecart disparaitra au rebranchement)")
