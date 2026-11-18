#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RETIRER DU REGISTRE LOCAL LES 5 DOUBLONS DEJA RETIRES CHEZ SUPABASE.   18/11/2026

    python -X utf8 phase2/checks/retirer_doublons_classeur_du_local_2026-11-18.py                 <- A BLANC
    python -X utf8 phase2/checks/retirer_doublons_classeur_du_local_2026-11-18.py --pour-de-vrai

A BLANC PAR DEFAUT -- meme patron que retour_arriere_recopie_app_seule.py. Un geste
destructif ne part pas sur une faute de frappe.

⛔⛔ POURQUOI CE GESTE EXISTE -- LE TROU DU PATCH DU 18/11
  `supabase/patch_retirer_doublons_offres_classeur_2026-11-18.sql` a retire les 5
  offres doublons (1001575, 1001576, 1001577, 1001604, 1001619) CHEZ SUPABASE
  SEULEMENT. Le registre LOCAL les porte encore (mesure du 18/11 a 16:40 : 31 361
  lignes en local contre 31 356 chez Supabase, l'ecart vaut EXACTEMENT ces 5).
  Or le LOCAL est le maitre d'app_affaire_ledger (pull_from_supabase.py:29), et le push
  de la nuit renvoie TOUTES les lignes locales par upsert (ledger_rows_for_push,
  affaire_ledger.py:3211 : SELECT * ; puis upsert l. 3460). Le patch ne les a PAS
  inscrites au journal app_affaire_supprimee, que le run applique en local AVANT de
  pousser (appliquer_les_suppressions, l. 3444).
  ➡ Sans ce geste, le run de 04:00 les RECREE chez Supabase -- et SANS leur marque :
    `transaction_origine` est dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS. Une ligne sans
    numero Hektor et sans marque reveille les lecteurs gardes par la marque, dont le
    filet du worker (poserNumerosManquants, filtre `transaction_origine=is.null`) qui
    le 15/11 avait colle a une ligne du classeur le numero d'une offre Hektor EXISTANTE.
  Le projet l'avait ecrit (retour_arriere_recopie_app_seule.py) : retire d'un seul
  cote, « le push remonte ».

⭐ POURQUOI LE RETRAIT LOCAL SUFFIT CETTE FOIS (dans l'autre sens, il ne suffisait pas) :
  la recopie 26bis ne fait entrer que ce qui est dans la DOUBLURE, et le run la
  rafraichit chez Supabase JUSTE AVANT la recopie -- or Supabase ne les a plus.
  ⛔ Seul interdit d'ici la nuit : NE PAS lancer affaire_ledger.py a la main (il
  relirait la doublure de ce matin, qui les porte encore).

LES GARDES, avant d'ecrire quoi que ce soit :
  ① exactement 5 lignes, ces 5 cles, toutes `transaction_origine = 'classeur'`,
    toutes des offres, toutes sans numero Hektor ;
  ② AUCUNE n'existe plus chez Supabase (lu en direct, avec un temoin positif : une
    ligne connue doit, elle, etre trouvee -- sinon la lecture est ratee, code 2) ;
  ③ une sauvegarde datee DANS LA BASE LOCALE avant le retrait.
IL JUGE SA PART (lecon 31) : apres, plus aucune des 5 ; les voisines intactes (les
autres lignes `classeur`, la plage app avec numero, tout le hors-plage), et le total
local egal a celui de Supabase.
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
SAUVEGARDE = "app_affaire_ledger_avant_doublons_classeur_20261118_local"
CLES = (1001575, 1001576, 1001577, 1001604, 1001619)
#: une ligne `classeur` qui DOIT exister des deux cotes : le temoin positif de la lecture
TEMOIN_PRESENT = 1001425
POUR_DE_VRAI = "--pour-de-vrai" in sys.argv


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- code 2")
    return cgh.SupabaseClient(url, cle, timeout_seconds=60)


