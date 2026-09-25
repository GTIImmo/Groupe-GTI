#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.9-f — L'IDENTIFIANT D'UN LIEN SE FABRIQUE AVEC *NOTRE* NUMERO DE BIEN
                                                                  25/09/2026

On appelle les VRAIES fonctions du build sur une base jetable :

    (1-3) le carnet relu : ancre -> numero qui a servi, ambiguite neutralisee
    (4bis) LA VRAIE load_relations, de bout en bout
    (4-6) la recette : lien connu -> identifiant INCHANGE ; lien neuf -> notre
          numero ; sans numero chez nous -> repli sur le numero Hektor
    (7)   un lien disparu puis revenu retrouve son identifiant
    (8-9) garde-fou d'ENTREE : carnet absent ou trop court -> on ne substitue pas
    (10-12) garde-fou de SORTIE : trop d'identifiants disparus -> on recommence
    (13)  la recette notee refabrique toujours l'identifiant
    (14)  le build cible substitue AUSSI (sinon il doublerait les liens)

⚠ LA PREUVE D'ABORD : sur la version epinglee (avant C.9-f), il n'y a pas de
  substitution -- le test doit ECHOUER.
      python phase2/checks/test_c9f_numero_bien_dans_cle.py --build <fichier>
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
TOTAL = 15


