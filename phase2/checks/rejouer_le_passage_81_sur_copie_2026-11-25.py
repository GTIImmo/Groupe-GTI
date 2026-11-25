#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""REJOUER LE PASSAGE 81 DU PROTOCOLE SUR UNE COPIE DU SOCLE (son mot du 25/11) -- le vrai socle NE PEUT PAS etre ecrit.

    python -X utf8 -u phase2\checks\rejouer_le_passage_81_sur_copie_2026-11-25.py <dossier de copie> [--entrees-de-81]

SON MOT : « Je veux savoir si ta retouche change UN SEUL verdict du passage 81. » ; « fais entrer dans l'empreinte du juge
TOUTES ses entrees vivantes [...] et dis-moi si le passage 81 avait d'autres entrees de ce genre qui ont bouge depuis ce
matin. Si oui, mes 100 lignes ont ete jugees sur un etat que je ne peux plus reconstituer » ; « Fais qu'un rejeu sur copie
ne PUISSE PLUS ecrire dans le vrai socle, meme par erreur. »

LE VERROU DU VRAI SOCLE, A DEUX ETAGES (25/11, apres le passage 82 ecrit par erreur a 14:51) :
  1. dans le juge : le vrai socle est inscrit dans P.SOCLES_INTERDITS -- socle() refuse de l'ouvrir, meme si un chemin
     n'a pas ete detourne ; temoin : on essaie, il DOIT refuser ;
  2. sur le disque : le vrai fichier est mis en LECTURE SEULE pendant tout le rejeu (rendu ensuite) -- meme un code qui
     contournerait le juge ne pourrait pas l'ecrire ; temoin du mecanisme sur une copie jetable : une ecriture DOIT echouer.
  Et le temoin de fin : date et empreinte du vrai socle, avant et apres.

