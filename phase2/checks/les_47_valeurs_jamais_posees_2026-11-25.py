#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LES 47 VALEURS DU SHEET JAMAIS POSEES (son mot du 25/11) -- LECTURE SEULE, ⛔ NE POSE RIEN.

    python -X utf8 -u phase2\checks\les_47_valeurs_jamais_posees_2026-11-25.py

SON MOT : « NE POSE RIEN. Range-les-moi par ce qu'elles valent : les 17 ventes reglees d'abord, avec leur montant et leur
ligne, puis les 29 dates. Et dis-moi pour chacune des 17 si c'est une vraie vente reglee de mon classeur ou une erreur de
saisie de ma part -- parce que si le registre ne la dit pas reglee, l'un des deux se trompe. »

D'ou elles viennent : les valeurs du classeur (vente reglee + facture, date d'annulation) ont ete posees les 16-17/11 en
suivant le GEL. Sur les 108 liens que le protocole RELIE (le gel ne les avait pas), la valeur de la ligne n'a jamais ete
posee sur la piece. Le registre ne dit donc pas « non reglee » : il n'a jamais recu la valeur -- il est MUET.

Pour chaque vente, les PREUVES qui disent si la ligne du Sheet est une vraie vente reglee, lues des deux cotes :
  . le Sheet : etat « Vente reglee », la date de « Vente Reglee », un numero de facture, la Commission TTC, le Prix ;
  . Hektor (le registre) : la piece de vente existe, sa date, son montant, ses honoraires ;
  . les accords : honoraires Hektor = Commission TTC ; montant Hektor = Prix (a 1 %) ; date de vente <= date de reglement.
Le verdict n'est pas une decision : VRAIE VENTE REGLEE si tout concorde, A REGARDER avec ce qui ne concorde pas.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

SORTIE = RACINE / "notice" / "CLASSEUR_LES_47_VALEURS_JAMAIS_POSEES_2026-11-25.csv"
#: le passage du protocole et son image (27/11 : reglables, pour remesurer au 82 sans toucher la mesure du 25/11)
PASSAGE, IMAGE = 81, "2026-11-25_072625"
ECARTEES_PAR_LUI = {"6U5DQQ4J": "sa decision du 25/11 : date anterieure au compromis, ecartee",
                    "S3HOG6UL": "sa decision du 25/11 : date anterieure au compromis, ecartee"}
#: ses doubles de saisie (25/11) : « NE TRANCHE PAS SEUL » -- rien ne se pose sur eux avant sa decision
SES_DOUBLES = {"3308P0UX": "VIALLARD", "YRUF0S9H": "VIALLARD", "T2GZOY5O": "PAOLONE", "O6R10ZQA": "PAOLONE"}
MOIS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}


def date_du_sheet(t: str):
    t = (t or "").strip().lower()
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", t)
    if m:
        a = int(m.group(3))
        return date(a + 2000 if a < 100 else a, int(m.group(2)), int(m.group(1)))
    m = re.search(r"(\d{1,2})\s*([a-zéû]+)\s*(\d{2,4})", t)
    if m and m.group(2) in MOIS:
        a = int(m.group(3))
        return date(a + 2000 if a < 100 else a, MOIS[m.group(2)], int(m.group(1)))
    return None


def date_hektor(t):
    t = str(t or "")[:10]
    try:
        return datetime.strptime(t, "%Y-%m-%d").date() if not t.startswith("0000") else None
    except ValueError:
        return None


def nombre(t):
    t = re.sub(r"[^\d,.]", "", str(t or "")).replace(",", ".")
    try:
        return float(t) if t else None
    except ValueError:
        return None


