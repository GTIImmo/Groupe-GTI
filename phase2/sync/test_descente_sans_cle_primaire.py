#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA DESCENTE D'UNE TABLE SANS CLE PRIMAIRE.                        15/11/2026

    python -X utf8 phase2/sync/test_descente_sans_cle_primaire.py

CE QU'ON EPROUVE. La descente du 15/11 est sortie en code 1 sur deux tables de GEL
du chantier classeur : 7 344 lignes lues sur 7 346, et 12 413 sur 12 422. Une table
creee par recopie (CREATE TABLE ... AS SELECT) n'a PAS de cle primaire ; le choix de
la colonne de parcours se rabat alors sur LA PREMIERE COLONNE, qui se repete, et le
parcours par valeur (« les lignes apres la derniere lue », avec un `gt` STRICT) saute
ce qui reste de la valeur coupee au bord d'une page.

⚠ ET LE RATTRAPAGE EXISTANT NE POUVAIT PAS LES SAUVER : il ne joue que sous
  RELECTURE_ENTIERE_MAX = 5 000 lignes. 7 346 et 12 422 sont au-dessus.

⭐ LE TEMOIN INVERSE EST LE COEUR DE CET ESSAI : la MEME table, lue comme AVANT le
  correctif (une seule cle qui se repete), doit PERDRE des lignes et faire REFUSER la
  copie. Sans lui, un essai vert ne prouverait pas que le correctif sert a quelque
  chose.

Aucun reseau, aucune base reelle : un faux lecteur qui imite PostgREST et une base
SQLite en memoire.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

import pull_from_supabase as pfs                                   # noqa: E402

VERTS = 0
ROUGES: list[str] = []


def juger(nom, attendu, obtenu):
    global VERTS
    if attendu == obtenu:
        VERTS += 1
        print("  OK    %s" % nom)
    else:
        ROUGES.append(nom)
        print("  ROUGE %s\n        attendu %r\n        obtenu %r" % (nom, attendu, obtenu))


class FauxLecteur:
    """Imite PostgREST sur une table en memoire. Compte ses appels."""

    def __init__(self, lignes, colonnes):
        self.lignes = lignes
        self.colonnes = colonnes
        self.dernier_poids = 0
        self.appels_valeur = 0
        self.appels_rang = 0

    def page_apres(self, table, cle, borne, size):
        self.appels_valeur += 1
        # ⚠ `gt` STRICT, exactement comme le vrai : c'est LUI qui saute des lignes
        #   quand la colonne de parcours se repete.
        vues = [r for r in self.lignes if borne is None or r[cle] > borne]
        vues.sort(key=lambda r: r[cle])
        return [dict(r) for r in vues[:size]]

    def page_par_rang(self, table, colonnes, rang, size):
        self.appels_rang += 1
        ordonnees = sorted(self.lignes,
                           key=lambda r: tuple(str(r[c]) for c in colonnes))
        return [dict(r) for r in ordonnees[rang:rang + size]]

    def count(self, table):
        return len(self.lignes)


def fabriquer(nb_lignes, lignes_par_valeur):
    """Une table dont la PREMIERE colonne se repete `lignes_par_valeur` fois."""
    lignes = []
    for i in range(nb_lignes):
        lignes.append({"app_chaine_id": i // lignes_par_valeur,
                       "cote": "entree" if i % 2 else "sortie",
                       "rang": i})
    return lignes, ["app_chaine_id", "cote", "rang"]


def descendre(lignes, colonnes, cles, page=100):
    """Joue copy_table sur une base en memoire. Rend ce qui est VRAIMENT pose."""
    ancienne_page, ancienne_pause = pfs.PAGE_SIZE, pfs.PAUSE_PAGE
    pfs.PAGE_SIZE, pfs.PAUSE_PAGE = page, 0          # petites pages, pas d'attente
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE sb_pull_state (table_name TEXT PRIMARY KEY, "
                    "lignes INTEGER, derniere_descente TEXT, dernier_echec TEXT)")
        lecteur = FauxLecteur(lignes, colonnes)
        cle = cles[0] if cles else colonnes[0]
        try:
            total, _ = pfs.copy_table(con, lecteur, "t_distante", "t_locale",
                                      colonnes, cle, "2026-11-15", cles)
            erreur = None
        except RuntimeError as exc:
            total, erreur = None, str(exc)
        existe = con.execute("SELECT COUNT(*) FROM sqlite_master "
                             "WHERE type='table' AND name='t_locale'").fetchone()[0]
        poses = con.execute('SELECT COUNT(*) FROM "t_locale"').fetchone()[0] if existe else None
        distincts = (con.execute('SELECT COUNT(DISTINCT rang) FROM "t_locale"').fetchone()[0]
                     if existe and "rang" in colonnes else None)
        con.close()
        return total, poses, distincts, lecteur, erreur
    finally:
        pfs.PAGE_SIZE, pfs.PAUSE_PAGE = ancienne_page, ancienne_pause


