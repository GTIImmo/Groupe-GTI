#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LE TEMOIN D'APRES DU PASSAGE 83 (R30a) -- LECTURE SEULE (son mot du 27/11 au soir : « le temoin d'apres est
obligatoire avant que l'ecrivain et la boucle y passent, et tu me le montres avant de recopier en base »).

    python -X utf8 -u phase2\checks\temoin_d_apres_le_passage_83_2026-11-27.py

Quatre controles, tous en lecture seule (le vrai socle est ouvert en mode ro) :
  1. le 83 contre le 82 : 0 verdict, 0 etiquette, 0 motif changes ; seules pieces et preuves bougent, et SEULEMENT par la
     phrase de R30a (les pieces ajoutees sont exactement celles que la phrase nomme) ;
  2. le 83 contre le rejeu sur copie du meme code (rejeu_82_r30_2026-11-27/r30a_validee, passage 83) : IDENTIQUES,
     colonne par colonne -- le passage officiel rend ce que la mesure avait annonce ;
  3. les temoins du passage (table temoin) : les memes ecarts qu'au 82, temoin par temoin ;
  4. les entrees vivantes et l'image : celles du 82.
Sortie : 0 tout est vert . 1 un controle crie.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
VRAI = Path(r"C:\Hektor\chantier_classeur_q6_cache\protocole\socle.sqlite")
COPIE = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
    r"C:\Hektor\chantier_classeur_q6_cache\rejeu_82_r30_2026-11-27\r30a_validee\socle.sqlite")
OFFICIEL = int(sys.argv[1]) if len(sys.argv) > 1 else 83          # le passage officiel juge (83, puis 84 le 27/11)
DE_LA_COPIE = int(sys.argv[3]) if len(sys.argv) > 3 else 83       # son jumeau dans la copie du rejeu
DOSSIER = VRAI.parent
COLS = ["verdict", "etiquette", "motif", "motif_texte", "pieces", "preuves", "biens", "num", "epreuve"]
PHRASE = "REGLE R30 (variante du 27/11, le geste 6)"


def verdicts(con, p):
    q = "select id_unique, %s from verdict where passage=?" % ", ".join(COLS)
    return {r[0]: dict(zip(COLS, r[1:])) for r in con.execute(q, (p,))}


def main() -> int:
    v = sqlite3.connect("file:%s?mode=ro" % VRAI.as_posix(), uri=True)
    dernier = v.execute("select max(id) from passage").fetchone()[0]
    if dernier != OFFICIEL:
        print("⛔ le dernier passage du vrai socle est %s, pas %s" % (dernier, OFFICIEL))
        return 1
    img82, img83 = (v.execute("select image from passage where id=?", (p,)).fetchone()[0] for p in (82, OFFICIEL))
    a, b = verdicts(v, 82), verdicts(v, OFFICIEL)
    t82 = Counter((r[0], r[1]) for r in v.execute("select temoin, ecart from temoin where passage=82"))
    t83 = Counter((r[0], r[1]) for r in v.execute("select temoin, ecart from temoin where passage=?", (OFFICIEL,)))
    v.close()
    cris = []
    # 1. le 83 contre le 82
    diff = {c: sorted(i for i in a if a[i][c] != b.get(i, {}).get(c)) for c in COLS}
    print("1. LE 83 CONTRE LE 82 (%d lignes, %d)" % (len(a), len(b)))
    for c in COLS:
        print("   %-12s differents : %d" % (c, len(diff[c])))
    for c in ("verdict", "etiquette", "motif", "motif_texte", "biens", "num", "epreuve"):
        if diff[c]:
            cris.append("%s change sur %d ligne(s) : %s" % (c, len(diff[c]), diff[c][:5]))
    mal = []
    n_pieces = 0
    for i in diff["pieces"]:
        pa, pb = set(json.loads(a[i]["pieces"] or "[]")), set(json.loads(b[i]["pieces"] or "[]"))
        nommees = set()
        for p in json.loads(b[i]["preuves"] or "[]"):
            if p.startswith(PHRASE):
                nommees |= {int(x) for x in p.rsplit(":", 1)[1].split()}
        n_pieces += len(pb - pa)
        if pa - pb or (pb - pa) != nommees:
            mal.append(i)
    print("   pieces ajoutees : %d sur %d lignes ; lignes ou l'ajout n'est pas EXACTEMENT ce que R30a nomme : %d"
          % (n_pieces, len(diff["pieces"]), len(mal)))
    if mal or set(diff["preuves"]) != set(diff["pieces"]):
        cris.append("pieces / preuves hors de R30a : %s" % (mal[:5] or sorted(set(diff["preuves"]) ^ set(diff["pieces"]))[:5]))
    # 2. contre le rejeu sur copie
    c = sqlite3.connect("file:%s?mode=ro" % COPIE.as_posix(), uri=True)
    r = verdicts(c, DE_LA_COPIE)
    c.close()
    dr = {k: sum(1 for i in b if b[i][k] != r.get(i, {}).get(k)) for k in COLS}
    print("2. LE 83 OFFICIEL CONTRE LE REJEU SUR COPIE : %s" % ("IDENTIQUES" if not any(dr.values()) and set(b) == set(r)
                                                                else "⛔ DIFFERENTS %s" % dr))
    if any(dr.values()) or set(b) != set(r):
        cris.append("le passage officiel differe du rejeu annonce")
    # 3. les temoins
    print("3. LES TEMOINS DU PASSAGE : 82 %s / 83 %s -- %s" % (
        sum(t82.values()), sum(t83.values()), "LES MEMES" if t82 == t83 else "⛔ DIFFERENTS"))
    if t82 != t83:
        cris.append("temoins differents : %s" % {k: (t82.get(k, 0), t83.get(k, 0)) for k in set(t82) | set(t83)
                                                 if t82.get(k, 0) != t83.get(k, 0)})
    # 4. l'image et les entrees vivantes
    e82 = json.loads((DOSSIER / "entrees_passage_82.json").read_text(encoding="utf-8"))["entrees"]
    e83 = json.loads((DOSSIER / ("entrees_passage_%d.json" % OFFICIEL)).read_text(encoding="utf-8"))["entrees"]
    print("4. IMAGE : 82 %s / 83 %s ; ENTREES VIVANTES : %s" % (img82, img83, "LES MEMES" if e82 == e83 else "⛔ CHANGEES"))
    if img82 != img83 or e82 != e83:
        cris.append("image ou entrees vivantes changees")
    print("\n⇒ %s" % ("VERT : le passage 83 est le 82 plus R30a, rien d'autre" if not cris else "⛔ ROUGE : " + " ; ".join(cris)))
    return 0 if not cris else 1


if __name__ == "__main__":
    sys.exit(main())
