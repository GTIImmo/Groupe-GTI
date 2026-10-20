"""MARQUER LOCALEMENT QU'UNE ANNONCE EST SORTIE DU BROUILLON -- chantier 7, piece ④.
                                                                  20/10/2026

POURQUOI CE SCRIPT EXISTE, ET POURQUOI IL EST SI PETIT.

Quand le worker sort une annonce du brouillon chez Hektor (`etatAnnonce = 1`), il le
PROUVE en relisant `isDraft` par GraphQL. Mais notre miroir local, lui, dit encore
« brouillon » : il n'est rafraichi que par `sync_hektor_drafts.py`, au run de 05:00.

⛔ SANS CETTE CORRECTION, L'ANNONCE SERAIT NULLE PART JUSQU'A 05:00.
   La garde de la piece ① (`est_un_brouillon` dans push_single_annonce_to_supabase)
   lit ce meme miroir : elle refuserait donc de faire entrer l'annonce dans
   `app_dossier_current`. Et elle vient de quitter le panier brouillon. Resultat :
   invisible des deux cotes, sans erreur, pendant des heures.

⭐ ON NE DEVINE RIEN : on ecrit ce qu'on VIENT de faire et de prouver chez Hektor.
  Et le run de nuit relit Hektor de toute facon -- si notre ecriture etait fausse,
  il la corrigerait.

⚠ ON N'ECRIT QUE SI LA LIGNE EXISTE ET DIT ENCORE « brouillon ». Sinon on ne touche
  a rien et on le DIT (statut « deja_a_jour » ou « ligne_absente »), au lieu de
  rendre un succes muet.
⚠ busy_timeout obligatoire : le run de nuit ecrit dans cette base (regle du projet).

    python phase2/sync/marquer_brouillon_sorti.py --hektor-annonce-id 63131
    python phase2/sync/marquer_brouillon_sorti.py --hektor-annonce-id 63131 --dry-run
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "hektor.sqlite"
TABLE = "hektor_annonce_draft_state"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hektor-annonce-id", required=True)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--dry-run", action="store_true",
                        help="dit ce qu'il ferait, sans rien ecrire")
    args = parser.parse_args()

    annonce = str(args.hektor_annonce_id).strip()
    if not annonce.isdigit():
        raise SystemExit("hektor_annonce_id numerique requis")

    chemin = Path(args.db_path)
    if not chemin.exists():
        print(json.dumps({"status": "miroir_absent", "db_path": str(chemin)}, ensure_ascii=False))
        return 1

    con = sqlite3.connect(str(chemin), timeout=30)
    try:
        con.execute("pragma busy_timeout = 30000")
        existe = con.execute(
            f"select count(*) from sqlite_master where type='table' and name='{TABLE}'"
        ).fetchone()[0]
        if not existe:
            print(json.dumps({"status": "table_absente", "table": TABLE}, ensure_ascii=False))
            return 1

        ligne = con.execute(
            f"select is_draft from {TABLE} where cast(hektor_annonce_id as text) = ?",
            (annonce,),
        ).fetchone()

        if ligne is None:
            # ⚠ Pas une panne : l'annonce n'a jamais ete vue comme brouillon en local.
            #   On le DIT, pour qu'un « succes » ne cache pas une absence.
            compte_rendu = {"status": "ligne_absente", "hektor_annonce_id": annonce}
        elif int(ligne[0] or 0) == 0:
            compte_rendu = {"status": "deja_a_jour", "hektor_annonce_id": annonce, "is_draft": 0}
        elif args.dry_run:
            compte_rendu = {"status": "dry_run", "hektor_annonce_id": annonce,
                            "is_draft_avant": 1, "is_draft_apres": 0}
        else:
            con.execute(
                f"update {TABLE} set is_draft = 0, seen_at = ? "
                f"where cast(hektor_annonce_id as text) = ?",
                (datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), annonce),
            )
            con.commit()
            # ⚠ ON RELIT : on exige la preuve du succes, jamais l'absence d'erreur.
            apres = con.execute(
                f"select is_draft from {TABLE} where cast(hektor_annonce_id as text) = ?",
                (annonce,),
            ).fetchone()
            if apres is None or int(apres[0] or 0) != 0:
                raise SystemExit(
                    f"ECHEC : {annonce} est toujours marque brouillon dans le miroir apres l'ecriture."
                )
            compte_rendu = {"status": "done", "hektor_annonce_id": annonce,
                            "is_draft_avant": 1, "is_draft_apres": 0}
    finally:
        con.close()

    print(json.dumps(compte_rendu, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
