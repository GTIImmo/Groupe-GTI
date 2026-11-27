#!/usr/bin/env python3
"""UNE PIECE EST-ELLE UNE COPIE OU UNE VRAIE PIECE ? -- LA fonction unique du chantier classeur (22/11/2026).

Son mot du 22/11 (point 7) : « pose UNE SEULE fonction qui dit si une piece est une copie ou une vraie piece, et
fais-la appeler par tous. Pas une regle recopiee dans six outils. Et ajoute-la aux temoins : une piece de la plage app
rangee comme copie doit faire crier le controle. »

POURQUOI ELLE EXISTE. Le registre a deux sortes de pieces au-dela de 1 000 000 (la plage de l'app), mesure du 22/11 :
  . 190 COPIES C5 -- creees depuis son Sheet (`transaction_origine = 'classeur'`), sans numero Hektor ;
  . 340 VRAIES PIECES -- nees dans l'app puis numerotees par Hektor (origine vide, numero Hektor present) ;
  103 de ces 340 sont reliees par le gel a l'une de ses lignes (51 lignes).
Deux de mes outils prenaient toute piece >= 1 000 000 pour une copie : le fabricant de la V3 (8 endroits) et la 1re
version du crible. Mesure du 22/11 : aucune decision rendue n'en a change. Mais le protocole s'appuie sur cette notion
a chaque ligne : elle ne se decide plus qu'ICI.

LA REGLE. Une COPIE est une piece dont l'origine est « classeur ». Le NUMERO de la piece ne decide jamais (une piece de
la plage peut etre une vraie piece). Le NUMERO HEKTOR sert de CONTRE-MARQUE : les deux marques doivent s'accorder.
  origine « classeur », sans numero Hektor     -> COPIE
  origine vide, quel que soit le numero        -> VRAIE  (dans la plage sans numero Hektor : nee dans l'app, en attente
                                                          de son numero -- vraie, marquee « sans_numero »)
  origine « classeur » AVEC un numero Hektor   -> REFUS  (PieceIncoherente : une copie que Hektor connaitrait)
  une AUTRE origine, non vide                  -> REFUS  (PieceIncoherente : une origine neuve se decide, elle ne se
                                                          devine pas -- c'est le defaut dormant de temps3, qui prenait
                                                          pour copie toute origine non vide)

LECTURE SEULE. Le controle ouvre le registre local en `mode=ro` et n'ecrit rien nulle part.

    python phase2/checks/piece_copie_ou_vraie.py        # le controle, sortie 0 vert / 1 rouge / 2 pas pu mesurer
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"

COPIE = "copie"
VRAIE = "vraie"
ORIGINE_COPIE = "classeur"
PLAGE_APP = 1_000_000          # la plage de l'app : elle dit OU une piece est nee, jamais si c'est une copie

# LES TEMOINS NOMMES (22/11) -- un par sens, pris dans le registre mesure ce matin :
#   1001361 : offre du bien 61672, nee dans la plage app, numero Hektor 33098 -> doit sortir VRAIE
#             (c'est exactement la piece qu'une regle « au numero » rangerait comme copie) ;
#   1001532 : compromis du bien 9748, cree depuis le Sheet (C5), sans numero Hektor -> doit sortir COPIE ;
#   19131   : compromis du bien 39845, piece Hektor ordinaire -> doit sortir VRAIE.
TEMOINS = {1001361: VRAIE, 1001532: COPIE, 19131: VRAIE}
# le compte du 22/11, pour que le controle dise si le parc a bouge (il ne crie pas pour autant : il le DIT)
COMPTE_22_11 = {"copies": 190, "vraies_plage": 340, "vraies_plage_reliees_gel": 103}


class PieceIncoherente(ValueError):
    """Les deux marques d'une piece ne s'accordent pas : la fonction refuse de repondre."""


def _texte(x) -> str:
    return "" if x is None else str(x).strip()


def nature(app_affaire_id, transaction_origine, hektor_affaire_id) -> str:
    """COPIE ou VRAIE. Leve PieceIncoherente si les marques se contredisent (jamais une reponse au plus probable)."""
    origine = _texte(transaction_origine)
    numero = _texte(hektor_affaire_id)
    if origine == ORIGINE_COPIE:
        if numero:
            raise PieceIncoherente("piece %s : origine « classeur » mais numero Hektor %s" % (app_affaire_id, numero))
        return COPIE
    if origine:
        raise PieceIncoherente("piece %s : origine inconnue %r -- a decider, pas a deviner" % (app_affaire_id, origine))
    return VRAIE


def est_copie(app_affaire_id, transaction_origine, hektor_affaire_id) -> bool:
    return nature(app_affaire_id, transaction_origine, hektor_affaire_id) == COPIE


def sans_numero_hektor(app_affaire_id, transaction_origine, hektor_affaire_id) -> bool:
    """Une VRAIE piece nee dans l'app qui n'a pas encore son numero Hektor (0 le 22/11) -- vraie, mais a compter a part."""
    return (nature(app_affaire_id, transaction_origine, hektor_affaire_id) == VRAIE
            and int(app_affaire_id) >= PLAGE_APP and not _texte(hektor_affaire_id))


def natures(con: sqlite3.Connection, table: str = "app_affaire_ledger") -> dict[int, str]:
    """La nature de CHAQUE piece d'un registre (sqlite local, ou toute connexion qui a les trois colonnes).
    Leve PieceIncoherente a la premiere piece incoherente -- le protocole ne tourne pas sur un registre incoherent."""
    return {int(a): nature(a, o, n) for a, o, n in con.execute(
        "select app_affaire_id, transaction_origine, hektor_affaire_id from %s" % table)}


def copies(con: sqlite3.Connection, table: str = "app_affaire_ledger") -> set[int]:
    return {a for a, v in natures(con, table).items() if v == COPIE}


def regle_au_numero(app_affaire_id, transaction_origine, hektor_affaire_id) -> str:
    """L'ANCIENNE regle, FAUSSE, gardee pour le temoin inverse : toute piece de la plage serait une copie."""
    return COPIE if int(app_affaire_id) >= PLAGE_APP else VRAIE


