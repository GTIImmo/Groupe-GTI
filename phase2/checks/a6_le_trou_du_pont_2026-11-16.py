#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A6 -- CE QUE LE RAPATRIEMENT NE VERRA PAS.                         16/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\a6_le_trou_du_pont_2026-11-16.py

⛔ LECTURE SEULE. Lit le Sheet et Supabase. N'ecrit rien en base ni chez Hektor.

POURQUOI A6 OUVRE L'ORDRE (audit du 16/11 au soir). Le critere de l'ordre n'est pas
« du plus facile au plus dur » : c'est **ce qui dit ce que les autres ne verront pas
passe d'abord**. C8 et C9 vont rapatrier Y, AA, AH, AI, AJ et C en passant par le
pont -- or le pont a DEUX trous, et aucun des deux ne se signale :

    TROU 1  des lignes du Sheet ABSENTES de `app_classeur_ligne_id` : elles n'ont
            meme pas de numero de ligne chez nous. Mesure du soir : 4 773 contre
            4 791 -> 18.
    TROU 2  des lignes QUI ONT un numero mais AUCUN LIEN dans `app_classeur_lien` :
            elles ont une identite, pas de destination. Le plan en annonce 85.

Rapatrier d'abord et decouvrir ensuite que N lignes n'ont jamais eu de place chez
nous, c'est rapatrier avec un trou et ne le savoir qu'apres.

⭐ CE SCRIPT NE SE CONTENTE PAS DE LES COMPTER : il mesure CE QU'ELLES PORTENT dans
  les colonnes de C8 et de C9. Un trou de 18 lignes vides ne coute rien ; un trou de
  18 lignes qui portent 18 numeros de facture en coute 18.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
sys.path.insert(0, str(RACINE / "monitoring"))

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402

SORTIE = RACINE / "notice" / "A6_LE_TROU_DU_PONT_2026-11-16.csv"
LOT_API = 60

#: Les colonnes que C8 et C9 doivent rapatrier, par leur LETTRE -- la seule facon de
#: ne pas se tromper si un libelle change (meme choix que A1).
COLONNES = {"Y": "C8 Vente Reglee", "AA": "C8 Numero de facture",
            "AH": "C9 Avis a envoyer", "AI": "C9 Commentaire avis",
            "AJ": "C9 Avis envoye", "C": "C9 Numero de mandat",
            "Z": "C3 Annulee (deja posee)"}


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- rien n'est mesure.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def tout_lire(cl, table, select, par_page=1000):
    """⚠ Sans pagination, PostgREST s'arrete a 1 000 lignes EN SILENCE -- et on
    croirait le pont plus petit qu'il n'est. On lit jusqu'a la page courte."""
    out, debut = [], 0
    while True:
        r = cl.get(table, {"select": select, "limit": str(par_page),
                           "offset": str(debut), "order": "ligne_classeur"}) or []
        out.extend(r)
        if len(r) < par_page:
            return out
        debut += par_page


def index_de(lettre: str) -> int:
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== A6 -- CE QUE LE RAPATRIEMENT NE VERRA PAS (lecture seule) ===")
    print()

    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    col_id = entetes.index("ID Unique")
    print("le Sheet : %d lignes de corps" % len(lignes))

    cl = client()
    ids_connus = {str(r["id_unique"]).strip()
                  for r in tout_lire(cl, "app_classeur_ligne_id", "id_unique,ligne_classeur")
                  if r.get("id_unique")}
    relies = {str(r["id_unique"]).strip()
              for r in tout_lire(cl, "app_classeur_lien", "id_unique,ligne_classeur")
              if r.get("id_unique")}
    print("app_classeur_ligne_id : %d identites" % len(ids_connus))
    print("app_classeur_lien     : %d identites RELIEES" % len(relies))
    print()

    def case(l, lettre):
        i = index_de(lettre)
        return str(l[i] if i < len(l) else "").strip()

    absentes, orphelines, detail = [], [], []
    sans_id = 0
    for rang, l in lignes:
        ident = str(l[col_id] if col_id < len(l) else "").strip()
        if not ident:
            sans_id += 1
            continue
        if ident not in ids_connus:
            verdict = "ABSENTE de app_classeur_ligne_id"
            absentes.append((rang, ident, l))
        elif ident not in relies:
            verdict = "connue mais AUCUN LIEN dans le gel"
            orphelines.append((rang, ident, l))
        else:
            continue
        ligne = {"verdict": verdict, "rang_sheet": rang, "id_unique": ident}
        for lettre, quoi in COLONNES.items():
            ligne[quoi] = case(l, lettre)
        detail.append(ligne)

    print("=== LES DEUX TROUS DU PONT ===")
    print()
    print("TROU 1  ABSENTES de app_classeur_ligne_id   : %4d  (le plan disait 17-18)"
          % len(absentes))
    print("TROU 2  connues mais SANS AUCUN LIEN        : %4d  (le plan disait 85)"
          % len(orphelines))
    print("        lignes du Sheet SANS « ID Unique »  : %4d" % sans_id)
    print("        -> en tout %d lignes hors de portee de C8 et C9"
          % (len(absentes) + len(orphelines) + sans_id))
    print()

    # ⭐ LE CHIFFRE QUI COMPTE : ce que ces lignes PORTENT.
    print("=== CE QUE CES LIGNES PORTENT -- le cout reel du trou ===")
    print()
    print("   colonne                      absentes   orphelines")
    for lettre, quoi in COLONNES.items():
        a = sum(1 for _r, _i, l in absentes if case(l, lettre))
        o = sum(1 for _r, _i, l in orphelines if case(l, lettre))
        print("   %-28s %6d     %6d" % (quoi, a, o))
    print()
    vides_a = sum(1 for _r, _i, l in absentes
                  if not any(case(l, x) for x in COLONNES))
    vides_o = sum(1 for _r, _i, l in orphelines
                  if not any(case(l, x) for x in COLONNES))
    print("   ENTIEREMENT VIDES sur ces colonnes : %d des %d absentes . %d des %d orphelines"
          % (vides_a, len(absentes), vides_o, len(orphelines)))
    print("   ⭐ une ligne vide sur TOUTES ces colonnes ne coute RIEN au rapatriement :")
    print("      c'est le reste qui chiffre le trou.")

    if absentes:
        print()
        print("=== LES ABSENTES, UNE PAR UNE (elles n'ont meme pas de numero chez nous) ===")
        print("   rang  id_unique   mandat            Y / AA / AH / AJ")
        for rang, ident, l in absentes[:25]:
            print("   %5s %-11s %-17s %s"
                  % (rang, ident, case(l, "C")[:17],
                     " / ".join(case(l, x)[:12] or "-" for x in ("Y", "AA", "AH", "AJ"))))
        if len(absentes) > 25:
            print("   ... et %d autres (tout est dans le CSV)" % (len(absentes) - 25))

    if orphelines:
        print()
        print("=== LES ORPHELINES : leur ANNEE de vente reglee, pour situer ===")
        ans = Counter((case(l, "Y")[-4:] if len(case(l, "Y")) >= 4 else "(vide)")
                      for _r, _i, l in orphelines)
        for a, nb in sorted(ans.items())[:12]:
            print("   %-10s %4d" % (a, nb))

    if detail:
        with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, delimiter=";", fieldnames=list(detail[0]))
            w.writeheader()
            w.writerows(detail)
        print()
        print("ecrit : %s" % SORTIE)
    print()
    print("⛔ RIEN N'A ETE ECRIT. A6 est une MESURE : elle dit ou sont les trous,")
    print("   elle ne les bouche pas (ca, c'est B2 et le re-gel).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
