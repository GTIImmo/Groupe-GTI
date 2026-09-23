#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4-b (②) — LE SERVEUR APPREND QUEL NUMERO HEKTOR EST QUELLE IDENTITE.
                                                                  21/09/2026

LE DEFAUT QUE CET OUTIL VIENT FERMER, mesure en reel le 21/09. Le premier
contact ne dans l'app a fini en DEUX fiches :

    10000001  ESSAI L4B  <- l'app lui a donne son identite
      605450  ESSAI L4B  <- le retour du worker l'a repose sous le numero Hektor

Le retour ne fait rien d'anormal : il lit 605450 dans le miroir et le pousse.
Simplement, RIEN ne lui dit que 605450 EST 10 000 001. La correspondance existe
pourtant depuis la seconde ou le worker a pose la case cible -- mais elle vit
dans Supabase, et `hektor_target_id` n'apparaissait dans AUCUN fichier de
phase2/ (mesure du 21/09). Ce script est le chainon manquant.

⚠ POURQUOI ICI, ET PAS DANS LE PUSH. La premiere idee etait de traduire au
  moment d'envoyer. Elle est FAUSSE, et de facon dangereuse : les cles des
  relations et des recherches ne CONTIENNENT pas le numero de contact, elles
  sont CALCULEES dessus (`relation_key = stable_hash({"contact_id": ...})`,
  build_contacts_layer.py:663). Traduire au push laisserait des empreintes
  calculees sur le numero Hektor et des colonnes portant l'identite -- et le run
  suivant prendrait ces lignes pour des disparues, donc il les SUPPRIMERAIT.
  La substitution doit avoir lieu AVANT le calcul des empreintes, dans le build.
  Ce script ne fait que lui apporter la table de correspondance.

CE QU'IL NE TOUCHE PAS : rien. Il ecrit une table a lui, `app_contact_identite_app`,
que personne d'autre ne lit. Tant que le build ne s'en sert pas, il est inerte.

AU 21/09 : 1 ligne (le contact d'essai « ESSAI L4B-2 »). Pour les 356 000 autres
contacts, identite = numero Hektor : il n'y a rien a traduire, et la table reste
vide de leur cote -- c'est voulu, on ne recopie pas 356 000 identites egales a
elles-memes.

IDEMPOTENT : rejouer repose les memes lignes.
RETOUR ARRIERE : DROP TABLE app_contact_identite_app; -- le build retombe alors
                 sur son comportement d'avant, celui qui fabrique deux fiches.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
TABLE = "app_contact_identite_app"
VUE = "app_v_correspondance_identite_cible"

# On emprunte au push la liste des fichiers d'environnement plutot que de la
# redeviner : c'est deja ce que fait elargir_perimetre_console.py, et une
# seconde liste qui derive est une panne qui attend son jour. On ne LIT jamais
# ces fichiers a l'ecran : ils portent la cle de service.
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: E402

# ── C-3, 23/09/2026 : LE GARDE-FOU NE PEUT PLUS ETRE UN COMPTE ─────────────
# La version du 21/09 refusait au-dela de 5 000 lignes : « un derapage est plus
# probable qu'un parc entier ne dans l'app ». C'etait vrai tant que la vue
# rendait 0 ou 1 ligne. LE JOUR DE LA BASCULE ELLE EN REND 61 984 -- tout le
# perimetre eligible -- et ce garde-fou arretait l'etape. Pire : l'etape etant
# non bloquante, le run continuait avec la correspondance de la veille, et le
# build rangeait tout un parc sous les numeros de Hektor.
#
# ⚠ ET ON NE LE REPARE PAS EN L'AUGMENTANT. Si un parc entier devient normal,
#   un derapage le devient aussi : le compte ne distingue plus rien.
#
# On verifie donc la FORME, pas la taille -- et la forme tient a n'importe quel
# volume. Un vrai derapage, c'est deux identites qui visent le meme numero de
# Hektor, ou un numero qui sort de sa plage. Pas un grand nombre.
PLAFOND_ABSURDE = 1_000_000
PLAGE_NUMEROS_APP = 10_000_000
PAGE = 1000  # PostgREST plafonne ses reponses ; on pagine au lieu d'esperer.


def charger_env() -> None:
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)


