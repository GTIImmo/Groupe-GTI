#!/usr/bin/env python3
"""Lit l'état ABSOLU d'un compromis ou d'une vente via l'API Hektor — porte 2.

POURQUOI « ABSOLU », et c'est la condition du filet de rejeu.

La première version vérifiait l'annulation d'un compromis en comptant les mentions
« Compromis clôturé » sur la fiche AVANT et APRÈS. Ça marche une fois. Mais rejoué
sur un compromis déjà annulé, le compte ne bouge plus — et le geste réussi serait
déclaré en échec, indéfiniment. Un filet qui rejoue exige une vérification qui ne
dépend pas de l'ordre des choses.

L'API donne cet état, par identifiant :

    /Api/Vente/CompromisById/  ->  {"res": {"id": 50048, "status": 2}}
    /Api/Vente/VenteById/      ->  200 si elle existe, 404 sinon

Correspondance des états de compromis, mesurée sur le miroir le 29/08 :
    status 1 = actif      9 206 lignes
    status 2 = annulé     1 367 lignes
soit exactement la répartition `active` / `cancelled` du registre d'affaires.

Sort une ligne JSON :
    {"trouve": true, "status": "2"}     compromis lu
    {"trouve": true}                    vente lue (pas d'état : elle existe, c'est tout)
    {"trouve": false}                   n'existe plus
    {"_error": "..."}                   lecture impossible — l'appelant décide
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

CHEMINS = {
    "compromis": ("/Api/Vente/CompromisById/", "idCompromis"),
    "vente": ("/Api/Vente/VenteById/", "id"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=sorted(CHEMINS))
    ap.add_argument("--id", required=True)
    args = ap.parse_args()
    ident = str(args.id).strip()
    if not ident.isdigit():
        print(json.dumps({"_error": "id non numerique"}))
        return 0

    chemin, param = CHEMINS[args.kind]
    try:
        client = HektorClient(Settings.from_env())
        payload = client.get_json(chemin, params={param: ident})
    except Exception as exc:
        texte = str(exc)
        # Un 404 est une REPONSE, pas une panne : l'objet n'existe plus.
        if "404" in texte:
            print(json.dumps({"trouve": False}))
            return 0
        print(json.dumps({"_error": texte[:200]}, ensure_ascii=False))
        return 0

    res = payload.get("res") if isinstance(payload, dict) else None
    if isinstance(res, list):
        res = res[0] if res else None

    if args.kind == "vente":
        # La vente n'a pas d'etat chez Hektor : elle existe, ou elle a disparu.
        vivante = bool(payload) and not (isinstance(res, (dict, list)) and not res)
        print(json.dumps({"trouve": bool(vivante)}))
        return 0

    if not isinstance(res, dict) or res.get("id") is None:
        print(json.dumps({"trouve": False}))
        return 0

    print(json.dumps({
        "trouve": True,
        "id": str(res.get("id")),
        "status": str(res.get("status")) if res.get("status") is not None else "",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
