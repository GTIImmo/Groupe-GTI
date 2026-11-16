#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C3 -- POURQUOI 107 DATES D'ANNULATION SONT ANTERIEURES AU COMPROMIS ?  16/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c3_pourquoi_107_anterieures_2026-11-16.py

⛔ LECTURE SEULE. Lit le Sheet et le CSV de la mesure C3. N'ecrit rien en base.

LE FAIT A EXPLIQUER. Avec la regle de Frederic (« la date d'annulation du Sheet est
celle du COMPROMIS »), 450 lignes sont posables -- mais 107 portent une date
d'annulation ANTERIEURE a la date du compromis chez nous. Un compromis annule avant
d'etre signe est absurde. Et l'ecart n'est pas aleatoire :

    1 jour 4 . 2-7 j 36 . 8-30 j 46 . 31-180 j 18 . >180 j 3
    mediane 11 jours . maxi 296 . AUCUN compromis sans date

⭐ L'HYPOTHESE, ET ELLE SE MESURE SANS RIEN SUPPOSER : le classeur porte SA PROPRE
  date de compromis (colonne « Compromis »). Trois reponses possibles, et une seule
  sera vraie :

    A  le classeur est COHERENT avec lui-meme (annulation >= son compromis)
       -> alors c'est NOTRE date de compromis qui differe de la sienne, et le
          rapport du gel a deja mesure ces ecarts : on sait quoi regarder.
    B  le classeur est INCOHERENT avec lui-meme (annulation < son compromis)
       -> alors la saisie du classeur est en cause, et on ne pose rien.
    C  un melange -> on tranche population par population, jamais en bloc.

⛔ ON NE CHOISIT PAS L'EXPLICATION QUI ARRANGE : on compte les trois.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

import apparier_classeur as ap                                      # noqa: E402
from rapport_gel_tous_les_champs import date_du_classeur_tolerante  # noqa: E402

MESURE = RACINE / "notice" / "C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv"
SORTIE = RACINE / "notice" / "C3_LES_107_ANTERIEURES_2026-11-16.csv"


