#!/usr/bin/env python3
"""Relit, TOUT DE SUITE, les deux fiches d'un couple qu'on vient de rattacher chez Hektor.   03/11/2026

COUPLES -- « Ajouter un conjoint » (synthese couples §52-53). Appele par le worker apres un
`transformeContactToConjunct` PROUVE (refCouple relu par l'API sur les deux fiches).

POURQUOI LE WORKER NE PEUT PAS ATTENDRE LA NUIT : un rattachement change la `datemaj` des
fiches mais PAS leur `dateLastTraitement` -- la liste de nuit triee par cette date ne les
relisait jamais (EA32621, synthese §40). Et la nature (« couple ») n'est calculee que par
nature_des_fiches.py : une simple relecture renverrait la nature de la nuit precedente et
l'ecran cesserait de montrer le couple jusqu'au lendemain (synthese §43).

LA SEQUENCE, celle qui a marche a la main pour EA32621 (§43) et pour le couple fictif (§35) :
    1. relecture complete du CONJOINT   (refresh_contact_inproc.py)  -- d'abord, pour que
    2. relecture complete de la PERSONNE (refresh_contact_inproc.py)    la personne trouve sa place 2
    3. la nature de toutes les fiches   (nature_des_fiches.py, ~8 s, table locale entiere)
    4. l'envoi des deux fiches          (push_contacts_to_supabase.py --contact-id, x2)

Chaque etape est un processus a part (meme commande qu'a la main). On continue apres un
echec d'etape (la suivante peut encore servir) mais le code de sortie le dit.
Sortie : une derniere ligne JSON {"etapes": [...], "ok": true|false}.

    python phase2/contacts/relire_couple_rattache.py --principal 10260586 --conjoint 10260585
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def etapes(principal: str, conjoint: str) -> list[tuple[str, list[str]]]:
    push = ["phase2/sync/push_contacts_to_supabase.py", "--push-mode", "full",
            "--contacts-scope", "active_or_eligible", "--skip-stats", "--include-archived-searches"]
    return [
        ("relecture_conjoint", ["phase2/sync/refresh_contact_inproc.py", "--contact-id", conjoint]),
        ("relecture_principal", ["phase2/sync/refresh_contact_inproc.py", "--contact-id", principal]),
        ("nature", ["phase2/contacts/nature_des_fiches.py"]),
        ("envoi_conjoint", push + ["--contact-id", conjoint]),
        ("envoi_principal", push + ["--contact-id", principal]),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--principal", required=True)
    ap.add_argument("--conjoint", required=True)
    ap.add_argument("--a-blanc", action="store_true", help="dit les commandes sans les lancer")
    args = ap.parse_args()
    principal, conjoint = str(args.principal).strip(), str(args.conjoint).strip()
    if not principal.isdigit() or not conjoint.isdigit() or principal == conjoint:
        print(json.dumps({"ok": False, "erreur": "numeros invalides"}, ensure_ascii=False))
        return 2
    bilan = []
    ok = True
    for nom, commande in etapes(principal, conjoint):
        if args.a_blanc:
            bilan.append({"etape": nom, "commande": commande})
            continue
        debut = time.time()
        fini = subprocess.run([sys.executable, *commande], cwd=str(ROOT), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        bilan.append({"etape": nom, "code": fini.returncode, "duree_s": round(time.time() - debut, 1),
                      "fin": (fini.stderr or fini.stdout or "").strip().splitlines()[-1:] or []})
        if fini.returncode != 0:
            ok = False
    print(json.dumps({"ok": ok, "etapes": bilan}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
