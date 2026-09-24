#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE REGISTRE NE DOIT JAMAIS DONNER DEUX NUMEROS A LA MEME PERSONNE.
                                                                  24/09/2026

POURQUOI CE FICHIER EXISTE. Le matin du 24/09, au premier run apres la bascule,
`app_contact` est passe de 356 166 a 650 353 lignes : 294 179 PERSONNES ONT RECU
UNE SECONDE IDENTITE, en une nuit, sans une erreur, sans une alerte.

LA CAUSE, et elle est instructive. La veille j'avais traduit TOUT le registre
(356 166 lignes) en identites. Mais le build ne traduit la couche que pour les
contacts dont il a une CORRESPONDANCE -- et cette correspondance etait descendue
de Supabase, qui ne connait que le PERIMETRE ELIGIBLE (61 985). Les 294 187
autres repartaient donc sous leur numero de Hektor ; le registre ne les
reconnaissait plus, et leur donnait un numero neuf.

⚠ CE N'EST PAS UNE ERREUR DE CODE, C'EST UNE ERREUR DE PORTEE. Les deux cotes
  etaient corrects pris separement. C'est leur DESACCORD qui a fabrique le degat
  -- et rien ne surveillait cet accord.

LE CORRECTIF : la correspondance vient d'abord du REGISTRE LOCAL, qui connait
les 356 166 paires, et plus seulement de la table descendue. « Supabase RECOIT
la serie, il ne la fabrique jamais » (regle du 19/08).

CE CONTROLE NE VERIFIE PAS QU'UN MECANISME EXISTE -- il verifie que les deux
cotes SONT D'ACCORD. C'est la seule forme qui aurait vu passer ce defaut.

NE TOUCHE A RIEN. Lecture seule.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
PLAGE_APP = 10_000_000
echecs: list[str] = []


def controle(nom: str, condition: bool, detail: str = "") -> None:
    print(f"{'  OK  ' if condition else 'ECHEC '} {nom}{'' if condition else ' -- ' + detail}")
    if not condition:
        echecs.append(nom)


conn = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
conn.execute("PRAGMA busy_timeout = 30000")
q = lambda s, p=(): conn.execute(s, p).fetchone()[0]

# ── ① UNE PERSONNE, UN NUMERO ─────────────────────────────────────────────
# Le signe du degat : une ligne en numero de Hektor alors qu'une AUTRE ligne
# porte deja ce numero dans sa case cible. C'est litteralement « deux fiches
# pour une personne » dans le registre d'identite.
doublons = q("""
  SELECT COUNT(*) FROM app_contact n
   WHERE CAST(n.hektor_contact_id AS INTEGER) < ?
     AND EXISTS (SELECT 1 FROM app_contact o
                  WHERE o.hektor_target_id = n.hektor_contact_id
                    AND CAST(o.hektor_contact_id AS INTEGER) >= ?)""", (PLAGE_APP, PLAGE_APP))
controle("(1) aucune personne n'a deux lignes dans le registre",
         doublons == 0, f"{doublons} doublon(s)")

controle("(1) un numero d'identite, une seule ligne",
         q("SELECT COUNT(*) FROM app_contact") == q("SELECT COUNT(DISTINCT app_contact_id) FROM app_contact"))

# ── ② LE NUMERO DE HEKTOR N'EST JAMAIS PERDU ──────────────────────────────
sans_cible = q("SELECT COUNT(*) FROM app_contact WHERE hektor_target_id IS NULL")
controle("(2) aucune fiche ne perd son numero de Hektor",
         sans_cible == 0, f"{sans_cible} sans case cible")

# ── ③ L'ACCORD ENTRE LE REGISTRE ET LA COUCHE ─────────────────────────────
# LE CONTROLE QUI MANQUAIT. Une fiche que le registre a numerotee doit etre
# rangee sous CETTE identite dans la couche -- sinon le registre la reverra
# comme inconnue au prochain run et lui donnera un second numero.
desaccord = q("""
  SELECT COUNT(*) FROM app_contact_current c
   JOIN app_contact r ON r.hektor_target_id = c.hektor_contact_id
  WHERE CAST(c.hektor_contact_id AS INTEGER) < ?
    AND CAST(r.hektor_contact_id AS INTEGER) >= ?""", (PLAGE_APP, PLAGE_APP))
controle("(3) la couche et le registre parlent de la MEME personne",
         desaccord == 0,
         f"{desaccord} fiche(s) rangees sous leur numero Hektor alors que le registre "
         f"leur a deja donne une identite -- elles recevront un SECOND numero au prochain run")

# ── ④ LE COULOIR N'A PAS DEBORDE ──────────────────────────────────────────
# La doublure vit de 10 000 001 a 19 999 999. Au-dela, c'est la plage des
# objets NES DANS L'APP : y deborder, c'est donner le meme numero a deux choses.
plus_haut = q("SELECT COALESCE(MAX(app_contact_id), 0) FROM app_contact")
controle("(4) la serie reste dans le couloir de la doublure",
         plus_haut < 20_000_000, f"le plus haut est {plus_haut}")

# ── ⑤ L'IDENTITE EST DANS LA COLONNE D'IDENTITE (L4-c-bis, 24/09) ──────────
# Les quatre points ci-dessus cherchent des DOUBLONS. Ils n'ont pas vu le defaut
# inverse : 23 contacts numerotes par le registre, mais dont le numero de Hektor
# occupait la colonne d'identite -- donc jamais traduits par le build.
mal_ranges = q("""SELECT COUNT(*) FROM app_contact
                   WHERE CAST(hektor_contact_id AS INTEGER) < ?
                     AND app_contact_id >= ?""", (PLAGE_APP, PLAGE_APP))
controle("(5) l'identite de chaque contact est dans la colonne d'identite",
         mal_ranges == 0, f"{mal_ranges} contact(s) numerote(s) mais range(s) sous leur n° Hektor")

print()
print(f"   registre : {q('SELECT COUNT(*) FROM app_contact')} lignes, "
      f"plus haut numero {plus_haut}")
conn.close()

if echecs:
    print()
    print(f"{len(echecs)} controle(s) en ECHEC : " + ", ".join(echecs))
    sys.exit(1)
print("Une personne, un numero -- et la couche est d'accord avec le registre.")