def main() -> int:
    con = sqlite3.connect("file:%s?mode=ro" % (P.DOSSIER / "socle.sqlite").as_posix(), uri=True)
    V = {i: (v, json.loads(ps) if ps else []) for i, v, ps in con.execute(
        "select id_unique, verdict, pieces from verdict where passage=?", (PASSAGE,))}
    con.close()
    sheet = json.loads((P.IMAGES / IMAGE / "sheet.json").read_text(encoding="utf-8"))
    ent = sheet["entete"]
    k = {c: ent.index(c) for c in ("Etat Actuel", "Vente Réglée", "Numéro de facture", "Commission TTC", "Prix",
                                   "Annulée", "Compromis", "Vente Fixée", "Signée", "Agence")}
    cn, cu = P.pooler()
    cu.execute("select id_unique, app_affaire_id from public.app_classeur_lien")
    gel = defaultdict(set)
    for i, a in cu.fetchall():
        gel[i].add(int(a))
    cu.execute("select app_affaire_id, kind, state, date::text, date_acte::text, montant, honoraires_entree, "
               "coalesce(vente_reglee_app,''), coalesce(numero_facture_app,''), coalesce(date_annulation_app,''), "
               "app_chaine_id, app_dossier_numero from public.app_affaire_ledger")
    R = {int(r[0]): r for r in cu.fetchall()}
    cu.execute("select distinct app_chaine_id from public.app_affaire_ledger where kind='vente' and "
               "coalesce(vente_reglee_app,'') <> ''")
    ch_reglee = {x[0] for x in cu.fetchall()}
    cn.rollback()
    cn.close()

    ventes, dates = [], []
    for i, (v, pp) in V.items():
        if v != "TRANCHEE":
            continue
        row = (sheet["par_id"].get(i) or [{}])[0].get("row")
        num = (sheet["par_id"].get(i) or [{}])[0].get("num")
        if not row:
            continue
        for a in sorted(set(pp) - gel.get(i, set())):
            if a not in R:
                continue
            _, genre, etat, d, dacte, mt, hon, vr, nf, da, ch, numero = R[a]
            if genre == "vente" and row[k["Etat Actuel"]] == "Vente réglée" and row[k["Vente Réglée"]].strip() and not vr:
                reglee = date_du_sheet(row[k["Vente Réglée"]])
                dv = date_hektor(dacte) or date_hektor(d)
                ttc, prix = nombre(row[k["Commission TTC"]]), nombre(row[k["Prix"]])
                ecarts = []
                if not row[k["Numéro de facture"]].strip():
                    ecarts.append("pas de numero de facture au Sheet")
                if ttc is None or hon is None or abs(float(hon) - ttc) > 1:
                    ecarts.append("honoraires Hektor %s / Commission TTC %s" % (hon, row[k["Commission TTC"]]))
                if prix is None or mt is None or abs(float(mt) - prix) > 0.01 * float(mt):
                    ecarts.append("montant Hektor %s / Prix %s" % (mt, row[k["Prix"]]))
                if reglee is None:
                    ecarts.append("date de reglement illisible (%r)" % row[k["Vente Réglée"]])
                elif dv and reglee < dv:
                    ecarts.append("reglee le %s AVANT la vente du %s" % (reglee, dv))
                if ch in ch_reglee:
                    ecarts.append("son dossier est DEJA regle par une autre piece")
                verdict = "VRAIE VENTE REGLEE (tout concorde)" if not ecarts else "A REGARDER : " + " ; ".join(ecarts)
                ventes.append({"quoi": "VENTE_REGLEE", "id_unique": i, "ligne": num, "piece": a, "dossier": numero,
                               "commission_ttc_sheet": row[k["Commission TTC"]], "prix_sheet": row[k["Prix"]],
                               "vente_reglee_sheet": row[k["Vente Réglée"]], "facture_sheet": row[k["Numéro de facture"]],
                               "vente_hektor": str(dv or ""), "montant_hektor": mt, "honoraires_hektor": hon,
                               "deja_reglee": "OUI" if ch in ch_reglee else "", "verdict": verdict,
                               "agence": row[k["Agence"]]})
            if genre == "compromis" and etat == "cancelled" and row[k["Annulée"]].strip() and not da:
                dan = date_du_sheet(row[k["Annulée"]])
                dc = date_hektor(d) or date_du_sheet(row[k["Compromis"]])
                if i in ECARTEES_PAR_LUI:
                    verdict = "ECARTEE : " + ECARTEES_PAR_LUI[i]
                elif i in SES_DOUBLES:
                    verdict = "ATTEND SA DECISION : %s est un de ses doubles de saisie (%s)" % (i, SES_DOUBLES[i])
                elif dan is None:
                    verdict = "A REGARDER : date d'annulation illisible (%r)" % row[k["Annulée"]]
                elif dc and dan < dc:
                    verdict = "A REGARDER : annulee le %s AVANT son compromis du %s (sa regle : ecartee)" % (dan, dc)
                else:
                    verdict = "POSABLE par sa regle (date du Sheet sur SON compromis)"
                dates.append({"quoi": "DATE_ANNULATION", "id_unique": i, "ligne": num, "piece": a, "dossier": numero,
                              "annulee_sheet": row[k["Annulée"]], "compromis": str(dc or ""), "verdict": verdict,
                              "commission_ttc_sheet": row[k["Commission TTC"]]})
    ventes.sort(key=lambda x: (x["deja_reglee"] == "OUI", -(nombre(x["commission_ttc_sheet"]) or 0)))
    dates.sort(key=lambda x: (not x["verdict"].startswith("POSABLE"), x["ligne"] or 0))
    print("LES VENTES REGLEES JAMAIS POSEES : %d (dont %d sur un dossier deja regle)" % (
        len(ventes), sum(1 for x in ventes if x["deja_reglee"])))
    tot = 0.0
    for x in ventes:
        tot += nombre(x["commission_ttc_sheet"]) or 0
        print("  %-9s ligne %-5s piece %-6s %-11s commission %-8s prix %-9s reglee %-14s facture %-26s | Hektor : vente %s, "
              "montant %s, honoraires %s -> %s" % (
                  x["id_unique"], x["ligne"], x["piece"], x["dossier"], x["commission_ttc_sheet"], x["prix_sheet"],
                  x["vente_reglee_sheet"][:14], x["facture_sheet"][:26], x["vente_hektor"], x["montant_hektor"],
                  x["honoraires_hektor"], x["verdict"]))
    print("  commissions TTC des %d : %.2f" % (len(ventes), tot))
    print("\nLES DATES D'ANNULATION JAMAIS POSEES : %d" % len(dates))
    for x in dates:
        print("  %-9s ligne %-5s piece %-6s %-11s annulee %-14s compromis %-10s -> %s" % (
            x["id_unique"], x["ligne"], x["piece"], x["dossier"], x["annulee_sheet"][:14], x["compromis"], x["verdict"]))
    champs = ["quoi", "id_unique", "ligne", "piece", "dossier", "commission_ttc_sheet", "prix_sheet", "vente_reglee_sheet",
              "facture_sheet", "vente_hektor", "montant_hektor", "honoraires_hektor", "deja_reglee", "annulee_sheet",
              "compromis", "verdict", "agence"]
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(ventes + dates)
    print("\nCSV : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
