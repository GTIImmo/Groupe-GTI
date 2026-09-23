#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C-4 — REPETITION : ce qui n'existe QUE dans Supabase ne se supprime pas.
                                                                  23/09/2026

POURQUOI CE FICHIER EXISTE. Le garde-fou `delete_contacts_except_dirty` a ete
ecrit le 21/09, teste par phase2/sync/test_dirty_guards.py, vert a chaque fois
-- et JAMAIS APPELE EN PRODUCTION. Il protegeait sur le papier. C'est le genre
de defaut que seul un controle de BRANCHEMENT attrape : verifier qu'une
fonction marche ne dit rien de savoir si quelqu'un l'appelle.

CE QU'ON EPROUVE :

  (1) LE BRANCHEMENT. La fonction est-elle appelee sur le chemin reel ?
  (2) CE QU'ELLE EPARGNE : un contact ne dans l'app, un contact « dirty ».
  (3) SES RELATIONS ET SES RECHERCHES, qui n'existent elles aussi que dans
      Supabase -- epargner la fiche et effacer ses relations ne vaut rien.
  (4) L'ORDRE, qui est une protection : `find_stale_row_keys` DOIT venir avant
      les deux retrecissements de `loaded`. S'il passait apres, le mode update
      declarerait disparu tout ce qui n'a pas change -- c'est-a-dire le parc.

N'APPELLE NI HEKTOR NI SUPABASE.
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
FICHIER = RACINE / "phase2" / "sync" / "push_contacts_to_supabase.py"
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

import push_contacts_to_supabase as push  # noqa: E402

src = io.open(FICHIER, encoding="utf-8").read()
echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


class FauxClient:
    """Note ce qu'on lui demande de supprimer, sans rien appeler."""

    def __init__(self) -> None:
        self.supprimes: list[str] = []

    def delete_rows_by_filter(self, table, colonne, valeurs, batch_size):
        self.supprimes.extend(str(v) for v in valeurs)
        return len(valeurs)


# ── (1) LE BRANCHEMENT ─────────────────────────────────────────────────────
def branchement(texte: str) -> bool:
    """La fonction est-elle appelee ailleurs que dans sa propre definition ?"""
    appels = texte.count("delete_contacts_except_dirty(")
    definition = texte.count("def delete_contacts_except_dirty(")
    return appels - definition >= 1


controle("(1) le garde-fou est APPELE sur le chemin reel", branchement(src),
         "il n'est appele nulle part : c'est le defaut du 21/09")

# ── (2) CE QU'IL EPARGNE ───────────────────────────────────────────────────
client = FauxClient()
push.delete_contacts_except_dirty(
    client,
    contact_ids=["605450", "10000001", "605451"],
    dirty_contact_ids={"605451"},
    batch_size=100)
controle("(2) un contact ne dans l'app est EPARGNE",
         "10000001" not in client.supprimes, str(client.supprimes))
controle("(2) un contact en cours de saisie est EPARGNE",
         "605451" not in client.supprimes, str(client.supprimes))
controle("(2) un contact ordinaire disparu est bien supprime",
         client.supprimes == ["605450"], str(client.supprimes))

controle("(2) et rien n'est demande quand tout est protege",
         push.delete_contacts_except_dirty(
             FauxClient(), ["10000001"], set(), 100) == 0)

# ── (3) RELATIONS ET RECHERCHES ────────────────────────────────────────────
controle("(3) les relations/recherches d'un contact ne dans l'app sont epargnees",
         "if est_ne_dans_l_app(row.get(\"hektor_contact_id\")):" in src)

controle("(3) la plage est bien celle du projet",
         push.PLAGE_NUMEROS_APP == 10000000 and push.est_ne_dans_l_app("10000000")
         and not push.est_ne_dans_l_app("9999999"))

# ── (4) L'ORDRE EST UNE PROTECTION ─────────────────────────────────────────
def ordre(texte: str) -> tuple[int, int, int]:
    calcul = texte.find("stale_by_table = {} if contact_ids else find_stale_row_keys")
    changes = texte.find("loaded = filter_changed_rows(")
    dirty = texte.find("dirty_search_pairs = fetch_dirty_search_pairs(")
    return calcul, changes, dirty


calcul, changes, dirty = ordre(src)
controle("(4) les disparues sont calculees AVANT le filtre des changements",
         0 < calcul < changes, f"calcul={calcul} filtre={changes}")
controle("(4) les disparues sont calculees AVANT le retrait des saisies en cours",
         0 < calcul < dirty, f"calcul={calcul} dirty={dirty}")

# ── LA PREUVE : CES CONTROLES ATTRAPENT-ILS LA VERSION D'AVANT ? ───────────
# Un controle qu'on n'a pas passe sur le defaut qu'il pretend voir n'est pas un
# controle. C'est la lecon des deux assertions fausses de la semaine derniere.
try:
    avant = subprocess.run(
        ["git", "show", "HEAD:phase2/sync/push_contacts_to_supabase.py"],
        cwd=str(RACINE), capture_output=True, text=True, encoding="utf-8", timeout=30)
    if avant.returncode == 0 and avant.stdout:
        controle("PREUVE : le controle de branchement ECHOUE sur la version d'avant",
                 not branchement(avant.stdout),
                 "il passait deja : le controle ne voit rien")
        controle("PREUVE : le filtre relations/recherches est ABSENT de la version d'avant",
                 "if est_ne_dans_l_app(row.get(\"hektor_contact_id\")):" not in avant.stdout)
    else:
        print("  ---  version d'avant illisible, preuve non faite")
except Exception as err:  # pragma: no cover
    print(f"  ---  preuve non faite : {type(err).__name__}")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Tous les controles passent : le garde-fou est branche, et il epargne ce qui n'a qu'un exemplaire.")
