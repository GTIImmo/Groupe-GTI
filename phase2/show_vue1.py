import sqlite3
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from refresh_views import PHASE2_DB, HEKTOR_DB, SQL_REFRESH_DEMANDES_MANDAT_DIFFUSION


def main() -> None:
    con = sqlite3.connect(PHASE2_DB)
    try:
        cur = con.cursor()
        cur.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        cur.executescript(SQL_REFRESH_DEMANDES_MANDAT_DIFFUSION)
        con.commit()

        total = cur.execute(
            "SELECT COUNT(*) FROM app_view_demandes_mandat_diffusion"
        ).fetchone()[0]
        print(f"count = {total}")
        print()

        for row in cur.execute(
            """
            SELECT
                numero_dossier,
                titre_bien,
                type_demande_label,
                work_status,
                validation_diffusion_state,
                etat_visibilite,
                priority,
                commercial_nom
            FROM app_view_demandes_mandat_diffusion
            LIMIT 20
            """
        ):
            print(row)
    finally:
        con.close()


if __name__ == "__main__":
    main()
