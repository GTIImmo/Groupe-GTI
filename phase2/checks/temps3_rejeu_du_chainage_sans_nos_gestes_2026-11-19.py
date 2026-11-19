#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""TEMPS 3 DU CHANTIER CLASSEUR -- CE QUE NOS GESTES ONT FAIT AU CHAINAGE, PROUVE.   19/11/2026

    .venv\Scripts\python.exe -X utf8 phase2\checks\temps3_rejeu_du_chainage_sans_nos_gestes_2026-11-19.py ^
        --photo <critical_20261110.sqlite decompresse>

⛔ CE SCRIPT N'ECRIT RIEN. phase2.sqlite et la photo sont ouverts en mode=ro ; tout le travail se
  fait dans des bases SQLite EN MEMOIRE, jetees a la fin. Il ecrit deux CSV dans notice/.

LA METHODE (celle du projet : « vraie fonction, copie en memoire ») :
    N   le registre d'AUJOURD'HUI, la VRAIE recalculer_les_chaines() rejouee dessus
    R   le meme registre, NOS 1 236 GESTES DEFAITS (temps 1) : l'etat d'avant lu dans la charge
        de chaque travail, et les entrees que nos gestes ont ajoutees au journal de l'offre
        retirees ; la colonne `date` reprise de la PHOTO du 10/11 a 08:00 (elle n'est dans
        aucune charge) -- puis la meme fonction
    C   N sans les 190 transactions CREEES depuis le classeur (C5, 16/11) -- l'autre geste de
        masse qui a touche le chainage, hors du journal des travaux
    ➡ MEME REGLE, MEMES DONNEES, A NOS GESTES PRES : toute difference N / R est l'effet de nos
      gestes d'etat, toute difference N / C l'effet de C5.

LES TEMOINS
    POSITIF     N rejoue == la base (sinon la fonction ne fait pas ce que la base croit)
    ALLER-RETOUR refaire nos gestes sur R redonne EXACTEMENT N
    INVERSE     les biens que nos gestes n'ont pas touches : 0 transaction ne change de
                compagnie entre N et R (le chainage travaille bien par bien)
    LA PHOTO    l'etat reconstitue des 1 217 transactions touchees, compare a la photo du
                10/11 a 08:00 (avant le premier geste) : etat et journal identiques

