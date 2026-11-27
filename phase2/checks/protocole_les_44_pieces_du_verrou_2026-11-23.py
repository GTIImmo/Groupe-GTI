#!/usr/bin/env python
"""LE RESTE A VIDER, DEUXIEME MOTIF : LES 69 LIGNES DU VERROU, OU PLUTOT SES 44 PIECES.     23/11/2026

    python -u -X utf8 phase2/checks/protocole_les_44_pieces_du_verrou_2026-11-23.py [--passage 23]

SON MOT DU 23/11 (12), § 2 : « 69 lignes bloquees, mais par 44 PIECES seulement [...] LES 44 SE RANGENT EN TROIS
FAMILLES. Donc TROIS regles, pas 69 cas [...] LE CHEMIN N'EST PAS DE DESSERRER LE VERROU -- c'est de TRANCHER LES 44. [...]
Le temoin inverse de tes trois regles est donc toujours le meme : une piece qu'une preuve POURRAIT encore rattacher doit
CONTINUER a bloquer. »

CE QU'IL FAIT -- LECTURE SEULE (le socle, l'image ; la coupe du bien rejouee EN MEMOIRE par K.couper_le_bien, comme le
passage) : pour chaque piece qui retient une ligne au verrou E7 --
  . sa famille, lue dans le motif du passage : PLUSIEURS (prix + honoraires de plusieurs acheteurs) / AUCUNE_LIGNE (prix
    + honoraires connus, ceux d'aucune ligne) / HON_INCONNUS (ni date utilisable, ni honoraires) / AUTRE ;
  . ce qu'elle est (genre, etat, date du registre, montant, honoraires) et OU elle vit (son dossier d'aujourd'hui) ;
  . les lignes pour lesquelles elle est « possible » (dates compatibles), celles qu'elle retient, et si son dossier
    d'aujourd'hui est celui d'une de ces lignes ;
  . ce qu'une preuve pourrait encore en dire : une date au jour exact sur une case d'une ligne ? un prix + honoraires
    d'une ligne ? -- la question de son temoin inverse.
ECRIT : notice/PROTOCOLE_LES_44_PIECES_DU_VERROU_PASSAGE_<P>_2026-11-23.csv. Rien d'autre.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
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


def famille(texte: str) -> str:
    if "plusieurs acheteurs" in texte:
        return "PLUSIEURS"
    if "ceux d'aucune ligne" in texte:
        return "AUCUNE_LIGNE"
    if "honoraires inconnus" in texte:
        return "HON_INCONNUS"
    return "AUTRE"


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
    verrou = {i: x for i, x in V.items() if x[3] == "VERROU_PIECE_PLUS_PETITE"}
    retient = defaultdict(set)
    for i, x in verrou.items():
        m_ = re.search(r"a part et plus petites : (.*)$", x[4])
        for p_ in re.findall(r"(\d+) \(", m_.group(1)):
            retient[int(p_)].add(i)
    biens = sorted({x[1][0] for x in verrou.values()})
    dire("LES 44 -- passage %d, image %s : %d lignes au verrou, %d pieces qui les retiennent, %d biens" % (
        pid, image, len(verrou), len(retient), len(biens)))
    lignes_csv, fam_cpt = [], Counter()
    par_fam = defaultdict(list)
    for b in biens:
        lignes_b = set(D.lignes_bien.get(b, set()))
        S = {q: I.pieces[q]["app_chaine_id"] for q in D.par_bien.get(b, [])}
        X = sorted(D.par_bien.get(b, []))
        r = K.couper_le_bien(D, b, lignes_b, S, X, P.A_PART_PAR_DECISION)
        ligne_du_dossier = defaultdict(set)          # chaine -> les lignes dont un morceau y a une piece
        for gl, ids in r["morceaux"].items():
            for q in ids:
                for i in gl:
                    ligne_du_dossier[S.get(q)].add(i)
        for p_ in sorted(q for q in retient if q in S):
            reg, piece = D.REG[p_], I.pieces[p_]
            possibles = sorted(set().union(*r["possibles"][p_])) if r["possibles"].get(p_) else []
            texte = r["apart"].get(p_, "")
            f = famille(texte)
            fam_cpt[f] += 1
            # ce qu'une preuve pourrait encore en dire
            date_case = []
            for i in sorted(lignes_b):
                for c in K.COLS_DATE.get(reg["genre"], []):
                    if reg["date"] and K.d_sheet(D.case(i, c)) == reg["date"]:
                        date_case.append("%s/%s" % (i, c))
            ph = sorted(i for i in lignes_b if D.touche_ph(p_, i))
            dossier_de = sorted(ligne_du_dossier.get(S.get(p_), set()))
            # UNE PREUVE POURRAIT-ELLE ENCORE VENIR ? une ligne possible dont la case de date de son genre est VIDE (on
            #   pourrait la remplir de sa date) -- seulement si la piece a une date ; sans date, aucune date ne la prouvera
            cases_vides = sorted(i for i in possibles if reg["date"]
                                 and all(not D.case(i, c).strip() for c in K.COLS_DATE.get(reg["genre"], [])))
            x = {"piece": p_, "bien": b, "famille": f, "genre": reg["genre"], "etat": reg["etat"],
                 "date": str(reg["date"] or ""), "montant": reg["montant"], "honoraires": reg["hon"],
                 "dossier": piece["app_dossier_numero"], "chaine": S.get(p_),
                 "origine": piece.get("transaction_origine") or "", "nature": I.nature[p_],
                 "lignes_possibles": " ".join(possibles), "lignes_retenues": " ".join(sorted(retient[p_])),
                 "lignes_du_meme_dossier": " ".join(dossier_de),
                 "dans_le_dossier_d_une_ligne_possible": " ".join(sorted(set(dossier_de) & set(possibles))),
                 "ligne_possible_a_case_de_date_vide": " ".join(cases_vides),
                 "date_au_jour_exact_sur": " ".join(date_case), "prix_hon_de": " ".join(ph), "pourquoi_a_part": texte}
            lignes_csv.append(x)
            par_fam[f].append(x)
    dire("   familles : %s" % dict(fam_cpt))
    for f in ("PLUSIEURS", "AUCUNE_LIGNE", "HON_INCONNUS", "AUTRE"):
        xs = par_fam.get(f, [])
        if not xs:
            continue
        dire("\n=== %s : %d piece(s), %d ligne(s) retenue(s)" % (f, len(xs), len({i for x in xs
                                                                              for i in x["lignes_retenues"].split()})))
        dire("   genres %s . etats %s . avec une date au registre %d . dans le dossier d'une ligne qu'elle retient %d"
             " . une date au jour exact sur une case %d . le prix + honoraires d'une ligne %d" % (
                 dict(Counter(x["genre"] for x in xs)), dict(Counter(x["etat"] for x in xs)),
                 sum(1 for x in xs if x["date"]), sum(1 for x in xs if set(x["lignes_du_meme_dossier"].split())
                                                      & set(x["lignes_retenues"].split())),
                 sum(1 for x in xs if x["date_au_jour_exact_sur"]), sum(1 for x in xs if x["prix_hon_de"])))
        dire("   dans le dossier d'une ligne POSSIBLE %d . une ligne possible a sa case de date VIDE (une preuve pourrait "
             "venir) %d . AUCUNE preuve possible (ni date exacte, ni prix + honoraires, ni case vide a remplir) ET hors "
             "du dossier de toute ligne possible : %d" % (
                 sum(1 for x in xs if x["dans_le_dossier_d_une_ligne_possible"]),
                 sum(1 for x in xs if x["ligne_possible_a_case_de_date_vide"]),
                 sum(1 for x in xs if not (x["date_au_jour_exact_sur"] or x["prix_hon_de"]
                                           or x["ligne_possible_a_case_de_date_vide"]
                                           or x["dans_le_dossier_d_une_ligne_possible"]))))
        for x in xs:
            dire("   %s bien %s %s %s du %s, %s / hon %s ; dossier %s ; possible pour %s ; retient %s ; meme dossier "
                 "que %s ; date exacte sur %s ; prix+hon de %s" % (
                     x["piece"], x["bien"], x["genre"], x["etat"], x["date"] or "?", x["montant"], x["honoraires"],
                     x["dossier"], x["lignes_possibles"] or "-", x["lignes_retenues"], x["lignes_du_meme_dossier"] or "-",
                     x["date_au_jour_exact_sur"] or "-", x["prix_hon_de"] or "-"))
    out = RACINE / "notice" / ("PROTOCOLE_LES_44_PIECES_DU_VERROU_PASSAGE_%d_2026-11-23.csv" % pid)
    with out.open("w", encoding="utf-8", newline="") as f_:
        w = csv.DictWriter(f_, fieldnames=list(lignes_csv[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(lignes_csv)
    dire("\n-> %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
