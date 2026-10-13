#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPREUVE de la fraicheur de copie ajoutee a `mandat_un_numero` le 13/10/2026.

POURQUOI UNE BASE EN MEMOIRE. Le cas qu'on veut eprouver -- « la copie est plus
vieille que le registre » -- ne se produit qu'entre 06:56 et ~07:58, et on ne va
pas attendre demain matin pour savoir si le correctif tient. Ni ecrire dans
phase2.sqlite en pleine journee pour le provoquer : le run tient le fichier, et
une base d'essai est de toute facon plus lisible qu'une vraie base abimee.

⚠ LE CAS QUI MARCHE NE PROUVE RIEN. La mesure rendait deja « 0 ecart » avant le
  correctif ; ce qu'il faut prouver, c'est qu'elle SE TAIT quand la copie est en
  retard, et surtout QU'ELLE CRIE ENCORE quand le push a vraiment echoue.

LECTURE SEULE sur la vraie base -- celle-ci n'est jamais ouverte.
    python phase2/checks/test_mandat_un_numero_fraicheur.py
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mandat_un_numero as mun  # noqa: E402


def _base(registre: list[tuple], copie: list[tuple], descendue: str | None,
          en_cours: bool = False, vu_le: str | None = None) -> sqlite3.Connection:
    """Une base d'essai minimale : le registre, sa copie, et l'etat du descendeur."""
    conn = sqlite3.connect(":memory:")
    for table in ("app_mandat", "app_mandat__sb"):
        conn.execute(
            f"CREATE TABLE {table} (app_mandat_id INTEGER, hektor_annonce_id TEXT, "
            "numero_mandat TEXT, last_seen_at TEXT)"
        )
    conn.executemany(
        "INSERT INTO app_mandat VALUES (?,?,?,?)",
        [(i, a, n, vu_le) for i, a, n in registre],
    )
    conn.executemany(
        "INSERT INTO app_mandat__sb VALUES (?,?,?,?)",
        [(i, a, n, vu_le) for i, a, n in copie],
    )
    conn.execute(
        "CREATE TABLE sb_pull_state (table_name TEXT, lignes INTEGER, "
        "derniere_descente TEXT, dernier_echec TEXT, derniere_complete TEXT)"
    )
    if descendue is not None:
        conn.execute(
            "INSERT INTO sb_pull_state VALUES ('app_mandat__sb', ?, ?, ?, ?)",
            (len(copie), descendue, "copie en cours" if en_cours else None, descendue),
        )
    return conn


