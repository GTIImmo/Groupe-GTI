#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LES REFUS DATES DU 11 ET DU 12/11/2026 : COMBIEN VIENNENT DE NOUS ? -- LECTURE SEULE, ⛔ RIEN N'EST ECRIT.

    python -X utf8 -u phase2\checks\compter_nos_refus_des_11_12_11_2026-11-25.py

SA QUESTION (25/11 au soir) : « sur ces 1 206 refus du 11 et 12 novembre, combien viennent de nous ? Si ce sont les
notres, c'est un chantier a part et je veux le savoir avant d'aller plus loin. »

LA DEFINITION, ecrite pour qu'on compte la meme chose des deux cotes :
  - une OFFRE du registre (app_affaire_ledger, kind = 'offre') ;
  - dont le journal de Hektor (propositions_json) porte AU MOINS UN evenement « refus » dont la date, TELLE QU'ELLE EST
    STOCKEE (les 10 premiers caracteres), est 2026-11-11 ou 2026-11-12 ;
  - « vient de nous » : un de nos travaux change_hektor_offre_status de type « refus » (app_console_job) porte le numero
    Hektor de cette offre ; son « origine » dit quel lot l'a pose.
Le temoin : les offres qui portent un refus d'une AUTRE date (son 1 133).

SORTIE : notice/CLASSEUR_NOS_REFUS_DES_11_12_11_LES_OFFRES_2026-11-25.csv -- des NUMEROS seulement (aucun nom), pour
que son controleur fasse la difference ligne par ligne.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

JOURS = ("2026-11-11", "2026-11-12")
SORTIE = RACINE / "notice" / "CLASSEUR_NOS_REFUS_DES_11_12_11_LES_OFFRES_2026-11-25.csv"


def evenements(pj) -> list[dict]:
    try:
        L = json.loads(pj) if pj else []
    except ValueError:
        return []
    return [x for p in (L if isinstance(L, list) else [L]) for x in (p if isinstance(p, list) else [p])
            if isinstance(x, dict)]


def main() -> int:
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, hektor_affaire_id::text, hektor_annonce_id::text, state, propositions_json::text "
               "from public.app_affaire_ledger where kind = 'offre'")
    offres = cu.fetchall()
    cu.execute("select payload_json->>'hektor_offre_id', created_at::text, coalesce(payload_json->>'origine', '?'), status "
               "from public.app_console_job where job_type = 'change_hektor_offre_status' "
               "and payload_json->>'type' = 'refus'")
    jobs: dict = {}
    for h, c, o, s in cu.fetchall():
        jobs.setdefault(str(h), []).append((c[:19], o, s))
    cn.rollback()
    cn.close()

    lignes, autre_date, origine, avant, etat = [], 0, Counter(), Counter(), Counter()
    for a, hid, ann, st, pj in offres:
        ev = evenements(pj)
        refus = [(k, x) for k, x in enumerate(ev) if x.get("type") == "refus"]
        if not refus:
            continue
        ces_jours = [(k, x) for k, x in refus if str(x.get("date") or "")[:10] in JOURS]
        if not ces_jours:
            autre_date += 1
            continue
        k0, x0 = ces_jours[0]
        accepte_avant = any(y.get("type") == "accepte" for y in ev[:k0])
        juste_avant = k0 > 0 and ev[k0 - 1].get("type") == "accepte"
        nos = sorted(j for j in jobs.get(str(hid), []) if j[0][:10] in JOURS)
        org = nos[0][1] if nos else "AUCUN DE NOS TRAVAUX"
        origine[org] += 1
        avant["acceptee avant (n'importe quand)" if accepte_avant else "jamais acceptee avant"] += 1
        avant["acceptee JUSTE avant le refus"] += int(juste_avant)
        etat[st or "?"] += 1
        lignes.append({"app_affaire_id": a, "hektor_offre_id": hid, "hektor_annonce_id": ann,
                       "refus_du": str(x0.get("date"))[:19], "refus_ces_jours_la": len(ces_jours),
                       "acceptee_avant": int(accepte_avant), "acceptee_juste_avant": int(juste_avant),
                       "etat_aujourd_hui": st, "notre_travail_le": nos[0][0] if nos else "",
                       "notre_travail_origine": org, "nos_travaux_ces_jours_la": len(nos)})
    lignes.sort(key=lambda r: r["app_affaire_id"])
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    print("offres portant un refus date du 11 ou du 12/11/2026 : %d" % len(lignes))
    print("   dont portees par UN DE NOS TRAVAUX de refus : %d ; sans aucun de nos travaux : %d" % (
        len(lignes) - origine["AUCUN DE NOS TRAVAUX"], origine["AUCUN DE NOS TRAVAUX"]))
    print("   par origine : %s" % dict(origine.most_common()))
    print("   %s" % dict(avant))
    print("   etat aujourd'hui : %s" % dict(etat.most_common()))
    print("temoin -- offres portant un refus d'une AUTRE date seulement : %d ; total des offres refusees un jour : %d" % (
        autre_date, autre_date + len(lignes)))
    print("la liste (numeros seulement) : %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
