#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""TEMPS 4, QUESTION 1 -- LA REGLE E (« une transaction sans date restee seule devient visible »)
MESUREE SUR TOUT LE REGISTRE, AVANT D'ETRE ALLUMEE.                                 19/11/2026

    .venv\Scripts\python.exe -X utf8 phase2\checks\temps4_regle_e_sans_date_visible_2026-11-19.py

⛔ CE SCRIPT N'ECRIT RIEN : phase2.sqlite en mode=ro, tout en memoire. L'interrupteur
  APP_CHAINAGE_SANS_DATE_VISIBLE n'est pose QUE dans ce processus, jamais dans .env.

    N   le registre d'aujourd'hui, la vraie fonction, regle E ETEINTE (= la base)
    E   le meme registre, la vraie fonction, regle E ALLUMEE
    ➡ toute difference est l'effet de la regle E, et de rien d'autre.

LES TEMOINS
    POSITIF   les cinq casses « sans date » du temps 3 (20088 DEBARD, 19070 POCHELON, 1335 THEVENON,
              14110 GENOUX, 16197 du bien 33458) rejoignent le dossier de leur acheteur
    INVERSE   aucun bien sans transaction sans date restee seule ne bouge
    SENS      la regle ne peut que REUNIR : 0 dossier coupe
    GARDES    apres E : 0 dossier a deux ventes, 0 a deux compromis vivants

L'ETIQUETTE -- la RPC app_poser_etiquettes_dossier garde, dans un groupe a plusieurs etiquettes,
celle de la transaction au PLUS PETIT NUMERO. On simule ce choix pour dire, reunion par reunion,
quelle etiquette survivrait et laquelle disparaitrait.

Sortie : 0 mesure faite . 2 un temoin a echoue.
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date as Date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
from phase2.sync.affaire_ledger import (                            # noqa: E402
    LEDGER_TABLE, ETATS_COMPROMIS_MORTS, _acquereurs, _date_de_tri, recalculer_les_chaines)

BASE = RACINE / "phase2" / "phase2.sqlite"
SORTIE = RACINE / "notice" / "TEMPS4_REGLE_E_REUNIONS_2026-11-19.csv"
TEMOINS = {20088: 41481, 19070: 39745, 1335: 3481, 14110: 28653, 16197: 33458}
#: LA GARDE « l'acheteur du compromis vivant » DOIT les laisser seuls (19/11, demande de Frederic) :
#: les 4 tentatives echouees dont la VENTE porte le nom chez Hektor, et le couple PYOT (abstention).
BLOQUES = {7499: ("15220", "GENILLON"), 8845: ("17536", "Rouchon"), 11103: ("23238", "Simonyan"),
           28214: ("54867", "PLANCHE"), 4385: ("9629", "PYOT, abstention")}
#: L'EXCLUSION DECLAREE (EXCLUES_DE_LA_REGLE_E, decision du 19/11) DOIT la laisser seule
EXCLUES = {26613: ("52166", "SHN6RKDI, exclusion declaree")}
SORTIE_RESTE = RACINE / "notice" / "TEMPS4_REGLE_E_SANS_DATE_RESTANTES_2026-11-19.csv"
INTERRUPTEUR = "APP_CHAINAGE_SANS_DATE_VISIBLE"


def copie() -> sqlite3.Connection:
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def rejouer(allumee: bool) -> tuple[dict, dict]:
    if allumee:
        os.environ[INTERRUPTEUR] = "1"
    else:
        os.environ.pop(INTERRUPTEUR, None)
    con = copie()
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        compte = recalculer_les_chaines(con)
    chaines = dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {LEDGER_TABLE}"))
    os.environ.pop(INTERRUPTEUR, None)
    return chaines, compte


def jour(t):
    try:
        return Date.fromisoformat(str(t)[:10])
    except (TypeError, ValueError):
        return None


