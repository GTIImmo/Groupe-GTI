# -*- coding: utf-8 -*-
"""C.13-b -- L'ENDROIT OU LA CLOTURE DE MANDAT CESSE D'APPARTENIR A HEKTOR.

LE PENDANT DE C.7, AU GRAIN DU MANDAT. appliquer_contrat.py arbitre les champs
d'ANNONCE (cle app_dossier_id) ; celui-ci arbitre les champs de MANDAT (cle
couple annonce+mandat, la seule qui soit unique -- 24 939 sur 24 939, mesure du
28/08). Une annonce porte plusieurs mandats dans sa vie : au grain de l'annonce,
on ne saurait pas QUEL mandat est clos.

LA REGLE, ET ELLE N'EST PAS CELLE DES CONTACTS :

    l'app a une valeur   ->  elle gagne
    l'app n'a rien       ->  ON NE TOUCHE A RIEN

Pourquoi. Le contrat des contacts applique « l'app gagne » sans condition, et
c'est sans danger : Hektor ne connait pas ces champs-la. Pour le mandat, il en
connait 94. Le tout premier passage du magasin en a trouve TROIS que Hektor dit
clos et que Supabase ignore : un « l'app gagne » aveugle les aurait effaces des
la premiere nuit, en silence. Arbitrage de Frederic, 28/08.

CE QU'IL ECRIT, ET OU. app_view_generale est DETRUITE et refaite chaque nuit :
c'est donc APRES sa reconstruction qu'il faut reposer ce que l'app detient. Il
n'ecrit que la colonne mandat_date_cloture, et seulement pour le mandat COURANT
de l'annonce -- c'est le seul que cette vue porte. Les mandats des cycles passes
se traitent dans le constructeur du registre, qui lit le meme magasin.

AUJOURD'HUI CETTE ETAPE NE FAIT RIEN, et c'est voulu : le magasin ne contient
que des observations ou l'app est VIDE, donc la regle ci-dessus les ecarte
toutes. La machinerie existe et attend que l'app produise des clotures.

RETOUR ARRIERE : retirer l'etape du run. Elle n'ecrit que dans app_view_generale,
qui est de toute facon refaite chaque nuit.

    python phase2/identite/appliquer_contrat_mandat.py --dry-run
    python phase2/identite/appliquer_contrat_mandat.py
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contrat_autorite import CHAMPS_APP_MANDAT, VIDE_NE_GAGNE_PAS, contrat_mandat_vide  # noqa: E402

CIBLE = "app_view_generale"
MAGASIN = "app_mandat_champ_app"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="montre sans rien ecrire")
    args = ap.parse_args()

    print("contrat mandat : %s" % (", ".join(CHAMPS_APP_MANDAT) or "(aucun)"))
    if contrat_mandat_vide():
        print("Contrat vide -- Hektor garde la main sur tous les champs de mandat.")
        return 0

    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")

    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if MAGASIN not in tables:
        print("Le magasin %s n'existe pas encore -- rien a appliquer." % MAGASIN)
        conn.close()
        return 0
    colonnes = {c[1] for c in conn.execute('PRAGMA table_info("%s")' % CIBLE)}
    inconnus = [c for c in CHAMPS_APP_MANDAT if c not in colonnes]
    if inconnus:
        # Meme garde-fou qu'en C.7 : on refuse plutot que d'ecrire a cote.
        print("REFUS : le contrat cite des champs absents de %s : %s" % (CIBLE, inconnus))
        conn.close()
        return 3

    applique = 0
    for champ in CHAMPS_APP_MANDAT:
        # LA REGLE : on ne retient QUE les valeurs non vides. C'est elle qui
        # empeche d'effacer une cloture que Hektor porte et que l'app ignore.
        condition = "AND COALESCE(TRIM(valeur_app),'') <> ''" if VIDE_NE_GAGNE_PAS else ""
        couples = conn.execute(
            "SELECT hektor_annonce_id, valeur_app FROM %s "
            "WHERE champ = ? %s" % (MAGASIN, condition), (champ,)).fetchall()

        if not couples:
            print("   %s : aucune valeur detenue par l'app -- rien a poser" % champ)
            continue
        if args.dry_run:
            print("   [dry-run] %s : %d valeur(s) a poser" % (champ, len(couples)))
            continue

        # Table temporaire INDEXEE puis UN SEUL UPDATE : app_view_generale n'a
        # aucun index sur hektor_annonce_id, et un UPDATE par ligne balaierait
        # les 61 092 lignes a chaque fois -- le piege mesure le 25/08 en C.7.
        conn.execute("DROP TABLE IF EXISTS temp._arbitrage_mandat")
        conn.execute("CREATE TEMP TABLE _arbitrage_mandat "
                     "(hektor_annonce_id TEXT PRIMARY KEY, valeur)")
        conn.executemany("INSERT OR REPLACE INTO temp._arbitrage_mandat VALUES (?,?)", couples)
        cur = conn.execute(
            'UPDATE "%s" SET "%s" = ('
            '   SELECT a.valeur FROM temp._arbitrage_mandat a '
            '    WHERE a.hektor_annonce_id = CAST("%s".hektor_annonce_id AS TEXT)) '
            ' WHERE CAST(hektor_annonce_id AS TEXT) IN '
            '   (SELECT hektor_annonce_id FROM temp._arbitrage_mandat)'
            % (CIBLE, champ, CIBLE))
        conn.execute("DROP TABLE temp._arbitrage_mandat")
        print("   %s : %d ligne(s) arbitree(s) en faveur de l'app" % (champ, cur.rowcount))
        applique += cur.rowcount

    if args.dry_run:
        conn.close()
        print("\n--dry-run : rien ecrit.")
        return 0

    conn.commit()
    conn.close()
    print("\n   %d valeur(s) posee(s) par le contrat de mandat." % applique)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
