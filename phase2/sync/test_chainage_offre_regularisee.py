"""05/11/2026 -- L'OFFRE OUBLIEE REGULARISEE : accepter suffit-il a la rattacher a son compromis la nuit ?

Note : notice/AUDIT_REFONTE_MODALE_STATUT_2026-11-05.md §14 (option 1).
On EXECUTE la vraie regle de nuit (`recalculer_les_chaines`) sur une base SQLite EN MEMOIRE -- aucune base
reelle n'est ouverte -- avec les interrupteurs tels qu'ils sont allumes en production (.env, lu par le module).

Le cas : une offre faite le 01/09 au nom de Monsieur (A1), restee « proposee » ; un compromis du 12/10 au nom de
Madame (B1). Noms differents : le § 2.8 ne les relie pas. L'ecran rend alors « Accepter » a l'offre
(offreARegulariser). On verifie que, l'offre une fois ACCEPTEE, la nuit met le compromis dans SON dossier.

TEMOIN INVERSE : la meme offre datee APRES le compromis, acceptee, ne doit PAS l'attirer tant
que les NOMS DIFFERENT -- c'etait la date qui refusait ; depuis la regle B (10/11), c'est le nom. Et l'offre laissee « proposee » ne doit rien attirer non plus (le probleme de depart).

    python phase2/sync/test_chainage_offre_regularisee.py
    sortie 0 = tout vert · 1 = un controle en echec
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import affaire_ledger as al  # noqa: E402

# ⛔ L'ENCODAGE DE LA CONSOLE, ET CE DEFAUT A COUTE UN DIAGNOSTIC (12/11/2026).
#   Cet essai ecrit « ⛔ » et « OK ». Sur la console Windows (cp1252), le premier
#   « ⛔ » levait UnicodeEncodeError -- l'essai s'arretait AVANT d'avoir dit ce qui
#   n'allait pas, et il paraissait CASSE alors qu'il avait simplement trouve deux
#   echecs. Il a fallu PYTHONIOENCODING=utf-8 pour le voir.
#   ⚠ Un essai qui ne peut pas AFFICHER son resultat ne vaut rien : son silence se
#     confond avec une panne. Meme patron que les autres scripts du projet
#     (apparier_classeur.py, apres_run_*.py).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

echecs = 0


def ok(cond: bool, libelle: str) -> None:
    global echecs
    print(("  OK  " if cond else "  ⛔  ") + libelle)
    if not cond:
        echecs += 1


def base(lignes: list[tuple]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute(f"""CREATE TABLE {al.LEDGER_TABLE} (
        app_affaire_id INTEGER PRIMARY KEY, hektor_annonce_id TEXT, kind TEXT, state TEXT, date TEXT,
        acquereurs_json TEXT, propositions_json TEXT, hektor_affaire_id TEXT, present_in_hektor TEXT,
        app_chaine_id INTEGER)""")
    for (ident, kind, state, jour, acq) in lignes:
        props = json.dumps([{"type": "proposition", "date": jour + " 10:00:00"}]) if kind == "offre" else None
        con.execute(f"INSERT INTO {al.LEDGER_TABLE} VALUES (?,?,?,?,?,?,?,?,?,NULL)",
                    (ident, "59132", kind, state, jour, json.dumps([{"id": acq}]), props, str(ident), "1"))
    return con


def chaines(lignes: list[tuple]) -> dict[int, int]:
    con = base(lignes)
    al.recalculer_les_chaines(con)
    return dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {al.LEDGER_TABLE}"))


print("interrupteurs lus par le module :",
      "V2" if al.chainage_v2_actif() else "-", "| 2.8" if al.chainage_offre_proposee_actif() else "| -")

print("Le probleme de depart — l'offre reste « proposee »")
c = chaines([(101, "offre", "proposed", "2026-09-01", "A1"), (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] != c[110], f"offre et compromis dans deux dossiers (offre {c[101]}, compromis {c[110]})")

print("La regularisation — l'offre ACCEPTEE")
c = chaines([(101, "offre", "accepted", "2026-09-01", "A1"), (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] == c[110], f"le compromis rejoint le dossier de l'offre (les deux en {c[110]})")
ok(c[110] == 101, "le dossier porte le numero de l'offre (le plus petit), comme la regle le dit")

print("Meme jour")
c = chaines([(101, "offre", "accepted", "2026-10-12", "A1"), (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] == c[110], "offre et compromis le meme jour : rattaches (l'offre est rangee d'abord)")

print("TEMOIN INVERSE — l'offre datee APRES le compromis, acceptee, NOMS DIFFERENTS")
c = chaines([(101, "offre", "accepted", "2026-10-20", "A1"), (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] != c[110], "elle ne l'attire pas -- la date le refusait, et depuis la regle B c'est le NOM")

print("Deja relie par le § 2.8 (meme acquereur), l'offre restee « proposee »")
c = chaines([(101, "offre", "proposed", "2026-09-01", "A1"), (110, "compromis", "active", "2026-10-12", "A1")])
ok(c[101] == c[110] if al.chainage_offre_proposee_actif() else True,
   "meme acquereur : deja dans le meme dossier (aucune regularisation necessaire)")

# ═══ LES TROIS REGLES DE RECOLLEMENT (10/11/2026) ═════════════════════
# ⚠⚠ POURQUOI ELLES SONT EPROUVEES ICI, et pas dans un fichier a part : la regle B
#   touche EXACTEMENT le cas du temoin inverse ci-dessus. Celui-ci reste vert parce
#   que ses deux noms different (A1 / B1) -- mais son libelle dit « c'est pourquoi
#   l'ecran exige la date », et avec B allumee ce n'est plus la date qui refuse,
#   C'EST LE NOM. Un temoin qui reste vert pour une autre raison que celle qu'il
#   annonce est un temoin qu'on ne peut plus lire : les cas ci-dessous le disent.
# ⭐ CHAQUE BLOC EST CONDITIONNEL A SON INTERRUPTEUR, comme celui du § 2.8 : le
#   test doit rester vert interrupteurs eteints, c'est-a-dire en production.

# ⭐ 12/11/2026 : LA REGLE D, posee a la demande de Frederic -- « un acheteur +
#   un bien = un dossier ». Elle passe OUTRE la fenetre de 31 jours de la regle B
#   et outre l'etat ANNULE d'un compromis : si c'est le MEME acheteur sur le MEME
#   bien, c'est UNE affaire.
#   ⚠ ELLE EST LUE ICI, AVANT LA REGLE B, parce que le premier temoin qui en depend
#     est celui de la fenetre de 31 jours -- ma premiere version la lisait 4 blocs
#     plus bas et l'essai tombait sur un NameError.
d_actif = al.chainage_meme_acheteur_actif()
b_actif = al.chainage_offre_acceptee_seule_actif()
print("REGLE B — l'offre acceptee datee APRES le compromis, AU MEME NOM")
c = chaines([(101, "offre", "accepted", "2026-10-26", "A1"),
             (110, "compromis", "active", "2026-10-12", "A1")])
ok((c[101] == c[110]) if b_actif else (c[101] != c[110]),
   "14 jours et meme nom : rattachee" if b_actif
   else "regle B eteinte : rien ne bouge (comportement d'avant)")

print("REGLE B, TEMOIN INVERSE — hors de la fenetre de 31 jours")
c = chaines([(101, "offre", "accepted", "2027-02-21", "A1"),
             (110, "compromis", "active", "2026-10-12", "A1")])
# ⚠ MEME ACHETEUR (A1 des deux cotes) : depuis la REGLE D, la fenetre de 31 jours
#   ne decide plus seule. D eteinte -> 132 jours les separent ; D allumee -> le
#   MEME acheteur sur le MEME bien les reunit, et c'est voulu.
ok((c[101] == c[110]) if d_actif else (c[101] != c[110]),
   "132 jours au MEME nom : reunis par la regle D" if d_actif
   else "132 jours : PAS rattachee, meme au meme nom")

print("REGLE B, TEMOIN INVERSE — dans la fenetre mais NOM DIFFERENT")
c = chaines([(101, "offre", "accepted", "2026-10-26", "A1"),
             (110, "compromis", "active", "2026-10-12", "B1")])
ok(c[101] != c[110], "14 jours mais deux acheteurs : PAS rattachee")

c_actif = al.chainage_vente_seule_actif()
print("REGLE C — la vente seule datee AVANT son compromis actif, au meme nom")
c = chaines([(101, "compromis", "active", "2026-10-12", "A1"),
             (110, "vente", "sold", "2026-09-01", "A1")])
ok((c[101] == c[110]) if c_actif else (c[101] != c[110]),
   "l'ordre des dates est ignore : rattachee" if c_actif
   else "regle C eteinte : rien ne bouge (comportement d'avant)")

print("REGLE C, TEMOIN INVERSE — le compromis est ANNULE")
c = chaines([(101, "compromis", "cancelled", "2026-10-12", "A1"),
             (110, "vente", "sold", "2026-09-01", "A1")])
# ⚠ MEME ACHETEUR (A1 des deux cotes). C'est LE CAS QUE FREDERIC A TRANCHE le
#   12/11 sur les dossiers 10753 et 10798 : un compromis annule puis une vente,
#   au MEME nom, c'est UNE SEULE affaire -- l'acheteur a fini par acheter.
#   D eteinte -> l'etat mort ferme le dossier (regle d'avant) ;
#   D allumee -> ils sont reunis.
ok((c[101] == c[110]) if d_actif else (c[101] != c[110]),
   "compromis annule + vente au MEME nom : reunis par la regle D" if d_actif
   else "un compromis annule ne capte pas la vente")

print("REGLE D, TEMOIN INVERSE — deux acheteurs sur le meme bien")
# ⛔ LE TEMOIN QUI MANQUAIT, et c'est le plus important de la regle D : elle ne
#   doit JAMAIS reunir deux acheteurs differents. Sans lui, le defaut du 12/11 au
#   matin (l'ordre de lecture decidait, et les montants avaient ete croises sur le
#   bien 1801) serait repasse sans bruit.
c = chaines([(101, "compromis", "cancelled", "2026-10-12", "A1"),
             (110, "vente", "sold", "2026-09-01", "B1")])
ok(c[101] != c[110], "deux acheteurs : la regle D ne les reunit PAS")

print("REGLE D, TEMOIN INVERSE — un acheteur, DEUX ventes")
# ⚠ L'AUTRE GARDE de la regle D, trouvee a blanc le 12/11 : un acheteur qui porte
#   PLUSIEURS ventes sur le meme bien est ECARTE EN ENTIER -- sinon l'ordre de
#   lecture choisit, et il avait croise les montants.
c = chaines([(101, "offre", "accepted", "2026-09-01", "A1"),
             (110, "vente", "sold", "2026-10-01", "A1"),
             (120, "vente", "sold", "2026-10-02", "A1")])
ok(len({c[101], c[110], c[120]}) > 1,
   "un acheteur a DEUX ventes : la regle D s'abstient")

print("REGLE C, TEMOIN INVERSE — nom different")
c = chaines([(101, "compromis", "active", "2026-10-12", "A1"),
             (110, "vente", "sold", "2026-09-01", "B1")])
ok(c[101] != c[110], "deux acheteurs : la vente reste seule")

print("TOUT VERT" if not echecs else f"⛔ {echecs} controle(s) en echec")
sys.exit(1 if echecs else 0)
