import sqlite3
from pathlib import Path

try:
    from phase2.pipeline.view_demandes_mandat_diffusion import SQL_REFRESH_DEMANDES_MANDAT_DIFFUSION
    from phase2.pipeline.view_generale import SQL_REFRESH_VUE_GENERALE
except ModuleNotFoundError:
    import sys

    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from phase2.pipeline.view_demandes_mandat_diffusion import SQL_REFRESH_DEMANDES_MANDAT_DIFFUSION
    from phase2.pipeline.view_generale import SQL_REFRESH_VUE_GENERALE


ROOT = Path(__file__).resolve().parent.parent
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"


def refresh_views() -> None:
    con = sqlite3.connect(PHASE2_DB)
    try:
        con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        con.executescript(SQL_REFRESH_DEMANDES_MANDAT_DIFFUSION)
        con.executescript(SQL_REFRESH_VUE_GENERALE)
        con.commit()
    finally:
        con.close()


if __name__ == "__main__":
    refresh_views()
    print("Refreshed: app_view_demandes_mandat_diffusion")
