# -*- coding: utf-8 -*-
"""C.2b -- le numero de contact descend jusqu'aux 18 tables satellites.

CE QUI MANQUAIT, et ce n'etait pas une erreur de conception : c'est un geste qui
n'a jamais ete rendu recurrent.

Le 25/08, une migration a pose `app_contact_id` sur les 19 tables de Supabase et
les a remplies « par jointure dans Postgres » -- 144 985 lignes, EN UNE FOIS.
L'entretien mis en place ensuite ne couvre qu'**une** de ces tables :

    registre_contacts.py        tient le registre local `app_contact`
    pousser_numeros_contact.py  recopie la serie dans app_contact_current
                                                       ^^^^^^^^^^^^^^^^^^^ une seule

Les 18 autres n'ont plus jamais ete alimentees. Toute ligne ecrite apres le
25/08 -- une relation, un rapprochement, une recherche -- naissait sans numero :

    25/08   161 · 26/08 1 301 · 27/08 3 216 · 28/08  29
    29/08   226 · 30/08    20 · 31/08   335        =  5 288 en 7 jours

Rien ne s'effacait : c'est le neuf qui arrivait vide. Et la sentinelle posee le
meme jour ne regardait que `app_contact_current` -- la seule table entretenue,
donc la seule au vert. Personne ne pouvait le voir.

POURQUOI DANS POSTGRES ET PAS DANS LE PUSH. La premiere idee etait de faire
porter la colonne a la couche LOCALE, comme les annonces la portent dans
`app_view_generale`. Deux defauts, trouves en l'ecrivant :

  1. l'empreinte du push couvre toutes les colonnes sauf `refreshed_at` :
     ajouter une colonne changerait TOUTES les empreintes et renverrait les
     200 000 lignes d'un coup. La descente du 22/08 a sature Supabase comme ca,
     au point qu'il a fallu le redemarrer ;
  2. l'exclure de l'empreinte reglait le premier defaut mais en creait un pire :
     une ligne poussee AVANT d'avoir son numero enverrait `app_contact_id = null`
     et EFFACERAIT celui deja present.

La propagation cote Postgres n'a aucun de ces defauts, et elle couvre en plus
`app_rapprochement` (2 754 lignes), qui est calcule dans Supabase et ne passe
jamais par le push.

CE QU'ELLE NE FAIT PAS, VOLONTAIREMENT :
  * elle ne remplit QUE les cases vides -- jamais elle n'ecrase un numero ;
  * elle ne touche AUCUNE autre colonne ;
  * elle laisse les 35 orphelines de `app_search_count_high_water` (contact
    disparu, deja signalees le 25/08) et les 58 envois sans contact rattache.
    Ils ne sont pas rattrapables, et une sentinelle qui les compterait ne
    redescendrait jamais a zero.

IDEMPOTENT : rejouer rend 0.
RETOUR ARRIERE : aucun necessaire -- la colonne n'est encore lue par personne.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)


def charge_env() -> None:
    """Meme chargeur que ses voisins -- les cles Supabase vivent dans
    apps/hektor-v1/.env, pas seulement a la racine."""
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="compte ce qui serait rempli, n'ecrit rien")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    charge_env()
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return 2

    client = SupabaseRestClient(base_url=url, service_role_key=cle)

    # L'etat d'avant, par la vue de la sentinelle : elle ne compte que le
    # RATTRAPABLE (contact existant, numero connu, ligne qui ne le porte pas).
    avant = client.request(method="GET",
                           path="app_contacts_sans_numero?select=source&limit=100000")
    a_rattraper = len(avant) if isinstance(avant, list) else 0
    print("   lignes rattrapables avant : %d" % a_rattraper)

    if args.dry_run:
        print("\n   --dry-run : rien ecrit.")
        return 0

    resultat = client.request(method="POST", path="rpc/app_contact_id_propager",
                              payload={})
    if isinstance(resultat, str):
        try:
            resultat = json.loads(resultat)
        except Exception:
            pass
    total = (resultat or {}).get("total", 0) if isinstance(resultat, dict) else 0
    detail = (resultat or {}).get("detail", {}) if isinstance(resultat, dict) else {}

    print("   lignes remplies           : %d" % total)
    for table, n in sorted(detail.items(), key=lambda x: -x[1]):
        print("      %-40s %6d" % (table, n))

    apres = client.request(method="GET",
                           path="app_contacts_sans_numero?select=source&limit=100000")
    reste = len(apres) if isinstance(apres, list) else 0
    print("   lignes rattrapables apres : %d" % reste)

    if reste:
        print()
        print("   ATTENTION : il reste %d ligne(s) rattrapable(s) apres la "
              "propagation -- ce n'est pas normal, a examiner." % reste)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
