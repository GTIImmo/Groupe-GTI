#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- DIAGNOSTIC : deux zeros a ne pas croire.      13/11/2026

Deux resultats de la passe 1 quater demandent un TEMOIN POSITIF avant d'etre
crus -- regle du projet : « un zero ne se croit pas sans temoin positif ».

  ① « 0 identifiant en commun entre acquereurs_json et app_contact_current »
     -> soit les deux SERIES de numeros diffferent (piege connu du projet),
        soit JE LIS LE MAUVAIS CHAMP. On REGARDE un blob reel.
  ② « 42,5 % des lignes du Sheet ne trouvent AUCUN bien par nom + prix »
     -> soit le PRIX du classeur n'est pas le `montant` de la transaction,
        soit mon intersection de noms est trop stricte. On COMPARE sur des cas
        ou l'on sait deja, par le mandat, de quel bien il s'agit.

LECTURE SEULE.
"""
from __future__ import annotations

import collections
import json
import sqlite3
import sys
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

from apparier_v2_socle import (chiffres, lire_le_registre, lire_le_sheet,  # noqa: E402
                               noms, noms_du_blob, pur, somme)


def main() -> int:
    tx = lire_le_registre()
    print("=" * 80)
    print("DIAGNOSTIC -- deux zeros a ne pas croire")
    print("=" * 80)

    # ── ① QUE CONTIENT VRAIMENT acquereurs_json ? ───────────────────────────
    print("\n" + "-" * 80)
    print("① LE TEMOIN POSITIF : on REGARDE trois blobs reels")
    print("-" * 80)
    montres = 0
    for t in tx:
        b = t.get("acquereurs_json")
        if not b or montres >= 3:
            continue
        s = b.decode("utf-8", "replace") if isinstance(b, (bytes, bytearray)) else str(b)
        if len(s) < 20:
            continue
        print("\n   transaction %s (%s) :" % (t["app_affaire_id"], t["kind"]))
        print("   %s" % s[:420].replace("\n", " "))
        try:
            v = json.loads(s)
            if isinstance(v, dict):
                print("   -> OBJET, cles : %s" % ", ".join(list(v.keys())[:14]))
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                print("   -> TABLEAU de %d, cles du 1er : %s"
                      % (len(v), ", ".join(list(v[0].keys())[:14])))
            else:
                print("   -> %s" % type(v).__name__)
        except Exception as e:                                      # noqa: BLE001
            print("   -> ILLISIBLE : %s" % e)
        montres += 1

    # quels champs d'identifiant existent reellement ?
    print("\n   --- les cles vues dans TOUS les blobs de personnes ---")
    cles = collections.Counter()
    for t in tx[:4000]:
        for ch in ("acquereur_json", "acquereurs_json", "mandants_json"):
            b = t.get(ch)
            if not b:
                continue
            s = b.decode("utf-8", "replace") if isinstance(b, (bytes, bytearray)) else str(b)
            try:
                v = json.loads(s)
            except Exception:                                       # noqa: BLE001
                continue
            pile = [v]
            while pile:
                x = pile.pop()
                if isinstance(x, dict):
                    for k, y in x.items():
                        cles[k] += 1
                        if isinstance(y, (dict, list)):
                            pile.append(y)
                elif isinstance(x, list):
                    pile.extend(x)
    for k, v in cles.most_common(22):
        print("      %-26s %6d" % (k, v))

    # ── ② LE PRIX DU CLASSEUR EST-IL LE MONTANT DE LA TRANSACTION ? ─────────
    print("\n" + "-" * 80)
    print("② LE PRIX DU CLASSEUR CONTRE LE `montant` DE LA TRANSACTION")
    print("   on se place sur les lignes dont le MANDAT designe un seul bien :")
    print("   la, on SAIT de quel bien il s'agit, et on peut comparer les prix.")
    print("-" * 80)
    par_mandat = collections.defaultdict(set)
    montants = collections.defaultdict(set)
    for t in tx:
        m = chiffres(t.get("numero_mandat"))
        if m:
            par_mandat[m].add(t["hektor_annonce_id"])
            v = somme(t.get("montant"))
            if v is not None:
                montants[(m, t["kind"])].add(v)

    entetes, lignes = lire_le_sheet()
    col = {k: next((x for x in entetes if pur(x) == pur(k)), None)
           for k in ("Mandat", "Prix", "Commission TTC", "Etat Actuel", "Acquéreur")}
    print("   colonnes : %s" % col)

    def case(l, nom):
        i = entetes.index(nom) if nom and nom in entetes else None
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    verdict = collections.Counter()
    exemples = []
    for _, l in lignes:
        man = chiffres(case(l, col["Mandat"]))
        if not man or len(par_mandat.get(man, ())) != 1:
            continue
        prix = somme(case(l, col["Prix"]))
        if prix is None:
            verdict["prix illisible"] += 1
            continue
        tous = set()
        for (m, k), s in montants.items():
            if m == man:
                tous |= s
        if not tous:
            verdict["aucun montant chez nous"] += 1
        elif prix in tous:
            verdict["EGAL a un montant  ⭐"] += 1
        else:
            proche = min(tous, key=lambda v: abs(v - prix))
            ecart = abs(proche - prix)
            if ecart <= max(100, 0.01 * prix):
                verdict["a moins de 1 %"] += 1
            else:
                verdict["DIFFERENT"] += 1
                if len(exemples) < 8:
                    exemples.append((man, prix, sorted(tous)[:4]))
    tot = sum(verdict.values())
    print("\n   sur %d lignes dont le mandat designe UN SEUL bien :" % tot)
    for k, v in verdict.most_common():
        print("      %-26s %5d  (%5.1f %%)" % (k, v, 100.0 * v / max(1, tot)))
    if exemples:
        print("\n   exemples de DIFFERENT (mandat . prix du classeur . nos montants) :")
        for man, prix, tous in exemples:
            print("      mandat %-8s classeur %-10s chez nous %s" % (man, prix, tous))

    # ── ③ ET LES NOMS, SE RETROUVENT-ILS ? ──────────────────────────────────
    print("\n" + "-" * 80)
    print("③ LES NOMS DU CLASSEUR SE RETROUVENT-ILS DANS LE BIEN ATTENDU ?")
    print("-" * 80)
    noms_par_bien = collections.defaultdict(set)
    for t in tx:
        for ch in ("acquereur_json", "acquereurs_json", "mandants_json"):
            noms_par_bien[t["hektor_annonce_id"]] |= noms_du_blob(t.get(ch))
    v2 = collections.Counter()
    for _, l in lignes:
        man = chiffres(case(l, col["Mandat"]))
        if not man or len(par_mandat.get(man, ())) != 1:
            continue
        bien = next(iter(par_mandat[man]))
        acq = noms(case(l, col["Acquéreur"]))
        if not acq:
            v2["pas de nom au classeur"] += 1
            continue
        chez = noms_par_bien.get(bien, set())
        inter = acq & chez
        if not chez:
            v2["aucun nom chez nous"] += 1
        elif len(inter) >= 2:
            v2["2 mots ou + en commun  ⭐"] += 1
        elif inter:
            v2["1 seul mot en commun"] += 1
        else:
            v2["AUCUN mot en commun"] += 1
    tot2 = sum(v2.values())
    print("   sur %d lignes :" % tot2)
    for k, v in v2.most_common():
        print("      %-28s %5d  (%5.1f %%)" % (k, v, 100.0 * v / max(1, tot2)))

    print("\n" + "=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
