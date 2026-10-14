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
          divergente: bool, en_cours: bool = False, avec_pull_state: bool = True,
          releve_le: str | None = None) -> Path:
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
                 (releve_le or datetime.now().strftime("%Y-%m-%d"),))
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


def _horloge_figee(quand_local: datetime):
    """Un `datetime` dont `now()` rend TOUJOURS l'instant donne.

    POURQUOI. Le defaut d'horloge ne se voit qu'entre minuit et 02:00, c'est-a-dire
    au seul passage de 01:48 -- une fois par nuit. On ne va pas attendre cette nuit
    pour savoir si le correctif tient, et on ne peut pas changer l'heure de la
    machine. On fige donc l'heure que la sonde croit etre.
    """
    aware = quand_local.astimezone()

    class Figee(datetime):
        @classmethod
        def now(cls, tz=None):
            return aware.astimezone(tz) if tz is not None else aware.replace(tzinfo=None)

    return Figee


def epreuve_journal() -> int:
    """3e PARTIE : `data.doublure_journal`, les DEUX defauts du 13/10.

    1. l'horloge : `releve_le` est une date LOCALE comparee a une date UTC ;
    2. la question etait mal posee : le releve est ecrit par la DESCENTE (vers
       08:03-08:49), donc « est-il d'aujourd'hui ? » est faux chaque nuit.

    Mesure sur 10 nuits de journaux AVANT le correctif : 01:48 disait « a jour »
    10 fois sur 10, et 03:48, 05:48, 07:48 avertissaient 10 fois sur 10 -- sur un
    etat parfaitement normal.
    """
    vrai_datetime = cgh.datetime
    rates = 0

    # Le passage de 01:48 locale : en UTC on est encore la VEILLE.
    nuit = datetime(2026, 10, 13, 1, 48, 54)
    # Un passage de plein jour, apres la Descente.
    jour = datetime(2026, 10, 13, 9, 48, 54)

    cas = [
        ("1. 09:48, releve du jour, descente du jour   -> a jour",
         jour, dict(releve_le="2026-10-13", descendue="2026-10-13T07:45:03"),
         "ok", "a jour"),
        ("2. 01:48, releve de la VEILLE, descente de la veille -> NORMAL, on se tait",
         nuit, dict(releve_le="2026-10-12", descendue="2026-10-12T08:15:02"),
         "ok", "NORMAL"),
        ("3. 07:48, releve de la veille, descente de la veille -> NORMAL aussi",
         datetime(2026, 10, 13, 7, 48, 54),
         dict(releve_le="2026-10-12", descendue="2026-10-12T08:15:02"),
         "ok", "NORMAL"),
        # ⚠ LE CAS QUI A RATE LE 14/10 AU MATIN. derniere_descente porte l'heure de
        #   DEPART : a 07:48 la sonde croyait la Descente finie et avertissait, alors
        #   que le releve est sa DERNIERE etape. Voir DELAI_DESCENTE_MINUTES.
        ("3-bis. 07:48, la Descente du jour vient de DEMARRER -> NORMAL, elle tourne",
         datetime(2026, 10, 13, 7, 48, 54),
         dict(releve_le="2026-10-12", descendue="2026-10-13T07:45:03"),
         "ok", "est EN COURS"),
        ("3-ter. 09:40, la Descente dure depuis 1 h 55 -> encore dans le delai",
         datetime(2026, 10, 13, 9, 40, 0),
         dict(releve_le="2026-10-12", descendue="2026-10-13T07:45:03"),
         "ok", "est EN COURS"),
        ("4. 09:48, la DESCENTE a tourne mais pas le releve -> LA VRAIE PANNE",
         jour, dict(releve_le="2026-10-12", descendue="2026-10-13T07:45:03"),
         "warning", "pas fait aujourd'hui"),
        ("5. releve d'AVANT-HIER, descente du jour     -> panne aussi",
         jour, dict(releve_le="2026-10-11", descendue="2026-10-13T07:45:03"),
         "warning", "pas fait aujourd'hui"),
        ("6. pas de sb_pull_state : on ne devine pas   -> comme avant, on avertit",
         nuit, dict(releve_le="2026-10-12", descendue=None, avec_pull_state=False),
         "warning", "pas fait aujourd'hui"),
    ]

    try:
        with tempfile.TemporaryDirectory(prefix="epreuve_journal_") as tmp:
            racine = Path(tmp)
            for titre, quand, args_base, statut_voulu, mot_voulu in cas:
                _base(racine, natif_ecrit_le="2026-10-13T04:49:18+00:00",
                      divergente=False, **args_base)
                cgh.datetime = _horloge_figee(quand)
                moniteur = cgh.Monitor(argparse.Namespace(project_root=str(racine)), None)
                moniteur.check_doublures()
                journal = [r for r in moniteur.results
                           if r.status_key == "data.doublure_journal"]
                if len(journal) != 1:
                    print("  ECHEC  " + titre)
                    print(f"         {len(journal)} ligne(s), attendu 1")
                    rates += 1
                    continue
                r = journal[0]
                if r.status != statut_voulu or mot_voulu not in r.message:
                    rates += 1
                    print("  ECHEC  " + titre)
                    print(f"         statut {r.status!r}, attendu {statut_voulu!r}")
                    print(f"         message : {r.message}")
                else:
                    print(f"  ok     {titre}  [{r.status}]")
    finally:
        cgh.datetime = vrai_datetime
    return rates


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
    print("-- data.doublure_journal : l'horloge, et la question mal posee --")
    rates += epreuve_journal()

    print()
    if rates:
        print(f"{rates} epreuve(s) en ECHEC.")
        return 1
    print(f"Les {len(scenarios)} + 8 epreuves passent : les deux sentinelles de cette sonde "
          "se taisent quand l'etat est normal, ET parlent quand il ne l'est pas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
