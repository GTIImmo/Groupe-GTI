#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- LE DUEL : mon bien CONTRE celui du gel.       13/11/2026

Pour chaque ligne en divergence, il met FACE A FACE les deux biens en jeu --
le mien et celui du gel -- avec tout ce qui permet de trancher : le mandat, les
noms, les dates par genre, le montant, la ville.

⛔ IL NE REND AUCUN VERDICT. Le jugement se fait a la lecture, et se trace
  ensuite a la main. C'est la demande de Frederic : « de l'intelligence ligne par
  ligne, pas du code ».

USAGE
    python phase2/checks/apparier_v2_duel.py --lignes 4758,4393
LECTURE SEULE.
"""
from __future__ import annotations

import argparse
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

from apparier_v2_socle import (chiffres, jour, lire_le_registre,     # noqa: E402
                               lire_le_sheet, noms, noms_du_blob,
                               personnes_du_blob, pur, somme)

RAPPORT = RACINE / "notice" / "RAPPORT_V2_CONTRE_GEL_2026-11-13.csv"
CHAMPS = ("acquereur_json", "acquereurs_json", "mandants_json")


def qui(blob) -> str:
    out = []
    for p in personnes_du_blob(blob):
        n = " ".join(str(p.get(k) or "").strip() for k in ("prenom", "nom") if p.get(k))
        out.append(n.strip() or "(sans nom)")
    return " + ".join(out) if out else "-"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lignes", required=True)
    args = ap.parse_args()
    voulues = [x.strip() for x in args.lignes.split(",") if x.strip()]

    # les deux biens en jeu, depuis le rapport
    duel: dict = {}
    with io.open(RAPPORT, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            if r["ligne"] in voulues and r["cas"] == "DIVERGENT":
                duel.setdefault(r["ligne"], {"gel": r["bien du gel"],
                                             "v2": r["bien de la v2"],
                                             "conf": r["confiance gel"],
                                             "etage": r["etage gel"],
                                             "fam": r["quelles familles"],
                                             "id": r["ID Unique"]})

    tx = lire_le_registre()
    par_bien = collections.defaultdict(list)
    for t in tx:
        par_bien[t["hektor_annonce_id"]].append(t)
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""select hektor_annonce_id, ville, type_bien, statut_annonce,
                        mandat_numero_reference, commercial_nom
                   from app_registre_mandats_current""")
    infos = {}
    for r in c.fetchall():
        infos.setdefault(r[0], {"ville": r[1], "type": r[2], "statut": r[3],
                                "ref": r[4], "nego": r[5]})
    con.close()

    entetes, lignes = lire_le_sheet()
    par_num = {str(n): l for n, l in lignes}
    ic = {k: (entetes.index(k) if k in entetes else None) for k in entetes}

    def case(l, nom):
        i = ic.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    for num in voulues:
        d = duel.get(num)
        l = par_num.get(num)
        if not d or l is None:
            print("\nligne %s : pas en divergence, ou introuvable" % num)
            continue
        print("\n" + "#" * 88)
        print("LIGNE %s   ID %s   (gel : %s, etage %s | mes familles : %s)"
              % (num, d["id"], d["conf"], str(d["etage"])[:38], d["fam"] or "aucune"))
        print("#" * 88)
        print("  CE QUE DIT LE CLASSEUR")
        for ch in ("Mandat", "Etat Actuel", "Acquéreur", "Vendeur", "Prix", "Ville",
                   "Négociateur 1", "Offre Achat", "Compromis", "Vente Prévue",
                   "Vente Fixée", "Annulée", "product_ref", "COMMENTAIRES"):
            v = case(l, ch)
            if v:
                print("     %-15s %s" % (ch, v[:120]))

        man = chiffres(case(l, "Mandat"))
        mots = noms(case(l, "Acquéreur")) | noms(case(l, "Vendeur"))
        dcl = {g: jour(case(l, k)) for k, g in
               (("Offre Achat", "offre"), ("Compromis", "compromis"),
                ("Vente Fixée", "vente"), ("Vente Prévue", "vente_prevue"))
               if jour(case(l, k))}
        prix = somme(case(l, "Prix"))

        for etiquette, bien in (("LE GEL dit", d["gel"]), ("MOI je dis", d["v2"])):
            try:
                b = int(bien)
            except (TypeError, ValueError):
                continue
            inf = infos.get(b, {})
            print("\n  %s  ->  BIEN %s   %s %s   statut %s   mandat ref %s   nego %s"
                  % (etiquette, b, inf.get("ville") or "?", inf.get("type") or "",
                     inf.get("statut") or "-", inf.get("ref") or "-",
                     inf.get("nego") or "-"))
            # les concordances, EXPLICITEMENT
            acc = []
            mandats = {chiffres(t.get("numero_mandat")) for t in par_bien[b]}
            if man and man in mandats:
                acc.append("MANDAT %s identique" % man)
            nb = set()
            for t in par_bien[b]:
                for ch in CHAMPS:
                    nb |= noms_du_blob(t.get(ch))
            comm = mots & nb
            if comm:
                acc.append("noms communs : %s" % ",".join(sorted(comm)))
            for g, dd in dcl.items():
                g2 = "vente" if g == "vente_prevue" else g
                for t in par_bien[b]:
                    if t["kind"] == g2 and jour(t.get("date")) == dd:
                        acc.append("date %s = %s" % (g, dd))
                        break
            mts = {somme(t.get("montant")) for t in par_bien[b]}
            mts.discard(None)
            if prix is not None and mts:
                if prix in mts:
                    acc.append("PRIX EGAL (%s)" % prix)
                else:
                    e = min(mts, key=lambda v: abs(v - prix))
                    acc.append("prix %s contre %s (%+d)" % (prix, e, e - prix))
            vl = pur(case(l, "Ville"))
            if vl and inf.get("ville") and (vl in pur(inf["ville"]) or pur(inf["ville"]) in vl):
                acc.append("VILLE identique")
            print("     concordances : %s" % (" | ".join(acc) if acc else "AUCUNE"))
            for t in sorted(par_bien[b], key=lambda z: z["app_affaire_id"]):
                print("     %-9s %-10s %-11s %-10s mandat %-7s n° %-6s  %s"
                      % (t["kind"], t.get("state") or "-",
                         jour(t.get("date")) or "(vide)",
                         somme(t.get("montant")) if somme(t.get("montant")) is not None else "-",
                         t.get("numero_mandat") or "-", t["app_affaire_id"],
                         qui(t.get("acquereurs_json") or t.get("acquereur_json"))[:60]))
    print("\n" + "#" * 88)
    print("AUCUN VERDICT ICI. Le jugement se lit, puis se trace a la main.")
    print("#" * 88)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
