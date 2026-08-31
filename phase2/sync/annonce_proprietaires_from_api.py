#!/usr/bin/env python3
"""Lit les PROPRIETAIRES (mandants) d'une annonce via l'API Hektor — porte 2.

POURQUOI CE SCRIPT, et c'est la leçon du 31/08.

Le worker vérifiait le lien mandant en scrapant la console (`div_display_prospects_liste`).
Cette page est **filtrée par l'agence du compte connecté** — et le worker agit sous
le négociateur du BIEN, pas du CONTACT. Un mandant appartenant à une autre agence
lui est donc invisible, et il conclut « pas lié ».

Mesuré le 31/08 sur les 22 755 liens vendeur des annonces actives :

    10 820  (47,6 %)  contact et bien ont un négociateur différent
     9 504  (41,8 %)  ils ont une agence différente

Ce n'est pas un cas de bord : c'est presque un mandant sur deux. Le défaut n'avait
mordu que trois fois parce qu'il n'y avait eu que trois gestes mandant en 90 jours.

Cas exact qui a déclenché ce script — annonce 62964, contact 603953 :

    console, en tant que GONZALEZ  ->  invisible   (le contact est d'une autre agence)
    API                            ->  visible     agence=1, id=603953

L'API s'authentifie par JETON, pas par session de négociateur : elle n'est pas
filtrée par agence. C'est donc la seule source qui répond juste quel que soit le
propriétaire du contact.

Même patron que `annonce_etat_from_api.py` (29/08), écrit pour la même raison :
une preuve doit venir d'une SOURCE EXACTE, pas d'un affichage.

Sort une ligne JSON :
    {"trouve": true, "ids": ["603953"], "proprietaires": [{...}]}
    {"trouve": false}                      annonce inconnue (404) ou sans détail
    {"_error": "..."}                      lecture impossible -- l'appelant DÉCIDE
                                           quoi en faire, ce script ne conclut pas
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--annonce-id", required=True)
    args = ap.parse_args()
    aid = str(args.annonce_id).strip()
    if not aid.isdigit():
        print(json.dumps({"_error": "annonce-id non numerique"}))
        return 0

    try:
        client = HektorClient(Settings.from_env())
        payload = client.get_json("/Api/Annonce/AnnonceById/", params={"id": aid})
    except Exception as exc:
        texte = str(exc)
        # Un 404 est une REPONSE, pas une panne : l'annonce n'existe plus.
        if "404" in texte:
            print(json.dumps({"trouve": False}))
            return 0
        print(json.dumps({"_error": texte[:200]}, ensure_ascii=False))
        return 0

    annonce = payload.get("annonce") if isinstance(payload, dict) else None
    if not isinstance(annonce, dict):
        print(json.dumps({"trouve": False}))
        return 0

    # `proprietaires` est la liste que le miroir range dans proprietaires_json
    # (voir refresh_single_annonce.py). Chaque entrée porte : id, nom, prenom,
    # civilite, agence, id_negociateur, archive...
    bruts = annonce.get("proprietaires")
    if bruts is None:
        # Distinguer « pas de propriétaire » de « la clé n'est pas là » : dans le
        # doute on ne prétend pas que l'annonce n'en a aucun.
        print(json.dumps({"_error": "cle proprietaires absente de la reponse"}))
        return 0
    if not isinstance(bruts, list):
        print(json.dumps({"_error": "proprietaires n'est pas une liste"}))
        return 0

    proprios = []
    ids = []
    for item in bruts:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id") or "").strip()
        if pid:
            ids.append(pid)
        proprios.append({
            "id": pid,
            "nom": str(item.get("nom") or ""),
            "prenom": str(item.get("prenom") or ""),
            "agence": str(item.get("agence") if item.get("agence") is not None else ""),
            "id_negociateur": str(item.get("id_negociateur") if item.get("id_negociateur") is not None else ""),
            "archive": str(item.get("archive") if item.get("archive") is not None else ""),
        })

    print(json.dumps({
        "trouve": True,
        "annonce_id": aid,
        "ids": ids,
        "proprietaires": proprios,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
