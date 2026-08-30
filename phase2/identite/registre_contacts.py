# -*- coding: utf-8 -*-
"""C.2b -- le registre d'identite des contacts : le creer, puis LE MAINTENIR.

LE PATRON EST CELUI DE app_dossier, A L'IDENTIQUE :

    app_dossier                          app_contact  (ici)
        id            AUTOINCREMENT          app_contact_id     AUTOINCREMENT
        hektor_annonce_id  NULLABLE          hektor_contact_id  NULLABLE
        absent_depuis                        absent_depuis
        UNIQUE(hektor_annonce_id)            UNIQUE(hektor_contact_id)

POURQUOI NULLABLE : un contact cree dans l'app n'a PAS de numero Hektor. La case
reste vide jusqu'a ce que le worker rapporte le sien. Le patron existe depuis
toujours cote annonce et n'a jamais servi (0 ligne sur 56 894) -- ici il servira.

POURQUOI absent_depuis ET PAS UNE SUPPRESSION : regle du projet, « un dossier ne
perd jamais son numero ». Si Hektor cesse de renvoyer un contact, on le MARQUE.
L'effacer orphelinerait tout ce qui pend dessus -- et rien ne le signalerait :
mesure du 24/08, AUCUNE contrainte de cle etrangere ne protege les 18 tables
qui pointent le contact. Elles le font PAR CONVENTION SEULE.

POURQUOI CE SCRIPT TOURNE CHAQUE NUIT, et pas une fois :
    le 25/08, juste apres la creation du registre, 15 contacts crees la veille
    dans Hektor etaient deja dans Supabase mais pas encore dans la base locale
    (elle se rafraichit la nuit). Un registre qui ne se maintient pas rote des
    le lendemain. Il se pose APRES build_contacts_layer, qui fabrique la source.

IDEMPOTENT : rejouer ne change rien et affiche 0 / 0 / 0.

RETOUR ARRIERE : DROP TABLE app_contact.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

BASE = Path(r"C:\Hektor\Projet\phase2\phase2.sqlite")
SOURCE = "app_contact_current"
REGISTRE = "app_contact"

SCHEMA = f"""
CREATE TABLE {REGISTRE} (
    app_contact_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    hektor_contact_id TEXT,
    created_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    absent_depuis     TEXT,
    UNIQUE(hektor_contact_id)
)
"""


def connecte() -> sqlite3.Connection:
    conn = sqlite3.connect(str(BASE), timeout=60)
    # phase2 est en WAL et plusieurs ecrivains coexistent : sans ce reglage, un
    # autre run (le rattrapage acquereurs) se fait tuer au bout de 5 secondes.
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def propage_aux_recherches(conn: sqlite3.Connection) -> int | None:
    """Redonne au registre des recherches le numero de contact de l'app.

    POURQUOI ICI ET PAS DANS build_contacts_layer. C'est build_contacts_layer qui
    ecrit dans app_search_registry -- mais il tourne AVANT ce script (ligne 370
    contre 380 du pipeline). Un contact tout neuf n'a donc pas encore son numero
    au moment ou sa recherche recoit le sien. Le remplir la-bas reviendrait a
    ecrire NULL une nuit sur deux.

    Ici, le registre des contacts vient d'etre mis a jour : le numero existe.
    C'est un rattrapage d'une ligne, rejouable, qui ne touche que les cases vides.

    ON NE CORRIGE JAMAIS UNE CASE DEJA REMPLIE : une recherche nee dans l'app
    portera son numero de contact sans jamais avoir eu de numero Hektor, et ce
    n'est pas a une jointure sur Hektor de le lui reprendre.

    Renvoie le nombre de cases remplies, ou None si le registre des recherches
    n'existe pas encore / n'a pas encore la colonne (base non migree).
    """
    existe = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='app_search_registry'"
    ).fetchone()[0] > 0
    if not existe:
        return None
    colonnes = {d[1] for d in conn.execute("PRAGMA table_info(app_search_registry)")}
    if "app_contact_id" not in colonnes:
        return None

    cur = conn.execute(
        f"""
        UPDATE app_search_registry
           SET app_contact_id = (
                 SELECT r.app_contact_id FROM {REGISTRE} r
                  WHERE r.hektor_contact_id = app_search_registry.hektor_contact_id)
         WHERE app_contact_id IS NULL
           AND hektor_contact_id IS NOT NULL
           AND EXISTS (SELECT 1 FROM {REGISTRE} r
                        WHERE r.hektor_contact_id = app_search_registry.hektor_contact_id)
        """
    )
    return cur.rowcount


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="mesure et affiche, n'ecrit rien")
    args = ap.parse_args()

    conn = connecte()
    try:
        existe = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
            (REGISTRE,)).fetchone()[0] > 0

        total = conn.execute(f"SELECT count(*) FROM {SOURCE}").fetchone()[0]
        vides = conn.execute(
            f"SELECT count(*) FROM {SOURCE} "
            "WHERE hektor_contact_id IS NULL OR trim(hektor_contact_id) = ''"
        ).fetchone()[0]
        doublons = conn.execute(
            f"SELECT count(*) FROM (SELECT hektor_contact_id FROM {SOURCE} "
            "GROUP BY 1 HAVING count(*) > 1)").fetchone()[0]

        # On refuse de batir une identite sur des donnees douteuses.
        if vides or doublons:
            print(f"REFUS : la source a {vides} numero(s) vide(s) et {doublons} doublon(s).")
            return 2

        if not existe:
            print(f"{REGISTRE} absent -- creation.")
            if not args.dry_run:
                conn.execute(SCHEMA)

        deja = 0 if not existe else conn.execute(
            f"SELECT count(*) FROM {REGISTRE}").fetchone()[0]

        # --- ce qui manque, ce qui revient, ce qui disparait
        req_neufs = (f"SELECT count(*) FROM {SOURCE} s WHERE NOT EXISTS "
                     f"(SELECT 1 FROM {REGISTRE} r WHERE r.hektor_contact_id = s.hektor_contact_id)")
        req_revenus = (f"SELECT count(*) FROM {REGISTRE} r WHERE r.absent_depuis IS NOT NULL "
                       f"AND EXISTS (SELECT 1 FROM {SOURCE} s WHERE s.hektor_contact_id = r.hektor_contact_id)")
        req_partis = (f"SELECT count(*) FROM {REGISTRE} r WHERE r.absent_depuis IS NULL "
                      f"AND r.hektor_contact_id IS NOT NULL "
                      f"AND NOT EXISTS (SELECT 1 FROM {SOURCE} s WHERE s.hektor_contact_id = r.hektor_contact_id)")

        neufs = conn.execute(req_neufs).fetchone()[0] if existe else total
        revenus = conn.execute(req_revenus).fetchone()[0] if existe else 0
        partis = conn.execute(req_partis).fetchone()[0] if existe else 0

        print(f"source {SOURCE:24s} {total:8d}")
        print(f"registre avant                   {deja:8d}")
        print(f"   a numeroter (neufs)           {neufs:8d}")
        print(f"   revenus (absent_depuis leve)  {revenus:8d}")
        print(f"   disparus (a marquer)          {partis:8d}")

        if args.dry_run:
            print("\n--dry-run : rien ecrit.")
            return 0

        if neufs:
            # L'ordre decide de la serie : on suit celui de Hektor, ce qui rend
            # la table lisible et la reprise reproductible.
            conn.execute(
                f"INSERT INTO {REGISTRE} (hektor_contact_id) "
                f"SELECT s.hektor_contact_id FROM {SOURCE} s "
                f"WHERE NOT EXISTS (SELECT 1 FROM {REGISTRE} r "
                "  WHERE r.hektor_contact_id = s.hektor_contact_id) "
                "ORDER BY CAST(s.hektor_contact_id AS INTEGER), s.hektor_contact_id")
        if revenus:
            conn.execute(
                f"UPDATE {REGISTRE} SET absent_depuis = NULL, "
                "updated_at = CURRENT_TIMESTAMP "
                "WHERE absent_depuis IS NOT NULL AND EXISTS "
                f"(SELECT 1 FROM {SOURCE} s WHERE s.hektor_contact_id = {REGISTRE}.hektor_contact_id)")
        if partis:
            conn.execute(
                f"UPDATE {REGISTRE} SET absent_depuis = date('now'), "
                "updated_at = CURRENT_TIMESTAMP "
                "WHERE absent_depuis IS NULL AND hektor_contact_id IS NOT NULL "
                f"AND NOT EXISTS (SELECT 1 FROM {SOURCE} s "
                f"  WHERE s.hektor_contact_id = {REGISTRE}.hektor_contact_id)")

        # Le registre des recherches suit : il porte le numero du contact chez nous.
        propages = propage_aux_recherches(conn)
        conn.commit()

        # --- verification, apres coup et sur la base reelle
        pose = conn.execute(f"SELECT count(*) FROM {REGISTRE}").fetchone()[0]
        distincts = conn.execute(
            f"SELECT count(DISTINCT app_contact_id) FROM {REGISTRE}").fetchone()[0]
        restent = conn.execute(req_neufs).fetchone()[0]
        absents = conn.execute(
            f"SELECT count(*) FROM {REGISTRE} WHERE absent_depuis IS NOT NULL").fetchone()[0]

        print(f"\nregistre apres                   {pose:8d}   ({distincts} numeros distincts)")
        print(f"   marques absents               {absents:8d}")
        print(f"   contacts sans numero          {restent:8d}")

        if propages is None:
            print("   recherches : registre absent ou non migre -- rien propage.")
        else:
            orphelines = conn.execute(
                "SELECT count(*) FROM app_search_registry "
                "WHERE app_contact_id IS NULL AND hektor_contact_id IS NOT NULL"
            ).fetchone()[0]
            print(f"   recherches numerotees (neuves){propages:8d}")
            print(f"   recherches sans numero        {orphelines:8d}")

        ok = (restent == 0 and distincts == pose)
        print("\n" + ("REGISTRE A JOUR ET VERIFIE." if ok else "ANOMALIE -- a examiner."))
        return 0 if ok else 4
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
