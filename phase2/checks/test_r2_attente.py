#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑧ R2 -- LA NUIT RESPECTE L'ATTENTE : essai hors ligne.                               25/10/2026

Etude : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md §12, §52 (decision A de Frederic :
pas de duree maximale, la protection ne tombe qu'au verdict « arrivee »).

CE QU'IL EPROUVE, DANS CET ORDRE
--------------------------------
  ⓵ LA FONCTION seule (`respecter_l_attente`) sur un petit registre en memoire : chaque regle, une par une
     (origine, verdict, genre, juge sur le registre, meme valeur), l'interrupteur, la lecture en panne.
  ⓶ LA VRAIE NUIT, SUR DES COPIES, avec LE VRAI CARNET lu une fois chez Supabase (lecture seule) :
     - TEMOIN INVERSE : la version d'AVANT (git HEAD) et la neuve ETEINTE rendent le meme registre, a l'octet
       (hors horodatages du run) -- ce fichier tourne chaque nuit des qu'il est enregistre ;
     - ALLUMEE : seules les valeurs annoncees changent (le 25/10 : 1001395.prix_net_vendeur -> 110000.00),
       et AUCUNE chaine ne bouge.

⚠ IL N'ECRIT RIEN DE VRAI : phase2.sqlite est lu en LECTURE SEULE et recopie dans un dossier temporaire ;
  le miroir de Hektor est attache en LECTURE SEULE ; Supabase n'est que LU, une fois. Jamais de --push.

    python -I phase2/checks/test_r2_attente.py
    sortie 0 = vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SYNC = RACINE / "phase2" / "sync"
PHASE2 = RACINE / "phase2" / "phase2.sqlite"
HEKTOR = RACINE / "data" / "hektor.sqlite"
TABLES = ("app_affaire_ledger", "app_affaire_ledger__sb", "app_console_job", "app_contact", "app_dossier")
HORODATAGES = {"first_seen_at", "last_seen_at"}
INTERRUPTEUR = "APP_AFFAIRE_R2_ATTENTE"

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8")
    except Exception:                                               # noqa: BLE001
        pass
sys.path.insert(0, str(SYNC))

R: list[tuple[str, bool, str]] = []


def ok(nom: str, vrai: bool, detail: str = "") -> None:
    R.append((nom, bool(vrai), detail))


def charger(nom: str, chemin: Path):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                                    # type: ignore[union-attr]
    return mod


def allume(valeur: str | None):
    if valeur is None:
        os.environ.pop(INTERRUPTEUR, None)
    else:
        os.environ[INTERRUPTEUR] = valeur


# ── ⓵ LA FONCTION ─────────────────────────────────────────────────────────
COLS = ("montant", "date", "date_acte", "sequestre", "prix_net_vendeur", "honoraires_entree", "numero_mandat",
        "jours_validite")


def petit_registre(lignes: list[dict]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute(f"CREATE TABLE app_affaire_ledger (app_affaire_id INTEGER PRIMARY KEY, kind TEXT, {', '.join(c + ' TEXT' for c in COLS)})")
    for l in lignes:
        con.execute(f"INSERT INTO app_affaire_ledger (app_affaire_id, kind, {', '.join(COLS)}) VALUES (?, ?, {', '.join('?' * len(COLS))})",
                    (l["id"], l["kind"], *[l.get(c) for c in COLS]))
    con.commit()
    return con


def valeur(con, aid: int, col: str):
    return con.execute(f"SELECT {col} FROM app_affaire_ledger WHERE app_affaire_id=?", (aid,)).fetchone()[0]


def C(aid, champ, v, etat=None, origine="creation_app"):
    return {"app_affaire_id": aid, "champ": champ, "valeur_app": v, "origine": origine, "etat": etat}


def essais_fonction(mod) -> None:
    reg = [{"id": 1, "kind": "vente", "prix_net_vendeur": None, "date_acte": None, "jours_validite": None,
            "numero_mandat": "18787", "montant": "115000.00", "date": "2026-10-23 17:41:00"},
           {"id": 2, "kind": "compromis", "prix_net_vendeur": "126000.00", "date": "2026-10-22", "jours_validite": None,
            "sequestre": None, "montant": "135000.00"},
           {"id": 3, "kind": "offre", "date": "2026-10-06 16:12:54", "montant": "16000", "jours_validite": "10",
            "numero_mandat": "18426"}]
    carnet = [
        C(1, "prix_net_vendeur", "110000.00", "sans_objet"),       # ✅ le cas du 24/10
        C(1, "date_acte", "2026-12-15", "sans_objet"),              # ❌ genre (R1 ne l'ecrit pas pour une vente)
        C(1, "jours_validite", "15", "sans_objet"),                 # ❌ genre
        C(1, "numero_mandat", "99999", "en_attente"),               # ❌ juge sur le registre
        C(1, "montant", "115000", "en_attente"),                    # ❌ meme valeur (115000 = 115000.00)
        C(2, "sequestre", "6000", "en_attente"),                    # ✅ en attente, registre vide
        C(2, "prix_net_vendeur", "120000", "conflit"),              # ✅ A : un conflit reste protege
        C(2, "date", "2026-10-21", "echec"),                        # ❌ echec : rien n'est parti
        C(2, "montant", "140000", "arrivee"),                       # ❌ arrivee : la protection est tombee
        C(2, "jours_validite", "10", None),                         # ❌ genre
        C(3, "date", "2026-10-05", "en_attente"),                   # ❌ date d'une offre : jugee sur le registre
        C(3, "montant", "160000", "en_attente", "saisie_app"),      # ❌ jamais envoyee
        C(3, "jours_validite", "12", "inconnu", "modification_app"),  # ✅ modification, sans verdict tranche
        C(3, "montant", "17000", None, "classeur"),                 # ❌ classeur
    ]
    allume("1")
    con = petit_registre(reg)
    r = mod.respecter_l_attente(con, carnet)
    attendu = {(1, "prix_net_vendeur"): "110000.00", (2, "sequestre"): "6000", (2, "prix_net_vendeur"): "120000",
               (3, "jours_validite"): "12"}
    inchange = {(1, "date_acte"): None, (1, "jours_validite"): None, (1, "numero_mandat"): "18787",
                (1, "montant"): "115000.00", (2, "date"): "2026-10-22", (2, "montant"): "135000.00",
                (2, "jours_validite"): None, (3, "date"): "2026-10-06 16:12:54", (3, "montant"): "16000"}
    ok("(1) le net vendeur d'une vente (sans objet chez Hektor) est repose : 110000.00",
       valeur(con, 1, "prix_net_vendeur") == "110000.00", str(r))
    ok("(2) reposes : exactement les 4 attendus (vente net, compromis sequestre + conflit, offre validite modifiee)",
       all(valeur(con, a, c) == v for (a, c), v in attendu.items()) and len(r.get("reposees", [])) == 4, str(r))
    ok("(3) intacts : genre, n de mandat, date d'offre, echec, arrivee, saisie_app, classeur, meme valeur",
       all(valeur(con, a, c) == v for (a, c), v in inchange.items()),
       str({(a, c): valeur(con, a, c) for (a, c) in inchange}))
    ok("(4) le journal nomme chaque valeur reposee (une ligne par valeur)",
       any("1.prix_net_vendeur : (vide) -> 110000.00" in x for x in r.get("reposees", [])), str(r))
    con.close()

    allume(None)
    con = petit_registre(reg)
    r = mod.respecter_l_attente(con, carnet)
    ok("(5) TEMOIN : interrupteur absent -> rien n'est lu, rien ne change", r == {"statut": "eteint"}
       and valeur(con, 1, "prix_net_vendeur") is None and valeur(con, 2, "sequestre") is None, str(r))
    con.close()

    allume("1")
    con = petit_registre(reg)
    garde = mod.lire_le_carnet_supabase

    def panne():
        raise RuntimeError("HTTP 503 simule")
    mod.lire_le_carnet_supabase = panne
    try:
        jete = False
        try:
            r = mod.respecter_l_attente(con)
        except Exception:                                           # noqa: BLE001
            jete = True
    finally:
        mod.lire_le_carnet_supabase = garde
    ok("(6) lecture du carnet en panne : rien ne change, AUCUNE exception (la nuit continue), et il le dit",
       not jete and r.get("statut") == "erreur" and valeur(con, 1, "prix_net_vendeur") is None, str(r))
    con.close()

    ok("(7) meme valeur : jour = jour avec heure, 168500 = 168500.00, une autre date non",
       mod._meme_valeur("2026-10-06", "2026-10-06 16:12:54") and mod._meme_valeur("168500", "168500.00")
       and not mod._meme_valeur("2026-10-06", "2026-10-07 10:00:00") and not mod._meme_valeur("110000", None), "")
    allume(None)

    # (7b) LES DEUX COPIES DE LA REGLE « quel champ pour quel genre » : celle de R2 et celle de la creation (R1),
    #      lue dans le generateur du patch pose (« colonne = case when v_kind = ... » / « in (...) »).
    import re
    r1 = (RACINE / "phase2" / "checks" / "gen_patch_r1_affaire_nait_complete.py").read_text(encoding="utf-8")
    ecarts = []
    for col in ("jours_validite", "date_acte", "sequestre", "prix_net_vendeur", "honoraires_entree"):
        m = re.search(rf"\b{col}\s*=\s*case when v_kind (?:= '(\w+)'|in \(([^)]*)\))", r1)
        genres_r1 = {m.group(1)} if m and m.group(1) else set(re.findall(r"'(\w+)'", m.group(2))) if m else None
        genres_r2 = {g for g, champs in mod.R2_CHAMPS_PAR_GENRE.items() if col in champs}
        if genres_r1 != genres_r2:
            ecarts.append((col, genres_r1, genres_r2))
    ok("(7b) la table de R2 par genre = celle de la creation (R1), colonne par colonne", not ecarts, str(ecarts))


# ── ⓶ LA VRAIE NUIT, SUR DES COPIES ──────────────────────────────────────
def fabriquer_copie(dossier: Path, nom: str) -> Path:
    cible = dossier / f"{nom}.sqlite"
    src = sqlite3.connect(f"file:{PHASE2.as_posix()}?mode=ro", uri=True, timeout=30)
    dst = sqlite3.connect(cible)
    for t in TABLES:
        for (sql,) in src.execute("select sql from sqlite_master where tbl_name=? and sql is not null "
                                  "and type in ('table', 'index') "
                                  "order by case type when 'table' then 0 else 1 end", (t,)):
            dst.execute(sql)
        cols = [r[1] for r in src.execute(f"PRAGMA table_info({t})")]
        dst.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                        src.execute(f"SELECT {','.join(cols)} FROM {t}"))
    dst.commit()
    src.close()
    dst.close()
    return cible


def jouer(mod, base: Path) -> dict:
    con = sqlite3.connect(f"file:{base.as_posix()}", uri=True, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("ATTACH DATABASE ? AS hektor", (f"file:{HEKTOR.as_posix()}?mode=ro",))
    res = mod.refresh_ledger(con, full=True)
    con.commit()
    con.close()
    return res


def lignes(base: Path) -> dict[int, dict]:
    con = sqlite3.connect(base)
    con.row_factory = sqlite3.Row
    out = {int(r["app_affaire_id"]): {k: r[k] for k in r.keys() if k not in HORODATAGES}
           for r in con.execute("SELECT * FROM app_affaire_ledger")}
    con.close()
    return out


def essais_nuit(mod_neuf, dossier: Path, carnet: list[dict]) -> None:
    head = dossier / "affaire_ledger_head.py"
    head.write_text(subprocess.run(["git", "show", "HEAD:phase2/sync/affaire_ledger.py"], cwd=RACINE,
                                   capture_output=True, text=True, encoding="utf-8", check=True).stdout,
                    encoding="utf-8")
    mod_head = charger("affaire_ledger_head", head)
    ok("(8) la version d'AVANT ne connait pas R2 (sinon le temoin ne temoigne de rien)",
       not hasattr(mod_head, "respecter_l_attente"), "")
    mod_neuf.lire_le_carnet_supabase = lambda: carnet        # le carnet LU une fois : la meme photo partout
    a, b, c = (fabriquer_copie(dossier, n) for n in ("avant", "eteint", "allume"))
    allume(None)
    jouer(mod_head, a)
    jouer(mod_neuf, b)
    la, lb = lignes(a), lignes(b)
    diff = [k for k in la if la[k] != lb.get(k)] + [k for k in lb if k not in la]
    ok(f"(9) TEMOIN INVERSE : eteinte, la nuit neuve rend le registre de la nuit d'avant ({len(la)} lignes)",
       not diff and len(la) == len(lb), f"{len(diff)} ligne(s) differente(s), ex. {diff[:5]}")

    allume("1")
    try:
        res = jouer(mod_neuf, c)
    finally:
        allume(None)
    lc = lignes(c)
    ecarts = sorted((k, col, lb[k][col], lc[k][col]) for k in lb for col in lb[k] if lb[k][col] != lc.get(k, {}).get(col))
    hors_annonce = [e for e in ecarts if not (e[0] == 1001395 and e[1] == "prix_net_vendeur")]
    ok("(10) allumee : 1001395.prix_net_vendeur passe de vide a 110000.00",
       lb.get(1001395, {}).get("prix_net_vendeur") in (None, "") and lc.get(1001395, {}).get("prix_net_vendeur") == "110000.00",
       f"avant {lb.get(1001395, {}).get('prix_net_vendeur')!r}, apres {lc.get(1001395, {}).get('prix_net_vendeur')!r}")
    ok("(11) allumee : RIEN d'autre ne change (aucune autre colonne, aucune autre ligne)",
       not hors_annonce, f"{len(hors_annonce)} ecart(s), ex. {hors_annonce[:5]}")
    chaines = [e for e in ecarts if e[1] == "app_chaine_id"]
    ok("(12) allumee : AUCUNE chaine ne bouge", not chaines, f"ex. {chaines[:5]}")
    r2 = (res or {}).get("r2") or {}
    ok("(13) le compte rendu de la nuit porte R2 (fait, 1 valeur nommee)",
       r2.get("statut") == "fait" and len(r2.get("reposees", [])) == 1, str(r2))


def main() -> int:
    if not PHASE2.exists() or not HEKTOR.exists():
        print("⛔ base introuvable : rien mesure")
        return 2
    neuf = charger("affaire_ledger_neuf", SYNC / "affaire_ledger.py")
    essais_fonction(neuf)
    neuf.chainage_v2_actif()                                          # charge .env (cles Supabase)
    try:
        carnet = neuf.lire_le_carnet_supabase()
    except Exception as e:                                          # noqa: BLE001
        print(f"⛔ le carnet n'a pas pu etre lu chez Supabase : {e!r}")
        return 2
    dossier = Path(tempfile.mkdtemp(prefix="essai_r2_"))
    try:
        essais_nuit(neuf, dossier, carnet)
    except Exception as e:                                          # noqa: BLE001
        print(f"⛔ la nuit n'a pas pu etre rejouee : {e!r}")
        for nom, vrai, detail in R:
            print(f"{'  OK  ' if vrai else 'ECHEC '} {nom}{'' if vrai else ' -- ' + detail}")
        return 2
    finally:
        shutil.rmtree(dossier, ignore_errors=True)
    echecs = 0
    for nom, vrai, detail in R:
        print(f"{'  OK  ' if vrai else 'ECHEC '} {nom}{'' if vrai else ' -- ' + detail}")
        echecs += 0 if vrai else 1
    print(f"\n⛔ {echecs} controle(s) en echec." if echecs else "\n✅ Tous les controles sont verts.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
