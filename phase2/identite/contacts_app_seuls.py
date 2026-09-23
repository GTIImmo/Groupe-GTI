#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""26bis-CONTACTS, 26bis-RELATIONS et 26bis-RECHERCHES — LE SERVEUR TIENT CE QUE
LE MIROIR IGNORE.                                                     21/09/2026

LE TROU, et il est le jumeau exact de celui des annonces (annonces_app_seule.py,
26bis-(1), pose le 26/08) :

    build_contacts_layer.py refait CHAQUE NUIT le corps des contacts, la table
    des relations ET celle des recherches -- DELETE FROM puis INSERT, depuis le
    miroir de Hektor (replace_table_rows, lignes 1281 et 1674).

    ⚠ LES RECHERCHES ONT ETE AJOUTEES LE 21/09, par l'audit « les recherches
      seront-elles autonomes a la coupure ? ». Le filet existait pour l'annonce
      (26/08), le contact et la relation (le matin meme) -- pas pour elle, alors
      qu'elle suit exactement le meme chemin. Personne ne l'avait vu.

    Un contact ne dans l'app n'a aucune ligne dans le miroir. Le serveur ne le
    connaitrait donc pas -- et le push du lendemain, qui supprime dans Supabase
    ce qui manque en local, l'EFFACERAIT de l'app. Il n'existe nulle part
    ailleurs : il serait perdu.

CE QUE CE SCRIPT N'EST PAS. Il ne remplace pas la couche, il ne la modifie pas,
il n'injecte rien nulle part. Il RECENSE : il relit ce que l'app detient, le
compare a ce que le serveur sait, et note ce qui n'existe que dans l'app.

POURQUOI RELIRE SUPABASE EN DIRECT et pas la copie locale : la descente tourne a
07:30, donc a 05:30 la copie a 22 heures de retard. Un contact cree hier a 9 h y
manquerait. Meme raisonnement que C.7 et que le script des annonces.

LA TABLE ACCUMULE, ELLE NE SE VIDE JAMAIS. Un echec de lecture veut dire « aucune
nouvelle ce matin », jamais « elles ont disparu ». C'est la regle 5 du projet.
Et comme partout : ABSENT_DEPUIS, JAMAIS DE SUPPRESSION.

AUJOURD'HUI : ZERO. Aucun contact, aucune relation, aucune recherche n'est ne dans l'app -- la
creation sans Hektor est le lot L4. Ce script est donc INERTE, et c'est voulu :
une doublure se pose AVANT d'en avoir besoin, jamais dans l'urgence. Le jour ou
le compteur bougera, la sonde le dira.

⚠ CE QU'IL NE FAIT PAS, DELIBEREMENT : injecter ces lignes dans la couche lue par
  le push. Ce geste-la changerait ce que l'app recoit, avec des colonnes vides ;
  il se decide champ par champ, et c'est le lot L3 (la liste des champs dont
  l'app est maitresse). Ici on OBSERVE.

RETOUR ARRIERE : retirer l'etape du run, puis
    DROP TABLE app_contact_app_seul;  DROP TABLE app_relation_app_seule;
    DROP TABLE app_recherche_app_seule;
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

# Ce que le serveur refait chaque nuit depuis le miroir.
COUCHE_CONTACT = "app_contact_current"
COUCHE_RELATION = "app_contact_relation_current"
COUCHE_RECHERCHE = "app_contact_search_current"
# Ce que l'app detient, relu dans Supabase.
REGISTRE_CONTACT = "app_contact_app_seul"
REGISTRE_RELATION = "app_relation_app_seule"
REGISTRE_RECHERCHE = "app_recherche_app_seule"

# Planchers : si la couche locale est anormalement courte, un run amont a
# echoue. On ne recense pas dans le vide -- on croirait que tout l'app est
# « ne dans l'app ».
PLANCHER_CONTACTS = 100000
PLANCHER_RELATIONS = 10000
PLANCHER_RECHERCHES = 10000

DDL = f"""
CREATE TABLE IF NOT EXISTS {REGISTRE_CONTACT} (
    hektor_contact_id   TEXT PRIMARY KEY,
    app_contact_id      INTEGER,
    donnees_json        TEXT NOT NULL,
    vu_la_premiere_fois TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vu_le               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    absent_depuis       TEXT
);
CREATE TABLE IF NOT EXISTS {REGISTRE_RECHERCHE} (
    contact_search_key  TEXT PRIMARY KEY,
    hektor_contact_id   TEXT,
    app_contact_id      INTEGER,
    donnees_json        TEXT NOT NULL,
    vu_la_premiere_fois TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vu_le               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    absent_depuis       TEXT
);
CREATE TABLE IF NOT EXISTS {REGISTRE_RELATION} (
    relation_key        TEXT PRIMARY KEY,
    hektor_contact_id   TEXT,
    hektor_annonce_id   TEXT,
    app_contact_id      INTEGER,
    donnees_json        TEXT NOT NULL,
    vu_la_premiere_fois TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vu_le               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    absent_depuis       TEXT
);
"""

