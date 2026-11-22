#!/usr/bin/env python3
"""LES PIECES QUE LA REGLE G2 DEPLACE HORS DES LIGNES TRANCHEES -- chantier classeur, ⑳, 22/11/2026.

Son mot (reponses au rapport 21, § 3) : « G2 reste en attente : lis d'abord ses 480 pieces. »

⛔ LECTURE SEULE. Les deux rejeux du VRAI chainage deja en cache (protocole_portes.py --rejeu A et --rejeu B, sur la
copie de l'image) : A = la nuit telle qu'elle tourne, B = A + G2. Rien en base, rien dans le Sheet, rien chez Hektor.

CE QU'IL DIT, pour chaque piece qui change de dossier sous G2 dans un bien SANS ligne tranchee :
  . le bien a-t-il des lignes de son classeur (en attente) ou AUCUNE ;
  . ce que G2 fait au dossier (le coupe en deux, en reunit, ...), par la composition avant / apres ;
  . l'etiquette (et le NUMERO) que la pose de nuit donnerait a chaque piece : gardee, ou NEUVE ;
  . l'offre acceptee datee qui fait s'abstenir la regle D, et les acquereurs des deux cotes (ce que G2 lit).
USAGE : python -u phase2/checks/protocole_g2_ailleurs.py [--passage P]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402


def dire(s: str = "") -> None:
    print(s, flush=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage", type=int)
    a = ap.parse_args()
    con = P.socle()
    pid = a.passage or con.execute("select max(id) from passage").fetchone()[0]
    image = con.execute("select image from passage where id=?", (pid,)).fetchone()[0]
    V = {i: (v, json.loads(bs)) for i, v, bs in con.execute("select id_unique, verdict, biens from verdict where "
                                                             "passage=?", (pid,))}
    con.close()
    I = P.Image(P.IMAGES / image)
    chA, _ = PO.rejeu_en_cache("A", image, PO.FICHIER_DET_PROD, PO.ETEINTS, False)
    chB, _ = PO.rejeu_en_cache("B", image, PO.FICHIER_DET_PROD, {"APP_CHAINAGE_GARDE_G2": "1",
                                                                  "APP_CHAINAGE_DETACHEMENTS": "0"}, False)
    bien_de = {q: str(I.pieces[q]["hektor_annonce_id"]) for q in I.pieces}
    biens_t = {bs[0] for v, bs in V.values() if v == "TRANCHEE"}
    lignes_du_bien = defaultdict(set)
    for i, (v, bs) in V.items():
        for b in bs:
            lignes_du_bien[b].add(i)
    bouge = sorted(q for q in chA if chA[q] != chB.get(q) and bien_de[q] not in biens_t)
    mA, mB = PO.membres(chA), PO.membres(chB)
    lab_img = {q: I.pieces[q]["app_dossier_uuid"] for q in I.pieces}
    num_de = {I.pieces[q]["app_dossier_uuid"]: I.pieces[q]["app_dossier_numero"] for q in I.pieces
              if I.pieces[q]["app_dossier_uuid"]}
    labB = K.pose_de_nuit(lab_img, chB)
    dire("G2 AILLEURS -- passage %d, image %s : %d pieces changent de dossier sous G2 dans un bien SANS ligne tranchee"
         % (pid, image, len(bouge)))
    par_bien = defaultdict(list)
    for q in bouge:
        par_bien[bien_de[q]].append(q)
    sorte = Counter()
    lignes_csv, gestes = [], Counter()
    lab_change = Counter()
    for b, qs in sorted(par_bien.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0):
        ls = sorted(lignes_du_bien.get(b, set()))
        att = [i for i in ls if V[i][0] == "ATTENTE"]
        k = "des lignes de son classeur, toutes EN ATTENTE" if att else "AUCUNE ligne dans son classeur"
        sorte[k] += 1
        avant = {frozenset(mA[chA[q]]) for q in qs}
        touchees = set().union(*avant) | set(qs)
        apres = {frozenset(mB[chB[q]]) for q in touchees}
        g = "COUPE en %d" % len(apres) if len(avant) < len(apres) else (
            "REUNIT %d en %d" % (len(avant), len(apres)) if len(avant) > len(apres) else "RECOMPOSE %d dossier(s)"
            % len(avant))
        gestes[g.split()[0]] += 1
        for q in sorted(qs):
            p = I.pieces[q]
            nouveau = labB[q]
            chg = "GARDE" if nouveau == lab_img[q] else ("NEUVE" if str(nouveau).startswith("NEUVE") else "AUTRE")
            lab_change[chg] += 1
            lignes_csv.append([b, k, "+".join(ls) or "-", g, q, PC.nature(q, p["transaction_origine"],
                                                                      p["hektor_affaire_id"]),
                               p["kind"], p["state"], p["date"], p["montant"],
                               " ".join(P.noms(p["acquereurs_json"]))[:60],
                               num_de.get(lab_img[q], "?"), " ".join(map(str, sorted(mA[chA[q]]))),
                               " ".join(map(str, sorted(mB[chB[q]]))), chg,
                               num_de.get(nouveau) or ("NEUF" if chg == "NEUVE" else "?")])
    dire("   %d biens : %s" % (len(par_bien), " . ".join("%s %d" % kv for kv in sorte.most_common())))
    dire("   le geste de G2 sur ces biens : %s" % " . ".join("%s %d" % kv for kv in gestes.most_common()))
    dire("   l'etiquette (le numero) de ces %d pieces dans l'app : %s" % (len(bouge), " . ".join(
        "%s %d" % kv for kv in lab_change.most_common())))
    sortie = P.NOTICE / ("PROTOCOLE_G2_LES_%d_PIECES_HORS_DES_LIGNES_TRANCHEES_2026-11-22.csv" % len(bouge))
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["bien", "son_classeur", "ses_lignes", "ce_que_G2_fait", "piece", "nature", "genre", "etat", "date",
                    "montant", "acquereurs_chez_hektor", "numero_aujourdhui", "dossier_aujourdhui",
                    "dossier_sous_G2", "etiquette", "numero_sous_G2"])
        w.writerows(lignes_csv)
    dire("-> %s" % sortie)
    ex = [b for b in par_bien][:3]
    for b in ex:
        dire("   ex. bien %s (%s) : pieces %s" % (b, "+".join(sorted(lignes_du_bien.get(b, set()))) or "aucune ligne",
                                                 par_bien[b]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