def epreuve_sentinelle() -> int:
    """2e PARTIE : LE MOT QUE LA SENTINELLE DIT.

    La formule peut avoir raison et la sentinelle crier quand meme -- c'est
    exactement ce qui s'est passe : la mesure voyait 4 absents (vrai pour la
    copie qu'elle avait) et le moniteur en faisait un « le push n'est pas
    passe » (faux). On eprouve donc la BRANCHE du moniteur, avec le vrai code.

    ⚠ ON N'APPELLE QUE CETTE SONDE. Le moniteur complet ENVOIE DES E-MAILS ;
      `check_mandat_un_numero` n'ecrit que dans une liste en memoire, et ouvre
      phase2.sqlite en lecture seule.
    """
    import argparse

    racine = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(racine / "monitoring"))
    import check_gti_health as cgh

    scenarios = [
        ("copie a jour, 1 manque  -> le push a vraiment echoue",
         {"copie_en_retard": False, "copie_en_cours": False, "absents_non_concluants": False},
         "critical", "le push n'est pas passe"),
        ("copie de la veille      -> non concluant",
         {"copie_en_retard": True, "copie_en_cours": False, "absents_non_concluants": True},
         "warning", "plus vieille que le registre"),
        ("copie en cours          -> non concluant",
         {"copie_en_retard": False, "copie_en_cours": True, "absents_non_concluants": True},
         "warning", "en cours de descente"),
        ("fraicheur inconnue      -> on ne devine pas, on juge comme avant",
         {"copie_en_retard": None, "copie_en_cours": False, "absents_non_concluants": False},
         "critical", "le push n'est pas passe"),
    ]

    socle = {"serveur": 26855, "supabase": 26851, "deux_numeros": 0, "croisements": 0,
             "plage_envahie": 0, "en_attente": 0, "absents_du_cloud": 4,
             "copie_descendue_le": "2026-10-12T08:15:04",
             "registre_ecrit_le": "2026-10-13T04:56:43+00:00"}

    vrai_mesurer = mun.mesurer
    rates = 0
    try:
        for titre, fraicheur, statut_voulu, mot_voulu in scenarios:
            mesure = dict(socle, **fraicheur)
            mun.mesurer = lambda _conn, _m=mesure: _m
            moniteur = cgh.Monitor(argparse.Namespace(project_root=str(racine)), None)
            moniteur.check_mandat_un_numero()
            if len(moniteur.results) != 1:
                print(f"  ECHEC  {titre}")
                print(f"         {len(moniteur.results)} resultat(s), attendu 1")
                rates += 1
                continue
            r = moniteur.results[0]
            if r.status != statut_voulu or mot_voulu not in r.message:
                rates += 1
                print(f"  ECHEC  {titre}")
                print(f"         statut {r.status!r}, attendu {statut_voulu!r}")
                print(f"         message : {r.message}")
            else:
                print(f"  ok     {titre}  [{r.status}]")
    finally:
        mun.mesurer = vrai_mesurer
    return rates


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Les horloges du vrai matin du 13/10, pour que l'epreuve colle au reel :
    #   le registre est ecrit a 06:56 locale  = 04:56 UTC
    #   la descente passe   a 07:45 locale  (sans fuseau ecrit, comme en base)
    registre_vu_le = "2026-10-13T04:56:43+00:00"
    descente_du_jour = "2026-10-13T07:45:03"
    descente_de_la_veille = "2026-10-12T08:15:04"

    # trois mandats au registre, deux seulement dans la copie -> 1 « absent »
    registre = [(1, "100", "M1"), (2, "200", "M2"), (3, "300", "M3")]
    copie_partielle = [(1, "100", "M1"), (2, "200", "M2")]
    copie_complete = list(registre)

    epreuves: list[tuple[str, sqlite3.Connection, dict]] = [
        (
            "1. copie A JOUR, rien ne manque -> tout va bien",
            _base(registre, copie_complete, descente_du_jour, vu_le=registre_vu_le),
            {"absents_du_cloud": 0, "copie_en_retard": False, "absents_non_concluants": False},
        ),
        (
            "2. copie A JOUR, 1 manque -> LE PUSH A VRAIMENT ECHOUE, on crie",
            _base(registre, copie_partielle, descente_du_jour, vu_le=registre_vu_le),
            {"absents_du_cloud": 1, "copie_en_retard": False, "absents_non_concluants": False},
        ),
        (
            "3. copie DE LA VEILLE, 1 manque -> on ne sait pas, on se tait",
            _base(registre, copie_partielle, descente_de_la_veille, vu_le=registre_vu_le),
            {"absents_du_cloud": 1, "copie_en_retard": True, "absents_non_concluants": True},
        ),
        (
            "4. copie EN COURS de descente, 1 manque -> on se tait aussi",
            _base(registre, copie_partielle, descente_du_jour, en_cours=True, vu_le=registre_vu_le),
            {"absents_du_cloud": 1, "copie_en_cours": True, "absents_non_concluants": True},
        ),
        (
            "5. aucune date de descente -> fraicheur INCONNUE, on ne devine pas",
            _base(registre, copie_partielle, None, vu_le=registre_vu_le),
            {"absents_du_cloud": 1, "copie_en_retard": None, "absents_non_concluants": False},
        ),
        (
            "6. date illisible -> fraicheur INCONNUE, on ne devine pas",
            _base(registre, copie_partielle, "pas une date", vu_le=registre_vu_le),
            {"absents_du_cloud": 1, "copie_en_retard": None, "absents_non_concluants": False},
        ),
        (
            "7. copie A JOUR mais registre SANS date -> on ne devine pas",
            _base(registre, copie_partielle, descente_du_jour, vu_le=None),
            {"absents_du_cloud": 1, "copie_en_retard": None, "absents_non_concluants": False},
        ),
    ]

    # ⚠ L'EPREUVE DU FUSEAU, celle qui aurait fait mentir la mesure de 2 heures.
    #   Sans conversion, '2026-10-13T05:30:00' (locale) passerait pour PLUS VIEUX
    #   que '2026-10-13T06:00:00+00:00' (UTC) -- alors qu'en vrai 05:30 locale
    #   vaut 03:30 UTC, donc la copie serait bien plus vieille. On construit donc
    #   un cas ou la comparaison TEXTUELLE et la comparaison VRAIE s'opposent.
    decalage = datetime.now().astimezone().utcoffset() or timedelta(0)
    heures = int(decalage.total_seconds() // 3600)
    # copie descendue a 08:00 locale ; registre ecrit a 07:00 UTC (= 09:00 locale
    # si l'on est a +2). En texte brut '08:00' > '07:00' -> on croirait la copie
    # a jour ; en verite elle est en RETARD d'une heure.
    piege = _base(registre, copie_partielle, "2026-10-13T08:00:00",
                  vu_le="2026-10-13T07:00:00+00:00")
    attendu_piege = {"copie_en_retard": heures > 1, "absents_du_cloud": 1}
    epreuves.append((
        f"8. PIEGE DU FUSEAU (machine a UTC{heures:+d}) : en texte la copie parait "
        "a jour, en verite elle est en retard",
        piege, attendu_piege,
    ))

    rates = 0
    for titre, conn, attendu in epreuves:
        try:
            mesure = mun.mesurer(conn)
        finally:
            conn.close()
        if mesure is None:
            print(f"  ECHEC  {titre}\n         la mesure a rendu None")
            rates += 1
            continue
        ecarts = {c: (mesure.get(c), v) for c, v in attendu.items() if mesure.get(c) != v}
        if ecarts:
            rates += 1
            print(f"  ECHEC  {titre}")
            for cle, (trouve, voulu) in ecarts.items():
                print(f"         {cle} = {trouve!r}, attendu {voulu!r}")
        else:
            print(f"  ok     {titre}")

    print()
    print("-- ce que la sentinelle du moniteur en dit --")
    rates += epreuve_sentinelle()

    print()
    if rates:
        print(f"{rates} epreuve(s) en ECHEC.")
        return 1
    print(f"Les {len(epreuves)} + 4 epreuves passent : la sentinelle se tait quand elle ne "
          "peut pas savoir, ET crie encore quand le push a vraiment echoue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
