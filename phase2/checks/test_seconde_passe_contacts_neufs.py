#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SECONDE PASSE DU BUILD — UN CONTACT NEUF PART-IL SOUS SON IDENTITE ?   24/09/2026

Le run fait build -> registre -> push. Un contact cree chez Hektor dans la journee
est ecrit par le build sous son numero Hektor, recoit son identite du registre
juste apres, et partait vers Supabase sous l'ancien numero. La seconde passe
relance le build apres le registre, seulement s'il y a des contacts a traduire.

On verifie :
  (1-3) la mesure « contacts a traduire » : 0 / le cas neuf / le cas deja traduit
  (4)   sans contact a traduire, l'option s'arrete SANS ouvrir le miroir
  (5-6) le run appelle la seconde passe APRES le registre et AVANT le push
  (7)   elle ne peut pas arreter le run (etape non bloquante)

⚠ LA PREUVE D'ABORD : la version epinglee du build ne connait pas l'option --
  le test doit ECHOUER.
      python phase2/checks/test_seconde_passe_contacts_neufs.py --build <fichier>
N'ECRIT RIEN dans la vraie base.
"""
from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
ECHECS: list[str] = []
TOTAL = 7


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK ' if ok else 'KO '} {nom}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        ECHECS.append(nom)


def base(chemin: Path, couche: list[str], registre: list[tuple]) -> None:
    c = sqlite3.connect(chemin)
    c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT PRIMARY KEY)")
    c.execute("CREATE TABLE app_contact (app_contact_id INTEGER, hektor_contact_id TEXT, hektor_target_id TEXT)")
    c.executemany("INSERT INTO app_contact_current VALUES (?)", [(x,) for x in couche])
    c.executemany("INSERT INTO app_contact VALUES (?,?,?)", registre)
    c.commit()
    c.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=str(RACINE / "phase2" / "contacts" / "build_contacts_layer.py"))
    args = ap.parse_args()
    print(f"build teste : {args.build}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        miroir_absent = tmp / "miroir_qui_ne_doit_pas_etre_cree.sqlite"

        def lancer(phase2: Path) -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, args.build, "--phase2-db", str(phase2), "--hektor-db", str(miroir_absent),
                 "--no-reports", "--seulement-si-contacts-a-traduire"],
                cwd=RACINE, capture_output=True, text=True, encoding="utf-8", errors="replace")

        # (1) rien a traduire : un contact d'avant la bascule, identite = son numero
        rien = tmp / "rien.sqlite"
        base(rien, ["10000123", "10650346"],
             [(10000123, "10000123", "123"), (10650346, "10650346", "605491")])
        # (2) un contact NEUF : la couche le porte sous 605514, le registre lui a donne 10650369
        neuf = tmp / "neuf.sqlite"
        base(neuf, ["10000123", "605514"],
             [(10000123, "10000123", "123"), (10650369, "10650369", "605514")])
        # (3) un vieux contact Hektor jamais numerote (identite = numero Hektor) : rien a traduire
        vieux = tmp / "vieux.sqlite"
        base(vieux, ["5411"], [(5411, "5411", None)])

        sys.path.insert(0, str(RACINE))
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_sous_test", args.build)
        B = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = B
        spec.loader.exec_module(B)
        if not hasattr(B, "contacts_a_traduire"):
            controle("(0) le build sait mesurer les contacts a traduire", False,
                     "contacts_a_traduire absent -- version d'avant la seconde passe")
        else:
            controle("(1) contacts deja sous leur identite -> 0 a traduire", B.contacts_a_traduire(rien) == 0)
            controle("(2) contact neuf sous son n° Hektor -> 1 a traduire", B.contacts_a_traduire(neuf) == 1)
            controle("(3) vieux contact Hektor sans identite propre -> 0", B.contacts_a_traduire(vieux) == 0)

        r = lancer(rien)
        controle("(4) rien a traduire : sortie 0, AUCUN build (le miroir n'est meme pas ouvert)",
                 r.returncode == 0 and "0 contact a traduire" in r.stdout and not miroir_absent.exists(),
                 f"code {r.returncode} ; {(r.stdout + r.stderr)[-160:]!r}")

    run = (RACINE / "run_full_pipeline.ps1").read_text(encoding="utf-8")
    i_registre = run.find('"phase2\\identite\\registre_contacts.py"')
    i_passe = run.find('"--seulement-si-contacts-a-traduire"')
    i_push = run.find('"phase2\\sync\\push_contacts_to_supabase.py"')
    controle("(5) la seconde passe vient APRES le registre", 0 < i_registre < i_passe, f"{i_registre} / {i_passe}")
    controle("(6) ... et AVANT le push des contacts", 0 < i_passe < i_push, f"{i_passe} / {i_push}")
    bloc = run[run.rfind("Invoke-", 0, i_passe):i_passe]
    controle("(7) elle ne peut pas arreter le run (etape non bloquante, sans FailOnError)",
             bloc.startswith("Invoke-OptionalStepWithRetry") and "-FailOnError" not in run[i_passe:i_passe + 200],
             bloc[:60])

    print(f"\n{'TOUT VERT' if not ECHECS else str(len(ECHECS)) + ' ECHEC(S)'} ({TOTAL - len(ECHECS)}/{TOTAL})")
    return 1 if ECHECS else 0


if __name__ == "__main__":
    sys.exit(main())
