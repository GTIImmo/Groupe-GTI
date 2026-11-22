#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE COTE LOCAL DE LA MISE DE COTE DES 3 CICATRICES DE LA FAMILLE 1.        22/11/2026

    python -X utf8 phase2/checks/mettre_de_cote_cicatrices_du_local_2026-11-22.py --verifier-avant   <- AVANT le patch SQL
    python -X utf8 phase2/checks/mettre_de_cote_cicatrices_du_local_2026-11-22.py                    <- A BLANC (apres)
    python -X utf8 phase2/checks/mettre_de_cote_cicatrices_du_local_2026-11-22.py --pour-de-vrai     <- le geste

⛔ FABRIQUE, NON JOUE -- son mot du 22/11 : « fabrique la mise de cote des 5 SANS LA JOUER ». Patron :
  retirer_doublons_classeur_du_local_2026-11-18.py (le trou du 18/11, § 4.6 de l'audit independant).

POURQUOI UN COTE LOCAL : le registre LOCAL est le MAITRE d'app_affaire_ledger (pull_from_supabase.py), et le push de la
nuit renvoie TOUTES ses lignes (ledger_rows_for_push, affaire_ledger.py : SELECT * puis upsert). Retirees chez Supabase
seulement, les 3 copies y REVIENDRAIENT la nuit suivante -- et SANS leur marque (`transaction_origine` est dans
COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS). D'ou : le meme jour, avant la nuit.

⛔⛔ ET L'ORDRE (mesure du 22/11, le vrai chainage rejoue sur copie) : sans 1001563 et 1001580, la nuit d'AUJOURD'HUI
  re-reunit GUERIN / PAYSAC (535 / 3540) et CIMINO / SOUDANI (2388 / 4113). Leur separation ne tient sans elles que par la
  COUPE « C5 aux portes ». --verifier-avant REFUSE tant que les 4 morceaux ne sont pas dans
  phase2/sync/detachements_manuels.csv ET que l'outil de coupe n'est pas allume (APP_CHAINAGE_DETACHEMENTS=1).

LES GARDES (--pour-de-vrai) : ① Supabase ne les a PLUS (avec un temoin positif : 1001425 doit etre lu) ; ② la coupe est
en production ; ③ exactement ces 3 lignes en local, toutes `classeur`, des offres, sans numero Hektor ; ④ REGLE 6 : elles
partent ENTIERES dans une table de garde datee DANS LA BASE LOCALE (avec leur ancien numero de dossier), jamais un
delete sec. IL JUGE SA PART : apres, plus aucune des 3 ; les autres copies, la plage app avec numero et le hors-plage
intacts ; le total local egal a celui de Supabase.
RETOUR ARRIERE : INSERT INTO app_affaire_ledger SELECT * FROM app_affaire_ledger_mise_de_cote_cicatrices_20261122_local;
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
import check_gti_health as cgh                                      # noqa: E402

PHASE2 = RACINE / "phase2" / "phase2.sqlite"
TABLE = "app_affaire_ledger"
SAUVEGARDE = "app_affaire_ledger_mise_de_cote_cicatrices_20261122_local"
CLES = (1001482, 1001563, 1001580)
TEMOIN_PRESENT = 1001425
DETACHEMENTS = RACINE / "phase2" / "sync" / "detachements_manuels.csv"
#: les 4 morceaux de la coupe « C5 aux portes » (brouillon du passage 22, valide par lui le 22/11)
COUPE = ({1875, 1876, 1878}, {1874, 1877}, {11956, 11958, 11960}, {11957, 11959})
POUR_DE_VRAI = "--pour-de-vrai" in sys.argv
VERIFIER_AVANT = "--verifier-avant" in sys.argv


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env", RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- code 2")
    return cgh.SupabaseClient(url, cle, timeout_seconds=60)


def coupe_en_production() -> tuple[bool, str]:
    """Les 4 morceaux dans le fichier de PRODUCTION, et l'outil de coupe allume (le nom de l'interrupteur seul est lu)."""
    for f in (RACINE / ".env",):
        if f.exists():
            cgh.load_env_file(f)
    allume = (os.environ.get("APP_CHAINAGE_DETACHEMENTS") or "0").strip() == "1"
    morceaux = set()
    if DETACHEMENTS.exists():
        for ligne in DETACHEMENTS.read_text(encoding="utf-8-sig").splitlines():
            if ligne.strip() and not ligne.startswith("#") and not ligne.startswith("transactions;"):
                try:
                    morceaux.add(frozenset(int(x) for x in ligne.split(";")[0].split()))
                except ValueError:
                    pass
    manquent = [sorted(m) for m in COUPE if frozenset(m) not in morceaux]
    return (allume and not manquent), ("outil de coupe %s ; morceaux manquants : %s" % (
        "ALLUME" if allume else "ETEINT", manquent or "aucun"))


