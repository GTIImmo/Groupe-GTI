#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""RELIRE LA COLONNE A CONTRE LE PROTOCOLE, LIGNE PAR LIGNE -- LECTURE SEULE (son mot du 25/11).

    python -X utf8 -u phase2\checks\relire_la_colonne_a_contre_le_protocole_2026-11-25.py <vague1> [<vague2> ...]

SON MOT : « FAIS-LE TOI, ET RENDS-MOI LE CHIFFRE : sur les 500, combien ont leur etiquette EGALE au dossier de leurs
pieces du protocole, et combien de dossiers distincts. [...] je veux les 500, pas 125. »

Un autre chemin que l'ecrivain : le Sheet relu par apparier_classeur (GET), le verdict par le socle (passage 81, en
lecture seule), les etiquettes par SQL direct (pooler). Pour CHAQUE ligne de chaque vague : tranchee par le protocole ;
le dossier de SES pieces (effectives : une copie ne decide pas) = la case A = l'etiquette a l'arrivee = l'etiquette du
fichier de vague. Puis la colonne entiere : rien hors des vagues, aucune etiquette sur deux lignes.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402

DOUBLES = ["3308P0UX", "YRUF0S9H", "T2GZOY5O", "O6R10ZQA"]
LES_DEUX_DE_E = []  # 27/11 : SON ordre a mis P252U1JH et d2108609 dans la vague2a (ecrites 10:09, relues avec elle) -- l'attente « vides » du 25/11 est levee


def main() -> int:
    vagues = [Path(a) for a in sys.argv[1:]]
    import apparier_classeur as ac
    ac.load_env_file(RACINE / ".env")
    entete, lignes = ac.lire_classeur()
    kE = entete.index("Etat Actuel")
    A, row, etat, n_id = {}, {}, {}, Counter()
    for num, l in lignes:
        l = [("" if x is None else str(x)) for x in list(l)] + [""] * 38
        i = l[37].strip()
        if i:
            n_id[i] += 1
            A[i], row[i], etat[i] = l[0].strip(), num, l[kE].strip()
    con = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
    V = {i: (v, e or "", json.loads(ps) if ps else []) for i, v, e, ps in con.execute(
        "select id_unique, verdict, etiquette, pieces from verdict where passage=82")}  # 26/11 : le 82 officiel, comme l'ecrivain
    con.close()
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, app_dossier_uuid::text, app_dossier_numero, transaction_origine, hektor_affaire_id "
               "from public.app_affaire_ledger")
    R = {int(a): (u, n, PC.est_copie(int(a), o, h)) for a, u, n, o, h in cu.fetchall()}
    cn.rollback()
    cn.close()

    def dossier(ps):
        k = [a for a in ps if a in R]
        hk = [a for a in k if not R[a][2]] or k
        return {R[a][0] for a in hk}

    def arrivee(e):
        return R.get(int(e.split(":")[1]), ("",))[0] if e.startswith("NEUVE:") else e

    print("Sheet relu : %d lignes, %d ID Unique, %d ID en double, %d cases A remplies" % (
        len(lignes), len(n_id), sum(1 for x in n_id.values() if x > 1), sum(1 for v in A.values() if v)))
    toutes = {}
    code = 0
    for f in vagues:
        with f.open(encoding="utf-8-sig") as h:
            vg = {r["id_unique"]: r for r in csv.DictReader(h, delimiter=";")}
        toutes.update(vg)
        justes, fausses = 0, []
        for i, r in vg.items():
            v, e, ps = V.get(i, ("ABSENTE", "", []))
            d = dossier(ps)
            ok = (v == "TRANCHEE" and len(d) == 1 and d == {A.get(i)} and A.get(i) == arrivee(e) == r["etiquette_prevue"])
            if ok:
                justes += 1
            else:
                fausses.append((i, v, A.get(i, "")[:8], sorted(x[:8] for x in d), arrivee(e)[:8]))
        uu = {A.get(i) for i in vg}
        meme_ligne = sum(1 for i, r in vg.items() if str(row.get(i)) == r["ligne_vue"])
        print("%s : %d lignes ; etiquette = dossier de SES pieces du protocole (= case A = arrivee = prevue) : %d ; "
              "fausses %d %s ; dossiers distincts %d ; a plusieurs dossiers %d ; meme ligne qu'a la preparation %d ; "
              "ventes reglees au Sheet %d" % (
                  f.name, len(vg), justes, len(fausses), fausses[:3], len(uu),
                  sum(1 for i in vg if len(dossier(V.get(i, ("", "", []))[2])) > 1), meme_ligne,
                  sum(1 for i in vg if etat.get(i) == "Vente réglée")))
        if fausses or len(uu) != len(vg):
            code = 1
    remplies = {i for i, v in A.items() if v}
    hors = sorted(remplies - set(toutes))
    manquantes = sorted(set(toutes) - remplies)
    deux = [u for u, n in Counter(v for v in A.values() if v).items() if n > 1]
    print("la colonne entiere : %d remplies ; hors des vagues %d %s ; manquantes %d %s ; etiquettes sur deux lignes %d" % (
        len(remplies), len(hors), hors[:5], len(manquantes), manquantes[:5], len(deux)))
    print("ses 4 doubles : %s ; les 2 de la liste E : %s" % ({i: A.get(i, "?") or "vide" for i in DOUBLES},
                                                             {i: A.get(i, "?") or "vide" for i in LES_DEUX_DE_E}))
    non_tr = [i for i, x in V.items() if x[0] != "TRANCHEE" and A.get(i)]
    print("lignes NON tranchees par le protocole dont la case A est remplie : %d %s" % (len(non_tr), non_tr[:5]))
    if hors or manquantes or deux or non_tr or any(A.get(i) for i in DOUBLES + LES_DEUX_DE_E):
        code = 1
    print("⇒ %s" % ("TOUT EST JUSTE" if code == 0 else "⛔ A REGARDER"))
    return code


if __name__ == "__main__":
    sys.exit(main())
