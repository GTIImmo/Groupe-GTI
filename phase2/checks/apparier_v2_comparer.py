#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- PASSE 4 : LA COMPARAISON AVEC LA v1.          13/11/2026

⛔⛔ C'EST LE SEUL FICHIER DE TOUT L'APPARIEUR V2 QUI OUVRE LE RESULTAT DE LA v1.
  Les passes 1 a 3 ne l'ont jamais lu, et ne lisent jamais le gel. L'independance
  etait garantie par construction ; ici, elle a deja produit son resultat, et on
  peut enfin confronter.

⚠ LES DEUX NE PARLENT PAS DE LA MEME CHOSE, ET IL FAUT LE TRADUIRE :
    la v1 rend UNE CHAINE  (un dossier -- recalcule chaque nuit)
    la v2 rend UN BIEN     (une annonce -- elle ne bouge jamais)
  ⭐ On traduit la chaine de la v1 en son BIEN pour comparer ce qui est
    comparable. Une chaine appartient a un seul bien ; l'inverse est faux.

CE QUE LA COMPARAISON PRODUIT :
    LES DEUX D'ACCORD        -> la ligne passe d'« appariee » a QUASI CERTAINE
    DESACCORD                -> la liste de travail, et c'est tout l'interet
    v2 trouve, v1 non        -> ce que la v2 APPORTE
    v1 trouve, v2 non        -> ce que la v2 RATE (il faut le dire aussi)

⭐ LE CRITERE DE CONCLUSION, POSE AVANT DE VOIR LE RESULTAT :
    CONCLUANT      si la v2 trouve des lignes ou la v1 se trompe, OU si l'accord
                   transforme « appariee » en « certaine » avec une liste FINIE
                   de cas a trancher
    PAS CONCLUANT  si elle redit la v1 sans ajouter de certitude, ou si elle fait
                   plus de bruit que de signal
