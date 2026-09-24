#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4-c-bis — UN CONTACT CREE CHEZ HEKTOR APRES LA BASCULE RECOIT-IL SON IDENTITE ?
                                                                  24/09/2026

On fait tourner le VRAI script du registre (phase2/identite/registre_contacts.py)
sur une base jetable, nuit apres nuit, et la VRAIE fonction du build qui lit la
correspondance (build_contacts_layer.charger_identites_app).

LES NUITS D'UN CONTACT NEUF
    nuit 1  il arrive sous son numero de Hektor (le build tourne avant le registre)
            -> le registre lui donne son identite, DANS LA BONNE COLONNE
            -> le build de la nuit 2 saura le traduire
    nuit 2  il arrive sous son identite -> reconnu, PAS de second numero
    nuit 3  il disparait sous ses deux numeros -> marque absent
    nuit 4  il revient sous son numero Hektor -> la marque tombe, pas de ligne neuve

⚠ LA PREUVE D'ABORD : l'ancien script (epingle, pas HEAD) doit REPRODUIRE le defaut
  -- identite rangee a cote, le build ne sait pas traduire.

N'ECRIT RIEN dans la vraie base, et le verifie a la fin.
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SCRIPT = RACINE / "phase2" / "identite" / "registre_contacts.py"
VRAIE_BASE = RACINE / "phase2" / "phase2.sqlite"
VERSION_AVANT = "d09d95b"   # le dernier commit SANS le correctif -- ne pas remplacer par HEAD
sys.path.insert(0, str(RACINE / "phase2" / "contacts"))
import build_contacts_layer as build  # noqa: E402

echecs: list[str] = []


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if ok else 'ECHEC '} {nom}{'' if ok else ' -- ' + detail}")
    if not ok:
        echecs.append(nom)


_reel = sqlite3.connect(f"file:{VRAIE_BASE.as_posix()}?mode=ro", uri=True)
DDL_REGISTRE = _reel.execute("SELECT sql FROM sqlite_master WHERE name='app_contact'").fetchone()[0]
DDL_RECHERCHES = _reel.execute("SELECT sql FROM sqlite_master WHERE name='app_search_registry'").fetchone()[0]
REEL_AVANT = _reel.execute("SELECT count(*), max(app_contact_id) FROM app_contact").fetchone()
_reel.close()
DOSSIER = Path(tempfile.mkdtemp(prefix="l4cbis_"))


def base_jetable(nom: str, registre: list[tuple], couche: list[str]) -> Path:
    chemin = DOSSIER / f"{nom}.sqlite"
    c = sqlite3.connect(chemin)
    c.execute(DDL_REGISTRE)
    c.execute("CREATE INDEX idx_app_contact_target ON app_contact(hektor_target_id)")
    c.execute(DDL_RECHERCHES)
    c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT PRIMARY KEY)")
    c.executemany("INSERT INTO app_contact (app_contact_id, hektor_contact_id, hektor_target_id) VALUES (?,?,?)", registre)
    c.executemany("INSERT INTO app_contact_current VALUES (?)", [(k,) for k in couche])
    c.commit(); c.close()
    return chemin


def couche(chemin: Path, cles: list[str]) -> None:
    c = sqlite3.connect(chemin)
    c.execute("DELETE FROM app_contact_current")
    c.executemany("INSERT INTO app_contact_current VALUES (?)", [(k,) for k in cles])
    c.commit(); c.close()


def lancer(script: Path, chemin: Path, avec_base: bool = True) -> tuple[int, str]:
    args = [sys.executable, str(script)] + (["--base", str(chemin)] if avec_base else [])
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def registre(chemin: Path) -> list[tuple]:
    c = sqlite3.connect(chemin)
    try:
        return c.execute("SELECT app_contact_id, hektor_contact_id, hektor_target_id, absent_depuis "
                         "FROM app_contact ORDER BY app_contact_id").fetchall()
    finally:
        c.close()


def traduction(chemin: Path, numero: str) -> str:
    c = sqlite3.connect(chemin)
    try:
        build.charger_identites_app(c)
        return build.identite_app(numero)
    finally:
        c.close()


ANCIENS = [(10000001, "10000001", "1"), (10000002, "10000002", "2")]
COUCHE_ANCIENNE = ["10000001", "10000002"]

# ── (0) LA PREUVE : l'ancien script reproduit le defaut ─────────────────────
source_avant = subprocess.run(["git", "show", f"{VERSION_AVANT}:phase2/identite/registre_contacts.py"],
                              cwd=RACINE, capture_output=True, text=True, encoding="utf-8").stdout
ligne_base = 'BASE = Path(r"C:\\Hektor\\Projet\\phase2\\phase2.sqlite")'
p0 = base_jetable("preuve", ANCIENS, COUCHE_ANCIENNE + ["605600"])
if source_avant.count(ligne_base) != 1:
    controle("(0) PREUVE : ancien script lisible et redirigeable", False,
             "chemin de base introuvable -- on ne le lance PAS (il viserait la vraie base)")
