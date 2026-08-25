# -*- coding: utf-8 -*-
"""C.7 -- L'ENDROIT OU L'ECART SE RESOUT.

LE MIROIR PASSE DE VERITE A TEMOIGNAGE. C'est la formule de Frederic, le 21/08 :
« le miroir de Hektor devient une source d'information ». Aujourd'hui il n'est pas
UNE source, il est LA source -- app_view_generale est detruite et refaite depuis lui
chaque nuit, donc HEKTOR REGAGNE PAR DEFAUT. Pas parce qu'on l'a decide : parce
qu'il est seul dans la piece.

    la nuit :
        ce que dit le MIROIR  +  ce que dit L'APP (relu dans Supabase)
             -> on tranche selon le CONTRAT D'AUTORITE
             -> on ecrit dans LA BASE LOCALE
             -> le push l'envoie vers Supabase

POURQUOI ICI ET PAS DANS LE PUSH. push_upgrade_to_supabase.py fait 1 566 lignes et
porte la logique de delta par empreinte ; on n'y touche pas. Et le plan dit bien
« ecrit dans LA BASE LOCALE » PUIS « envoye vers Supabase » : l'arbitrage se pose
AVANT le push, pas dedans. Le push, lui, ne change pas d'un iota -- il lira
simplement une table deja arbitree.

POURQUOI RELIRE SUPABASE EN DIRECT, et pas le magasin local (C.6). Le magasin est
bati par la descente de 07:30 ; a 05:30 il aurait 22 heures de retard. Or le seul
moment ou cette etape SERT, c'est quand l'envoi vers Hektor a echoue -- une saisie
recente, precisement. Une photo de la veille la manquerait.

LE GARDE-FOU EST REPRIS MOT POUR MOT DU COTE CONTACT, et il a une histoire :
    « /!\\ Le garde-fou reste INDISPENSABLE : si la relecture Supabase echoue, on
      ne touche a rien (sans lui, on ecrirait des vides partout). »
Cote contact, l'oubli d'une regle voisine avait coute 1 104 recherches actives et
13 384 rapprochements orphelins. ON N'ECRIT RIEN QUAND ON N'EST PAS SUR.

AUJOURD'HUI CETTE ETAPE NE FAIT RIEN, et c'est voulu : le contrat d'annonce est
vide, donc « Hektor gagne partout », donc le comportement est identique. La
machinerie existe ; l'interrupteur est ailleurs (contrat_autorite.py).

RETOUR ARRIERE : retirer l'etape du run. Elle n'ecrit que dans app_view_generale,
qui est de toute facon refaite chaque nuit.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
sys.path.insert(0, str(RACINE / "phase2" / "identite"))

from contrat_autorite import CHAMPS_APP_ANNONCE, contrat_vide  # noqa: E402
from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)

BASE = RACINE / "phase2" / "phase2.sqlite"
CIBLE = "app_view_generale"
PAGE = 1000   # plafond impose par PostgREST


def connecte() -> sqlite3.Connection:
    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("contrat d'autorite -- champs d'annonce appartenant a l'app :",
          ", ".join(CHAMPS_APP_ANNONCE) if CHAMPS_APP_ANNONCE else "(aucun)")

    if contrat_vide():
        print("Le contrat est VIDE : Hektor garde l'autorite sur tous les champs.")
        print("Rien a arbitrer -- comportement identique a aujourd'hui.")
        return 0

    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return 2

    conn = connecte()
    try:
        colonnes = {c[1] for c in conn.execute(f'PRAGMA table_info("{CIBLE}")')}
        inconnus = [c for c in CHAMPS_APP_ANNONCE if c not in colonnes]
        if inconnus:
            print(f"REFUS : le contrat cite des champs absents de {CIBLE} : {inconnus}")
            return 3

        client = SupabaseRestClient(base_url=url, service_role_key=cle)
        select = "app_dossier_id," + ",".join(CHAMPS_APP_ANNONCE)

        # LA RELECTURE, PAGINEE.
        # PIEGE MESURE LE 25/08 : PostgREST plafonne TOUTE reponse a 1 000 lignes,
        # quelle que soit la limite demandee. Sans pagination, on relisait 1 000
        # annonces sur 13 209 et on aurait applique le contrat au douzieme du parc
        # -- EN SILENCE, ce qui est la pire forme d'echec. On pagine par curseur sur
        # app_dossier_id, comme la descente.
        # Si la relecture echoue, on leve : on ne poursuit surtout pas avec des
        # valeurs vides (garde-fou repris du cote contact).
        distant: list[dict] = []
        curseur = -1
        while True:
            page = client.request(
                method="GET",
                path=(f"app_dossier_current?select={select}"
                      f"&app_dossier_id=gt.{curseur}"
                      "&order=app_dossier_id.asc&limit=1000"),
            )
            if not isinstance(page, list):
                print("REFUS : relecture Supabase inexploitable -- rien n'est modifie.")
                return 4
            if not page:
                break
            distant.extend(page)
            suivant = page[-1].get("app_dossier_id")
            if suivant is None or int(suivant) <= curseur:
                print("REFUS : curseur qui n'avance pas -- arret pour ne pas boucler.")
                return 4
            curseur = int(suivant)
            if len(page) < 1000:
                break

        attendu = conn.execute(f"SELECT count(*) FROM {CIBLE}").fetchone()[0]
        print(f"relu depuis Supabase : {len(distant)} annonces "
              f"(la base locale en compte {attendu})")
        if not distant:
            print("REFUS : relecture vide -- rien n'est modifie.")
            return 4

        # L'ECRITURE, EN UN SEUL PASSAGE.
        # PIEGE MESURE LE 25/08 : app_view_generale n'a AUCUN INDEX sur app_dossier_id
        # -- view_generale.py n'en cree que deux, sur commercial_id et sur la diffusion.
        # Un `UPDATE ... WHERE app_dossier_id = ?` par annonce balaie donc les 56 899
        # lignes a chaque fois : 13 209 x 56 899 = ~750 millions de comparaisons. Le
        # premier essai a tourne plus de dix minutes sans finir.
        # On passe par une table temporaire INDEXEE (cle primaire) et un seul UPDATE
        # par champ : une passe sur la table, avec recherche indexee. Et on NE POSE PAS
        # d'index sur app_view_generale : elle est detruite et refaite chaque nuit,
        # l'index disparaitrait avec elle.
        applique = 0
        for champ in CHAMPS_APP_ANNONCE:
            couples = [
                (row.get("app_dossier_id"), row.get(champ))
                for row in distant
                if row.get("app_dossier_id") is not None
            ]
            if args.dry_run:
                print(f"   [dry-run] {champ} : {len(couples)} valeurs a poser")
                continue
            conn.execute("DROP TABLE IF EXISTS temp._arbitrage")
            conn.execute("CREATE TEMP TABLE _arbitrage "
                         "(app_dossier_id INTEGER PRIMARY KEY, valeur)")
            conn.executemany("INSERT OR REPLACE INTO temp._arbitrage VALUES (?, ?)",
                             couples)
            cur = conn.execute(f'''
                UPDATE {CIBLE}
                   SET "{champ}" = (SELECT a.valeur FROM temp._arbitrage a
                                     WHERE a.app_dossier_id = {CIBLE}.app_dossier_id)
                 WHERE app_dossier_id IN (SELECT app_dossier_id FROM temp._arbitrage)
            ''')
            conn.execute("DROP TABLE temp._arbitrage")
            print(f"   {champ} : {cur.rowcount} lignes arbitrees")
            applique += cur.rowcount

        if args.dry_run:
            print("\n--dry-run : rien ecrit.")
            return 0

        conn.commit()
        print(f"\n   {applique} valeurs arbitrees en faveur de l'app, "
              f"ecrites dans {CIBLE}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
