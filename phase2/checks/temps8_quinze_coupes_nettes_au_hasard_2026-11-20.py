"""Chantier classeur, ⑭ -- QUINZE COUPES NETTES TIREES AU HASARD, pour que Frederic juge les 331 lignes sur pieces.

LECTURE SEULE (le fichier des 803, la photo du 19/11 20:09, le registre local en mode=ro). Rien n'est ecrit nulle
part ailleurs que dans notice/.

LE TIRAGE
  . la population : les lignes du fichier des 803 (TEMPS6_LES_803_...csv) dont `ce_qui_la_debloque` porte
    « coupe NETTE » -- 331 lignes, regroupees par COUPE (une coupe = un groupe : ses lignes partagent la meme coupe) ;
  . « les plus variees » : un tirage STRATIFIE -- chaque strate (famille F1..F4 x « la garde G2 la coupe ») recoit au
    moins une coupe, le reste au prorata ; plus au moins une coupe a 3 lignes. Dans chaque strate, le hasard est
    `random.Random(GRAINE)` : le tirage est REJOUABLE a l'identique, et la graine est ecrite ici AVANT de tirer ;
  . pour chaque coupe : ses lignes du Sheet (colonnes R, S, T, AB, AF, C), ses transactions (genre, etat, date,
    montant, contact chez Hektor, dossier aujourd'hui), ce que le juge dit de chaque transaction, et la coupe.

Usage :  python -u phase2/checks/temps8_quinze_coupes_nettes_au_hasard_2026-11-20.py
Sortie : notice/TEMPS8_QUINZE_COUPES_NETTES_AU_HASARD_2026-11-20.md (les pieces brutes, pour ma relecture).
"""
from __future__ import annotations

import csv
import json
import random
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache")
LES_803 = RACINE / "notice" / "TEMPS6_LES_803_LIGNES_NON_ECRITES_ET_CE_QUI_LES_DEBLOQUE_2026-11-19.csv"
PHOTO = CACHE / "t6_photo.json"
REGISTRE = RACINE / "phase2" / "phase2.sqlite"
SORTIE = RACINE / "notice" / "TEMPS8_QUINZE_COUPES_NETTES_AU_HASARD_2026-11-20.md"
GRAINE = 20112026          # la date du tirage ; ecrite AVANT le premier tirage, jamais changee apres
N = 15
C_, R_, S_, T_, AB_, AF_ = 2, 17, 18, 19, 27, 31


def main() -> int:
    with LES_803.open(encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))
    nettes = [x for x in lignes if "coupe NETTE" in x["ce_qui_la_debloque"]]
    coupes = defaultdict(list)
    for x in nettes:
        m = re.search(r"coupe NETTE : (.*?)(?: -- |$)", x["ce_qui_la_debloque"])
        coupes[m.group(1)].append(x)
    print("lignes « coupe NETTE » : %d ; coupes (groupes) : %d" % (len(nettes), len(coupes)), flush=True)
    if len(nettes) != 331:
        print("⛔ 331 attendues", flush=True)
        return 1

    strates = defaultdict(list)
    for texte, ls in coupes.items():
        strates[(ls[0]["famille"][:2], ls[0]["la_garde_g2_la_coupe"])].append(texte)
    rnd = random.Random(GRAINE)
    tirees = []
    for k in sorted(strates):
        strates[k].sort()
        tirees.append(rnd.choice(strates[k]))
    a_trois = sorted(t for t, ls in coupes.items() if len(ls) >= 3 and t not in tirees)
    if not any(len(coupes[t]) >= 3 for t in tirees):
        tirees.append(rnd.choice(a_trois))
    reste = N - len(tirees)
    total = sum(len(v) for v in strates.values())
    for k in sorted(strates, key=lambda k: -len(strates[k])):
        part = round(reste * len(strates[k]) / total)
        dispo = [t for t in strates[k] if t not in tirees]
        for t in rnd.sample(dispo, min(part, len(dispo))):
            if len(tirees) < N:
                tirees.append(t)
    while len(tirees) < N:
        dispo = sorted(t for t in coupes if t not in tirees)
        tirees.append(rnd.choice(dispo))
    print("strates : %s" % {"%s/G2=%s" % k: len(v) for k, v in sorted(strates.items())}, flush=True)

    P = json.loads(PHOTO.read_text(encoding="utf-8"))
    LIG, TX = P["lignes"], {int(a): v for a, v in P["tx"].items()}
    con = sqlite3.connect("file:%s?mode=ro" % REGISTRE.as_posix(), uri=True)

    def tx_reg(a):
        r = con.execute("select kind, state, date, date_acte, montant, acquereur_json, app_chaine_id, "
                        "hektor_annonce_id, transaction_origine from app_affaire_ledger where app_affaire_id=?",
                        (a,)).fetchone()
        if not r:
            return None
        try:
            nom = json.loads(r[5] or "{}").get("nom", "")
        except ValueError:
            nom = "?"
        return {"genre": r[0], "etat": r[1], "date": r[2], "acte": r[3], "montant": r[4], "contact": nom,
                "dossier": r[6], "annonce": r[7], "origine": r[8]}

    out = ["# Quinze coupes nettes tirees au hasard (graine %d) -- les pieces brutes" % GRAINE, "",
           "Population : %d lignes « coupe NETTE », %d coupes. Strates : %s." % (
               len(nettes), len(coupes), {"%s/G2=%s" % k: len(v) for k, v in sorted(strates.items())}), ""]
    for n, texte in enumerate(tirees, 1):
        ls = coupes[texte]
        out.append("## %d. %s -- G2 la coupe : %s -- %d ligne(s)" % (n, ls[0]["famille"], ls[0]["la_garde_g2_la_coupe"], len(ls)))
        out.append("")
        out.append("COUPE : " + texte)
        out.append("")
        ids = sorted({i for x in ls for i in [x["id_unique"]] + x["autres_lignes_du_meme_dossier"].split()} - {""})
        txs = set()
        for i in ids:
            if i not in LIG:
                continue
            r = LIG[i]["row"]
            out.append("- LIGNE %s (n° %s) : %s | offre %s | compromis %s | %s | prix %s | mandat %s"
                       % (i, LIG[i]["num"], r[R_], r[S_] or "-", r[T_] or "-", r[AB_], r[AF_], r[C_]))
        for x in ls:
            txs |= {int(a) for a in re.findall(r"(\d+)\(", x["transactions_et_genre"])}
        for a in re.findall(r"(\d+) \w+\(", texte) + re.findall(r"\+(\d+) ", texte):
            txs.add(int(a))
        txs |= {int(a) for a in re.findall(r"\b(\d{3,7})\b", texte.split("||")[0])}
        for a in sorted(txs):
            t = tx_reg(a)
            j = TX.get(a, {})
            if t is None:
                out.append("    - transaction %d : absente du registre" % a)
                continue
            out.append("    - %d %s/%s du %s (acte %s) %s EUR, contact %s, dossier %s, annonce %s%s ; le juge : %s -- %s"
                       % (a, t["genre"], t["etat"], t["date"], t["acte"], t["montant"], t["contact"], t["dossier"],
                          t["annonce"], " (C5)" if t["origine"] == "classeur" else "",
                          " ".join(j.get("designe", [])) or "personne", (j.get("pourquoi") or "")[:200]))
        out.append("")
    SORTIE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("ECRIT : %s (%d coupes)" % (SORTIE.name, len(tirees)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
