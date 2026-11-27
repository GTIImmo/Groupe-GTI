#!/usr/bin/env python
"""LE RESTE A VIDER, PAQUET « COPIE_SEULE » : LE PAQUET ENTIER, BIEN PAR BIEN.     23/11/2026

    python -u -X utf8 phase2/checks/protocole_paquet_copie_seule_2026-11-23.py [--passage 27]

SON MOT DU 23/11 (15) : « lire le paquet entier, bien par bien, sans a priori ; chercher LA CAUSE COMMUNE ; UNE REGLE PAR
FAMILLE, avec sa preuve nommee ET SON TEMOIN INVERSE ; la mesurer a blanc. »
LECTURE SEULE (le socle, l'image ; la coupe du bien rejouee EN MEMOIRE par K.couper_le_bien, comme le passage).
Pour chaque ligne : sa copie (genre, etat, date, montant, honoraires, origine, dossier) ; les VRAIES pieces du bien (et
pourquoi la coupe les laisse a part) ; ce que le gel donne a la ligne ; et la vraie piece « jumelle » de la copie s'il y en
a une -- meme genre, meme montant ou meme date.
ECRIT : notice/PROTOCOLE_PAQUET_COPIE_SEULE_PASSAGE_<P>_2026-11-23.csv. Rien d'autre.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402

RACINE = ICI.parents[1]


def dire(s: str = "") -> None:
    print(s, flush=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage", type=int)
    a = ap.parse_args()
    con = P.socle()
    pid = a.passage or con.execute("select max(id) from passage where image is not null").fetchone()[0]
    image = con.execute("select image from passage where id=?", (pid,)).fetchone()[0]
    V = {i: (num, json.loads(b), v, m, mt) for i, num, b, v, m, mt in con.execute(
        "select id_unique, num, biens, verdict, motif, motif_texte from verdict where passage=?", (pid,))}
    con.close()
    I = P.Image(P.IMAGES / image)
    D = I.D
    cibles = sorted((x[0], i) for i, x in V.items() if x[3] == "COPIE_SEULE")
    dire("LE PAQUET COPIE_SEULE -- passage %d, image %s : %d lignes" % (pid, image, len(cibles)))
    lignes, fam = [], Counter()
    for _num, i in cibles:
        num, biens, _v, _m, mt = V[i]
        b = biens[0]
        lignes_b = set(D.lignes_bien.get(b, set()))
        S = {q: I.pieces[q]["app_chaine_id"] for q in D.par_bien.get(b, [])}
        r = K.couper_le_bien(D, b, lignes_b, S, sorted(D.par_bien.get(b, [])), P.A_PART_PAR_DECISION)
        copies = [q for q in D.par_bien.get(b, []) if I.nature[q] != PC.VRAIE]
        vraies = [q for q in D.par_bien.get(b, []) if I.nature[q] == PC.VRAIE]
        sa_copie = [q for q in copies if any(q in ids for gl, ids in r["morceaux"].items() if i in gl)]
        gel = sorted(int(g["piece"]) for g in I.gel_par_ligne.get(i, []))
        desc = lambda q: "%d %s %s %s %s/hon %s ch %s %s" % (  # noqa: E731
            q, D.REG[q]["genre"], D.REG[q]["etat"], D.REG[q]["date"] or "?", D.REG[q]["montant"], D.REG[q]["hon"],
            S.get(q), I.pieces[q]["app_dossier_numero"])
        jumelles = []
        for c in sa_copie:
            for q in vraies:
                if D.REG[q]["genre"] == D.REG[c]["genre"] and (
                        (D.REG[q]["montant"] and D.REG[q]["montant"] == D.REG[c]["montant"])
                        or (D.REG[q]["date"] and D.REG[q]["date"] == D.REG[c]["date"])):
                    jumelles.append(q)
        a_qui = {q: ("a la ligne " + "+".join(sorted(r["va"][q]))) if q in r["va"] else ("A PART : " + r["apart"].get(q, "?"))
                 for q in vraies}
        vraies_au_gel = [q for q in gel if q in vraies]
        if not vraies:
            f = "AUCUNE VRAIE PIECE AU BIEN"
        elif jumelles and all(q in r["apart"] for q in jumelles):
            f = "SA JUMELLE VRAIE EST A PART"
        elif jumelles:
            f = "SA JUMELLE VRAIE VA A UNE AUTRE LIGNE"
        elif vraies_au_gel and all(q in r["apart"] for q in vraies_au_gel):
            f = "LE GEL LUI DONNE UNE VRAIE PIECE, A PART"
        else:
            f = "AUTRE"
        fam[f] += 1
        dire("\n%s (ligne %s) bien %s -- %s" % (i, num, b, f))
        dire("   sa copie : %s ; origine %s" % ("; ".join(desc(c) for c in sa_copie),
                                               ", ".join(str(I.pieces[c].get("transaction_origine")) for c in sa_copie)))
        dire("   gel de la ligne : %s" % gel)
        for q in vraies:
            dire("   vraie %s -> %s%s" % (desc(q), a_qui[q][:110], "   <- JUMELLE" if q in jumelles else ""))
        lignes.append({"id_unique": i, "ligne": num, "bien": b, "famille": f, "copie": " ".join(map(str, sa_copie)),
                       "copie_detail": "; ".join(desc(c) for c in sa_copie), "gel": " ".join(map(str, gel)),
                       "vraies": " | ".join("%s -> %s" % (desc(q), a_qui[q]) for q in vraies),
                       "jumelles": " ".join(map(str, jumelles)),
                       "autres_lignes_du_bien": " ".join(sorted(lignes_b - {i}))})
    dire("\nFAMILLES : %s" % dict(fam))
    out = RACINE / "notice" / ("PROTOCOLE_PAQUET_COPIE_SEULE_PASSAGE_%d_2026-11-23.csv" % pid)
    with out.open("w", encoding="utf-8", newline="") as f_:
        w = csv.DictWriter(f_, fieldnames=list(lignes[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    dire("-> %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
