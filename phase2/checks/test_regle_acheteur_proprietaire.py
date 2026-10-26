# -*- coding: utf-8 -*-
"""Essais de la regle « l'acheteur d'une vente n'est pas le mandant du bien »
(phase2/contacts/regle_acheteur_proprietaire.py, 26/10/2026).

    python phase2/checks/test_regle_acheteur_proprietaire.py

Base en memoire : aucun fichier, aucune base reelle, aucun reseau.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.contacts import regle_acheteur_proprietaire as R  # noqa: E402

ECHECS: list[str] = []


def ok(cond: bool, nom: str) -> None:
    print(("  ok   " if cond else "  ECHEC ") + nom)
    if not cond:
        ECHECS.append(nom)


def base(mandats: list[tuple], contacts: list[tuple]) -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE app_mandat (hektor_annonce_id TEXT, mandants_texte TEXT,"
              " payload_json TEXT, versions_json TEXT)")
    c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT, nom TEXT)")
    c.executemany("INSERT INTO app_mandat VALUES (?,?,?,?)", mandats)
    c.executemany("INSERT INTO app_contact_current VALUES (?,?)", contacts)
    return c


def lien(contact, annonce, role, date=None):
    return {"hektor_contact_id": contact, "hektor_annonce_id": annonce,
            "role_contact": role, "transaction_date": date}


def main() -> int:
    print("1. le nom compare : accents, espaces, nom colle a l'adresse")
    ok(R.nom_compare("Coué Valérian") == "COUEVALERIAN", "accents et espace retires")
    ok(R.est_nomme("RENDELA", ["RENDELA CHRISTINE180 chemin des combes"]), "nom colle a l'adresse trouve")
    ok(not R.est_nomme("JACQUIER", ["M. GARCIA Quentin - 89 rue"]), "nom absent non trouve")
    ok(not R.ne_de_la_vente("", ["texte"]), "fiche sans nom : on ne juge pas")
    ok(not R.ne_de_la_vente("X", ["texte"]), "nom d'une lettre : on ne juge pas")

    print("2. le cas du defaut : acheteur absent du texte de Hektor, PRESENT dans le notre")
    c = base(
        [("61730", "M. Quentin GARCIA | M_Mme Florian JACQUIER",           # le NOTRE, pollue
          json.dumps({"mandants": "M. GARCIA Quentin - 89 rue maurice chomel"}),
          json.dumps([{"mandants": "M. GARCIA Quentin - 89 rue maurice chomel"}]))],
        [("10354352", "JACQUIER"), ("10000001", "GARCIA")])
    res = R.couples_nes_de_la_vente(c, [
        lien("10354352", "61730", "mandant"),
        lien("10354352", "61730", "acquereur_vente", "2026-09-25"),
        lien("10000001", "61730", "mandant"),                              # le vendeur
    ])
    ok(res == {("10354352", "61730"): "2026-09-25"}, "l'acheteur est ne de la vente, date de la vente")
    ok(("10000001", "61730") not in res, "le vendeur reste mandant (D3)")

    print("3. le VRAI mandant d'une vente ancienne, nomme dans le texte de Hektor (D5 b)")
    c = base([("19850", None, json.dumps({"mandants": "Loic DESCHAMPS Amandine CELLIERLes raffa"}), "[]")],
             [("10024608", "CELLIER")])
    res = R.couples_nes_de_la_vente(c, [lien("10024608", "19850", "mandant"),
                                        lien("10024608", "19850", "acquereur_vente", "2018-05-04")])
    ok(res == {}, "nomme au mandat : on n'y touche pas")

    print("4. le critere 1 : sans VENTE, rien (le compromis et l'offre ne comptent pas)")
    c = base([("1", None, json.dumps({"mandants": "M. DUPONT"}), "[]")], [("10000002", "MARTIN")])
    res = R.couples_nes_de_la_vente(c, [lien("10000002", "1", "proprietaire"),
                                        lien("10000002", "1", "acquereur_compromis", "2026-08-01"),
                                        lien("10000002", "1", "acquereur_offre", "2026-07-01")])
    ok(res == {}, "un acquereur de compromis reste ce que Hektor dit")
    res = R.couples_nes_de_la_vente(c, [lien("10000002", "1", "acquereur_vente", "2026-08-01")])
    ok(res == {}, "un acheteur SANS lien au bien : rien a juger")

    print("5. deux ventes du meme bien a la meme personne : la plus ancienne date")
    res = R.couples_nes_de_la_vente(c, [lien("10000002", "1", "mandant"),
                                        lien("10000002", "1", "acquereur_vente", "2026-09-01 10:00:00"),
                                        lien("10000002", "1", "acquereur_vente", "2026-03-02")])
    ok(res == {("10000002", "1"): "2026-03-02"}, "date = la premiere vente, coupee au jour")

    print("6. un bien SANS mandat connu : l'acheteur n'est nomme nulle part -> ne de la vente")
    c = base([], [("10000003", "LEROY")])
    res = R.couples_nes_de_la_vente(c, [lien("10000003", "9", "proprietaire"),
                                        lien("10000003", "9", "acquereur_vente", "2026-07-20")])
    ok(res == {("10000003", "9"): "2026-07-20"}, "sans mandat : propriétaire depuis la vente")

    print("7. sans registre des mandats, on REFUSE de juger (jamais de declassement a l'aveugle)")
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT, nom TEXT)")
    try:
        R.couples_nes_de_la_vente(c, [lien("10000004", "5", "mandant"),
                                      lien("10000004", "5", "acquereur_vente", "2026-07-20")])
        ok(False, "aurait du refuser")
    except RuntimeError:
        ok(True, "RuntimeError sans app_mandat")

    print("8. l'interrupteur : eteint par defaut")
    import os
    ancien = os.environ.pop(R.INTERRUPTEUR, None)
    R._ENV_DEJA_CHARGE = True                      # pas de .env dans l'essai
    ok(R.actif() is False, "sans variable : eteint")
    os.environ[R.INTERRUPTEUR] = "1"
    ok(R.actif() is True, "a 1 : allume")
    os.environ.pop(R.INTERRUPTEUR)
    if ancien is not None:
        os.environ[R.INTERRUPTEUR] = ancien

    print()
    print("ECHECS :", len(ECHECS) if ECHECS else 0)
    return 1 if ECHECS else 0


if __name__ == "__main__":
    raise SystemExit(main())
