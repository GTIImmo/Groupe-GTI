#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""REJOUER LE PASSAGE 82 DU PROTOCOLE SUR UNE COPIE DU SOCLE, AVEC OU SANS UNE VARIANTE (27/11) -- le vrai socle NE PEUT
PAS etre ecrit. Patron : rejouer_le_passage_81_sur_copie_2026-11-25.py (memes deux verrous, meme temoin de fin).

    python -X utf8 -u phase2\checks\rejouer_le_passage_82_avec_une_variante_sur_copie_2026-11-27.py <dossier de copie> [--variantes R30]

SON MOT DU 27/11 : « la regle des 334 [...] c'est ton geste 6. Mesure cette variante dans le juge, sur copie. »
LA METHODE (memoire « une regle se mesure dans le juge ») : d'abord SANS variante -- le temoin : le juge d'aujourd'hui doit
rendre les 4 803 verdicts du passage 82 a l'identique ; sinon une difference AVEC la variante ne dirait pas PAR QUOI. Puis
AVEC : le chiffre annonce est celui du rejeu (verdicts, etiquettes, pieces, preuves), jamais celui d'un script a part.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

VRAI = P.DOSSIER / "socle.sqlite"
VRAI_DOSSIER = P.DOSSIER
REFERENCE = 82


def emp(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("copie")
    ap.add_argument("--variantes", default="", help="ex. R30 ; vide = le temoin, sans variante")
    args = ap.parse_args()
    variantes = {v.strip() for v in args.variantes.split(",") if v.strip()}
    copie_dir = Path(args.copie)
    copie_dir.mkdir(parents=True, exist_ok=False)
    avant = (VRAI.stat().st_mtime, emp(VRAI))
    shutil.copy2(VRAI, copie_dir / "socle.sqlite")
    con = sqlite3.connect("file:%s?mode=ro" % VRAI.as_posix(), uri=True)
    image, code_ref = con.execute("select image, code from passage where id=?", (REFERENCE,)).fetchone()
    con.close()
    ent_ref = json.loads((VRAI_DOSSIER / ("entrees_passage_%d.json" % REFERENCE)).read_text(encoding="utf-8"))

    # ── LE VERROU, etage 1 (le juge) : le vrai socle est interdit -- temoin : il DOIT refuser ──
    P.SOCLES_INTERDITS.add(VRAI)
    P.DOSSIER, P.SOCLE = copie_dir, copie_dir / "socle.sqlite"
    sauve_socle = P.SOCLE
    P.SOCLE = VRAI
    try:
        P.socle()
        print("⛔ TEMOIN DU VERROU (juge) : le vrai socle s'est OUVERT -- ARRET")
        return 2
    except SystemExit as e:
        print("temoin du verrou (juge) : le vrai socle est refuse -> %s" % str(e)[:90])
    P.SOCLE = sauve_socle
    assert P.SOCLE.resolve() != VRAI.resolve() and P.DOSSIER.resolve() != VRAI_DOSSIER.resolve()

    # ── LE VERROU, etage 2 (le disque) : temoin du mecanisme sur une copie JETABLE, puis le vrai en lecture seule ──
    jetable = copie_dir / "temoin_lecture_seule.sqlite"
    shutil.copy2(copie_dir / "socle.sqlite", jetable)
    os.chmod(jetable, stat.S_IREAD)
    c = None
    try:
        c = sqlite3.connect(jetable.as_posix())
        c.execute("create table _temoin (x)")
        c.commit()
        print("⛔ TEMOIN DU VERROU (disque) : un fichier en lecture seule a ete ECRIT -- ARRET")
        return 2
    except sqlite3.OperationalError as e:
        print("temoin du verrou (disque) : un fichier en lecture seule refuse l'ecriture -> %s" % e)
    finally:
        if c is not None:
            c.close()
        os.chmod(jetable, stat.S_IREAD | stat.S_IWRITE)
        jetable.unlink()
    os.chmod(VRAI, stat.S_IREAD)
    try:
        print("passage %d : image %s, code %s ; code du juge aujourd'hui : %s" % (REFERENCE, image, code_ref, P.md5_code()))
        I = P.Image(P.IMAGES / image)
        code = P.etape_passage(I, "rejeu du passage %d SUR COPIE%s" % (
            REFERENCE, (" -- VARIANTE " + "+".join(sorted(variantes))) if variantes else " -- TEMOIN sans variante"),
            "bien", variantes)
    finally:
        os.chmod(VRAI, stat.S_IREAD | stat.S_IWRITE)
    c = sqlite3.connect((copie_dir / "socle.sqlite").as_posix())
    nouveau = c.execute("select max(id) from passage").fetchone()[0]
    q = "select id_unique, verdict, etiquette, motif, pieces, preuves from verdict where passage=?"
    a = {r[0]: r[1:] for r in c.execute(q, (REFERENCE,))}
    b = {r[0]: r[1:] for r in c.execute(q, (nouveau,))}
    c.close()
    assert nouveau != REFERENCE, "le rejeu n'est pas dans la copie"
    noms = ["verdict", "etiquette", "motif", "pieces", "preuves"]
    diff = {n: sorted(i for i in set(a) & set(b) if a[i][k] != b[i][k]) for k, n in enumerate(noms)}
    print("\nREJEU : passage %d (copie) contre le passage %d -- %d lignes au %d, %d dans le rejeu" % (
        nouveau, REFERENCE, len(a), REFERENCE, len(b)))
    for n in noms:
        print("   %-10s differents : %d %s" % (n, len(diff[n]), diff[n][:10]))
    ent = json.loads((copie_dir / ("entrees_passage_%d.json" % nouveau)).read_text(encoding="utf-8"))
    memes = {k.split(" (")[0]: ("=" if ent_ref["entrees"].get(k) == v else "⛔ CHANGEE") for k, v in ent["entrees"].items()}
    print("   les entrees vivantes du rejeu contre celles du %d : %s" % (REFERENCE, memes))
    apres = (VRAI.stat().st_mtime, emp(VRAI))
    print("le VRAI socle : date et empreinte %s" % ("INCHANGEES" if apres == avant else "⛔ CHANGEES"))
    (copie_dir / "rejeu_resume.json").write_text(json.dumps({
        "reference": REFERENCE, "rejeu": nouveau, "variantes": sorted(variantes), "diff": diff,
        "entrees": memes, "vrai_socle_inchange": apres == avant}, ensure_ascii=False, indent=1), encoding="utf-8")
    zero = not any(diff.values()) and set(a) == set(b)
    print("⇒ %s" % ("AUCUN VERDICT DU PASSAGE %d NE CHANGE" % REFERENCE if zero else
                    "%d ligne(s) changent (verdict %d, etiquette %d, pieces %d, preuves %d)" % (
                        len(set().union(*diff.values())), len(diff["verdict"]), len(diff["etiquette"]),
                        len(diff["pieces"]), len(diff["preuves"]))))
    return 0 if apres == avant and code in (0, 1) else 1


if __name__ == "__main__":
    sys.exit(main())
