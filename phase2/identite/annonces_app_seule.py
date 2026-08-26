# -*- coding: utf-8 -*-
"""26bis-(1) -- LE SERVEUR SAIT TENIR UNE ANNONCE QUE LE MIROIR IGNORE.

CE QUE CETTE TACHE N'EST PAS, et il a fallu deux erreurs le 26/08 pour le cerner.

  FAUX N.1 : « le corps de l'annonce n'existe pas cote serveur ». Il existe --
  app_view_generale, 56 913 lignes, 130 colonnes.

  FAUX N.2 : « a la coupure, le DROP de 05:30 effacera ces 56 913 lignes ». Non :
  LE MIROIR GELE, IL NE DISPARAIT PAS. Le fichier data/hektor.sqlite reste, la
  reconstruction reproduit le meme contenu. Les annonces existantes gardent leur corps.

  Et pour ces annonces-la, la machinerie est DEJA complete : appliquer_contrat.py
  (C.7) re-applique chaque nuit ce que l'app detient, relu dans Supabase. Il ne
  manque que l'interrupteur CHAMPS_APP_ANNONCE.

LE TROU REEL, LUI, TIENT EN UNE PHRASE :

    une annonce NEE DANS L'APP n'a aucune ligne dans le miroir
        -> donc aucune ligne dans app_view_generale
        -> donc LE SERVEUR NE LA CONNAIT PAS DU TOUT

et C.7 sait METTRE A JOUR des lignes existantes, pas en CREER. C'est exactement ce
que le plan dit depuis le 21/08 : « sans 26bis, une annonce creee dans l'app
n'existe QUE dans Supabase, et le serveur ne l'apprend que si Hektor la confirme ».

------------------------------------------------------------------ POURQUOI UNE TABLE
On pourrait injecter directement depuis Supabase a chaque run, sans rien conserver.
Ce serait fragile : une relecture Supabase qui echoue un matin ferait DISPARAITRE
ces annonces du serveur -- alors qu'elles n'existent nulle part ailleurs. La table
les ACCUMULE : un echec de lecture signifie « aucune nouvelle ce matin », jamais
« elles ont disparu ». C'est la regle 5 du projet, appliquee ici.

Et comme partout : ABSENT_DEPUIS, JAMAIS DE SUPPRESSION.

------------------------------------------------------------------ LES DEUX GESTES
    --recenser   relit Supabase EN DIRECT, note les annonces que le miroir ignore
    --injecter   les pose dans app_view_generale, apres sa reconstruction

POURQUOI RELIRE SUPABASE EN DIRECT et pas app_dossier_current en local : la descente
tourne a 07:30, donc a 05:30 la copie locale a 22 heures de retard. Une annonce creee
hier a 9 h y manquerait. C'est le meme raisonnement que C.7, et pour la meme raison.

------------------------------------------------------------------ AUJOURD'HUI : ZERO
Mesure du 26/08 : ZERO annonce est connue de l'app et pas du miroir. Ce script est
donc INERTE -- il ne peut rien changer. C'est voulu : c'est une doublure, on la pose
avant d'en avoir besoin, precisement pour ne pas la poser dans l'urgence.

PERSONNE NE LIT app_annonce_app_seule. app_view_generale, elle, est deja lue -- mais
on n'y ajoute que des lignes qui n'y seraient pas autrement, donc rien ne change tant
que le compte est a zero.

RETOUR ARRIERE : retirer les deux etapes du run, puis DROP TABLE app_annonce_app_seule.
Aucune donnee existante n'est modifiee : on n'ecrit QUE des lignes neuves.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)

BASE = RACINE / "phase2" / "phase2.sqlite"
VERROU = RACINE / "pull_from_supabase.lock"

VUE = "app_view_generale"        # le corps, refait chaque nuit depuis le miroir
SOURCE = "app_dossier_current"   # ce que dit l'app, relu dans Supabase
REGISTRE = "app_annonce_app_seule"

# Plancher de securite : si la vue est plus courte que ca, c'est qu'un run a
# echoue en amont. On n'injecte rien dans une table a moitie construite.
PLANCHER_VUE = 1000

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {REGISTRE} (
    app_dossier_id      INTEGER PRIMARY KEY,
    hektor_annonce_id   TEXT,
    donnees_json        TEXT NOT NULL,
    vu_la_premiere_fois TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vu_le               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    absent_depuis       TEXT
)
"""


