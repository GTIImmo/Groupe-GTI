#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""REJOUER LE PASSAGE 81 DU PROTOCOLE AVEC LE CODE D'AUJOURD'HUI, SUR UNE COPIE DU SOCLE (son mot du 25/11).

    python -X utf8 -u phase2\checks\rejouer_le_passage_81_sur_copie_2026-11-25.py <dossier de copie>

SON MOT : « Je veux savoir si ta retouche change UN SEUL verdict du passage 81. »
Le juge (protocole_classeur.py et ses deux modules) est rejoue sur LA MEME IMAGE (2026-11-25_072625) que le passage 81,
dans une COPIE du socle : le vrai socle n'est pas ouvert en ecriture (sa date et son empreinte sont relues avant et
apres). Puis chaque ligne est comparee : verdict, etiquette, motif, pieces, preuves.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

VRAI = P.DOSSIER / "socle.sqlite"


def emp(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    copie_dir = Path(sys.argv[1])
    copie_dir.mkdir(parents=True, exist_ok=False)
    avant = (VRAI.stat().st_mtime, emp(VRAI))
    shutil.copy2(VRAI, copie_dir / "socle.sqlite")
    con = sqlite3.connect("file:%s?mode=ro" % VRAI.as_posix(), uri=True)
    image, code81, version81 = con.execute("select image, code, version from passage where id=81").fetchone()
    con.close()
    print("passage 81 : image %s, code %s, %s" % (image, code81, version81))
    print("code d'aujourd'hui : %s -> %s" % (P.md5_code(), "IDENTIQUE" if P.md5_code() == code81 else "⛔ DIFFERENT"))
    # ⛔ 25/11, 14:51 : la 1re version ne changeait QUE P.DOSSIER -- or socle() ouvre P.SOCLE, fixe a l'import : le
    #   passage s'est ecrit dans le VRAI socle (son propre temoin l'a vu : « date et empreinte CHANGEES »). Remis a
    #   l'identique depuis la copie, l'etat pollue garde en sauvegarde datee. LES DEUX chemins vont dans la copie :
    P.DOSSIER = copie_dir                                   # les fichiers du passage (mises de cote)
    P.SOCLE = copie_dir / "socle.sqlite"                    # le socle lui-meme
    assert P.SOCLE.resolve() != VRAI.resolve()
    I = P.Image(P.IMAGES / image)
    code = P.etape_passage(I, "rejeu du passage 81 avec le code du 25/11 (son mot) -- SUR COPIE", "bien")
    c = sqlite3.connect((copie_dir / "socle.sqlite").as_posix())
    nouveau = c.execute("select max(id) from passage").fetchone()[0]
    q = "select id_unique, verdict, etiquette, motif, pieces, preuves from verdict where passage=?"
    a = {r[0]: r[1:] for r in c.execute(q, (81,))}
    b = {r[0]: r[1:] for r in c.execute(q, (nouveau,))}
    c.close()
    noms = ["verdict", "etiquette", "motif", "pieces", "preuves"]
    diff = {n: sorted(i for i in set(a) & set(b) if a[i][k] != b[i][k]) for k, n in enumerate(noms)}
    print("\nREJEU : passage %d (copie) contre le passage 81 -- %d lignes en 81, %d dans le rejeu, communes %d" % (
        nouveau, len(a), len(b), len(set(a) & set(b))))
    for n in noms:
        print("   %-10s differents : %d %s" % (n, len(diff[n]), diff[n][:10]))
    print("   lignes seulement en 81 : %s ; seulement dans le rejeu : %s" % (sorted(set(a) - set(b))[:10],
                                                                         sorted(set(b) - set(a))[:10]))
    apres = (VRAI.stat().st_mtime, emp(VRAI))
    print("le VRAI socle : date et empreinte %s" % ("INCHANGEES" if apres == avant else "⛔ CHANGEES"))
    # la cause, nommee : le juge lit EN DIRECT les exclusions de la regle E (affaire_ledger.py), hors de son empreinte
    for i in sorted(set(diff["verdict"])):
        print("   %s : 81 %s %s | rejeu %s %s" % (i, a[i][0], a[i][2], b[i][0], b[i][3]))
    import ast
    src = (ICI.parents[1] / "phase2" / "sync" / "affaire_ledger.py").read_text(encoding="utf-8")
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "EXCLUES_DE_LA_REGLE_E":
            print("   EXCLUES_DE_LA_REGLE_E aujourd'hui (lu en direct par le juge) : %s" % sorted(ast.literal_eval(n.value)))
    zero = not any(diff.values()) and set(a) == set(b) and apres == avant
    print("⇒ %s" % ("AUCUN VERDICT DU PASSAGE 81 NE CHANGE" if zero else "⛔ DES VERDICTS CHANGENT -- ARRET"))
    return 0 if zero and code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
