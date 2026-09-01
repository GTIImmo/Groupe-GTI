#!/usr/bin/env python3
"""Liste les offres, compromis ou ventes d'UNE annonce, par l'API Hektor — porte 2.

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

    /Api/Offre/ListOffres/      data[].id_annonce      (page 1, les 20 plus recentes)
    /Api/Vente/ListCompromis/   liste[].annonce.id     (page 0, tri dateStart desc)
    /Api/Vente/ListVentes/      sales[].annonce.id     (fenetre de dates)

L'OFFRE A ETE AJOUTEE LE 01/09/2026, et voici pourquoi.

Elle etait le SEUL des trois genres exclu de l'arbitre, sur la foi d'une phrase
du worker : « l'offre garde son propre chemin (sa reponse, elle, parle) ». Un
essai reel a montre qu'elle ne parle pas : l'offre 1 001 324, creee depuis l'app
sur l'annonce 24933, est restee sans numero Hektor -- donc invisible aux gestes
« refuser » et « accepter » -- en attendant le run de nuit.

Or la lecture etait a portee de main : la premiere page de ListOffres porte les
20 plus recentes, et une offre creee a l'instant y est forcement. Verifie en
direct le 01/09 : l'offre 33037 y figurait, avec son annonce et son acquereur.
Hektor n'accepte aucun filtre par annonce (idAnnonce et id_annonce sont ignores,
teste) -- c'est donc bien la page 1 qu'il faut lire, puis filtrer ici.

BORNES ASSUMEES, et il faut les dire :
  * offres — la PREMIERE page seulement, soit les 20 plus recentes de l'agence.
    Une offre qu'on vient de creer y est forcement. Ce n'est pas un inventaire :
    une offre ancienne n'y sera pas, et c'est voulu.
  * compromis — on ne lit que la PREMIERE page du tri par date decroissante,
    soit les 20 plus recents. Une transaction qu'on vient de creer y est
    forcement. Ce pont ne sert qu'a cela ; ce n'est pas un inventaire.
  * ventes — le listing exige une fenetre de dates. On la centre sur la date
    de la vente, +/- 3 jours, ce qui suffit pour la retrouver sans ramener
    les 7 500 autres.

Sort une ligne JSON :
    {"trouve": true, "ids": [...], "actifs": [...]}   ce que l'annonce porte
    "actifs" = ce qui EMPECHE d'en creer un autre : un compromis de status 1,
    ou n'importe quelle vente (elle n'a pas d'etat, elle se supprime).
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
    ap.add_argument("--kind", required=True, choices=("offre", "compromis", "vente"))
    ap.add_argument("--date", default=None,
                    help="date de la transaction (AAAA-MM-JJ), pour centrer la fenetre des ventes")
    args = ap.parse_args()

    annonce = str(args.annonce_id).strip()
    if not annonce.isdigit():
        print(json.dumps({"_error": "annonce non numerique"}))
        return 0

    try:
        reglages = Settings.from_env()
        client = HektorClient(reglages)
        if args.kind == "offre":
            # Page 1 : les 20 offres les plus recentes de l'agence. Hektor ignore
            # tout filtre par annonce -- on filtre donc nous-memes, plus bas.
            #
            # ⚠ `version` EST OBLIGATOIRE ICI, et son absence ne se voit pas :
            # sans lui la route repond 200 avec data = null, sans le moindre
            # message. Les deux autres listings s'en passent -- c'est une
            # particularite de ListOffres, trouvee en la branchant le 01/09.
            payload = client.get_json("/Api/Offre/ListOffres/",
                                      params={"page": "1", "version": reglages.api_version})
            lignes = payload.get("data") or []
        elif args.kind == "compromis":
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
    actifs = []
    for ligne in lignes:
        if not isinstance(ligne, dict):
            continue
        if _id_annonce(ligne) != annonce:
            continue
        identifiant = ligne.get("id")
        if identifiant is None:
            continue
        identifiant = str(identifiant).strip()
        ids.append(identifiant)
        # ⚠ « actifs » DECRIT UN ETAT, IL NE PREDIT PAS UN BLOCAGE.
        #
        # J'avais d'abord ecrit ici qu'un compromis actif empeche d'en creer un
        # autre. C'est FAUX, et la mesure du 31/08 le dit sans ambiguite :
        #
        #     statut de l'annonce   etat du compromis courant
        #     Vendu                 active      9 075   <- la majorite du parc
        #     Clos                  cancelled     704
        #     Sous compromis        active         90
        #
        # 9 075 annonces VENDUES portent un compromis toujours actif : une fois
        # la vente enregistree, personne ne revient le clore. Le miroir compte
        # 9 206 compromis actifs remontant a 2019. « Actif » veut donc dire
        # « jamais clos », pas « en cours ».
        #
        # Et mes propres essais l'ont montre sans que je le voie : les compromis
        # 50050 et 50051 ont ete crees ALORS QU'UN COMPROMIS ACTIF EXISTAIT.
        #
        # Ce champ sert donc a DECRIRE (un compromis de status 1, ou n'importe
        # quelle vente -- elle n'a aucune colonne d'etat et ne s'annule pas, elle
        # se supprime). Il ne doit PAS servir a refuser un envoi tant que la
        # vraie condition de blocage n'est pas etablie.
        if args.kind == "offre":
            # UNE OFFRE NE PORTE PAS D'ETAT : elle porte un HISTORIQUE.
            # Chaque refus, chaque acceptation AJOUTE un evenement -- l'ecran du
            # 01/09 en montrait six sur une seule offre. C'est donc le DERNIER
            # qui dit ou elle en est, regle deja etablie ailleurs dans le projet
            # (normalize_source : offre_last_proposition_type).
            props = ligne.get("propositions")
            dernier = ""
            if isinstance(props, list) and props:
                fin = props[-1]
                if isinstance(fin, dict):
                    dernier = str(fin.get("type", "")).strip().lower()
            if dernier != "refus":
                actifs.append(identifiant)
        elif args.kind == "vente" or str(ligne.get("status", "")).strip() == "1":
            actifs.append(identifiant)

    print(json.dumps({"trouve": True, "ids": ids, "actifs": actifs}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
