#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES 13 ANCIENS NEGOCIATEURS DU CLASSEUR.                      13/11/2026

Prealable OBLIGATOIRE de la decision de Frederic du 02/11 sur les colonnes
I K M (negociateurs) et J L N (pourcentages) : « les anciens negociateurs CREES
dans l'annuaire d'abord -- sinon des cases pointent vers un negociateur qui
n'existe pas chez nous ».

⛔⛔ POURQUOI ON NE LES CREE PAS DANS SUPABASE, et c'est une fausse piste deja
  evitee le 01/11 : `app_hektor_negotiator_agency_directory` est RECONSTRUIT ET
  PURGE CHAQUE NUIT par push_hektor_directory_to_supabase.py, qui finit par
  `delete_missing`. Une ligne ajoutee la-haut a la main VIT MOINS DE 24 H.

⭐ LA SOURCE, ELLE, N'EST JAMAIS PURGEE : data/hektor.sqlite, table
  `hektor_negociateur`, alimentee en UPSERT PUR (normalize_source.upsert_negos).
  C'est donc LA qu'il faut poser, et le run les remontera tout seul.

CE QUE LE CODE DU PUSH GARANTIT, verifie le 13/11 :
    ligne 304 : is_active = l'identifiant est dans listNegos actif=1 CHEZ HEKTOR
    ligne 324 : sinon active_source = « local_hektor_negociateur_inactive »
  Un identifiant 9001 n'y sera JAMAIS -> il part INACTIF, et delete_missing le
  CONSERVE puisqu'il vient de la source locale.

LES QUATRE GARANTIES, toutes mesurees :
    il survit a la purge         source locale, jamais purgee
    il est INACTIF               absent de listNegos actif=1
    il n'ouvre AUCUN droit       189 inactifs sur 189 (mesure du 01/11), et le
                                 double verrou app_user_directory + is_active
    il n'est PAS proposable      decision de Frederic du 01/11 : « le but n'est
                                 pas de pouvoir choisir ces negociateurs mais
                                 juste faire apparaitre leurs noms »

⚠ LA PLAGE 9001+ EST LIBRE : les identifiants de la repartition vont de 0 a 267,
  AUCUN au-dessus de 1000 (mesure du 13/11). Zero collision possible.

    python phase2/checks/creer_anciens_negociateurs.py            (a blanc)
    python phase2/checks/creer_anciens_negociateurs.py --poser    (ecrit)
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "data" / "hektor.sqlite"