--entrees-de-81 : les entrees vivantes REMISES dans l'etat du passage 81 (07:26) -- la liste E telle que la sauvegarde de
la vague (09:02, avant qu'elle la touche) la donne ; « ses 20 a part » et les mandants R16 n'ont pas bouge depuis le 22-23/11.
Si le rejeu rend alors les 4 802 verdicts du 81 a l'identique, l'etat du 81 est RECONSTITUE : son empreinte d'entrees est
ecrite a cote du socle (entrees_passage_81.json).
"""
from __future__ import annotations

import argparse
import ast
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
MODULE_AVANT_LA_VAGUE = Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir\20261125_090205_GESTE\sauvegardes"
                             r"\affaire_ledger.py")


def emp(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def liste_e(p: Path) -> dict:
    for n in ast.parse(p.read_text(encoding="utf-8")).body:
        cible = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
        if isinstance(cible, ast.Name) and cible.id == "EXCLUES_DE_LA_REGLE_E":
            return ast.literal_eval(n.value)
    raise SystemExit("⛔ EXCLUES_DE_LA_REGLE_E introuvable dans %s" % p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("copie")
    ap.add_argument("--entrees-de-81", action="store_true")
    args = ap.parse_args()
    copie_dir = Path(args.copie)
    copie_dir.mkdir(parents=True, exist_ok=False)
    avant = (VRAI.stat().st_mtime, emp(VRAI))
    shutil.copy2(VRAI, copie_dir / "socle.sqlite")
    con = sqlite3.connect("file:%s?mode=ro" % VRAI.as_posix(), uri=True)
    image, code81, version81 = con.execute("select image, code, version from passage where id=81").fetchone()
    con.close()

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
            c.close()                       # ⚠ 25/11 : une connexion ouverte empechait d'effacer la copie jetable
        os.chmod(jetable, stat.S_IREAD | stat.S_IWRITE)
        jetable.unlink()
    os.chmod(VRAI, stat.S_IREAD)
    try:
        print("passage 81 : image %s, code %s" % (image, code81))
        print("code du juge aujourd'hui : %s (%s)" % (P.md5_code(), "IDENTIQUE" if P.md5_code() == code81 else
                                                      "DIFFERENT -- v22 : l'empreinte des entrees et le verrou du socle"))
        if args.entrees_de_81:
            e81 = liste_e(MODULE_AVANT_LA_VAGUE)
            P._EXCLUES_E.clear()
            P._EXCLUES_E.update(e81)
            print("ENTREES DU 81 REMISES : liste E de la sauvegarde de 09:02 (avant la vague) = %s ; aujourd'hui = %s" % (
                sorted(e81), sorted(liste_e(P.RACINE / "phase2" / "sync" / "affaire_ledger.py"))))
        I = P.Image(P.IMAGES / image)
        code = P.etape_passage(I, "rejeu du passage 81 SUR COPIE%s" % (" -- entrees du 81 remises" if args.entrees_de_81
                                                                      else " -- entrees d'aujourd'hui"), "bien")
    finally:
        os.chmod(VRAI, stat.S_IREAD | stat.S_IWRITE)
    c = sqlite3.connect((copie_dir / "socle.sqlite").as_posix())
    nouveau = c.execute("select max(id) from passage").fetchone()[0]
    q = "select id_unique, verdict, etiquette, motif, pieces, preuves from verdict where passage=?"
    a = {r[0]: r[1:] for r in c.execute(q, (81,))}
    b = {r[0]: r[1:] for r in c.execute(q, (nouveau,))}
    c.close()
    assert nouveau != 81, "le rejeu n'est pas dans la copie"
    noms = ["verdict", "etiquette", "motif", "pieces", "preuves"]
    diff = {n: sorted(i for i in set(a) & set(b) if a[i][k] != b[i][k]) for k, n in enumerate(noms)}
    print("\nREJEU : passage %d (copie) contre le passage 81 -- %d lignes en 81, %d dans le rejeu" % (nouveau, len(a), len(b)))
    for n in noms:
        print("   %-10s differents : %d %s" % (n, len(diff[n]), diff[n][:10]))
    for i in sorted(set(diff["verdict"])):
        print("   %s : 81 %s %s | rejeu %s %s" % (i, a[i][0], a[i][2], b[i][0], b[i][3]))
    ent = json.loads((copie_dir / ("entrees_passage_%d.json" % nouveau)).read_text(encoding="utf-8"))
    print("   les entrees du rejeu : %s ; empreinte du juge %s" % (
        {k.split(" (")[0]: v[:8] for k, v in ent["entrees"].items()}, ent["empreinte_du_juge"][:8]))
    apres = (VRAI.stat().st_mtime, emp(VRAI))
    print("le VRAI socle : date et empreinte %s" % ("INCHANGEES" if apres == avant else "⛔ CHANGEES"))
    zero = not any(diff.values()) and set(a) == set(b)
    if args.entrees_de_81 and zero and apres == avant:
        sortie = VRAI_DOSSIER / "entrees_passage_81.json"
        sortie.write_text(json.dumps({
            "passage": 81, "image": image, "code": code81, "entrees": ent["entrees"],
            "reconstitue_le": ent["fait_le"], "comment": "les entrees vivantes du passage 81 (07:26:42), RECONSTITUEES : "
            "liste E de la sauvegarde de la vague (09:02, avant sa modification) ; a20 et mandants R16 inchanges depuis le "
            "22-23/11. Preuve : le rejeu avec ces entrees rend les 4 802 verdicts du 81 a l'identique (verdict, etiquette, "
            "motif, pieces, preuves). Le code du 81 est b47f603b (v21) ; l'empreinte du juge v22 ne s'applique pas au 81."},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print("⇒ L'ETAT DU 81 EST RECONSTITUE : 4 802 / 4 802 identiques -> %s" % sortie)
    print("⇒ %s" % ("AUCUN VERDICT DU PASSAGE 81 NE CHANGE" if zero else "%d VERDICT(S) CHANGENT" % len(diff["verdict"])))
    return 0 if apres == avant and code in (0, 1) else 1


if __name__ == "__main__":
    sys.exit(main())