else:
    ancien = DOSSIER / "registre_avant.py"
    ancien.write_text(source_avant.replace(ligne_base, f'BASE = Path(r"{p0}")'), encoding="utf-8")
    assert str(VRAIE_BASE) not in ancien.read_text(encoding="utf-8")
    code, sortie = lancer(ancien, p0, avec_base=False)
    ligne = [r for r in registre(p0) if r[2] == "605600" or r[1] == "605600"]
    controle("(0) PREUVE : l'ancien script range le n° Hektor dans la colonne d'identite",
             bool(ligne) and ligne[0][1] == "605600", f"{ligne} / {sortie[-200:]}")
    controle("(0) PREUVE : ... donc le build ne sait pas le traduire",
             traduction(p0, "605600") == "605600", traduction(p0, "605600"))

# ── (1) nuit 1 : le contact neuf arrive sous son numero de Hektor ───────────
p = base_jetable("nuits", ANCIENS, COUCHE_ANCIENNE + ["605600"])
c = sqlite3.connect(p)
c.execute("INSERT INTO app_search_registry (app_search_id, hektor_contact_id, search_index, contact_search_key) "
          "VALUES (99, '605600', 0, 'cle-fige')")
c.commit(); c.close()
code, sortie = lancer(SCRIPT, p)
reg = registre(p)
neuf = [r for r in reg if r[2] == "605600"]
controle("(1) nuit 1 : le registre se dit a jour", code == 0 and "REGISTRE A JOUR" in sortie, sortie[-300:])
controle("(1) nuit 1 : l'identite est dans hektor_contact_id, Hektor dans la cible",
         len(neuf) == 1 and neuf[0][1] == str(neuf[0][0]) and neuf[0][0] >= 10000000, str(neuf))
controle("(1) nuit 1 : il n'est pas marque absent", neuf and neuf[0][3] is None, str(neuf))
controle("(1) nuit 1 : le build saura le traduire", traduction(p, "605600") == str(neuf[0][0]) if neuf else False)
c = sqlite3.connect(p)
rech = c.execute("SELECT app_contact_id FROM app_search_registry WHERE app_search_id = 99").fetchone()[0]
c.close()
controle("(1) nuit 1 : sa recherche recoit le numero du contact", neuf and rech == neuf[0][0], str(rech))
identite = str(neuf[0][0]) if neuf else "?"

# ── (2) nuit 2 : il arrive sous son identite -> PAS de second numero ────────
couche(p, COUCHE_ANCIENNE + [identite])
code, sortie = lancer(SCRIPT, p)
reg2 = registre(p)
controle("(2) nuit 2 : reconnu sous son identite, AUCUNE ligne neuve", len(reg2) == len(reg), f"{len(reg)} -> {len(reg2)}")
controle("(2) nuit 2 : toujours pas absent", all(r[3] is None for r in reg2), str(reg2))
controle("(2) nuit 2 : registre a jour", code == 0, sortie[-200:])

# ── (3) nuit 3 : disparu sous ses deux numeros -> marque absent ────────────
couche(p, COUCHE_ANCIENNE)
lancer(SCRIPT, p)
ligne = [r for r in registre(p) if r[1] == identite]
controle("(3) nuit 3 : disparu sous ses deux numeros -> marque absent", ligne and ligne[0][3] is not None, str(ligne))

# ── (4) nuit 4 : il revient sous son numero Hektor -> marque levee ─────────
couche(p, COUCHE_ANCIENNE + ["605600"])
lancer(SCRIPT, p)
reg4 = registre(p)
ligne = [r for r in reg4 if r[1] == identite]
controle("(4) nuit 4 : revenu sous son n° Hektor -> la marque tombe", ligne and ligne[0][3] is None, str(ligne))
controle("(4) nuit 4 : ... sans ligne neuve", len(reg4) == len(reg), f"{len(reg)} -> {len(reg4)}")

# ── (5) la reparation des lignes posees par l'ancien code ──────────────────
p5 = base_jetable("reparation", ANCIENS + [(10000003, "605700", "605700")], COUCHE_ANCIENNE + ["605700"])
code, sortie = lancer(SCRIPT, p5)
ligne = [r for r in registre(p5) if r[0] == 10000003]
controle("(5) une ligne posee par l'ancien code est REPAREE",
         ligne and ligne[0][1] == "10000003" and ligne[0][2] == "605700", str(ligne))
controle("(5) ... et le build sait la traduire", traduction(p5, "605700") == "10000003")
code, sortie = lancer(SCRIPT, p5)
controle("(5) rejouer : plus rien a reparer, aucune ligne neuve",
         "identite remise en place" not in sortie and len(registre(p5)) == 3, sortie[-200:])

# ── (6) la vraie base n'a pas bouge ────────────────────────────────────────
_reel = sqlite3.connect(f"file:{VRAIE_BASE.as_posix()}?mode=ro", uri=True)
REEL_APRES = _reel.execute("SELECT count(*), max(app_contact_id) FROM app_contact").fetchone()
_reel.close()
controle("(6) la vraie base n'a pas bouge", REEL_AVANT == REEL_APRES, f"{REEL_AVANT} -> {REEL_APRES}")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Un contact neuf recoit son identite dans la bonne colonne -- et un seul numero, nuit apres nuit.")
