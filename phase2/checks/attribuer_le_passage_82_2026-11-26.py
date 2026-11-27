#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""L'ATTRIBUTION DU PASSAGE 82, LIGNE PAR LIGNE -- LECTURE SEULE (les socles des rejeux sur copie, et le vrai en mode=ro).

    python -X utf8 -u phase2\checks\attribuer_le_passage_82_2026-11-26.py

SON MOT (26/11) : « Le 81 a ete joue en v21, le 82 le sera en v23.1 : il porte donc mes quatre cases et tes trois regles
d'un coup [...] Montre-moi donc l'attribution, ligne par ligne : ce qui vient de mes cases, ce qui vient de v23.1 et de
quelle regle. »

LES COUCHES (chacune ne change QU'UNE chose par rapport a la precedente) :
  C0  le passage 81 (v21, image du 25/11 07:26, entrees du 81)                       -- le vrai socle, en lecture seule
  C1  + le juge v23 (R27, R28, R29)                                                    -- rejeu 71
  C2  + v23.1 (3741 sortie de ses neuf a part, sa decision du 25/11 au soir)           -- rejeu 73
  C3  + ses deux cases de la 286 (Mandat, Prix)                                        -- rejeu 74
  C4  + ses deux autres cases (245 Prix, 286 Charge Commission)                        -- rejeu 87
  C5  + l'image neuve entiere (la vague de 09:02, la nuit, la vie du classeur)         -- rejeu 83
  C6  + les entrees vivantes du jour (= le 82 tel qu'il sera joue)                     -- rejeu 80
(v21 -> v22 ne change aucun verdict : le rejeu du 25/11 en v22 avec les entrees du 81 a rendu les 4 802 a l'identique.)
"""
from __future__ import annotations

import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Hektor/chantier_classeur_q6_cache/prepa_25_11/"
COUCHES = [
    ("C0 passage 81", "C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite", 81),
    ("C1 juge v23 (R27 R28 R29)", R + "rejeu_81_juge_v23_r27_r28_r29/socle.sqlite", 82),
    ("C2 v23.1 (3741 hors de ses a part)", R + "rejeu_81_juge_v23_1_3741_sortie/socle.sqlite", 82),
    ("C3 ses 2 cases de la 286", R + "rejeu_81_v23_1_image_simulee_9q0fhakk/socle.sqlite", 82),
    ("C4 ses 2 autres cases (245 Prix, 286 Charge)", R + "rejeu_82_v23_1_image_81_plus_ses_quatre_cases/socle.sqlite", 82),
    ("C5 l'image neuve (vague, nuit, classeur)", R + "rejeu_82_image_neuve_26_11_entrees_de_81/socle.sqlite", 82),
    ("C6 les entrees du jour", R + "rejeu_82_image_neuve_26_11_entrees_du_jour/socle.sqlite", 82),
]
CHAMPS = ("verdict", "etiquette", "motif", "pieces", "preuves")


def lire(p: str, n: int) -> dict:
    c = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
    d = {r[0]: r[1:] for r in c.execute("select id_unique, verdict, etiquette, motif, pieces, preuves, motif_texte "
                                         "from verdict where passage=?", (n,))}
    c.close()
    return d


def regle(v: tuple) -> str:
    t = " ".join(str(x) for x in (v[4], v[5]) if x)
    return ",".join(sorted(set(re.findall(r"REGLE (R\d+\w?)", t)))) or "-"


def court(v: tuple | None) -> str:
    if v is None:
        return "absente"
    return "%s %s %s %s" % (v[0], str(v[1])[:13] if v[1] else "-", v[2] or "", v[3] or "")


def main() -> int:
    L = [(nom, lire(p, n)) for nom, p, n in COUCHES]
    print("LES COMPTES PAR COUCHE")
    for nom, d in L:
        t = sum(1 for v in d.values() if v[0] == "TRANCHEE")
        print("   %-46s %d lignes : %d tranchees + %d en attente" % (nom, len(d), t, len(d) - t))
    c0, c6 = L[0][1], L[-1][1]
    touchees = sorted(i for i in c6 if c0.get(i, (None,) * 6)[:5] != c6[i][:5])
    print("\n%d LIGNES DIFFERENT ENTRE LE 81 ET LE 82 (sur verdict, etiquette, motif, pieces ou preuves)" % len(touchees))
    par_couche = {nom: [] for nom, _ in L[1:]}
    neuve_reelle = []
    for i in touchees:
        etapes = []
        for k in range(1, len(L)):
            a, b = L[k - 1][1].get(i), L[k][1].get(i)
            if (a or (None,) * 6)[:5] != (b or (None,) * 6)[:5]:
                champs = [CHAMPS[j] for j in range(5) if (a or (None,) * 6)[j] != b[j]]
                etapes.append((L[k][0], champs, a, b))
        # le cas massif : seule l'etiquette passe de NEUVE:x a une etiquette reelle, a la couche de l'image neuve
        if (len(etapes) == 1 and etapes[0][0].startswith("C5") and etapes[0][1] == ["etiquette"]
                and str(etapes[0][2][1]).startswith("NEUVE:")):
            neuve_reelle.append(i)
            continue
        for nom, champs, a, b in etapes:
            par_couche[nom].append((i, champs, a, b))
    for nom, lst in par_couche.items():
        print("\n== %s : %d ligne(s)" % (nom, len(lst)))
        for i, champs, a, b in lst:
            print("   %-9s %-34s %s  ->  %s   [regle au 82 : %s]" % (i, "/".join(champs), court(a), court(b), regle(c6[i])))
            if "preuves" in champs and champs != ["etiquette", "preuves"] and a is not None:
                pa = set(re.findall(r'"([^"]+)"', a[4] or "")); pb = set(re.findall(r'"([^"]+)"', b[4] or ""))
                for x in sorted(pb - pa)[:3]:
                    print("             + %s" % x[:170])
                for x in sorted(pa - pb)[:3]:
                    print("             - %s" % x[:170])
    print("\n== C5, le cas massif : %d ligne(s) dont SEULE l'etiquette passe de « NEUVE:x » a une etiquette reelle "
          "(la vague de 09:02 a realise ces dossiers)" % len(neuve_reelle))
    print("   " + " ".join(neuve_reelle))
    return 0


if __name__ == "__main__":
    sys.exit(main())