def notre_date(v) -> date | None:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(v or "").strip())
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    with MESURE.open(encoding="utf-8-sig", newline="") as h:
        mesure = list(csv.DictReader(h, delimiter=";"))
    cas = {x["id_unique"]: x for x in mesure if x["verdict"] == "date_anterieure"}
    if not cas:
        print("⛔ aucune ligne « date_anterieure » dans la mesure -- rien a expliquer.")
        return 2
    print("=== POURQUOI %d DATES D'ANNULATION SONT ANTERIEURES AU COMPROMIS ? ===" % len(cas))
    print()

    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes seulement. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    col_id = entetes.index("ID Unique")
    col_comp = entetes.index("Compromis")
    col_annul = entetes.index("Annulée")
    #: ⭐ L'HYPOTHESE COMPLEMENTAIRE : « Annulee » coinciderait-elle avec la date
    #:   d'OFFRE du classeur ? Si oui, ce n'est pas une faute de saisie mais une
    #:   convention (ou un decalage de colonne), et ca se traite autrement.
    col_offre = entetes.index("Offre Achat")
    print("le Sheet : %d lignes . « Compromis » en %d . « Annulee » en %d"
          % (len(lignes), col_comp, col_annul))
    print()

    def case(l, i):
        return l[i] if i < len(l) else ""

    verdicts = Counter()
    detail = []
    for _rang, l in lignes:
        ident = str(case(l, col_id)).strip()
        if ident not in cas:
            continue
        x = cas[ident]
        c_comp = date_du_classeur_tolerante(case(l, col_comp))
        c_annul = date_du_classeur_tolerante(case(l, col_annul))
        c_offre = date_du_classeur_tolerante(case(l, col_offre))
        n_comp = notre_date(x["date_transaction"])
        if c_annul is None:
            v = "classeur : annulation ILLISIBLE"
        elif c_comp is None:
            v = "le classeur n'a PAS de date de compromis"
        elif c_annul >= c_comp:
            v = "A -- le classeur est COHERENT avec lui-meme"
        else:
            v = "B -- le classeur est INCOHERENT avec lui-meme"
        verdicts[v] += 1
        detail.append({
            "id_unique": ident, "annonce": x["annonce"],
            "app_affaire_id": x["app_affaire_id"],
            "compromis_CHEZ_NOUS": x["date_transaction"][:10],
            "compromis_AU_CLASSEUR": c_comp.strftime("%Y-%m-%d") if c_comp else "",
            "offre_AU_CLASSEUR": c_offre.strftime("%Y-%m-%d") if c_offre else "",
            "annulation_AU_CLASSEUR": c_annul.strftime("%Y-%m-%d") if c_annul else "",
            "annulation_EGALE_l_offre": "oui" if (c_offre and c_annul and c_offre == c_annul) else "",
            "ecart_nous_vs_classeur_jours": ((n_comp - c_comp).days
                                             if (n_comp and c_comp) else ""),
            "verdict": v})

    print("=== LE VERDICT, COMPTE ===")
    for v, n in verdicts.most_common():
        print("   %-48s %4d" % (v, n))
    print()
    trouves = sum(verdicts.values())
    print("   lignes retrouvees dans le Sheet : %d sur %d" % (trouves, len(cas)))
    if trouves != len(cas):
        print("   ⚠ %d introuvables -- elles ne sont PAS comptees comme un verdict"
              % (len(cas) - trouves))

    # ⭐ LE CHIFFRE QUI DECIDE : notre date de compromis differe-t-elle de la sienne ?
    ecarts = [d["ecart_nous_vs_classeur_jours"] for d in detail
              if isinstance(d["ecart_nous_vs_classeur_jours"], int)]
    if ecarts:
        print()
        print("=== NOTRE DATE DE COMPROMIS CONTRE CELLE DU CLASSEUR ===")
        memes = sum(1 for e in ecarts if e == 0)
        print("   identiques                  : %4d sur %d" % (memes, len(ecarts)))
        print("   nous PLUS TARD que lui      : %4d" % sum(1 for e in ecarts if e > 0))
        print("   nous PLUS TOT que lui       : %4d" % sum(1 for e in ecarts if e < 0))
        aut = sorted(e for e in ecarts if e != 0)
        if aut:
            print("   ecart median (hors egalite) : %d jours . de %d a %d"
                  % (aut[len(aut) // 2], aut[0], aut[-1]))

    # ⭐ L'HYPOTHESE COMPLEMENTAIRE, COMPTEE
    print()
    print("=== « Annulee » SERAIT-ELLE LA DATE DE L'OFFRE DU CLASSEUR ? ===")
    b = [d for d in detail if d["verdict"].startswith("B")]
    egales = sum(1 for d in b if d["annulation_EGALE_l_offre"] == "oui")
    print("   sur les %d lignes « B » : annulation = offre du classeur  %d" % (len(b), egales))
    entre = 0
    for d in b:
        o, a, c = d["offre_AU_CLASSEUR"], d["annulation_AU_CLASSEUR"], d["compromis_AU_CLASSEUR"]
        if o and a and c and o <= a <= c:
            entre += 1
    print("   annulation TOMBE ENTRE l'offre et le compromis            %d" % entre)
    print("   ⭐ si c'est la quasi-totalite, « Annulee » marque un evenement d'AVANT la")
    print("      signature -- une promesse qui n'a pas abouti -- et non l'annulation")
    print("      d'un compromis signe. C'est alors une DECISION de Frederic, pas un calcul.")

    print()
    print("=== HUIT EXEMPLES ===")
    print("   annonce  compromis NOUS  compromis CLASSEUR  annule CLASSEUR  verdict")
    for d in detail[:8]:
        print("   %-8s %-15s %-19s %-16s %s"
              % (d["annonce"], d["compromis_CHEZ_NOUS"], d["compromis_AU_CLASSEUR"],
                 d["annulation_AU_CLASSEUR"], d["verdict"][:34]))

    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=list(detail[0]))
        w.writeheader()
        w.writerows(detail)
    print()
    print("ecrit : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