def compter(con, ou, params=()):
    return con.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE {ou}", params).fetchone()[0]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    if not PHASE2.exists():
        print("pas de base locale : %s" % PHASE2)
        return 2
    ok_coupe, dit = coupe_en_production()
    print("LA COUPE « C5 aux portes » EN PRODUCTION : %s -- %s" % ("OUI" if ok_coupe else "⛔ NON", dit))
    marques = ",".join("?" * len(CLES))
    con = sqlite3.connect(PHASE2, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    visees = con.execute(f"SELECT app_affaire_id, kind, transaction_origine, hektor_affaire_id, app_dossier_numero "
                         f"FROM {TABLE} WHERE app_affaire_id IN ({marques}) ORDER BY app_affaire_id", CLES).fetchall()
    print("en local : %d ligne(s) visee(s)" % len(visees))
    for v in visees:
        print("   %s %s origine=%s numero_hektor=%s dossier=%s" % v)
    bonnes = [v for v in visees if v[1] == "offre" and v[2] == "classeur" and str(v[3] or "").strip() == ""]
    if VERIFIER_AVANT:
        pret = ok_coupe and len(bonnes) == 3 and len(visees) == 3
        print("✅ PRET : la coupe est en production, les 3 sont la -- le patch SQL peut se coller" if pret else
              "⛔ PAS PRET : NE PAS coller le patch SQL (sans la coupe, la nuit re-reunit deux paires de dossiers)")
        return 0 if pret else 1
    cl = client()
    la_haut = cl.get(TABLE, {"select": "app_affaire_id", "app_affaire_id": "in.(%s)" % ",".join(map(str, CLES))}) or []
    temoin = cl.get(TABLE, {"select": "app_affaire_id", "app_affaire_id": "eq.%d" % TEMOIN_PRESENT}) or []
    total_sb = cl.count(TABLE, {"select": "*"})
    print("chez Supabase : %d des 3 presentes . temoin %d %s . total %s" % (len(la_haut), TEMOIN_PRESENT,
                                                                          "TROUVE" if temoin else "ABSENT", total_sb))
    if not temoin:
        print("⛔ le temoin positif n'est pas lu : lecture ratee, on ne conclut rien (code 2).")
        return 2
    if la_haut:
        print("⛔ Supabase les porte encore %s : le patch SQL n'est pas joue -- rien a faire ici (code 1)."
              % [r["app_affaire_id"] for r in la_haut])
        return 1
    if not ok_coupe:
        print("⛔⛔ SUPABASE NE LES A PLUS MAIS LA COUPE N'EST PAS EN PRODUCTION : jouer TOUT DE SUITE l'INVERSE SQL")
        print("   (supabase/patch_mise_de_cote_cicatrices_famille1_2026-11-22_INVERSE.sql) -- RIEN n'est ecrit ici.")
        return 1
    if len(visees) == 0:
        print("✅ rien a mettre de cote : le local ne les porte deja plus (code 0).")
        return 0
    if len(bonnes) != 3 or len(visees) != 3:
        print("⛔ garde : %d ligne(s) conformes sur %d (il en faut 3 et 3) -- RIEN n'est ecrit." % (len(bonnes),
                                                                                                    len(visees)))
        return 1
    avant = {"total": compter(con, "1=1"),
             "classeur_autres": compter(con, f"transaction_origine = 'classeur' AND app_affaire_id NOT IN ({marques})",
                                        CLES),
             "plage_avec_numero": compter(con, "CAST(app_affaire_id AS INTEGER) >= 1000000"
                                               " AND TRIM(COALESCE(CAST(hektor_affaire_id AS TEXT),''))<>''"),
             "hors_plage": compter(con, "CAST(app_affaire_id AS INTEGER) < 1000000")}
    print("voisines AVANT : %s" % avant)
    if not POUR_DE_VRAI:
        print("A BLANC : rien n'est ecrit. Relancer avec --pour-de-vrai.")
        print("   attendu apres : total %d (= Supabase %s) . classeur_autres %d . plage_avec_numero %d . hors_plage %d"
              % (avant["total"] - 3, total_sb, avant["classeur_autres"], avant["plage_avec_numero"], avant["hors_plage"]))
        return 0
    with con:
        con.execute(f"CREATE TABLE IF NOT EXISTS {SAUVEGARDE} AS SELECT * FROM {TABLE} WHERE 0")
        con.execute(f"INSERT INTO {SAUVEGARDE} SELECT * FROM {TABLE} WHERE app_affaire_id IN ({marques})", CLES)
        n = con.execute(f"SELECT COUNT(*) FROM {SAUVEGARDE} WHERE app_affaire_id IN ({marques})", CLES).fetchone()[0]
        if n != 3:
            raise SystemExit("⛔ garde : %d ligne(s) au lieu de 3 -- annule" % n)
        cur = con.execute(f"DELETE FROM {TABLE} WHERE app_affaire_id IN ({marques}) AND transaction_origine = 'classeur'",
                          CLES)
        if cur.rowcount != 3:
            raise SystemExit("⛔ %d ligne(s) mises de cote au lieu de 3 -- annule" % cur.rowcount)
    apres = {"total": compter(con, "1=1"), "classeur_autres": compter(con, "transaction_origine = 'classeur'"),
             "plage_avec_numero": compter(con, "CAST(app_affaire_id AS INTEGER) >= 1000000"
                                               " AND TRIM(COALESCE(CAST(hektor_affaire_id AS TEXT),''))<>''"),
             "hors_plage": compter(con, "CAST(app_affaire_id AS INTEGER) < 1000000"),
             "restantes": compter(con, f"app_affaire_id IN ({marques})", CLES)}
    print("APRES : %s" % apres)
    ok = (apres["restantes"] == 0 and apres["total"] == avant["total"] - 3
          and apres["classeur_autres"] == avant["classeur_autres"]
          and apres["plage_avec_numero"] == avant["plage_avec_numero"] and apres["hors_plage"] == avant["hors_plage"]
          and apres["total"] == total_sb)
    print("✅ CONFORME" if ok else "⛔ UN ECART -- a regarder avant la nuit")
    print("retour arriere : INSERT INTO %s SELECT * FROM %s;" % (TABLE, SAUVEGARDE))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
