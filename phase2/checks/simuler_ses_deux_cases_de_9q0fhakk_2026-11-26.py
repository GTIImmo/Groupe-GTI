#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SES DEUX CASES CORRIGEES SUR LA LIGNE 286 (9Q0FHAKK), SIMULEES SUR UNE COPIE DE L'IMAGE DU PASSAGE 81 -- LECTURE SEULE.

    python -X utf8 -u phase2\checks\simuler_ses_deux_cases_de_9q0fhakk_2026-11-26.py <dossier de sortie>

SON MOT (25/11 au soir) : « Ma ligne 286 porte deux cases qui sont celles de ma ligne 245 : mandat 17253 [...] prix
112 800 [...] Je corrige mes deux cases -- mandat 17010, prix 460 000. Dis-moi d'abord : une fois ces deux cases
corrigees dans mon Sheet, est-ce que 9Q0FHAKK sort du bien 5617 toute seule, est-ce que la vente de PAGES EYRAUD revient
a 7W7XUBPO sans que son etiquette change, et est-ce que R29 peut alors travailler sans franchir aucune garde ? Mesure-le
sur une copie et montre-moi les verdicts qui bougent. »

CE QUE FAIT L'OUTIL : il copie l'image 2026-11-25_072625 dans <dossier de sortie> (JAMAIS dans protocole/images : aucun
passage ne doit la prendre pour la derniere image), y remplace les deux cases de la ligne 9Q0FHAKK dans les deux
fichiers qui portent le Sheet (sheet.json, que lit le juge ; t6_photo.json, que lit l'outil de coupe), et refait le
manifeste en le marquant SIMULEE. Rien d'autre ne change : le registre et le gel sont ceux du 81, octet pour octet.
Le rejeu se lance ensuite avec : rejouer_le_passage_81_sur_copie_2026-11-25.py <copie> --entrees-de-81 --image <image>
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
LIGNE, NUM = "9Q0FHAKK", 286
CORRECTION = {"Mandat": ("17253", "17010"), "Prix": ("112800", "460000")}


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def main() -> int:
    sortie = Path(sys.argv[1]).resolve()
    if P.IMAGES.resolve() in sortie.parents or sortie == P.IMAGES.resolve():
        raise SystemExit("⛔ la copie simulee ne va JAMAIS dans %s" % P.IMAGES)
    d = sortie / (IMAGE_81.name + "_SIMULEE_9Q0FHAKK_MANDAT_17010_PRIX_460000")
    if d.exists():
        raise SystemExit("⛔ %s existe deja" % d)
    P.verifier_image(IMAGE_81)                         # l'image du 81 n'a pas bouge
    shutil.copytree(IMAGE_81, d)
    sheet = json.loads((d / "sheet.json").read_text(encoding="utf-8"))
    photo = json.loads((d / "t6_photo.json").read_text(encoding="utf-8"))
    e = sheet["entete"]
    assert e == photo["entete"]
    lignes = sheet["par_id"][LIGNE]
    assert len(lignes) == 1 and lignes[0]["num"] == NUM, lignes
    rangs = [lignes[0]["row"], photo["lignes"][LIGNE]["row"]]
    lb = sheet.get("lignes_brutes")                    # dans l'image, un COMPTE (pas les rangees)
    brutes = [x for x in (lb if isinstance(lb, list) else []) if isinstance(x, dict) and x.get("num") == NUM]
    rangs += [x["row"] for x in brutes if "row" in x]
    for col, (avant, apres) in CORRECTION.items():
        k = e.index(col)
        for r in rangs:
            assert str(r[k]).strip() == avant, (col, r[k])
            r[k] = apres
    (d / "sheet.json").write_text(json.dumps(sheet, ensure_ascii=False), encoding="utf-8")
    (d / "t6_photo.json").write_text(json.dumps(photo, ensure_ascii=False), encoding="utf-8")
    man = json.loads((d / "manifeste.json").read_text(encoding="utf-8"))
    man["fichiers"] = {f: md5(d / f) for f in man["fichiers"]}
    man["SIMULEE"] = ("copie de l'image %s : ligne %s (n° %d), Mandat 17253 -> 17010 et Prix 112800 -> 460000 -- sa "
                      "correction annoncee le 25/11 au soir ; registre et gel inchanges" % (IMAGE_81.name, LIGNE, NUM))
    (d / "manifeste.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in ("registre.sqlite", "gel.json"):
        assert md5(d / f) == md5(IMAGE_81 / f), f
    print("IMAGE SIMULEE : %s" % d)
    print("   %s (ligne %d) : %s ; %d rangee(s) corrigee(s) (sheet.json, t6_photo.json%s)" % (
        LIGNE, NUM, " ; ".join("%s %s -> %s" % (c, a, b) for c, (a, b) in CORRECTION.items()), len(rangs),
        ", lignes_brutes" if brutes else ""))
    print("   registre.sqlite et gel.json : identiques a l'image du 81")
    return 0


if __name__ == "__main__":
    sys.exit(main())