LE CLASSEMENT d'une paire de transactions du MEME BIEN qui etaient ensemble et ne le sont plus
(ou l'inverse), avec les yeux de la regle (les numeros d'acquereur, jamais les noms) :
    CASSE            meme NUMERO d'acquereur des deux cotes : une seule affaire, coupee en deux
    CASSE PROBABLE   numeros differents mais MEME NOM DE FAMILLE sur le meme bien : le meme menage
                     sous deux fiches Hektor (26 paires connues)
    A JUGER          noms differents a 31 jours ou moins (le contact change chez Hektor dans
                     une meme affaire : 501 cas connus -- ou c'est un autre acheteur) ; ou un
                     cote sans acquereur ; ou une date qui manque
    CORRECTION       noms differents et plus de 31 jours : deux acheteurs successifs

Sortie : 0 mesure faite . 2 un temoin a echoue (rien n'est prouve).
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date as Date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
from phase2.sync.affaire_ledger import (                            # noqa: E402
    LEDGER_TABLE, _acquereurs, _date_de_tri, recalculer_les_chaines)

GESTES = RACINE / "notice" / "TEMPS1_GESTES_DE_MASSE_2026-11-19.csv"
BASE = RACINE / "phase2" / "phase2.sqlite"
SORTIE_PAIRES = RACINE / "notice" / "TEMPS3_PAIRES_CHANGEES_2026-11-19.csv"
SORTIE_DOSSIERS = RACINE / "notice" / "TEMPS3_DOSSIERS_CHANGES_2026-11-19.csv"
FENETRE = ("2026-11-10", "2026-11-13")       # le jour du premier geste, le lendemain du dernier
JOURS_MEME_AFFAIRE = 31                      # FENETRE_OFFRE_REGULARISEE_JOURS, la regle B


def copie_en_memoire(chemin: Path) -> sqlite3.Connection:
    src = sqlite3.connect(f"file:{chemin}?mode=ro", uri=True)
    mem = sqlite3.connect(":memory:")
    ddl = src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                      (LEDGER_TABLE,)).fetchone()
    mem.execute(ddl[0])
    cols = [r[1] for r in src.execute(f"PRAGMA table_info({LEDGER_TABLE})")]
    mem.executemany(f"INSERT INTO {LEDGER_TABLE} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    list(src.execute(f"SELECT {','.join(cols)} FROM {LEDGER_TABLE}")))
    mem.commit()
    src.close()
    return mem


def cloner(con: sqlite3.Connection) -> sqlite3.Connection:
    autre = sqlite3.connect(":memory:")
    con.backup(autre)
    return autre


def rejouer(con: sqlite3.Connection) -> tuple[dict[int, int], dict]:
    """La VRAIE fonction du run. Son compte rendu imprime est capture, pas perdu."""
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        compte = recalculer_les_chaines(con)
    return dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {LEDGER_TABLE}")), compte


def journal(brut) -> list:
    if isinstance(brut, str):
        try:
            brut = json.loads(brut)
        except ValueError:
            return []
    return brut if isinstance(brut, list) else []


def lire_gestes() -> dict[int, dict]:
    """Par transaction : l'etat d'avant de SON PREMIER geste, et la liste de ses gestes."""
    par_aff: dict[int, dict] = {}
    for g in csv.DictReader(GESTES.open(encoding="utf-8")):
        a = int(g["app_affaire_id"])
        if a not in par_aff:
            par_aff[a] = {"etat_avant": g["etat_avant_lu"], "gestes": []}
        par_aff[a]["gestes"].append(g)
    return par_aff


def defaire(con, gestes, photo_date: dict[int, object]) -> Counter:
    """R : l'etat d'avant (charge), le journal sans nos entrees, la date de la photo."""
    bilan = Counter()
    for a, g in gestes.items():
        ligne = con.execute(f"SELECT state, propositions_json, date FROM {LEDGER_TABLE} "
                            "WHERE app_affaire_id=?", (a,)).fetchone()
        if ligne is None:
            bilan["absente du registre"] += 1
            continue
        etat = None if g["etat_avant"] in ("", "(vide)") else g["etat_avant"]
        entrees = journal(ligne[1])
        gardees = [e for e in entrees if not (
            isinstance(e, dict) and e.get("type") in ("refus", "accepte")
            and FENETRE[0] <= str(e.get("date") or "") < FENETRE[1])]
        bilan["entrees de journal retirees"] += len(entrees) - len(gardees)
        props = json.dumps(gardees, ensure_ascii=False) if ligne[1] is not None else None
        if a in photo_date:
            date = photo_date[a]
            bilan["date reprise de la photo"] += 1
        else:
            date = ligne[2]
            bilan["date GARDEE (absente de la photo)"] += 1
        con.execute(f"UPDATE {LEDGER_TABLE} SET state=?, propositions_json=?, date=? "
                    "WHERE app_affaire_id=?", (etat, props, date, a))
    con.commit()
    return bilan


def refaire(con, gestes, aujourdhui: sqlite3.Connection) -> None:
    """L'aller-retour : remettre exactement les colonnes d'aujourd'hui sur les transactions touchees."""
    for a in gestes:
        v = aujourdhui.execute(f"SELECT state, propositions_json, date FROM {LEDGER_TABLE} "
                               "WHERE app_affaire_id=?", (a,)).fetchone()
        if v:
            con.execute(f"UPDATE {LEDGER_TABLE} SET state=?, propositions_json=?, date=? "
                        "WHERE app_affaire_id=?", (*v, a))
    con.commit()


def infos(con) -> dict[int, dict]:
    out = {}
    for a, bien, genre, etat, d, acq, hacq, props, montant, num, pres, orig in con.execute(
            f"SELECT app_affaire_id, hektor_annonce_id, kind, state, date, acquereurs_json, "
            f"hektor_acquereur_id, propositions_json, montant, hektor_affaire_id, present_in_hektor, "
            f"transaction_origine FROM {LEDGER_TABLE}"):
        acqs = _acquereurs(acq)
        if not acqs and str(hacq or "").strip() not in ("", "0"):
            acqs = {str(hacq).strip()}
        # LES NOMS DE FAMILLE -- jamais pour REUNIR (la regle ne le fait pas, un nom partage est
        # un couple ou un homonyme dans 109 cas mesures), seulement pour CLASSER une separation
        # sur un MEME bien : meme nom des deux cotes = le meme menage sous deux fiches Hektor.
        brut = acq
        if isinstance(brut, str):
            try:
                brut = json.loads(brut)
            except ValueError:
                brut = []
        if isinstance(brut, dict):
            brut = [brut]
        noms = {str(p.get("nom") or "").strip().upper() for p in (brut if isinstance(brut, list) else [])
                if isinstance(p, dict) and str(p.get("nom") or "").strip()}
        out[int(a)] = {"bien": str(bien), "genre": str(genre or ""), "etat": str(etat or ""),
                       "tri": _date_de_tri(genre, d, props), "acqs": acqs, "noms": noms, "montant": montant,
                       "effacee": bool(str(num or "").strip()) and str(pres) in ("0", "false", "False"),
                       "classeur": bool(str(orig or "").strip())}
    return out


def groupes(chaines: dict[int, int], univers: set[int]) -> dict[int, frozenset]:
    """transaction -> l'ensemble de ses compagnons de dossier (elle comprise), dans l'univers."""
    par = defaultdict(set)
    for a in univers:
        par[chaines[a]].add(a)
    return {a: frozenset(par[chaines[a]]) for a in univers}


def jour(t):
    try:
        return Date.fromisoformat(str(t)[:10])
    except (TypeError, ValueError):
        return None


def classer(x: dict, y: dict) -> str:
    if not x["acqs"] or not y["acqs"]:
        return "A JUGER (un cote sans acquereur)"
    if x["acqs"] & y["acqs"]:
        return "CASSE (meme acquereur)"
    if x["noms"] & y["noms"]:
        return "CASSE PROBABLE (meme nom, deux fiches Hektor)"
    jx, jy = jour(x["tri"]), jour(y["tri"])
    if jx is None or jy is None:
        return "A JUGER (une date manque)"
    if abs((jx - jy).days) <= JOURS_MEME_AFFAIRE:
        try:
            meme = float(x["montant"] or 0) == float(y["montant"] or 0) and float(x["montant"] or 0) > 0
        except (TypeError, ValueError):
            meme = False
        return "A JUGER (noms differents, 31 j, meme montant)" if meme else "A JUGER (31 j, montants differents)"
    return "CORRECTION (deux acheteurs successifs)"


RANG = ["CASSE (meme acquereur)", "CASSE PROBABLE (meme nom, deux fiches Hektor)",
        "A JUGER (noms differents, 31 j, meme montant)", "A JUGER (31 j, montants differents)",
        "A JUGER (un cote sans acquereur)", "A JUGER (une date manque)",
        "CORRECTION (deux acheteurs successifs)"]


def verdict_par_dossier(paires: list[dict]) -> Counter:
    """Un dossier d'avant coupe prend le verdict de SA PIRE paire separee."""
    par = defaultdict(list)
    for p in paires:
        if p["sens"].startswith("SEPAREES"):
            par[p["dossier_avant_a"]].append(p["classement"])
    return Counter(min(v, key=lambda k: RANG.index(k) if k in RANG else 99) for v in par.values())


def comparer(avant: dict[int, int], apres: dict[int, int], univers: set[int], info: dict,
             touchees: set[int], geste: str) -> tuple[list[dict], list[dict]]:
    ga, gp = groupes(avant, univers), groupes(apres, univers)
    paires, vus = [], set()
    for a in univers:
        if ga[a] == gp[a]:
            continue
        for b in (ga[a] ^ gp[a]):
            cle = (min(a, b), max(a, b))
            if cle in vus:
                continue
            vus.add(cle)
            x, y = info[cle[0]], info[cle[1]]
            sens = "SEPAREES par le geste" if b in ga[a] else "REUNIES par le geste"
            paires.append({
                "geste": geste, "sens": sens, "bien": x["bien"],
                "a": cle[0], "genre_a": x["genre"], "etat_a": x["etat"], "date_a": x["tri"] or "",
                "b": cle[1], "genre_b": y["genre"], "etat_b": y["etat"], "date_b": y["tri"] or "",
                "touchee": ",".join(str(t) for t in cle if t in touchees),
                "classement": classer(x, y) if sens.startswith("SEPAREES") else
                ("REUNION (meme acquereur)" if (x["acqs"] & y["acqs"]) else "REUNION (acquereurs differents)"),
                "dossier_avant_a": avant[cle[0]], "dossier_avant_b": avant[cle[1]],
                "dossier_apres_a": apres[cle[0]], "dossier_apres_b": apres[cle[1]]})
    # LES DOSSIERS : un dossier d'avant coupe, ou des dossiers d'avant reunis
    dossiers = []
    avant_par = defaultdict(set)
    apres_par = defaultdict(set)
    for a in univers:
        avant_par[avant[a]].add(a)
        apres_par[apres[a]].add(a)
    for ch, membres in avant_par.items():
        devenus = {apres[m] for m in membres}
        if len(devenus) > 1:
            dossiers.append({"geste": geste, "sens": "SCISSION", "dossier": ch, "membres": len(membres),
                             "en": len(devenus), "bien": info[next(iter(membres))]["bien"],
                             "touchees": len(membres & touchees)})
    for ch, membres in apres_par.items():
        venus = {avant[m] for m in membres}
        if len(venus) > 1:
            dossiers.append({"geste": geste, "sens": "REUNION", "dossier": ch, "membres": len(membres),
                             "en": len(venus), "bien": info[next(iter(membres))]["bien"],
                             "touchees": len(membres & touchees)})
    return paires, dossiers


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True, help="critical_20261110.sqlite decompresse")
    args = ap.parse_args()
    photo = Path(args.photo)
    gestes = lire_gestes()
    touchees = set(gestes)
    echecs = []

    # ── N : aujourd'hui ──────────────────────────────────────────────────────────
    n_con = copie_en_memoire(BASE)
    en_base = dict(n_con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {LEDGER_TABLE}"))
    n, compte_n = rejouer(cloner(n_con))
    ecart_base = sum(1 for a, c in n.items() if en_base.get(a) != c)
    print("N  registre d'aujourd'hui : %d transactions, %d dossiers . ecart avec la base : %d"
          % (len(n), len(set(n.values())), ecart_base))
    if ecart_base:
        echecs.append("temoin positif : N rejoue != la base")
    info_n = infos(n_con)

    # ── la photo du 10/11 a 08:00 ────────────────────────────────────────────────
    p_con = copie_en_memoire(photo)
    p_lignes = {int(a): (s, pj, d) for a, s, pj, d in p_con.execute(
        f"SELECT app_affaire_id, state, propositions_json, date FROM {LEDGER_TABLE}")}
    photo_date = {a: v[2] for a, v in p_lignes.items()}

    # ── R : nos gestes defaits ───────────────────────────────────────────────────
    r_con = cloner(n_con)
    bilan = defaire(r_con, gestes, photo_date)
    print("R  defaire nos gestes : %s" % dict(bilan))
    # LA PHOTO JUGE LA RECONSTITUTION, transaction par transaction
    juge = Counter()
    for a in touchees:
        v = r_con.execute(f"SELECT state, propositions_json FROM {LEDGER_TABLE} WHERE app_affaire_id=?",
                          (a,)).fetchone()
        if a not in p_lignes:
            juge["absente de la photo"] += 1
            continue
        ps, ppj, _ = p_lignes[a]
        juge["etat identique" if (v[0] or "") == (ps or "") else "ETAT DIFFERENT"] += 1
        jr = [(e.get("type"), str(e.get("date"))) for e in journal(v[1]) if isinstance(e, dict)]
        jp = [(e.get("type"), str(e.get("date"))) for e in journal(ppj) if isinstance(e, dict)]
        juge["journal identique" if sorted(jr) == sorted(jp) else "JOURNAL DIFFERENT"] += 1
    print("   la photo du 10/11 juge la reconstitution : %s" % dict(juge))
    r, compte_r = rejouer(cloner(r_con))
    print("R  registre sans nos gestes : %d dossiers" % len(set(r.values())))

    # ── LA FAUSSE PISTE ① DU § 8.3, REJOUEE : l'ETAT seul, dates et journaux d'aujourd'hui ──
    e_con = cloner(n_con)
    for a, g in gestes.items():
        etat = None if g["etat_avant"] in ("", "(vide)") else g["etat_avant"]
        e_con.execute(f"UPDATE {LEDGER_TABLE} SET state=? WHERE app_affaire_id=?", (etat, a))
    e_con.commit()
    e, _ = rejouer(e_con)
    ecart_date = sum(1 for a in r if e.get(a) != r[a])
    print("§ 8.3 ① : defaire l'ETAT SEUL (dates et journaux d'aujourd'hui) donne R a %d ecart(s) pres"
          " -- la date et le journal deplaces par nos gestes %s" % (
              ecart_date, "N'ONT RIEN FAIT au chainage" if ecart_date == 0 else "ONT JOUE"))

    # ── l'aller-retour ───────────────────────────────────────────────────────────
    aller = cloner(r_con)
    refaire(aller, gestes, n_con)
    retour, _ = rejouer(aller)
    ecart_retour = sum(1 for a, c in n.items() if retour.get(a) != c)
    print("ALLER-RETOUR : refaire nos gestes sur R redonne N a %d ecart(s) pres" % ecart_retour)
    if ecart_retour:
        echecs.append("aller-retour")

    # ── l'effet de nos gestes d'etat : R -> N ────────────────────────────────────
    univers = {a for a, i in info_n.items() if not i["effacee"]}
    paires_g, dossiers_g = comparer(r, n, univers, info_n, touchees, "etat (1 236 gestes)")
    biens_touches = {info_n[a]["bien"] for a in touchees if a in info_n}
    hors = [p for p in paires_g if p["bien"] not in biens_touches]
    print("TEMOIN INVERSE : paires changees sur un bien NON touche : %d" % len(hors))
    if hors:
        echecs.append("temoin inverse : un bien non touche a bouge")

    # ── C : sans les 190 creations du classeur ───────────────────────────────────
    c_con = cloner(n_con)
    c_ids = {a for a, i in info_n.items() if i["classeur"]}
    c_con.executemany(f"DELETE FROM {LEDGER_TABLE} WHERE app_affaire_id=?", [(a,) for a in c_ids])
    c_con.commit()
    c, _ = rejouer(c_con)
    univers_c = univers - c_ids
    paires_c, dossiers_c = comparer(c, n, univers_c, info_n, set(), "C5 (190 creations)")
    # ce que C5 fait aux transactions de HEKTOR (les creations elles-memes sont a part)
    c5_seules = sum(1 for a in c_ids if a in univers and sum(1 for b in univers if n[b] == n[a]) == 1)

    # ── LE COMPTE RENDU ──────────────────────────────────────────────────────────
    for titre, paires, dossiers in (("NOS 1 236 GESTES D'ETAT", paires_g, dossiers_g),
                                    ("LES 190 CREATIONS C5 (sur les transactions de Hektor)", paires_c, dossiers_c)):
        print("\n=== %s ===" % titre)
        print("   dossiers coupes   : %d" % sum(1 for d in dossiers if d["sens"] == "SCISSION"))
        print("   dossiers reunis   : %d" % sum(1 for d in dossiers if d["sens"] == "REUNION"))
        print("   paires de transactions qui ont change de compagnie : %d" % len(paires))
        for (s, k), v in sorted(Counter((p["sens"], p["classement"]) for p in paires).items()):
            print("      %-22s %-48s %5d" % (s, k, v))
        print("   par genres : %s" % dict(Counter("%s-%s" % tuple(sorted((p["genre_a"], p["genre_b"])))
                                                for p in paires)))
        print("   DOSSIERS COUPES, au verdict de leur pire paire :")
        for k, v in sorted(verdict_par_dossier(paires).items(), key=lambda kv: RANG.index(kv[0])):
            print("      %-48s %5d" % (k, v))
        print("   paires dont AUCUN membre n'a ete touche (ricochet dans le bien) : %d"
              % sum(1 for p in paires if not p["touchee"]))
    print("\nC5 : %d creations seules dans leur dossier (sur %d)" % (c5_seules, len(c_ids)))
    cles = sorted(set(compte_n) | set(compte_r))
    print("\nCE QUE LES REGLES ONT FAIT -- avec nos gestes (N) / sans (R) :")
    for k in cles:
        if isinstance(compte_n.get(k), (int, float)) and not isinstance(compte_n.get(k), bool) \
                and compte_n.get(k) != compte_r.get(k):
            print("   %-70s %6s / %6s" % (k[:70], compte_n.get(k), compte_r.get(k)))

    champs = ["geste", "sens", "classement", "bien", "a", "genre_a", "etat_a", "date_a", "b", "genre_b",
              "etat_b", "date_b", "touchee", "dossier_avant_a", "dossier_avant_b", "dossier_apres_a",
              "dossier_apres_b"]
    with SORTIE_PAIRES.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(paires_g + paires_c)
    with SORTIE_DOSSIERS.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["geste", "sens", "dossier", "membres", "en", "bien", "touchees"])
        w.writeheader()
        w.writerows(dossiers_g + dossiers_c)
    print("\nCSV : %s\n      %s" % (SORTIE_PAIRES, SORTIE_DOSSIERS))
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s -- rien n'est prouve (code 2)." % echecs)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
