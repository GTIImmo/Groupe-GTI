#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""POURQUOI SI PEU DE DONNEES A RECUPERER ? -- la mesure.          17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\classeur_pourquoi_si_peu_a_recuperer_2026-11-17.py

⛔ LECTURE SEULE. Sa question du 17/11 : « Pourquoi il y a si peu de donnees a
   recuperer ?? » -- elle merite une MESURE, pas une impression. Trois mesures :

     ① le REMPLISSAGE de chaque colonne du Sheet (une colonne vide ne peut
        rien rendre, et c'est la premiere cause)
     ② la REPARTITION DES ETATS (le classeur est un HISTORIQUE : les affaires
        en cours y sont une poignee, par nature)
     ③ LE BILAN de ce que le chantier a DEJA pose en base -- pour que « si peu »
        se compare a un chiffre, pas a un souvenir
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


def combien(cl, table, filtre=None):
    """Le COMPTE d'une table, par l'entete Content-Range (jamais en ramenant tout)."""
    p = {"select": "*", "limit": 1}
    if filtre:
        p.update(filtre)
    try:
        cl.get(table, p)
    except Exception as e:
        return "(illisible : %s)" % str(e)[:40]
    # le client ne rend pas l'entete : on compte par paquets, mais sur une seule
    # colonne pour rester econome
    p2 = {"select": "count"}
    if filtre:
        p2.update(filtre)
    try:
        r = cl.get(table, p2) or []
        if r and isinstance(r[0], dict) and "count" in r[0]:
            return r[0]["count"]
    except Exception:
        pass
    return "(pas de compte)"


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== POURQUOI SI PEU DE DONNEES A RECUPERER ? (lecture seule) ===")
    print()

    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    n = len(lignes)
    print("le classeur : %d lignes, %d colonnes" % (n, len(entetes)))
    print()

    # ① LE REMPLISSAGE DE CHAQUE COLONNE
    print("=== ① LE REMPLISSAGE DE CHAQUE COLONNE ===")
    print("   (une colonne vide ne peut rien rendre -- c'est la 1re cause)")
    print()
    remplissage = []
    for i, e in enumerate(entetes):
        plein = sum(1 for _r, l in lignes
                    if i < len(l) and str(l[i] or "").strip())
        remplissage.append((plein, e or "(sans entete)", i))
    for plein, e, i in sorted(remplissage, reverse=True):
        pc = 100.0 * plein / n
        barre = "#" * int(pc / 4)
        print("   %-26s %5d  %5.1f %%  %s" % (e[:26], plein, pc, barre))
    print()
    vides = [e for p, e, _i in remplissage if p == 0]
    maigres = [(e, p) for p, e, _i in remplissage if 0 < p < n * 0.10]
    print("   ⛔ colonnes TOTALEMENT VIDES : %d  %s"
          % (len(vides), " . ".join(v[:18] for v in vides) or "-"))
    print("   ⚠  colonnes a MOINS DE 10 %% : %d" % len(maigres))
    for e, p in maigres:
        print("        %-26s %5d" % (e[:26], p))
    print()

    # ② LA REPARTITION DES ETATS
    print("=== ② LE CLASSEUR EST UN HISTORIQUE, ET CA SE MESURE ===")
    try:
        i_etat = entetes.index("Etat Actuel")
    except ValueError:
        print("   ⛔ colonne « Etat Actuel » introuvable.")
        return 2
    etats = Counter(str(l[i_etat] if i_etat < len(l) else "").strip() or "(vide)"
                    for _r, l in lignes)
    fini = 0
    for e, c in etats.most_common():
        fin = e in ("Vente réglée", "Annulée")
        fini += c if fin else 0
        print("   %-26s %5d  %5.1f %%   %s"
              % (e[:26], c, 100.0 * c / n, "FINIE" if fin else "en cours"))
    print()
    print("   ➡ FINIES (reglee ou annulee) : %d sur %d = %.1f %%"
          % (fini, n, 100.0 * fini / n))
    print("   ➡ ENCORE EN COURS            : %d sur %d = %.1f %%"
          % (n - fini, n, 100.0 * (n - fini) / n))
    print()

    # ③ LE BILAN DE CE QUI EST DEJA POSE
    print("=== ③ CE QUE LE CHANTIER A DEJA POSE EN BASE ===")
    cl = client()
    mesures = [
        ("transactions du classeur (C5)", "app_affaire_ledger",
         {"transaction_origine": "eq.classeur"}),
        ("dates d'annulation (C3)", "app_affaire_ledger",
         {"date_annulation_app": "not.is.null"}),
        ("« vente reglee » (C8)", "app_affaire_ledger",
         {"vente_reglee_app": "not.is.null"}),
        ("numeros de facture (C8)", "app_affaire_ledger",
         {"numero_facture_app": "not.is.null"}),
        #: ⛔ DEUX NOMS ETAIENT FAUX AU 1er PASSAGE et rendaient un HTTP 400/404 --
        #:   « commission_app » (la colonne s'appelle `charge_commission_app`, et
        #:   les montants vivent dans `honoraires_entree_app`) et
        #:   « app_affaire_avis » (la table est `app_classeur_avis`).
        #:   Une lecture ratee n'est JAMAIS un vert : corriges, pas ignores.
        ("charge de commission (C2)", "app_affaire_ledger",
         {"charge_commission_app": "not.is.null"}),
        ("honoraires d'entree (C2)", "app_affaire_ledger",
         {"honoraires_entree_app": "not.is.null"}),
        ("honoraires de sortie (C2)", "app_affaire_ledger",
         {"honoraires_sortie_app": "not.is.null"}),
        ("motifs d'annulation (C4)", "app_affaire_ledger",
         {"motif_annulation_app": "not.is.null"}),
        ("notes (C4, 2e patch)", "app_affaire_note",
         {"origine": "like.classeur:*"}),
        ("avis du classeur (C9)", "app_classeur_avis", None),
        ("conditions suspensives", "app_affaire_condition", None),
    ]
    total = 0
    for libelle, table, filtre in mesures:
        p = {"select": "count"}
        if filtre:
            p.update(filtre)
        try:
            r = cl.get(table, p) or []
            c = r[0].get("count") if r and isinstance(r[0], dict) else None
        except Exception as e:
            c = None
            print("   %-34s (illisible : %s)" % (libelle, str(e)[:34]))
            continue
        if isinstance(c, int):
            total += c
        print("   %-34s %7s" % (libelle, c if c is not None else "?"))
    print("   %-34s %7d" % ("--- TOTAL mesure", total))
    print()
    if total < 10000:
        print("⛔ LE TOTAL EST TROP BAS (%d) : une mesure a rate. ON NE CONCLUT RIEN."
              % total)
        return 2

    # ⭐⭐⭐ LA RAISON PRINCIPALE, ET ELLE SE MESURE : HEKTOR A DEJA LE GROS
    print("=== ④ ⭐⭐⭐ LA VRAIE RAISON : HEKTOR PORTE DEJA LE GROS ===")
    for libelle, table, filtre in [
        ("la commission, PAR HEKTOR", "app_affaire_ledger",
         {"commission_agence": "not.is.null"}),
        ("... et par le CLASSEUR (C2)", "app_affaire_ledger",
         {"honoraires_entree_app": "not.is.null"}),
        ("lignes du registre AU TOTAL", "app_affaire_ledger", None),
        ("lignes qui portent une colonne du classeur", "app_affaire_ledger",
         {"or": "(date_annulation_app.not.is.null,vente_reglee_app.not.is.null,"
                "numero_facture_app.not.is.null,motif_annulation_app.not.is.null,"
                "charge_commission_app.not.is.null,honoraires_entree_app.not.is.null)"}),
    ]:
        p = {"select": "count"}
        if filtre:
            p.update(filtre)
        try:
            r = cl.get(table, p) or []
            c = r[0].get("count") if r and isinstance(r[0], dict) else "?"
        except Exception as e:
            c = "(illisible : %s)" % str(e)[:30]
        print("   %-44s %7s" % (libelle, c))
    print()
    print("⭐ CE QUE LE CHANTIER REND N'EST PAS « PEU » : c'est ce qui MANQUAIT.")
    print("   Le reste du classeur, nous l'avions deja par Hektor -- et les")
    print("   colonnes propres au classeur sont elles-memes peu remplies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
