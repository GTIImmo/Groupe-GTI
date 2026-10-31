#!/usr/bin/env python3
"""Trouve la SECONDE fiche d'un couple que l'app vient de creer chez Hektor.

Couples · piece B (31/10/2026) -- notice/COUPLES_ERGONOMIE_ET_ECRITURE_PROPOSITION_2026-10-30.md §15-§16.

POURQUOI. Creer un couple fabrique DEUX fiches chez Hektor (essai E1 du 30/10).
La reponse de creation ne donne que la premiere, et la premiere ne nomme pas la
seconde : son `refCouple` vaut elle-meme. C'est la SECONDE qui designe la
premiere (`refCouple` = la premiere). On lit donc les fiches qui suivent, et on
n'en accepte une QUE si elle designe la premiere -- jamais « +1 » suppose.

LA MESURE (miroir, couples crees depuis 02/2026) : 379 secondes fiches sur 393
sont la suivante, 1 est deux plus loin ; les 13 autres sont tres loin (fiches
rattachees apres coup), aucune lecture raisonnable ne les trouverait. D'ou au
plus --essais lectures (3 par defaut).

PRUDENCE (le mur Hektor) : une lecture a la fois, au rythme plancher du client ;
ARRET NET au premier refus (403 / 429) ou si Hektor ne repond pas (5xx) -- on ne
force jamais. Une fiche introuvable (404) n'est pas un refus : on passe a la
suivante.

LECTURE SEULE : aucune ecriture, ni locale ni Supabase. Le worker range le
resultat lui-meme.

Sortie : UNE ligne JSON
    {"seconde": "606072", "lus": [{"id": "606072", "issue": "seconde"}]}
    {"seconde": null, "lus": [...], "arret": "refus 429 ..."}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import HektorClient, HektorNonRetryableError, Settings  # noqa: E402


def issue_de_la_lecture(payload: object, premiere: str, candidat: str) -> str:
    """« seconde », « autre » ou « absente », d'apres la reponse de ContactById."""
    data = payload.get("data") if isinstance(payload, dict) else None
    # meme deballage que la nuit (normalize_source.get_detail_payload)
    contact = data.get("contact") if isinstance(data, dict) and isinstance(data.get("contact"), dict) else data
    if not isinstance(contact, dict) or not str(contact.get("id") or "").strip():
        return "absente"
    if str(contact.get("id")).strip() != candidat:
        return "autre"
    ref = str(contact.get("refCouple") or "").strip()
    return "seconde" if ref == premiere and candidat != premiere else "autre"


def chercher(client: HektorClient, premiere: str, essais: int, version: str) -> dict:
    lus: list[dict] = []
    for decalage in range(1, essais + 1):
        candidat = str(int(premiere) + decalage)
        try:
            payload = client.get_json("/Api/Contact/ContactById", params={"id": candidat, "version": version})
        except HektorNonRetryableError as exc:
            texte = str(exc)
            if "404" in texte:
                lus.append({"id": candidat, "issue": "absente"})
                continue
            lus.append({"id": candidat, "issue": "refus"})
            return {"seconde": None, "lus": lus, "arret": f"refus de Hektor : {texte[:160]}"}
        except Exception as exc:  # 5xx apres les essais du client, reseau : on s'arrete
            lus.append({"id": candidat, "issue": "erreur"})
            return {"seconde": None, "lus": lus, "arret": f"Hektor ne repond pas : {str(exc)[:160]}"}
        issue = issue_de_la_lecture(payload, premiere, candidat)
        lus.append({"id": candidat, "issue": issue})
        if issue == "seconde":
            return {"seconde": candidat, "lus": lus}
    return {"seconde": None, "lus": lus}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--premiere", required=True, help="numero Hektor de la premiere fiche du couple")
    ap.add_argument("--essais", type=int, default=3, help="fiches suivantes a lire, au plus (1 a 5)")
    args = ap.parse_args()
    premiere = str(args.premiere).strip()
    essais = max(1, min(int(args.essais), 5))
    if not premiere.isdigit() or int(premiere) >= 10_000_000:
        # un numero de NOTRE plage n'est jamais un numero de Hektor
        print(json.dumps({"seconde": None, "lus": [], "arret": f"premiere invalide : {premiere!r}"}, ensure_ascii=False))
        return 0
    try:
        settings = Settings.from_env()
        client = HektorClient(settings)
        resultat = chercher(client, premiere, essais, settings.api_version)
    except Exception as exc:  # authentification, configuration : on ne sait pas
        resultat = {"seconde": None, "lus": [], "arret": f"lecture impossible : {str(exc)[:160]}"}
    print(json.dumps(resultat, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