def compter(con, ou, params=()):
    return con.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE {ou}", params).fetchone()[0]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not PHASE2.exists():
        print("pas de base locale : %s" % PHASE2)
        return 2
    marques = ",".join("?" * len(CLES))

    # ② SUPABASE NE LES A PLUS -- avec un temoin positif
    cl = client()
    la_haut = cl.get(TABLE, {"select": "app_affaire_id",
                             "app_affaire_id": "in.(%s)" % ",".join(map(str, CLES))}) or []
    temoin = cl.get(TABLE, {"select": "app_affaire_id",
                            "app_affaire_id": "eq.%d" % TEMOIN_PRESENT}) or []
    total_sb = cl.count(TABLE, {"select": "*"})
    print("chez Supabase : %d des 5 cles presentes . temoin %d %s . total %s"
          % (len(la_haut), TEMOIN_PRESENT, "TROUVE" if temoin else "ABSENT", total_sb))
    if not temoin:
        print("⛔ le temoin positif n'est pas lu : lecture ratee, on ne conclut rien (code 2).")
        return 2
    if la_haut:
        print("⛔ Supabase porte encore %s : ce geste n'a pas lieu d'etre (code 1)."
              % [r["app_affaire_id"] for r in la_haut])
        return 1

    con = sqlite3.connect(PHASE2, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    # ① LES 5, ET SEULEMENT ELLES
    visees = con.execute(
        f"SELECT app_affaire_id, kind, transaction_origine, hektor_affaire_id FROM {TABLE}"
        f" WHERE app_affaire_id IN ({marques}) ORDER BY app_affaire_id", CLES).fetchall()
    print("en local : %d ligne(s) visee(s)" % len(visees))
    for v in visees:
        print("   %s %s origine=%s numero_hektor=%s" % v)
    bonnes = [v for v in visees if v[1] == "offre" and v[2] == "classeur"
              and str(v[3] or "").strip() == ""]
    if len(visees) == 0:
        print("✅ rien a retirer : le local ne les porte deja plus (code 0).")
        return 0
    if len(bonnes) != 5 or len(visees) != 5:
        print("⛔ garde : %d ligne(s) conformes sur %d (il en faut 5 et 5) -- RIEN n'est ecrit."
              % (len(bonnes), len(visees)))
        return 1

    # LES VOISINES, mesurees AVANT
    avant = {
        "total": compter(con, "1=1"),
        "classeur_autres": compter(con, f"transaction_origine = 'classeur'"
                                        f" AND app_affaire_id NOT IN ({marques})", CLES),
        "plage_avec_numero": compter(con, "CAST(app_affaire_id AS INTEGER) >= 1000000"
                                          " AND TRIM(COALESCE(CAST(hektor_affaire_id AS TEXT),''))<>''"),
        "hors_plage": compter(con, "CAST(app_affaire_id AS INTEGER) < 1000000"),
    }
    print("voisines AVANT : %s" % avant)
    if not POUR_DE_VRAI:
        print("A BLANC : rien n'est ecrit. Relancer avec --pour-de-vrai.")
        print("   attendu apres : total %d (= Supabase %s) . classeur_autres %d . "
              "plage_avec_numero %d . hors_plage %d"
              % (avant["total"] - 5, total_sb, avant["classeur_autres"],
                 avant["plage_avec_numero"], avant["hors_plage"]))
        return 0

    # ③ LA SAUVEGARDE DATEE, puis le retrait -- une seule transaction
    with con:
        con.execute(f"CREATE TABLE IF NOT EXISTS {SAUVEGARDE} AS SELECT * FROM {TABLE} WHERE 0")
        con.execute(f"INSERT INTO {SAUVEGARDE} SELECT * FROM {TABLE}"
                    f" WHERE app_affaire_id IN ({marques})", CLES)
        n = con.execute(f"SELECT COUNT(*) FROM {SAUVEGARDE}").fetchone()[0]
        if n != 5:
            raise SystemExit("⛔ sauvegarde : %d ligne(s) au lieu de 5 -- annule" % n)
        cur = con.execute(f"DELETE FROM {TABLE} WHERE app_affaire_id IN ({marques})"
                          f" AND transaction_origine = 'classeur'", CLES)
        if cur.rowcount != 5:
            raise SystemExit("⛔ %d ligne(s) retiree(s) au lieu de 5 -- annule" % cur.rowcount)

    # IL JUGE SA PART
    apres = {
        "total": compter(con, "1=1"),
        "classeur_autres": compter(con, "transaction_origine = 'classeur'"),
        "plage_avec_numero": compter(con, "CAST(app_affaire_id AS INTEGER) >= 1000000"
                                          " AND TRIM(COALESCE(CAST(hektor_affaire_id AS TEXT),''))<>''"),
        "hors_plage": compter(con, "CAST(app_affaire_id AS INTEGER) < 1000000"),
        "restantes": compter(con, f"app_affaire_id IN ({marques})", CLES),
    }
    print("APRES : %s" % apres)
    ok = (apres["restantes"] == 0 and apres["total"] == avant["total"] - 5
          and apres["classeur_autres"] == avant["classeur_autres"]
          and apres["plage_avec_numero"] == avant["plage_avec_numero"]
          and apres["hors_plage"] == avant["hors_plage"]
          and apres["total"] == total_sb)
    print("✅ CONFORME" if ok else "⛔ UN ECART -- a regarder avant la nuit")
    print("retour arriere : INSERT INTO %s SELECT * FROM %s;" % (TABLE, SAUVEGARDE))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
