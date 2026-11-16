#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""26bis-TRANSACTIONS -- L'ESSAI SUR LES VRAIES DONNEES, SANS RIEN TOUCHER.

    python -X utf8 phase2/checks/essai_reel_sur_copie_26bis.py

⭐ POURQUOI CET ESSAI EXISTE, alors que l'epreuve hors ligne est a 44/44. Elle
  monte ses propres lignes : elle prouve que le mecanisme est juste, pas qu'il est
  juste SUR NOTRE BASE. Ici les lignes sont les vraies, lues dans phase2.sqlite --
  mais dans une base NEUVE, batie avec le VRAI DDL (contraintes comprises) et
  remplie depuis la base reelle ouverte EN LECTURE SEULE. Meme patron que
  test_r2_attente (qui recopie phase2.sqlite dans un dossier temporaire).

⛔ IL N'ECRIT RIEN DE VRAI : la base reelle est ouverte en `mode=ro` + `query_only`,
  et tout se passe dans un fichier temporaire efface a la fin.

⛔⛔ REECRIT LE 16/11/2026, ET VOICI POURQUOI -- C'EST LA LECON DE CE FICHIER.
  La premiere version decrivait des ETATS DATES : « PASSAGE 1 : l'etat d'aujourd'hui
  (ni le local ni la doublure n'ont la colonne) », « PASSAGE 2 : l'etat de la nuit
  prochaine ». Elle attendait « 1 recopiee, cles [1001424] ».

  La nuit du 15 au 16/11 est passee, la recopie a fait son travail -- et l'essai est
  devenu ROUGE pour cette raison meme : la recopie n'admet que ce qui n'est PAS DEJA
  EN LOCAL (affaire_ledger.py), et la ligne y etait desormais. Son echec etait donc
  LA PREUVE QUE LA NUIT AVAIT MARCHE. Un essai qui dit le contraire de la verite
  n'est plus un essai -- et celui qui le lirait croirait a un defaut.

  ⭐ LA FORME JUSTE NE DECRIT PAS UN ETAT, ELLE LE FABRIQUE. Cette version MESURE
    d'abord l'etat de depart, puis RETIRE de SA COPIE les lignes candidates pour
    recreer « l'instant d'avant la recopie ». Elle redevient donc vraie n'importe
    quel jour, et elle servira telle quelle pour les 241 du classeur.
  ⚠ ET SI LA DOUBLURE N'A AUCUN CANDIDAT (par exemple apres le retrait du cobaye),
    elle le DIT et sort en 0 : on ne prouve rien sur des lignes qui n'existent pas,
    et on ne maquille pas une absence de sujet en succes. Le mecanisme, lui, reste
    porte par phase2/sync/test_recopie_app_seule.py (44/44).

LE CRITERE EST ECRIT AVANT D'AVOIR LE RESULTAT -- sinon on juge apres coup :

    PASSAGE 0  on MESURE l'etat de depart : combien de candidates dans la doublure
               (plage app, sans numero Hektor), et combien sont deja en local
    PASSAGE 1  on RETIRE les candidates de la copie locale -> la recopie DOIT les
               reposer, toutes, avec leurs colonnes, et le temoin doit boucler
    PASSAGE 2  on relance sans rien retirer -> 0 recopiee (le geste ne se repete pas)
    PASSAGE 3  la meme chose SANS la colonne `transaction_origine` -> le code DIT
               qu'elle manque au lieu de tomber
    ET DANS TOUS : les lignes de la plage AVEC numero et celles du hors-plage ne
    bougent PAS d'une ligne.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

import affaire_ledger as al                                          # noqa: E402

REELLE = RACINE / "phase2" / "phase2.sqlite"
TABLE = "app_affaire_ledger"
DOUBLURE = TABLE + "__sb"
PLAGE = al.PLAGE_RESERVEE_APP

# « de la plage app ET sans numero Hektor » -- mot pour mot le perimetre de la recopie.
CANDIDATE = (f"CAST(app_affaire_id AS INTEGER) >= {PLAGE}"
             f" AND (hektor_affaire_id IS NULL"
             f"      OR TRIM(CAST(hektor_affaire_id AS TEXT)) = '')")

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


def fabriquer(dossier: Path, avec_colonne: bool, retirer_les_candidates: bool) -> Path:
    """Une base NEUVE, vrai DDL, remplie depuis la base reelle en lecture seule.

    `retirer_les_candidates` recree « l'instant d'avant la recopie » : il enleve de la
    copie LOCALE les lignes que la doublure porte et qui entrent dans le perimetre.
    ⛔ Il ne touche QUE la copie temporaire -- la base reelle est en `mode=ro`.
    """
    nom = ("avec_colonne" if avec_colonne else "sans_colonne")
    nom += "_vide" if retirer_les_candidates else "_tel_quel"
    copie = dossier / (nom + ".sqlite")
    src = sqlite3.connect(f"file:{REELLE.as_posix()}?mode=ro", uri=True)
    src.execute("pragma query_only = 1")
    ddl_table = src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                            (TABLE,)).fetchone()[0]
    index = [r[0] for r in src.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL",
        (TABLE,))]
    cols_table = [r[1] for r in src.execute(f"PRAGMA table_info({TABLE})")]
    cols_doublure = [r[1] for r in src.execute(f"PRAGMA table_info({DOUBLURE})")]
    src.close()

    # uri=True est OBLIGATOIRE ici : sans lui, ATTACH refuse l'adresse « file:...?mode=ro »
    # et on perdrait la garantie de lecture seule sur la base reelle.
    con = sqlite3.connect(copie, uri=True)
    con.execute(ddl_table)
    for sql in index:
        con.execute(sql)
    # la doublure, comme pull_from_supabase la recree : sans contraintes
    con.execute('CREATE TABLE "%s" (%s)' % (DOUBLURE, ", ".join('"%s"' % c
                                                                for c in cols_doublure)))
    if not avec_colonne:
        # ⚠ LA COLONNE EXISTE MAINTENANT DES DEUX COTES dans la vraie base (posee le
        #   15/11, descendue le 16). Pour rejouer l'etat d'avant, on la RETIRE de la
        #   copie -- l'inverse de ce que faisait la premiere version, qui partait d'une
        #   base qui ne l'avait pas encore.
        cols_table = [c for c in cols_table if c != "transaction_origine"]
        cols_doublure = [c for c in cols_doublure if c != "transaction_origine"]
        # on refait les deux tables sans la colonne
        con.execute(f"DROP TABLE {TABLE}")
        con.execute(f'DROP TABLE "{DOUBLURE}"')
        ddl_sans = _ddl_sans_colonne(ddl_table, "transaction_origine")
        con.execute(ddl_sans)
        for sql in index:
            con.execute(sql)
        con.execute('CREATE TABLE "%s" (%s)' % (DOUBLURE, ", ".join('"%s"' % c
                                                                    for c in cols_doublure)))
    con.commit()
    con.execute("ATTACH DATABASE ? AS reel", (f"file:{REELLE.as_posix()}?mode=ro",))
    ou = (" WHERE NOT (%s)" % CANDIDATE) if retirer_les_candidates else ""
    con.execute(f"INSERT INTO {TABLE} ({', '.join(cols_table)}) "
                f"SELECT {', '.join(cols_table)} FROM reel.{TABLE}{ou}")
    con.execute(f'INSERT INTO "{DOUBLURE}" ({", ".join(cols_doublure)}) '
                f'SELECT {", ".join(cols_doublure)} FROM reel."{DOUBLURE}"')
    con.commit()
    con.execute("DETACH DATABASE reel")
    con.close()
    return copie


