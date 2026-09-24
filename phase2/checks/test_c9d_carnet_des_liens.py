#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.9-d — LE CARNET DES LIENS NOTE-T-IL CHAQUE LIEN AVEC SA RECETTE EXACTE ?
                                                                  24/09/2026

On appelle la VRAIE fonction du build (enregistrer_registre_relations) sur une
base jetable, nuit apres nuit :
    nuit 1  trois liens ecrits            -> trois notes, recette rejouable
    nuit 2  un lien a disparu             -> marque disparu, jamais efface
    nuit 3  il revient                    -> la marque tombe, pas de note neuve
    build cible (complet=False)           -> ne marque RIEN disparu
et on verifie qu'il ne peut PAS faire tomber le build : un carnet qui tombe
en panne en cours de route -> bilan « erreur », ses ecritures annulees, celles du build intactes.

⚠ LA PREUVE D'ABORD : sur la version epinglee (avant C.9-d), le carnet n'existe
  pas -- le test doit ECHOUER.
      python phase2/checks/test_c9d_carnet_des_liens.py --build <fichier>
N'ECRIT RIEN dans la vraie base.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
ECHECS: list[str] = []
TOTAL = 19


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK ' if ok else 'KO '} {nom}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        ECHECS.append(nom)


def charger(chemin: Path):
    sys.path.insert(0, str(RACINE))
    spec = importlib.util.spec_from_file_location("build_sous_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # exige par @dataclass
    spec.loader.exec_module(module)
    return module


def noter(B, notes: dict) -> None:
    B._ANCRES_RELATIONS.clear()
    for cle, (recette, dossier) in notes.items():
        B._ANCRES_RELATIONS[cle] = {"recette": recette, "app_dossier_id": dossier}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=str(RACINE / "phase2" / "contacts" / "build_contacts_layer.py"))
    args = ap.parse_args()
    B = charger(Path(args.build))
    print(f"build teste : {args.build}")

    if not hasattr(B, "enregistrer_registre_relations"):
        controle("(0) le build sait tenir le carnet des liens", False,
                 "enregistrer_registre_relations absent -- version d'avant C.9-d")
        print(f"\n{len(ECHECS)} ECHEC(S)")
        return 1

    def recette(contact, annonce, role="acquereur", source="non_transaction", tt="", ti=""):
        return {"contact_id": contact, "annonce_id": annonce, "role": role, "source": source,
                "transaction_type": tt, "transaction_id": ti}

    def cle(r):
        return B.stable_hash(r)[:24]

    r1 = recette("10000001", "5001")
    r2 = recette("10000002", "5001", role="mandant")
    r3 = recette("20000001", "5002", source="offre", tt="offre", ti="77")
    k1, k2, k3 = cle(r1), cle(r2), cle(r3)

    conn = sqlite3.connect(":memory:", isolation_level=None)
    q = lambda s, p=(): conn.execute(s, p).fetchone()[0]  # noqa: E731
    conn.execute("BEGIN")

    # ── nuit 1
    noter(B, {k1: (r1, 7001), k2: (r2, 7001), k3: (r3, None)})
    b = B.enregistrer_registre_relations(conn, [k1, k2, k3], "2026-09-25T03:00:00Z", complet=True)
    controle("(1) trois liens ecrits -> trois notes neuves", b.get("statut") == "ok" and b["nouveaux"] == 3
             and q("SELECT COUNT(*) FROM app_relation_registry") == 3, str(b))
    rejouables = sum(1 for k, j in conn.execute("SELECT relation_key, recette_json FROM app_relation_registry")
                     if B.stable_hash(json.loads(j))[:24] == k)
    controle("(2) la recette notee refabrique l'identifiant, 3/3", rejouables == 3, f"{rejouables}/3")
    controle("(3) notre numero de bien est note a cote du numero Hektor",
             q("SELECT app_dossier_id FROM app_relation_registry WHERE relation_key=?", (k1,)) == 7001
             and q("SELECT hektor_annonce_id FROM app_relation_registry WHERE relation_key=?", (k1,)) == "5001")
    controle("(4) le role est celui de la RECETTE (avant reecriture)",
             q("SELECT role FROM app_relation_registry WHERE relation_key=?", (k2,)) == "mandant")
    controle("(5) un lien sans numero de bien est compte", b["sans_numero_de_bien"] == 1, str(b))

    # ── nuit 2 : k2 disparu ; k3 recoit son numero de bien
    noter(B, {k1: (r1, 7001), k3: (r3, 7002)})
    b = B.enregistrer_registre_relations(conn, [k1, k3], "2026-09-26T03:00:00Z", complet=True)
    controle("(6) un lien disparu est MARQUE, pas efface",
             b["disparus_marques"] == 1 and q("SELECT COUNT(*) FROM app_relation_registry") == 3
             and q("SELECT absent_depuis FROM app_relation_registry WHERE relation_key=?", (k2,))
             == "2026-09-26T03:00:00Z", str(b))
    controle("(7) un numero de bien arrive plus tard est complete",
             q("SELECT app_dossier_id FROM app_relation_registry WHERE relation_key=?", (k3,)) == 7002)
    controle("(8) la premiere vue ne bouge jamais",
             q("SELECT first_seen_at FROM app_relation_registry WHERE relation_key=?", (k1,))
             == "2026-09-25T03:00:00Z")

    # ── nuit 3 : k2 revient
    noter(B, {k1: (r1, 7001), k2: (r2, 7001), k3: (r3, 7002)})
    b = B.enregistrer_registre_relations(conn, [k1, k2, k3], "2026-09-27T03:00:00Z", complet=True)
    controle("(9) un lien revenu perd sa marque, sans note neuve",
             b["nouveaux"] == 0
             and q("SELECT COUNT(*) FROM app_relation_registry WHERE absent_depuis IS NOT NULL") == 0, str(b))
    controle("(10) aucune ancre en conflit", b["ancres_en_conflit"] == 0, str(b))

    # ── build cible : ne voit qu'un lien, ne doit rien marquer disparu
    noter(B, {k1: (r1, 7001)})
    b = B.enregistrer_registre_relations(conn, [k1], "2026-09-27T10:00:00Z", complet=False)
    controle("(11) le build cible ne marque RIEN disparu",
             b["disparus_marques"] == 0
             and q("SELECT COUNT(*) FROM app_relation_registry WHERE absent_depuis IS NOT NULL") == 0, str(b))

    # ── une cle ecrite sans recette connue (ne doit pas arriver) : comptee, pas inventee
    b = B.enregistrer_registre_relations(conn, [k1, "cle_sans_recette"], "2026-09-27T11:00:00Z", complet=False)
    controle("(12) une cle sans recette est comptee, jamais notee",
             b["sans_recette"] == 1
             and q("SELECT COUNT(*) FROM app_relation_registry WHERE relation_key='cle_sans_recette'") == 0, str(b))

    # ── deux identifiants pour la meme ancre : le conflit est VU
    r1bis = recette("10000001", "5099")  # autre n° Hektor, MEME bien chez nous
    noter(B, {k1: (r1, 7001), cle(r1bis): (r1bis, 7001), k2: (r2, 7001), k3: (r3, 7002)})
    b = B.enregistrer_registre_relations(conn, [k1, cle(r1bis), k2, k3], "2026-09-28T03:00:00Z", complet=True)
    controle("(13) deux identifiants pour une meme ancre -> conflit compte", b["ancres_en_conflit"] == 1, str(b))
    conn.execute("COMMIT")

    # ── il ne peut PAS faire tomber le build
    c2 = sqlite3.connect(":memory:", isolation_level=None)
    c2.execute("CREATE TABLE travail_du_build (x)")
    # La panne arrive APRES une ecriture reussie (le lien neuf est deja insere quand
    # le marquage des disparus casse) : c'est ce cas que le SAVEPOINT doit annuler.
    for instruction in B.REGISTRE_RELATIONS_DDL.strip().split(";"):
        if instruction.strip():
            c2.execute(instruction)
    c2.execute("INSERT INTO app_relation_registry (relation_key, contact_id, recette_json, "
               "first_seen_at, last_seen_at) VALUES ('ancienne', '1', '{}', 'x', '2000-01-01')")
    c2.execute("CREATE TRIGGER panne BEFORE UPDATE OF absent_depuis ON app_relation_registry "
               "BEGIN SELECT RAISE(ABORT, 'panne simulee'); END")
    c2.execute("BEGIN")
    c2.execute("INSERT INTO travail_du_build VALUES (1)")
    noter(B, {k1: (r1, 7001)})
    try:
        b = B.enregistrer_registre_relations(c2, [k1], "2026-09-28T03:00:00Z", complet=True)
        leve = False
    except Exception:  # noqa: BLE001
        leve, b = True, {}
    controle("(14) une erreur du carnet ne leve pas", not leve and b.get("statut") == "erreur", str(b))
    controle("(15) le travail du build reste intact et la transaction ouverte",
             c2.in_transaction and c2.execute("SELECT COUNT(*) FROM travail_du_build").fetchone()[0] == 1)
    controle("(16) le lien insere avant la panne a ete annule",
             c2.execute("SELECT COUNT(*) FROM app_relation_registry").fetchone()[0] == 1)
    c2.execute("COMMIT")

    # ── le build complet l'appelle, le build cible jamais
    source = Path(args.build).read_text(encoding="utf-8").replace("\r\n", "\n")
    appels = source.count("enregistrer_registre_relations(\n")
    controle("(17) un seul appel au carnet (definition + appel)", appels == 2, f"{appels}")
    debut_cible = source.find("def refresh_contact_slice")
    fin_cible = source.find("\ndef ", debut_cible + 10)
    controle("(18) le build cible n'appelle pas le carnet",
             debut_cible > 0 and "enregistrer_registre_relations" not in source[debut_cible:fin_cible])
    controle("(19) l'identifiant est hache sur la recette notee",
             "relation_key = stable_hash(recette)[:24]" in source and '"recette": recette' in source)

    print(f"\n{'TOUT VERT' if not ECHECS else str(len(ECHECS)) + ' ECHEC(S)'} ({TOTAL - len(ECHECS)}/{TOTAL})")
    return 1 if ECHECS else 0


if __name__ == "__main__":
    sys.exit(main())
