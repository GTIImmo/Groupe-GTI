#!/usr/bin/env python3
"""Read-through contact en UN SEUL process (optimisation n°8).

Enchaîne les 4 étapes du rafraîchissement d'un contact —
  1) sync_contact_details (ContactById Hektor)
  2) normalize_source
  3) build_contacts_layer
  4) push_contacts_to_supabase
— dans un SEUL démarrage Python, au lieu de 4 process séparés (~3 s de démarrage
chacun). Reproduit À L'IDENTIQUE les commandes lancées par le worker
(`runContactRefreshPipeline`), via runpy → même sémantique que `python xxx.py`
(mêmes flags, même cwd, mêmes chemins). Les 4 scripts d'origine ne sont PAS modifiés.

Arrêt à la 1re étape en échec (comme l'enchaînement séquentiel actuel du worker).
Code de sortie : 0 = OK, sinon le code de l'étape fautive.

Usage : python phase2/sync/refresh_contact_inproc.py --contact-id <id>
"""
from __future__ import annotations

import argparse
import os
import runpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _steps(contact_id: str):
    """(libellé, chemin relatif depuis ROOT, argv) — flags IDENTIQUES au worker."""
    return [
        ("detail", "phase2/sync/sync_contact_details.py", [
            "--skip-listing-refresh", "--contact-id", contact_id,
            "--batch-size", "1", "--limit", "0",
            "--request-delay-seconds", "0", "--batch-pause-seconds", "0",
            "--max-hard-errors", "1", "--max-consecutive-hard-errors", "1",
            "--no-normalize",
        ]),
        ("normalize", "normalize_source.py", ["--contact-id", contact_id]),
        ("build", "phase2/contacts/build_contacts_layer.py", [
            "--contact-id", contact_id, "--no-reports",
        ]),
        ("push", "phase2/sync/push_contacts_to_supabase.py", [
            "--contact-id", contact_id,
            "--push-mode", "full", "--contacts-scope", "active_or_eligible",
            "--skip-stats",
        ]),
    ]


def _run_step(rel_path: str, argv: list[str]) -> int:
    """Exécute un script comme le ferait `python <rel_path> <argv>`, en process."""
    abs_path = str(ROOT / rel_path)
    script_dir = os.path.dirname(abs_path)
    old_argv, old_path = sys.argv, list(sys.path)
    sys.argv = [abs_path] + argv
    # Reproduit le contexte d'import de `python xxx.py` : dossier du script + ROOT.
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, script_dir)
    try:
        runpy.run_path(abs_path, run_name="__main__")
        return 0
    except SystemExit as exc:                # `raise SystemExit(main())` côté script
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 1
    finally:
        sys.argv, sys.path = old_argv, old_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-through contact en 1 process (n°8).")
    ap.add_argument("--contact-id", required=True)
    args = ap.parse_args()
    cid = str(args.contact_id).strip()
    if not cid.isdigit():
        print(f"[refresh-inproc] contact-id invalide: {cid!r}", file=sys.stderr)
        return 2

    t0 = time.time()
    for label, rel, argv in _steps(cid):
        print(f"=== [refresh-inproc] ETAPE {label} ===", flush=True)
        st = time.time()
        rc = _run_step(rel, argv)
        print(f"=== [refresh-inproc] {label} fini en {round(time.time() - st, 1)}s (code {rc}) ===", flush=True)
        if rc != 0:
            print(f"[refresh-inproc] ARRET : etape {label} en echec (code {rc})", file=sys.stderr)
            return rc or 1
    print(f"[refresh-inproc] OK contact {cid} en {round(time.time() - t0, 1)}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
