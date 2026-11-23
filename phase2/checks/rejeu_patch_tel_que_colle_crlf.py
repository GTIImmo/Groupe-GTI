#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE REJEU DU PATCH DU JOURNAL, TEL QU'IL A ETE COLLE : avec des fins de ligne Windows (CRLF).        23/11/2026

    python -u -X utf8 phase2/checks/rejeu_patch_tel_que_colle_crlf.py --pg <binaires du Postgres local>

POURQUOI. Colle dans l'editeur SQL de Supabase, le patch a recu un retour chariot au bout de CHAQUE ligne : la fonction
posee en production porte 214 CR dans son corps (md5(prosrc) 1431b364..., 10 455 caracteres), la copie du 22/11 n'en
portait aucun (ea1d0db1..., 10 241). Sans les CR, les deux sont identiques a l'octet (e695bf7e des deux cotes).
Ce script rejoue LE MEME REJEU que rejeu_patch_journal_sur_copie.py (S0 a S4, temoin du hasard, temoin inverse,
repetition, inverse), mais chaque fichier colle (le patch, l'inverse) est d'abord converti en CRLF -- comme un collage.
Il prouve donc la fonction QUI TOURNE EN PRODUCTION, pas celle du fichier.
⚠ Il ecrit son rejeu.json dans la copie : celui du 22/11 est d'abord garde sous rejeu_22_11_patch_en_LF.json, et le
  neuf est renomme rejeu_23_11_patch_tel_que_colle_CRLF.json, puis l'ancien remis a sa place.
⛔ Rien n'est ecrit en production.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import rejeu_patch_journal_sur_copie as R  # noqa: E402


def jouer_comme_colle(base: str, f: Path, remplacer: tuple | None = None) -> None:
    """Comme R.jouer_fichier, mais le texte passe en CRLF d'abord -- ce que le collage a fait."""
    texte = f.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\n", "\r\n")
    if remplacer:
        if texte.count(remplacer[0]) != 1:
            raise SystemExit("⛔ l'ancre du temoin inverse est trouvee %d fois" % texte.count(remplacer[0]))
        texte = texte.replace(*remplacer)
    cn = R.Local.cnx(base)
    try:
        cn.cursor().execute(texte)
    finally:
        cn.close()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pg", required=True)
    a = ap.parse_args()
    d = R.CACHE / "2026-11-22_201242"
    garde = d / "rejeu_22_11_patch_en_LF.json"
    if not garde.exists():
        shutil.copy2(d / "rejeu.json", garde)
    R.jouer_fichier = jouer_comme_colle
    print("⚠ CHAQUE FICHIER COLLE (patch, inverse) PASSE EN CRLF AVANT D'ETRE JOUE -- comme le collage du 23/11", flush=True)
    code = R.etape_rejouer(Path(a.pg), "2026-11-22_201242")
    (d / "rejeu.json").replace(d / "rejeu_23_11_patch_tel_que_colle_CRLF.json")
    shutil.copy2(garde, d / "rejeu.json")
    cn = None
    print("(rejeu du 22/11 remis en place ; le neuf : %s)" % (d / "rejeu_23_11_patch_tel_que_colle_CRLF.json"), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
