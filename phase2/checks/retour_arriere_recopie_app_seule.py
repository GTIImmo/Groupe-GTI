#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE RETOUR ARRIERE DE 26bis-TRANSACTIONS (piece 4 de C.19-d).      15/11/2026

Il retire du registre LOCAL les transactions que la recopie y a fait entrer : la
plage app (>= 1 000 000) ET sans numero Hektor. Rien d'autre, jamais.

    python -X utf8 phase2/checks/retour_arriere_recopie_app_seule.py              <- A BLANC
    python -X utf8 phase2/checks/retour_arriere_recopie_app_seule.py --pour-de-vrai

A BLANC PAR DEFAUT -- meme patron que Console/menage_coffre_documents.js. Un geste
destructif ne part pas sur une faute de frappe.

⚠ IL NE TOUCHE QUE LE LOCAL. Les lignes vivent aussi chez Supabase, ou elles sont
  nees : c'est leur place, et le serveur fait foi pour elles. Si on veut aussi les
  retirer la-haut, c'est un AUTRE geste, et il se fait avec son propre patch SQL.
  ⛔ ET DANS CET ORDRE : le local d'abord. Un local vide avec Supabase rempli, c'est
    l'etat d'avant la piece 4 -- connu, mesure, sans danger. L'inverse laisserait le
    push recreer en ligne ce qu'on vient d'effacer.

⚠ ET IL JUGE SA PART (lecon 31) : apres le geste, il verifie qu'il ne reste AUCUNE
  ligne de la plage sans numero, ET que les voisines sont intactes -- la plage AVEC
  numero (les 340 adoptees) et tout le hors-plage. Un retour arriere qui ne mesure
  que ce qu'il voulait faire ne prouve rien.
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PHASE2 = RACINE / "phase2" / "phase2.sqlite"
PLAGE = 1_000_000
TABLE = "app_affaire_ledger"
POUR_DE_VRAI = "--pour-de-vrai" in sys.argv

CIBLEES = (f"CAST(app_affaire_id AS INTEGER) >= {PLAGE}"
           f" AND (hektor_affaire_id IS NULL"
           f"      OR TRIM(CAST(hektor_affaire_id AS TEXT)) = '')")


def compter(con, ou):
    return con.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE {ou}").fetchone()[0]


def main() -> int:
    if not PHASE2.exists():
        print(f"pas de base locale : {PHASE2}")
        return 2
    con = sqlite3.connect(PHASE2)

    visees = [r[0] for r in con.execute(
        f"SELECT app_affaire_id FROM {TABLE} WHERE {CIBLEES} ORDER BY app_affaire_id")]
    # LES VOISINES, mesurees AVANT : ce sont elles qui diront que le geste a vise juste.
    plage_avec_numero = compter(con, f"CAST(app_affaire_id AS INTEGER) >= {PLAGE}"
                                     f" AND hektor_affaire_id IS NOT NULL"
                                     f" AND TRIM(CAST(hektor_affaire_id AS TEXT)) <> ''")
    hors_plage = compter(con, f"CAST(app_affaire_id AS INTEGER) < {PLAGE}")

    print(f"registre local : {PHASE2}")
    print(f"  a retirer (plage app, sans numero Hektor) : {len(visees)}")
    if visees:
        print("    " + ", ".join(str(v) for v in visees[:20])
              + (" ..." if len(visees) > 20 else ""))
    print(f"  VOISINES a ne pas toucher : {plage_avec_numero} de la plage AVEC numero, "
          f"{hors_plage} hors plage")

    if not visees:
        print("\nrien a retirer -- le registre local est deja dans l'etat d'avant 26bis.")
        return 0
    if not POUR_DE_VRAI:
        print("\nA BLANC : rien n'a ete touche. Relancer avec --pour-de-vrai.")
        return 0

    # SAUVEGARDE DATEE AVANT UN GESTE DESTRUCTIF -- la regle du projet.
    copie = PHASE2.with_name(f"phase2_avant_retour_26bis_{time.strftime('%Y%m%d_%H%M%S')}"
                             f".sqlite")
    print(f"\nsauvegarde : {copie} ...")
    con.close()
    shutil.copy2(PHASE2, copie)
    con = sqlite3.connect(PHASE2)

    curseur = con.execute(f"DELETE FROM {TABLE} WHERE {CIBLEES}")
    con.commit()
    retirees = curseur.rowcount or 0
    print(f"retirees : {retirees}")

    # IL JUGE SA PART, et seulement apres avoir ecrit.
    reste = compter(con, CIBLEES)
    voisines_apres = compter(con, f"CAST(app_affaire_id AS INTEGER) >= {PLAGE}"
                                  f" AND hektor_affaire_id IS NOT NULL"
                                  f" AND TRIM(CAST(hektor_affaire_id AS TEXT)) <> ''")
    hors_apres = compter(con, f"CAST(app_affaire_id AS INTEGER) < {PLAGE}")
    rouges = []
    if retirees != len(visees):
        rouges.append(f"{retirees} retirees pour {len(visees)} visees")
    if reste:
        rouges.append(f"il reste {reste} ligne(s) de la plage sans numero")
    if voisines_apres != plage_avec_numero:
        rouges.append(f"la plage AVEC numero passe de {plage_avec_numero} a "
                      f"{voisines_apres}")
    if hors_apres != hors_plage:
        rouges.append(f"le hors-plage passe de {hors_plage} a {hors_apres}")
    con.close()

    if rouges:
        print("\n⛔ LE RETOUR ARRIERE NE SE JUGE PAS PROPRE : " + " . ".join(rouges))
        print(f"   la base d'avant est intacte dans {copie}")
        return 1
    print(f"\nOK : {retirees} retiree(s), 0 restante, voisines intactes "
          f"({voisines_apres} + {hors_apres}). Sauvegarde : {copie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
