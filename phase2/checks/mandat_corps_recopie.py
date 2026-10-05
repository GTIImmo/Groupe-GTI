# -*- coding: utf-8 -*-
"""UN MANDAT NE PORTE PAS LE CORPS D'UN AUTRE.                      05/10/2026

================================================================================
CE QUE CETTE SENTINELLE SURVEILLE, ET POURQUOI IL A FALLU L'ECRIRE
================================================================================
SIGNALE PAR FREDERIC, en remontant la piste des mandants du registre : des lignes
de 2026 nommaient un mandant qui n'etait pas le proprietaire du bien.

LA CAUSE, ETABLIE SUR LA REPONSE BRUTE DE HEKTOR (descente du 05/10 a 04:21) :

    hektor_mandat_id = 105 sert DEUX annonces, avec le MEME corps
       annonce   454  numero 14898  debut 2022-07-20  montant 62000  « Marie-Jose BANO »
       annonce 39707  numero 18523  debut 2026-04-10  montant 62000  « Marie-Jose BANO »

    l'annonce 39707 : « Maison de bourg », Montregard, prix 112 500
    ses proprietaires selon Hektor : M. Paul SOUVIGNET

  Les DEUX blocs viennent de la MEME reponse : le bloc mandats nomme BANO, le bloc
  proprietaires nomme SOUVIGNET. Et BANO est proprietaire de l'annonce 454.

LE MOTIF EST SANS AMBIGUITE, mesure sur les 91 cas :
     les 91 identifiants Hektor valent moins de 2000   (min 3, max 660)
     89 des 91 apparient un mandat ancien (2022-2024) a un mandat de 2026
     l'annonce ancienne a un identifiant bas (29, 447, 450, 454), la neuve un haut
  Hektor a RECOMMENCE sa numerotation de mandats a 3. Les mandats de 2026 ont donc
  recu des identifiants DEJA PRIS, et son point d'entree « detail de l'annonce »
  rend, pour le mandat NEUF, le corps de l'ANCIEN -- en gardant le numero et la
  date neufs. C'est un defaut de Hektor, pas le notre.

CE QUI EST CONTAMINE, ET CE QUI NE L'EST PAS
     numero de mandat, date de debut, date de fin : JUSTES (ce sont les neufs)
     mandants, montant                            : CEUX DE L'AUTRE ANNONCE
  Second signal, mesure : montant du mandat != prix de l'annonce dans 92 % des
  lignes atteintes, contre 9 % des lignes saines.

CE QUE NOTRE IDENTIFIANT A DEJA EVITE. La cle du registre est le couple
  (annonce, numero), PAS `hektor_mandat_id` -- choix fait bien avant ce defaut, et
  qui l'a contenu : sur les 182 lignes touchees on a 182 lignes distinctes, AUCUNE
  fusion. Avec une cle sur l'identifiant de Hektor, 91 mandats auraient disparu et
  deux annonces se seraient ecrasees l'une l'autre a chaque run.
  MAIS un identifiant juste ne verifie pas le CONTENU. D'ou cette sentinelle :
  c'est la piece qui manquait a la chaine.

LECTURE SEULE. Code 1 si le defaut s'aggrave.
   python phase2/checks/mandat_corps_recopie.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIROIR = ROOT / "data" / "hektor.sqlite"

# Le seuil n'est PAS un reglage de confort : c'est l'etat connu au 05/10/2026.
# Il doit BAISSER quand Hektor corrige, jamais monter en silence.
CONNU_AU_05_10 = 91

# Les deux formes de partage d'identifiant, qu'il ne faut JAMAIS confondre :
#   meme corps + meme numero  -> UN mandat qui couvre plusieurs lots. NORMAL.
#   meme corps + numeros DIFFERENTS -> le corps d'un mandat servi pour un autre.
_GROUPES = (
    "WITH partages AS ("
    "   SELECT hektor_mandat_id FROM hektor_mandat"
    "    GROUP BY 1 HAVING COUNT(DISTINCT hektor_annonce_id) > 1),"
    " groupes AS ("
    "   SELECT hektor_mandat_id,"
    "          COUNT(DISTINCT COALESCE(mandants_texte, '')) AS nb_mandants,"
    "          COUNT(DISTINCT COALESCE(numero, ''))         AS nb_numeros"
    "     FROM hektor_mandat"
    "    WHERE hektor_mandat_id IN (SELECT hektor_mandat_id FROM partages)"
    "    GROUP BY 1)"
)


def _table(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?", (nom,)
    ).fetchone() is not None


def mesurer(conn: sqlite3.Connection) -> dict | None:
    if not _table(conn, "hektor_mandat"):
        return None

    corps_recopie = conn.execute(
        _GROUPES + " SELECT COUNT(*) FROM groupes WHERE nb_mandants = 1 AND nb_numeros > 1"
    ).fetchone()[0]

    # Ce que l'agence voit vraiment : des LIGNES de mandat, pas des identifiants.
    lignes_atteintes = conn.execute(
        _GROUPES
        + " SELECT COUNT(*) FROM hektor_mandat WHERE hektor_mandat_id IN"
          " (SELECT hektor_mandat_id FROM groupes WHERE nb_mandants = 1 AND nb_numeros > 1)"
    ).fetchone()[0]

    un_mandat_plusieurs_lots = conn.execute(
        _GROUPES + " SELECT COUNT(*) FROM groupes WHERE nb_mandants = 1 AND nb_numeros = 1"
    ).fetchone()[0]

    # LA PRESSION QUI MONTE : 75 % des mandats de 2026 ont un identifiant deja pris,
    # contre 5 a 9 % les annees d'avant. C'est ce chiffre qui dit que le defaut va
    # s'aggraver et non se resorber.
    par_annee = conn.execute(
        "WITH partages AS ("
        "   SELECT hektor_mandat_id FROM hektor_mandat"
        "    GROUP BY 1 HAVING COUNT(DISTINCT hektor_annonce_id) > 1)"
        " SELECT substr(date_debut, 1, 4) AS an, COUNT(*),"
        "        SUM(CASE WHEN hektor_mandat_id IN (SELECT hektor_mandat_id FROM partages)"
        "                 THEN 1 ELSE 0 END)"
        "   FROM hektor_mandat WHERE date_debut >= '2024'"
        "  GROUP BY 1 ORDER BY 1 DESC"
    ).fetchall()

    comptes = {
        "corps_recopie": corps_recopie,
        "lignes_atteintes": lignes_atteintes,
        "un_mandat_plusieurs_lots": un_mandat_plusieurs_lots,
        "par_annee": par_annee,
        # L'AGGRAVATION EST L'ALERTE, pas le niveau : 91 est l'etat connu et subi.
        # Ce qui doit reveiller, c'est qu'il MONTE.
        "aggravation": max(0, corps_recopie - CONNU_AU_05_10),
    }
    comptes["graves"] = comptes["aggravation"]
    return comptes


def montant_incoherent(conn: sqlite3.Connection) -> tuple[int, int] | None:
    """Le second signal : montant du mandat != prix de l'annonce.

    Il ne PROUVE rien a lui seul -- un mandat peut legitimement porter un montant
    different du prix affiche (revision, net vendeur) : 9 % des lignes saines sont
    dans ce cas. Il ne vaut que par l'ECART, 92 % sur les lignes atteintes. On le
    rend donc en couple, jamais seul.
    """
    if not _table(conn, "hektor_annonce"):
        return None
    r = conn.execute(
        _GROUPES
        + " SELECT COUNT(*),"
          "        SUM(CASE WHEN m.montant IS NOT NULL AND a.prix IS NOT NULL"
          "                  AND ABS(m.montant - a.prix) > 1 THEN 1 ELSE 0 END)"
          "   FROM hektor_mandat m"
          "   LEFT JOIN hektor_annonce a"
          "          ON CAST(a.hektor_annonce_id AS TEXT) = CAST(m.hektor_annonce_id AS TEXT)"
          "  WHERE m.hektor_mandat_id IN"
          "        (SELECT hektor_mandat_id FROM groupes WHERE nb_mandants = 1 AND nb_numeros > 1)"
    ).fetchone()
    return int(r[0] or 0), int(r[1] or 0)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    conn = sqlite3.connect("file:%s?mode=ro" % MIROIR.as_posix(), uri=True)
    try:
        m = mesurer(conn)
        mt = montant_incoherent(conn) if m else None
    finally:
        conn.close()
    if m is None:
        print("NON MESURABLE : hektor_mandat manque -- ce n'est pas un zero")
        return 2

    print("UN MANDAT NE PORTE PAS LE CORPS D'UN AUTRE")
    print("   corps recopie sur une autre annonce : %s   (connu au 05/10 : %s)"
          % (m["corps_recopie"], CONNU_AU_05_10))
    print("      lignes de mandat atteintes       : %s" % m["lignes_atteintes"])
    if mt:
        total, ecart = mt
        print("      dont montant != prix annonce     : %s sur %s   (9 %% sur les lignes saines)"
              % (ecart, total))
    print("   un mandat sur plusieurs lots (NORMAL): %s" % m["un_mandat_plusieurs_lots"])
    print("")
    print("   -- la pression : part d'identifiants Hektor deja pris --")
    for an, total, part in m["par_annee"]:
        print("      %s : %5s mandats, %4s partages  (%2.0f %%)"
              % (an, total, part, 100 * (part or 0) / max(total or 1, 1)))
    print("")
    print("   -- ce qui est contamine, et ce qui ne l'est pas --")
    print("      JUSTES  : numero de mandat et dates (ceux du mandat neuf)")
    print("      FAUSSES : mandants et montant (ceux de l'autre annonce)")
    print("      les MANDANTS affiches ne le sont plus : le registre lit nos liens")
    print("      depuis le 05/10. Reste le MONTANT, et lui, il ment.")

    if m["graves"]:
        print("")
        print("GRAVE : %s cas de PLUS qu'au 05/10 -- le defaut de Hektor s'aggrave."
              % m["graves"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
