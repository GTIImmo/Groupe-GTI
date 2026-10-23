#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑧ défaut 6 — UN CONTACT NÉ DANS L'APP GARDE-T-IL SON NUMÉRO ?            23/10/2026

On fait tourner le VRAI script du registre (phase2/identite/registre_contacts.py) sur des
bases jetables, et on lit le résultat comme la nuit le lit : la table de correspondance de
affaire_ledger.py (mêmes colonnes, même ordre) et la VRAIE fonction du build.

LE DÉFAUT (nuit du 22-23/10) : la couche porte 20000008 / cible 605946 ; le registre
inscrivait (10650807, '20000008', cible VIDE) -> deux numéros à nous, la nuit des
transactions ne trouve plus 605946, et pousser_numeros_contact recopie 10650807 chez
Supabase (fait pour 20000007 le 22/10).

⚠ LA PREUVE D'ABORD : l'ancien script (épinglé, pas HEAD) doit REPRODUIRE le défaut.
N'ÉCRIT RIEN dans la vraie base, et le vérifie à la fin.

    python -I phase2/checks/test_adoption_contact_ne_dans_app.py
    sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RACINE = Path(__file__).resolve().parents[2]
SCRIPT = RACINE / "phase2" / "identite" / "registre_contacts.py"
VRAIE_BASE = RACINE / "phase2" / "phase2.sqlite"
VERSION_AVANT = "c92003f"   # le dernier commit SANS l'adoption -- ne pas remplacer par HEAD
sys.path.insert(0, str(RACINE / "phase2" / "contacts"))
import build_contacts_layer as build  # noqa: E402

echecs: list[str] = []


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if ok else 'ECHEC '} {nom}{'' if ok else ' -- ' + str(detail)}")
    if not ok:
        echecs.append(nom)


_reel = sqlite3.connect(f"file:{VRAIE_BASE.as_posix()}?mode=ro", uri=True)
DDL_REGISTRE = _reel.execute("SELECT sql FROM sqlite_master WHERE name='app_contact'").fetchone()[0]
DDL_RECHERCHES = _reel.execute("SELECT sql FROM sqlite_master WHERE name='app_search_registry'").fetchone()[0]
REEL_AVANT = _reel.execute("SELECT count(*), max(app_contact_id), "
                           "sum(app_contact_id), group_concat(hektor_target_id) FROM app_contact "
                           "WHERE CAST(hektor_contact_id AS INTEGER) >= 20000000").fetchone()
REEL_TOTAL_AVANT = _reel.execute("SELECT count(*), max(app_contact_id) FROM app_contact").fetchone()
_reel.close()
DOSSIER = Path(tempfile.mkdtemp(prefix="adoption_contact_"))

ANCIENS = [(10000001, "10000001", "1"), (10000002, "10000002", "2")]
COUCHE_ANCIENNE = [("10000001", "1"), ("10000002", "2")]


def base_jetable(nom: str, registre: list[tuple], couche: list[tuple]) -> Path:
    chemin = DOSSIER / f"{nom}.sqlite"
    c = sqlite3.connect(chemin)
    c.execute(DDL_REGISTRE)
    c.execute("CREATE INDEX idx_app_contact_target ON app_contact(hektor_target_id)")
    c.execute(DDL_RECHERCHES)
    c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT PRIMARY KEY, hektor_target_id TEXT)")
    c.executemany("INSERT INTO app_contact (app_contact_id, hektor_contact_id, hektor_target_id) VALUES (?,?,?)", registre)
    c.executemany("INSERT INTO app_contact_current VALUES (?,?)", couche)
    c.commit(); c.close()
    return chemin


def poser_couche(chemin: Path, couche: list[tuple]) -> None:
    c = sqlite3.connect(chemin)
    c.execute("DELETE FROM app_contact_current")
    c.executemany("INSERT INTO app_contact_current VALUES (?,?)", couche)
    c.commit(); c.close()


