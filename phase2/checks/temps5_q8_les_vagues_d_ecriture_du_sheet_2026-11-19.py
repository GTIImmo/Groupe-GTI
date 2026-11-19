#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""QUESTION 8 -- ECRIRE NOS ETIQUETTES DANS LE SHEET (colonne A « affair_uuid ») : LA MESURE AVANT.
                                                                                      19/11/2026

    .venv\Scripts\python.exe -X utf8 -u phase2\checks\temps5_q8_les_vagues_d_ecriture_du_sheet_2026-11-19.py

⛔ CE SCRIPT N'ECRIT RIEN, ET SURTOUT PAS DANS LE SHEET : il le LIT (un GET), lit la base en mode=ro,
  et ecrit deux fichiers dans notice/. Il ne decide rien : il range chaque ligne du Sheet dans UNE case
  -- la PREMIERE raison, dans l'ordre ci-dessous, qui l'empeche d'entrer dans la vague 1.

LES RAISONS D'ATTENDRE, dans l'ordre (une ligne prend la premiere qui la concerne) :
    A_DEJA_REMPLIE      la colonne A porte deja une valeur : on n'ecrase JAMAIS
    SANS_LIEN           aucune transaction reliee (le gel)
    EN_ATTENTE          une des 37 lignes a question ouverte, incertaine, ou sortie du patch V2
    PATCH_V2            le patch V2 lui retire ou lui ajoute un lien : elle attend qu'il soit joue
    CETTE_NUIT          une de ses transactions change de dossier cette nuit (les 10 menages)
    PLUSIEURS_DOSSIERS  ses transactions sont dans plusieurs dossiers (⑥) : quelle etiquette ?
    ETIQUETTE_PARTAGEE  son dossier porte aussi une AUTRE ligne : le meme UUID sur deux affaires
    LIEN_A_VALIDER      un de ses liens n'est pas de confiance « sure »
    AUDIT_NON_JUSTE     l'audit du 18/11 l'a jugee autrement que JUSTE
    C5_SEULE            toutes ses transactions sont des creations C5 (circulaire par construction)
    GEL_SEUL            le juge de ⑤ ne retrouve, par les colonnes independantes, AUCUNE transaction
                        de son dossier sur cette ligne : le lien ne tient qu'au gel
    VAGUE_1             rien de tout cela

Et la meme mesure dans l'etat « APRES » : apres la nuit (les 10 menages appliques) et apres le patch V2
joue -- les cases PATCH_V2 et CETTE_NUIT s'y vident.

Sortie : 0 mesure faite . 2 un temoin a echoue . 3 une etape de ⑥ manque (le cache des chaines).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
BASE = RACINE / "phase2" / "phase2.sqlite"
CACHE = RACINE.parent / "chantier_classeur_q6_cache"
PATCH_V2 = RACINE / "supabase" / "patch_correction_gel_audit_v2_2026-11-19.sql"
VERDICTS = RACINE / "notice" / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv"
OPERATIONS = RACINE / "notice" / "AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv"
SORTIE = RACINE / "notice" / "TEMPS5_Q8_LES_LIGNES_DU_SHEET_ET_LEUR_VAGUE_2026-11-19.csv"
ORDRE = ["A_DEJA_REMPLIE", "SANS_LIEN", "EN_ATTENTE", "PATCH_V2", "CETTE_NUIT", "PLUSIEURS_DOSSIERS",
         "ETIQUETTE_PARTAGEE", "LIEN_A_VALIDER", "AUDIT_NON_JUSTE", "C5_SEULE", "GEL_SEUL", "VAGUE_1"]


def charger_juge():
    spec = importlib.util.spec_from_file_location(
        "juge_q5", RACINE / "phase2" / "checks" / "temps5_q5_les_48_a_juger_par_le_classeur_2026-11-19.py")
    juge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(juge)
    return juge


