#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D6 (audit C.9) — LE RECENSEMENT « CONNU DE L'APP SEULE » MARQUE-T-IL LES DEPARTS ?
                                                                  24/09/2026

On appelle la VRAIE fonction (contacts_app_seuls.recenser_objet) sur une base
jetable, avec un faux Supabase qui rend des pages comme PostgREST :
    matin 1  X et Y inconnus du serveur        -> notes
    matin 2  le serveur a rattrape Y           -> Y MARQUE, pas efface ; X reste
    matin 3  Y redevient inconnu               -> la marque tombe
    relecture COURTE (sous le plancher app)    -> on note, on NE MARQUE RIEN
    sans plancher_app (appel d'avant)          -> on NE MARQUE RIEN
    refus G-12 (langues differentes)           -> rien n'est touche
    une ligne deja marquee garde sa 1re date

⚠ LA PREUVE D'ABORD : sur la version epinglee (avant D6), rien n'est jamais
  marque -- le test doit ECHOUER.
      python phase2/checks/test_d6_recensement_expire.py --script <fichier>
N'ECRIT RIEN dans la vraie base, n'appelle pas Supabase.
"""
from __future__ import annotations

import argparse
import importlib.util
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
ECHECS: list[str] = []
TOTAL = 10


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK ' if ok else 'KO '} {nom}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        ECHECS.append(nom)


def charger(chemin: Path):
    sys.path.insert(0, str(RACINE / "phase2" / "sync"))
    spec = importlib.util.spec_from_file_location("recensement_sous_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FauxSupabase:
    """Rend `lignes` par pages de 1 000, triees et filtrees par le curseur (gt.)."""

    def __init__(self, lignes: list[dict]):
        self.lignes = sorted(lignes, key=lambda r: r["relation_key"])

    def request(self, *, method: str, path: str):
        curseur = path.split("relation_key=gt.")[1] if "relation_key=gt." in path else ""
        return [r for r in self.lignes if r["relation_key"] > curseur][:1000]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default=str(RACINE / "phase2" / "identite" / "contacts_app_seuls.py"))
    args = ap.parse_args()
    M = charger(Path(args.script))
    print(f"script teste : {args.script}")

    conn = sqlite3.connect(":memory:")
    conn.executescript(M.DDL)
    conn.execute("CREATE TABLE app_contact_relation_current (relation_key TEXT PRIMARY KEY)")
    # la couche locale : 300 liens connus du serveur
    connus = [f"k{i:04d}" for i in range(300)]
    conn.executemany("INSERT INTO app_contact_relation_current VALUES (?)", [(k,) for k in connus])
    q = lambda s, p=(): conn.execute(s, p).fetchone()[0]  # noqa: E731

    def appel(cles_app: list[str], plancher_app=250, defaut=False):
        client = FauxSupabase([{"relation_key": k, "hektor_contact_id": "1", "hektor_annonce_id": "2",
                                "app_contact_id": None, "role_contact": "r"} for k in cles_app])
        kw = dict(couche="app_contact_relation_current", registre="app_relation_app_seule",
                  cle="relation_key", champs=["relation_key"], plancher=100, libelle="relations")
        if not defaut:
            kw["plancher_app"] = plancher_app
        try:
            return M.recenser_objet(conn, client, **kw)
        except TypeError as exc:  # la version d'avant ne connait pas plancher_app
            print(f"     (appel refuse par cette version : {type(exc).__name__})")
            return M.recenser_objet(conn, client, **{k: v for k, v in kw.items() if k != "plancher_app"})

    absent = lambda k: q("SELECT absent_depuis FROM app_relation_app_seule WHERE relation_key=?", (k,))  # noqa: E731

    # matin 1 : X et Y inconnus
    appel(connus + ["zX", "zY"])
    controle("(1) deux liens inconnus du serveur sont notes",
             q("SELECT COUNT(*) FROM app_relation_app_seule") == 2 and absent("zX") is None and absent("zY") is None)

    # matin 2 : le serveur a rattrape Y (il est dans la couche locale)
    conn.execute("INSERT INTO app_contact_relation_current VALUES ('zY')")
    appel(connus + ["zX", "zY"])
    controle("(2) le lien rattrape par le serveur est MARQUE", absent("zY") is not None, f"{absent('zY')}")
    controle("(3) il n'est PAS efface", q("SELECT COUNT(*) FROM app_relation_app_seule") == 2)
    controle("(4) le lien encore inconnu n'est pas marque", absent("zX") is None)

    # une ligne deja marquee garde sa premiere date
    conn.execute("UPDATE app_relation_app_seule SET absent_depuis='2026-01-01 00:00:00' WHERE relation_key='zY'")
    appel(connus + ["zX", "zY"])
    controle("(5) une ligne deja marquee garde sa premiere date", absent("zY") == "2026-01-01 00:00:00")

    # matin 3 : Y redevient inconnu
    conn.execute("DELETE FROM app_contact_relation_current WHERE relation_key='zY'")
    appel(connus + ["zX", "zY"])
    controle("(6) un lien revenu perd sa marque", absent("zY") is None)

    # relecture courte : sous le plancher app -> aucune conclusion
    appel(["zX"] + connus[:10], plancher_app=250)
    controle("(7) relecture COURTE : rien n'est marque",
             absent("zY") is None and absent("zX") is None,
             f"zX={absent('zX')} zY={absent('zY')}")

    # appel sans plancher_app (comme un appel d'avant D6) : on ne marque pas
    r = appel(connus + ["zX"], defaut=True)
    controle("(8) sans plancher_app : rien n'est marque", r is not None and absent("zY") is None)

    # refus G-12 : Supabase ne parle plus la meme langue -> rien n'est touche
    avant = conn.execute("SELECT relation_key, absent_depuis FROM app_relation_app_seule ORDER BY 1").fetchall()
    r = appel([f"w{i:04d}" for i in range(300)])
    apres = conn.execute("SELECT relation_key, absent_depuis FROM app_relation_app_seule ORDER BY 1").fetchall()
    controle("(9) refus G-12 : registre intact", r is None and avant == apres)

    # la vraie etape du run passe bien les planchers app
    source = Path(args.script).read_text(encoding="utf-8")
    controle("(10) les trois appels du run portent un plancher app",
             source.count("plancher_app=PLANCHER_APP_") == 3, str(source.count("plancher_app=PLANCHER_APP_")))

    print(f"\n{'TOUT VERT' if not ECHECS else str(len(ECHECS)) + ' ECHEC(S)'} ({TOTAL - len(ECHECS)}/{TOTAL})")
    return 1 if ECHECS else 0


if __name__ == "__main__":
    sys.exit(main())
