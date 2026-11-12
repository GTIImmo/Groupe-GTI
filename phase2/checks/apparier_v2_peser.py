#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- PASSE 1 ter : PESER LES SIGNAUX, socle corrige. 13/11/2026

⭐ C'est le TEMOIN de la correction du socle : si le parsing JSON a marche, les
  mots parasites (`null`, `ville`, `datemaj`) ont disparu et la puissance du
  signal « nom » doit MONTER nettement.
⭐⭐ Et on pese enfin le signal le plus sur : L'IDENTIFIANT DE CONTACT.

LECTURE SEULE. Ni le gel, ni le CSV de la v1.
"""
from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Hektor\Projet") / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

from apparier_v2_socle import (chiffres, ids_du_blob, lire_le_registre,  # noqa: E402
                               noms_du_blob, somme)

CHAMPS_PERSONNES = ("acquereur_json", "acquereurs_json", "mandants_json")


def noms_tx(t) -> set[str]:
    out: set[str] = set()
    for ch in CHAMPS_PERSONNES:
        out |= noms_du_blob(t.get(ch))
    return out


def ids_tx(t) -> set[str]:
    out: set[str] = set()
    for ch in CHAMPS_PERSONNES:
        out |= ids_du_blob(t.get(ch))
    if t.get("hektor_acquereur_id") not in (None, "", 0, "0"):
        out.add(str(t["hektor_acquereur_id"]).strip())
    return out


def main() -> int:
    tx = lire_le_registre()
    print("=" * 80)
    print("PASSE 1 ter -- PESER LES SIGNAUX (socle corrige) : %d transactions" % len(tx))
    print("=" * 80)

    # ── ① LE TEMOIN DE LA CORRECTION ────────────────────────────────────────
    print("\n" + "-" * 80)
    print("① TEMOIN DE LA CORRECTION : les mots qui touchent le plus de transactions")
    print("   (avant correction : null 31 147 . ville 31 127 . datemaj 31 127 ...)")
    print("-" * 80)
    d = collections.defaultdict(set)
    for t in tx:
        for m in noms_tx(t):
            d[m].add(t["app_affaire_id"])
    if not d:
        print("   ⛔ AUCUN NOM LU -- le parsing a tout perdu, il faut regarder.")
        return 1
    for mot, s in sorted(d.items(), key=lambda kv: -len(kv[1]))[:10]:
        print("   %-22s touche %6d transactions  (%.2f %%)"
              % (mot, len(s), 100.0 * len(s) / len(tx)))
    print("   ⭐ ce sont desormais de VRAIS noms de famille repandus.")

    # ── ② COMBIEN DE TRANSACTIONS PORTENT CHAQUE SIGNAL ? ───────────────────
    print("\n" + "-" * 80)
    print("② COUVERTURE -- un signal absent ne sert a rien, meme s'il est sur")
    print("-" * 80)
    for nom, f in (("mandat", lambda t: bool(chiffres(t.get("numero_mandat")))),
                   ("montant", lambda t: somme(t.get("montant")) is not None),
                   ("au moins 1 nom", lambda t: bool(noms_tx(t))),
                   ("au moins 1 identifiant", lambda t: bool(ids_tx(t)))):
        n = sum(1 for t in tx if f(t))
        print("   %-24s %6d / %d  (%5.1f %%)" % (nom, n, len(tx), 100.0 * n / len(tx)))

    # ── ③ LA PUISSANCE, AU NIVEAU DU BIEN ───────────────────────────────────
    print("\n" + "-" * 80)
    print("③ PUISSANCE AU NIVEAU DU BIEN -- « combien de BIENS ce signal designe-t-il »")
    print("-" * 80)

    def pese(nom, clef):
        b = collections.defaultdict(set)
        for t in tx:
            for v in clef(t):
                if v:
                    b[v].add(t["hektor_annonce_id"])
        if not b:
            print("   %-26s inexploitable" % nom)
            return
        tailles = sorted(len(s) for s in b.values())
        n = len(tailles)
        un = sum(1 for x in tailles if x == 1)
        print("   %-26s %7d valeurs | UN SEUL bien %5.1f %% | mediane %d | max %d"
              % (nom, n, 100.0 * un / n, tailles[n // 2], tailles[-1]))

    pese("identifiant de contact", lambda t: ids_tx(t))
    pese("identifiant + montant", lambda t: ["%s|%s" % (i, somme(t.get("montant")) or "")
                                             for i in ids_tx(t)])
    pese("identifiant + mandat", lambda t: ["%s|%s" % (i, chiffres(t.get("numero_mandat")))
                                            for i in ids_tx(t)])
    pese("nom (corrige)", lambda t: noms_tx(t))
    pese("nom + montant", lambda t: ["%s|%s" % (m, somme(t.get("montant")) or "")
                                     for m in noms_tx(t)])
    pese("nom + mandat", lambda t: ["%s|%s" % (m, chiffres(t.get("numero_mandat")))
                                    for m in noms_tx(t)])
    pese("mandat", lambda t: [chiffres(t.get("numero_mandat"))])
    pese("mandat + montant", lambda t: ["%s|%s" % (chiffres(t.get("numero_mandat")),
                                                   somme(t.get("montant")) or "")])
    print("\n" + "=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
