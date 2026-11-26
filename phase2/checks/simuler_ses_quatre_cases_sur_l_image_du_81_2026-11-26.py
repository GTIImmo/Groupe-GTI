#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SES QUATRE CASES DU 26/11, ET ELLES SEULES, POSEES SUR UNE COPIE DE L'IMAGE DU PASSAGE 81 -- LECTURE SEULE.

    python -X utf8 -u phase2\checks\simuler_ses_quatre_cases_sur_l_image_du_81_2026-11-26.py <dossier de sortie>

SON MOT (26/11) : « Montre-moi donc l'attribution, ligne par ligne : ce qui vient de mes cases, ce qui vient de v23.1 et
de quelle regle. Tu l'as presque : rejoue la copie avec v23.1 et l'image du 81 -- l'ecart avec tes deux rejeux
d'aujourd'hui, c'est exactement la part de mes cases. »

⚠ POURQUOI UNE SIMULATION ET PAS SEULEMENT L'ECART : entre l'image du 81 (25/11 07:26) et celle du 26/11 (09:49), il n'y a
pas que ses cases -- la vague de 09:02 a change le REGISTRE (chaines, etiquettes, liste E), la nuit a pose 3 pieces, et le
classeur a vecu (8 lignes recentes, une ligne neuve). Pour que « la part de ses cases » soit EXACTE, on pose ses quatre
cases, et rien d'autre, sur l'image du 81 : registre et gel du 81 octet pour octet.

LES QUATRE CASES : leur valeur NEUVE est LUE dans l'image du 26/11 (jamais tapee ici), leur valeur d'avant est VERIFIEE
dans l'image du 81 -- 286 Mandat, 286 Prix, 286 Charge Commission (le juge ne la lit pas), 245 Prix.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

IMAGE_81 = P.IMAGES / "2026-11-25_072625"
IMAGE_NEUVE = P.IMAGES / "2026-11-26_094931"
CASES = [("9Q0FHAKK", 286, "Mandat"), ("9Q0FHAKK", 286, "Prix"), ("9Q0FHAKK", 286, "Charge Commission"),
         ("7W7XUBPO", 245, "Prix")]


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def main() -> int:
    sortie = Path(sys.argv[1]).resolve()
    if P.IMAGES.resolve() in sortie.parents or sortie == P.IMAGES.resolve():
        raise SystemExit("⛔ la copie simulee ne va JAMAIS dans %s" % P.IMAGES)
    d = sortie / (IMAGE_81.name + "_SIMULEE_SES_QUATRE_CASES_DU_26_11")
    if d.exists():
        raise SystemExit("⛔ %s existe deja" % d)
    P.verifier_image(IMAGE_81)
    P.verifier_image(IMAGE_NEUVE)
    neuve = json.loads((IMAGE_NEUVE / "sheet.json").read_text(encoding="utf-8"))
    shutil.copytree(IMAGE_81, d)
    sheet = json.loads((d / "sheet.json").read_text(encoding="utf-8"))
    photo = json.loads((d / "t6_photo.json").read_text(encoding="utf-8"))
    e = sheet["entete"]
    assert e == photo["entete"] == neuve["entete"]
    faites = []
    for ligne, num, col in CASES:
        k = e.index(col)
        (avant_l,) = sheet["par_id"][ligne]
        (apres_l,) = neuve["par_id"][ligne]
        assert avant_l["num"] == apres_l["num"] == num, (ligne, avant_l["num"], apres_l["num"])
        avant, apres = avant_l["row"][k], apres_l["row"][k]
        assert avant != apres, (ligne, col, "la case n'a pas change")
        for r in (avant_l["row"], photo["lignes"][ligne]["row"]):
            assert r[k] == avant, (ligne, col, r[k])
            r[k] = apres
        faites.append("%s (n° %d) « %s » : %r -> %r" % (ligne, num, col, avant, apres))
    (d / "sheet.json").write_text(json.dumps(sheet, ensure_ascii=False), encoding="utf-8")
    (d / "t6_photo.json").write_text(json.dumps(photo, ensure_ascii=False), encoding="utf-8")
    man = json.loads((d / "manifeste.json").read_text(encoding="utf-8"))
    man["fichiers"] = {f: md5(d / f) for f in man["fichiers"]}
    man["SIMULEE"] = ("copie de l'image %s + SES QUATRE CASES lues dans %s, et rien d'autre : %s ; registre et gel du 81"
                      % (IMAGE_81.name, IMAGE_NEUVE.name, " ; ".join(faites)))
    (d / "manifeste.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in ("registre.sqlite", "gel.json"):
        assert md5(d / f) == md5(IMAGE_81 / f), f
    print("IMAGE SIMULEE : %s" % d)
    for f in faites:
        print("   " + f)
    print("   registre.sqlite et gel.json : identiques a l'image du 81")
    return 0


if __name__ == "__main__":
    sys.exit(main())
