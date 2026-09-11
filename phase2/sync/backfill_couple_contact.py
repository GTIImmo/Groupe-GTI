#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE LIEN DE MENAGE, POSE SUR TOUT LE PARC.                      11/09/2026

Remplit `hektor_contact.hektor_couple_contact_id` depuis `raw_json`, ou la
valeur dort depuis toujours. AUCUN APPEL A HEKTOR : la donnee est deja chez
nous, ligne par ligne, dans la charge brute que le run garde a chaque passage.

POURQUOI CE SCRIPT EXISTE. Le run de nuit n'ecrira le lien que pour les
contacts qu'il revoit. Il travaille par delta : sans ce rattrapage, la colonne
resterait vide pour l'essentiel du parc pendant des mois.

CE QUE LE LIEN VEUT DIRE, mesure le 11/09 sur les 355 978 contacts :

    Hektor donne un numero de MENAGE a chaque contact (`refCouple`). Toutes les
    fiches d'un meme menage le partagent, et il vaut l'identifiant de celle qui
    PORTE l'identite. Quand la civilite est « Mr./Mme », Hektor cree une seconde
    fiche, vide, pour le second membre -- 133 343 chez nous, jamais remplies.

    contacts au miroir                             355 978
    sans nom ni prenom                             133 343   37,5 %
    dont nommables en suivant le lien               96 877
    liens vers une AUTRE fiche                     124 455
    dont la porteuse a disparu de Hektor            14 080   verifie par API, 404

IDEMPOTENT : rejouer n'change rien et affiche 0 mis a jour.
RETOUR ARRIERE : UPDATE hektor_contact SET hektor_couple_contact_id = NULL.
La colonne peut aussi rester, personne n'est oblige de la lire.

    python phase2/sync/backfill_couple_contact.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

MIROIR = Path(r"C:\Hektor\Projet\data\hektor.sqlite")


def valeur_du_lien(brut: str | None) -> str | None:
    """Le `refCouple` de la charge Hektor, ramene a None quand il ne dit rien.

    Hektor ecrit « 0 » pour dire « aucun menage » : meme regle que
    normalized_id() dans normalize_source.py, a l'identique et volontairement.
    """
    try:
        charge = json.loads(brut or "{}")
    except Exception:
        return None
    if not isinstance(charge, dict):
        return None
    texte = str(charge.get("refCouple") or "").strip()
    if not texte or texte in {"0", "null", "None"}:
        return None
    return texte


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Compter sans ecrire.")
    args = ap.parse_args()

    conn = sqlite3.connect(str(MIROIR))
    conn.row_factory = sqlite3.Row

    # La colonne, si le pipeline n'est pas encore passe. Meme geste que la
    # migration douce de hektor_pipeline/common.py, et aussi anodin.
    colonnes = {r["name"] for r in conn.execute("PRAGMA table_info(hektor_contact)")}
    if "hektor_couple_contact_id" not in colonnes:
        if args.dry_run:
            print("La colonne hektor_couple_contact_id n'existe pas encore.")
            return 0
        conn.execute("ALTER TABLE hektor_contact ADD COLUMN hektor_couple_contact_id TEXT")
        conn.commit()
        print("colonne hektor_couple_contact_id ajoutee")

    total = conn.execute("SELECT COUNT(*) FROM hektor_contact").fetchone()[0]
    avant = conn.execute(
        "SELECT COUNT(*) FROM hektor_contact WHERE hektor_couple_contact_id IS NOT NULL"
    ).fetchone()[0]

    a_ecrire: list[tuple[str, str]] = []
    for ligne in conn.execute(
        "SELECT hektor_contact_id, raw_json, hektor_couple_contact_id FROM hektor_contact"
    ):
        lien = valeur_du_lien(ligne["raw_json"])
        if lien and lien != (ligne["hektor_couple_contact_id"] or None):
            a_ecrire.append((lien, str(ligne["hektor_contact_id"])))

    print("contacts au miroir        %8d" % total)
    print("lien deja pose            %8d" % avant)
    print("a ecrire                  %8d" % len(a_ecrire))

    if args.dry_run:
        print("\n--dry-run : rien n'a ete ecrit.")
        return 0

    if a_ecrire:
        # Une seule transaction : ou tout le parc recoit son lien, ou rien.
        with conn:
            conn.executemany(
                "UPDATE hektor_contact SET hektor_couple_contact_id = ? WHERE hektor_contact_id = ?",
                a_ecrire,
            )

    apres = conn.execute(
        "SELECT COUNT(*) FROM hektor_contact WHERE hektor_couple_contact_id IS NOT NULL"
    ).fetchone()[0]
    print("lien pose apres           %8d" % apres)

    # ── LA VERIFICATION QUI COMPTE : la colonne dit-elle la meme chose que le
    #    brut ? On ne se contente pas d'un compte, on confronte les deux.
    ecarts = 0
    for ligne in conn.execute(
        "SELECT raw_json, hektor_couple_contact_id FROM hektor_contact"
    ):
        if valeur_du_lien(ligne["raw_json"]) != (ligne["hektor_couple_contact_id"] or None):
            ecarts += 1
    print("ecart colonne / brut      %8d   %s" % (ecarts, "OK" if ecarts == 0 else "A REGARDER"))

    conn.close()
    return 0 if ecarts == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
