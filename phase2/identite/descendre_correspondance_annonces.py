#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.9-a — LE SERVEUR APPREND LE NUMERO D'UNE ANNONCE NEE DANS L'APP.
                                                                  24/09/2026

LE JUMEAU DE descendre_correspondance_contacts.py (L4-b ②), POUR L'ANNONCE.
Audit : notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md, defaut D1.

LE DEFAUT QU'IL FERME -- et il se produirait dans le cas NORMAL, pas dans un cas
rare. Aujourd'hui Hektor repond en 30 s a une creation (77 fois sur 77) :

    jour J     l'app donne 10 000 001 ; le worker cree chez Hektor : 63 200
               Supabase : app_dossier_id 10 000 001, hektor_annonce_id 63 200
    nuit J+1   bootstrap_phase2 ne reconnait une annonce QUE par son numero
               Hektor (LEFT JOIN app_dossier deja ON deja.hektor_annonce_id) ;
               le serveur ne connait pas 10 000 001, donc il en fabrique un :
               7 589 129.                            -> DEUX NUMEROS, en silence

Ce script tourne AVANT le bootstrap. Il relit dans Supabase les annonces de la
plage de l'app et pose dans app_dossier la ligne (10 000 001, 63 200) : le
bootstrap la retrouve alors par son numero Hektor, et la garde.

