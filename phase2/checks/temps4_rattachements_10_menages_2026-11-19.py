#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""TEMPS 4 -- LE REJEU DES 10 RATTACHEMENTS « MENAGE » DECIDES LE 19/11/2026.

    .venv\Scripts\python.exe -X utf8 phase2\checks\temps4_rattachements_10_menages_2026-11-19.py

⛔ CE SCRIPT N'ECRIT RIEN : phase2.sqlite en mode=ro, tout en memoire. Il ne touche pas au fichier
  des rattachements : il en fabrique une copie SANS les 10 lignes du 19/11 dans un fichier temporaire.

    AVANT   le registre d'aujourd'hui, la vraie fonction, le fichier SANS les 10 (= la base)
    APRES   le meme registre, la vraie fonction, le fichier tel qu'il est (16 decisions)
    ➡ toute difference est l'effet des 10 lignes, et de rien d'autre.

LES TEMOINS
    FICHIER   exactement 16 decisions, dont les 10 attendues, a l'identique
    BASE      AVANT = la base, 0 ecart (sinon la comparaison ne prouve rien)
    POSITIF   chaque offre rejoint le dossier de son compromis : 10 sur 10
    INVERSE   AUCUNE autre transaction ne change de dossier : seules les 10 offres bougent
    GARDES    apres : 0 dossier a deux ventes, 0 a deux compromis vivants
    ETIQUETTE la RPC garde celle du plus petit numero : c'est celle du COMPROMIS, 10 sur 10

