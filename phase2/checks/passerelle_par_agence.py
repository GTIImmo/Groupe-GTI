# -*- coding: utf-8 -*-
"""L'EPREUVE : le numero de passerelle de CHAQUE agence, verifie CHEZ HEKTOR.

POURQUOI
    Le 30/09/2026 on a decouvert que la passerelle leboncoinDirect n° 37 n'existe
    plus chez Hektor depuis le 03/04 : elle a ete renumerotee 44. Notre carte de
    routage (`app_diffusion_agency_target`) pointe toujours sur la 37, et 1 795
    annonces (Montbrison + Saint-Just-Saint-Rambert) partent donc sur une
    passerelle morte -- depuis SIX MOIS, sans que rien ne le dise.

    Hektor annonce une refonte LeBonCoin (fin du regroupement d'agences, une
    passerelle par agence). Elle va renumeroter HUIT passerelles d'un coup.
    Ce controle est ce qui fera la difference entre le voir le jour meme et le
    decouvrir dans six mois.

COMMENT ON RATTACHE UNE PASSERELLE A UNE AGENCE
    Hektor ne le dit PAS directement. Il donne, pour chaque passerelle, la liste
    des annonces diffusees AVEC LEUR NEGOCIATEUR. On remonte donc :
        passerelle -> ses negociateurs -> leur agence
    ⚠ C'est une DEDUCTION, et elle a une limite qu'il faut dire : une passerelle
      SANS AUCUNE ANNONCE ne rattache personne. Elle est alors rendue « muette »,
      jamais « fausse » -- on ne condamne pas sur une absence de preuve.

CE QU'IL LIT
    Hektor, EN DIRECT   /Api/Passerelle/DetailedBroadcastList/   (une requete)
    le miroir           hektor_negociateur + hektor_agence (le rattachement)
    notre carte         app_diffusion_agency_target (phase2/phase2.sqlite)

USAGE
    python phase2/checks/passerelle_par_agence.py            # Hektor en direct
    python phase2/checks/passerelle_par_agence.py --hors-ligne  # le brut deja descendu
    python phase2/checks/passerelle_par_agence.py --json     # pour la sonde

SORTIE
    code 0 = tout concorde ; code 1 = au moins un numero faux ou absent.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import unicodedata
from typing import Any, Dict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from hektor_pipeline.common import HektorClient, Settings  # noqa: E402

CHEMIN_MIROIR = os.path.join("data", "hektor.sqlite")
CHEMIN_CARTE = os.path.join("phase2", "phase2.sqlite")
ROUTE = "/Api/Passerelle/DetailedBroadcastList/"


def sans_accent(valeur: str) -> str:
    texte = unicodedata.normalize("NFD", str(valeur or ""))
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return " ".join(texte.split()).strip().lower()


# ----------------------------------------------------------------- la matiere


def passerelles_en_direct(settings: Settings) -> list[dict]:
    """UNE requete a Hektor. Le client porte deja le plancher de debit."""
    client = HektorClient(settings)
    payload = client.get_json(ROUTE, params={"version": settings.api_version, "page": 0})
    return deballer(payload)


def passerelles_hors_ligne() -> list[dict]:
    conn = sqlite3.connect("file:%s?mode=ro" % CHEMIN_MIROIR, uri=True)
    ligne = conn.execute(
        "SELECT payload_json FROM raw_api_response WHERE endpoint_name = 'list_broadcasts'"
        " ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not ligne:
        raise SystemExit("Aucun brut list_broadcasts en base -- lancer avec Hektor en direct.")
    return deballer(json.loads(ligne[0]))


def deballer(payload: Any) -> list[dict]:
    """La meme regle que normalize_source : le carton, et rien d'implicite.

    ⚠ On n'ecrit PAS `data.get('platforms') or []` : un carton d'une autre forme
      deviendrait indiscernable d'une reponse vide, et ce controle se tairait
      exactement comme le deballeur s'est tu pendant trois mois.
    """
    data = payload.get("data") if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        contenu = data.get("platforms")
        if not isinstance(contenu, list):
            raise SystemExit(
                "Forme de reponse INCONNUE : data = dict(%s). Le controle s'arrete "
                "au lieu de conclure sur du vide." % ",".join(sorted(data)[:5])
            )
        data = contenu
    if not isinstance(data, list):
        raise SystemExit("Forme de reponse INCONNUE : data = %s" % type(data).__name__)
    return [x for x in data if isinstance(x, dict)]


def annuaire() -> tuple[dict, dict]:
    """negociateur -> agence, et agence -> nom."""
    conn = sqlite3.connect("file:%s?mode=ro" % CHEMIN_MIROIR, uri=True)
    nego_vers_agence = {
        str(r[0]): str(r[1])
        for r in conn.execute(
            "SELECT hektor_negociateur_id, hektor_agence_id FROM hektor_negociateur"
        )
        if r[1] is not None
    }
    agences = {str(r[0]): r[1] for r in conn.execute("SELECT hektor_agence_id, nom FROM hektor_agence")}
    conn.close()
    return nego_vers_agence, agences


def notre_carte() -> list[dict]:
    conn = sqlite3.connect("file:%s?mode=ro" % CHEMIN_CARTE, uri=True)
    conn.row_factory = sqlite3.Row
    lignes = [
        dict(r)
        for r in conn.execute(
            "SELECT agence_nom, portal_key, hektor_broadcast_id FROM app_diffusion_agency_target"
            " WHERE COALESCE(is_active, 1) = 1"
        )
    ]
    conn.close()
    return lignes


# ------------------------------------------------------------------ l'epreuve


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hors-ligne", action="store_true",
                        help="Lire le brut deja descendu au lieu d'appeler Hektor.")
    parser.add_argument("--json", action="store_true", help="Sortie machine.")
    args = parser.parse_args()

    settings = Settings.from_env()
    items = passerelles_hors_ligne() if args.hors_ligne else passerelles_en_direct(settings)
    nego_vers_agence, agences = annuaire()

    # passerelle -> {portail, agences deduites, nb annonces}
    vivantes: Dict[str, dict] = {}
    for item in items:
        pid = str(item.get("id") or "").strip()
        if not pid:
            continue
        trouvees = set()
        listings = item.get("listings") or []
        for listing in listings if isinstance(listings, list) else []:
            commercial = listing.get("commercial") if isinstance(listing, dict) else None
            if not isinstance(commercial, dict):
                continue
            agence_id = nego_vers_agence.get(str(commercial.get("id")))
            if agence_id:
                trouvees.add(agence_id)
        vivantes[pid] = {
            "portail": str(item.get("nom") or ""),
            "agences": {sans_accent(agences.get(a, "")) for a in trouvees if agences.get(a)},
            "noms": sorted(agences.get(a, "") for a in trouvees if agences.get(a)),
            "annonces": len(listings) if isinstance(listings, list) else 0,
        }

    verdicts = []
    for ligne in notre_carte():
        agence = str(ligne["agence_nom"] or "")
        portail = str(ligne["portal_key"] or "")
        numero = str(ligne["hektor_broadcast_id"] or "").strip()
        vivante = vivantes.get(numero)

        if vivante is None:
            # Le numero n'est plus rendu par Hektor. On cherche qui a pris sa place.
            remplacante = next(
                (p for p, v in vivantes.items()
                 if v["portail"] == portail and sans_accent(agence) in v["agences"]),
                None,
            )
            verdicts.append({
                "agence": agence, "portail": portail, "numero": numero,
                "etat": "MORTE", "remplacante": remplacante,
                "detail": "la passerelle n'existe plus chez Hektor"
                          + (" -- remplacee par la n° %s" % remplacante if remplacante else ""),
            })
        elif vivante["portail"] != portail:
            verdicts.append({
                "agence": agence, "portail": portail, "numero": numero,
                "etat": "MAUVAIS PORTAIL", "remplacante": None,
                "detail": "la n° %s est un flux %s" % (numero, vivante["portail"]),
            })
        elif not vivante["agences"]:
            verdicts.append({
                "agence": agence, "portail": portail, "numero": numero,
                "etat": "MUETTE", "remplacante": None,
                "detail": "passerelle vivante mais AUCUNE annonce : on ne peut ni "
                          "confirmer ni infirmer le rattachement",
            })
        elif sans_accent(agence) in vivante["agences"]:
            verdicts.append({
                "agence": agence, "portail": portail, "numero": numero,
                "etat": "OK", "remplacante": None,
                "detail": "confirmee par %s annonce(s)" % vivante["annonces"],
            })
        else:
            remplacante = next(
                (p for p, v in vivantes.items()
                 if v["portail"] == portail and sans_accent(agence) in v["agences"]),
                None,
            )
            verdicts.append({
                "agence": agence, "portail": portail, "numero": numero,
                "etat": "MAUVAISE AGENCE", "remplacante": remplacante,
                "detail": "la n° %s sert : %s" % (numero, ", ".join(vivante["noms"]) or "personne"),
            })

    # les passerelles vivantes que notre carte ignore
    connus = {str(l["hektor_broadcast_id"] or "").strip() for l in notre_carte()}
    orphelines = [
        {"numero": p, "portail": v["portail"], "annonces": v["annonces"], "agences": v["noms"]}
        for p, v in vivantes.items() if p not in connus
    ]

    faux = [v for v in verdicts if v["etat"] in ("MORTE", "MAUVAISE AGENCE", "MAUVAIS PORTAIL")]
    muets = [v for v in verdicts if v["etat"] == "MUETTE"]

    if args.json:
        print(json.dumps({
            "source": "hors-ligne" if args.hors_ligne else "hektor-direct",
            "passerelles_vivantes": len(vivantes),
            "lignes_carte": len(verdicts),
            "faux": len(faux), "muets": len(muets),
            "verdicts": verdicts, "orphelines": orphelines,
        }, ensure_ascii=False, indent=2))
        return 1 if faux else 0

    print("=" * 84)
    print("LE NUMERO DE PASSERELLE DE CHAQUE AGENCE  --  source : %s"
          % ("le brut deja descendu" if args.hors_ligne else "HEKTOR EN DIRECT"))
    print("=" * 84)
    print("  %s passerelles vivantes chez Hektor  |  %s lignes dans notre carte"
          % (len(vivantes), len(verdicts)))
    print()

    for portail in sorted({v["portail"] for v in verdicts}):
        print("  -- %s " % portail + "-" * (78 - len(portail)))
        for v in sorted((x for x in verdicts if x["portail"] == portail),
                        key=lambda x: sans_accent(x["agence"])):
            marque = {"OK": "  ", "MUETTE": " ?", "MORTE": " X",
                      "MAUVAISE AGENCE": " X", "MAUVAIS PORTAIL": " X"}[v["etat"]]
            print("   %s %-38s n° %-4s %-16s %s"
                  % (marque, v["agence"][:38], v["numero"], v["etat"], v["detail"]))
        print()

    if orphelines:
        print("  -- passerelles VIVANTES absentes de notre carte " + "-" * 33)
        for o in sorted(orphelines, key=lambda x: int(x["numero"])):
            print("   ? n° %-4s %-18s %4s annonces  %s"
                  % (o["numero"], o["portail"], o["annonces"], ", ".join(o["agences"])[:46]))
        print()

    print("=" * 84)
    print("  numeros FAUX   : %s" % len(faux))
    print("  non prouvables : %s (passerelle sans annonce -- ni confirmee ni infirmee)" % len(muets))
    print("  orphelines     : %s" % len(orphelines))
    print("=" * 84)
    return 1 if faux else 0


if __name__ == "__main__":
    raise SystemExit(main())
