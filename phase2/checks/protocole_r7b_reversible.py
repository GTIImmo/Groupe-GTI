#!/usr/bin/env python3
"""R7b SE DEFAIT -- LA PREUVE PAR LE VRAI CHAINAGE -- chantier classeur, ㉑bis, 22/11/2026 (soir).

Son mot (reponses au rapport 21 bis, point 2) : « R7b QUI FIGE 3QZ4DAD1 (VACHER PEYRARD) ET ARF57GC5 (THOURY) : OUI.
  A DEUX CONDITIONS : a) C'est REVERSIBLE -- figer n'est pas graver. b) CES DEUX LIGNES RESTENT DANS LE RESTE A VIDER. »

⛔ LECTURE SEULE. Deux rejeux du VRAI chainage sur la copie de l'image (protocole_portes.rejeu_en_cache) :
  E  = le brouillon du protocole, tel qu'il serait pose ;
  E' = le MEME brouillon, SANS ses lignes « protocole_mise_de_cote » -- c'est exactement le geste de defaire R7b :
       retirer ces lignes du fichier. Rien d'autre.
CE QU'IL PROUVE :
  a) figer ne change RIEN aux dossiers figes : dans E, chacun est le dossier de l'image, piece pour piece ;
  b) defaire ne touche QUE ces dossiers et ceux que leur liberte rendrait au chainage : tout le reste est identique ;
  c) ce que le chainage ferait de chacun s'il etait libre (E'), et l'etiquette (le NUMERO) que la nuit lui donnerait ;
  d) les lignes du classeur qui portent ces dossiers : leur verdict au passage (3QZ4DAD1 et ARF57GC5 doivent rester
     EN ATTENTE -- « figees ne veut pas dire reglees »).
USAGE : python -u phase2/checks/protocole_r7b_reversible.py [--passage P]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import coupe_preuve_interne as K  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402

SES_DEUX = {"3QZ4DAD1": "VACHER PEYRARD", "ARF57GC5": "THOURY"}
ENV = {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}


def dire(s: str = "") -> None:
    print(s, flush=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--passage", type=int, default=20)
    a = ap.parse_args()
    pid = a.passage
    con = P.socle()
    image = con.execute("select image from passage where id=?", (pid,)).fetchone()[0]
    V = {i: (v, m) for i, v, m in con.execute("select id_unique, verdict, motif from verdict where passage=?", (pid,))}
    con.close()
    I = P.Image(P.IMAGES / image)
    brouillon = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % pid)
    lignes = brouillon.read_text(encoding="utf-8").splitlines()
    mdc_l = [l_ for l_ in lignes if ";protocole_mise_de_cote;" in l_]
    sans = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d_SANS_R7b.csv" % pid)
    sans.write_text("\n".join(l_ for l_ in lignes if ";protocole_mise_de_cote;" not in l_) + "\n", encoding="utf-8")
    dire("R7b SE DEFAIT -- passage %d, image %s : le brouillon a %d lignes, dont %d « mise de cote » ; on les retire "
         "(-> %s)" % (pid, image, len(lignes), len(mdc_l), sans.name))
    chE, _ = PO.rejeu_en_cache("E", image, brouillon, ENV, False)
    chS, resS = PO.rejeu_en_cache("E", image, sans, ENV, True)
    lab_img = {q: I.pieces[q]["app_dossier_uuid"] for q in I.pieces}
    num_de = {I.pieces[q]["app_dossier_uuid"]: I.pieces[q]["app_dossier_numero"] for q in I.pieces
              if I.pieces[q]["app_dossier_uuid"]}
    mImg = PO.membres({q: I.pieces[q]["app_chaine_id"] for q in I.pieces})
    mE, mS = PO.membres(chE), PO.membres(chS)
    labE, labS = K.pose_de_nuit(lab_img, chE), K.pose_de_nuit(lab_img, chS)
    MDC = json.loads((P.DOSSIER / ("mises_de_cote_passage_%d.json" % pid)).read_text(encoding="utf-8"))
    groupes = {}
    for q, x in MDC.items():
        groupes.setdefault(frozenset(x["groupe"]), x)
    dire("   %d piece(s) mise(s) de cote, %d dossier(s) figes" % (len(MDC), len(groupes)))
    lignes_de_piece = {}
    for i_, gs in I.gel_par_ligne.items():
        for g in gs:
            lignes_de_piece.setdefault(g["piece"], set()).add(i_)

    def num(l_) -> str:
        return num_de.get(l_) or ("NEUF" if str(l_).startswith("NEUVE") else str(l_))
    a_ok, rapport = 0, []
    for g_, x in sorted(groupes.items(), key=lambda kv: min(kv[0])):
        q0 = min(g_)
        img = frozenset(mImg[I.pieces[q0]["app_chaine_id"]])
        dansE = frozenset(mE[chE[q0]])
        figes_tel_quel = dansE == img == g_ and all(labE[q] == x["ancien_uuid"] for q in g_)
        a_ok += figes_tel_quel
        libre = sorted({frozenset(mS[chS[q]]) for q in g_}, key=min)
        rapport.append({"dossier": x["ancien_numero"], "bien": x["bien"], "pieces": sorted(g_),
                        "fige_tel_quel_dans_E": figes_tel_quel,
                        "libre_E_prime": [{"pieces": sorted(m), "numero": num(labS[min(m)])} for m in libre],
                        "lignes": sorted({i_ for q in g_ for i_ in lignes_de_piece.get(q, ())})})
        dire("   %s (bien %s) %s : fige dans E %s ; LIBRE (E') -> %s" % (
            x["ancien_numero"], x["bien"], sorted(g_), "TEL QUEL" if figes_tel_quel else "⛔ CHANGE",
            " | ".join("%s = %s" % (" ".join(map(str, sorted(m))), num(labS[min(m)])) for m in libre)))
    # b) defaire ne touche que ces dossiers
    differe = sorted(q for q in chE if frozenset(mE[chE[q]]) != frozenset(mS[chS[q]]))
    hors = sorted(q for q in differe if not any(q in g_ or frozenset(mS[chS[q]]) & g_ for g_ in groupes))
    lab_diff = sorted(q for q in labE if labE[q] != labS[q])
    dire("   a) FIGER NE CHANGE RIEN : %d dossier(s) sur %d sont, dans E, le dossier de l'image piece pour piece, avec "
         "leur numero" % (a_ok, len(groupes)))
    dire("   b) DEFAIRE (retirer les %d lignes) : %d piece(s) changent de dossier entre E et E', dont %d HORS des dossiers "
         "figes ; %d etiquette(s) changent" % (len(mdc_l), len(differe), len(hors), len(lab_diff)))
    # d) les lignes qui portent ces dossiers
    lig = sorted({i_ for g_ in groupes for q in g_ for i_ in lignes_de_piece.get(q, ())})
    for i in sorted(set(lig) | set(SES_DEUX)):
        v = V.get(i, ("ABSENTE", ""))
        dire("   d) ligne %s%s : %s%s" % (i, (" (%s)" % SES_DEUX[i]) if i in SES_DEUX else "", v[0],
                                        (" -- motif %s" % v[1]) if v[1] else ""))
    res = {"passage": pid, "image": image, "lignes_mise_de_cote": mdc_l, "figes_tel_quel": a_ok,
           "dossiers": rapport, "pieces_qui_changent": differe, "hors_des_figes": hors,
           "etiquettes_qui_changent": lab_diff,
           "ses_deux": {i: V.get(i, ("ABSENTE", ""))[0] for i in SES_DEUX}, "compte_rendu_E_prime":
               {k: v for k, v in resS.items() if str(k).startswith("[X]")}}
    (P.DOSSIER / ("r7b_reversible_passage_%d.json" % pid)).write_text(json.dumps(res, ensure_ascii=False, indent=1,
                                                                                default=str), encoding="utf-8")
    deux_ok = all(V.get(i, ("",))[0] == "ATTENTE" for i in SES_DEUX)
    dire("VERDICT : figer %s . defaire %s . ses deux lignes %s" % (
        "ne change rien (%d/%d)" % (a_ok, len(groupes)) if a_ok == len(groupes) else "⛔ CHANGE",
        "ne touche rien d'autre" if not hors else "⛔ touche %d piece(s) ailleurs" % len(hors),
        "EN ATTENTE (reste a vider)" if deux_ok else "⛔ PAS EN ATTENTE"))
    return 0 if a_ok == len(groupes) and not hors and deux_ok else 1


if __name__ == "__main__":
    sys.exit(main())