⚠ IL N'ADOPTE QUE CE QUE LE MIROIR CONNAIT DEJA. app_view_generale part de
  app_dossier SANS filtre et y joint le miroir : une annonce adoptee que le
  miroir ignore y apparaitrait VIDE, et le push du matin enverrait ce vide PAR
  DESSUS la vraie fiche dans Supabase. Donc :
      numero Hektor inconnu           -> on attend (Hektor n'a pas repondu)
      numero Hektor absent du miroir  -> on attend (le run ne l'a pas encore tire)
  Ce qui attend reste dans Supabase, ou l'app en est la source. Le proteger du
  push qui efface les annonces que le serveur ignore, c'est C.9-c -- pas ici.

⚠ LE GARDE-FOU DU COMPTEUR (defaut D2-3). app_dossier.id est AUTOINCREMENT : la
  premiere adoption fait sauter sqlite_sequence a 10 000 00x, et SQLite refuse
  de le redescendre. Des lors, tout INSERT qui oublierait l'id naitrait DANS LA
  PLAGE DE L'APP -- le meme numero que la prochaine annonce creee par l'app. Les
  deux chemins d'insertion donnent l'id aujourd'hui, mais rien ne l'impose.
  Un declencheur l'impose : un numero >= 10 000 000 n'entre dans app_dossier que
  s'il a ete ADOPTE (table app_dossier_adoption, remplie par ce script seul).
  Sinon l'INSERT echoue -- bruyamment, au lieu de fabriquer un doublon.

CE QU'IL NE FAIT JAMAIS : modifier l'id d'une ligne, remplacer un numero Hektor
existant, toucher une annonce de la plage de Hektor. Deux numeros pour une
annonce, s'il en trouve, il les SIGNALE et n'y touche pas : lequel survit est
une decision humaine (« un dossier ne perd jamais son numero »).

CODES DE SORTIE
    0  fait, ou rien a faire
    3  la liste lue est incoherente -- rien n'est ecrit
    4  deux numeros pour une meme annonce -- signale, non touche
    5  Supabase illisible ALORS QU'une annonce est deja nee dans l'app
       (tant qu'aucune ne l'est, un echec de lecture ne coute rien : on rend 0)
    Le run l'appelle avec -FailOnError : 3, 4 et 5 ARRETENT le run avant le
    bootstrap. Une nuit sans synchronisation vaut mieux qu'un second numero.

AU 24/09 : ZERO annonce dans la plage de l'app. Le script est inerte, c'est
voulu : il est pose AVANT que la creation app-first existe (C.9-e).

IDEMPOTENT : rejouer n'ecrit rien.
RETOUR ARRIERE : retirer l'etape du run ; puis, s'il n'y a eu aucune adoption,
    DROP TRIGGER app_dossier_plage_app_insert;
    DROP TRIGGER app_dossier_plage_app_update;
    DROP TABLE app_dossier_adoption;
  S'il y en a eu, les lignes adoptees sont celles de app_dossier_adoption.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
MIROIR = RACINE / "data" / "hektor.sqlite"

# Les fichiers d'environnement : la liste du push, pas une seconde copie (meme
# raison que descendre_correspondance_contacts.py). On ne les AFFICHE jamais.
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: E402

PLAGE_ANNONCE_APP = 10_000_000   # L4-a : app_dossier_id_app_seq demarre ici
PAGE = 1000                      # PostgREST plafonne ; on pagine, trie
PLAFOND_ABSURDE = 1_000_000
TABLE_ADOPTION = "app_dossier_adoption"


def charger_env() -> None:
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)


def assurer_garde(conn: sqlite3.Connection) -> None:
    """La table des adoptions et les deux declencheurs. Idempotent."""
    conn.execute(
        f"""CREATE TABLE IF NOT EXISTS {TABLE_ADOPTION} (
                app_dossier_id    INTEGER PRIMARY KEY,
                hektor_annonce_id INTEGER NOT NULL,
                adopte_le         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
    for nom, evenement in (("app_dossier_plage_app_insert", "INSERT"),
                           ("app_dossier_plage_app_update", "UPDATE OF id")):
        conn.execute(
            f"""CREATE TRIGGER IF NOT EXISTS {nom}
                AFTER {evenement} ON app_dossier
                WHEN NEW.id >= {PLAGE_ANNONCE_APP}
                 AND NOT EXISTS (SELECT 1 FROM {TABLE_ADOPTION} a
                                  WHERE a.app_dossier_id = NEW.id)
                BEGIN
                    SELECT RAISE(ABORT,
                        'C.9-a : numero de la plage de l''app entre dans app_dossier sans adoption');
                END""")


def lire_supabase() -> list[dict]:
    """Les annonces de la plage de l'app, page par page, dans un ordre stable."""
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
    base = (f"{url.rstrip('/')}/rest/v1/app_dossier_current"
            f"?select=app_dossier_id,hektor_annonce_id"
            f"&app_dossier_id=gte.{PLAGE_ANNONCE_APP}"
            f"&order=app_dossier_id.asc")
    toutes: list[dict] = []
    depart = 0
    while True:
        requete = urllib.request.Request(f"{base}&offset={depart}&limit={PAGE}", headers={
            "apikey": cle, "Authorization": f"Bearer {cle}", "Accept": "application/json"})
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            page = json.loads(reponse.read().decode("utf-8"))
        if not isinstance(page, list):
            raise RuntimeError("reponse inattendue de Supabase (pas une liste)")
        toutes.extend(page)
        if len(page) < PAGE:
            break
        depart += len(page)
        if len(toutes) > PLAFOND_ABSURDE:
            raise RuntimeError(f"{len(toutes)} lignes lues : au-dela du concevable.")
    return toutes


def _entier(valeur) -> int | None:
    texte = str(valeur if valeur is not None else "").strip()
    return int(texte) if texte.isdigit() else None


def verifier_la_forme(lignes: list[dict]) -> list[str]:
    """La FORME, pas la taille (lecon C-3 du 23/09)."""
    griefs: list[str] = []
    vus: dict[int, int] = {}
    for ligne in lignes:
        app_id = _entier(ligne.get("app_dossier_id"))
        brut_hektor = ligne.get("hektor_annonce_id")
        hektor = _entier(brut_hektor)
        if app_id is None or app_id < PLAGE_ANNONCE_APP:
            griefs.append(f"numero d'app invalide ou hors plage : {ligne.get('app_dossier_id')!r}")
            continue
        if brut_hektor not in (None, "") and hektor is None:
            griefs.append(f"{app_id} : numero Hektor non numerique {brut_hektor!r}")
            continue
        if hektor is None:
            continue
        if hektor >= PLAGE_ANNONCE_APP:
            griefs.append(f"{app_id} : numero Hektor {hektor} dans NOTRE plage")
        if hektor in vus and vus[hektor] != app_id:
            griefs.append(f"deux numeros d'app visent l'annonce Hektor {hektor} : "
                          f"{vus[hektor]} et {app_id}")
        vus[hektor] = app_id
    return griefs[:20]


def presents_dans_le_miroir(miroir: sqlite3.Connection, numeros: set[int]) -> set[int]:
    """Parmi ces numeros Hektor, ceux que le miroir tient pour PRESENTS -- la
    condition meme du bootstrap (annonce_source_status = 'present')."""
    if not numeros:
        return set()
    trouves: set[int] = set()
    liste = sorted(numeros)
    for i in range(0, len(liste), 500):
        tranche = [str(n) for n in liste[i:i + 500]]
        marques = ",".join("?" for _ in tranche)
        for (brut,) in miroir.execute(
                f"SELECT hektor_annonce_id FROM case_dossier_source "
                f"WHERE annonce_source_status = 'present' AND hektor_annonce_id IN ({marques})",
                tranche):
            n = _entier(brut)
            if n is not None:
                trouves.add(n)
    return trouves


def adopter(conn: sqlite3.Connection, lignes: list[dict], presents: set[int],
            *, dry: bool = False) -> dict:
    """Le coeur. Rend les comptes et la liste des anomalies ; n'ecrit rien si dry."""
    bilan = {"adoptees": 0, "completees": 0, "deja_la": 0,
             "attente_hektor": 0, "attente_miroir": 0, "anomalies": []}
    for ligne in lignes:
        app_id = _entier(ligne.get("app_dossier_id"))
        hektor = _entier(ligne.get("hektor_annonce_id"))
        if hektor is None:
            bilan["attente_hektor"] += 1
            continue
        if hektor not in presents:
            bilan["attente_miroir"] += 1
            continue
        par_id = conn.execute(
            "SELECT hektor_annonce_id FROM app_dossier WHERE id = ?", (app_id,)).fetchone()
        par_hektor = conn.execute(
            "SELECT id FROM app_dossier WHERE hektor_annonce_id = ?", (hektor,)).fetchone()

        if par_id is not None:
            actuel = _entier(par_id[0])
            if actuel == hektor:
                bilan["deja_la"] += 1
                if not dry:
                    conn.execute(f"INSERT OR IGNORE INTO {TABLE_ADOPTION} "
                                 "(app_dossier_id, hektor_annonce_id) VALUES (?, ?)",
                                 (app_id, hektor))
                continue
            if actuel is not None:
                bilan["anomalies"].append(
                    f"{app_id} porte deja le numero Hektor {actuel}, Supabase dit {hektor} "
                    "-- non touche")
                continue
            if par_hektor is not None:
                bilan["anomalies"].append(
                    f"DEUX NUMEROS : l'annonce Hektor {hektor} est deja {par_hektor[0]} sur le "
                    f"serveur, et {app_id} dans l'app -- non touche")
                continue
            # D2-1 : la ligne existe sans son numero Hektor ; on le COMPLETE, sans rien remplacer.
            bilan["completees"] += 1
            if not dry:
                conn.execute(f"INSERT OR IGNORE INTO {TABLE_ADOPTION} "
                             "(app_dossier_id, hektor_annonce_id) VALUES (?, ?)", (app_id, hektor))
                conn.execute("UPDATE app_dossier SET hektor_annonce_id = ?, "
                             "updated_at = CURRENT_TIMESTAMP "
                             "WHERE id = ? AND hektor_annonce_id IS NULL", (hektor, app_id))
            continue

        if par_hektor is not None:
            bilan["anomalies"].append(
                f"DEUX NUMEROS : l'annonce Hektor {hektor} a deja recu {par_hektor[0]} du "
                f"serveur, et {app_id} dans l'app -- non touche")
            continue
        bilan["adoptees"] += 1
        if not dry:
            # L'adoption D'ABORD : c'est elle qui ouvre la porte du declencheur.
            conn.execute(f"INSERT INTO {TABLE_ADOPTION} (app_dossier_id, hektor_annonce_id) "
                         "VALUES (?, ?)", (app_id, hektor))
            conn.execute("INSERT INTO app_dossier (id, hektor_annonce_id) VALUES (?, ?)",
                         (app_id, hektor))
    return bilan


def quelque_chose_est_ne_dans_l_app(conn: sqlite3.Connection) -> bool:
    """Sert a decider si un echec de lecture de Supabase coute quelque chose."""
    if conn.execute("SELECT 1 FROM app_dossier WHERE id >= ? LIMIT 1",
                    (PLAGE_ANNONCE_APP,)).fetchone():
        return True
    existe = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                          "AND name='app_dossier_current'").fetchone()
    if existe and conn.execute("SELECT 1 FROM app_dossier_current WHERE app_dossier_id >= ? "
                               "LIMIT 1", (PLAGE_ANNONCE_APP,)).fetchone():
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="Lecture seule : compte ce qui serait fait, n'ecrit rien, "
                             "n'installe pas le garde-fou.")
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--miroir", type=Path, default=MIROIR)
    args = parser.parse_args()

    if args.dry_run:
        conn = sqlite3.connect(f"file:{args.base.as_posix()}?mode=ro", uri=True, timeout=60)
    else:
        conn = sqlite3.connect(str(args.base), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        charger_env()
        try:
            lignes = lire_supabase()
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, OSError) as err:
            if quelque_chose_est_ne_dans_l_app(conn):
                print(f"[annonces app] ECHEC : Supabase illisible ({type(err).__name__}) alors "
                      "qu'une annonce est deja nee dans l'app. On arrete AVANT le bootstrap : "
                      "il lui donnerait un second numero.")
                return 5
            print(f"[annonces app] Supabase illisible ({type(err).__name__}) -- sans consequence : "
                  "aucune annonce n'est encore nee dans l'app.")
            return 0

        griefs = verifier_la_forme(lignes)
        if griefs:
            print(f"REFUS : liste incoherente ({len(lignes)} ligne(s) lues). Rien n'est ecrit.")
            for grief in griefs:
                print(f"        - {grief}")
            return 3

        numeros = {h for h in (_entier(l.get("hektor_annonce_id")) for l in lignes) if h is not None}
        miroir = sqlite3.connect(f"file:{args.miroir.as_posix()}?mode=ro", uri=True, timeout=60)
        try:
            presents = presents_dans_le_miroir(miroir, numeros)
        finally:
            miroir.close()

        if not args.dry_run:
            assurer_garde(conn)
        bilan = adopter(conn, lignes, presents, dry=args.dry_run)
        if not args.dry_run:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    mode = " (dry-run, rien d'ecrit)" if args.dry_run else ""
    print(f"[annonces app] {len(lignes)} annonce(s) dans la plage de l'app{mode}")
    print(f"               adoptees {bilan['adoptees']} · completees {bilan['completees']} · "
          f"deja connues {bilan['deja_la']}")
    print(f"               en attente : de Hektor {bilan['attente_hektor']} · "
          f"du miroir {bilan['attente_miroir']}")
    if bilan["anomalies"]:
        print(f"ANOMALIE : {len(bilan['anomalies'])} annonce(s) -- rien n'a ete touche pour elles :")
        for texte in bilan["anomalies"][:20]:
            print(f"        - {texte}")
        return 4
    if not lignes:
        print("               aucune annonce n'est encore nee dans l'app : rien a faire.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
