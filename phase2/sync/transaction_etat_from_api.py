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
    # 16/09 : l'offre y entre. Le balayage du miroir doit pouvoir verifier les
    # TROIS genres, sinon il continue de deviner sur l'un d'eux.
    "offre": ("/Api/Offre/OffreById/", "id"),
}


def etat_transaction(kind: str, ident: str,
                     client: HektorClient | None = None) -> dict:
    """L'etat d'une transaction chez Hektor, par son numero.

    ⚠ TROIS REPONSES, ET ELLES NE SE CONFONDENT PAS :
        {"trouve": True, ...}   elle existe
        {"trouve": False}       Hektor repond 404 : elle n'existe plus
        {"_error": "..."}       on n'a pas pu savoir -- L'APPELANT DECIDE, et la
                                seule decision sure est de NE RIEN SUPPRIMER.

    ⚠ ON N'IMPRIME JAMAIS L'EXCEPTION BRUTE ailleurs que dans `_error` tronque :
      `authenticate()` met le secret dans l'URL, et une trace le recopierait.

    ⚠ `client` SE PASSE QUAND ON APPELLE EN BOUCLE -- 17/09/2026.
      Sans lui, chaque appel fabrique un client neuf, donc un LOGIN OAuth complet.
      Dix-sept pieces a verifier le 17/09 = dix-sept logins en vingt-deux
      secondes : notre IP a ete bloquee au seizieme. Le parametre est OPTIONNEL,
      donc le chemin en ligne de commande (le worker lance ce script en
      sous-processus, UNE piece a la fois) ne change pas d'un iota.
    """
    ident = str(ident or "").strip()
    if kind not in CHEMINS or not ident.isdigit():
        return {"_error": "genre ou identifiant invalide"}
    chemin, param = CHEMINS[kind]
    try:
        client = client or HektorClient(Settings.from_env())
        payload = client.get_json(chemin, params={param: ident})
    except Exception as exc:                                        # noqa: BLE001
        texte = str(exc)
        if "404" in texte:
            return {"trouve": False}
        return {"_error": texte[:200]}

    # ⚠ L'OFFRE NE REPOND PAS SOUS `res`, MAIS SOUS `offre`. Mesure du 16/09 :
    #   OffreById rend {"offre": {...}, "refresh": ...}. Lire `res` rendait None,
    #   donc « trouve: False » sur une offre BIEN VIVANTE -- le pire des defauts
    #   pour un verificateur de suppression : il aurait confirme des effacements
    #   a tort. Teste sur trois offres : 9469 et 33050 vivantes, 32790 en 404.
    cle = "offre" if kind == "offre" else "res"
    res = payload.get(cle) if isinstance(payload, dict) else None
    if isinstance(res, list):
        res = res[0] if res else None
    if kind == "vente":
        vivante = bool(payload) and not (isinstance(res, (dict, list)) and not res)
        return {"trouve": bool(vivante)}
    if not isinstance(res, dict) or res.get("id") is None:
        return {"trouve": False}
    lu = {"trouve": True, "id": str(res.get("id")),
          "status": str(res.get("status")) if res.get("status") is not None else ""}
    if kind == "offre":
        lu["details"] = details_offre(res)
    elif kind == "compromis":
        # 18/09 : CompromisById rend EXACTEMENT les champs de la liste
        # (prixPublique, prixNetVendeur, honorairesEntree/Sortie, sequestre,
        # dateStart, dateSignatureActe, acquereurs, mandants) -- mesure sur le
        # compromis reel 50039. On les rend tels quels, comme la liste le fait
        # (« sans les interpreter ») : la preuve du worker les lit a l'identique.
        lu["details"] = res
    return lu


def details_offre(res: dict) -> dict:
    """Ce qu'une offre porte AUJOURD'HUI, lu dans son historique -- 18/09/2026.

    Une offre n'a pas de prix « a plat » : Hektor garde une ligne par
    proposition, puis une par acceptation ou refus. L'historique est TOUJOURS
    chronologique (0 exception sur 11 098 offres, mesure du 18/09), donc la
    valeur courante est celle de la DERNIERE ligne « proposition » -- la meme
    regle que le run (affaire_ledger.py).

    ⚠ LA DATE EST RENDUE SANS L'HEURE. Hektor date la proposition avec la date
      saisie PLUS une heure (« 2026-09-04 18:30:06 ») : la comparer telle quelle
      a la date envoyee fabriquerait un faux ecart. Et elle s'appelle
      `dateProposition`, pas `date`, pour que le report au registre ne
      l'ecrive pas a la place de la date de l'offre.
    """
    props = res.get("propositions")
    props = props if isinstance(props, list) else []
    lignes = [p for p in props if isinstance(p, dict)]
    faites = [p for p in lignes if str(p.get("type", "")).strip().lower() == "proposition"]
    derniere = faites[-1] if faites else {}
    def propre(v):
        t = str(v if v is not None else "").strip()
        return "" if t in ("", "0") else t
    return {
        "montant": propre(derniere.get("montant")),
        "validite": propre(derniere.get("validite")),
        "dateProposition": str(derniere.get("date") or "").strip()[:10],
        "etat": str((lignes[-1] if lignes else {}).get("type", "")).strip().lower(),
        "propositions": len(faites),
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

    # ─── 18/09/2026 : UNE SEULE LECTURE, CELLE DE etat_transaction() ───
    # Cette commande recopiait la logique au lieu de l'appeler. Le 16/09 on a
    # corrige la fonction (l'offre repond sous `offre`, pas sous `res`) -- et
    # la copie, ici, est restee fausse : pour une offre, elle rendait TOUJOURS
    # « trouve: False ». Latent (l'app ne supprime pas d'offre, le balayage
    # appelle la fonction), mais c'est cette commande que le worker lance.
    # Compromis et vente : memes reponses qu'avant, a la lettre.
    print(json.dumps(etat_transaction(args.kind, ident), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
