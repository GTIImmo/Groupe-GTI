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
        acquereurs_json TEXT, hektor_affaire_id TEXT, present_in_hektor INTEGER,
        -- 16/09 : la regle ordonne desormais l'offre sur SA date, lue dans ses
        -- propositions. La table jetable doit porter la colonne, sinon le test
        -- n'exerce plus la vraie fonction -- il la fait echouer.
        propositions_json TEXT)""")
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

    # ═══════════════════════════════════════════════════════════════════════════
    # ⚠⚠ DEUX DECISIONS DU PROJET SE RENCONTRENT ICI -- 12/11/2026
    # ═══════════════════════════════════════════════════════════════════════════
    # 08/09/2026, cet essai : « une vente ferme toujours » -- une vente EN TETE se
    #   SEPARE de l'offre et du compromis qui la suivent, pour que le bien
    #   redevienne « engage » au sens de la modale. Attendu : DEUX dossiers.
    # 12/11/2026, REGLE D (demandee par Frederic) : « un acheteur + un bien = UN
    #   dossier ». Attendu : UN SEUL dossier.
    #
    # ⭐ CE QUE LA MESURE DU 12/11 A TRANCHE, et elle donne raison a la regle D :
    #     dossiers portant une vente                          9 280
    #     dont la vente est datee AVANT leur offre                 8   (0,09 %)
    #   Et en les regardant un par un, L'ANOMALIE N'EST PAS LA VENTE : dans la
    #   moitie des cas l'ordre compromis -> vente est CORRECT, et c'est l'OFFRE qui
    #   est datee apres -- parce qu'elle a ete SAISIE APRES COUP, pour completer le
    #   dossier. C'est le sujet de l'essai voisin (test_chainage_offre_regularisee).
    #   ➡ Les separer fabriquerait DEUX dossiers pour UNE SEULE vente.
    #     La regle du 08/09 servait 8 dossiers ; la regle D en reunit 727.
    #
    # ⛔ ON N'EFFACE PAS LE RAISONNEMENT DU 08/09 POUR AUTANT : l'essai lit
    #   l'interrupteur et verifie LES DEUX comportements. Le jour ou la regle D est
    #   eteinte, l'attendu du 08/09 redevient celui qui est mesure.
    #   (Meme forme que test_chainage_offre_regularisee et test_chainage_v2.)
    # ⛔ ET LE LEVIER N'EST PAS CELUI QUE J'AI CRU D'ABORD (12/11, mesure) :
    #   j'avais ecrit « c'est la regle D ». FAUX. Les DEUX regles reunissent ces
    #   trois transactions, CHACUNE INDEPENDAMMENT :
    #       regle C (vente seule)      rattache la vente au compromis actif du meme nom
    #       regle D (meme acheteur)    reunit tout ce qui porte le meme acheteur
    #   Mesure :  D eteinte + C allumee -> 1 dossier
    #             C eteinte + D allumee -> 1 dossier
    #             LES DEUX eteintes     -> 2 dossiers, l'attendu du 08/09
    #   ➡ La condition est donc « C OU D », et la lire sur une seule des deux
    #     aurait rendu cet essai faux dans un cas sur deux.
    import phase2.sync.affaire_ledger as _al
    c_actif = _al.chainage_vente_seule_actif()
    d_actif = _al.chainage_meme_acheteur_actif()
    reunies = c_actif or d_actif
    print("regle C (vente seule) : %s . regle D (meme acheteur) : %s"
          % ("allumee" if c_actif else "eteinte", "allumee" if d_actif else "eteinte"))
    print("-> " + ("elles REUNISSENT : un seul dossier attendu"
                   if reunies else "aucune des deux : le comportement du 08/09"))
    print("")

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
        if reunies:
            # La regle C ou D reunit : UN dossier, ferme par sa vente, et la vente n'y
            # est pas seule. C'est l'etat voulu depuis le 12/11.
            verdict("UN SEUL dossier (reuni par la regle C ou D)",
                    1, len(res[annonce]))
            verdict("aucun dossier OUVERT (la vente le ferme)",
                    0, sum(1 for m in res[annonce].values() if ouvert(m)))
            verdict("la vente N'EST PAS seule (elle a rejoint son compromis)",
                    False, any(len(m) == 1 and m[0][1] == "vente"
                               for m in res[annonce].values()))
        else:
            # ⭐ L'ATTENDU DU 08/09, CONSERVE MOT POUR MOT : il redevient le juge
            #   des que la regle D est eteinte.
            verdict("deux dossiers au lieu d'un", 2, len(res[annonce]))
            verdict("un dossier OUVERT (le bien redevient « engagé »)",
                    1, sum(1 for m in res[annonce].values() if ouvert(m)))
            verdict("la vente est SEULE dans le sien",
                    True, any(len(m) == 1 and m[0][1] == "vente"
                              for m in res[annonce].values()))
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
