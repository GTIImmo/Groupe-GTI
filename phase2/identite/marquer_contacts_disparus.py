#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C.16 — LES CONTACTS QUE HEKTOR NE CONNAIT PLUS.            21/09/2026

CE QUE HEKTOR DIT, ET QU'ON NE NOTAIT NULLE PART. Quand une fiche est supprimee
chez lui, son detail repond 404. Le pipeline le sait -- il tient une liste noire
pour ne pas s'acharner (sync_contact_detail_skip, 7 659 fiches en 404) -- mais
RIEN ne le disait au serveur ni a l'app : la fiche restait « normale », et
seule une modification aurait revele le probleme, en finissant en conflit.

LA REGLE DU PROJET : ON NE SUPPRIME JAMAIS, ON MARQUE. `absent_depuis` existe
dans le registre depuis le 25/08, pose exactement pour ce cas -- et n'avait
jamais servi (0 ligne marquee sur 356 111). Effacer la fiche orphelinerait tout
ce qui pend dessus, sans que rien ne le signale : mesure du 24/08, AUCUNE
contrainte de cle etrangere ne protege les 18 tables qui pointent le contact.

MESURE DU 21/09, et elle corrige le plan :
    fiches que Hektor ne connait plus       7 659
       dont actives cote serveur            2 205
       dont archivees                       5 453
    ⚠ DANS L'APP, il n'en reste qu'UNE SEULE active. Le plan parlait de « 825
      fiches actives » : le chiffre a vieilli parce que l'app ne porte que les
      contacts ELIGIBLES (relation ou recherche active) -- en perdant leur
      eligibilite, ces fiches ont quitte l'app d'elles-memes.

IDEMPOTENT : rejouer n'ecrit rien de plus et affiche 0.
RETOUR ARRIERE : UPDATE app_contact SET absent_depuis = NULL.
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
MIROIR = RACINE / "data" / "hektor.sqlite"


def main() -> int:
    parser = argparse.ArgumentParser(description="Marque les contacts que Hektor ne connait plus.")
    parser.add_argument("--dry-run", action="store_true", help="Compter sans ecrire.")
    args = parser.parse_args()

    miroir = sqlite3.connect(f"file:{MIROIR}?mode=ro", uri=True)
    disparus = [str(r[0]) for r in miroir.execute(
        "SELECT hektor_contact_id FROM sync_contact_detail_skip WHERE reason LIKE '%404%'")]
    miroir.close()
    if not disparus:
        print("[contacts-disparus] la liste noire est vide -- rien a marquer.")
        return 0

    # GARDE-FOU : si la liste noire explose, on ne marque pas le parc entier sur
    # un incident d'une nuit. 7 659 fiches aujourd'hui ; au-dela de 20 000 on
    # s'arrete et on regarde.
    if len(disparus) > 20000:
        print(f"REFUS : {len(disparus)} fiches en liste noire (plafond 20 000).")
        print("        Un incident de lecture est plus probable qu'une suppression de masse.")
        return 3

    conn = sqlite3.connect(str(BASE), timeout=60)
    conn.execute("PRAGMA busy_timeout = 30000")
    maintenant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marques = 0
    for lot in (disparus[i:i + 400] for i in range(0, len(disparus), 400)):
        places = ",".join("?" for _ in lot)
        # ── G-9, 23/09/2026 : LES DEUX NUMEROS, ICI AUSSI ───────────────────
        # La liste noire vient du MIROIR : ce sont des numeros de Hektor. Le
        # registre, lui, sera range par IDENTITE des la bascule. Sans le second
        # terme, ce script ne marquerait plus personne -- et il l'annoncerait
        # tranquillement : « 0 nouvellement marquee ». Une fonction qui meurt en
        # disant zero est pire qu'une qui leve.
        # `app_contact.hektor_target_id` a ete pose le 23/09 (356 156 lignes).
        if args.dry_run:
            n = conn.execute(
                f"SELECT COUNT(*) FROM app_contact WHERE absent_depuis IS NULL "
                f"AND (hektor_contact_id IN ({places}) OR hektor_target_id IN ({places}))",
                [*lot, *lot]).fetchone()[0]
            marques += n
            continue
        cur = conn.execute(
            f"UPDATE app_contact SET absent_depuis = ?, updated_at = ? "
            f"WHERE absent_depuis IS NULL "
            f"AND (hektor_contact_id IN ({places}) OR hektor_target_id IN ({places}))",
            [maintenant, maintenant, *lot, *lot])
        marques += cur.rowcount or 0
    if not args.dry_run:
        conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM app_contact WHERE absent_depuis IS NOT NULL").fetchone()[0]
    print(f"[contacts-disparus] {len(disparus)} fiche(s) inconnues de Hektor, "
          f"{marques} nouvellement marquee(s){' (dry-run)' if args.dry_run else ''} "
          f"-- total marque : {total}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