# Les colonnes que `recenser_objet` recopie quand Supabase les rend. Si l'une
# manque a la table, l'INSERT tombe -- et comme l'etape est « optionnelle », le
# run continue et PERSONNE ne le voit.
#
# ⚠ CONSTATE EN REEL LE 21/09, au premier vrai passage : la table des relations
#   n'avait pas `app_contact_id` alors que la requete le demandait. Le
#   recensement des CONTACTS avait reussi (2 lignes), celui des RELATIONS est
#   tombe, et le run s'est termine en « succes ».
#
# CREATE TABLE IF NOT EXISTS n'ajoute RIEN a une table deja creee : il faut donc
# rattraper les installations existantes, ici, a chaque passage.
COLONNES_ATTENDUES = {
    REGISTRE_CONTACT:   {"app_contact_id": "INTEGER"},
    REGISTRE_RELATION:  {"app_contact_id": "INTEGER", "hektor_annonce_id": "TEXT"},
    REGISTRE_RECHERCHE: {"app_contact_id": "INTEGER", "hektor_contact_id": "TEXT"},
}


def assurer_colonnes(conn: sqlite3.Connection) -> list[str]:
    """Ajoute les colonnes manquantes aux registres deja crees. Idempotent."""
    ajoutees: list[str] = []
    for table, colonnes in COLONNES_ATTENDUES.items():
        presentes = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if not presentes:
            continue
        for nom, type_sql in colonnes.items():
            if nom not in presentes:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {nom} {type_sql}")
                ajoutees.append(f"{table}.{nom}")
    return ajoutees


def connecte() -> sqlite3.Connection:
    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def client_supabase() -> SupabaseRestClient | None:
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return None
    return SupabaseRestClient(base_url=url, service_role_key=cle)


def lire_supabase(client: SupabaseRestClient, table: str, champs: list[str], cle_tri: str) -> list[dict] | None:
    """Relit une table de l'app, PAGINE par sa cle.

    PIEGE MESURE LE 25/08 : PostgREST plafonne TOUTE reponse a 1 000 lignes,
    quelle que soit la limite demandee. Sans pagination on lirait 1 000 contacts
    sur 61 955 et on conclurait, EN SILENCE, que les 60 955 autres n'existent que
    dans l'app -- l'inverse exact de la verite.
    """
    select = ",".join(champs)
    lignes: list[dict] = []
    curseur = ""
    while True:
        chemin = (f"{table}?select={select}&order={cle_tri}.asc&limit=1000")
        if curseur:
            chemin += f"&{cle_tri}=gt.{curseur}"
        page = client.request(method="GET", path=chemin)
        if not isinstance(page, list):
            print(f"REFUS : relecture Supabase inexploitable ({table}) -- rien n'est modifie.")
            return None
        if not page:
            break
        lignes.extend(page)
        suivant = page[-1].get(cle_tri)
        if suivant is None or str(suivant) == curseur:
            print("REFUS : curseur qui n'avance pas -- arret pour ne pas boucler.")
            return None
        curseur = str(suivant)
        if len(page) < 1000:
            break
    return lignes


