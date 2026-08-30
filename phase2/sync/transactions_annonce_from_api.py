#!/usr/bin/env python3
"""Liste les compromis ou les ventes d'UNE annonce, par l'API Hektor — porte 2.

POURQUOI CE PONT EXISTE, et c'est une nuit qui l'a impose.

L'arbitre de C.4 relisait la FICHE (`chargeannonce_Accueil`) pour savoir si une
transaction venait d'etre creee. Pour la vente cela marchait ; pour le compromis
c'est faux, et deux fois plutot qu'une :

    31/08  compromis 50050 cree -> la fiche rendait encore l'ancien identifiant
    31/08  compromis 50051 cree -> la fiche ne l'a JAMAIS montre (elle affichait
           50050, puis 50048 apres suppression)

La fiche ne montre **qu'un compromis a la fois**, et pas toujours le dernier.
Le piege etait deja au dossier le 29/08 — « elle n'affichait qu'un seul
compromis alors que 50044 et 50045 existaient tous deux » — et je m'y suis
laisse prendre quand meme. L'arbitre declarait donc « rien cree » sur des gestes
REUSSIS : exactement le faux echec qu'il est cense empecher.

L'API, elle, ne masque rien. Les deux listings portent le lien vers l'annonce :

    /Api/Vente/ListCompromis/   liste[].annonce.id     (page 0, tri dateStart desc)
    /Api/Vente/ListVentes/      sales[].annonce.id     (fenetre de dates)

BORNES ASSUMEES, et il faut les dire :
  * compromis — on ne lit que la PREMIERE page du tri par date decroissante,
    soit les 20 plus recents. Une transaction qu'on vient de creer y est
    forcement. Ce pont ne sert qu'a cela ; ce n'est pas un inventaire.
  * ventes — le listing exige une fenetre de dates. On la centre sur la date
    de la vente, +/- 3 jours, ce qui suffit pour la retrouver sans ramener
    les 7 500 autres.

Sort une ligne JSON :
    {"trouve": true, "ids": ["50051"]}     ce que l'annonce porte
    {"trouve": true, "ids": []}            elle n'en porte aucun
    {"_error": "..."}                      lecture impossible -- l'appelant decide
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import HektorClient, Settings  # noqa: E402


def _id_annonce(ligne: dict) -> str:
    annonce = ligne.get("annonce")
    if isinstance(annonce, dict) and annonce.get("id") is not None:
        return str(annonce["id"]).strip()
    for cle in ("idAnnonce", "id_annonce", "hektor_annonce_id"):
        if ligne.get(cle) is not None:
            return str(ligne[cle]).strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--annonce-id", required=True)
    ap.add_argument("--kind", required=True, choices=("compromis", "vente"))
    ap.add_argument("--date", default=None,
                    help="date de la transaction (AAAA-MM-JJ), pour centrer la fenetre des ventes")
    args = ap.parse_args()

    annonce = str(args.annonce_id).strip()
    if not annonce.isdigit():
        print(json.dumps({"_error": "annonce non numerique"}))
        return 0

    try:
        client = HektorClient(Settings.from_env())
        if args.kind == "compromis":
            payload = client.get_json("/Api/Vente/ListCompromis/",
                                      params={"page": 0, "sort": "dateStart", "way": "desc"})
            lignes = payload.get("liste") or []
        else:
            pivot = args.date or dt.date.today().isoformat()
            try:
                jour = dt.date.fromisoformat(pivot)
            except ValueError:
                jour = dt.date.today()
            payload = client.get_json("/Api/Vente/ListVentes/", params={
                "page": 0, "sort": "date", "order": "desc",
                "dateStart": (jour - dt.timedelta(days=3)).isoformat(),
                "dateEnd": (jour + dt.timedelta(days=3)).isoformat(),
            })
            lignes = payload.get("sales") or []
    except Exception as exc:  # noqa: BLE001 -- l'appelant decide quoi en faire
        print(json.dumps({"_error": str(exc)[:200]}, ensure_ascii=False))
        return 0

    if not isinstance(lignes, list):
        print(json.dumps({"_error": "reponse inattendue"}))
        return 0

    ids = []
    for ligne in lignes:
        if not isinstance(ligne, dict):
            continue
        if _id_annonce(ligne) != annonce:
            continue
        identifiant = ligne.get("id")
        if identifiant is not None:
            ids.append(str(identifiant).strip())

    print(json.dumps({"trouve": True, "ids": ids}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
