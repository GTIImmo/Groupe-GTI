#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPREUVE de `check_doublures` apres le correctif de fraicheur du 13/10/2026.

LA SOEUR DE `mandat_un_numero`. Meme defaut, meme correctif : `data.recherche_
divergente` tirait un `critical` en comparant le NATIF de ce matin (reecrit par
le run vers 06:49) a la DOUBLURE de la veille (descendue a 07:45, finie entre
08:03 et 08:49 selon les jours), alors que le moniteur passe a 07:48.
Diagnostic pose le 29/08/2026, jamais corrige avant aujourd'hui.

⚠ ON NE LANCE PAS LE MONITEUR COMPLET : il ENVOIE DES E-MAILS. On appelle cette
  seule sonde, qui n'ecrit que dans une liste en memoire, sur une BASE D'ESSAI
  construite ici -- jamais la vraie phase2.sqlite.

    python monitoring/test_recherche_divergente_fraicheur.py
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_gti_health as cgh  # noqa: E402

COLONNES = ("hektor_contact_id TEXT, search_index INTEGER, prix_min TEXT, prix_max TEXT, "
            "surface_min TEXT, pieces_min TEXT, chambre_min TEXT, refreshed_at TEXT")


def _base(dossier: Path, natif_ecrit_le: str | None, descendue: str | None,
          divergente: bool, en_cours: bool = False, avec_pull_state: bool = True) -> Path:
    """Le plus petit phase2.sqlite qui fasse tourner `check_doublures`."""
    (dossier / "phase2").mkdir(parents=True, exist_ok=True)
    chemin = dossier / "phase2" / "phase2.sqlite"
    if chemin.exists():
        chemin.unlink()
    conn = sqlite3.connect(chemin)
    conn.execute("CREATE TABLE app_doublure_journal (releve_le TEXT, doublure TEXT, "
                 "cle TEXT, accord INTEGER, hektor_seul INTEGER, app_seule INTEGER)")
    conn.execute("INSERT INTO app_doublure_journal VALUES "
                 "(?, 'app_contact_search_current', 'cle', 2, 0, 0)",
                 (datetime.now().strftime("%Y-%m-%d"),))
    conn.execute("CREATE TABLE app_contact_search_current (" + COLONNES + ")")
    conn.execute("CREATE TABLE app_contact_search_current__sb (" + COLONNES + ")")
    # une recherche identique des deux cotes, plus une qui diverge si on le demande
    conn.execute("INSERT INTO app_contact_search_current VALUES "
                 "('111', 0, '100000', '200000', '50', '3', '2', ?)", (natif_ecrit_le,))
    conn.execute("INSERT INTO app_contact_search_current__sb VALUES "
                 "('111', 0, '100000', '200000', '50', '3', '2', ?)", (natif_ecrit_le,))
    conn.execute("INSERT INTO app_contact_search_current VALUES "
                 "('222', 0, ?, '300000', '70', '4', '3', ?)",
                 ("150000" if divergente else "120000", natif_ecrit_le))
    conn.execute("INSERT INTO app_contact_search_current__sb VALUES "
                 "('222', 0, '120000', '300000', '70', '4', '3', ?)", (natif_ecrit_le,))
    # le registre des recherches possedees par l'app : VIDE, sinon il excluerait tout
    conn.execute("CREATE TABLE app_search_pending (hektor_contact_id TEXT, search_index INTEGER)")
    if avec_pull_state:
        conn.execute("CREATE TABLE sb_pull_state (table_name TEXT, lignes INTEGER, "
                     "derniere_descente TEXT, dernier_echec TEXT, derniere_complete TEXT)")
        if descendue is not None:
            conn.execute("INSERT INTO sb_pull_state VALUES "
                         "('app_contact_search_current__sb', 2, ?, ?, ?)",
                         (descendue, "copie en cours" if en_cours else None, descendue))
    conn.commit()
    conn.close()
    return chemin


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Les horloges du vrai 13/10 : le natif ecrit a 04:49 UTC (= 06:49 locale),
    # la descente passee a 07:45 LOCALE SANS FUSEAU ECRIT (= 05:45 UTC).
    natif = "2026-10-13T04:49:18+00:00"
    descente_du_jour = "2026-10-13T07:45:03"
    descente_de_la_veille = "2026-10-12T08:15:02"

    scenarios = [
        ("1. copie a jour, rien ne diverge   -> tout va bien",
         dict(natif_ecrit_le=natif, descendue=descente_du_jour, divergente=False),
         "ok", "0 (seuil 0)"),
        ("2. copie a jour, 1 diverge         -> C'EST VRAI, on crie",
         dict(natif_ecrit_le=natif, descendue=descente_du_jour, divergente=True),
         "critical", "different app/Hektor : 1"),
        ("3. copie de la VEILLE, 1 diverge   -> on ne sait pas, on se tait",
         dict(natif_ecrit_le=natif, descendue=descente_de_la_veille, divergente=True),
         "warning", "plus vieille que le natif"),
        ("4. descente EN COURS, 1 diverge    -> on se tait aussi",
         dict(natif_ecrit_le=natif, descendue=descente_du_jour, divergente=True, en_cours=True),
         "warning", "en cours de descente"),
        ("5. pas de ligne de descente        -> on ne devine pas, on crie",
         dict(natif_ecrit_le=natif, descendue=None, divergente=True),
         "critical", "different app/Hektor : 1"),
        ("6. pas de table sb_pull_state      -> on ne devine pas, on crie",
         dict(natif_ecrit_le=natif, descendue=None, divergente=True, avec_pull_state=False),
         "critical", "different app/Hektor : 1"),
        ("7. natif sans date                 -> on ne devine pas, on crie",
         dict(natif_ecrit_le=None, descendue=descente_du_jour, divergente=True),
         "critical", "different app/Hektor : 1"),
    ]

    # ⚠ LE PIEGE DU FUSEAU, celui que `parse_iso` aurait fait tomber : elle lit une
    #   date sans fuseau COMME DE L'UTC, ce qui RAJEUNIT la copie de deux heures --
    #   une copie perimee passerait pour fraiche et la sentinelle crierait.
    decalage = datetime.now().astimezone().utcoffset() or timedelta(0)
    heures = int(decalage.total_seconds() // 3600)
    scenarios.append((
        f"8. PIEGE DU FUSEAU (machine a UTC{heures:+d}) : '08:00' locale parait plus "
        "recent que '07:00+00:00', en verite il est plus vieux",
        dict(natif_ecrit_le="2026-10-13T07:00:00+00:00",
             descendue="2026-10-13T08:00:00", divergente=True),
        "warning" if heures > 1 else "critical",
        "plus vieille que le natif" if heures > 1 else "different app/Hektor : 1",
    ))

    rates = 0
    with tempfile.TemporaryDirectory(prefix="epreuve_doublures_") as tmp:
        racine = Path(tmp)
        for titre, args_base, statut_voulu, mot_voulu in scenarios:
            _base(racine, **args_base)
            moniteur = cgh.Monitor(argparse.Namespace(project_root=str(racine)), None)
            moniteur.check_doublures()
            divergence = [r for r in moniteur.results
                          if r.status_key == "data.recherche_divergente"]
            if len(divergence) != 1:
                print("  ECHEC  " + titre)
                print(f"         {len(divergence)} ligne(s) data.recherche_divergente, attendu 1")
                rates += 1
                continue
            r = divergence[0]
            if r.status != statut_voulu or mot_voulu not in r.message:
                rates += 1
                print("  ECHEC  " + titre)
                print(f"         statut {r.status!r}, attendu {statut_voulu!r}")
                print(f"         message : {r.message}")
            else:
                print(f"  ok     {titre}  [{r.status}]")

    print()
    if rates:
        print(f"{rates} epreuve(s) sur {len(scenarios)} en ECHEC.")
        return 1
    print(f"Les {len(scenarios)} epreuves passent : la soeur se tait quand elle ne peut pas "
          "savoir, ET crie encore quand les criteres divergent pour de vrai.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
