#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C-6 — REPETITION : le miroir ne recoit que des numeros de Hektor.
                                                                  23/09/2026

`data/hektor.sqlite` est L'ARCHIVE DE TOUT CE QUE HEKTOR A DIT, pour toujours.
Y ecrire un numero ne dans l'app le ferait mentir -- et le run suivant relirait
cette fiche vide comme un vrai contact.

LE CHEMIN QUI L'Y AMENAIT, en trois pas :
  1. sync_active_searches tire sa liste de NOTRE couche ;
  2. il la passe telle quelle a `normalize_source --contact-id` ;
  3. dans upsert_contacts, un id sans detail connu devient `{"id": contact_id}`
     et arrive a la porte d'ecriture -- qui ne verifiait rien.

Et le meme defaut existait dans refresh_contact_inproc (le rafraichissement
declenche par le worker quand on ouvre une fiche) : UN seul numero pour quatre
etapes dont deux parlent la langue de Hektor et deux la notre.

N'APPELLE NI HEKTOR NI SUPABASE. Bases en memoire.
"""
from __future__ import annotations

import io
import sqlite3
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


# ── (1) LA PORTE DU MIROIR ─────────────────────────────────────────────────
import normalize_source as norme  # noqa: E402


def miroir_temoin() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE hektor_contact ("
        " hektor_contact_id TEXT PRIMARY KEY, typologie_json TEXT,"
        " nom TEXT, prenom TEXT, source_json TEXT, updated_at TEXT)")
    return conn


conn = miroir_temoin()
try:
    ecrit = norme.upsert_contact_from_sources(conn, {"id": "10000001"})
except Exception as err:  # une exception vaudrait refus, mais on veut un refus PROPRE
    ecrit = f"exception {type(err).__name__}"
reste = conn.execute("SELECT COUNT(*) FROM hektor_contact").fetchone()[0]
controle("(1) un numero de l'app est REFUSE a la porte du miroir",
         ecrit is False, f"retour={ecrit!r}")
controle("(1) et rien n'a ete ecrit", reste == 0, f"{reste} ligne(s)")

# ── (2) LA LISTE QUI PART CHEZ HEKTOR ──────────────────────────────────────
import sync_active_searches as sas  # noqa: E402


def couche_temoin(chemin: Path) -> None:
    conn = sqlite3.connect(str(chemin))
    conn.execute("CREATE TABLE app_contact_current ("
                 " hektor_contact_id TEXT, hektor_target_id TEXT)")
    conn.execute("CREATE TABLE app_contact_search_current ("
                 " hektor_contact_id TEXT, is_active INT, archive INT)")
    # un contact ordinaire : identite = cible
    conn.execute("INSERT INTO app_contact_current VALUES ('605450','605450')")
    conn.execute("INSERT INTO app_contact_search_current VALUES ('605450',1,0)")
    # un contact NE DANS L'APP : identite a nous, cible chez Hektor
    conn.execute("INSERT INTO app_contact_current VALUES ('10000001','605999')")
    conn.execute("INSERT INTO app_contact_search_current VALUES ('10000001',1,0)")
    conn.commit()
    conn.close()


import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as dossier:
    base = Path(dossier) / "temoin.sqlite"
    couche_temoin(base)
    pour_hektor = sas.active_search_contact_ids(base)
    controle("(2) la liste qui part chez Hektor porte les CIBLES",
             pour_hektor == ["605450", "605999"], str(pour_hektor))
    controle("(2) aucun numero de l'app n'y figure",
             all(int(i) < 10_000_000 for i in pour_hektor), str(pour_hektor))

    retour = sas.identites_pour_ces_cibles(base, pour_hektor)
    controle("(2) le chemin inverse rend NOS numeros pour les etapes locales",
             retour == ["605450", "10000001"], str(retour))
    controle("(2) une cible inconnue de la couche se rend elle-meme",
             sas.identites_pour_ces_cibles(base, ["777777"]) == ["777777"])

# ── (3) LES QUATRE ETAPES DU RAFRAICHISSEMENT ──────────────────────────────
src_inproc = io.open(RACINE / "phase2" / "sync" / "refresh_contact_inproc.py",
                     encoding="utf-8").read()
controle("(3) le rafraichissement distingue les deux langues",
         "pour_hektor = cible_hektor(identite)" in src_inproc)
controle("(3) Hektor et le miroir recoivent la CIBLE",
         src_inproc.count('"--contact-id", pour_hektor') == 2, )
controle("(3) le build et le push recoivent l'IDENTITE",
         src_inproc.count('"--contact-id", identite') == 2)

src_sas = io.open(RACINE / "phase2" / "sync" / "sync_active_searches.py",
                  encoding="utf-8").read()
controle("(3) les etapes locales ne partagent plus une seule liste",
         "csv_hektor" in src_sas and "csv_app" in src_sas)

# ── LA PREUVE : CES CONTROLES ATTRAPENT-ILS LA VERSION D'AVANT ? ───────────
try:
    for rel, motif, nom in (
        ("normalize_source.py", "REFUS d'ecrire le numero d'app",
         "PREUVE : la porte du miroir n'existait pas avant"),
        ("phase2/sync/refresh_contact_inproc.py", "pour_hektor = cible_hektor(identite)",
         "PREUVE : le rafraichissement ne distinguait rien avant"),
        ("phase2/sync/sync_active_searches.py", "csv_hektor",
         "PREUVE : les etapes locales partageaient une liste avant"),
    ):
        avant = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(RACINE),
                               capture_output=True, text=True, encoding="utf-8", timeout=30)
        if avant.returncode == 0 and avant.stdout:
            controle(nom, motif not in avant.stdout, "le motif y est deja")
        else:
            print(f"  ---  {rel} illisible en HEAD, preuve non faite")
except Exception as err:  # pragma: no cover
    print(f"  ---  preuve non faite : {type(err).__name__}")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Tous les controles passent : le miroir reste une copie de Hektor.")
