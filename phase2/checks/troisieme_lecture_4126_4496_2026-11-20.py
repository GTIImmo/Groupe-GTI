#!/usr/bin/env python
"""LA TROISIEME LECTURE DE 4126 ET 4496 -- chantier classeur, ⑬, 20/11/2026. LECTURE SEULE.

Ce que ferait au chainage le rattachement, DECIDE A LA MAIN, de chaque compromis annule sans date a l'offre
refusee de l'acheteur dont il est probablement la tentative ratee :
     4126 -> 4128   bien 9232   GAIGA (offre refusee du 30/09/2021, 77 000)
     4496 -> 4498   bien 9769   BISCH (offre refusee du 14/04/2021, 155 000 -- le compromis annule vaut 155 000)

⛔ RIEN N'EST AJOUTE A phase2/sync/rattachements_manuels.csv : c'est la decision de Frederic, ligne a ligne.
   Le rejeu lit une COPIE du fichier (dans un dossier temporaire) et une COPIE de la base (en memoire).

USAGE (une etape par appel, python -u) :
   rejeu tel_quel        le chainage d'aujourd'hui (E allumee, comme le run de samedi)
   rejeu avec_les_deux   le meme, avec les deux lignes proposees -- ⚠ LE CODE D'AUJOURD'HUI LES REFUSE
                         (« transaction introuvable ») : une transaction sans date exclue de E n'est jamais
                         sous les yeux du fichier manuel. C'est un TEMOIN, il doit montrer 0 changement.
   rejeu copie_avec_la_piece   les deux lignes ET la piece qui manque, sur une COPIE du module (l'original
                         n'est pas touche) : dans la boucle du fichier manuel, une source SANS DATE restee seule
                         du MEME bien rejoint directement le dossier de la cible -- sans passer par E ni D.
   comparer <variante>   ce qui bouge par rapport a tel_quel -- avec_les_deux : RIEN (le temoin) ;
                         copie_avec_la_piece : les deux dossiers attendus, et RIEN d'autre
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
CACHE = RACINE.parent / "chantier_classeur_q6_cache" / "troisieme_lecture_4126_4496"
JOURNAL = CACHE / "journal.txt"
BASE = RACINE / "phase2" / "phase2.sqlite"

LES_DEUX = (
    "4126;4128;9232;PROPOSEE-20/11;GAIGA -- le compromis annule sans date de la tentative de GAIGA (offre 4128 du "
    "30/09/2021, 77 000) ; le Sheet P252U1JH dit le dossier ouvert chez les notaires le 07/01 puis annule le 22/01/2022\n"
    "4496;4498;9769;PROPOSEE-20/11;BISCH -- le compromis annule vaut 155 000 = l'offre de BISCH (4498, 155 000) ; "
    "la chaine NOIRJEAN FAUCHEZ vaut 159 000\n"
)
SUIVIES = (4125, 4126, 4127, 4128, 4129, 4495, 4496, 4497, 4498, 4499)


def journal(texte: str) -> None:
    print(texte, flush=True)
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write("%s  %s\n" % (datetime.now().strftime("%H:%M:%S"), texte))


PIECE_ANCRE = """                if ch_source is None or ch_cible is None:
                    # ⚠ Une transaction disparue de chez Hektor sort du registre :"""
PIECE_CODE = """                if (ch_source is None and ch_cible is not None
                        and source_id in {sd[0] for sd in sans_date_du_bien}):
                    ch_cible["membres"].append(source_id)
                    signale("[M] COPIE -- transaction SANS DATE rattachee a la main")
                    continue
"""


