#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- QUEL CHAMP EST « LE PRIX » DU CLASSEUR ?      13/11/2026

Le diagnostic a montre que le « Prix » du classeur DIFFERE de notre `montant`
dans 44,5 % des cas, et TOUJOURS dans le meme sens : le classeur porte PLUS.
  classeur 375 000 / nous 365 000 . classeur 136 000 / nous 125 000 ...

⭐ Ce n'est donc pas du bruit de saisie, c'est UN AUTRE CHAMP. Lequel ?
  On teste tous les candidats sur les lignes dont le mandat designe UN SEUL
  bien -- la, on SAIT de quel bien il s'agit, donc la comparaison est honnete.
⭐⭐ Et on teste aussi des COMBINAISONS : montant + honoraires, par exemple, si
  le classeur porte le prix « honoraires inclus ».

⚠ ON NE CHOISIT PAS AU JUGEMENT : on prend celui qui gagne, chiffre en main.

LECTURE SEULE.
"""
from __future__ import annotations

import collections
import sqlite3
import sys
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

from apparier_v2_socle import chiffres, lire_le_sheet, pur, somme  # noqa: E402

CANDIDATS = (
    "montant",
    "prix_net_vendeur",
    "montant + honoraires_entree",
    "montant + honoraires_sortie",
    "montant + les deux honoraires",
    "prix_net_vendeur + les deux honoraires",
    "montant + commission_agence",
    "prix de l'annonce (dossier)",
)


def main() -> int:
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""
        select app_affaire_id, kind, numero_mandat, hektor_annonce_id, montant,
               prix_net_vendeur, honoraires_entree, honoraires_sortie, commission_agence
          from app_affaire_ledger
    """)
    cols = [d[0] for d in c.description]
    tx = [dict(zip(cols, r)) for r in c.fetchall()]

    # le prix de l'annonce, s'il existe
    prix_annonce: dict = {}
    try:
        c.execute("pragma table_info(app_dossier_current)")
        dc = [r[1] for r in c.fetchall()]
        champ = next((x for x in dc if pur(x) in {"prix", "prix_vente", "prix_affiche"}), None)
        if champ:
            c.execute("select hektor_annonce_id, %s from app_dossier_current" % champ)
            prix_annonce = {r[0]: somme(r[1]) for r in c.fetchall()}
            print("   prix de l'annonce lu dans app_dossier_current.%s (%d biens)"
                  % (champ, len(prix_annonce)))
    except Exception as e:                                          # noqa: BLE001
        print("   (prix de l'annonce non lisible : %s)" % str(e)[:70])
    con.close()

    par_mandat = collections.defaultdict(set)
    for t in tx:
        m = chiffres(t.get("numero_mandat"))
        if m:
            par_mandat[m].add(t["hektor_annonce_id"])

    def valeurs(t, quoi):
        m = somme(t.get("montant"))
        nv = somme(t.get("prix_net_vendeur"))
        he = somme(t.get("honoraires_entree")) or 0
        hs = somme(t.get("honoraires_sortie")) or 0
        ca = somme(t.get("commission_agence")) or 0
        if quoi == "montant":
            return [m]
        if quoi == "prix_net_vendeur":
            return [nv]
        if quoi == "montant + honoraires_entree":
            return [m + he] if m is not None else []
        if quoi == "montant + honoraires_sortie":
            return [m + hs] if m is not None else []
        if quoi == "montant + les deux honoraires":
            return [m + he + hs] if m is not None else []
        if quoi == "prix_net_vendeur + les deux honoraires":
            return [nv + he + hs] if nv is not None else []
        if quoi == "montant + commission_agence":
            return [m + ca] if m is not None else []
        if quoi == "prix de l'annonce (dossier)":
            return [prix_annonce.get(t["hektor_annonce_id"])]
        return []

    entetes, lignes = lire_le_sheet()
    icol = {k: entetes.index(k) for k in ("Mandat", "Prix") if k in entetes}

    def case(l, nom):
        i = icol.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    # on prepare, par mandat, l'ensemble des valeurs de chaque candidat
    print("\n" + "=" * 80)
    print("QUEL CHAMP EST « LE PRIX » DU CLASSEUR ?")
    print("=" * 80)
    cibles = []
    for _, l in lignes:
        man = chiffres(case(l, "Mandat"))
        prix = somme(case(l, "Prix"))
        if man and prix is not None and len(par_mandat.get(man, ())) == 1:
            cibles.append((man, prix))
    print("\nbase de comparaison : %d lignes dont le mandat designe UN SEUL bien" % len(cibles))

    resultats = []
    for quoi in CANDIDATS:
        par_man = collections.defaultdict(set)
        for t in tx:
            m = chiffres(t.get("numero_mandat"))
            if not m:
                continue
            for v in valeurs(t, quoi):
                if v is not None:
                    par_man[m].add(v)
        exact = proche = diff = vide = 0
        for man, prix in cibles:
            s = par_man.get(man)
            if not s:
                vide += 1
            elif prix in s:
                exact += 1
            elif min(abs(v - prix) for v in s) <= max(100, 0.01 * prix):
                proche += 1
            else:
                diff += 1
        tot = max(1, len(cibles))
        resultats.append((quoi, exact, proche, diff, vide,
                          100.0 * (exact + proche) / tot))
    resultats.sort(key=lambda r: -r[5])
    print("\n  %-40s %7s %7s %7s %7s %8s" % ("candidat", "EGAL", "<1 %", "diff", "absent", "reussi"))
    print("  " + "-" * 78)
    for quoi, e, p, d, v, pc in resultats:
        print("  %-40s %7d %7d %7d %7d %7.1f %%" % (quoi, e, p, d, v, pc))

    print("\n" + "=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
