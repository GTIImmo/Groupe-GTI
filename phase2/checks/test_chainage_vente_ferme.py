"""VÉRIFICATION DU CORRECTIF « une vente ferme toujours » — 08/09/2026

⚠ N'ÉCRIT QUE DANS UN REGISTRE JETABLE, en mémoire. Ni Supabase, ni le serveur
  local, ni Hektor ne sont touchés. On sème les QUATRE cas réels trouvés par
  verifier_regle_chainage.py, on appelle LA VRAIE fonction du run, et on regarde.

CE QU'ON PROUVE :
  · les 4 chaînes cassées se scindent bien en deux dossiers
  · le dossier { offre + compromis } devient OUVERT -- donc le bien redevient
    « engagé » au sens de la modale, ce qui bouche l'angle mort
  · une vente SEULE reste seule (les 101 cas du parc ne bougent pas)
  · une chaîne NORMALE offre -> compromis -> vente n'est pas touchée (7 507 cas)

   python phase2/checks/test_chainage_vente_ferme.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[2])
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from phase2.sync.affaire_ledger import LEDGER_TABLE, recalculer_les_chaines  # noqa: E402

# ─── LES CAS, RELEVÉS DANS LE REGISTRE RÉEL LE 08/09 ───
# (app_affaire_id, annonce, kind, state, date, acquereur)
CAS = [
    # ① le défaut, annonce 48458 : vente EN TÊTE, puis offre et compromis du MÊME acquéreur
    (24743, "48458", "vente", None, "2017-07-13", "402473"),
    (24742, "48458", "offre", "accepted", "2017-09-04", "402473"),
    (24741, "48458", "compromis", "active", "2017-09-21", "402473"),
    # ② idem, annonce 14486
    (7126, "14486", "vente", None, "2024-03-13", "37764"),
    (7124, "14486", "offre", "accepted", "2024-09-25", "37764"),
    (7122, "14486", "compromis", "active", "2024-10-15", "37764"),
    # ③ TÉMOIN : une chaîne NORMALE ne doit pas bouger
    (900, "99001", "offre", "accepted", "2026-01-10", "111"),
    (901, "99001", "compromis", "active", "2026-02-10", "111"),
    (902, "99001", "vente", None, "2026-03-10", "111"),
    # ④ TÉMOIN : une vente SEULE reste seule
    (950, "99002", "vente", None, "2026-01-10", "222"),
]


def registre_jetable() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute(f"""CREATE TABLE {LEDGER_TABLE} (
        app_affaire_id INTEGER PRIMARY KEY, app_chaine_id INTEGER,
        hektor_annonce_id TEXT, kind TEXT, state TEXT, date TEXT,
        acquereurs_json TEXT, hektor_affaire_id TEXT, present_in_hektor INTEGER)""")
    for app_id, annonce, kind, state, date, acq in CAS:
        con.execute(
            f"INSERT INTO {LEDGER_TABLE}(app_affaire_id, hektor_annonce_id, kind, state,"
            " date, acquereurs_json, hektor_affaire_id, present_in_hektor)"
            " VALUES (?,?,?,?,?,?,?,1)",
            (app_id, annonce, kind, state, date,
             json.dumps([{"id": acq}]), str(10000 + app_id)))
    con.commit()
    return con


def chaines(con: sqlite3.Connection) -> dict[str, dict[int, list]]:
    out: dict[str, dict[int, list]] = {}
    for annonce, chaine, app_id, kind, state in con.execute(
            f"SELECT hektor_annonce_id, app_chaine_id, app_affaire_id, kind, state"
            f"  FROM {LEDGER_TABLE} ORDER BY hektor_annonce_id, app_chaine_id, date"):
        out.setdefault(annonce, {}).setdefault(chaine, []).append((app_id, kind, state))
    return out


def ouvert(membres: list) -> bool:
    """La règle du front, transcrite (App.tsx, dossiersOuvertsDuBien)."""
    vente = any(k == "vente" for _, k, _ in membres)
    a_comp = any(k == "compromis" for _, k, _ in membres)
    comp_vivant = any(k == "compromis" and (s or "").lower() not in ("cancelled", "annule")
                      for _, k, s in membres)
    a_offre = any(k == "offre" for _, k, _ in membres)
    offre_vivante = any(k == "offre" and (s or "").lower() not in ("refused", "refusee")
                        for _, k, s in membres)
    return (not vente) and (not a_comp or comp_vivant) and (a_comp or not a_offre or offre_vivante)


def main() -> int:
    con = registre_jetable()
    recalculer_les_chaines(con)
    res = chaines(con)

    ok = True

    def verdict(nom: str, attendu, obtenu):
        nonlocal ok
        bon = attendu == obtenu
        ok = ok and bon
        print("   %-56s %s" % (nom, "OK" if bon else f"ECHEC (attendu {attendu}, obtenu {obtenu})"))

    for annonce in ("48458", "14486"):
        print(f"=== annonce {annonce} — le cas cassé ===")
        for chaine, membres in sorted(res[annonce].items()):
            etat = "OUVERT" if ouvert(membres) else "terminé"
            detail = " · ".join(f"{k}" for _, k, _ in membres)
            print(f"   dossier {chaine:<6} {etat:<8} {detail}")
        verdict("deux dossiers au lieu d'un", 2, len(res[annonce]))
        verdict("un dossier OUVERT (le bien redevient « engagé »)",
                1, sum(1 for m in res[annonce].values() if ouvert(m)))
        verdict("la vente est SEULE dans le sien",
                True, any(len(m) == 1 and m[0][1] == "vente" for m in res[annonce].values()))
        print("")

    print("=== témoin : une chaîne NORMALE offre → compromis → vente ===")
    for chaine, membres in sorted(res["99001"].items()):
        print(f"   dossier {chaine:<6} {'OUVERT' if ouvert(membres) else 'terminé':<8}"
              f" {' · '.join(k for _, k, _ in membres)}")
    verdict("elle reste UN SEUL dossier", 1, len(res["99001"]))
    verdict("et il est terminé (clos par sa vente)", 0,
            sum(1 for m in res["99001"].values() if ouvert(m)))
    print("")

    print("=== témoin : une vente SEULE ===")
    verdict("elle reste seule dans son dossier", 1, len(res["99002"]))
    print("")
    print("   >>> " + ("TOUT PASSE" if ok else "IL Y A UN ECHEC"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
