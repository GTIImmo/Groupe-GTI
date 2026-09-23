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


def cible_hektor(identite: str) -> str:
    """Le numero que HEKTOR comprend, pour ce contact.

    ⚠ C-6, 23/09/2026 -- QUATRE ETAPES, DEUX LANGUES. Le worker appelle ce point
      d'entree avec le numero que le front connait : l'IDENTITE. Or les etapes 1
      et 2 ne parlent pas cette langue -- l'une interroge Hektor, l'autre ecrit
      dans le MIROIR, qui est une copie de Hektor. Tant que les deux numeros sont
      egaux, un seul argument suffit ; a la bascule, ouvrir une fiche contact
      aurait envoye notre numero chez Hektor (404, puis liste noire) et fait
      ecrire une fiche vide dans le miroir sous notre numero.

    En cas de doute -- base illisible, contact inconnu -- on rend l'identite,
    c'est-a-dire le comportement d'avant.
    """
    texte = str(identite or "").strip()
    if not texte.isdigit():
        return texte
    try:
        import sqlite3
        conn = sqlite3.connect(str(ROOT / "phase2" / "phase2.sqlite"), timeout=30)
        try:
            ligne = conn.execute(
                "SELECT hektor_target_id FROM app_contact_current "
                "WHERE hektor_contact_id = ? LIMIT 1", (texte,)).fetchone()
        finally:
            conn.close()
    except Exception:
        return texte
    cible = str(ligne[0] or "").strip() if ligne else ""
    return cible or texte


def _steps(contact_id: str):
    """(libellé, chemin relatif depuis ROOT, argv) — flags IDENTIQUES au worker."""
    identite = str(contact_id or "").strip()
    pour_hektor = cible_hektor(identite)
    return [
        # ETAPES 1 et 2 : la langue de HEKTOR et de son miroir.
        ("detail", "phase2/sync/sync_contact_details.py", [
            "--skip-listing-refresh", "--contact-id", pour_hektor,
            "--batch-size", "1", "--limit", "0",
            "--request-delay-seconds", "0", "--batch-pause-seconds", "0",
            "--max-hard-errors", "1", "--max-consecutive-hard-errors", "1",
            "--no-normalize",
        ]),
        ("normalize", "normalize_source.py", ["--contact-id", pour_hektor]),
        # ETAPES 3 et 4 : NOTRE langue. (Le build accepte les deux, il traduit
        # dans les deux sens ; on lui donne l'identite, qui est la sienne.)
        ("build", "phase2/contacts/build_contacts_layer.py", [
            "--contact-id", identite, "--no-reports",
        ]),
        # --include-archived-searches (21/08/2026) : meme raison que dans le run de 03:00.
        # Sans elle, ouvrir une fiche contact suffirait a resupprimer ses recherches
        # archivees de Supabase, et a reorpheliner ce qui pointait dessus.
        ("push", "phase2/sync/push_contacts_to_supabase.py", [
            "--contact-id", identite,
            "--push-mode", "full", "--contacts-scope", "active_or_eligible",
            "--skip-stats", "--include-archived-searches",
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
