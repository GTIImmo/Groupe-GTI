# -*- coding: utf-8 -*-
"""Essai du chantier 1 (⑧ types, 26/10/2026) sur une COPIE de phase2.sqlite.

    python phase2/checks/test_acheteur_proprietaire_sur_copie.py --base <copie.sqlite> [--types]

⛔ JAMAIS sur phase2/phase2.sqlite : le script ECRIT dans la base qu'on lui donne
   (il joue la nuit du registre des liens). Il refuse le chemin de production.
Il n'appelle ni Hektor ni Supabase (pas de push).

Ce qu'il prouve :
  1. interrupteur ALLUME : les liens nes d'une vente sont poses (~113 le 26/10), le
     temoin 61730 / JACQUIER porte la date de la vente, les 10 vrais mandants non ;
  2. la date n'est JAMAIS reecrite ;
  3. le registre des mandats n'inscrit plus l'acheteur parmi les mandants ;
  4. le push nommerait les deux colonnes ;
  5. interrupteur ETEINT : tout est remis a vide, et le vide part UNE fois ;
  6. (--types) la nuit des contacts ne dit plus « mandant » pour ces acheteurs.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.contacts import regle_acheteur_proprietaire as R  # noqa: E402
from phase2.sync import relation_ledger as L  # noqa: E402
from phase2.sync.export_app_payload import charger_mandants_du_registre_des_liens  # noqa: E402

ECHECS: list[str] = []
# les 10 vrais mandants (Hektor, 26/10) : (annonce, numero HEKTOR de la personne)
VRAIS = [("10293", "31405"), ("10447", "132724"), ("10776", "167529"), ("19850", "46028"),
         ("29546", "153073"), ("29822", "166093"), ("39359", "334205"), ("45119", "179814"),
         ("45172", "179417"), ("9823", "68121")]


def ok(cond: bool, nom: str) -> None:
    print(("  ok   " if cond else "  ECHEC ") + nom)
    if not cond:
        ECHECS.append(nom)


def interrupteur(allume: bool) -> None:
    R._ENV_DEJA_CHARGE = True            # l'essai ne lit pas .env : il decide
    os.environ[R.INTERRUPTEUR] = "1" if allume else "0"


def nuit(con: sqlite3.Connection) -> dict:
    L._ACHETEUR_A_VIDER_CHEZ_SUPABASE = False
    return L.refresh(con, full=True)


def mandants_de(con, annonce: str) -> list[str]:
    return [str(e.get("nom")) for e in charger_mandants_du_registre_des_liens(con).get(annonce, [])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--types", action="store_true", help="joue aussi load_relations (lit data/hektor.sqlite)")
    args = ap.parse_args()
    base = Path(args.base).resolve()
    if base == (ROOT / "phase2" / "phase2.sqlite").resolve():
        print("REFUS : c'est la base de production. Donner une COPIE.")
        return 2
    con = sqlite3.connect(str(base), timeout=60)
    con.row_factory = sqlite3.Row

    print("0. avant : la regle eteinte, rien de pose")
    interrupteur(False)
    nuit(con)
    jacquier_avant = mandants_de(con, "61730")
    total_avant = sum(len(v) for v in charger_mandants_du_registre_des_liens(con).values())
    ok(con.execute("SELECT COUNT(*) FROM app_relation WHERE origine IS NOT NULL").fetchone()[0] == 0,
       "aucune origine posee interrupteur eteint")
    ok(any("JACQUIER" in n.upper() for n in jacquier_avant),
       f"le defaut est la : JACQUIER parmi les mandants de 61730 ({jacquier_avant})")

    print("1. la nuit, interrupteur ALLUME")
    interrupteur(True)
    bilan = nuit(con)
    n = con.execute("SELECT COUNT(*) FROM app_relation WHERE origine = 'vente'").fetchone()[0]
    print(f"     bilan : { {k: v for k, v in bilan.items() if k.startswith(('acheteur_', 'filet_'))} }")
    ok(100 <= n <= 140, f"liens nes d'une vente poses : {n} (~113 attendus)")
    t = con.execute("SELECT origine, proprietaire_depuis FROM app_relation"
                    " WHERE app_contact_id = 10354352 AND hektor_annonce_id = '61730'").fetchone()
    ok(t is not None and t["origine"] == "vente" and t["proprietaire_depuis"] == "2026-09-25",
       f"temoin 61730 / JACQUIER : {dict(t) if t else None}")
    vrais = con.execute(
        "SELECT COUNT(*) FROM app_relation WHERE origine IS NOT NULL AND (hektor_annonce_id, hektor_contact_id) IN ("
        + ",".join("(?,?)" for _ in VRAIS) + ")", [x for p in VRAIS for x in p]).fetchone()[0]
    ok(vrais == 0, "les 10 vrais mandants n'ont pas d'origine vente (D5 b)")

    print("2. la date n'est jamais reecrite")
    con.execute("UPDATE app_relation SET proprietaire_depuis = '2000-01-01'"
                " WHERE app_contact_id = 10354352 AND hektor_annonce_id = '61730'")
    nuit(con)
    d = con.execute("SELECT proprietaire_depuis FROM app_relation"
                    " WHERE app_contact_id = 10354352 AND hektor_annonce_id = '61730'").fetchone()[0]
    ok(d == "2000-01-01", f"une 2e nuit garde la date posee ({d})")
    con.execute("UPDATE app_relation SET proprietaire_depuis = '2026-09-25'"
                " WHERE app_contact_id = 10354352 AND hektor_annonce_id = '61730'")

    print("3. le registre des mandats")
    jacquier_apres = mandants_de(con, "61730")
    total_apres = sum(len(v) for v in charger_mandants_du_registre_des_liens(con).values())
    ok(not any("JACQUIER" in x.upper() for x in jacquier_apres),
       f"JACQUIER n'est plus mandant de 61730 ({jacquier_apres})")
    ok(len(jacquier_apres) == len(jacquier_avant) - 1, "les vendeurs de 61730 sont tous restes")
    ok(0 < total_avant - total_apres <= n, f"mandants retires du registre : {total_avant - total_apres} (<= {n})")

    print("4. le push nommerait les deux colonnes")
    ok(set(L.COLONNES_ACHETEUR) <= set(L.colonnes_poussees()), "colonnes poussees, interrupteur allume")
    ligne = next(l for l in L.lignes_a_pousser(con)
                 if l["app_contact_id"] == 10354352 and str(l["hektor_annonce_id"]) == "61730")
    ok(ligne.get("origine") == "vente", "la ligne du temoin part avec origine = vente")

    print("5. interrupteur ETEINT : le retour arriere")
    interrupteur(False)
    bilan = nuit(con)
    reste = con.execute("SELECT COUNT(*) FROM app_relation WHERE origine IS NOT NULL").fetchone()[0]
    ok(reste == 0 and bilan.get("acheteur_remis_a_vide") == n, f"tout remis a vide ({bilan.get('acheteur_remis_a_vide')})")
    ok(set(L.COLONNES_ACHETEUR) <= set(L.colonnes_poussees()), "la nuit ou l'on eteint, le vide PART chez Supabase")
    nuit(con)
    ok(not (set(L.COLONNES_ACHETEUR) & set(L.colonnes_poussees())), "la nuit d'apres, les colonnes ne partent plus")
    ok(any("JACQUIER" in x.upper() for x in mandants_de(con, "61730")), "le registre des mandats revient a l'ancien calcul")

    if args.types:
        print("6. la nuit des contacts (types) -- lit data/hektor.sqlite en LECTURE")
        from phase2.contacts import build_contacts_layer as B
        hk = sqlite3.connect(f"file:{ROOT / 'data' / 'hektor.sqlite'}?mode=ro", uri=True, timeout=60)
        hk.row_factory = sqlite3.Row
        B.charger_identites_app(con)
        interrupteur(False)
        _, roles_off = B.load_relations(hk, con)
        interrupteur(True)
        _, roles_on = B.load_relations(hk, con)
        perdent = sorted(c for c in roles_off if "mandant" in roles_off[c] and "mandant" not in roles_on.get(c, set()))
        gagnent = sorted(c for c in roles_on if "mandant" in roles_on[c] and "mandant" not in roles_off.get(c, set()))
        print(f"     contacts qui ne sont plus « mandant » : {len(perdent)} ; qui le deviennent : {len(gagnent)}")
        ok(len(gagnent) == 0, "personne ne DEVIENT mandant")
        ok(0 < len(perdent) <= 113, "des acheteurs ne sont plus mandants (<= 113)")
        ok("10354352" in perdent and "proprietaire" in roles_on["10354352"]
           and any(r.startswith("acquereur") for r in roles_on["10354352"]),
           f"JACQUIER : {sorted(roles_on.get('10354352', []))} -> Acheteur + Proprietaire")

    con.commit()
    con.close()
    print()
    print("ECHECS :", len(ECHECS))
    return 1 if ECHECS else 0


if __name__ == "__main__":
    raise SystemExit(main())
