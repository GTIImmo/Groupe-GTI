#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LE TEMOIN DE LA NUIT SUR LES ECRITURES DU CLASSEUR (son mot du 27/11 au soir) -- LECTURE SEULE.

    python -X utf8 -u phase2\checks\temoin_de_la_nuit_ecritures_du_classeur_2026-11-27.py --photo    # le 27/11 au soir
    python -X utf8 -u phase2\checks\temoin_de_la_nuit_ecritures_du_classeur_2026-11-27.py --juger    # le 28/11, APRES 07:45

SON MOT : « Demain matin, avant toute chose, le temoin de la nuit [...] Si un seul de ces quatre bouge, on s'arrete et on
cherche avant de continuer. »
  1. les notes (4 628 au soir du 27/11) : toujours la, TEXTE A L'OCTET (md5 de chaque note) ;
  2. les parts du classeur (classeur_reconstitue, dont les 419 du lot C) : toutes tenues, a l'identique -- donc la nuit a
     bien SAUTE leurs chaines (app_repartition_absorber saute une chaine qui porte une part non « hektor ») ;
  3. les 9 notes saisies a la main : intactes a l'octet ;
  4. les avis : toujours 2 283, 393 et 2 414 cases remplies, chaque ligne a l'octet.
  + (a titre d'information, il ne fait pas tomber le temoin) les dates d'annulation posees chez nous.
⛔ Ne se juge pas entre 04:00 et 07:45 (la nuit et la descente). La photo est dans le cache, pas dans le depot.
Sortie : 0 vert . 1 un des quatre a bouge (on s'arrete) . 2 pas pu mesurer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

PHOTO = Path(r"C:\Hektor\chantier_classeur_q6_cache\temoin_de_la_nuit_2026-11-27.json")
SAISIES = [1001384, 1001388, 1001389, 1001390, 1001391, 1001392, 1001393, 1001394, 1001395]


def h(s) -> str:
    return hashlib.md5(("" if s is None else str(s)).encode("utf-8")).hexdigest()


def mesurer() -> dict:
    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, origine, md5(coalesce(texte, '')) from public.app_affaire_note")
    notes = {str(a): [o, m] for a, o, m in cu.fetchall()}
    cu.execute("select app_chaine_id, cote, rang, hektor_user_id, pourcentage::text, origine, ecrit_par "
               "from public.app_affaire_repartition where origine = 'classeur_reconstitue'")
    parts = {"%s|%s|%s" % (c, co, r): [u, p, o, e] for c, co, r, u, p, o, e in cu.fetchall()}
    cu.execute("select id_unique, coalesce(avis_a_envoyer,''), coalesce(commentaire_avis,''), coalesce(avis_envoye,'') "
               "from public.app_classeur_avis")
    avis = {i: [a, c, e] for i, a, c, e in cu.fetchall()}
    cu.execute("select app_affaire_id, date_annulation_app from public.app_affaire_ledger "
               "where nullif(trim(coalesce(date_annulation_app, '')), '') is not null")
    dates = {str(a): d for a, d in cu.fetchall()}
    cn.close()
    return {"pris_le": datetime.now().isoformat(timespec="seconds"), "notes": notes, "parts": parts, "avis": avis,
            "dates_annulation": dates}


def comptes(m: dict) -> dict:
    av = m["avis"].values()
    return {"notes": len(m["notes"]), "parts_classeur": len(m["parts"]),
            "parts_du_lot_c": sum(1 for v in m["parts"].values() if v[3] == "classeur:3bisC:2026-11-27"),
            "chaines_du_lot_c": len({k.split("|")[0] for k, v in m["parts"].items() if v[3] == "classeur:3bisC:2026-11-27"}),
            "saisies": sum(1 for a in SAISIES if str(a) in m["notes"] and m["notes"][str(a)][0] == "saisie"),
            "avis": [sum(1 for v in av if v[0]), sum(1 for v in av if v[1]), sum(1 for v in av if v[2])],
            "dates_annulation": len(m["dates_annulation"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--photo", action="store_true")
    g.add_argument("--juger", action="store_true")
    a = ap.parse_args()
    heure = datetime.now().strftime("%H:%M")
    if a.juger and "04:00" <= heure < "07:45":
        print("⛔ %s : la nuit ou la descente tourne -- se juge apres 07:45" % heure)
        return 2
    m = mesurer()
    c = comptes(m)
    print("MESURE %s : %s" % (m["pris_le"], c))
    if a.photo:
        if PHOTO.exists():
            print("⛔ la photo existe deja (%s) -- on ne l'ecrase pas" % PHOTO)
            return 2
        PHOTO.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        print("PHOTO ecrite : %s (%d octets, md5 %s)" % (PHOTO, PHOTO.stat().st_size, h(PHOTO.read_text(encoding="utf-8"))[:8]))
        return 0
    p = json.loads(PHOTO.read_text(encoding="utf-8"))
    print("PHOTO    %s : %s" % (p["pris_le"], comptes(p)))
    cris = []
    # 1. les notes, a l'octet
    perdues = sorted(set(p["notes"]) - set(m["notes"]))
    changees = sorted(k for k in p["notes"] if k in m["notes"] and m["notes"][k] != p["notes"][k])
    neuves = sorted(set(m["notes"]) - set(p["notes"]))
    print("1. NOTES : %d perdues, %d changees, %d neuves (une note neuve n'est pas un ecart, elle se NOMME)"
          % (len(perdues), len(changees), len(neuves)))
    if perdues or changees:
        cris.append("notes : perdues %s, changees %s" % (perdues[:10], changees[:10]))
    if neuves:
        print("   neuves : %s" % neuves[:20])
    # 2. les parts du classeur
    pp = sorted(set(p["parts"]) - set(m["parts"]))
    pc = sorted(k for k in p["parts"] if k in m["parts"] and m["parts"][k] != p["parts"][k])
    print("2. PARTS DU CLASSEUR : %d disparues, %d changees (dont lot C : %d) -- %s" % (
        len(pp), len(pc), sum(1 for k in pp + pc if p["parts"][k][3] == "classeur:3bisC:2026-11-27"),
        "la nuit a SAUTE leurs chaines" if not (pp or pc) else "⛔ la nuit les a TOUCHEES"))
    if pp or pc:
        cris.append("parts : disparues %s, changees %s" % (pp[:10], pc[:10]))
    # 3. les 9 notes saisies
    s_ = [a for a in SAISIES if p["notes"].get(str(a)) != m["notes"].get(str(a))]
    print("3. LES 9 NOTES SAISIES : %s" % ("intactes a l'octet" if not s_ else "⛔ touchees : %s" % s_))
    if s_:
        cris.append("notes saisies touchees %s" % s_)
    # 4. les avis
    ap_ = sorted(i for i in p["avis"] if p["avis"][i] != m["avis"].get(i))
    print("4. AVIS : %s / %s -- %s" % (comptes(m)["avis"], comptes(p)["avis"],
                                       "chaque ligne a l'octet" if not ap_ else "⛔ %d ligne(s) changee(s)" % len(ap_)))
    if ap_ or comptes(m)["avis"] != comptes(p)["avis"]:
        cris.append("avis changes %s" % ap_[:10])
    # + les dates d'annulation (information)
    dp = sorted(k for k in p["dates_annulation"] if m["dates_annulation"].get(k) != p["dates_annulation"][k])
    print("+ DATES D'ANNULATION (information) : %d perdues ou changees%s" % (len(dp), (" : %s" % dp[:10]) if dp else ""))
    print("\n⇒ %s" % ("VERT : les quatre tiennent, on peut avancer" if not cris else
                      "⛔ ROUGE -- ON S'ARRETE ET ON CHERCHE : " + " ; ".join(cris)))
    return 0 if not cris else 1


if __name__ == "__main__":
    sys.exit(main())
