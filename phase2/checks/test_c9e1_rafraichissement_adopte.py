#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.9-e (e1) — LE RAFRAICHISSEMENT N'EFFACE PLUS LE NUMERO D'UNE ANNONCE NEE DANS L'APP.
                                                                  24/09/2026

On fait tourner les VRAIES fonctions de push_single_annonce_to_supabase.py :
    sync_target_app_dossier        (fabrique ou retrouve le numero serveur)
    reconcile_annonce_dossiers     (efface les « fantomes » d'une annonce)
sur une base jetable, avec le vrai schema de app_dossier, et un FAUX Supabase qui
ENREGISTRE ce qu'on lui demande d'effacer -- rien ne part nulle part.

⚠ LA PREUVE D'ABORD : sans e1, le cas (1) DOIT effacer 10 000 001. S'il ne l'efface
  pas, ce test ne prouve rien, et il le dit.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from phase2.sync import push_single_annonce_to_supabase as ps  # noqa: E402

echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


_reel = sqlite3.connect(f"file:{(RACINE / 'phase2' / 'phase2.sqlite').as_posix()}?mode=ro", uri=True)
DDL = _reel.execute("SELECT sql FROM sqlite_master WHERE name='app_dossier'").fetchone()[0]
_reel.close()
DOSSIER = Path(tempfile.mkdtemp(prefix="c9e1_"))


class FauxSupabase:
    """Tient app_dossier_current en memoire ; enregistre les suppressions et re-pointages."""

    def __init__(self, lignes: list[tuple[int, int | None]], panne: bool = False):
        self.lignes = [{"app_dossier_id": a, "hektor_annonce_id": h} for a, h in lignes]
        self.effaces: list[int] = []
        self.repointes: list[tuple[str, int]] = []
        self.panne = panne

    def _request(self, *, method, path, query=None, payload=None, prefer=None):
        if self.panne:
            raise OSError("Supabase muet (simule)")
        if method == "GET" and path == "app_dossier_current":
            q = query or {}
            h = int(q["hektor_annonce_id"].split(".", 1)[1])
            res = [l for l in self.lignes if l["hektor_annonce_id"] == h]
            if "app_dossier_id" in q:
                seuil = int(q["app_dossier_id"].split(".", 1)[1])
                res = [l for l in res if l["app_dossier_id"] >= seuil]
            return res
        if method == "PATCH":
            self.repointes.append((path, int(query["app_dossier_id"].split(".", 1)[1])))
            return []
        return []

    def delete_rows_by_ids(self, *, path, column, ids):
        if path == "app_dossier_current":
            self.effaces.extend(int(i) for i in ids)
            self.lignes = [l for l in self.lignes if l["app_dossier_id"] not in ids]


def miroir(presents: list[int]) -> Path:
    chemin = DOSSIER / f"miroir_{len(list(DOSSIER.iterdir()))}.sqlite"
    m = sqlite3.connect(chemin)
    m.executescript("""
        CREATE TABLE case_dossier_source (hektor_annonce_id TEXT, annonce_source_status TEXT,
            mandat_id TEXT, no_mandat TEXT, no_dossier TEXT, hektor_negociateur_id TEXT,
            negociateur_prenom TEXT, negociateur_nom TEXT);
        CREATE TABLE hektor_mandat (hektor_annonce_id TEXT, hektor_mandat_id TEXT, numero TEXT, synced_at TEXT);
    """)
    m.executemany("INSERT INTO case_dossier_source VALUES (?, 'present', NULL, ?, ?, '7', 'Jo', 'NEGO')",
                  [(str(n), f"M{n}", f"D{n}") for n in presents])
    m.commit(); m.close()
    return chemin


def serveur(lignes) -> sqlite3.Connection:
    c = sqlite3.connect(DOSSIER / f"serveur_{len(list(DOSSIER.iterdir()))}.sqlite")
    c.execute(DDL)
    c.executemany("INSERT INTO app_dossier (id, hektor_annonce_id) VALUES (?, ?)", lignes)
    c.commit()
    return c


def rafraichir(con, supa, m: Path, hektor: str, avec_e1: bool) -> int:
    """Le chemin de main(), reduit a ce qui decide du numero."""
    ps.HEKTOR_DB = m
    if avec_e1:
        ps.adopter_numero_app_si_existe(supa, con, hektor, miroir=m)
    app_id = ps.sync_target_app_dossier(con, hektor)
    supa.lignes = [l for l in supa.lignes if l["app_dossier_id"] != app_id] + \
                  [{"app_dossier_id": app_id, "hektor_annonce_id": int(hektor)}]   # le push de la fiche
    ps.reconcile_annonce_dossiers(supa, hektor, app_id)
    return app_id


# ── (1) LA PREUVE : sans e1, D8 se produit ────────────────────────────────
m1 = miroir([100, 63200]); s1 = serveur([(1, 100)])
supa1 = FauxSupabase([(1, 100), (10000001, 63200)])
garde = rafraichir(s1, supa1, m1, "63200", avec_e1=False)
controle("(1) PREUVE : sans e1, le rafraichissement fabrique un numero serveur",
         garde < ps.PLAGE_ANNONCE_APP, f"garde={garde}")
controle("(1) PREUVE : ... et EFFACE 10 000 001 comme un fantome",
         10000001 in supa1.effaces, f"effaces={supa1.effaces} -- D8 ne se reproduit pas : ce test ne prouve rien")

# ── (2) avec e1 : le numero de l'app est garde, rien n'est efface ─────────
m2 = miroir([100, 63200]); s2 = serveur([(1, 100)])
supa2 = FauxSupabase([(1, 100), (10000001, 63200)])
garde = rafraichir(s2, supa2, m2, "63200", avec_e1=True)
controle("(2) avec e1, le rafraichissement GARDE 10 000 001", garde == 10000001, f"garde={garde}")
controle("(2) rien n'est efface, rien n'est re-pointe",
         supa2.effaces == [] and supa2.repointes == [], f"{supa2.effaces} {supa2.repointes[:3]}")
controle("(2) le serveur n'a qu'une ligne pour 63200",
         [r[0] for r in s2.execute("SELECT id FROM app_dossier WHERE hektor_annonce_id=63200")] == [10000001])

# ── (3) une annonce nee chez Hektor : rien ne change ──────────────────────
m3 = miroir([100, 500]); s3 = serveur([(1, 100)])
supa3 = FauxSupabase([(1, 100)])
garde = rafraichir(s3, supa3, m3, "500", avec_e1=True)
controle("(3) une annonce ordinaire recoit son numero serveur comme avant",
         garde == 2 and supa3.effaces == [], f"garde={garde} effaces={supa3.effaces}")

# ── (4) deux numeros deja la : on s'ARRETE, on n'efface rien ──────────────
m4 = miroir([100, 63200]); s4 = serveur([(1, 100), (7, 63200)])
supa4 = FauxSupabase([(1, 100), (7, 63200), (10000001, 63200)])
try:
    rafraichir(s4, supa4, m4, "63200", avec_e1=True)
    controle("(4) deux numeros deja la : le rafraichissement S'ARRETE", False, "il a continue")
except RuntimeError as err:
    controle("(4) deux numeros deja la : le rafraichissement S'ARRETE", "DEUX NUMEROS" in str(err), str(err))
controle("(4) ... et n'a rien efface", supa4.effaces == [], str(supa4.effaces))

# ── (5) Supabase muet : on s'ARRETE, on ne fabrique pas a l'aveugle ───────
m5 = miroir([63200]); s5 = serveur([])
try:
    ps.adopter_numero_app_si_existe(FauxSupabase([], panne=True), s5, "63200", miroir=m5)
    controle("(5) Supabase muet : arret", False, "il a continue")
except OSError:
    controle("(5) Supabase muet : arret", True)
controle("(5) ... et rien n'est entre sur le serveur", s5.execute("SELECT COUNT(*) FROM app_dossier").fetchone()[0] == 0)

# ── (6) Hektor a numerote mais le miroir ne l'a pas encore tire : on attend ─
m6 = miroir([100]); s6 = serveur([(1, 100)])
bilan = ps.adopter_numero_app_si_existe(FauxSupabase([(10000001, 63200)]), s6, "63200", miroir=m6)
controle("(6) miroir en retard : on n'adopte pas (sinon ligne VIDE poussee)",
         bilan.get("attente_miroir") == 1 and s6.execute("SELECT COUNT(*) FROM app_dossier").fetchone()[0] == 1,
         str(bilan))

for c in (s1, s2, s3, s4, s5, s6):
    c.close()
print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Le rafraichissement garde le numero de l'app -- et s'arrete plutot que d'en effacer un.")
