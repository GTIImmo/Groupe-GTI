# -*- coding: utf-8 -*-
"""AUDIT V2 -- le dossier complet d'une ligne : la ligne du Sheet, et TOUTES les transactions du
bien que j'ai choisi (et du second), avec leurs vraies dates et leurs acquereurs.
Lecture de la photo seulement. Usage : a3_dossier.py IU [IU ...]"""
import csv
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
# ⛔ BORD (19/11) : ce chemin s'etait coupe en deux au rangement dans le depot (« \n » de
#   « \notice » lu comme un retour a la ligne) -- le script ne compilait plus. On ne
#   l'ecrit donc plus avec des barres obliques inverses.
CSV_MOI = Path(__file__).resolve().parents[2] / "notice" / "AUDIT_INDEPENDANT_V2_MON_APPARIEMENT_2026-11-19.csv"
sys.argv, ids = sys.argv[:1], sys.argv[1:]
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("apparieur_v2", ICI / "audit_v2_apparier_2026-11-19.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)  # recharge la photo et REJOUE l'appariement (il reecrit le CSV, a l'identique)

R = {r["id_unique"]: r for r in csv.DictReader(open(CSV_MOI, encoding="utf-8-sig"), delimiter=";")}
for iu in ids:
    r = R[iu]
    L = A.LIGNE_DE[iu]
    print("=" * 100)
    print("%s  L%s  %s  mandat %s  prix %s  com %s  ville %s" % (iu, L["rang"], L["etat"], L["mandat"], L["prix"], L["com"], L["ville_txt"]))
    print("   acq : %s   -> %s" % (L["acq_txt"], sorted(L["acq"])))
    print("   vend: %s   -> %s" % (L["vend_txt"], sorted(L["vend"])))
    print("   dates : " + " . ".join("%s %s" % (k, v) for k, v in L["d"].items() if v))
    print("   ponts : lien_id=%s ref=%s netty=%s" % (L["lien_id"], L["ref"], L["netty"]))
    print("   MOI -> annonce %s  O %s C %s V %s  [%s]  %s %s" % (r["annonce"], r["offre"], r["compromis"], r["vente"], r["familles"], r["certitude"], r["drapeaux"]))
    for h in [r["annonce"], r["second_annonce"]]:
        if not h:
            continue
        e = A.ANN.get(h, {})
        print("   -- annonce %s  dossiers %s  mandats %s  ville %s  mandants %s" % (
            h, sorted(e.get("dossiers", ()))[:3], sorted(e.get("mandats", ()))[:6], sorted(e.get("ville", ()))[:2], sorted(e.get("mandants", ()))[:6]))
        for t in sorted(A.TX_DE_ANNONCE.get(h, ()), key=lambda t: (str(t["date"]), t["k"])):
            print("      %-9s %7s  %-9s  %s  acte %s  %9s  hon %s  mandat %s  acq %s  ch %s %s" % (
                t["k"], t["id"], str(t["etat"])[:9], t["date"], t["date_acte"], t["montant"], t["hon"], t["mandat"],
                sorted(t["acq"])[:4], t["chaine"], t["dossier"]))