def main() -> int:
    echecs = []
    juge = charger_juge()
    J = juge.preparer_juge()                       # lit le Sheet (GET) et le registre (mode=ro)
    tx, vue, designe, src = J["tx"], J["vue"], J["designe"], J["src"]
    entete, lignes = juge.ac.lire_classeur()       # la colonne A n'est pas dans `vue` : on la relit
    print("le juge est pret ; Sheet relu : %d lignes" % len(lignes), flush=True)
    col_a = {}
    for num, l in lignes:
        l = list(l) + [""] * 38
        col_a[l[37].strip()] = l[0].strip()
    assert entete[0] == "affair_uuid" and entete[37] == "ID Unique", "l'en-tete du Sheet a bouge"

    # le gel, ses confiances, et le gel apres le patch V2
    gel, conf = defaultdict(set), defaultdict(set)
    for ident, a, c in src.execute("SELECT id_unique, app_affaire_id, confiance FROM app_classeur_lien"):
        gel[ident].add(a)
        conf[ident].add(c)
    texte = PATCH_V2.read_text(encoding="utf-8")
    b3 = texte.split("-- ── ③ RETIRER")[1].split("-- ── ④ AJOUTER")[0]
    b4 = texte.split("-- ── ④ AJOUTER")[1].split("-- ── ⑤ LE CONTROLE")[0]
    retraits = {(i, int(a)) for i, a in re.findall(r"\('([^']+)',\s*(\d+),\s*'\w+'\)", b3)}
    ajouts = [(i, int(a), c) for a, c, i in re.findall(r"\(\d+,\s*(\d+),\s*'\w+',\s*'([^']+)',.*?'([^']+)'\)", b4)]
    touchees_v2 = {i for i, _ in retraits} | {i for i, _, _ in ajouts}
    gel_v2, conf_v2 = defaultdict(set, {k: set(v) for k, v in gel.items()}), defaultdict(set)
    for i, a in retraits:
        gel_v2[i].discard(a)
    for i, a, c in ajouts:
        gel_v2[i].add(a)
    for i in gel:
        conf_v2[i] = set(conf[i])
    for i, a, c in ajouts:
        conf_v2[i].add(c)
    print("patch V2 : %d retraits, %d ajouts, %d lignes touchees" % (len(retraits), len(ajouts), len(touchees_v2)),
          flush=True)

    # les lignes qui attendent une decision
    verdicts = {}
    with VERDICTS.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            verdicts[r["id_unique"]] = r
    en_attente = {i for i, r in verdicts.items() if r["question_pour_frederic"].strip()
                  or "INCERTAIN" in (r["verdict"] + r["correction_contre_expert"]).upper()} | {"SHN6RKDI"}
    with OPERATIONS.open(encoding="utf-8-sig") as f:
        en_attente |= {r["id_unique"] for r in csv.DictReader(f, delimiter=";") if r["decision_v2"] != "GARDEE"}
    print("lignes en attente de decision : %d" % len(en_attente), flush=True)

    # les chaines et les etiquettes
    base_ch, base_uuid = {}, {}
    for a, ch, u in src.execute("SELECT app_affaire_id, app_chaine_id, app_dossier_uuid FROM app_affaire_ledger"):
        base_ch[a], base_uuid[a] = ch, u
    s1_fichier = CACHE / "chaines_s1.json"
    if not s1_fichier.exists():
        print("⛔ le cache de ⑥ manque : lancer d'abord « rejeu 1 » de temps5_q6 (code 3)", flush=True)
        return 3
    s1 = {int(a): c for a, c in json.loads(s1_fichier.read_text(encoding="utf-8")).items()}
    cette_nuit = {a for a in base_ch if s1.get(a) != base_ch[a]}
    print("transactions qui changent de dossier cette nuit : %d (attendu 10)" % len(cette_nuit), flush=True)
    if len(cette_nuit) != 10:
        echecs.append("cette nuit : %d" % len(cette_nuit))
    # TEMOIN : une etiquette par dossier, un dossier par etiquette, sur la base
    par_ch = defaultdict(set)
    for a, ch in base_ch.items():
        par_ch[ch].add(base_uuid[a])
    uuid_ch = defaultdict(set)
    for a, u in base_uuid.items():
        uuid_ch[u].add(base_ch[a])
    mauvais = sum(1 for v in par_ch.values() if len(v) != 1 or None in v) + sum(1 for v in uuid_ch.values() if len(v) != 1)
    print("TEMOIN etiquette = dossier sur la base : %d ecart(s) (attendu 0)" % mauvais, flush=True)
    if mauvais:
        echecs.append("etiquette != dossier")

    def ranger(g: dict, cf: dict, ch: dict, apres: bool) -> dict:
        lignes_du_dossier = defaultdict(set)
        for i, ts in g.items():
            for a in ts:
                if a in ch:
                    lignes_du_dossier[ch[a]].add(i)
        rangs = {}
        for num, rec in vue.items():
            i = rec["id"]
            ts = {a for a in g.get(i, set()) if a in ch}
            dossiers = {ch[a] for a in ts}
            if col_a.get(i):
                r = "A_DEJA_REMPLIE"
            elif not ts:
                r = "SANS_LIEN"
            elif i in en_attente:
                r = "EN_ATTENTE"
            elif not apres and i in touchees_v2:
                r = "PATCH_V2"
            elif not apres and ts & cette_nuit:
                r = "CETTE_NUIT"
            elif len(dossiers) > 1:
                r = "PLUSIEURS_DOSSIERS"
            elif lignes_du_dossier[next(iter(dossiers))] - {i}:
                r = "ETIQUETTE_PARTAGEE"
            elif cf.get(i, set()) - {"sûre"}:
                r = "LIEN_A_VALIDER"
            elif i in verdicts and verdicts[i]["verdict"] not in ("JUSTE", "JUSTE_SANS_PREUVE_FORTE"):
                r = "AUDIT_NON_JUSTE"
            elif all(tx.get(a, {}).get("classeur") for a in ts):
                r = "C5_SEULE"
            elif not any(i in {x["id"] for x in designe(a)[0]} for a in ts):
                r = "GEL_SEUL"
            else:
                r = "VAGUE_1"
            rangs[i] = (r, num, sorted(dossiers), sorted(ts))
        return rangs

    avant = ranger(gel, conf, base_ch, False)
    apres = ranger(gel_v2, conf_v2, s1, True)
    print("\nLES %d LIGNES DU SHEET, rangees par la premiere raison d'attendre :" % len(vue), flush=True)
    print("   %-20s %10s %22s" % ("", "AUJOURD'HUI", "APRES nuit + patch V2"), flush=True)
    ca, cb = Counter(r[0] for r in avant.values()), Counter(r[0] for r in apres.values())
    for k in ORDRE:
        print("   %-20s %10d %22d" % (k, ca[k], cb[k]), flush=True)
    print("   %-20s %10d %22d" % ("TOTAL", sum(ca.values()), sum(cb.values())), flush=True)

    # LA VAGUE 1 D'AUJOURD'HUI : l'etiquette a ecrire, et ses gardes
    sorties = []
    for i, (r, num, dossiers, ts) in sorted(avant.items(), key=lambda x: x[1][1]):
        uuid = base_uuid[ts[0]] if r == "VAGUE_1" else ""
        if r == "VAGUE_1" and len({base_uuid[a] for a in ts}) != 1:
            echecs.append("vague 1 a deux etiquettes : %s" % i)
        sorties.append({"id_unique": i, "ligne_au_19_11": num, "case_aujourd_hui": r, "case_apres": apres[i][0],
                        "etiquette_a_ecrire": uuid, "dossier": " ".join(map(str, dossiers)),
                        "transactions": " ".join(map(str, ts))})
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sorties[0].keys()))
        w.writeheader()
        w.writerows(sorties)
    print("CSV : %s" % SORTIE, flush=True)
    v1 = [s for s in sorties if s["case_aujourd_hui"] == "VAGUE_1"]
    print("VAGUE 1 : %d lignes ; etiquettes distinctes %d (attendu : autant que de lignes)"
          % (len(v1), len({s["etiquette_a_ecrire"] for s in v1})), flush=True)
    if len(v1) != len({s["etiquette_a_ecrire"] for s in v1}):
        echecs.append("une etiquette sur deux lignes de la vague 1")
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
