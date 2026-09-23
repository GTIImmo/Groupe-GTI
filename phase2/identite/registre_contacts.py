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
    hektor_target_id  TEXT,
    created_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    absent_depuis     TEXT,
    UNIQUE(hektor_contact_id)
)
"""


def assurer_la_case_cible(conn: sqlite3.Connection) -> int:
    """Le registre garde le numero de Hektor a part, AVANT qu'on y touche.

    ⚠ TRANCHE LE 23/09/2026, ET CELA CORRIGE MA PROPRE PROCEDURE DE BASCULE.
      Le plan disait « traduire app_contact.hektor_contact_id en identite ».
      Mesure faite ce jour : cette table n'a QUE deux colonnes de numero --
      app_contact_id et hektor_contact_id. Traduire en place EFFACERAIT le
      numero de Hektor du registre, et avec lui la seule correspondance locale
      dont `affaire_ledger` se sert pour relier une VENTE a son ACHETEUR
      (le lien que Frederic avait fait doubler le 01/09 precisement parce qu'il
      etait le seul non double du projet).

      C'est le meme geste que L4-c ④ a fait cote couche : on garde la cible a
      part. La couche l'avait, le registre ne l'a jamais eu.

    Idempotent : un CREATE TABLE IF NOT EXISTS n'ajoute RIEN a une table qui
    existe deja -- d'ou cet ALTER explicite.
    Dormant : tant que rien n'est traduit, cible = numero de Hektor.
    """
    colonnes = {d[1] for d in conn.execute(f"PRAGMA table_info({REGISTRE})")}
    if "hektor_target_id" not in colonnes:
        conn.execute(f"ALTER TABLE {REGISTRE} ADD COLUMN hektor_target_id TEXT")
    # On ne remplit QUE les cases vides : apres la bascule, hektor_contact_id
    # portera l'identite, et il ne faudrait surtout pas la recopier par-dessus.
    curseur = conn.execute(
        f"UPDATE {REGISTRE} SET hektor_target_id = hektor_contact_id "
        f"WHERE hektor_target_id IS NULL AND hektor_contact_id IS NOT NULL "
        f"  AND CAST(hektor_contact_id AS INTEGER) < 10000000")
    return curseur.rowcount or 0


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

        # (2) 23/09 : la case cible, AVANT toute traduction. Voir la fonction.
        if not args.dry_run:
            posees = assurer_la_case_cible(conn)
            if posees:
                print(f"case cible du registre : {posees} numero(s) de Hektor mis a l'abri.")

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
            # L4-b 21/09/2026 -- LE NUMERO EST DONNE EXPLICITEMENT. La table est
            # en AUTOINCREMENT et SQLite refuse de faire redescendre un compteur
            # qui a saute : on calcule donc nous-memes.
            #
            # ⛔ CORRIGE LE 22/09, ET LE DEFAUT ETAIT MUET. La version du 21/09
            #   cherchait « le plus grand numero SOUS 10 000 000 », pour rester
            #   sous la plage reservee a l'app. Le decalage du 22/09 (L4-c ⓪) a
            #   fait monter TOUTE la doublure au-dessus de 10 000 000 : plus une
            #   seule ligne ne passait ce filtre, COALESCE rendait 0, et le
            #   contact suivant aurait recu le numero 1, puis 2, puis 3 --
            #   recreant exactement le recouvrement des deux series qu'on venait
            #   de supprimer. Et sans rien casser : les numeros 1 a 100 sont
            #   libres depuis le decalage, l'INSERT aurait reussi.
            #
            # ⚠ ET UN SECOND DEFAUT, TROUVE DANS LA FOULEE : retirer le filtre
            #   ne suffisait pas. Le registre LOCAL sert les contacts venus de
            #   HEKTOR ; le distributeur de Supabase sert ceux qui NAISSENT dans
            #   l'app. Les deux auraient donne 10 356 138 au suivant -- deux
            #   personnes, un seul numero. Mesure du 22/09.
            #
            # D'OU TROIS ETAGES, et chacun se reconnait a son ordre de grandeur :
            #       < 10 000 000                 Hektor (mort a la coupure)
            #       10 000 001 a 19 999 999      la doublure, contacts de Hektor
            #       >= 20 000 000                contacts NES DANS L'APP
            # Tout ce qui est au-dessus de 10 M est a nous ; le second seuil
            # separe seulement nos deux sources. Le distributeur de Supabase a
            # ete repositionne a 20 000 000 le meme jour.
            conn.execute(
                f"INSERT INTO {REGISTRE} (app_contact_id, hektor_contact_id) "
                f"SELECT (SELECT COALESCE(MAX(app_contact_id), 0) FROM {REGISTRE} "
                "         WHERE app_contact_id < 20000000) "
                "       + ROW_NUMBER() OVER (ORDER BY CAST(s.hektor_contact_id AS INTEGER), s.hektor_contact_id), "
                f"       s.hektor_contact_id FROM {SOURCE} s "
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

        # ⚠ LA CASE CIBLE, UNE SECONDE FOIS -- ET C'EST ICI QU'ELLE COMPTE.
        # L'appel du haut sert aux fiches DEJA presentes. Mais les contacts
        # NEUFS sont inseres APRES lui : au run du 23/09, les 10 nouveaux sont
        # repartis sans leur case cible, et ne l'auraient eue que la nuit
        # SUIVANTE. Or c'est justement elle qui garde le numero de Hektor quand
        # la bascule reecrira hektor_contact_id -- sans elle, pour ces dix-la,
        # le numero de Hektor aurait ete PERDU.
        # Defaut de mon propre correctif du matin, trouve par le run du soir.
        posees_apres = assurer_la_case_cible(conn)
        if posees_apres:
            print(f"case cible des neufs : {posees_apres} numero(s) mis a l'abri.")

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
