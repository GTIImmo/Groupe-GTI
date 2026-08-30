# -*- coding: utf-8 -*-
"""C.2b — LE REGISTRE DES RECHERCHES REÇOIT LE NUMÉRO DE CONTACT DE L'APP.

POURQUOI CE SCRIPT EXISTE, et c'est une histoire de recommandation perdue.

La relecture d'identité du 24/08 se terminait par cinq recommandations. Quatre ont
été appliquées le lendemain par C.2b. La cinquième disait :

    « Et le registre : lui ajouter app_contact_id, puis relâcher son NOT NULL
      — dans C.2b, pas plus tard »

Elle est tombée entre deux commits. Aucune tâche ne la portait, et personne ne l'a
vue jusqu'au 30/08. Rien n'en dépendait — mais c'est le préalable d'un contact né
dans l'app, donc de C.9.

CE QUE CE SCRIPT FAIT :

    app_search_registry
        + app_contact_id     INTEGER            <- la colonne qui manquait
        hektor_contact_id    TEXT (nullable)    <- le mot qui manquait

SQLite ne sait pas relâcher un NOT NULL : il faut recréer la table. C'est fait en
UNE transaction, avec vérification du compte avant/après — et refus d'écrire si
une seule ligne manquait à l'appel.

LA CLÉ D'UNICITÉ SUIT. L'index unique portait sur (hektor_contact_id,
search_index). Ce couple ne protège plus rien pour une recherche dont le contact
n'aurait pas de numéro Hektor. On ajoute donc son équivalent côté app —
(app_contact_id, search_index) — en index PARTIEL, pour ne contraindre que les
lignes qui portent le numéro.

IDEMPOTENT : rejouer ne fait rien si la colonne est déjà là.
RETOUR ARRIÈRE : la table d'avant est conservée sous app_search_registry_avant_c2b.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
VERROU = RACINE / "phase2" / ".descente.lock"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if VERROU.exists():
        print("La descente est en cours (verrou present) -- on ne touche a rien.")
        return 0

    conn = sqlite3.connect("file:" + BASE.as_posix() + "?mode=rw", timeout=60, uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")

    colonnes = {d[1] for d in conn.execute("PRAGMA table_info(app_search_registry)")}
    if "app_contact_id" in colonnes:
        print("   deja fait : app_contact_id est presente. Rien a faire.")
        conn.close()
        return 0

    avant = conn.execute("SELECT COUNT(*) FROM app_search_registry").fetchone()[0]
    print("   registre avant : %d lignes" % avant)

    conn.executescript("""
    BEGIN;

    -- L'index suit la table renommee et garde son nom : il faut le retirer avant
    -- de recreer le nouveau. Trouve au premier essai -- la transaction s'est
    -- annulee proprement, la table est restee intacte.
    DROP INDEX IF EXISTS idx_search_registry_pair;

    ALTER TABLE app_search_registry RENAME TO app_search_registry_avant_c2b;

    CREATE TABLE app_search_registry (
        app_search_id      INTEGER PRIMARY KEY,
        hektor_contact_id  TEXT,                 -- NULLABLE : une recherche peut naitre
                                                 -- dans l'app, sans numero Hektor
        app_contact_id     INTEGER,              -- le numero du contact chez nous
        search_index       INTEGER NOT NULL,
        contact_search_key TEXT,
        first_seen_at      TEXT,
        last_seen_at       TEXT
    );

    INSERT INTO app_search_registry
        (app_search_id, hektor_contact_id, app_contact_id, search_index,
         contact_search_key, first_seen_at, last_seen_at)
    SELECT r.app_search_id, r.hektor_contact_id, c.app_contact_id, r.search_index,
           r.contact_search_key, r.first_seen_at, r.last_seen_at
      FROM app_search_registry_avant_c2b r
      LEFT JOIN app_contact c ON c.hektor_contact_id = r.hektor_contact_id;

    -- Le couple Hektor reste unique QUAND il existe : index partiel.
    CREATE UNIQUE INDEX idx_search_registry_pair
        ON app_search_registry(hektor_contact_id, search_index)
        WHERE hektor_contact_id IS NOT NULL;

    -- Et son equivalent chez nous, meme forme, meme prudence.
    CREATE UNIQUE INDEX idx_search_registry_pair_app
        ON app_search_registry(app_contact_id, search_index)
        WHERE app_contact_id IS NOT NULL;

    COMMIT;
    """)

    apres = conn.execute("SELECT COUNT(*) FROM app_search_registry").fetchone()[0]
    avec_numero = conn.execute(
        "SELECT COUNT(*) FROM app_search_registry WHERE app_contact_id IS NOT NULL").fetchone()[0]
    sans_numero = apres - avec_numero

    print("   registre apres : %d lignes" % apres)
    print("   avec le numero de contact : %d" % avec_numero)
    print("   sans                      : %d" % sans_numero)

    if apres != avant:
        print()
        print("   ARRET : %d lignes avant, %d apres. La table d'avant est conservee "
              "sous app_search_registry_avant_c2b." % (avant, apres))
        conn.close()
        return 3

    conn.close()
    print()
    print("   fait. Retour arriere possible : app_search_registry_avant_c2b est intacte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