def _ddl_sans_colonne(ddl: str, colonne: str) -> str:
    """Retire une colonne d'un CREATE TABLE, pour rejouer l'etat d'avant son ajout.

    ⚠ La colonne a ete ajoutee par un ALTER TABLE, elle est donc la DERNIERE et sans
      contrainte. On coupe sur sa declaration exacte, jamais sur un simple nom --
      « transaction_origine » pourrait apparaitre ailleurs dans le DDL un jour.
    """
    for forme in (",\n    %s TEXT" % colonne, ", %s TEXT" % colonne,
                  ',\n    "%s" TEXT' % colonne, ', "%s" TEXT' % colonne):
        if forme in ddl:
            return ddl.replace(forme, "")
    raise SystemExit("⛔ je ne sais pas retirer %r du DDL -- l'essai s'arrete plutot "
                     "que de deviner.\n%s" % (colonne, ddl))


def voisines(con):
    avec = con.execute(
        f"SELECT COUNT(*) FROM {TABLE} WHERE CAST(app_affaire_id AS INTEGER) >= {PLAGE}"
        f" AND hektor_affaire_id IS NOT NULL"
        f" AND TRIM(CAST(hektor_affaire_id AS TEXT)) <> ''").fetchone()[0]
    hors = con.execute(
        f"SELECT COUNT(*) FROM {TABLE} "
        f"WHERE CAST(app_affaire_id AS INTEGER) < {PLAGE}").fetchone()[0]
    return avec, hors


def etat_de_depart():
    """Ce que porte la VRAIE base, mesure avant de juger quoi que ce soit."""
    con = sqlite3.connect(f"file:{REELLE.as_posix()}?mode=ro", uri=True)
    con.execute("pragma query_only = 1")
    dans_doublure = [r[0] for r in con.execute(
        f'SELECT app_affaire_id FROM "{DOUBLURE}" WHERE {CANDIDATE} ORDER BY 1')]
    deja_locales = [r[0] for r in con.execute(
        f"SELECT app_affaire_id FROM {TABLE} WHERE {CANDIDATE} ORDER BY 1")]
    con.close()
    return dans_doublure, deja_locales