def connecte() -> sqlite3.Connection:
    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def colonnes(conn: sqlite3.Connection, table: str) -> list[str]:
    return [c[1] for c in conn.execute(f'PRAGMA table_info("{table}")')]


def client_supabase() -> SupabaseRestClient | None:
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return None
    return SupabaseRestClient(base_url=url, service_role_key=cle)


def lire_supabase(client: SupabaseRestClient, champs: list[str]) -> list[dict] | None:
    """Relit app_dossier_current, PAGINE.

    PIEGE MESURE LE 25/08 : PostgREST plafonne TOUTE reponse a 1 000 lignes, quelle
    que soit la limite demandee. Sans pagination on lirait 1 000 annonces sur 13 210
    et on conclurait a tort que les autres n'existent pas -- EN SILENCE.
    """
    select = ",".join(champs)
    lignes: list[dict] = []
    curseur = -1
    while True:
        page = client.request(
            method="GET",
            path=(f"{SOURCE}?select={select}"
                  f"&app_dossier_id=gt.{curseur}"
                  "&order=app_dossier_id.asc&limit=1000"),
        )
        if not isinstance(page, list):
            print("REFUS : relecture Supabase inexploitable -- rien n'est modifie.")
            return None
        if not page:
            break
        lignes.extend(page)
        suivant = page[-1].get("app_dossier_id")
        if suivant is None or int(suivant) <= curseur:
            print("REFUS : curseur qui n'avance pas -- arret pour ne pas boucler.")
            return None
        curseur = int(suivant)
        if len(page) < 1000:
            break
    return lignes


def recenser(conn: sqlite3.Connection, dry: bool) -> int:
    champs_vue = colonnes(conn, VUE)
    if "app_dossier_id" not in champs_vue:
        print(f"REFUS : {VUE} n'a pas de colonne app_dossier_id.")
        return 3
    total_vue = conn.execute(f'SELECT COUNT(*) FROM "{VUE}"').fetchone()[0]
    if total_vue < PLANCHER_VUE:
        print(f"REFUS : {VUE} ne compte que {total_vue} lignes (plancher {PLANCHER_VUE}).")
        print("        Un run amont a probablement echoue -- on ne recense pas dans le vide.")
        return 3

    client = client_supabase()
    if client is None:
        return 2

    # On ne demande que les colonnes communes : le reste ne servirait a rien puisque
    # c'est dans app_view_generale que ces lignes iront.
    champs_source = colonnes(conn, SOURCE)
    communes = [c for c in champs_source if c in champs_vue]
    if "app_dossier_id" not in communes:
        communes.insert(0, "app_dossier_id")

    distant = lire_supabase(client, communes)
    if distant is None:
        return 4

    connues = {int(r[0]) for r in conn.execute(f'SELECT app_dossier_id FROM "{VUE}"')
               if r[0] is not None}
    app_seules = [r for r in distant
                  if r.get("app_dossier_id") is not None
                  and int(r["app_dossier_id"]) not in connues]

    print(f"Supabase : {len(distant)} annonces lues")
    print(f"{VUE}    : {total_vue} annonces")
    print(f"APP SEULE : {len(app_seules)} annonce(s) que le miroir ignore")

    if dry:
        for r in app_seules[:10]:
            print("   ", r.get("app_dossier_id"), "|", r.get("hektor_annonce_id"), "|",
                  str(r.get("titre_bien"))[:50])
        print("(essai a blanc : rien n'est ecrit)")
        return 0

    conn.executescript(SCHEMA)
    vus = set()
    for r in app_seules:
        did = int(r["app_dossier_id"])
        vus.add(did)
        conn.execute(
            f"""INSERT INTO {REGISTRE}(app_dossier_id, hektor_annonce_id, donnees_json)
                VALUES (?, ?, ?)
                ON CONFLICT(app_dossier_id) DO UPDATE SET
                    hektor_annonce_id = excluded.hektor_annonce_id,
                    donnees_json      = excluded.donnees_json,
                    vu_le             = CURRENT_TIMESTAMP,
                    absent_depuis     = NULL""",
            (did, r.get("hektor_annonce_id"),
             json.dumps(r, ensure_ascii=True, separators=(",", ":"))),
        )
    # DISPARITION : on MARQUE, on ne supprime jamais (regle 5).
    marquees = conn.execute(
        f"""UPDATE {REGISTRE} SET absent_depuis = CURRENT_TIMESTAMP
             WHERE absent_depuis IS NULL
               AND app_dossier_id NOT IN (%s)"""
        % (",".join(str(d) for d in vus) if vus else "-1")
    ).rowcount
    conn.commit()
    total = conn.execute(f"SELECT COUNT(*) FROM {REGISTRE}").fetchone()[0]
    print(f"registre : {len(vus)} vue(s), {marquees} marquee(s) absente(s), {total} au total")
    return 0


