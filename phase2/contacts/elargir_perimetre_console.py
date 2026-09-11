#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SI HEKTOR NOMME QUELQU'UN DANS UNE TRANSACTION, L'APP DOIT POUVOIR LE NOMMER.
                                                                  11/09/2026

LE PERIMETRE D'AVANT, et pourquoi il laissait des trous. Un contact ne montait
vers l'app qu'a deux conditions, posees dans build_contacts_layer :

    active_annonce_relation   il est lie a une annonce ACTIVE
    active_search             il a une recherche ACTIVE

58 723 contacts sur 355 978, soit 16,5 %. Cette regle est anterieure a la
lecture console, et elle ne pouvait pas voir ce que celle-ci a revele.

CE QUI MANQUAIT, mesure le 11/09 apres le rattrapage des 9 216 compromis :

    role nomme par Hektor      personnes    absentes de l'annuaire
    mandant                       23 271                     1 191
    acquereur                     11 362                       465
    notaire cote vendeur              84                        80
    notaire cote acquereur            59                        57
                                                    ------------------
                                            1 738 personnes distinctes

⚠ DEUX MANQUES DE NATURE DIFFERENTE, et un seul critere les couvre.
  · Les mandants et acquereurs absents sont ceux dont la transaction est FAITE :
    le bien est vendu ou archive, donc plus actif, donc la regle les ecartait.
    Leur nom n'apparaissait plus dans l'app alors que Hektor l'affiche encore.
  · Les notaires manquent presque TOUS (137 sur 143), et pour une autre raison :
    ils n'entrent dans AUCUNE relation. L'API ne les rend jamais (0 sur 10 586,
    mesure du 10/09) et ils ne sont ni vendeurs ni acheteurs. Aucun elargissement
    fonde sur les relations ne les aurait rattrapes -- seule la lecture du
    formulaire les connait.

POURQUOI UNE PASSE SEPAREE, ET PAS UNE LIGNE DANS build_contacts_layer. Celui-ci
lit la base LOCALE ; or `app_affaire_console` est ecrite dans SUPABASE par le
rattrapage et par le worker (9 216 lignes en ligne, 1 400 en local). Il faut donc
relire Supabase, ce que ce script fait -- exactement comme annonces_app_seule.py,
et pour la meme raison. On se pose APRES la construction de la couche, comme le
registre d'identite des contacts.

⚠ A REJOUER CHAQUE NUIT, APRES build_contacts_layer : celui-ci refait
  `app_contact_current` par DELETE + INSERT et remet donc l'eligibilite a ce que
  sa regle dit. Sans cette passe, l'elargissement dure une journee.

IDEMPOTENT : rejouer n'ajoute rien et affiche 0 marque.
RETOUR ARRIERE : ne plus l'appeler. La nuit suivante remet le perimetre d'avant.

    python phase2/contacts/elargir_perimetre_console.py [--dry-run]
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
SOURCE = "app_affaire_console"
CIBLE = "app_contact_current"
RAISON = "console_transaction_party"

# Les quatre roles que le formulaire de l'assistant nomme, et eux seuls.
# `acquereurs` et `mandants` portent les NUMEROS ; `parties_json` porte en plus
# les noms et telephones, notaires compris.
ROLES_PARTIES = ("acquereurs", "mandants", "notaires_acquereur", "notaires_mandant")


def client_supabase() -> SupabaseRestClient | None:
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return None
    return SupabaseRestClient(base_url=url, service_role_key=cle)


def numero(valeur) -> str | None:
    """Un identifiant de contact, ou rien. On ne fabrique jamais de numero."""
    texte = str(valeur if valeur is not None else "").strip().strip('"')
    return texte if texte.isdigit() else None


