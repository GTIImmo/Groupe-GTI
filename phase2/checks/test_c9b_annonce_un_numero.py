#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.9-b — le controle « une annonce, un numero » voit-il vraiment les ecarts ?
                                                                  24/09/2026

EPROUVE DANS LES DEUX SENS (regle du 23/09) : il doit rester a ZERO sur une
situation saine -- sinon il crierait chaque nuit pour rien -- ET compter chaque
ecart qu'on lui fabrique. Puis on le passe sur la vraie base, en lecture seule.

N'ECRIT RIEN dans les vraies bases. N'appelle ni Hektor ni Supabase.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
import annonce_un_numero as a1n  # noqa: E402

echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


_reel = sqlite3.connect(f"file:{a1n.BASE.as_posix()}?mode=ro", uri=True)
DDL = _reel.execute("SELECT sql FROM sqlite_master WHERE name='app_dossier'").fetchone()[0]
_reel.close()


def base(serveur, supabase, adoptions=None, travaux=()) -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.execute(DDL)
    c.execute("CREATE TABLE app_dossier_current (app_dossier_id, hektor_annonce_id)")
    c.executemany("INSERT INTO app_dossier (id, hektor_annonce_id) VALUES (?, ?)", serveur)
    c.executemany("INSERT INTO app_dossier_current VALUES (?, ?)", supabase)
    if adoptions is not None:
        c.execute("CREATE TABLE app_dossier_adoption (app_dossier_id INTEGER PRIMARY KEY, "
                  "hektor_annonce_id INTEGER NOT NULL, adopte_le TEXT)")
        c.executemany("INSERT INTO app_dossier_adoption VALUES (?, ?, NULL)", adoptions)
    # 4c (11/10/2026) : la doublure des travaux, qui porte LA COUPURE entre une
    # attente normale et une creation echouee. `travaux=None` simule son absence
    # -- la mesure doit alors se declarer AVEUGLE, jamais rendre un zero.
    # Le numero du dossier vit dans la CHARGE du travail (la colonne, elle, est
    # vide sur les 79 creations reelles -- mesure du 11/10).
    if travaux is not None:
        c.execute("CREATE TABLE app_console_job (id, job_type, app_dossier_id, "
                  "payload_json, status)")
        c.executemany(
            "INSERT INTO app_console_job VALUES (?, ?, NULL, ?, ?)",
            [(f"job-{i}", genre, '{"app_dossier_id": %d}' % dossier, etat)
             for i, (genre, dossier, etat) in enumerate(travaux)])
    return c


def mesure(serveur, supabase, adoptions=None, travaux=()) -> dict:
    c = base(serveur, supabase, adoptions, travaux)
    try:
        return a1n.mesurer(c)
    finally:
        c.close()


CREATION = "create_hektor_draft_annonce"


SAIN_S = [(1, 100), (2, 101), (3, 102)]           # 3 : archivee, absente de Supabase -- normal
SAIN_SB = [(1, 100), (2, 101)]

m = mesure(SAIN_S, SAIN_SB)
controle("(0) une situation saine reste a ZERO", m["graves"] == 0 and m["en_attente"] == 0, str(m))

m = mesure(SAIN_S, [(str(i), str(h)) for i, h in SAIN_SB])
controle("(0) des numeros stockes en TEXTE ne font pas crier pour rien", m["graves"] == 0, str(m))

# Les comparaisons A LA PLAGE (< / >= 10 000 000) se trompent sur du texte sans
# conversion : '5' < 10000000 est FAUX pour SQLite (le texte passe apres les nombres).
# La mutation du 24/09 l'a montre : sans ces deux cas, retirer le CAST ne faisait rien
# echouer -- le test ne prouvait pas qu'il sert.
m = mesure([(1, 100)], [("1", "100"), ("5", "105")])
controle("(0) en TEXTE, un numero de la plage Hektor inconnu est quand meme COMPTE",
         m["inconnus_du_serveur"] == 1, str(m))
m = mesure([(1, 100)], [("1", "100"), ("10000002", None)])
controle("(0) en TEXTE, une annonce qui attend reste « en attente », pas grave",
         m["en_attente"] == 1 and m["graves"] == 0, str(m))

m = mesure([(1, 100), (7, 63200)], [(1, 100), (10000001, 63200)])
controle("(1) D1 : une annonce Hektor avec deux numeros est COMPTEE",
         m["deux_numeros"] == 1 and m["graves"] >= 1, str(m))

m = mesure([(1, 100)], [(1, 999)])
controle("(2) un numero qui vise deux annonces Hektor est COMPTE", m["croisements"] == 1, str(m))

