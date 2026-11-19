#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""QUESTION 6 (et la part chiffree de la 7) -- LES LIGNES DU SHEET A PLUSIEURS ETIQUETTES,
APRES CHAQUE CORRECTION.                                                               19/11/2026

⛔ CE SCRIPT N'ECRIT RIEN en base, chez Hektor ni dans le Sheet : phase2.sqlite en mode=ro, tout en
  memoire ; le Sheet en lecture (le juge de ⑤) ; les interrupteurs et le fichier des rattachements ne
  sont modifies QUE dans ce processus.

⚠ DECOUPE EN ETAPES (19/11, apres une premiere mesure d'un seul bloc tuee par son delai, sortie vide).
  Chaque etape tient en moins de dix minutes, ECRIT SON RESULTAT SUR LE DISQUE (dans CACHE, hors du
  depot) et imprime au fil de l'eau. Une coupure ne fait perdre que l'etape en cours.

    .venv\Scripts\python.exe -X utf8 -u phase2\checks\temps5_q6_les_lignes_a_plusieurs_etiquettes_2026-11-19.py rejeu 1
    ... rejeu 2 . rejeu 3 . compte . classer

POURQUOI UNE LIGNE « A PLUSIEURS ETIQUETTES » = UNE LIGNE DONT LES TRANSACTIONS SONT DANS PLUSIEURS
DOSSIERS. La pose de nuit (app_poser_etiquettes_dossier) fait pose -> propagation -> fusion -> scission :
apres elle, chaque dossier porte UNE etiquette et deux dossiers n'en partagent jamais. On le VERIFIE sur
la base d'aujourd'hui (temoin de l'etape « compte »), puis on compte par dossiers dans chaque scenario.

LES SCENARIOS (chacun ajoute au precedent) -- et le gel tel quel / le gel apres le patch V2 :
    0  la base d'aujourd'hui
    1  + les 10 rattachements « menage » (ECRITS le 19/11 : ils jouent cette nuit)
    2  + la regle E, avec l'exclusion de 26613 (codee, ETEINTE : simulee ici seulement)
    3  + les 8 lignes « pures » de ⑤ (PROPOSEES, non ecrites : simulees ici seulement)

CE QUI RESTE, classe par le juge de ⑤ (colonnes independantes, jamais le gel pour choisir) :
    C5          la ligne tient une transaction creee depuis le Sheet, coupee de son dossier le 18/11
    LE SHEET LES TIENT   la ligne designe, de facon independante, une transaction de CHAQUE dossier :
                c'est le chainage qui coupe une affaire (casse) ou qui en melange deux
    LE GEL DEBORDE       un des dossiers n'a AUCUNE transaction que la ligne designe : le lien vient du
                gel seul -- a lire comme une erreur possible du gel
    NON TRANCHE          le juge ne voit la ligne nulle part

Sortie : 0 etape faite . 2 un temoin a echoue . 3 une etape precedente manque.
"""
from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
import phase2.sync.affaire_ledger as al                                            # noqa: E402

BASE = RACINE / "phase2" / "phase2.sqlite"
PATCH_V2 = RACINE / "supabase" / "patch_correction_gel_audit_v2_2026-11-19.sql"
#: hors du depot (C:\Hektor n'est pas un depot git) : durable, et pas de fouillis dans git status
CACHE = RACINE.parent / "chantier_classeur_q6_cache"
#: ⚠ en .md : les .txt de notice/ sont ignores par git
SORTIE_COMPTES = RACINE / "notice" / "TEMPS5_Q6_COMPTES_PAR_SCENARIO_2026-11-19.md"
SORTIE = RACINE / "notice" / "TEMPS5_Q6_LIGNES_A_PLUSIEURS_ETIQUETTES_2026-11-19.csv"
LES_DIX = {5356, 5408, 13056, 16866, 17278, 20196, 21339, 22069, 26825, 28328}
LES_HUIT = """988;987;1950;2026-11-19;EL FAQRAOUI (propose, Q5)
4907;4906;10374;2026-11-19;VIALLE (propose, Q5)
4932;4931;10396;2026-11-19;URBAIN (propose, Q5)
7600;7599;15439;2026-11-19;GASMI (propose, Q5)
14928;14927;30678;2026-11-19;BEZIER GUILLEMIN (propose, Q5)
16879;16878;35735;2026-11-19;BOUCHARD (propose, Q5)
21799;21798;43432;2026-11-19;BESSET (propose, Q5)
25992;25991;50165;2026-11-19;MAGAND (propose, Q5)
"""
NOMS = {0: "0 la base d'aujourd'hui", 1: "1 + les 10 menages (cette nuit)",
        2: "2 + la regle E avec l'exclusion", 3: "3 + les 8 lignes pures de Q5"}


def ecrire_json(chemin: Path, obj) -> None:
    """Ecriture atomique : une coupure ne laisse jamais un fichier a moitie ecrit."""
    tmp = chemin.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(chemin)


def lire_json(chemin: Path):
    if not chemin.exists():
        print("⛔ etape precedente absente : %s (code 3)" % chemin, flush=True)
        sys.exit(3)
    return json.loads(chemin.read_text(encoding="utf-8"))


def copie() -> sqlite3.Connection:
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def rejouer(regle_e: bool, fichier: Path) -> dict:
    d_origine = al.FICHIER_RATTACHEMENTS
    al.FICHIER_RATTACHEMENTS = fichier
    if regle_e:
        os.environ["APP_CHAINAGE_SANS_DATE_VISIBLE"] = "1"
    else:
        os.environ.pop("APP_CHAINAGE_SANS_DATE_VISIBLE", None)
    try:
        con = copie()
        with contextlib.redirect_stdout(io.StringIO()):
            al.recalculer_les_chaines(con)
        return dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {al.LEDGER_TABLE}"))
    finally:
        al.FICHIER_RATTACHEMENTS = d_origine
        os.environ.pop("APP_CHAINAGE_SANS_DATE_VISIBLE", None)


def etape_rejeu(n: int) -> int:
    t0 = time.time()
    print("REJEU du scenario %s ..." % NOMS[n], flush=True)
    fichier_reel = al.FICHIER_RATTACHEMENTS
    with tempfile.TemporaryDirectory() as tmp:
        fichier = fichier_reel
        if n == 3:
            fichier = Path(tmp) / "rattachements_avec_les_huit.csv"
            fichier.write_text(fichier_reel.read_text(encoding="utf-8-sig") + LES_HUIT, encoding="utf-8")
        chaines = rejouer(n >= 2, fichier)
    CACHE.mkdir(exist_ok=True)
    ecrire_json(CACHE / ("chaines_s%d.json" % n), {str(a): c for a, c in chaines.items()})
    print("   %d transactions, %d dossiers, en %.0f s -> %s"
          % (len(chaines), len(set(chaines.values())), time.time() - t0, CACHE / ("chaines_s%d.json" % n)),
          flush=True)
    return 0


def lire_patch_v2() -> tuple[set, set]:
    """Les 45 retraits et les 78 ajouts du patch V2, lus DANS le fichier (blocs ③ et ④)."""
    texte = PATCH_V2.read_text(encoding="utf-8")
    bloc3 = texte.split("-- ── ③ RETIRER")[1].split("-- ── ④ AJOUTER")[0]
    bloc4 = texte.split("-- ── ④ AJOUTER")[1].split("-- ── ⑤ LE CONTROLE")[0]
    retraits = {(i, int(a)) for i, a in re.findall(r"\('([^']+)',\s*(\d+),\s*'\w+'\)", bloc3)}
    ajouts = {(i, int(a)) for a, i in re.findall(r"\(\d+,\s*(\d+),\s*'\w+',.*?'([^']+)'\)", bloc4)}
    return retraits, ajouts


def les_gels(src) -> tuple[dict, dict, list]:
    echecs = []
    gel = defaultdict(set)
    for ident, a in src.execute("SELECT id_unique, app_affaire_id FROM app_classeur_lien"):
        gel[ident].add(a)
    retraits, ajouts = lire_patch_v2()
    print("PATCH V2 lu dans le fichier : %d retraits, %d ajouts (attendu 45 / 78)" % (len(retraits), len(ajouts)),
          flush=True)
    if (len(retraits), len(ajouts)) != (45, 78):
        echecs.append("lecture du patch")
    gel_v2 = defaultdict(set, {k: set(v) for k, v in gel.items()})
    for ident, a in retraits:
        gel_v2[ident].discard(a)
    for ident, a in ajouts:
        gel_v2[ident].add(a)
    n0, n2 = sum(len(v) for v in gel.values()), sum(len(v) for v in gel_v2.values())
    print("   gel : %d liens -> %d apres le patch (attendu 12 787 -> 12 820)" % (n0, n2), flush=True)
    if (n0, n2) != (12787, 12820):
        echecs.append("taille du gel")
    return gel, gel_v2, echecs


def multi(g: dict, chaines: dict) -> dict:
    sortie = {}
    for i, ts in g.items():
        ds = {chaines[a] for a in ts if a in chaines}
        if len(ds) > 1:
            sortie[i] = sorted(ds)
    return sortie


def etape_compte() -> int:
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    gel, gel_v2, echecs = les_gels(src)
    base_ch, base_uuid = {}, {}
    for a, ch, u in src.execute("SELECT app_affaire_id, app_chaine_id, app_dossier_uuid FROM app_affaire_ledger"):
        base_ch[a], base_uuid[a] = ch, u
    # TEMOIN 1 : sur la base, « plusieurs etiquettes » = « plusieurs dossiers »
    m_uuid = {i for i, ts in gel.items() if len({base_uuid[a] for a in ts if a in base_uuid}) > 1}
    m_ch = set(multi(gel, base_ch))
    print("TEMOIN : lignes a plusieurs ETIQUETTES %d . a plusieurs DOSSIERS %d . difference %d (attendu 0)"
          % (len(m_uuid), len(m_ch), len(m_uuid ^ m_ch)), flush=True)
    if m_uuid ^ m_ch:
        echecs.append("etiquette != dossier : %s" % sorted(m_uuid ^ m_ch)[:10])
    scen = {0: base_ch}
    for n in (1, 2, 3):
        scen[n] = {int(a): c for a, c in lire_json(CACHE / ("chaines_s%d.json" % n)).items()}
    # TEMOIN 2 : le scenario 1 ne differe de la base QUE par les 10 offres du 19/11
    ecart1 = {a for a in base_ch if scen[1].get(a) != base_ch[a]}
    print("TEMOIN : scenario 1 contre la base : %d transactions bougent, dont %d hors des 10 (attendu 10 / 0)"
          % (len(ecart1), len(ecart1 - LES_DIX)), flush=True)
    if ecart1 != LES_DIX:
        echecs.append("scenario 1 : %s" % sorted(ecart1 ^ LES_DIX)[:10])
    lignes = ["LIGNES DU SHEET A PLUSIEURS ETIQUETTES       gel tel quel   gel apres le patch V2"]
    resultat = {}
    for n in (0, 1, 2, 3):
        a_, b_ = multi(gel, scen[n]), multi(gel_v2, scen[n])
        resultat[n] = {"gel": a_, "gel_v2": b_}
        lignes.append("   %-40s %8d %16d" % (NOMS[n], len(a_), len(b_)))
    for l in lignes:
        print(l, flush=True)
    # qui sort, qui entre, d'un scenario a l'autre (gel tel quel puis gel V2)
    for cle in ("gel", "gel_v2"):
        for n in (1, 2, 3):
            avant, apres = set(resultat[n - 1][cle]), set(resultat[n][cle])
            lignes.append("   %-7s %d -> %d : %d lignes reglees, %d lignes NOUVELLES %s"
                          % (cle, n - 1, n, len(avant - apres), len(apres - avant), sorted(apres - avant)[:8]))
    for n in (0, 1, 2, 3):
        avant, apres = set(resultat[n]["gel"]), set(resultat[n]["gel_v2"])
        lignes.append("   patch V2 sur le scenario %d : %d lignes reglees, %d lignes NOUVELLES %s"
                      % (n, len(avant - apres), len(apres - avant), sorted(apres - avant)[:8]))
    for l in lignes[5:]:
        print(l, flush=True)
    SORTIE_COMPTES.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    ecrire_json(CACHE / "compte.json", {str(n): {k: v for k, v in r.items()} for n, r in resultat.items()})
    print("ECRIT : %s et %s" % (SORTIE_COMPTES, CACHE / "compte.json"), flush=True)
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs, flush=True)
        return 2
    return 0


def etape_classer() -> int:
    spec = importlib.util.spec_from_file_location(
        "juge_q5", RACINE / "phase2" / "checks" / "temps5_q5_les_48_a_juger_par_le_classeur_2026-11-19.py")
    juge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(juge)
    J = juge.preparer_juge()
    tx, designe, src = J["tx"], J["designe"], J["src"]
    print("le juge de ⑤ est pret", flush=True)
    gel, gel_v2, echecs = les_gels(src)
    compte = lire_json(CACHE / "compte.json")
    sorties, classes_par = [], {}
    for n, cle in ((1, "gel"), (3, "gel_v2")):
        ch = {int(a): c for a, c in lire_json(CACHE / ("chaines_s%d.json" % n)).items()}
        g = gel if cle == "gel" else gel_v2
        classes = Counter()
        for ident in sorted(compte[str(n)][cle]):
            ts = g[ident]
            par_dossier = defaultdict(list)
            for a in ts:
                par_dossier[ch[a]].append(a)
            if any(tx.get(a, {}).get("classeur") for a in ts):
                seul = [d for d, ms in par_dossier.items() if all(tx.get(a, {}).get("classeur") for a in ms)]
                classe = "C5 -- une creation du Sheet seule dans son dossier" if seul else "C5 -- autre"
            else:
                vus = {d: any(ident in {r["id"] for r in designe(a)[0]} for a in ms)
                       for d, ms in par_dossier.items()}
                if all(vus.values()):
                    classe = "LE SHEET LES TIENT -- le chainage coupe (ou melange)"
                elif any(vus.values()):
                    classe = "LE GEL DEBORDE -- un dossier que la ligne ne designe pas"
                else:
                    classe = "NON TRANCHE -- le juge ne voit pas la ligne"
            classes[classe] += 1
            sorties.append({"scenario": "%d (%s)" % (n, cle), "id_unique": ident, "dossiers": len(par_dossier),
                            "classe": classe,
                            "transactions": " ".join(
                                "%s:%s(%s)" % (d, "+".join(map(str, sorted(ms))),
                                               "/".join(sorted({tx.get(a, {}).get("genre", "?") for a in ms})))
                                for d, ms in sorted(par_dossier.items()))})
        classes_par[n] = classes
        print("\nCLASSEMENT -- scenario %s, %s : %d lignes" % (NOMS[n], cle, sum(classes.values())), flush=True)
        for k, v in classes.most_common():
            print("   %-60s %4d" % (k, v), flush=True)
        # l'autre bout : un dossier tenu par PLUSIEURS lignes (une meme etiquette ecrite deux fois)
        par_dossier_lignes = defaultdict(set)
        for ident, ts in g.items():
            for a in ts:
                if a in ch:
                    par_dossier_lignes[ch[a]].add(ident)
        plusieurs = {d: ls for d, ls in par_dossier_lignes.items() if len(ls) > 1}
        print("   L'AUTRE BOUT -- dossiers tenus par PLUSIEURS lignes : %d dossiers, %d lignes ; repartition %s"
              % (len(plusieurs), len({i for ls in plusieurs.values() for i in ls}),
                 sorted(Counter(len(v) for v in plusieurs.values()).items())), flush=True)
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sorties[0].keys()))
        w.writeheader()
        w.writerows(sorties)
    print("CSV : %s" % SORTIE, flush=True)
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs, flush=True)
        return 2
    return 0


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "rejeu" and sys.argv[2] in ("1", "2", "3"):
        return etape_rejeu(int(sys.argv[2]))
    if len(sys.argv) >= 2 and sys.argv[1] == "compte":
        return etape_compte()
    if len(sys.argv) >= 2 and sys.argv[1] == "classer":
        return etape_classer()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
