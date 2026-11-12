#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- PASSE 1 bis : LA MESURE AU BON NIVEAU.        13/11/2026

⛔⛔ POURQUOI CE SECOND FICHIER. Ma premiere mesure demandait « combien de
  TRANSACTIONS un signal designe-t-il ? » et repondait « mediane 3 » pour le
  numero de mandat. J'allais en conclure qu'aucun signal n'identifie rien.
  ⭐ C'ETAIT LA MAUVAISE QUESTION : une affaire porte typiquement TROIS
    transactions (offre + compromis + vente) qui partagent le mandat, le montant
    et l'annonce. « Mediane 3 » ne dit pas « ambigu », il dit « UN DOSSIER
    COMPLET ».
  ➡ La bonne question se pose a DEUX niveaux :
       niveau DOSSIER   combien d'affaires distinctes ce signal designe-t-il ?
                        -> c'est lui qui dit si le signal IDENTIFIE
       niveau GENRE     une fois le dossier trouve, le genre de la ligne
                        (offre / compromis / vente) choisit la transaction
  ⭐ Et on mesure sur l'ANNONCE, pas sur la chaine : une chaine est RECALCULEE
    chaque nuit, l'annonce ne bouge pas. (Regle du plan : « un numero de chaine
    ne doit jamais servir de point d'accrochage ».)

LECTURE SEULE. Ni le gel, ni le CSV de la v1, ni sa logique.
"""
from __future__ import annotations

import collections
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass


def sans_accent(t) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(t or ""))
                   if unicodedata.category(c) != "Mn")


def chiffres(t) -> str:
    return "".join(c for c in str(t or "") if c.isdigit())


def somme(t):
    s = sans_accent(str(t or "")).strip()
    if not s:
        return None
    s = re.sub(r"[^0-9.,\-]", "", s.replace(" ", ""))
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") \
            else s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        v = float(s or 0)
    except ValueError:
        return None
    return int(round(v)) if v else None


MOTS_VIDES = {
    "mr", "mme", "mlle", "monsieur", "madame", "mademoiselle",
    "sci", "sarl", "sas", "sasu", "eurl", "scp", "snc", "indivision",
    "et", "ou", "de", "du", "des", "la", "le", "les", "ep", "epoux",
    "veuve", "vve", "nee", "consorts", "succession", "hoirie",
}


def noms(t) -> set[str]:
    mots = re.split(r"[^A-Za-z\u00c0-\u024f]+", sans_accent(t or ""))
    return {m.lower() for m in mots if len(m) >= 3 and m.lower() not in MOTS_VIDES}


def main() -> int:
    con = sqlite3.connect("file:%s?mode=ro"
                          % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""
        select app_affaire_id, kind, date, montant, numero_mandat,
               hektor_annonce_id, acquereur_json, acquereurs_json, mandants_json
          from app_affaire_ledger
    """)
    cols = [d[0] for d in c.description]
    tx = [dict(zip(cols, r)) for r in c.fetchall()]
    print("=" * 78)
    print("PASSE 1 bis -- LA MESURE AU BON NIVEAU : %d transactions" % len(tx))
    print("=" * 78)

    # ── ① LE SIGNAL IDENTIFIE-T-IL UNE ANNONCE (= un bien) ? ────────────────
    print("\n" + "-" * 78)
    print("① AU NIVEAU DU BIEN (l'annonce -- elle NE BOUGE PAS)")
    print("   « combien de BIENS distincts ce signal designe-t-il ? »")
    print("-" * 78)

    def pese_bien(nom, clef):
        d = collections.defaultdict(set)
        for t in tx:
            for v in clef(t):
                if v:
                    d[v].add(t["hektor_annonce_id"])
        if not d:
            print("   %-24s inexploitable" % nom)
            return
        tailles = sorted(len(s) for s in d.values())
        n = len(tailles)
        un = sum(1 for x in tailles if x == 1)
        deux = sum(1 for x in tailles if x == 2)
        print("   %-24s %6d valeurs | UN SEUL bien %5.1f %% | deux %4.1f %% | "
              "mediane %d | max %d"
              % (nom, n, 100.0 * un / n, 100.0 * deux / n, tailles[n // 2], tailles[-1]))

    def noms_tx(t):
        out = set()
        for ch in ("acquereur_json", "acquereurs_json", "mandants_json"):
            out |= noms(t.get(ch))
        return out

    pese_bien("mandat", lambda t: [chiffres(t.get("numero_mandat"))])
    pese_bien("montant", lambda t: [str(somme(t.get("montant")) or "")])
    pese_bien("mandat+montant", lambda t: ["%s|%s" % (chiffres(t.get("numero_mandat")),
                                                      somme(t.get("montant")) or "")])
    pese_bien("1 mot de nom", lambda t: noms_tx(t))
    pese_bien("nom+montant", lambda t: ["%s|%s" % (m, somme(t.get("montant")) or "")
                                        for m in noms_tx(t)])
    pese_bien("nom+mandat", lambda t: ["%s|%s" % (m, chiffres(t.get("numero_mandat")))
                                       for m in noms_tx(t)])

    # ── ② LE GENRE DEPARTAGE-T-IL DANS UN BIEN ? ────────────────────────────
    print("\n" + "-" * 78)
    print("② UNE FOIS LE BIEN TROUVE, le GENRE suffit-il a choisir LA transaction ?")
    print("-" * 78)
    par_bien = collections.defaultdict(lambda: collections.Counter())
    for t in tx:
        par_bien[t["hektor_annonce_id"]][t["kind"]] += 1
    tot = len(par_bien)
    for genre in ("offre", "compromis", "vente"):
        c2 = collections.Counter(min(par_bien[b][genre], 4) for b in par_bien)
        print("   %-10s : 0 -> %5d biens . 1 -> %5d . 2 -> %4d . 3 -> %4d . 4+ -> %4d"
              % (genre, c2[0], c2[1], c2[2], c2[3], c2[4]))
    uniques = sum(1 for b in par_bien
                  if all(par_bien[b][g] <= 1 for g in ("offre", "compromis", "vente")))
    print("\n   ⭐ biens ou CHAQUE genre est present AU PLUS UNE FOIS : %d / %d  (%.1f %%)"
          % (uniques, tot, 100.0 * uniques / tot))
    print("      -> pour ceux-la, « le bien + le genre » IDENTIFIE la transaction")

    # ── ③ LE MOT DE NOM QUI TOUCHE TOUT -- mon max de 31 147 ────────────────
    print("\n" + "-" * 78)
    print("③ LE MOT DE NOM PARASITE -- mon premier calcul donnait max 31 147")
    print("-" * 78)
    d = collections.defaultdict(set)
    for t in tx:
        for m in noms_tx(t):
            d[m].add(t["app_affaire_id"])
    pires = sorted(d.items(), key=lambda kv: -len(kv[1]))[:12]
    for mot, s in pires:
        print("   %-22s touche %6d transactions" % (mot, len(s)))
    print("   ➡ ces mots ne sont PAS des noms : ils doivent partir de la liste.")

    print("\n" + "=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