def recenser_objet(conn, client, *, couche, registre, cle, champs, plancher, libelle) -> int | None:
    total_local = conn.execute(f'SELECT COUNT(*) FROM "{couche}"').fetchone()[0]
    if total_local < plancher:
        print(f"REFUS : {couche} ne compte que {total_local} lignes (plancher {plancher}).")
        print("        Un run amont a probablement echoue -- on ne recense pas dans le vide.")
        return None

    distant = lire_supabase(client, couche, champs, cle)
    if distant is None:
        return None

    connus = {str(r[0]) for r in conn.execute(f'SELECT "{cle}" FROM "{couche}"')}
    inconnus = [r for r in distant if str(r.get(cle) or "") and str(r.get(cle)) not in connus]

    # ── G-12, 23/09/2026 : LE PLANCHER NE PROTEGE PAS DE CE CAS-LA ──────────
    # Les planchers ci-dessus refusent une couche locale TROP COURTE. Ils ne
    # disent rien d'une couche locale COMPLETE mais qui ne parle plus la meme
    # langue : pendant la fenetre de bascule, un cote porte les identites et
    # l'autre encore les numeros de Hektor. Alors AUCUNE cle ne se retrouve, et
    # ce script conclut que TOUT SUPABASE est « ne dans l'app ». Il inscrirait
    # le parc entier dans un registre qui, lui, NE SE VIDE JAMAIS.
    #
    # Le signe est sans ambiguite : la couche locale est pleine, et pourtant
    # elle ne reconnait presque rien de ce que Supabase lui montre.
    if distant and len(inconnus) > 0.9 * len(distant) and len(distant) > 100:
        print(f"REFUS : {couche} -- {len(inconnus)} lignes sur {len(distant)} inconnues "
              f"de la couche locale, qui compte pourtant {total_local} lignes.")
        print("        Les deux cotes ne parlent probablement pas la meme serie de")
        print("        numeros (bascule en cours ?). On ne recense pas un parc entier")
        print("        comme « ne dans l'app » : ce registre ne se vide jamais.")
        return None

    maintenant = "CURRENT_TIMESTAMP"
    neufs = 0
    for ligne in inconnus:
        valeur = str(ligne.get(cle))
        colonnes_sup = [c for c in ("app_contact_id", "hektor_contact_id", "hektor_annonce_id") if c in ligne and c != cle]
        champs_sql = [cle] + colonnes_sup + ["donnees_json"]
        valeurs = [valeur] + [ligne.get(c) for c in colonnes_sup] + [json.dumps(ligne, ensure_ascii=False)]
        place = ",".join("?" for _ in champs_sql)
        cur = conn.execute(
            f'INSERT INTO {registre} ({",".join(champs_sql)}, vu_le) VALUES ({place}, {maintenant}) '
            f'ON CONFLICT({cle}) DO UPDATE SET donnees_json = excluded.donnees_json, vu_le = {maintenant}, absent_depuis = NULL',
            valeurs,
        )
        neufs += 1 if cur.rowcount else 0
    conn.commit()
    total_registre = conn.execute(f"SELECT COUNT(*) FROM {registre}").fetchone()[0]
    print(f"[{libelle}] app={len(distant)} serveur={total_local} "
          f"connus de l'app seule={len(inconnus)} (registre : {total_registre})")
    return len(inconnus)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recense les contacts et relations que le miroir Hektor ignore.")
    parser.add_argument("--recenser", action="store_true", help="Relit l'app et note ce qu'elle seule connait.")
    args = parser.parse_args()
    if not args.recenser:
        print("Rien a faire : passer --recenser.")
        return 0

    conn = connecte()
    conn.executescript(DDL)
    ajoutees = assurer_colonnes(conn)
    if ajoutees:
        print(f"[schema] colonnes ajoutees aux registres : {', '.join(ajoutees)}")
    conn.commit()

    client = client_supabase()
    if client is None:
        return 2

    contacts = recenser_objet(
        conn, client, couche=COUCHE_CONTACT, registre=REGISTRE_CONTACT, cle="hektor_contact_id",
        champs=["hektor_contact_id", "app_contact_id", "display_name", "email", "date_maj"],
        plancher=PLANCHER_CONTACTS, libelle="contacts")
    if contacts is None:
        return 4

    relations = recenser_objet(
        conn, client, couche=COUCHE_RELATION, registre=REGISTRE_RELATION, cle="relation_key",
        champs=["relation_key", "hektor_contact_id", "hektor_annonce_id", "app_contact_id", "role_contact"],
        plancher=PLANCHER_RELATIONS, libelle="relations")
    if relations is None:
        return 4

    # 26bis-RECHERCHES, ajoutee le 21/09 par l'audit d'autonomie des recherches :
    # le filet existait pour l'annonce, le contact et la relation, PAS pour elle --
    # alors que sa table est refaite chaque nuit depuis le miroir, comme les autres.
    # ⚠ L'APP N'EN PORTE QUE LES ACTIVES (11 369 sur 77 061) : la comparaison se
    #   fait donc sur la CLE, pas sur un volume, et le plancher protege du cas ou
    #   la couche locale serait tronquee par un run amont en echec.
    recherches = recenser_objet(
        conn, client, couche=COUCHE_RECHERCHE, registre=REGISTRE_RECHERCHE, cle="contact_search_key",
        champs=["contact_search_key", "hektor_contact_id", "app_contact_id", "search_index", "is_active"],
        plancher=PLANCHER_RECHERCHES, libelle="recherches")
    if recherches is None:
        return 4

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
