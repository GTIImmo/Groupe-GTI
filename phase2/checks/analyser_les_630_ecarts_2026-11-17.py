#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES ~630 ECARTS QUI RESTENT : QU'EN SAIT-ON DEJA ?              17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\analyser_les_630_ecarts_2026-11-17.py

⛔ LECTURE SEULE. Il lit le CSV du rapport du gel, rien d'autre.

⭐⭐⭐ SA DEMANDE : « peux-tu relire et analyser mes notes et historique de ce
  chantier pour eventuellement recuperer des info sur ces lignes car normalement
  nous avions deja tout survole ». Il a raison, et c'est la regle du projet
  (lecon 15) : CHERCHER SI LE PROJET A DEJA TRANCHE avant de reposer la question.

CE QUE LA RELECTURE DU PLAN A DEJA TROUVE, ET QUI S'APPLIQUE ICI :

  ① OFFRE ACHAT (128 ecarts) -- DEJA INSTRUIT LE 14/11. Le chiffre est passe de
    104 a 128 apres la correction du double format de date, et le plan dit
    « le decompte tolerant predit, A L'UNITE ». ⭐ Et il nomme la reserve :
    « les 26 ecarts a plus d'un mois restent a regarder », dont 15 VENTES
    REGLEES et ⭐⭐ TROIS DECALAGES D'ANNEE EXACTS (un de 7 305 jours = vingt ans
    pile, deux de 366 jours) -- des FAUTES DE SAISIE, pas des desaccords.
    ➡ donc sur 128 : ~102 a moins d'un mois, 26 a regarder, 3 evidents.

  ② MANDAT (145 ecarts) -- LE PROJET SAIT DEJA que le numero de mandat
    N'IDENTIFIE PAS un mandat : 4 142 doublons, et 33 numeros du classeur sont
    RECYCLES a charges divergentes. Hektor recycle ses identifiants (memoire
    « Mandats 2026 : ids recycles »).

  ③ COMMISSION TTC (84) -- le classeur est TTC, `commission_agence` est HT. Le
    rapport lit donc `honoraires_entree` (4 389 fois). Les 84 restants sont des
    ecarts APRES cette correction.

LA METHODE ICI : pour chaque champ, on RANGE les ecarts par ORDRE DE GRANDEUR
  (jours pour une date, euros ou pourcents pour un montant). Un ecart de 1 jour
  et un ecart de vingt ans ne se traitent pas pareil, et les melanger dans un
  total de 630 empeche de decider.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ECARTS = RACINE / "notice" / "A4_RAPPORT_GEL_ECARTS_SEULS_2026-11-17.csv"
#: les champs que ses decisions ont ECARTES ou deja tranches « RIEN »
ECARTES = {"Vente Prevue", "Prix", "Nature", "Ville", "Notaire", "Agence",
           "Acquereur", "Vendeur", "product_ref", "Acquéreur"}


def nombre(v: str):
    t = re.sub(r"[\s €]", "", (v or "").strip()).replace(",", ".")
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return None
    return float(t)