Sortie : 0 tout est vert . 2 un temoin a echoue.
"""
from __future__ import annotations

import contextlib
import csv
import io
import os
import sqlite3
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
import phase2.sync.affaire_ledger as al                             # noqa: E402

BASE = RACINE / "phase2" / "phase2.sqlite"
SORTIE = RACINE / "notice" / "TEMPS4_RATTACHEMENTS_10_MENAGES_REJEU_2026-11-19.csv"
#: offre -> (compromis cible, bien) -- la liste du § 2.6, validee le 19/11
LES_DIX = {5356: (5355, 10955), 5408: (5407, 11014), 13056: (13055, 27037), 16866: (16865, 35702),
           17278: (17277, 36712), 20196: (20195, 41584), 21339: (21337, 42883), 22069: (22068, 44276),
           26825: (26824, 52724), 28328: (28327, 55040)}
DECISIONS_ATTENDUES = 16


def copie() -> sqlite3.Connection:
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def rejouer(fichier: Path) -> tuple[dict, dict]:
    d_origine = al.FICHIER_RATTACHEMENTS
    al.FICHIER_RATTACHEMENTS = fichier
    try:
        con = copie()
        tampon = io.StringIO()
        with contextlib.redirect_stdout(tampon):
            compte = al.recalculer_les_chaines(con)
        chaines = dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {al.LEDGER_TABLE}"))
    finally:
        al.FICHIER_RATTACHEMENTS = d_origine
    return chaines, compte


def main() -> int:
    echecs = []
    decisions = al.lire_rattachements_manuels()
    print("FICHIER : %d decisions (attendu %d)" % (len(decisions), DECISIONS_ATTENDUES))
    if len(decisions) != DECISIONS_ATTENDUES:
        echecs.append("nombre de decisions")
    lues = {s: (c, b) for s, c, b, _ in decisions}
    for s, (c, b) in LES_DIX.items():
        if lues.get(s) != (c, b):
            echecs.append("ligne %s absente ou differente" % s)
    print("   les 10 du 19/11 presentes a l'identique : %s" % ("OUI" if not echecs else "⛔ NON"))

    texte = al.FICHIER_RATTACHEMENTS.read_text(encoding="utf-8-sig")
    garde = []
    for brut in texte.splitlines():
        p = brut.strip().split(";")
        if p and p[0].strip().isdigit() and int(p[0]) in LES_DIX:
            continue
        garde.append(brut)
    with tempfile.TemporaryDirectory() as tmp:
        sans_les_dix = Path(tmp) / "rattachements_sans_les_dix.csv"
        sans_les_dix.write_text("\n".join(garde) + "\n", encoding="utf-8")
        avant, compte_avant = rejouer(sans_les_dix)
    apres, compte_apres = rejouer(al.FICHIER_RATTACHEMENTS)

    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    info = {}
    for a, bien, k, s, ch, u, num, pres in src.execute(
            f"SELECT app_affaire_id, hektor_annonce_id, kind, state, app_chaine_id, app_dossier_uuid, "
            f"hektor_affaire_id, present_in_hektor FROM {al.LEDGER_TABLE}"):
        info[a] = {"bien": str(bien), "genre": k, "etat": (s or "").lower(), "base": ch, "uuid": u,
                   "effacee": bool(str(num or "").strip()) and str(pres) in ("0", "false", "False")}
    ecart = sum(1 for a in avant if avant[a] != info[a]["base"])
    print("AVANT (fichier sans les 10) : %d dossiers . ecart avec la base : %d (attendu 0)"
          % (len(set(avant.values())), ecart))
    if ecart:
        echecs.append("AVANT != base")
    print("APRES (fichier tel quel)    : %d dossiers" % len(set(apres.values())))

    bougent = sorted(a for a in avant if avant[a] != apres[a])
    print("\nTRANSACTIONS QUI CHANGENT DE DOSSIER : %d (attendu 10, les 10 offres)" % len(bougent))
    hors = [a for a in bougent if a not in LES_DIX]
    print("   temoin inverse : transactions qui bougent HORS des 10 offres : %d" % len(hors))
    if hors:
        echecs.append("temoin inverse : %s" % hors[:20])

    par_apres = defaultdict(set)
    for a, c in apres.items():
        par_apres[c].add(a)
    lignes = []
    print("\nCHAQUE DOSSIER QUI BOUGE :")
    for s, (c, b) in LES_DIX.items():
        ok = apres[s] == apres[c]
        groupe = par_apres[apres[c]]
        gagnante = info[min(groupe)]["uuid"]
        garde_cp = gagnante == info[c]["uuid"]
        print("   bien %-6s offre %-6s : dossier %-6s -> dossier %-6s (celui du compromis %s) . %d membres "
              ". %s . etiquette gardee = celle du %s"
              % (b, s, avant[s], apres[s], c, len(groupe), "REUNI" if ok else "⛔ PAS REUNI",
                 "COMPROMIS" if garde_cp else "⛔ AUTRE"))
        if not ok:
            echecs.append("offre %s pas reunie" % s)
        if not garde_cp:
            echecs.append("etiquette %s" % s)
        lignes.append({"bien": b, "offre": s, "dossier_avant": avant[s], "compromis": c,
                       "dossier_apres": apres[s], "membres_apres": len(groupe),
                       "etiquette_gardee": gagnante, "etiquette_absorbee": info[s]["uuid"],
                       "reunie": ok})

    def compte_gardes(ch):
        par = defaultdict(list)
        for a, c in ch.items():
            if not info[a]["effacee"]:
                par[c].append(info[a])
        v = sum(1 for m in par.values() if sum(1 for x in m if x["genre"] == "vente") >= 2)
        cp = sum(1 for m in par.values() if sum(1 for x in m if x["genre"] == "compromis"
                                                and x["etat"] not in al.ETATS_COMPROMIS_MORTS) >= 2)
        return v, cp
    print("\nGARDES apres : deux ventes %d . deux compromis vivants %d (avant : %d . %d)"
          % (compte_gardes(apres) + compte_gardes(avant)))
    if compte_gardes(apres) != compte_gardes(avant):
        echecs.append("gardes")
    print("CE QUE LE FICHIER A FAIT -- avant / apres :")
    for k in sorted(set(compte_avant) | set(compte_apres)):
        if k.startswith("[M]"):
            print("   %-70s %6s / %6s" % (k[:70], compte_avant.get(k), compte_apres.get(k)))
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    print("CSV : %s" % SORTIE)
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs)
        return 2
    print("✅ TOUT EST VERT : 10 dossiers bougent, et pas un de plus")
    return 0


if __name__ == "__main__":
    sys.exit(main())
