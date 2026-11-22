#!/usr/bin/env python
"""LES LIGNES EN ATTENTE GARDENT-ELLES LE NUMERO QU'ELLES PORTENT ? -- chantier classeur, 22/11 soir.

SON MOT (reponses 21 ter, demande A) : « AU MOMENT D'ECRIRE, EST-CE QUE TU LAISSES EN PLACE LE NUMERO QU'ELLES PORTENT
  AUJOURD'HUI, OU EST-CE QUE TU L'EFFACES ? Ma ligne 40 affiche D2025-0107 aujourd'hui. Elle ne doit pas se retrouver
  VIDE parce qu'on n'a pas encore tranche son cas. » Ses trois premieres a verifier : lignes 40, 105 et 311.

LECTURE SEULE (l'image figee, le cache du protocole). Pour chaque ligne EN ATTENTE du passage, trois endroits ou un
numero peut vivre, et ce que l'ecriture leur fait :
  1. LA CASE A DU SHEET : ce qu'elle porte aujourd'hui. L'ecrivain ne remplit qu'une case VIDE, jamais une ligne hors
     de la vague, et saute une case deja remplie (« on n'ecrase jamais ») -- il n'a AUCUN geste qui vide une case, sauf
     le retour arriere, qui ne vide que NOTRE valeur.
  2. LE REGISTRE (app_affaire_ledger) : l'etiquette et le numero des pieces du gel de la ligne AUJOURD'HUI (l'image),
     et A L'ARRIVEE (le chainage du rejeu E du passage -- le brouillon de detachements du protocole pose -- puis la
     pose de nuit). C'est le seul endroit que l'ecriture peut deplacer : par les portes des AUTRES lignes, si l'une
     d'elles coupe un dossier qu'une ligne en attente partage.
  3. app_classeur_avis (C9, 16/11) : le numero de la photo du 16/11, pour les lignes des 2 560. L'ecriture n'y touche
     pas (aucun ecrivain de cette table dans le protocole).

VERDICT d'une ligne : GARDE (chaque piece du gel garde son etiquette d'aujourd'hui, donc son numero) . CHANGE (nommee,
piece par piece) . SANS_PIECE (le gel ne la relie a aucune piece : il n'y a pas de numero a perdre).

USAGE : python -u phase2/checks/protocole_en_attente_garde_son_numero.py [--passage N]
CODES : 0 toutes GARDE (ou sans piece) . 1 au moins une CHANGE (nommee) . 2 pas pu lire
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import coupe_preuve_interne as K  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402

PREMIERES = ("40", "105", "311")


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
    V = {i: (num, v, m, mt) for i, num, v, m, mt in con.execute(
        "select id_unique, num, verdict, motif, motif_texte from verdict where passage=?", (pid,))}
    con.close()
    attente = {i: x for i, x in V.items() if x[1] != "TRANCHEE"}
    I = P.Image(P.IMAGES / image)
    brouillon = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % pid)
    try:
        chE, _ = PO.rejeu_en_cache("E", image, brouillon, {"APP_CHAINAGE_GARDE_G2": "0",
                                                           "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
    except SystemExit as e:
        dire(str(e))
        return 2
    lab_img = {q: I.pieces[q]["app_dossier_uuid"] for q in I.pieces}
    num_de = {I.pieces[q]["app_dossier_uuid"]: I.pieces[q]["app_dossier_numero"] for q in I.pieces
              if I.pieces[q]["app_dossier_uuid"]}
    labE = K.pose_de_nuit(lab_img, chE)
    # les numeros neufs : ceux de l'outil des numeros neufs (passage 20), valables si le chainage d'arrivee est le meme
    f_nn = P.DOSSIER / "numeros_neufs_passage_20.json"
    numero_neuf = json.loads(f_nn.read_text(encoding="utf-8"))["numero_neuf"] if f_nn.exists() else {}
    if pid != 20 and f_nn.exists():
        ch20, _ = PO.rejeu_en_cache("E", image, P.DOSSIER / "brouillon_detachements_protocole_passage_20.csv",
                                    {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
        if ch20 != chE:
            numero_neuf = {}
            dire("   ⚠ le chainage d'arrivee du passage %d differe de celui du 20 : numeros neufs non repris" % pid)
    f_av = P.DOSSIER / "avis" / ("avis_contre_passage_%d.json" % pid)
    avis = {r[0]: r[2] for r in json.loads(f_av.read_text(encoding="utf-8"))["lignes"]} if f_av.exists() else {}

    def numero(l_) -> str:
        if not l_:
            return "-"
        if str(l_).startswith("NEUVE"):
            return numero_neuf.get(l_, "NEUF")
        return num_de.get(l_) or "?"

    dire("LES LIGNES EN ATTENTE ET LEUR NUMERO -- passage %d, image %s : %d lignes en attente sur %d" % (
        pid, image, len(attente), len(V)))
    sortie_l, verdicts, case_a = [], Counter(), Counter()
    for i, (num, v, m, mt) in sorted(attente.items(), key=lambda kv: kv[1][0] or 0):
        row = I.sheet["par_id"][i][0]["row"] if i in I.sheet["par_id"] else [""] * 38
        a_auj = str(row[0] if row and row[0] is not None else "").strip()
        case_a["remplie" if a_auj else "vide"] += 1
        pieces = sorted({int(g["piece"]) for g in I.gel_par_ligne.get(i, [])})
        if not pieces:
            verdict, detail = "SANS_PIECE", "le gel ne la relie a aucune piece"
        else:
            bouge = [q for q in pieces if labE.get(q) != lab_img.get(q)]
            if bouge:
                verdict = "CHANGE"
                detail = " ; ".join("%d : %s -> %s" % (q, numero(lab_img.get(q)), numero(labE.get(q))) for q in bouge)
            else:
                verdict, detail = "GARDE", ""
        verdicts[verdict] += 1
        auj = sorted({numero(lab_img.get(q)) for q in pieces})
        arr = sorted({numero(labE.get(q)) for q in pieces})
        sortie_l.append([i, num, "%s (%s)" % (v, m), " ".join(map(str, pieces)), " + ".join(auj) or "-",
                         " + ".join(arr) or "-", verdict, detail, a_auj or "(vide)", avis.get(i, "")])
    for r in sortie_l:
        if str(r[1]) in PREMIERES:
            dire("   SA LIGNE %s (%s) : %s ; pieces %s ; aujourd'hui %s -> a l'arrivee %s : %s ; case A %s ; avis du "
                 "16/11 %s" % (r[1], r[0], r[2], r[3], r[4], r[5], r[6], r[8], r[9] or "-"))
    dire("   VERDICT : %s" % " . ".join("%s %d" % kv for kv in sorted(verdicts.items())))
    dire("   LA CASE A DU SHEET de ces lignes, aujourd'hui : %s -- l'ecrivain ne touche ni aux unes (hors vague) ni aux "
         "autres (« on n'ecrase jamais »)" % " . ".join("%s %d" % kv for kv in sorted(case_a.items())))
    des_2560 = [r for r in sortie_l if r[9]]
    dire("   DONT LES LIGNES DES 2 560 (un numero dans app_classeur_avis) : %d -- %s" % (len(des_2560), " . ".join(
        "%s %d" % kv for kv in sorted(Counter(r[6] for r in des_2560).items()))))
    avis_diff = [r for r in des_2560 if r[9] not in r[4].split(" + ")]
    if avis_diff:
        dire("   dont le numero du 16/11 n'est plus celui d'aujourd'hui : %d -> %s" % (len(avis_diff), " ".join(
            "%s:%s->%s" % (r[1], r[9], r[4]) for r in avis_diff[:12])))
    for r in sortie_l:
        if r[6] == "CHANGE":
            dire("   ⛔ CHANGE : ligne %s (%s) %s -- %s" % (r[1], r[0], r[2], r[7]))
    sortie = P.NOTICE / ("PROTOCOLE_LES_LIGNES_EN_ATTENTE_GARDENT_LEUR_NUMERO_PASSAGE_%d_2026-11-22.csv" % pid)
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "ligne_du_sheet", "le_protocole", "pieces_du_gel", "numero_aujourdhui",
                    "numero_a_l_arrivee", "verdict", "ce_qui_change", "case_A_du_sheet_aujourdhui",
                    "numero_du_16_11_app_classeur_avis"])
        w.writerows(sorted(sortie_l, key=lambda r: (r[6] != "CHANGE", not r[9], r[1] or 0)))
    dire("   -> %s" % sortie)
    (P.DOSSIER / ("en_attente_numero_passage_%d.json" % pid)).write_text(json.dumps(
        {"passage": pid, "verdicts": dict(verdicts), "case_a": dict(case_a), "lignes": sortie_l}, ensure_ascii=False,
        indent=1), encoding="utf-8")
    return 1 if verdicts["CHANGE"] else 0


if __name__ == "__main__":
    sys.exit(main())