def juger(con: sqlite3.Connection, regle) -> dict:
    """Confronte une regle a la fonction unique, piece par piece. Une regle juste donne 0 desaccord."""
    lignes = list(con.execute("select app_affaire_id, transaction_origine, hektor_affaire_id from app_affaire_ledger"))
    des = [int(a) for a, o, n in lignes if regle(a, o, n) != nature(a, o, n)]
    return {"pieces": len(lignes), "desaccords": len(des), "exemples": sorted(des)[:5]}


def controle(con: sqlite3.Connection) -> tuple[bool, list[str]]:
    """Le controle de la fonction, avec ses temoins nommes et son temoin inverse."""
    dit, ok = [], True
    try:
        N = natures(con)
    except PieceIncoherente as e:
        return False, ["⛔ REGISTRE INCOHERENT -- la fonction refuse de repondre : %s" % e]
    n_cop = sum(1 for v in N.values() if v == COPIE)
    plage = {a for a, v in N.items() if v == VRAIE and a >= PLAGE_APP}
    sans_num = [a for a, o, n in con.execute(
        "select app_affaire_id, transaction_origine, hektor_affaire_id from app_affaire_ledger "
        "where cast(app_affaire_id as integer) >= ?", (PLAGE_APP,)) if sans_numero_hektor(a, o, n)]
    dit.append("registre : %d pieces ; %d copies ; %d vraies pieces dans la plage app (dont %d sans numero Hektor)"
               % (len(N), n_cop, len(plage), len(sans_num)))
    for k, attendu in (("copies", n_cop), ("vraies_plage", len(plage))):
        if attendu != COMPTE_22_11[k]:
            dit.append("   ⚠ %s : %d, contre %d le 22/11 -- le parc a bouge (ce n'est pas un rouge, c'est un fait a dire)"
                       % (k, attendu, COMPTE_22_11[k]))
    # 1. les temoins nommes
    for a, attendu in TEMOINS.items():
        obtenu = N.get(a)
        bon = obtenu == attendu
        ok &= bon
        dit.append("   %s temoin %d : attendu %s, obtenu %s" % ("✅" if bon else "⛔", a, attendu, obtenu))
    # 2. aucune vraie piece de la plage rangee comme copie, aucune copie avec un numero (deja garanti par nature())
    cop_plage_num = [a for a, o, n in con.execute(
        "select app_affaire_id, transaction_origine, hektor_affaire_id from app_affaire_ledger "
        "where cast(app_affaire_id as integer) >= ? and coalesce(hektor_affaire_id,'') <> ''", (PLAGE_APP,))
        if N[int(a)] == COPIE]
    ok &= not cop_plage_num
    dit.append("   %s pieces de la plage AVEC numero Hektor rangees comme copie : %d %s"
               % ("✅" if not cop_plage_num else "⛔", len(cop_plage_num), cop_plage_num[:5]))
    # 3. LE TEMOIN INVERSE : l'ancienne regle « au numero » DOIT faire crier, exactement sur les vraies pieces de la plage
    j = juger(con, regle_au_numero)
    crie = j["desaccords"] == len(plage) and j["desaccords"] > 0
    ok &= crie
    dit.append("   %s temoin inverse -- l'ancienne regle « au numero » : %d desaccord(s) sur %d pieces (attendu %d, les "
               "vraies pieces de la plage) %s" % ("✅" if crie else "⛔", j["desaccords"], j["pieces"], len(plage),
                                                  j["exemples"]))
    return ok, dit


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not BASE.exists():
        print("⛔ registre local introuvable : %s" % BASE)
        return 2
    con = sqlite3.connect("file:%s?mode=ro" % BASE.as_posix(), uri=True)
    try:
        ok, dit = controle(con)
    finally:
        con.close()
    print("\n".join(dit))
    print("CONTROLE DE LA FONCTION UNIQUE : %s" % ("VERT" if ok else "⛔ ROUGE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
