#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES 5 BIENS « VIVANTS OU REGLES SANS PIECE » -- CINQ LECTURES CHEZ HEKTOR, LECTURE SEULE.     23/11/2026

    .venv\\Scripts\\python.exe -u -X utf8 phase2/checks/lire_les_5_biens_sans_piece_2026-11-23.py

SON MOT (dans la conversation, 23/11) : « FEU VERT pour les 5 lectures chez Hektor (lecture seule). C'est la priorite :
si des ventes reglees manquent a notre registre, tout le reste passe apres -- tu t'arretes et tu me le dis. »

⛔ CE SCRIPT N'ECRIT RIEN, NULLE PART, SAUF SON COMPTE RENDU HORS DU DEPOT. CINQ requetes GET, UN SEUL client, une toutes
   les 1,2 s (le mur de Hektor : 1 req/s par processus). Aucun upval, aucune ecriture.
LES CINQ LECTURES -- une par bien, la plus decisive pour LUI :
  . les trois « Vente reglee » (24464, 51585, 45938) : /Api/Vente/ListVentes/ sur une FENETRE de 7 jours centree entre
    la « Vente Fixee » et la « Vente Reglee » du Sheet (la forme du pont transactions_annonce_from_api.py, avec
    `version`) -- la vente du bien est-elle chez Hektor ?
    ⭐ TEMOIN POSITIF, dans la meme lecture : les AUTRES ventes de la fenetre doivent etre dans notre miroir local
      (data/hektor.sqlite, hektor_vente) -- sinon un « absente » ne prouverait rien ;
  . les deux affaires vivantes (61592 « Vente fixee » au 10/12/2026, 62503 « Compromis en attente ») : leur vente n'est pas
    passee -- /Api/Annonce/AnnonceById/ dit le statut que Hektor leur donne (et l'archive).
ECRIT : C:\\Hektor\\chantier_classeur_q6_cache\\les_5_biens\\lecture_<horodatage>.json (hors du depot).
CODES : 0 aucune vente reglee ne manque . 1 UNE VENTE REGLEE MANQUE A NOTRE REGISTRE (on s'arrete) . 2 lecture ratee
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from hektor_pipeline.common import HektorClient, Settings  # noqa: E402

SORTIE = Path(r"C:\Hektor\chantier_classeur_q6_cache\les_5_biens")
HEKTOR_DB = RACINE / "data" / "hektor.sqlite"
# bien -> (ligne du Sheet, ce que dit la ligne, le pivot de la fenetre)
VENTES = {"24464": ("QXDW8EQA", "Vente reglee 06/11/2020 (fixee 04/11/2020)", "2020-11-05"),
          "51585": ("2U5QPKRC", "Vente reglee 19/12/2018 (fixee 14/12/2018)", "2018-12-16"),
          "45938": ("MQ6H8TVQ", "Vente reglee 09/07/2018 (fixee 06/07/2018)", "2018-07-07")}
VIVANTES = {"61592": ("a8aaeb2b", "Vente fixee 10/12/2026, offre 31/08/2026, vente directe"),
            "62503": ("130d81ac", "Compromis en attente, compromis 05/11/2026, offre 01/10/2026")}


def dire(s: str = "") -> None:
    print(s, flush=True)


def annonce_de(v: dict) -> str:
    a = v.get("annonce")
    if isinstance(a, dict):
        return str(a.get("id") or "")
    return str(v.get("id_annonce") or v.get("idAnnonce") or "")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect("file:%s?mode=ro" % HEKTOR_DB.as_posix(), uri=True)
    cols = [r[1] for r in con.execute("pragma table_info(hektor_vente)")]
    cle = "hektor_vente_id" if "hektor_vente_id" in cols else cols[0]
    ventes_locales = {str(r[0]) for r in con.execute("select %s from hektor_vente" % cle)}
    con.close()
    dire("miroir local : %d ventes (hektor_vente.%s)" % (len(ventes_locales), cle))
    reglages = Settings.from_env()
    client = HektorClient(reglages)
    res, manque, ratee = {}, [], False
    premiere = True
    for bien, (ligne, dit, pivot) in VENTES.items():
        if not premiere:
            time.sleep(1.2)
        premiere = False
        jour = dt.date.fromisoformat(pivot)
        d1, d2 = (jour - dt.timedelta(days=3)).isoformat(), (jour + dt.timedelta(days=3)).isoformat()
        try:
            payload = client.get_json("/Api/Vente/ListVentes/", params={
                "page": 0, "sort": "date", "order": "desc", "dateStart": d1, "dateEnd": d2,
                "version": reglages.api_version})
            lignes = payload.get("data") if "data" in payload else payload.get("sales")
        except Exception as exc:  # noqa: BLE001
            lignes, payload = None, {"_error": str(exc)[:200]}
        if not isinstance(lignes, list):
            dire("⛔ %s (%s) : la route n'a pas rendu de liste (%s) -- on ne conclut pas" % (bien, ligne,
                                                                                         str(payload)[:160]))
            res[bien] = {"_error": str(payload)[:300]}
            ratee = True
            continue
        du_bien = [v for v in lignes if annonce_de(v) == bien]
        autres = [v for v in lignes if annonce_de(v) != bien]
        autres_chez_nous = [v for v in autres if str(v.get("id")) in ventes_locales]
        dire("%s (%s, %s) : fenetre %s -> %s : %d vente(s) lue(s) ; DU BIEN %d %s ; temoin : %d autre(s), dont %d dans "
             "notre miroir%s" % (bien, ligne, dit, d1, d2, len(lignes), len(du_bien),
                                 [(v.get("id"), v.get("date"), v.get("prix")) for v in du_bien], len(autres),
                                 len(autres_chez_nous), " ⚠ page pleine (20) : il peut y en avoir d'autres"
                                 if len(lignes) >= 20 else ""))
        for v in du_bien:
            if str(v.get("id")) not in ventes_locales:
                manque.append((bien, ligne, v.get("id"), v.get("date")))
        res[bien] = {"ligne": ligne, "dit": dit, "fenetre": [d1, d2], "lues": len(lignes),
                     "du_bien": [{"id": v.get("id"), "date": v.get("date"), "prix": v.get("prix")} for v in du_bien],
                     "autres": [str(v.get("id")) for v in autres], "autres_chez_nous": len(autres_chez_nous)}
    for bien, (ligne, dit) in VIVANTES.items():
        time.sleep(1.2)
        try:
            payload = client.get_json("/Api/Annonce/AnnonceById/", params={"id": bien})
            a = payload.get("annonce") if isinstance(payload, dict) else None
            kd = a.get("keyData") if isinstance(a, dict) else None
            st = a.get("statut") if isinstance(a, dict) and isinstance(a.get("statut"), dict) else {}
            if not isinstance(kd, dict) or not kd.get("id"):
                r = {"trouve": False}
            else:
                r = {"trouve": True, "statut": str(st.get("id") or ""), "statut_nom": str(st.get("name") or ""),
                     "archive": str(kd.get("archive") if kd.get("archive") is not None else ""),
                     "datemaj": str(kd.get("datemaj") or "")}
        except Exception as exc:  # noqa: BLE001
            r = {"_error": str(exc)[:200]}
            ratee = True
        dire("%s (%s, %s) : AnnonceById -> %s" % (bien, ligne, dit, r))
        res[bien] = dict(r, ligne=ligne, dit=dit)
    SORTIE.mkdir(parents=True, exist_ok=True)
    f = SORTIE / ("lecture_%s.json" % datetime.now().strftime("%Y-%m-%d_%H%M%S"))
    f.write_text(json.dumps({"res": res, "manque": manque}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    dire("-> %s" % f)
    if manque:
        dire("⛔⛔ UNE VENTE REGLEE MANQUE A NOTRE REGISTRE : %s -- ON S'ARRETE" % manque)
        return 1
    return 2 if ratee else 0


if __name__ == "__main__":
    sys.exit(main())
