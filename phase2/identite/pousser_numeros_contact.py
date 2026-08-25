# -*- coding: utf-8 -*-
"""C.2b -- Lot 2 : Supabase RECOIT la serie de numeros de contact.

LA REGLE, etablie le 19/08 pour les annonces : UNE SEULE SERIE, nee localement
(phase2.app_contact), et Supabase la recopie. Deux series independantes
divergeraient -- c'est exactement le sinistre des annonces.

CE SCRIPT NE FABRIQUE AUCUN NUMERO. Il lit le registre local et le transmet.

POURQUOI PAR UNE FONCTION ET PAS UN UPSERT : un upsert PostgREST insererait une
ligne fantome pour tout identifiant que Supabase ne connait pas. Le local a
355 687 contacts, Supabase 57 553 -- le cas est MAJORITAIRE, pas theorique.
app_contact_id_backfill ne peut QUE mettre a jour.

FREIN : lots de 2 000 et une pause entre chaque. La descente du 22/08 avait
sature Supabase au point qu'il fallait le redemarrer ; on ne recommence pas.

IDEMPOTENT : rejouer ne touche aucune ligne et renvoie 0.

RETOUR ARRIERE : update app_contact_current set app_contact_id = null.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)

BASE = RACINE / "phase2" / "phase2.sqlite"
LOT = 2000
PAUSE = 0.4


def charge_env() -> None:
    """Le projet lit .env A LA RACINE **et** apps/hektor-v1/.env -- les cles
    Supabase sont dans le second. On reutilise son chargeur plutot que d'en
    ecrire un autre qui divergerait."""
    for fichier in DEFAULT_ENV_FILES:
        load_env_file(fichier)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--lot", type=int, default=LOT)
    args = ap.parse_args()

    charge_env()
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return 2

    conn = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        # On n'envoie QUE ce que Supabase connait : la doublure descendue le dit.
        lignes = conn.execute("""
            SELECT r.hektor_contact_id, r.app_contact_id
              FROM app_contact r
              JOIN app_contact_current__sb s
                ON s.hektor_contact_id = r.hektor_contact_id
             ORDER BY r.app_contact_id
        """).fetchall()
    finally:
        conn.close()

    total_local = 355687
    print(f"registre local          {total_local:8d} numeros")
    print(f"connus de Supabase      {len(lignes):8d}  -> a transmettre")
    print(f"lots de {args.lot}, pause {PAUSE}s -> {(len(lignes)+args.lot-1)//args.lot} requetes")

    if args.dry_run:
        print("\n--dry-run : rien envoye.")
        return 0

    client = SupabaseRestClient(base_url=url, service_role_key=cle)
    touchees = 0
    envoyees = 0
    debut = time.time()
    for depart in range(0, len(lignes), args.lot):
        lot = [{"h": h, "a": a} for h, a in lignes[depart:depart + args.lot]]
        n = client.request(method="POST", path="rpc/app_contact_id_backfill",
                           payload={"payload": lot})
        touchees += int(n or 0)
        envoyees += len(lot)
        print(f"   {envoyees:6d}/{len(lignes)}   mises a jour cumulees : {touchees}")
        time.sleep(PAUSE)

    print(f"\n   {envoyees} transmis, {touchees} lignes mises a jour, "
          f"{time.time()-debut:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