def injecter(conn: sqlite3.Connection, dry: bool) -> int:
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (REGISTRE,)
    ).fetchone():
        print(f"{REGISTRE} n'existe pas encore : rien a injecter.")
        return 0

    total_vue = conn.execute(f'SELECT COUNT(*) FROM "{VUE}"').fetchone()[0]
    if total_vue < PLANCHER_VUE:
        print(f"REFUS : {VUE} ne compte que {total_vue} lignes -- on n'injecte pas.")
        return 3

    champs_vue = colonnes(conn, VUE)
    presentes = {int(r[0]) for r in conn.execute(f'SELECT app_dossier_id FROM "{VUE}"')
                 if r[0] is not None}

    lignes = conn.execute(
        f"SELECT app_dossier_id, donnees_json FROM {REGISTRE} WHERE absent_depuis IS NULL"
    ).fetchall()
    a_poser = [(d, json.loads(j)) for d, j in lignes if int(d) not in presentes]

    print(f"{REGISTRE} : {len(lignes)} active(s), {len(a_poser)} a poser dans {VUE}")
    if dry or not a_poser:
        if dry:
            print("(essai a blanc : rien n'est ecrit)")
        return 0

    pose = 0
    for did, donnees in a_poser:
        cols = [c for c in donnees if c in champs_vue]
        if "app_dossier_id" not in cols:
            cols.append("app_dossier_id")
            donnees["app_dossier_id"] = did
        sql = (f'INSERT INTO "{VUE}" (%s) VALUES (%s)'
               % (",".join(f'"{c}"' for c in cols), ",".join("?" for _ in cols)))
        conn.execute(sql, [donnees.get(c) for c in cols])
        pose += 1
    conn.commit()
    print(f"{pose} annonce(s) posee(s) dans {VUE} -- elles n'y seraient pas autrement")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="26bis-(1) : les annonces que l'app connait et que le miroir ignore.")
    ap.add_argument("--recenser", action="store_true", help="relire Supabase et noter")
    ap.add_argument("--injecter", action="store_true", help="poser dans app_view_generale")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.recenser or args.injecter):
        args.recenser = args.injecter = True

    if VERROU.exists():
        print(f"REFUS : la descente est en cours ({VERROU.name}).")
        return 5

    conn = connecte()
    try:
        code = 0
        if args.recenser:
            code = recenser(conn, args.dry_run)
            if code:
                return code
        if args.injecter:
            code = injecter(conn, args.dry_run)
        return code
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