"""
from __future__ import annotations

import collections
import csv
import io
import sqlite3
import sys
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

# ⛔⛔ CORRIGE LE 13/11 SUR LA QUESTION DE FREDERIC : « quel v1 ? mon calcul du
#   regel n'est pas a sa v1, il a ete optimise depuis non ? » -- IL AVAIT RAISON.
#   Je comparais le CSV du 12/11 a 09:48 alors que le CODE avait ete modifie le
#   12/11 a 11:59 (commit 518b08b, « regle D »). Je confrontais donc ma methode a
#   un resultat PERIME DE DEUX HEURES.
#   ⭐ On prend desormais LE PLUS RECENT, automatiquement, et on l'AFFICHE.
#   ⭐ Et « la v1 » est un mauvais nom : c'est L'APPARIEUR ACTUEL. On l'appelle
#     « apparieur » dans tout le fichier.
def _dernier_csv_apparieur():
    cands = sorted((RACINE / "notice").glob("APPARIEMENT_CLASSEUR_*.csv"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        raise SystemExit("aucun CSV d'appariement dans notice/")
    return cands[0]


V1 = _dernier_csv_apparieur()
V2 = RACINE / "notice" / "APPARIEUR_V2_ACCORD_2026-11-13.csv"
SORTIE = RACINE / "notice" / "APPARIEUR_V2_vs_V1_2026-11-13.csv"


def main() -> int:
    print("=" * 84)
    print("PASSE 4 -- LA COMPARAISON v2 CONTRE v1")
    print("=" * 84)

    # ── la chaine de la v1 -> son bien ──────────────────────────────────────
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""select app_chaine_id, hektor_annonce_id, count(*)
                   from app_affaire_ledger
                  where app_chaine_id is not null
                  group by app_chaine_id, hektor_annonce_id""")
    chaine_bien: dict = {}
    multi = 0
    for ch, ann, _ in c.fetchall():
        if ch in chaine_bien and chaine_bien[ch] != ann:
            multi += 1
        chaine_bien[ch] = ann
    con.close()
    print("\n%d chaines traduites en biens (%d chaines a cheval sur 2 biens)"
          % (len(chaine_bien), multi))

    # ── la v1 ───────────────────────────────────────────────────────────────
    v1: dict = {}
    with io.open(V1, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            k = [x for x in r if "quelle" in x][0]
            kc = [x for x in r if "confiance" in x][0]
            kch = [x for x in r if "cha" in x and "trouv" in x][0]
            kid = "ID Unique"
            ch = (r.get(kch) or "").strip()
            try:
                bien = chaine_bien.get(int(ch)) if ch else None
            except ValueError:
                bien = None
            v1[(r.get(kid) or "").strip()] = {
                "chaine": ch, "bien": bien,
                "confiance": (r.get(kc) or "").strip(),
                "cle": (r.get(k) or "").strip(),
            }
    import datetime
    print("APPARIEUR : %s" % V1.name)
    print("           modifie le %s -- %d lignes lues"
          % (datetime.datetime.fromtimestamp(V1.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
             len(v1)))

    # ── la v2 ───────────────────────────────────────────────────────────────
    v2: dict = {}
    with io.open(V2, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            v2[(r.get("ID Unique") or "").strip()] = r
    print("v2 : %d lignes lues" % len(v2))

    # ── LA CONFRONTATION ────────────────────────────────────────────────────
    res = collections.Counter()
    par_verdict = collections.defaultdict(collections.Counter)
    desaccords = []
    for ident, b2 in v2.items():
        a = v1.get(ident)
        bien2 = (b2.get("bien retenu") or "").strip()
        verdict2 = (b2.get("verdict") or "").split("--")[0].strip()
        bien1 = str(a["bien"]) if (a and a.get("bien") is not None) else ""
        if not a:
            res["absente de la v1"] += 1
            continue
        if bien1 and bien2:
            if bien1 == bien2:
                res["LES DEUX D'ACCORD"] += 1
                par_verdict[verdict2]["accord"] += 1
            else:
                res["DESACCORD"] += 1
                par_verdict[verdict2]["desaccord"] += 1
                desaccords.append([ident, b2.get("ligne"), bien1, bien2,
                                   a["confiance"], a["cle"], b2.get("verdict"),
                                   b2.get("A bien"), b2.get("B bien"), b2.get("C bien"),
                                   b2.get("arbitre (n° dossier)")])
        elif bien2 and not bien1:
            res["la v2 trouve, la v1 NON"] += 1
            par_verdict[verdict2]["v2 seule"] += 1
            desaccords.append([ident, b2.get("ligne"), "", bien2, a["confiance"],
                               a["cle"], b2.get("verdict"), b2.get("A bien"),
                               b2.get("B bien"), b2.get("C bien"),
                               b2.get("arbitre (n° dossier)")])
        elif bien1 and not bien2:
            res["la v1 trouve, la v2 NON"] += 1
            desaccords.append([ident, b2.get("ligne"), bien1, "", a["confiance"],
                               a["cle"], b2.get("verdict"), b2.get("A bien"),
                               b2.get("B bien"), b2.get("C bien"),
                               b2.get("arbitre (n° dossier)")])
        else:
            res["aucune des deux"] += 1

    tot = sum(res.values())
    print("\n" + "-" * 84)
    print("LE RESULTAT")
    print("-" * 84)
    for k, n in res.most_common():
        print("   %-28s %5d  (%5.1f %%)" % (k, n, 100.0 * n / max(1, tot)))

    print("\n" + "-" * 84)
    print("L'ACCORD, PAR NIVEAU DE CERTITUDE DE LA v2")
    print("   ⭐ c'est la mesure qui compte : un accord sur une ligne que la v2")
    print("     declare CERTAINE (3 familles disjointes) vaut une preuve.")
    print("-" * 84)
    for v in ("CERTAIN", "SOLIDE", "FAIBLE", "A REGARDER", "A TRANCHER", "AUCUNE"):
        c2 = par_verdict.get(v)
        if not c2:
            continue
        t = sum(c2.values())
        print("   %-12s total %5d | accord %5d (%5.1f %%) | desaccord %4d | v2 seule %4d"
              % (v, t, c2["accord"], 100.0 * c2["accord"] / max(1, t),
                 c2["desaccord"], c2["v2 seule"]))

    print("\n" + "-" * 84)
    print("LES DESACCORDS PAR CLE DE LA v1 -- ou la v1 est-elle fragile ?")
    print("-" * 84)
    par_cle = collections.Counter(d[5] for d in desaccords if d[2] and d[3])
    for k, n in par_cle.most_common(10):
        print("   %-52s %4d" % (k[:52], n))

    with io.open(SORTIE, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ID Unique", "ligne", "bien v1", "bien v2", "confiance v1",
                    "cle v1", "verdict v2", "A (mandat)", "B (identite)",
                    "C (dates)", "arbitre"])
        w.writerows(desaccords)
    print("\n   ecrit : %s  (%d lignes)" % (SORTIE, len(desaccords)))
    print("\n" + "=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
