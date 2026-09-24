#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.9-a — UNE ANNONCE NEE DANS L'APP NE RECOIT PAS DE SECOND NUMERO.
                                                                  24/09/2026

On fait tourner le VRAI bootstrap (bootstrap_phase2.bootstrap_app_dossier, le
meme SQL que chaque nuit) sur des bases jetables, avec le VRAI schema de
app_dossier (relu dans phase2.sqlite, en lecture seule).

⚠ LA PREUVE D'ABORD (regle du 23/09 : un controle qu'on n'a pas vu echouer sur
  le defaut n'est pas un controle). Le cas (1) joue le bootstrap SANS l'etape :
  il DOIT fabriquer le second numero. S'il ne le fabrique pas, ce test ne
  prouve rien, et il le dit.

N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT RIEN dans les vraies bases.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2"))
sys.path.insert(0, str(RACINE / "phase2" / "identite"))
import bootstrap_phase2  # noqa: E402
import descendre_correspondance_annonces as c9a  # noqa: E402

echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


# Le vrai schema de app_dossier, relu tel quel (AUTOINCREMENT, UNIQUE, absent_depuis).
_reel = sqlite3.connect(f"file:{(RACINE / 'phase2' / 'phase2.sqlite').as_posix()}?mode=ro", uri=True)
DDL_APP_DOSSIER = _reel.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='app_dossier'").fetchone()[0]
_reel.close()

DOSSIER = Path(tempfile.mkdtemp(prefix="c9a_"))


def miroir(presents: list[int]) -> Path:
    chemin = DOSSIER / f"miroir_{len(list(DOSSIER.iterdir()))}.sqlite"
    m = sqlite3.connect(chemin)
    m.executescript("""
        CREATE TABLE case_dossier_source (
            hektor_annonce_id TEXT, annonce_source_status TEXT, mandat_id TEXT,
            no_mandat TEXT, no_dossier TEXT, hektor_negociateur_id TEXT,
            negociateur_prenom TEXT, negociateur_nom TEXT);
        CREATE TABLE hektor_mandat (
            hektor_annonce_id TEXT, hektor_mandat_id TEXT, numero TEXT, synced_at TEXT);
    """)
    m.executemany("INSERT INTO case_dossier_source VALUES (?, 'present', NULL, ?, ?, '7', 'Jo', 'NEGO')",
                  [(str(n), f"M{n}", f"D{n}") for n in presents])
    m.commit()
    m.close()
    return chemin


def serveur(lignes: list[tuple[int, int | None]]) -> sqlite3.Connection:
    chemin = DOSSIER / f"serveur_{len(list(DOSSIER.iterdir()))}.sqlite"
    conn = sqlite3.connect(chemin)
    conn.execute(DDL_APP_DOSSIER)
    conn.executemany("INSERT INTO app_dossier (id, hektor_annonce_id) VALUES (?, ?)", lignes)
    conn.commit()
    return conn


def bootstrap(conn: sqlite3.Connection, chemin_miroir: Path) -> None:
    bootstrap_phase2.HEKTOR_DB = chemin_miroir
    bootstrap_phase2.bootstrap_app_dossier(conn)


def numeros_pour(conn, hektor: int) -> list[int]:
    return [r[0] for r in conn.execute(
        "SELECT id FROM app_dossier WHERE hektor_annonce_id = ? ORDER BY id", (hektor,))]


def presents(chemin_miroir: Path, lignes: list[dict]) -> set[int]:
    m = sqlite3.connect(chemin_miroir)
    try:
        nums = {c9a._entier(l.get("hektor_annonce_id")) for l in lignes} - {None}
        return c9a.presents_dans_le_miroir(m, nums)
    finally:
        m.close()


SUPABASE = [{"app_dossier_id": 10000001, "hektor_annonce_id": 63200}]

# ── (1) LA PREUVE : sans l'etape, le bootstrap fabrique le second numero ─────
m1 = miroir([100, 101, 63200])
s1 = serveur([(1, 100), (2, 101)])
bootstrap(s1, m1)
avant = numeros_pour(s1, 63200)
controle("(1) PREUVE : sans C.9-a, le bootstrap donne a 63200 un numero SERVEUR",
         avant and avant[0] < c9a.PLAGE_ANNONCE_APP and 10000001 not in avant,
         f"obtenu {avant} -- le defaut ne se reproduit pas : ce test ne prouve rien")

# ── (2) AVEC l'etape avant le bootstrap : un seul numero, celui de l'app ─────
m2 = miroir([100, 101, 63200])
s2 = serveur([(1, 100), (2, 101)])
c9a.assurer_garde(s2)
bilan = c9a.adopter(s2, SUPABASE, presents(m2, SUPABASE))
s2.commit()
bootstrap(s2, m2)
controle("(2) avec C.9-a, l'annonce garde SON numero, et un seul",
         numeros_pour(s2, 63200) == [10000001], f"obtenu {numeros_pour(s2, 63200)}")
_ligne = s2.execute("SELECT numero_mandat FROM app_dossier WHERE id=10000001").fetchone()
controle("(2) le bootstrap a complete la ligne adoptee (numero de mandat)",
         _ligne is not None and _ligne[0] == "M63200", f"obtenu {_ligne}")
controle("(2) aucune ligne de trop", s2.execute("SELECT COUNT(*) FROM app_dossier").fetchone()[0] == 3)
controle("(2) le bilan dit 1 adoptee", bilan["adoptees"] == 1 and not bilan["anomalies"], str(bilan))

# ── (3) idempotent ────────────────────────────────────────────────────────
bilan = c9a.adopter(s2, SUPABASE, presents(m2, SUPABASE))
s2.commit()
bootstrap(s2, m2)
controle("(3) rejouer n'ajoute rien", bilan["adoptees"] == 0 and bilan["deja_la"] == 1
         and numeros_pour(s2, 63200) == [10000001], str(bilan))

