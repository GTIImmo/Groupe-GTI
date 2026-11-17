#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ALLEGER LE DOSSIER, ET AFFINER LA RECOMMANDATION.               18/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\alleger_le_dossier_2026-11-18.py

⛔ LECTURE SEULE sur le JSON deja produit. Il en ecrit une version pour l'ecran.

DEUX RAISONS :
  ① LE JSON FAIT 867 Ko -- trop lourd a embarquer dans une page. On ne garde que
    ce qui s'affiche, et MODELO n'y entre que par ses dates.
  ② ⭐⭐⭐ UN CRITERE DE PLUS, TROUVE EN LISANT UN CAS : pour 74IL9C8F, notre offre
    porte 2002-01-31 quand le classeur dit 2022-01-31 -- et LE COMPROMIS DU MEME
    DOSSIER porte 2022-04-25, exactement la date du classeur. Donc une AUTRE
    transaction de la chaine peut trancher : si elle s'accorde avec le classeur
    sur SON propre champ, l'annee du classeur est la bonne, et notre offre porte
    une faute de frappe. C'est une preuve interne, pas un avis.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = RACINE / "notice" / "LIGNES_A_TRANCHER_2026-11-18.json"
DST = RACINE / "notice" / "LIGNES_A_TRANCHER_ECRAN_2026-11-18.json"


def une_date(v):
    t = str(v or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2}).*", t)
    if m:
        try:
            return date(*(int(x) for x in m.groups()))
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", t)
    if m:
        j, mo, a = (int(x) for x in m.groups())
        a = a + 2000 if a < 100 else a
        try:
            return date(a, mo, j)
        except ValueError:
            return None
    return None


def main() -> int:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    print("source : %d lignes, %d Ko" % (len(d), SRC.stat().st_size // 1024))
    out = []
    affines = 0
    for x in d:
        reco, pourquoi = x["reco"], list(x["pourquoi"])
        #: ⭐ LE CRITERE INTERNE : une AUTRE transaction de la chaine s'accorde-t-elle
        #:   avec le classeur sur SON champ ? Si oui, l'annee du classeur est bonne.
        if x["famille"] == "date d offre":
            d_cl = une_date(x["classeur"])
            paires = [("compromis", x.get("sheet_compromis")),
                      ("vente", x.get("sheet_vente"))]
            temoins = []
            for kind, au_sheet in paires:
                d_sh = une_date(au_sheet)
                if not d_sh:
                    continue
                for t in x["app"]:
                    if t["kind"] != kind:
                        continue
                    d_no = une_date(t["date"])
                    if d_no and d_no == d_sh:
                        temoins.append("%s : le classeur dit %s et nous aussi"
                                       % (kind, d_sh.isoformat()))
            if temoins and d_cl:
                reco = "le CLASSEUR a raison -- notre date d'offre est une faute de frappe"
                pourquoi.append("⭐⭐ PREUVE INTERNE : " + " ; ".join(temoins)
                                + " -> le reste du dossier s'accorde avec le "
                                  "classeur, seule notre OFFRE derive")
                affines += 1
        out.append({
            "id": x["id"], "ligne": x["ligne_sheet"], "famille": x["famille"],
            "ecart": x["ecart"], "classeur": x["classeur"], "nous": x["nous"],
            "etat": x["etat_classeur"], "mandat": x["mandat"],
            "ville": x["ville"][:46], "vendeur": x["vendeur"][:36],
            "acquereur": x["acquereur"][:36],
            "prix": x["prix_sheet"], "commission": x["commission_sheet"],
            "sheet": {"offre": x["sheet_offre"], "compromis": x["sheet_compromis"],
                      "vente": x["sheet_vente"]},
            #: ⭐ ON GARDE L'AVERTISSEMENT : une date rendue par la cascade doit
            #:   DIRE qu'elle a ete corrigee, sinon on ne sait pas d'ou elle vient.
            "app": [{"id": t["id"], "k": t["kind"], "s": t["state"],
                     "d": t["date"], "he": t["he"], "hs": t["hs"],
                     "ca": t["ca"], "an": t["annonce"],
                     "alerte": t.get("alerte_date") or ""} for t in x["app"]],
            "modelo": [{"debut": m["debut"], "fin": m["fin"],
                        "compromis": m["compromis"], "acte": m["acte"],
                        "etat": m["etat"], "ref": str(m["ref"] or "")[:20]}
                       for m in x["modelo"][:2]],
            "reco": reco, "pourquoi": pourquoi})
    DST.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print("ecrit : %s  (%d Ko)" % (DST.name, DST.stat().st_size // 1024))
    print("recommandations AFFINEES par la preuve interne : %d" % affines)
    print()
    from collections import Counter
    print("=== LES RECOMMANDATIONS ===")
    for r, n in Counter(x["reco"] for x in out).most_common():
        print("   %-58s %3d" % (r[:58], n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
