#!/usr/bin/env python
"""LE RESTE A VIDER, PAQUETS « SES_PIECES_A_PART » (29) ET « AUCUNE_PIECE_PROUVEE » (28) : LE PAQUET ENTIER.   23/11/2026

    python -u -X utf8 phase2/checks/protocole_paquets_a_part_et_sans_preuve_2026-11-23.py [--passage 28]

SON MOT DU 23/11 (15) : lire le paquet entier, chercher la cause commune, une regle par famille avec son temoin inverse.
LECTURE SEULE (le socle, l'image ; la coupe rejouee en memoire). Pour chaque ligne, chaque vraie piece du bien qu'elle
pourrait tenir (son gel ; a defaut, tout le bien) : genre, etat, date, montant, honoraires ; l'ECART EN JOURS entre la date
de la piece et la case de la ligne de son genre ; montant contre « Prix » et « Prix + Commission » ; honoraires contre
« Commission TTC » ; les autres lignes du bien ; ce que la coupe en dit.
ECRIT : notice/PROTOCOLE_PAQUETS_A_PART_ET_SANS_PREUVE_PASSAGE_<P>_2026-11-23.csv. Rien d'autre.
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


def nb(s):
    try:
        return round(float(str(s).replace(" ", "").replace(",", ".")))
    except ValueError:
        return None


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
    out = []
    for motif in ("SES_PIECES_A_PART", "AUCUNE_PIECE_PROUVEE"):
        cibles = sorted((x[0], i) for i, x in V.items() if x[3] == motif)
        resume = Counter()
        dire("\n===== %s : %d lignes" % (motif, len(cibles)))
        for _n, i in cibles:
            num, biens, _v, _m, mt = V[i]
            b = biens[0]
            lignes_b = set(D.lignes_bien.get(b, set()))
            S = {q: I.pieces[q]["app_chaine_id"] for q in D.par_bien.get(b, [])}
            r = K.couper_le_bien(D, b, lignes_b, S, sorted(D.par_bien.get(b, [])), P.A_PART_PAR_DECISION)
            gel = {int(g["piece"]) for g in I.gel_par_ligne.get(i, [])}
            vraies = [q for q in sorted(D.par_bien.get(b, [])) if I.nature[q] == PC.VRAIE]
            regard = [q for q in vraies if q in gel] or vraies
            prix, com = nb(D.case(i, "Prix")), nb(D.case(i, "Commission TTC"))
            dire("%s (ligne %s) bien %s : Prix %s . Commission %s . Etat %r . Offre %r . Compromis %r . Vente fixee %r ; "
                 "gel %s ; autres lignes %s" % (i, num, b, prix, com, D.case(i, "Etat Actuel"), D.case(i, "Offre Achat"),
                                                D.case(i, "Compromis"), D.case(i, "Vente Fixée"), sorted(gel),
                                                sorted(lignes_b - {i})))
            for q in regard:
                reg = D.REG[q]
                ecarts = []
                for c in K.COLS_DATE.get(reg["genre"], []):
                    d_case = K.d_sheet(D.case(i, c))
                    if d_case and reg["date"]:
                        ecarts.append((c, (reg["date"] - d_case).days))
                m = reg["montant"]
                dit = []
                if m is not None and prix is not None and round(m) == prix:
                    dit.append("montant = Prix")
                if m is not None and prix is not None and com is not None and round(m) == prix + com:
                    dit.append("montant = Prix + Commission")
                if reg["hon"] is not None and com is not None and round(reg["hon"]) == com:
                    dit.append("honoraires = Commission")
                ou = ("a " + "+".join(sorted(r["va"][q]))) if q in r["va"] else ("A PART : " + r["apart"].get(q, "?"))
                gel_autres = sorted(x for x in I.gel_par_piece.get(q, []) if x != i)
                dire("   %d %s %s %s %s/hon %s | ecart(s) %s | %s | gel d'autres lignes %s | %s" % (
                    q, reg["genre"], reg["etat"], reg["date"] or "?", m, reg["hon"], ecarts or "-", ", ".join(dit) or "-",
                    gel_autres or "-", ou[:90]))
                for c_, d_ in ecarts:
                    resume["ecart %s" % ("0" if d_ == 0 else "1-7 j" if abs(d_) <= 7 else "8-31 j" if abs(d_) <= 31
                                         else "> 31 j")] += 1
                for x in dit:
                    resume[x] += 1
                out.append({"motif": motif, "id_unique": i, "ligne": num, "bien": b, "piece": q, "genre": reg["genre"],
                            "etat": reg["etat"], "date": str(reg["date"] or ""), "montant": m, "honoraires": reg["hon"],
                            "prix_ligne": prix, "commission_ligne": com, "ecarts_jours": " ".join("%s:%d" % e for e in ecarts),
                            "ce_qui_colle": ", ".join(dit), "au_gel_de_la_ligne": q in gel,
                            "au_gel_d_autres": " ".join(gel_autres), "coupe": ou})
        dire("RESUME %s : %s" % (motif, dict(resume)))
    f = RACINE / "notice" / ("PROTOCOLE_PAQUETS_A_PART_ET_SANS_PREUVE_PASSAGE_%d_2026-11-23.csv" % pid)
    with f.open("w", encoding="utf-8", newline="") as f_:
        w = csv.DictWriter(f_, fieldnames=list(out[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(out)
    dire("-> %s" % f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
