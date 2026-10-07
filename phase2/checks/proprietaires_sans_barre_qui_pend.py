"""CONTROLE -- plus aucune barre qui pend dans les resumes proprietaires.  07/10/2026

LE DEFAUT, signale par Frederic sur l'annonce 63198 : la fiche affichait
« Emmanuel MILAGRO | ». GROUP_CONCAT garde les chaines VIDES, donc un
proprietaire sans nom -- les fiches de couple MUETTES -- laissait le separateur
tout seul. Mesure du 07/10 : 6 596 fiches sur 12 687 pour les noms, 7 112 sur
12 124 pour les coordonnees.

⛔ ET C'EST MON COMMIT e060bb5 (06/10) QUI L'A RENDU VISIBLE : il a inverse le
  COALESCE de `mandants_texte` pour que NOS mandants gagnent -- ce qui etait juste
  -- et a du meme coup promu ce resume mal forme au premier rang de la fiche.

L'EPREUVE NE SIMULE RIEN, ET SON « AVANT » N'EST PAS UNE RECONSTITUTION :
    AVANT = la table app_view_generale TELLE QU'ELLE EST, fabriquee cette nuit
            par la version PRECEDENTE du code
    APRES = la meme table refabriquee SUR UNE COPIE avec SQL_REFRESH_VUE_GENERALE,
            la constante du run, importee et non recopiee
C'est donc une vraie preuve a l'envers : si le correctif ne faisait rien, les deux
mesures seraient identiques.
    ➡ memoire `eprouver-c-est-executer-le-code`

⚠ IL ECRIT, mais UNIQUEMENT dans une COPIE placee dans le dossier temporaire.
  La base de production est ouverte en LECTURE SEULE.

    python phase2/checks/proprietaires_sans_barre_qui_pend.py

CE QUI DOIT ETRE VRAI
    ① apres : ZERO resume qui commence ou finit par « | »
    ② le nombre de lignes de la table ne change pas
    ③ un resume ne devient vide QUE si tous ses proprietaires sont muets
      (et alors `mandants_texte` retombe sur le texte de Hektor, ce qui est mieux)
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
RACINE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RACINE))

from phase2.pipeline.view_generale import SQL_REFRESH_VUE_GENERALE  # noqa: E402

PHASE2_DB = RACINE / "phase2" / "phase2.sqlite"
HEKTOR_DB = RACINE / "data" / "hektor.sqlite"

CHAMPS = ("proprietaires_resume", "proprietaires_contacts", "honoraires_resume")


def mesurer(con: sqlite3.Connection) -> dict[str, tuple[int, int, int]]:
    """Par champ : (renseignes, barre_au_bout, barre_au_debut)."""
    sortie = {}
    for champ in CHAMPS:
        r = con.execute(
            "SELECT"
            "  SUM(CASE WHEN COALESCE({c},'') <> '' THEN 1 ELSE 0 END),"
            "  SUM(CASE WHEN TRIM(COALESCE({c},'')) LIKE '%|' THEN 1 ELSE 0 END),"
            "  SUM(CASE WHEN TRIM(COALESCE({c},'')) LIKE '|%' THEN 1 ELSE 0 END)"
            " FROM app_view_generale".format(c=champ)
        ).fetchone()
        sortie[champ] = tuple(int(v or 0) for v in r)
    return sortie


def imprimer(titre: str, m: dict[str, tuple[int, int, int]], lignes: int) -> None:
    print("   %s  (%d lignes)" % (titre, lignes))
    for champ, (renseignes, bout, debut) in m.items():
        print("      %-24s renseignes %6d   barre au bout %5d   au debut %4d"
              % (champ, renseignes, bout, debut))


def main() -> int:
    echecs = 0
    print("CONTROLE -- les resumes proprietaires et leur barre qui pend")
    print()

    # ── AVANT : la production telle qu'elle est, en LECTURE SEULE ──────────────
    src = sqlite3.connect("file:%s?mode=ro" % PHASE2_DB.as_posix(), uri=True, timeout=30)
    avant = mesurer(src)
    lignes_avant = src.execute("SELECT COUNT(*) FROM app_view_generale").fetchone()[0]
    imprimer("AVANT -- table fabriquee par la version precedente", avant, lignes_avant)
    src.close()
    print()

    # ── APRES : la meme table refabriquee sur une COPIE ────────────────────────
    dossier = Path(os.environ.get("TEMP") or tempfile.gettempdir())
    copie = dossier / "controle_proprietaires_barre.sqlite"
    print("   copie de la base (%.1f Go)..." % (PHASE2_DB.stat().st_size / 1e9))
    t = time.time()
    shutil.copy2(PHASE2_DB, copie)
    print("   copiee en %.1f s" % (time.time() - t))
    try:
        con = sqlite3.connect(copie, timeout=60)
        con.execute("PRAGMA busy_timeout=60000")
        con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        t = time.time()
        con.executescript(SQL_REFRESH_VUE_GENERALE)
        con.commit()
        print("   app_view_generale refabriquee en %.1f s" % (time.time() - t))
        apres = mesurer(con)
        lignes_apres = con.execute("SELECT COUNT(*) FROM app_view_generale").fetchone()[0]
        print()
        imprimer("APRES -- avec le correctif", apres, lignes_apres)

        # ── LES TROIS GARDES ──────────────────────────────────────────────────
        print()
        for champ, (_, bout, debut) in apres.items():
            if bout or debut:
                print("      ECHEC  %s porte encore %d + %d barres" % (champ, bout, debut))
                echecs += 1
        if lignes_apres != lignes_avant:
            print("      ECHEC  le nombre de lignes a change : %d -> %d"
                  % (lignes_avant, lignes_apres))
            echecs += 1
        # ③ un resume ne se vide que si TOUS les proprietaires sont muets
        vides_a_tort = con.execute(
            "SELECT COUNT(*) FROM app_view_generale v"
            " WHERE COALESCE(v.proprietaires_resume,'') = ''"
            "   AND EXISTS ("
            "     SELECT 1 FROM hektor.hektor_annonce_detail d,"
            "                   json_each(d.proprietaires_json) j"
            "      WHERE d.hektor_annonce_id = CAST(v.hektor_annonce_id AS TEXT)"
            "        AND TRIM(COALESCE(json_extract(j.value,'$.prenom'),'') || ' ' ||"
            "                 COALESCE(json_extract(j.value,'$.nom'),'')) <> '')"
        ).fetchone()[0]
        print("      resumes vides alors qu'un proprietaire a un nom : %d   %s"
              % (vides_a_tort, "OK" if vides_a_tort == 0 else "INTERDIT"))
        if vides_a_tort:
            echecs += 1
        # ④ MEME GARDE SUR LES COORDONNEES. Elle compte, parce que le correctif en
        #   vide 6 845 : il fallait prouver qu'elles ne portaient QUE des
        #   separateurs. Mesure du 07/10 sur la production : les 6 845 valaient
        #   litteralement ' | ', et les 46 654 autres portent un vrai telephone
        #   ou un vrai email -- exactement le compte d'apres.
        coords_a_tort = con.execute(
            "SELECT COUNT(*) FROM app_view_generale v"
            " WHERE COALESCE(v.proprietaires_contacts,'') = ''"
            "   AND EXISTS ("
            "     SELECT 1 FROM hektor.hektor_annonce_detail d,"
            "                   json_each(d.proprietaires_json) j"
            "      WHERE d.hektor_annonce_id = CAST(v.hektor_annonce_id AS TEXT)"
            "        AND TRIM(COALESCE(json_extract(j.value,'$.coordonnees.portable'),'') ||"
            "                 COALESCE(json_extract(j.value,'$.coordonnees.email'),'')) <> '')"
        ).fetchone()[0]
        print("      coordonnees vides alors qu'il y a un tel. ou un mail : %d   %s"
              % (coords_a_tort, "OK" if coords_a_tort == 0 else "INTERDIT"))
        if coords_a_tort:
            echecs += 1

        gagnees = (avant["proprietaires_resume"][1] + avant["proprietaires_resume"][2]
                   - apres["proprietaires_resume"][1] - apres["proprietaires_resume"][2])
        gagnees2 = (avant["proprietaires_contacts"][1] + avant["proprietaires_contacts"][2]
                    - apres["proprietaires_contacts"][1] - apres["proprietaires_contacts"][2])
        print()
        print("   FICHES NETTOYEES : %d sur les noms, %d sur les coordonnees"
              % (gagnees, gagnees2))
        if gagnees <= 0:
            print("      ECHEC  le correctif n'a rien change sur les noms --"
                  " soit il ne marche pas, soit le defaut n'existait pas")
            echecs += 1
        con.close()
    finally:
        try:
            copie.unlink()
            print("   copie supprimee")
        except OSError as exc:
            print("   ⚠ copie NON supprimee (%s) : %s" % (exc, copie))

    print()
    print(("ECHEC -- %d probleme(s)" % echecs) if echecs else "OK -- AUCUN ECHEC")
    return 1 if echecs else 0


if __name__ == "__main__":
    raise SystemExit(main())
