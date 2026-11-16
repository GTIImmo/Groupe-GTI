#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA GARDE DE L'ORIGINE SUR LES DEUX LECTEURS SANS GARDE.          16/11/2026

    python -X utf8 phase2/checks/test_garde_origine_classeur.py

CE QU'ON EPROUVE. Une transaction reprise du classeur n'est JAMAIS allee chez Hektor :
elle ne peut donc ni « disparaitre de Hektor cette nuit », ni etre affichee « plus dans
Hektor depuis ... ». L'audit du 16/11 a balaye TOUTE la famille des lecteurs de
`present_in_hektor = false` et en a trouve SIX. Quatre etaient deja proteges (le filet
du worker par `transaction_origine=is.null` ; l'app et les trois gestes de masse parce
qu'ils exigent un numero Hektor EN PLUS). DEUX ne l'etaient pas, et ce sont eux :

  A  monitoring/check_gti_health.py -- la sentinelle `data.transaction_disparue`.
     Elle lit la TABLE en direct. Avec les 241 lignes du classeur, elle crierait
     241 fois PAR NUIT, et le bruit couvrirait la vraie disparition qu'elle existe
     pour attraper.

  B  phase2/sync/export_app_payload.py -- le filet du cockpit, ET C'EST LE PLUS GRAVE.
     Il ressortirait chaque ligne du classeur avec `_dropped`, et le cockpit
     AFFICHERAIT « · plus dans Hektor depuis <date> » (App.tsx:31502) : une phrase
     FAUSSE montree a l'utilisateur, pas une alarme dans un journal.

⛔ CE QU'ON NE FAIT PAS, et c'est l'arbitrage de Frederic du 15/11 : on ne garde PAS sur
  la plage de numeros, et on ne touche PAS a `present_in_hektor` (575 lectures dans
  150 fichiers). On distingue L'INTENTION -- la marque -- jamais la plage.

⭐ L'ESSAI NE RECOPIE RIEN : il EXTRAIT la vraie requete et la vraie garde du fichier
  source, puis les joue sur une base SQLite en memoire. Si quelqu'un change le code,
  l'essai suit -- il ne peut pas rester vert sur une copie perimee.

Aucun reseau, aucune base reelle.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PAYLOAD = RACINE / "phase2" / "sync" / "export_app_payload.py"
MONITEUR = RACINE / "monitoring" / "check_gti_health.py"
WORKER = RACINE / "Console" / "console_job_worker.js"

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


# ─────────────────────────────────────────────────────────────────────────────
# On extrait du fichier source la requete ET la garde, pour jouer LE VRAI CODE.
# ─────────────────────────────────────────────────────────────────────────────
def lire_requete_et_garde() -> tuple[str, str]:
    """Rend (le SELECT du filet, la clause de garde) tels qu'ils sont ECRITS."""
    src = PAYLOAD.read_text(encoding="utf-8")
    m_garde = re.search(r'garde_origine = \("\s*(AND transaction_origine[^"]*)"', src)
    m_sql = re.search(
        r'ledger_dropped = fetch_rows\(con, """(.*?)"""', src, re.S)
    if not (m_garde and m_sql):
        raise SystemExit("ROUGE : impossible d'extraire la requete ou la garde du fichier.")
    return m_sql.group(1), m_garde.group(1).strip()


def base_avec(lignes, avec_colonne=True):
    """Un ledger local minimal. `lignes` = (app_affaire_id, present, origine, acq)."""
    con = sqlite3.connect(":memory:")
    colonne = ", transaction_origine TEXT" if avec_colonne else ""
    con.execute(
        "CREATE TABLE app_affaire_ledger ("
        " app_affaire_id INTEGER PRIMARY KEY, hektor_annonce_id TEXT,"
        " hektor_mandat_id TEXT, kind TEXT, hektor_affaire_id TEXT, state TEXT,"
        " hektor_acquereur_id TEXT, acquereur_json TEXT, montant TEXT,"
        " date TEXT, date_acte TEXT, sequestre TEXT, last_seen_at TEXT,"
        " present_in_hektor INTEGER NOT NULL DEFAULT 1" + colonne + ")")
    for aid, present, origine, acq in lignes:
        cols = ("app_affaire_id, hektor_annonce_id, kind, hektor_affaire_id,"
                " hektor_acquereur_id, present_in_hektor")
        vals = [aid, "28351", "offre", None if aid >= 1000000 else "33027", acq, present]
        if avec_colonne:
            cols += ", transaction_origine"
            vals.append(origine)
        con.execute("INSERT INTO app_affaire_ledger (%s) VALUES (%s)"
                    % (cols, ",".join("?" * len(vals))), vals)
    con.commit()
    return con


def jouer(con, sql, garde):
    """Rejoue EXACTEMENT ce que fait le payload, garde comprise quand la colonne est la."""
    colonnes = {c[1] for c in con.execute("PRAGMA table_info(app_affaire_ledger)")}
    clause = (" " + garde) if "transaction_origine" in colonnes else ""
    cur = con.execute(sql + clause)
    return [r[0] for r in cur.fetchall()]       # hektor_annonce_id en 1re colonne


def main():
    sql, garde = lire_requete_et_garde()
    print("=== CE QUE L'ESSAI A EXTRAIT DU FICHIER (pas une copie) ===")
    print("    garde : %s" % garde)
    print()

    # app_affaire_id >= 1 000 000 = la plage app ; < = une ligne venue de Hektor.
    LIGNES = [
        (1001424, 0, None, None),            # le cobaye : plage app, PAS marque
        (1001500, 0, "classeur", "605075"),  # une des 241 : MARQUEE
        (1001501, 0, "classeur", None),      # une des 241, sans acquereur
        (1001502, 0, "", "605076"),          # chaine vide : traitee comme non marquee ?
        (50128, 0, None, "191970"),          # VRAIE disparition Hektor -> doit rester
        (50129, 1, None, "191971"),          # presente chez Hektor -> hors sujet
    ]

    print("=== 1. LE FILET DU COCKPIT (B) : la garde exclut le classeur ===")
    # ⛔ LE PREMIER JET DE CE CONTROLE ETAIT VIDE : il comparait 0 a une expression
    #   qui valait 0 par construction, donc il etait vert sans rien prouver.
    #   On compte maintenant les lignes du classeur qui SORTENT : ce doit etre zero,
    #   et le temoin inverse du 2 montre qu'elles sortaient avant.
    con = base_avec(LIGNES)
    ids_marquees = [r[0] for r in con.execute(
        "SELECT app_affaire_id FROM app_affaire_ledger WHERE present_in_hektor = 0 "
        + garde + " AND app_affaire_id IN (1001500, 1001501)")]
    con.close()
    juger("1  aucune des 2 lignes MARQUEES `classeur` ne sort", [], ids_marquees)
    con = base_avec(LIGNES)
    ids = [r[0] for r in con.execute(
        "SELECT app_affaire_id FROM app_affaire_ledger WHERE present_in_hektor = 0 "
        + garde.replace("AND", "AND", 1))]
    con.close()
    juger("1b exactement QUI sort : le cobaye et la vraie disparition, RIEN D'AUTRE",
          [50128, 1001424], sorted(ids))
    juger("1c ⭐ LA VRAIE DISPARITION HEKTOR (50128) SORT TOUJOURS", True, 50128 in ids)
    juger("1d et la ligne PRESENTE chez Hektor (50129) ne sort pas", False, 50129 in ids)
    # ⛔⛔ LE POINT QUE LA QUESTION DE FREDERIC A FAIT TOMBER (16/11) : « c'est a dire ? »
    #   Une case est sans contenu de DEUX facons que la base ne confond pas : NON
    #   RENSEIGNEE (NULL) ou VIDE. Mon premier jet tolerait le vide, donc une ligne du
    #   classeur mal marquee aurait CRIE / AFFICHE quand meme. `IS NULL` seul l'ecarte :
    #   c'est le critere le plus PRUDENT, et c'est deja celui du filet du worker.
    juger("1e ⛔ une marque VIDE est traitee comme MARQUEE (le choix prudent)",
          False, 1001502 in ids)

    print()
    print("=== 2. TEMOIN INVERSE : la MEME base SANS la garde ===")
    con = base_avec(LIGNES)
    ids_sans = [r[0] for r in con.execute(
        "SELECT app_affaire_id FROM app_affaire_ledger WHERE present_in_hektor = 0")]
    con.close()
    juger("2  sans la garde, les 2 lignes du classeur RESSORTENT",
          True, 1001500 in ids_sans and 1001501 in ids_sans)
    juger("2b la garde retire exactement 3 lignes (les 2 marquees + la vide)",
          3, len(ids_sans) - len(ids))

    print()
    print("=== 3. ⛔ LA COLONNE ABSENTE NE DOIT PAS VIDER LA LISTE ===")
    print("    (sinon les 19 affichages legitimes disparaitraient sans un mot)")
    con = base_avec(LIGNES, avec_colonne=False)
    vues_sans_colonne = jouer(con, sql, garde)
    con.close()
    juger("3  la liste n'est PAS vide quand la colonne n'existe pas encore",
          True, len(vues_sans_colonne) > 0)
    # ⛔ MON PREMIER CRITERE DISAIT 4, ET C'ETAIT MOI QUI AVAIS TORT : les lignes a
    #   `present_in_hektor = 0` sont CINQ (1001424, 1001500, 1001501, 1001502, 50128).
    #   Le code rendait bien 5. Une deduction ne change pas ce que la base contient.
    juger("3b et elle rend alors LES CINQ absentes, comme avant le correctif",
          5, len(vues_sans_colonne))

    print()
    print("=== 4. LA GARDE EST BIEN DANS LE FICHIER DU PAYLOAD ===")
    src_p = PAYLOAD.read_text(encoding="utf-8")
    juger("4  la presence de colonne est MESUREE avant (PRAGMA)", True,
          'PRAGMA table_info(app_affaire_ledger)' in src_p)
    juger("4b la garde n'est posee QUE si la colonne existe", True,
          'if "transaction_origine" in colonnes_ledger else ""' in src_p)
    juger("4c et elle est bien COLLEE a la requete", True,
          '""" + garde_origine)' in src_p)
    juger("4d ⛔ le danger est ECRIT dans le fichier (une exclusion se DECLARE)", True,
          "plus dans Hektor depuis" in src_p and "App.tsx:31502" in src_p)

    print()
    print("=== 5. LA SENTINELLE (A) : sa garde et SES DEUX PORTES ===")
    src_m = MONITEUR.read_text(encoding="utf-8")
    # ⚠ ON BORNE SUR LA SENTINELLE SUIVANTE, PAS SUR UN NOMBRE DE CARACTERES :
    #   mon premier jet lisait 900 caracteres apres la cle et ne trouvait rien, parce
    #   que le commentaire de la garde fait plus que ca. Un essai qui depend d'une
    #   longueur devient faux des qu'on ecrit une ligne de plus.
    i_sent = src_m.index('"key": "data.transaction_disparue"')
    i_suiv = src_m.index('"key": "data.geste_abandonne"', i_sent)
    bloc = src_m[i_sent:i_suiv]
    juger("5  la garde est dans les params de data.transaction_disparue", True,
          '"transaction_origine": "is.null"' in bloc)
    juger("5b elle garde ses deux filtres d'origine", True,
          '"present_in_hektor": "is.false"' in bloc and '"last_seen_at"' in bloc)
    juger("5c ⛔ L'ECHANTILLON herite des params (porte n° 1)", True,
          'params.update(sentinel.get("params") or {})' in src_m)
    juger("5d ⛔ LE COMPTAGE recoit les params (porte n° 2)", True,
          'self.supabase.count(sentinel["table"], sentinel.get("params"))' in src_m)
    juger("5e ⛔ et PLUS de tolerance a la chaine vide (le `or` a ete RETIRE)", True,
          'transaction_origine.eq.' not in bloc)

    print()
    print("=== 6. ⭐⭐ LES TROIS PORTES DISENT-ELLES LA MEME CHOSE ? ===")
    print("    (c'est la question de Frederic du 16/11 : une divergence se supprime,")
    print("     elle ne se surveille pas)")
    src_w = WORKER.read_text(encoding="utf-8", errors="replace")
    juger("6  le filet du worker : `&transaction_origine=is.null`", True,
          '&transaction_origine=is.null' in src_w)
    juger("6b la sentinelle : `is.null` AUSSI, et rien de plus", True,
          '"transaction_origine": "is.null"' in bloc
          and 'transaction_origine.eq.' not in bloc)
    juger("6c le payload : `IS NULL` AUSSI, et rien de plus", True,
          '" AND transaction_origine IS NULL"' in src_p
          and "TRIM(transaction_origine)" not in src_p)
    juger("6d ⛔ et le pourquoi est ECRIT dans les deux fichiers", True,
          "VIDE" in src_p and "non renseignee" in src_p
          and "NON RENSEIGNEE" in src_m)

    print()
    print("%d/%d verts" % (VERTS, VERTS + len(ROUGES)))
    if ROUGES:
        print("ROUGES : " + " . ".join(ROUGES))
    return 1 if ROUGES else 0


if __name__ == "__main__":
    raise SystemExit(main())