def assurer_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""CREATE TABLE IF NOT EXISTS {TABLE} (
                hektor_contact_id TEXT PRIMARY KEY,
                app_identite      TEXT NOT NULL,
                vu_le             TEXT NOT NULL
            )"""
    )


def lire_supabase() -> list[dict]:
    """Lit la correspondance ENTIERE, page par page.

    ⚠ La version du 21/09 demandait `limit=10000` en une fois. PostgREST plafonne
      ses reponses : au-dela, il rend une page et se tait. Avec 0 ou 1 ligne cela
      ne se voyait pas ; a la bascule, la correspondance serait arrivee TRONQUEE,
      et les contacts manquants auraient ete ranges sous leur numero Hektor --
      c'est-a-dire une seconde fiche pour chacun d'eux.
    """
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
    base = f"{url.rstrip('/')}/rest/v1/{VUE}?select=app_identite,hektor_contact_id"
    # ORDRE STABLE OBLIGATOIRE : sans `order`, deux pages successives peuvent
    # rendre la meme ligne et en sauter une autre. Une pagination sans tri n'est
    # pas une pagination.
    base += "&order=hektor_contact_id.asc"
    toutes: list[dict] = []
    depart = 0
    while True:
        adresse = f"{base}&offset={depart}&limit={PAGE}"
        requete = urllib.request.Request(adresse, headers={
            "apikey": cle, "Authorization": f"Bearer {cle}", "Accept": "application/json"})
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            page = json.loads(reponse.read().decode("utf-8"))
        if not isinstance(page, list) or not page:
            break
        toutes.extend(page)
        if len(page) < PAGE:
            break
        depart += len(page)
        if len(toutes) > PLAFOND_ABSURDE:
            raise RuntimeError(
                f"{len(toutes)} correspondances lues : au-dela du concevable, on s'arrete.")
    return toutes


def verifier_la_correspondance(lignes: list[dict]) -> list[str]:
    """Le garde-fou : la FORME, pas la taille. Rend la liste des griefs.

    Un derapage ne se reconnait pas a son volume mais a son incoherence :
      - une identite qui ne serait pas dans NOTRE plage ;
      - un numero Hektor qui serait dans la notre ;
      - DEUX identites qui visent le meme numero Hektor -- c'est exactement le
        defaut du 21/09 (une personne, deux fiches), vu depuis l'autre bout ;
      - une identite qui apparaitrait deux fois.
    """
    griefs: list[str] = []
    vus_hektor: dict[str, str] = {}
    vus_identite: dict[str, str] = {}
    for ligne in lignes:
        hektor = str(ligne.get("hektor_contact_id") or "").strip()
        identite = str(ligne.get("app_identite") or "").strip()
        if not hektor.isdigit() or not identite.isdigit():
            griefs.append(f"non numerique : hektor={hektor!r} identite={identite!r}")
            continue
        if int(identite) < PLAGE_NUMEROS_APP:
            griefs.append(f"identite {identite} hors de notre plage (< {PLAGE_NUMEROS_APP})")
        if int(hektor) >= PLAGE_NUMEROS_APP:
            griefs.append(f"numero Hektor {hektor} dans NOTRE plage (>= {PLAGE_NUMEROS_APP})")
        if hektor in vus_hektor and vus_hektor[hektor] != identite:
            griefs.append(
                f"deux identites visent le numero Hektor {hektor} : "
                f"{vus_hektor[hektor]} et {identite}")
        if identite in vus_identite and vus_identite[identite] != hektor:
            griefs.append(
                f"l'identite {identite} vise deux numeros Hektor : "
                f"{vus_identite[identite]} et {hektor}")
        vus_hektor[hektor] = identite
        vus_identite[identite] = hektor
    return griefs[:20]  # on en montre assez pour comprendre, pas de deluge


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Redescend la correspondance identite app <-> numero Hektor.")
    parser.add_argument("--dry-run", action="store_true", help="Compter sans ecrire.")
    args = parser.parse_args()

    charger_env()
    try:
        lignes = lire_supabase()
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError) as err:
        # ON NE FAIT PAS TOMBER LE RUN. Sans correspondance, le build retombe sur
        # son comportement d'avant : il range sous le numero Hektor. C'est le
        # defaut qu'on corrige, pas une perte de donnees -- et la sonde
        # `data.contacts_double_identite` le dira.
        print(f"[correspondance] lecture impossible, on garde la table precedente : {type(err).__name__}")
        return 0

    griefs = verifier_la_correspondance(lignes)
    if griefs:
        print(f"REFUS : la correspondance est incoherente ({len(lignes)} ligne(s) lues).")
        for grief in griefs:
            print(f"        - {grief}")
        print("        On ne traduit pas sur une table dont la forme est fausse.")
        return 3

    maintenant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        assurer_table(conn)
        if args.dry_run:
            print(f"[correspondance] {len(lignes)} correspondance(s) lue(s) (dry-run)")
            return 0
        # On REPOSE, on ne cumule pas : une case cible corrigee doit se refleter.
        conn.execute(f"DELETE FROM {TABLE}")
        conn.executemany(
            f"INSERT OR REPLACE INTO {TABLE} (hektor_contact_id, app_identite, vu_le) VALUES (?,?,?)",
            [(str(l["hektor_contact_id"]), str(l["app_identite"]), maintenant)
             for l in lignes
             if str(l.get("hektor_contact_id") or "").strip()
             and str(l.get("app_identite") or "").strip()])
        conn.commit()
        total = conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
    finally:
        conn.close()

    print(f"[correspondance] {total} contact(s) ne(s) dans l'app, leur numero Hektor est connu du serveur")
    if total == 0:
        print("[correspondance] aucun contact n'est encore ne dans l'app : rien a traduire.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
