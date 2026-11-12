#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- LE RAPPORT COMPARATIF AVEC LE GEL.            13/11/2026

Mission de Frederic : *« fais-moi un rapport comparatif avec mon regel actuel.
Je controlerai ton rapport demain matin. »*

⭐⭐ LA COMPARAISON EST ENFIN EXACTE. Jusqu'ici je comparais des BIENS a des
  CHAINES, ce qui demandait une traduction. Maintenant les deux portent le MEME
  triplet :
        (ligne du classeur, role, app_affaire_id)
  Le gel : `app_classeur_lien`. Moi : APPARIEUR_V2_LIENS_2026-11-13.csv.
  ⭐ Et c'est le bon niveau : le numero de transaction NE BOUGE JAMAIS, alors
    qu'une chaine est recalculee chaque nuit.

CE QUE LE RAPPORT ETABLIT :
    . les liens IDENTIQUES  -> ce qui est confirme par deux methodes disjointes
    . les liens DIVERGENTS  -> meme ligne, meme role, transaction DIFFERENTE
                               ⛔ c'est la liste de travail : l'un des deux a tort
    . les liens que SEUL LE GEL a    -> ce que ma methode rate
    . les liens que SEUL MOI ai      -> le gain possible
    . et pour chacun, le NOMBRE DE FAMILLES de temoins qui soutiennent mon lien,
      pour que Frederic puisse juger sans me croire sur parole

