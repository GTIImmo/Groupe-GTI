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


def par_agence(settings: Settings, portail: str = "leboncoinDirect", essais: int = 6) -> dict:
    """LA PREUVE DIRECTE : on DEMANDE a Hektor, agence par agence.

    ⚠ POURQUOI CE MODE EXISTE, ALORS QUE LE MODE PAR DEFAUT REPOND DEJA
        Le mode par defaut DEDUIT (passerelle -> negociateurs -> agence). Il a
        suffi a trouver la panne, mais il ne peut pas prouver « un numero par
        agence » : deux agences peuvent partager une passerelle sans qu'on le
        voie, et un negociateur pose une annonce hors de son agence (c'est ce qui
        m'a fait douter de la n° 54). Ici, Hektor REPOND.

    ⚠ DEUX PIEGES, ET ILS ONT FAIT RATER LES DEUX PREMIERS ESSAIS
        ① `ListPasserelles` ne rend la configuration que pour un bien DIFFUSABLE.
           Une annonce prise au hasard rend `data: []` -- 18 agences sur 19 ont
           repondu vide au premier essai, ce qui ressemblait a une absence de
           passerelle alors que c'etait un mauvais temoin.
        ② LE TEMOIN NE DOIT PAS ETRE CHOISI SUR LE PORTAIL QU'ON MESURE, sinon la
           reponse est fabriquee par la question. On prend donc un bien diffuse
           sur un AUTRE portail (bienici, etreproprio, paper, superimmo).
    """
    client = HektorClient(settings)
    payload = client.get_json(ROUTE, params={"version": settings.api_version, "page": 0})
    plateformes = deballer(payload)

    conn = sqlite3.connect("file:%s?mode=ro" % CHEMIN_MIROIR, uri=True)
    annonce_vers_agence = {
        str(r[0]): r[1]
        for r in conn.execute(
            "SELECT a.hektor_annonce_id, ag.nom FROM hektor_annonce a "
            "JOIN hektor_agence ag ON ag.hektor_agence_id = a.hektor_agence_id"
        )
    }
    conn.close()

    temoins: Dict[str, list] = {}
    for plateforme in plateformes:
        if plateforme.get("nom") == portail:
            continue  # ② jamais un temoin pris sur le portail mesure
        for listing in plateforme.get("listings") or []:
            identifiant = str(listing.get("annonce_id") or "") if isinstance(listing, dict) else ""
            agence = annonce_vers_agence.get(identifiant)
            if agence and identifiant not in temoins.setdefault(agence, []):
                temoins[agence].append(identifiant)

    resultat, muettes = {}, []
    for agence in sorted(temoins):
        for annonce in temoins[agence][:essais]:
            reponse = client.get_json(
                "/Api/Annonce/ListPasserelles/",
                params={"idAnnonce": annonce, "version": settings.api_version},
            )
            trouvees = [
                x for x in (reponse.get("data") or [])
                if isinstance(x, dict) and x.get("passerelle") == portail
            ]
            if trouvees:
                resultat[agence] = {
                    "numero": str(trouvees[0].get("id")),
                    "identifiant": str(trouvees[0].get("identifiant") or ""),
                    "actif": str(trouvees[0].get("actif") or ""),
                    "nb_annonces": str(trouvees[0].get("nbAnnonces") or ""),
                    "temoin": annonce,
                }
                break
        else:
            muettes.append(agence)
    return {"portail": portail, "agences": resultat, "muettes": muettes,
            "attendues": len(temoins)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hors-ligne", action="store_true",
                        help="Lire le brut deja descendu au lieu d'appeler Hektor.")
    parser.add_argument("--json", action="store_true", help="Sortie machine.")
    parser.add_argument("--par-agence", metavar="PORTAIL", nargs="?", const="leboncoinDirect",
                        help="LA PREUVE DIRECTE : Hektor repond agence par agence "
                             "(defaut leboncoinDirect). Un appel par agence.")
    args = parser.parse_args()

    settings = Settings.from_env()

    if args.par_agence:
        bilan = par_agence(settings, portail=args.par_agence)
        carte = {sans_accent(l["agence_nom"]): str(l["hektor_broadcast_id"] or "").strip()
                 for l in notre_carte() if l["portal_key"] == args.par_agence}
        if args.json:
            print(json.dumps(bilan, ensure_ascii=False, indent=2))
        else:
            print("=" * 84)
            print("HEKTOR REPOND, AGENCE PAR AGENCE  --  portail %s" % args.par_agence)
            print("=" * 84)
            print("   %-36s %-7s %-12s %-9s %s"
                  % ("agence", "numero", "identifiant", "notre carte", "verdict"))
            for agence in sorted(bilan["agences"]):
                v = bilan["agences"][agence]
                notre = carte.get(sans_accent(agence), "-")
                verdict = "OK" if notre == v["numero"] else "A CORRIGER (%s -> %s)" % (notre, v["numero"])
                print("   %-36s %-7s %-12s %-9s %s"
                      % (agence[:36], v["numero"], v["identifiant"], notre, verdict))
            for agence in bilan["muettes"]:
                print("   %-36s %-7s %s" % (agence[:36], "?", "AUCUN temoin n'ouvre ce portail -- non mesure"))
            numeros = [v["numero"] for v in bilan["agences"].values()]
            ident = [v["identifiant"] for v in bilan["agences"].values()]
            print()
            print("   agences attendues %s | repondues %s | muettes %s"
                  % (bilan["attendues"], len(bilan["agences"]), len(bilan["muettes"])))
            print("   numeros distincts %s | identifiants distincts %s"
                  % (len(set(numeros)), len(set(ident))))
            if bilan["muettes"]:
                print("   -> COUVERTURE INCOMPLETE : on ne conclut pas sur les agences muettes.")
            elif len(numeros) == len(set(numeros)):
                print("   -> UN NUMERO PAR AGENCE : CONFIRME sur les %s agences." % len(numeros))
            else:
                from collections import Counter
                partages = {k: v for k, v in Counter(numeros).items() if v > 1}
                print("   -> NUMEROS ENCORE PARTAGES : %s" % partages)
            a_corriger = sum(1 for a, v in bilan["agences"].items()
                             if carte.get(sans_accent(a), "-") != v["numero"])
            print("   lignes de carte a corriger : %s" % a_corriger)
        return 1 if any(carte.get(sans_accent(a), "-") != v["numero"]
                        for a, v in bilan["agences"].items()) else 0

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
