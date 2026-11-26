#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA GARDE DE LA DESCENTE -- les regles du 26/11, chacune avec son temoin inverse.

    python -X utf8 phase2/sync/test_garde_de_la_descente.py

Audit : notice/AUDIT_GARDE_DE_LA_DESCENTE_2026-11-26.md (§ 10.6 pour la liste des regles).

CE QU'ON EPROUVE, regle par regle :
  0  la date d'une copie est celle de la copie EN PLACE (DATE_DE_LA_COPIE_EN_PLACE) :
     apres un refus, sb_pull_state garde la date de la veille -- c'est elle que lisent
     relation_ledger, relation_disparue, mandat_un_numero et la sante.

CHAQUE REGLE A SON TEMOIN INVERSE : son interrupteur eteint, le meme cas DOIT reproduire
le comportement d'avant. Un essai qui passerait aussi interrupteur eteint ne prouverait rien.

On joue EXACTEMENT ce que main() fait pour une table : copy_table puis marquer_complete,
et marquer_echec si copy_table leve. Aucun reseau, aucune base reelle : un faux lecteur qui
imite PostgREST, et une base SQLite en memoire.
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

VEILLE = "2026-11-26T06:59:12"
CE_MATIN = "2026-11-27T06:45:00"
COLONNES = ["id", "nom"]


def juger(nom, attendu, obtenu):
    global VERTS
    if attendu == obtenu:
        VERTS += 1
        print("  OK    %s" % nom)
    else:
        ROUGES.append(nom)
        print("  ROUGE %s\n        attendu %r\n        obtenu %r" % (nom, attendu, obtenu))


class Lecteur:
    """Imite PostgREST. `compte` : 'juste' (le vrai total), ou la valeur a rendre (None, 0, n)."""

    def __init__(self, lignes, compte="juste"):
        self.lignes = lignes
        self.compte = compte
        self.dernier_poids = 0

    def page_apres(self, table, cle, borne, size):
        vues = [r for r in self.lignes if borne is None or r[cle] > borne]
        vues.sort(key=lambda r: r[cle])
        return [dict(r) for r in vues[:size]]

    def page_par_rang(self, table, colonnes, rang, size):
        ordonnees = sorted(self.lignes, key=lambda r: tuple(str(r[c]) for c in colonnes))
        return [dict(r) for r in ordonnees[rang:rang + size]]

    def count(self, table):
        return len(self.lignes) if self.compte == "juste" else self.compte


def lignes(n):
    return [{"id": i, "nom": "n%d" % i} for i in range(n)]


def base(ancienne=None, etat=None):
    """Une base en memoire : la copie locale d'avant (n lignes) et sa ligne d'etat."""
    con = sqlite3.connect(":memory:")
    pfs.ensure_state_table(con)
    if ancienne is not None:
        con.execute('CREATE TABLE "t_locale" ("id", "nom")')
        con.executemany('INSERT INTO "t_locale" VALUES (?, ?)',
                        [(r["id"], r["nom"]) for r in lignes(ancienne)])
    if etat is not None:
        con.execute("INSERT INTO sb_pull_state(table_name, lignes, derniere_descente, dernier_echec,"
                    " derniere_complete) VALUES ('t_locale', ?, ?, ?, ?)", etat)
    con.commit()
    return con


def passer(con, lecteur):
    """Ce que main() fait pour une table (l. ~1220-1235). Rend le message d'echec, ou None."""
    try:
        pfs.copy_table(con, lecteur, "t_distante", "t_locale", COLONNES, "id", CE_MATIN, ["id"])
        pfs.marquer_complete(con, "t_locale", CE_MATIN)
        return None
    except Exception as exc:                                       # noqa: BLE001
        pfs.marquer_echec(con, "t_locale", str(exc))
        return str(exc)


def etat(con):
    r = con.execute("SELECT lignes, derniere_descente, dernier_echec FROM sb_pull_state"
                    " WHERE table_name='t_locale'").fetchone()
    return r if r else (None, None, None)