def controle(nom: str, ok: bool, detail: str = "") -> None:
    print(f"  {'OK ' if ok else 'KO '} {nom}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        ECHECS.append(nom)


def charger(chemin: Path):
    sys.path.insert(0, str(RACINE))
    spec = importlib.util.spec_from_file_location("build_sous_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def base_jetable(B, notes: list[tuple], liens_ecrits: int = 0) -> sqlite3.Connection:
    """notes = (relation_key, contact, app_dossier_id, role, source, recette)."""
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row  # comme la vraie base du build
    for instruction in B.REGISTRE_RELATIONS_DDL.strip().split(";"):
        if instruction.strip():
            conn.execute(instruction)
    conn.execute("CREATE TABLE app_contact_relation_current (relation_key TEXT PRIMARY KEY)")
    conn.executemany(
        "INSERT INTO app_relation_registry (relation_key, contact_id, app_dossier_id, role,"
        " source, recette_json, first_seen_at, last_seen_at) VALUES (?,?,?,?,?,?,'x','x')",
        [(k, c, d, r, s, json.dumps(rec, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
         for k, c, d, r, s, rec in notes])
    conn.executemany("INSERT INTO app_contact_relation_current VALUES (?)",
                     [(f"bidon{i:06d}",) for i in range(liens_ecrits)])
    return conn


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=str(RACINE / "phase2" / "contacts" / "build_contacts_layer.py"))
    args = ap.parse_args()
    B = charger(Path(args.build))
    print(f"build teste : {args.build}")

    for nom in ("_CLES_FIGEES", "charger_cles_figees", "_ancre_relation", "verifier_substitution"):
        if not hasattr(B, nom):
            controle("(0) le build sait substituer le numero de bien", False,
                     f"{nom} absent -- version d'avant C.9-f")
            print(f"\n{len(ECHECS)} ECHEC(S)")
            return 1

    # ⚠ tt / ti a None, PAS "" : c'est ce que la VRAIE add_relation met dans la
    # recette hors transaction (le test de bout en bout l'a revele le 25/09).
    def recette(contact, annonce, role="acquereur", source="non_transaction", tt=None, ti=None):
        return {"contact_id": contact, "annonce_id": annonce, "role": role, "source": source,
                "transaction_type": tt, "transaction_id": ti}

    cle = lambda r: B.stable_hash(r)[:24]  # noqa: E731

    # un lien connu : fabrique jadis avec le numero HEKTOR 5001, notre bien = 7001
    r_connu = recette("10000001", "5001")
    k_connu = cle(r_connu)
    # une ancre ambigue : deux identifiants pour la meme ancre
    r_amb1, r_amb2 = recette("10000009", "5555"), recette("10000009", "5556")
    notes = [
        (k_connu, "10000001", 7001, "acquereur", "non_transaction", r_connu),
        (cle(r_amb1), "10000009", 7009, "acquereur", "non_transaction", r_amb1),
        (cle(r_amb2), "10000009", 7009, "acquereur", "non_transaction", r_amb2),
    ]

    conn = base_jetable(B, notes)
    figees, bilan = B.charger_cles_figees(conn)
    ancre_connue = B._ancre_relation("10000001", "7001", "acquereur", "non_transaction", None, None)
    controle("(1) le carnet rend le numero qui a SERVI au hache",
             figees.get(ancre_connue) == "5001", str(figees.get(ancre_connue)))
    controle("(2) une ancre ambigue est neutralisee (on ne reprend rien)",
             figees.get(B._ancre_relation("10000009", "7009", "acquereur", "non_transaction", None, None)) is None
             and bilan["ambigues"] == 1, str(bilan))
    controle("(3) l'ancre se fabrique pareil des deux cotes (JSON et Python)",
             B._ancre_relation("1", 7001, "r", "s", None, 77) == B._ancre_relation("1", "7001", "r", "s", "", "77"),
             f"{B._ancre_relation('1', 7001, 'r', 's', None, 77)}")

    # ── la recette, les trois cas
    def cle_obtenue(figees_dict, dossier_id, annonce_hektor, contact="10000001",
                    role="acquereur", source="non_transaction", tt=None, ti=None):
        """Rejoue EXACTEMENT le choix de add_relation (memes trois lignes)."""
        B._CLES_FIGEES = figees_dict
        annonce_pour_la_cle = annonce_hektor
        if dossier_id is not None:
            notre = str(dossier_id)
            f = B._CLES_FIGEES.get(B._ancre_relation(contact, notre, role, source, tt, ti))
            annonce_pour_la_cle = f if f else notre
        return cle(recette(contact, annonce_pour_la_cle, role, source, tt, ti)), annonce_pour_la_cle

    k, utilise = cle_obtenue(figees, 7001, "5001")
    controle("(4) lien CONNU -> identifiant INCHANGE", k == k_connu and utilise == "5001",
             f"{k} vs {k_connu} (numero utilise {utilise})")
    k, utilise = cle_obtenue(figees, 7002, "5002", contact="10000002")
    controle("(5) lien NEUF -> fabrique avec NOTRE numero",
             utilise == "7002" and k == cle(recette("10000002", "7002")), f"numero utilise {utilise}")
    k, utilise = cle_obtenue(figees, None, "5003", contact="10000003")
    controle("(6) sans numero chez nous -> repli sur le numero Hektor",
             utilise == "5003" and k == cle(recette("10000003", "5003")), f"numero utilise {utilise}")

    # (7) un lien revenu : sa note est marquee disparue, il doit retrouver sa cle
    conn.execute("UPDATE app_relation_registry SET absent_depuis = 'hier' WHERE relation_key = ?", (k_connu,))
    figees_apres, _ = B.charger_cles_figees(conn)
    k, _ = cle_obtenue(figees_apres, 7001, "5001")
    controle("(7) un lien disparu puis revenu retrouve son identifiant", k == k_connu, k)

    # ── LA VRAIE load_relations, DE BOUT EN BOUT ────────────────────────────
    # Rejouer la regle dans le test ne prouverait que le test. On fait donc
    # tourner la VRAIE fonction sur un miroir minimal : une seule table de liens
    # suffit a la faire passer par add_relation.
    def vrai_build(conn_test, liens: list[tuple], biens: list[tuple]):
        """liens = (annonce_hektor, contact, role) ; biens = (notre_id, annonce_hektor)."""
        conn_test.execute("CREATE TABLE IF NOT EXISTS app_dossier (id INTEGER PRIMARY KEY, hektor_annonce_id TEXT)")
        conn_test.execute("CREATE TABLE IF NOT EXISTS app_view_generale (app_dossier_id INTEGER, titre_bien TEXT)")
        for col in ("numero_dossier", "numero_mandat"):
            try:
                conn_test.execute(f"ALTER TABLE app_dossier ADD COLUMN {col} TEXT")
            except sqlite3.Error:
                pass
        conn_test.executemany("INSERT OR REPLACE INTO app_dossier (id, hektor_annonce_id) VALUES (?,?)", biens)
        miroir = sqlite3.connect(":memory:")
        miroir.row_factory = sqlite3.Row
        miroir.execute("CREATE TABLE sync_annonce_contact_link (hektor_annonce_id TEXT,"
                       " hektor_contact_id TEXT, role_contact TEXT, contact_date_maj TEXT, last_seen_at TEXT)")
        miroir.executemany("INSERT INTO sync_annonce_contact_link VALUES (?,?,?,NULL,NULL)", liens)
        lignes, _ = B.load_relations(miroir, conn_test)
        return {(r["hektor_contact_id"], r["hektor_annonce_id"]): r["relation_key"]
                for rows in lignes.values() for r in rows}

    conn_bout = base_jetable(B, notes)
    conn_bout.executemany("INSERT INTO app_contact_relation_current VALUES (?)",
                          [(k_connu,)] + [(f"bidon{i}",) for i in range(2)])
    obtenues = vrai_build(conn_bout,
                          [("5001", "10000001", "acquereur"), ("5002", "10000002", "acquereur")],
                          [(7001, "5001"), (7002, "5002")])
    controle("(4bis) LA VRAIE load_relations : lien connu INCHANGE, lien neuf sous notre numero",
             obtenues.get(("10000001", "5001")) == k_connu
             and obtenues.get(("10000002", "5002")) == cle(recette("10000002", "7002", role="acquereur")),
             str(obtenues))

    # ── garde-fou d'ENTREE (via la vraie load_relations, miroir vide)
    def figees_apres_chargement(conn_test):
        miroir = sqlite3.connect(":memory:")
        miroir.row_factory = sqlite3.Row
        try:
            B.load_relations(miroir, conn_test)
        except Exception:  # le miroir vide fera tomber la suite : seul le debut nous interesse
            pass
        return dict(B._CLES_FIGEES)

    conn_court = base_jetable(B, notes, liens_ecrits=5000)  # 3 ancres pour 5 000 liens
    controle("(8) carnet trop court -> on ne substitue PAS", figees_apres_chargement(conn_court) == {},
             f"{len(figees_apres_chargement(conn_court))} ancres retenues")
    conn_vide = base_jetable(B, [], liens_ecrits=5000)
    controle("(9) carnet vide -> on ne substitue PAS", figees_apres_chargement(conn_vide) == {})

    # ── garde-fou de SORTIE
    conn_sortie = base_jetable(B, notes, liens_ecrits=0)
    conn_sortie.executemany("INSERT INTO app_contact_relation_current VALUES (?)",
                            [(f"ancienne{i:05d}",) for i in range(3000)])
    calcule = {"c": [{"relation_key": f"neuve{i:05d}"} for i in range(3000)]}
    bilan = B.verifier_substitution(conn_sortie, calcule)
    controle("(10) trop d'identifiants disparus -> on RECOMMENCE",
             bilan["recommence"] and bilan["identifiants_disparus"] == 3000, str(bilan))
    garde = {"c": [{"relation_key": f"ancienne{i:05d}"} for i in range(2995)]}
    bilan = B.verifier_substitution(conn_sortie, garde)
    controle("(11) quelques disparitions -> on continue",
             not bilan["recommence"] and bilan["identifiants_disparus"] == 5, str(bilan))
    controle("(12) premier build (couche vide) -> jamais d'alerte",
             B.verifier_substitution(base_jetable(B, notes), {})["recommence"] is False)

    # (13) l'invariant du carnet
    ok = all(cle(json.loads(j)) == k for k, j in
             conn.execute("SELECT relation_key, recette_json FROM app_relation_registry"))
    controle("(13) la recette notee refabrique toujours l'identifiant", ok)

    # (14) le build cible substitue aussi
    source = Path(args.build).read_text(encoding="utf-8").replace("\r\n", "\n")
    debut = source.find("def refresh_contact_slice")
    bloc = source[debut:source.find("\ndef ", debut + 10)]
    controle("(14) le build cible appelle load_relations SANS couper la substitution",
             "load_relations(" in bloc and "substituer=False" not in bloc, bloc[:80])

    print(f"\n{'TOUT VERT' if not ECHECS else str(len(ECHECS)) + ' ECHEC(S)'} ({TOTAL - len(ECHECS)}/{TOTAL})")
    return 1 if ECHECS else 0


if __name__ == "__main__":
    sys.exit(main())