LECTURE SEULE.
"""
from __future__ import annotations

import collections
import csv
import io
import sqlite3
import sys
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

LIENS_V2 = RACINE / "notice" / "APPARIEUR_V2_LIENS_2026-11-13.csv"
FINAL_V2 = RACINE / "notice" / "APPARIEUR_V2_FINAL_2026-11-13.csv"
SORTIE = RACINE / "notice" / "RAPPORT_V2_CONTRE_GEL_2026-11-13.csv"


def main() -> int:
    print("=" * 88)
    print("RAPPORT COMPARATIF -- MA METHODE CONTRE LE GEL")
    print("   comparaison EXACTE : (ligne du classeur, role, numero de transaction)")
    print("=" * 88)

    # ── LE GEL ──────────────────────────────────────────────────────────────
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""select ligne_classeur, role, app_affaire_id, confiance, etage,
                        gele_le, id_unique
                   from app_classeur_lien""")
    gel = {}
    gel_par_ligne = collections.defaultdict(dict)
    for lig, role, aff, conf, et, le, ident in c.fetchall():
        gel[(str(lig), str(role))] = {"aff": aff, "conf": conf, "etage": et,
                                      "le": le, "id": ident}
        gel_par_ligne[str(lig)][str(role)] = aff
    # pour eclairer : le bien et le genre de chaque transaction
    c.execute("select app_affaire_id, kind, hektor_annonce_id, numero_mandat from app_affaire_ledger")
    quoi = {r[0]: {"kind": r[1], "bien": r[2], "mandat": r[3]} for r in c.fetchall()}
    con.close()
    print("\nLE GEL   : %d liens, %d lignes du classeur" % (len(gel), len(gel_par_ligne)))
    dates_gel = collections.Counter(str(v["le"])[:10] for v in gel.values())
    print("           pose le : %s" % " . ".join("%s (%d)" % (k, n)
                                                 for k, n in dates_gel.most_common(4)))

    # ── MOI ─────────────────────────────────────────────────────────────────
    mien, mien_par_ligne = {}, collections.defaultdict(dict)
    with io.open(LIENS_V2, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            k = (r["ligne du classeur"], r["role"])
            mien[k] = {"aff": int(r["app_affaire_id"]), "score": int(r["score"]),
                       "pourquoi": r["pourquoi"]}
            mien_par_ligne[r["ligne du classeur"]][r["role"]] = int(r["app_affaire_id"])
    familles = {}
    with io.open(FINAL_V2, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            familles[r["ligne"]] = {"n": int(r["nb familles"] or 0),
                                    "quelles": r["familles"],
                                    "ecart": int(r["ecart au 2e"] or 0),
                                    "id": r["ID Unique"]}
    print("MA v2    : %d liens, %d lignes du classeur" % (len(mien), len(mien_par_ligne)))

    # ── LA CONFRONTATION, LIEN PAR LIEN ─────────────────────────────────────
    res = collections.Counter()
    par_familles = collections.defaultdict(collections.Counter)
    divergents, moi_seul, gel_seul = [], [], []
    for k in set(gel) | set(mien):
        lig, role = k
        g, m = gel.get(k), mien.get(k)
        nf = familles.get(lig, {}).get("n", 0)
        if g and m:
            if g["aff"] == m["aff"]:
                res["IDENTIQUES"] += 1
                par_familles[nf]["accord"] += 1
            else:
                res["DIVERGENTS"] += 1
                par_familles[nf]["divergent"] += 1
                divergents.append([lig, familles.get(lig, {}).get("id", ""), role,
                                   g["aff"], m["aff"], g["conf"], g["etage"],
                                   nf, familles.get(lig, {}).get("quelles", ""),
                                   m["pourquoi"],
                                   quoi.get(g["aff"], {}).get("bien", ""),
                                   quoi.get(m["aff"], {}).get("bien", "")])
        elif m:
            res["MOI SEUL"] += 1
            par_familles[nf]["moi seul"] += 1
            moi_seul.append([lig, familles.get(lig, {}).get("id", ""), role, "",
                             m["aff"], "", "", nf,
                             familles.get(lig, {}).get("quelles", ""), m["pourquoi"],
                             "", quoi.get(m["aff"], {}).get("bien", "")])
        else:
            res["LE GEL SEUL"] += 1
            gel_seul.append([lig, g.get("id", ""), role, g["aff"], "", g["conf"],
                             g["etage"], nf, familles.get(lig, {}).get("quelles", ""),
                             "", quoi.get(g["aff"], {}).get("bien", ""), ""])

    tot = sum(res.values())
    print("\n" + "-" * 88)
    print("① LE RESULTAT, LIEN PAR LIEN")
    print("-" * 88)
    for k in ("IDENTIQUES", "DIVERGENTS", "MOI SEUL", "LE GEL SEUL"):
        print("   %-14s %6d  (%5.1f %%)" % (k, res[k], 100.0 * res[k] / max(1, tot)))

    print("\n" + "-" * 88)
    print("② L'ACCORD SELON LE NOMBRE DE FAMILLES DE TEMOINS QUI SOUTIENNENT MON LIEN")
    print("   ⭐ c'est la mesure qui permet de JUGER sans me croire sur parole :")
    print("     plus il y a de familles, plus le gel confirme -- donc mon echelle")
    print("     de certitude dit quelque chose de vrai.")
    print("-" * 88)
    print("   %-10s %9s %9s %9s %9s" % ("familles", "accord", "divergent", "moi seul", "accord %"))
    print("   " + "-" * 56)
    for nf in sorted(par_familles, reverse=True):
        cc = par_familles[nf]
        juges = cc["accord"] + cc["divergent"]
        pc = (100.0 * cc["accord"] / juges) if juges else 0.0
        print("   %-10d %9d %9d %9d %8.1f %%"
              % (nf, cc["accord"], cc["divergent"], cc["moi seul"], pc))

    print("\n" + "-" * 88)
    print("③ LES DIVERGENCES, PAR ETAGE DU GEL -- ou le gel est-il fragile ?")
    print("-" * 88)
    for k, n in collections.Counter(d[6] for d in divergents).most_common(8):
        print("   %-56s %4d" % (str(k)[:56], n))
    print("\n   et par CONFIANCE du gel :")
    for k, n in collections.Counter(d[5] for d in divergents).most_common():
        print("      %-16s %4d" % (k, n))

    print("\n" + "-" * 88)
    print("④ MEME BIEN OU BIEN DIFFERENT ? -- la divergence est-elle grave ?")
    print("-" * 88)
    meme_bien = sum(1 for d in divergents if d[10] and d[10] == d[11])
    print("   divergences sur la MEME annonce (on hesite entre 2 transactions"
          " du meme bien) : %d" % meme_bien)
    print("   divergences sur une annonce DIFFERENTE (vraie erreur de l'un des"
          " deux)          : %d" % (len(divergents) - meme_bien))

    with io.open(SORTIE, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ligne", "ID Unique", "role", "transaction GEL", "transaction v2",
                    "confiance gel", "etage gel", "familles v2", "quelles familles",
                    "comment v2 a choisi", "bien du gel", "bien de la v2", "cas"])
        for d in divergents:
            w.writerow(d + ["DIVERGENT"])
        for d in moi_seul:
            w.writerow(d + ["MOI SEUL"])
        for d in gel_seul:
            w.writerow(d + ["LE GEL SEUL"])
    print("\n   ecrit : %s  (%d lignes)"
          % (SORTIE.name, len(divergents) + len(moi_seul) + len(gel_seul)))
    print("\n" + "=" * 88)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
