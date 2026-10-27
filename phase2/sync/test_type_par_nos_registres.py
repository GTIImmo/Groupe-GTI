"""⑧ TYPES, ÉTAPE 2 (27/10/2026) — essai HORS LIGNE de l'envoi des contacts sans le type.

On EXÉCUTE le vrai code (push_contacts_to_supabase.rows_pour_envoi, stable_payload_hash), sans réseau ni base.
  1. interrupteur éteint : l'envoi est IDENTIQUE à avant (les mêmes objets) ;
  2. allumé : les fiches contact partent SANS `relation_roles_json`, toutes avec les mêmes clés (PGRST102) ;
     les autres tables partent intactes ;
  3. ⭐ l'EMPREINTE de chaque fiche ne change pas (sinon les 62 000 fiches repartiraient toutes) ;
  4. `loaded` n'est jamais modifié (c'est lui que mark_pushed_rows enregistre) ;
  5. MUTANT : un envoi qui retirerait le type de `loaded` lui-même changerait l'empreinte -> attrapé ;
  6. recalculer_types_contacts.py, interrupteur éteint : sort en 0 sans appeler personne.

    python phase2/sync/test_type_par_nos_registres.py     (sortie 0 = tout vert)
"""
from __future__ import annotations

import copy
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phase2" / "sync"))
import push_contacts_to_supabase as p  # noqa: E402

echecs = 0


def verifier(nom: str, ok: bool, detail: str = "") -> None:
    global echecs
    print(("OK    " if ok else "ECHEC ") + nom + ("" if ok else "  -> " + detail))
    if not ok:
        echecs += 1


fiches = [
    {"hektor_contact_id": "10354352", "nom": "JACQUIER", "relation_roles_json": ["acquereur_offre", "mandant"], "archive": False},
    {"hektor_contact_id": "10000167", "nom": "X", "relation_roles_json": [], "archive": False},
]
liens = [{"relation_key": "k1", "hektor_contact_id": "10354352", "role_contact": "mandant"}]
loaded = [("app_contact_current", fiches), ("app_contact_relation_current", liens)]
temoin = copy.deepcopy(loaded)
empreintes = [p.stable_payload_hash(r) for r in fiches]

# 1. éteint
os.environ.pop("APP_TYPE_PAR_NOS_REGISTRES", None)
verifier("interrupteur eteint : l'envoi est identique (les memes objets)", p.rows_pour_envoi(loaded) is loaded)

# 2-4. allumé
os.environ["APP_TYPE_PAR_NOS_REGISTRES"] = "1"
envoi = dict(p.rows_pour_envoi(loaded))
verifier("allume : les fiches contact partent SANS le type",
         all("relation_roles_json" not in r for r in envoi["app_contact_current"]))
verifier("allume : toutes les fiches d'un lot ont les memes cles (PGRST102)",
         len({tuple(sorted(r)) for r in envoi["app_contact_current"]}) == 1)
verifier("allume : les autres colonnes partent intactes",
         all(r["nom"] == f["nom"] and r["archive"] == f["archive"] for r, f in zip(envoi["app_contact_current"], fiches)))
verifier("allume : les autres tables partent telles quelles", envoi["app_contact_relation_current"] is liens)
verifier("l'EMPREINTE de chaque fiche ne change pas (pas d'envoi massif la nuit suivante)",
         [p.stable_payload_hash(r) for r in fiches] == empreintes)
verifier("`loaded` n'est pas modifie (c'est lui que l'etat d'envoi enregistre)", loaded == temoin)

# 5. MUTANT : retirer le type de `loaded` lui-même
mutant = copy.deepcopy(fiches)
for r in mutant:
    r.pop("relation_roles_json")
verifier("MUTANT (retirer le type de la fiche locale) : l'empreinte changerait -> attrape",
         [p.stable_payload_hash(r) for r in mutant] != empreintes)

# 6. le script de fin de nuit, éteint
env = dict(os.environ)
env["APP_TYPE_PAR_NOS_REGISTRES"] = "0"
sortie = subprocess.run([sys.executable, str(ROOT / "phase2" / "sync" / "recalculer_types_contacts.py")],
                        capture_output=True, text=True, env=env, cwd=str(ROOT), encoding="utf-8", errors="replace")
verifier("recalculer_types_contacts.py eteint : sort en 0 et le dit, sans appel",
         sortie.returncode == 0 and "eteint" in sortie.stdout, f"code {sortie.returncode} : {sortie.stdout[-200:]} {sortie.stderr[-200:]}")

print("\ntout vert" if not echecs else f"\n{echecs} controle(s) en echec")
sys.exit(1 if echecs else 0)
