#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑧ PIECE 3 (nuit) -- LE REGISTRE RANGE NOTRE NUMERO DE NOTAIRE.                     24/10/2026

Etude : notice/ETUDE_NUMEROS_PERSONNES_REGISTRE_TRANSACTIONS_2026-10-24.md (§12).

CE QU'IL EPROUVE
----------------
  ⓵ TEMOIN INVERSE : `registre_depuis_console.py` de la version d'AVANT (git HEAD) et la version neuve
     INTERRUPTEUR ETEINT, joues sur deux copies identiques -> registres IDENTIQUES. Ce script tourne chaque
     nuit des qu'il est enregistre : c'est le controle qui compte.
  ⓶ ALLUME : seules `notaire_acquereur_id` / `notaire_mandant_id` changent ; chaque valeur neuve est
     NOTRE numero de la meme personne (la paire de la doublure) ; noms, origine, taux, unites intacts.
  ⓷ STABLE : une SECONDE nuit allumee n'a plus rien a ecrire (sinon chaque nuit reecrirait tout).

⚠ IL N'ECRIT RIEN DE VRAI : les tables utiles sont recopiees depuis phase2.sqlite ouvert en LECTURE
  SEULE, dans un dossier temporaire efface a la fin ; jamais `--pousser`.

    python phase2/checks/test_notaires_notre_numero.py
    sortie 0 = vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
"""
from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SYNC = RACINE / "phase2" / "sync"
SCRIPT = SYNC / "registre_depuis_console.py"
PHASE2 = RACINE / "phase2" / "phase2.sqlite"
TABLES = ("app_affaire_ledger", "app_affaire_console", "app_contact")
CLE = "APP_AFFAIRE_NOTAIRES_NOTRE_NUMERO"

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8")
    except Exception:                                               # noqa: BLE001
        pass

R: list[tuple[str, bool, str]] = []


def ok(nom: str, vrai: bool, detail: str = "") -> None:
    R.append((nom, bool(vrai), detail))


def fabriquer_copie(dossier: Path, nom: str) -> Path:
    cible = dossier / f"{nom}.sqlite"
    src = sqlite3.connect(f"file:{PHASE2.as_posix()}?mode=ro", uri=True, timeout=30)
    dst = sqlite3.connect(cible)
    for t in TABLES:
        for (sql,) in src.execute("select sql from sqlite_master where tbl_name=? and sql is not null "
                                  "and type in ('table', 'index') "
                                  "order by case type when 'table' then 0 else 1 end", (t,)):
            dst.execute(sql)
        cols = [r[1] for r in src.execute(f"PRAGMA table_info({t})")]
        dst.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                        src.execute(f"SELECT {','.join(cols)} FROM {t}"))
    dst.commit()
    src.close()
    dst.close()
    return cible


def jouer(script: Path, base: Path, allume: bool) -> str:
    env = dict(os.environ)
    env.pop(CLE, None)
    if allume:
        env[CLE] = "1"
    env["PYTHONPATH"] = str(SYNC)
    env["PYTHONIOENCODING"] = "utf-8"
    sortie = subprocess.run([sys.executable, str(script), "--ecrire", "--db", str(base)],
                            capture_output=True, env=env, cwd=RACINE)
    texte = sortie.stdout.decode("utf-8", "replace") + sortie.stderr.decode("utf-8", "replace")
    if sortie.returncode != 0:
        raise RuntimeError(f"{script.name} a rendu {sortie.returncode} : {texte[-800:]}")
    return texte


def lignes(base: Path) -> dict[int, dict]:
    con = sqlite3.connect(base)
    con.row_factory = sqlite3.Row
    out = {int(r["app_affaire_id"]): dict(r) for r in con.execute("SELECT * FROM app_affaire_ledger")}
    con.close()
    return out


def paires(base: Path) -> dict[str, str]:
    con = sqlite3.connect(base)
    t = {str(c).strip(): str(n).strip() for n, c in con.execute(
        "SELECT app_contact_id, hektor_target_id FROM app_contact WHERE hektor_target_id IS NOT NULL")}
    con.close()
    return t


def main() -> int:
    if not PHASE2.exists():
        print("⛔ phase2.sqlite introuvable : rien mesure")
        return 2
    dossier = Path(tempfile.mkdtemp(prefix="essai_notaires_"))
    try:
        head = dossier / "registre_depuis_console_head.py"
        head.write_text(subprocess.run(["git", "show", "HEAD:phase2/sync/registre_depuis_console.py"], cwd=RACINE,
                                       capture_output=True, text=True, encoding="utf-8", check=True).stdout,
                        encoding="utf-8")
        a, b, c = (fabriquer_copie(dossier, n) for n in ("avant", "eteint", "allume"))
        jouer(head, a, False)
        sortie_b = jouer(SCRIPT, b, False)
        la, lb = lignes(a), lignes(b)
        diff = [k for k in la if la[k] != lb.get(k)] + [k for k in lb if k not in la]
        ok(f"TEMOIN INVERSE : eteint, le registre rendu est celui de la version d'avant ({len(la)} lignes)",
           not diff and len(la) == len(lb), f"{len(diff)} ecart(s), ex. {diff[:5]}")
        ok("eteint : le journal dit ETEINT", "ETEINT (APP_AFFAIRE_NOTAIRES_NOTRE_NUMERO)" in sortie_b, sortie_b[-400:])

        sortie_c = jouer(SCRIPT, c, True)
        lc, t = lignes(c), paires(c)
        autres, faux, traduits, gardes = [], [], 0, 0
        for k, rb in lb.items():
            rc = lc[k]
            for col in rb:
                if col in ("notaire_acquereur_id", "notaire_mandant_id"):
                    if rb[col] != rc[col]:
                        if t.get(str(rb[col] or "").strip()) == str(rc[col] or "").strip():
                            traduits += 1
                        else:
                            faux.append((k, col, rb[col], rc[col]))
                    elif rc[col] and int(str(rc[col])) < 10_000_000:
                        gardes += 1
                elif rb[col] != rc[col]:
                    autres.append((k, col))
        ok("allume : AUCUNE autre colonne ne change (noms, origine, taux, unites)", not autres,
           f"{len(autres)} ecart(s), ex. {autres[:5]}")
        ok("allume : chaque notaire change pour NOTRE numero de la meme personne", not faux, f"ex. {faux[:5]}")
        ok(f"allume : des notaires passent sous notre numero ({traduits} ; {gardes} gardes au numero de Hektor, sans paire)",
           traduits > 0, "")
        m = re.search(r"notaires sous NOTRE numero\s+(\d+)", sortie_c)
        ok("allume : le journal compte ce qu'il a traduit", bool(m) and int(m.group(1)) > 0, sortie_c[-400:])

        sortie_d = jouer(SCRIPT, c, True)
        m = re.search(r"lignes a ecrire\s+(\d+)", sortie_d)
        ok("STABLE : une seconde nuit allumee n'a plus rien a ecrire", bool(m) and int(m.group(1)) == 0,
           (m.group(0) if m else sortie_d[-400:]))
    except Exception as e:                                          # noqa: BLE001
        print(f"⛔ l'essai n'a pas pu etre joue : {e!r}")
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