def module_avec_la_piece():
    """Une COPIE de affaire_ledger.py avec la piece, chargee a part. L'original n'est pas touche."""
    import importlib.util
    source = (RACINE / "phase2" / "sync" / "affaire_ledger.py").read_text(encoding="utf-8")
    assert source.count(PIECE_ANCRE) == 1, "l'ancre du fichier manuel a bouge"
    source = source.replace(PIECE_ANCRE, PIECE_CODE + PIECE_ANCRE)
    for avant, apres in (("ROOT = Path(__file__).resolve().parents[2]", "ROOT = Path(%r)" % str(RACINE)),
                         ('FICHIER_RATTACHEMENTS = Path(__file__).resolve().parent / "rattachements_manuels.csv"',
                          "FICHIER_RATTACHEMENTS = Path(%r)" % str(RACINE / "phase2" / "sync" / "rattachements_manuels.csv"))):
        assert source.count(avant) == 1, "ancre absente : %s" % avant
        source = source.replace(avant, apres)
    copie = CACHE / "affaire_ledger_AVEC_LA_PIECE_mesure_seulement.py"
    copie.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("affaire_ledger_avec_la_piece", copie)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rejeu(variante: str) -> int:
    if variante == "copie_avec_la_piece":
        al = module_avec_la_piece()
    else:
        from phase2.sync import affaire_ledger as al
    t0 = time.time()
    al.chainage_v2_actif()                      # charge .env comme le run (E y est allumee depuis le 20/11 07:26)
    journal("REJEU %s : E lue = %s" % (variante, al.chainage_sans_date_visible_actif()))
    if not al.chainage_sans_date_visible_actif():
        journal("⛔ E n'est pas lue allumee : le rejeu ne serait pas celui du run de samedi (code 2)")
        return 2
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    con = sqlite3.connect(":memory:")
    src.backup(con)
    src.close()
    journal("   base copiee en memoire (%.0f s)" % (time.time() - t0))
    with tempfile.TemporaryDirectory() as tmp:
        if variante in ("avec_les_deux", "copie_avec_la_piece"):
            f = Path(tmp) / "rattachements_avec_les_deux.csv"
            f.write_text(al.FICHIER_RATTACHEMENTS.read_text(encoding="utf-8-sig") + LES_DEUX, encoding="utf-8")
            al.FICHIER_RATTACHEMENTS = f
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            compte = al.recalculer_les_chaines(con)
    ch = {a: c for a, c in con.execute("SELECT app_affaire_id, app_chaine_id FROM app_affaire_ledger")}
    texte = sortie.getvalue()
    refus = [l for l in texte.splitlines() if "REFUS" in l.upper() and ("4126" in l or "4496" in l)]
    (CACHE / ("chaines_%s.json" % variante)).write_text(json.dumps(
        {"chaines": {str(a): c for a, c in ch.items()}, "compte": {k: v for k, v in compte.items()},
         "refus": refus}, ensure_ascii=False), encoding="utf-8")
    journal("   %d transactions, %d dossiers ; rattachements a la main lus : %s ; refus nommant 4126/4496 : %s (%.0f s)"
            % (len(ch), len(set(ch.values())),
               {k: v for k, v in compte.items() if "manuel" in k.lower() or "[M]" in k}, refus, time.time() - t0))
    for a in SUIVIES:
        journal("      %s -> dossier %s" % (a, ch.get(a)))
    return 0


def comparer(variante: str) -> int:
    t = json.loads((CACHE / "chaines_tel_quel.json").read_text(encoding="utf-8"))["chaines"]
    d = json.loads((CACHE / ("chaines_%s.json" % variante)).read_text(encoding="utf-8"))["chaines"]
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    uuid = {str(a): u for a, u in src.execute("SELECT app_affaire_id, app_dossier_uuid FROM app_affaire_ledger")}

    def groupes(ch):
        g = defaultdict(set)
        for a, c in ch.items():
            g[c].add(int(a))
        return {frozenset(v) for v in g.values()}
    gt, gd = groupes(t), groupes(d)
    partis, venus = sorted(map(sorted, gt - gd)), sorted(map(sorted, gd - gt))
    journal("COMPARER tel_quel / %s : %d dossiers, %d" % (variante, len(gt), len(gd)))
    journal("   dossiers qui disparaissent : %s" % partis)
    journal("   dossiers qui apparaissent  : %s" % venus)
    attendu = [sorted({4126, 4128}), sorted({4496, 4498})]
    hors = [g for g in venus if g not in attendu]
    touchees = sorted({a for g in partis for a in g})
    journal("   transactions touchees : %s" % touchees)
    for g in venus:
        garde = uuid[str(min(g))]
        journal("   dossier %s : l'etiquette de %d (la plus petite) est GARDEE = %s ; ABSORBEES : %s"
                % (g, min(g), garde, sorted({uuid[str(a)] for a in g} - {garde})))
    if variante == "avec_les_deux":
        ok = not partis and not venus
        journal("   VERDICT DU TEMOIN : %s" % ("VERT -- le code d'aujourd'hui REFUSE les deux lignes : rien ne bouge"
                                             if ok else "ROUGE -- le code d'aujourd'hui les a prises"))
        return 0 if ok else 1
    ok = sorted(venus) == sorted(attendu) and not hors and set(touchees) == {4126, 4128, 4496, 4498}
    journal("   VERDICT : %s" % ("VERT -- les deux dossiers attendus, rien d'autre ne bouge" if ok else
                                 "ROUGE -- autre chose bouge, ou le rattachement n'a pas joue"))
    return 0 if ok else 1


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    variantes = ("tel_quel", "avec_les_deux", "copie_avec_la_piece")
    if len(sys.argv) >= 3 and sys.argv[1] == "rejeu" and sys.argv[2] in variantes:
        return rejeu(sys.argv[2])
    if len(sys.argv) >= 3 and sys.argv[1] == "comparer" and sys.argv[2] in variantes[1:]:
        return comparer(sys.argv[2])
    print(__doc__)
    return 3


if __name__ == "__main__":
    os.chdir(RACINE)
    sys.exit(main())