def une_date(v: str):
    t = (v or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        try:
            return date(*(int(x) for x in m.groups()))
        except ValueError:
            return None
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", t)
    if m:
        j, mo, a = (int(x) for x in m.groups())
        a = a + 2000 if a < 100 else a
        try:
            return date(a, mo, j)
        except ValueError:
            return None
    return None


def main() -> int:
    if not ECARTS.exists():
        print("⛔ le CSV des ecarts est absent : %s" % ECARTS)
        return 2
    with ECARTS.open(encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))
    print("=== LES ECARTS DU RAPPORT DU GEL (lecture seule) ===")
    print("le CSV : %d lignes . colonnes : %s"
          % (len(lignes), " . ".join(list(lignes[0].keys())[:8])))
    print()

    #: le CSV porte une ligne par LIGNE du classeur, avec une colonne par champ.
    #: on cherche donc les colonnes « <champ> verdict » ou equivalent.
    #: ⭐ LA FORME REELLE DU CSV, mesuree et non supposee : trois prefixes par
    #:   champ -- `c_` ce que dit le CLASSEUR, `n_` ce que NOUS portons,
    #:   `v_` le VERDICT. Ma premiere version cherchait « <champ> verdict » et a
    #:   REFUSE DE CONCLURE : c'est le bon reflexe, un script muet vaut mieux
    #:   qu'un script qui rend 0.
    cols = list(lignes[0].keys())
    champs = sorted({c[2:] for c in cols if c.startswith("v_")})
    if not champs:
        print("⛔ aucune colonne « v_<champ> » -- la forme du CSV a change.")
        print("   les colonnes : %s" % " | ".join(cols))
        return 2
    print("champs porteurs d'un verdict : %d" % len(champs))
    print()

    print("=== LES ECARTS PAR CHAMP, ET LE TRI PAR SES DECISIONS ===")
    restants = {}
    for ch in champs:
        n = sum(1 for l in lignes if "ECART" in str(l.get("v_" + ch, "")).upper())
        if not n:
            continue
        if ch in ECARTES:
            print("   %-20s %5d   ⛔ ECARTE ou deja « RIEN »" % (ch, n))
        else:
            restants[ch] = n
    print()
    print("=== ⭐ CE QUI RESTE A TRANCHER, PAR ORDRE DE GRANDEUR ===")
    for ch, n in sorted(restants.items(), key=lambda x: -x[1]):
        print()
        print("   %s -- %d ecarts" % (ch.upper(), n))
        c_cl, c_no = "c_" + ch, "n_" + ch
        if c_cl not in cols or c_no not in cols:
            print("      (les deux valeurs ne sont pas dans le CSV)")
            continue
        jours, euros, autres = [], [], 0
        for l in lignes:
            if "ECART" not in str(l.get("v_" + ch, "")).upper():
                continue
            a, b = l.get(c_cl, ""), l.get(c_no, "")
            da, db = une_date(a), une_date(b)
            if da and db:
                jours.append(abs((da - db).days))
                continue
            na, nb = nombre(a), nombre(b)
            if na is not None and nb is not None:
                euros.append(abs(na - nb))
                continue
            autres += 1
        if jours:
            j = sorted(jours)
            print("      des DATES : %d . ecart median %d j . le plus grand %d j"
                  % (len(j), j[len(j) // 2], j[-1]))
            for lib, test in (("1 jour (fuseau ?)", lambda x: x <= 1),
                              ("2 a 31 jours", lambda x: 1 < x <= 31),
                              ("1 a 12 mois", lambda x: 31 < x <= 365),
                              ("⛔ 366 jours pile (un AN d ecart)",
                               lambda x: 365 < x <= 367),
                              ("plus d un an", lambda x: x > 367)):
                k = sum(1 for x in j if test(x))
                if k:
                    print("         %-34s %4d" % (lib, k))
        if euros:
            e = sorted(euros)
            print("      des NOMBRES : %d . ecart median %.0f . le plus grand %.0f"
                  % (len(e), e[len(e) // 2], e[-1]))
            for lib, test in (("moins de 1", lambda x: x < 1),
                              ("1 a 99", lambda x: 1 <= x < 100),
                              ("100 a 999", lambda x: 100 <= x < 1000),
                              ("1 000 et plus", lambda x: x >= 1000)):
                k = sum(1 for x in e if test(x))
                if k:
                    print("         %-34s %4d" % (lib, k))
        if autres:
            print("      ni date ni nombre comparable : %d" % autres)
    print()
    print("⭐⭐ CE QUE CE TRI CHANGE : un ecart de 1 jour n'est pas un desaccord,")
    print("  c'est un fuseau horaire. Un ecart de 366 jours est une faute de saisie.")
    print("  Les melanger dans un total de 630 empeche de decider.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
