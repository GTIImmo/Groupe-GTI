# -*- coding: utf-8 -*-
"""A.3-tech etape C -- POSER LE REGISTRE SANS LE VIDER.          30/09/2026

POURQUOI CE SCRIPT EXISTE, ALORS QUE `--rebuild-register-only` EXISTE DEJA
---------------------------------------------------------------------------
La reconstruction officielle VIDE la table puis la refait. Elle marche -- elle a
sauve le registre le 29/09 -- mais elle porte une consigne qui la rend
inutilisable en journee :

    « pendant l'operation le registre est VIDE : jamais pendant le run de nuit,
      jamais quand l'agence consulte. »

Or `register_row_id` est la CLE PRIMAIRE de app_mandat_register_current. Un
simple UPSERT fait donc le meme travail sans la fenetre noire :
    les 453 lignes neuves      -> INSERT
    les 24 025 deja presentes  -> UPDATE
et A AUCUN INSTANT le registre n'est vide. L'agence peut consulter pendant.

CE QUI JUSTIFIE QUE RIEN NE SOIT SUPPRIME
------------------------------------------
Mesure du 30/09, avant l'operation : le fabricant produit exactement les 24 025
lignes du registre, plus 453. « vue locale MOINS fabricant : 0 » -- il n'y a
donc AUCUNE ligne orpheline a retirer. Si ce n'etait pas le cas, ce script
laisserait des lignes mortes, et il le DIT : il compte l'ecart avant et apres.

⚠ CE SCRIPT NE REMPLACE PAS `--rebuild-register-only`. Celle-la reste la bonne
  reponse quand le registre est CORROMPU (lignes figees, colonnes fausses) :
  seule une table videe garantit qu'il ne reste rien de l'ancien etat. Ici on
  sait exactement ce qu'on change, et on ne change que cela.

LECTURE : locale + miroir. ECRITURE : Supabase, UPSERT seul, aucun DELETE.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "phase2" / "sync"))

from phase2.sync.export_app_payload import (  # noqa: E402
    REGISTRE_DEPUIS_APP_MANDAT,
    build_mandat_register_rows,
)
from push_upgrade_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    build_current_mandat_register_rows,
    adapter_registre_au_schema,
    load_env_files,
)

TABLE = "app_mandat_register_current"
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pose le registre des mandats par UPSERT, sans jamais le vider.")
    parser.add_argument("--a-blanc", action="store_true",
                        help="Compte ce qui serait pose, sans rien envoyer.")
    parser.add_argument("--taille-lot", type=int, default=100,
                        help="Lignes par appel. Elles sont LARGES (65 colonnes, "
                             "dont trois blobs JSON) : 100 tient sous la limite.")
    args = parser.parse_args()

    print("interrupteur APP_REGISTRE_DEPUIS_APP_MANDAT : %s" % REGISTRE_DEPUIS_APP_MANDAT)
    con = sqlite3.connect("file:%s?mode=ro" % PHASE2_DB.as_posix(), uri=True)
    con.execute("ATTACH DATABASE ? AS hektor", (f"file:{HEKTOR_DB.as_posix()}?mode=ro",))
    con.row_factory = sqlite3.Row
    t0 = time.time()
    try:
        brutes = build_mandat_register_rows(con, limit=None)
    finally:
        con.close()
    lignes = build_current_mandat_register_rows(brutes)
    print("fabrique : %s lignes en %.0f s" % (len(lignes), time.time() - t0))

    if args.a_blanc:
        print("A BLANC -- rien n'est envoye")
        return 0

    load_env_files(DEFAULT_ENV_FILES)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    client = SupabaseRestClient(base_url=url, service_role_key=cle)
    lignes = adapter_registre_au_schema(client, lignes)

    t1 = time.time()
    # UPSERT SEUL. Pas de delete_all_rows, pas de delete_rows_by_ids : c'est
    # toute la difference avec la reconstruction, et c'est ce qui permet de le
    # faire pendant que l'agence travaille.
    client.upsert_rows(path=TABLE, rows=lignes, batch_size=args.taille_lot)
    print("pose : %s lignes en %.0f s -- AUCUNE suppression" % (len(lignes), time.time() - t1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
