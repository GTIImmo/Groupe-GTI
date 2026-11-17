#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D1-1.5 -- L'ETAT REEL DES 6 LIENS, ET LE DEFAUT DE LA TABLE DES LIGNES.
                                                                     17/11/2026
    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\d1_etat_des_6_liens_2026-11-17.py

⛔ LECTURE SEULE.

⛔⛔ LA LISTE DU PLAN DATE DU 13/11 ET ELLE A VIEILLI -- mesure du 17/11 :
     Z3DYDC4X  ligne 3990 -> 14111   ligne connue, transaction la, PAS ENCORE LIEE
     d7cbb8fa  ligne 4790 -> 30806   ⭐ DEJA LIEE depuis
     b7439331  ligne 4791 -> 30809   a lier, mais SA LIGNE EST INCONNUE de la table
     c67ccc6a  ligne 4792 -> 30808   ⭐ DEJA LIEE depuis
     ME6S0TR9  ligne 3406           ⬜ rien a geler (1.4) -- SA DECISION
     6a259cce  ligne 4372           ⬜ rien a geler (1.4) -- SA DECISION
  ➡ « 6 lignes a regeler » est devenu « 1 posable, 2 deja faites, 1 bloquee,
    2 qui demandent une decision ». Une liste de travail se REMESURE avant
    d'etre jouee -- celle-ci avait quatre jours.

⛔⛔ ET LE DEFAUT DE FOND, TROUVE EN LA VERIFIANT : `app_classeur_ligne_id` est
  PERIMEE. Elle porte 4 773 lignes quand le Sheet en a ~4 794, et **14 id_unique
  sont pointes par un lien alors qu'ils ne sont PAS dans cette table**. Or c'est
  elle qui donne le numero de ligne : sans elle, un re-gel ne sait pas quelle
  ligne accrocher. Ce script mesure l'ampleur exacte et NOMME les manquantes.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
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

LES_6 = [("Z3DYDC4X", 3990, 14111, "sûre"), ("d7cbb8fa", 4790, 30806, "sûre"),
         ("b7439331", 4791, 30809, "sûre"), ("c67ccc6a", 4792, 30808, "sûre"),
         ("ME6S0TR9", 3406, None, "à valider"), ("6a259cce", 4372, None, "à valider")]


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


def tout_lire(cl, table, select, ordre):
    out, pas, dep = [], 1000, 0
    while True:
        lot = cl.get(table, {"select": select, "order": ordre,
                             "limit": pas, "offset": dep}) or []
        out.extend(lot)
        if len(lot) < pas:
            return out
        dep += pas


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== D1-1.5 : L'ETAT REEL DES 6 LIENS (lecture seule) ===")
    print()
    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes." % len(lignes))
        return 2
    i_id = entetes.index("ID Unique")
    #: la ligne REELLE de chaque id_unique, telle que le Sheet la donne aujourd'hui
    ligne_du_sheet = {}
    for rang, l in lignes:
        ident = str(l[i_id] if i_id < len(l) else "").strip()
        if ident:
            ligne_du_sheet[ident] = rang
    print("le Sheet : %d lignes, %d id_unique" % (len(lignes), len(ligne_du_sheet)))

    cl = client()
    gel = {str(r["id_unique"]).strip(): r
           for r in tout_lire(cl, "app_classeur_ligne_id",
                              "id_unique,ligne_classeur", "ligne_classeur")}
    liens = tout_lire(cl, "app_classeur_lien",
                      "id_unique,app_affaire_id,role,confiance,gele_par",
                      "ligne_classeur")
    par_ident = {}
    for r in liens:
        par_ident.setdefault(str(r["id_unique"]).strip(), []).append(r)
    print("app_classeur_ligne_id : %d . app_classeur_lien : %d id_unique"
          % (len(gel), len(par_ident)))
    print()

    print("=== ① L'ETAT DES 6, UN PAR UN ===")
    a_lier = []
    for ident, ligne_plan, aff, conf in LES_6:
        dans_gel = ident in gel
        dans_lien = ident in par_ident
        ligne_reelle = ligne_du_sheet.get(ident)
        print("   %-9s  plan: ligne %-5s -> %-7s %s"
              % (ident, ligne_plan, aff if aff else "(aucune)", conf))
        print("             table des lignes : %s . Sheet : ligne %s"
              % ("ligne %s" % gel[ident]["ligne_classeur"] if dans_gel else "⛔ ABSENT",
                 ligne_reelle if ligne_reelle else "⛔ introuvable"))
        if dans_lien:
            for r in par_ident[ident]:
                print("             ⭐ DEJA LIEE : %s/%s -> %s (%s)"
                      % (r["role"], r["confiance"], r["app_affaire_id"], r["gele_par"]))
        else:
            print("             pas encore liee")
        if aff and not dans_lien:
            a_lier.append((ident, ligne_reelle or (gel[ident]["ligne_classeur"]
                                                   if dans_gel else None), aff))
        print()

    print("=== ② ⭐ CE QUI EST REELLEMENT POSABLE ===")
    for ident, ligne, aff in a_lier:
        print("   %-9s ligne %-6s -> transaction %s   %s"
              % (ident, ligne, aff, "✅ posable" if ligne else "⛔ SANS LIGNE"))
    print("   -> %d posable(s) sur les 6 du plan" % sum(1 for _i, l, _a in a_lier if l))
    print()

    print("=== ③ ⛔⛔ LE DEFAUT DE LA TABLE DES LIGNES ===")
    manquants_du_gel = [i for i in ligne_du_sheet if i not in gel]
    print("   id_unique du Sheet ABSENTS de app_classeur_ligne_id : %d"
          % len(manquants_du_gel))
    pointes = [i for i in par_ident if i not in gel]
    print("   ⛔ et pointes par un LIEN alors qu'ils en sont absents : %d" % len(pointes))
    if pointes:
        print("      les voici : %s" % " . ".join(sorted(pointes)))
    print("   ➡ cette table donne LE NUMERO DE LIGNE. Sans elle, un re-gel ne sait")
    print("     pas quelle ligne accrocher -- c'est pour ca que b7439331 est bloquee.")
    print()
    if manquants_du_gel:
        print("   les 12 premiers id_unique du Sheet qu'elle ignore :")
        for i in sorted(manquants_du_gel,
                        key=lambda x: ligne_du_sheet[x])[:12]:
            print("      ligne %-6s %s" % (ligne_du_sheet[i], i))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