def locales(con):
    existe = {x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    n = con.execute('SELECT COUNT(*) FROM "t_locale"').fetchone()[0] if "t_locale" in existe else None
    return n, sorted(x for x in existe if x.endswith("__tmp"))


def relation_ledger_la_croit_du_jour(con):
    """La garde de fraicheur de relation_ledger.py (l. ~587), recopiee : « du jour » ou non."""
    d = etat(con)[1]
    return bool(d) and str(d)[:10] == CE_MATIN[:10]


def avec(nom, valeur, fonction):
    """Joue `fonction` avec l'interrupteur `nom` force a `valeur`, puis le remet."""
    avant = getattr(pfs, nom)
    setattr(pfs, nom, valeur)
    try:
        return fonction()
    finally:
        setattr(pfs, nom, avant)


def regle_0():
    print("=== REGLE 0 : la date d'une copie est celle de la copie EN PLACE ===")
    juger("0  l'interrupteur est ALLUME dans le fichier", True, pfs.DATE_DE_LA_COPIE_EN_PLACE)

    # Une copie refusee (compte 499 pour 500 lues : la relecture par rang ne le comble pas).
    def refus():
        con = base(ancienne=500, etat=(500, VEILLE, None, VEILLE))
        erreur = passer(con, Lecteur(lignes(500), compte=499))
        return con, erreur
    con, erreur = refus()
    juger("0a la copie est REFUSEE (le cas d'essai mord)", True,
          erreur is not None and "incomplete" in erreur)
    juger("0b la date reste celle de LA VEILLE", VEILLE, etat(con)[1])
    juger("0c la copie d'avant est intacte (500), aucune __tmp", (500, []), locales(con))
    juger("0d relation_ledger ne la croit PAS du jour -> il s'abstient", False,
          relation_ledger_la_croit_du_jour(con))
    juger("0e le refus reste ecrit (lignes vide, message nomme)", (None, True),
          (etat(con)[0], (etat(con)[2] or "").startswith("copie incomplete")))

    # TEMOIN INVERSE : interrupteur eteint, le piege d'avant DOIT reapparaitre.
    con, erreur = avec("DATE_DE_LA_COPIE_EN_PLACE", False, refus)
    juger("0f INVERSE eteint : la date dit « ce matin » pour une copie de la veille", CE_MATIN,
          etat(con)[1])
    juger("0g INVERSE eteint : relation_ledger serait TROMPE", True,
          relation_ledger_la_croit_du_jour(con))

    # Une copie reussie : la date avance, comme avant.
    con = base(ancienne=500, etat=(500, VEILLE, None, VEILLE))
    erreur = passer(con, Lecteur(lignes(520)))
    juger("0h une copie reussie : aucune erreur, 520 posees", (None, 520), (erreur, locales(con)[0]))
    juger("0i et sa date AVANCE a ce matin, sans message", (520, CE_MATIN, None), etat(con))

    # Une table neuve qui echoue : pas de date du tout (aucune copie n'existe).
    con = base()
    passer(con, Lecteur(lignes(500), compte=499))
    juger("0j une table neuve refusee n'a AUCUNE date", None, etat(con)[1])
    con = avec("DATE_DE_LA_COPIE_EN_PLACE", False,
               lambda: (lambda c: (passer(c, Lecteur(lignes(500), compte=499)), c)[1])(base()))
    juger("0k INVERSE eteint : elle portait la date de ce matin", CE_MATIN, etat(con)[1])
    print()


def main():
    vieux = (pfs.PAGE_SIZE, pfs.PAUSE_PAGE)
    pfs.PAGE_SIZE, pfs.PAUSE_PAGE = 100, 0
    try:
        regle_0()
    finally:
        pfs.PAGE_SIZE, pfs.PAUSE_PAGE = vieux
    print("%d/%d verts" % (VERTS, VERTS + len(ROUGES)))
    if ROUGES:
        print("ROUGES : " + " . ".join(ROUGES))
    return 1 if ROUGES else 0


if __name__ == "__main__":
    raise SystemExit(main())