m = mesure([(1, 100)], [(1, 100), (5, 105)])
controle("(3) un numero de la plage Hektor inconnu du serveur est COMPTE",
         m["inconnus_du_serveur"] == 1, str(m))

m = mesure(SAIN_S, SAIN_SB + [(10000002, None), (10000003, 63300)])
controle("(4) une annonce nee dans l'app qui ATTEND n'est pas grave",
         m["graves"] == 0 and m["en_attente"] == 2, str(m))

m = mesure(SAIN_S + [(10000009, 500)], SAIN_SB)
controle("(5) un numero >= 10 M sans adoption est COMPTE (le compteur a deborde)",
         m["plage_sans_adoption"] == 1, str(m))
m = mesure(SAIN_S + [(10000009, 500)], SAIN_SB + [(10000009, 500)], adoptions=[(10000009, 500)])
controle("(5) et une adoption en regle ne l'est pas", m["graves"] == 0, str(m))

c = sqlite3.connect(":memory:")
c.execute(DDL)
controle("(6) une table manquante rend « non mesurable », pas zero", a1n.mesurer(c) is None)
c.close()

# ── (8) 4c : SEPARER L'ATTENTE NORMALE DE LA CREATION ECHOUEE ───────────────
# Eprouve dans les deux sens, et surtout SUR LE CAS PIEGE : l'attente normale va
# jusqu'a 44 minutes (file comprise, mesure du 11/10), donc le travail qui dort
# en `pending` ou tourne en `running` ne doit RIEN declencher.
APP = SAIN_SB + [(10000002, None)]

for etat in ("pending", "running", "done"):
    m = mesure(SAIN_S, APP, travaux=[(CREATION, 10000002, etat)])
    controle(f"(8a) travail « {etat} » -> on se TAIT (attente normale)",
             m["graves"] == 0 and m["en_attente"] == 1 and m["creation_echouee"] == 0, str(m))

m = mesure(SAIN_S, APP, travaux=[(CREATION, 10000002, "error")])
controle("(8b) travail « error » -> la creation echouee est COMPTEE, et c'est GRAVE",
         m["creation_echouee"] == 1 and m["graves"] >= 1 and m["en_attente"] == 0, str(m))

# La somme des deux comptes doit valoir la population d'avant : un cas ne doit
# pas se PERDRE entre les deux colonnes en passant de l'une a l'autre.
m = mesure(SAIN_S, SAIN_SB + [(10000002, None), (10000003, None), (10000004, None)],
           travaux=[(CREATION, 10000002, "error"), (CREATION, 10000003, "pending")])
controle("(8c) la somme est conservee : 1 echouee + 2 en attente = 3 nees dans l'app",
         m["creation_echouee"] == 1 and m["en_attente"] == 2, str(m))

# Un travail en erreur d'un AUTRE genre, ou qui vise un AUTRE dossier, ne compte pas.
m = mesure(SAIN_S, APP, travaux=[("update_hektor_annonce_fields", 10000002, "error"),
                                 (CREATION, 10000099, "error")])
controle("(8d) un autre genre de travail, ou un autre dossier, ne fait pas crier",
         m["creation_echouee"] == 0 and m["en_attente"] == 1 and m["graves"] == 0, str(m))

# En TEXTE aussi (la copie Supabase stocke parfois les numeros en texte).
m = mesure(SAIN_S, [("1", "100"), ("2", "101"), ("10000002", None)],
           travaux=[(CREATION, 10000002, "error")])
controle("(8e) en TEXTE, la creation echouee est quand meme COMPTEE",
         m["creation_echouee"] == 1 and m["graves"] >= 1, str(m))

# SANS la doublure des travaux : aveugle, et qui le DIT -- jamais un zero.
m = mesure(SAIN_S, APP, travaux=None)
controle("(8f) sans app_console_job : « non mesurable », PAS un zero",
         m["creation_echouee"] is None and m["creation_echouee_mesurable"] is False
         and m["en_attente"] == 1 and m["graves"] == 0, str(m))

# ── (7) la vraie base, en lecture seule ─────────────────────────────────────
reel = sqlite3.connect(f"file:{a1n.BASE.as_posix()}?mode=ro", uri=True)
t = time.time()
m = a1n.mesurer(reel)
duree = time.time() - t
reel.close()
controle("(7) la vraie base : une annonce, un numero", m is not None and m["graves"] == 0, str(m))
controle("(7) et la mesure est assez rapide pour une sonde (< 5 s)", duree < 5, f"{duree:.1f} s")
print(f"       reel : serveur {m['serveur']} · Supabase {m['supabase']} · "
      f"en attente {m['en_attente']} · {duree:.2f} s")

print()
if echecs:
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Le controle voit chaque ecart, et se tait quand tout va bien.")