# Les 13, releves dans le rapport du gel du 13/11 : ce sont les noms du classeur
# que notre annuaire ne connait pas. Le nombre de lignes du classeur est donne
# pour que l'ordre de grandeur soit visible, il ne sert pas au geste.
# ⚠ Le classeur ne porte QUE le nom de famille, sauf FRANCHINI.
ANCIENS = [
    (9001, "ABED", "", 6),
    (9002, "ALLEMAND", "", 4),
    (9003, "BERTRAND", "", 3),
    (9004, "AGRAIN", "", 2),
    (9005, "BRUNON", "", 1),
    (9006, "EXBRAYAT", "", 1),
    (9007, "COMMERE", "", 1),
    (9008, "LEFAURE", "", 1),
    (9009, "PETROSINO", "", 1),
    (9010, "LAUGIER", "", 1),
    (9011, "ADAMO", "", 1),
    (9012, "BALIQUE", "", 1),
    (9013, "FRANCHINI", "Marjorie", 1),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--poser", action="store_true",
                    help="ecrit vraiment ; sans ce drapeau, rien n'est ecrit")
    args = ap.parse_args()

    if not BASE.exists():
        print("N'A PAS PU MESURER : %s introuvable" % BASE)
        return 2

    con = sqlite3.connect(BASE)
    con.row_factory = sqlite3.Row
    try:
        avant = con.execute("select count(*) from hektor_negociateur").fetchone()[0]
        mx = con.execute(
            "select max(cast(hektor_negociateur_id as integer)) from hektor_negociateur"
        ).fetchone()[0]

        # ⛔ GARDE 1 : la plage doit etre libre. Si Hektor a grandi jusqu'a 9000,
        #   on s'arrete -- une collision ecraserait un VRAI negociateur.
        if mx is not None and int(mx) >= 9001:
            print("ARRET : l'identifiant maximum est %s, la plage 9001+ n'est plus libre." % mx)
            return 1

        # ⛔ GARDE 2 : ne jamais creer un nom qui existe deja. Un doublon de
        #   negociateur couperait sa commission en deux -- c'est exactement le
        #   defaut que la table d'alias evite pour GIRAUD et ALVES MENDES.
        connus = {
            (str(r["nom"] or "").strip().upper(), str(r["prenom"] or "").strip().upper())
            for r in con.execute("select nom, prenom from hektor_negociateur")
        }
        noms_seuls = {n for n, _ in connus}

        a_poser, deja, homonymes = [], [], []
        for ident, nom, prenom, lignes in ANCIENS:
            existe = con.execute(
                "select 1 from hektor_negociateur where hektor_negociateur_id = ?",
                (str(ident),)).fetchone()
            if existe:
                deja.append((ident, nom))
                continue
            if (nom.upper(), prenom.upper()) in connus:
                homonymes.append((ident, nom, prenom, "nom ET prenom deja connus"))
                continue
            if nom.upper() in noms_seuls:
                homonymes.append((ident, nom, prenom, "ce NOM existe deja dans l'annuaire"))
                continue
            a_poser.append((ident, nom, prenom, lignes))

        print()
        print("  LES 13 ANCIENS NEGOCIATEURS DU CLASSEUR")
        print("  " + "=" * 64)
        print("  annuaire local : %d lignes, identifiant max %s" % (avant, mx))
        print()
        for ident, nom, prenom, lignes in a_poser:
            print("  A POSER   %-5s %-12s %-10s (%d ligne(s) au classeur)"
                  % (ident, nom, prenom or "-", lignes))
        for ident, nom in deja:
            print("  DEJA LA   %-5s %s" % (ident, nom))
        for ident, nom, prenom, pourquoi in homonymes:
            print("  ⛔ ECARTE %-5s %-12s %-10s -- %s" % (ident, nom, prenom or "-", pourquoi))
        print("  " + "-" * 64)
        print("  a poser : %d . deja la : %d . ecartes : %d"
              % (len(a_poser), len(deja), len(homonymes)))

        if homonymes:
            print()
            print("  ⚠ DES HOMONYMES ONT ETE TROUVES. Un doublon de negociateur")
            print("    COUPERAIT SA COMMISSION EN DEUX -- c'est le defaut que les")
            print("    alias GIRAUD et ALVES MENDES evitent deja. Ils ne sont pas")
            print("    poses : a trancher a la main (alias, ou vraie personne ?).")

        if not args.poser:
            print()
            print("  ⛔ A BLANC : rien n'a ete ecrit. Relancer avec --poser.")
            return 0

        if not a_poser:
            print()
            print("  rien a poser.")
            return 0

        quand = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for ident, nom, prenom, _ in a_poser:
            brut = json.dumps({
                "id": str(ident), "idUser": str(ident), "nom": nom, "prenom": prenom,
                "origine": "ancien du classeur, cree le 13/11/2026 -- jamais connu de Hektor",
            }, ensure_ascii=False)
            con.execute(
                "insert into hektor_negociateur"
                " (hektor_negociateur_id, hektor_user_id, hektor_agence_id,"
                "  nom, prenom, email, telephone, portable, raw_json, synced_at)"
                " values (?, ?, NULL, ?, ?, NULL, NULL, NULL, ?, ?)",
                (str(ident), str(ident), nom, prenom or None, brut, quand))
        con.commit()

        apres = con.execute("select count(*) from hektor_negociateur").fetchone()[0]
        poses = con.execute(
            "select count(*) from hektor_negociateur"
            " where cast(hektor_negociateur_id as integer) >= 9001").fetchone()[0]
        print()
        print("  POSE : %d -> %d lignes (+%d) . identifiants 9001+ : %d"
              % (avant, apres, apres - avant, poses))
        print("  ⭐ Ils partiront INACTIFS au prochain run, et y resteront.")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
