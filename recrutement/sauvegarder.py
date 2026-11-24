# -*- coding: utf-8 -*-
"""Etape ⑦ du run du recrutement (tous les deux mois) : la SAUVEGARDE de la base locale (note, §13 R5).

    python -X utf8 recrutement/sauvegarder.py            -> copie datee + rotation (6 gardees)
    python -X utf8 recrutement/sauvegarder.py --essai    -> dit ce qu'il ferait, n'ecrit rien

Patron : scheduled/run_backup.ps1 (dossier date sous C:\\Hektor\\Backups\\, retention glissante).
  - la copie passe par l'API de sauvegarde de SQLite, jamais par une copie de fichier : la base est
    en WAL, et un fichier copie pendant une ecriture peut etre incomplet (vu le 20/11 : la copie
    par fichier ne portait pas le journal WAL) ;
  - la copie est RELUE (integrity_check + nombre de fiches egal a l'original) : une sauvegarde
    qu'on ne relit pas n'en est pas une ;
  - le CSV de la collecte est copie a cote ;
  - on garde les 6 plus recentes : UN AN au rythme de tous les deux mois (decision du 24/11 ; c'etait
    12 au rythme mensuel). Les plus anciennes sont supprimees --
    c'est aussi ainsi qu'une personne effacee dans l'app disparait des sauvegardes (un an au plus,
    duree ecrite dans la mention d'information).
Sortie : 0 = copie faite et relue, 1 = echec (le run le verra).
"""
import argparse
import datetime as dt
import os
import shutil
import sqlite3
import sys
from pathlib import Path

DOSSIER = Path(os.environ.get("RECRUTEMENT_DONNEES", r"C:\Hektor\recrutement_donnees"))
BASE = DOSSIER / "recrutement.sqlite"
CIBLE = Path(os.environ.get("RECRUTEMENT_SAUVEGARDES", r"C:\Hektor\Backups\recrutement"))
GARDER = 6  # un an, une collecte tous les deux mois


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--essai", action="store_true")
    args = p.parse_args()
    if not BASE.exists():
        print(f"ECHEC : base introuvable {BASE}")
        return 1
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    copie = CIBLE / f"recrutement_{stamp}.sqlite"
    src = sqlite3.connect(BASE, timeout=60)
    n_src = src.execute("select count(*) from fiche").fetchone()[0]
    if args.essai:
        print(f"[essai] copierait {BASE} ({n_src} fiches) vers {copie}")
        anciennes = sorted(CIBLE.glob("recrutement_*.sqlite"))[:-GARDER] if CIBLE.exists() else []
        print(f"[essai] supprimerait {len(anciennes)} ancienne(s) copie(s)")
        return 0
    CIBLE.mkdir(parents=True, exist_ok=True)
    dst = sqlite3.connect(copie)
    src.backup(dst)
    dst.close()
    src.close()
    relue = sqlite3.connect(copie)
    integrite = relue.execute("pragma integrity_check").fetchone()[0]
    n_copie = relue.execute("select count(*) from fiche").fetchone()[0]
    relue.close()
    if integrite != "ok" or n_copie != n_src:
        print(f"ECHEC : copie relue {integrite}, {n_copie} fiches contre {n_src}")
        return 1
    csvs = sorted((DOSSIER / "sortie").glob("candidats_region_*.csv"))
    if csvs:
        shutil.copy2(csvs[-1], CIBLE / f"{csvs[-1].stem}_{stamp}.csv")
    for vieux in sorted(CIBLE.glob("recrutement_*.sqlite"))[:-GARDER]:
        vieux.unlink()
    for vieux in sorted(CIBLE.glob("candidats_region_*.csv"))[:-GARDER]:
        vieux.unlink()
    print(f"sauvegarde : {copie.name} ({n_copie} fiches, integrite ok) ; "
          f"{len(list(CIBLE.glob('recrutement_*.sqlite')))} copie(s) gardee(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
