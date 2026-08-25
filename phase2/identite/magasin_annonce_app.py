# -*- coding: utf-8 -*-
"""C.6 -- LE DOMICILE DE L'ANNONCE : le magasin de ce que l'app detient.

LE DIAGNOSTIC A ETE CORRIGE LE 21/08, et c'est ce qui rend cette tache petite.
On croyait que « le serveur ne detient pas les annonces ». Faux : app_view_generale
compte 56 899 lignes et 130 colonnes, refaite chaque nuit en 37 secondes, et le
miroir GELE a la coupure -- il ne disparait pas.

LE VRAI PROBLEME N'EST PAS LA CONSERVATION, C'EST L'ECRITURE :

    phase2/pipeline/view_generale.py:35
        DROP TABLE IF EXISTS app_view_generale;
        CREATE TABLE app_view_generale AS ...

Une valeur ecrite par l'app dans cette table ne survivrait pas jusqu'a 05:30.
Il faut donc une table A COTE, JAMAIS RECONSTRUITE -- exactement le patron qui a
deja marche trois fois ici : app_dossier, app_affaire_ledger, app_search_registry.

POURQUOI CLE/VALEUR ET PAS UNE COLONNE PAR CHAMP :
    la carte A1 recense 189 champs et l'ensemble grandira ; une colonne par champ
    imposerait un ALTER a chaque ajout. Et c'est CREUX : la plupart des annonces
    n'ont rien que l'app detienne.

CE QUE CE SCRIPT ENREGISTRE, et ce qu'il n'affirme PAS.
    Il compare ce que Supabase dit (app_dossier_current, descendu chaque matin)
    a ce que le miroir dit (app_view_generale), et il NOTE les ecarts.
    Un ecart n'est PAS une preuve que l'app est l'auteur : ce peut etre un simple
    decalage. Le magasin OBSERVE, il ne tranche pas. C'est C.7 qui tranchera, et
    la carte A1 qui dira qui possede quoi.

PERSONNE NE LIT ENCORE CETTE TABLE. C'est une doublure : on observe avant de commuter.

RETOUR ARRIERE : DROP TABLE app_annonce_champ_app.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

BASE = Path(r"C:\Hektor\Projet\phase2\phase2.sqlite")
VERROU = Path(r"C:\Hektor\Projet\pull_from_supabase.lock")

MIROIR = "app_view_generale"          # ce que dit HEKTOR, refait chaque nuit
APP = "app_dossier_current"           # ce que dit L'APP, descendu chaque matin
MAGASIN = "app_annonce_champ_app"

SCHEMA = f"""
CREATE TABLE {MAGASIN} (
    app_dossier_id  INTEGER NOT NULL,
    champ           TEXT    NOT NULL,
    valeur_app      TEXT,
    valeur_miroir   TEXT,
    vu_le           TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vu_la_premiere_fois TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (app_dossier_id, champ)
)
"""

# Champs techniques ou derives : un ecart n'y veut rien dire. On ne les note pas,
# sinon le magasin serait noye et illisible.
IGNORES = {
    "app_dossier_id", "hektor_annonce_id",
    "refreshed_at", "source_hash", "source_updated_at", "search_text",
}


def norme(expr: str) -> str:
    """Compare ce qui se compare -- pas les representations.

    DEUX PIEGES, tous deux mesures le 25/08 :

    1. Supabase stocke NULL la ou le miroir stocke 0.0. Sans normalisation, `prix`
       semblait diverger sur 7 143 des 13 211 annonces. Le projet a deja la regle :
       « 0 vaut vide » (memoire dpe-0-vaut-vide-fiche-hektor).

    2. Le meme montant est un ENTIER cote app et un TEXTE cote miroir : 0 contre '0'.
       Ma premiere version ecrivait GLOB '[-0-9][0-9.]*' en pensant « expression
       reguliere ». GLOB SUIT LA SYNTAXE DU SHELL : `*` y est un joker, pas un
       quantificateur, donc ce motif EXIGE AU MOINS DEUX CARACTERES et '0' n'y
       correspondait pas. 23 faux ecarts.

    3. Hektor ecrit '0000-00-00 00:00:00' pour une date vide -- la sentinelle MySQL.
       Cote Supabase c'est NULL. Meme valeur, deux ecritures.

    LE TEST NUMERIQUE EXCLUT LE TIRET, exprès : '2026-08-24' ne contient que des
    chiffres et des tirets ; le convertir en nombre donnerait 2026, et deux dates
    differentes deviendraient egales. Les montants n'etant jamais negatifs ici, on
    ne perd rien.
    """
    txt = f"trim(CAST({expr} AS TEXT))"
    canon = "rtrim(rtrim(printf('%.6f', CAST({v} AS REAL)), '0'), '.')"
    return f"""CASE
        WHEN {expr} IS NULL THEN ''
        WHEN {txt} = '' THEN ''
        WHEN {txt} IN ('0000-00-00 00:00:00', '0000-00-00') THEN ''
        WHEN typeof({expr}) IN ('integer','real')
          THEN CASE WHEN {expr} = 0 THEN '' ELSE {canon.format(v=expr)} END
        WHEN {txt} NOT GLOB '*[^0-9.]*'
          THEN CASE WHEN CAST({expr} AS REAL) = 0 THEN '' ELSE {canon.format(v=expr)} END
        ELSE {txt}
    END"""


def connecte() -> sqlite3.Connection:
    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def colonnes(conn: sqlite3.Connection, table: str) -> list[str]:
    return [c[1] for c in conn.execute(f'PRAGMA table_info("{table}")')]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rebatir", action="store_true",
                    help="jette le magasin et le refait -- apres un correctif de comparaison")
    args = ap.parse_args()

    # La descente tient ce verrou pendant ~21 minutes. Ecrire pendant qu'elle
    # tourne, c'est l'incident du 22/08 -- on ne recommence pas.
    if VERROU.exists() and not args.dry_run:
        print(f"REFUS : la descente tourne ({VERROU.name} present). Reessayer apres.")
        return 5

    conn = connecte()
    try:
        cols_miroir = set(colonnes(conn, MIROIR))
        cols_app = colonnes(conn, APP)
        communs = [c for c in cols_app if c in cols_miroir and c not in IGNORES]

        n_app = conn.execute(f"SELECT count(*) FROM {APP}").fetchone()[0]
        n_miroir = conn.execute(f"SELECT count(*) FROM {MIROIR}").fetchone()[0]
        print(f"{APP:24s} {n_app:8d} lignes  {len(cols_app):3d} colonnes  (ce que dit l'APP)")
        print(f"{MIROIR:24s} {n_miroir:8d} lignes  {len(cols_miroir):3d} colonnes  (ce que dit HEKTOR)")
        print(f"champs comparables       {len(communs):8d}   ({len(IGNORES)} techniques ecartes)")

        existe = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
            (MAGASIN,)).fetchone()[0] > 0
        if existe and args.rebatir:
            print(f"--rebatir : {MAGASIN} vide avant reconstruction.")
            if not args.dry_run:
                conn.execute(f"DROP TABLE {MAGASIN}")
                existe = False
        if not existe:
            print(f"\n{MAGASIN} absent -- creation.")
            if not args.dry_run:
                conn.execute(SCHEMA)

        # Une seule requete par champ : SQLite compare 13 211 lignes en un clin d'oeil,
        # et 53 requetes valent mieux qu'un produit cartesien de 53 colonnes.
        ecarts: list[tuple[str, int]] = []
        for champ in communs:
            n = conn.execute(f'''
                SELECT count(*) FROM {APP} a JOIN {MIROIR} m
                  ON m.app_dossier_id = a.app_dossier_id
                 WHERE {norme(f'a."{champ}"')} <> {norme(f'm."{champ}"')}
            ''').fetchone()[0]
            if n:
                ecarts.append((champ, n))

        ecarts.sort(key=lambda x: -x[1])
        print(f"\n=== CHAMPS QUI DIVERGENT ({len(ecarts)} sur {len(communs)}) ===")
        for champ, n in ecarts[:25]:
            print(f"   {champ:38s} {n:6d}")
        if len(ecarts) > 25:
            print(f"   ... et {len(ecarts)-25} autres")

        if args.dry_run:
            print("\n--dry-run : rien ecrit.")
            return 0

        # On enregistre. `vu_la_premiere_fois` ne bouge jamais : c'est la memoire.
        pose = 0
        for champ, _ in ecarts:
            cur = conn.execute(f'''
                INSERT INTO {MAGASIN} (app_dossier_id, champ, valeur_app, valeur_miroir)
                SELECT a.app_dossier_id, ?, a."{champ}", m."{champ}"
                  FROM {APP} a JOIN {MIROIR} m ON m.app_dossier_id = a.app_dossier_id
                 WHERE {norme(f'a."{champ}"')} <> {norme(f'm."{champ}"')}
                ON CONFLICT(app_dossier_id, champ) DO UPDATE SET
                     valeur_app    = excluded.valeur_app,
                     valeur_miroir = excluded.valeur_miroir,
                     vu_le         = CURRENT_TIMESTAMP
            ''', (champ,))
            pose += cur.rowcount
        conn.commit()

        total = conn.execute(f"SELECT count(*) FROM {MAGASIN}").fetchone()[0]
        annonces = conn.execute(
            f"SELECT count(DISTINCT app_dossier_id) FROM {MAGASIN}").fetchone()[0]
        print(f"\n   {pose} lignes ecrites -- le magasin contient {total} valeurs "
              f"sur {annonces} annonces")
        print("\nMAGASIN A JOUR. Personne ne le lit : on observe avant de commuter.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
