#!/usr/bin/env python3
"""LES 340 VRAIES PIECES DE LA PLAGE APP, CROISEES AVEC TOUT CE QUI EST DEJA DECIDE -- chantier classeur, ⑳, 22/11/2026.

Son mot du 22/11, point 10 : « ET LE CROISEMENT DES 340 avec tout ce qui est deja decide, pour savoir ce qui est a
refaire. » LECTURE SEULE : le registre local (mode=ro), le cache du chantier, l'image du protocole. Une piece par ligne
du CSV (sa regle du 22/11 : jamais deux pieces dans une case).

Pour chaque vraie piece de la plage (>= 1 000 000, origine vide, numero Hektor) : ses lignes du gel, ce que chaque
decision deja rendue en a fait (la V3, les 132 coupes, les 29 faibles, les 20 a part, les gestes du gel du 20/11), ou
tombent ses lignes (le classement du 22/11 au matin, avant et apres la V3 ; le passage v0 du protocole), et QUI l'a
jugee comme une copie -- puis ce qui est a refaire.

Sortie : notice/PROTOCOLE_LES_340_CROISEES_AVEC_LE_DECIDE_2026-11-22.csv
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import piece_copie_ou_vraie as PC  # noqa: E402

CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache")
SOCLE = CACHE / "protocole" / "socle.sqlite"
SORTIE = RACINE / "notice" / "PROTOCOLE_LES_340_CROISEES_AVEC_LE_DECIDE_2026-11-22.csv"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    N = PC.natures(con)
    INFO = {int(a): (b, k, s, n) for a, b, k, s, n in con.execute(
        "select app_affaire_id, hektor_annonce_id, kind, state, hektor_affaire_id from app_affaire_ledger")}
    con.close()
    P340 = sorted(a for a, v in N.items() if v == PC.VRAIE and a >= PC.PLAGE_APP)
    T = json.loads((CACHE / "protocole" / "temoins.json").read_text(encoding="utf-8"))
    d = json.loads((CACHE / "v3_calcul.json").read_text(encoding="utf-8"))
    g = json.loads((CACHE / "v3_gestes.json").read_text(encoding="utf-8"))
    cl = json.loads((CACHE / "t13_vague1.json").read_text(encoding="utf-8"))
    img = sorted((CACHE / "protocole" / "images").iterdir())[-1]
    gel = json.loads((img / "gel.json").read_text(encoding="utf-8"))["liens"]
    lignes_de = defaultdict(set)
    for i, a, *_ in gel:
        lignes_de[int(a)].add(i)
    v3 = defaultdict(list)
    for x in T["familles"]["v3"]:
        for a in x["pieces"]:
            v3[a].append("%s -> %s" % (x["geste"], x["ligne"] or "-"))
    c132, c29 = defaultdict(list), defaultdict(list)
    for fam, out in (("coupes_132", c132), ("coupes_29", c29)):
        for e in T["familles"][fam]:
            for m in e["morceaux"]:
                for a in m["pieces"]:
                    out[a].append("coupe %s -> %s" % (e["coupe"] or "faible", "+".join(m["lignes"])))
    apart = {x["piece"] for x in T["familles"]["a_part_20"]}
    gestes20 = defaultdict(list)
    for i, geste, xs in d["gestes_20_11"]:
        for a in xs:
            gestes20[a].append("%s %s" % (geste, i))
    gestes_v3 = defaultdict(list)
    for i, a, *_ in g["relier"]:
        gestes_v3[a].append("relier %s" % i)
    for i, a, *_ in g["delier"]:
        gestes_v3[a].append("delier %s" % i)
    cs = sqlite3.connect("file:%s?mode=ro" % SOCLE.as_posix(), uri=True)
    pmax = cs.execute("select max(id) from passage").fetchone()[0]
    motif = {i: m for i, m in cs.execute("select id_unique, motif from verdict where passage=?", (pmax,))}
    cs.close()
    rows, cpt = [], Counter()
    for a in P340:
        b, k, s, n = INFO[a]
        ls = sorted(lignes_de.get(a, set()))
        dans = [x for x, on in (("V3", a in v3), ("132", a in c132), ("29", a in c29), ("a part", a in apart),
                                ("gestes 20/11", a in gestes20), ("gestes V3", a in gestes_v3)) if on]
        # QUI l'a jugee comme une copie : le fabricant de la V3 (au numero) -- seulement si elle est dans son perimetre
        par_numero = "fabricant de la V3 (8 endroits, au numero)" if (a in v3 or a in gestes_v3 or
                                                                     any(i in d["sort_ligne"] for i in ls)) else ""
        if par_numero:
            refaire = "NON -- la V3 rejouee par l'origine le 22/11 donne les memes gestes et le meme gel d'apres"
        elif dans:
            refaire = "NON -- jugee par l'origine (vraie piece) dans %s" % ", ".join(dans)
        else:
            refaire = "NON -- aucune decision rendue ne la touche ; le protocole la jugera comme vraie piece"
        cpt["reliees au gel" if ls else "sans ligne du gel"] += 1
        for x in dans:
            cpt["dans " + x] += 1
        cpt["jugee copie par le fabricant V3 (sans effet)" if par_numero else "jamais jugee copie"] += 1
        rows.append([a, b, k, s, n, " ".join(ls), len(ls), "; ".join(v3.get(a, [])), "; ".join(c132.get(a, [])),
                     "; ".join(c29.get(a, [])), "oui" if a in apart else "", "; ".join(gestes20.get(a, [])),
                     "; ".join(gestes_v3.get(a, [])),
                     " ".join(sorted({cl["avant"][i]["case"] for i in ls if i in cl["avant"]})),
                     " ".join(sorted({cl["apres"][i]["case"] for i in ls if i in cl["apres"]})),
                     " ".join(sorted({motif.get(i) or "?" for i in ls})), par_numero, refaire])
    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["piece", "bien", "genre", "etat", "numero_hektor", "lignes_du_gel", "nb_lignes_du_gel",
                    "dans_la_v3", "dans_les_132_coupes", "dans_les_29_faibles", "a_part", "gestes_du_gel_20_11",
                    "gestes_du_gel_v3", "case_de_ses_lignes_22_11_avant_v3", "case_de_ses_lignes_22_11_apres_v3",
                    "motif_protocole_v0", "jugee_comme_copie_par", "a_refaire"])
        w.writerows(rows)
    print("LES 340 : %d pieces ; lignes du gel distinctes : %d" % (len(P340), len({i for a in P340 for i in lignes_de.get(a, ())})))
    for k_, v_ in sorted(cpt.items()):
        print("   %-48s %4d" % (k_, v_))
    print("-> %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
