import sqlite3
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from refresh_views import PHASE2_DB, HEKTOR_DB, SQL_REFRESH_VUE_GENERALE


def main() -> None:
    con = sqlite3.connect(PHASE2_DB)
    try:
        cur = con.cursor()
        cur.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        cur.executescript(SQL_REFRESH_VUE_GENERALE)
        con.commit()

        total = cur.execute("SELECT COUNT(*) FROM app_view_generale").fetchone()[0]
        print(f"count = {total}")
        print()

        for row in cur.execute(
            """
            SELECT
                numero_dossier,
                titre_bien,
                commercial_nom,
                statut_global,
                sous_statut,
                alerte_principale,
                validation_diffusion_state,
                etat_visibilite,
                etat_transaction,
                priority
            FROM app_view_generale
            LIMIT 20
            """
        ):
            print(row)
    finally:
        con.close()


if __name__ == "__main__":
    main()
