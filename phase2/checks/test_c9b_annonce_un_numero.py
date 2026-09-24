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


def base(serveur, supabase, adoptions=None) -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.execute(DDL)
    c.execute("CREATE TABLE app_dossier_current (app_dossier_id, hektor_annonce_id)")
    c.executemany("INSERT INTO app_dossier (id, hektor_annonce_id) VALUES (?, ?)", serveur)
    c.executemany("INSERT INTO app_dossier_current VALUES (?, ?)", supabase)
    if adoptions is not None:
        c.execute("CREATE TABLE app_dossier_adoption (app_dossier_id INTEGER PRIMARY KEY, "
                  "hektor_annonce_id INTEGER NOT NULL, adopte_le TEXT)")
        c.executemany("INSERT INTO app_dossier_adoption VALUES (?, ?, NULL)", adoptions)
    return c


def mesure(serveur, supabase, adoptions=None) -> dict:
    c = base(serveur, supabase, adoptions)
    try:
        return a1n.mesurer(c)
    finally:
        c.close()


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
