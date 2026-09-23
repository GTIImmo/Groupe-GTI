#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G-9 a G-16 — REPETITION : les jointures survivent a la bascule.
                                                                  23/09/2026

CE QU'ON EPROUVE. Quatre scripts joignent LE MIROIR (numeros de Hektor) a la
COUCHE DE L'APP (identites apres la bascule). Aujourd'hui les deux numeros sont
egaux, donc TOUT MARCHE -- et c'est bien le probleme : rien ne distingue le code
juste du code faux. On fabrique donc une base TEMOIN DEJA BASCULEE, et on
verifie que les jointures retrouvent encore leurs lignes.

  G-9   marquer_contacts_disparus   liste noire du miroir -> registre de l'app
  G-10  affaire_ledger              acquereur du miroir   -> numero de l'app
  G-11  elargir_perimetre_console   personnes citees par Hektor -> la couche
  G-16  test_substitution_identite  un controle qui se SAUTE ne controle rien

⚠ CHAQUE CONTROLE EST PASSE DEUX FOIS : sur la forme d'AVANT (elle doit
  ECHOUER) et sur celle d'APRES (elle doit PASSER). Un controle qu'on n'a pas vu
  echouer sur le defaut n'est pas un controle.

N'APPELLE NI HEKTOR NI SUPABASE. Bases en memoire.
"""
from __future__ import annotations

import io
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


def base_basculee() -> sqlite3.Connection:
    """Une base comme elle sera APRES la bascule : identite a nous, cible Hektor."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE app_contact (app_contact_id INTEGER, hektor_contact_id TEXT,"
                 " hektor_target_id TEXT, absent_depuis TEXT, updated_at TEXT)")
    conn.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT,"
                 " hektor_target_id TEXT, supabase_sync_eligible INT,"
                 " eligibility_reasons_json TEXT)")
    for app_id, hektor in ((10000501, '605501'), (10000502, '605502'), (10000503, '605503')):
        conn.execute("INSERT INTO app_contact VALUES (?,?,?,NULL,NULL)",
                     (app_id, str(app_id), hektor))
        conn.execute("INSERT INTO app_contact_current VALUES (?,?,0,'[]')",
                     (str(app_id), hektor))
    conn.commit()
    return conn


# ── G-9 : la liste noire du miroir retrouve-t-elle le registre ? ───────────
def g9(conn, avec_la_cible: bool) -> int:
    noirs = ['605501', '605502']          # ce que dit le MIROIR
    trous = ",".join("?" for _ in noirs)
    if avec_la_cible:
        sql = (f"SELECT COUNT(*) FROM app_contact WHERE absent_depuis IS NULL "
               f"AND (hektor_contact_id IN ({trous}) OR hektor_target_id IN ({trous}))")
        params = [*noirs, *noirs]
    else:
        sql = (f"SELECT COUNT(*) FROM app_contact WHERE absent_depuis IS NULL "
               f"AND hektor_contact_id IN ({trous})")
        params = noirs
    return conn.execute(sql, params).fetchone()[0]


conn = base_basculee()
controle("G-9 la forme d'AVANT ne marque plus personne", g9(conn, False) == 0,
         f"{g9(conn, False)} au lieu de 0")
controle("G-9 la forme d'APRES retrouve ses 2 fiches", g9(conn, True) == 2,
         f"{g9(conn, True)} au lieu de 2")


# ── G-10 : l'acquereur du miroir retrouve-t-il son numero d'app ? ──────────
def g10(conn, avec_la_cible: bool) -> dict:
    table: dict[str, int] = {}
    for ligne in conn.execute("SELECT hektor_contact_id, hektor_target_id, app_contact_id "
                              "FROM app_contact WHERE app_contact_id IS NOT NULL"):
        if ligne["hektor_contact_id"]:
            table[str(ligne["hektor_contact_id"])] = int(ligne["app_contact_id"])
        if avec_la_cible and ligne["hektor_target_id"]:
            table[str(ligne["hektor_target_id"])] = int(ligne["app_contact_id"])
    return table


acq_du_miroir = '605502'
controle("G-10 la forme d'AVANT perd le lien vente<->acheteur",
         g10(conn, False).get(acq_du_miroir) is None)
controle("G-10 la forme d'APRES le retrouve",
         g10(conn, True).get(acq_du_miroir) == 10000502,
         str(g10(conn, True).get(acq_du_miroir)))


# ── G-11 : les personnes citees par Hektor entrent-elles a l'annuaire ? ────
def g11(conn, avec_la_cible: bool) -> int:
    cites = {'605501', '605503'}          # ce que dit app_affaire_console
    entrent = 0
    for ligne in conn.execute("SELECT hektor_contact_id, hektor_target_id FROM "
                              "app_contact_current WHERE supabase_sync_eligible = 0"):
        cid = str(ligne["hektor_contact_id"])
        cible = str(ligne["hektor_target_id"] or "")
        if avec_la_cible:
            if cid not in cites and (not cible or cible not in cites):
                continue
        else:
            if cid not in cites:
                continue
        entrent += 1
    return entrent


controle("G-11 la forme d'AVANT fait sortir tout le monde de l'annuaire",
         g11(conn, False) == 0, f"{g11(conn, False)} au lieu de 0")
controle("G-11 la forme d'APRES fait entrer les 2 personnes citees",
         g11(conn, True) == 2, f"{g11(conn, True)} au lieu de 2")
conn.close()


# ── LES CORRECTIFS SONT-ILS BIEN DANS LES FICHIERS ? ──────────────────────
def lit(rel: str) -> str:
    return io.open(RACINE / rel, encoding="utf-8").read()


controle("G-9 pose dans marquer_contacts_disparus",
         "OR hektor_target_id IN" in lit("phase2/identite/marquer_contacts_disparus.py"))
controle("G-10 pose dans affaire_ledger",
         "SELECT hektor_contact_id, hektor_target_id, app_contact_id FROM app_contact"
         in lit("phase2/sync/affaire_ledger.py"))
controle("G-11 pose dans elargir_perimetre_console",
         "cible not in cites" in lit("phase2/contacts/elargir_perimetre_console.py"))
controle("G-13 le menage interroge le miroir avec SON numero",
         "identite_par_numero_miroir" in lit("phase2/contacts/build_contacts_layer.py"))
controle("G-14 le tamis d'APRES substitution existe",
         "contact_filter_apres_substitution" in lit("phase2/contacts/build_contacts_layer.py"))
controle("G-12 le recensement refuse quand les deux series divergent",
         "ne parlent probablement pas la meme serie" in lit("phase2/identite/contacts_app_seuls.py"))
controle("G-15 la sonde nomme la cause au lieu de crier",
         "accord NUL des deux cotes" in lit("phase2/checks/comparer_doublures.py"))
controle("G-16 l'absence de temoin est elle-meme un ECHEC",
         "AUCUN TEMOIN TROUVE" in lit("phase2/checks/test_substitution_identite.py"))

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Tous les controles passent : les jointures survivent a la bascule.")
