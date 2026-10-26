# -*- coding: utf-8 -*-
"""Essai du chantier 2 -- a (⑧ types, C4, 26/10/2026) sur une COPIE de phase2.sqlite :
la nuit du registre des transactions pose NOTRE numero sur chaque vendeur (mandants_json).

    python phase2/checks/test_vendeurs_deux_numeros_sur_copie.py --base <copie.sqlite>

⛔ JAMAIS sur phase2/phase2.sqlite : le script joue la nuit (il ECRIT dans la base
   donnee). Il lit data/hektor.sqlite en LECTURE SEULE. Aucun push, aucun appel a Hektor.
   (R2, dans la nuit, LIT le carnet chez Supabase : une lecture, rien n'est ecrit.)
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync import affaire_ledger as A  # noqa: E402

ECHECS: list[str] = []


def ok(cond: bool, nom: str) -> None:
    print(("  ok   " if cond else "  ECHEC ") + nom)
    if not cond:
        ECHECS.append(nom)


def photo(con) -> dict:
    return {(r[0], r[1], r[2]): (r[3], r[4], r[5], r[6])
            for r in con.execute("SELECT hektor_annonce_id, kind, hektor_affaire_id, mandants_json,"
                                 " acquereurs_json, state, present_in_hektor FROM app_affaire_ledger")}


def vendeurs(texte):
    if not texte:
        return []
    v = json.loads(texte)
    return [v] if isinstance(v, dict) else v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    args = ap.parse_args()
    base = Path(args.base).resolve()
    if base == (ROOT / "phase2" / "phase2.sqlite").resolve():
        print("REFUS : c'est la base de production. Donner une COPIE.")
        return 2
    con = sqlite3.connect(f"file:{base}", uri=True, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("ATTACH DATABASE ? AS hektor", (f"file:{A.HEKTOR_DB}?mode=ro",))
    A._ENV_DEJA_CHARGE = True              # l'essai decide des interrupteurs, pas .env
    os.environ["APP_AFFAIRE_PERSONNES_DEUX_NUMEROS"] = "1"   # comme en production

    print("1. la nuit, interrupteur des vendeurs ETEINT")
    os.environ["APP_AFFAIRE_VENDEURS_DEUX_NUMEROS"] = "0"
    A.refresh_ledger(con, full=True)
    avant = photo(con)
    n_avec = sum(1 for (m, _, _, _) in avant.values() for p in vendeurs(m) if isinstance(p, dict) and "app_contact_id" in p)
    ok(n_avec == 0, f"aucun vendeur ne porte notre numero ({n_avec})")

    print("2. la nuit, interrupteur des vendeurs ALLUME")
    os.environ["APP_AFFAIRE_VENDEURS_DEUX_NUMEROS"] = "1"
    A.refresh_ledger(con, full=True)
    apres = photo(con)
    total = poses = hors_plage = id_change = 0
    absents_total = absents_poses = 0
    for cle, (m, acq, etat, present) in apres.items():
        anciens = vendeurs(avant.get(cle, (None,))[0])
        neufs = vendeurs(m)
        if [p.get("id") for p in anciens if isinstance(p, dict)] != [p.get("id") for p in neufs if isinstance(p, dict)]:
            id_change += 1
        for p in neufs:
            if not isinstance(p, dict):
                continue
            if not present:
                # ⚠ une transaction que Hektor ne liste plus n'est PAS revue par la nuit
                #   (delete-never) : sa liste reste celle d'avant. Mesure du 26/10 : 36
                #   vendeurs (30 compromis, 6 ventes), tous traduisibles -- un rattrapage a part.
                absents_total += 1
                absents_poses += "app_contact_id" in p
                continue
            total += 1
            if "app_contact_id" in p:
                poses += 1
                if int(p["app_contact_id"]) < 10_000_000:
                    hors_plage += 1
    ok(total > 50_000 and poses == total,
       f"vendeurs des transactions VIVANTES avec notre numero : {poses} sur {total} (58 514 le 26/10)")
    print(f"     (transactions que Hektor ne liste plus : {absents_poses} sur {absents_total} vendeurs -- non revues"
          f" par la nuit, a rattraper a part)")
    ok(hors_plage == 0, f"aucun numero hors de notre plage ({hors_plage})")
    ok(id_change == 0, f"`id` (Hektor) inchange sur toutes les transactions ({id_change} differences)")
    autres = sum(1 for k in apres if k in avant and apres[k][1:] != avant[k][1:])
    ok(autres == 0, f"acquereurs et etats inchanges ({autres} differences)")
    ok(set(apres) == set(avant), "aucune transaction gagnee ni perdue")

    print("3. retour arriere : interrupteur ETEINT a nouveau")
    os.environ["APP_AFFAIRE_VENDEURS_DEUX_NUMEROS"] = "0"
    A.refresh_ledger(con, full=True)
    ok(photo(con) == avant, "la nuit eteinte rend EXACTEMENT les octets d'avant")

    con.rollback()
    con.close()
    print()
    print("ECHECS :", len(ECHECS))
    return 1 if ECHECS else 0


if __name__ == "__main__":
    raise SystemExit(main())