def main() -> int:
    echecs = []
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    info, en_base = {}, {}
    for a, bien, k, s, d, acq, hacq, pj, ch, u, num, pres in src.execute(
            f"SELECT app_affaire_id, hektor_annonce_id, kind, state, date, acquereurs_json, "
            f"hektor_acquereur_id, propositions_json, app_chaine_id, app_dossier_uuid, "
            f"hektor_affaire_id, present_in_hektor FROM {LEDGER_TABLE}"):
        info[a] = {"bien": str(bien), "genre": k, "etat": (s or "").lower(), "tri": _date_de_tri(k, d, pj),
                   "acqs": _acquereurs(acq), "uuid": u,
                   "effacee": bool(str(num or "").strip()) and str(pres) in ("0", "false", "False")}
        en_base[a] = ch

    n, compte_n = rejouer(False)
    ecarts = {a for a in n if n[a] != en_base[a]}
    # ⚠ LES 10 RATTACHEMENTS DU 19/11 (rattachements_manuels.csv) sont dans le fichier mais pas
    #   encore dans la base tant que la nuit n'a pas recalcule : un ecart sur CES 10 offres est
    #   attendu jusque-la ; un ecart sur n'importe quelle autre transaction est un rouge.
    pas_encore_en_base = {5356, 5408, 13056, 16866, 17278, 20196, 21339, 22069, 26825, 28328}
    print("N  regle E eteinte : %d dossiers . ecart avec la base : %d (dont %d = les 10 rattachements "
          "du 19/11 que la nuit n'a pas encore appliques)"
          % (len(set(n.values())), len(ecarts), len(ecarts & pas_encore_en_base)))
    if ecarts - pas_encore_en_base:
        echecs.append("E eteinte != base : %s" % sorted(ecarts - pas_encore_en_base)[:20])
    e, compte_e = rejouer(True)
    print("E  regle E allumee : %d dossiers" % len(set(e.values())))
    print("   transactions sans date rendues visibles : %s" % compte_e.get(
        "[E] transaction sans date restee seule -- rendue visible", 0))

    # LES REUNIONS : un dossier de E qui reunit plusieurs dossiers de N
    par_e = defaultdict(set)
    for a, c in e.items():
        par_e[c].add(a)
    reunions, coupes = [], 0
    par_n = defaultdict(set)
    for a, c in n.items():
        par_n[c].add(a)
    for c, membres in par_n.items():
        if len({e[m] for m in membres}) > 1:
            coupes += 1
    for c, membres in par_e.items():
        venus = defaultdict(set)
        for m in membres:
            venus[n[m]].add(m)
        if len(venus) < 2:
            continue
        # la part RENDUE VISIBLE : le(s) dossier(s) de N d'un seul membre sans date
        seuls = [next(iter(v)) for v in venus.values() if len(v) == 1 and info[next(iter(v))]["tri"] is None]
        reunions.append((c, membres, venus, seuls))
    print("   dossiers coupes par E : %d (attendu 0)" % coupes)
    if coupes:
        echecs.append("E a coupe un dossier")

    # LES TEMOINS
    for t, bien in TEMOINS.items():
        ok = any(t in m and len(m) > 1 for _, m, _, _ in reunions)
        print("   temoin positif %-6s (bien %s) : %s" % (t, bien, "REUNI" if ok else "⛔ RESTE SEUL"))
        if not ok:
            echecs.append("temoin %s" % t)
    for t, (bien, nom) in BLOQUES.items():
        seul = len(par_e[e[t]]) == 1
        print("   temoin de la GARDE %-6s (bien %s, %s) : %s" % (
            t, bien, nom, "RESTE SEUL" if seul else "⛔ REUNI A TORT"))
        if not seul:
            echecs.append("garde %s" % t)
    for t, (bien, nom) in EXCLUES.items():
        seul = len(par_e[e[t]]) == 1
        print("   temoin de l'EXCLUSION %-6s (bien %s, %s) : %s" % (
            t, bien, nom, "RESTE SEUL" if seul else "⛔ REUNI MALGRE L'EXCLUSION"))
        if not seul:
            echecs.append("exclusion %s" % t)
    dites = compte_e.get("[E] exclusion declaree -- laissee seule (EXCLUES_DE_LA_REGLE_E)", 0)
    print("   exclusions DITES par le compte rendu : %s (attendu %d)" % (dites, len(EXCLUES)))
    if dites != len(EXCLUES):
        echecs.append("exclusion muette")
    biens_bougent = {info[next(iter(m))]["bien"] for _, m, _, _ in reunions}
    seuls_n = {a for a, c in n.items() if info[a]["tri"] is None and not info[a]["effacee"]
               and len(par_n[c]) == 1}
    biens_avec_seul = {info[a]["bien"] for a in seuls_n}
    hors = biens_bougent - biens_avec_seul
    print("   temoin inverse : biens qui bougent SANS transaction sans date seule : %d" % len(hors))
    if hors:
        echecs.append("temoin inverse")

    # LES GARDES APRES E
    def compte_gardes(ch):
        par = defaultdict(list)
        for a, c in ch.items():
            if not info[a]["effacee"]:
                par[c].append(info[a])
        v = sum(1 for m in par.values() if sum(1 for x in m if x["genre"] == "vente") >= 2)
        cp = sum(1 for m in par.values() if sum(1 for x in m if x["genre"] == "compromis"
                                                and x["etat"] not in ETATS_COMPROMIS_MORTS) >= 2)
        return v, cp
    print("   gardes apres E : deux ventes %d . deux compromis vivants %d" % compte_gardes(e))
    if compte_gardes(e) != (0, 0):
        echecs.append("gardes")

    # LE CLASSEMENT DE CHAQUE REUNION
    lignes, verdicts, etiq = [], Counter(), Counter()
    for c, membres, venus, seuls in reunions:
        for t in seuls:
            T = info[t]
            autres = [info[m] | {"id": m} for m in membres if m != t]
            meme = [x for x in autres if T["acqs"] & x["acqs"]]
            genres = Counter("%s %s" % (x["genre"], x["etat"] or "") for x in meme)
            dates = [jour(x["tri"]) for x in autres if jour(x["tri"])]
            etendue = (max(dates) - min(dates)).days if len(dates) >= 2 else 0
            autres_acheteurs = any(not (T["acqs"] & x["acqs"]) and x["acqs"] for x in autres)
            if T["genre"] == "compromis" and T["etat"] in ETATS_COMPROMIS_MORTS:
                deja = any(x["genre"] == "compromis" and x["etat"] in ETATS_COMPROMIS_MORTS for x in meme)
                forme = ("A VERIFIER (le dossier porte deja un compromis annule du meme acheteur)" if deja
                         else "A RAISON (l'essai annule rejoint l'affaire du meme acheteur)")
            elif T["genre"] == "compromis":
                forme = ("A RAISON (compromis -> vente du meme acheteur)"
                         if any(x["genre"] == "vente" for x in meme)
                         else "A VERIFIER (compromis actif sans vente)")
            elif T["genre"] == "offre":
                forme = "A RAISON (l'offre rejoint l'affaire du meme acheteur)"
            else:
                forme = "A VERIFIER (%s)" % T["genre"]
            if etendue > 3 * 365:
                forme = "A VERIFIER (le dossier s'etend sur %d ans : contact reutilise ?)" % (etendue // 365)
            verdicts[forme] += 1
            # L'ETIQUETTE : la RPC garde celle du plus petit numero du groupe
            uuids = {info[m]["uuid"] for m in membres}
            gagnante = info[min(membres)]["uuid"]
            perd_cible = gagnante == T["uuid"]
            etiq["l'etiquette du DOSSIER CIBLE disparait (la transaction seule a le plus petit numero)"
                 if perd_cible else "l'etiquette de la transaction seule disparait (cas normal)"] += 1
            lignes.append({"bien": T["bien"], "transaction": t, "genre": T["genre"], "etat": T["etat"],
                           "rejoint_dossier_de": ",".join(str(x["id"]) for x in meme),
                           "membres_apres": len(membres), "autres_acheteurs_dans_le_dossier": autres_acheteurs,
                           "etendue_jours": etendue, "verdict": forme,
                           "etiquette_gardee": gagnante, "etiquettes_du_groupe": len(uuids),
                           "etiquette_du_dossier_cible_absorbee": perd_cible})
    print("\nREUNIONS PAR LA REGLE E : %d dossiers, %d transactions sans date rattachees, sur %d biens"
          % (len(reunions), len(lignes), len(biens_bougent)))
    for k, v in verdicts.most_common():
        print("   %-85s %4d" % (k, v))
    print("ETIQUETTES (simulation de la RPC) :")
    for k, v in etiq.most_common():
        print("   %-85s %4d" % (k, v))
    print("   ⚠ fusions qu'une seule nuit ferait : %d (le cri de la nuit est a 10)" % len(reunions))
    print("SANS DATE SEULES : %d avant E . %d apres E" % (
        len(seuls_n), sum(1 for a in seuls_n if len(par_e[e[a]]) == 1)))

    # CE QUI RESTE DES SANS DATE, ET POURQUOI -- une raison par transaction, lue dans les donnees
    reste, raisons = [], Counter()
    ventes_par_acq: dict[tuple, int] = Counter()
    for a, x in info.items():
        if x["genre"] == "vente" and not x["effacee"]:
            for q in x["acqs"]:
                ventes_par_acq[(x["bien"], q)] += 1
    for t in sorted(seuls_n):
        if len(par_e[e[t]]) > 1:
            continue
        T = info[t]
        if t in EXCLUES:
            raison = "EXCLUSION DECLAREE : question ouverte (EXCLUES_DE_LA_REGLE_E)"
        elif not T["acqs"]:
            raison = "aucun numero d'acquereur : rien a comparer"
        else:
            dossiers = {e[a] for a, x in info.items() if a != t and x["bien"] == T["bien"]
                        and not x["effacee"] and (T["acqs"] & x["acqs"])}
            if not dossiers:
                raison = "aucun autre dossier de cet acheteur sur le bien"
            else:
                def cp_vivants(d):
                    return [info[m] for m in par_e[d] if info[m]["genre"] == "compromis"
                            and info[m]["etat"] not in ETATS_COMPROMIS_MORTS]
                if all(any(not (T["acqs"] & c["acqs"]) for c in cp_vivants(d)) and
                       not any(T["acqs"] & c["acqs"] for c in cp_vivants(d)) and cp_vivants(d)
                       for d in dossiers):
                    raison = "GARDE E : le compromis vivant du dossier est a un autre acheteur"
                elif any(ventes_par_acq[(T["bien"], q)] > 1 for q in T["acqs"]):
                    raison = "regle D : plusieurs ventes a ce nom sur le bien, le nom est ecarte"
                elif (T["genre"] == "compromis" and T["etat"] not in ETATS_COMPROMIS_MORTS
                      and any(cp_vivants(d) for d in dossiers)):
                    raison = "regle D : deux compromis vivants"
                else:
                    raison = "AUTRE -- a lire"
        raisons[raison] += 1
        reste.append({"bien": T["bien"], "transaction": t, "genre": T["genre"], "etat": T["etat"],
                      "acquereurs": ",".join(sorted(T["acqs"])), "raison": raison})
    print("CE QUI RESTE DES %d SANS DATE SEULES : %d" % (len(seuls_n), len(reste)))
    for k, v in raisons.most_common():
        print("   %-75s %4d" % (k, v))
    with SORTIE_RESTE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["bien", "transaction", "genre", "etat", "acquereurs", "raison"])
        w.writeheader()
        w.writerows(reste)
    print("CSV : %s" % SORTIE_RESTE)
    print("CE QUE LES REGLES ONT FAIT -- E eteinte / allumee :")
    for k in sorted(set(compte_n) | set(compte_e)):
        vn, ve = compte_n.get(k), compte_e.get(k)
        if isinstance(vn, int) and not isinstance(vn, bool) and vn != ve or (vn is None and isinstance(ve, int)):
            print("   %-70s %6s / %6s" % (k[:70], vn, ve))
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()) if lignes else ["vide"])
        w.writeheader()
        w.writerows(lignes)
    print("CSV : %s" % SORTIE)
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
