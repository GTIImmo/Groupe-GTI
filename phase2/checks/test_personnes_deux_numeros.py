#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑧ PIECE 2 -- LES PERSONNES DU REGISTRE DES TRANSACTIONS RECOIVENT NOTRE NUMERO, LA NUIT.   24/10/2026

Etude : notice/ETUDE_NUMEROS_PERSONNES_REGISTRE_TRANSACTIONS_2026-10-24.md (§8 a §11).

CE QU'IL EPROUVE, DANS CET ORDRE
--------------------------------
  ⓵ LA FONCTION seule (`poser_nos_numeros`) : liste, objet seul, texte, inconnu, illisible, vide, « 0 »,
     deja pose, l'ordre et les autres cles gardes.
  ⓶ LE TEMOIN INVERSE, SUR LA VRAIE NUIT : `refresh_ledger` de la version d'AVANT (git HEAD) et celui de
     la version neuve INTERRUPTEUR ETEINT, joues sur deux copies identiques -> les registres rendus doivent
     etre IDENTIQUES a l'octet (hors horodatages du run). C'est le controle qui compte : ce fichier tourne
     chaque nuit des qu'il est enregistre.
  ⓷ ALLUME, sur une troisieme copie : seules `acquereur_json` / `acquereurs_json` changent, et seulement
     par l'AJOUT de `app_contact_id` ; on compte les personnes qui l'ont recu.

⚠ IL N'ECRIT RIEN DE VRAI. Les tables utiles sont recopiees depuis phase2.sqlite ouvert en LECTURE SEULE ;
  le miroir de Hektor (data/hektor.sqlite) est attache en LECTURE SEULE. Tout se passe dans un dossier
  temporaire, efface a la fin.

    python -I phase2/checks/test_personnes_deux_numeros.py
    sortie 0 = vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SYNC = RACINE / "phase2" / "sync"
PHASE2 = RACINE / "phase2" / "phase2.sqlite"
HEKTOR = RACINE / "data" / "hektor.sqlite"
TABLES = ("app_affaire_ledger", "app_affaire_ledger__sb", "app_console_job", "app_contact", "app_dossier")
HORODATAGES = {"first_seen_at", "last_seen_at"}

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8")
    except Exception:                                               # noqa: BLE001
        pass
sys.path.insert(0, str(SYNC))

R: list[tuple[str, bool, str]] = []


def ok(nom: str, vrai: bool, detail: str = "") -> None:
    R.append((nom, bool(vrai), detail))


def charger(nom: str, chemin: Path):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                                    # type: ignore[union-attr]
    return mod


# ── ⓵ LA FONCTION ─────────────────────────────────────────────────────────
def essais_fonction(mod) -> None:
    poser = mod.poser_nos_numeros
    t = {"605976": 20000015, "605227": 10355906, "20000015": 20000015}
    liste = json.dumps([{"id": "605976", "nom": "A", "coordonnees": {"email": "x"}}, {"id": "999", "nom": "B"}])
    txt, n = poser(liste, t)
    v = json.loads(txt)
    ok("liste : la personne connue recoit notre numero, l'inconnue rien",
       n == 1 and v[0]["app_contact_id"] == 20000015 and "app_contact_id" not in v[1], txt)
    ok("liste : id, nom, coordonnees et l'ordre sont gardes",
       v[0]["id"] == "605976" and v[0]["nom"] == "A" and v[0]["coordonnees"] == {"email": "x"} and v[1]["id"] == "999", txt)
    txt, n = poser(json.dumps({"id": "605227", "nom": "N"}), t)
    ok("objet seul : la forme est gardee (un objet, pas une liste)",
       n == 1 and isinstance(json.loads(txt), dict) and json.loads(txt)["app_contact_id"] == 10355906, str(txt))
    brut = json.dumps([{"id": "999"}])
    ok("rien a poser : le texte d'origine a l'octet pres", poser(brut, t) == (brut, 0), "")
    ok("illisible, vide, None : rendus tels quels",
       poser("{pas du json", t) == ("{pas du json", 0) and poser("", t) == ("", 0) and poser(None, t) == (None, 0), "")
    ok("un id « 0 » ou vide ne recoit rien", poser(json.dumps([{"id": "0"}, {"id": ""}]), t)[1] == 0, "")
    deja = json.dumps([{"id": "605976", "app_contact_id": 20000015}])
    ok("deja pose a l'identique : rien a refaire, texte d'origine", poser(deja, t) == (deja, 0), "")
    txt, n = poser(json.dumps([{"id": "20000015"}]), t)
    ok("une personne deja sous NOTRE numero recoit le sien (lui-meme)", n == 1 and json.loads(txt)[0]["app_contact_id"] == 20000015, str(txt))


# ── ⓶ ⓷ LA VRAIE NUIT, SUR DES COPIES ────────────────────────────────────
def fabriquer_copie(dossier: Path, nom: str) -> Path:
    cible = dossier / f"{nom}.sqlite"
    src = sqlite3.connect(f"file:{PHASE2.as_posix()}?mode=ro", uri=True, timeout=30)
    dst = sqlite3.connect(cible)
    for t in TABLES:
        # les tables et leurs index seulement : un declencheur viserait des tables non recopiees
        for (sql,) in src.execute("select sql from sqlite_master where tbl_name=? and sql is not null "
                                  "and type in ('table', 'index') "
                                  "order by case type when 'table' then 0 else 1 end", (t,)):
            dst.execute(sql)
        cols = [r[1] for r in src.execute(f"PRAGMA table_info({t})")]
        marques = ",".join("?" * len(cols))
        dst.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({marques})",
                        src.execute(f"SELECT {','.join(cols)} FROM {t}"))
    dst.commit()
    src.close()
    dst.close()
    return cible


