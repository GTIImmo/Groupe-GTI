#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SES TROIS QUESTIONS DU 17/11 AU SOIR.                           17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\d1_z3dydc4x_et_les_2_ventes_2026-11-17.py

⛔ LECTURE SEULE.

  ① « Quelle ligne Z3DYDC4X ? » -> on SORT la ligne entiere du Sheet, et les trois
     compromis du bien 28653 en face, pour qu'il tranche sur piece.
  ② « C'est quoi les 2 ventes posables de C6, date ? » -> les deux lignes, avec
     leur date, leur bien, et ce que nous avons deja.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402

AUDIT = RACINE / "notice" / "AUDIT_C5_LOT_B_2026-11-17.csv"


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(lignes))
        return 2
    i_id = entetes.index("ID Unique")
    par_ident = {}
    for rang, l in lignes:
        ident = str(l[i_id] if i_id < len(l) else "").strip()
        if ident:
            par_ident[ident] = (rang, l)

    cl = client()

    # ─── ① Z3DYDC4X ──────────────────────────────────────────────────────────
    print("=== ① LA LIGNE Z3DYDC4X, EN ENTIER ===")
    if "Z3DYDC4X" not in par_ident:
        print("⛔ introuvable au Sheet.")
        return 2
    rang, l = par_ident["Z3DYDC4X"]
    print("   ligne %s du Sheet" % rang)
    for i, nom in enumerate(entetes):
        v = str(l[i] if i < len(l) else "").strip()
        if v and nom:
            print("      %-26s %s" % (nom[:26], re.sub(r"\s+", " ", v)[:70]))
    print()
    print("   ⭐ ET LA LIGNE VOISINE AYIHPHF5, qui porte DEJA la transaction 14111 :")
    if "AYIHPHF5" in par_ident:
        rang2, l2 = par_ident["AYIHPHF5"]
        print("   ligne %s du Sheet" % rang2)
        for i, nom in enumerate(entetes):
            v = str(l2[i] if i < len(l2) else "").strip()
            if v and nom:
                print("      %-26s %s" % (nom[:26], re.sub(r"\s+", " ", v)[:70]))
    print()
    print("   ⭐ LES TRANSACTIONS DU BIEN 28653, CHEZ NOUS :")
    for r in (cl.get("app_affaire_ledger",
                     {"select": "app_affaire_id,kind,state,date,date_acte,montant,"
                                "app_chaine_id,acquereur_json",
                      "hektor_annonce_id": "eq.28653",
                      "order": "app_affaire_id.asc"}) or []):
        lie = cl.get("app_classeur_lien",
                     {"select": "id_unique,role",
                      "app_affaire_id": "eq.%s" % r["app_affaire_id"]}) or []
        acq = str(r.get("acquereur_json") or "")[:46]
        print("      %-8s %-10s %-10s date %-11s acte %-11s %s"
              % (r["app_affaire_id"], r["kind"], r["state"],
                 str(r.get("date") or "-")[:10], str(r.get("date_acte") or "-")[:10],
                 ("LIE a " + lie[0]["id_unique"]) if lie else "libre"))
        if acq and acq not in ("None", "null", ""):
            print("               acquereur : %s" % re.sub(r"\s+", " ", acq))
    print()

    # ─── ② LES 2 VENTES POSABLES ─────────────────────────────────────────────
    print("=== ② LES VENTES POSABLES DE C6 ===")
    with AUDIT.open(encoding="utf-8-sig", newline="") as f:
        manque = list(csv.DictReader(f, delimiter=";"))
    ventes = [m for m in manque if m["type"] == "vente"]
    print("   ventes manquantes au total : %d" % len(ventes))
    for m in ventes:
        sure = m["confiance_du_lien"].strip().lower() in ("sure", "sûre")
        close = m["chaine_VIVANTE"].strip().lower() in ("false", "0", "")
        marque = "✅ POSABLE" if (sure and close) else "⬜ ecartee"
        print()
        print("   %s  %-10s  date du classeur %s  (annee %s)"
              % (marque, m["id_unique"], m["date_classeur"], m["annee"]))
        print("      etat au classeur : %-22s lien : %s . chaine %s"
              % (m["etat_classeur"], m["confiance_du_lien"],
                 "VIVANTE" if not close else "close"))
        print("      annonce %-8s chaine %-8s  ce que la chaine a deja : %s"
              % (m["annonce"], m["chaine"], m["etats_de_la_chaine"]))
        if m["id_unique"] in par_ident:
            _r, ll = par_ident[m["id_unique"]]
            for nom in ("Vendeur", "Acquéreur", "Ville", "Prix", "Commission TTC",
                        "Offre Achat", "Compromis", "Vente Réglée", "Mandat"):
                if nom in entetes:
                    v = str(ll[entetes.index(nom)]
                            if entetes.index(nom) < len(ll) else "").strip()
                    if v:
                        print("         %-16s %s" % (nom, re.sub(r"\s+", " ", v)[:56]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
