#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE STATUT D'AUJOURD'HUI DES 15 BIENS REMIS « SOUS OFFRE » LE 12/11 -- LECTURE SEULE CHEZ HEKTOR.   23/11/2026

    .venv\\Scripts\\python.exe -u -X utf8 phase2/checks/lire_statut_des_15_biens_2026-11-23.py

SON MOT DU 23/11 (2), § 1.3 : « LES 15 LECTURES CHEZ HEKTOR -> OUI, FAIS-LES [...] je veux savoir qu'ils sont « Vendu »
AUJOURD'HUI, pas le supposer depuis une lecture du 14/11. ⛔ LECTURE SEULE. Aucun upval, aucune ecriture. »

⛔ CE SCRIPT N'ECRIT RIEN, NULLE PART. Une seule requete GET par bien (/Api/Annonce/AnnonceById/, la lecture de
   phase2/sync/annonce_etat_from_api.py, meme client), UN SEUL client pour les 16, une lecture toutes les 1,2 s
   (le mur de Hektor : 1 req/s par processus).
⭐ LE TEMOIN POSITIF, lu en dernier : le bien 55086, que notre sentinelle des ecarts dit « Sous offre » chez Hektor. Le
   lecteur doit le rendre DIFFERENT de « Vendu » -- sinon un « 15/15 Vendu » ne prouverait rien.
Liste : notice/A_CORRIGER_STATUT_VENDU_2026-11-13.csv (les 15 du 12/11).
ECRIT : C:\\Hektor\\chantier_classeur_q6_cache\\garde_du_bien\\statut_des_15_<horodatage>.json (hors du depot).
CODES : 0 les 15 « Vendu » et le temoin lu autrement . 1 un bien n'est pas « Vendu » . 2 une lecture ratee / temoin faux
"""
from __future__ import annotations

import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from hektor_pipeline.common import HektorClient, Settings  # noqa: E402

LISTE = RACINE / "notice" / "A_CORRIGER_STATUT_VENDU_2026-11-13.csv"
TEMOIN = "55086"
SORTIE = Path(r"C:\Hektor\chantier_classeur_q6_cache\garde_du_bien")


def lire(client, aid: str) -> dict:
    try:
        payload = client.get_json("/Api/Annonce/AnnonceById/", params={"id": aid})
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc)[:200]}
    annonce = payload.get("annonce") if isinstance(payload, dict) else None
    kd = annonce.get("keyData") if isinstance(annonce, dict) else None
    if not isinstance(kd, dict) or not kd.get("id"):
        return {"trouve": False}
    st = annonce.get("statut") if isinstance(annonce.get("statut"), dict) else {}
    return {"trouve": True, "statut": str(st.get("id") or ""), "statut_nom": str(st.get("name") or ""),
            "archive": str(kd.get("archive") if kd.get("archive") is not None else ""),
            "datemaj": str(kd.get("datemaj") or "")}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    biens = [r["n° annonce Hektor"].strip() for r in csv.DictReader(LISTE.open(encoding="utf-8-sig"), delimiter=";")]
    if len(biens) != 15:
        print("⛔ la liste porte %d biens, pas 15 -- code 2" % len(biens))
        return 2
    client = HektorClient(Settings.from_env())
    res = {}
    for i, aid in enumerate(biens + [TEMOIN]):
        if i:
            time.sleep(1.2)
        r = lire(client, aid)
        res[aid] = r
        print("%-6s %s%s" % (aid, json.dumps(r, ensure_ascii=False), "   <- LE TEMOIN" if aid == TEMOIN else ""),
              flush=True)
    SORTIE.mkdir(parents=True, exist_ok=True)
    f = SORTIE / ("statut_des_15_%s.json" % datetime.now().strftime("%Y-%m-%d_%H%M%S"))
    f.write_text(json.dumps({"lu_le": datetime.now().isoformat(), "resultats": res}, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    rates = [a for a, r in res.items() if not r.get("trouve")]
    t = res[TEMOIN]
    vendus = [a for a in biens if res[a].get("statut") == "5"]
    autres = [a for a in biens if res[a].get("trouve") and res[a].get("statut") != "5"]
    print("-> %s" % f)
    print("les 15 : %d « Vendu » (statut 5), %d autre(s) %s, %d lecture(s) ratee(s) %s ; temoin %s : statut %s « %s »"
          % (len(vendus), len(autres), autres, len(rates), rates, TEMOIN, t.get("statut"), t.get("statut_nom")))
    if rates or not t.get("trouve") or t.get("statut") == "5":
        print("⛔ une lecture ratee, ou le temoin rendu « Vendu » : on ne conclut rien (code 2)")
        return 2
    return 0 if len(vendus) == 15 else 1


if __name__ == "__main__":
    raise SystemExit(main())