# ── (4) le compteur : le declencheur tient la plage ───────────────────────
seq = s2.execute("SELECT seq FROM sqlite_sequence WHERE name='app_dossier'").fetchone()[0]
controle("(4) le compteur a bien SAUTE dans la plage (le risque est reel)",
         seq >= c9a.PLAGE_ANNONCE_APP, f"seq={seq}")
try:
    s2.execute("INSERT INTO app_dossier (hektor_annonce_id) VALUES (999)")  # INSERT sans id
    s2.commit()
    controle("(4) un INSERT sans id est REFUSE apres une adoption", False,
             "il est passe : il aurait pris le numero de la prochaine annonce de l'app")
except sqlite3.IntegrityError as err:
    s2.rollback()
    controle("(4) un INSERT sans id est REFUSE apres une adoption", "C.9-a" in str(err), str(err))
try:
    s2.execute("INSERT INTO app_dossier (id, hektor_annonce_id) VALUES (10000009, 998)")
    s2.commit()
    controle("(4) un numero de la plage non adopte est REFUSE", False, "il est passe")
except sqlite3.IntegrityError:
    s2.rollback()
    controle("(4) un numero de la plage non adopte est REFUSE", True)
s4 = serveur([(1, 100)])
c9a.assurer_garde(s4)
s4.execute("INSERT INTO app_dossier (hektor_annonce_id) VALUES (500)")
s4.commit()
controle("(4) AVANT toute adoption, le couloir du serveur n'est pas gene",
         numeros_pour(s4, 500) == [2], f"obtenu {numeros_pour(s4, 500)}")
bootstrap(s4, miroir([100, 500, 600]))
controle("(4) et le bootstrap passe avec le declencheur pose",
         numeros_pour(s4, 600) and numeros_pour(s4, 600)[0] < c9a.PLAGE_ANNONCE_APP)

# ── (5) ce qu'on n'adopte PAS ─────────────────────────────────────────────
m5 = miroir([100])
s5 = serveur([(1, 100)])
c9a.assurer_garde(s5)
lignes5 = [{"app_dossier_id": 10000002, "hektor_annonce_id": None},
           {"app_dossier_id": 10000003, "hektor_annonce_id": 63300}]
bilan = c9a.adopter(s5, lignes5, presents(m5, lignes5))
s5.commit()
controle("(5) Hektor n'a pas repondu : on attend", bilan["attente_hektor"] == 1, str(bilan))
controle("(5) le miroir ne la connait pas : on attend (sinon ligne VIDE poussee)",
         bilan["attente_miroir"] == 1, str(bilan))
controle("(5) et rien n'est entre dans app_dossier",
         s5.execute("SELECT COUNT(*) FROM app_dossier").fetchone()[0] == 1)

# ── (6) deux numeros deja la : signale, JAMAIS touche ─────────────────────
bilan = c9a.adopter(s1, SUPABASE, presents(m1, SUPABASE))
s1.commit()
controle("(6) un doublon deja fabrique est SIGNALE", len(bilan["anomalies"]) == 1, str(bilan))
controle("(6) et on n'y touche pas", numeros_pour(s1, 63200) == avant, f"{numeros_pour(s1, 63200)}")

# ── (7) completer, jamais remplacer ───────────────────────────────────────
m7 = miroir([100, 63500])
s7 = serveur([(1, 100)])
c9a.assurer_garde(s7)
s7.execute("INSERT INTO app_dossier_adoption (app_dossier_id, hektor_annonce_id) VALUES (10000005, 0)")
s7.execute("INSERT INTO app_dossier (id, hektor_annonce_id) VALUES (10000005, NULL)")
s7.commit()
lignes7 = [{"app_dossier_id": 10000005, "hektor_annonce_id": 63500}]
bilan = c9a.adopter(s7, lignes7, presents(m7, lignes7))
s7.commit()
controle("(7) un numero Hektor manquant est COMPLETE", numeros_pour(s7, 63500) == [10000005], str(bilan))
lignes7b = [{"app_dossier_id": 10000005, "hektor_annonce_id": 63600}]
bilan = c9a.adopter(s7, lignes7b, {63600})
controle("(7) un numero Hektor present n'est JAMAIS remplace",
         numeros_pour(s7, 63500) == [10000005] and len(bilan["anomalies"]) == 1, str(bilan))

# ── (8) la forme ──────────────────────────────────────────────────────────
controle("(8) deux numeros d'app pour une annonce Hektor : refuse",
         bool(c9a.verifier_la_forme([{"app_dossier_id": 10000001, "hektor_annonce_id": 5},
                                      {"app_dossier_id": 10000002, "hektor_annonce_id": 5}])))
controle("(8) un numero Hektor dans notre plage : refuse",
         bool(c9a.verifier_la_forme([{"app_dossier_id": 10000001, "hektor_annonce_id": 10000004}])))
controle("(8) une liste saine passe",
         not c9a.verifier_la_forme(SUPABASE + [{"app_dossier_id": 10000002, "hektor_annonce_id": None}]))

# ── (9) le dry-run n'ecrit RIEN ───────────────────────────────────────────
m9 = miroir([63200])
s9 = serveur([])
bilan = c9a.adopter(s9, SUPABASE, presents(m9, SUPABASE), dry=True)
controle("(9) le dry-run compte sans ecrire",
         bilan["adoptees"] == 1 and s9.execute("SELECT COUNT(*) FROM app_dossier").fetchone()[0] == 0)

for c in (s1, s2, s4, s5, s7, s9):
    c.close()
print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Une annonce nee dans l'app garde son numero -- et la plage de l'app est gardee.")
