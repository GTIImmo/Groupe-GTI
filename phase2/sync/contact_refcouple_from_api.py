#!/usr/bin/env python3
"""Lit la case de menage (`refCouple`) de un ou plusieurs contacts, par l'API Hektor
(porte 2 / ContactById).                                                   03/11/2026

COUPLES -- « Ajouter un conjoint » (synthese couples §52-53). Le worker rattache un
conjoint chez Hektor par `contacts-create-transformeContactToConjunct`, dont la
reponse peut etre VIDE (vrai cas EA32621, 02/11) : elle ne prouve rien. Seule la
relecture de `refCouple` des DEUX fiches le prouve -- la forme normale d'un menage
Hektor est « porteuse -> elle-meme, conjoint -> la porteuse » (sonde du 02/11).

LECTURE SEULE, comme contact_datemaj_from_api.py : un appel `ContactById` par
fiche, aucune ecriture locale, ni Supabase, ni Hektor.

    python phase2/sync/contact_refcouple_from_api.py --contact-id 467326 --contact-id 467325

Sort UNE ligne JSON :
    {"lus": {"467326": {"trouve": true, "refCouple": "467326"}, ...}}
Une fiche illisible porte {"trouve": false, "erreur": "..."} : le worker ne conclut
JAMAIS sur une lecture ratee (« une lecture ratee n'est jamais un vert »).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import HektorClient, Settings  # noqa: E402

CLES_MENAGE = ("refCouple", "ref_couple", "refcouple")


def case_de_menage(contact: dict) -> str:
    """La valeur brute de la case, en texte ; '' si absente ou vide."""
    for cle in CLES_MENAGE:
        if cle in contact:
            valeur = contact.get(cle)
            return "" if valeur is None else str(valeur).strip()
    return ""


def extraire_contact(paquet: object) -> dict | None:
    if not isinstance(paquet, dict):
        return None
    data = paquet.get("data")
    if isinstance(data, dict) and isinstance(data.get("contact"), dict):
        return data["contact"]
    if isinstance(paquet.get("contact"), dict):
        return paquet["contact"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contact-id", action="append", required=True)
    args = ap.parse_args()
    ids = [str(x).strip() for x in args.contact_id]
    lus: dict[str, dict] = {}
    try:
        settings = Settings.from_env()
        client = HektorClient(settings)
    except Exception as exc:
        print(json.dumps({"lus": {}, "_error": str(exc)[:200]}, ensure_ascii=False))
        return 0
    for cid in ids:
        if not cid.isdigit():
            lus[cid] = {"trouve": False, "erreur": "numero non numerique"}
            continue
        try:
            paquet = client.get_json("/Api/Contact/ContactById", params={"id": cid, "version": settings.api_version})
        except Exception as exc:
            lus[cid] = {"trouve": False, "erreur": str(exc)[:200]}
            continue
        contact = extraire_contact(paquet)
        if contact is None:
            lus[cid] = {"trouve": False, "erreur": "reponse sans fiche"}
            continue
        lus[cid] = {"trouve": True, "refCouple": case_de_menage(contact)}
    print(json.dumps({"lus": lus}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