def main() -> int:
    if not REELLE.exists():
        print(f"pas de base locale : {REELLE}")
        return 2

    print("=== PASSAGE 0 : L'ETAT DE DEPART, MESURE (on ne le suppose pas) ===")
    candidates, deja_locales = etat_de_depart()
    print(f"  dans la doublure (plage app, sans numero Hektor) : {len(candidates)}")
    if candidates:
        print("    " + ", ".join(str(c) for c in candidates[:20])
              + (" ..." if len(candidates) > 20 else ""))
    print(f"  deja dans le registre local                      : {len(deja_locales)}")

    if not candidates:
        # ⛔ CE N'EST PAS UN ECHEC, ET CE N'EST PAS UN SUCCES DEGUISE : il n'y a pas
        #   de sujet. On le dit, et on renvoie a l'epreuve qui porte le mecanisme.
        print()
        print("RIEN A EPROUVER SUR LES VRAIES LIGNES : la doublure ne porte aucune")
        print("ligne de la plage app sans numero Hektor aujourd'hui.")
        print("  -> c'est l'etat attendu une fois le cobaye retire, et ce sera de")
        print("     nouveau faux le jour ou les 241 du classeur seront posees.")
        print("  -> le MECANISME reste eprouve par phase2/sync/test_recopie_app_seule.py")
        return 0

    # ignore_cleanup_errors : Windows garde parfois la main sur un fichier SQLite
    # une seconde de trop -- un brouillon qui survit ne doit pas faire echouer un
    # essai qui, lui, a reussi.
    with tempfile.TemporaryDirectory(prefix="essai26bis_",
                                     ignore_cleanup_errors=True) as brouillon:
        dossier = Path(brouillon)
        attendues = sorted(candidates)

        print()
        print("=== PASSAGE 1 : L'INSTANT D'AVANT LA RECOPIE, REFABRIQUE ===")
        print(f"    (on retire les {len(attendues)} candidate(s) de la copie locale)")
        con = sqlite3.connect(fabriquer(dossier, avec_colonne=True,
                                        retirer_les_candidates=True))
        avant = voisines(con)
        print(f"  les voisines avant : {avant[0]} de la plage AVEC numero, "
              f"{avant[1]} hors plage")
        juger("1  elles sont bien ABSENTES du local au depart", 0, con.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE {CANDIDATE}").fetchone()[0])
        r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
        juger("1b toutes les candidates sont recopiees", len(attendues), r["recopiees"])
        juger("1c et ce sont EXACTEMENT celles-la", attendues, sorted(r.get("cles") or []))
        juger("1d aucune ecartee", None, r.get("ecartees_colonne_obligatoire_vide"))
        juger("1e le temoin boucle (0 -> le compte des candidates)",
              (0, len(attendues)),
              (r["plage_sans_numero_avant"], r["plage_sans_numero_apres"]))
        juger("1f la colonne `transaction_origine` entre dans la recopie", True,
              r.get("colonnes_recopiees", 0) > 49)
        juger("1g les colonnes obligatoires sont les trois attendues",
              ["app_affaire_id", "kind", "present_in_hektor"],
              sorted(r.get("colonnes_obligatoires", [])))
        juger("1h ⭐ LES VOISINES N'ONT PAS BOUGE", avant, voisines(con))
        juger("1i elles sont VRAIMENT dans le registre", len(attendues), con.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE {CANDIDATE}").fetchone()[0])
        # ⭐ et leur numero n'a pas ete invente : c'est celui du serveur
        juger("1j aucun doublon n'a ete cree", len(attendues), con.execute(
            f"SELECT COUNT(DISTINCT app_affaire_id) FROM {TABLE} "
            f"WHERE {CANDIDATE}").fetchone()[0])

        print()
        print("=== PASSAGE 2 : ON RELANCE, RIEN N'A CHANGE ===")
        r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
        juger("2  le geste ne se repete pas", 0, r["recopiees"])
        juger("2b et il n'y a plus de candidate", 0, r["candidates"])
        juger("2c toujours aucun doublon", len(attendues), con.execute(
            f"SELECT COUNT(DISTINCT app_affaire_id) FROM {TABLE} "
            f"WHERE {CANDIDATE}").fetchone()[0])
        juger("2d LES VOISINES N'ONT TOUJOURS PAS BOUGE", avant, voisines(con))
        con.close()

        print()
        print("=== PASSAGE 3 : SANS LA COLONNE -- le code le DIT, il ne tombe pas ===")
        con = sqlite3.connect(fabriquer(dossier, avec_colonne=False,
                                        retirer_les_candidates=True))
        avant3 = voisines(con)
        juger("3  la copie n'a VRAIMENT pas la colonne", False,
              "transaction_origine" in {c[1] for c in
                                        con.execute(f"PRAGMA table_info({TABLE})")})
        r = al.recopier_ce_que_hektor_ne_rendra_jamais(con)
        juger("3b la recopie marche quand meme", len(attendues), r["recopiees"])
        juger("3c et elle recopie MOINS de colonnes (l'intersection joue)", True,
              0 < r.get("colonnes_recopiees", 0) < 50)
        juger("3d LES VOISINES N'ONT PAS BOUGE", avant3, voisines(con))
        con.close()

    print()
    print("%d/%d verts" % (VERTS, VERTS + len(ROUGES)))
    if ROUGES:
        print("ROUGES : " + " . ".join(ROUGES))
    return 1 if ROUGES else 0


if __name__ == "__main__":
    raise SystemExit(main())
