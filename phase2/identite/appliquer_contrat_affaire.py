# -*- coding: utf-8 -*-
"""C.19 (etape 2) -- L'ENDROIT OU LES CHAMPS D'AFFAIRE CESSENT D'APPARTENIR A HEKTOR.

LE TROISIEME PENDANT DE C.7. appliquer_contrat.py arbitre les champs d'ANNONCE
(cle app_dossier_id) ; appliquer_contrat_mandat.py ceux du MANDAT (couple
annonce+mandat) ; celui-ci ceux de l'AFFAIRE, au grain app_affaire_id -- l'identite
posee le 20/08, UNE seule serie pour offre, compromis et vente.

LA REGLE, celle du mandat et pas celle des contacts :

    l'app a une valeur   ->  elle gagne
    l'app n'a rien       ->  ON NE TOUCHE A RIEN

Parce que Hektor connait ces champs-la, lui. Un « l'app gagne » aveugle effacerait
un prix que Hektor detient et que l'app n'a jamais saisi.

CE QU'IL ECRIT, ET OU. Deux endroits, parce que les transactions vivent a deux
endroits :

  1. app_affaire_ledger -- il accumule, mais affaire_ledger.py le rafraichit
     depuis le miroir a chaque run : sans cette etape, la valeur de l'app y serait
     ecrasee des le lendemain.

  2. app_view_generale -- DETRUITE et refaite chaque nuit. C'est donc APRES sa
     reconstruction qu'il faut reposer ce que l'app detient, et seulement pour la
     transaction COURANTE de l'annonce (la seule que cette vue porte). Les autres
     restent dans le ledger, ou la fiche ira les chercher a l'etape 3.

L'APPARIEMENT est fait sur le TRIPLET (annonce, type, identifiant Hektor), jamais
sur l'identifiant seul : Hektor tient trois compteurs qui se telescopent -- 7 541
numeros portes par deux types differents.

AUJOURD'HUI CETTE ETAPE NE FAIT RIEN, et c'est voulu : le magasin est vide tant
que l'ecran (etape 3) ne sait pas ecrire. La machinerie existe et attend.

RETOUR ARRIERE : retirer l'etape du run. Sur la vue, sans effet -- elle est refaite
chaque nuit. Sur le ledger, le run suivant d'affaire_ledger.py remet la valeur de
Hektor.

    python phase2/identite/appliquer_contrat_affaire.py --dry-run
    python phase2/identite/appliquer_contrat_affaire.py
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
sys.path.insert(0, str(RACINE / "phase2" / "identite"))

from contrat_autorite import CHAMPS_APP_AFFAIRE, contrat_affaire_vide  # noqa: E402

MAGASIN = "app_affaire_champ_app"
LEDGER = "app_affaire_ledger"
VUE = "app_view_generale"

# (type d'affaire, champ du magasin) -> colonne de app_view_generale.
# Seule la transaction COURANTE de l'annonce est concernee : c'est la seule que
# la vue porte. Les absents de cette carte ne vont que dans le ledger.
CARTE_VUE = {
    ("offre", "montant"):        "offre_montant",
    ("offre", "date"):           "offre_event_date",
    ("compromis", "montant"):    "prix_publique",
    ("compromis", "date"):       "compromis_date_start",
    ("compromis", "date_acte"):  "date_signature_acte",
    ("compromis", "sequestre"):  "compromis_sequestre",
    ("vente", "montant"):        "vente_prix",
    ("vente", "date"):           "vente_date",
}

# La colonne de la vue qui porte l'identifiant Hektor de la transaction courante.
COLONNE_ID = {"offre": "offre_id", "compromis": "compromis_id", "vente": "vente_id"}


def colonnes(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute('PRAGMA table_info("%s")' % table)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="montre sans rien ecrire")
    args = ap.parse_args()

    if contrat_affaire_vide():
        print("contrat affaire vide : rien a appliquer.")
        return 0
    print("contrat affaire : %s" % ", ".join(CHAMPS_APP_AFFAIRE))

    conn = sqlite3.connect("file:" + BASE.as_posix() + "?mode=rw", timeout=60, uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")

    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (MAGASIN,)).fetchone():
        print("%s n'existe pas encore : rien a appliquer." % MAGASIN)
        conn.close()
        return 0

    champs_vue = colonnes(conn, VUE)
    champs_ledger = colonnes(conn, LEDGER)

    # Ce que l'app detient, et qui compte. VIDE NE GAGNE PAS.
    saisies = conn.execute(
        "SELECT app_affaire_id, champ, valeur_app FROM " + MAGASIN + " "
        "WHERE valeur_app IS NOT NULL AND TRIM(valeur_app) <> '' "
        "  AND champ IN (%s)" % ",".join("?" * len(CHAMPS_APP_AFFAIRE)),
        tuple(CHAMPS_APP_AFFAIRE)).fetchall()
    print("magasin : %d valeur(s) que l'app detient" % len(saisies))
    if not saisies:
        print("\nRien a poser -- l'app n'a encore rien saisi.")
        conn.close()
        return 0

    # De quelle affaire s'agit-il ? On lit le ledger, jamais on ne devine.
    infos = {}
    for aid, annonce, kind, hid in conn.execute(
            "SELECT app_affaire_id, CAST(hektor_annonce_id AS TEXT), kind, "
            "CAST(hektor_affaire_id AS TEXT) FROM " + LEDGER):
        if aid is not None:
            infos[int(aid)] = (annonce, kind, hid)

    pose_ledger = pose_vue = ignores = 0
    for aid, champ, valeur in saisies:
        ref = infos.get(int(aid))
        if ref is None:
            ignores += 1
            continue
        annonce, kind, hid = ref

        # 1. le ledger, qui porte toutes les transactions
        if champ in champs_ledger and not args.dry_run:
            conn.execute('UPDATE "%s" SET "%s" = ? WHERE app_affaire_id = ?'
                         % (LEDGER, champ), (valeur, aid))
        if champ in champs_ledger:
            pose_ledger += 1

        # 2. la vue, mais SEULEMENT si c'est la transaction courante de l'annonce
        colonne = CARTE_VUE.get((kind, champ))
        colonne_id = COLONNE_ID.get(kind)
        if colonne and colonne in champs_vue and colonne_id and hid:
            if not args.dry_run:
                conn.execute(
                    'UPDATE "%s" SET "%s" = ? '
                    'WHERE CAST(hektor_annonce_id AS TEXT) = ? '
                    '  AND CAST("%s" AS TEXT) = ?' % (VUE, colonne, colonne_id),
                    (valeur, annonce, hid))
            pose_vue += 1

    if not args.dry_run:
        conn.commit()
    conn.close()

    print()
    print("   posees dans le ledger              : %d" % pose_ledger)
    print("   posees dans la vue (courantes)     : %d" % pose_vue)
    print("   affaires inconnues du ledger       : %d" % ignores)
    if args.dry_run:
        print("\n--dry-run : rien ecrit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
