#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- PASSE 1 quater : LE PIVOT.                    13/11/2026

Ma methode entre par l'IDENTITE RESOLUE EN IDENTIFIANTS, pas par le mandat.
Tout repose donc sur un pivot : **le nom ecrit dans le classeur se resout-il en
un identifiant de contact sans ambiguite ?** Si non, la methode s'effondre, et il
vaut mieux le savoir maintenant que dans six heures.

TROIS MESURES, dans l'ordre :
  ① LES DEUX SERIES DE NUMEROS. ⚠⚠ Piege connu du projet : `hektor_contact_id`
    porte PARFOIS NOTRE numero, et « 43 » peut designer deux personnes selon la
    serie. Avant de croiser, on VERIFIE que les identifiants trouves dans
    `acquereurs_json` existent bien dans `app_contact_current`.
  ② L'AMBIGUITE DU NOM : « NOM PRENOM » designe-t-il un seul contact ?
  ③ ET SURTOUT, LA SEULE QUI COMPTE : une fois le nom du classeur resolu et
    croise avec le PRIX, combien de BIENS reste-t-il ? C'est la mesure qui dit si
    la methode tient.

LECTURE SEULE. Ni le gel, ni le CSV de la v1.
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

from apparier_v2_socle import (ids_du_blob, lire_le_registre, lire_le_sheet,  # noqa: E402
                               noms, pur, somme)

CHAMPS_PERSONNES = ("acquereur_json", "acquereurs_json", "mandants_json")


def main() -> int:
    tx = lire_le_registre()
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("select hektor_contact_id, nom, prenom from app_contact_current")
    contacts = c.fetchall()
    con.close()
    print("=" * 80)
    print("PASSE 1 quater -- LE PIVOT : %d transactions, %d contacts"
          % (len(tx), len(contacts)))
    print("=" * 80)

    # ── ① LES DEUX SERIES DE NUMEROS ────────────────────────────────────────
    print("\n" + "-" * 80)
    print("① LES DEUX SERIES DE NUMEROS -- avant de croiser, on VERIFIE")
    print("-" * 80)
    connus = {str(r[0]).strip() for r in contacts if r[0] not in (None, "")}
    dans_tx: set[str] = set()
    for t in tx:
        for ch in CHAMPS_PERSONNES:
            dans_tx |= ids_du_blob(t.get(ch))
    inter = dans_tx & connus
    print("   identifiants trouves dans les transactions : %6d" % len(dans_tx))
    print("   identifiants connus de app_contact_current  : %6d" % len(connus))
    print("   EN COMMUN                                   : %6d  (%5.1f %% des premiers)"
          % (len(inter), 100.0 * len(inter) / max(1, len(dans_tx))))
    orphelins = sorted(dans_tx - connus)[:10]
    if orphelins:
        print("   ⚠ inconnus (10 premiers) : %s" % ", ".join(orphelins))
    if len(inter) < 0.5 * len(dans_tx):
        print("   ⛔⛔ MOINS DE LA MOITIE SE CROISE : LES DEUX SERIES NE SONT PAS")
        print("       LA MEME CHOSE. La methode doit passer par les NOMS, pas les ids.")
    else:
        print("   ⭐ les deux series se croisent : on peut resoudre nom -> id -> transactions")

    # ── ② L'AMBIGUITE DU NOM ────────────────────────────────────────────────
    print("\n" + "-" * 80)
    print("② « NOM PRENOM » designe-t-il UN SEUL contact ?")
    print("-" * 80)
    par_cle = collections.defaultdict(set)
    for cid, nom, prenom in contacts:
        if cid in (None, ""):
            continue
        cle = " ".join(sorted(noms(nom) | noms(prenom)))
        if cle:
            par_cle[cle].add(str(cid).strip())
    tailles = sorted(len(s) for s in par_cle.values())
    n = len(tailles)
    un = sum(1 for x in tailles if x == 1)
    print("   cles « nom+prenom » distinctes : %d" % n)
    print("   n'en designent QU'UN seul contact : %5.1f %%" % (100.0 * un / max(1, n)))
    print("   mediane %d . max %d" % (tailles[n // 2], tailles[-1]))
    print("   ⚠ un nom qui designe 2 contacts n'est pas forcement 2 PERSONNES :")
    print("     le projet a 356 952 contacts et des doublons connus.")

    # ── ③ LA MESURE QUI DECIDE ──────────────────────────────────────────────
    print("\n" + "-" * 80)
    print("③ LA MESURE QUI DECIDE : nom du classeur + PRIX -> combien de BIENS ?")
    print("-" * 80)
    # index : (mot de nom, montant) -> biens
    from apparier_v2_socle import noms_du_blob
    idx = collections.defaultdict(set)
    for t in tx:
        m = somme(t.get("montant"))
        if m is None:
            continue
        mots: set[str] = set()
        for ch in CHAMPS_PERSONNES:
            mots |= noms_du_blob(t.get(ch))
        for mot in mots:
            idx[(mot, m)].add(t["hektor_annonce_id"])

    entetes, lignes = lire_le_sheet()
    col = {k: next((x for x in entetes if pur(x) == pur(k)), None)
           for k in ("Acquéreur", "Vendeur", "Prix", "ID Unique")}

    def case(l, nom):
        i = entetes.index(nom) if nom in entetes else None
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    compte = collections.Counter()
    for _, l in lignes:
        prix = somme(case(l, col["Prix"])) if col["Prix"] else None
        mots = set()
        if col["Acquéreur"]:
            mots |= noms(case(l, col["Acquéreur"]))
        if col["Vendeur"]:
            mots |= noms(case(l, col["Vendeur"]))
        if prix is None or not mots:
            compte["pas de signal"] += 1
            continue
        biens: set = set()
        premier = True
        for mot in mots:
            s = idx.get((mot, prix))
            if s:
                biens = set(s) if premier else (biens & s) or biens
                premier = False
        if not biens:
            compte["0 bien"] += 1
        elif len(biens) == 1:
            compte["1 bien  ⭐"] += 1
        elif len(biens) <= 3:
            compte["2 ou 3 biens"] += 1
        else:
            compte["4 biens ou +"] += 1

    print("   sur les %d lignes du Sheet :" % len(lignes))
    for k in ("1 bien  ⭐", "2 ou 3 biens", "4 biens ou +", "0 bien", "pas de signal"):
        if compte[k]:
            print("      %-16s %5d  (%5.1f %%)" % (k, compte[k],
                                                   100.0 * compte[k] / len(lignes)))
    print("\n" + "=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
