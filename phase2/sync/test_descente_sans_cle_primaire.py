#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA DESCENTE D'UNE TABLE SANS CLE PRIMAIRE.                        15/11/2026

    python -X utf8 phase2/sync/test_descente_sans_cle_primaire.py

CE QU'ON EPROUVE. La descente sortait en code 1 depuis le 14/11 sur deux tables de GEL
du chantier classeur : 7 344 lignes lues sur 7 346, et 12 413 sur 12 422. Une table
creee par `CREATE TABLE ... AS SELECT` n'a AUCUNE cle primaire ; le choix de la colonne
de parcours se rabat alors sur LA PREMIERE COLONNE, qui se repete, et le parcours par
valeur -- avec son `gt` STRICT -- saute ce qui reste de la valeur coupee au bord d'une
page. Le rattrapage par rang savait deja reparer exactement cela : il ne jouait pas,
parce que ces deux tables sont au-dessus de l'ancien plafond de 5 000.

LE CORRECTIF EPROUVE ICI est donc UNIQUEMENT `RELECTURE_ENTIERE_MAX : 5 000 -> 15 000`.

⛔⛔ ET L'ESSAI PORTE AUSSI LA GARDE DE CE QU'IL NE FAUT PAS FAIRE. Partir par rang
  d'emblee des qu'il n'y a pas de cle primaire paraissait plus propre -- c'est FAUX et
  dangereux : les VUES n'ont pas de cle primaire non plus. `app_v_mandat_statut` fait
  24 596 lignes sur 76 colonnes, sa premiere colonne est UNIQUE, et elle descend
  parfaitement par valeur. Le controle 3 tient cette garde : une telle table ne doit
  JAMAIS passer par le rang.

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
    """Une table dont la PREMIERE colonne se repete `lignes_par_valeur` fois.

    ⛔ LA TAILLE DE PAGE NE DOIT PAS ETRE UN MULTIPLE DE `lignes_par_valeur`, sinon
      chaque page tombe PILE sur une frontiere de valeur et le parcours par valeur ne
      saute rien -- l'essai serait vert sans rien prouver. C'est arrive a la premiere
      ecriture de ce fichier : 4 lignes par valeur et des pages de 100, soit 25 valeurs
      entieres par page, et les trois temoins inverses etaient verts A TORT.
      `lignes_par_valeur = 1` fabrique une premiere colonne UNIQUE.
    """
    lignes = []
    for i in range(nb_lignes):
        lignes.append({"app_chaine_id": i // lignes_par_valeur,
                       "cote": "entree" if i % 2 else "sortie",
                       "rang": i})
    return lignes, ["app_chaine_id", "cote", "rang"]


def descendre(lignes, colonnes, cles, page=100, plafond=None):
    """Joue copy_table sur une base en memoire. Rend ce qui est VRAIMENT pose."""
    vieux = (pfs.PAGE_SIZE, pfs.PAUSE_PAGE, pfs.RELECTURE_ENTIERE_MAX)
    pfs.PAGE_SIZE, pfs.PAUSE_PAGE = page, 0          # petites pages, pas d'attente
    if plafond is not None:
        pfs.RELECTURE_ENTIERE_MAX = plafond
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
        pfs.PAGE_SIZE, pfs.PAUSE_PAGE, pfs.RELECTURE_ENTIERE_MAX = vieux


def main():
    print("=== 1. LE CAS DU 15/11 : 12 422 lignes, aucune cle, 1re colonne repetee ===")
    # app_classeur_lien_avant_regel_20261113 : 12 422 lignes pour 4 688 valeurs.
    gel, colonnes = fabriquer(12422, 3)
    total, poses, distincts, lecteur, erreur = descendre(gel, colonnes, cles=[], page=1000)
    juger("1  aucune erreur -- la table n'est plus refusee", None, erreur)
    juger("1b les 12 422 lignes sont posees", 12422, poses)
    juger("1c et aucune n'est en double", 12422, distincts)
    juger("1d le parcours commence PAR VALEUR (chemin inchange)", True,
          lecteur.appels_valeur > 0)
    juger("1e puis LE RATTRAPAGE PAR RANG la repare", True, lecteur.appels_rang > 0)

    print()
    print("=== 2. TEMOIN INVERSE : le MEME gel avec l'ancien plafond de 5 000 ===")
    total, poses, distincts, lecteur, erreur = descendre(gel, colonnes, cles=[],
                                                         page=1000, plafond=5000)
    juger("2  le rattrapage NE JOUE PAS (au-dela du plafond)", 0, lecteur.appels_rang)
    juger("2b la copie est REFUSEE", True,
          erreur is not None and "incomplete" in (erreur or ""))
    juger("2c et rien n'a bascule -- l'ancienne copie est conservee", None, total)

    print()
    print("=== 3. ⛔ LA GARDE : une GROSSE table sans cle dont la 1re colonne est UNIQUE ===")
    print("    (c'est app_v_mandat_statut : 24 596 lignes, 76 colonnes, une VUE)")
    vue, colonnes_vue = fabriquer(24596, 1)          # 1 ligne par valeur = colonne unique
    total, poses, distincts, lecteur, erreur = descendre(vue, colonnes_vue, cles=[],
                                                         page=1000)
    juger("3  elle descend ENTIERE", 24596, poses)
    juger("3b par VALEUR, et JAMAIS par rang", (True, 0),
          (lecteur.appels_valeur > 0, lecteur.appels_rang))
    juger("3c aucune erreur", None, erreur)
    # ⭐ ET SI UNE TELLE TABLE ECHOUAIT UN JOUR : au-dela de 15 000, elle est REFUSEE
    #   bruyamment, pas relue par offset. C'est ce que le plafond protege.
    grosse_repetee, _ = fabriquer(24596, 3)
    total, poses, distincts, lecteur, erreur = descendre(grosse_repetee, colonnes_vue,
                                                          cles=[], page=1000)
    juger("3d au-dela de 15 000, une table en echec est REFUSEE, pas relue par offset",
          (0, True), (lecteur.appels_rang,
                      erreur is not None and "incomplete" in (erreur or "")))

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
    petit, colonnes_p = fabriquer(1200, 3)
    total, poses, distincts, lecteur, erreur = descendre(
        petit, colonnes_p, cles=["app_chaine_id", "cote", "rang"])
    juger("5  les 1 200 lignes sont posees", 1200, poses)
    juger("5b et le parcours est PAR RANG d'emblee, comme avant", True,
          lecteur.appels_rang > 0 and lecteur.appels_valeur == 0)

    print()
    print("=== 6. LE PLAFOND ET LA CONDITION, lus dans le fichier ===")
    src = (RACINE / "phase2" / "sync" / "pull_from_supabase.py").read_text(encoding="utf-8")
    juger("6  le plafond est a 15 000", 15000, pfs.RELECTURE_ENTIERE_MAX)
    juger("6b la condition du parcours par rang est INCHANGEE", True,
          "composite = bool(cles) and len(cles or []) > 1" in src)
    juger("6c ⛔ et le piege des VUES est ECRIT dans le fichier", True,
          "app_v_mandat_statut" in src and "VUES n'ont pas de cle primaire" in src)

    print()
    print("%d/%d verts" % (VERTS, VERTS + len(ROUGES)))
    if ROUGES:
        print("ROUGES : " + " . ".join(ROUGES))
    return 1 if ROUGES else 0


if __name__ == "__main__":
    raise SystemExit(main())