def personnes_citees(client: SupabaseRestClient) -> set[str] | None:
    """Tous les numeros nommes par Hektor dans une transaction, PAGINE.

    ⚠ PIEGE DEJA PAYE LE 25/08 : PostgREST plafonne TOUTE reponse a 1 000 lignes,
      quelle que soit la limite demandee. Sans pagination on lirait 1 000 lignes
      sur 9 216 et on conclurait a tort -- EN SILENCE -- que le reste n'existe pas.
    """
    champs = "app_affaire_id,acquereurs,mandants,parties_json"
    vus: set[str] = set()
    curseur = -1
    lignes = 0
    while True:
        page = client.request(
            method="GET",
            path=(f"{SOURCE}?select={champs}"
                  f"&app_affaire_id=gt.{curseur}"
                  "&order=app_affaire_id.asc&limit=1000"),
        )
        if not isinstance(page, list):
            print("REFUS : lecture Supabase inexploitable -- rien n'est modifie.")
            return None
        if not page:
            break
        for ligne in page:
            lignes += 1
            for cle in ("acquereurs", "mandants"):
                for x in (ligne.get(cle) or []):
                    n = numero(x)
                    if n:
                        vus.add(n)
            parties = ligne.get("parties_json") or {}
            if isinstance(parties, str):
                try:
                    parties = json.loads(parties)
                except Exception:
                    parties = {}
            if isinstance(parties, dict):
                for role in ROLES_PARTIES:
                    for personne in (parties.get(role) or []):
                        n = numero((personne or {}).get("id") if isinstance(personne, dict) else personne)
                        if n:
                            vus.add(n)
        suivant = page[-1].get("app_affaire_id")
        if suivant is None or int(suivant) <= curseur:
            print("REFUS : curseur qui n'avance pas -- arret pour ne pas boucler.")
            return None
        curseur = int(suivant)
    print("lignes de transaction lues   %7d" % lignes)
    return vus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Compter sans ecrire.")
    args = ap.parse_args()

    client = client_supabase()
    if client is None:
        return 1
    cites = personnes_citees(client)
    if cites is None:
        return 1
    print("personnes citees par Hektor  %7d" % len(cites))
    if not cites:
        print("Rien a faire.")
        return 0

    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.row_factory = sqlite3.Row

    avant = conn.execute(
        f"SELECT COUNT(*) FROM {CIBLE} WHERE supabase_sync_eligible = 1").fetchone()[0]

    # Qui est cite ET aujourd'hui ecarte. On ne touche a personne d'autre.
    a_marquer: list[tuple[str, str]] = []
    for ligne in conn.execute(
        f"SELECT hektor_contact_id, eligibility_reasons_json FROM {CIBLE} "
        f"WHERE supabase_sync_eligible = 0"
    ):
        cid = str(ligne["hektor_contact_id"])
        if cid not in cites:
            continue
        try:
            raisons = json.loads(ligne["eligibility_reasons_json"] or "[]")
        except Exception:
            raisons = []
        if not isinstance(raisons, list):
            raisons = []
        if RAISON not in raisons:
            raisons.append(RAISON)
        a_marquer.append((json.dumps(raisons, ensure_ascii=False), cid))

    print("annuaire avant               %7d" % avant)
    print("a faire entrer               %7d" % len(a_marquer))

    if args.dry_run:
        print("\n--dry-run : rien n'a ete ecrit.")
        conn.close()
        return 0

    if a_marquer:
        # Une seule transaction : ou tout le monde entre, ou personne.
        with conn:
            conn.executemany(
                f"UPDATE {CIBLE} SET supabase_sync_eligible = 1, "
                f"eligibility_reasons_json = ? WHERE hektor_contact_id = ?",
                a_marquer,
            )

    apres = conn.execute(
        f"SELECT COUNT(*) FROM {CIBLE} WHERE supabase_sync_eligible = 1").fetchone()[0]
    print("annuaire apres               %7d   (+%d)" % (apres, apres - avant))

    # ── LA VERIFICATION QUI COMPTE : personne n'est entre sans raison, et
    #    personne n'est sorti. On confronte, on ne se contente pas d'un compte.
    sans_raison = conn.execute(
        f"SELECT COUNT(*) FROM {CIBLE} "
        f"WHERE supabase_sync_eligible = 1 AND eligibility_reasons_json IN ('', '[]')"
    ).fetchone()[0]
    print("eligibles sans aucune raison %7d   %s"
          % (sans_raison, "OK" if sans_raison == 0 else "A REGARDER"))
    conn.close()
    return 0 if sans_raison == 0 and apres >= avant else 1


if __name__ == "__main__":
    raise SystemExit(main())