def lancer(script: Path, chemin: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(script), "--base", str(chemin)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def lignes(chemin: Path, cle: str | None = None) -> list[tuple]:
    c = sqlite3.connect(chemin)
    try:
        q = "SELECT app_contact_id, hektor_contact_id, hektor_target_id FROM app_contact"
        if cle is None:
            return c.execute(q + " ORDER BY app_contact_id").fetchall()
        return c.execute(q + " WHERE hektor_contact_id = ? OR hektor_target_id = ?", (cle, cle)).fetchall()
    finally:
        c.close()


def lien_de_nuit(chemin: Path, numero_hektor: str):
    """La table de correspondance de affaire_ledger.py (l. ~756), à l'identique."""
    c = sqlite3.connect(chemin)
    try:
        table: dict[str, int] = {}
        for h, cible, a in c.execute("SELECT hektor_contact_id, hektor_target_id, app_contact_id "
                                     "FROM app_contact WHERE app_contact_id IS NOT NULL"):
            if h is not None and str(h).strip():
                table[str(h).strip()] = int(a)
            if cible is not None and str(cible).strip():
                table[str(cible).strip()] = int(a)
        return table.get(numero_hektor)
    finally:
        c.close()


def traduction(chemin: Path, numero: str) -> str:
    c = sqlite3.connect(chemin)
    try:
        build._IDENTITE_APP.clear(); build._NUMERO_MIROIR.clear()
        build.charger_identites_app(c)
        return build.identite_app(numero)
    finally:
        c.close()


ESSAI = ("20000008", "605946")

# ── (0) LA PREUVE : l'ancien script reproduit le défaut ─────────────────────
source_avant = subprocess.run(["git", "show", f"{VERSION_AVANT}:phase2/identite/registre_contacts.py"],
                              cwd=RACINE, capture_output=True, text=True, encoding="utf-8").stdout
if "--base" not in source_avant or "adopter_les_nes_dans_l_app" in source_avant:
    print("⛔ l'ancien script n'est pas celui attendu -- on ne mesure pas.")
    sys.exit(2)
ancien = DOSSIER / "registre_avant.py"
ancien.write_text(source_avant, encoding="utf-8")
p0 = base_jetable("preuve", ANCIENS, COUCHE_ANCIENNE + [ESSAI])
code, sortie = lancer(ancien, p0)
l0 = lignes(p0, "20000008")
controle("(0) PREUVE : l'ancien script donne un AUTRE numéro à 20000008, sans cible",
         len(l0) == 1 and l0[0][0] != 20000008 and l0[0][2] is None, f"{l0} / {sortie[-200:]}")
controle("(0) PREUVE : ... donc la nuit ne relie plus 605946", lien_de_nuit(p0, "605946") is None,
         lien_de_nuit(p0, "605946"))

# ── (1) le nouveau : adopté sous SON numéro, avec sa cible ──────────────────
p = base_jetable("nuit1", ANCIENS, COUCHE_ANCIENNE + [ESSAI, ("605600", None)])
c = sqlite3.connect(p)
c.execute("INSERT INTO app_search_registry (app_search_id, hektor_contact_id, search_index, contact_search_key) "
          "VALUES (77, '20000008', 0, 'cle-fige')")
c.commit(); c.close()
code, sortie = lancer(SCRIPT, p)
l1 = lignes(p, "20000008")
controle("(1) le registre se dit à jour", code == 0 and "REGISTRE A JOUR" in sortie, sortie[-400:])
controle("(1) 20000008 est ADOPTÉ : app_contact_id = 20000008, cible 605946",
         l1 == [(20000008, "20000008", "605946")], l1)
controle("(1) la sortie le dit (1 adopté)", "1 adopte(s)" in sortie, sortie[-400:])
controle("(1) la nuit des transactions relie 605946 -> 20000008", lien_de_nuit(p, "605946") == 20000008,
         lien_de_nuit(p, "605946"))
controle("(1) le build traduit 605946 -> 20000008", traduction(p, "605946") == "20000008", traduction(p, "605946"))
c = sqlite3.connect(p)
rech = c.execute("SELECT app_contact_id FROM app_search_registry WHERE app_search_id = 77").fetchone()[0]
c.close()
controle("(1) sa recherche reçoit 20000008", rech == 20000008, rech)
hk = [r for r in lignes(p) if r[2] == "605600"]
controle("(1) TÉMOIN : un contact venu de Hektor suit le chemin d'avant (numéro 10 M tiré, cible gardée)",
         len(hk) == 1 and 10000000 <= hk[0][0] < 20000000 and hk[0][1] == str(hk[0][0]), hk)
controle("(1) aucun numéro tiré dans la plage de l'app",
         all(r[0] < 20000000 or r[0] == int(r[1]) for r in lignes(p)), lignes(p))

# ── (2) rejouer : rien de neuf ──────────────────────────────────────────────
avant = lignes(p)
code, sortie = lancer(SCRIPT, p)
controle("(2) rejouer : aucune ligne neuve, aucune adoption", lignes(p) == avant and "adopte(s)" not in sortie,
         sortie[-300:])

# ── (3) adopté AVANT que Hektor réponde, puis la cible arrive ──────────────
p3 = base_jetable("cible_tardive", ANCIENS, COUCHE_ANCIENNE + [("20000010", None)])
code, _ = lancer(SCRIPT, p3)
controle("(3) nuit 1 : adopté sans cible", lignes(p3, "20000010") == [(20000010, "20000010", None)],
         lignes(p3, "20000010"))
poser_couche(p3, COUCHE_ANCIENNE + [("20000010", "605999")])
code, sortie = lancer(SCRIPT, p3)
controle("(3) nuit 2 : la cible 605999 se pose, sans ligne neuve",
         lignes(p3, "20000010") == [(20000010, "20000010", "605999")] and len(lignes(p3)) == 3,
         f"{lignes(p3)} / {sortie[-200:]}")

# ── (4) la cible est déjà portée par une autre fiche : on ne la vole pas ────
p4 = base_jetable("cible_prise", ANCIENS + [(10650900, "10650900", "605946")], COUCHE_ANCIENNE + [("10650900", "605946"), ESSAI])
code, sortie = lancer(SCRIPT, p4)
controle("(4) adopté, mais la cible déjà prise n'est PAS recopiée",
         lignes(p4, "20000008") == [(20000008, "20000008", None)] and code == 0, f"{lignes(p4, '20000008')} / {sortie[-200:]}")

# ── (5) une ligne parasite d'avant le 23/10 : signalée, pas de 3e numéro, pas d'arrêt ──
p5 = base_jetable("parasite", ANCIENS + [(10650807, "20000008", None)], COUCHE_ANCIENNE + [ESSAI])
code, sortie = lancer(SCRIPT, p5)
controle("(5) la nuit ne s'arrête pas (code 0)", code == 0, sortie[-300:])
controle("(5) elle signale le contact à DEUX numéros", "DEUX numeros" in sortie, sortie[-300:])
controle("(5) aucun troisième numéro", lignes(p5, "20000008") == [(10650807, "20000008", None)], lignes(p5, "20000008"))

# ── (6) LE GARDE-FOU : une régression qui retirerait l'adoption est ARRÊTÉE ──
mutant = DOSSIER / "registre_sans_adoption.py"
texte = SCRIPT.read_text(encoding="utf-8")
cible_mut = "adoptes, cibles_adoptes = adopter_les_nes_dans_l_app(conn)"
if texte.count(cible_mut) != 1:
    controle("(6) mutant fabricable", False, "ligne d'adoption introuvable")
else:
    mutant.write_text(texte.replace(cible_mut, "adoptes, cibles_adoptes = 0, 0"), encoding="utf-8")
    p6 = base_jetable("garde", ANCIENS, COUCHE_ANCIENNE + [ESSAI])
    avant6 = lignes(p6)
    code, sortie = lancer(mutant, p6)
    controle("(6) GARDE-FOU : sans adoption, le passage s'ARRÊTE (code 5)",
             code == 5 and "SECOND numero" in sortie, f"{code} / {sortie[-300:]}")
    controle("(6) ... et n'écrit RIEN", lignes(p6) == avant6, lignes(p6))

# ── (7) la vraie base n'a pas bougé ────────────────────────────────────────
_reel = sqlite3.connect(f"file:{VRAIE_BASE.as_posix()}?mode=ro", uri=True)
REEL_APRES = _reel.execute("SELECT count(*), max(app_contact_id), "
                           "sum(app_contact_id), group_concat(hektor_target_id) FROM app_contact "
                           "WHERE CAST(hektor_contact_id AS INTEGER) >= 20000000").fetchone()
REEL_TOTAL_APRES = _reel.execute("SELECT count(*), max(app_contact_id) FROM app_contact").fetchone()
_reel.close()
controle("(7) la vraie base n'a pas bougé", REEL_AVANT == REEL_APRES and REEL_TOTAL_AVANT == REEL_TOTAL_APRES,
         f"{REEL_AVANT} -> {REEL_APRES} / {REEL_TOTAL_AVANT} -> {REEL_TOTAL_APRES}")

print()
print(f"⛔ {len(echecs)} contrôle(s) en échec." if echecs else "✅ Tous les contrôles sont verts.")
sys.exit(1 if echecs else 0)