def jouer(mod, base: Path) -> None:
    con = sqlite3.connect(f"file:{base.as_posix()}", uri=True, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("ATTACH DATABASE ? AS hektor", (f"file:{HEKTOR.as_posix()}?mode=ro",))
    mod.refresh_ledger(con, full=True)
    con.commit()
    con.close()


def lignes(base: Path) -> dict[int, dict]:
    con = sqlite3.connect(base)
    con.row_factory = sqlite3.Row
    out = {int(r["app_affaire_id"]): {k: r[k] for k in r.keys() if k not in HORODATAGES}
           for r in con.execute("SELECT * FROM app_affaire_ledger")}
    con.close()
    return out


def personnes(v) -> list:
    """Les deux formes du blob, et la valeur JSON « null » (vue dans le registre)."""
    return [v] if isinstance(v, dict) else (v if isinstance(v, list) else [])


def sans_nos_numeros(brut):
    if not brut:
        return brut
    v = json.loads(brut)
    for p in personnes(v):
        if isinstance(p, dict):
            p.pop("app_contact_id", None)
    return v


def essais_nuit(mod_neuf, dossier: Path) -> None:
    head = dossier / "affaire_ledger_head.py"
    head.write_text(subprocess.run(["git", "show", "HEAD:phase2/sync/affaire_ledger.py"], cwd=RACINE,
                                   capture_output=True, text=True, encoding="utf-8", check=True).stdout,
                    encoding="utf-8")
    mod_head = charger("affaire_ledger_head", head)
    a, b, c = (fabriquer_copie(dossier, n) for n in ("avant", "eteint", "allume"))
    os.environ.pop("APP_AFFAIRE_PERSONNES_DEUX_NUMEROS", None)
    jouer(mod_head, a)
    jouer(mod_neuf, b)
    la, lb = lignes(a), lignes(b)
    diff = [k for k in la if la[k] != lb.get(k)] + [k for k in lb if k not in la]
    ok(f"TEMOIN INVERSE : eteint, la nuit neuve rend le registre de la nuit d'avant ({len(la)} lignes)",
       not diff and len(la) == len(lb), f"{len(diff)} ligne(s) differente(s), ex. {diff[:5]}")

    os.environ["APP_AFFAIRE_PERSONNES_DEUX_NUMEROS"] = "1"
    try:
        jouer(mod_neuf, c)
    finally:
        os.environ.pop("APP_AFFAIRE_PERSONNES_DEUX_NUMEROS", None)
    lc = lignes(c)
    autres, mauvais, gens_poses, lignes_touchees = [], [], 0, 0
    for k, rb in lb.items():
        rc = lc.get(k)
        if rc is None:
            autres.append(k)
            continue
        for col in rb:
            if col in ("acquereur_json", "acquereurs_json"):
                if rb[col] != rc[col]:
                    if sans_nos_numeros(rc[col]) != (json.loads(rb[col]) if rb[col] else rb[col]):
                        mauvais.append((k, col))
            elif rb[col] != rc[col]:
                autres.append((k, col))
        if rb.get("acquereurs_json") != rc.get("acquereurs_json") or rb.get("acquereur_json") != rc.get("acquereur_json"):
            lignes_touchees += 1
        for col in ("acquereur_json", "acquereurs_json"):
            if rc.get(col):
                v = json.loads(rc[col])
                gens_poses += sum(1 for p in personnes(v)
                                  if isinstance(p, dict) and "app_contact_id" in p)
    ok("allume : AUCUNE autre colonne ne change", not autres, f"{len(autres)} ecart(s), ex. {autres[:5]}")
    ok("allume : les listes ne changent QUE par l'ajout de app_contact_id", not mauvais, f"ex. {mauvais[:5]}")
    ok(f"allume : des personnes recoivent notre numero ({gens_poses} sur {lignes_touchees} lignes)", gens_poses > 0, "")
    # le co-acquereur : au moins une liste de 2 personnes ou toutes ont notre numero
    multiples = 0
    for rc in lc.values():
        if rc.get("acquereurs_json"):
            v = json.loads(rc["acquereurs_json"])
            if isinstance(v, list) and len(v) >= 2 and all(isinstance(p, dict) and "app_contact_id" in p for p in v):
                multiples += 1
    ok(f"allume : les CO-ACQUEREURS ont notre numero ({multiples} listes multiples completes)", multiples > 0, "")


def main() -> int:
    if not PHASE2.exists() or not HEKTOR.exists():
        print("⛔ base introuvable : rien mesure")
        return 2
    neuf = charger("affaire_ledger_neuf", SYNC / "affaire_ledger.py")
    essais_fonction(neuf)
    dossier = Path(tempfile.mkdtemp(prefix="essai_personnes_"))
    try:
        essais_nuit(neuf, dossier)
    except Exception as e:                                          # noqa: BLE001
        print(f"⛔ la nuit n'a pas pu etre rejouee : {e!r}")
        for nom, vrai, detail in R:
            print(f"{'  OK  ' if vrai else 'ECHEC '} {nom}{'' if vrai else ' -- ' + detail}")
        return 2
    finally:
        shutil.rmtree(dossier, ignore_errors=True)
    echecs = 0
    for nom, vrai, detail in R:
        print(f"{'  OK  ' if vrai else 'ECHEC '} {nom}{'' if vrai else ' -- ' + detail}")
        echecs += 0 if vrai else 1
    print(f"\n⛔ {echecs} controle(s) en echec." if echecs else "\n✅ Tous les controles sont verts.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