def main():
    print("=== 1. AUCUNE CLE PRIMAIRE, 1re colonne repetee -- LE CAS DU 15/11 ===")
    # ⛔ LA TAILLE DE PAGE NE DOIT PAS ETRE UN MULTIPLE DU NOMBRE DE LIGNES PAR
    #   VALEUR, sinon chaque page tombe PILE sur une frontiere de valeur et le
    #   parcours par valeur ne saute rien -- l'essai serait vert sans rien prouver.
    #   Premiere ecriture de cet essai : 4 lignes par valeur et des pages de 100,
    #   donc 25 valeurs entieres par page. Les trois temoins inverses etaient verts
    #   a tort. 3 lignes par valeur pour 100 par page coupe au milieu de la 34e.
    lignes, colonnes = fabriquer(1200, 3)
    total, poses, distincts, lecteur, erreur = descendre(lignes, colonnes, cles=[])
    juger("1  aucune erreur", None, erreur)
    juger("1b les 1 200 lignes sont posees", 1200, poses)
    juger("1c et aucune n'est en double", 1200, distincts)
    juger("1d le parcours est PAR RANG", True, lecteur.appels_rang > 0)
    juger("1e et jamais par valeur", 0, lecteur.appels_valeur)

    print()
    print("=== 2. TEMOIN INVERSE : la MEME table lue COMME AVANT le correctif ===")
    # Avant, sans cle primaire, le code prenait colonnes[0] et passait par valeur.
    # Une seule cle declaree reproduit exactement ce chemin.
    total, poses, distincts, lecteur, erreur = descendre(lignes, colonnes,
                                                         cles=["app_chaine_id"])
    # ⭐ MON CRITERE ETAIT FAUX ICI, ET C'EST LE CODE QUI AVAIT RAISON. J'attendais
    #   une copie REFUSEE. Sous RELECTURE_ENTIERE_MAX (5 000), le rattrapage par rang
    #   joue et SAUVE la table : le journal dit « 1178/1200 -- relecture par rang ».
    #   Donc sous le plafond on ne perdait rien -- on payait une SECONDE LECTURE
    #   COMPLETE de la table, chaque nuit, en silence. C'est ca que le correctif
    #   economise, et c'est au-dela du plafond (controle 3) qu'il evite une vraie perte.
    juger("2  le parcours est PAR VALEUR", True, lecteur.appels_valeur > 0)
    juger("2b IL MANQUAIT DES LIGNES -> le rattrapage a du relire la table", True,
          lecteur.appels_rang > 0)
    juger("2c sauvee, mais au prix d'une seconde lecture entiere", (1200, None),
          (poses, erreur))

    print()
    print("=== 3. AU-DELA DU PLAFOND DE RELECTURE (5 000) : le vrai echec du 15/11 ===")
    # 3 lignes par valeur, pages de 1 000 : la frontiere coupe une valeur en deux
    # (voir la note du controle 1). app_affaire_repartition_avant_classeur_20261113
    # fait 7 346 lignes pour 3 673 valeurs, et elle perdait 2 lignes en vrai.
    grandes, colonnes3 = fabriquer(7346, 3)
    total, poses, distincts, lecteur, erreur = descendre(grandes, colonnes3, cles=[],
                                                         page=1000)
    juger("3  7 346 lignes passent SANS CLE PRIMAIRE", 7346, poses)
    juger("3b aucune en double", 7346, distincts)
    juger("3c une SEULE passe, pas de relecture de rattrapage", True,
          lecteur.appels_rang <= 9)                # 7 pages pleines + la derniere
    total, poses, distincts, lecteur, erreur = descendre(grandes, colonnes3,
                                                         cles=["app_chaine_id"],
                                                         page=1000)
    juger("3d TEMOIN INVERSE : avant, elle etait REFUSEE", True,
          erreur is not None and "incomplete" in (erreur or ""))
    juger("3e et le rattrapage par rang NE POUVAIT PAS la sauver (> 5 000)",
          0, lecteur.appels_rang)

    print()
    print("=== 4. ON NE CASSE RIEN : une vraie cle primaire SIMPLE ET UNIQUE ===")
    uniques = [{"id": i, "nom": "n%d" % i} for i in range(450)]
    total, poses, distincts, lecteur, erreur = descendre(uniques, ["id", "nom"],
                                                         cles=["id"])
    juger("4  les 450 lignes sont posees", 450, poses)
    juger("4b et le parcours reste PAR VALEUR (le chemin rapide)", True,
          lecteur.appels_valeur > 0 and lecteur.appels_rang == 0)

    print()
    print("=== 5. ON NE CASSE RIEN : une cle COMPOSITE (correctif du 15/09) ===")
    total, poses, distincts, lecteur, erreur = descendre(
        lignes, colonnes, cles=["app_chaine_id", "cote", "rang"])
    juger("5  les 1 200 lignes sont posees", 1200, poses)
    juger("5b et le parcours est PAR RANG, comme avant", True,
          lecteur.appels_rang > 0 and lecteur.appels_valeur == 0)

    print()
    print("=== 6. LA CONDITION ELLE-MEME, lue dans le fichier ===")
    src = (RACINE / "phase2" / "sync" / "pull_from_supabase.py").read_text(encoding="utf-8")
    juger("6  la condition couvre l'absence de cle", True,
          "composite = (not cles) or len(cles) > 1" in src)
    juger("6b l'ordre total se prend sur TOUTES les colonnes", True,
          "ordre_cle = list(cles) if cles else list(columns)" in src)
    juger("6c et le journal le DIT, au lieu de mentir « cle composite »", True,
          "AUCUNE cle primaire" in src)

    print()
    print("%d/%d verts" % (VERTS, VERTS + len(ROUGES)))
    if ROUGES:
        print("ROUGES : " + " . ".join(ROUGES))
    return 1 if ROUGES else 0


if __name__ == "__main__":
    raise SystemExit(main())
