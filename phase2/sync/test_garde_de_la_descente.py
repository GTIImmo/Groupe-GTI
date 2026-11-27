#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA GARDE DE LA DESCENTE -- les regles du 26/11, chacune avec son temoin inverse.

    python -X utf8 phase2/sync/test_garde_de_la_descente.py

Audit : notice/AUDIT_GARDE_DE_LA_DESCENTE_2026-11-26.md (§ 10.6 pour la liste des regles).

CE QU'ON EPROUVE, regle par regle :
  0  la date d'une copie est celle de la copie EN PLACE (DATE_DE_LA_COPIE_EN_PLACE) :
     apres un refus, sb_pull_state garde la date de la veille -- c'est elle que lisent
     relation_ledger, relation_disparue, mandat_un_numero et la sante.
  1  pas de compte, pas de bascule (EXIGER_LE_COMPTE) : un compte qui ne repond pas
     refuse la copie neuve. Le cas qui compte : une lecture COUPEE (300 sur 500) avec un
     compte absent passait en silence.
  2  un message ne promet pas une copie qui n'existe pas (UN_MESSAGE_DIT_VRAI).
  3  un objet suivi que le serveur n'expose plus se declare (objets_disparus) ; rien n'est
     supprime. L'interrupteur DECLARER_LES_DISPARUS, lui, vit dans main() : il s'eprouve
     par un --dry-run (voir la note d'audit, § 11).
  4  une chute ne se croit pas sans geste humain (REFUSER_LES_CHUTES) : moins de la moitie
     de la copie en place, des 100 lignes pour tout objet, des 2 lignes pour une table a cle
     qui n'est pas une file d'attente ; --accepter-chute la laisse passer.

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


def passer(con, lecteur, distant="t_distante", cles=("id",), accepter=False):
    """Ce que main() fait pour une table (sa boucle de copie). Rend le message d'echec, ou None.
    `cles` vide = une vue ou une table sans cle primaire ; `accepter` = --accepter-chute."""
    try:
        pfs.copy_table(con, lecteur, distant, "t_locale", COLONNES, "id", CE_MATIN, list(cles),
                       accepter_chute=accepter)
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


class LecteurCoupe(Lecteur):
    """Un serveur qui coupe la lecture : au-dela de `coupe`, les pages reviennent VIDES --
    exactement le signal d'une fin de table. C'est le cas que seul le compte peut juger."""

    def __init__(self, lignes, compte, coupe):
        super().__init__(lignes, compte)
        self.coupe = coupe

    def page_apres(self, table, cle, borne, size):
        return [r for r in super().page_apres(table, cle, borne, size) if r[cle] < self.coupe]


def regle_1():
    print("=== REGLE 1 : pas de compte, pas de bascule ===")
    juger("1  l'interrupteur est ALLUME dans le fichier", True, pfs.EXIGER_LE_COMPTE)

    # Le compte ne repond pas, la lecture est complete : on refuse quand meme (on ne sait pas).
    con = base(ancienne=500, etat=(500, VEILLE, None, VEILLE))
    erreur = passer(con, Lecteur(lignes(500), compte=None))
    juger("1a compte None : la bascule est REFUSEE, et le refus est nomme", True,
          erreur is not None and erreur.startswith("comptage impossible"))
    juger("1b la copie d'avant est intacte (500), aucune __tmp", (500, []), locales(con))
    juger("1c et sa date reste celle de la veille (regle 0)", VEILLE, etat(con)[1])

    # LE CAS QUI COMPTE : le serveur coupe a 300 lignes sur 500, et le compte ne repond pas.
    def coupee():
        con = base(ancienne=500, etat=(500, VEILLE, None, VEILLE))
        erreur = passer(con, LecteurCoupe(lignes(500), compte=None, coupe=300))
        return con, erreur
    con, erreur = coupee()
    juger("1d lecture coupee + compte None : REFUSEE, les 500 restent", (True, 500),
          (erreur is not None, locales(con)[0]))
    # TEMOIN INVERSE : interrupteur eteint, la copie amputee passe EN SILENCE.
    con, erreur = avec("EXIGER_LE_COMPTE", False, coupee)
    juger("1e INVERSE eteint : aucune erreur, et la copie tombe a 300 sans un mot", (None, 300),
          (erreur, locales(con)[0]))
    juger("1f INVERSE eteint : et l'etat la dit complete, du jour", (300, CE_MATIN, None), etat(con))

    # Le compte repond juste : rien ne change.
    con = base(ancienne=500, etat=(500, VEILLE, None, VEILLE))
    erreur = passer(con, Lecteur(lignes(510)))
    juger("1g compte juste : la copie passe (510), sans message", (None, 510), (erreur, locales(con)[0]))

    # La lecture coupee AVEC un compte : refusee comme avant (le compte la juge).
    con = base(ancienne=500, etat=(500, VEILLE, None, VEILLE))
    erreur = passer(con, LecteurCoupe(lignes(500), compte=500, coupe=300))
    juger("1h lecture coupee, compte present : la relecture par rang la repare (500)", (None, 500),
          (erreur, locales(con)[0]))

    # LIMITE DE LA REGLE 1 SEULE, gardee comme preuve : sans la regle 4, 0 = 0 passe.
    def vide():
        con = base(ancienne=500, etat=(500, VEILLE, None, VEILLE))
        return passer(con, Lecteur([], compte=0)), con
    erreur, con = avec("REFUSER_LES_CHUTES", False, vide)
    juger("1i regle 1 SEULE (regle 4 eteinte) : une source VIDE remplace 500 lignes par 0",
          (None, 0), (erreur, locales(con)[0]))
    print()


def regle_2():
    print("=== REGLE 2 : un message ne promet pas une copie qui n'existe pas ===")
    juger("2  l'interrupteur est ALLUME dans le fichier", True, pfs.UN_MESSAGE_DIT_VRAI)
    garde = " -- l'ancienne copie est conservee"

    erreur = passer(base(), Lecteur(lignes(500), compte=499))
    juger("2a sans copie locale : le refus le DIT, et ne promet rien", (True, True, False),
          ("incomplete" in erreur, "AUCUNE copie locale" in erreur, garde in erreur))
    erreur = passer(base(ancienne=500, etat=(500, VEILLE, None, VEILLE)), Lecteur(lignes(500), compte=499))
    juger("2b avec une copie locale : « l'ancienne copie est conservee », comme avant", True,
          erreur.endswith(garde))
    erreur = passer(base(), Lecteur(lignes(500), compte=None))
    juger("2c le refus de la regle 1 dit vrai lui aussi", True,
          erreur.startswith("comptage impossible") and "AUCUNE copie locale" in erreur)

    # TEMOIN INVERSE : eteint, le mensonge d'avant revient, au mot pres.
    erreur = avec("UN_MESSAGE_DIT_VRAI", False,
                  lambda: passer(base(), Lecteur(lignes(500), compte=499)))
    juger("2d INVERSE eteint : le texte d'avant, A L'OCTET PRES (il promettait une copie absente)",
          "copie incomplete : 500 lignes lues, 499 attendues cote Supabase -- l'ancienne copie est conservee",
          erreur)
    print()


def regle_3():
    print("=== REGLE 3 : un objet suivi qui disparait du serveur se declare ===")
    juger("3  l'interrupteur est ALLUME dans le fichier", True, pfs.DECLARER_LES_DISPARUS)
    con = sqlite3.connect(":memory:")
    pfs.ensure_state_table(con)
    suivis = {"present": 3, "present_doublure__sb": 2, "parti": 2, "parti_doublure__sb": 1,
              "parti_sans_copie": None}
    for nom, n in suivis.items():
        con.execute("INSERT INTO sb_pull_state(table_name, lignes) VALUES (?, ?)", (nom, n))
        if n is not None:
            con.execute('CREATE TABLE "%s" (x)' % nom)
            con.executemany('INSERT INTO "%s" VALUES (?)' % nom, [(i,) for i in range(n)])
    con.commit()
    schema = {"present": None, "present_doublure": None, "autre_table_du_serveur": None}
    avant = (sorted(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")),
             con.execute("SELECT count(*) FROM sb_pull_state").fetchone()[0])
    juger("3a les trois disparus sont nommes, avec ce qui reste en local",
          [("parti", 2), ("parti_doublure__sb", 1), ("parti_sans_copie", None)],
          pfs.objets_disparus(con, schema))
    juger("3b une doublure __sb dont l'original existe n'est PAS prise pour disparue", True,
          "present_doublure__sb" not in [n for n, _ in pfs.objets_disparus(con, schema)])
    apres = (sorted(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")),
             con.execute("SELECT count(*) FROM sb_pull_state").fetchone()[0])
    juger("3c et RIEN n'est supprime (tables et lignes d'etat inchangees)", avant, apres)
    juger("3d le serveur sans aucun suivi disparu : liste vide", [],
          pfs.objets_disparus(con, {n.removesuffix("__sb"): None for n in suivis}))
    print()


def regle_4():
    print("=== REGLE 4 : une chute ne se croit pas sans geste humain ===")
    juger("4  l'interrupteur est ALLUME, seuils 50 % / 100 lignes / 2 lignes", (True, 0.5, 100, 2),
          (pfs.REFUSER_LES_CHUTES, pfs.CHUTE_FRACTION, pfs.CHUTE_SEUIL_GENERAL,
           pfs.CHUTE_SEUIL_TABLE_A_CLE))

    def cas(ancienne, neuve, **k):
        con = base(ancienne=ancienne, etat=(ancienne, VEILLE, None, VEILLE))
        return passer(con, Lecteur(lignes(neuve)), **k), con

    # (a) LA FAILLE B : une source videe en amont.
    erreur, con = cas(500, 0)
    juger("4a source VIDE (500 -> 0) : REFUSEE, et le refus dit comment l'accepter", True,
          erreur is not None and erreur.startswith("chute refusee")
          and "--accepter-chute t_distante" in erreur)
    juger("4b les 500 restent, aucune __tmp, la date reste celle de la veille", (500, [], VEILLE),
          locales(con) + (etat(con)[1],))
    juger("4c 500 -> 240 (48 %) : REFUSEE", True, (cas(500, 240)[0] or "").startswith("chute refusee"))
    juger("4d 500 -> 300 (60 %) : passe", None, cas(500, 300)[0])
    # (b) les petites tables a cle : les saisies de l'app.
    juger("4e table a cle 48 -> 20 : REFUSEE (seuil de 2 lignes)", True,
          (cas(48, 20)[0] or "").startswith("chute refusee"))
    juger("4f table a cle 48 -> 30 : passe", None, cas(48, 30)[0])
    juger("4g table a cle 1 -> 0 : passe (sous le seuil de 2)", None, cas(1, 0)[0])
    # Les files d'attente, ecartees de (b) mais pas de (a).
    juger("4h file d'attente 3 -> 1 (le cas du 20/11) : passe", None,
          cas(3, 1, distant="app_relation_provisional")[0])
    juger("4i file d'attente 300 -> 0 : REFUSEE quand meme (seuil de 100)", True,
          (cas(300, 0, distant="app_search_pending")[0] or "").startswith("chute refusee"))
    juger("4j app_pending_resolution n'est PAS une file : 40 -> 0 REFUSEE", True,
          (cas(40, 0, distant="app_pending_resolution")[0] or "").startswith("chute refusee"))
    # Une vue (sans cle) : seulement le seuil general.
    juger("4k vue 26 -> 0 (le cas du 26/11, orphelines) : passe", None, cas(26, 0, cles=())[0])
    juger("4l vue 25 175 -> 0 : REFUSEE (seuil de 100)", True,
          (cas(25175, 0, cles=())[0] or "").startswith("chute refusee"))
    # Une table neuve n'a pas de temoin : elle passe.
    juger("4m table neuve, 0 ligne : passe (rien a comparer)", None,
          passer(base(), Lecteur([], compte=0)))
    # LE GESTE HUMAIN.
    erreur, con = cas(500, 0, accepter=True)
    juger("4n --accepter-chute : la chute voulue passe (500 -> 0)", (None, 0), (erreur, locales(con)[0]))
    # TEMOIN INVERSE : interrupteur eteint, la faille B revient.
    erreur, con = avec("REFUSER_LES_CHUTES", False, lambda: cas(500, 0))
    juger("4o INVERSE eteint : 500 lignes remplacees par 0, sans un mot", (None, 0),
          (erreur, locales(con)[0]))
    print()


def main():
    vieux = (pfs.PAGE_SIZE, pfs.PAUSE_PAGE)
    pfs.PAGE_SIZE, pfs.PAUSE_PAGE = 100, 0
    try:
        regle_0()
        regle_1()
        regle_2()
        regle_3()
        regle_4()
    finally:
        pfs.PAGE_SIZE, pfs.PAUSE_PAGE = vieux
    print("%d/%d verts" % (VERTS, VERTS + len(ROUGES)))
    if ROUGES:
        print("ROUGES : " + " . ".join(ROUGES))
    return 1 if ROUGES else 0


if __name__ == "__main__":
    raise SystemExit(main())
